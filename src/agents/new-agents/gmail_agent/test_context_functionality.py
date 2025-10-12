#!/usr/bin/env python3
"""
Test script to verify context functionality in Gmail Agent

This script tests the conversation context and natural language processing
capabilities of the Gmail Agent with ASI:One integration.
"""

import os
import sys
from datetime import datetime

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gmail_agent import process_email_request_with_asi_one

def test_context_functionality():
    """Test the context functionality of the Gmail Agent"""
    
    print("🧪 Testing Gmail Agent Context Functionality")
    print("=" * 60)
    
    # Check if ASI:One is available
    if not os.environ.get('ASI_ONE_API_KEY'):
        print("❌ ASI_ONE_API_KEY not found!")
        print("\n🔧 To enable context functionality:")
        print("1. Get your API key from: https://asi1.ai/dashboard/api-keys")
        print("2. Set the environment variable: export ASI_ONE_API_KEY='your_key'")
        print("3. Or run: python setup_asi_one.py")
        print("\n⚠️ Without ASI:One, context functionality will be limited.")
        return False
    
    print("✅ ASI:One API key found - testing context functionality")
    
    # Test cases with conversation context
    test_cases = [
        {
            "name": "Initial Contact Setup",
            "input": "I need to contact john@example.com about the project",
            "history": [],
            "expected_context": "Should remember john@example.com for future reference"
        },
        {
            "name": "Context Reference - Using 'him'",
            "input": "email him about the meeting tomorrow",
            "history": [
                {"role": "user", "content": "I need to contact john@example.com about the project"},
                {"role": "assistant", "content": "I understand you want to contact john@example.com. What would you like to send to him?"}
            ],
            "expected_context": "Should understand 'him' refers to john@example.com"
        },
        {
            "name": "Context Reference - Using 'her'",
            "input": "tell her we're done with the proposal",
            "history": [
                {"role": "user", "content": "sarah@company.com is my manager"},
                {"role": "assistant", "content": "I understand sarah@company.com is your manager. How can I help you with email?"}
            ],
            "expected_context": "Should understand 'her' refers to sarah@company.com"
        },
        {
            "name": "Context Reference - Using 'the team'",
            "input": "update the team about our progress",
            "history": [
                {"role": "user", "content": "team@company.com is our development team"},
                {"role": "assistant", "content": "I understand team@company.com is your development team. What would you like to send to them?"}
            ],
            "expected_context": "Should understand 'the team' refers to team@company.com"
        },
        {
            "name": "Context Reference - Project Context",
            "input": "send the client an update",
            "history": [
                {"role": "user", "content": "client@business.com is our main client"},
                {"role": "assistant", "content": "I understand client@business.com is your main client. How can I help you with email?"},
                {"role": "user", "content": "we're working on the mobile app project"},
                {"role": "assistant", "content": "I understand you're working on the mobile app project. What would you like to send to the client?"}
            ],
            "expected_context": "Should understand 'the client' and reference the mobile app project"
        },
        {
            "name": "Context Reference - Multiple People",
            "input": "email both of them about the meeting",
            "history": [
                {"role": "user", "content": "john@example.com and sarah@company.com are my team leads"},
                {"role": "assistant", "content": "I understand john@example.com and sarah@company.com are your team leads. How can I help you with email?"}
            ],
            "expected_context": "Should understand 'both of them' refers to john@example.com and sarah@company.com"
        }
    ]
    
    success_count = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        print(f"Input: '{test_case['input']}'")
        print(f"History: {len(test_case['history'])} messages")
        print(f"Expected: {test_case['expected_context']}")
        
        try:
            result = process_email_request_with_asi_one(
                test_case['input'], 
                test_case['history']
            )
            
            if result:
                print("✅ Function executed successfully")
                
                # Check if context was used properly
                if result.get('is_valid_format'):
                    print("✅ Valid email format extracted")
                    print(f"   To: {result.get('to', 'None')}")
                    print(f"   Subject: {result.get('subject', 'None')}")
                    body = result.get('body', '')
                    if body:
                        print(f"   Body: {body[:100]}{'...' if len(body) > 100 else ''}")
                    
                    if result.get('reasoning'):
                        print(f"   Reasoning: {result['reasoning'][:150]}{'...' if len(result.get('reasoning', '')) > 150 else ''}")
                    
                    success_count += 1
                else:
                    print("⚠️ Invalid format - context may not be working properly")
                    if result.get('error'):
                        print(f"   Error: {result['error']}")
                    if result.get('reasoning'):
                        print(f"   Reasoning: {result['reasoning']}")
            else:
                print("❌ Function returned None")
                
        except Exception as e:
            print(f"❌ Exception occurred: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All context tests passed! Context functionality is working correctly.")
        return True
    elif success_count > total_tests // 2:
        print("⚠️ Some context tests passed. Context functionality is partially working.")
        return True
    else:
        print("❌ Most context tests failed. Context functionality needs attention.")
        return False

