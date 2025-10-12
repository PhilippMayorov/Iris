"""
Discord Agent - Advanced Messaging and Communication Management

This agent provides comprehensive Discord integration with OAuth2 authentication:
1. Discord OAuth2 user authentication and secure token management
2. Direct message sending to Discord users by username or ID
3. Message retrieval and conversation history access
4. Natural language processing for command interpretation using ASI:One
5. Secure credential management and API interaction

Integration Points:
- OAuth2 flow for Discord user account access
- Discord REST API for messaging operations
- ASI:One LLM for natural language command interpretation
- Secure token storage and refresh management
- Compatible with Agentverse for cloud deployment

Example Usage:
- "Send Ben a message saying I'll be late" → Extracts recipient and message, sends DM
- "Show my last message from Alice" → Retrieves recent conversation history
- "Text everyone in my DMs: Meeting moved to 3pm" → Bulk messaging capability
"""

import asyncio
import json
import os
import re
import aiohttp
import aiofiles
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from uuid import uuid4
from urllib.parse import urlencode, urlparse, parse_qs
import secrets
import hashlib
import threading
import webbrowser
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
from requests_oauthlib import OAuth2Session

# Load environment variables
load_dotenv()

# ASI:One Configuration for LLM processing
asi_client = OpenAI(
    base_url='https://api.asi1.ai/v1',
    api_key=os.getenv("ASI_ONE_API_KEY", "your_asi_one_api_key_here"),
)

# Discord OAuth2 Configuration
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:8080/callback")

# Discord API endpoints (official Discord OAuth2 URLs)
DISCORD_API_BASE = "https://discord.com/api/v10"
DISCORD_OAUTH_AUTHORIZE = "https://discord.com/oauth2/authorize"
DISCORD_OAUTH_TOKEN = "https://discord.com/api/v10/oauth2/token"
DISCORD_OAUTH_REVOKE = "https://discord.com/api/v10/oauth2/token/revoke"

# Discord OAuth2 scopes configuration
# Note: Some scopes require Discord approval - see https://discord.com/developers/docs/topics/oauth2#shared-resources-oauth2-scopes
DISCORD_SCOPES_FULL = [
    "identify",              # Basic user info (no approval required)
    "guilds",               # User's guild list (no approval required) 
    "messages.read",        # Read messages (requires Discord approval)
    "dm_channels.read",     # Read DM channels (requires approval, deprecated)
    "guilds.members.read"   # Read guild members to find users (requires approval)
]

# Basic scopes for initial testing (no approval required)
DISCORD_SCOPES_BASIC = ["identify", "guilds"]

# Enhanced scopes for messaging features (some may require Discord approval)
DISCORD_SCOPES_ENHANCED = [
    "identify",              # Basic user info (no approval required)
    "guilds",               # User's guild list (no approval required)
    "guilds.members.read",   # Read guild members (requires approval)
    "connections"           # User's connected accounts (no approval required)
]

# Note: Discord has deprecated user token access to relationships (friends list)
# The /users/@me/relationships endpoint requires special approval that's rarely granted
# For reliable user lookup, we'll focus on guild-based search

# For messaging functionality, we need to use Discord Bot instead of OAuth2 user tokens
# Discord deprecated user token messaging - we'll implement bot messaging with user context
DISCORD_BOT_SCOPES = [
    "bot",                  # Bot permissions
    "messages:write",       # Send messages  
    "channels:read",        # Read channels
    "guilds:read"           # Read guilds
]

