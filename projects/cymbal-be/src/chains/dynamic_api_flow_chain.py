from typing import Dict, Union, Tuple, Optional
from helpers.vertexai import LoggingVertexAI, LoggingVertexAIChat
from langchain.chains import LLMChain
from helpers.json_parsers import (
    parse_malformed_dynamicapi_json,
    retry_on_error_with_llm_output_parser,
)
from helpers.logging_configurator import logger, request_origin
from prompts.dynamic_api_prompt import DynamicAPIPrompt
import logging
from helpers.vertexai import LoggingVertexAIEmbeddings
from langchain.vectorstores import FAISS
import os
from google.cloud import storage
from config.config import configcontex
from langchain.llms.vertexai import _VertexAICommon


class DynamicAPIFlowChain:
    def __init__(
        self,
        bucket_name: str = "gs://cymbal-kb-bucket",
        llm: Optional[_VertexAICommon] = None,
        dynamic_api_prompt: Optional[DynamicAPIPrompt] = None,
        llm_chain: Optional[LLMChain] = None,
        folder_name: Optional[str] = "preprocessed_output",
        index_name: Optional[str] = "nlp_router_examples_dynamic",
        vertexai_params: Optional[dict] = {
            "temperature": 0.3,
            "max_output_tokens": 64,
            "top_p": 0.8,
            "top_k": 40,
        },
        similarity_search_k: Optional[int] = 3,
    ):
        """
        The constructor for the SmallTalkChain class.
        """
        self.bucket_name = self.strip_gs_prefix(bucket_name)
        self.folder_name = folder_name
        self.index_name = index_name
        self.logger = self._setup_logger()
        if(configcontex.FEATURE_CHAT_BISON == "True"):
            self.llm = llm if llm else LoggingVertexAIChat(**vertexai_params)
        else:
            self.llm = llm if llm else LoggingVertexAI(**vertexai_params)
        self.dynamic_api_prompt = dynamic_api_prompt or DynamicAPIPrompt(
            bucket_name=self.bucket_name
        )
        (
            self.prompt,
            self.output_parser,
        ) = self.dynamic_api_prompt.create_dynamic_api_prompt()
        self.embeddings = LoggingVertexAIEmbeddings()
        self.vectorstore = self.vectorstore_load_from_gcs()
        self.initialize_llm_chain(llm_chain)
        self.similarity_search_k = similarity_search_k

    def strip_gs_prefix(self, bucket_name):
        """Strips 'gs://' from the bucket name if present"""
        return bucket_name[5:] if "gs://" in bucket_name else bucket_name

    def _setup_logger(self):
        """Sets up a logger for the class."""
        logger = logging.getLogger(__name__)
        return logger

    def log(self, level, message):
        """Logs a message at a given level."""
        self.logger.log(
            level, f"DynamicAPIFlowChain - Origin: {request_origin.get()} | {message}"
        )

    def copy_from_gcs(self, path_name: str):
        """Copy the folder from a GCS Bucket to a local path.

        Args:
            bucket_name: Name of the GCS bucket.
            folder_name: Name of the folder to download from the GCS bucket.
            destination_folder_path: Local path where the folder will be copied to.
        """
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(self.bucket_name)
        blobs = blobs = bucket.list_blobs(
            prefix="preprocessed_output/nlp_router_examples_dynamic/", delimiter="/"
        )

        for blob in blobs:
            self.log(logging.INFO, f"Blob {blob.name}")
            file_name = blob.name.split("/")[-1]
            destination_file_name = os.path.join(path_name, file_name)
            blob.download_to_filename(destination_file_name)
            self.log(
                logging.INFO, f"Blob {blob.name} downloaded to {destination_file_name}."
            )

        return True

    def vectorstore_load_from_gcs(self):
        path_name = os.path.join(self.folder_name, self.index_name)
        self.log(logging.INFO, f"Path Name:{path_name}")
        os.makedirs(path_name, exist_ok=True)
        
        if not os.listdir(path_name):
            self.log(logging.INFO, f"Path Name:{path_name} NOT FOUND, COPYING from GCS")
            self.copy_from_gcs(path_name)
        else:
            self.log(logging.INFO, f"Path Name:{path_name} FOUND, REFRESHING from GCS")
            self.copy_from_gcs(path_name)
            
        db = FAISS.load_local(path_name, self.embeddings)
        return db

    def initialize_llm_chain(self, llm_chain: Optional[LLMChain]):
        """Initializes the LLMChain with the given llm and prompt."""
        try:
            self.llm_chain = (
                llm_chain if llm_chain else LLMChain(llm=self.llm, prompt=self.prompt)
            )
        except Exception as e:
            self.log(
                logging.ERROR,
                f"An error occurred while initializing LLMChain: {str(e)}",
            )
            raise

    def parse_llm_response(
        self, llm_response: Union[Dict[str, str], str]
    ) -> Union[Dict[str, str], str]:
        """Parses the LLM response and logs the information."""
        try:
            parsed_llm_response = self._parse_and_check_keys(llm_response)
        except KeyError:
            self.log(logging.ERROR, f"Missing keys in response: {llm_response}")
            raise
        except Exception:
            self.log(
                logging.WARNING,
                f"Coercion to Pydantic Object failed. Attempting to parse malformed JSON: {str(llm_response)}",
            )
            parsed_llm_response = self._handle_malformed_json(llm_response)

        return parsed_llm_response

    def _parse_and_check_keys(self, llm_response):
        """Parses the LLM response and checks for required keys."""
        parsed_llm_response = self.output_parser.parse(llm_response).dict()
        required_keys = {"Response"}
        missing_keys = required_keys - parsed_llm_response.keys()
        if missing_keys:
            raise KeyError(f"Missing keys in response: {', '.join(missing_keys)}")
        return parsed_llm_response["Response"]

    def _handle_malformed_json(self, llm_response):
        """Handles situations where the LLM response cannot be parsed into a dictionary."""
        try:
            parsed_llm_response = parse_malformed_dynamicapi_json(llm_response)
            self.log(
                logging.WARNING,
                f"Post Static JSON Parsing Attempt: {parsed_llm_response}",
            )
        except Exception:
            parsed_llm_response = retry_on_error_with_llm_output_parser(
                llm_response, self.output_parser
            )
            self.log(logging.WARNING, f"Post LLM Fixing Attempt: {parsed_llm_response}")
        return parsed_llm_response

    def process_query(self, query: str) -> Union[Dict[str, str], str]:
        """
        Processes the query, logging the necessary information and parsing the response.
        """
        if not query:
            self.log(logging.ERROR, "Query cannot be None or empty")
            raise ValueError("Query cannot be None or empty")

        dynamic_api_example_docs = self.vectorstore.similarity_search(
            query, k=self.similarity_search_k
        )
        dynamic_api_example_list = [dict(e.metadata) for e in dynamic_api_example_docs]
        dynamic_api_examples = "\n\n".join(
            [
                f"{str(k)}: {str(v)}"
                for d in dynamic_api_example_list
                for k, v in d.items()
            ]
        )
        self.log(logging.INFO, f"Query: {query} Examples: {dynamic_api_examples}")

        llm_response = self.llm_chain.run(
            {"Query": query, "Examples": dynamic_api_examples}
        )
        if not llm_response:
            self.log(
                logging.ERROR,
                "LLM-Response Error, DynamicAPIFlowChain Stage Response is empty.",
            )
            raise ValueError(
                "LLM-Response Error, DynamicAPIFlowChain Stage Response cannot be empty or None"
            )

        return self.parse_llm_response(llm_response)
