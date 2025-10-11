"""
Gmail Agent - Sends emails using Gmail API

This agent can send emails when requested. It uses the Gmail API with OAuth2 authentication.
Make sure to set up your Google Cloud credentials and enable the Gmail API.
"""

import base64
import os
from email.message import EmailMessage
from enum import Enum
from typing import Optional

import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from uagents import Agent, Context, Model
from uagents.experimental.quota import QuotaProtocol, RateLimit
from uagents_core.models import ErrorMessage

# Configuration
AGENT_NAME = os.getenv("AGENT_NAME", "Gmail Agent")
AGENT_SEED = os.getenv("AGENT_SEED", "your_seed_phrase_here")
PORT = int(os.getenv("PORT", "8000"))

# Initialize the agent
agent = Agent(
    name=AGENT_NAME,
    seed=AGENT_SEED,
    port=PORT,
    endpoint=f"http://localhost:{PORT}/submit",
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


# Quota protocol for rate limiting
proto = QuotaProtocol(
    storage_reference=agent.storage,
    name="Gmail-Sender-Protocol",
    version="0.1.0",
    default_rate_limit=RateLimit(window_size_minutes=60, max_requests=10),
)


def send_gmail_message(to_email: str, subject: str, body: str, from_email: Optional[str] = None) -> dict:
    """
    Send an email using Gmail API
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body content
        from_email: Sender email (optional, uses authenticated user if not provided)
    
    Returns:
        dict: Response with status and message_id or error information
    """
    try:
        # Load credentials from environment or default location
        creds, _ = google.auth.default()
        
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


# Include protocols in agent
agent.include(proto)
agent.include(health_protocol, publish_manifest=True)


@agent.on_event("startup")
async def startup(ctx: Context):
    """Agent startup event"""
    ctx.logger.info(f"Gmail Agent started: {agent.address}")
    ctx.logger.info("Ready to send emails via Gmail API")


if __name__ == "__main__":
    print(f"Gmail Agent Address: {agent.address}")
    print("Make sure you have:")
    print("1. Set up Google Cloud credentials")
    print("2. Enabled Gmail API")
    print("3. Authenticated with gcloud auth application-default login")
    print("\nStarting agent...")
    agent.run()
