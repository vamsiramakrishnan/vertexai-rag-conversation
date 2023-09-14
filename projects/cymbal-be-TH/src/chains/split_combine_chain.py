from typing import Dict, Union, Optional
from helpers.vertexai import LoggingVertexAI
from prompts.split_combine_prompt import SplitPrompt, CombinePrompt
from langchain.chains import LLMChain
from helpers.logging_configurator import logger, request_origin
from langchain.output_parsers import CommaSeparatedListOutputParser
import logging


class SplitChain:
    """Creates a chain for splitting tasks based on VertexAI, with logging."""

    def __init__(
        self,
        llm: Optional[LoggingVertexAI] = None,
        split_prompt: Optional[SplitPrompt] = None,
        llm_chain: Optional[LLMChain] = None,
        vertexai_params: Optional[dict] = {
            "temperature": 0.3,
            "max_output_tokens": 128,
            "top_p": 0.8,
            "top_k": 40,
        },
        output_parser: Optional[CommaSeparatedListOutputParser] = None,
    ):
        """
        The constructor for the SplitChain class.
        """
        self.logger = self._setup_logger()
        self.llm = llm if llm else LoggingVertexAI(**vertexai_params)
        self.split_prompt = (
            split_prompt.create_split_prompt()
            if split_prompt
            else SplitPrompt().create_split_prompt()
        )
        self.output_parser = (
            output_parser if output_parser else CommaSeparatedListOutputParser()
        )
        self.initialize_llm_chain(llm_chain)

    def _setup_logger(self):
        logger = logging.getLogger(__name__)
        return logger

    def log(self, level, message):
        self.logger.log(
            level, f"SplitChain - Origin: {request_origin.get()} | {message}"
        )

    def initialize_llm_chain(self, llm_chain: Optional[LLMChain]):
        """
        Initializes the LLMChain with the given llm and prompt.
        """
        try:
            self.llm_chain = (
                llm_chain
                if llm_chain
                else LLMChain(llm=self.llm, prompt=self.split_prompt)
            )
        except Exception as e:
            self.log(logging.ERROR, f"An error occurred: {str(e)}")
            raise

    def process_query(self, query: str) -> Union[Dict[str, str], str]:
        """
        Processes the query, logging the necessary information and parsing the response.
        """
        if not query:
            raise ValueError("Query cannot be None or empty")

        llm_response = self.llm_chain({"query": query}, return_only_outputs=True)

        if not llm_response:
            self.log(
                logging.ERROR, "Text-Bison-001, Combine Chain Stage Response is empty."
            )
            raise ValueError(
                "Text-Bison-001, Combine Chain Stage Response cannot be empty or None"
            )
        return llm_response


class CombineChain:
    """Creates a chain for combining tasks based on VertexAI, with logging."""

    def __init__(
        self,
        llm: Optional[LoggingVertexAI] = None,
        combine_prompt: Optional[CombinePrompt] = None,
        llm_chain: Optional[LLMChain] = None,
        vertexai_params: Optional[dict] = {
            "temperature": 0.3,
            "max_output_tokens": 512,
            "top_p": 0.8,
            "top_k": 40,
        },
    ):
        """
        The constructor for the CombineChain class.
        """
        self.llm = llm if llm else LoggingVertexAI(**vertexai_params)
        self.combine_prompt = (
            combine_prompt.create_combine_prompt()
            if combine_prompt
            else CombinePrompt().create_combine_prompt()
        )
        self.initialize_llm_chain(llm_chain)

    def _setup_logger(self):
        logger = logging.getLogger(__name__)
        return logger

    def log(self, level, message):
        self.logger.log(
            level, f"SplitChain - Origin: {request_origin.get()} | {message}"
        )

    def initialize_llm_chain(self, llm_chain: Optional[LLMChain]):
        """
        Initializes the LLMChain with the given llm and prompt.
        """
        try:
            self.llm_chain = (
                llm_chain
                if llm_chain
                else LLMChain(llm=self.llm, prompt=self.combine_prompt)
            )
        except Exception as e:
            self.log(logging.ERROR, f"An error occurred: {str(e)}")
            raise

    def process_query(self, query: str) -> Union[Dict[str, str], str]:
        """
        Processes the query, logging the necessary information and parsing the response.
        """
        if not query:
            raise ValueError("Query cannot be None or empty")

        llm_response = self.llm_chain({"query": query}, return_only_outputs=True)

        if not llm_response:
            self.log(
                logging.ERROR, "Text-Bison-001, Combine Chain Stage Response is empty."
            )
            raise ValueError(
                "Text-Bison-001, Combine Chain Stage Response cannot be empty or None"
            )
        return llm_response
