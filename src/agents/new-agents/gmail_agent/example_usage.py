#!/usr/bin/env python3
"""
Example: How to use the Gmail Agent in your application

This shows a practical example of integrating the Gmail agent
into a real application for sending notifications.
"""

import asyncio
from typing import Optional
from uagents import Agent, Context, Model

# Import the same models as the Gmail agent
class EmailSendRequest(Model):
    """Request to send an email"""
    to: str
    subject: str
    body: str
    from_email: Optional[str] = None

class EmailStatusResponse(Model):
    """Response after attempting to send email"""
    status_code: int
    message_id: Optional[str] = None
    error_message: Optional[str] = None
    success: bool = False

# Your application agent
app_agent = Agent(
    name="My Application",
    port=8002,
    endpoint="http://localhost:8002/submit"
)

# Gmail agent address (replace with your actual address)
GMAIL_AGENT_ADDRESS = "agent1qw6kgumlfqp9drr54qsfngdkz50vgues3u7sewg2fgketekqk8hz500ytg3"

# Example: User registration notification
@app_agent.on_event("startup")
async def send_welcome_email(ctx: Context):
    """Send welcome email when app starts (demo)"""
    ctx.logger.info("Sending welcome email...")
    
    await ctx.send(GMAIL_AGENT_ADDRESS, EmailSendRequest(
        to="newuser@example.com",
        subject="Welcome to MyApp!",
        body="Thank you for joining MyApp! We're excited to have you on board."
    ))

# Example: System monitoring
@app_agent.on_interval(period=300)  # Every 5 minutes
async def health_check_notification(ctx: Context):
    """Send periodic health check email"""
    ctx.logger.info("Sending health check notification...")
    
    await ctx.send(GMAIL_AGENT_ADDRESS, EmailSendRequest(
        to="admin@myapp.com",
        subject="System Health Check",
        body="All systems are running normally. Last check: 5 minutes ago."
    ))

# Example: Error notification
async def send_error_notification(ctx: Context, error_message: str):
    """Send error notification to admin"""
    ctx.logger.error(f"Sending error notification: {error_message}")
    
    await ctx.send(GMAIL_AGENT_ADDRESS, EmailSendRequest(
        to="admin@myapp.com",
        subject="🚨 System Error Alert",
        body=f"An error occurred in the system:\n\n{error_message}\n\nPlease investigate immediately."
    ))

# Example: User action notification
async def send_user_action_email(ctx: Context, user_email: str, action: str):
    """Send notification about user action"""
    await ctx.send(GMAIL_AGENT_ADDRESS, EmailSendRequest(
        to=user_email,
        subject="Action Confirmation",
        body=f"Your action '{action}' has been completed successfully."
    ))

# Handle email responses
@app_agent.on_message(EmailStatusResponse)
async def handle_email_response(ctx: Context, sender: str, msg: EmailStatusResponse):
    """Handle responses from Gmail agent"""
    if msg.success:
        ctx.logger.info(f"✅ Email sent successfully! Message ID: {msg.message_id}")
        
        # You can add logic here based on the email type
        # For example, update database, send to another service, etc.
        
    else:
        ctx.logger.error(f"❌ Failed to send email: {msg.error_message}")
        
        # Handle email failures
        # You might want to retry, log to database, or send to backup service
        if "quota" in msg.error_message.lower():
            ctx.logger.warning("Rate limit reached, will retry later")
        elif "auth" in msg.error_message.lower():
            ctx.logger.error("Authentication failed, check Google Cloud setup")

# Example: Simulate some application events
@app_agent.on_interval(period=10)
async def simulate_events(ctx: Context):
    """Simulate various application events that might trigger emails"""
    import random
    
    events = [
        ("user_registration", "newuser@example.com", "User Registration"),
        ("password_reset", "user@example.com", "Password Reset Request"),
        ("order_confirmation", "customer@example.com", "Order Confirmation"),
        ("system_alert", "admin@myapp.com", "System Alert")
    ]
    
    event_type, email, subject = random.choice(events)
    
    if event_type == "user_registration":
        await ctx.send(GMAIL_AGENT_ADDRESS, EmailSendRequest(
            to=email,
            subject=f"Welcome! {subject}",
            body="Thank you for joining our platform. Get started by exploring our features!"
        ))
    elif event_type == "password_reset":
        await ctx.send(GMAIL_AGENT_ADDRESS, EmailSendRequest(
            to=email,
            subject=f"Password Reset - {subject}",
            body="You requested a password reset. Click the link to reset your password."
        ))
    elif event_type == "order_confirmation":
        await ctx.send(GMAIL_AGENT_ADDRESS, EmailSendRequest(
            to=email,
            subject=f"Order Confirmed - {subject}",
            body="Your order has been confirmed and will be processed shortly."
        ))
    elif event_type == "system_alert":
        await ctx.send(GMAIL_AGENT_ADDRESS, EmailSendRequest(
            to=email,
            subject=f"🚨 {subject}",
            body="System monitoring detected an issue that requires attention."
        ))

if __name__ == "__main__":
    print("🚀 My Application with Gmail Integration")
    print(f"Gmail Agent: {GMAIL_AGENT_ADDRESS}")
    print("This example shows how to integrate Gmail agent into your app")
    print("Make sure the Gmail agent is running!")
    print("\nStarting application...")
    app_agent.run()
