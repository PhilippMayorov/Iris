#!/usr/bin/env python3
"""
Gmail Agent Communication Helper

This module provides specialized functions for communicating with the Gmail agent
deployed on Agentverse. It handles the specific message formats and protocols
required for reliable email sending through the agentic chat system.
"""

import re
from typing import Dict, Optional, Tuple


class GmailAgentHelper:
    """Helper class for Gmail agent communication."""
    
    # Gmail agent address on Agentverse
    GMAIL_AGENT_ADDRESS = "agent1qw6kgumlfqp9drr54qsfngdkz50vgues3u7sewg2fgketekqk8hz500ytg3"
    
    @staticmethod
    def format_email_request(to_email: str, subject: str, content: str) -> str:
        """
        Format an email request in the structured format expected by the Gmail agent.
        
        Args:
            to_email: Recipient email address
            subject: Email subject (can be empty)
            content: Email body content
            
        Returns:
            Formatted email request string
        """
        # Validate email format
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if not re.match(email_pattern, to_email):
            raise ValueError(f"Invalid email format: {to_email}")
        
        # Format the request
        request = f"send\nto: {to_email}\n"
        
        if subject and subject.strip():
            request += f"subject: {subject.strip()}\n"
        
        request += f"content: {content.strip()}"
        
        return request
    
    @staticmethod
    def parse_email_request(text: str) -> Optional[Dict[str, str]]:
        """
        Parse an email request from natural language text.
        
        Args:
            text: Natural language text containing email request
            
        Returns:
            Dictionary with email details or None if parsing fails
        """
        # Look for email patterns
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        if not emails:
            return None
        
        # Extract subject (look for "subject:" or "about:" or similar)
        subject_patterns = [
            r'subject[:\s]+([^\n\r]+)',
            r'about[:\s]+([^\n\r]+)',
            r'title[:\s]+([^\n\r]+)',
            r're[:\s]+([^\n\r]+)'
        ]
        
        subject = ""
        for pattern in subject_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                subject = match.group(1).strip()
                break
        
        # Extract content (everything after common email indicators)
        content_patterns = [
            r'(?:message|content|body|text)[:\s]+(.+)',
            r'(?:say|tell|write)[:\s]+(.+)',
            r'(?:email|send)[:\s]+(.+)'
        ]
        
        content = ""
        for pattern in content_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                break
        
        # If no specific content pattern found, try to extract the main message
        if not content:
            # Remove email and subject from text to get content
            content = text
            for email in emails:
                content = content.replace(email, "")
            if subject:
                content = content.replace(subject, "")
            content = re.sub(r'^(?:send|email|message|to|subject|about|title|re)[:\s]*', '', content, flags=re.IGNORECASE)
            content = content.strip()
        
        return {
            "to": emails[0],  # Use first email found
            "subject": subject,
            "content": content
        }
    
    @staticmethod
    def create_gmail_agent_prompt(user_request: str) -> str:
        """
        Create a prompt that will help the agentic model communicate with the Gmail agent.
        
        Args:
            user_request: The user's original request
            
        Returns:
            Formatted prompt for the agentic model
        """
        return f"""I need to send an email. Please use the Gmail Agent at address {GmailAgentHelper.GMAIL_AGENT_ADDRESS} to send this email.

User request: {user_request}

Please format the email request using this exact structure:
```
send
to: [recipient email]
subject: [email subject - optional]
content: [email message]
```

Make sure to:
1. Use the exact Gmail agent address: {GmailAgentHelper.GMAIL_AGENT_ADDRESS}
2. Format the request exactly as shown above
3. Wait for confirmation that the email was sent
4. Report back to the user with the status"""
    
    @staticmethod
    def is_email_request(text: str) -> bool:
        """
        Check if the text contains an email sending request.
        
        Args:
            text: Text to analyze
            
        Returns:
            True if this appears to be an email request
        """
        email_indicators = [
            "send email",
            "send an email", 
            "email to",
            "send a message",
            "email someone",
            "send mail",
            "compose email",
            "write email"
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in email_indicators)
    
    @staticmethod
    def extract_email_info(text: str) -> Tuple[bool, Optional[Dict[str, str]]]:
        """
        Extract email information from text and determine if it's a valid email request.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (is_valid_request, email_info_dict)
        """
        if not GmailAgentHelper.is_email_request(text):
            return False, None
        
        email_info = GmailAgentHelper.parse_email_request(text)
        if not email_info:
            return False, None
        
        # Validate that we have required fields
        if not email_info.get("to") or not email_info.get("content"):
            return False, None
        
        return True, email_info


def test_gmail_helper():
    """Test the Gmail helper functions."""
    print("Testing Gmail Agent Helper...")
    
    # Test email formatting
    try:
        formatted = GmailAgentHelper.format_email_request(
            "test@example.com", 
            "Test Subject", 
            "This is a test message"
        )
        print(f"✅ Formatted email: {formatted}")
    except Exception as e:
        print(f"❌ Format error: {e}")
    
    # Test email parsing
    test_text = "Send an email to john@example.com about the meeting tomorrow. Tell him we need to reschedule."
    is_valid, email_info = GmailAgentHelper.extract_email_info(test_text)
    print(f"✅ Email request detected: {is_valid}")
    if email_info:
        print(f"   To: {email_info['to']}")
        print(f"   Subject: {email_info['subject']}")
        print(f"   Content: {email_info['content']}")
    
    # Test prompt creation
    prompt = GmailAgentHelper.create_gmail_agent_prompt("Send an email to my boss about the project status")
    print(f"✅ Generated prompt: {prompt[:100]}...")


if __name__ == "__main__":
    test_gmail_helper()
