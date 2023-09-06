import logging
from langchain import PromptTemplate
from helpers.logging_configurator import logger
from config.config import configcontex
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

class LangTranslationPrompt:
    PROMPT_PREFIX = """
    Given the phrase, translate into the target language indicated in ISO 639‑1 langCode

    Examples
    Phrase - Apa kabarmu
    LangCode - en
    Response - how are you

    """

    PROMPT_QUERY = """
    Phrase: {Query}
    LangCode - {LanguageCode}
    """

    PROMPT_SUFFIX = """
    Response:
    """

    def create_lang_translation_prompt(self):
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
                    input_variables=["Query", "LanguageCode"],
                    template= self.PROMPT_QUERY + self.PROMPT_SUFFIX,
                    )
                )
                ]
                chat_prompt_template = ChatPromptTemplate.from_messages(messages)
                return chat_prompt_template
            else:         
                return PromptTemplate(
                    input_variables=["Query", "LanguageCode"],
                    template= self.PROMPT_PREFIX + self.PROMPT_QUERY + self.PROMPT_SUFFIX
                )                                                                
        except Exception as e:
            logger.error(
                "Error creating LangTranslationPrompt template:", exc_info=True
            )
            raise e