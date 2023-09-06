import logging
from typing import Tuple
from langchain import PromptTemplate
from langchain.prompts.few_shot import FewShotPromptTemplate
from output_validators.routing_output_validator import NLURouterResponse
from langchain.output_parsers import PydanticOutputParser
from config.config import configcontex
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from helpers.logging_configurator import request_origin

class NLURoutingPrompt:
    PREFIX_TEXT = """
You NEVER LIE or MAKE UP INFORMATION. YOU STRICTLY FOLLOW INSTRUCTIONS
You are Indira, a multi-lingual conversational AI expert for IM3 customer care. 

You recognize below IM3 specific terms among other non-exhaustive list of telecom <Topics> 
    IM3 - The brand 
    MyIM3 - The self care app & portal
    IM3 Lifestyle Services - News, Games, TV, Movies
    IM3 Benefits - Bonus, Cashback, Promos, Referrals, Kios
    Fiber Internet - HiFi Broadband
    Prepaid & Postpaid - Starter Pack, PRIME Plan, eSIM    
    Customer Own Account - Balances, Quotas, Bills, Payments, Loyalty Membership & Points

Understand <Query> & <Topic> of Interest and Classify Intent into one of 5 categories that best matches the <Query>
    "SmallTalk": General Queries that start with greetings, pleasantries, open-world questions. 
    "DynamicAPIFlow": Queries about the customer's own account profile or account balances / quotas / credits / pulses or bill information or payment information or loyalty points / loyalty membership / IMPoin. These questions often contain words like "My .." or "What is my.." or "When is my .." or or "Status of .." or "Due Date of.." or "History"
    "ProductFlow": Queries NOT RELATED TO HiFi but related to below -
        Buying or recommendation of mobile data internet / voice / SMS plans
        Freedom U | Freedom Internet mobile internet plans related information
    "StaticKnowledgebase": Other IM3 Brand Topics or service | HiFi Broadband FTTH | eSIM | General Telecom | Telecom adjacent | Other Product Queries 
    "FallBack": Queries that have <Topics> you don't understand; eg. Romantic, Sensitive, Controversial, Ambiguous topics with no right or factual answer, Questions about Competitive Companies & Brands

If Intent is "SmallTalk":
    Intent: SmallTalk

If Intent is "StaticKnowledgebase":
    Intent: StaticKnowledgebase

If Intent is "ProductFlow":
    Intent: ProductFlow   

If intent is "DynamicAPIFlow":
    Intent: DynamicAPIFlow

If intent is "FallBack":
    Intent: FallBack

Explanation: Think and explain why you chose that intent in 10 words or less


"""
    QUERY_TEXT = """
"Query": {Query}

"""
    SUFFIX_TEXT = """
"Examples": {Examples}

"FormatInstructions":The response should be formatted as a JSON instance {{"Intent": "...", "Explanation": "..."}}

JSON Response:
    """

    EXAMPLES_INDEX_NAME = "nlp_router_examples"
    EXAMPLES_FOLDER_NAME = "preprocessed_output"
    K_NEAREST = 3

    def __init__(self, bucket_name: str = "gs://ioh-kb-bucket"):
        self.logger = self._setup_logger()
        self.bucket_name = bucket_name
        self.router_output_parser = PydanticOutputParser(
            pydantic_object=NLURouterResponse
        )

    def _setup_logger(self):
        logger = logging.getLogger(__name__)
        return logger

    def log(self, level, message):
        self.logger.log(
            level, f"NLURoutingPrompt - Origin: {request_origin.get()} | {message}"
        )

    def create_router_output_parser(self):
        try:
            return
        except Exception as e:
            self.log(logging.ERROR, "Error creating nlu router output parser")
            raise e

    def create_nlu_routing_prompt(self):
        try:
            if(configcontex.FEATURE_CHAT_BISON == "True"):   
                messages = [
                    SystemMessagePromptTemplate(
                        prompt=PromptTemplate(
                            input_variables=["Query", "Examples"],
                            template=self.PREFIX_TEXT + self.QUERY_TEXT + self.SUFFIX_TEXT
                        )
                    ),                    
                    HumanMessagePromptTemplate(
                        prompt=PromptTemplate(
                            input_variables=["Query"],
                            template=self.QUERY_TEXT
                        )
                    )
                ]
                chat_prompt_template = ChatPromptTemplate.from_messages(messages)
                return (
                    chat_prompt_template,
                    self.router_output_parser,
                )                 
            else:
                return (
                    PromptTemplate(
                        input_variables=["Query", "Examples"],
                        template=self.PREFIX_TEXT + self.QUERY_TEXT + self.SUFFIX_TEXT
                    ),
                    self.router_output_parser,
                )                

        except Exception as e:
            self.log(
                logging.ERROR, "Error creating NLURoutingPrompt template:"
            )
            raise e