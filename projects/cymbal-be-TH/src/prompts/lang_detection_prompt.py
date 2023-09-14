import logging
from langchain import PromptTemplate
from helpers.logging_configurator import logger
from config.config import configcontex
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

class LangDetectionPrompt:
    PROMPT_PREFIX = """
    For input phrase, detect language in ISO 639‑1 Code, respond with JSON {{"lang":"ISO 639‑1 Code"}}

    Example
    Phrase - Apa Kabar
    Response - {{"lang":"th"}}

    """

    PROMPT_QUERY = """
    Phrase: {Query}
    """

    PROMPT_SUFFIX = """
    Response:
    """

    def create_lang_detection_prompt(self):
        try:
            if(configcontex.FEATURE_CHAT_BISON == "True"):   
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
                "Error creating LangDetectionPrompt template:", exc_info=True
            )
            raise e