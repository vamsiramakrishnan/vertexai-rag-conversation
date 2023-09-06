import logging
from langchain.prompts.few_shot import FewShotPromptTemplate
from langchain.vectorstores import FAISS
from helpers.vertexai import LoggingVertexAIEmbeddings
from langchain import PromptTemplate
from helpers.logging_configurator import logger, request_origin
from output_validators.dynamic_api_output_validator import DynamicAPIResponse
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from config.config import configcontex
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)


class DynamicAPIPrompt:
    INPUT_VARIABLES = ["Query", "Examples"]
    EXAMPLES_INDEX_NAME = "nlp_router_examples_dynamic"
    EXAMPLES_FOLDER_NAME = "preprocessed_output"
    K_NEAREST = 4

    PREFIX_TEXT = """
    Query: account-related balance / quota / free units / free credits, Response: "accountInfo"
    Query: bill-payment related, Response: "billPaymentInfo"
    Query: IMPoin loyalty program related, Response: "imPoinInfo"
    Respond in JSON

    """
    QUERY_TEXT = """
    "Query": {Query}

    """
    SUFFIX_TEXT = """
    "Examples": {Examples}
    "FormatInstructions":{format_instructions}
    "JSON":

    """

    def __init__(self, bucket_name: str = "gs://ioh-kb-bucket"):
        self.logger = self._setup_logger()
        self.bucket_name = bucket_name
        self.dynamic_api_output_parser = PydanticOutputParser(
            pydantic_object=DynamicAPIResponse
        )

    def _setup_logger(self):
        logger = logging.getLogger(__name__)
        return logger

    def log(self, level, message):
        self.logger.log(
            level, f"DynamicAPIPrompt - Origin: {request_origin.get()} | {message}"
        )

    def create_dynamic_api_prompt(self):
        try:
            if(configcontex.FEATURE_CHAT_BISON == "True"):   
                messages = [
                    SystemMessagePromptTemplate(
                        prompt=PromptTemplate(
                            input_variables=self.INPUT_VARIABLES,
                            template=self.PREFIX_TEXT + self.QUERY_TEXT + self.SUFFIX_TEXT,
                            partial_variables={
                                "format_instructions": self.dynamic_api_output_parser.get_format_instructions()
                            },
                        )                                      
                    ),                    
                    HumanMessagePromptTemplate(
                        prompt=PromptTemplate(
                            input_variables=["Query"],
                            template=self.QUERY_TEXT,
                        )
                    )
                ]
                chat_prompt_template = ChatPromptTemplate.from_messages(messages)
                return (
                    chat_prompt_template,
                    self.dynamic_api_output_parser,
                )
            else:         
                return (
                    PromptTemplate(
                        input_variables=self.INPUT_VARIABLES,
                        template=self.PREFIX_TEXT + self.QUERY_TEXT + self.SUFFIX_TEXT,
                        partial_variables={
                            "format_instructions": self.dynamic_api_output_parser.get_format_instructions()
                        },
                    ),
                    self.dynamic_api_output_parser,
                )                        
        except Exception as e:
            self.log(
                logging.ERROR, "Error creating DynamicAPIPrompt template:"
            )
            raise e