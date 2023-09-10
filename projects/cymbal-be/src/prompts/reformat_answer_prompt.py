import logging
from langchain import PromptTemplate
from helpers.logging_configurator import logger
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

class ReformatAnswerPrompt:
    PROMPT_PREFIX = ""
    PROMPT_QUERY = ""
    PROMPT_SUFFIX = ""

    def load_prompt(self, langcode: str):
        match langcode:
            case "en":
                self.PROMPT_PREFIX = """
                SYSTEM: Always Answer in ENGLISH
                You are a call centre agent providing information to customers over the phone.
                Summarize the information provided in <Context> while preserving all the key information in it while ignore any formatting.
    
                """

                self.PROMPT_QUERY = """
                Context:
                {RawResponse}

                """

                self.PROMPT_SUFFIX = """
                Phone Response:
                """
            
            case "id":
                self.PROMPT_PREFIX = """
                SYSTEM: Selalu Jawab dalam BAHASA INDONESIA
                Anda adalah agen pusat panggilan yang memberikan informasi kepada pelanggan melalui telepon.
                Ringkaslah informasi yang disediakan di <Context> sambil mempertahankan semua informasi penting di dalamnya sambil mengabaikan format apa pun.

                """

                self.PROMPT_QUERY = """
                Context:
                {RawResponse}

                """

                self.PROMPT_SUFFIX = """
                Respon Telepon:
                """                            

    def create_reformat_answer_prompt(self, isChatLLm: bool, langcode: str):
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
                    input_variables=["RawResponse"],
                    template= self.PROMPT_QUERY + self.PROMPT_SUFFIX,
                    )
                )
                ]
                chat_prompt_template = ChatPromptTemplate.from_messages(messages)
                return chat_prompt_template
            else:         
                return PromptTemplate(
                    input_variables=["RawResponse"],
                    template= self.PROMPT_PREFIX + self.PROMPT_QUERY + self.PROMPT_SUFFIX
                )                            
        except Exception as e:
            logger.error(
                "Error creating ReformatAnswerPrompt template:", exc_info=True
            )
            raise e