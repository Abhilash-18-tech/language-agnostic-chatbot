"""Chat history and context management."""

from collections import deque
from datetime import datetime
from config import Config
import json


class ChatHistory:
    """Manages conversation history and context."""

    def __init__(self, session_id: str = None):
        self.session_id = session_id or datetime.now().strftime('%Y%m%d%H%M%S')
        self.history = deque(maxlen=Config.MAX_HISTORY_LENGTH)
        self.context = {}

    def add_message(self, role: str, content: str, language: str = 'en',
                    intent: str = None, confidence: float = None):
        """
        Add a message to the conversation history.

        Args:
            role: 'user' or 'assistant'
            content: Message content
            language: Language code of the message
            intent: Detected intent (for user messages)
            confidence: Confidence score (for user messages)
        """
        message = {
            'role': role,
            'content': content,
            'language': language,
            'timestamp': datetime.now().isoformat(),
        }

        if intent:
            message['intent'] = intent
        if confidence is not None:
            message['confidence'] = confidence

        self.history.append(message)

    def get_history(self, limit: int = None) -> list:
        """
        Get conversation history.

        Args:
            limit: Maximum number of messages to return

        Returns:
            List of message dictionaries
        """
        if limit:
            return list(self.history)[-limit:]
        return list(self.history)

    def get_last_user_intent(self) -> dict:
        """Get the last user intent from history."""
        for message in reversed(self.history):
            if message['role'] == 'user' and 'intent' in message:
                return {
                    'intent': message['intent'],
                    'confidence': message.get('confidence', 0)
                }
        return None

    def get_context_value(self, key: str, default=None):
        """Get a value from the context."""
        return self.context.get(key, default)

    def set_context(self, key: str, value):
        """Set a context value."""
        self.context[key] = value

    def clear_context(self):
        """Clear the context."""
        self.context.clear()

    def export_history(self) -> str:
        """Export history as JSON string."""
        return json.dumps(list(self.history), indent=2)

    def get_summary(self) -> str:
        """Get a brief summary of the conversation."""
        if not self.history:
            return "No conversation yet."

        messages = list(self.history)
        return f"Conversation with {len(messages)} messages. Last topic: {messages[-1].get('intent', 'unknown')}"
