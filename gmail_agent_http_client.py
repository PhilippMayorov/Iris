#!/usr/bin/env python3
"""
HTTP Client for Gmail Agent

This script demonstrates how to send HTTP POST requests to the Gmail agent
using both structured email requests and natural language chat messages.

The Gmail agent runs on port 8000 by default and supports:
1. Structured email requests (EmailSendRequest)
2. Natural language chat messages (ChatMessage)
3. Health checks
"""

import json
import requests
import time
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import uuid4

class GmailAgentHTTPClient:
    """HTTP client for interacting with the Gmail agent"""
    
    def __init__(self, agent_url: str = "http://127.0.0.1:8000", oauth_url: str = "http://localhost:8080"):
        """
        Initialize the Gmail agent HTTP client
        
        Args:
            agent_url: URL of the Gmail agent (default: http://127.0.0.1:8000)
            oauth_url: URL of the OAuth server (default: http://localhost:8080)
        """
        self.agent_url = agent_url
        self.oauth_url = oauth_url
        self.session = requests.Session()
        
    def check_agent_health(self) -> Dict[str, Any]:
        """
        Check if the Gmail agent is running and healthy
        
        Returns:
            Dict with health status information
        """
        try:
            # uAgents typically expose health endpoints
            response = self.session.get(f"{self.agent_url}/health", timeout=5)
            if response.status_code == 200:
                return {"healthy": True, "response": response.json()}
            else:
                return {"healthy": False, "status_code": response.status_code}
        except requests.exceptions.RequestException as e:
            return {"healthy": False, "error": str(e)}
    
    def check_oauth_status(self) -> Dict[str, Any]:
        """
        Check OAuth authentication status
        
        Returns:
            Dict with authentication status
        """
        try:
            response = self.session.get(f"{self.oauth_url}/status", timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                return {"authenticated": False, "error": "OAuth server not responding"}
        except requests.exceptions.RequestException as e:
            return {"authenticated": False, "error": str(e)}
    
    def send_structured_email(self, to: str, subject: str, body: str, from_email: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a structured email request to the Gmail agent
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            from_email: Optional sender email (uses authenticated user if not provided)
            
        Returns:
            Dict with response from the agent
        """
        # Create the email request payload
        email_request = {
            "to": to,
            "subject": subject,
            "body": body
        }
        
        if from_email:
            email_request["from_email"] = from_email
        
        # uAgents uses a specific message format
        message_payload = {
            "type": "EmailSendRequest",
            "data": email_request,
            "timestamp": datetime.utcnow().isoformat(),
            "msg_id": str(uuid4())
        }
        
        try:
            # Send POST request to the agent's submit endpoint
            response = self.session.post(
                f"{self.agent_url}/submit",
                json=message_payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                return {"success": True, "response": response.json()}
            else:
                return {
                    "success": False, 
                    "status_code": response.status_code,
                    "error": response.text
                }
                
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def send_natural_language_message(self, message: str) -> Dict[str, Any]:
        """
        Send a natural language message to the Gmail agent
        
        Args:
            message: Natural language message (e.g., "Send an email to john@example.com about the meeting")
            
        Returns:
            Dict with response from the agent
        """
        # Create chat message payload
        chat_message = {
            "type": "ChatMessage",
            "data": {
                "content": [
                    {
                        "type": "text",
                        "text": message
                    }
                ],
                "timestamp": datetime.utcnow().isoformat(),
                "msg_id": str(uuid4())
            }
        }
        
        try:
            response = self.session.post(
                f"{self.agent_url}/submit",
                json=chat_message,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                return {"success": True, "response": response.json()}
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }
                
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def send_health_check(self) -> Dict[str, Any]:
        """
        Send a health check request to the Gmail agent
        
        Returns:
            Dict with health check response
        """
        health_request = {
            "type": "HealthCheck",
            "data": {},
            "timestamp": datetime.utcnow().isoformat(),
            "msg_id": str(uuid4())
        }
        
        try:
            response = self.session.post(
                f"{self.agent_url}/submit",
                json=health_request,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                return {"success": True, "response": response.json()}
            else:
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }
                
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}


def main():
    """Example usage of the Gmail Agent HTTP Client"""
    
    print("🚀 Gmail Agent HTTP Client")
    print("=" * 50)
    
    # Initialize client
    client = GmailAgentHTTPClient()
    
    # Check if agent is running
    print("1. Checking agent health...")
    health = client.check_agent_health()
    if health["healthy"]:
        print("✅ Gmail agent is running")
    else:
        print("❌ Gmail agent is not responding")
        print(f"Error: {health.get('error', 'Unknown error')}")
        return
    
    # Check OAuth status
    print("\n2. Checking OAuth authentication...")
    oauth_status = client.check_oauth_status()
    if oauth_status.get("authenticated"):
        print(f"✅ Authenticated as: {oauth_status.get('email', 'Unknown')}")
    else:
        print("❌ Not authenticated")
        print(f"Error: {oauth_status.get('error', 'Unknown error')}")
        print(f"🔐 Please authenticate at: {client.oauth_url}")
        return
    
    # Send health check
    print("\n3. Sending health check request...")
    health_response = client.send_health_check()
    if health_response["success"]:
        print("✅ Health check successful")
        print(f"Response: {health_response['response']}")
    else:
        print("❌ Health check failed")
        print(f"Error: {health_response['error']}")
    
    # Example 1: Send structured email
    print("\n4. Sending structured email...")
    email_response = client.send_structured_email(
        to="test@example.com",
        subject="Test Email from HTTP Client",
        body="This is a test email sent via HTTP POST request to the Gmail agent!"
    )
    
    if email_response["success"]:
        print("✅ Structured email request sent successfully")
        print(f"Response: {email_response['response']}")
    else:
        print("❌ Structured email request failed")
        print(f"Error: {email_response['error']}")
    
    # Example 2: Send natural language message
    print("\n5. Sending natural language message...")
    chat_response = client.send_natural_language_message(
        "Send an email to john@example.com about the meeting tomorrow at 2pm"
    )
    
    if chat_response["success"]:
        print("✅ Natural language message sent successfully")
        print(f"Response: {chat_response['response']}")
    else:
        print("❌ Natural language message failed")
        print(f"Error: {chat_response['error']}")
    
    print("\n" + "=" * 50)
    print("🎉 HTTP client demo completed!")


if __name__ == "__main__":
    main()
