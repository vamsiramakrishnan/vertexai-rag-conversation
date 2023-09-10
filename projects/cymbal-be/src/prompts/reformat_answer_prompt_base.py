# import logging
# from langchain import PromptTemplate
# from helpers.logging_configurator import logger
# from langchain.prompts.chat import (
#     ChatPromptTemplate,
#     SystemMessagePromptTemplate,
#     HumanMessagePromptTemplate,
# )

# class ReformatAnswerPrompt:
#     PROMPT_PREFIX = ""
#     PROMPT_QUERY = ""
#     PROMPT_SUFFIX = ""

#     def load_prompt(self, langcode: str):
#         match langcode:
#             case "en":
#                 self.PROMPT_PREFIX = """
#                 SYSTEM: Always Answer in ENGLISH
#                 1/ Split <Context> into steps without changing the information in it, optimize for Mobile screen readability
#                 2/ Format as <Context> as Markdown
#                 3/ Break-down <Context> and organize as Paragraphs, Bullet Points, use Bold, Italics wherever necessary

#                 """

#                 self.PROMPT_QUERY = """
#                 Context:
#                 {RawResponse}

#                 """

#                 self.PROMPT_SUFFIX = """
#                 Markdown Response:
#                 """
            
#             case "id":
#                 self.PROMPT_PREFIX = """
#                 SYSTEM: Selalu Jawab dalam BAHASA INDONESIA
#                 1/ Pisahkan <Konteks> menjadi langkah-langkah tanpa mengubah informasi di dalamnya, optimalkan untuk keterbacaan layar Seluler
#                 2/ Format sebagai <Konteks> sebagai Markdown
#                 3/ Pecahkan <Konteks> dan atur sebagai Paragraf, Poin Peluru, gunakan Bold, Italics jika diperlukan
#                 """

#                 self.PROMPT_QUERY = """
#                 Context:
#                 {RawResponse}

#                 """

#                 self.PROMPT_SUFFIX = """
#                 Markdown Jawaban:
#                 """                            

#     def create_reformat_answer_prompt(self, isChatLLm: bool, langcode: str):
#         self.load_prompt(langcode)

#         try:
#             if(isChatLLm):   
#                 messages = [
#                 SystemMessagePromptTemplate(
#                     prompt=PromptTemplate(
#                     input_variables=[],
#                     template= self.PROMPT_PREFIX
#                     )
#                 ),
#                 HumanMessagePromptTemplate(
#                     prompt=PromptTemplate(
#                     input_variables=["RawResponse"],
#                     template= self.PROMPT_QUERY + self.PROMPT_SUFFIX,
#                     )
#                 )
#                 ]
#                 chat_prompt_template = ChatPromptTemplate.from_messages(messages)
#                 return chat_prompt_template
#             else:         
#                 return PromptTemplate(
#                     input_variables=["RawResponse"],
#                     template= self.PROMPT_PREFIX + self.PROMPT_QUERY + self.PROMPT_SUFFIX
#                 )                            
#         except Exception as e:
#             logger.error(
#                 "Error creating ReformatAnswerPrompt template:", exc_info=True
#             )
#             raise e