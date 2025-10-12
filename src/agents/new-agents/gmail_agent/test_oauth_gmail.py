"""
Test script for OAuth Gmail functionality

This script tests the OAuth-authenticated Gmail sending functionality.
"""

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# File paths
TOKEN_FILE = 'token.json'


def load_credentials():
    """Load OAuth credentials from token file"""
    if not os.path.exists(TOKEN_FILE):
        print("❌ No OAuth token found!")
        print("Please run: python oauth_setup.py")
        return None
    
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
        # Refresh token if needed
        if creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...")
            creds.refresh(Request())
            
            # Save refreshed token
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        
        return creds
    except Exception as e:
        print(f"❌ Error loading credentials: {e}")
        return None


def send_test_email(creds, to_email, subject, body):
    """Send a test email using OAuth credentials"""
    try:
        service = build('gmail', 'v1', credentials=creds)
        
        # Create email message
        from email.message import EmailMessage
        import base64
        
        message = EmailMessage()
        message.set_content(body)
        message['To'] = to_email
        message['Subject'] = subject
        
        # Get authenticated user's email
        profile = service.users().getProfile(userId='me').execute()
        from_email = profile['emailAddress']
        message['From'] = from_email
        
        # Encode message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # Create message for sending
        create_message = {'raw': encoded_message}
        
        # Send message
        send_message = service.users().messages().send(
            userId='me', body=create_message).execute()
        
        return {
            'success': True,
            'message_id': send_message['id'],
            'from_email': from_email
        }
        
    except HttpError as error:
        return {
            'success': False,
            'error': f'Gmail API error: {error}'
        }
    except Exception as error:
        return {
            'success': False,
            'error': f'Unexpected error: {error}'
        }


def main():
    """Main test function"""
    print("Gmail OAuth Test")
    print("=" * 20)
    print()
    
    # Load credentials
    creds = load_credentials()
    if not creds:
        return False
    
    print("✅ OAuth credentials loaded successfully")
    print()
    
    # Get test email details
    print("Enter test email details:")
    to_email = input("To email address: ").strip()
    subject = input("Subject (or press Enter for default): ").strip() or "Test Email from Gmail Agent"
    body = input("Message body (or press Enter for default): ").strip() or "This is a test email sent from the Gmail Agent using OAuth 2.0 authentication."
    
    print()
    print("📧 Sending test email...")
    print(f"To: {to_email}")
    print(f"Subject: {subject}")
    print(f"Body: {body}")
    print()
    
    # Send test email
    result = send_test_email(creds, to_email, subject, body)
    
    if result['success']:
        print("✅ Test email sent successfully!")
        print(f"Message ID: {result['message_id']}")
        print(f"From: {result['from_email']}")
        print()
        print("Check the recipient's inbox for the test email.")
        return True
    else:
        print("❌ Failed to send test email:")
        print(f"Error: {result['error']}")
        return False


if __name__ == "__main__":
    success = main()
    if success:
        print("🎉 OAuth Gmail test completed successfully!")
    else:
        print("❌ OAuth Gmail test failed!")
        exit(1)
