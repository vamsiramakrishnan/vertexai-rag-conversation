import logging
from langchain import PromptTemplate
from helpers.logging_configurator import logger
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from temporaryconfig.product_info_config import PRODUCT_CONFIG_EN, PRODUCT_CONFIG_TH

class ProductQueryPrompt:
    PROMPT_PREFIX = ""
    PROMPT_QUERY = ""
    PROMPT_SUFFIX = ""

    def load_prompt(self, langcode: str):
        match langcode:
            case "en":
                self.PROMPT_PREFIX = PRODUCT_CONFIG_EN

                self.PROMPT_QUERY = """
                Query:
                {Query}

                """

                self.PROMPT_SUFFIX = """
                Response:
                """
            
            case "th":
                self.PROMPT_PREFIX = PRODUCT_CONFIG_TH

                self.PROMPT_QUERY = """
                แบบสอบถาม:
                {Query}

                """

                self.PROMPT_SUFFIX = """
                การตอบสนอง:
                """                            

    def create_product_query_prompt(self, isChatLLm: bool, langcode: str):
        self.load_prompt(langcode)

        try:
            if(isChatLLm):   
                messages = [
                SystemMessagePromptTemplate(
                    prompt=PromptTemplate(
                    input_variables=[],
                    template= self.PROMPT_PREFIX
                    )
                ),
                HumanMessagePromptTemplate(
                    prompt=PromptTemplate(
                    input_variables=["Query"],
                    template= self.PROMPT_QUERY + self.PROMPT_SUFFIX,
                    )
                )
                ]
                chat_prompt_template = ChatPromptTemplate.from_messages(messages)
                return chat_prompt_template
            else:         
                return PromptTemplate(
                    input_variables=["Query"],
                    template= self.PROMPT_PREFIX + self.PROMPT_QUERY + self.PROMPT_SUFFIX
                )                            
        except Exception as e:
            logger.error(
                "Error creating ProductQueryPrompt template:", exc_info=True
            )
            raise e