import logging
from logging.handlers import RotatingFileHandler
import google.cloud.logging
from contextvars import ContextVar
from helpers.service_metrics import ServiceMetrics

class ContextFilter(logging.Filter):
    def filter(self, record):
        record.client_info = client_info_var.get()
        record.user_info = user_info_var.get()
        record.session_info = session_info_var.get()
        return True

# To supress logging from imported modules due to use of common root logger
class SupressModuleFilter(logging.Filter):
    def filter(self, record):
        if record.module in ["text_splitter"]:
            return False
        else:
            return True

class LoggingContext:
    def __init__(self, logger):
        self.logger = logger
        self.client_info_var = ContextVar("client_info_var", default=None)
        self.session_info_var = ContextVar("session_info_var", default=None)
        self.user_info_var = ContextVar("user_info_var", default=None)
        self.request_origin = ContextVar("request_origin", default=None)
        self.service_metrics = ContextVar("service_metrics", default=None)

    def set_client_info(self, value):
        self.client_info_var.set(value)

    def set_session_info(self, value):
        self.session_info_var.set(value)

    def set_user_info(self, value):
        self.user_info_var.set(value)

    def set_request_origin(self, value):
        self.user_info_var.set(value)


def configure_logging(
    console_level=logging.INFO, log_file="application.log", log_file_level=logging.INFO
):
    client = google.cloud.logging.Client()

    # Create a file handler with log rotation
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5
    )
    file_handler.setLevel(log_file_level)

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)

    # Create a JSON formatter for the file handler and a simple one for the console handler
    json_formatter = logging.Formatter(
        '{"client_info": "%(client_info)s", "user_info": "%(user_info)s", "session_info": "%(session_info)s", '
        '"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "message": %(message)s}'
    )
    simple_formatter = logging.Formatter(
        "%(client_info)s - %(user_info)s - %(session_info)s - %(asctime)s - %(name)s - %(levelname)s - %(module)s  - %(message)s"
    )

    file_handler.setFormatter(json_formatter)
    console_handler.setFormatter(simple_formatter)

    context_filter = ContextFilter()
    file_handler.addFilter(context_filter)
    console_handler.addFilter(context_filter)

    # To supress logging from imported modules due to use of common root logger
    module_filter = SupressModuleFilter()
    file_handler.addFilter(module_filter)
    console_handler.addFilter(module_filter)    

    # Remove existing handlers to avoid duplicate logs
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Set logger level to the lowest level handler
    root_logger.setLevel(min(console_level, log_file_level))

    # Add the handlers to the root logger
    root_logger.addHandler(file_handler)
    # Commenting below since this output also goes into Cloud Logging as duplicate and additionally also overflows into multiple log entries
    # root_logger.addHandler(console_handler)

    # Use the Google Cloud Logging handler
    cloud_handler = google.cloud.logging.handlers.CloudLoggingHandler(client)
    cloud_handler.setLevel(console_level)
    cloud_handler.addFilter(context_filter)
    cloud_handler.addFilter(module_filter)
    root_logger.addHandler(cloud_handler)

    logger = root_logger
    context = LoggingContext(logger)
    return context


logging_context = configure_logging()
logger = logging_context.logger
client_info_var = logging_context.client_info_var
session_info_var = logging_context.session_info_var
user_info_var = logging_context.user_info_var
request_origin = logging_context.request_origin
service_metrics = logging_context.service_metrics