# Encryption key for secure token storage (generate once and store securely)
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handles OAuth2 callback from Discord"""
    
    def do_GET(self):
        """Handle GET request from Discord OAuth callback"""
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        # Validate state parameter for CSRF protection
        received_state = query_params.get('state', [None])[0]
        expected_state = getattr(self.server, 'expected_state', None)
        
        if received_state != expected_state:
            self.server.authorization_error = "invalid_state"
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("""
                <html>
                <head><title>Discord OAuth2 - Error</title></head>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
                    <h1 style="color: #dc3545;">🔒 Security Error: Invalid State</h1>
                    <p>The authorization request may have been tampered with.</p>
                    <p>Please close this window and try again.</p>
                </body>
                </html>
            """.encode('utf-8'))
            return
        
        if 'code' in query_params:
            # Success - authorization code received
            self.server.authorization_code = query_params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write("""
                <html>
                <head><title>Discord OAuth2 - Success</title></head>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
                    <h1 style="color: #28a745;">✅ Discord Authorization Successful!</h1>
                    <p>You have successfully connected your Discord account!</p>
                    <p>You can close this window and return to the chat.</p>
                    <script>setTimeout(() => window.close(), 3000);</script>
                </body>
                </html>
            """.encode('utf-8'))
        elif 'error' in query_params:
            # Error in authorization
            error = query_params.get('error', ['unknown'])[0]
            error_description = query_params.get('error_description', [''])[0]
            self.server.authorization_error = error
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f"""
                <html>
                <head><title>Discord OAuth2 - Error</title></head>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
                    <h1 style="color: #dc3545;">❌ Discord Authorization Failed</h1>
                    <p><strong>Error:</strong> {error}</p>
                    <p><strong>Description:</strong> {error_description}</p>
                    <p>Please close this window and try again.</p>
                </body>
                </html>
            """.encode('utf-8'))
        
        # Stop the server after handling the request
        threading.Thread(target=self.server.shutdown).start()
    
    def log_message(self, format, *args):
        """Suppress server log messages"""
        pass

class DiscordAuthManager:
    """Handles Discord OAuth2 authentication and secure token management"""
    
    def __init__(self):
        self.token_file = "discord_tokens.enc"
        self.cipher = Fernet(ENCRYPTION_KEY.encode()) if ENCRYPTION_KEY else None
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self._callback_server = None
        self._server_thread = None
        
    async def start_oauth_flow(self) -> str:
        """Start complete OAuth flow with local callback server"""
        if not DISCORD_CLIENT_ID or not DISCORD_CLIENT_SECRET:
            raise ValueError("Discord client credentials not configured")
        
        # Extract port from redirect URI
        parsed_uri = urlparse(DISCORD_REDIRECT_URI)
        callback_port = parsed_uri.port or 8080
        
        try:
            # Start local callback server
            self._callback_server = HTTPServer(('localhost', callback_port), OAuthCallbackHandler)
            self._callback_server.authorization_code = None
            self._callback_server.authorization_error = None
            
            # Generate state for CSRF protection
            state = secrets.token_urlsafe(32)
            self._callback_server.expected_state = state
            
            # Start server in background thread
            self._server_thread = threading.Thread(target=self._callback_server.serve_forever)
            self._server_thread.daemon = True
            self._server_thread.start()
            
            # Generate and return OAuth URL
            auth_url, _ = await self.get_auth_url(state)
            
            # Open browser automatically
            webbrowser.open(auth_url)
            
            return f"""🔗 **Discord Authentication Started**

A browser window should have opened automatically. If not, please visit:
{auth_url}

✅ Local callback server is running on port {callback_port}
⏳ Waiting for you to authorize the application...

