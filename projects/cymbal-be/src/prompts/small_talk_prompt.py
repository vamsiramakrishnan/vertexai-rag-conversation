import logging
from langchain import PromptTemplate
from helpers.logging_configurator import logger
from config.config import configcontex
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

class SmallTalkPrompt:
    INPUT_VARIABLES = ["query"]
    PREFIX_TEXT = """You are Indira, you are a Telecom expert in IM3 
    Your job is to respond to your Customer <query> with a 50-100 word answer that is factual, and in first person, polite, chit-chatty
    Never make up facts. You never lie. You are extremely Truthful.
    
    """ 
    QUERY_TEXT = """
    Query: {query}

    """
    SUFFIX_TEXT = """
    Small Talk Answer:
    """

    def create_small_talk_prompt(self):
        try:
            if(configcontex.FEATURE_CHAT_BISON == "True"):   
                messages = [
                    SystemMessagePromptTemplate(
                        prompt=PromptTemplate(
                            input_variables=self.INPUT_VARIABLES, template=self.PREFIX_TEXT + self.QUERY_TEXT + self.SUFFIX_TEXT
                        )                
                    ),                    
                    HumanMessagePromptTemplate(
                        prompt=PromptTemplate(
                            input_variables=["query"],
                            template=self.QUERY_TEXT,
                        )
                    )
                ]
                chat_prompt_template = ChatPromptTemplate.from_messages(messages)
                return chat_prompt_template
            else:         
                return PromptTemplate(
                    input_variables=self.INPUT_VARIABLES, template=self.PREFIX_TEXT + self.QUERY_TEXT + self.SUFFIX_TEXT
                )            
        except Exception as e:
            logger.error(
                "Error creating SmallTalkPrompt template:", exc_info=True
            )
            raise e