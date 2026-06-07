"""Language detection and translation module."""

from deep_translator import GoogleTranslator
from langdetect import detect, DetectorFactory
from config import Config

# Set seed for consistent language detection
DetectorFactory.seed = 0


class LanguageService:
    """Handles language detection and translation."""

    def __init__(self):
        self.translator = GoogleTranslator()

    def detect_language(self, text: str) -> str:
        """
        Detect the language of input text.

        Args:
            text: Input text to analyze

        Returns:
            ISO language code (e.g., 'en', 'es', 'fr')
        """
        try:
            # Short text handling
            if len(text.strip()) < 10:
                return Config.DEFAULT_LANGUAGE

            detected = detect(text)
            return detected if detected in Config.SUPPORTED_LANGUAGES else Config.DEFAULT_LANGUAGE
        except Exception:
            return Config.DEFAULT_LANGUAGE

    def translate_to_english(self, text: str, src_lang: str) -> str:
        """
        Translate text to English for processing.

        Args:
            text: Input text in any language
            src_lang: Source language code

        Returns:
            Translated text in English
        """
        if src_lang == 'en':
            return text

        try:
            return GoogleTranslator(source=src_lang, target='en').translate(text)
        except Exception:
            return text

    def translate_from_english(self, text: str, dest_lang: str) -> str:
        """
        Translate English text to target language.

        Args:
            text: English text to translate
            dest_lang: Destination language code

        Returns:
            Translated text in target language
        """
        if dest_lang == 'en':
            return text

        try:
            return GoogleTranslator(source='en', target=dest_lang).translate(text)
        except Exception:
            return text

    def process_input(self, text: str) -> tuple:
        """
        Full pipeline: detect language and translate to English.

        Args:
            text: User input in any language

        Returns:
            Tuple of (detected_language, english_text)
        """
        detected_lang = self.detect_language(text)
        english_text = self.translate_to_english(text, detected_lang)
        return detected_lang, english_text

    def process_output(self, text: str, target_lang: str) -> str:
        """
        Translate response back to user's language.

        Args:
            text: English response text
            target_lang: Target language code

        Returns:
            Translated response
        """
        return self.translate_from_english(text, target_lang)
