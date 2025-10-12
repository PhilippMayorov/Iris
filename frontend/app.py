"""
Flask GUI for Vocal Agent
A desktop application interface for the voice-driven AI assistant
"""

import os
# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GRPC_TRACE'] = ''

from flask import Flask, render_template, jsonify, request, redirect, url_for
import logging
import base64
import io
import re
from dotenv import load_dotenv
# Import will be handled later in the initialization section

# Load environment variables
load_dotenv()

# Configure logging first
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_gemini_connection():
    """
    Test connection to Gemini API to verify API key and service availability
    """
    if not genai:
        logger.warning("Gemini module not available")
        return False
    
    try:
        logger.info("Testing Gemini API connection...")
        
        # Use a valid model name
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Send a simple, safe test request
        test_prompt = "Hi, how are you doing?"
        
        # Configure safety settings to be less restrictive
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        ]
        
        response = model.generate_content(
            test_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0,
                # max_output_tokens=50
            ),
            # safety_settings=safety_settings,
            request_options={'timeout': 10}
        )
        
        logger.info(f"Gemini test response: {response}")
        logger.info(f"Gemini text response: {response.text}")

        # Better error handling for blocked responses
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'finish_reason'):
                logger.info(f"Response finish reason: {candidate.finish_reason}")
                
                if candidate.finish_reason == 2:  # SAFETY
                    logger.warning("⚠️ Response was blocked by safety filters")
                    return False
                elif candidate.finish_reason == 3:  # RECITATION  
                    logger.warning("⚠️ Response was blocked due to recitation")
                    return False
        
        if response and hasattr(response, 'text') and response.text:
            result_text = response.text.strip().lower()
            logger.info(f"Gemini test response: '{response.text.strip()}'")
            logger.info("✅ Gemini API connection successful")
            return True
        else:
            logger.error("❌ Gemini returned empty response")
            return False
            
    except Exception as e:
        logger.error(f"❌ Gemini connection test failed: {str(e)}")
        return False



# Refine user speech using Gemini API
def gemini_refinement(raw_speech):
    """
    Use Gemini API to refine user's speech into a clear, actionable command
    """
    if not raw_speech or not genai:
        logger.warning("No speech provided or Gemini not available")
        return raw_speech
    
    try:
        logger.info("Making Gemini API call for speech refinement...")
        
        # Enhanced prompt for speech refinement with correction handling
        refinement_prompt = f"""You are a speech cleanup assistant. Your job is to take messy, conversational speech and turn it into a clean, simple command.

Rules:
1. Handle corrections (when someone says "no" or "actually" they are correcting themselves)
2. Use the FINAL/LATEST version when there are corrections
3. Simplify the language while keeping the core intent
4. Return ONLY the cleaned command, nothing else
5. Don't add explanations, quotes, or extra text

Examples:
- "book meeting at 6 pm, no actually book meet at 8pm" → "book meeting at 8pm"
- "send email to john — wait, no send to mary instead" → "send email to mary"
- "create note about groceries, um, actually make it about shopping" → "create note about shopping"

Clean up this speech: {raw_speech}"""

        # Configure safety settings to be less restrictive (same as test function)
        safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        ]

        # Use generation config for better control
        generation_config = genai.types.GenerationConfig(
            temperature=0,
            # top_p=0.8
        )
        
        model = genai.GenerativeModel('gemini-2.5-flash')

        logger.info("Sending refinement prompt to Gemini...")
        # logger.info(f"API Key present: {bool(os.getenv('GEMINI_API_KEY'))}")
        logger.info(f"Using model: gemini-2.5-flash")

        response = model.generate_content(
            refinement_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0,
            ),
            safety_settings=safety_settings,
            request_options={'timeout': 10}
        )        

        logger.info(f"Gemini refinement response: {response.text}")
        
        # Better error handling for blocked responses (same as test function)
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'finish_reason'):
                logger.info(f"Refinement finish reason: {candidate.finish_reason}")
                
                if candidate.finish_reason == 2:  # SAFETY
                    logger.warning("⚠️ Refinement response was blocked by safety filters")
                    return raw_speech  # Return original speech if blocked
                elif candidate.finish_reason == 3:  # RECITATION  
                    logger.warning("⚠️ Refinement response was blocked due to recitation")
                    return raw_speech  # Return original speech if blocked
        
        # Try to access text
        if hasattr(response, 'text'):
            logger.info(f"Gemini refinement text response: {response.text}")
        else:
            logger.warning("Response has no 'text' attribute")
            logger.info(f"Available attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")
       
        if response and hasattr(response, 'text') and response.text:
            refined_text = response.text.strip().strip('"\'')
            logger.info(f"Gemini refined: '{raw_speech}' → '{refined_text}'")
            return refined_text
        else:
            logger.warning("Gemini returned empty response")
            return raw_speech
            
    except Exception as e:
        logger.error(f"Gemini refinement error: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        return raw_speech
    


# Initialize APIs only if keys are available
try:
    import google.generativeai as genai
    if os.getenv('GEMINI_API_KEY'):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        logger.info("Gemini API initialized successfully")
        # Test the connection
        if test_gemini_connection():
            logger.info("Gemini API connection test passed")
        else:
            logger.warning("Gemini API connection test failed")
    else:
        logger.warning("GEMINI_API_KEY not found, using rule-based refinement only")
except ImportError:
    logger.warning("google-generativeai not available, using rule-based refinement only")
    genai = None

try:
    from elevenlabs import ElevenLabs
    if os.getenv('ELEVENLABS_API_KEY'):
        elevenlabs_client = ElevenLabs(api_key=os.getenv('ELEVENLABS_API_KEY'))
        logger.info("ElevenLabs API initialized successfully")
except ImportError:
    logger.warning("elevenlabs not available")
    elevenlabs_client = None

app = Flask(__name__)

@app.route('/')
def index():
    """Main page - Hello World for testing"""
    return render_template('index.html')

@app.route('/test-spotify')
def test_spotify():
    """Test page for Spotify integration debugging"""
    return render_template('test_spotify.html')

@app.route('/api/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Vocal Agent Frontend is running',
        'version': '1.0.0'
    })

