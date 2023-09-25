class LanguageDetectionError(Exception):
    """
    Exception raised when there is an error in language detection.
    """
    def __init__(self, message):
        """
        Initializes the LanguageDetectionError with a message.
        """
        super().__init__(message)


class TranslationError(Exception):
    """
    Exception raised when there is an error in translation.
    """
    def __init__(self, message):
        """
        Initializes the TranslationError with a message.
        """
        super().__init__(message)
