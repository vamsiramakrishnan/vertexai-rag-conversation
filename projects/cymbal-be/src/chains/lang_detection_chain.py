from typing import Dict, Union, Optional
from helpers.vertexai import LoggingVertexAI, LoggingVertexAIChat
from langchain.chains import LLMChain
from helpers.logging_configurator import logger, request_origin
from prompts.lang_detection_prompt import LangDetectionPrompt
import logging
from config.config import configcontex
from langchain.llms.vertexai import _VertexAICommon


class LangDetectionChain:
    """Creates a chain for language detection based on VertexAI, with logging."""

    def __init__(
        self,
        llm: Optional[_VertexAICommon] = None,
        lang_detection_prompt: Optional[LangDetectionPrompt] = None,
        llm_chain: Optional[LLMChain] = None,
        vertexai_params: Optional[dict] = {
            "temperature": 0.3,
            "max_output_tokens": 256,
            "top_p": 0.8,
            "top_k": 40,
        },
    ):
        """
        The constructor for the LangDetectionChain class.
        """
        self.logger = self._setup_logger()
        if(configcontex.FEATURE_CHAT_BISON == "True"):
            self.llm = llm if llm else LoggingVertexAIChat(**vertexai_params)
        else:
            self.llm = llm if llm else LoggingVertexAI(**vertexai_params)
        self.lang_detection_prompt = (
            lang_detection_prompt.create_lang_detection_prompt()
            if lang_detection_prompt
            else LangDetectionPrompt().create_lang_detection_prompt()
        )
        self.initialize_llm_chain(llm_chain)

    def _setup_logger(self):
        logger = logging.getLogger(__name__)
        return logger

    def log(self, level, message):
        self.logger.log(
            level, f"LangDetectionChain - Origin: {request_origin.get()} | {message}"
        )

    def initialize_llm_chain(self, llm_chain: Optional[LLMChain]):
        """
        Initializes the LLMChain with the given llm and prompt.
        """
        try:
            self.llm_chain = (
                llm_chain
                if llm_chain
                else LLMChain(llm=self.llm, prompt=self.lang_detection_prompt)
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
                logging.ERROR, "LLM-Response Error, LangDetectionChain Stage Response is empty."
            )
            raise ValueError(
                "LLM-Response Error, LangDetectionChain Stage Response cannot be empty or None"
            )
        return llm_response.get("text")
