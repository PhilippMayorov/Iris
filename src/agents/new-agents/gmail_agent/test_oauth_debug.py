"""
Debug script to test OAuth authentication and identify scope issues
"""

import json
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configuration
OAUTH_SCOPES = ['https://www.googleapis.com/auth/gmail.send']
TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'credentials.json'

def test_oauth_authentication():
    """Test OAuth authentication and identify issues"""
    print("🔍 OAuth Authentication Debug Test")
    print("=" * 40)
    
    # Check if files exist
    print(f"1. Checking files...")
    print(f"   credentials.json exists: {os.path.exists(CREDENTIALS_FILE)}")
    print(f"   token.json exists: {os.path.exists(TOKEN_FILE)}")
    
    if not os.path.exists(CREDENTIALS_FILE):
        print("❌ credentials.json not found!")
        return False
    
    if not os.path.exists(TOKEN_FILE):
        print("❌ token.json not found! Need to authenticate first.")
        return False
    
    # Load credentials
    print(f"\n2. Loading credentials...")
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, OAUTH_SCOPES)
        print(f"   ✅ Credentials loaded successfully")
        print(f"   Scopes: {creds.scopes}")
        print(f"   Expired: {creds.expired}")
        print(f"   Valid: {creds.valid}")
        
        # Check if token is expired
        if creds.expired and creds.refresh_token:
            print(f"   🔄 Token expired, attempting refresh...")
            try:
                creds.refresh(Request())
                print(f"   ✅ Token refreshed successfully")
                
                # Save refreshed token
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
                print(f"   💾 Refreshed token saved")
                
            except Exception as e:
                print(f"   ❌ Token refresh failed: {e}")
                return False
        
    except Exception as e:
        print(f"   ❌ Failed to load credentials: {e}")
        return False
    
    # Test Gmail API access
    print(f"\n3. Testing Gmail API access...")
    try:
        service = build('gmail', 'v1', credentials=creds)
        print(f"   ✅ Gmail service created successfully")
        
        # Try to get user profile
        print(f"   📧 Attempting to get user profile...")
        profile = service.users().getProfile(userId='me').execute()
        email_address = profile['emailAddress']
        print(f"   ✅ Successfully authenticated as: {email_address}")
        
        # Try to get message list (this requires read scope)
        print(f"   📬 Testing message access...")
        try:
            messages = service.users().messages().list(userId='me', maxResults=1).execute()
            print(f"   ✅ Message access successful")
        except HttpError as e:
            if e.resp.status == 403:
                print(f"   ⚠️  Message access failed (expected - we only have send scope)")
            else:
                print(f"   ❌ Message access failed: {e}")
        
        return True
        
    except HttpError as e:
        print(f"   ❌ Gmail API error: {e}")
        if e.resp.status == 403:
            print(f"   🔍 Error details: {e.error_details}")
            print(f"   📋 This suggests a scope or permission issue")
            print(f"   💡 Check OAuth consent screen configuration")
        return False
        
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def check_credentials_file():
    """Check the credentials.json file structure"""
    print(f"\n4. Checking credentials.json structure...")
    try:
        with open(CREDENTIALS_FILE, 'r') as f:
            creds_data = json.load(f)
        
        print(f"   Client ID: {creds_data.get('web', {}).get('client_id', 'Not found')}")
        print(f"   Project ID: {creds_data.get('web', {}).get('project_id', 'Not found')}")
        print(f"   Redirect URIs: {creds_data.get('web', {}).get('redirect_uris', [])}")
        print(f"   JavaScript Origins: {creds_data.get('web', {}).get('javascript_origins', [])}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error reading credentials.json: {e}")
        return False

def main():
    """Main debug function"""
    success = test_oauth_authentication()
    check_credentials_file()
    
    print(f"\n" + "=" * 40)
    if success:
        print("✅ OAuth authentication is working correctly!")
        print("The issue might be in the web OAuth server implementation.")
    else:
        print("❌ OAuth authentication has issues.")
        print("\nTroubleshooting steps:")
        print("1. Check OAuth consent screen has Gmail scopes")
        print("2. Ensure your email is added as a test user")
        print("3. Try deleting token.json and re-authenticating")
        print("4. Verify credentials.json is for a web application")

if __name__ == "__main__":
    main()
