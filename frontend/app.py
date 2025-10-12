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
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
# Import will be handled later in the initialization section

# Load environment variables
load_dotenv()

# Configure logging first
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChatContextManager:
    """
    Manages conversation context and memory for the AI assistant
    """
    
    def __init__(self, max_context_length: int = 10, max_tokens_per_message: int = 500):
        self.max_context_length = max_context_length
        self.max_tokens_per_message = max_tokens_per_message
        self.current_session_id = None
        self.conversation_history: List[Dict[str, Any]] = []
        self.user_preferences: Dict[str, Any] = {}
        self.session_start_time = None
        
    def start_new_session(self, session_id: Optional[str] = None) -> str:
        """Start a new conversation session"""
        if session_id is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_id = f"session_{timestamp}_{str(uuid.uuid4())[:8]}"
        
        self.current_session_id = session_id
        self.conversation_history = []
        self.user_preferences = {}
        self.session_start_time = datetime.now()
        
        logger.info(f"Started new chat session: {session_id}")
        return session_id
    
    def add_interaction(self, user_input: str, assistant_response: str, interaction_type: str = "general") -> None:
        """Add a new interaction to the conversation history"""
        if not self.current_session_id:
            self.start_new_session()
        
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "type": interaction_type,
            "user_input": user_input[:self.max_tokens_per_message],  # Truncate if too long
            "assistant_response": assistant_response[:self.max_tokens_per_message]
        }
        
        self.conversation_history.append(interaction)
        
        # Keep only the most recent interactions
        if len(self.conversation_history) > self.max_context_length:
            self.conversation_history = self.conversation_history[-self.max_context_length:]
        
        logger.info(f"Added {interaction_type} interaction to context (total: {len(self.conversation_history)})")
    
    def get_context_for_prompt(self, current_input: str, include_recent: int = 5) -> str:
        """Get formatted context string for inclusion in prompts"""
        if not self.conversation_history:
            return ""
        
        # Get recent interactions
        recent_interactions = self.conversation_history[-include_recent:] if include_recent > 0 else []
        
        if not recent_interactions:
            return ""
        
        context_parts = ["## CONVERSATION CONTEXT"]
        context_parts.append(f"Session: {self.current_session_id}")
        context_parts.append(f"Previous interactions ({len(recent_interactions)} recent):")
        context_parts.append("")
        
        for i, interaction in enumerate(recent_interactions, 1):
            context_parts.append(f"**Interaction {i}** ({interaction['type']}):")
            context_parts.append(f"User: {interaction['user_input']}")
            context_parts.append(f"Assistant: {interaction['assistant_response']}")
            context_parts.append("")
        
        # Add user preferences if any
        if self.user_preferences:
            context_parts.append("## USER PREFERENCES")
            for key, value in self.user_preferences.items():
                context_parts.append(f"- {key}: {value}")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def update_user_preferences(self, preferences: Dict[str, Any]) -> None:
        """Update user preferences"""
        self.user_preferences.update(preferences)
        logger.info(f"Updated user preferences: {preferences}")
    
    def get_context_status(self) -> Dict[str, Any]:
        """Get current context status"""
        return {
            "session_id": self.current_session_id,
            "interaction_count": len(self.conversation_history),
            "recent_types": [interaction["type"] for interaction in self.conversation_history[-5:]],
            "user_preferences": self.user_preferences.copy(),
            "session_start_time": self.session_start_time.isoformat() if self.session_start_time else None
        }
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get full conversation history"""
        return self.conversation_history.copy()
    
    def clear_context(self) -> None:
        """Clear all context and start fresh"""
        self.conversation_history = []
        self.user_preferences = {}
        logger.info("Context cleared")
    
    def extract_preferences_from_interaction(self, user_input: str, assistant_response: str) -> Dict[str, Any]:
        """Extract potential user preferences from the interaction"""
        preferences = {}
        
        # Simple preference extraction patterns
        user_lower = user_input.lower()
        
        # Name extraction
        if "my name is" in user_lower:
            name_match = re.search(r"my name is (\w+)", user_lower)
            if name_match:
                preferences["name"] = name_match.group(1).title()
        
        # Music preferences
        if any(word in user_lower for word in ["love", "like", "enjoy", "favorite"]):
            if "rock" in user_lower:
                preferences["music_genre"] = "rock"
            elif "pop" in user_lower:
                preferences["music_genre"] = "pop"
            elif "jazz" in user_lower:
                preferences["music_genre"] = "jazz"
            elif "classical" in user_lower:
                preferences["music_genre"] = "classical"
        
        # Interests
        interests = []
        if "ai" in user_lower or "artificial intelligence" in user_lower:
            interests.append("AI")
        if "music" in user_lower:
            interests.append("music")
        if "technology" in user_lower or "tech" in user_lower:
            interests.append("technology")
        if "programming" in user_lower or "coding" in user_lower:
            interests.append("programming")
        
        if interests:
            preferences["interests"] = interests
        
        return preferences

# Initialize the context manager
context_manager = ChatContextManager(
    max_context_length=10,
    max_tokens_per_message=500
)

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
            # Enhanced error message for Spotify connection issues
            return "I'm having trouble connecting to the music service. To use music features, please click the 'Integrate with apps' button in the top right corner and connect your Spotify account."
        
        # Check if the Spotify response indicates authentication/connection issues
        if isinstance(spotify_response, dict):
            spotify_text = str(spotify_response).lower()
        else:
            spotify_text = str(spotify_response).lower()
        
        # Check for common Spotify error patterns
        spotify_error_patterns = [
            'not authenticated', 'authentication failed', 'authorization required',
            'login required', 'permission denied', 'access denied', 'token expired',
            'invalid token', 'unable to access', 'cannot connect', 'integration failed',
            'api error', 'service unavailable', 'trouble connecting', 'connection failed',
            'agent not available', 'agent connection failed', 'cannot reach', 'timeout',
            'connection refused', 'service down', 'unreachable'
        ]
        
        has_spotify_error = any(pattern in spotify_text for pattern in spotify_error_patterns)
        
        if has_spotify_error:
            logger.warning(f"Spotify error detected in response: {spotify_response}")
            return "I'm having trouble accessing your music service. To use music features, please click the 'Integrate with apps' button in the top right corner and connect your Spotify account."
        
        # Process Spotify response through Gemini for user-friendly output
        if genai and os.getenv('GEMINI_API_KEY'):
            try:
                # Get system information for context
                system_info = get_system_info()
                
                # Build system context for music processing
                system_context = ""
                if system_info:
                    spotify_auth = system_info['current_authentications'].get('spotify', {})
                    spotify_integration = system_info['available_integrations'].get('spotify', {})
                    
                    system_context = f"""

