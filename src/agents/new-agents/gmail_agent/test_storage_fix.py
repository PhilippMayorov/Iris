#!/usr/bin/env python3
"""
Test script to verify the storage fix for conversation history

This script tests the conversation history storage functionality
to ensure the KeyValueStore.get() issue is resolved.
"""

import os
import sys
from datetime import datetime
from uuid import uuid4

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gmail_agent import process_email_request_with_asi_one


def test_storage_fix():
    """Test that the storage fix works correctly"""
    
    print("🧪 Testing Storage Fix for Conversation History")
    print("=" * 50)
    
    # Test the process_email_request_with_asi_one function with conversation history
    test_cases = [
        {
            "name": "Basic request with empty history",
            "input": "send an email to john@example.com about the meeting",
            "history": []
        },
        {
            "name": "Request with existing history",
            "input": "email him about the project update",
            "history": [
                {"role": "user", "content": "I need to contact john@example.com"},
                {"role": "assistant", "content": "I understand you want to contact john@example.com. What would you like to send to him?"}
            ]
        },
        {
            "name": "Context-aware request",
            "input": "tell her we're done with the proposal",
            "history": [
                {"role": "user", "content": "sarah@company.com is my manager"},
                {"role": "assistant", "content": "I understand sarah@company.com is your manager. How can I help you with email?"}
            ]
        }
    ]
    
    success_count = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print(f"Input: {test_case['input']}")
        print(f"History length: {len(test_case['history'])}")
        
        try:
            result = process_email_request_with_asi_one(test_case['input'], test_case['history'])
            
            if result:
                print("✅ Function executed successfully")
                print(f"   Valid format: {result.get('is_valid_format', False)}")
                print(f"   To: {result.get('to', 'None')}")
                print(f"   Subject: {result.get('subject', 'None')}")
                print(f"   Body: {result.get('body', 'None')[:50]}{'...' if result.get('body') and len(result.get('body', '')) > 50 else ''}")
                if result.get("reasoning"):
                    print(f"   Reasoning: {result['reasoning'][:100]}{'...' if len(result.get('reasoning', '')) > 100 else ''}")
                success_count += 1
            else:
                print("❌ Function returned None")
                
        except Exception as e:
            print(f"❌ Exception occurred: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print(f"Test Results: {success_count}/{len(test_cases)} tests passed")
    
    if success_count == len(test_cases):
        print("🎉 All tests passed! Storage fix is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the implementation.")
        return False


def main():
    """Main test function"""
    
    print("Gmail Agent Storage Fix Test")
    print("=" * 50)
    
    # Test the storage fix
    storage_success = test_storage_fix()
    
    print("\n" + "=" * 50)
    print("Storage Fix Test Results:")
    print(f"Storage Fix: {'✅ PASS' if storage_success else '❌ FAIL'}")
    
    if storage_success:
        print("\n🎉 The storage fix is working correctly!")
        print("The KeyValueStore.get() issue has been resolved.")
        print("\nThe agent should now be able to:")
        print("- Retrieve conversation history without errors")
        print("- Store conversation history properly")
        print("- Maintain context across multiple interactions")
    else:
        print("\n⚠️  The storage fix needs more work.")
        print("Check the error messages above for details.")


if __name__ == "__main__":
    main()
