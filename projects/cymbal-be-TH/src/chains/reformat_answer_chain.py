from typing import Dict, Union, Optional
from helpers.vertexai import LoggingVertexAI, LoggingVertexAIChat
from langchain.chains import LLMChain
from helpers.logging_configurator import logger, request_origin
from prompts.reformat_answer_prompt import ReformatAnswerPrompt
import logging
from config.config import configcontex
from langchain.llms.vertexai import _VertexAICommon


class ReformatAnswerChain:
    """Creates a chain for reformat answer based on VertexAI, with logging."""

    def __init__(
        self,
        llm: Optional[_VertexAICommon] = None,
        reformat_answer_prompt: Optional[ReformatAnswerPrompt] = None,
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
        The constructor for the ReformatAnswerChain class.
        """
        self.logger = self._setup_logger()

        isChatLLm = False

        if(configcontex.FEATURE_CHAT_BISON == "True"):
            self.llm = llm if llm else LoggingVertexAIChat(**vertexai_params)
            isChatLLm = True
        else:
            self.llm = llm if llm else LoggingVertexAI(**vertexai_params)
            isChatLLm = False

        self.reformat_answer_prompt = (
            reformat_answer_prompt.create_reformat_answer_prompt(isChatLLm, langcode)
            if reformat_answer_prompt
            else ReformatAnswerPrompt().create_reformat_answer_prompt(isChatLLm, langcode)
        )
        self.initialize_llm_chain(llm_chain)

    def _setup_logger(self):
        logger = logging.getLogger(__name__)
        return logger

    def log(self, level, message):
        self.logger.log(
            level, f"ReformatAnswerChain - Origin: {request_origin.get()} | {message}"
        )

    def initialize_llm_chain(self, llm_chain: Optional[LLMChain]):
        """
        Initializes the LLMChain with the given llm and prompt.
        """
        try:
            self.llm_chain = (
                llm_chain
                if llm_chain
                else LLMChain(llm=self.llm, prompt=self.reformat_answer_prompt)
            )
        except Exception as e:
            self.log(logging.ERROR, f"An error occurred: {str(e)}")
            raise

    def process_query(self, query: str, answer: str) -> Union[Dict[str, str], str]:
        """
        Processes the answer, logging the necessary information and reformat for response.
        """
        if not answer:
            raise ValueError("Answer cannot be None or empty")

        llm_response = self.llm_chain({"RawResponse": answer, "Query": query}, return_only_outputs=True)

        if not llm_response:
            self.log(
                logging.ERROR, "LLM-Response Error, ReformatAnswerChain Stage Response is empty."
            )
            raise ValueError(
                "LLM-Response Error, ReformatAnswerChain Stage Response cannot be empty or None"
            )
        return llm_response.get("text")
