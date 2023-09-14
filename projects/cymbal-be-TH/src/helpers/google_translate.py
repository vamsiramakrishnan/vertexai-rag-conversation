from google.cloud import translate_v2 as translate
from google.cloud import translate as translate_nmt
import iso639
import logging
#from helpers.logging_configurator import logger, request_origin
from helpers.logging_configurator import logger, request_origin, service_metrics
from errors.translation_errors import LanguageDetectionError, TranslationError


class TranslationService:
    def __init__(
        self,
        project_id: str = "marc-genai-01",
        region: str = "us-central1",
    ):
        self.project_id = project_id
        self.region = region
        self.logger = self._setup_logger()
        self.translate_client = translate.Client()
        self.translate_service_client = translate_nmt.TranslationServiceClient()

    def _setup_logger(self):
        logger = logging.getLogger(__name__)
        return logger

    def log(self, level, message):
        self.logger.log(level, f"TranslationService - Origin: {request_origin.get()} | {message}")

    def get_language_name(self, language_code):
        try:
            language_name = iso639.to_name(language_code)
            return language_name
        except ValueError as e:
            self.log(logging.ERROR, f"Could not find language for code {language_code}")
            raise e

    def detect_language(self, text):
        result = self.translate_client.detect_language(text)
        return result["language"]

    def translate_text(self, text, target):
        result = self.translate_client.translate(text, target_language=target)
        return result["translatedText"]

    def detect_language_nmt(self, text: str) -> str:
        try:
            self.log(
                logging.INFO,
                f"DetectLanguage - Text: {text}",
            )
            self.log(
                logging.INFO,
                f"DetectLanguagePayload: {len(text)}",
            )
            service_metrics.get().setMetrics("MetricsLangDetect", len(text))
            result = self.translate_service_client.detect_language(
                parent=f"projects/{self.project_id}/locations/{self.region}",
                content=text,
                mime_type="text/plain",
            )
            self.log(logging.INFO, f"DetectLanguage - Output: {result}")
            result = max(
                result.languages, key=lambda language: language.confidence, default=None
            )
            return (
                "th"
                if (
                    #float(result.confidence) < 0.3 and 
                    result.language_code not in ["en", "th"]
                )
                else result.language_code
            )
        except Exception as e:
            self.log(
                logging.ERROR, f"Error occurred while detecting language: {str(e)}"
            )
            raise LanguageDetectionError(
                "Error occurred while detecting language: " + str(e)
            ) from e

    def translate_text_nmt(self, text, target):
        try:
            self.log(
                logging.INFO,
                f"TranslateLanguage - Target: {target} | Text: {text}",
            )     
            self.log(
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
            self.log(logging.INFO, f"TranslateLanguage - Output: {result.translated_text}")
            return result.translated_text
        except Exception as e:
            self.log(logging.ERROR, f"Error occurred while translating text: {str(e)}")
            raise TranslationError(
                "Error occured while translating text" + str(e)
            ) from e
            
            
    def translate_text_nmt_from_src(self, text, source, target):
        try:
            self.log(
                logging.INFO,
                f"TranslateLanguage - Target: {target} | Text: {text}",
            )     
            self.log(
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
            self.log(logging.INFO, f"TranslateLanguage - Output: {result.translated_text}")
            return result.translated_text
        except Exception as e:
            self.log(logging.ERROR, f"Error occurred while translating text: {str(e)}")
            raise TranslationError(
                "Error occured while translating text" + str(e)
            ) from e            