## SYSTEM INFORMATION
You are Iris, an AI assistant with access to Spotify integration:

### Spotify Integration Status:
- **Status**: {'✅ Connected' if spotify_auth.get('authenticated', False) else '❌ Not connected'}
- **Capabilities**: {', '.join(spotify_integration.get('capabilities', []))}
"""
                    if spotify_auth.get('authenticated') and 'user' in spotify_auth:
                        system_context += f"- **Connected as**: {spotify_auth['user'].get('display_name', 'Unknown')}\n"
                
                # Get conversation context for music processing
                conversation_context = context_manager.get_context_for_prompt(voice_input, include_recent=3)
                
                # Create a prompt to make the Spotify response more user-friendly
                music_processing_prompt = f"""You are Iris, a helpful AI assistant. The user made a music request, and here's what the music service found:

{system_context}

{conversation_context}

User's request: {voice_input}
Music service response: {spotify_response}

Please provide a friendly, conversational response to the user about what was found. Make it sound natural and helpful, as if you're personally helping them with their music request. Keep it concise but informative.

**CONTEXT AWARENESS**: Use the conversation context above to provide more personalized music recommendations. Reference previous music preferences, genres mentioned, or artists the user has shown interest in.

IMPORTANT: If the music service response indicates any authentication, connection, or access issues, you MUST tell the user to click the "Integrate with apps" button in the top right corner to connect their Spotify account.

