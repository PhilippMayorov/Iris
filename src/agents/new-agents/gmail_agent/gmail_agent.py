"""
Gmail Agent - Sends emails using Gmail API with Chat Protocol Support

This agent can send emails when requested and supports natural language chat interactions.
It uses the Gmail API with OAuth2 authentication and integrates with the ASI:One chat protocol.
Make sure to set up your Google Cloud credentials and enable the Gmail API.
"""

import base64
import os
import re
import signal
import sys
import threading
import time
from datetime import datetime
from email.message import EmailMessage
from enum import Enum
from typing import Optional, List, Dict
from uuid import uuid4

import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from openai import OpenAI
from uagents import Agent, Context, Model, Protocol
from uagents.experimental.quota import QuotaProtocol, RateLimit
from uagents_core.models import ErrorMessage
from uagents_core.contrib.protocols.chat import (
    AgentContent,
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

# Configuration
AGENT_NAME = os.getenv("AGENT_NAME", "Gmail Agent")
AGENT_SEED = os.getenv("AGENT_SEED", "your_seed_phrase_here")
PORT = int(os.getenv("PORT", "8000"))

# ASI:One Configuration
ASI_ONE_API_KEY = os.getenv("ASI_ONE_API_KEY")
ASI_ONE_BASE_URL = "https://api.asi1.ai/v1"


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

# No memory cleanup needed - mailbox agent manages all conversation context

# Signal handler for graceful shutdown
def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\n🛑 Received signal {signum} - shutting down gracefully...")
    print("👋 Gmail Agent shutdown complete")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

# Initialize the agent
agent = Agent(
    name=AGENT_NAME,
    seed=AGENT_SEED,
    port=PORT,
    mailbox=True,
    publish_agent_details=True,
)

# Initialize ASI:One client
asi_one_client = None
if ASI_ONE_API_KEY:
    try:
        asi_one_client = OpenAI(
            base_url=ASI_ONE_BASE_URL,
            api_key=ASI_ONE_API_KEY,
        )
        print("✅ ASI:One client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize ASI:One client: {e}")
        asi_one_client = None
else:
    print("⚠️ ASI_ONE_API_KEY not found - ASI:One features will be disabled")

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

# Agent-to-Agent Communication Models (for mailbox agent communication)
class AgentEmailRequest(Model):
    """Request from mailbox agent to gmail agent for email sending"""
    to: str
    subject: str
    body: str
    from_email: Optional[str] = None
    original_message: str  # The original user message for context
    conversation_history: Optional[List[Dict[str, str]]] = None  # Full conversation context

class AgentEmailResponse(Model):
    """Response from gmail agent to mailbox agent"""
    success: bool
    message_id: Optional[str] = None
    error_message: Optional[str] = None
    status_code: int = 200
    needs_clarification: bool = False
    suggestions: Optional[List[str]] = None
    reasoning: Optional[str] = None


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
    
    # Check if subject is missing and log info
    if not msg.subject or not msg.subject.strip():
        ctx.logger.info("No subject provided - sending email without subject")
        msg.subject = ""
    
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

@proto.on_message(AgentEmailRequest, replies={AgentEmailResponse, ErrorMessage})
async def handle_agent_email_request(ctx: Context, sender: str, msg: AgentEmailRequest):
    """
    Handle email requests from mailbox agent with intelligent processing
    
    Args:
        ctx: Agent context
        sender: Address of the requesting agent (mailbox agent)
        msg: Agent email request with original user message
    """
    ctx.logger.info(f"📧 Received agent email request from {sender}")
    ctx.logger.info(f"📧 Original message: {msg.original_message}")
    ctx.logger.info(f"📧 To: {msg.to}, Subject: {msg.subject}")
    
    # Check OAuth authentication first
    is_authenticated, auth_message = check_oauth_credentials()
    if not is_authenticated:
        response = AgentEmailResponse(
            success=False,
            error_message=f"Gmail authentication required: {auth_message}",
            status_code=401,
            needs_clarification=False
        )
        ctx.logger.error(f"📧 Authentication failed: {auth_message}")
        await ctx.send(sender, response)
        return
    
    # Use ASI:One to process the original message and extract email information
    if asi_one_client:
        # Use conversation history from the mailbox agent (no local storage)
        conversation_history = msg.conversation_history or []
        ctx.logger.info(f"📧 Using conversation history from mailbox agent: {len(conversation_history)} messages")
        
        # Process with ASI:One using the conversation context from mailbox agent
        email_info = process_email_request_with_asi_one(msg.original_message, conversation_history)
        ctx.logger.info(f"📧 ASI:One processing result: {email_info}")
        
        # Debug: Log the actual ASI:One response fields
        if email_info.get("error") and "ASI:One processing failed" in email_info.get("error", ""):
            ctx.logger.error(f"📧 ASI:One processing failed: {email_info.get('error')}")
        else:
            ctx.logger.info(f"📧 ASI:One is_valid_format: {email_info.get('is_valid_format')}")
            ctx.logger.info(f"📧 ASI:One needs_clarification: {email_info.get('needs_clarification')}")
        
        # Check if ASI:One needs clarification
        if not email_info["is_valid_format"] or email_info.get("needs_clarification", False):
            # Get the error message, handling None values properly
            error_msg = email_info.get("error")
            if not error_msg or error_msg == "None":
                error_msg = "Need more information to send the email"
            
            # Return clarification request
            response = AgentEmailResponse(
                success=False,
                error_message=error_msg,
                status_code=400,
                needs_clarification=True,
                suggestions=email_info.get("suggestions", []),
                reasoning=email_info.get("reasoning", "")
            )
            ctx.logger.info(f"📧 Returning clarification request: {error_msg}")
            await ctx.send(sender, response)
            return
        
        # Use ASI:One extracted information
        final_to = email_info.get("to", msg.to)
        final_subject = email_info.get("subject", msg.subject)
        final_body = email_info.get("body", msg.body)
        
    else:
        # Fallback to provided information
        final_to = msg.to
        final_subject = msg.subject
        final_body = msg.body
    
    # Validate final email information
    if not final_to or not final_to.strip():
        response = AgentEmailResponse(
            success=False,
            error_message="Missing recipient email address",
            status_code=400,
            needs_clarification=True,
            suggestions=["Please provide the recipient's email address"],
            reasoning="No email address found in the request"
        )
        ctx.logger.error("📧 Missing recipient email address")
        await ctx.send(sender, response)
        return
    
    if not final_body or not final_body.strip():
        response = AgentEmailResponse(
            success=False,
            error_message="Missing message content - what would you like to say?",
            status_code=400,
            needs_clarification=True,
            suggestions=[
                "What would you like to say in the email?",
                "Please provide the message content"
            ],
            reasoning="No message content found in the request"
        )
        ctx.logger.error("📧 Missing message content")
        await ctx.send(sender, response)
        return
    
    # Send the email
    result = send_gmail_message(
        to_email=final_to,
        subject=final_subject or "",
        body=final_body,
        from_email=msg.from_email
    )
    
    # Create response
    if result["success"]:
        response = AgentEmailResponse(
            success=True,
            message_id=result["message_id"],
            status_code=200,
            needs_clarification=False,
            reasoning=email_info.get("reasoning", "") if asi_one_client else ""
        )
        ctx.logger.info(f"📧 Email sent successfully. Message ID: {result['message_id']}")
    else:
        response = AgentEmailResponse(
            success=False,
            error_message=result["error"],
            status_code=500,
            needs_clarification=False
        )
        ctx.logger.error(f"📧 Failed to send email: {result['error']}")
    
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




def process_email_request_with_asi_one(text: str, conversation_history: list = None) -> dict:
    """
    Process natural language email requests using ASI:One LLM with intelligent reasoning
    
    Args:
        text: Natural language text containing email request
        conversation_history: List of previous conversation messages for context
        
    Returns:
        dict: Extracted email information (to, subject, body) or error info
    """
    if not asi_one_client:
        return {
            "to": None,
            "subject": None,
            "body": None,
            "error": "ASI:One client not available. Please set ASI_ONE_API_KEY environment variable.",
            "is_valid_format": False
        }
    
    try:
        # Enhanced system prompt with intelligent reasoning and conversation context
        system_prompt = """You are an intelligent Gmail assistant with advanced reasoning capabilities. Your task is to understand user intent and extract email information from ANY natural language input.

CONVERSATION CONTEXT:
- You have access to the full conversation history with this user
- Use previous messages to understand context, references, and ongoing conversations
- Remember information shared earlier (names, email addresses, preferences, etc.)
- Build upon previous interactions to provide better assistance
- If the user refers to "him", "her", "it", "that", etc., use conversation history to understand what they mean

CAPABILITIES:
- Understand conversational, casual, formal, or incomplete language
- Infer missing information from context
- Handle ambiguous requests intelligently
- Use common sense and chat history to fill in details already discussed in previous turns
- Suggest reasonable defaults when information is missing
- Understand various ways people express email requests

INTELLIGENT EXTRACTION RULES:
1. RECIPIENT (to):
   - Look for email addresses anywhere in the text
   - If no email is found but a name/role is mentioned, ask for their email
   - Accept partial emails and suggest completion
   - Handle phrasing like “send to John” by asking for John’s email
   - If a recipient was clearly mentioned in a previous turn, reuse it

2. SUBJECT (subject):
   - Extract explicit subjects (e.g., “subject: Meeting”)
   - Infer subjects from context (“meeting tomorrow” → “Meeting Tomorrow”)
   - Generate a clear and relevant subject when missing
   - Maintain consistency with previous context if the topic is ongoing
   - Use a conversational tone when appropriate

3. CONTENT (body):
   - Extract or compose the main message content
   - Expand brief or incomplete inputs into full, natural-sounding emails
   - Always ensure the message is complete — no placeholders or “fill-in-the-blank” text
   - If essential information is missing (e.g., the sender’s name or key details), ask for it directly before finalizing
   - Add polite greetings and closings, maintaining the user’s intended tone and style

4. REASONING:
   - Use chat history and context to maintain continuity
   - Apply common sense when interpreting ambiguous inputs
   - If a request is unclear, ask clarifying questions
   - If information is missing, suggest what’s needed
   - If a request seems incomplete, offer to help complete it
   - Always be helpful, conversational, and context-aware

EXAMPLES OF FLEXIBLE INPUTS YOU CAN HANDLE:
- “email John about the meeting” → Ask for John’s email, suggest a subject
- “send something to team@company.com” → Ask what to send
- “write to Sarah” → Ask for Sarah’s email and what to write
- “meeting tomorrow 2pm” → Ask who to send to, suggest subject/body
- “tell the client we’re done” → Ask for client email, suggest professional message
- "quick note to boss" → Ask for boss email, suggest brief professional note
- If the user says "same person as before" or "same topic," reuse prior fields intelligently

CONVERSATION CONTEXT EXAMPLES:
- If user previously said "john@company.com" and now says "email him about the meeting" → Use john@company.com
- If user mentioned "the project" earlier and now says "update the team" → Reference the project context
- If user said "sarah is my manager" and now says "tell her we're done" → Use sarah's context
- Build upon previous email requests and clarifications

RESPONSE FORMAT:
Always respond in this JSON format:
{
    "to": "email@example.com or null if missing",
    "subject": "extracted or suggested subject",
    "body": "extracted or suggested complete message content",
    "is_valid": true/false,
    "error": null or "helpful error message",
    "reasoning": "brief explanation of what you understood and any suggestions",
    "needs_clarification": true/false,
    "suggestions": ["list of suggestions if clarification needed"]
}

BEHAVIOR SUMMARY:
- Use common sense and past context from chat history
- Never return incomplete messages
- Always produce ready-to-send, natural emails
- If any critical info is missing (like the recipient’s email or the sender’s name), ask clearly instead of leaving blanks
- Keep tone adaptive, polite, and consistent with the user’s intent"""

        # Build messages array with conversation history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current user message
        messages.append({"role": "user", "content": text})
        
        # Query ASI:One with conversation context
        response = asi_one_client.chat.completions.create(
            model="asi1-mini",
            messages=messages,
            max_tokens=1500,  # Increased for more detailed reasoning
            temperature=0.3   # Higher temperature for more creative responses
        )
        
        # Parse the response
        response_text = response.choices[0].message.content.strip()
        
        # Try to extract JSON from response
        import json
        try:
            # Look for JSON in the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)
                
                # Enhanced response handling with reasoning
                if result.get("is_valid", False):
                    return {
                        "to": result.get("to"),
                        "subject": result.get("subject", ""),
                        "body": result.get("body"),
                        "error": None,
                        "is_valid_format": True,
                        "reasoning": result.get("reasoning", ""),
                        "needs_clarification": result.get("needs_clarification", False),
                        "suggestions": result.get("suggestions", [])
                    }
                else:
                    # Handle cases where ASI:One needs clarification
                    if result.get("needs_clarification", False):
                        suggestions = result.get("suggestions", [])
                        suggestion_text = "\n".join([f"- {s}" for s in suggestions]) if suggestions else ""
                        error_msg = f"{result.get('error', 'Need more information')}\n\nSuggestions:\n{suggestion_text}"
                    else:
                        error_msg = result.get("error", "Invalid email request")
                    
                    return {
                        "to": result.get("to"),
                        "subject": result.get("subject", ""),
                        "body": result.get("body"),
                        "error": error_msg,
                        "is_valid_format": False,
                        "reasoning": result.get("reasoning", ""),
                        "needs_clarification": result.get("needs_clarification", False),
                        "suggestions": result.get("suggestions", [])
                    }
            else:
                raise ValueError("No JSON found in response")
                
        except (json.JSONDecodeError, ValueError) as e:
            # Enhanced fallback with intelligent parsing
            return intelligent_fallback_parsing(text, response_text, str(e))
            
    except Exception as e:
        return {
            "to": None,
            "subject": None,
            "body": None,
            "error": f"ASI:One processing failed: {str(e)}",
            "is_valid_format": False
        }


def intelligent_fallback_parsing(original_text: str, response_text: str, error: str) -> dict:
    """
    Intelligent fallback parsing when ASI:One response parsing fails
    
    Args:
        original_text: Original user input
        response_text: ASI:One response text
        error: Parsing error message
        
    Returns:
        dict: Parsed email information with helpful suggestions
    """
    import re
    
    # Try to extract email address from original text
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_match = re.search(email_pattern, original_text)
    
    # Try to extract names or roles
    name_patterns = [
        r'\b(?:send|email|write)\s+to\s+(\w+)',
        r'\b(?:john|jane|sarah|mike|team|boss|client|manager)\b',
        r'\b(?:the\s+)?(\w+)\s+(?:about|regarding)',
    ]
    
    potential_recipient = None
    for pattern in name_patterns:
        match = re.search(pattern, original_text.lower())
        if match:
            potential_recipient = match.group(1) if match.groups() else match.group(0)
            break
    
    # Try to extract subject hints
    subject_hints = []
    subject_patterns = [
        r'\b(?:about|regarding|re:?)\s+(.+)',
        r'\b(?:subject|title):\s*(.+)',
        r'\b(?:meeting|project|update|proposal|invoice)\b',
    ]
    
    for pattern in subject_patterns:
        match = re.search(pattern, original_text.lower())
        if match:
            subject_hints.append(match.group(1) if match.groups() else match.group(0))
    
    # Generate helpful suggestions
    suggestions = []
    
    if not email_match and not potential_recipient:
        suggestions.append("Please specify who to send the email to (e.g., 'john@example.com' or 'send to john')")
    elif not email_match and potential_recipient:
        suggestions.append(f"I found '{potential_recipient}' but need their email address")
    
    if not subject_hints:
        suggestions.append("Consider adding a subject (e.g., 'about the meeting' or 'subject: Project Update')")
    
    if len(original_text.strip()) < 20:
        suggestions.append("Please provide more details about what you want to send")
    
    # Create helpful error message
    if suggestions:
        error_msg = f"I understand you want to send an email, but I need more information:\n\n" + "\n".join([f"- {s}" for s in suggestions])
    else:
        error_msg = f"Could not parse your request. Please try rephrasing or use the structured format."
    
    return {
        "to": email_match.group(0) if email_match else None,
        "subject": subject_hints[0] if subject_hints else "",
        "body": "",
        "error": error_msg,
        "is_valid_format": False,
        "reasoning": f"Fallback parsing used due to: {error}",
        "needs_clarification": True,
        "suggestions": suggestions
    }


# Structured format extraction removed - now using AI-only parsing


@chat_protocol.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    """
    Handle chat messages for natural language email requests with conversation context
    
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
    
    # No local conversation history storage - mailbox agent manages all context
    conversation_history = []
    
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
            asi_one_status = "✅ ASI:One AI enabled" if asi_one_client else "⚠️ ASI:One AI disabled (set ASI_ONE_API_KEY to enable)"
            response_text = f"""👋 Hello! I'm your intelligent Gmail assistant. ✅ {auth_message}

{asi_one_status}

🎯 **I can help you send emails in ANY way you want to express it!**

**Just talk to me naturally:**
- "Send an email to john@example.com about the meeting tomorrow"
- "Email the team about the project update" 
- "Write to client@company.com saying we'll deliver on time"
- "Quick note to boss about the budget"
- "Tell sarah we're running late"
- "Meeting tomorrow 2pm" (I'll ask who to send to!)

**I understand:**
- Casual, formal, or incomplete language
- Names, roles, or email addresses
- Context and intent
- Missing information (I'll ask for what I need)

**💡 Don't worry about being perfect** - just tell me what you want to send and I'll figure it out! I'm here to make email sending as easy as possible.

What would you like to send today?"""
        
        # No conversation history storage - mailbox agent manages all context
        
        await ctx.send(sender, ChatMessage(
            timestamp=datetime.utcnow(),
            msg_id=uuid4(),
            content=[
                TextContent(type="text", text=response_text),
            ]
        ))
        return
    
    # Use ASI:One for intelligent natural language processing with conversation context
    if asi_one_client:
        email_info = process_email_request_with_asi_one(text, conversation_history)
        ctx.logger.info(f"ASI:One processing result: {email_info}")
    else:
        # If ASI:One is not available, provide helpful guidance
        email_info = {
            "to": None,
            "subject": None,
            "body": None,
            "error": "ASI:One AI is required for natural language email processing. Please set ASI_ONE_API_KEY environment variable to enable intelligent email parsing.",
            "is_valid_format": False,
            "needs_clarification": True,
            "suggestions": [
                "Get your ASI:One API key from https://asi1.ai/dashboard/api-keys",
                "Set the environment variable: export ASI_ONE_API_KEY='your_api_key_here'",
                "Restart the agent to enable natural language processing"
            ]
        }
    
    # Check if the format is valid
    if not email_info["is_valid_format"]:
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

After authentication, you can send emails using natural language.

{email_info["error"]}"""
        else:
            asi_one_status = "✅ ASI:One AI enabled" if asi_one_client else "⚠️ ASI:One AI disabled (set ASI_ONE_API_KEY to enable)"
            
            # Enhanced error handling with reasoning and suggestions
            if email_info.get("needs_clarification", False):
                response_text = f"""🤔 I need a bit more information to help you send that email.

✅ {auth_message}
{asi_one_status}

**What I understood:** {email_info.get("reasoning", "Your request")}

**What I need:**
{email_info["error"]}

**💡 Try these examples:**
- "Send an email to john@example.com about the meeting tomorrow"
- "Email the team about the project update" 
- "Write to sarah@company.com saying we'll deliver on time"
- "Quick note to boss about the budget approval"
- "email john about the meeting" (I'll ask for john's email)
- "tell the boss we're done" (I'll ask for boss's email)"""
            else:
                response_text = f"""❌ {email_info["error"]}

✅ {auth_message}
{asi_one_status}

**Natural Language Examples:**
- "Send an email to john@example.com about the meeting tomorrow"
- "Email the team about the project update"
- "Write to client@company.com saying we'll deliver on time"
- "email john about the meeting" (I'll ask for john's email)
- "tell the boss we're done" (I'll ask for boss's email)
- "quick note to client" (I'll ask for client's email and what to write)

**💡 Tip:** Be as specific or casual as you want - I can understand both! Just talk to me naturally!"""
        
        # No conversation history storage - mailbox agent manages all context
        
        await ctx.send(sender, ChatMessage(
            timestamp=datetime.utcnow(),
            msg_id=uuid4(),
            content=[
                TextContent(type="text", text=response_text),
            ]
        ))
        return
    
    # If we get here, the format is valid and we have the required information
    # Check if subject is missing and provide info
    subject_warning = ""
    if not email_info["subject"]:
        email_info["subject"] = ""
        subject_warning = "\nℹ️ Note: No subject was provided, so the email will be sent without a subject."
    
    # Send the email
    result = send_gmail_message(
        to_email=email_info["to"],
        subject=email_info["subject"],
        body=email_info["body"]
    )
    
    if result["success"]:
        # Enhanced success message with reasoning
        reasoning_text = ""
        if email_info.get("reasoning"):
            reasoning_text = f"\n\n🧠 **AI Understanding:** {email_info['reasoning']}"
        
        response_text = f"✅ Email sent successfully!\n\nTo: {email_info['to']}\nSubject: {email_info['subject'] if email_info['subject'] else '(no subject)'}\nMessage ID: {result['message_id']}{subject_warning}{reasoning_text}"
    else:
        response_text = f"❌ Failed to send email: {result['error']}"
    
    # No conversation history storage - mailbox agent manages all context
    
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
    
    # No memory management needed - mailbox agent handles all conversation context
    
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
    ctx.logger.info("📧 Gmail agent operates in stateless mode - mailbox agent manages all conversation context")
    if asi_one_client:
        ctx.logger.info("✅ ASI:One AI integration enabled - all email parsing handled by AI")
        ctx.logger.info("🎯 No strict formatting requirements - AI handles all parsing intelligently")
    else:
        ctx.logger.warning("❌ ASI:One AI integration disabled - natural language processing unavailable")
        ctx.logger.warning("⚠️ Set ASI_ONE_API_KEY environment variable to enable email functionality")


@agent.on_event("shutdown")
async def shutdown(ctx: Context):
    """Agent shutdown event"""
    ctx.logger.info("Gmail Agent shutting down...")
    ctx.logger.info("👋 Gmail Agent shutdown complete")


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
    
    # Show ASI:One status
    if asi_one_client:
        print("\n✅ ASI:One AI integration enabled")
        print("Enhanced natural language email processing available")
    else:
        print("\n⚠️ ASI:One AI integration disabled")
        print("Set ASI_ONE_API_KEY environment variable to enable")
        print("Get your API key at: https://asi1.ai/dashboard/api-keys")
    
    print("\nStarting agent...")
    agent.run()

