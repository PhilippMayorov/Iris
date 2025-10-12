#!/usr/bin/env python3
"""
Simple HTTP POST Examples for Gmail Agent

This script shows simple examples of sending HTTP POST requests
directly to the Gmail agent using the requests library.
"""

import requests
import json
from datetime import datetime
from uuid import uuid4

# Configuration
GMAIL_AGENT_URL = "http://127.0.0.1:8000"
OAUTH_SERVER_URL = "http://localhost:8080"

def send_email_request(to_email, subject, body, from_email=None):
    """
    Send a structured email request to the Gmail agent
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body content
        from_email: Optional sender email
    """
    
    # Create the email request payload
    email_data = {
        "to": to_email,
        "subject": subject,
        "body": body
    }
    
    if from_email:
        email_data["from_email"] = from_email
    
    # uAgents message format
    message = {
        "type": "EmailSendRequest",
        "data": email_data,
        "timestamp": datetime.utcnow().isoformat(),
        "msg_id": str(uuid4())
    }
    
    try:
        # Send POST request
        response = requests.post(
            f"{GMAIL_AGENT_URL}/submit",
            json=message,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
            
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def send_chat_message(message_text):
    """
    Send a natural language message to the Gmail agent
    
    Args:
        message_text: Natural language message
    """
    
    # Create chat message payload
    chat_data = {
        "content": [
            {
                "type": "text",
                "text": message_text
            }
        ],
        "timestamp": datetime.utcnow().isoformat(),
        "msg_id": str(uuid4())
    }
    
    message = {
        "type": "ChatMessage",
        "data": chat_data
    }
    
    try:
        response = requests.post(
            f"{GMAIL_AGENT_URL}/submit",
            json=message,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
            
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def check_oauth_status():
    """Check OAuth authentication status"""
    try:
        response = requests.get(f"{OAUTH_SERVER_URL}/status", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return {"authenticated": False, "error": "OAuth server not responding"}
    except requests.exceptions.RequestException as e:
        return {"authenticated": False, "error": str(e)}

def main():
    """Example usage"""
    
    print("📧 Gmail Agent HTTP POST Examples")
    print("=" * 40)
    
    # Check OAuth status first
    print("1. Checking OAuth status...")
    oauth_status = check_oauth_status()
    print(f"OAuth Status: {oauth_status}")
    
    if not oauth_status.get("authenticated"):
        print("❌ Not authenticated. Please authenticate first:")
        print(f"   Visit: {OAUTH_SERVER_URL}")
        return
    
    print("✅ Authenticated!")
    
    # Example 1: Structured email request
    print("\n2. Sending structured email request...")
    result1 = send_email_request(
        to_email="test@example.com",
        subject="Test Email from HTTP POST",
        body="This is a test email sent via HTTP POST request!"
    )
    print(f"Result: {result1}")
    
    # Example 2: Natural language message
    print("\n3. Sending natural language message...")
    result2 = send_chat_message(
        "Send an email to john@example.com about the meeting tomorrow"
    )
    print(f"Result: {result2}")
    
    # Example 3: Another natural language example
    print("\n4. Sending another natural language message...")
    result3 = send_chat_message(
        "Email the team about the project update"
    )
    print(f"Result: {result3}")

if __name__ == "__main__":
    main()