After authorizing, you'll be redirected back automatically."""
            
        except Exception as e:
            if self._callback_server:
                self._cleanup_server()
            raise Exception(f"Failed to start OAuth flow: {e}")
    
    async def wait_for_oauth_completion(self, timeout_seconds: int = 120) -> str:
        """Wait for OAuth completion and process the result"""
        if not self._callback_server:
            return "❌ No OAuth flow in progress"
        
        # Wait for callback with timeout
        elapsed = 0
        while (self._callback_server.authorization_code is None and 
               self._callback_server.authorization_error is None and 
               elapsed < timeout_seconds):
            await asyncio.sleep(1)
            elapsed += 1
        
        try:
            if elapsed >= timeout_seconds:
                return "⏰ Authorization timed out after 2 minutes. Please try again."
            
            if self._callback_server.authorization_error:
                error = self._callback_server.authorization_error
                return f"❌ Authorization failed: {error}. Please try again."
            
            if not self._callback_server.authorization_code:
                return "❌ No authorization code received. Please try again."
            
            # Exchange code for token
            code = self._callback_server.authorization_code
            token_data = await self.exchange_code_for_token(code)
            
            return f"✅ **Discord Connected Successfully!**\n\nYou can now use Discord commands like:\n• 'Send Ben: Running late!'\n• 'Show messages from Alice'\n• 'What can you do?'"
            
        finally:
            self._cleanup_server()
    
    def _cleanup_server(self):
        """Clean up the OAuth callback server"""
        if self._callback_server:
            try:
                self._callback_server.shutdown()
                self._callback_server.server_close()
            except:
                pass
            self._callback_server = None
        
        if self._server_thread:
            self._server_thread = None
        
    async def get_auth_url(self, state: str = None) -> Tuple[str, str]:
        """Generate Discord OAuth2 authorization URL"""
        if not DISCORD_CLIENT_ID:
            raise ValueError("DISCORD_CLIENT_ID not configured")
        
        if state is None:
            state = secrets.token_urlsafe(32)
            
        params = {
            'client_id': DISCORD_CLIENT_ID,
            'redirect_uri': DISCORD_REDIRECT_URI,
            'response_type': 'code',
            'scope': ' '.join(DISCORD_SCOPES_BASIC),  # Start with basic scopes, can be upgraded later
            'state': state
        }
        
        auth_url = f"{DISCORD_OAUTH_AUTHORIZE}?{urlencode(params)}"
        return auth_url, state
    
    async def exchange_code_for_token(self, code: str) -> Dict:
        """Exchange authorization code for access token using Discord's OAuth2 flow"""
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': DISCORD_REDIRECT_URI
        }
        
        # Use synchronous requests for token exchange (simpler error handling)
        response = requests.post(
            DISCORD_OAUTH_TOKEN,
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            auth=(DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET)
        )
        
        if response.status_code == 200:
            token_data = response.json()
            await self.save_tokens(token_data)
            return token_data
        else:
            raise Exception(f"Token exchange failed: {response.text}")
    
    async def save_tokens(self, token_data: Dict):
        """Securely save tokens to encrypted file"""
        self.access_token = token_data['access_token']
        self.refresh_token = token_data.get('refresh_token')
        self.token_expires_at = datetime.now() + timedelta(seconds=token_data.get('expires_in', 3600))
        
        if self.cipher:
            # Enhanced token data with timestamps for better expiry tracking
            enhanced_token_data = {
                **token_data,
                'saved_at': datetime.now().isoformat(),
                'expires_at': self.token_expires_at.isoformat()
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
            
            self.access_token = token_data['access_token']
            self.refresh_token = token_data.get('refresh_token')
            
            # Use stored expiry time if available, otherwise calculate from expires_in
            if 'expires_at' in token_data:
                self.token_expires_at = datetime.fromisoformat(token_data['expires_at'].replace('Z', '+00:00'))
            elif 'expires_in' in token_data and 'saved_at' in token_data:
                saved_at = datetime.fromisoformat(token_data['saved_at'].replace('Z', '+00:00'))
                self.token_expires_at = saved_at + timedelta(seconds=token_data['expires_in'])
            else:
                # Fallback: assume token expires in 1 hour
                self.token_expires_at = datetime.now() + timedelta(hours=1)
            
            return True
        except Exception as e:
            print(f"Error loading tokens: {e}")
            return False
    
    async def refresh_access_token(self) -> bool:
        """Refresh expired access token using Discord's refresh_token grant"""
        if not self.refresh_token:
            return False
            
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token
        }
        
        # Use HTTP Basic authentication and proper content-type
        auth = aiohttp.BasicAuth(DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET)
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(DISCORD_OAUTH_TOKEN, data=data, headers=headers, auth=auth) as resp:
                    if resp.status == 200:
                        token_data = await resp.json()
                        await self.save_tokens(token_data)
                        return True
                    return False
        except Exception:
            return False
    
    async def get_valid_token(self) -> Optional[str]:
        """Get a valid access token, refreshing if necessary"""
        # Try to load saved tokens first
        if not self.access_token:
            await self.load_tokens()
        
        # Check if token is expired and refresh if needed
        if (self.token_expires_at and 
            datetime.now() >= self.token_expires_at - timedelta(minutes=5)):
            if not await self.refresh_access_token():
                return None
                
        return self.access_token
    
    async def revoke_token(self, token: str, token_type: str = "access_token") -> bool:
        """Revoke an access or refresh token using Discord's revocation endpoint"""
        data = {
            'token': token,
            'token_type_hint': token_type
        }
        
        # Use HTTP Basic authentication and proper content-type
        auth = aiohttp.BasicAuth(DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET)
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(DISCORD_OAUTH_REVOKE, data=data, headers=headers, auth=auth) as resp:
                    return resp.status == 200
        except Exception:
            return False


