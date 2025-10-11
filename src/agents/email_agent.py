"""
Email Agent - Gmail Integration

This agent handles all email-related tasks:
1. Composing and sending emails
2. Reading and summarizing inbox
3. Organizing emails (labels, folders)
4. Setting up email filters
5. Managing email templates

Integration Points:
- Receives task requests from vocal_core_agent
- Uses Gmail API for email operations
- Sends status updates back to vocal_core_agent
"""

import asyncio
from typing import Dict, Any, List, Optional
from uagents import Agent, Context, Model
from pydantic import BaseModel
from datetime import datetime
import os

# Initialize the email agent
agent = Agent(
    name="email_agent",
    port=8002,
    seed="email_agent_seed",
    endpoint=["http://127.0.0.1:8002/submit"]
)

# Message Models
class EmailTask(Model):
    """Email task from vocal_core_agent"""
    intent: str
    parameters: Dict[str, Any]
    request_id: str

class EmailResponse(Model):
    """Response back to vocal_core_agent"""
    success: bool
    message: str
    email_data: Optional[Dict[str, Any]]
    request_id: str

class EmailDetails(BaseModel):
    """Email message details"""
    to: List[str]
    subject: str
    body: str
    cc: List[str] = []
    bcc: List[str] = []
    attachments: List[str] = []

@agent.on_startup
async def startup(ctx: Context):
    """Initialize email agent"""
    ctx.logger.info("Email Agent starting up...")
    ctx.logger.info(f"Agent address: {agent.address}")
    
    # TODO: Initialize Gmail API client
    # TODO: Authenticate with Gmail
    # TODO: Set up email service connection

@agent.on_message(model=EmailTask)
async def handle_email_task(ctx: Context, sender: str, msg: EmailTask):
    """Handle email task from vocal_core_agent"""
    ctx.logger.info(f"Received email task: {msg.intent}")
    
    try:
        response = None
        
        if msg.intent == "send_email":
            response = await send_email(ctx, msg.parameters)
        elif msg.intent == "read_emails":
            response = await read_recent_emails(ctx, msg.parameters)
        elif msg.intent == "search_emails":
            response = await search_emails(ctx, msg.parameters)
        elif msg.intent == "organize_emails":
            response = await organize_emails(ctx, msg.parameters)
        elif msg.intent == "create_template":
            response = await create_email_template(ctx, msg.parameters)
        else:
            response = EmailResponse(
                success=False,
                message=f"Unknown email intent: {msg.intent}",
                email_data=None,
                request_id=msg.request_id
            )
        
        # Send response back to vocal_core_agent
        await ctx.send(sender, response)
        
    except Exception as e:
        ctx.logger.error(f"Error handling email task: {e}")
        error_response = EmailResponse(
            success=False,
            message=f"Error processing email task: {str(e)}",
            email_data=None,
            request_id=msg.request_id
        )
        await ctx.send(sender, error_response)

async def send_email(ctx: Context, parameters: Dict[str, Any]) -> EmailResponse:
    """
    Send an email
    TODO: Implement actual Gmail API call
    """
    ctx.logger.info("Sending email...")
    
    # Extract parameters
    to = parameters.get("to", [])
    subject = parameters.get("subject", "")
    body = parameters.get("body", "")
    cc = parameters.get("cc", [])
    
    # TODO: Use Gmail API to send email
    # TODO: Handle attachments if any
    # TODO: Return message ID
    
    # Placeholder response
    email_data = {
        "message_id": "mock_message_123",
        "to": to,
        "subject": subject,
        "sent_at": datetime.now().isoformat()
    }
    
    return EmailResponse(
        success=True,
        message=f"Email sent successfully to {', '.join(to)}",
        email_data=email_data,
        request_id=parameters.get("request_id", "")
    )

async def read_recent_emails(ctx: Context, parameters: Dict[str, Any]) -> EmailResponse:
    """
    Read recent emails from inbox
    TODO: Implement actual Gmail API call
    """
    ctx.logger.info("Reading recent emails...")
    
    limit = parameters.get("limit", 10)
    
    # TODO: Use Gmail API to fetch recent emails
    # TODO: Parse and summarize email content
    
    # Placeholder response
    recent_emails = [
        {
            "from": "john@example.com",
            "subject": "Project Update",
            "snippet": "The project is progressing well...",
            "date": "2024-10-10"
        },
        {
            "from": "sarah@company.com",
            "subject": "Meeting Reminder",
            "snippet": "Don't forget about tomorrow's meeting...",
            "date": "2024-10-10"
        }
    ]
    
    return EmailResponse(
        success=True,
        message=f"Found {len(recent_emails)} recent emails",
        email_data={"emails": recent_emails},
        request_id=parameters.get("request_id", "")
    )

async def search_emails(ctx: Context, parameters: Dict[str, Any]) -> EmailResponse:
    """
    Search emails by query
    TODO: Implement actual Gmail API call
    """
    ctx.logger.info("Searching emails...")
    
    query = parameters.get("query", "")
    
    # TODO: Use Gmail API search functionality
    
    return EmailResponse(
        success=True,
        message=f"Found 5 emails matching '{query}'",
        email_data={"search_results": []},
        request_id=parameters.get("request_id", "")
    )

async def organize_emails(ctx: Context, parameters: Dict[str, Any]) -> EmailResponse:
    """
    Organize emails with labels/folders
    TODO: Implement actual Gmail API call
    """
    ctx.logger.info("Organizing emails...")
    
    # TODO: Apply labels, move to folders, etc.
    
    return EmailResponse(
        success=True,
        message="Emails organized successfully",
        email_data=None,
        request_id=parameters.get("request_id", "")
    )

async def create_email_template(ctx: Context, parameters: Dict[str, Any]) -> EmailResponse:
    """
    Create email template for reuse
    TODO: Implement template storage
    """
    ctx.logger.info("Creating email template...")
    
    template_name = parameters.get("name", "")
    template_content = parameters.get("content", "")
    
    # TODO: Store template for future use
    
    return EmailResponse(
        success=True,
        message=f"Email template '{template_name}' created successfully",
        email_data={"template_id": "mock_template_123"},
        request_id=parameters.get("request_id", "")
    )

if __name__ == "__main__":
    print("Starting Email Agent...")
    print(f"Agent will run on: {agent.address}")
    print("This agent handles:")
    print("  - Composing and sending emails")
    print("  - Reading and summarizing inbox")
    print("  - Organizing emails with labels")
    print("  - Creating email templates")
    
    agent.run()