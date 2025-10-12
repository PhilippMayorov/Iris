#!/usr/bin/env python3
"""
Test script for Gmail Agent HTTP endpoints
This script tests the newly added HTTP endpoints similar to the Spotify agent
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# Configuration
GMAIL_AGENT_URL = "http://localhost:8000"  # Default Gmail agent port
TEST_ENDPOINTS = [
    "/health",
    "/capabilities", 
    "/chat"
]

def test_endpoint(endpoint: str, method: str = "GET", data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Test a single endpoint"""
    url = f"{GMAIL_AGENT_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        return {
            "endpoint": endpoint,
            "method": method,
            "status_code": response.status_code,
            "response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            "success": response.status_code == 200
        }
    except requests.exceptions.ConnectionError:
        return {
            "endpoint": endpoint,
            "method": method,
            "error": "Connection refused - Gmail agent may not be running",
            "success": False
        }
    except requests.exceptions.Timeout:
        return {
            "endpoint": endpoint,
            "method": method,
            "error": "Request timeout",
            "success": False
        }
    except Exception as e:
        return {
            "endpoint": endpoint,
            "method": method,
            "error": str(e),
            "success": False
        }

def main():
    """Main test function"""
    print("🧪 Testing Gmail Agent HTTP Endpoints")
    print("=" * 50)
    
    # Test health endpoint
    print("\n1. Testing /health endpoint...")
    health_result = test_endpoint("/health")
    print(f"   Status: {'✅ PASS' if health_result['success'] else '❌ FAIL'}")
    if health_result['success']:
        print(f"   Response: {json.dumps(health_result['response'], indent=2)}")
    else:
        print(f"   Error: {health_result.get('error', 'Unknown error')}")
    
    # Test capabilities endpoint
    print("\n2. Testing /capabilities endpoint...")
    capabilities_result = test_endpoint("/capabilities")
    print(f"   Status: {'✅ PASS' if capabilities_result['success'] else '❌ FAIL'}")
    if capabilities_result['success']:
        print(f"   Response: {json.dumps(capabilities_result['response'], indent=2)}")
    else:
        print(f"   Error: {capabilities_result.get('error', 'Unknown error')}")
    
    # Test chat endpoint
    print("\n3. Testing /chat endpoint...")
    chat_data = {
        "text": "Send a test email to test@example.com with subject 'Test Email' and body 'This is a test email from the Gmail agent HTTP endpoint.'"
    }
    chat_result = test_endpoint("/chat", method="POST", data=chat_data)
    print(f"   Status: {'✅ PASS' if chat_result['success'] else '❌ FAIL'}")
    if chat_result['success']:
        print(f"   Response: {json.dumps(chat_result['response'], indent=2)}")
    else:
        print(f"   Error: {chat_result.get('error', 'Unknown error')}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    total_tests = 3
    passed_tests = sum([
        health_result['success'],
        capabilities_result['success'], 
        chat_result['success']
    ])
    
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {passed_tests}")
    print(f"   Failed: {total_tests - passed_tests}")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! Gmail agent HTTP endpoints are working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Check the Gmail agent configuration.")
        return 1

if __name__ == "__main__":
    print("Make sure the Gmail agent is running before executing this test.")
    print("You can start it with: python src/agents/new-agents/gmail_agent/gmail_agent.py")
    print()
    
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