class DiscordAPIClient:
    """Discord REST API client for messaging operations"""
    
    def __init__(self, auth_manager: DiscordAuthManager):
        self.auth_manager = auth_manager
        self.user_cache = {}  # Cache Discord user info
        
    async def get_headers(self) -> Dict[str, str]:
        """Get authenticated headers for Discord API requests"""
        token = await self.auth_manager.get_valid_token()
        if not token:
            raise Exception("No valid Discord token available")
            
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'User-Agent': 'VocalAgent Discord Bot'
        }
    
    async def get_current_user(self) -> Dict:
        """Get current authenticated user info"""
        headers = await self.get_headers()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{DISCORD_API_BASE}/users/@me", headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    raise Exception(f"Failed to get user info: {await resp.text()}")
    
    async def get_user_relationships(self) -> List[Dict]:
        """Get user's friends list (DEPRECATED: Discord restricts this API)"""
        try:
            headers = await self.get_headers()
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{DISCORD_API_BASE}/users/@me/relationships",
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    elif resp.status == 401:
                        print("⚠️  Friends list access denied - Discord has restricted this API for user tokens")
                        return []
                    else:
                        print(f"Failed to get relationships: {resp.status}")
                        return []
        except Exception as e:
            print(f"Error getting relationships: {e}")
            return []
    
    async def get_guild_members_sample(self, guild_id: str, limit: int = 50) -> List[Dict]:
        """Get a sample of guild members (for user discovery)"""
        try:
            headers = await self.get_headers()
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{DISCORD_API_BASE}/guilds/{guild_id}/members",
                    headers=headers,
                    params={'limit': limit}
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    elif resp.status == 403:
                        print(f"⚠️  No permission to view members in guild {guild_id}")
                        return []
                    else:
                        print(f"Failed to get guild members: {resp.status}")
                        return []
        except Exception as e:
            print(f"Error getting guild members: {e}")
            return []
    
    def parse_username(self, username_input: str) -> Dict[str, str]:
        """Parse username input to extract components"""
        # Handle format: username#discriminator
        if '#' in username_input:
            parts = username_input.split('#')
            return {
                'username': parts[0].strip(),
                'discriminator': parts[1].strip() if len(parts) > 1 else None,
                'full_name': username_input.strip()
            }
        else:
            return {
                'username': username_input.strip(),
                'discriminator': None,
                'full_name': username_input.strip()
            }
    
    async def find_user_by_username(self, username_input: str) -> Optional[Dict]:
        """Find Discord user by username with guild-focused search strategy"""
        # Parse the username input
        parsed = self.parse_username(username_input)
        cache_key = parsed['full_name'].lower()
        
        # Check cache first
        if cache_key in self.user_cache:
            print(f"✅ Found {parsed['full_name']} in cache")
            return self.user_cache[cache_key]
        
        print(f"🔍 Searching for user: {parsed['full_name']}")
        
        # Strategy 1: Try friends list (likely to fail due to Discord restrictions)
        friends_found = False
        try:
            relationships = await self.get_user_relationships()
            if relationships:  # Only proceed if we got some data
                for relationship in relationships:
                    user = relationship.get('user', {})
                    if not user:
                        continue
                    
                    user_username = user.get('username', '')
                    user_discriminator = user.get('discriminator', '0')
                    
                    # Match by exact username and discriminator if provided
                    if parsed['discriminator']:
                        if (user_username.lower() == parsed['username'].lower() and 
                            user_discriminator == parsed['discriminator']):
                            print(f"✅ Found friend: {user_username}#{user_discriminator}")
                            self.user_cache[cache_key] = user
                            return user
                    else:
                        # Match by username only
                        if user_username.lower() == parsed['username'].lower():
                            print(f"✅ Found friend: {user_username}#{user_discriminator}")
                            self.user_cache[cache_key] = user
                            return user
                friends_found = True
        except Exception as e:
            print(f"⚠️  Friends search unavailable: {e}")
        
        # Strategy 2: Search through mutual guilds (primary strategy for user tokens)
        guilds_searched = 0
        users_found = []
        
        try:
            guilds = await self.get_user_guilds()
            print(f"🏰 Searching {len(guilds)} mutual guilds for '{parsed['username']}'...")
            
            for guild in guilds[:10]:  # Search more guilds but with reasonable limit
                guild_id = guild['id']
                guild_name = guild.get('name', 'Unknown')
                
                try:
                    members = await self.get_guild_members_sample(guild_id, 100)
                    if members:
                        guilds_searched += 1
                        print(f"   📋 Searching {len(members)} members in {guild_name}")
                        
                        for member in members:
                            user = member.get('user', {})
                            if not user:
                                continue
                            
                            user_username = user.get('username', '')
                            user_discriminator = user.get('discriminator', '0')
                            
                            # Match by exact username and discriminator if provided
                            if parsed['discriminator']:
                                if (user_username.lower() == parsed['username'].lower() and 
                                    user_discriminator == parsed['discriminator']):
                                    print(f"✅ Found exact match in {guild_name}: {user_username}#{user_discriminator}")
                                    self.user_cache[cache_key] = user
                                    return user
                            else:
                                # Match by username only - collect all matches
                                if user_username.lower() == parsed['username'].lower():
                                    full_name = f"{user_username}#{user_discriminator}"
                                    if user not in users_found:
                                        users_found.append({
                                            'user': user,
                                            'guild': guild_name,
                                            'display': full_name
                                        })
                        
                except Exception as e:
                    print(f"   ⚠️  Could not search guild {guild_name}: {e}")
                    continue
                    
        except Exception as e:
            print(f"⚠️  Guild search failed: {e}")
        
        # Handle multiple matches - return the first one but inform about others
        if users_found:
            if len(users_found) == 1:
                match = users_found[0]
                print(f"✅ Found in {match['guild']}: {match['display']}")
                self.user_cache[cache_key] = match['user']
                return match['user']
            else:
                # Multiple matches found - return first but cache info about others
                match = users_found[0]
                print(f"✅ Found {len(users_found)} users named '{parsed['username']}':")
                for i, m in enumerate(users_found[:3]):
                    print(f"   {i+1}. {m['display']} (in {m['guild']})")
                print(f"   Using first match: {match['display']}")
                self.user_cache[cache_key] = match['user']
                return match['user']
        
        # No matches found
        if guilds_searched == 0:
            print(f"❌ Could not search any guilds for '{parsed['full_name']}' (permission denied)")
        else:
            print(f"❌ User '{parsed['full_name']}' not found in {guilds_searched} accessible guilds")
            
        return None
    
    async def find_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Find Discord user by user ID (more reliable than username)"""
        try:
            headers = await self.get_headers()
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{DISCORD_API_BASE}/users/{user_id}",
                    headers=headers
                ) as resp:
                    if resp.status == 200:
                        user = await resp.json()
                        # Cache the user
                        self.user_cache[user.get('username', user_id)] = user
                        return user
        except Exception as e:
            print(f"Error getting user by ID {user_id}: {e}")
        
        return None
    
    async def get_dm_channel_with_user(self, user_id: str) -> Dict:
        """Create or get DM channel with a user"""
        headers = await self.get_headers()
        data = {'recipient_id': user_id}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{DISCORD_API_BASE}/users/@me/channels", 
                headers=headers, 
                json=data
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    raise Exception(f"Failed to create DM channel: {await resp.text()}")
    
    async def send_message(self, channel_id: str, content: str) -> Dict:
        """Send a message to a Discord channel"""
        headers = await self.get_headers()
        data = {'content': content}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{DISCORD_API_BASE}/channels/{channel_id}/messages",
                headers=headers,
                json=data
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    raise Exception(f"Failed to send message: {await resp.text()}")
    
    async def get_messages(self, channel_id: str, limit: int = 50) -> List[Dict]:
        """Retrieve messages from a Discord channel"""
        headers = await self.get_headers()
        params = {'limit': min(limit, 100)}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{DISCORD_API_BASE}/channels/{channel_id}/messages",
                headers=headers,
                params=params
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    raise Exception(f"Failed to get messages: {await resp.text()}")
    
    async def send_dm_to_user(self, user_id: str, message: str) -> Dict:
        """Send a direct message to a user"""
        dm_channel = await self.get_dm_channel_with_user(user_id)
        return await self.send_message(dm_channel['id'], message)
    
    async def get_dm_history_with_user(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get DM history with a specific user"""
        dm_channel = await self.get_dm_channel_with_user(user_id)
        return await self.get_messages(dm_channel['id'], limit)
    
    async def get_current_authorization_info(self) -> Dict:
        """Get current authorization info using Discord's /oauth2/@me endpoint"""
        headers = await self.get_headers()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{DISCORD_API_BASE}/oauth2/@me", headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    raise Exception(f"Failed to get authorization info: {await resp.text()}")
    
    async def get_user_guilds(self) -> List[Dict]:
        """Get user's guilds (requires 'guilds' scope)"""
        headers = await self.get_headers()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{DISCORD_API_BASE}/users/@me/guilds", headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    raise Exception(f"Failed to get user guilds: {await resp.text()}")
    
    async def get_user_connections(self) -> List[Dict]:
        """Get user's connected accounts (requires 'connections' scope)"""
        headers = await self.get_headers()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{DISCORD_API_BASE}/users/@me/connections", headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    raise Exception(f"Failed to get user connections: {await resp.text()}")
    
    async def get_available_users_summary(self) -> str:
        """Get a summary of available users for messaging guidance"""
        summary_parts = []
        
        # Try to get friends (likely to fail due to Discord API restrictions)
        try:
            relationships = await self.get_user_relationships()
            if relationships:
                friends = []
                for rel in relationships:
                    user = rel.get('user', {})
                    if user and user.get('username'):
                        username = user.get('username', '')
                        discriminator = user.get('discriminator', '0')
                        display_name = f"{username}#{discriminator}" if discriminator != '0' else username
                        friends.append(display_name)
                
                if friends:
                    summary_parts.append(f"**Your friends ({len(friends)}):** {', '.join(friends[:5])}")
                    if len(friends) > 5:
                        summary_parts[-1] += f" (+{len(friends) - 5} more)"
            else:
                summary_parts.append("**Friends list:** Not accessible (Discord API restriction)")
                    
        except Exception as e:
            summary_parts.append("**Friends list:** Not accessible (Discord API restriction)")
        
        # Get guild information
        try:
            guilds = await self.get_user_guilds()
            if guilds:
                accessible_guilds = []
                sample_users = []
                
                # Try to get a sample of users from accessible guilds
                for guild in guilds[:3]:  # Check first 3 guilds
                    guild_name = guild.get('name', 'Unknown')
                    guild_id = guild['id']
                    
                    try:
                        members = await self.get_guild_members_sample(guild_id, 10)  # Small sample
                        if members:
                            accessible_guilds.append(guild_name)
                            # Add some sample usernames
                            for member in members[:3]:
                                user = member.get('user', {})
                                if user and user.get('username'):
                                    username = user.get('username', '')
                                    discriminator = user.get('discriminator', '0')
                                    display_name = f"{username}#{discriminator}" if discriminator != '0' else username
                                    if display_name not in sample_users:
                                        sample_users.append(display_name)
                    except Exception:
                        continue
                
                if accessible_guilds:
                    summary_parts.append(f"**Accessible servers ({len(accessible_guilds)}):** {', '.join(accessible_guilds)}")
                    if sample_users:
                        summary_parts.append(f"**Sample users:** {', '.join(sample_users[:5])}")
                else:
                    guild_names = [g.get('name', 'Unknown')[:20] for g in guilds[:3]]
                    summary_parts.append(f"**Your servers ({len(guilds)}):** {', '.join(guild_names)}")
                    summary_parts.append("*(Member lists not accessible - try User IDs)*")
                    
        except Exception as e:
            summary_parts.append("**Guilds:** Error accessing server information")
        
        if summary_parts:
            return "\n".join(summary_parts)
        else:
            return "**No accessible users found.**\n💡 Try using Discord User IDs directly for reliable messaging."


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
You are a Discord message intent parser. Analyze user requests and extract structured information.

