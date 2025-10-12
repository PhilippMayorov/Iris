"""
Slack Authentication Setup Script

Run this script once to authenticate your Slack agent with your account.
This script follows Slack's OAuth 2.0 flow documentation exactly as specified at:
https://api.slack.com/authentication/oauth-v2

After successful authentication, the agent will use cached credentials.
"""

import os
import webbrowser
import asyncio
import json
import threading
import time
import ssl
import socket
import ipaddress
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import aiofiles
import requests
from dotenv import load_dotenv

# Load environment variables from project root
load_dotenv("../../../../.env")

# Slack OAuth 2.0 Configuration
SLACK_CLIENT_ID = os.getenv("SLACK_CLIENT_ID")
SLACK_CLIENT_SECRET = os.getenv("SLACK_CLIENT_SECRET")
SLACK_REDIRECT_URI = os.getenv("SLACK_REDIRECT_URI", "https://localhost:8080/callback")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())

# Slack OAuth 2.0 endpoints (following official documentation)
SLACK_OAUTH_AUTHORIZE_URL = "https://slack.com/oauth/v2/authorize"
SLACK_OAUTH_ACCESS_URL = "https://slack.com/api/oauth.v2.access"

# Slack scopes following official documentation
# Bot scopes - for app identity and capabilities
SLACK_BOT_SCOPES = [
    "chat:write",          # Send messages to channels and DMs
    "im:write",            # Send direct messages  
    "im:read",             # Read direct messages
    "channels:read",       # View basic info about public channels
    "im:history",          # View messages in direct messages
    "users:read"           # View people in workspace
]

# User scopes - for acting on behalf of users (optional)
SLACK_USER_SCOPES = [
    "chat:write"           # Send messages as user
]

