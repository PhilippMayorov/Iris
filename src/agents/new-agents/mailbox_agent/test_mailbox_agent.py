#!/usr/bin/env python3
"""
Test script for the Intelligent Mailbox Agent

This script tests the mailbox agent functionality including HTTP endpoints.
"""

import os
import sys
import asyncio
import httpx
import json
from datetime import datetime

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir))))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from mailbox_agent import intelligent_handler
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    sys.exit(1)

# Test configuration
HTTP_BASE_URL = "http://localhost:8002"
TEST_MESSAGES = [
    "Hello, how are you?",
    "Send an email to john@example.com about the meeting tomorrow",
    "What is the capital of France?",
    "Can you help me search for restaurants near me?",
    "Create a todo list for my project",
    "Explain how photosynthesis works"
]

async def test_http_endpoints():
    """Test the HTTP endpoints"""
    print("🌐 Testing HTTP Endpoints...")
    print("=" * 50)
    
    async with httpx.AsyncClient() as client:
        # Test health check
        try:
            response = await client.get(f"{HTTP_BASE_URL}/health")
            if response.status_code == 200:
                print("✅ Health check passed")
                health_data = response.json()
                print(f"   Status: {health_data['status']}")
                print(f"   Message: {health_data['message']}")
                if health_data.get('agent_address'):
                    print(f"   Agent Address: {health_data['agent_address']}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Health check error: {e}")
        
        print()
        
        # Test available models
        try:
            response = await client.get(f"{HTTP_BASE_URL}/models")
            if response.status_code == 200:
                print("✅ Models endpoint working")
                models_data = response.json()
                print(f"   Regular models: {models_data['regular_models']}")
                print(f"   Agentic models: {models_data['agentic_models']}")
            else:
                print(f"❌ Models endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Models endpoint error: {e}")
        
        print()
        
        # Test agent config
        try:
            response = await client.get(f"{HTTP_BASE_URL}/agent-config")
            if response.status_code == 200:
                print("✅ Agent config endpoint working")
                config_data = response.json()
                print(f"   Available categories: {list(config_data['agent_categories'].keys())}")
            else:
                print(f"❌ Agent config endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Agent config endpoint error: {e}")
        
        print()
        
        # Test chat endpoint with various messages
        print("💬 Testing Chat Endpoint...")
        for i, message in enumerate(TEST_MESSAGES, 1):
            print(f"\nTest {i}: {message}")
            try:
                response = await client.post(
                    f"{HTTP_BASE_URL}/chat",
                    json={
                        "message": message,
                        "conversation_id": f"test_conversation_{i}"
                    }
                )
                
                if response.status_code == 200:
                    print("✅ Chat request successful")
                    chat_data = response.json()
                    print(f"   Model used: {chat_data['model_used']}")
                    print(f"   Response: {chat_data['response'][:100]}...")
                    
                    if chat_data.get('agent_routing'):
                        routing = chat_data['agent_routing']
                        print(f"   🎯 Agent routing: {routing['matched_agent']} (confidence: {routing['confidence']:.1%})")
                    
                    if chat_data.get('complexity_analysis'):
                        analysis = chat_data['complexity_analysis']
                        print(f"   🧠 Complexity: {'Agentic' if analysis['needs_agentic'] else 'Regular'} (confidence: {analysis['confidence']:.1%})")
                else:
                    print(f"❌ Chat request failed: {response.status_code}")
                    print(f"   Error: {response.text}")
            except Exception as e:
                print(f"❌ Chat request error: {e}")
        
        print()
        
        # Test analysis endpoint
        print("🔍 Testing Analysis Endpoint...")
        test_message = "Send an email to my friend about the project update"
        try:
            response = await client.post(
                f"{HTTP_BASE_URL}/analyze",
                json={"message": test_message}
            )
            
            if response.status_code == 200:
                print("✅ Analysis request successful")
                analysis_data = response.json()
                
                if analysis_data.get('agent_routing'):
                    routing = analysis_data['agent_routing']
                    print(f"   🎯 Agent routing: {routing.get('matched_agent', 'None')} (confidence: {routing.get('confidence', 0):.1%})")
                
                if analysis_data.get('complexity_analysis'):
                    complexity = analysis_data['complexity_analysis']
                    print(f"   🧠 Complexity: {'Agentic' if complexity.get('needs_agentic') else 'Regular'} (confidence: {complexity.get('confidence', 0):.1%})")
            else:
                print(f"❌ Analysis request failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Analysis request error: {e}")

def test_intelligent_handler():
    """Test the intelligent handler directly"""
    print("🧠 Testing Intelligent Handler Directly...")
    print("=" * 50)
    
    for i, message in enumerate(TEST_MESSAGES, 1):
        print(f"\nTest {i}: {message}")
        try:
            result = intelligent_handler.get_intelligent_response(message)
            
            if result["success"]:
                print("✅ Handler response successful")
                print(f"   Model used: {result['model_used']}")
                print(f"   Response: {result['response'][:100]}...")
                
                if result.get('agent_routing'):
                    routing = result['agent_routing']
                    print(f"   🎯 Agent routing: {routing['matched_agent']} (confidence: {routing['confidence']:.1%})")
                
                if result.get('complexity_analysis'):
                    analysis = result['complexity_analysis']
                    print(f"   🧠 Complexity: {'Agentic' if analysis['needs_agentic'] else 'Regular'} (confidence: {analysis['confidence']:.1%})")
            else:
                print(f"❌ Handler response failed: {result['error_message']}")
        except Exception as e:
            print(f"❌ Handler error: {e}")

async def main():
    """Main test function"""
    print("🧪 Intelligent Mailbox Agent Test Suite")
    print("=" * 60)
    
    # Check environment
    if not os.getenv('ASI_ONE_API_KEY'):
        print("❌ ASI_ONE_API_KEY environment variable not set")
        print("Please set your API key: export ASI_ONE_API_KEY='your_key_here'")
        return
    
    print("✅ Environment check passed")
    print()
    
    # Test intelligent handler directly
    test_intelligent_handler()
    
    print("\n" + "=" * 60)
    
    # Test HTTP endpoints (if server is running)
    print("🌐 Testing HTTP endpoints (make sure server is running)...")
    try:
        await test_http_endpoints()
    except Exception as e:
        print(f"❌ HTTP endpoint tests failed: {e}")
        print("💡 Make sure the HTTP server is running: python run_with_http.py")
    
    print("\n" + "=" * 60)
    print("🎉 Test suite completed!")

if __name__ == "__main__":
    asyncio.run(main())