FORMATTING GUIDELINES:
- Use markdown formatting when appropriate to make your responses more readable
- Use **bold** for emphasis on important points like song titles or artist names
- Use *italics* for subtle emphasis
- Use bullet points (-) when listing multiple songs, albums, or artists
- Use `code formatting` for technical terms or specific values
- Use [links](url) when referencing external resources
- Use > blockquotes for important notes or warnings

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
                    
                    # Add music interaction to context
                    context_manager.add_interaction(voice_input, processed_response, "music")
                    
                    # Extract and update user preferences from music interaction
                    extracted_preferences = context_manager.extract_preferences_from_interaction(voice_input, processed_response)
                    if extracted_preferences:
                        context_manager.update_user_preferences(extracted_preferences)
                    
                    return processed_response
                else:
                    logger.warning("Gemini returned empty response for music request")
                    fallback_response = f"I found some music for you: {spotify_response}"
                    
                    # Add fallback interaction to context
                    context_manager.add_interaction(voice_input, fallback_response, "music")
                    
                    return fallback_response
                    
            except Exception as gemini_error:
                logger.warning(f"Gemini processing failed for music request: {gemini_error}")
                return f"I found some music for you: {spotify_response}"
        else:
            # Fallback if Gemini is not available
            logger.warning("Gemini not available, returning raw Spotify response")
            return f"I found some music for you: {spotify_response}"
            
    except Exception as e:
        logger.error(f"Error processing music request: {str(e)}")
        return "I'm having trouble processing your music request. To use music features, please click the 'Integrate with apps' button in the top right corner and connect your Spotify account."

