from models.llm_cr_be_models import (
    RouterAgentPostResponse,
    SmallTalkResponse,
    StaticKnowledgebaseQnAResponse,
    DynamicAPIFlowResponse,
    FallbackIntentResponse,
    ResponseType,
    FlowType,
)

RESPONSE_BUILDERS = {
    "SmallTalk": "SmallTalkResponseBuilder",
    "StaticKnowledgebaseQnA": "StaticKnowledgebaseQnAResponseBuilder",
    "ProductFlow": "StaticKnowledgebaseQnAResponseBuilder",
    "DynamicAPIFlow": "DynamicAPIFlowResponseBuilder",
}

class RouterAgentResponseFactory:
    @staticmethod
    def get_response_builder(response_type):
        response_type = response_type.casefold()
        builder = RESPONSE_BUILDERS.get(response_type)
        if builder:
            return globals()[builder]()
        else:
            return FallbackIntentResponseBuilder()

class RouterAgentResponseBuilder:
    def build_response(self, llm_response, original_user_query):
        raise NotImplementedError()

class SmallTalkResponseBuilder(RouterAgentResponseBuilder):
    def build_response(self, llm_response, original_user_query):
        smallTalkResponse = SmallTalkResponse(
            answer=llm_response["answer"], recognized_nlp_entities=None
        )
        return RouterAgentPostResponse(
            responseType=ResponseType.smallTalk,
            smallTalkResponse=smallTalkResponse,
            originalUserQuery=original_user_query,
        )

class StaticKnowledgebaseQnAResponseBuilder(RouterAgentResponseBuilder):
    def build_response(self, llm_response, original_user_query):
        static_knowledgebase_response = StaticKnowledgebaseQnAResponse(
            answer=llm_response["answer"]
        )
        return RouterAgentPostResponse(
            responseType=ResponseType.staticKnowledgebaseQnA,
            staticKnowledgebaseQnAResponse=static_knowledgebase_response,
            originalUserQuery=original_user_query,
        )

class DynamicAPIFlowResponseBuilder(RouterAgentResponseBuilder):
    def build_response(self, llm_response, original_user_query):
        flow_type = (
            FlowType.accountInfo
            if llm_response["answer"] == "accountInfo"
            else FlowType.billPaymentInfo
            if llm_response["answer"] == "billPaymentInfo"
            else FlowType.imPoinInfo
        )
        dynamic_api_flow_response = DynamicAPIFlowResponse(flowType=flow_type)
        return RouterAgentPostResponse(
            responseType=ResponseType.dynamicAPIFlow,
            dynamicAPIFlowResponse=dynamic_api_flow_response,
            originalUserQuery=original_user_query,
        )

class FallbackIntentResponseBuilder(RouterAgentResponseBuilder):
    def build_response(self, llm_response, original_user_query):
        fallback_intent_response = FallbackIntentResponse(
            fallBackReason="Unknown Intent", fallBackResponse=llm_response["answer"]
        )
        return RouterAgentPostResponse(
            responseType=ResponseType.fallbackIntent,
            fallbackIntentResponse=fallback_intent_response,
            originalUserQuery=original_user_query,
        )

