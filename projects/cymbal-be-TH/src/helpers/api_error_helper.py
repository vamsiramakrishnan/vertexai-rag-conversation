import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def handle_api_error(e: Exception):
    error_message = str(e)
    logger.error(error_message, exc_info=True)
    return HTTPException(status_code=500, detail=error_message)
