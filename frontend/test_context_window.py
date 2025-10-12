#!/usr/bin/env python3
"""
Test script for the Gemini agent context window functionality
"""

import requests
import json
import time

# Base URL for the frontend API
BASE_URL = "http://127.0.0.1:5001"

def test_context_endpoints():
    """Test the context management endpoints"""
    print("🧪 Testing Context Window Functionality")
    print("=" * 50)
    
    # Test 1: Start a new session
    print("\n1. Starting new chat session...")
    response = requests.post(f"{BASE_URL}/api/context/start-session", 
                           json={"session_id": "test_session_123"})
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Session started: {data['session_id']}")
        session_id = data['session_id']
    else:
        print(f"❌ Failed to start session: {response.text}")
        return
    
    # Test 2: Check context status
    print("\n2. Checking context status...")
    response = requests.get(f"{BASE_URL}/api/context/status")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Context status: {json.dumps(data['context'], indent=2)}")
    else:
        print(f"❌ Failed to get context status: {response.text}")
    
    # Test 3: Send some test messages to build context
    print("\n3. Building conversation context...")
    
    test_messages = [
        "Hello, my name is John and I love rock music",
        "What's the weather like today?",
        "Can you help me find some good rock songs?",
        "I'm working on a project about AI"
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n   Sending message {i}: '{message}'")
        
        response = requests.post(f"{BASE_URL}/api/gemini-direct-response", 
                               json={"voice_input": message})
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Response: {data['gemini_response'][:100]}...")
        else:
            print(f"   ❌ Failed: {response.text}")
        
        # Small delay between messages
        time.sleep(1)
    
    # Test 4: Check context history
    print("\n4. Checking context history...")
    response = requests.get(f"{BASE_URL}/api/context/history")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Context history ({data['count']} interactions):")
        for i, interaction in enumerate(data['history'], 1):
            print(f"   {i}. [{interaction['type']}] User: {interaction['user_input'][:50]}...")
            print(f"      Assistant: {interaction['assistant_response'][:50]}...")
    else:
        print(f"❌ Failed to get context history: {response.text}")
    
    # Test 5: Test context-aware response
    print("\n5. Testing context-aware response...")
    context_message = "What was my name again?"
    
    response = requests.post(f"{BASE_URL}/api/gemini-direct-response", 
                           json={"voice_input": context_message})
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Context-aware response: {data['gemini_response']}")
    else:
        print(f"❌ Failed: {response.text}")
    
    # Test 6: Update user preferences
    print("\n6. Testing user preferences...")
    preferences = {
        "music_genre": "rock",
        "name": "John",
        "interests": ["AI", "music", "technology"]
    }
    
    response = requests.post(f"{BASE_URL}/api/context/preferences", 
                           json={"preferences": preferences})
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Preferences updated: {json.dumps(data['preferences'], indent=2)}")
    else:
        print(f"❌ Failed to update preferences: {response.text}")
    
    # Test 7: Get preferences
    print("\n7. Getting user preferences...")
    response = requests.get(f"{BASE_URL}/api/context/preferences")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Current preferences: {json.dumps(data['preferences'], indent=2)}")
    else:
        print(f"❌ Failed to get preferences: {response.text}")
    
    # Test 8: Clear context
    print("\n8. Testing context clearing...")
    response = requests.post(f"{BASE_URL}/api/context/clear")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Context cleared: {data['message']}")
    else:
        print(f"❌ Failed to clear context: {response.text}")
    
    # Test 9: Verify context is cleared
    print("\n9. Verifying context is cleared...")
    response = requests.get(f"{BASE_URL}/api/context/status")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Context after clearing: {json.dumps(data['context'], indent=2)}")
    else:
        print(f"❌ Failed to get context status: {response.text}")
    
    print("\n🎉 Context window testing completed!")

def test_music_context():
    """Test context with music requests"""
    print("\n🎵 Testing Music Context Functionality")
    print("=" * 50)
    
    # Start a new session
    requests.post(f"{BASE_URL}/api/context/start-session")
    
    # Build music context
    music_messages = [
        "I love listening to rock music",
        "My favorite band is Led Zeppelin",
        "Can you find me some classic rock songs?"
    ]
    
    for message in music_messages:
        print(f"\nSending: '{message}'")
        response = requests.post(f"{BASE_URL}/api/gemini-direct-response", 
                               json={"voice_input": message})
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data['gemini_response'][:100]}...")
        time.sleep(1)
    
    # Test context-aware music request
    print("\nTesting context-aware music request...")
    context_music_message = "Find me more songs like the ones I mentioned"
    
    response = requests.post(f"{BASE_URL}/api/gemini-direct-response", 
                           json={"voice_input": context_music_message})
    
    if response.status_code == 200:
        data = response.json()
        print(f"Context-aware music response: {data['gemini_response']}")
    else:
        print(f"Failed: {response.text}")

if __name__ == "__main__":
    try:
        # Test basic context functionality
        test_context_endpoints()
        
        # Test music-specific context
        test_music_context()
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the frontend server.")
        print("Make sure the frontend is running on http://127.0.0.1:5001")
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
