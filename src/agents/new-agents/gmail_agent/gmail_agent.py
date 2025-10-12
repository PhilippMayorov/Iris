"""
Gmail Agent - Sends emails using Gmail API with Chat Protocol Support

This agent can send emails when requested and supports natural language chat interactions.
It uses the Gmail API with OAuth2 authentication and integrates with the ASI:One chat protocol.
Make sure to set up your Google Cloud credentials and enable the Gmail API.
"""

import base64
import os
import re
import threading
import time
from datetime import datetime
from email.message import EmailMessage
from enum import Enum
from typing import Optional
from uuid import uuid4

import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from uagents import Agent, Context, Model, Protocol
from uagents.experimental.quota import QuotaProtocol, RateLimit
from uagents_core.models import ErrorMessage
from uagents_core.contrib.protocols.chat import (
    AgentContent,
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

# Configuration
AGENT_NAME = os.getenv("AGENT_NAME", "Gmail Agent")
AGENT_SEED = os.getenv("AGENT_SEED", "your_seed_phrase_here")
PORT = int(os.getenv("PORT", "8000"))

# OAuth Configuration - Add more scopes for better compatibility
OAUTH_SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'  # Google automatically adds this scope
]
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

# Web OAuth Server Configuration
OAUTH_SERVER_HOST = 'localhost'
OAUTH_SERVER_PORT = 8080
OAUTH_BASE_URL = f'http://{OAUTH_SERVER_HOST}:{OAUTH_SERVER_PORT}'

# Global OAuth server instance
oauth_server = None
oauth_server_thread = None

# Initialize the agent
agent = Agent(
    name=AGENT_NAME,
    seed=AGENT_SEED,
    port=PORT,
    mailbox=True,
    publish_agent_details=True,
)

# Models for communication
class EmailSendRequest(Model):
    """Request to send an email"""
    to: str
    subject: str
    body: str
    from_email: Optional[str] = None  # If not provided, uses authenticated user's email


class EmailStatusResponse(Model):
    """Response after attempting to send email"""
    status_code: int
    message_id: Optional[str] = None
    error_message: Optional[str] = None
    success: bool = False


class EmailStatus(str, Enum):
    """Email sending status"""
    SUCCESS = "success"
    FAILED = "failed"
    ERROR = "error"


# OAuth Server Functions
def start_oauth_server():
    """Start the web OAuth server for chat authentication"""
    global oauth_server, oauth_server_thread
    
    try:
        from web_oauth_server import start_oauth_server as start_server
        oauth_server, oauth_server_thread = start_server()
        return oauth_server is not None
    except Exception as e:
        print(f"❌ Failed to start OAuth server: {e}")
        return False


def check_oauth_status():
    """Check OAuth authentication status via web server"""
    try:
        import requests
        response = requests.get(f'{OAUTH_BASE_URL}/status', timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {'authenticated': False, 'error': 'Server not responding'}
    except Exception as e:
        return {'authenticated': False, 'error': str(e)}


# OAuth Authentication Functions
def check_oauth_credentials():
    """Check if OAuth credentials are available and valid"""
    # First try web server status check
    try:
        status = check_oauth_status()
        if status.get('authenticated'):
            return True, f"Authenticated as: {status.get('email', 'Unknown')}"
    except:
        pass
    
    # Fallback to direct file check
    # Check if credentials file exists
    if not os.path.exists(CREDENTIALS_FILE):
        return False, "OAuth credentials file not found. Please contact administrator to set up OAuth."
    
    # Check if token file exists
    if not os.path.exists(TOKEN_FILE):
        return False, "OAuth token not found. Please authenticate using the provided link."
    
    try:
        # Load and validate credentials
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, OAUTH_SCOPES)
        
        # Refresh token if needed
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save refreshed token
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        
        # Test Gmail API access
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        
        return True, f"Authenticated as: {profile['emailAddress']}"
        
    except Exception as e:
        return False, f"OAuth authentication failed: {str(e)}"


def get_oauth_credentials():
    """Get valid OAuth credentials"""
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, OAUTH_SCOPES)
        
        # Refresh token if needed
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save refreshed token
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        
        return creds
    except Exception as e:
        raise Exception(f"Failed to load OAuth credentials: {str(e)}")


