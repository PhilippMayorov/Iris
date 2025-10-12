"""
Simple test script for ASI One API client

This script tests the basic functionality of the ASI One client.
Run this to verify your setup is working correctly.
"""

import os
import sys

# Handle both relative and absolute imports
try:
    from asi_client import ASIOneClient
except ImportError:
    from .asi_client import ASIOneClient


def test_client_initialization():
    """Test client initialization."""
    print("Testing client initialization...")
    
    try:
        # Test with environment variable
        client = ASIOneClient()
        print("✅ Client initialized successfully with environment variable")
        return client
    except ValueError as e:
        print(f"❌ Client initialization failed: {e}")
        print("Make sure to set ASI_ONE_API_KEY environment variable")
        return None


def test_simple_request(client):
    """Test a simple API request."""
    if not client:
        print("Skipping API test - client not initialized")
        return
    
    print("\nTesting simple API request...")
    
    try:
        response = client.simple_chat("Hello! This is a test message.")
        print(f"✅ API request successful!")
        print(f"Response: {response[:100]}{'...' if len(response) > 100 else ''}")
        return True
    except Exception as e:
        print(f"❌ API request failed: {e}")
        return False


def test_response_structure(client):
    """Test the full response structure."""
    if not client:
        print("Skipping response structure test - client not initialized")
        return
    
    print("\nTesting response structure...")
    
    try:
        messages = [{"role": "user", "content": "What is 2+2?"}]
        response = client.chat_completion(messages)
        
        # Check required fields
        required_fields = ["choices", "usage", "model", "id"]
        missing_fields = [field for field in required_fields if field not in response]
        
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            return False
        
        # Check choices structure
        if not response["choices"] or len(response["choices"]) == 0:
            print("❌ No choices in response")
            return False
        
        choice = response["choices"][0]
        if "message" not in choice or "content" not in choice["message"]:
            print("❌ Invalid choice structure")
            return False
        
        print("✅ Response structure is valid")
        print(f"Model: {response['model']}")
        print(f"Total tokens: {response['usage']['total_tokens']}")
        print(f"Content: {choice['message']['content'][:100]}{'...' if len(choice['message']['content']) > 100 else ''}")
        
        return True
        
    except Exception as e:
        print(f"❌ Response structure test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("ASI One API Client Test Suite")
    print("=" * 40)
    
    # Check environment
    api_key = os.getenv('ASI_ONE_API_KEY')
    if not api_key:
        print("❌ ASI_ONE_API_KEY environment variable not set")
        print("Please set your API key: export ASI_ONE_API_KEY='your_key_here'")
        sys.exit(1)
    else:
        print(f"✅ API key found (length: {len(api_key)})")
    
    # Run tests
    client = test_client_initialization()
    api_success = test_simple_request(client)
    structure_success = test_response_structure(client)
    
    # Summary
    print("\n" + "=" * 40)
    print("Test Summary:")
    print(f"Client Initialization: {'✅ PASS' if client else '❌ FAIL'}")
    print(f"API Request: {'✅ PASS' if api_success else '❌ FAIL'}")
    print(f"Response Structure: {'✅ PASS' if structure_success else '❌ FAIL'}")
    
    if client and api_success and structure_success:
        print("\n🎉 All tests passed! Your ASI One API integration is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
