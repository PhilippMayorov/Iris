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
import requests
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



# Music-related keyword detection
def is_music_related_request(text):
    """
    Detect if the user's request is music-related
    """
    if not text:
        return False
    
    # Convert to lowercase for case-insensitive matching
    text_lower = text.lower()
    
    # Music-related keywords
    music_keywords = [
        'music', 'song', 'songs', 'play', 'playing', 'playlist', 'artist', 'album',
        'spotify', 'search for', 'find', 'listen', 'hear', 'track', 'tracks',
        'play music', 'play song', 'play songs', 'search music', 'search songs',
        'what song', 'what music', 'recommend', 'suggest', 'genre', 'band',
        'singer', 'musician', 'concert', 'lyrics', 'beat', 'rhythm', 'melody',
        'drake', 'taylor swift', 'beyonce', 'ed sheeran', 'justin bieber',
        'ariana grande', 'billie eilish', 'the weeknd', 'post malone',
        'kanye west', 'rihanna', 'adele', 'bruno mars', 'shawn mendes'
    ]
    
    # Check if any music keyword is present
    for keyword in music_keywords:
        if keyword in text_lower:
            return True
    
    return False

# Call Spotify agent endpoint
def call_spotify_agent(user_request):
    """
    Call the Spotify agent endpoint with the user's music request
    """
    try:
        logger.info(f"Calling Spotify agent with request: {user_request}")
        
        # Spotify agent endpoint
        spotify_url = "http://localhost:8005/chat"
        
        # Prepare the request payload
        payload = {
            "text": user_request
        }
        
        # Make the request to Spotify agent
        response = requests.post(
            spotify_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30  # 30 second timeout
        )
        
        if response.status_code == 200:
            spotify_response = response.json()
            logger.info(f"Spotify agent response: {spotify_response}")
            return spotify_response
        else:
            logger.error(f"Spotify agent returned status {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Spotify agent: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error calling Spotify agent: {str(e)}")
        return None

# Process music request through Spotify agent and Gemini
def process_music_request(voice_input):
    """
    Process music-related requests through Spotify agent and then through Gemini
    """
    try:
        logger.info(f"Processing music request: {voice_input}")
        
        # Call Spotify agent
        spotify_response = call_spotify_agent(voice_input)
        
        if not spotify_response:
            return "I'm having trouble connecting to the music service. Please try again later."
        
        # Process Spotify response through Gemini for user-friendly output
        if genai and os.getenv('GEMINI_API_KEY'):
            try:
                # Create a prompt to make the Spotify response more user-friendly
                music_processing_prompt = f"""You are Iris, a helpful AI assistant. The user made a music request, and here's what the music service found:

User's request: {voice_input}
Music service response: {spotify_response}

Please provide a friendly, conversational response to the user about what was found. Make it sound natural and helpful, as if you're personally helping them with their music request. Keep it concise but informative.

Respond as Iris:"""

                # Configure safety settings
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

                # Use generation config
                generation_config = genai.types.GenerationConfig(
                    temperature=0.7,
                )
                
                model = genai.GenerativeModel('gemini-2.5-flash')

                logger.info("Processing Spotify response through Gemini...")

                response = model.generate_content(
                    music_processing_prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings,
                    request_options={'timeout': 15}
                )

                if response and hasattr(response, 'text') and response.text:
                    processed_response = response.text.strip()
                    logger.info(f"Gemini processed music response: {processed_response}")
                    return processed_response
                else:
                    logger.warning("Gemini returned empty response for music request")
                    return f"I found some music for you: {spotify_response}"
                    
            except Exception as gemini_error:
                logger.warning(f"Gemini processing failed for music request: {gemini_error}")
                return f"I found some music for you: {spotify_response}"
        else:
            # Fallback if Gemini is not available
            logger.warning("Gemini not available, returning raw Spotify response")
            return f"I found some music for you: {spotify_response}"
            
    except Exception as e:
        logger.error(f"Error processing music request: {str(e)}")
        return "I'm having trouble processing your music request. Please try again."

