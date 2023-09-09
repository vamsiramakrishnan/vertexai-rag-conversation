import json

def fn_print_router_response(json_obj: dict):

    if json_obj["responseType"]=="smallTalk":
        return "SmallTalk -> "+json_obj["smallTalkResponse"]["answer"]
    elif json_obj["responseType"]=="staticKnowledgebaseQnA":
        return "Q&A -> "+json_obj["staticKnowledgebaseQnAResponse"]["answer"]
    elif json_obj["responseType"]=="dynamicAPIFlow":
        return "DynamicAPI -> "+json_obj["dynamicAPIFlowResponse"]["flowType"]
    elif json_obj["responseType"]=="fallbackIntent":
        return "Fallback -> "+json_obj["fallbackIntentResponse"]["fallBackResponse"]
    else:
        return "Unknown RouterAgent Reponse"

def fn_get_router_response(json_obj: dict):

    if json_obj["responseType"]=="smallTalk":
        return json_obj["smallTalkResponse"]["answer"]
    elif json_obj["responseType"]=="staticKnowledgebaseQnA":
        return json_obj["staticKnowledgebaseQnAResponse"]["answer"]
    elif json_obj["responseType"]=="dynamicAPIFlow":
        return json_obj["dynamicAPIFlowResponse"]["flowType"]
    elif json_obj["responseType"]=="fallbackIntent":
        return json_obj["fallbackIntentResponse"]["fallBackResponse"]
    else:
        return "Unknown RouterAgent Reponse"                  