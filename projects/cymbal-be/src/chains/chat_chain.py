from typing import Optional
from helpers.logging_configurator import logger, request_origin
from helpers.vertexai import LoggingVertexAI
import logging


class ChatChain:
    """
    The ChatChain class is responsible for generating responses using the LoggingVertexAI model.
    It uses the logger to log information and errors.
    """
    def __init__(
        self,
        model_name: str,
        vertexai_params: Optional[dict] = {
            "temperature": 0.3,
            "max_output_tokens": 256,
            "top_p": 0.8,
            "top_k": 40,
        },
    ):
        """
        Initializes the ChatChain with a logger and a LoggingVertexAI model.
        """
        self.logger = self._setup_logger()
        self.chat_chain = LoggingVertexAI(model_name=model_name, **vertexai_params)

    def _setup_logger(self):
        """
        Sets up the logger for the ChatChain class.
        """
        logger = logging.getLogger(__name__)
        return logger

    def log(self, level, message):
        """
        Logs a message at a specified level.
        """
        self.logger.log(
            level, f"ChatChain - Origin: {request_origin.get()} | {message}"
        )

    def generate_response(self, prompt):
        """
        Generates a response using the LoggingVertexAI model.
        If the prompt is None, it logs an error and raises a ValueError.
        If the response is None, it logs an error and raises a ValueError.
        """
        if prompt is None:
            self.log(logging.ERROR, "Model Prompt cannot be None")
            raise ValueError("Model prompt cannot be None")

        try:
            response = self.chat_chain(prompt)
        except Exception as e:
            self.log(
                logging.ERROR,
                f"Exception occurred in processing Chat Agent Answer: {str(e)}",
            )
            raise

        if response is None:
            self.log(logging.ERROR, "Chat agent answer cannot be None")
            raise ValueError("Chat agent answer cannot be None")

        return response
