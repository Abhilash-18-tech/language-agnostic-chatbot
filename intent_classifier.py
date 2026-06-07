"""NLP Processing and Intent Classification module - Enhanced version."""

from config import Config
import re
from difflib import SequenceMatcher


class IntentClassifier:
    """Classifies user intent using keyword matching, word overlap, and fuzzy matching."""

    def __init__(self, domain: str = Config.DEFAULT_DOMAIN):
        self.domain = domain
        self.intents = {}
        self._load_domain_intents()

    def _load_domain_intents(self):
        """Load intents for the specified domain."""
        self.intents = DOMAIN_INTENTS.get(self.domain, DOMAIN_INTENTS['general'])

    def set_domain(self, domain: str):
        """Change the chatbot domain."""
        self.domain = domain
        self._load_domain_intents()

    def _tokenize(self, text: str) -> set:
        """Simple tokenization - split on whitespace and punctuation."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        words = set(text.split())
        # Remove very short words
        return {w for w in words if len(w) > 2}

    def _fuzzy_match(self, text: str, pattern: str) -> float:
        """Calculate fuzzy similarity ratio between text and pattern."""
        text_lower = text.lower()
        pattern_lower = pattern.lower()

        # Check if pattern is contained in text
        if pattern_lower in text_lower:
            return 1.0

        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, text_lower, pattern_lower).ratio()

    def _calculate_overlap(self, text: str, pattern: str) -> float:
        """Calculate word overlap ratio between text and pattern."""
        text_tokens = self._tokenize(text)
        pattern_tokens = self._tokenize(pattern)

        if not pattern_tokens:
            return 0.0

        matches = len(text_tokens & pattern_tokens)

        # Also check for partial matches (word contains another word)
        for t_token in text_tokens:
            for p_token in pattern_tokens:
                if p_token in t_token or t_token in p_token:
                    matches += 0.5

        return matches / len(pattern_tokens)

    def _get_keyword_score(self, text: str, keywords: list) -> tuple:
        """Score text based on keyword matches. Returns (score, matched_keywords)."""
        text_lower = text.lower()
        matched = []

        for keyword in keywords:
            keyword_lower = keyword.lower()
            # Check for exact word or phrase match
            if keyword_lower in text_lower:
                matched.append(keyword)
            # Check for word stem match
            elif len(keyword) > 4:
                stem = keyword[:4]
                if stem in text_lower:
                    matched.append(keyword)

        if not matched:
            return 0.0, []

        # Score based on number of matched keywords
        score = len(matched) / len(keywords)
        return min(score + 0.3, 1.0), matched

    def classify(self, text: str) -> dict:
        """
        Classify user input and return intent with confidence.

        Uses a three-tier approach:
        1. Exact pattern/keyword matching (high confidence)
        2. Fuzzy string matching (medium-high confidence)
        3. Word overlap scoring (medium confidence)

        Args:
            text: User input text (in English)

        Returns:
            Dict with intent, confidence, matched_pattern, and method
        """
        text_lower = text.lower()
        best_intent = None
        best_confidence = 0.0
        best_pattern = None
        best_method = 'fallback'
        best_matched_keywords = []

        # Tier 1: Check for direct keyword matches with scoring
        for intent_name, intent_data in self.intents.items():
            patterns = intent_data.get('patterns', [])
            score, matched = self._get_keyword_score(text, patterns)

            if score > best_confidence:
                best_confidence = score
                best_intent = intent_name
                best_pattern = matched[0] if matched else None
                best_matched_keywords = matched
                best_method = 'keyword_score'

            # Check for exact phrase match (highest priority)
            for pattern in patterns:
                if pattern.lower() in text_lower:
                    return {
                        'intent': intent_name,
                        'confidence': 0.95,
                        'matched_pattern': pattern,
                        'method': 'exact_match',
                        'matched_keywords': [pattern]
                    }

        # Tier 2: Fuzzy matching
        if best_confidence < 0.7:
            for intent_name, intent_data in self.intents.items():
                for pattern in intent_data.get('patterns', []):
                    fuzzy_score = self._fuzzy_match(text, pattern)

                    # Boost if significant words match
                    if fuzzy_score > 0.6:
                        fuzzy_score += 0.1

                    if fuzzy_score > best_confidence:
                        best_confidence = fuzzy_score
                        best_intent = intent_name
                        best_pattern = pattern
                        best_method = 'fuzzy_match'

        # Tier 3: Word overlap (already checked in keyword score)
        if best_confidence < 0.5:
            for intent_name, intent_data in self.intents.items():
                for pattern in intent_data.get('patterns', []):
                    overlap = self._calculate_overlap(text, pattern)

                    if overlap > best_confidence:
                        best_confidence = overlap
                        best_intent = intent_name
                        best_pattern = pattern
                        best_method = 'word_overlap'

        # Apply confidence adjustments
        if best_method == 'exact_match':
            final_confidence = 0.95
        elif best_method == 'keyword_score':
            final_confidence = min(best_confidence + 0.1, 0.90)
        elif best_method == 'fuzzy_match':
            final_confidence = min(best_confidence, 0.80)
        elif best_method == 'word_overlap':
            final_confidence = min(best_confidence + 0.15, 0.75)
        else:
            final_confidence = 0.0

        # Return if above threshold
        if final_confidence >= Config.CONFIDENCE_THRESHOLD:
            return {
                'intent': best_intent,
                'confidence': round(final_confidence, 2),
                'matched_pattern': best_pattern,
                'method': best_method,
                'matched_keywords': best_matched_keywords
            }

        # Default fallback
        return {
            'intent': 'unknown',
            'confidence': 0.0,
            'matched_pattern': None,
            'method': 'fallback',
            'matched_keywords': []
        }


# Domain-specific intents and patterns - EXPANDED
DOMAIN_INTENTS = {
    'general': {
        'greeting': {
            'patterns': [
                'hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening',
                'how are you', 'whats up', 'whatsapp', 'yo', 'greetings', 'sup',
                'how is it going', 'how do you do', 'nice to meet you', 'whats new'
            ],
            'responses': [
                'Hello! How can I help you today?',
                'Hi there! What can I do for you?',
                'Hey! Feel free to ask me anything.',
                'Greetings! I am ready to assist you.',
                'Hello! What would you like to know?'
            ]
        },
        'goodbye': {
            'patterns': [
                'bye', 'goodbye', 'see you', 'exit', 'quit', 'farewell',
                'take care', 'later', 'catch you later', 'have a good day',
                'im leaving', 'gotta go', 'talk to you later', 'ttyl'
            ],
            'responses': [
                'Goodbye! Have a great day!',
                'See you later!',
                'Bye! Feel free to come back anytime.',
                'Take care! Come back soon!',
                'Farewell! It was nice chatting with you.'
            ]
        },
        'thanks': {
            'patterns': [
                'thank you', 'thanks', 'appreciate', 'helpful', 'very helpful',
                'thanks a lot', 'thank you so much', 'i appreciate it', 'much appreciated',
                'you helped me', 'that helped', 'great help'
            ],
            'responses': [
                'You\'re welcome! Happy to help.',
                'No problem at all!',
                'Glad I could help!',
                'Anytime! That\'s what I\'m here for.',
                'My pleasure! Don\'t hesitate to ask more questions.'
            ]
        },
        'help': {
            'patterns': [
                'help', 'what can you do', 'how to use', 'support', 'assist',
                'what are you', 'who are you', 'what is this', 'how does this work',
                'tell me about yourself', 'your capabilities', 'features'
            ],
            'responses': [
                'I can help you with general questions. Just ask me anything!',
                'I\'m here to assist. What would you like to know?',
                'I\'m a multilingual chatbot that can answer questions in many languages!',
                'Ask me anything! I support multiple languages and domains.',
                'I can help with various topics. Select a domain to specialize my responses.'
            ]
        },
        'joke': {
            'patterns': [
                'joke', 'funny', 'laugh', 'humor', 'make me laugh', 'tell me a joke',
                'something funny', 'comedy', 'hilarious', 'lol'
            ],
            'responses': [
                'Why do programmers prefer dark mode? Because light attracts bugs!',
                'Why did the scarecrow win an award? He was outstanding in his field!',
                'What do you call a fake noodle? An impasta!',
                'Why don\'t scientists trust atoms? Because they make up everything!',
                'I\'m great at jokes, but my humor is sometimes too artificial!'
            ]
        },
        'unknown': {
            'patterns': [],
            'responses': [
                'I\'m not sure I understand. Could you rephrase that?',
                'I didn\'t quite get that. Can you ask in a different way?',
                'I\'m still learning. Could you clarify your question?',
                'Hmm, I\'m not certain about that. Could you try asking differently?',
                'I want to help! Can you rephrase your question?'
            ]
        }
    },

    'college': {
        'greeting': {
            'patterns': ['hello', 'hi', 'hey', 'good morning', 'good afternoon'],
            'responses': [
                'Hello! Welcome to the college assistant. How can I help?',
                'Hi! I\'m here to help with college-related questions.',
                'Greetings! Ask me about admissions, courses, exams, and more!'
            ]
        },
        'admission': {
            'patterns': [
                'admission', 'apply', 'enroll', 'registration', 'how to join',
                'admissions process', 'application process', 'how to apply', 'enrollment',
                'joining procedure', 'admission requirements', 'eligibility', 'criteria',
                'when do applications open', 'application deadline', 'admission form'
            ],
            'responses': [
                'For admissions, visit our website or contact the admissions office at admissions@college.edu.',
                'Applications are open from January to March. You can apply online through our portal.',
                'You need to submit your transcripts, test scores, and application form.',
                'Admission requirements vary by program. Generally, you need completed high school transcripts and test scores.',
                'The application process takes 2-4 weeks. You\'ll be notified via email about your status.'
            ]
        },
        'courses': {
            'patterns': [
                'courses', 'classes', 'subjects', 'majors', 'degree', 'program',
                'what courses', 'available courses', 'course list', 'curriculum',
                'specialization', 'concentration', 'what can i study', 'programs offered'
            ],
            'responses': [
                'We offer various programs in Engineering, Arts, Science, and Business.',
                'Check our course catalog on the student portal for available classes.',
                'Popular majors include Computer Science, Business Administration, and Psychology.',
                'Our programs include B.Tech, MBA, M.Sc, and various certificate courses.',
                'You can view the complete course list with descriptions on our academic portal.'
            ]
        },
        'fees': {
            'patterns': [
                'fee', 'tuition', 'cost', 'payment', 'scholarship', 'financial aid',
                'how much', 'expensive', 'afford', 'loan', 'bursary', 'grant',
                'fee structure', 'tuition fees', 'payment plan', 'installments'
            ],
            'responses': [
                'Tuition fees vary by program. Contact the finance office for details.',
                'Scholarships are available based on merit and need. Apply through the student portal.',
                'Payment plans are available. Visit the finance office for more information.',
                'Financial aid is available for eligible students. Fill out the FAFSA form.',
                'We offer merit scholarships up to 50% and need-based aid for qualifying students.'
            ]
        },
        'exam': {
            'patterns': [
                'exam', 'test', 'quiz', 'assignment', 'deadline', 'midterm', 'final',
                'exam schedule', 'test date', 'when is the exam', 'exam preparation',
                'assignment due', 'submission deadline', 'exam results', 'grades'
            ],
            'responses': [
                'Check your course syllabus for exam dates and assignment deadlines.',
                'Midterms are in October and finals in December.',
                'You can view your exam schedule on the student portal.',
                'Assignment submissions are typically due at 11:59 PM on the specified date.',
                'Exam results are usually released within 2 weeks of the exam date.'
            ]
        },
        'library': {
            'patterns': [
                'library', 'book', 'borrow', 'study room', 'librarian', 'catalog',
                'reserve book', 'return book', 'library hours', 'study space',
                'research papers', 'journals', 'dissertation', 'thesis'
            ],
            'responses': [
                'The library is open 24/7 during exam season.',
                'You can borrow up to 5 books for 2 weeks.',
                'Study rooms can be reserved online through the library portal.',
                'The library has over 100,000 books and access to millions of digital resources.',
                'Librarians are available for research help Monday through Friday, 9 AM to 5 PM.'
            ]
        },
        'campus': {
            'patterns': [
                'campus', 'hostel', 'dormitory', 'housing', 'cafeteria', 'food',
                'student life', 'clubs', 'sports', 'gym', 'facilities', 'parking',
                'where do i live', 'accommodation', 'residence', 'dining'
            ],
            'responses': [
                'Campus housing is available for all students. Apply early as spaces are limited.',
                'The cafeteria serves meals from 7 AM to 10 PM on weekdays.',
                'We have over 50 student clubs and organizations you can join.',
                'The campus gym is free for all enrolled students with ID.',
                'Parking permits are required for all vehicles on campus. Apply online.'
            ]
        },
        'unknown': {
            'patterns': [],
            'responses': [
                'I\'m not sure about that college-related question. Try contacting the admin office.',
                'Could you rephrase? I can help with admissions, courses, fees, exams, and campus info.',
                'For specific questions, contact the relevant department. I can help with general college queries.'
            ]
        }
    },

    'health': {
        'greeting': {
            'patterns': ['hello', 'hi', 'hey', 'feeling sick', 'not well', 'need help'],
            'responses': [
                'Hello! I\'m here to provide general health information. How can I help?',
                'Hi! Remember, I provide information, not medical advice. What\'s on your mind?',
                'Hello! How are you feeling today? I can provide general health information.'
            ]
        },
        'symptom': {
            'patterns': [
                'headache', 'fever', 'cough', 'pain', 'tired', 'nausea', 'symptom',
                'sore throat', 'cold', 'flu', 'stomach ache', 'back pain', 'dizzy',
                'vomiting', 'diarrhea', 'rash', 'allergy', 'sneezing', 'congestion',
                'fatigue', 'weak', 'aches', 'chills', 'shortness of breath'
            ],
            'responses': [
                'For persistent symptoms, please consult a healthcare professional.',
                'Common remedies include rest, hydration, and over-the-counter medications.',
                'If symptoms worsen or persist beyond a few days, see a doctor.',
                'Monitor your symptoms and keep track of when they started. This helps your doctor.',
                'Stay hydrated and get plenty of rest. Most minor illnesses resolve on their own.'
            ]
        },
        'medicine': {
            'patterns': [
                'medicine', 'medication', 'pill', 'dosage', 'prescription', 'drug',
                'pharmacy', 'antibiotics', 'painkiller', 'tablet', 'capsule', 'syrup',
                'side effects', 'drug interaction', 'how to take', 'when to take'
            ],
            'responses': [
                'Always follow your doctor\'s prescription for medications.',
                'Take medications as directed on the label or by your healthcare provider.',
                'Consult a pharmacist for information about drug interactions.',
                'Never share prescription medications with others.',
                'If you experience side effects, contact your healthcare provider immediately.'
            ]
        },
        'diet': {
            'patterns': [
                'diet', 'food', 'nutrition', 'eat', 'healthy', 'weight', 'calories',
                'protein', 'carbs', 'vitamins', 'minerals', 'meal', 'recipe',
                'lose weight', 'gain weight', 'balanced diet', 'what should i eat'
            ],
            'responses': [
                'A balanced diet includes fruits, vegetables, proteins, and whole grains.',
                'Stay hydrated by drinking 8 glasses of water daily.',
                'Limit processed foods and sugar for better health.',
                'Aim for 5 servings of fruits and vegetables per day.',
                'Consult a nutritionist for personalized diet recommendations.'
            ]
        },
        'exercise': {
            'patterns': [
                'exercise', 'workout', 'fitness', 'gym', 'running', 'yoga',
                'physical activity', 'stretching', 'cardio', 'strength training',
                'how to exercise', 'workout routine', 'stay active'
            ],
            'responses': [
                'Aim for at least 30 minutes of moderate exercise daily.',
                'Combine cardio and strength training for best results.',
                'Start slow and gradually increase intensity to avoid injury.',
                'Even walking 30 minutes a day has significant health benefits.',
                'Find activities you enjoy - exercise should be sustainable and fun!'
            ]
        },
        'mental_health': {
            'patterns': [
                'stress', 'anxiety', 'depression', 'sad', 'worried', 'overwhelmed',
                'mental health', 'therapy', 'counseling', 'panic', 'mood',
                'cant sleep', 'insomnia', 'feeling down', 'hopeless', 'lonely'
            ],
            'responses': [
                'Mental health is just as important as physical health. Consider speaking with a counselor.',
                'Stress management techniques include deep breathing, meditation, and exercise.',
                'If you\'re feeling overwhelmed, talking to a therapist can help significantly.',
                'Many people benefit from counseling. It\'s a sign of strength to seek help.',
                'For immediate crisis support, contact a mental health helpline in your area.'
            ]
        },
        'emergency': {
            'patterns': [
                'emergency', 'urgent', 'severe', 'chest pain', 'bleeding', 'unconscious',
                'can\'t breathe', 'heart attack', 'stroke', 'broken bone', 'poison',
                'suicide', 'overdose', 'critical', 'life threatening', 'ambulance'
            ],
            'responses': [
                '⚠️ This sounds serious. Please call emergency services immediately!',
                'For medical emergencies, call your local emergency number right away.',
                'Don\'t wait - seek immediate medical attention for severe symptoms.',
                'EMERGENCY: Call 911 (or your local emergency number) immediately!',
                'This requires immediate medical attention. Do not delay - call for help now!'
            ]
        },
        'doctor': {
            'patterns': [
                'doctor', 'physician', 'specialist', 'appointment', 'clinic', 'hospital',
                'see a doctor', 'medical checkup', 'consultation', 'referral',
                'where to find', 'best doctor', 'recommend a doctor', 'healthcare provider'
            ],
            'responses': [
                'Regular checkups are important. Schedule an annual physical with your doctor.',
                'For specialists, ask your primary care physician for a referral.',
                'Many clinics offer same-day appointments for urgent issues.',
                'Check if your insurance requires a referral before seeing specialists.',
                'Telemedicine appointments are available for many non-emergency conditions.'
            ]
        },
        'unknown': {
            'patterns': [],
            'responses': [
                'I\'m not a doctor. For medical advice, please consult a healthcare professional.',
                'I can provide general health information, but for specific concerns, see a doctor.',
                'For personalized medical advice, please consult with a qualified healthcare provider.',
                'Health information I provide is general. Your doctor can give specific advice for your situation.'
            ]
        }
    },

    'helpdesk': {
        'greeting': {
            'patterns': ['hello', 'hi', 'hey', 'support', 'help', 'it help'],
            'responses': [
                'Hello! Welcome to IT support. How can I assist you today?',
                'Hi! I\'m here to help with your technical issues.',
                'IT Support here! What technical problem can I help you solve?'
            ]
        },
        'password': {
            'patterns': [
                'password', 'reset', 'forgot password', 'login', 'account', 'locked out',
                'cant login', 'change password', 'new password', 'password not working',
                'account locked', 'username', 'credentials', 'authentication', 'sign in'
            ],
            'responses': [
                'To reset your password, go to the login page and click "Forgot Password".',
                'Password reset link will be sent to your registered email.',
                'Contact IT support if you\'re locked out of your account.',
                'Make sure Caps Lock is off when entering your password.',
                'For security, passwords must be changed every 90 days.'
            ]
        },
        'internet': {
            'patterns': [
                'internet', 'wifi', 'connection', 'network', 'offline', 'disconnect',
                'slow internet', 'no connection', 'cant connect', 'network error',
                'wireless', 'ethernet', 'router', 'modem', 'dns', 'ip address'
            ],
            'responses': [
                'Try restarting your router and device first.',
                'Check if other devices can connect to the network.',
                'Run the network troubleshooter in your system settings.',
                'Forget the network and reconnect. Sometimes this fixes connection issues.',
                'Check if airplane mode is accidentally turned on.'
            ]
        },
        'software': {
            'patterns': [
                'software', 'install', 'update', 'download', 'application', 'program',
                'app', 'crash', 'not working', 'error', 'license', 'activation',
                'compatible', 'version', 'upgrade', 'reinstall'
            ],
            'responses': [
                'Download software only from official sources.',
                'Check system requirements before installing new software.',
                'Keep your applications updated for security.',
                'Try running the program as administrator if you\'re having permission issues.',
                'Uninstall and reinstall the software if it\'s crashing frequently.'
            ]
        },
        'hardware': {
            'patterns': [
                'printer', 'scanner', 'monitor', 'keyboard', 'mouse', 'hardware',
                'not working', 'broken', 'damaged', 'replacement', 'peripheral',
                'usb', 'bluetooth', 'display', 'screen', 'speakers', 'microphone',
                'webcam', 'camera', 'headphones', 'external drive'
            ],
            'responses': [
                'Try reconnecting the device and restarting your computer.',
                'Check if the device drivers are up to date.',
                'For hardware issues, contact the IT helpdesk for assistance.',
                'Try a different USB port if the device isn\'t being recognized.',
                'Check Device Manager to see if the hardware is detected by the system.'
            ]
        },
        'email': {
            'patterns': [
                'email', 'outlook', 'mail', 'sending', 'receiving', 'inbox',
                'spam', 'attachment', 'compose', 'forward', 'reply', 'signature',
                'cant send email', 'email not working', 'mailbox full', 'bounce'
            ],
            'responses': [
                'Check your internet connection if emails aren\'t sending.',
                'Verify your email settings and server configuration.',
                'Clear your email cache if the app is running slowly.',
                'Check your spam folder if you\'re missing expected emails.',
                'Large attachments may fail to send. Try using cloud storage links instead.'
            ]
        },
        'security': {
            'patterns': [
                'virus', 'malware', 'antivirus', 'security', 'hack', 'phishing',
                'suspicious', 'unsafe', 'firewall', 'infected', 'trojan',
                'ransomware', 'spyware', 'scan', 'quarantine', 'threat'
            ],
            'responses': [
                'Run a full antivirus scan if you suspect malware.',
                'Don\'t click on suspicious links or download attachments from unknown senders.',
                'Keep your antivirus software updated for best protection.',
                'If you suspect a security breach, disconnect from the network and contact IT immediately.',
                'Enable two-factor authentication for additional security.'
            ]
        },
        'backup': {
            'patterns': [
                'backup', 'restore', 'recover', 'lost data', 'deleted', 'file recovery',
                'cloud storage', 'onedrive', 'google drive', 'dropbox', 'sync'
            ],
            'responses': [
                'Regular backups prevent data loss. Set up automatic backups today.',
                'Check your cloud storage for automatically synced files.',
                'For file recovery, check the Recycle Bin first.',
                'Use version history in cloud services to recover previous versions of files.',
                'Contact IT for assistance with data recovery from backup systems.'
            ]
        },
        'unknown': {
            'patterns': [],
            'responses': [
                'I\'m not sure about that issue. Please contact IT support at support@company.com.',
                'For complex technical issues, please submit a ticket to the helpdesk.',
                'This might require hands-on assistance. Please create a support ticket.',
                'I can help with common IT issues. For specialized problems, contact the helpdesk.'
            ]
        }
    }
}
