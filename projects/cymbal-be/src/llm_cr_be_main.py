from typing import Union
from fastapi import FastAPI, Depends
from models.llm_cr_be_models import *
from helpers.api_error_helper import handle_api_error
from factories.router_agent_response_factory import RouterAgentResponseFactory
from factories.agent_factory import AgentFactory
from agents.router_agent import RouterAgent
from agents.chat_agent import ChatAgent
from agents.conversational_chat_agent import ConversationalChatAgent
from config.config import AppConfig, configcontex
import logging
from helpers.logging_configurator import (
    logging_context,
    client_info_var,
    session_info_var,
    user_info_var,
    logger,
    request_origin,
    service_metrics
)
import asyncio
from helpers.service_metrics import ServiceMetrics

#config = AppConfig("./config/config.ini")
config = configcontex
app = FastAPI()
logger.info("Starting Application")
startup_lock = asyncio.Lock()


@app.on_event("startup")
async def startup_event():
    await AgentFactory.initialize_agents(app, config)


def get_agent(agent_name: str):
    return app.state.agents.get(agent_name)


@app.post(
    "/chatagent",
    response_model=ChatAgentPostResponse,
    responses={
        400: {"model": ChatAgentErrorResponse},
        500: {"model": ChatAgentErrorResponse},
    },
)
async def get_chat_agent_response(
    body: ChatAgentPostRequest,
    chat_agent: ChatAgent = Depends(lambda: get_agent("chat_agent")),
) -> Union[ChatAgentPostResponse, ChatAgentErrorResponse]:
    chat_agent_metadata = body.requestMetadata or None
    service_metrics.set(ServiceMetrics())
    if chat_agent_metadata is not None:
        client_info_var.set(chat_agent_metadata.clientInfo)
        session_info_var.set(chat_agent_metadata.sessionInfo)
        user_info_var.set(chat_agent_metadata.userInfo)
        request_origin.set(
            f"{chat_agent_metadata.clientInfo}_{chat_agent_metadata.userInfo}_{chat_agent_metadata.sessionInfo}"
        )
    else:
        request_origin.set(
            "NA_NA_NA"
        )        
    logger.info(
        f"Main ChatAgentFlow Input - Origin: {request_origin.get()} | Request: {body}"
    )    
    try:
        llm_chat_response = chat_agent.invoke(body=body)
        logger.info(
            f"Main ChatAgentFlow Output - Origin: {request_origin.get()} | Response: {llm_chat_response}"
        )            
        return ChatAgentPostResponse(
            responseType=ResponseType.llmChatResponse, llmChatResponse=llm_chat_response
        )
    except Exception as e:
        raise handle_api_error(e)


@app.post(
    "/conversationalchatagent",
    response_model=ChatAgentPostResponse,
    responses={
        400: {"model": ChatAgentErrorResponse},
        500: {"model": ChatAgentErrorResponse},
    },
)
async def get_chat_agent_response(
    body: ChatAgentPostRequest,
    conversational_chat_agent: ConversationalChatAgent = Depends(
        lambda: get_agent("conversational_chat_agent")
    ),
) -> Union[ChatAgentPostResponse, ChatAgentErrorResponse]:
    chat_agent_metadata = body.requestMetadata or None
    service_metrics.set(ServiceMetrics())
    if chat_agent_metadata is not None:
        client_info_var.set(chat_agent_metadata.clientInfo)
        session_info_var.set(chat_agent_metadata.sessionInfo)
        user_info_var.set(chat_agent_metadata.userInfo)
        request_origin.set(
            f"{chat_agent_metadata.clientInfo}_{chat_agent_metadata.userInfo}_{chat_agent_metadata.sessionInfo}"
        )
    else:
        request_origin.set(
            "NA_NA_NA"
        )        
    logger.info(
        f"Main ConversationChatAgentFlow Input - Origin: {request_origin.get()} | Request: {body}"
    )        
    try:
        llm_chat_response = conversational_chat_agent.invoke(body=body)
        logger.info(
            f"Main ConversationChatAgentFlow Output - Origin: {request_origin.get()} | Response: {llm_chat_response}"
        )        
        return ChatAgentPostResponse(
            responseType=ResponseType.llmChatResponse, llmChatResponse=llm_chat_response
        )
    except Exception as e:
        raise handle_api_error(e)


@app.post(
    "/routeragent",
    response_model=RouterAgentPostResponse,
    responses={
        400: {"model": RouterAgentErrorResponse},
        500: {"model": RouterAgentErrorResponse},
    },
)
async def get_router_agent_response(
    body: RouterAgentPostRequest,
    router_agent: RouterAgent = Depends(lambda: get_agent("router_agent")),
) -> Union[RouterAgentPostResponse, RouterAgentErrorResponse]:
    user_query = body.llmRouterRequest
    user_history_messages = body.messages or None
    router_agent_metadata = body.requestMetadata or None
    service_metrics.set(ServiceMetrics())
    if router_agent_metadata is not None:
        client_info_var.set(router_agent_metadata.clientInfo)
        session_info_var.set(router_agent_metadata.sessionInfo)
        user_info_var.set(router_agent_metadata.userInfo)
        request_origin.set(
            f"{router_agent_metadata.clientInfo}_{router_agent_metadata.userInfo}_{router_agent_metadata.sessionInfo}"
        )
    else:
        request_origin.set(
            "NA_NA_NA"
        )        
    router_agent_developer_options = body.developerOptions or None
    logger.info(
        f"Main RouterAgentFlow Input - Origin: {request_origin.get()} | Request: {body}"
    )
    try:
        llm_response = router_agent.invoke(query=user_query, history_messages=user_history_messages)
        original_user_query = OriginalUserQuery(__root__=user_query)
        response_builder = RouterAgentResponseFactory.get_response_builder(
            llm_response["responseType"]
        )
        router_agent_response = response_builder.build_response(
            llm_response, original_user_query
        )
        logger.info(
            f"Main RouterAgentFlow Output - Origin: {request_origin.get()} | Response: {router_agent_response}"
        )
        return router_agent_response
    except Exception as e:
        raise handle_api_error(e)