def create_self_signed_cert():
    """
    Create a self-signed SSL certificate for localhost HTTPS server
    Required for Slack OAuth which mandates HTTPS redirect URIs
    """
    cert_file = "localhost.crt"
    key_file = "localhost.key"
    
    # Check if certificate already exists and is valid
    if os.path.exists(cert_file) and os.path.exists(key_file):
        try:
            # Load and check existing certificate
            with open(cert_file, 'rb') as f:
                cert_data = f.read()
            cert = x509.load_pem_x509_certificate(cert_data)
            
            # Check if certificate is still valid (not expired)
            if cert.not_valid_after > datetime.utcnow():
                print("✅ Valid SSL certificate found")
                return cert_file, key_file
            else:
                print("⏰ SSL certificate expired, creating new one...")
        except Exception:
            print("⚠️  Invalid SSL certificate found, creating new one...")
    
    print("🔐 Creating self-signed SSL certificate for localhost...")
    
    try:
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Dev"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Localhost"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Slack Agent Dev"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)  # Valid for 1 year
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Write certificate to file
        with open(cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        # Write private key to file
        with open(key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        print(f"✅ SSL certificate created: {cert_file}")
        print(f"✅ SSL private key created: {key_file}")
        print("⚠️  Note: Browser will show security warning for self-signed certificate")
        
        return cert_file, key_file
        
    except Exception as e:
        print(f"❌ Failed to create SSL certificate: {e}")
        raise Exception(f"SSL certificate creation failed: {e}")

class HTTPSServer(HTTPServer):
    """HTTPS Server for Slack OAuth callback"""
    
    def __init__(self, server_address, RequestHandlerClass, cert_file, key_file):
        super().__init__(server_address, RequestHandlerClass)
        
        # Create SSL context
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(cert_file, key_file)
        
        # Wrap the socket with SSL
        self.socket = context.wrap_socket(self.socket, server_side=True)
        
        # Initialize OAuth response tracking
        self.authorization_code = None
        self.authorization_error = None
        self.state = None

class SlackOAuthCallbackHandler(BaseHTTPRequestHandler):
    """
    Handles OAuth2 callback from Slack during setup
    Following Slack's OAuth 2.0 documentation for callback handling
    """
    
    def do_GET(self):
        """Handle GET request from Slack OAuth callback"""
        print(f"📨 Callback received: {self.path}")
        
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        if 'code' in query_params:
            # Success - authorization code received
            self.server.authorization_code = query_params['code'][0]
            
            # Check state parameter if provided (security measure)
            if 'state' in query_params:
                self.server.state = query_params['state'][0]
            
            print(f"✅ Authorization code received: {self.server.authorization_code[:20]}...")
            self.send_success_response()
            
        elif 'error' in query_params:
            # Error in authorization
            error = query_params.get('error', ['unknown'])[0]
            error_description = query_params.get('error_description', ['No description'])[0]
            self.server.authorization_error = error
            print(f"❌ OAuth error: {error} - {error_description}")
            self.send_error_response(f"Authorization Failed: {error}", error_description)
        else:
            # Unexpected callback
            print("⚠️  Unexpected callback format")
            self.send_error_response("Invalid Callback", "No authorization code or error received")
        
        # Schedule server shutdown after handling the request
        threading.Thread(target=self._shutdown_server).start()
    
    def _shutdown_server(self):
        """Shutdown server after a brief delay to allow response to complete"""
        time.sleep(0.5)  # Allow response to be sent
        self.server.shutdown()
    
    def send_success_response(self):
        """Send success HTML response following Slack's best practices"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.end_headers()
        
        html_response = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Slack OAuth - Success</title>
                <meta charset="utf-8">
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
                           max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }
                    .success { color: #2eb886; font-size: 48px; margin-bottom: 20px; }
                    .title { color: #1d1c1d; font-size: 24px; margin-bottom: 16px; }
                    .message { color: #616061; font-size: 16px; line-height: 1.5; }
                </style>
            </head>
            <body>
                <div class="success">✅</div>
                <h1 class="title">Slack Authorization Successful!</h1>
                <p class="message">Your Slack agent has been authorized successfully.</p>
                <p class="message">Authorization code received and token exchange is in progress...</p>
                <p class="message"><strong>You can close this window and return to the terminal.</strong></p>
                <script>
                    // Auto-close after 3 seconds
                    setTimeout(() => {
                        try { window.close(); } catch(e) { console.log("Cannot auto-close window"); }
                    }, 3000);
                </script>
            </body>
            </html>
        """
        self.wfile.write(html_response.encode('utf-8'))
    
    def send_error_response(self, title: str, description: str = ""):
        """Send error HTML response following Slack's error handling practices"""
        self.send_response(400)
        self.send_header('Content-type', 'text/html')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.end_headers()
        
        html_response = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Slack OAuth - Error</title>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; 
                           max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }}
                    .error {{ color: #e01e5a; font-size: 48px; margin-bottom: 20px; }}
                    .title {{ color: #1d1c1d; font-size: 24px; margin-bottom: 16px; }}
                    .message {{ color: #616061; font-size: 16px; line-height: 1.5; }}
                </style>
            </head>
            <body>
                <div class="error">❌</div>
                <h1 class="title">{title}</h1>
                <p class="message"><strong>Error:</strong> {description}</p>
                <p class="message">Please close this window and try the setup again.</p>
                <p class="message">Check the terminal for troubleshooting information.</p>
            </body>
            </html>
        """
        self.wfile.write(html_response.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Suppress default server log messages for cleaner output"""
        pass

def generate_oauth_url(state: str = None):
    """
    Generate Slack OAuth 2.0 authorization URL following official documentation
    https://api.slack.com/authentication/oauth-v2#asking
    """
    if not SLACK_CLIENT_ID:
        print("❌ Cannot generate OAuth URL: SLACK_CLIENT_ID is missing")
        return None
    
    # OAuth parameters exactly as specified in Slack documentation
    oauth_params = {
        'client_id': SLACK_CLIENT_ID,
        'scope': ','.join(SLACK_BOT_SCOPES),  # Bot scopes (comma-separated)
        'redirect_uri': SLACK_REDIRECT_URI,
        'response_type': 'code'
    }
    
    # Add user scopes if specified (optional)
    if SLACK_USER_SCOPES:
        oauth_params['user_scope'] = ','.join(SLACK_USER_SCOPES)
    
    # Add state parameter for security (optional but recommended)
    if state:
        oauth_params['state'] = state
    
    # Generate the full OAuth URL following Slack's format
    oauth_url = f"{SLACK_OAUTH_AUTHORIZE_URL}?{urlencode(oauth_params)}"
    
    print(f"🔗 Generated OAuth URL with scopes: {oauth_params['scope']}")
    return oauth_url

def exchange_code_for_token(code: str) -> dict:
    """
    Exchange authorization code for access token following Slack documentation
    https://api.slack.com/authentication/oauth-v2#exchanging
    """
    print("🔄 Exchanging authorization code for access token...")
    print(f"   Using code: {code[:20]}...")
    
    # Prepare the request data exactly as specified in Slack documentation
    # Using form data as shown in: curl -F code=1234 -F client_id=... -F client_secret=...
    data = {
        'code': code,
        'client_id': SLACK_CLIENT_ID,
        'client_secret': SLACK_CLIENT_SECRET,
        'redirect_uri': SLACK_REDIRECT_URI  # Must match the one used in authorization
    }
    
    print(f"   Posting to: {SLACK_OAUTH_ACCESS_URL}")
    
    try:
        # Make the token exchange request using form data (application/x-www-form-urlencoded)
        response = requests.post(
            SLACK_OAUTH_ACCESS_URL, 
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        print(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            
            if token_data.get('ok'):
                print("✅ Token exchange successful!")
                
                # Display received data (following Slack's response format)
                if 'access_token' in token_data:
                    print(f"   Bot token: {token_data['access_token'][:20]}...")
                
                if 'team' in token_data:
                    team_info = token_data['team']
                    print(f"   Workspace: {team_info.get('name', 'Unknown')} (ID: {team_info.get('id', 'Unknown')})")
                
                if 'authed_user' in token_data:
                    user_info = token_data['authed_user']
                    print(f"   User: {user_info.get('id', 'Unknown')}")
                    if 'access_token' in user_info:
                        print(f"   User token: {user_info['access_token'][:20]}...")
                
                return token_data
            else:
                error_msg = token_data.get('error', 'Unknown error')
                error_detail = token_data.get('error_description', 'No additional details')
                raise Exception(f"Slack API error: {error_msg} - {error_detail}")
        else:
            print(f"❌ HTTP Error {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            raise Exception(f"Token exchange failed: HTTP {response.status_code}")
            
    except requests.RequestException as e:
        print(f"❌ Network error during token exchange: {e}")
        raise Exception(f"Network error during token exchange: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {e}")
        raise Exception(f"Invalid JSON response from Slack: {e}")

async def save_tokens_securely(token_data: dict):
    """Save tokens securely using encryption like the main agent"""
    print("💾 Saving tokens securely...")
    
    token_file = "slack_tokens.enc"
    
    if not ENCRYPTION_KEY:
        print("⚠️  Warning: No encryption key available, tokens won't be encrypted")
        return False
    
    try:
        cipher = Fernet(ENCRYPTION_KEY.encode())
        
        # Enhanced token data with timestamps (matching main agent format)
        enhanced_token_data = {
            **token_data,
            'saved_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(days=365)).isoformat()  # Slack tokens don't expire typically
        }
        
        encrypted_data = cipher.encrypt(json.dumps(enhanced_token_data).encode())
        
        async with aiofiles.open(token_file, 'wb') as f:
            await f.write(encrypted_data)
        
        print(f"✅ Tokens saved securely to {token_file}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to save tokens: {e}")
        return False

async def complete_oauth_flow():
    """
    Complete OAuth flow with HTTPS callback server and token exchange
    Following Slack's OAuth 2.0 documentation with HTTPS requirement
    """
    print("\n🚀 Starting Slack OAuth 2.0 flow with HTTPS...")
    print("   Following: https://api.slack.com/authentication/oauth-v2")
    print("   Note: Slack requires HTTPS for OAuth redirect URIs")
    
    # Extract port from redirect URI
    parsed_uri = urlparse(SLACK_REDIRECT_URI)
    callback_port = parsed_uri.port or 8080
    callback_host = parsed_uri.hostname or 'localhost'
    
    print(f"📍 Callback server config:")
    print(f"   Host: {callback_host}")
    print(f"   Port: {callback_port}")
    print(f"   Protocol: HTTPS (required by Slack)")
    print(f"   Full URI: {SLACK_REDIRECT_URI}")
    
    server = None
    server_thread = None
    
    try:
        # Step 1: Create SSL certificate for HTTPS
        print("\n🔐 Step 1: Setting up HTTPS server...")
        cert_file, key_file = create_self_signed_cert()
        
        # Step 2: Start HTTPS callback server
        print("\n🌐 Step 2: Starting HTTPS OAuth callback server...")
        server = HTTPSServer((callback_host, callback_port), SlackOAuthCallbackHandler, cert_file, key_file)
        
        # Start server in background thread
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        print(f"✅ HTTPS callback server running at https://{callback_host}:{callback_port}")
        print("⚠️  Browser may show security warning for self-signed certificate")
        
        # Step 3: Generate OAuth URL and redirect user
        print("\n🔗 Step 3: Generating OAuth authorization URL...")
        state_value = f"setup_{int(time.time())}"  # Simple state for security
        oauth_url = generate_oauth_url(state=state_value)
        
        if not oauth_url:
            raise Exception("Cannot generate OAuth URL - missing Client ID")
        
        print("🌐 Opening authorization URL in browser...")
        print(f"   URL: {oauth_url[:100]}...")
        
        # Open browser for user authorization
        try:
            webbrowser.open(oauth_url)
            print("✅ Browser opened for authorization")
        except Exception as e:
            print(f"⚠️  Could not open browser automatically: {e}")
            print("Please manually open this URL in your browser:")
            print(f"   {oauth_url}")
        
        # Step 4: Wait for user to authorize and callback
        print("\n⏳ Step 4: Waiting for user authorization...")
        print("   → Please authorize the app in your browser")
        print("   → Browser will show security warning - click 'Advanced' then 'Proceed to localhost'")
        print("   → You will be redirected back to this HTTPS server")
        
        timeout = 180  # 3 minutes for user to complete authorization
        elapsed = 0
        
        while (server.authorization_code is None and 
               server.authorization_error is None and 
               elapsed < timeout):
            time.sleep(1)
            elapsed += 1
            
            # Show progress every 15 seconds
            if elapsed % 15 == 0:
                remaining = timeout - elapsed
                print(f"   Still waiting... ({elapsed}s elapsed, {remaining}s remaining)")
                if elapsed == 15:
                    print("   💡 If browser shows security warning, click 'Advanced' → 'Proceed to localhost'")
        
        # Step 5: Process callback result
        print("\n🔄 Step 5: Processing authorization result...")
        
        if server.authorization_error:
            raise Exception(f"OAuth authorization failed: {server.authorization_error}")
        
        if not server.authorization_code:
            if elapsed >= timeout:
                raise Exception("OAuth authorization timed out - please try again")
            else:
                raise Exception("No authorization code received")
        
        print(f"✅ Authorization code received: {server.authorization_code[:15]}...")
        
        # Step 6: Exchange code for tokens
        print("\n🔑 Step 6: Exchanging authorization code for access tokens...")
        token_data = exchange_code_for_token(server.authorization_code)
        
        # Step 7: Save tokens securely
        print("\n💾 Step 7: Saving tokens securely...")
        success = await save_tokens_securely(token_data)
        
        if success:
            print("\n🎉 SLACK OAUTH SETUP COMPLETE!")
            print("=" * 50)
            print("✅ Authorization successful")
            print("✅ Tokens exchanged")
            print("✅ Credentials saved securely")
            print(f"✅ Workspace: {token_data.get('team', {}).get('name', 'Unknown')}")
            
            # Show next steps
            print("\n🚀 NEXT STEPS:")
            print("1. Start the agent: python slack_agent.py")
            print("2. Send test commands like:")
            print("   → 'Send Alice a message saying hello'")
            print("   → 'Read my last DM from Bob'")
            print("   → 'Send a message to #general saying good morning'")
            
            return True
        else:
            raise Exception("Token saving failed - check permissions and encryption key")
            
    except Exception as e:
        print(f"\n❌ OAuth flow failed: {e}")
        
        # Show troubleshooting info
        print("\n🔧 TROUBLESHOOTING:")
        if "connection refused" in str(e).lower() or "err_connection_refused" in str(e).lower():
            print("• Connection Refused is normal during setup - it means callback server isn't ready")
            print("• Try running this setup script again")
            print("• Ensure no other process is using the callback port")
        elif "redirect_uri" in str(e).lower():
            print(f"• Redirect URI mismatch - ensure Slack app is configured with: {SLACK_REDIRECT_URI}")
            print("• Go to https://api.slack.com/apps → Your App → OAuth & Permissions")
            print("• Add the exact redirect URI to 'Redirect URLs' section")
        elif "invalid_client" in str(e).lower():
            print("• Check SLACK_CLIENT_ID and SLACK_CLIENT_SECRET in .env file")
            print("• Ensure credentials match your Slack app configuration")
        elif "timeout" in str(e).lower():
            print("• Authorization timed out - try running setup again")
            print("• Ensure you complete the authorization within 3 minutes")
        
        return False
        
    finally:
        # Clean up server
        if server:
            try:
                server.shutdown()
                server.server_close()
                print("🧹 Callback server stopped")
            except Exception as e:
                print(f"⚠️  Error stopping server: {e}")
        
        if server_thread and server_thread.is_alive():
            server_thread.join(timeout=2)

def validate_redirect_uri():
    """
    Validate redirect URI for Slack OAuth compliance
    Slack requires HTTPS for all redirect URIs, including localhost
    """
    if not SLACK_REDIRECT_URI:
        return False, "No redirect URI configured"
    
    # Slack requires HTTPS for OAuth redirect URIs
    if not SLACK_REDIRECT_URI.startswith('https://'):
        return False, f"Slack requires HTTPS for redirect URIs. Current: {SLACK_REDIRECT_URI}"
    
    # Check for callback path
    if not SLACK_REDIRECT_URI.endswith('/callback'):
        return False, f"Redirect URI should end with '/callback'. Current: {SLACK_REDIRECT_URI}"
    
    # Check for localhost (common for development)
    if 'localhost' in SLACK_REDIRECT_URI:
        return True, "Valid HTTPS localhost redirect URI (self-signed certificate will be created)"
    else:
        return True, "Valid HTTPS redirect URI"

async def setup_slack_auth():
    """
    Set up Slack authentication following Slack's OAuth 2.0 documentation
    https://api.slack.com/authentication/oauth-v2
    """
    
    print("💬 Slack Agent OAuth 2.0 Setup")
    print("=" * 50)
    print("📚 Following: https://api.slack.com/authentication/oauth-v2")
    print()
    
    try:
        # Step 1: Validate environment configuration
        print("🔍 Step 1: Validating configuration...")
        
        if not SLACK_CLIENT_ID:
            print("❌ SLACK_CLIENT_ID not found in .env file")
            print("   Please add your Slack app's Client ID to .env")
            return False
            
        if not SLACK_CLIENT_SECRET:
            print("❌ SLACK_CLIENT_SECRET not found in .env file")
            print("   Please add your Slack app's Client Secret to .env")
            return False
        
        print(f"✅ Client ID: {SLACK_CLIENT_ID[:10]}...")
        print(f"✅ Client Secret: {'*' * 20}")
        
        # Step 2: Validate redirect URI
        print("\n🔍 Step 2: Validating redirect URI...")
        
        uri_valid, uri_message = validate_redirect_uri()
        if not uri_valid:
            print(f"❌ {uri_message}")
            print("\n� SLACK REDIRECT URI REQUIREMENTS:")
            print("• Must use HTTP or HTTPS protocol")
            print("• For production: HTTPS is required")
            print("• For local development: HTTP localhost is acceptable")
            print("• Must end with '/callback'")
            print("• Must match EXACTLY in Slack App settings")
            print(f"\n🔧 Current URI: {SLACK_REDIRECT_URI}")
            print("\n� TO FIX:")
            print("1. Go to https://api.slack.com/apps")
            print("2. Select your app → OAuth & Permissions")
            print("3. Add your redirect URI to 'Redirect URLs'")
            return False
        
        print(f"✅ {uri_message}: {SLACK_REDIRECT_URI}")
        
        # Step 3: Display Slack app configuration requirements
        print("\n📋 Step 3: Required Slack App Configuration")
        print("   (Configure at: https://api.slack.com/apps)")
        print()
        print("🔗 OAuth & Permissions → Redirect URLs:")
        print(f"   {SLACK_REDIRECT_URI}")
        print("   ⚠️  Must be EXACTLY this HTTPS URL (Slack requirement)")
        print()
        print("🤖 OAuth & Permissions → Bot Token Scopes:")
        for scope in SLACK_BOT_SCOPES:
            print(f"   • {scope}")
        
        if SLACK_USER_SCOPES:
            print()
            print("👤 OAuth & Permissions → User Token Scopes:")
            for scope in SLACK_USER_SCOPES:
                print(f"   • {scope}")
        
        # Step 4: Generate OAuth URL for verification
        print("\n🔗 Step 4: OAuth URL Generation...")
        oauth_url = generate_oauth_url()
        if not oauth_url:
            print("❌ Cannot generate OAuth URL")
            return False
        
        print(f"✅ OAuth URL generated successfully")
        
        # Step 5: Choose setup method
        print("\n🎯 Step 5: Choose Setup Method")
        print("=" * 30)
        print("1. 🚀 Complete OAuth flow now (Recommended)")
        print("2. 📋 Show OAuth URL for manual testing")
        print("3. ⏭️  Skip for now")
        print()
        
        choice = input("Enter your choice (1/2/3): ").strip()
        
        if choice == "1":
            # Complete automated OAuth flow
            print("\n🚀 Starting automated OAuth flow...")
            print("📌 IMPORTANT: Ensure your Slack app is configured with:")
            print(f"   Redirect URL: {SLACK_REDIRECT_URI}")
            print("   All required scopes (shown above)")
            print()
            
            confirm = input("Are you ready to proceed? (y/N): ").strip().lower()
            if confirm not in ['y', 'yes']:
                print("⏸️  Setup cancelled. Configure your Slack app first.")
                return False
            
            success = await complete_oauth_flow()
            return success
            
        elif choice == "2":
            # Show manual OAuth flow information
            print("\n📋 Manual OAuth Flow")
            print("=" * 20)
            print("🔗 OAuth Authorization URL:")
            print(f"{oauth_url}")
            print()
            print("📝 Manual Steps:")
            print("1. Copy the URL above and open it in your browser")
            print("2. Sign in to your Slack workspace if prompted")
            print("3. Review and approve the requested permissions")
            print("4. You'll be redirected to your callback URL")
            print("5. Copy the 'code' parameter from the redirect URL")
            print("6. Use the code to manually exchange for tokens")
            print()
            print("🌐 Opening URL in browser...")
            webbrowser.open(oauth_url)
            
        else:
            print("⏭️  Setup skipped. You can run this script again later.")
        
        print("\n✅ Setup completed successfully!")
        print("\n🚀 Next Steps:")
        print("1. Ensure your Slack app is properly configured")
        print("2. Run the agent: python slack_agent.py")
        print("3. Send commands like 'authenticate' to start OAuth")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        print("\n🔧 Common Issues:")
        print("• Check your .env file has correct Slack credentials")
        print("• Verify redirect URI matches Slack app configuration")
        print("• Ensure all required scopes are configured in Slack app")
        print("• Make sure your Slack app is not restricted to specific workspaces")
        return False


async def main():
    """Main setup function"""
    # Create .env template if needed
    
    # Run setup
    await setup_slack_auth()

if __name__ == "__main__":
    asyncio.run(main())