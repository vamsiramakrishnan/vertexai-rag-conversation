import logging
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from helpers.logging_configurator import logger
from typing import Dict


class NLURouterResponse(BaseModel):
    Intent: str = Field(
        description="User Intent detected in Query - SmallTalk, StaticKnowledgeBase, DynamicAPIFlow, FallBack"
    )

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, dict):
            return NLURouterResponse(**v)
        return v