@app.route('/api/speech-to-text', methods=['POST'])
def speech_to_text():
    """Convert speech audio to text - For now, using a mock implementation"""
    try:
        # Get audio data from request
        data = request.get_json()
        audio_data = data.get('audio_data', '')
        
        if not audio_data:
            return jsonify({'success': False, 'error': 'No audio data provided'}), 400
        
        logger.info("Processing speech to text...")
        
        # TODO: Implement proper STT API integration
        # For now, return a mock transcription to test the pipeline
        mock_transcription = "Book a meeting with Ben at 8 p.m. — no, actually book with Alice at 6 p.m."
        
        logger.info(f"Mock transcribed text: {mock_transcription}")
        
        return jsonify({
            'success': True,
            'transcribed_text': mock_transcription
        })
        
    except Exception as e:
        logger.error(f"Speech-to-text error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Speech-to-text failed: {str(e)}'
        }), 500

@app.route('/api/refine-speech', methods=['POST'])
def refine_speech():
    """Refine raw speech text using rule-based processing and optional Gemini fallback"""
    try:
        data = request.get_json()
        raw_speech = data.get('raw_speech', '')
        
        if not raw_speech:
            return jsonify({'success': False, 'error': 'No raw speech provided'}), 400
        
        logger.info(f"Refining speech: {raw_speech}")
        
        # Use Gemini for speech refinement
        if os.getenv('GEMINI_API_KEY'):
            try:
                logger.info("Using Gemini for speech refinement...")
                refined_command = gemini_refinement(raw_speech)
                if not refined_command:
                    refined_command = raw_speech  # Fallback to original if Gemini fails
            except Exception as gemini_error:
                logger.warning(f"Gemini refinement failed: {gemini_error}")
                refined_command = raw_speech  # Fallback to original
        else:
            logger.warning("No Gemini API key found, using original speech")
            refined_command = raw_speech
        
        logger.info(f"Refined command: {refined_command}")
        
        return jsonify({
            'success': True,
            'raw_speech': raw_speech,
            'refined_command': refined_command
        })
        
    except Exception as e:
        logger.error(f"Speech refinement error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Speech refinement failed: {str(e)}'
        }), 500



@app.route('/api/process-command', methods=['POST'])
def process_command():
    """Process refined command with ASI:One (placeholder for now)"""
    try:
        data = request.get_json()
        refined_command = data.get('refined_command', '')
        
        if not refined_command:
            return jsonify({'success': False, 'error': 'No refined command provided'}), 400
        
        logger.info(f"Processing command with ASI:One: {refined_command}")
        
        # TODO: Integrate with ASI:One reasoning module
        # For now, create a mock response
        
        # Simulate ASI:One processing
        mock_response = {
            'task_type': 'calendar_event',  # This would be determined by ASI:One
            'parameters': {
                'attendee': 'Alice',
                'time': '6pm',
                'action': 'book_meeting'
            },
            'confidence': 0.95,
            'suggested_action': f'I understand you want to: {refined_command}. Shall I proceed?'
        }
        
        return jsonify({
            'success': True,
            'refined_command': refined_command,
            'asi_one_response': mock_response,
            'next_steps': 'Command ready for agent execution'
        })
        
    except Exception as e:
        logger.error(f"Command processing error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Command processing failed: {str(e)}'
        }), 500


