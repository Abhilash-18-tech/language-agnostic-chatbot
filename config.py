"""Configuration settings for the chatbot."""

class Config:
    # Supported languages
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'zh-cn': 'Chinese (Simplified)',
        'ja': 'Japanese',
        'ko': 'Korean',
        'hi': 'Hindi',
        'ar': 'Arabic',
        'ta': 'Tamil',
        'te': 'Telugu',
        'bn': 'Bengali',
    }

    # Default language
    DEFAULT_LANGUAGE = 'en'

    # Domain options
    DOMAINS = ['college', 'health', 'helpdesk', 'general']
    DEFAULT_DOMAIN = 'general'

    # Confidence threshold
    CONFIDENCE_THRESHOLD = 0.6

    # Chat history limit
    MAX_HISTORY_LENGTH = 10
