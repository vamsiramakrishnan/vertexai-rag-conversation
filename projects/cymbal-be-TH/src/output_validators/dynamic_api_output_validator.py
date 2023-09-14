import logging
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from helpers.logging_configurator import logger
from typing import Dict


class DynamicAPIResponse(BaseModel):
    Response: str = Field(
        description="Response - Can be accountInfo, billPaymentInfo, imPoinInfo "
    )

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if isinstance(v, dict):
            return DynamicAPIResponse(**v)
        return v
