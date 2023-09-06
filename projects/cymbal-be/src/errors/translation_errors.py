class LanguageDetectionError(Exception):
    def __init__(self, message):
        super().__init__(message)


class TranslationError(Exception):
    def __init__(self, message):
        super().__init__(message)
