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

# Import contacts functionality
try:
    from Contacts import CNContactStore, CNContact, CNContactFormatter
    from Contacts import CNContactGivenNameKey, CNContactFamilyNameKey, CNContactNicknameKey
    from Contacts import CNContactPhoneNumbersKey, CNContactEmailAddressesKey, CNContactPostalAddressesKey
    from Contacts import CNContactBirthdayKey, CNContactJobTitleKey, CNContactDepartmentNameKey
    from Contacts import CNContactOrganizationNameKey, CNContactMiddleNameKey, CNContactNoteKey
    from Contacts import CNContactImageDataKey, CNContactThumbnailImageDataKey
    from Contacts import CNContactUrlAddressesKey, CNContactInstantMessageAddressesKey, CNContactSocialProfilesKey
    from Foundation import NSData, NSString
    import Contacts
    CONTACTS_AVAILABLE = True
    logger.info("Contacts framework imported successfully")
except ImportError as e:
    logger.warning(f"Contacts framework not available: {e}")
    CONTACTS_AVAILABLE = False

def clean_text_for_tts(text: str) -> str:
    """
    Clean text for TTS by removing markdown formatting and special characters
    that cause pronunciation issues.
    """
    if not text:
        return text
    
    # Remove markdown formatting
    # Remove bold formatting (**text** or __text__)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    
    # Remove italic formatting (*text* or _text_)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'_(.*?)_', r'\1', text)
    
    # Remove code formatting (`text`)
    text = re.sub(r'`(.*?)`', r'\1', text)
    
    # Remove strikethrough formatting (~~text~~)
    text = re.sub(r'~~(.*?)~~', r'\1', text)
    
    # Remove headers (# ## ###)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    
    # Remove links but keep the text ([text](url) -> text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    
    # Remove blockquotes (> text)
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
    
    # Remove horizontal rules (--- or ***)
    text = re.sub(r'^[-*_]{3,}$', '', text, flags=re.MULTILINE)
    
    # Remove list markers (- * + 1. 2. etc.)
    text = re.sub(r'^[\s]*[-*+]\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[\s]*\d+\.\s*', '', text, flags=re.MULTILINE)
    
    # Clean up multiple spaces and newlines
    text = re.sub(r'\n\s*\n', '\n', text)  # Multiple newlines to single
    text = re.sub(r'[ \t]+', ' ', text)    # Multiple spaces to single
    text = re.sub(r'\n ', '\n', text)      # Remove leading spaces after newlines
    
    # Remove any remaining special characters that might cause issues
    # Keep common punctuation but remove problematic ones
    text = re.sub(r'[^\w\s.,!?;:\-"\']', '', text)
    
    # Clean up multiple spaces again after character removal
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Clean up the final result
    text = text.strip()
    
    logger.info(f"TTS text cleaned: '{text[:50]}...'")
    return text

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

# Contacts Helper Functions
def get_all_contacts_from_mac():
    """Retrieve all contacts from the MacBook using PyObjC"""
    if not CONTACTS_AVAILABLE:
        logger.error("Contacts framework not available")
        return []
    
    try:
        store = CNContactStore()
        
        # Define the keys we want to fetch
        keys_to_fetch = [
            CNContactGivenNameKey,
            CNContactFamilyNameKey,
            CNContactNicknameKey,
            CNContactMiddleNameKey,
            CNContactPhoneNumbersKey,
            CNContactEmailAddressesKey,
            CNContactPostalAddressesKey,
            CNContactBirthdayKey,
            CNContactJobTitleKey,
            CNContactDepartmentNameKey,
            CNContactOrganizationNameKey,
            CNContactNoteKey,
            CNContactImageDataKey,
            CNContactThumbnailImageDataKey,
            CNContactUrlAddressesKey,
            CNContactInstantMessageAddressesKey,
            CNContactSocialProfilesKey
        ]
        
        # Create a fetch request
        request = Contacts.CNContactFetchRequest.alloc().initWithKeysToFetch_(keys_to_fetch)
        
        # Fetch all contacts
        contacts = []
        
        def contact_enumeration_handler(contact, stop):
            contacts.append(contact)
        
        store.enumerateContactsWithFetchRequest_error_usingBlock_(
            request, None, contact_enumeration_handler
        )
        
        logger.info(f"Retrieved {len(contacts)} contacts from MacBook")
        return contacts
        
    except Exception as e:
        logger.error(f"Error fetching contacts: {e}")
        return []

