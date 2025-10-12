#!/usr/bin/env python3
"""
Example usage of Gmail Agent with ASI:One integration

This script demonstrates how to interact with the Gmail Agent
using natural language through ASI:One.
"""

import os
import sys
from datetime import datetime
from uuid import uuid4

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from uagents import Agent, Context
from uagents_core.contrib.protocols.chat import ChatMessage, TextContent


def create_client_agent():
    """Create a client agent to communicate with the Gmail agent"""
    
    # You'll need to replace this with the actual Gmail agent address
    # The address will be shown when you run the Gmail agent
    GMAIL_AGENT_ADDRESS = "agent1qw6kgumlfq"  # Replace with actual address
    
    client_agent = Agent(
        name="gmail-client",
        seed="client_seed_phrase_for_testing",
        port=8002,
        endpoint=["http://127.0.0.1:8002/submit"],
    )
    
    return client_agent, GMAIL_AGENT_ADDRESS


def send_natural_language_email(client_agent, gmail_agent_address, message):
    """Send a natural language email request to the Gmail agent"""
    
    print(f"Sending message: {message}")
    
    # Create chat message
    chat_message = ChatMessage(
        timestamp=datetime.now(),
        msg_id=uuid4(),
        content=[TextContent(type="text", text=message)]
    )
    
    # Send to Gmail agent
    client_agent.send(gmail_agent_address, chat_message)


def main():
    """Main example function"""
    
    print("Gmail Agent ASI:One Integration Example")
    print("=" * 50)
    
    # Check if ASI:One API key is set
    if not os.getenv("ASI_ONE_API_KEY"):
        print("⚠️  ASI_ONE_API_KEY not set")
        print("Please set your ASI:One API key:")
        print("export ASI_ONE_API_KEY='your_api_key_here'")
        print("Get your API key at: https://asi1.ai/dashboard/api-keys")
        return
    
    print("✅ ASI_ONE_API_KEY is set")
    
    # Create client agent
    client_agent, gmail_agent_address = create_client_agent()
    
    print(f"Client agent created: {client_agent.address}")
    print(f"Target Gmail agent: {gmail_agent_address}")
    print()
    
    # Example natural language email requests - now much more lenient
    example_requests = [
        "Send an email to john@example.com saying hello and asking how he's doing",
        "Email team@company.com with subject 'Project Update' and tell them we're on track for delivery",
        "Write to client@business.com about the proposal review and ask for their feedback",
        "Send a thank you email to sarah@company.com for the great meeting yesterday",
        "email john about the meeting",
        "tell the boss we're done",
        "quick note to client",
        "meeting tomorrow 2pm",
        "write to sarah",
        "send something to team@company.com"
    ]
    
    print("Example natural language email requests:")
    print("=" * 50)
    
    for i, request in enumerate(example_requests, 1):
        print(f"{i}. {request}")
    
    print()
    print("To use this example:")
    print("1. Start the Gmail agent: python gmail_agent.py")
    print("2. Note the agent address from the output")
    print("3. Update GMAIL_AGENT_ADDRESS in this script")
    print("4. Run this script: python example_asi_one_usage.py")
    print("5. The Gmail agent will process your natural language requests using ASI:One")
    
    print()
    print("AI-Only Processing Flow:")
    print("1. User sends natural language request (any format)")
    print("2. ASI:One analyzes the request with intelligent reasoning")
    print("3. ASI:One extracts or suggests email details (to, subject, body)")
    print("4. If information is missing, AI asks for clarification")
    print("5. Gmail agent validates and sends the email")
    print("6. User receives confirmation with AI reasoning")
    
    print()
    print("Benefits of AI-Only Processing:")
    print("- No formatting requirements whatsoever")
    print("- Natural, conversational language support")
    print("- Intelligent context understanding and reasoning")
    print("- Automatic email detail extraction and suggestions")
    print("- Helpful clarification requests for missing information")
    print("- Enhanced user experience with zero learning curve")


if __name__ == "__main__":
    main()
