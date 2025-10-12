#!/usr/bin/env python3
"""
Test Gmail Agent Communication

This script tests the communication between the agentic chat and the Gmail agent
to ensure proper email sending functionality.
"""

import os
import sys
import time

# Add the src directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from asi_integration.agentic_chat import AgenticChat
from asi_integration.gmail_agent_helper import GmailAgentHelper


def test_gmail_helper():
    """Test the Gmail helper functions."""
    print("🧪 Testing Gmail Agent Helper...")
    print("=" * 50)
    
    # Test 1: Email request detection
    test_requests = [
        "Send an email to john@example.com about the meeting",
        "Email my boss about the project status",
        "I need to send a message to sarah@company.com",
        "Can you help me book a restaurant?",  # Not an email request
        "Send mail to admin@site.com regarding the issue"
    ]
    
    for request in test_requests:
        is_email = GmailAgentHelper.is_email_request(request)
        print(f"📧 '{request[:30]}...' -> Email request: {is_email}")
    
    print("\n" + "=" * 50)
    
    # Test 2: Email parsing
    test_text = "Send an email to john@example.com about the meeting tomorrow. Tell him we need to reschedule for 3 PM."
    is_valid, email_info = GmailAgentHelper.extract_email_info(test_text)
    
    print(f"📝 Parsing test: '{test_text}'")
    print(f"   Valid: {is_valid}")
    if email_info:
        print(f"   To: {email_info['to']}")
        print(f"   Subject: {email_info['subject']}")
        print(f"   Content: {email_info['content']}")
    
    print("\n" + "=" * 50)
    
    # Test 3: Email formatting
    try:
        formatted = GmailAgentHelper.format_email_request(
            "test@example.com",
            "Test Subject",
            "This is a test message for the Gmail agent."
        )
        print(f"📋 Formatted email request:")
        print(formatted)
    except Exception as e:
        print(f"❌ Format error: {e}")
    
    print("\n" + "=" * 50)


def test_agentic_chat_email_detection():
    """Test email detection in agentic chat."""
    print("🤖 Testing Agentic Chat Email Detection...")
    print("=" * 50)
    
    # Create a test chat instance (without initializing client)
    chat = AgenticChat(model="asi1-agentic")
    
    test_messages = [
        "Send an email to john@example.com about the meeting",
        "Email my boss about the project status",
        "I need to send a message to sarah@company.com",
        "Can you help me book a restaurant?",
        "Send mail to admin@site.com regarding the issue"
    ]
    
    for message in test_messages:
        is_email = chat.is_email_request(message)
        enhanced = chat.enhance_email_request(message)
        
        print(f"📧 Message: '{message[:40]}...'")
        print(f"   Is email request: {is_email}")
        if enhanced != message:
            print(f"   Enhanced: {enhanced[:60]}...")
        print()


def test_gmail_agent_communication():
    """Test actual communication with Gmail agent."""
    print("🔗 Testing Gmail Agent Communication...")
    print("=" * 50)
    
    # Check for API key
    if not os.getenv('ASI_ONE_API_KEY'):
        print("❌ ASI_ONE_API_KEY environment variable not set")
        print("Please set your API key: export ASI_ONE_API_KEY='your_key_here'")
        return False
    
    try:
        # Create agentic chat instance
        chat = AgenticChat(model="asi1-agentic")
        
        # Initialize client
        if not chat.initialize_client():
            print("❌ Failed to initialize ASI One client")
            return False
        
        print("✅ ASI One client initialized successfully")
        print(f"📧 Gmail Agent Address: {GmailAgentHelper.GMAIL_AGENT_ADDRESS}")
        
        # Test email request
        test_message = "Send an email to test@example.com about testing the Gmail agent integration. Tell them this is a test message."
        
        print(f"\n📝 Testing with message: '{test_message}'")
        print("🔄 Getting response from agentic model...")
        
        # Get response (this will test the full flow)
        response = chat.get_response(test_message)
        
        print(f"\n✅ Response received:")
        print(f"   Length: {len(response)} characters")
        print(f"   Contains Gmail agent address: {GmailAgentHelper.GMAIL_AGENT_ADDRESS in response}")
        print(f"   Contains 'send' command: {'send' in response.lower()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during communication test: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Gmail Agent Communication Test Suite")
    print("=" * 60)
    
    # Test 1: Gmail Helper Functions
    test_gmail_helper()
    
    # Test 2: Agentic Chat Email Detection
    test_agentic_chat_email_detection()
    
    # Test 3: Actual Communication (requires API key)
    print("\n" + "=" * 60)
    print("🔑 Testing actual communication (requires ASI_ONE_API_KEY)...")
    
    if os.getenv('ASI_ONE_API_KEY'):
        success = test_gmail_agent_communication()
        if success:
            print("\n✅ All tests completed successfully!")
            print("\n📋 Next steps:")
            print("1. Run the agentic chat: python agentic_chat.py")
            print("2. Try sending an email: 'Send an email to test@example.com about testing'")
            print("3. Check the logs for detailed communication flow")
        else:
            print("\n❌ Communication test failed. Check the error messages above.")
    else:
        print("⚠️  Skipping communication test - ASI_ONE_API_KEY not set")
        print("   Set your API key and run again to test full communication")
    
    print("\n" + "=" * 60)
    print("🏁 Test suite completed!")


if __name__ == "__main__":
    main()