@app.route('/api/process_voice', methods=['POST'])
def process_voice():
    """Legacy endpoint - kept for backward compatibility"""
    data = request.get_json()
    command = data.get('command', '')
    
    logger.info(f"Received voice command (legacy): {command}")
    
    response = {
        'success': True,
        'message': f'Received command: {command}',
        'processed_command': command,
        'agent_response': 'Use the new voice workflow endpoints for enhanced processing'
    }
    
    return jsonify(response)

@app.route('/api/spotify/auth')
def spotify_auth():
    """Initiate Spotify OAuth authentication"""
    try:
        # Import spotipy here to avoid issues if not installed
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
        
        # Get Spotify credentials from environment
        client_id = os.getenv('SPOTIFY_CLIENT_ID')
        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        # Override redirect URI for frontend integration
        redirect_uri = 'http://127.0.0.1:5001/api/spotify/callback'
        
        if not all([client_id, client_secret]):
            return jsonify({
                'success': False,
                'error': 'Spotify credentials not configured. Please check your .env file.'
            }), 400
        
        # Spotify scopes needed for playlist creation and music search
        scope = "playlist-modify-public playlist-modify-private playlist-read-private user-library-read"
        
        # Create auth manager
        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope,
            cache_path=".spotify_cache"
        )
        
        # Get authorization URL
        auth_url = auth_manager.get_authorize_url()
        
        logger.info(f"Spotify auth URL generated: {auth_url}")
        
        return jsonify({
            'success': True,
            'auth_url': auth_url,
            'message': 'Redirect to Spotify for authentication'
        })
        
    except ImportError:
        return jsonify({
            'success': False,
            'error': 'Spotify library not installed. Please install spotipy.'
        }), 500
    except Exception as e:
        logger.error(f"Spotify auth error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Spotify authentication failed: {str(e)}'
        }), 500

@app.route('/api/spotify/callback')
def spotify_callback():
    """Handle Spotify OAuth callback"""
    try:
        # Import spotipy here to avoid issues if not installed
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
        
        # Get the authorization code from the callback
        code = request.args.get('code')
        error = request.args.get('error')
        
        if error:
            logger.error(f"Spotify OAuth error: {error}")
            return redirect(url_for('index') + '?spotify_auth=error')
        
        if not code:
            logger.error("No authorization code received from Spotify")
            return redirect(url_for('index') + '?spotify_auth=error')
        
        # Get Spotify credentials from environment
        client_id = os.getenv('SPOTIFY_CLIENT_ID')
        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        # Override redirect URI for frontend integration
        redirect_uri = 'http://127.0.0.1:5001/api/spotify/callback'
        
        # Spotify scopes
        scope = "playlist-modify-public playlist-modify-private playlist-read-private user-library-read"
        
        # Create auth manager
        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope,
            cache_path=".spotify_cache"
        )
        
        # Exchange code for token
        token_info = auth_manager.get_access_token(code)
        
        if token_info:
            # Create Spotify client to test the connection
            spotify = spotipy.Spotify(auth_manager=auth_manager)
            user_info = spotify.current_user()
            
            logger.info(f"Spotify authentication successful for user: {user_info['display_name']}")
            
            # Redirect back to main page with success message
            return redirect(url_for('index') + '?spotify_auth=success')
        else:
            logger.error("Failed to get access token from Spotify")
            return redirect(url_for('index') + '?spotify_auth=error')
            
    except ImportError:
        logger.error("Spotify library not installed")
        return redirect(url_for('index') + '?spotify_auth=error')
    except Exception as e:
        logger.error(f"Spotify callback error: {str(e)}")
        return redirect(url_for('index') + '?spotify_auth=error')

if __name__ == '__main__':
    logger.info("Starting Vocal Agent Frontend...")
    logger.info("Starting standard Flask server...")
    logger.info("Please open http://127.0.0.1:5001 in your browser")
    app.run(debug=True, host='127.0.0.1', port=5001)