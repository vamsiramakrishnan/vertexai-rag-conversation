from typing import Dict, Union, Optional
from helpers.vertexai import LoggingVertexAI, LoggingVertexAIChat
from langchain.chains import LLMChain
from helpers.logging_configurator import logger, request_origin
from prompts.reframe_query_prompt import ReframeQueryPrompt
import logging
from config.config import configcontex
from langchain.llms.vertexai import _VertexAICommon
from models.llm_cr_be_models import *

class ReframeQueryChain:
    """Creates a chain for reframing query based on VertexAI, with logging."""

    def __init__(
        self,
        llm: Optional[_VertexAICommon] = None,
        reframe_query_prompt: Optional[ReframeQueryPrompt] = None,
        llm_chain: Optional[LLMChain] = None,
        vertexai_params: Optional[dict] = {
            "temperature": 0.3,
            "max_output_tokens": 256,
            "top_p": 0.8,
            "top_k": 40,
        },
        langcode: str = "en"
    ):
        """
        The constructor for the ReframeQueryChain class.
        """
        self.logger = self._setup_logger()
        self.CONFIG_MSG_HISTORY = int(configcontex.CONFIG_MSG_HISTORY)
        
        isChatLLm = False

        # Currently always use Text Bison since output is more consistent. Retaining code for future
        if(configcontex.FEATURE_CHAT_BISON == "True"):
            #self.llm = llm if llm else LoggingVertexAIChat(**vertexai_params)            
            #isChatLLm = True
            self.llm = llm if llm else LoggingVertexAI(**vertexai_params)
            isChatLLm = False
        else:
            self.llm = llm if llm else LoggingVertexAI(**vertexai_params)
            isChatLLm = False
            
        self.reframe_query_prompt = (
            reframe_query_prompt.create_reframe_query_prompt(isChatLLm, langcode)
            if reframe_query_prompt
            else ReframeQueryPrompt().create_reframe_query_prompt(isChatLLm, langcode)
        )
        self.initialize_llm_chain(llm_chain)

    def _setup_logger(self):
        logger = logging.getLogger(__name__)
        return logger

    def log(self, level, message):
        self.logger.log(
            level, f"ReframeQueryChain - Origin: {request_origin.get()} | {message}"
        )

    def initialize_llm_chain(self, llm_chain: Optional[LLMChain]):
        """
        Initializes the LLMChain with the given llm and prompt.
        """
        try:
            self.llm_chain = (
                llm_chain
                if llm_chain
                else LLMChain(llm=self.llm, prompt=self.reframe_query_prompt)
            )
        except Exception as e:
            self.log(logging.ERROR, f"An error occurred: {str(e)}")
            raise

    def process_query(self, query: str, history: List[Message]) -> Union[Dict[str, str], str]:
        """
        Processes the query, logging the necessary information and parsing the response.
        """
        if not query:
            raise ValueError("Query cannot be None or empty")

        chat_history = ""
        # Select last four messages
        for msg in history[len(history)-self.CONFIG_MSG_HISTORY:len(history)]:
            chat_history = chat_history + f"{msg.author.value}: {msg.content}" + "\n"

        llm_response = self.llm_chain({"ChatHistory": chat_history, "Query": query}, return_only_outputs=True)

        if not llm_response:
            self.log(
                logging.ERROR, "LLM-Response Error, ReframeQueryChain Stage Response is empty."
            )
            raise ValueError(
                "LLM-Response Error, ReframeQueryChain Stage Response cannot be empty or None"
            )
        return llm_response.get("text")
