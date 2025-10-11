"""
Flask GUI for Vocal Agent
A simple web interface for the voice-driven AI assistant
"""

from flask import Flask, render_template, jsonify, request
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def index():
    """Main page - Hello World for testing"""
    return render_template('index.html')

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Vocal Agent Frontend is running',
        'version': '1.0.0'
    })

@app.route('/api/process_voice', methods=['POST'])
def process_voice():
    """Endpoint for processing voice commands (placeholder)"""
    data = request.get_json()
    command = data.get('command', '')
    
    logger.info(f"Received voice command: {command}")
    
    # TODO: Connect to vocal_core_agent.py backend
    response = {
        'success': True,
        'message': f'Received command: {command}',
        'processed_command': command,
        'agent_response': 'Command processing placeholder - will connect to uAgents backend'
    }
    
    return jsonify(response)

if __name__ == '__main__':
    logger.info("Starting Vocal Agent Frontend...")
    app.run(debug=True, host='127.0.0.1', port=5001)