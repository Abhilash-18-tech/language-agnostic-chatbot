"""Main Chatbot Engine - ties all components together."""

from translator import LanguageService
from intent_classifier import IntentClassifier
from chat_history import ChatHistory
from ai_api import AIResponseGenerator
from config import Config
import random


class Chatbot:
    """
    Language-Agnostic AI Chatbot with API support.

    Features:
    - Auto language detection
    - Translate → Process → Translate back
    - Context awareness
    - Domain-specific responses
    - Google Gemini AI integration (optional)
    - Confidence scoring
    """

    def __init__(self, domain: str = Config.DEFAULT_DOMAIN, api_key: str = None):
        self.language_service = LanguageService()
        self.intent_classifier = IntentClassifier(domain)
        self.history = ChatHistory()
        self.domain = domain
        self.current_language = Config.DEFAULT_LANGUAGE

        # Initialize AI response generator
        self.ai_generator = AIResponseGenerator(api_key)

    def set_domain(self, domain: str):
        """Change the chatbot domain."""
        self.domain = domain
        self.intent_classifier.set_domain(domain)

    def set_language(self, language: str):
        """Manually set the response language."""
        self.current_language = language

    def set_api_key(self, api_key: str):
        """Set API key for AI responses."""
        self.ai_generator.set_api_key(api_key)

    def is_api_available(self) -> bool:
        """Check if AI API is available."""
        return self.ai_generator.is_api_available()

    def get_response(self, user_input: str) -> dict:
        """
        Process user input and generate response.

        Args:
            user_input: User message in any language

        Returns:
            Dict with response, language, intent, confidence
        """
        # Step 1: Detect language and translate to English
        detected_lang, english_input = self.language_service.process_input(user_input)
        self.current_language = detected_lang

        # Step 2: Get context from history
        context = self.history.get_history(limit=4)

        # Step 3: Generate response (AI or local)
        result = self.ai_generator.generate_response(
            query=english_input,
            domain=self.domain,
            context=context,
            language=detected_lang
        )

        response_text = result['response']
        confidence = result['confidence']
        source = result.get('source', 'local')
        intent = result.get('intent', 'unknown')

        # Step 4: Translate response back to user's language
        if source == 'gemini':
            # AI responses are already contextual, translate if needed
            if detected_lang != 'en':
                translated_response = self.language_service.process_output(
                    response_text, self.current_language
                )
            else:
                translated_response = response_text
        else:
            # Local responses - translate
            translated_response = self.language_service.process_output(
                response_text, self.current_language
            )

        # Step 5: Store in history
        self.history.add_message(
            'user', user_input, detected_lang, intent, confidence
        )
        self.history.add_message(
            'assistant', translated_response, self.current_language
        )

        return {
            'response': translated_response,
            'language': self.current_language,
            'detected_language': detected_lang,
            'intent': intent,
            'confidence': round(confidence, 2),
            'domain': self.domain,
            'source': source,
            'api_available': self.is_api_available()
        }

    def get_history(self) -> list:
        """Get conversation history."""
        return self.history.get_history()

    def clear_history(self):
        """Clear conversation history."""
        self.history = ChatHistory()

    def get_status(self) -> dict:
        """Get chatbot status."""
        return {
            'domain': self.domain,
            'language': self.current_language,
            'supported_languages': list(Config.SUPPORTED_LANGUAGES.values()),
            'message_count': len(self.history.history),
            'api_available': self.is_api_available()
        }