# Get system information for Gemini
def get_system_info():
    """
    Get current system information about available integrations and their status
    """
    try:
        # Get system info from the endpoint we just created
        response = requests.get('http://127.0.0.1:5001/api/system-info', timeout=5)
        if response.status_code == 200:
            return response.json()['system_info']
        else:
            logger.warning("Failed to get system info from endpoint")
            return None
    except Exception as e:
        logger.warning(f"Could not get system info: {e}")
        return None

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
        
        # Get system information
        system_info = get_system_info()
        
        # Build system context
        system_context = ""
        if system_info:
            system_context = f"""

## SYSTEM INFORMATION
You are Iris, an AI assistant with access to the following integrations and capabilities:

### Available Integrations:
"""
            for integration_id, integration in system_info['available_integrations'].items():
                auth_status = system_info['current_authentications'].get(integration_id, {})
                status_icon = "✅" if auth_status.get('authenticated', False) else "❌"
                
                system_context += f"- {status_icon} **{integration['name']}** ({integration['icon']}): {integration['description']}\n"
                system_context += f"  - Capabilities: {', '.join(integration['capabilities'])}\n"
                if auth_status.get('authenticated'):
                    if 'user' in auth_status:
                        system_context += f"  - Connected as: {auth_status['user'].get('display_name', 'Unknown')}\n"
                else:
                    system_context += f"  - Status: {auth_status.get('status', 'Not connected')}\n"
                system_context += "\n"
            
            system_context += f"""
### System Status:
- Frontend: {system_info['system_status']['frontend']}
- Gemini AI: {system_info['system_status']['gemini_ai']}
- Text-to-Speech: {system_info['system_status']['elevenlabs_tts']}
- Speech Recognition: {system_info['system_status']['speech_recognition']}

### AI Capabilities:
- Natural Language Processing: {system_info['ai_capabilities']['natural_language_processing']}
- Speech-to-Text: {system_info['ai_capabilities']['speech_to_text']}
- Text-to-Speech: {system_info['ai_capabilities']['text_to_speech']}
- Intent Recognition: {system_info['ai_capabilities']['intent_recognition']}
- Multi-Agent Coordination: {system_info['ai_capabilities']['multi_agent_coordination']}
"""
        
        # Get conversation context
        conversation_context = context_manager.get_context_for_prompt(voice_input, include_recent=5)
        
        # Enhanced prompt for direct response with system information and context
        direct_response_prompt = f"""You are Iris, a helpful AI assistant. The user has spoken to you via voice input. Respond naturally and helpfully to what they've said.

{system_context}

{conversation_context}

## RESPONSE GUIDELINES:
1. Be conversational and friendly
2. If they're asking for help with something, provide useful assistance
3. If they're making a request, acknowledge it and offer to help
4. Keep responses concise but informative
5. If you're unsure what they want, ask for clarification
6. Be helpful and proactive
7. **CONTEXT AWARENESS**: Use the conversation context above to provide more personalized and relevant responses. Reference previous topics, user preferences, and maintain conversation continuity.
8. **IMPORTANT**: If the user mentions music, songs, playlists, Spotify, or any music-related requests, and you detect they might be having issues with music features, guide them to click the "Integrate with apps" button in the top right corner to connect their Spotify account.
9. **INTEGRATION GUIDANCE**: If the user asks about capabilities or what you can do, reference the available integrations above. If they want to use a specific integration that's not connected, guide them to the "Integrate with apps" button.

## FORMATTING GUIDELINES:
- Use markdown formatting when appropriate to make your responses more readable
- Use **bold** for emphasis on important points
- Use *italics* for subtle emphasis
- Use bullet points (-) or numbered lists (1.) when providing multiple items or steps
- Use `code formatting` for technical terms, commands, or specific values
- Use [links](url) when referencing external resources
- Use > blockquotes for important notes or warnings
- Use ## headings for organizing longer responses into sections

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
            
            # Add interaction to context
            context_manager.add_interaction(voice_input, direct_response, "general")
            
            # Extract and update user preferences
            extracted_preferences = context_manager.extract_preferences_from_interaction(voice_input, direct_response)
            if extracted_preferences:
                context_manager.update_user_preferences(extracted_preferences)
            
            return direct_response
        else:
            logger.warning("Gemini returned empty response")
            error_response = "I heard you, but I'm having trouble formulating a response. Could you try again?"
            
            # Add error interaction to context
            context_manager.add_interaction(voice_input, error_response, "error")
            
            return error_response
            
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
            
            # Add refinement interaction to context (but don't include in main conversation flow)
            context_manager.add_interaction(raw_speech, refined_text, "refinement")
            
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

@app.route('/api/text-to-speech', methods=['POST'])
def text_to_speech():
    """Convert text to speech using ElevenLabs API"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        voice_id = data.get('voice_id', 'JBFqnCBsd6RMkjVDRZzb')  # Default voice
        model_id = data.get('model_id', 'eleven_multilingual_v2')  # Default model
        output_format = data.get('output_format', 'mp3_44100_128')  # Default format
        
        if not text:
            return jsonify({'success': False, 'error': 'No text provided'}), 400
        
        if not elevenlabs_client:
            return jsonify({
                'success': False, 
                'error': 'ElevenLabs API not configured. Please set ELEVENLABS_API_KEY environment variable.'
            }), 500
        
        logger.info(f"Converting text to speech: '{text[:50]}...' with voice {voice_id}")
        
        # Prepare the request payload
        payload = {
            "text": text,
            "model_id": model_id
        }
        
        # Make the request to ElevenLabs API
        response = elevenlabs_client.text_to_speech.convert(
            voice_id=voice_id,
            output_format=output_format,
            **payload
        )
        
        # Handle generator response from ElevenLabs API
        if hasattr(response, '__iter__') and not isinstance(response, (bytes, str)):
            # Convert generator to bytes
            audio_bytes = b''.join(response)
        else:
            # Direct bytes response
            audio_bytes = response
        
        # Convert the audio response to base64 for frontend
        audio_data = base64.b64encode(audio_bytes).decode('utf-8')
        
        logger.info("Text-to-speech conversion successful")
        
        return jsonify({
            'success': True,
            'audio_data': audio_data,
            'format': output_format,
            'voice_id': voice_id,
            'model_id': model_id
        })
        
    except Exception as e:
        logger.error(f"Text-to-speech error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Text-to-speech conversion failed: {str(e)}'
        }), 500

