import logging
from langchain import PromptTemplate
from helpers.logging_configurator import logger
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

class ReframeQueryPrompt:
    PROMPT_PREFIX = ""
    PROMPT_QUERY = ""
    PROMPT_SUFFIX = ""

    def load_prompt(self, langcode: str):
        match langcode:
            case "en":
                self.PROMPT_PREFIX = """
                Given the following chat history and a follow up phrase, convert the follow up phrase if it is incomplete into a standalone phrase while preserving all original information in follow up phrase.

                Do NOT ATTEMPT to provide an answer to the standalone phrase

                Chat History:
                {ChatHistory}

                """

                self.PROMPT_QUERY = """
                Follow Up Phrase: {Query}

                """

                self.PROMPT_SUFFIX = """
                Standalone Phrase:
                """
                
            case "id":
                self.PROMPT_PREFIX = """
                Mengingat riwayat obrolan berikut dan frasa tindak lanjut, ulangi frasa tindak lanjut menjadi frasa mandiri, pertahankan semua informasi dalam frasa tindak lanjut.

                JANGAN MENCOBA untuk memberikan jawaban atas frasa yang berdiri sendiri

                Riwayat Obrolan:               
                {ChatHistory}

                """

                self.PROMPT_QUERY = """
                Frase Tindak Lanjut: {Query}

                """

                self.PROMPT_SUFFIX = """
                Frase Mandiri:
                """ 

    def create_reframe_query_prompt(self, isChatLLm: bool, langcode: str):
        self.load_prompt(langcode)

        try:
            if(isChatLLm):   
                messages = [
                SystemMessagePromptTemplate(
                    prompt=PromptTemplate(
                    input_variables=["ChatHistory"],
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
                    input_variables=["ChatHistory", "Query"],
                    template= self.PROMPT_PREFIX + self.PROMPT_QUERY + self.PROMPT_SUFFIX
                )                                            
        except Exception as e:
            logger.error(
                "Error creating ReframeQueryPrompt template:", exc_info=True
            )
            raise e