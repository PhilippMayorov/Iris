#!/usr/bin/env python3
"""
Test script for Spotify integration in the frontend
This script tests the Spotify authentication endpoints
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_spotify_auth_endpoint():
    """Test the Spotify authentication endpoint"""
    print("🧪 Testing Spotify Authentication Endpoint...")
    
    try:
        # Test the auth endpoint
        response = requests.get('http://localhost:5001/api/spotify/auth')
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Spotify auth endpoint working correctly!")
                print(f"Auth URL: {data.get('auth_url', 'N/A')}")
                return True
            else:
                print(f"❌ Auth endpoint returned error: {data.get('error')}")
                return False
        else:
            print(f"❌ Auth endpoint failed with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Flask server. Make sure it's running on port 5001")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def test_environment_variables():
    """Test if required environment variables are set"""
    print("\n🔧 Checking Environment Variables...")
    
    required_vars = ['SPOTIFY_CLIENT_ID', 'SPOTIFY_CLIENT_SECRET', 'SPOTIFY_REDIRECT_URI']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * 10}...{value[-4:] if len(value) > 4 else '****'}")
        else:
            print(f"❌ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("Please add these to your .env file:")
        for var in missing_vars:
            print(f"   {var}=your_value_here")
        return False
    else:
        print("\n✅ All required environment variables are set!")
        return True

def test_health_endpoint():
    """Test the health endpoint to ensure Flask is running"""
    print("\n🏥 Testing Health Endpoint...")
    
    try:
        response = requests.get('http://localhost:5001/api/health')
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data.get('message')}")
            return True
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Flask server. Make sure it's running on port 5001")
        return False
    except Exception as e:
        print(f"❌ Health check failed with error: {e}")
        return False

def main():
    """Run all tests"""
    print("🎵 Spotify Integration Test Suite")
    print("=" * 50)
    
    # Test 1: Environment variables
    env_ok = test_environment_variables()
    
    # Test 2: Health endpoint
    health_ok = test_health_endpoint()
    
    # Test 3: Spotify auth endpoint (only if env vars are set)
    auth_ok = False
    if env_ok and health_ok:
        auth_ok = test_spotify_auth_endpoint()
    else:
        print("\n⏭️  Skipping auth endpoint test due to missing requirements")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   Environment Variables: {'✅ PASS' if env_ok else '❌ FAIL'}")
    print(f"   Health Endpoint: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"   Spotify Auth Endpoint: {'✅ PASS' if auth_ok else '❌ FAIL'}")
    
    if env_ok and health_ok and auth_ok:
        print("\n🎉 All tests passed! Spotify integration is ready to use.")
        print("\nNext steps:")
        print("1. Start the frontend: python app.py")
        print("2. Open http://localhost:5001 in your browser")
        print("3. Click 'Integrate with apps' → 'Spotify'")
        print("4. Complete the OAuth flow")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above before using Spotify integration.")

if __name__ == "__main__":
    main()
