#!/usr/bin/env python3
"""
Debug script for ASI:One API issues
"""

import os
import sys
import json
import requests
from typing import Dict, Any

def test_asi_api():
    """Test the ASI:One API with a simple request"""
    
    # Get API key
    api_key = os.getenv('ASI_ONE_API_KEY')
    if not api_key:
        print("❌ ASI_ONE_API_KEY not set")
        return
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    # Test basic request
    url = "https://api.asi1.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Simple test payload
    payload = {
        "model": "asi1-mini",
        "messages": [
            {"role": "user", "content": "Hello, this is a test message."}
        ],
        "stream": False
    }
    
    print("🔍 Testing API request...")
    print(f"URL: {url}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ API request successful!")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception during API request: {e}")

def test_agentic_model():
    """Test with an agentic model"""
    
    api_key = os.getenv('ASI_ONE_API_KEY')
    if not api_key:
        print("❌ ASI_ONE_API_KEY not set")
        return
    
    url = "https://api.asi1.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test with agentic model
    payload = {
        "model": "asi1-fast-agentic",
        "messages": [
            {"role": "user", "content": "Hello, this is a test message."}
        ],
        "stream": False
    }
    
    print("\n🔍 Testing agentic model...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Agentic model request successful!")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ Agentic model request failed: {response.status_code}")
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception during agentic model request: {e}")

if __name__ == "__main__":
    print("🧪 ASI:One API Debug Test")
    print("=" * 50)
    
    test_asi_api()
    test_agentic_model()