# Quota protocol for rate limiting
proto = QuotaProtocol(
    storage_reference=agent.storage,
    name="Gmail-Sender-Protocol",
    version="0.1.0",
    default_rate_limit=RateLimit(window_size_minutes=60, max_requests=10),
)


def send_gmail_message(to_email: str, subject: str, body: str, from_email: Optional[str] = None) -> dict:
    """
    Send an email using Gmail API with OAuth authentication
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body content
        from_email: Sender email (optional, uses authenticated user if not provided)
    
    Returns:
        dict: Response with status and message_id or error information
    """
    try:
        # Check OAuth credentials first
        is_valid, message = check_oauth_credentials()
        if not is_valid:
            return {
                "success": False,
                "message_id": None,
                "error": f"Authentication required: {message}"
            }
        
        # Get OAuth credentials
        creds = get_oauth_credentials()
        
        # Build Gmail service
        service = build("gmail", "v1", credentials=creds)
        
        # Create email message
        message = EmailMessage()
        message.set_content(body)
        message["To"] = to_email
        message["Subject"] = subject
        
        # Get authenticated user's email if from_email not provided
        if not from_email:
            profile = service.users().getProfile(userId="me").execute()
            from_email = profile["emailAddress"]
        
        message["From"] = from_email
        
        # Encode message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # Create message for sending
        create_message = {"raw": encoded_message}
        
        # Send message
        send_message = (
            service.users()
            .messages()
            .send(userId="me", body=create_message)
            .execute()
        )
        
        return {
            "success": True,
            "message_id": send_message["id"],
            "error": None
        }
        
    except HttpError as error:
        return {
            "success": False,
            "message_id": None,
            "error": f"Gmail API error: {error}"
        }
    except Exception as error:
        return {
            "success": False,
            "message_id": None,
            "error": f"Unexpected error: {error}"
        }


@proto.on_message(EmailSendRequest, replies={EmailStatusResponse, ErrorMessage})
async def handle_email_request(ctx: Context, sender: str, msg: EmailSendRequest):
    """
    Handle email send requests
    
    Args:
        ctx: Agent context
        sender: Address of the requesting agent
        msg: Email send request
    """
    ctx.logger.info(f"Received email request from {sender}")
    ctx.logger.info(f"To: {msg.to}, Subject: {msg.subject}")
    
    # Validate required fields
    missing_fields = []
    if not msg.to or not msg.to.strip():
        missing_fields.append("recipient email address")
    if not msg.body or not msg.body.strip():
        missing_fields.append("message content")
    
    # Check if we have required fields
    if missing_fields:
        error_message = f"Missing required fields: {', '.join(missing_fields)}"
        response = EmailStatusResponse(
            status_code=400,
            error_message=error_message,
            success=False
        )
        ctx.logger.error(f"Email request failed: {error_message}")
        await ctx.send(sender, response)
        return
    
    # Check if subject is missing and log warning
    if not msg.subject or not msg.subject.strip():
        ctx.logger.warning("No subject provided - using default subject")
        msg.subject = "Message from Gmail Agent"
    
    # Send the email
    result = send_gmail_message(
        to_email=msg.to,
        subject=msg.subject,
        body=msg.body,
        from_email=msg.from_email
    )
    
    # Create response
    if result["success"]:
        response = EmailStatusResponse(
            status_code=200,
            message_id=result["message_id"],
            success=True
        )
        ctx.logger.info(f"Email sent successfully. Message ID: {result['message_id']}")
    else:
        response = EmailStatusResponse(
            status_code=500,
            error_message=result["error"],
            success=False
        )
        ctx.logger.error(f"Failed to send email: {result['error']}")
    
    await ctx.send(sender, response)


# Health check protocol
class HealthCheck(Model):
    """Health check request"""
    pass