def format_contact_for_api(contact):
    """Format contact data into a Python dictionary for API response"""
    if not CONTACTS_AVAILABLE:
        return None
    
    def safe_get(contact, method_name, default=''):
        """Safely get a contact property, handling cases where it wasn't fetched."""
        try:
            method = getattr(contact, method_name)
            result = method()
            return str(result) if result else default
        except:
            return default
    
    contact_data = {
        'identifier': str(contact.identifier()),
        'firstName': safe_get(contact, 'givenName'),
        'lastName': safe_get(contact, 'familyName'),
        'middleName': safe_get(contact, 'middleName'),
        'nickname': safe_get(contact, 'nickname'),
        'jobTitle': safe_get(contact, 'jobTitle'),
        'departmentName': safe_get(contact, 'departmentName'),
        'organizationName': safe_get(contact, 'organizationName'),
        'note': safe_get(contact, 'note'),
        'phoneNumbers': [],
        'emailAddresses': [],
        'postalAddresses': [],
        'urlAddresses': [],
        'instantMessageAddresses': [],
        'socialProfiles': [],
        'birthday': '',
        'hasImage': False,
        'hasThumbnail': False
    }
    
    # Handle birthday
    try:
        birthday = contact.birthday()
        if birthday and birthday.year() and birthday.month() and birthday.day():
            contact_data['birthday'] = f"{birthday.year():04d}-{birthday.month():02d}-{birthday.day():02d}"
    except:
        pass
    
    # Handle phone numbers
    try:
        for phone in contact.phoneNumbers():
            phone_data = {
                'label': str(phone.label()) if phone.label() else 'Other',
                'value': str(phone.value().stringValue()) if phone.value() else ''
            }
            contact_data['phoneNumbers'].append(phone_data)
    except:
        pass
    
    # Handle email addresses
    try:
        for email in contact.emailAddresses():
            email_data = {
                'label': str(email.label()) if email.label() else 'Other',
                'value': str(email.value()) if email.value() else ''
            }
            contact_data['emailAddresses'].append(email_data)
    except:
        pass
    
    # Handle postal addresses
    try:
        for address in contact.postalAddresses():
            addr = address.value()
            address_data = {
                'label': str(address.label()) if address.label() else 'Other',
                'street': str(addr.street()) if addr.street() else '',
                'city': str(addr.city()) if addr.city() else '',
                'state': str(addr.state()) if addr.state() else '',
                'postalCode': str(addr.postalCode()) if addr.postalCode() else '',
                'country': str(addr.country()) if addr.country() else '',
                'formatted': str(CNContactFormatter.stringFromPostalAddress_style_(addr, CNContactFormatterStyleMailingAddress))
            }
            contact_data['postalAddresses'].append(address_data)
    except:
        pass
    
    # Handle URL addresses
    try:
        for url in contact.urlAddresses():
            url_data = {
                'label': str(url.label()) if url.label() else 'Other',
                'value': str(url.value()) if url.value() else ''
            }
            contact_data['urlAddresses'].append(url_data)
    except:
        pass
    
    # Handle instant message addresses
    try:
        for im in contact.instantMessageAddresses():
            im_data = {
                'label': str(im.label()) if im.label() else 'Other',
                'service': str(im.value().service()) if im.value() else '',
                'username': str(im.value().username()) if im.value() else ''
            }
            contact_data['instantMessageAddresses'].append(im_data)
    except:
        pass
    
    # Handle social profiles
    try:
        for social in contact.socialProfiles():
            social_data = {
                'label': str(social.label()) if social.label() else 'Other',
                'service': str(social.value().service()) if social.value() else '',
                'username': str(social.value().username()) if social.value() else '',
                'urlString': str(social.value().urlString()) if social.value() else ''
            }
            contact_data['socialProfiles'].append(social_data)
    except:
        pass
    
    # Check for images
    try:
        contact_data['hasImage'] = contact.imageData() is not None
    except:
        contact_data['hasImage'] = False
    
    try:
        contact_data['hasThumbnail'] = contact.thumbnailImageData() is not None
    except:
        contact_data['hasThumbnail'] = False
    
    return contact_data

def filter_contacts(contacts, filters):
    """Filter contacts based on provided criteria"""
    if not filters:
        return contacts
    
    filtered_contacts = []
    
    for contact in contacts:
        include_contact = True
        
        # Filter by has email addresses
        if filters.get('has_email', False):
            if not contact.get('emailAddresses') or len(contact['emailAddresses']) == 0:
                include_contact = False
        
        # Filter by has phone numbers
        if filters.get('has_phone', False):
            if not contact.get('phoneNumbers') or len(contact['phoneNumbers']) == 0:
                include_contact = False
        
        # Filter by has postal addresses
        if filters.get('has_address', False):
            if not contact.get('postalAddresses') or len(contact['postalAddresses']) == 0:
                include_contact = False
        
        # Filter by has profile image
        if filters.get('has_image', False):
            if not contact.get('hasImage', False):
                include_contact = False
        
        # Filter by name (partial match)
        if filters.get('name_contains'):
            name_query = filters['name_contains'].lower()
            full_name = f"{contact.get('firstName', '')} {contact.get('lastName', '')}".lower()
            nickname = contact.get('nickname', '').lower()
            
            if name_query not in full_name and name_query not in nickname:
                include_contact = False
        
        # Filter by organization
        if filters.get('organization_contains'):
            org_query = filters['organization_contains'].lower()
            organization = contact.get('organizationName', '').lower()
            
            if org_query not in organization:
                include_contact = False
        
        if include_contact:
            filtered_contacts.append(contact)
    
    return filtered_contacts

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
def ai_route_request(text):
    """
    Use AI to intelligently route user requests to the most appropriate endpoint.
    Returns a dictionary with routing information.
    """
    if not text or not genai:
        return {'route': 'gemini', 'confidence': 0.0, 'reasoning': 'No text or Gemini unavailable'}
    
    try:
        # Get system information for context
        system_info = get_system_info()
        
        # Build available services context
        services_context = ""
        if system_info:
            services_context = "Available services:\n"
            for service_id, service in system_info['available_integrations'].items():
                auth_status = system_info['current_authentications'].get(service_id, {})
                status = "✅ Available" if auth_status.get('authenticated', False) else "❌ Unavailable"
                services_context += f"- {service['name']} ({service_id}): {status}\n"
                services_context += f"  Capabilities: {', '.join(service['capabilities'])}\n"
        
        # Create the routing prompt
        routing_prompt = f"""
You are an intelligent request router for an AI assistant named Iris. Analyze the user's request and determine the most appropriate service to handle it.

{services_context}

User Request: "{text}"

Available routing options:
1. "spotify" - For music-related requests (play songs, create playlists, search music, recommendations)
2. "contacts" - For contact lookup, finding phone numbers, email addresses, contact information
3. "gmail" - For composing, sending, or managing emails
4. "gemini" - For general conversation, questions, or requests that don't fit other services

Consider the primary intent of the request. If a request could fit multiple services, choose the most specific one.

Examples:
- "Play some music" → spotify
- "Find John's phone number" → contacts  
- "Send an email to Sarah" → gmail
- "What's the weather like?" → gemini
- "Find Philip's email address" → contacts (contact lookup, not email composition)

Respond with ONLY a JSON object in this exact format:
{{
    "route": "service_name",
    "confidence": 0.95,
    "reasoning": "Brief explanation of why this service was chosen"
}}
"""

        # Get AI routing decision
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(routing_prompt)
        
        # Parse the JSON response
        try:
            routing_data = json.loads(response.text.strip())
            logger.info(f"AI routing decision: {routing_data}")
            return routing_data
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI routing response: {e}")
            # Fallback to keyword-based detection
            return fallback_route_request(text)
            
    except Exception as e:
        logger.error(f"AI routing failed: {e}")
        # Fallback to keyword-based detection
        return fallback_route_request(text)

