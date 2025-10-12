#!/usr/bin/env python3
"""
Test script for Spotify authentication endpoints
Demonstrates how to use the new Spotify auth endpoints in the Flask app
"""

import requests
import json
import time

# Flask app base URL
BASE_URL = "http://127.0.0.1:8888"

def test_spotify_auth_status():
    """Test the Spotify authentication status endpoint"""
    print("🔍 Testing Spotify authentication status...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/spotify/auth-status")
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if data.get('success') and data.get('authenticated'):
            print("✅ User is authenticated with Spotify!")
            return True
        else:
            print("❌ User is not authenticated with Spotify")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Flask app. Make sure it's running on port 8888")
        return False
    except Exception as e:
        print(f"❌ Error testing auth status: {e}")
        return False

def test_spotify_auth_initiate():
    """Test initiating Spotify authentication"""
    print("\n🎵 Testing Spotify authentication initiation...")
    
    try:
        response = requests.post(f"{BASE_URL}/api/spotify/auth")
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if data.get('success') and data.get('auth_url'):
            print("✅ Authentication URL generated successfully!")
            print(f"🔗 Auth URL: {data['auth_url']}")
            print("\n📝 To complete authentication:")
            print("1. Open the auth_url in your browser")
            print("2. Log in to Spotify and authorize the app")
            print("3. You'll be redirected to the callback URL")
            return data['auth_url']
        else:
            print("❌ Failed to generate authentication URL")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Flask app. Make sure it's running on port 8888")
        return None
    except Exception as e:
        print(f"❌ Error initiating auth: {e}")
        return None

def test_health_endpoint():
    """Test the health endpoint to ensure Flask app is running"""
    print("🏥 Testing health endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if data.get('status') == 'healthy':
            print("✅ Flask app is running and healthy!")
            return True
        else:
            print("❌ Flask app health check failed")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Flask app. Make sure it's running on port 8888")
        return False
    except Exception as e:
        print(f"❌ Error testing health: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing Spotify Authentication Endpoints")
    print("=" * 50)
    
    # Test health first
    if not test_health_endpoint():
        print("\n❌ Flask app is not running. Please start it first:")
        print("   cd frontend && python app.py")
        return
    
    # Test auth status
    is_authenticated = test_spotify_auth_status()
    
    # If not authenticated, test auth initiation
    if not is_authenticated:
        auth_url = test_spotify_auth_initiate()
        
        if auth_url:
            print(f"\n⏳ Waiting for authentication...")
            print("After completing authentication in your browser, press Enter to check status...")
            input()
            
            # Check auth status again
            test_spotify_auth_status()
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    main()
