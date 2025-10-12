"""
Web-based OAuth Server for Gmail Agent

This server provides a web interface for OAuth authentication
that can be accessed via clickable links in chat messages.
"""

import json
import os
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import secrets
import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# OAuth Configuration - Add more scopes for better compatibility
OAUTH_SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'  # Google automatically adds this scope
]
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

# Server Configuration
SERVER_HOST = 'localhost'
SERVER_PORT = 8080
BASE_URL = f'http://{SERVER_HOST}:{SERVER_PORT}'

# Store pending authentications
pending_auths = {}


class OAuthHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback"""
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        
        if path == '/':
            self.serve_auth_page()
        elif path == '/auth':
            self.handle_auth_request()
        elif path == '/callback':
            self.handle_oauth_callback(query_params)
        elif path == '/status':
            self.handle_status_check(query_params)
        else:
            self.send_error(404)
    
    def serve_auth_page(self):
        """Serve the authentication page"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Gmail Agent Authentication</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
                .container { background: #f5f5f5; padding: 30px; border-radius: 10px; }
                .success { color: #28a745; }
                .error { color: #dc3545; }
                .info { color: #17a2b8; }
                button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
                button:hover { background: #0056b3; }
                .status { margin: 20px 0; padding: 15px; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔐 Gmail Agent Authentication</h1>
                <div id="status" class="status">
                    <p>Click the button below to authenticate with your Google account.</p>
                    <button onclick="startAuth()">Authenticate with Google</button>
                </div>
                <div id="result"></div>
            </div>
            
            <script>
                function startAuth() {
                    const authId = Math.random().toString(36).substr(2, 9);
                    window.location.href = `/auth?id=${authId}`;
                }
                
                // Check for auth result in URL
                const urlParams = new URLSearchParams(window.location.search);
                const result = urlParams.get('result');
                const message = urlParams.get('message');
                
                if (result) {
                    const statusDiv = document.getElementById('status');
                    const resultDiv = document.getElementById('result');
                    
                    if (result === 'success') {
                        statusDiv.innerHTML = '<div class="success">✅ Authentication successful!</div>';
                        resultDiv.innerHTML = `<p>${message}</p><p>You can now close this window and return to your chat.</p>`;
                    } else {
                        statusDiv.innerHTML = '<div class="error">❌ Authentication failed</div>';
                        resultDiv.innerHTML = `<p>${message}</p><p>Please try again.</p>`;
                    }
                }
            </script>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def handle_auth_request(self):
        """Handle authentication request"""
        try:
            query_params = parse_qs(urlparse(self.path).query)
            auth_id = query_params.get('id', [None])[0]
            
            if not auth_id:
                self.send_error(400, "Missing auth ID")
                return
            
            # Check if credentials file exists
            if not os.path.exists(CREDENTIALS_FILE):
                self.redirect_with_error("OAuth credentials not configured. Please contact administrator.")
                return
            
            # Create OAuth flow for web application
            flow = Flow.from_client_secrets_file(
                CREDENTIALS_FILE,
                scopes=OAUTH_SCOPES,
                redirect_uri=f'{BASE_URL}/callback'
            )
            
            # Generate authorization URL
            auth_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true'
            )
            
            # Store pending authentication
            pending_auths[auth_id] = {
                'flow': flow,
                'state': state,
                'timestamp': time.time()
            }
            
            # Redirect to Google OAuth
            self.send_response(302)
            self.send_header('Location', auth_url)
            self.end_headers()
            
        except Exception as e:
            self.redirect_with_error(f"Authentication setup failed: {str(e)}")
    
    def handle_oauth_callback(self, query_params):
        """Handle OAuth callback from Google"""
        try:
            # Get authorization code
            code = query_params.get('code', [None])[0]
            state = query_params.get('state', [None])[0]
            error = query_params.get('error', [None])[0]
            
            if error:
                self.redirect_with_error(f"OAuth error: {error}")
                return
            
            if not code or not state:
                self.redirect_with_error("Missing authorization code or state")
                return
            
            # Find pending authentication
            auth_id = None
            for aid, auth_data in pending_auths.items():
                if auth_data['state'] == state:
                    auth_id = aid
                    break
            
            if not auth_id:
                self.redirect_with_error("Invalid authentication session")
                return
            
            # Complete OAuth flow
            flow = pending_auths[auth_id]['flow']
            flow.fetch_token(code=code)
            
            # Save credentials
            credentials = flow.credentials
            with open(TOKEN_FILE, 'w') as token_file:
                token_file.write(credentials.to_json())
            
            # Test Gmail access
            service = build('gmail', 'v1', credentials=credentials)
            profile = service.users().getProfile(userId='me').execute()
            email_address = profile['emailAddress']
            
            # Clean up pending auth
            del pending_auths[auth_id]
            
            # Redirect with success
            self.redirect_with_success(f"Successfully authenticated as {email_address}")
            
        except Exception as e:
            self.redirect_with_error(f"Authentication failed: {str(e)}")
    
    def handle_status_check(self, query_params):
        """Handle status check requests"""
        try:
            # Check if token exists and is valid
            if os.path.exists(TOKEN_FILE):
                creds = Credentials.from_authorized_user_file(TOKEN_FILE, OAUTH_SCOPES)
                
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    with open(TOKEN_FILE, 'w') as token_file:
                        token_file.write(creds.to_json())
                
                # Test Gmail access
                service = build('gmail', 'v1', credentials=creds)
                profile = service.users().getProfile(userId='me').execute()
                
                response = {
                    'authenticated': True,
                    'email': profile['emailAddress']
                }
            else:
                response = {
                    'authenticated': False,
                    'email': None
                }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            response = {
                'authenticated': False,
                'error': str(e)
            }
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
    
    def redirect_with_success(self, message):
        """Redirect with success message"""
        self.send_response(302)
        self.send_header('Location', f'/?result=success&message={message}')
        self.end_headers()
    
    def redirect_with_error(self, message):
        """Redirect with error message"""
        self.send_response(302)
        self.send_header('Location', f'/?result=error&message={message}')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


def start_oauth_server():
    """Start the OAuth server"""
    try:
        server = HTTPServer((SERVER_HOST, SERVER_PORT), OAuthHandler)
        print(f"🔐 OAuth server started at {BASE_URL}")
        print("Ready to handle authentication requests from chat users")
        
        # Start server in a separate thread
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        return server, server_thread
        
    except Exception as e:
        print(f"❌ Failed to start OAuth server: {e}")
        return None, None


def check_oauth_status():
    """Check OAuth authentication status"""
    try:
        import requests
        response = requests.get(f'{BASE_URL}/status', timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {'authenticated': False, 'error': 'Server not responding'}
    except Exception as e:
        return {'authenticated': False, 'error': str(e)}


if __name__ == "__main__":
    print("Starting Gmail Agent OAuth Server...")
    server, thread = start_oauth_server()
    
    if server:
        try:
            print(f"Server running at {BASE_URL}")
            print("Press Ctrl+C to stop")
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            server.shutdown()
    else:
        print("Failed to start server")