def fallback_route_request(text):
    """
    Fallback routing using keyword detection when AI routing fails
    """
    if not text:
        return {'route': 'gemini', 'confidence': 0.0, 'reasoning': 'No text provided'}
    
    text_lower = text.lower()
    
    # Music keywords
    music_keywords = [
        'music', 'song', 'songs', 'play', 'playing', 'playlist', 'artist', 'album',
        'spotify', 'listen', 'hear', 'track', 'tracks', 'recommend', 'suggest', 
        'genre', 'band', 'singer', 'musician', 'concert', 'lyrics'
    ]
    
    # Contact keywords (prioritize over email for lookups)
    contact_keywords = [
        'contact', 'contacts', 'phone number', 'phone', 'call', 'calling',
        'find', 'lookup', 'search for', 'who is', 'what is', 'where is', 
        'how to contact', 'get in touch', 'reach', 'contact info', 
        'contact information', 'details', 'address', 'location', 
        'business card', 'directory', 'email of', 'email for'
    ]
    
    # Email keywords (for composition, not lookup)
    email_keywords = [
        'send email', 'compose email', 'write email', 'mail', 'send mail',
        'compose mail', 'write mail', 'message', 'send message',
        'email to', 'mail to', 'send to', 'compose to', 'write to',
        'draft', 'compose', 'reply', 'forward', 'inbox', 'outbox'
    ]
    
    # Check for music
    for keyword in music_keywords:
        if keyword in text_lower:
            return {'route': 'spotify', 'confidence': 0.8, 'reasoning': f'Contains music keyword: {keyword}'}
    
    # Check for contact lookup (prioritize over email)
    for keyword in contact_keywords:
        if keyword in text_lower:
            return {'route': 'contacts', 'confidence': 0.8, 'reasoning': f'Contains contact keyword: {keyword}'}
    
    # Check for email composition
    for keyword in email_keywords:
        if keyword in text_lower:
            return {'route': 'gmail', 'confidence': 0.8, 'reasoning': f'Contains email keyword: {keyword}'}
    
    # Default to Gemini
    return {'route': 'gemini', 'confidence': 0.5, 'reasoning': 'No specific service keywords detected'}

# Legacy functions kept for backward compatibility
def is_music_related_request(text):
    """Legacy function - use ai_route_request instead"""
    routing = ai_route_request(text)
    return routing['route'] == 'spotify'

def is_email_related_request(text):
    """Legacy function - use ai_route_request instead"""
    routing = ai_route_request(text)
    return routing['route'] == 'gmail'

def is_contact_related_request(text):
    """Legacy function - use ai_route_request instead"""
    routing = ai_route_request(text)
    return routing['route'] == 'contacts'

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

# Call Gmail agent endpoint
def call_gmail_agent(user_request):
    """
    Call the Gmail agent endpoint with the user's email request
    """
    try:
        logger.info(f"Calling Gmail agent with request: {user_request}")
        
        # Gmail agent endpoint
        gmail_url = "http://localhost:8000/chat"
        
        # Prepare the request payload
        payload = {
            "text": user_request
        }
        
        # Make the request to Gmail agent
        response = requests.post(
            gmail_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30  # 30 second timeout
        )
        
        if response.status_code == 200:
            gmail_response = response.json()
            logger.info(f"Gmail agent response: {gmail_response}")
            return gmail_response
        else:
            logger.error(f"Gmail agent returned status {response.status_code}: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Gmail agent: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error calling Gmail agent: {str(e)}")
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

