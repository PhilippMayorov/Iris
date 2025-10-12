"""
Simple OAuth setup script to properly authenticate with Gmail
"""

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# File paths
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

def authenticate():
    """Perform OAuth 2.0 authentication"""
    print("🔐 Gmail OAuth Authentication Setup")
    print("=" * 40)
    
    # Check if credentials file exists
    if not os.path.exists(CREDENTIALS_FILE):
        print("❌ credentials.json not found!")
        print("Please download it from Google Cloud Console and place it in this directory.")
        return False
    
    print("✅ credentials.json found")
    
    creds = None
    
    # Load existing token if available
    if os.path.exists(TOKEN_FILE):
        print("🔄 Loading existing token...")
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            print("✅ Token loaded successfully")
        except Exception as e:
            print(f"❌ Failed to load token: {e}")
            print("Deleting invalid token...")
            os.remove(TOKEN_FILE)
            creds = None
    
    # If there are no valid credentials, request authorization
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...")
            try:
                creds.refresh(Request())
                print("✅ Token refreshed successfully")
            except Exception as e:
                print(f"❌ Token refresh failed: {e}")
                print("Need to re-authenticate...")
                creds = None
        
        if not creds:
            print("🔐 Starting OAuth 2.0 authentication...")
            print("📱 This will open your browser for Google authentication")
            print("⚠️  Make sure you're logged into the correct Google account!")
            
            try:
                # Use Flow instead of InstalledAppFlow for web application credentials
                from google_auth_oauthlib.flow import Flow
                
                # Create flow with the redirect URI from credentials.json
                flow = Flow.from_client_secrets_file(
                    CREDENTIALS_FILE, 
                    SCOPES,
                    redirect_uri='http://localhost:8080/callback'
                )
                
                # Get authorization URL
                auth_url, _ = flow.authorization_url(
                    access_type='offline',
                    include_granted_scopes='true'
                )
                
                print(f"🔗 Please visit this URL to authorize the application:")
                print(f"   {auth_url}")
                print()
                print("After authorization, you'll be redirected to a page that may show an error.")
                print("Copy the 'code' parameter from the URL and paste it below.")
                print()
                
                # Get authorization code from user
                auth_code = input("Enter the authorization code: ").strip()
                
                # Exchange code for token
                flow.fetch_token(code=auth_code)
                creds = flow.credentials
                print("✅ Authentication successful!")
                
            except Exception as e:
                print(f"❌ Authentication failed: {e}")
                return False
        
        # Save credentials for next run
        print("💾 Saving credentials...")
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        print("✅ Credentials saved successfully")
    
    # Test Gmail API access
    print("\n🧪 Testing Gmail API access...")
    try:
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        email_address = profile['emailAddress']
        print(f"✅ Successfully authenticated as: {email_address}")
        print("✅ Gmail API access confirmed")
        return True
        
    except Exception as e:
        print(f"❌ Gmail API test failed: {e}")
        return False

def main():
    """Main function"""
    success = authenticate()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 OAuth setup completed successfully!")
        print("\nNext steps:")
        print("1. Restart the Gmail agent")
        print("2. Try sending an email via chat")
    else:
        print("❌ OAuth setup failed!")
        print("\nTroubleshooting:")
        print("1. Check OAuth consent screen has Gmail scopes")
        print("2. Ensure your email is added as a test user")
        print("3. Verify credentials.json is correct")
        print("4. Make sure you're logged into the right Google account")

if __name__ == "__main__":
    main()
