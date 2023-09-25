import logging
from fastapi import HTTPException


logger = logging.getLogger(__name__)


def handle_api_error(exception: Exception):
    """
    Handle API errors by logging the error message and returning an HTTPException with status code 500 and the error message as detail.
    :param exception: The exception to handle.
    :return: An HTTPException with status code 500 and the error message as detail.
    """
    error_message = str(exception)
    logger.error(error_message, exc_info=True)
    return HTTPException(status_code=500, detail=error_message)
