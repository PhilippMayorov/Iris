"""
Test client for Gmail Agent

This client demonstrates how to interact with the Gmail agent to send emails.
Make sure the Gmail agent is running before using this client.
"""

import asyncio
from uagents import Agent, Context, Model

# Import the same models from the Gmail agent
class EmailSendRequest(Model):
    """Request to send an email"""
    to: str
    subject: str
    body: str
    from_email: str = None


class EmailStatusResponse(Model):
    """Response after attempting to send email"""
    status_code: int
    message_id: str = None
    error_message: str = None
    success: bool = False


# Create a test client agent
test_agent = Agent(
    name="Gmail Test Client",
    port=8001,
    endpoint="http://localhost:8001/submit"
)

# Gmail agent address (you'll need to replace this with the actual address)
GMAIL_AGENT_ADDRESS = "agent1qvw8gy6c7uc6xn5tvhwqmzelugyqal0fvhe73tahcg5q7638qqn2z8h33t9"  # Replace with actual address


@test_agent.on_event("startup")
async def send_test_email(ctx: Context):
    """Send a test email when the client starts"""
    ctx.logger.info("Sending test email request...")
    
    # Create email request
    email_request = EmailSendRequest(
        to="test@example.com",  # Replace with actual recipient
        subject="Test Email from Gmail Agent",
        body="This is a test email sent via the Gmail Agent. If you receive this, the agent is working correctly!"
    )
    
    # Send request to Gmail agent
    await ctx.send(GMAIL_AGENT_ADDRESS, email_request)
    ctx.logger.info("Email request sent to Gmail agent")


@test_agent.on_message(EmailStatusResponse)
async def handle_email_response(ctx: Context, sender: str, msg: EmailStatusResponse):
    """Handle response from Gmail agent"""
    ctx.logger.info(f"Received response from {sender}:")
    
    if msg.success:
        ctx.logger.info(f"✅ Email sent successfully!")
        ctx.logger.info(f"Message ID: {msg.message_id}")
        ctx.logger.info(f"Status Code: {msg.status_code}")
    else:
        ctx.logger.error(f"❌ Failed to send email")
        ctx.logger.error(f"Error: {msg.error_message}")
        ctx.logger.error(f"Status Code: {msg.status_code}")


@test_agent.on_interval(period=30.0)
async def send_periodic_email(ctx: Context):
    """Send a periodic email (optional - for testing)"""
    ctx.logger.info("Sending periodic test email...")
    
    email_request = EmailSendRequest(
        to="test@example.com",  # Replace with actual recipient
        subject="Periodic Test Email",
        body="This is a periodic test email from the Gmail Agent client."
    )
    
    await ctx.send(GMAIL_AGENT_ADDRESS, email_request)


if __name__ == "__main__":
    print("Gmail Test Client")
    print("================")
    print(f"Client Address: {test_agent.address}")
    print(f"Target Gmail Agent: {GMAIL_AGENT_ADDRESS}")
    print("\nMake sure:")
    print("1. Gmail agent is running")
    print("2. Update GMAIL_AGENT_ADDRESS with the correct address")
    print("3. Update recipient email address in the test requests")
    print("\nStarting test client...")
    test_agent.run()
