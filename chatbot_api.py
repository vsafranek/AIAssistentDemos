"""Flask API pro webpage chatbot"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from webpage_assistant import WebpageAssistant
from webpage_content import WEBPAGE_CONTENT

app = Flask(__name__)
CORS(app)  # Povolit CORS pro všechny domény

# Globální instance asistenta
assistant = WebpageAssistant(WEBPAGE_CONTENT)

@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint pro chat zprávy"""
    try:
        data = request.json
        user_message = data.get('message', '')

        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        # Získání odpovědi od asistenta
        response = assistant.chat(user_message)

        return jsonify({
            'response': response,
            'status': 'success'
        })

    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500


@app.route('/api/init', methods=['GET'])
def init_chat():
    """Endpoint pro inicializaci chatu"""
    try:
        # Reset a nový start
        assistant.reset()
        greeting = assistant.start_conversation()

        return jsonify({
            'greeting': greeting,
            'status': 'success'
        })

    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500


@app.route('/api/reset', methods=['POST'])
def reset_chat():
    """Endpoint pro reset konverzace"""
    try:
        assistant.reset()
        greeting = assistant.start_conversation()

        return jsonify({
            'greeting': greeting,
            'status': 'success'
        })

    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