# Process email request through Gmail agent and Gemini
def process_email_request(voice_input):
    """
    Process email-related requests through Gmail agent and then through Gemini
    """
    try:
        logger.info(f"Processing email request: {voice_input}")
        
        # Call Gmail agent
        gmail_response = call_gmail_agent(voice_input)
        
        if not gmail_response:
            # Enhanced error message for Gmail connection issues
            return "I'm having trouble connecting to the email service. To use email features, please make sure the Gmail agent is running and properly configured."
        
        # Check if the Gmail response indicates authentication/connection issues
        if isinstance(gmail_response, dict):
            gmail_text = str(gmail_response).lower()
        else:
            gmail_text = str(gmail_response).lower()
        
        # Check for common Gmail error patterns
        gmail_error_patterns = [
            'not authenticated', 'authentication failed', 'authorization required',
            'login required', 'permission denied', 'access denied', 'token expired',
            'invalid token', 'unable to access', 'cannot connect', 'integration failed',
            'oauth', 'credentials', 'api key', 'connection refused', 'service down', 'unreachable'
        ]
        
        has_gmail_error = any(pattern in gmail_text for pattern in gmail_error_patterns)
        
        if has_gmail_error:
            logger.warning(f"Gmail error detected in response: {gmail_response}")
            return "I'm having trouble accessing your email service. Please make sure the Gmail agent is running and properly authenticated."
        
        # Process Gmail response through Gemini for user-friendly output
        if genai and os.getenv('GEMINI_API_KEY'):
            try:
                # Get system information for context
                system_info = get_system_info()
                
                # Build system context for email processing
                system_context = ""
                if system_info:
                    gmail_auth = system_info['current_authentications'].get('gmail', {})
                    gmail_integration = system_info['available_integrations'].get('gmail', {})
                    
                    system_context = f"""

## SYSTEM INFORMATION
You are Iris, an AI assistant with access to Gmail integration:

### Gmail Integration Status:
- **Status**: {'✅ Connected' if gmail_auth.get('authenticated', False) else '❌ Not connected'}
- **Capabilities**: {', '.join(gmail_integration.get('capabilities', []))}
"""
                    if gmail_auth.get('authenticated') and 'user' in gmail_auth:
                        system_context += f"- **Connected as**: {gmail_auth['user'].get('email', 'Unknown')}\n"
                
                # Get conversation context for email processing
                conversation_context = context_manager.get_context_for_prompt(voice_input, include_recent=3)
                
                # Create a prompt to make the Gmail response more user-friendly
                email_processing_prompt = f"""You are Iris, a helpful AI assistant. The user made an email request, and here's what the email service found:

{system_context}

## CONVERSATION CONTEXT
{conversation_context}

User's request: {voice_input}
Email service response: {gmail_response}

Please provide a friendly, conversational response to the user about what was found. Make it sound natural and helpful, as if you're personally helping them with their email request. Keep it concise but informative.

**CONTEXT AWARENESS**: Use the conversation context above to provide more personalized email assistance. Reference previous email requests, recipients mentioned, or email topics the user has discussed.

IMPORTANT: If the email service response indicates any authentication, connection, or access issues, you MUST tell the user to check their Gmail agent configuration.

FORMATTING GUIDELINES:
- Use markdown formatting when appropriate to make your responses more readable
- Use emojis sparingly but effectively (📧 for email-related content)
- Keep responses conversational and helpful
- If an email was sent successfully, confirm the details (recipient, subject)
- If there were issues, explain what went wrong and how to fix it

RESPONSE STYLE:
- Be warm and helpful
- Use "I" when referring to actions you took
- Be specific about what happened
- Offer next steps if appropriate
- Keep it concise but informative

Please provide a natural, helpful response to the user."""

                # Configure generation settings for email processing
                generation_config = genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=500,
                )
                
                # Safety settings
                safety_settings = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                ]
                
                model = genai.GenerativeModel('gemini-2.5-flash')

                logger.info("Processing Gmail response through Gemini...")

                response = model.generate_content(
                    email_processing_prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings,
                    request_options={'timeout': 15}
                )

                if response and hasattr(response, 'text') and response.text:
                    processed_response = response.text.strip()
                    logger.info(f"Gemini processed email response: {processed_response}")
                    
                    # Add email interaction to context
                    context_manager.add_interaction(voice_input, processed_response, "email")
                    
                    # Extract and update user preferences from email interaction
                    extracted_preferences = context_manager.extract_preferences_from_interaction(voice_input, processed_response)
                    if extracted_preferences:
                        context_manager.update_user_preferences(extracted_preferences)
                    
                    return processed_response
                else:
                    logger.warning("Gemini returned empty response for email request")
                    fallback_response = f"I've processed your email request: {gmail_response}"
                    
                    # Add fallback interaction to context
                    context_manager.add_interaction(voice_input, fallback_response, "email")
                    
                    return fallback_response
                    
            except Exception as gemini_error:
                logger.warning(f"Gemini processing failed for email request: {gemini_error}")
                return f"I've processed your email request: {gmail_response}"
        else:
            # Fallback if Gemini is not available
            logger.warning("Gemini not available, returning raw Gmail response")
            return f"I've processed your email request: {gmail_response}"
            
    except Exception as e:
        logger.error(f"Error processing email request: {str(e)}")
        return "I'm having trouble processing your email request. Please make sure the Gmail agent is running and properly configured."

