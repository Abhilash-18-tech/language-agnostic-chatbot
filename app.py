"""Flask Web Application for the Chatbot."""

from flask import Flask, render_template, request, jsonify
from chatbot import Chatbot
from config import Config
import os

app = Flask(__name__)

# Get API key from environment or use None (falls back to local responses)
API_KEY = os.environ.get('GEMINI_API_KEY')

# Global chatbot instance
chatbot = Chatbot(domain=Config.DEFAULT_DOMAIN, api_key=API_KEY)


@app.route('/')
def index():
    """Render the main chat interface."""
    return render_template('index.html',
                           languages=Config.SUPPORTED_LANGUAGES,
                           domains=Config.DOMAINS,
                           default_language=Config.DEFAULT_LANGUAGE,
                           default_domain=Config.DEFAULT_DOMAIN,
                           api_available=chatbot.is_api_available())


@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages."""
    data = request.get_json()
    user_input = data.get('message', '')

    if not user_input.strip():
        return jsonify({
            'error': 'Empty message',
            'response': 'Please enter a message.'
        })

    result = chatbot.get_response(user_input)
    return jsonify(result)


@app.route('/api/domain', methods=['POST'])
def set_domain():
    """Change the chatbot domain."""
    data = request.get_json()
    domain = data.get('domain', Config.DEFAULT_DOMAIN)

    if domain in Config.DOMAINS:
        chatbot.set_domain(domain)
        return jsonify({'success': True, 'domain': domain})

    return jsonify({'success': False, 'error': 'Invalid domain'}), 400


@app.route('/api/language', methods=['POST'])
def set_language():
    """Manually set the response language."""
    data = request.get_json()
    language = data.get('language', Config.DEFAULT_LANGUAGE)

    chatbot.set_language(language)
    return jsonify({'success': True, 'language': language})


@app.route('/api/api-key', methods=['POST'])
def set_api_key():
    """Set Google Gemini API key."""
    data = request.get_json()
    api_key = data.get('api_key', '')

    if api_key.strip():
        chatbot.set_api_key(api_key.strip())
        if chatbot.is_api_available():
            return jsonify({'success': True, 'message': 'AI API enabled'})
        else:
            return jsonify({'success': False, 'message': 'Failed to initialize API'})

    return jsonify({'success': False, 'message': 'Empty API key'}), 400


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get conversation history."""
    history = chatbot.get_history()
    return jsonify({'history': history})


@app.route('/api/history', methods=['DELETE'])
def clear_history():
    """Clear conversation history."""
    chatbot.clear_history()
    return jsonify({'success': True})


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get chatbot status."""
    status = chatbot.get_status()
    return jsonify(status)


if __name__ == '__main__':
    os.system('chcp 65001 > nul')  # Set UTF-8 codepage
    print("=" * 50)
    print("[AI Chatbot] Language-Agnostic AI Chatbot")
    print("=" * 50)
    print(f"Domain: {Config.DEFAULT_DOMAIN}")
    print(f"Supported Languages: {len(Config.SUPPORTED_LANGUAGES)}")
    print(f"AI API Available: {chatbot.is_api_available()}")
    if not chatbot.is_api_available():
        print("\n[INFO] No API key found. Running in local mode.")
        print("To enable AI responses, set GEMINI_API_KEY environment variable")
        print("or enter your API key in the chat interface.")
        print("\nGet a free API key at: https://aistudio.google.com/app/apikey")
    print("=" * 50)
    print("Starting server at http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
