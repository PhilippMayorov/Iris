"""
OAuth 2.0 Setup Script for Gmail Agent

This script handles the OAuth 2.0 authentication flow for the Gmail Agent.
It creates the necessary credentials and tokens for Gmail API access.
"""

import json
import os
import webbrowser
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# File paths
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'


def check_credentials_file():
    """Check if credentials.json exists"""
    if not os.path.exists(CREDENTIALS_FILE):
        print("❌ credentials.json not found!")
        print("\nPlease follow these steps:")
        print("1. Go to Google Cloud Console: https://console.cloud.google.com/")
        print("2. Create a new project or select existing one")
        print("3. Enable Gmail API")
        print("4. Create OAuth 2.0 credentials (Desktop application)")
        print("5. Download the JSON file and save as 'credentials.json'")
        print("\nSee OAUTH_SETUP_GUIDE.md for detailed instructions.")
        return False
    
    print("✅ credentials.json found")
    return True


def authenticate_user():
    """Perform OAuth 2.0 authentication flow"""
    creds = None
    
    # Load existing token if available
    if os.path.exists(TOKEN_FILE):
        print("🔄 Loading existing token...")
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # If there are no valid credentials, request authorization
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("🔐 Starting OAuth 2.0 authentication...")
            print("📱 This will open your browser for Google authentication")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        print("💾 Saving credentials...")
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    return creds


def test_gmail_access(creds):
    """Test Gmail API access with the credentials"""
    try:
        print("🧪 Testing Gmail API access...")
        service = build('gmail', 'v1', credentials=creds)
        
        # Get user profile to test access
        profile = service.users().getProfile(userId='me').execute()
        email_address = profile['emailAddress']
        
        print(f"✅ Successfully authenticated as: {email_address}")
        print("✅ Gmail API access confirmed")
        return True
        
    except Exception as e:
        print(f"❌ Gmail API test failed: {e}")
        return False


def main():
    """Main setup function"""
    print("Gmail Agent OAuth 2.0 Setup")
    print("=" * 30)
    print()
    
    # Check if credentials file exists
    if not check_credentials_file():
        return False
    
    print()
    
    # Perform authentication
    try:
        creds = authenticate_user()
        print("✅ Authentication successful!")
        print()
        
        # Test Gmail access
        if test_gmail_access(creds):
            print()
            print("🎉 Setup completed successfully!")
            print()
            print("Next steps:")
            print("1. Run the Gmail agent: python gmail_agent.py")
            print("2. Test with: python test_oauth_gmail.py")
            print()
            print("Your credentials are saved securely in token.json")
            return True
        else:
            print("❌ Setup failed - Gmail API access test failed")
            return False
            
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure credentials.json is valid")
        print("2. Check your internet connection")
        print("3. Verify Gmail API is enabled in Google Cloud Console")
        return False


if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Setup failed. Please check the error messages above.")
        exit(1)
    else:
        print("\n✅ Setup completed successfully!")
        exit(0)
