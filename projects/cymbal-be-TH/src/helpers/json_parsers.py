import re
import json
from helpers.vertexai import LoggingVertexAI
from langchain.output_parsers import RetryWithErrorOutputParser
from typing import Dict
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from helpers.logging_configurator import logger,  request_origin


def retry_on_error_with_llm_output_parser(malformed_json, parser):
    llm = LoggingVertexAI(temperature=0)
    prompt = PromptTemplate(
        template="STRICTLY GENERATE A COMPLIANT JSON OUTPUT FOR  INPUT \n INPUT:{query} \n JSON OUTPUT:\n\n {format_instructions}",
        input_variables=["query"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    llm_chain = LLMChain(llm=llm, prompt=prompt)
    try:
        parsed_output = parser.parse(llm_chain(malformed_json).get("text")).dict()

    except Exception:
        parsed_output = {"Intent": "Unknown"}

    return parsed_output


def parse_malformed_nlurouter_json(input_string: str) -> Dict[str, str]:
    """Parse the input string to extract intent and response."""

    intents = {
        "StaticKnowledgebase": "StaticKnowledgebase",
        "DynamicAPIFlow": "DynamicAPIFlow",
        "ProductFlow": "ProductFlow",
        "SmallTalk": "SmallTalk",
        "FallBack": "Fallback"
    }
    response_dict = {}
    for intent_key, intent_value in intents.items():
        if intent_key.casefold() in input_string.casefold():
            response_dict["Intent"] = intent_value
            break               
    return response_dict


def parse_malformed_dynamicapi_json(input_string: str) -> Dict[str, str]:
    """Parse the input string to extract intent and response."""

    flows = ["accountInfo","billPaymentInfo","imPoinInfo"]
    response_dict = {}
    for flow in flows:
        if flow.casefold() in input_string.casefold():
            response_dict["answer"] = intent_value
            break               
    return response_dict