# Get direct response from Gemini API
def get_gemini_direct_response(voice_input):
    """
    Use Gemini API to provide a direct response to user's voice input
    """
    if not voice_input:
        logger.warning("No voice input provided")
        return "I'm sorry, I couldn't process your request."
    
    # Check if this is a music-related request
    if is_music_related_request(voice_input):
        logger.info("Music-related request detected, routing to Spotify agent")
        return process_music_request(voice_input)
    
    # If not music-related, use Gemini for general responses
    if not genai:
        logger.warning("Gemini not available for non-music requests")
        return "I heard you, but I need my AI service to be configured to help with that."
    
    try:
        logger.info("Making Gemini API call for direct response...")
        
        # Enhanced prompt for direct response
        direct_response_prompt = f"""You are Iris, a helpful AI assistant. The user has spoken to you via voice input. Respond naturally and helpfully to what they've said.

Guidelines:
1. Be conversational and friendly
2. If they're asking for help with something, provide useful assistance
3. If they're making a request, acknowledge it and offer to help
4. Keep responses concise but informative
5. If you're unsure what they want, ask for clarification
6. Be helpful and proactive

User's voice input: {voice_input}

Respond as Iris:"""

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

        # Use generation config for better control
        generation_config = genai.types.GenerationConfig(
            temperature=0.7,  # Slightly more creative for conversational responses
        )
        
        model = genai.GenerativeModel('gemini-2.5-flash')

        logger.info("Sending direct response prompt to Gemini...")
        logger.info(f"Using model: gemini-2.5-flash")

        response = model.generate_content(
            direct_response_prompt,
            generation_config=generation_config,
            safety_settings=safety_settings,
            request_options={'timeout': 15}
        )        

        logger.info(f"Gemini direct response: {response.text}")
        
        # Better error handling for blocked responses
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'finish_reason'):
                logger.info(f"Direct response finish reason: {candidate.finish_reason}")
                
                if candidate.finish_reason == 2:  # SAFETY
                    logger.warning("⚠️ Direct response was blocked by safety filters")
                    return "I understand you're trying to communicate with me. Could you rephrase that in a different way?"
                elif candidate.finish_reason == 3:  # RECITATION  
                    logger.warning("⚠️ Direct response was blocked due to recitation")
                    return "I heard what you said, but I need to respond in my own words. Could you try asking that differently?"
        
        # Try to access text
        if hasattr(response, 'text'):
            logger.info(f"Gemini direct response text: {response.text}")
        else:
            logger.warning("Response has no 'text' attribute")
            logger.info(f"Available attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")
       
        if response and hasattr(response, 'text') and response.text:
            direct_response = response.text.strip()
            logger.info(f"Gemini direct response: '{voice_input}' → '{direct_response}'")
            return direct_response
        else:
            logger.warning("Gemini returned empty response")
            return "I heard you, but I'm having trouble formulating a response. Could you try again?"
            
    except Exception as e:
        logger.error(f"Gemini direct response error: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        return "I'm experiencing some technical difficulties. Please try again in a moment."


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

@app.route('/api/gemini-direct-response', methods=['POST'])
def gemini_direct_response():
    """Get direct response from Gemini for voice input without filtering"""
    try:
        data = request.get_json()
        voice_input = data.get('voice_input', '')
        
        if not voice_input:
            return jsonify({'success': False, 'error': 'No voice input provided'}), 400
        
        logger.info(f"Getting direct Gemini response for: {voice_input}")
        
        # Use Gemini for direct response
        if os.getenv('GEMINI_API_KEY') and genai:
            try:
                logger.info("Using Gemini for direct response...")
                direct_response = get_gemini_direct_response(voice_input)
                if not direct_response:
                    direct_response = "I'm sorry, I couldn't process your request. Please try again."
            except Exception as gemini_error:
                logger.warning(f"Gemini direct response failed: {gemini_error}")
                direct_response = "I'm having trouble connecting to my AI service. Please try again later."
        else:
            logger.warning("No Gemini API key found, using fallback response")
            direct_response = f"I heard you say: '{voice_input}'. I'm ready to help, but I need my AI service to be configured."
        
        logger.info(f"Gemini direct response: {direct_response}")
        
        return jsonify({
            'success': True,
            'voice_input': voice_input,
            'gemini_response': direct_response
        })
        
    except Exception as e:
        logger.error(f"Gemini direct response error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Direct response failed: {str(e)}'
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

@app.route('/api/spotify/status')
def spotify_status():
    """Check Spotify authentication status"""
    try:
        # Import spotipy here to avoid issues if not installed
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
        
        # Get Spotify credentials from environment
        client_id = os.getenv('SPOTIFY_CLIENT_ID')
        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        redirect_uri = 'http://127.0.0.1:5001/api/spotify/callback'
        scope = "playlist-modify-public playlist-modify-private playlist-read-private user-library-read"
        
        if not all([client_id, client_secret]):
            return jsonify({
                'authenticated': False,
                'error': 'Spotify credentials not configured'
            }), 400
        
        # Create auth manager
        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope,
            cache_path=".spotify_cache"
        )
        
        # Check if we have cached credentials
        token_info = auth_manager.cache_handler.get_cached_token()
        
        if not token_info:
            return jsonify({
                'authenticated': False,
                'message': 'No cached credentials found'
            })
        
        # Test the connection by getting current user
        try:
            spotify = spotipy.Spotify(auth_manager=auth_manager)
            user_info = spotify.current_user()
            
            return jsonify({
                'authenticated': True,
                'user': {
                    'display_name': user_info['display_name'],
                    'email': user_info.get('email', 'N/A'),
                    'followers': user_info['followers']['total']
                },
                'message': f'Connected as {user_info["display_name"]}'
            })
            
        except Exception as e:
            logger.error(f"Spotify API test failed: {str(e)}")
            return jsonify({
                'authenticated': False,
                'error': 'Token expired or invalid',
                'message': 'Please re-authenticate'
            })
        
    except ImportError:
        return jsonify({
            'authenticated': False,
            'error': 'Spotify library not installed'
        }), 500
    except Exception as e:
        logger.error(f"Spotify status check error: {str(e)}")
        return jsonify({
            'authenticated': False,
            'error': f'Status check failed: {str(e)}'
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