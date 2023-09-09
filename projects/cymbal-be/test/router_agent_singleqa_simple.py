import requests
import json
import argparse
import datetime
import time
import logging
from config import ENV_SETTINGS

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

logging.basicConfig(level=logging.INFO)

def get_env_settings(env):
    return ENV_SETTINGS.get(env, ENV_SETTINGS.get('local'))

def create_session():
    return datetime.datetime.now().strftime("%d%m%y%H%M")

def get_user_input():
    return input("Enter your question: ")

def post_request(url, headers, data):
    try:
        return requests.post(url, headers=headers, data=json.dumps(data))
    except Exception as e:
        logging.error(f"Failed to send request: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='CLI tool for testing API')
    parser.add_argument('-e', '--environment', default='local', help='Environment option ["dev","uat","local"]')

    args = parser.parse_args()
    env_settings = get_env_settings(args.environment)
    logging.info(f"Selected Environment: {args.environment}")

    session = create_session()
    current_q = 0
    user_1, bot_1 = "Hi", "Hello"
    user_2, bot_2 = "How are you", "I am great"
    user_3, bot_3 = "Nice to meet you", "Likewise"

    while True:
        question = get_user_input()
        current_q += 1
        start_time = time.time()

        logging.info(f"\nSession ID {session}__{current_q} | Question :: {question}")
        timestamp = datetime.datetime.now().strftime("%d%m%y%H%M")
        data = {
            "llmRouterRequest": question,
            "requestMetadata": {
                "clientInfo": "Shanky",
                "sessionInfo": f"{timestamp}__{current_q}",
                "userInfo": "0192787785"
            },
            "messages": [
                {
                    "author": "user",
                    "content": user_1
                },
                {
                    "author": "bot",
                    "content": bot_1
                },
                {
                    "author": "user",
                    "content": user_2
                },
                {
                    "author": "bot",
                    "content": bot_2
                },
                {
                    "author": "user",
                    "content": user_3
                },
                {
                    "author": "bot",
                    "content": bot_3
                }                                
            ]  
        }

        response = post_request(env_settings['url'], env_settings['headers'], data)
        if response is None:
            continue

        response_time = (time.time() - start_time) * 1000
        response_json = response.json()

        logging.info(f"Response Time - {response_time}")
        logging.info(f"RESPONSE ::: {fn_print_router_response(response_json)}\n")

        query_response = fn_get_router_response(response_json)

        user_1, user_2, user_3 = user_2, user_3, question
        bot_1, bot_2, bot_3 = bot_2, bot_3, query_response

        if question.lower() == "exit":
            break

if __name__ == "__main__":
    main()