@app.route('/api/system-info')
def system_info():
    """Get system information about available integrations and their status"""
    try:
        system_info = {
            'available_integrations': {
                'spotify': {
                    'name': 'Spotify',
                    'description': 'Music streaming service for playlist creation, music search, and playback control',
                    'icon': '🎵',
                    'capabilities': [
                        'Create custom playlists',
                        'Search for songs, artists, and albums',
                        'Get music recommendations',
                        'Manage existing playlists',
                        'Random song selection from playlists'
                    ],
                    'endpoint': 'http://localhost:8005/chat',
                    'status': 'available'
                },
                'gmail': {
                    'name': 'Gmail',
                    'description': 'Email service for composing, sending, and managing emails',
                    'icon': '📧',
                    'capabilities': [
                        'Compose and send emails',
                        'Read inbox messages',
                        'Search emails',
                        'Organize messages'
                    ],
                    'endpoint': 'http://localhost:8002/chat',
                    'status': 'available'
                },
                'google_calendar': {
                    'name': 'Google Calendar',
                    'description': 'Calendar service for scheduling meetings and managing events',
                    'icon': '📅',
                    'capabilities': [
                        'Schedule meetings and events',
                        'Check availability',
                        'Manage calendar events',
                        'Set reminders'
                    ],
                    'endpoint': 'http://localhost:8001/chat',
                    'status': 'available'
                },
                'notes': {
                    'name': 'Notes',
                    'description': 'Note-taking service for creating and organizing notes',
                    'icon': '📝',
                    'capabilities': [
                        'Create notes',
                        'Search existing notes',
                        'Organize notes by category',
                        'Edit and update notes'
                    ],
                    'endpoint': 'http://localhost:8003/chat',
                    'status': 'available'
                },
                'discord': {
                    'name': 'Discord',
                    'description': 'Communication platform for sending messages and managing Discord interactions',
                    'icon': '💬',
                    'capabilities': [
                        'Send messages to Discord channels',
                        'Manage Discord server interactions',
                        'User lookup and management'
                    ],
                    'endpoint': 'http://localhost:8004/chat',
                    'status': 'available'
                }
            },
            'current_authentications': {},
            'system_status': {
                'frontend': 'running',
                'gemini_ai': 'available' if genai and os.getenv('GEMINI_API_KEY') else 'unavailable',
                'elevenlabs_tts': 'available' if elevenlabs_client else 'unavailable',
                'speech_recognition': 'available'
            },
            'ai_capabilities': {
                'natural_language_processing': 'Available via Google Gemini',
                'speech_to_text': 'Available via Web Speech API',
                'text_to_speech': 'Available via ElevenLabs',
                'intent_recognition': 'Available via Gemini AI',
                'multi_agent_coordination': 'Available via uAgents protocol'
            }
        }
        
        # Check authentication status for each integration
        try:
            # Check Spotify authentication
            spotify_status = check_spotify_auth_status()
            system_info['current_authentications']['spotify'] = spotify_status
        except Exception as e:
            logger.warning(f"Could not check Spotify auth status: {e}")
            system_info['current_authentications']['spotify'] = {
                'authenticated': False,
                'error': str(e)
            }
        
        # For other integrations, we'll add status checks as they're implemented
        system_info['current_authentications']['gmail'] = {'authenticated': False, 'status': 'not_configured'}
        system_info['current_authentications']['google_calendar'] = {'authenticated': False, 'status': 'not_configured'}
        system_info['current_authentications']['notes'] = {'authenticated': False, 'status': 'not_configured'}
        system_info['current_authentications']['discord'] = {'authenticated': False, 'status': 'not_configured'}
        
        return jsonify({
            'success': True,
            'system_info': system_info
        })
        
    except Exception as e:
        logger.error(f"System info error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get system info: {str(e)}'
        }), 500

