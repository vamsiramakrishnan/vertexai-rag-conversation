from typing import Dict, Union, Optional
from helpers.vertexai import LoggingVertexAI, LoggingVertexAIChat
from langchain.chains import LLMChain
from helpers.logging_configurator import logger, request_origin
from prompts.small_talk_prompt import SmallTalkPrompt
import logging
from config.config import configcontex
from langchain.llms.vertexai import _VertexAICommon


class SmallTalkChain:
    """Creates a chain for small talk tasks based on VertexAI, with logging."""

    def __init__(
        self,
        llm: Optional[_VertexAICommon] = None,
        small_talk_prompt: Optional[SmallTalkPrompt] = None,
        llm_chain: Optional[LLMChain] = None,
        vertexai_params: Optional[dict] = {
            "temperature": 0.3,
            "max_output_tokens": 256,
            "top_p": 0.8,
            "top_k": 40,
        },
    ):
        """
        The constructor for the SmallTalkChain class.
        """
        self.logger = self._setup_logger()
        if(configcontex.FEATURE_CHAT_BISON == "True"):
            self.llm = llm if llm else LoggingVertexAIChat(**vertexai_params)
        else:
            self.llm = llm if llm else LoggingVertexAI(**vertexai_params)
        self.small_talk_prompt = (
            small_talk_prompt.create_small_talk_prompt()
            if small_talk_prompt
            else SmallTalkPrompt().create_small_talk_prompt()
        )
        self.initialize_llm_chain(llm_chain)

    def _setup_logger(self):
        logger = logging.getLogger(__name__)
        return logger

    def log(self, level, message):
        self.logger.log(
            level, f"SmallTalkChain - Origin: {request_origin.get()} | {message}"
        )

    def initialize_llm_chain(self, llm_chain: Optional[LLMChain]):
        """
        Initializes the LLMChain with the given llm and prompt.
        """
        try:
            self.llm_chain = (
                llm_chain
                if llm_chain
                else LLMChain(llm=self.llm, prompt=self.small_talk_prompt)
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
                logging.ERROR, "LLM-Response Error, SmallTalk Chain Stage Response is empty."
            )
            raise ValueError(
                "LLM-Response Error, SmallTalk Chain Stage Response cannot be empty or None"
            )
        return llm_response.get("text")
