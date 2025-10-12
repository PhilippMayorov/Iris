#!/usr/bin/env python3
"""
Complete Discord OAuth2 Flow Test

This script runs a complete OAuth2 flow test with real Discord API integration.
It starts a local callback server and guides you through the authorization process.
"""

import os
import asyncio
import webbrowser
import secrets
import json
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs, urlencode
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import requests
from dotenv import load_dotenv
from cryptography.fernet import Fernet

# Load environment variables
load_dotenv()

# Discord configuration from environment
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:8080/callback")

# Encryption key for secure token storage (same as discord_agent.py)
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())

class SecureTokenStorage:
    """Secure token storage using encryption - matches discord_agent.py implementation"""
    
    def __init__(self):
        self.token_file = "discord_tokens.enc"
        self.cipher = Fernet(ENCRYPTION_KEY.encode()) if ENCRYPTION_KEY else None
    
    def save_tokens(self, token_data: dict) -> bool:
        """Securely save tokens to encrypted file"""
        try:
            if not self.cipher:
                print("⚠️  Warning: No encryption key available, tokens not saved")
                return False
            
            # Add timestamp for expiry calculation
            token_data_with_timestamp = {
                **token_data,
                'saved_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(seconds=token_data.get('expires_in', 3600))).isoformat()
            }
            
            encrypted_data = self.cipher.encrypt(json.dumps(token_data_with_timestamp).encode())
            with open(self.token_file, 'wb') as f:
                f.write(encrypted_data)
            
            print("🔐 Tokens securely saved to encrypted file")
            return True
            
        except Exception as e:
            print(f"❌ Error saving tokens: {e}")
            return False
    
    def load_tokens(self) -> dict:
        """Load and decrypt saved tokens"""
        try:
            if not os.path.exists(self.token_file) or not self.cipher:
                return None
                
            with open(self.token_file, 'rb') as f:
                encrypted_data = f.read()
                
            decrypted_data = self.cipher.decrypt(encrypted_data)
            token_data = json.loads(decrypted_data.decode())
            
            return token_data
            
        except Exception as e:
            print(f"❌ Error loading tokens: {e}")
            return None

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
                <head><title>Discord OAuth2 Test - Error</title></head>
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
                <head><title>Discord OAuth2 Test - Success</title></head>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px;">
                    <h1 style="color: #28a745;">✅ Discord Authorization Successful!</h1>
                    <p>Authorization code received successfully.</p>
                    <p>You can close this window and return to the terminal to see the results.</p>
                    <script>setTimeout(() => window.close(), 5000);</script>
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
                <head><title>Discord OAuth2 Test - Error</title></head>
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