def check_spotify_auth_status():
    """Check Spotify authentication status"""
    try:
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth
        
        client_id = os.getenv('SPOTIFY_CLIENT_ID')
        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        redirect_uri = 'http://127.0.0.1:5001/api/spotify/callback'
        scope = "playlist-modify-public playlist-modify-private playlist-read-private user-library-read"
        
        if not all([client_id, client_secret]):
            return {
                'authenticated': False,
                'error': 'Spotify credentials not configured'
            }
        
        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope,
            cache_path=".spotify_cache"
        )
        
        token_info = auth_manager.cache_handler.get_cached_token()
        
        if not token_info:
            return {
                'authenticated': False,
                'status': 'no_cached_credentials'
            }
        
        # Test the connection
        try:
            spotify = spotipy.Spotify(auth_manager=auth_manager)
            user_info = spotify.current_user()
            
            return {
                'authenticated': True,
                'user': {
                    'display_name': user_info['display_name'],
                    'email': user_info.get('email', 'N/A'),
                    'followers': user_info['followers']['total']
                },
                'status': 'active'
            }
            
        except Exception as e:
            return {
                'authenticated': False,
                'error': 'Token expired or invalid',
                'status': 'token_expired'
            }
        
    except ImportError:
        return {
            'authenticated': False,
            'error': 'Spotify library not installed'
        }
    except Exception as e:
        return {
            'authenticated': False,
            'error': f'Status check failed: {str(e)}'
        }

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
            
            # Trigger the setup script to ensure proper configuration
            try:
                # Import the setup function from the Spotify agent
                import sys
                
                # Add the Spotify agent directory to the path
                spotify_agent_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'agents', 'new-agents', 'spotifyAgent')
                if spotify_agent_path not in sys.path:
                    sys.path.append(spotify_agent_path)
                
                from setup_spotify_auth import setup_spotify_auth_with_params
                
                # Call the setup function with the authentication parameters
                # Use the frontend cache file as source, setup script will copy to agent directory
                setup_result = setup_spotify_auth_with_params(
                    client_id=client_id,
                    client_secret=client_secret,
                    redirect_uri=redirect_uri,
                    auth_code=code,
                    cache_path=".spotify_cache"  # This is the frontend cache file
                )
                
                if setup_result['success']:
                    logger.info(f"Spotify setup script completed successfully: {setup_result['message']}")
                else:
                    logger.warning(f"Spotify setup script had issues: {setup_result['error']}")
                    
            except Exception as setup_error:
                logger.warning(f"Failed to run Spotify setup script: {str(setup_error)}")
                # Don't fail the authentication if setup script fails
            
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

# Context Management Endpoints

@app.route('/api/context/start-session', methods=['POST'])
def start_context_session():
    """Start a new conversation session"""
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id')
        
        new_session_id = context_manager.start_new_session(session_id)
        
        return jsonify({
            'success': True,
            'session_id': new_session_id,
            'message': f'Started new session: {new_session_id}'
        })
        
    except Exception as e:
        logger.error(f"Error starting context session: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to start session: {str(e)}'
        }), 500

@app.route('/api/context/status')
def get_context_status():
    """Get current context status"""
    try:
        status = context_manager.get_context_status()
        
        return jsonify({
            'success': True,
            'context': status
        })
        
    except Exception as e:
        logger.error(f"Error getting context status: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get context status: {str(e)}'
        }), 500

@app.route('/api/context/history')
def get_context_history():
    """Get conversation history"""
    try:
        history = context_manager.get_conversation_history()
        
        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        })
        
    except Exception as e:
        logger.error(f"Error getting context history: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get context history: {str(e)}'
        }), 500

@app.route('/api/context/clear', methods=['POST'])
def clear_context():
    """Clear conversation context"""
    try:
        context_manager.clear_context()
        
        return jsonify({
            'success': True,
            'message': 'Context cleared successfully'
        })
        
    except Exception as e:
        logger.error(f"Error clearing context: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to clear context: {str(e)}'
        }), 500

@app.route('/api/context/preferences', methods=['GET', 'POST'])
def manage_user_preferences():
    """Get or update user preferences"""
    try:
        if request.method == 'GET':
            # Get current preferences
            preferences = context_manager.user_preferences.copy()
            
            return jsonify({
                'success': True,
                'preferences': preferences
            })
        
        elif request.method == 'POST':
            # Update preferences
            data = request.get_json()
            if not data or 'preferences' not in data:
                return jsonify({
                    'success': False,
                    'error': 'No preferences provided'
                }), 400
            
            preferences = data['preferences']
            context_manager.update_user_preferences(preferences)
            
            return jsonify({
                'success': True,
                'preferences': context_manager.user_preferences.copy(),
                'message': 'Preferences updated successfully'
            })
        
    except Exception as e:
        logger.error(f"Error managing user preferences: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to manage preferences: {str(e)}'
        }), 500

if __name__ == '__main__':
    logger.info("Starting Vocal Agent Frontend...")
    
    # Initialize context manager with a default session
    context_manager.start_new_session()
    logger.info("Context manager initialized with default session")
    
    logger.info("Starting standard Flask server...")
    logger.info("Please open http://127.0.0.1:5001 in your browser")
    app.run(debug=True, host='127.0.0.1', port=5001)