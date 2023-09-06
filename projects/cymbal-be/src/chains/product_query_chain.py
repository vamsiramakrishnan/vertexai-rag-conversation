from typing import Dict, Union, Optional
from helpers.vertexai import LoggingVertexAI, LoggingVertexAIChat
from langchain.chains import LLMChain
from helpers.logging_configurator import logger, request_origin
from prompts.product_query_prompt import ProductQueryPrompt
import logging
from config.config import configcontex
from langchain.llms.vertexai import _VertexAICommon


class ProductQueryChain:
    """Creates a chain for product query based on VertexAI, with logging."""

    def __init__(
        self,
        llm: Optional[_VertexAICommon] = None,
        product_query_prompt: Optional[ProductQueryPrompt] = None,
        llm_chain: Optional[LLMChain] = None,
        vertexai_params: Optional[dict] = {
            "temperature": 0.3,
            "max_output_tokens": 450,
            "top_p": 0.8,
            "top_k": 40,
        },
        langcode: str = "en"
    ):
        """
        The constructor for the ProductQueryChain class.
        """
        self.logger = self._setup_logger()

        isChatLLm = False

        if(configcontex.FEATURE_CHAT_BISON == "True"):
            self.llm = llm if llm else LoggingVertexAIChat(**vertexai_params)
            isChatLLm = True
        else:
            self.llm = llm if llm else LoggingVertexAI(**vertexai_params)
            isChatLLm = False

        self.product_query_prompt = (
            product_query_prompt.create_product_query_prompt(isChatLLm, langcode)
            if product_query_prompt
            else ProductQueryPrompt().create_product_query_prompt(isChatLLm, langcode)
        )
        self.initialize_llm_chain(llm_chain)

    def _setup_logger(self):
        logger = logging.getLogger(__name__)
        return logger

    def log(self, level, message):
        self.logger.log(
            level, f"ProductQueryChain - Origin: {request_origin.get()} | {message}"
        )

    def initialize_llm_chain(self, llm_chain: Optional[LLMChain]):
        """
        Initializes the LLMChain with the given llm and prompt.
        """
        try:
            self.llm_chain = (
                llm_chain
                if llm_chain
                else LLMChain(llm=self.llm, prompt=self.product_query_prompt)
            )
        except Exception as e:
            self.log(logging.ERROR, f"An error occurred: {str(e)}")
            raise

    def process_query(self, query: str) -> Union[Dict[str, str], str]:
        """
        Processes the query, logging the necessary information and reformat for response.
        """
        if not query:
            raise ValueError("Query cannot be None or empty")

        llm_response = self.llm_chain({"Query": query}, return_only_outputs=True)

        if not llm_response:
            self.log(
                logging.ERROR, "LLM-Response Error, ProductQueryChain Stage Response is empty."
            )
            raise ValueError(
                "LLM-Response Error, ProductQueryChain Stage Response cannot be empty or None"
            )
        return llm_response.get("text")
