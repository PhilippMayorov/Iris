#!/usr/bin/env python3
"""
Simple test to verify Gmail agent is working
"""

import asyncio
from typing import Optional
from uagents import Agent, Context, Model

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

# Create test agent
test_agent = Agent(
    name="Test Client",
    port=8001,
    endpoint="http://localhost:8001/submit"
)

# Gmail agent address (from the output we saw)
GMAIL_AGENT_ADDRESS = "agent1qw6kgumlfqp9drr54qsfngdkz50vgues3u7sewg2fgketekqk8hz500ytg3"

@test_agent.on_event("startup")
async def send_test_email(ctx: Context):
    """Send a test email request"""
    ctx.logger.info("Sending test email request...")
    
    # Create a test email request
    email_request = EmailSendRequest(
        to="test@example.com",  # This will fail but we can see the error
        subject="Test Email from Gmail Agent",
        body="This is a test email to verify the Gmail agent is working!"
    )
    
    try:
        await ctx.send(GMAIL_AGENT_ADDRESS, email_request)
        ctx.logger.info("Email request sent successfully")
    except Exception as e:
        ctx.logger.error(f"Failed to send request: {e}")

@test_agent.on_message(EmailStatusResponse)
async def handle_response(ctx: Context, sender: str, msg: EmailStatusResponse):
    """Handle response from Gmail agent"""
    ctx.logger.info(f"Received response from {sender}:")
    ctx.logger.info(f"Success: {msg.success}")
    ctx.logger.info(f"Status Code: {msg.status_code}")
    if msg.message_id:
        ctx.logger.info(f"Message ID: {msg.message_id}")
    if msg.error_message:
        ctx.logger.info(f"Error: {msg.error_message}")
    
    # Stop the agent after receiving response
    ctx.logger.info("Test completed, stopping agent...")
    import sys
    sys.exit(0)

if __name__ == "__main__":
    print("🧪 Gmail Agent Test Client")
    print(f"Target Agent: {GMAIL_AGENT_ADDRESS}")
    print("Sending test email request...")
    test_agent.run()