# Process contact request through contacts API and Gemini
def process_contact_request(voice_input):
    """
    Process contact-related requests through contacts API and then through Gemini
    """
    try:
        logger.info(f"Processing contact request: {voice_input}")
        
        if not CONTACTS_AVAILABLE:
            return "I don't have access to your contacts. This feature requires macOS and proper permissions to access your Contacts app."
        
        # Extract potential names from the voice input
        import re
        
        # Common patterns for names and relationships
        name_patterns = [
            r"(\b[A-Z][a-z]+\b)",  # Capitalized words (potential names)
            r"my (\w+)",  # "my boss", "my mom", etc.
            r"(\w+)'s",  # "John's", "Sarah's", etc.
        ]
        
        potential_names = []
        for pattern in name_patterns:
            matches = re.findall(pattern, voice_input)
            potential_names.extend(matches)
        
        # Remove common words that aren't names
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'my', 'me', 'i', 'you', 'he', 'she', 'it', 'we', 'they'}
        potential_names = [name for name in potential_names if name.lower() not in common_words and len(name) > 2]
        
        # Search for contacts if we found potential names
        contact_results = []
        if potential_names:
            for name in potential_names[:3]:  # Limit to first 3 potential names
                try:
                    # Search contacts for this name
                    response = requests.post('http://127.0.0.1:5001/api/contacts/search', 
                                           json={'query': name, 'limit': 3}, timeout=5)
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('success') and result.get('contacts'):
                            contact_results.extend(result['contacts'])
                except Exception as e:
                    logger.warning(f"Error searching contacts for '{name}': {e}")
        
        # Process contact results through Gemini for user-friendly output
        if genai and os.getenv('GEMINI_API_KEY'):
            try:
                # Get system information for context
                system_info = get_system_info()
                
                # Build system context for contact processing
                system_context = ""
                if system_info:
                    contacts_auth = system_info['current_authentications'].get('contacts', {})
                    contacts_integration = system_info['available_integrations'].get('contacts', {})
                    
                    system_context = f"""

## SYSTEM INFORMATION
You are Iris, an AI assistant with access to Contacts integration:

### Contacts Integration Status:
- **Status**: {'✅ Connected' if contacts_auth.get('authenticated', False) else '❌ Not connected'}
- **Capabilities**: {', '.join(contacts_integration.get('capabilities', []))}
"""
                    if contacts_auth.get('authenticated') and 'contact_count' in contacts_auth:
                        system_context += f"- **Available contacts**: {contacts_auth['contact_count']}\n"
                
                # Get conversation context for contact processing
                conversation_context = context_manager.get_context_for_prompt(voice_input, include_recent=3)
                
                # Create a prompt to make the contact response more user-friendly
                contact_processing_prompt = f"""You are Iris, a helpful AI assistant. The user made a contact-related request, and here's what I found in their contacts:

{system_context}

{conversation_context}

User's request: {voice_input}
Contact search results: {contact_results}

Please provide a friendly, conversational response to the user about what was found. Make it sound natural and helpful, as if you're personally helping them with their contact request. Keep it concise but informative.

**CONTEXT AWARENESS**: Use the conversation context above to provide more personalized contact assistance. Reference previous contact requests or people the user has mentioned.

**CONTACT RESPONSE GUIDELINES**:
- If contacts were found, list them clearly with their information
- If no contacts were found, suggest alternative ways to help
- If the user is looking for someone specific, help them refine their search
- Be helpful and offer to search for more specific information if needed
- If they're looking for contact information for email or calling, provide the relevant details

FORMATTING GUIDELINES:
- Use markdown formatting when appropriate to make your responses more readable
- Use **bold** for contact names and important information
- Use bullet points (-) when listing multiple contacts
- Use `code formatting` for phone numbers and email addresses
- Be warm and helpful in your tone

Respond as Iris:"""

                # Configure generation settings for contact processing
                generation_config = genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.8,
                    top_k=40,
                    max_output_tokens=500,
                )
                
                # Safety settings
                safety_settings = [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                ]
                
                model = genai.GenerativeModel('gemini-2.5-flash')

                logger.info("Processing contact results through Gemini...")

                response = model.generate_content(
                    contact_processing_prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings,
                    request_options={'timeout': 15}
                )

                if response and hasattr(response, 'text') and response.text:
                    processed_response = response.text.strip()
                    logger.info(f"Gemini processed contact response: {processed_response}")
                    
                    # Add contact interaction to context
                    context_manager.add_interaction(voice_input, processed_response, "contacts")
                    
                    return processed_response
                else:
                    logger.warning("Gemini returned empty response for contact request")
                    fallback_response = f"I found some contacts for you: {contact_results}"
                    
                    # Add fallback interaction to context
                    context_manager.add_interaction(voice_input, fallback_response, "contacts")
                    
                    return fallback_response
                    
            except Exception as gemini_error:
                logger.warning(f"Gemini processing failed for contact request: {gemini_error}")
                return f"I found some contacts for you: {contact_results}"
        else:
            # Fallback if Gemini is not available
            logger.warning("Gemini not available, returning raw contact response")
            return f"I found some contacts for you: {contact_results}"
            
    except Exception as e:
        logger.error(f"Error processing contact request: {str(e)}")
        return "I'm having trouble processing your contact request. Please make sure contacts access is properly configured."

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
    Use AI routing to intelligently determine the best service for user's voice input
    """
    if not voice_input:
        logger.warning("No voice input provided")
        return "I'm sorry, I couldn't process your request."
    
    # Use AI-powered routing to determine the best service
    routing = ai_route_request(voice_input)
    route = routing.get('route', 'gemini')
    confidence = routing.get('confidence', 0.0)
    reasoning = routing.get('reasoning', 'No reasoning provided')
    
    logger.info(f"AI routing decision: {route} (confidence: {confidence:.2f}) - {reasoning}")
    
    # Route to appropriate service based on AI decision
    if route == 'spotify':
        logger.info("Routing to Spotify agent")
        return process_music_request(voice_input)
    elif route == 'contacts':
        logger.info("Routing to contacts processing")
        return process_contact_request(voice_input)
    elif route == 'gmail':
        logger.info("Routing to Gmail agent")
        return process_email_request(voice_input)
    
    # If not music, email, or contact-related, use Gemini for general responses
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
10. **CONTACTS INTEGRATION**: If the user mentions names of people (like "John", "Sarah", "my boss", "mom", etc.) in the context of emails, calls, or contact information, you can help them by:
    - Searching their contacts to find the person's email address or phone number
    - Suggesting using the contacts feature to resolve names to contact information
    - Helping them find contact details for people they mention
    - If they say something like "send email to John" but don't know John's email, you can suggest using the contacts lookup feature

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
    """Process refined command and route to appropriate agent"""
    try:
        data = request.get_json()
        refined_command = data.get('refined_command', '')
        
        if not refined_command:
            return jsonify({'success': False, 'error': 'No refined command provided'}), 400
        
        logger.info(f"Processing command: {refined_command}")
        
        # Check if this is an email-related request
        if is_email_related_request(refined_command):
            logger.info("Email request detected, routing to Gmail agent")
            try:
                # Process through Gmail agent
                gmail_response = call_gmail_agent(refined_command)
                
                if gmail_response:
                    return jsonify({
                        'success': True,
                        'refined_command': refined_command,
                        'agent_response': gmail_response,
                        'task_type': 'email',
                        'next_steps': 'Email processed by Gmail agent'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Gmail agent is not responding. Please make sure it is running on port 8000.'
                    }), 503
                    
            except Exception as gmail_error:
                logger.error(f"Gmail agent error: {str(gmail_error)}")
                return jsonify({
                    'success': False,
                    'error': f'Gmail agent error: {str(gmail_error)}'
                }), 500
        
        # Check if this is a music-related request
        elif is_music_related_request(refined_command):
            logger.info("Music request detected, routing to Spotify agent")
            try:
                # Process through Spotify agent
                spotify_response = call_spotify_agent(refined_command)
                
                if spotify_response:
                    return jsonify({
                        'success': True,
                        'refined_command': refined_command,
                        'agent_response': spotify_response,
                        'task_type': 'music',
                        'next_steps': 'Music request processed by Spotify agent'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Spotify agent is not responding. Please make sure it is running on port 8005.'
                    }), 503
                    
            except Exception as spotify_error:
                logger.error(f"Spotify agent error: {str(spotify_error)}")
                return jsonify({
                    'success': False,
                    'error': f'Spotify agent error: {str(spotify_error)}'
                }), 500
        
        # For other requests, use Gemini for general processing
        else:
            logger.info("General request, processing with Gemini")
            try:
                # Process with Gemini
                gemini_response = get_gemini_direct_response(refined_command)
                
                return jsonify({
                    'success': True,
                    'refined_command': refined_command,
                    'gemini_response': gemini_response,
                    'task_type': 'general',
                    'next_steps': 'Request processed by Gemini AI'
                })
                
            except Exception as gemini_error:
                logger.error(f"Gemini processing error: {str(gemini_error)}")
                return jsonify({
                    'success': False,
                    'error': f'Gemini processing error: {str(gemini_error)}'
                }), 500
        
    except Exception as e:
        logger.error(f"Command processing error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Command processing failed: {str(e)}'
        }), 500

@app.route('/api/gmail/auth')
def gmail_auth():
    """Get Gmail authentication URL"""
    try:
        # Gmail OAuth server runs on port 8080
        gmail_auth_url = "http://localhost:8080"
        
        # Check if Gmail agent is running by checking its health endpoint
        try:
            import requests
            health_response = requests.get("http://localhost:8000/health", timeout=5)
            if health_response.status_code == 200:
                return jsonify({
                    'success': True,
                    'auth_url': gmail_auth_url,
                    'message': 'Gmail authentication URL ready'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Gmail agent is not responding. Please make sure it is running on port 8000.'
                }), 503
        except requests.exceptions.ConnectionError:
            return jsonify({
                'success': False,
                'error': 'Gmail agent is not running. Please start the Gmail agent first.'
            }), 503
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error checking Gmail agent status: {str(e)}'
            }), 500
            
    except Exception as e:
        logger.error(f"Gmail auth error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Gmail authentication setup failed: {str(e)}'
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
        
        # Clean the text for TTS to remove markdown and special characters
        cleaned_text = clean_text_for_tts(text)
        
        logger.info(f"Converting text to speech: '{cleaned_text[:50]}...' with voice {voice_id}")
        
        # Prepare the request payload
        payload = {
            "text": cleaned_text,
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
                    'endpoint': 'http://localhost:8000/chat',
                    'status': 'available'
                },
                'contacts': {
                    'name': 'Contacts',
                    'description': 'MacBook contacts database for contact lookup, email resolution, and contact management',
                    'icon': '👥',
                    'capabilities': [
                        'Search contacts by name, email, or phone',
                        'Resolve names to email addresses',
                        'Find contact information and details',
                        'Filter contacts by criteria (has email, phone, etc.)',
                        'Get contact statistics and insights',
                        'Validate contact existence before actions'
                    ],
                    'endpoint': 'http://localhost:5001/api/contacts',
                    'status': 'available' if CONTACTS_AVAILABLE else 'unavailable'
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
        
        # Check Gmail authentication status
        try:
            gmail_status = check_gmail_auth_status()
            system_info['current_authentications']['gmail'] = gmail_status
        except Exception as e:
            logger.warning(f"Could not check Gmail auth status: {e}")
            system_info['current_authentications']['gmail'] = {
                'authenticated': False,
                'error': str(e)
            }
        
        # Check Contacts authentication status
        try:
            contacts_status = check_contacts_auth_status()
            system_info['current_authentications']['contacts'] = contacts_status
        except Exception as e:
            logger.warning(f"Could not check Contacts auth status: {e}")
            system_info['current_authentications']['contacts'] = {
                'authenticated': False,
                'error': str(e)
            }
        
        # For other integrations, we'll add status checks as they're implemented
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

def check_gmail_auth_status():
    """Check Gmail agent authentication status"""
    try:
        # Check if Gmail agent is running and accessible
        gmail_url = "http://localhost:8000/health"
        
        response = requests.get(gmail_url, timeout=5)
        
        if response.status_code == 200:
            health_data = response.json()
            gmail_api_status = health_data.get('gmail_api', 'disconnected')
            
            if gmail_api_status == 'connected':
                return {
                    'authenticated': True,
                    'status': 'active',
                    'agent_address': health_data.get('agent_address'),
                    'gmail_api': gmail_api_status
                }
            else:
                return {
                    'authenticated': False,
                    'status': 'gmail_api_disconnected',
                    'error': 'Gmail API not connected'
                }
        else:
            return {
                'authenticated': False,
                'status': 'agent_unreachable',
                'error': f'Gmail agent returned status {response.status_code}'
            }
            
    except requests.exceptions.ConnectionError:
        return {
            'authenticated': False,
            'status': 'agent_not_running',
            'error': 'Gmail agent is not running'
        }
    except requests.exceptions.Timeout:
        return {
            'authenticated': False,
            'status': 'agent_timeout',
            'error': 'Gmail agent timeout'
        }
    except Exception as e:
        return {
            'authenticated': False,
            'error': f'Status check failed: {str(e)}'
        }

def check_contacts_auth_status():
    """Check Contacts framework authentication status"""
    try:
        if not CONTACTS_AVAILABLE:
            return {
                'authenticated': False,
                'status': 'framework_unavailable',
                'error': 'Contacts framework not available. Requires macOS and PyObjC.'
            }
        
        # Test contacts access by trying to get authorization status
        try:
            auth_status = Contacts.CNContactStore.authorizationStatusForEntityType_(Contacts.CNEntityTypeContacts)
            
            if auth_status == Contacts.CNAuthorizationStatusAuthorized:
                # Test actual contact access
                test_contacts = get_all_contacts_from_mac()
                if test_contacts:
                    return {
                        'authenticated': True,
                        'status': 'active',
                        'contact_count': len(test_contacts),
                        'message': f'Access to {len(test_contacts)} contacts granted'
                    }
                else:
                    return {
                        'authenticated': False,
                        'status': 'no_contacts',
                        'error': 'Contacts access granted but no contacts found'
                    }
            elif auth_status == Contacts.CNAuthorizationStatusDenied:
                return {
                    'authenticated': False,
                    'status': 'denied',
                    'error': 'Contacts access denied. Please enable in System Preferences > Security & Privacy > Privacy > Contacts'
                }
            elif auth_status == Contacts.CNAuthorizationStatusRestricted:
                return {
                    'authenticated': False,
                    'status': 'restricted',
                    'error': 'Contacts access restricted (e.g., by parental controls)'
                }
            else:
                return {
                    'authenticated': False,
                    'status': 'not_determined',
                    'error': 'Contacts access not yet requested'
                }
                
        except Exception as e:
            return {
                'authenticated': False,
                'status': 'access_error',
                'error': f'Error checking contacts access: {str(e)}'
            }
            
    except Exception as e:
        return {
            'authenticated': False,
            'error': f'Contacts status check failed: {str(e)}'
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

@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    """Get all contacts with optional filtering"""
    try:
        if not CONTACTS_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Contacts framework not available. This feature requires macOS and PyObjC.'
            }), 503
        
        # Get query parameters for filtering
        filters = {}
        
        # Boolean filters
        if request.args.get('has_email', '').lower() in ['true', '1', 'yes']:
            filters['has_email'] = True
        if request.args.get('has_phone', '').lower() in ['true', '1', 'yes']:
            filters['has_phone'] = True
        if request.args.get('has_address', '').lower() in ['true', '1', 'yes']:
            filters['has_address'] = True
        if request.args.get('has_image', '').lower() in ['true', '1', 'yes']:
            filters['has_image'] = True
        
        # String filters
        if request.args.get('name_contains'):
            filters['name_contains'] = request.args.get('name_contains')
        if request.args.get('organization_contains'):
            filters['organization_contains'] = request.args.get('organization_contains')
        
        # Get limit and offset for pagination
        limit = int(request.args.get('limit', 100))  # Default to 100 contacts
        offset = int(request.args.get('offset', 0))  # Default to start from beginning
        
        logger.info(f"Fetching contacts with filters: {filters}, limit: {limit}, offset: {offset}")
        
        # Get all contacts from MacBook
        raw_contacts = get_all_contacts_from_mac()
        
        if not raw_contacts:
            return jsonify({
                'success': True,
                'contacts': [],
                'total_count': 0,
                'filtered_count': 0,
                'filters_applied': filters,
                'message': 'No contacts found or contacts access denied'
            })
        
        # Format contacts for API response
        formatted_contacts = []
        for contact in raw_contacts:
            formatted_contact = format_contact_for_api(contact)
            if formatted_contact:
                formatted_contacts.append(formatted_contact)
        
        # Apply filters
        filtered_contacts = filter_contacts(formatted_contacts, filters)
        
        # Apply pagination
        total_count = len(formatted_contacts)
        filtered_count = len(filtered_contacts)
        paginated_contacts = filtered_contacts[offset:offset + limit]
        
        # Generate summary statistics
        stats = {
            'total_contacts': total_count,
            'filtered_contacts': filtered_count,
            'returned_contacts': len(paginated_contacts),
            'contacts_with_email': len([c for c in formatted_contacts if c.get('emailAddresses')]),
            'contacts_with_phone': len([c for c in formatted_contacts if c.get('phoneNumbers')]),
            'contacts_with_address': len([c for c in formatted_contacts if c.get('postalAddresses')]),
            'contacts_with_image': len([c for c in formatted_contacts if c.get('hasImage', False)])
        }
        
        logger.info(f"Returning {len(paginated_contacts)} contacts (filtered from {total_count} total)")
        
        return jsonify({
            'success': True,
            'contacts': paginated_contacts,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total_count': total_count,
                'filtered_count': filtered_count,
                'has_more': offset + limit < filtered_count
            },
            'filters_applied': filters,
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"Error fetching contacts: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to fetch contacts: {str(e)}'
        }), 500

@app.route('/api/contacts/search', methods=['POST'])
def search_contacts():
    """Search contacts with advanced filtering options"""
    try:
        if not CONTACTS_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Contacts framework not available. This feature requires macOS and PyObjC.'
            }), 503
        
        data = request.get_json() or {}
        search_query = data.get('query', '').strip()
        filters = data.get('filters', {})
        limit = data.get('limit', 50)
        offset = data.get('offset', 0)
        
        logger.info(f"Searching contacts with query: '{search_query}', filters: {filters}")
        
        # Get all contacts
        raw_contacts = get_all_contacts_from_mac()
        
        if not raw_contacts:
            return jsonify({
                'success': True,
                'contacts': [],
                'total_count': 0,
                'search_query': search_query,
                'message': 'No contacts found or contacts access denied'
            })
        
        # Format contacts
        formatted_contacts = []
        for contact in raw_contacts:
            formatted_contact = format_contact_for_api(contact)
            if formatted_contact:
                formatted_contacts.append(formatted_contact)
        
        # Apply search query if provided
        if search_query:
            search_results = []
            query_lower = search_query.lower()
            
            for contact in formatted_contacts:
                # Search in name fields
                full_name = f"{contact.get('firstName', '')} {contact.get('lastName', '')}".lower()
                nickname = contact.get('nickname', '').lower()
                organization = contact.get('organizationName', '').lower()
                job_title = contact.get('jobTitle', '').lower()
                
                # Search in email addresses
                emails = [email.get('value', '').lower() for email in contact.get('emailAddresses', [])]
                
                # Search in phone numbers
                phones = [phone.get('value', '').lower() for phone in contact.get('phoneNumbers', [])]
                
                # Check if query matches any field
                if (query_lower in full_name or 
                    query_lower in nickname or 
                    query_lower in organization or 
                    query_lower in job_title or
                    any(query_lower in email for email in emails) or
                    any(query_lower in phone for phone in phones)):
                    search_results.append(contact)
            
            formatted_contacts = search_results
        
        # Apply additional filters
        filtered_contacts = filter_contacts(formatted_contacts, filters)
        
        # Apply pagination
        total_count = len(formatted_contacts)
        paginated_contacts = filtered_contacts[offset:offset + limit]
        
        return jsonify({
            'success': True,
            'contacts': paginated_contacts,
            'search_query': search_query,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total_count': total_count,
                'has_more': offset + limit < total_count
            },
            'filters_applied': filters
        })
        
    except Exception as e:
        logger.error(f"Error searching contacts: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to search contacts: {str(e)}'
        }), 500

@app.route('/api/contacts/stats')
def get_contacts_stats():
    """Get statistics about contacts"""
    try:
        if not CONTACTS_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Contacts framework not available. This feature requires macOS and PyObjC.'
            }), 503
        
        # Get all contacts
        raw_contacts = get_all_contacts_from_mac()
        
        if not raw_contacts:
            return jsonify({
                'success': True,
                'stats': {
                    'total_contacts': 0,
                    'contacts_with_email': 0,
                    'contacts_with_phone': 0,
                    'contacts_with_address': 0,
                    'contacts_with_image': 0
                },
                'message': 'No contacts found or contacts access denied'
            })
        
        # Format contacts and calculate stats
        formatted_contacts = []
        for contact in raw_contacts:
            formatted_contact = format_contact_for_api(contact)
            if formatted_contact:
                formatted_contacts.append(formatted_contact)
        
        stats = {
            'total_contacts': len(formatted_contacts),
            'contacts_with_email': len([c for c in formatted_contacts if c.get('emailAddresses')]),
            'contacts_with_phone': len([c for c in formatted_contacts if c.get('phoneNumbers')]),
            'contacts_with_address': len([c for c in formatted_contacts if c.get('postalAddresses')]),
            'contacts_with_image': len([c for c in formatted_contacts if c.get('hasImage', False)]),
            'contacts_with_organization': len([c for c in formatted_contacts if c.get('organizationName')]),
            'contacts_with_birthday': len([c for c in formatted_contacts if c.get('birthday')])
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting contacts stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to get contacts stats: {str(e)}'
        }), 500

if __name__ == '__main__':
    logger.info("Starting Vocal Agent Frontend...")
    
    # Initialize context manager with a default session
    context_manager.start_new_session()
    logger.info("Context manager initialized with default session")
    
    logger.info("Starting standard Flask server...")
    logger.info("Please open http://127.0.0.1:5001 in your browser")
    app.run(debug=True, host='127.0.0.1', port=5001)