class HealthStatus(str, Enum):
    """Health status options"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class AgentHealth(Model):
    """Agent health response"""
    agent_name: str
    status: HealthStatus
    message: str = "Gmail Agent is running"


health_protocol = QuotaProtocol(
    storage_reference=agent.storage, 
    name="HealthProtocol", 
    version="0.1.0"
)


@health_protocol.on_message(HealthCheck, replies={AgentHealth})
async def handle_health_check(ctx: Context, sender: str, msg: HealthCheck):
    """Handle health check requests"""
    await ctx.send(
        sender, 
        AgentHealth(
            agent_name=AGENT_NAME, 
            status=HealthStatus.HEALTHY,
            message="Gmail Agent is running and ready to send emails"
        )
    )


# Chat Protocol for natural language email interactions
chat_protocol = Protocol(spec=chat_protocol_spec)


def extract_email_info(text: str) -> dict:
    """
    Extract email information from natural language text using regex patterns
    
    Args:
        text: Natural language text containing email request
        
    Returns:
        dict: Extracted email information (to, subject, body)
    """
    email_info = {
        "to": None,
        "subject": None,
        "body": None
    }
    
    # Extract email address
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    if emails:
        email_info["to"] = emails[0]
    
    # Look for common patterns
    # Subject patterns
    subject_patterns = [
        r'subject[:\s]+([^\n\r]+)',
        r'title[:\s]+([^\n\r]+)',
        r'about[:\s]+([^\n\r]+)',
    ]
    
    for pattern in subject_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            email_info["subject"] = match.group(1).strip()
            break
    
    # Body patterns - look for content after common keywords
    body_patterns = [
        r'(?:message|content|body|text)[:\s]+([^\n\r]+)',
        r'(?:say|tell|write)[:\s]+([^\n\r]+)',
    ]
    
    for pattern in body_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            email_info["body"] = match.group(1).strip()
            break
    
    # If no specific body found, use the whole text as body (minus email and subject)
    if not email_info["body"]:
        # Remove email address and subject from text for body
        body_text = text
        if email_info["to"]:
            body_text = body_text.replace(email_info["to"], "")
        if email_info["subject"]:
            body_text = body_text.replace(email_info["subject"], "")
        email_info["body"] = body_text.strip()
    
    return email_info


@chat_protocol.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    """
    Handle chat messages for natural language email requests
    
    Args:
        ctx: Agent context
        sender: Address of the requesting agent
        msg: Chat message containing natural language request
    """
    # Send acknowledgement
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id),
    )
    
    # Collect text content from message
    text = ''
    for item in msg.content:
        if isinstance(item, TextContent):
            text += item.text
    
    ctx.logger.info(f"Received chat message: {text}")
    
    # Check OAuth authentication status
    is_authenticated, auth_message = check_oauth_credentials()
    
    # Check if this is an empty or very short message (likely initialization)
    if not text or len(text.strip()) < 3:
        if not is_authenticated:
            response_text = f"""❌ Gmail authentication required!

{auth_message}

🔐 To send emails, you need to authenticate with your Google account.

**Click here to authenticate:**
🔗 {OAUTH_BASE_URL}

This will:
✅ Open your browser
✅ Request permission to send emails  
✅ Save credentials securely
✅ Enable email sending

After authentication, you can send emails normally!

**Alternative:** Use the structured EmailSendRequest format for direct API access."""
        else:
            response_text = f"""Hello! I'm your Gmail Agent assistant. ✅ {auth_message}

I can assist you with:
- Sending emails via Gmail API
- Email management tasks
- Remembering our conversation context

To send an email, just tell me:
- Who to send it to (email address)
- What the subject should be (optional)
- What message to send

Example: "Send an email to john@example.com with subject 'Meeting' saying 'Let's meet tomorrow'"