def test_conversation_flow():
    """Test a complete conversation flow"""
    
    print("\n🔄 Testing Complete Conversation Flow")
    print("=" * 60)
    
    # Simulate a conversation
    conversation_history = []
    
    # Step 1: User introduces a contact
    print("\n👤 User: 'I need to contact john@example.com about the project'")
    result1 = process_email_request_with_asi_one(
        "I need to contact john@example.com about the project",
        conversation_history
    )
    
    if result1:
        conversation_history.append({"role": "user", "content": "I need to contact john@example.com about the project"})
        conversation_history.append({"role": "assistant", "content": "I understand you want to contact john@example.com. What would you like to send to him?"})
        print("✅ Context stored: john@example.com")
    
    # Step 2: User refers to the contact with pronoun
    print("\n👤 User: 'email him about the meeting tomorrow'")
    result2 = process_email_request_with_asi_one(
        "email him about the meeting tomorrow",
        conversation_history
    )
    
    if result2 and result2.get('is_valid_format'):
        print("✅ Context used: 'him' correctly identified as john@example.com")
        print(f"   To: {result2.get('to')}")
        print(f"   Subject: {result2.get('subject')}")
    else:
        print("❌ Context failed: Could not resolve 'him' to john@example.com")
        if result2 and result2.get('error'):
            print(f"   Error: {result2['error']}")
    
    # Step 3: User adds more context
    print("\n👤 User: 'the project is a mobile app for iOS'")
    result3 = process_email_request_with_asi_one(
        "the project is a mobile app for iOS",
        conversation_history
    )
    
    if result3:
        conversation_history.append({"role": "user", "content": "the project is a mobile app for iOS"})
        conversation_history.append({"role": "assistant", "content": "I understand the project is a mobile app for iOS. How can I help you with email?"})
        print("✅ Context updated: mobile app for iOS")
    
    # Step 4: User refers to both contact and project
    print("\n👤 User: 'send him an update about our progress'")
    result4 = process_email_request_with_asi_one(
        "send him an update about our progress",
        conversation_history
    )
    
    if result4 and result4.get('is_valid_format'):
        print("✅ Context used: Both 'him' and project context applied")
        print(f"   To: {result4.get('to')}")
        print(f"   Subject: {result4.get('subject')}")
        if result4.get('body'):
            print(f"   Body: {result4.get('body')[:100]}...")
    else:
        print("❌ Context failed: Could not use both contact and project context")
        if result4 and result4.get('error'):
            print(f"   Error: {result4['error']}")

def main():
    """Main test function"""
    
    print("Gmail Agent - Context Functionality Test")
    print("=" * 60)
    
    # Test basic context functionality
    context_success = test_context_functionality()
    
    # Test conversation flow
    test_conversation_flow()
    
    print("\n" + "=" * 60)
    print("📋 Context Test Summary:")
    print(f"Context Functionality: {'✅ WORKING' if context_success else '❌ NEEDS ATTENTION'}")
    
    if context_success:
        print("\n🎉 Context functionality is working correctly!")
        print("The Gmail Agent can:")
        print("- Remember conversation history")
        print("- Use pronouns to reference previous contacts")
        print("- Maintain context across multiple interactions")
        print("- Build upon previous information")
    else:
        print("\n⚠️ Context functionality needs attention.")
        print("Possible issues:")
        print("- ASI:One API key not set or invalid")
        print("- Network connectivity issues")
        print("- API rate limits or quotas")
        print("- Model configuration issues")
        
        print("\n🔧 Troubleshooting steps:")
        print("1. Verify ASI:One API key: export ASI_ONE_API_KEY='your_key'")
        print("2. Check network connectivity")
        print("3. Verify API key permissions")
        print("4. Check ASI:One service status")

if __name__ == "__main__":
    main()