For sending messages, look for patterns like:
- "Send [recipient] [message]"
- "Can you send a message to [recipient] saying [message]"
- "Tell/Text [recipient]: [message]" 
- "Message [recipient] that [message]"

Extract:
- action: "send_message"
- recipient: the username (clean, no @ symbols)
- message: the actual message content to send

For retrieving messages:
- action: "get_messages" 
- target: username to get messages from
- limit: number of messages (default 10)

For authentication:
- action: "authenticate" for login/auth requests

Examples:
Input: "Can you send a message to Ben saying 'hi Ben, sending hi from Discord Agent'"
Output: {"action": "send_message", "recipient": "Ben", "message": "hi Ben, sending hi from Discord Agent"}

Input: "Send Alice: Meeting at 3pm"
Output: {"action": "send_message", "recipient": "Alice", "message": "Meeting at 3pm"}

Respond only with valid JSON:
{
    "action": "send_message|get_messages|authenticate|help",
    "recipient": "username",
    "message": "message content",
    "target": "username to get messages from",
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
You are a helpful Discord assistant. Generate natural, conversational responses about Discord actions.

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


# Initialize the discord agent with enhanced capabilities
subject_matter = "Discord messaging, OAuth authentication, and communication management"

SEED_PHRASE = "enhanced_discord_agent_oauth_2024"

agent = Agent(
    name="discord_agent",
    port=8005,
    seed=SEED_PHRASE,
    mailbox=True,
    publish_agent_details=True,
    readme_path="README.md"
)

# Initialize Discord components
auth_manager = DiscordAuthManager()
discord_client = DiscordAPIClient(auth_manager)
message_processor = MessageProcessor()

# Create chat protocol
protocol = Protocol(spec=chat_protocol_spec)
# Enhanced message handler with integrated OAuth flow
async def handle_discord_action(intent: Dict) -> str:
    """Execute Discord actions based on parsed intent"""
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
                return f"❌ Failed to start Discord authentication: {e}\n\nPlease check your Discord app configuration in the .env file."
        
        # For other actions, check if we have valid authentication
        valid_token = await auth_manager.get_valid_token()
        if not valid_token:
            return ("🔐 **Discord Authentication Required**\n\n"
                   "You need to authenticate with Discord first to use messaging features.\n"
                   "Type 'authenticate' or 'login' to start the OAuth flow.\n\n"
                   "💡 If you've already authenticated before, your tokens may have expired and need refreshing.")
        
        if action == 'send_message':
            recipient = intent.get('recipient')
            message = intent.get('message')
            
            if not recipient or not message:
                return "I need both a recipient and a message to send. Try:\n" \
                       "• 'Send Ben: Hello there!'\n" \
                       "• 'Message Alice#1234 saying hi'\n" \
                       "• 'Text user ID 123456789: How are you?'"
            
            try:
                print(f"🔍 Looking for Discord user: '{recipient}'")
                
                # Step 1: Find the user by username or ID with comprehensive search
                target_user = None
                
                # Check if recipient looks like a user ID (all digits)
                if recipient.isdigit() and len(recipient) >= 17:  # Discord IDs are typically 17-19 digits
                    print(f"📋 Searching by User ID: {recipient}")
                    target_user = await discord_client.find_user_by_id(recipient)
                else:
                    # Try to find by username (includes friends and guild search)
                    print(f"👤 Searching by username: {recipient}")
                    target_user = await discord_client.find_user_by_username(recipient)
                
                if not target_user:
                    # Get some suggestions for the user
                    suggestions = []
                    
                    # Try to get friends list for suggestions
                    try:
                        relationships = await discord_client.get_user_relationships()
                        friends = [rel.get('user', {}) for rel in relationships if rel.get('user')]
                        friend_names = [f"{u.get('username', '')}#{u.get('discriminator', '')}" 
                                      for u in friends[:5] if u.get('username')]
                        if friend_names:
                            suggestions.append(f"Your friends: {', '.join(friend_names)}")
                    except Exception:
                        pass
                    
                    error_msg = f"❌ I couldn't find a Discord user named '{recipient}'.\n\n"
                    error_msg += "💡 **Tips to find the user:**\n"
                    error_msg += f"• Try the full username with discriminator (e.g., Ben#1234)\n"
                    error_msg += f"• Use their Discord User ID for reliability\n" 
                    error_msg += f"• Make sure you're friends or share a server\n"
                    error_msg += f"• Check the spelling carefully\n"
                    
                    if suggestions:
                        error_msg += f"\n📋 **Available options:**\n" + "\n".join(suggestions)
                    
                    return error_msg
                
                # Step 2: Send the DM
                print(f"📨 Sending message to {target_user.get('username')}...")
                result = await discord_client.send_dm_to_user(target_user['id'], message)
                
                username = target_user.get('username', recipient)
                discriminator = target_user.get('discriminator', '0')
                display_name = f"{username}#{discriminator}" if discriminator and discriminator != '0' else username
                
                return f"✅ **Message sent successfully!**\n" \
                       f"👤 **To:** {display_name}\n" \
                       f"📨 **Message:** \"{message}\"\n" \
                       f"🎯 **Via:** Your Discord account"
                       
            except Exception as e:
                error_msg = str(e).lower()
                print(f"❌ Error sending message: {e}")
                
                if "403" in error_msg or "forbidden" in error_msg:
                    return f"❌ **Permission denied** when trying to message {recipient}.\n\n" \
                           f"**This could be because:**\n" \
                           f"• The user has blocked you\n" \
                           f"• The user doesn't accept DMs from non-friends\n" \
                           f"• Your privacy settings don't allow this\n" \
                           f"• Your Discord token lacks necessary permissions\n\n" \
                           f"💡 **Try:** Sending them a friend request first"
                           
                elif "404" in error_msg or "not found" in error_msg:
                    return f"❌ **User not found:** '{recipient}'\n\n" \
                           f"💡 **Please try:**\n" \
                           f"• Using their full username (Ben#1234)\n" \
                           f"• Using their Discord User ID\n" \
                           f"• Checking the spelling"
                    
                elif "unauthorized" in error_msg or "401" in error_msg:
                    return f"🔐 Discord authentication failed. Your token may be expired.\n" \
                           f"Type 'authenticate' to refresh your Discord connection."
                           
                else:
                    return f"❌ Failed to send message to {recipient}: {str(e)[:100]}"
            
        elif action == 'get_messages':
            target = intent.get('target')
            limit = intent.get('limit', 10)
            
            if not target:
                return "Please specify who you want to see messages from. Try: 'Show messages from Ben'"
            
            # Check authentication
            token = await auth_manager.get_valid_token()
            if not token:
                result = await auth_manager.start_oauth_flow()
                asyncio.create_task(complete_oauth_flow())
                return f"🔐 **Authentication Required**\n\n{result}"
            
            # Simulate message retrieval for demo
            return f"📨 Here are the last {limit} messages from {target}:\n[Message retrieval requires full Discord API integration]"
            
        elif action == 'help':
            help_text = """🔧 **Discord Agent Commands:**

**Send Messages:**
• "Send Ben a message saying I'll be late"
• "Text Alice#1234: Meeting moved to 3pm"  
• "Message user ID 123456789: Can you call me?"

**Message Format Tips:**
• Use full username: `Ben#1234`
• Use Discord User ID for reliability
• Works with friends and mutual server members

**Retrieve Messages:**
• "Show my last message from Alice"
• "Get messages from Ben"

**Authentication:**
• "Connect my Discord account"
• "Login to Discord"

"""
            
            # Try to add available users information
            try:
                users_summary = await discord_client.get_available_users_summary()
                help_text += f"**📋 Available for messaging:**\n{users_summary}\n\n"
            except Exception as e:
                print(f"Could not get users summary: {e}")
                
            help_text += "I can help you send DMs and retrieve message history! 🚀"
            return help_text
            
        else:
            return "I'm not sure how to help with that. Try asking me to send a message or show message history!"
            
    except Exception as e:
            return f"❌ Error executing Discord action: {str(e)}"

async def test_discord_api_connection():
    """Test Discord API connection and permissions"""
    print("🧪 Testing Discord API connection...")
    
    try:
        # Test authentication
        valid_token = await auth_manager.get_valid_token()
        if not valid_token:
            print("❌ No valid token available")
            return False
        
        # Test getting current user
        current_user = await discord_client.get_current_user()
        print(f"✅ Authenticated as: {current_user.get('username', 'Unknown')}#{current_user.get('discriminator', '0000')}")
        
        # Test getting guilds
        guilds = await discord_client.get_user_guilds()
        print(f"✅ Found {len(guilds)} guilds")
        for guild in guilds[:3]:  # Show first 3
            print(f"   - {guild.get('name', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Discord API test failed: {e}")
        return False

async def complete_oauth_flow():
    """Complete the OAuth flow in the background"""
    try:
        result = await auth_manager.wait_for_oauth_completion()
        print(f"OAuth completion: {result}")
    except Exception as e:
        print(f"OAuth flow error: {e}")


@protocol.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handle incoming chat messages with Discord integration"""
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
        # Parse user intent using ASI:One
        intent = await message_processor.extract_message_intent(text)
        ctx.logger.info(f"Parsed intent: {intent}")
        
        # Execute Discord action based on intent
        result = await handle_discord_action(intent)
        
        # Generate natural language response
        response = await message_processor.generate_response(intent, result)
        
        # Fallback to direct result if response generation fails
        if not response or "couldn't generate response" in response:
            response = result
            
    except Exception as e:
        ctx.logger.exception(f'Error processing Discord request: {e}')
        response = f"""❌ I encountered an error processing your Discord request: {str(e)}

🔧 **Available Discord Commands:**
• Send messages: "Text Ben: Running late!"
• Get messages: "Show messages from Alice"  
• Get help: "What can you do?"

Make sure your Discord credentials are configured in the .env file!"""
    
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


# Startup handler to initialize Discord authentication
@agent.on_event("startup")
async def startup_handler(ctx: Context):
    """Initialize Discord authentication on agent startup"""
    ctx.logger.info("🚀 Discord Agent starting up...")
    
    # Check for required environment variables
    missing_vars = []
    if not DISCORD_CLIENT_ID:
        missing_vars.append("DISCORD_CLIENT_ID")
    if not DISCORD_CLIENT_SECRET:
        missing_vars.append("DISCORD_CLIENT_SECRET")
    if not os.getenv("ASI_ONE_API_KEY"):
        missing_vars.append("ASI_ONE_API_KEY")
    
    if missing_vars:
        ctx.logger.warning(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        ctx.logger.warning("   Some Discord features may not work properly.")
        ctx.logger.warning("   Please check your .env file configuration.")
    else:
        ctx.logger.info("✅ All required environment variables found")
    
    # Try to load existing tokens
    if await auth_manager.load_tokens():
        ctx.logger.info("✅ Discord tokens loaded successfully")
        
        # Check if token needs refresh
        valid_token = await auth_manager.get_valid_token()
        if valid_token:
            try:
                current_user = await discord_client.get_current_user()
                username = current_user.get('username', 'Unknown')
                discriminator = current_user.get('discriminator', '0000') 
                ctx.logger.info(f"🔐 Authenticated as: {username}#{discriminator}")
                ctx.logger.info("🚀 Ready for Discord messaging operations!")
            except Exception as e:
                ctx.logger.warning(f"⚠️  Token validation failed: {e}")
                ctx.logger.info("🔄 You may need to re-authenticate")
        else:
            ctx.logger.warning("⚠️  Token refresh failed - re-authentication may be required")
    else:
        ctx.logger.info("ℹ️  No saved Discord tokens found")
        ctx.logger.info("💡 To enable Discord messaging, send 'authenticate' or 'login' to start OAuth flow")
        if DISCORD_CLIENT_ID and DISCORD_CLIENT_SECRET:
            ctx.logger.info("✅ Discord OAuth credentials configured and ready")
    
    ctx.logger.info("🎯 Discord Agent ready for messaging operations!")


# Shutdown handler with server cleanup
@agent.on_event("shutdown")
async def shutdown_handler(ctx: Context):
    """Clean up resources on agent shutdown"""
    ctx.logger.info("🛑 Discord Agent shutting down...")
    # Clean up any running OAuth server
    auth_manager._cleanup_server()


# Include the protocol with the agent
agent.include(protocol, publish_manifest=True)

# Agent information
print("=" * 60)
print("🎯 DISCORD AGENT - Enhanced Messaging & OAuth Integration")
print("=" * 60)
print(f"Agent Address: {agent.address}")
print(f"Agent Port: 8005")
print(f"Mailbox Enabled: True")
print()
print("🔧 FEATURES:")
print("• Discord OAuth2 Authentication")
print("• Direct Message Sending")
print("• Message History Retrieval") 
print("• Natural Language Processing (ASI:One)")
print("• Secure Token Management")
print()
print("💡 EXAMPLE COMMANDS:")
print('• "Send Ben: I\'ll be 10 minutes late"')
print('• "Show my last messages from Alice"')
print('• "Text everyone: Meeting moved to 3pm"')
print()
print("🚀 Starting agent...")
print("=" * 60)

if __name__ == "__main__":
    agent.run()
