from typing import Optional
from helpers.logging_configurator import logger, request_origin
from helpers.vertexai import LoggingVertexAI
import logging


class ChatChain:
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
        self.logger = self._setup_logger()
        self.chat_chain = LoggingVertexAI(model_name=model_name, **vertexai_params)

    def _setup_logger(self):
        logger = logging.getLogger(__name__)
        return logger

    def log(self, level, message):
        self.logger.log(
            level, f"ChatChain - Origin: {request_origin.get()} | {message}"
        )

    def generate_response(self, prompt):
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
