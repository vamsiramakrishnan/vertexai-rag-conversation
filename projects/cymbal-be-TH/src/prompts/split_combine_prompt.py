import logging
from langchain import PromptTemplate
from langchain.vectorstores import FAISS
from helpers.vertexai import LoggingVertexAIEmbeddings
from helpers.logging_configurator import logger
from langchain.output_parsers import CommaSeparatedListOutputParser


class SplitPrompt:
    INPUT_VARIABLES = ["query"]
    TEMPLATE_TEXT = """You are an expert in Splitting Combined Questions into separate ones and creating a Python List of Strings
    Example: 
    Query: What is ESIM and How do I buy it ?
    Answer: "What is ESIM ?", "How do I Buy an ESIM ?"]

    Query: Tell me how do I pay my bill and bill amount due
    Answer: ["How do I pay my Bill ?","What is my Bill amount due ?"]

    Query: Compare Service A and Service B
    Answer: ["What is Service A", "What is Service B"]

    Query: {query}
    Answer:
    Format_Instructions: {format_instructions}
    """

    def create_split_prompt(self):
        try:
            output_parser = CommaSeparatedListOutputParser()
            format_instructions = output_parser.get_format_instructions()
            return PromptTemplate(
                input_variables=self.INPUT_VARIABLES,
                template=self.TEMPLATE_TEXT,
                partial_variables={"format_instructions": format_instructions},
            )
        except Exception as e:
            logger.error("Error creating Split prompt template:", exc_info=True)
            raise e


class CombinePrompt:
    INPUT_VARIABLES = ["context"]
    TEMPLATE_TEXT = """You are an expert in Combining answers meaningfully in bullet points & sections provided to you
    Example: 
    Context: <Answer1> <Answer 2>
    Combined Answer:  Rephrased Grammatically Correct Combined Answer = <Answer1> + <Answer2>

    Context: {context}
    Combined Answer:
    """

    def create_combine_prompt(self):
        try:
            return PromptTemplate(
                input_variables=self.INPUT_VARIABLES, template=self.TEMPLATE_TEXT
            )
        except Exception as e:
            logger.error("Error creating Combine prompt template:", exc_info=True)
            raise e
