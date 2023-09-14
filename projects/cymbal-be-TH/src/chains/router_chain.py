import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Union
import pytz
from google.cloud import storage

from helpers.json_parsers import (
    parse_malformed_nlurouter_json,
    retry_on_error_with_llm_output_parser,
)
from helpers.logging_configurator import logger, request_origin
from helpers.vertexai import LoggingVertexAIEmbeddings, LoggingVertexAI, LoggingVertexAIChat
from langchain.chains import LLMChain
from langchain.vectorstores import FAISS
from prompts.routing_prompt import NLURoutingPrompt
from config.config import configcontex
from langchain.llms.vertexai import _VertexAICommon

class NLURouterChain:
    def __init__(
        self,
        bucket_name: str = "gs://cymbal-kb-bucket",
        llm: Optional[_VertexAICommon] = None,
        vertexai_params: Optional[Dict[str, float]] = None,
        folder_name: Optional[str] = "preprocessed_output",
        index_name: Optional[str] = "nlp_router_examples",
        nlu_routing_prompt: Optional[NLURoutingPrompt] = None,
    ):
        self.logger = self._setup_logger()
        self.bucket_name = bucket_name[5:] if "gs://" in bucket_name else bucket_name
        self.folder_name = folder_name
        self.index_name = index_name

        if(configcontex.FEATURE_CHAT_BISON == "True"):
            self.llm = (
                llm
                if llm
                else LoggingVertexAIChat(
                    **(
                        vertexai_params
                        or {
                            "temperature": 0.3,
                            "max_output_tokens": 64,
                            "top_p": 0.5,
                            "top_k": 20,
                        }
                    )
                )
            )
        else:
            self.llm = (
                llm
                if llm
                else LoggingVertexAI(
                    **(
                        vertexai_params
                        or {
                            "temperature": 0.3,
                            "max_output_tokens": 64,
                            "top_p": 0.5,
                            "top_k": 20,
                        }
                    )
                )
            )            
            
        self.nlu_routing_prompt = nlu_routing_prompt or NLURoutingPrompt(
            bucket_name=self.bucket_name
        )
        (
            self.prompt,
            self.output_parser,
        ) = self.nlu_routing_prompt.create_nlu_routing_prompt()
        self.embeddings = LoggingVertexAIEmbeddings(model_name="textembedding-gecko@latest", task_type = "SEMANTIC_SIMILARITY")
        self.vectorstore = self._load_vectorstore_from_gcs()
        self._initialize_llm_chain()

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(__name__)
        return logger

    def log(self, level: int, message: str) -> None:
        self.logger.log(
            level, f"NLURouterChain - Origin: {request_origin.get()} | {message}"
        )

    def copy_from_gcs(self, path_name: str) -> bool:
        storage_client = storage.Client()
        bucket = storage_client.get_bucket(self.bucket_name)
        blobs = bucket.list_blobs(
            prefix="preprocessed_output/nlp_router_examples/", delimiter="/"
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

    def _load_vectorstore_from_gcs(self) -> FAISS:
        path_name = os.path.join(self.folder_name, self.index_name)
        self.log(logging.INFO, f"Path Name: {path_name}")
        os.makedirs(path_name, exist_ok=True)
        
        if not os.listdir(path_name):
            self.log(logging.INFO, f"Path Name:{path_name} NOT FOUND, COPYING from GCS")
            self.copy_from_gcs(path_name)
        else:
            self.log(logging.INFO, f"Path Name:{path_name} FOUND, REFRESHING from GCS")
            self.copy_from_gcs(path_name)
        
        db = FAISS.load_local(path_name, self.embeddings)
        return db

    def _initialize_llm_chain(self) -> None:
        try:
            self.llm_chain = LLMChain(llm=self.llm, prompt=self.prompt)
        except AssertionError as ae:
            self.log(logging.ERROR, f"AssertionError: {str(ae)}")
            raise
        except Exception as e:
            self.log(logging.ERROR, f"An error occurred: {str(e)}")
            raise

    def parse_llm_response(
        self, llm_response: Union[Dict[str, str], str]
    ) -> Union[Dict[str, str], str]:
        try:
            parsed_llm_response = self.output_parser.parse(llm_response).dict()
            self.log(logging.INFO, f"Parsed LLM Response {parsed_llm_response}")
            required_keys = {"Intent"}
            missing_keys = required_keys - parsed_llm_response.keys()
            if missing_keys:
                raise KeyError(f"Missing keys in response: {', '.join(missing_keys)}")
        except KeyError:
            self.log(logging.ERROR, f"Missing keys in response: {llm_response}")
            raise
        except Exception:
            self.log(
                logging.WARNING,
                f"Coercion to Pydantic Object failed. Attempting to parse malformed JSON: {str(llm_response)}",
            )
            try:
                parsed_llm_response = parse_malformed_nlurouter_json(llm_response)
                self.log(
                    logging.WARNING,
                    f"Post Static JSON Parsing Attempt: {parsed_llm_response}",
                )
            except Exception as e:
                self.log(
                    logging.WARNING,
                    f"Programmatic Malformation Fix Failed: {llm_response}, {type(llm_response)}. Exception occured - {str(e)}",
                )
                parsed_llm_response = retry_on_error_with_llm_output_parser(
                    llm_response, self.output_parser
                )
                self.log(
                    logging.WARNING, f"Post LLM Fixing Attempt: {parsed_llm_response}"
                )

        return parsed_llm_response

    def process_query(self, query: str) -> Union[Dict[str, str], str]:
        if not query:
            raise ValueError("Query cannot be None or empty")
        nlu_routing_examples = self.vectorstore.similarity_search(query, k=3)
        nlu_routing_example_list = [dict(e.metadata) for e in nlu_routing_examples]
        self.log(logging.INFO, f"Query: {query} Examples: {nlu_routing_example_list}")
        llm_response = self.llm_chain.run(
            {"Query": query, "Examples": nlu_routing_example_list}
        )
        if not llm_response:
            self.log(
                logging.ERROR, "LLM-Response Error, NLURouterChain Stage Response is empty."
            )
            raise ValueError(
                "LLM-Response Error, NLURouterChain Stage Response cannot be empty or None"
            )
        parsed_llm_response = self.parse_llm_response(llm_response)
        #logger.info(f"DataType: {type(parsed_llm_response)}")
        return parsed_llm_response

    def get_current_time_in_jakarta(self) -> str:
        jakarta_timezone = pytz.timezone("Asia/Jakarta")
        current_datetime = datetime.now(jakarta_timezone)
        return current_datetime.strftime(
            "For Your Information. In Indonesia the date and time now is: Date: %B %d, %Y Time: %I:%M %p Day: %A"
        )
