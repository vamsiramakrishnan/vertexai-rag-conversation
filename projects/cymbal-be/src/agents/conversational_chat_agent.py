import logging
from typing import List, Tuple, Optional
from models.llm_cr_be_models import LlmChatResponse, Message, SafetyAttributes, Example, Parameters
from chains.chat_chain import ChatChain
from helpers.google_translate import TranslationService
#from helpers.logging_configurator import logger, request_origin
from helpers.logging_configurator import logger, request_origin, service_metrics
import re
from helpers.service_metrics import ServiceMetrics

class ConversationalChatAgent:
    TEMPERATURE = 0
    MAX_OUTPUT_TOKENS = 128
    TOP_P = 0.95
    TOP_K = 40
    DEFAULT_LANGUAGE = "en"

    def __init__(self, project_id: str = "marc-genai-01", region: str = "us-central1"):
        self.translation_service = TranslationService(project_id=project_id, region=region)
        self.logger = self._setup_logger()

    @staticmethod
    def _setup_logger() -> logging.Logger:
        return logging.getLogger(__name__)

    def log(self, level: int, message: str) -> None:
        self.logger.log(level, f"ChatAgent - Origin: {request_origin} | {message}")

    @staticmethod
    def _extract_message_history(messages: List[Message]) -> str:
        if not messages:
            return ""
        else:
            message_history = "\n\n".join(f"{message.author.value}: {message.content}" for message in messages)
            message_history = "HISTORY:\n" + message_history
            return message_history

    @staticmethod
    def _extract_examples(examples: List[Example]) -> str:
        if not examples:
            return ""
        else:
            example_list = "\n\n".join(f"{example.input.content}: {example.output.content}" for example in examples)
            example_list = "Use EXAMPLES: below to answer question\n EXAMPLES:\n" + example_list
            return example_list

    @staticmethod
    def _extract_customer_question(text):
        match = re.search(r'(.*)(CUSTOMER_QUESTION:.*$)', text, re.DOTALL)
        if match:
            text_before = match.group(1)
            text_after = match.group(2)
        else:
            text_before = text_after = None
        return text_before, text_after

    def _translate_query_if_required(self, query: str, default_language: str = DEFAULT_LANGUAGE) -> Tuple[str, str]:
        detected_language = self.translation_service.detect_language_nmt(query)
        if detected_language != default_language:
            translated_query = self.translation_service.translate_text_nmt(query, default_language)
        else:
            translated_query = query
        return detected_language, translated_query

    def _translate_response_if_required(self, response: str, target_language: str) -> str:
        """Translates the response if the language of response and incoming query do not match"""        
        # detected_language = self.translation_service.detect_language_nmt(response)
        # if detected_language != target_language:
        #     translated_response = self.translation_service.translate_text_nmt(response, target_language)
        # else:
        #     translated_response = response
        
        # Translate only for non English targets
        # if target_language != 'en':
        #     translated_response = self.translation_service.translate_text_nmt(response, target_language)
        # else:
        #     translated_response = response
        
        # FORCE translate response. Even for high confidence EN scenarios, FORCE translation enabled since some balance desc in Indonesian Bahasa
        # INEFFICIENT CODE. FIRES FOR ALL DYNAMIC FLOWS for EN, Indonesia Bahasa balance desc only for ACCT INFO dynamic flow
        if target_language != 'en':
            translated_response = self.translation_service.translate_text_nmt(response, target_language)
        else:
            translated_response = self.translation_service.translate_text_nmt_from_src(response, "id" ,target_language)            
                    
        return translated_response

    def _prepare_model_prompt(self, context: str, examples: str, question: str, message_history: str) -> str:
        return f"""
Context:
{context}
{question}
{message_history}
{examples}
ANSWER:
"""

    def _generate_chat_response(self, model_prompt: str, parameters: Optional[Parameters]) -> str:
        vertexai_params = {
            "temperature": parameters.temperature if parameters and parameters.temperature else self.TEMPERATURE,
            "max_output_tokens": parameters.maxOutputTokens if parameters and parameters.maxOutputTokens else self.MAX_OUTPUT_TOKENS,
            "top_p": parameters.topP if parameters and parameters.topP else self.TOP_P,
            "top_k": parameters.topK if parameters and parameters.topK else self.TOP_K,
        }

        chat_chain = ChatChain(model_name="text-bison", vertexai_params=vertexai_params)
        chat_agent_answer = chat_chain.generate_response(model_prompt)

        return chat_agent_answer

    def _extract_request_parameters(self, body) -> Tuple[str, str, List[Message], Optional[Parameters]]:
        chat_agent_request = body.llmChatRequest

        context = chat_agent_request.context or ""
        examples = chat_agent_request.examples or []
        messages = chat_agent_request.messages or []
        parameters = chat_agent_request.parameters

        return context, examples, messages, parameters

    def invoke(self, body) -> LlmChatResponse:
        context, examples, messages, parameters = self._extract_request_parameters(body)

        service_metrics.get().setFlowType("ChatQA")

        context, customer_question = self._extract_customer_question(context)
        self.log(logging.INFO, f"Extracted CUSTOMER_QUESTION: {customer_question}")

        customer_question_language, customer_question = self._translate_query_if_required(customer_question)

        message_history = self._extract_message_history(messages)
        examples_prompt = self._extract_examples(examples)

        model_prompt = self._prepare_model_prompt(context, examples_prompt, customer_question, message_history)

        self.log(logging.INFO, f"Generated Model Prompt: {model_prompt}")

        chat_response = self._generate_chat_response(model_prompt, parameters)
        self.log(logging.INFO, f"PreTranslation Chat Response: {chat_response}")

        chat_agent_answer = self._translate_response_if_required(chat_response, customer_question_language)
        self.log(logging.INFO, f"Final Chat Response: {chat_agent_answer}")

        response_safety_attributes = SafetyAttributes(scores=[], blocked=False, categories=[])
        llm_chat_response = LlmChatResponse(answer=chat_agent_answer, safetyAttributes=response_safety_attributes)

        self.log(logging.INFO, f"ServiceMetrics: {service_metrics.get().getServiceMetricsSummary()}")

        return llm_chat_response