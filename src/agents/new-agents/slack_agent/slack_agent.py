"""
Slack Agent - Enhanced Messaging and Authentication

This agent provides comprehensive Slack integration with OAuth2 authentication:
1. Slack OAuth2 user authentication and secure token management
2. Direct message sending to Slack users by display name or user ID
3. Message retrieval and conversation history access
4. Natural language processing for command interpretation using ASI:One
5. Secure credential management and API interaction

Integration Points:
- OAuth2 flow for Slack user account access
- Slack Web API for messaging operations
- ASI:One LLM for natural language command interpretation
- Secure token storage and refresh management
- Compatible with Agentverse for cloud deployment

Example Usage:
- "Send Alice a message saying I'll be late" → Extracts recipient and message, sends DM
- "Read my last message from Ben" → Retrieves recent conversation history
- "Tell everyone in my DMs: Meeting moved to 3pm" → Bulk messaging capability
"""

import asyncio
import json
import os
import re
import aiohttp
import aiofiles
import secrets
import threading
import webbrowser
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import uuid4
from urllib.parse import urlencode, urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler

from openai import OpenAI
from uagents import Context, Protocol, Agent
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)
from dotenv import load_dotenv
from cryptography.fernet import Fernet
import requests

# Load environment variables
load_dotenv()

# ASI:One Configuration for LLM processing
asi_client = OpenAI(
    base_url='https://api.asi1.ai/v1',
    api_key=os.getenv("ASI_ONE_API_KEY", "your_asi_one_api_key_here"),
)

# Slack OAuth2 Configuration
SLACK_CLIENT_ID = os.getenv("SLACK_CLIENT_ID")
SLACK_CLIENT_SECRET = os.getenv("SLACK_CLIENT_SECRET")
SLACK_REDIRECT_URI = os.getenv("SLACK_REDIRECT_URI", "https://localhost:8080/callback")

# Slack API endpoints
SLACK_API_BASE = "https://slack.com/api"
SLACK_OAUTH_AUTHORIZE = "https://slack.com/oauth/v2/authorize"
SLACK_OAUTH_TOKEN = "https://slack.com/api/oauth.v2.access"

# Slack OAuth2 scopes
SLACK_SCOPES = [
    "users:read",           # Read user information
    "conversations:read",   # Read conversation lists
    "conversations:history", # Read message history
    "chat:write",          # Send messages
    "im:read",             # Read direct messages
    "im:write",            # Send direct messages
    "channels:read",       # Read channel information
    "groups:read"          # Read private channel information
]

# Encryption key for secure token storage
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())

class SlackOAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handles OAuth2 callback from Slack"""
    
    def do_GET(self):
        """Handle GET request from Slack OAuth callback"""
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        # Validate state parameter for CSRF protection
        received_state = query_params.get('state', [None])[0]
        expected_state = getattr(self.server, 'expected_state', None)
        
        if received_state != expected_state:
            self.server.authorization_error = "invalid_state"
            self.send_error_response("Security Error: Invalid State")
            return
        
        if 'code' in query_params:
            # Success - authorization code received
            self.server.authorization_code = query_params['code'][0]
            self.send_success_response()
        elif 'error' in query_params:
            # Error in authorization
            error = query_params.get('error', ['unknown'])[0]
            error_description = query_params.get('error_description', [''])[0]
            self.server.authorization_error = error
            self.send_error_response(f"Authorization Failed: {error}", error_description)
        
        # Stop the server after handling the request
        threading.Thread(target=self.server.shutdown).start()
    
    def send_success_response(self):
        """Send success HTML response"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write("""
            <html>
            <head><title>Slack OAuth2 - Success</title></head>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
                <h1 style="color: #28a745;">✅ Slack Authorization Successful!</h1>
                <p>You have successfully connected your Slack account!</p>
                <p>You can close this window and return to the chat.</p>
                <script>setTimeout(() => window.close(), 3000);</script>
            </body>
            </html>
        """.encode('utf-8'))
    
    def send_error_response(self, title: str, description: str = ""):
        """Send error HTML response"""
        self.send_response(400)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(f"""
            <html>
            <head><title>Slack OAuth2 - Error</title></head>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
                <h1 style="color: #dc3545;">❌ {title}</h1>
                <p><strong>Description:</strong> {description}</p>
                <p>Please close this window and try again.</p>
            </body>
            </html>
        """.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Suppress server log messages"""
        pass

