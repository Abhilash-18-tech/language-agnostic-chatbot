// Chatbot Frontend JavaScript with Voice Support and AI API

document.addEventListener('DOMContentLoaded', function() {
    const chatContainer = document.getElementById('chat-container');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const domainSelect = document.getElementById('domain-select');
    const languageSelect = document.getElementById('language-select');
    const clearBtn = document.getElementById('clear-btn');
    const statusDomain = document.getElementById('status-domain');
    const statusLanguage = document.getElementById('status-language');
    const statusConfidence = document.getElementById('status-confidence');
    const currentDomain = document.getElementById('current-domain');
    const voiceToggle = document.getElementById('voice-toggle');
    const voiceIcon = document.getElementById('voice-icon');
    const voiceStatus = document.getElementById('voice-status');

    // API Modal elements
    const apiModal = document.getElementById('api-modal');
    const apiKeyBtn = document.getElementById('api-key-btn');
    const modalClose = document.getElementById('modal-close');
    const apiKeySave = document.getElementById('api-key-save');
    const apiKeyClear = document.getElementById('api-key-clear');
    const apiKeyInput = document.getElementById('api-key-input');
    const apiStatus = document.getElementById('api-status');

    let autoDetect = true;
    let isListening = false;
    let isSpeaking = false;
    let recognition = null;
    let synth = window.speechSynthesis;
    let currentVoice = null;

    // Initialize Speech Recognition
    function initSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (SpeechRecognition) {
            recognition = new SpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = true;
            recognition.lang = 'en-US';

            recognition.onstart = function() {
                isListening = true;
                voiceIcon.textContent = '🔴';
                voiceStatus.textContent = 'Listening...';
                voiceStatus.style.color = '#e74c3c';
            };

            recognition.onresult = function(event) {
                const transcript = Array.from(event.results)
                    .map(result => result[0].transcript)
                    .join('');
                userInput.value = transcript;
            };

            recognition.onend = function() {
                isListening = false;
                voiceIcon.textContent = '🎤';
                voiceStatus.textContent = 'Voice ready';
                voiceStatus.style.color = '#27ae60';

                // Auto-send if there's content
                if (userInput.value.trim()) {
                    sendMessage();
                }
            };

            recognition.onerror = function(event) {
                isListening = false;
                voiceIcon.textContent = '🎤';
                voiceStatus.textContent = 'Voice error: ' + event.error;
                voiceStatus.style.color = '#e74c3c';
                console.error('Speech recognition error:', event.error);
            };
        } else {
            voiceToggle.style.display = 'none';
            voiceStatus.textContent = 'Voice not supported';
            voiceStatus.style.color = '#95a5a6';
        }
    }

    // Text-to-Speech
    function speak(text, lang) {
        if (!synth) return;

        // Cancel any ongoing speech
        synth.cancel();

        const utterance = new SpeechSynthesisUtterance(text);

        // Set language
        const langMap = {
            'en': 'en-US',
            'es': 'es-ES',
            'fr': 'fr-FR',
            'de': 'de-DE',
            'it': 'it-IT',
            'pt': 'pt-BR',
            'ru': 'ru-RU',
            'zh-cn': 'zh-CN',
            'ja': 'ja-JP',
            'ko': 'ko-KR',
            'hi': 'hi-IN',
            'ar': 'ar-SA',
            'ta': 'ta-IN',
            'te': 'te-IN',
            'bn': 'bn-IN'
        };
        utterance.lang = langMap[lang] || 'en-US';

        // Try to find a suitable voice
        const voices = synth.getVoices();
        const preferredVoice = voices.find(voice =>
            voice.lang.startsWith(langMap[lang]?.split('-')[0] || 'en')
        );
        if (preferredVoice) {
            utterance.voice = preferredVoice;
        }

        // Adjust speech rate
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;

        utterance.onstart = function() {
            isSpeaking = true;
        };

        utterance.onend = function() {
            isSpeaking = false;
        };

        utterance.onerror = function(event) {
            isSpeaking = false;
            console.error('Speech synthesis error:', event);
        };

        synth.speak(utterance);
    }

    // Load voices when available
    if (synth) {
        synth.onvoiceschanged = function() {
            synth.getVoices();
        };
    }

    // Send message function
    function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;

        // Add user message to chat
        addMessage(message, 'user');
        userInput.value = '';

        // Show typing indicator
        showTypingIndicator();

        // Send to API
        fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            removeTypingIndicator();

            if (data.error) {
                addMessage(data.response, 'assistant');
            } else {
                addMessage(data.response, 'assistant', {
                    confidence: data.confidence,
                    intent: data.intent,
                    language: data.detected_language,
                    source: data.source
                });
                updateStatus(data);

                // Speak the response if voice is enabled
                if (isListening || voiceToggle.classList.contains('active')) {
                    speak(data.response, data.detected_language || 'en');
                }
            }
        })
        .catch(error => {
            removeTypingIndicator();
            addMessage('Error: Could not connect to server.', 'assistant');
            console.error('Error:', error);
        });
    }

    // Add message to chat UI
    function addMessage(content, role, meta = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;

        messageDiv.appendChild(contentDiv);

        // Add speak button for assistant messages
        if (role === 'assistant') {
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'message-actions';

            const speakBtn = document.createElement('button');
            speakBtn.className = 'btn-speak';
            speakBtn.innerHTML = '🔊';
            speakBtn.title = 'Read aloud';
            speakBtn.onclick = function() {
                speak(content, 'en');
            };

            actionsDiv.appendChild(speakBtn);
            messageDiv.appendChild(actionsDiv);
        }

        if (meta) {
            const metaDiv = document.createElement('div');
            metaDiv.className = 'message-meta';

            let metaText = '';
            if (meta.source) {
                metaText += meta.source === 'gemini' ? '🤖 AI ' : '📝 Local ';
            }
            if (meta.confidence !== undefined) {
                metaText += `Confidence: ${(meta.confidence * 100).toFixed(0)}%`;
            }
            if (meta.intent) {
                metaText += ` • Intent: ${meta.intent}`;
            }
            if (meta.language) {
                metaText += ` • Language: ${meta.language.toUpperCase()}`;
            }

            metaDiv.textContent = metaText;
            messageDiv.appendChild(metaDiv);
        }

        // Remove welcome message if present
        const welcomeMsg = chatContainer.querySelector('.welcome-message');
        if (welcomeMsg) {
            welcomeMsg.remove();
        }

        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Show typing indicator
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant';
        typingDiv.id = 'typing-indicator';

        const indicatorDiv = document.createElement('div');
        indicatorDiv.className = 'typing-indicator';
        indicatorDiv.innerHTML = '<span></span><span></span><span></span>';

        typingDiv.appendChild(indicatorDiv);
        chatContainer.appendChild(typingDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Remove typing indicator
    function removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    // Update status bar
    function updateStatus(data) {
        statusDomain.textContent = `Domain: ${data.domain}`;
        statusLanguage.textContent = `Language: ${data.detected_language?.toUpperCase() || 'Auto'}`;

        // Update confidence badge
        const confidence = data.confidence;
        statusConfidence.textContent = `Confidence: ${(confidence * 100).toFixed(0)}%`;
        statusConfidence.className = 'confidence-badge';

        if (confidence >= 0.8) {
            statusConfidence.classList.add('high');
        } else if (confidence >= 0.6) {
            statusConfidence.classList.add('medium');
        } else {
            statusConfidence.classList.add('low');
        }
    }

    // API Modal functions
    function openApiModal() {
        apiModal.classList.add('show');
        apiKeyInput.focus();
    }

    function closeApiModal() {
        apiModal.classList.remove('show');
        apiKeyInput.value = '';
    }

    function saveApiKey() {
        const apiKey = apiKeyInput.value.trim();
        if (!apiKey) {
            alert('Please enter an API key');
            return;
        }

        fetch('/api/api-key', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: apiKey })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('AI API enabled successfully!');
                closeApiModal();
                // Update status
                apiStatus.innerHTML = '<span class="status-dot green"></span> AI Mode: Active';
            } else {
                alert('Failed to enable API: ' + (data.message || 'Unknown error'));
            }
        })
        .catch(error => {
            alert('Error: ' + error);
        });
    }

    function clearApiKey() {
        fetch('/api/api-key', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: '' })
        })
        .then(response => response.json())
        .then(data => {
            alert('API key removed. Running in local mode.');
            closeApiModal();
            // Update status
            apiStatus.innerHTML = '<span class="status-dot orange"></span> AI Mode: Local';
        })
        .catch(error => {
            alert('Error: ' + error);
        });
    }

    // API Modal event listeners
    apiKeyBtn.addEventListener('click', openApiModal);
    modalClose.addEventListener('click', closeApiModal);
    apiKeySave.addEventListener('click', saveApiKey);
    apiKeyClear.addEventListener('click', clearApiKey);

    // Close modal when clicking outside
    apiModal.addEventListener('click', function(e) {
        if (e.target === apiModal) {
            closeApiModal();
        }
    });

    // Save API key on Enter
    apiKeyInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            saveApiKey();
        }
    });

    // Event listeners
    sendBtn.addEventListener('click', sendMessage);

    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Voice toggle
    voiceToggle.addEventListener('click', function() {
        if (!recognition) {
            alert('Speech recognition is not supported in your browser. Try Chrome or Edge.');
            return;
        }

        if (isListening) {
            recognition.stop();
            isListening = false;
            voiceToggle.classList.remove('active');
            voiceIcon.textContent = '🎤';
            voiceStatus.textContent = 'Voice ready';
            voiceStatus.style.color = '#27ae60';
        } else {
            recognition.start();
            voiceToggle.classList.add('active');
        }
    });

    // Domain change
    domainSelect.addEventListener('change', function() {
        const domain = this.value;
        fetch('/api/domain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ domain: domain })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                statusDomain.textContent = `Domain: ${domain}`;
                currentDomain.textContent = domain;
                addMessage(`Domain changed to ${domain}. How can I help?`, 'assistant');
            }
        });
    });

    // Language change
    languageSelect.addEventListener('change', function() {
        if (this.value === 'auto') {
            autoDetect = true;
            statusLanguage.textContent = 'Language: Auto';
        } else {
            autoDetect = false;
            const language = this.value;
            fetch('/api/language', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ language: language })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    statusLanguage.textContent = `Language: ${language.toUpperCase()}`;
                }
            });
        }
    });

    // Clear history
    clearBtn.addEventListener('click', function() {
        fetch('/api/history', { method: 'DELETE' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                chatContainer.innerHTML = `
                    <div class="welcome-message">
                        <h2>Welcome!</h2>
                        <p>I'm your language-agnostic AI assistant with voice support.</p>
                        <ul>
                            <li>I understand <strong>any language</strong></li>
                            <li>I specialize in <strong id="current-domain">${domainSelect.value}</strong> domain</li>
                            <li>I remember our conversation context</li>
                            <li>Click the microphone to <strong>speak</strong> your questions</li>
                            <li>Click the speaker icon to <strong>hear</strong> responses</li>
                        </ul>
                        <p class="api-note">
                            <em>For accurate AI-powered answers, click "API Key" and enter your Google Gemini API key.</em>
                            <br>Get a free key at: <a href="https://aistudio.google.com/app/apikey" target="_blank">aistudio.google.com/app/apikey</a>
                        </p>
                    </div>
                `;
                statusConfidence.textContent = 'Confidence: --';
                statusConfidence.className = 'confidence-badge';
            }
        });
    });

    // Initialize speech recognition
    initSpeechRecognition();

    // Focus input on load
    userInput.focus();
});
