#!/usr/bin/env python3
"""
Test script for ASI:One integration with Gmail Agent

This script demonstrates how the Gmail Agent processes natural language
email requests using ASI:One LLM.
"""

import os
import sys
from datetime import datetime
from uuid import uuid4

# Add the current directory to the path so we can import the gmail_agent
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gmail_agent import process_email_request_with_asi_one, asi_one_client
from uagents_core.contrib.protocols.chat import ChatMessage, TextContent


def test_asi_one_processing():
    """Test ASI:One natural language processing"""
    
    print("🧪 Testing ASI:One Integration with Gmail Agent")
    print("=" * 50)
    
    # Check if ASI:One client is available
    if not asi_one_client:
        print("❌ ASI:One client not available")
        print("⚠️ Email functionality requires ASI:One AI integration")
        print("Please set ASI_ONE_API_KEY environment variable")
        print("Get your API key at: https://asi1.ai/dashboard/api-keys")
        return False
    
    print("✅ ASI:One client is available")
    print()
    
    # Test cases for natural language email requests - now much more lenient
    test_cases = [
        {
            "name": "Simple email request",
            "input": "Send an email to john@example.com saying hello",
            "expected_fields": ["to", "body"]
        },
        {
            "name": "Email with subject",
            "input": "Email team@company.com with subject 'Project Update' and tell them we're on track",
            "expected_fields": ["to", "subject", "body"]
        },
        {
            "name": "Complex email request",
            "input": "Write to client@business.com about the proposal review and ask for their thoughts on the timeline",
            "expected_fields": ["to", "body"]
        },
        {
            "name": "Meeting invitation",
            "input": "Send a meeting invitation to sarah@company.com for tomorrow at 2 PM",
            "expected_fields": ["to", "body"]
        },
        {
            "name": "Very casual request",
            "input": "email john about the meeting",
            "expected_fields": ["body"],
            "should_ask_clarification": True
        },
        {
            "name": "Incomplete request",
            "input": "send something to team@company.com",
            "expected_fields": ["to"],
            "should_ask_clarification": True
        },
        {
            "name": "Just a name",
            "input": "write to sarah",
            "expected_fields": [],
            "should_ask_clarification": True
        },
        {
            "name": "Context only",
            "input": "meeting tomorrow 2pm",
            "expected_fields": [],
            "should_ask_clarification": True
        },
        {
            "name": "Role-based request",
            "input": "tell the boss we're done",
            "expected_fields": ["body"],
            "should_ask_clarification": True
        },
        {
            "name": "Very brief",
            "input": "quick note to client",
            "expected_fields": [],
            "should_ask_clarification": True
        },
        {
            "name": "Context-aware request",
            "input": "email him about the meeting",
            "expected_fields": ["body"],
            "should_ask_clarification": True,
            "conversation_context": [
                {"role": "user", "content": "I need to contact john@company.com"},
                {"role": "assistant", "content": "I understand you want to contact john@company.com. What would you like to send to him?"}
            ]
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print(f"Input: {test_case['input']}")
        
        try:
            # Test with conversation history for context-aware processing
            conversation_history = test_case.get('conversation_context', [
                {"role": "user", "content": "Hi, I need to send some emails"},
                {"role": "assistant", "content": "Hello! I'm your Gmail assistant. I can help you send emails using natural language. Just tell me what you want to send!"}
            ])
            result = process_email_request_with_asi_one(test_case['input'], conversation_history)
            
            if result["is_valid_format"]:
                print("✅ Processing successful")
                print(f"   To: {result['to']}")
                print(f"   Subject: {result['subject'] or '(no subject)'}")
                print(f"   Body: {result['body'][:50]}{'...' if len(result['body']) > 50 else ''}")
                if result.get("reasoning"):
                    print(f"   Reasoning: {result['reasoning']}")
                
                # Check if expected fields are present
                missing_fields = []
                for field in test_case['expected_fields']:
                    if not result.get(field):
                        missing_fields.append(field)
                
                if missing_fields:
                    print(f"⚠️  Missing expected fields: {missing_fields}")
                else:
                    print("✅ All expected fields present")
                    success_count += 1
            else:
                # Check if this was expected to need clarification
                if test_case.get("should_ask_clarification", False):
                    if result.get("needs_clarification", False):
                        print("✅ Correctly asked for clarification")
                        print(f"   Error: {result['error']}")
                        if result.get("suggestions"):
                            print(f"   Suggestions: {result['suggestions']}")
                        success_count += 1
                    else:
                        print(f"⚠️  Expected clarification request but got: {result['error']}")
                else:
                    print(f"❌ Processing failed: {result['error']}")
                    if result.get("reasoning"):
                        print(f"   Reasoning: {result['reasoning']}")
            
        except Exception as e:
            print(f"❌ Exception occurred: {str(e)}")
        
        print()
    
    print("=" * 50)
    print(f"Test Results: {success_count}/{len(test_cases)} tests passed")
    
    if success_count == len(test_cases):
        print("🎉 All tests passed! ASI:One integration is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the ASI:One API key and network connection.")
        return False


def test_chat_message_processing():
    """Test chat message processing with ASI:One"""
    
    print("\n🧪 Testing Chat Message Processing")
    print("=" * 50)
    
    if not asi_one_client:
        print("❌ ASI:One client not available - email functionality requires AI integration")
        return False
    
    # Create a test chat message
    test_message = ChatMessage(
        timestamp=datetime.now(),
        msg_id=uuid4(),
        content=[
            TextContent(type="text", text="Send an email to test@example.com about the project status")
        ]
    )
    
    print("Test Chat Message:")
    print(f"Content: {test_message.content[0].text}")
    
    # Extract text content
    text = ''
    for item in test_message.content:
        if hasattr(item, 'text'):
            text += item.text
    
    print(f"Extracted text: {text}")
    
    # Process with ASI:One
    result = process_email_request_with_asi_one(text)
    
    if result["is_valid_format"]:
        print("✅ Chat message processing successful")
        print(f"   To: {result['to']}")
        print(f"   Subject: {result['subject'] or '(no subject)'}")
        print(f"   Body: {result['body']}")
        return True
    else:
        print(f"❌ Chat message processing failed: {result['error']}")
        return False


def main():
    """Main test function"""
    
    print("Gmail Agent ASI:One Integration Test")
    print("=" * 50)
    
    # Test ASI:One processing
    processing_success = test_asi_one_processing()
    
    # Test chat message processing
    chat_success = test_chat_message_processing()
    
    print("\n" + "=" * 50)
    print("Overall Test Results:")
    print(f"ASI:One Processing: {'✅ PASS' if processing_success else '❌ FAIL'}")
    print(f"Chat Message Processing: {'✅ PASS' if chat_success else '❌ FAIL'}")
    
    if processing_success and chat_success:
        print("\n🎉 All tests passed! The Gmail Agent is ready with AI-only processing.")
        print("\nTo use the agent:")
        print("1. Set your ASI_ONE_API_KEY environment variable")
        print("2. Set up Gmail OAuth authentication")
        print("3. Run: python gmail_agent.py")
        print("4. Just talk naturally - no formatting requirements!")
        print("5. Connect via ASI:One chat or use the agent directly")
    else:
        print("\n⚠️  Some tests failed. Please check your setup.")
        print("Make sure you have:")
        print("- Valid ASI_ONE_API_KEY environment variable")
        print("- Internet connection")
        print("- Proper OpenAI client installation")
        print("\n⚠️  Note: Email functionality requires ASI:One AI integration")


if __name__ == "__main__":
    main()