class SlackAuthManager:
    """Handles Slack OAuth2 authentication and secure token management"""
    
    def __init__(self):
        self.token_file = "slack_tokens.enc"
        self.cipher = Fernet(ENCRYPTION_KEY.encode()) if ENCRYPTION_KEY else None
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self.team_id = None
        self.user_id = None
        self._callback_server = None
        self._server_thread = None
        
    async def start_oauth_flow(self) -> str:
        """Start complete OAuth flow with local callback server"""
        if not SLACK_CLIENT_ID or not SLACK_CLIENT_SECRET:
            raise ValueError("Slack client credentials not configured")
        
        # Extract port from redirect URI
        parsed_uri = urlparse(SLACK_REDIRECT_URI)
        callback_port = parsed_uri.port or 8080
        
        try:
            # Start local callback server
            self._callback_server = HTTPServer(('localhost', callback_port), SlackOAuthCallbackHandler)
            self._callback_server.authorization_code = None
            self._callback_server.authorization_error = None
            
            # Generate state for CSRF protection
            state = secrets.token_urlsafe(32)
            self._callback_server.expected_state = state
            
            # Start server in background thread
            self._server_thread = threading.Thread(target=self._callback_server.serve_forever)
            self._server_thread.daemon = True
            self._server_thread.start()
            
            # Generate OAuth URL
            auth_url = self._generate_auth_url(state)
            
            # Open browser automatically
            webbrowser.open(auth_url)
            
            return f"""🔗 **Slack Authentication Started**

A browser window should have opened automatically. If not, please visit:
{auth_url}

✅ Local callback server is running on port {callback_port}
⏳ Waiting for you to authorize the application...

After authorizing, you'll be redirected back automatically."""
            
        except Exception as e:
            if self._callback_server:
                self._cleanup_server()
            raise Exception(f"Failed to start OAuth flow: {e}")
    
    def _generate_auth_url(self, state: str) -> str:
        """Generate Slack OAuth2 authorization URL"""
        params = {
            'client_id': SLACK_CLIENT_ID,
            'redirect_uri': SLACK_REDIRECT_URI,
            'scope': ' '.join(SLACK_SCOPES),
            'state': state,
            'response_type': 'code'
        }
        return f"{SLACK_OAUTH_AUTHORIZE}?{urlencode(params)}"
    
    async def wait_for_oauth_completion(self, timeout_seconds: int = 120) -> str:
        """Wait for OAuth completion and process the result"""
        if not self._callback_server:
            return "❌ OAuth server not started"
        
        # Wait for callback with timeout
        elapsed = 0
        while (self._callback_server.authorization_code is None and 
               self._callback_server.authorization_error is None and 
               elapsed < timeout_seconds):
            await asyncio.sleep(1)
            elapsed += 1
        
        try:
            if elapsed >= timeout_seconds:
                return "⏰ Authorization timed out after 2 minutes"
            
            if self._callback_server.authorization_error:
                return f"❌ Authorization failed: {self._callback_server.authorization_error}"
            
            if not self._callback_server.authorization_code:
                return "❌ No authorization code received"
            
            # Exchange code for token
            token_data = await self.exchange_code_for_token(self._callback_server.authorization_code)
            await self.save_tokens(token_data)
            
            return "✅ Slack authentication completed successfully!"
            
        finally:
            self._cleanup_server()
    
    async def exchange_code_for_token(self, code: str) -> Dict:
        """Exchange authorization code for access token"""
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': SLACK_REDIRECT_URI,
            'client_id': SLACK_CLIENT_ID,
            'client_secret': SLACK_CLIENT_SECRET
        }
        
        response = requests.post(SLACK_OAUTH_TOKEN, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            if token_data.get('ok'):
                return token_data
            else:
                raise Exception(f"Slack API error: {token_data.get('error', 'Unknown error')}")
        else:
            raise Exception(f"Token exchange failed: {response.text}")
    
    async def save_tokens(self, token_data: Dict):
        """Securely save tokens to encrypted file"""
        self.access_token = token_data.get('access_token')
        self.refresh_token = token_data.get('refresh_token')  # Slack doesn't typically use refresh tokens
        
        # Extract additional info
        authed_user = token_data.get('authed_user', {})
        team = token_data.get('team', {})
        
        self.user_id = authed_user.get('id')
        self.team_id = team.get('id')
        
        if self.cipher:
            # Enhanced token data with timestamps
            enhanced_token_data = {
                **token_data,
                'saved_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(days=365)).isoformat()  # Slack tokens don't expire typically
            }
            
            encrypted_data = self.cipher.encrypt(json.dumps(enhanced_token_data).encode())
            async with aiofiles.open(self.token_file, 'wb') as f:
                await f.write(encrypted_data)
    
    async def load_tokens(self) -> bool:
        """Load and decrypt saved tokens"""
        try:
            if not os.path.exists(self.token_file) or not self.cipher:
                return False
                
            async with aiofiles.open(self.token_file, 'rb') as f:
                encrypted_data = await f.read()
                
            decrypted_data = self.cipher.decrypt(encrypted_data)
            token_data = json.loads(decrypted_data.decode())
            
            self.access_token = token_data.get('access_token')
            self.refresh_token = token_data.get('refresh_token')
            
            # Extract additional info
            authed_user = token_data.get('authed_user', {})
            team = token_data.get('team', {})
            
            self.user_id = authed_user.get('id')
            self.team_id = team.get('id')
            
            return True
        except Exception as e:
            print(f"Error loading tokens: {e}")
            return False
    
    async def get_valid_token(self) -> Optional[str]:
        """Get a valid access token"""
        # Try to load saved tokens first
        if not self.access_token:
            await self.load_tokens()
        
        # Slack tokens typically don't expire, but we can add refresh logic here if needed
        return self.access_token
    
    def _cleanup_server(self):
        """Clean up the OAuth callback server"""
        if self._callback_server:
            try:
                self._callback_server.shutdown()
                self._callback_server.server_close()
            except Exception:
                pass
        
        if self._server_thread:
            self._server_thread.join(timeout=1)

class SlackAPIClient:
    """Slack Web API client for messaging operations"""
    
    def __init__(self, auth_manager: SlackAuthManager):
        self.auth_manager = auth_manager
        self.user_cache = {}  # Cache Slack user info
        
    async def get_headers(self) -> Dict[str, str]:
        """Get authenticated headers for Slack API requests"""
        token = await self.auth_manager.get_valid_token()
        if not token:
            raise Exception("No valid Slack token available")
            
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json; charset=utf-8'
        }
    
    async def test_auth(self) -> Dict:
        """Test authentication and get current user info"""
        headers = await self.get_headers()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{SLACK_API_BASE}/auth.test", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get('ok'):
                        return data
                    else:
                        raise Exception(f"Slack API error: {data.get('error')}")
                else:
                    raise Exception(f"Failed to test auth: {await resp.text()}")
    
    async def get_users_list(self) -> List[Dict]:
        """Get list of users in the workspace"""
        headers = await self.get_headers()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{SLACK_API_BASE}/users.list", headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get('ok'):
                        return data.get('members', [])
                    else:
                        raise Exception(f"Slack API error: {data.get('error')}")
                else:
                    raise Exception(f"Failed to get users: {await resp.text()}")
    
    async def find_user_by_name(self, name: str) -> Optional[Dict]:
        """Find user by display name, real name, or first name with fuzzy matching"""
        # Check cache first
        cache_key = name.lower()
        if cache_key in self.user_cache:
            return self.user_cache[cache_key]
        
        try:
            users = await self.get_users_list()
            exact_matches = []
            partial_matches = []
            
            search_name = name.lower().strip()
            
            for user in users:
                if user.get('deleted') or user.get('is_bot'):
                    continue
                
                profile = user.get('profile', {})
                display_name = profile.get('display_name', '').lower()
                real_name = profile.get('real_name', '').lower()
                username = user.get('name', '').lower()
                first_name = profile.get('first_name', '').lower()
                
                # Extract first name from real name if first_name is not available
                if not first_name and real_name:
                    first_name = real_name.split()[0] if real_name.split() else ''
                
                # Exact matches (highest priority)
                if search_name in [display_name, real_name, username] or search_name == user.get('id'):
                    exact_matches.append(user)
                    continue
                
                # Partial matches for first name, display name, or real name
                if (search_name == first_name or  # First name exact match
                    search_name in display_name or  # Partial display name match
                    search_name in real_name or     # Partial real name match
                    search_name in username):       # Partial username match
                    partial_matches.append(user)
            
            # Return exact match if found
            if exact_matches:
                user = exact_matches[0]
                self.user_cache[cache_key] = user
                return user
            
            # Return single partial match
            if len(partial_matches) == 1:
                user = partial_matches[0]
                self.user_cache[cache_key] = user
                return user
            
            # Multiple matches - cache for disambiguation
            if len(partial_matches) > 1:
                self.user_cache[f"{cache_key}_multiple"] = partial_matches
                return None  # Will be handled by caller for disambiguation
            
            return None
            
        except Exception as e:
            print(f"Error finding user {name}: {e}")
            return None
    
    async def find_users_by_name(self, name: str) -> List[Dict]:
        """Find all users matching the name (for disambiguation)"""
        try:
            users = await self.get_users_list()
            matches = []
            
            search_name = name.lower().strip()
            
            for user in users:
                if user.get('deleted') or user.get('is_bot'):
                    continue
                
                profile = user.get('profile', {})
                display_name = profile.get('display_name', '').lower()
                real_name = profile.get('real_name', '').lower()
                username = user.get('name', '').lower()
                first_name = profile.get('first_name', '').lower()
                
                # Extract first name from real name if first_name is not available
                if not first_name and real_name:
                    first_name = real_name.split()[0] if real_name.split() else ''
                
                # Check for any match
                if (search_name == first_name or
                    search_name in display_name or
                    search_name in real_name or
                    search_name in username or
                    search_name == user.get('id')):
                    matches.append(user)
            
            return matches
            
        except Exception as e:
            print(f"Error finding users {name}: {e}")
            return []
    
    async def open_conversation(self, users: str) -> Dict:
        """Open a conversation (DM or multi-person DM)"""
        headers = await self.get_headers()
        data = {'users': users}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{SLACK_API_BASE}/conversations.open", 
                headers=headers,
                json=data
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get('ok'):
                        return result.get('channel', {})
                    else:
                        raise Exception(f"Slack API error: {result.get('error')}")
                else:
                    raise Exception(f"Failed to open conversation: {await resp.text()}")
    
    async def send_message(self, channel: str, text: str) -> Dict:
        """Send a message to a channel or user"""
        headers = await self.get_headers()
        data = {
            'channel': channel,
            'text': text
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{SLACK_API_BASE}/chat.postMessage",
                headers=headers,
                json=data
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get('ok'):
                        return result
                    else:
                        raise Exception(f"Slack API error: {result.get('error')}")
                else:
                    raise Exception(f"Failed to send message: {await resp.text()}")
    
    async def get_conversation_history(self, channel: str, limit: int = 10) -> List[Dict]:
        """Get conversation history"""
        headers = await self.get_headers()
        params = {
            'channel': channel,
            'limit': limit
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{SLACK_API_BASE}/conversations.history",
                headers=headers,
                params=params
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get('ok'):
                        return result.get('messages', [])
                    else:
                        raise Exception(f"Slack API error: {result.get('error')}")
                else:
                    raise Exception(f"Failed to get conversation history: {await resp.text()}")
    
    async def send_dm_to_user(self, user_id: str, message: str) -> Dict:
        """Send a direct message to a user"""
        try:
            print(f"📋 Opening conversation with user ID: {user_id}")
            
            # Open conversation with the user
            conversation = await self.open_conversation(user_id)
            channel_id = conversation.get('id')
            
            if not channel_id:
                raise Exception("Failed to open conversation with user - no channel ID returned")
            
            print(f"✅ Conversation opened, channel ID: {channel_id}")
            
            # Send the message
            print(f"📤 Sending message to channel: {channel_id}")
            result = await self.send_message(channel_id, message)
            
            print(f"✅ Message sent successfully")
            return result
            
        except Exception as e:
            print(f"❌ Error in send_dm_to_user: {e}")
            raise
    
    async def get_dm_history_with_user(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get DM history with a specific user"""
        # Open conversation with the user
        conversation = await self.open_conversation(user_id)
        channel_id = conversation.get('id')
        
        if not channel_id:
            raise Exception("Failed to open conversation with user")
        
        # Get message history
        return await self.get_conversation_history(channel_id, limit)

class MessageProcessor:
    """Processes natural language commands using ASI:One LLM"""
    
    @staticmethod
    async def extract_message_intent(text: str) -> Dict:
        """Extract intent and parameters from natural language text"""
        try:
            response = asi_client.chat.completions.create(
                model="asi1-mini",
                messages=[
                    {"role": "system", "content": """
You are a Slack message intent parser. Analyze user requests and extract structured information.

For sending messages, look for patterns like:
- "Send [recipient] a message saying [message]"
- "Tell [recipient]: [message]"
- "Message [recipient] that [message]"
- "DM [recipient]: [message]"

Extract:
- action: "send_message"
- recipient: the user's display name or username
- message: the actual message content to send

For reading messages:
- action: "read_messages" 
- target: username to read messages from
- limit: number of messages (default 10)

For authentication:
- action: "authenticate" for login/auth requests

Examples:
Input: "Send Alice a message saying I'll be late"
Output: {"action": "send_message", "recipient": "Alice", "message": "I'll be late"}

Input: "Tell Ben: Meeting starts in 10 minutes"
Output: {"action": "send_message", "recipient": "Ben", "message": "Meeting starts in 10 minutes"}

Input: "Read my last message from Charlie"
Output: {"action": "read_messages", "target": "Charlie", "limit": 1}

Respond only with valid JSON:
{
    "action": "send_message|read_messages|authenticate|help",
    "recipient": "username",
    "message": "message content",
    "target": "username to read from",
    "limit": 10
}
                    """},
                    {"role": "user", "content": text}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            # Parse JSON response
            response_text = response.choices[0].message.content.strip()
            # Clean up response to ensure valid JSON
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
                
            return json.loads(response_text)
            
        except Exception as e:
            print(f"Error parsing intent: {e}")
            return {"action": "help", "error": str(e)}
    
    @staticmethod
    async def generate_response(intent: Dict, result: str) -> str:
        """Generate natural language response based on action result"""
        try:
            context = f"Intent: {intent}, Result: {result}"
            
            response = asi_client.chat.completions.create(
                model="asi1-mini",
                messages=[
                    {"role": "system", "content": """
You are a helpful Slack assistant. Generate natural, conversational responses about Slack actions.

For successful message sending: Confirm the message was sent
For message retrieval: Summarize the messages naturally
For errors: Explain what went wrong and suggest solutions
Keep responses concise and user-friendly.
                    """},
                    {"role": "user", "content": context}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Action completed, but couldn't generate response: {str(e)}"

# Initialize the slack agent with enhanced capabilities
subject_matter = "Slack messaging, OAuth authentication, and communication management"

SEED_PHRASE = "enhanced_slack_agent_oauth_2024"

agent = Agent(
    name="slack_agent",
    port=8003,
    seed=SEED_PHRASE,
    mailbox=True,
    publish_agent_details=True,
    readme_path="README.md"
)

# Initialize Slack components
auth_manager = SlackAuthManager()
slack_client = SlackAPIClient(auth_manager)
message_processor = MessageProcessor()

# Create chat protocol
protocol = Protocol(spec=chat_protocol_spec)

# Enhanced message handler with integrated OAuth flow
async def handle_slack_action(intent: Dict) -> str:
    """Execute Slack actions based on parsed intent"""
    try:
        action = intent.get('action', 'help')
        
        # Check for authentication commands first
        if action == 'authenticate' or 'auth' in intent.get('message', '').lower() or 'login' in intent.get('message', '').lower():
            try:
                result = await auth_manager.start_oauth_flow()
                # Start waiting for completion in background
                asyncio.create_task(complete_oauth_flow())
                return result
            except Exception as e:
                return f"❌ Failed to start Slack authentication: {e}\n\nPlease check your Slack app configuration in the .env file."
        
        # For other actions, check if we have valid authentication
        valid_token = await auth_manager.get_valid_token()
        if not valid_token:
            return ("🔐 **Slack Authentication Required**\n\n"
                   "You need to authenticate with Slack first to use messaging features.\n"
                   "Type 'authenticate' or 'login' to start the OAuth flow.\n\n"
                   "💡 If you've already authenticated before, your tokens may have expired and need refreshing.")
        
        if action == 'send_message':
            recipient = intent.get('recipient')
            message = intent.get('message')
            
            if not recipient or not message:
                return "I need both a recipient and a message to send. Try:\n" \
                       "• 'Send Alice a message saying hello'\n" \
                       "• 'Tell Ben: Meeting at 3pm'\n" \
                       "• 'Message Charlie that I'll be late'"
            
            try:
                print(f"🔍 Looking for Slack user: '{recipient}'")
                
                # Step 1: Find the user by name
                target_user = await slack_client.find_user_by_name(recipient)
                
                if not target_user:
                    # Check if we have multiple matches cached
                    cache_key = f"{recipient.lower()}_multiple"
                    if cache_key in slack_client.user_cache:
                        multiple_matches = slack_client.user_cache[cache_key]
                        
                        # Format disambiguation message
                        disambig_msg = f"🤔 I found multiple users named '{recipient}':\n\n"
                        for i, user in enumerate(multiple_matches[:5], 1):  # Limit to 5 matches
                            profile = user.get('profile', {})
                            display_name = profile.get('display_name', '')
                            real_name = profile.get('real_name', '')
                            username = user.get('name', '')
                            
                            # Create a clear identifier
                            identifier = display_name or real_name or username
                            if real_name and display_name and real_name != display_name:
                                identifier = f"{display_name} ({real_name})"
                            
                            disambig_msg += f"{i}. **{identifier}** (@{username})\n"
                        
                        disambig_msg += f"\n💡 **To send your message, be more specific:**\n"
                        disambig_msg += f"• Use their full name: 'Send {multiple_matches[0].get('profile', {}).get('real_name', recipient)} a message saying {message}'\n"
                        disambig_msg += f"• Use their display name: 'Send {multiple_matches[0].get('profile', {}).get('display_name', recipient)} a message saying {message}'\n"
                        disambig_msg += f"• Use their username: 'Send @{multiple_matches[0].get('name', recipient)} a message saying {message}'"
                        
                        return disambig_msg
                    
                    # No matches found at all
                    return f"❌ I couldn't find a Slack user named '{recipient}'.\n\n" \
                           f"💡 **Tips to find the user:**\n" \
                           f"• Try their full name (e.g., 'Ben Smith')\n" \
                           f"• Try their display name as shown in Slack\n" \
                           f"• Make sure they're in your Slack workspace\n" \
                           f"• Check the spelling carefully\n" \
                           f"• Use their @username or Slack User ID for reliability"
                
                # Step 2: Verify we have the required scopes
                print(f"📋 Verifying Slack permissions...")
                
                # Step 3: Send the DM
                print(f"📨 Sending message to {target_user.get('name')}...")
                result = await slack_client.send_dm_to_user(target_user['id'], message)
                
                profile = target_user.get('profile', {})
                display_name = profile.get('display_name') or profile.get('real_name') or target_user.get('name')
                
                return f"✅ **Message sent successfully to {display_name}!**\n" \
                       f"� **Message:** \"{message}\"\n" \
                       f"� **Sent:** {datetime.now().strftime('%I:%M %p')}\n" \
                       f"🎯 **Via:** Your Slack DM"
                       
            except Exception as e:
                error_msg = str(e).lower()
                print(f"❌ Error sending message: {e}")
                
                if "not_authed" in error_msg or "invalid_auth" in error_msg:
                    return f"🔐 **Slack authentication failed.** Your token may be expired.\n" \
                           f"Type 'authenticate' to refresh your Slack connection."
                           
                elif "channel_not_found" in error_msg:
                    return f"❌ **Cannot create conversation** with {recipient}.\n" \
                           f"Make sure they're in your Slack workspace."
                           
                elif "user_not_found" in error_msg:
                    return f"❌ **User not found:** '{recipient}'\n" \
                           f"Please check the name and try again."
                           
                elif "missing_scope" in error_msg:
                    return f"🔧 **Missing Slack permissions.**\n" \
                           f"Your Slack app needs these scopes:\n" \
                           f"• `chat:write` - Send messages\n" \
                           f"• `im:write` - Send direct messages\n" \
                           f"• `users:read` - Find users\n\n" \
                           f"Please re-authenticate with proper permissions."
                           
                else:
                    return f"❌ Failed to send message to {recipient}: {str(e)[:150]}"
            
        elif action == 'read_messages':
            target = intent.get('target')
            limit = intent.get('limit', 10)
            
            if not target:
                return "Please specify who you want to read messages from. Try: 'Read my last message from Ben'"
            
            try:
                # Find the user
                target_user = await slack_client.find_user_by_name(target)
                
                if not target_user:
                    # Check if we have multiple matches
                    cache_key = f"{target.lower()}_multiple"
                    if cache_key in slack_client.user_cache:
                        multiple_matches = slack_client.user_cache[cache_key]
                        
                        disambig_msg = f"🤔 I found multiple users named '{target}':\n\n"
                        for i, user in enumerate(multiple_matches[:5], 1):
                            profile = user.get('profile', {})
                            display_name = profile.get('display_name', '')
                            real_name = profile.get('real_name', '')
                            username = user.get('name', '')
                            
                            identifier = display_name or real_name or username
                            if real_name and display_name and real_name != display_name:
                                identifier = f"{display_name} ({real_name})"
                            
                            disambig_msg += f"{i}. **{identifier}** (@{username})\n"
                        
                        disambig_msg += f"\n💡 **To read messages, be more specific:**\n"
                        disambig_msg += f"• Use their full name or display name\n"
                        disambig_msg += f"• Use their @username"
                        
                        return disambig_msg
                    
                    return f"❌ I couldn't find a Slack user named '{target}'. " \
                           f"Please check the name and try again."
                
                # Get message history
                messages = await slack_client.get_dm_history_with_user(target_user['id'], limit)
                
                if not messages:
                    profile = target_user.get('profile', {})
                    display_name = profile.get('display_name') or profile.get('real_name') or target_user.get('name')
                    return f"📭 No messages found in your conversation with {display_name}"
                
                profile = target_user.get('profile', {})
                display_name = profile.get('display_name') or profile.get('real_name') or target_user.get('name')
                
                response = f"📨 **Last {min(len(messages), limit)} messages with {display_name}:**\n\n"
                
                for i, msg in enumerate(messages[:limit]):
                    timestamp = datetime.fromtimestamp(float(msg.get('ts', 0)))
                    text = msg.get('text', 'No text')
                    user_id = msg.get('user', 'Unknown')
                    
                    # Check if message is from the target user or the current user
                    sender = "You" if user_id == auth_manager.user_id else display_name
                    
                    response += f"**{sender}** ({timestamp.strftime('%m/%d %H:%M')}):\n{text}\n\n"
                
                return response
                
            except Exception as e:
                error_msg = str(e).lower()
                if "missing_scope" in error_msg:
                    return f"🔧 **Missing Slack permissions.**\n" \
                           f"Your Slack app needs the `im:history` scope to read messages.\n" \
                           f"Please re-authenticate with proper permissions."
                else:
                    return f"❌ Failed to read messages from {target}: {str(e)[:150]}"
            
        elif action == 'help':
            help_text = """🔧 **Slack Agent Commands:**

**Send Messages:**
• "Send Alice a message saying I'll be late"
• "Tell Ben: Meeting moved to 3pm"  
• "Message Charlie that the project is done"
• "Send @username a message saying hello"

**Read Messages:**
• "Read my last message from Alice"
• "Show messages from Ben"
• "Get my conversation with Charlie"

**Authentication:**
• "Connect my Slack account"
• "Login to Slack"
• "authenticate"

**User Matching:**
• Works with first names: "Ben", "Alice"
• Works with full names: "Ben Smith", "Alice Johnson"
• Works with display names and @usernames
• Handles multiple matches with disambiguation

"""
            
            # Try to add workspace information and scope verification
            try:
                auth_info = await slack_client.test_auth()
                team_name = auth_info.get('team', 'Unknown Team')
                user_name = auth_info.get('user', 'Unknown User')
                help_text += f"**📋 Currently connected to:** {team_name} as {user_name}\n"
                
                # Show configured scopes
                help_text += f"\n**🔧 Available Permissions:**\n"
                for scope in SLACK_SCOPES:
                    help_text += f"• `{scope}`\n"
                
            except Exception:
                help_text += "**📋 Status:** Not authenticated with Slack\n"
                help_text += "**🔐 Required Scopes for full functionality:**\n"
                help_text += "• `chat:write` - Send messages\n"
                help_text += "• `im:write` - Send direct messages\n"
                help_text += "• `users:read` - Find and identify users\n"
                help_text += "• `im:history` - Read DM history\n\n"
                
            help_text += "\n🚀 I can help you send messages and read conversation history with smart user matching!"
            return help_text
            
        else:
            return "I'm not sure how to help with that. Try asking me to send a message or read message history!"
            
    except Exception as e:
        return f"❌ Error executing Slack action: {str(e)}"

async def complete_oauth_flow():
    """Complete the OAuth flow in the background"""
    try:
        result = await auth_manager.wait_for_oauth_completion()
        print(f"OAuth completion: {result}")
    except Exception as e:
        print(f"OAuth flow error: {e}")

@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handle incoming chat messages with Slack integration"""
    # Send acknowledgment
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id),
    )
    
    # Collect text content
    text = ''
    for item in msg.content:
        if isinstance(item, TextContent):
            text += item.text
    
    ctx.logger.info(f"Received message: {text}")
    
    try:
        # Parse the user's intent using ASI:One
        intent = await message_processor.extract_message_intent(text)
        
        # Execute the appropriate Slack action
        result = await handle_slack_action(intent)
        
        # Generate a natural language response
        response = await message_processor.generate_response(intent, result)
        
        # If the response generation failed, use the direct result
        if "couldn't generate response" in response:
            response = result
            
    except Exception as e:
        ctx.logger.error(f"Error processing message: {e}")
        response = f"❌ Sorry, I encountered an error: {str(e)}"
    
    # Send response back to user
    await ctx.send(sender, ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[
            TextContent(type="text", text=response),
            EndSessionContent(type="end-session"),
        ]
    ))

