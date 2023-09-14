from fastapi import FastAPI
from agents.router_agent import RouterAgent
from agents.chat_agent import ChatAgent
from agents.conversational_chat_agent import ConversationalChatAgent
from config.config import AppConfig
import vertexai
import logging
import asyncio

logger = logging.getLogger(__name__)
startup_lock = asyncio.Lock()


class AgentFactory:
    @staticmethod
    async def create_agent(agent_type: str, app: FastAPI, config: AppConfig):
        if agent_type == "router_agent":
            BUCKET_NAME = (
                "gs://"
                + config.PROJECT_ID
                + "-"
                + config.BUCKET_PREFIX
                + "-"
                + config.DEPLOYMENT_ENV
            )
            return RouterAgent(
                bucket_name=BUCKET_NAME,
                project_id=config.PROJECT_ID,
                index_name=config.INDEX_EN,
                index_name_id=config.INDEX_ID
            )
        elif agent_type == "chat_agent":
            return ChatAgent(project_id=config.PROJECT_ID, region=config.REGION)
        elif agent_type == "conversational_chat_agent":
            return ConversationalChatAgent(
                project_id=config.PROJECT_ID, region=config.REGION
            )
        else:
            raise ValueError(f"Invalid agent type: {agent_type}")

    @staticmethod
    async def initialize_agents(app: FastAPI, config: AppConfig):
        async with startup_lock:
            logger.info("********** Configuration **********"+config.getConfigAsString())
            if not hasattr(app.state, "agents"):  # check if already initialized
                logger.info("Reading Configurations")
                vertexai.init(project=config.PROJECT_ID, location=config.REGION)

                app.state.agents = {
                    "router_agent": await AgentFactory.create_agent(
                        "router_agent", app, config
                    ),
                    "chat_agent": await AgentFactory.create_agent(
                        "chat_agent", app, config
                    ),
                    "conversational_chat_agent": await AgentFactory.create_agent(
                        "conversational_chat_agent", app, config
                    ),
                }

                logger.info("Ready to accept Application Requests")
