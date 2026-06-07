"""AI API Integration - Google Gemini for intelligent responses."""

import os

# Try to import google-generativeai
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class AIResponseGenerator:
    """
    Generates intelligent responses using AI APIs.
    Falls back to keyword-based responses if API is unavailable.
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get('GEMINI_API_KEY')
        self.model = None
        self.use_api = False

        if self.api_key and GEMINI_AVAILABLE:
            self._initialize_model()

    def _initialize_model(self):
        """Initialize the Gemini model."""
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.use_api = True
            print("[AI] Gemini API initialized successfully")
        except Exception as e:
            print(f"[AI] Failed to initialize Gemini: {e}")
            self.use_api = False

    def set_api_key(self, api_key: str):
        """Set API key and initialize model."""
        self.api_key = api_key
        if GEMINI_AVAILABLE:
            self._initialize_model()

    def generate_response(self, query: str, domain: str = 'general',
                          context: list = None, language: str = 'en') -> dict:
        """
        Generate an intelligent response.

        Args:
            query: User's question (in English)
            domain: Domain context (college, health, helpdesk, general)
            context: Recent conversation history
            language: User's language code

        Returns:
            Dict with response, confidence, and source
        """
        if self.use_api and self.model:
            return self._generate_with_api(query, domain, context, language)
        else:
            return self._generate_local(query, domain)

    def _generate_with_api(self, query: str, domain: str,
                           context: list, language: str) -> dict:
        """Generate response using Gemini API."""
        try:
            # Build context-aware prompt
            system_prompt = self._get_system_prompt(domain, language)

            # Add conversation context if available
            context_text = ""
            if context and len(context) > 0:
                recent = context[-4:]  # Last 4 messages
                context_text = "Recent conversation:\n"
                for msg in recent:
                    role = "User" if msg.get('role') == 'user' else "Assistant"
                    context_text += f"{role}: {msg.get('content', '')}\n"
                context_text += "\n"

            full_prompt = f"""{system_prompt}

{context_text}User's question: {query}

Provide a helpful, accurate, and concise response."""

            # Generate response
            response = self.model.generate_content(full_prompt)

            return {
                'response': response.text.strip(),
                'confidence': 0.95,
                'source': 'gemini',
                'intent': 'api_generated'
            }

        except Exception as e:
            print(f"[AI] API Error: {e}")
            # Fallback to local responses
            return self._generate_local(query, domain)

    def _generate_local(self, query: str, domain: str) -> dict:
        """Generate response using local keyword matching."""
        from intent_classifier import IntentClassifier

        classifier = IntentClassifier(domain)
        intent_result = classifier.classify(query)

        # Get response from intent classifier
        intents = classifier.intents
        intent = intent_result['intent']

        if intent in intents and 'responses' in intents[intent]:
            import random
            response = random.choice(intents[intent]['responses'])
            return {
                'response': response,
                'confidence': intent_result['confidence'],
                'source': 'local',
                'intent': intent
            }

        # Fallback
        return {
            'response': "I'm not sure I understand. Could you rephrase your question?",
            'confidence': 0.0,
            'source': 'local',
            'intent': 'unknown'
        }

    def _get_system_prompt(self, domain: str, language: str) -> str:
        """Get system prompt based on domain."""

        domain_prompts = {
            'college': """You are a helpful college admissions assistant. Help users with:
- Admissions and application process
- Courses, majors, and programs
- Tuition fees and financial aid
- Exams, assignments, and deadlines
- Library and campus facilities
- Student life and housing

Provide accurate, encouraging information. For specific cases, advise contacting the admissions office.""",

            'health': """You are a health information assistant. IMPORTANT: You provide general health INFORMATION, not medical advice.

Help users understand:
- Common symptoms and remedies
- Medications (general info only)
- Diet and nutrition
- Exercise and fitness
- Mental health resources

ALWAYS remind users to consult healthcare professionals for:
- Persistent symptoms
- Medical emergencies
- Prescription decisions
- Specific diagnoses

For emergencies, tell them to call emergency services immediately.""",

            'helpdesk': """You are an IT support assistant. Help users troubleshoot:
- Password and login issues
- Internet/network connectivity
- Software installation and errors
- Hardware problems (printers, monitors, etc.)
- Email issues
- Security concerns (viruses, phishing)
- Data backup and recovery

Provide step-by-step troubleshooting. For complex issues, advise creating a support ticket.""",

            'general': """You are a friendly, multilingual AI assistant. Help users with:
- General questions
- Casual conversation
- Information requests
- Jokes and entertainment

Be helpful, friendly, and concise. If you don't know something, admit it honestly."""
        }

        base_prompt = domain_prompts.get(domain, domain_prompts['general'])

        # Add language note
        language_note = f"\n\nRespond in {language} language if it's not English."
        if language == 'en':
            language_note = ""

        return base_prompt + language_note

    def is_api_available(self) -> bool:
        """Check if API is available."""
        return self.use_api


# Domain-specific FAQ for improved local responses
LOCAL_FAQ = {
    'college': {
        'admission requirements': 'You typically need completed high school transcripts, standardized test scores (SAT/ACT), letters of recommendation, and a personal statement.',
        'application deadline': 'Application deadlines vary by program. Regular decision is typically January-March. Early decision may be available in November.',
        'tuition cost': 'Tuition varies by program. In-state students typically pay less. Contact the financial aid office for specific costs and available scholarships.',
        'campus housing': 'Most colleges offer dormitories for first-year students. Apply early as spaces are limited. Off-campus housing is also available.',
    },
    'health': {
        'how to reduce fever': 'Rest, stay hydrated, and consider over-the-counter fever reducers like acetaminophen or ibuprofen. Consult a doctor if fever persists beyond 3 days.',
        'headache relief': 'Try resting in a quiet, dark room, staying hydrated, and taking OTC pain relievers. See a doctor for severe or persistent headaches.',
        'stress management': 'Practice deep breathing, meditation, regular exercise, and maintain work-life balance. Consider counseling if stress affects daily life.',
    },
    'helpdesk': {
        'forgot password': 'Click "Forgot Password" on the login page. A reset link will be sent to your registered email. Contact IT if you don\'t receive it.',
        'slow computer': 'Try restarting, closing unused programs, checking for malware, and ensuring adequate free disk space. Consider adding more RAM if it\'s an older system.',
        'printer not working': 'Check connections, ensure printer is powered on, verify it\'s set as default, and try restarting both printer and computer.',
    }
}