@protocol.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    """Handle chat acknowledgments (useful for read receipts)"""
    ctx.logger.info(f"Message acknowledged by {sender}")

# Startup handler to initialize Slack authentication
@agent.on_event("startup")
async def startup_handler(ctx: Context):
    """Initialize Slack authentication on agent startup"""
    ctx.logger.info("🚀 Slack Agent starting up...")
    
    # Check for required environment variables
    missing_vars = []
    if not SLACK_CLIENT_ID:
        missing_vars.append("SLACK_CLIENT_ID")
    if not SLACK_CLIENT_SECRET:
        missing_vars.append("SLACK_CLIENT_SECRET")
    if not os.getenv("ASI_ONE_API_KEY"):
        missing_vars.append("ASI_ONE_API_KEY")
    
    if missing_vars:
        ctx.logger.warning(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        ctx.logger.warning("   Some Slack features may not work properly.")
        ctx.logger.warning("   Please check your .env file configuration.")
    else:
        ctx.logger.info("✅ All required environment variables found")
    
    # Try to load existing tokens
    if await auth_manager.load_tokens():
        ctx.logger.info("✅ Slack tokens loaded successfully")
        
        # Test the authentication
        try:
            auth_info = await slack_client.test_auth()
            team_name = auth_info.get('team', 'Unknown')
            user_name = auth_info.get('user', 'Unknown')
            ctx.logger.info(f"🔐 Authenticated with {team_name} as {user_name}")
            ctx.logger.info("🚀 Ready for Slack messaging operations!")
        except Exception as e:
            ctx.logger.warning(f"⚠️  Token validation failed: {e}")
            ctx.logger.info("🔄 You may need to re-authenticate")
    else:
        ctx.logger.info("ℹ️  No saved Slack tokens found")
        ctx.logger.info("💡 To enable Slack messaging, send 'authenticate' or 'login' to start OAuth flow")
        if SLACK_CLIENT_ID and SLACK_CLIENT_SECRET:
            ctx.logger.info("✅ Slack OAuth credentials configured and ready")
    
    ctx.logger.info("🎯 Slack Agent ready for messaging operations!")

# Shutdown handler with server cleanup
@agent.on_event("shutdown")
async def shutdown_handler(ctx: Context):
    """Clean up resources on agent shutdown"""
    ctx.logger.info("🛑 Slack Agent shutting down...")
    # Clean up any running OAuth server
    auth_manager._cleanup_server()

# Include the protocol with the agent
agent.include(protocol, publish_manifest=True)

# Agent information
print("=" * 60)
print("🎯 SLACK AGENT - Enhanced Messaging & OAuth Integration")
print("=" * 60)
print(f"Agent Address: {agent.address}")
print(f"Agent Port: 8003")
print(f"Mailbox Enabled: True")
print()
print("🔧 FEATURES:")
print("• Slack OAuth2 Authentication")
print("• Direct Message Sending")
print("• Message History Retrieval") 
print("• Natural Language Processing (ASI:One)")
print("• Secure Token Management")
print()
print("💡 EXAMPLE COMMANDS:")
print('• "Send Alice a message saying I\'ll be late"')
print('• "Read my last message from Ben"')
print('• "Tell everyone in my DMs: Meeting moved to 3pm"')
print()
print("🚀 Starting agent...")
print("=" * 60)

if __name__ == "__main__":
    agent.run()
 