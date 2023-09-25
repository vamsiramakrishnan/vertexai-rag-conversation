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
    AGENT_CLASSES = {
        "router_agent": RouterAgent,
        "chat_agent": ChatAgent,
        "conversational_chat_agent": ConversationalChatAgent,
    }

    @classmethod
    async def create_agent(cls, agent_type: str, app: FastAPI, config: AppConfig):
        agent_class = cls.AGENT_CLASSES.get(agent_type)
        if agent_class is None:
            raise ValueError(f"Invalid agent type: {agent_type}")

        if agent_type == "router_agent":
            BUCKET_NAME = (
                "gs://"
                + config.PROJECT_ID
                + "-"
                + config.BUCKET_PREFIX
                + "-"
                + config.DEPLOYMENT_ENV
            )
            return agent_class(
                bucket_name=BUCKET_NAME,
                project_id=config.PROJECT_ID,
                index_name=config.INDEX_EN,
                index_name_id=config.INDEX_ID
            )
        else:
            return agent_class(project_id=config.PROJECT_ID, region=config.REGION)

    @classmethod
    async def initialize_agents(cls, app: FastAPI, config: AppConfig):
        async with startup_lock:
            logger.info("********** Configuration **********"+config.getConfigAsString())
            if not hasattr(app.state, "agents"):  # check if already initialized
                logger.info("Reading Configurations")
                vertexai.init(project=config.PROJECT_ID, location=config.REGION)

                app.state.agents = {
                    agent_type: await cls.create_agent(agent_type, app, config)
                    for agent_type in cls.AGENT_CLASSES.keys()
                }

                logger.info("Ready to accept Application Requests")

