import logging
from typing import Dict, Union, Optional
from chains.router_chain import NLURouterChain
from chains.static_knowledgebase_chain import StaticKnowledgebaseChain
from chains.small_talk_chain import SmallTalkChain
from chains.dynamic_api_flow_chain import DynamicAPIFlowChain
from chains.fallback_chain import FallBackChain
from chains.split_combine_chain import SplitChain, CombineChain
from chains.lang_detection_chain import LangDetectionChain
from chains.lang_translation_chain import LangTranslationChain
from chains.reframe_query_chain import ReframeQueryChain
from chains.reformat_answer_chain import ReformatAnswerChain
from chains.product_query_chain import ProductQueryChain
from google.cloud import translate_v2 as translate
from google.cloud import translate as translate_nmt
#from helpers.logging_configurator import logger, request_origin
from helpers.logging_configurator import logger, request_origin, service_metrics
from helpers.google_translate import TranslationService
from helpers.service_metrics import ServiceMetrics
from config.config import configcontex
from models.llm_cr_be_models import *
from helpers.vertexai import LoggingVertexAIEmbeddings

class RouterAgent:
    def __init__(
        self,
        bucket_name: str = "gs://cymbal-kb-bucket",
        project_id: str = "marc-genai-01",
        region: str = "us-central1",
        index_name: str = "cymbal_kb_index_EN",
        index_name_id: str = "cymbal_kb_index_ID",
        log_level: int = logging.INFO,
    ):
        self.bucket_name = bucket_name
        self.project_id = project_id
        self.region = region
        self.logger = self._setup_logger()

        self.nlu_router_chain = NLURouterChain(bucket_name=self.bucket_name)
        self.translation_service = TranslationService(
            project_id=project_id, region=region
        )
        self.staticknowledgebase_chain = StaticKnowledgebaseChain(
            bucket_name=self.bucket_name, index_name=index_name, embeddings_non_english=False
        )
        self.staticknowledgebase_chain_id = StaticKnowledgebaseChain(
            bucket_name=self.bucket_name, index_name=index_name_id, embeddings_non_english=True
        )        
        self.split_chain = SplitChain()
        self.combine_chain = CombineChain()
        self.small_talk_chain = SmallTalkChain()
        self.dynamic_api_flow_chain = DynamicAPIFlowChain(bucket_name=self.bucket_name)
        self.fall_back_chain = FallBackChain()
        
        self.lang_detection_chain = LangDetectionChain()
        self.lang_translation_chain = LangTranslationChain()

        self.reframe_query_chain = ReframeQueryChain()
        self.reframe_query_chain_id = ReframeQueryChain(langcode="id")

        self.reformat_answer_chain = ReformatAnswerChain()
        self.reformat_answer_chain_id = ReformatAnswerChain(langcode="id")

        self.product_query_chain = ProductQueryChain()
        self.product_query_chain_id = ProductQueryChain(langcode="id")        

    @property
    def default_language(self):
        return "en"

    @property
    def default_bucket_name(self):
        return "gs://cymbal-kb-bucket"

    @property
    def default_project_id(self):
        return "marc-genai-01"

    @property
    def default_region(self):
        return "us-central1"

    @property
    def default_index_names(self):
        return {"en": "cymbal_kb_index_EN", "id": "cymbal_kb_index_ID"}

    @property
    def default_response(self):
        return {
            "responseType": "Fallback",
            "answer": "Could not understand what you said. Could you rephrase the question?",
        }

    def _setup_logger(self):
        logger = logging.getLogger(__name__)
        return logger

    def log(self, level, message):
        self.logger.log(
            level, f"RouterAgent - Origin: {request_origin.get()} | {message}"
        )

    def reframe_query(self, query: str, detected_language: str, history_messages: List[Message]) -> str:
        try:
            if(history_messages and configcontex.FEATURE_REFRAME_QUERY == 'True'):
                if (len(history_messages) >= 1):
                    if(detected_language == 'id'):
                        return self.reframe_query_chain_id.process_query(query, history_messages)
                    else:
                        return self.reframe_query_chain.process_query(query, history_messages)
                else:
                    return query                        
            else:
                return query

        except Exception as e:
            self.log(
                logging.ERROR, f"Error occurred in reframe_query: %s {str(e)}"
            )
            return ""

    def reformat_answer(self, answer: str, detected_language: str) -> str:
        try:
            if(answer and configcontex.FEATURE_REFORMAT_ANSWER == 'True'):
                if(detected_language == 'id'):
                    return self.reformat_answer_chain_id.process_query(answer)
                else:
                    return self.reformat_answer_chain.process_query(answer)                                       
            else:
                return answer

        except Exception as e:
            self.log(
                logging.ERROR, f"Error occurred in reformat_answer: %s {str(e)}"
            )
            return ""            

    def get_nlu_router_response(self, query: str) -> Union[Dict[str, str], str]:
        try:
            return self.nlu_router_chain.process_query(query=query)
        except Exception as e:
            self.log(
                logging.ERROR, f"Error occurred in get_nlu_router_response: %s {str(e)}"
            )
            return ""

    def process_intent(
        self,
        intent_type: str,
        query: str, 
        original_query: str, 
        detected_language: str
    ) -> Dict[str, Optional[str]]:
        
        intent_type = intent_type.casefold()
        
        if(intent_type == 'staticknowledgebase' and configcontex.FEATURE_KDB_ID == 'True' and detected_language == 'id'):
            query = original_query
            chain_map = {
                "staticknowledgebase": (
                    self.staticknowledgebase_chain_id,
                    "StaticKnowledgebaseQnA",
                )
            }
            self.log(logging.INFO, f"Using chain staticknowledgebase_chain_id for intent_type {intent_type}")
        if(intent_type == 'productflow' and detected_language == 'id'):
            query = original_query
            chain_map = {
                "productflow": (
                    self.product_query_chain_id,
                    "ProductFlow",
                )
            }
            self.log(logging.INFO, f"Using chain product_query_chain_id for intent_type {intent_type}")            
        else:
            chain_map = {
                "smalltalk": (self.small_talk_chain, "SmallTalk"),
                "dynamicapiflow": (self.dynamic_api_flow_chain, "DynamicAPIFlow"),
                "staticknowledgebase": (
                    self.staticknowledgebase_chain,
                    "StaticKnowledgebaseQnA",
                ),
                "fallback": (self.fall_back_chain, "Fallback"),
                "productflow": (
                    self.product_query_chain,
                    "ProductFlow",
                )                
            }
            self.log(logging.INFO, f"Using chain DEFAULT for intent_type {intent_type}")    
        
        if intent_type in chain_map:
            chain, response_type = chain_map[intent_type]
            response = chain.process_query(query)
            self.log(logging.INFO, f"responseType {response_type} answer: {response}")

            if(response_type in ["StaticKnowledgebaseQnA", "ProductFlow"] and configcontex.FEATURE_REFORMAT_ANSWER == 'True'):
                return {"responseType": response_type, "answer": self.reformat_answer(response, detected_language)}
            else:                                                        
                return {"responseType": response_type, "answer": response}
        else:
            self.log(logging.ERROR, f"Unrecognized intent type: {intent_type}")
            return self.default_response

    def get_qa_response(
        self, query: str, nlu_router_response: Union[Dict[str, str], str], original_query: str, detected_language: str
    ) -> Dict[str, Union[str, Dict[str, str]]]:
        default_response = self.default_response
        if isinstance(nlu_router_response, dict):
            intent = nlu_router_response.get("Intent")
            service_metrics.get().setFlowType(intent)            
            if intent.casefold() in [
                "staticknowledgebase",
                "smalltalk",
                "dynamicapiflow",
                "fallback",
                "productflow"
            ]:
                return self.process_intent(intent, query, original_query, detected_language)

        return default_response

    def translate_query_if_needed(self, query: str, detected_language: str) -> str:
        """Translates the query if it is not in English or Bahasa"""
        if detected_language not in ["en"]:
            self.log(logging.INFO, f"Language detected {detected_language} is not en, translating query to English.")
            query = self.translation_service.translate_text_nmt(text=query, target="en")
        return query

    def translate_response_if_needed(
        self, detected_language: str, qa_response: Dict[str, str]
    ) -> Dict[str, str]:
        """Translates the response if the language of response and incoming query do not match"""
        # Always detect response language and use to drive translation
        # qa_response_language = self.translation_service.detect_language_nmt(
        #     qa_response["answer"]
        # )
        # if (
        #     detected_language != qa_response_language
        #     and qa_response["responseType"] != "DynamicAPIFlow"
        # ):
        #     qa_response["answer"] = self.translation_service.translate_text_nmt(
        #         text=qa_response["answer"], target=detected_language
        #     )
        
        bool_translate = False
        qa_response_type = qa_response["responseType"]       
         
        # Only translate response if the request language was not english
        if (
            detected_language != 'en'
            and qa_response_type != "DynamicAPIFlow"
        ):
            if (
                qa_response_type == 'StaticKnowledgebaseQnA' 
                and configcontex.FEATURE_KDB_ID == 'True'
            ):
                if(detected_language not in ['id', 'en']):
                    bool_translate = True
            else:
                bool_translate = True
                
        if(bool_translate):
            qa_response["answer"] = self.translation_service.translate_text_nmt(
                text=qa_response["answer"], target=detected_language
            )
        else:
            self.log(logging.INFO, f"No translation for {qa_response_type}, feature_kdb_id {configcontex.FEATURE_KDB_ID} and detected_language {detected_language}")        
        return qa_response

    def invoke(self, query: str, history_messages: List[Message]) -> Dict[str, Union[str, Dict[str, str]]]:
        try:
            original_query = query
            detected_language = self.translation_service.detect_language_nmt(query)

            reframed_query = self.reframe_query(original_query, detected_language, history_messages)

            query = self.translate_query_if_needed(reframed_query, detected_language)

            nlu_router_response = self.get_nlu_router_response(query)
            self.log(
                logging.INFO,
                f"Input Query: {query} | NLURouter Response:{nlu_router_response}",
            )

            qa_response = self.get_qa_response(query, nlu_router_response, reframed_query, detected_language)
            self.log(logging.INFO, f"PreTranslation QA Response: {qa_response}")
            
            qa_response = self.translate_response_if_needed(
                detected_language=detected_language,
                qa_response=qa_response,
            )
            self.log(logging.INFO, f"Final QA Response: {qa_response}")

            self.log(logging.INFO, f"ServiceMetrics: {service_metrics.get().getServiceMetricsSummary()}")
            
            return qa_response

        except Exception as e:
            self.log(logging.ERROR, f"Error in RouterAgent.invoke while processing query: {str(e)}")
            return self.default_response