async def run_complete_oauth_flow():
    """Run complete OAuth2 flow with Discord"""
    print("=" * 70)
    print("🎯 DISCORD OAUTH2 - Complete Flow Test")
    print("=" * 70)
    
    # Validate environment variables
    if not DISCORD_CLIENT_ID or not DISCORD_CLIENT_SECRET:
        print("❌ Missing Discord credentials in environment variables")
        print("   Please check your .env file")
        return False
    
    print(f"✅ Client ID: {DISCORD_CLIENT_ID}")
    print(f"✅ Redirect URI: {DISCORD_REDIRECT_URI}")
    
    # Extract port from redirect URI
    parsed_uri = urlparse(DISCORD_REDIRECT_URI)
    callback_port = parsed_uri.port or 8080
    
    print(f"🔧 Starting callback server on port {callback_port}...")
    
    # Start local callback server
    server = HTTPServer(('localhost', callback_port), OAuthCallbackHandler)
    server.authorization_code = None
    server.authorization_error = None
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    server.expected_state = state
    
    # Start server in background thread
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    # Generate OAuth URL
    scopes = ['identify', 'guilds']  # Basic scopes that don't require approval
    oauth_url = (
        f"https://discord.com/oauth2/authorize?"
        f"client_id={DISCORD_CLIENT_ID}&"
        f"redirect_uri={DISCORD_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope={'+'.join(scopes)}&"
        f"state={state}"
    )
    
    print(f"\n🔗 Opening Discord authorization URL...")
    print(f"URL: {oauth_url}")
    print(f"\n📍 If the browser doesn't open automatically, copy and paste the URL above")
    print("⏳ Waiting for you to authorize the application...")
    
    # Open browser
    webbrowser.open(oauth_url)
    
    # Wait for callback with timeout
    timeout_seconds = 120  # 2 minutes
    elapsed = 0
    
    while server.authorization_code is None and server.authorization_error is None and elapsed < timeout_seconds:
        await asyncio.sleep(1)
        elapsed += 1
        if elapsed % 10 == 0:
            print(f"   Still waiting... ({elapsed}/{timeout_seconds}s)")
    
    # Clean up server
    server.shutdown()
    server.server_close()
    
    if elapsed >= timeout_seconds:
        print("⏰ Authorization timed out after 2 minutes")
        return False
    
    if server.authorization_error:
        print(f"❌ Authorization failed: {server.authorization_error}")
        return False
    
    if not server.authorization_code:
        print("❌ No authorization code received")
        return False
    
    print(f"✅ Authorization code received: {server.authorization_code[:20]}...")
    
    # Exchange code for token
    print("\n🔄 Exchanging authorization code for access token...")
    
    try:
        token_response = requests.post(
            'https://discord.com/api/v10/oauth2/token',
            data={
                'grant_type': 'authorization_code',
                'code': server.authorization_code,
                'redirect_uri': DISCORD_REDIRECT_URI
            },
            headers={
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            auth=(DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET)  # HTTP Basic authentication
        )
        
        if token_response.status_code == 200:
            token_data = token_response.json()
            print("✅ Successfully obtained access token!")
            print(f"   Token Type: {token_data.get('token_type')}")
            print(f"   Expires In: {token_data.get('expires_in')} seconds")
            print(f"   Scope: {token_data.get('scope')}")
            print(f"   Access Token: {token_data['access_token'][:20]}...")
            
            if 'refresh_token' in token_data:
                print(f"   Refresh Token: {token_data['refresh_token'][:20]}...")
            
            # Save tokens securely for discord_agent to use
            print("\n💾 Saving tokens securely...")
            token_storage = SecureTokenStorage()
            if token_storage.save_tokens(token_data):
                print("✅ Tokens saved successfully! discord_agent can now use them automatically.")
            else:
                print("⚠️  Warning: Token save failed - you may need to re-authenticate")
            
            # Test the token by getting user info
            print("\n👤 Testing access token by getting user info...")
            user_response = requests.get(
                'https://discord.com/api/v10/users/@me',
                headers={'Authorization': f"Bearer {token_data['access_token']}"}
            )
            
            if user_response.status_code == 200:
                user_data = user_response.json()
                username = user_data.get('username', 'Unknown')
                discriminator = user_data.get('discriminator', '0')
                user_id = user_data.get('id', 'Unknown')
                
                print(f"✅ Successfully authenticated as:")
                print(f"   Username: {username}#{discriminator}")
                print(f"   User ID: {user_id}")
                print(f"   Avatar: {user_data.get('avatar', 'None')}")
                
                # Test guild access if available
                if 'guilds' in token_data.get('scope', ''):
                    print("\n🏰 Testing guild access...")
                    guilds_response = requests.get(
                        'https://discord.com/api/v10/users/@me/guilds',
                        headers={'Authorization': f"Bearer {token_data['access_token']}"}
                    )
                    
                    if guilds_response.status_code == 200:
                        guilds = guilds_response.json()
                        print(f"✅ User is in {len(guilds)} guild(s)")
                        for guild in guilds[:3]:  # Show first 3 guilds
                            print(f"   - {guild.get('name', 'Unknown')} (ID: {guild.get('id')})")
                        if len(guilds) > 3:
                            print(f"   ... and {len(guilds) - 3} more")
                    else:
                        print(f"⚠️  Guild access failed: {guilds_response.status_code}")
                
                print("\n🎉 Complete OAuth2 flow test successful!")
                print("📡 discord_agent can now authenticate automatically using saved tokens")
                return True
            else:
                print(f"❌ Token validation failed: {user_response.status_code}")
                print(f"   Response: {user_response.text}")
                return False
        else:
            print(f"❌ Token exchange failed: {token_response.status_code}")
            print(f"   Response: {token_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during token exchange: {e}")
        return False

async def main():
    """Main test function"""
    try:
        success = await run_complete_oauth_flow()
        
        print("\n" + "=" * 70)
        if success:
            print("🎉 COMPLETE OAUTH2 FLOW TEST: SUCCESS")
            print("   Your Discord OAuth2 implementation is working correctly!")
        else:
            print("❌ COMPLETE OAUTH2 FLOW TEST: FAILED")
            print("   Please check the errors above and try again.")
        print("=" * 70)
        
        return success
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(main())