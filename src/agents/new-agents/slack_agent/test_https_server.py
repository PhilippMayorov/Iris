#!/usr/bin/env python3
"""
Simple test to verify HTTPS server starts correctly for Slack OAuth
"""

import os
import sys
import ssl
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from dotenv import load_dotenv

# Add the parent directory to import from setup_slack_agent
sys.path.append('.')
from setup_slack_agent import create_self_signed_cert, HTTPSServer, SlackOAuthCallbackHandler

# Load environment
load_dotenv("../../../../.env")
SLACK_REDIRECT_URI = os.getenv("SLACK_REDIRECT_URI", "https://localhost:8080/callback")

def test_https_server():
    """Test HTTPS server startup"""
    print("🌐 Testing HTTPS server for Slack OAuth...")
    
    # Extract server config
    parsed_uri = urlparse(SLACK_REDIRECT_URI)
    callback_port = parsed_uri.port or 8080
    callback_host = parsed_uri.hostname or 'localhost'
    
    print(f"   Host: {callback_host}")
    print(f"   Port: {callback_port}")
    print(f"   URI: {SLACK_REDIRECT_URI}")
    
    try:
        # Create SSL certificate
        print("\n🔐 Creating SSL certificate...")
        cert_file, key_file = create_self_signed_cert()
        
        # Start HTTPS server
        print("\n🚀 Starting HTTPS server...")
        server = HTTPSServer((callback_host, callback_port), SlackOAuthCallbackHandler, cert_file, key_file)
        
        # Start server in background thread
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        print(f"✅ HTTPS server running at https://{callback_host}:{callback_port}")
        print("   Server is ready to receive Slack OAuth callbacks")
        
        # Let server run for a few seconds
        print("\n⏳ Testing server for 5 seconds...")
        time.sleep(5)
        
        # Stop server
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=2)
        
        print("✅ HTTPS server stopped successfully")
        return True
        
    except Exception as e:
        print(f"❌ HTTPS server test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Slack OAuth HTTPS Server")
    print("=" * 40)
    
    success = test_https_server()
    
    if success:
        print("\n🎉 SUCCESS: HTTPS server works correctly!")
        print("   Ready for Slack OAuth with HTTPS requirement")
        print("\n🚀 Next steps:")
        print("   1. Update Slack app redirect URI to: https://localhost:8080/callback")
        print("   2. Run: python setup_slack_agent.py")
        print("   3. Choose option 1 for complete OAuth flow")
    else:
        print("\n❌ FAILED: HTTPS server needs debugging")
        sys.exit(1)