I'll remember our conversation, so you can ask follow-up questions or send multiple emails in one session. How can I help you with email today?"""
        
        await ctx.send(sender, ChatMessage(
            timestamp=datetime.utcnow(),
            msg_id=uuid4(),
            content=[
                TextContent(type="text", text=response_text),
            ]
        ))
        return
    
    # Check if the message contains email-related intent
    email_intent_keywords = ['send', 'email', 'mail', 'gmail', 'message', '@']
    has_email_intent = any(keyword in text.lower() for keyword in email_intent_keywords)
    
    # If no email intent detected, provide general help
    if not has_email_intent:
        if not is_authenticated:
            response_text = f"""I'm your Gmail Agent assistant, but I need authentication first.

❌ {auth_message}

🔐 To send emails, please authenticate:

**Click here to authenticate:**
🔗 {OAUTH_BASE_URL}

This will open your browser for Google authentication. After authentication, you can send emails!

What would you like to do with email?"""
        else:
            response_text = f"""I'm your Gmail Agent assistant, specialized in sending emails. ✅ {auth_message}

It looks like you might want to send an email. To do that, please provide:
- Recipient email address
- Subject (optional but recommended)
- Message content

Example: "Send an email to john@example.com saying 'Hello, how are you?'"

I'll remember our conversation, so feel free to ask questions or send multiple emails. What would you like to do with email?"""
        
        await ctx.send(sender, ChatMessage(
            timestamp=datetime.utcnow(),
            msg_id=uuid4(),
            content=[
                TextContent(type="text", text=response_text),
            ]
        ))
        return
    
    # Extract email information from user text using regex patterns
    email_info = extract_email_info(text)
    
    # Validate required fields for email sending
    missing_fields = []
    if not email_info["to"]:
        missing_fields.append("recipient email address")
    if not email_info["body"]:
        missing_fields.append("message content")
    
    # Check if we have the minimum required information to send an email
    if email_info["to"] and email_info["body"]:
        # Check if subject is missing and provide recommendation
        subject_warning = ""
        if not email_info["subject"]:
            email_info["subject"] = "Message from Gmail Agent"
            subject_warning = "\n⚠️ Note: No subject was provided, so I used a default subject. It's recommended to include a subject for better email organization."
        
        # Send the email
        result = send_gmail_message(
            to_email=email_info["to"],
            subject=email_info["subject"],
            body=email_info["body"]
        )
        
        if result["success"]:
            response_text = f"✅ Email sent successfully!\n\nTo: {email_info['to']}\nSubject: {email_info['subject']}\nMessage ID: {result['message_id']}{subject_warning}"
        else:
            response_text = f"❌ Failed to send email: {result['error']}"
    else:
        # Provide specific error message about missing fields
        if len(missing_fields) == 1:
            response_text = f"❌ Cannot send email: Missing {missing_fields[0]}.\n\nPlease provide the missing information and try again."
        else:
            response_text = f"❌ Cannot send email: Missing {', '.join(missing_fields)}.\n\nPlease provide all required information and try again."
        
        response_text += "\n\nRequired fields:\n- Recipient email address\n- Message content\n\nOptional fields:\n- Subject (recommended for better organization)"
    
    # Send response back
    await ctx.send(sender, ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[
            TextContent(type="text", text=response_text),
        ]
    ))


@chat_protocol.on_message(ChatAcknowledgement)
async def handle_chat_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    """Handle chat acknowledgements"""
    ctx.logger.info(f"Received chat acknowledgement from {sender}")


# Include protocols in agent
agent.include(proto)
agent.include(health_protocol, publish_manifest=True)
agent.include(chat_protocol, publish_manifest=True)


@agent.on_event("startup")
async def startup(ctx: Context):
    """Agent startup event"""
    ctx.logger.info(f"Gmail Agent started: {agent.address}")
    
    # Start OAuth server for web-based authentication
    if start_oauth_server():
        ctx.logger.info(f"🔐 OAuth server started at {OAUTH_BASE_URL}")
        ctx.logger.info("Users can authenticate via clickable links in chat")
    else:
        ctx.logger.warning("❌ Failed to start OAuth server - authentication links will not work")
    
    # Check OAuth authentication status
    is_authenticated, auth_message = check_oauth_credentials()
    
    if is_authenticated:
        ctx.logger.info(f"✅ OAuth authentication successful: {auth_message}")
        ctx.logger.info("Ready to send emails via Gmail API")
    else:
        ctx.logger.warning(f"❌ OAuth authentication required: {auth_message}")
        ctx.logger.warning("Users will be prompted to authenticate before sending emails")
    
    ctx.logger.info("Chat protocol enabled for natural language email requests")
    ctx.logger.info("Using regex-based email extraction for chat messages")


if __name__ == "__main__":
    print(f"Gmail Agent Address: {agent.address}")
    
    # Check authentication status
    is_authenticated, auth_message = check_oauth_credentials()
    
    if is_authenticated:
        print(f"✅ {auth_message}")
        print("Ready to send emails!")
    else:
        print(f"❌ {auth_message}")
        print(f"\n🔐 OAuth server will be available at: {OAUTH_BASE_URL}")
        print("Users can authenticate via clickable links in chat messages")
        print("\nSee OAUTH_SETUP_GUIDE.md for detailed instructions")
    
    print("\nStarting agent...")
    agent.run()
