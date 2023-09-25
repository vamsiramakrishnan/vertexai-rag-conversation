from google.cloud import translate_v2 as translate
from google.cloud import translate as translate_nmt
import iso639
import logging
from helpers.logging_configurator import logger, request_origin, service_metrics
from errors.translation_errors import LanguageDetectionError, TranslationError


class TranslationService:
    """
    A class used to represent a Translation Service.
    """
    def __init__(
        self,
        project_id: str = "marc-genai-01",
        region: str = "us-central1",
    ):
        """
        Constructs all the necessary attributes for the TranslationService object.
        :param project_id: The project id.
        :param region: The region.
        """
        self.project_id = project_id
        self.region = region
        self.logger = self._initialize_logger()
        self.translate_client = translate.Client()
        self.translate_service_client = translate_nmt.TranslationServiceClient()

    def _initialize_logger(self):
        """
        Initializes the logger.
        :return: The logger.
        """
        logger = logging.getLogger(__name__)
        return logger

    def log_message(self, level, message):
        """
        Logs a message.
        :param level: The level of the message.
        :param message: The message.
        """
        self.logger.log(level, f"TranslationService - Origin: {request_origin.get()} | {message}")

    def get_language_name(self, language_code):
        """
        Gets the name of a language.
        :param language_code: The language code.
        :return: The name of the language.
        """
        try:
            language_name = iso639.to_name(language_code)
            return language_name
        except ValueError as e:
            self.log_message(logging.ERROR, f"Could not find language for code {language_code}")
            raise e

    def detect_language(self, text):
        """
        Detects the language of a text.
        :param text: The text.
        :return: The language.
        """
        result = self.translate_client.detect_language(text)
        return result["language"]

    def translate_text(self, text, target):
        """
        Translates a text to a target language.
        :param text: The text.
        :param target: The target language.
        :return: The translated text.
        """
        result = self.translate_client.translate(text, target_language=target)
        return result["translatedText"]

    def detect_language_nmt(self, text: str) -> str:
        """
        Detects the language of a text using NMT.
        :param text: The text.
        :return: The language.
        """
        try:
            self.log_message(
                logging.INFO,
                f"DetectLanguage - Text: {text}",
            )
            self.log_message(
                logging.INFO,
                f"DetectLanguagePayload: {len(text)}",
            )
            service_metrics.get().setMetrics("MetricsLangDetect", len(text))
            result = self.translate_service_client.detect_language(
                parent=f"projects/{self.project_id}/locations/{self.region}",
                content=text,
                mime_type="text/plain",
            )
            self.log_message(logging.INFO, f"DetectLanguage - Output: {result}")
            result = max(
                result.languages, key=lambda language: language.confidence, default=None
            )
            return (
                "id"
                if (
                    result.language_code not in ["en", "id"]
                )
                else result.language_code
            )
        except Exception as e:
            self.log_message(
                logging.ERROR, f"Error occurred while detecting language: {str(e)}"
            )
            raise LanguageDetectionError(
                "Error occurred while detecting language: " + str(e)
            ) from e

    def translate_text_nmt(self, text, target):
        """
        Translates a text to a target language using NMT.
        :param text: The text.
        :param target: The target language.
        :return: The translated text.
        """
        try:
            self.log_message(
                logging.INFO,
                f"TranslateLanguage - Target: {target} | Text: {text}",
            )     
            self.log_message(
                logging.INFO,
                f"TranslateLanguagePayload: {len(text)}",
            )
            service_metrics.get().setMetrics("MetricsLangTranslate", len(text))                   
            result = self.translate_service_client.translate_text(
                request={
                    "parent": f"projects/{self.project_id}/locations/{self.region}",
                    "contents": [text],
                    "mime_type": "text/plain",
                    "target_language_code": target,
                }
            )
            result = max(
                result.translations,
                key=lambda language: language.translated_text,
                default=None,
            )
            self.log_message(logging.INFO, f"TranslateLanguage - Output: {result.translated_text}")
            return result.translated_text
        except Exception as e:
            self.log_message(logging.ERROR, f"Error occurred while translating text: {str(e)}")
            raise TranslationError(
                "Error occurred while translating text" + str(e)
            ) from e
            
            
    def translate_text_nmt_from_source(self, text, source, target):
        """
        Translates a text from a source language to a target language using NMT.
        :param text: The text.
        :param source: The source language.
        :param target: The target language.
        :return: The translated text.
        """
        try:
            self.log_message(
                logging.INFO,
                f"TranslateLanguage - Target: {target} | Text: {text}",
            )     
            self.log_message(
                logging.INFO,
                f"TranslateLanguagePayload: {len(text)}",
            )
            service_metrics.get().setMetrics("MetricsLangTranslate", len(text))                   
            result = self.translate_service_client.translate_text(
                request={
                    "parent": f"projects/{self.project_id}/locations/{self.region}",
                    "contents": [text],
                    "mime_type": "text/plain",
                    "source_language_code": source,
                    "target_language_code": target,
                }
            )
            result = max(
                result.translations,
                key=lambda language: language.translated_text,
                default=None,
            )
            self.log_message(logging.INFO, f"TranslateLanguage - Output: {result.translated_text}")
            return result.translated_text
        except Exception as e:
            self.log_message(logging.ERROR, f"Error occurred while translating text: {str(e)}")
            raise TranslationError(
                "Error occurred while translating text" + str(e)
            ) from e            
