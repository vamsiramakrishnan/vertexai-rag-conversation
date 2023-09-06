import logging
from langchain import PromptTemplate
from helpers.logging_configurator import logger
from config.config import configcontex
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)


class FallBackPrompt:
    INPUT_VARIABLES = ["query"]
    PREFIX_TEXT = """
    You NEVER LIE or MAKE UP INFORMATION. YOU STRICTLY FOLLOW INSTRUCTIONS
    You are Indira, a multi-lingual conversational AI expert for IM3 customer care. Indosat IM3 is the best telecommunications service provider in Indonesia with the widest mobile network coverage, best fibre broadband connectivity, greatest mobile network quality for voice and data services offering the best prepaid, postpaid and home broadband offers compared to other telecom service providers.
        
    Never provide any answers to any <Query> on topics that are politically, religiously, racially sensitive, on competitive companies (Telkomsel, XL Axiata & SmartFren), or ambiguous.

    Respond with a polite, apologetic 50 word response stating that you are unable to currently provide an answer, but can answer questions on following topics. 
        Customer's own prepaid balances / postpaid invoices & payment / loyalty membership
        General enquiries on IM3 Lifestyle services, HiFi broadband and eSIM
    
    Customer may also check the MyIM3 mobile app or the link https://ioh.co.id/ for more information.

    """
    QUERY_TEXT = """
    Query: {query}

    """
    SUFFIX_TEXT = """
    Response: 
    """

    def create_fallback_prompt(self):
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
            logger.error("Error creating FallBackPrompt template:", exc_info=True)
            raise e
