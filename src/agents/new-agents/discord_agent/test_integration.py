#!/usr/bin/env python3
"""
Integration Test - OAuth Flow to Discord Agent Token Usage

This script tests the complete workflow:
1. Run OAuth flow and save tokens (simulating test_complete_oauth_flow.py)
2. Start discord_agent and verify it automatically loads and uses saved tokens
3. Test automatic token refresh functionality
"""

import os
import asyncio
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from cryptography.fernet import Fernet

# Load environment variables
load_dotenv()

# Import Discord agent components
from discord_agent import DiscordAuthManager, DiscordAPIClient

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())

async def test_token_persistence():
    """Test that tokens are saved and loaded correctly"""
    print("=" * 70)
    print("🧪 TESTING TOKEN PERSISTENCE INTEGRATION")
    print("=" * 70)
    
    # Initialize auth manager
    auth_manager = DiscordAuthManager()
    
    # Test 1: Check if tokens already exist
    print("\n📁 Checking for existing tokens...")
    if await auth_manager.load_tokens():
        print("✅ Existing tokens found and loaded")
        print(f"   Access Token: {auth_manager.access_token[:20] if auth_manager.access_token else 'None'}...")
        print(f"   Refresh Token: {auth_manager.refresh_token[:20] if auth_manager.refresh_token else 'None'}...")
        print(f"   Expires At: {auth_manager.token_expires_at}")
        
        # Test 2: Validate token
        print("\n🔍 Validating token...")
        valid_token = await auth_manager.get_valid_token()
        if valid_token:
            print("✅ Token is valid (or was successfully refreshed)")
            
            # Test 3: Try to use the token with Discord API
            print("\n🌐 Testing Discord API access...")
            discord_client = DiscordAPIClient(auth_manager)
            try:
                user_info = await discord_client.get_current_user()
                username = user_info.get('username', 'Unknown')
                discriminator = user_info.get('discriminator', '0000')
                print(f"✅ Successfully authenticated as: {username}#{discriminator}")
                print("🎉 Integration test PASSED!")
                return True
            except Exception as e:
                print(f"❌ Discord API test failed: {e}")
                return False
        else:
            print("❌ Token validation failed")
            return False
    else:
        print("ℹ️  No existing tokens found")
        print("💡 Run test_complete_oauth_flow.py first to authenticate")
        return False

async def test_token_refresh_simulation():
    """Simulate token expiry and test refresh functionality"""
    print("\n" + "=" * 70)
    print("🔄 TESTING TOKEN REFRESH SIMULATION")
    print("=" * 70)
    
    auth_manager = DiscordAuthManager()
    
    # Load existing tokens
    if not await auth_manager.load_tokens():
        print("❌ No tokens to test refresh with")
        return False
    
    print("📅 Simulating token expiry...")
    # Simulate expired token by setting expiry to past
    auth_manager.token_expires_at = datetime.now() - timedelta(minutes=10)
    print(f"   Set token expiry to: {auth_manager.token_expires_at}")
    
    print("\n🔄 Testing automatic refresh...")
    valid_token = await auth_manager.get_valid_token()
    
    if valid_token:
        print("✅ Token refresh successful!")
        print(f"   New expiry: {auth_manager.token_expires_at}")
        return True
    else:
        print("❌ Token refresh failed")
        return False

async def display_token_info():
    """Display current token information"""
    print("\n" + "=" * 70)
    print("📊 CURRENT TOKEN STATUS")
    print("=" * 70)
    
    token_file = "discord_tokens.enc"
    if not os.path.exists(token_file):
        print("❌ No token file found")
        return
    
    try:
        cipher = Fernet(ENCRYPTION_KEY.encode())
        with open(token_file, 'rb') as f:
            encrypted_data = f.read()
        
        decrypted_data = cipher.decrypt(encrypted_data)
        token_data = json.loads(decrypted_data.decode())
        
        print(f"📝 Token Type: {token_data.get('token_type', 'Unknown')}")
        print(f"🔑 Access Token: {token_data.get('access_token', '')[:20]}...")
        print(f"🔄 Refresh Token: {token_data.get('refresh_token', '')[:20] if token_data.get('refresh_token') else 'None'}...")
        print(f"⏰ Expires In: {token_data.get('expires_in', 'Unknown')} seconds")
        print(f"🏷️  Scope: {token_data.get('scope', 'Unknown')}")
        
        if 'saved_at' in token_data:
            saved_at = datetime.fromisoformat(token_data['saved_at'])
            print(f"💾 Saved At: {saved_at}")
        
        if 'expires_at' in token_data:
            expires_at = datetime.fromisoformat(token_data['expires_at'])
            now = datetime.now()
            if expires_at > now:
                time_left = expires_at - now
                print(f"✅ Expires At: {expires_at} ({time_left} remaining)")
            else:
                print(f"⚠️  Expired At: {expires_at}")
        
    except Exception as e:
        print(f"❌ Error reading token data: {e}")

async def main():
    """Run all integration tests"""
    print("🚀 Discord Agent Integration Tests")
    print("Testing OAuth → Token Storage → Agent Usage workflow")
    
    # Display current token status
    await display_token_info()
    
    # Test token persistence
    persistence_result = await test_token_persistence()
    
    # Test token refresh if persistence worked
    if persistence_result:
        refresh_result = await test_token_refresh_simulation()
    else:
        refresh_result = False
    
    print("\n" + "=" * 70)
    print("📊 INTEGRATION TEST RESULTS")
    print("=" * 70)
    print(f"Token Persistence: {'✅ PASS' if persistence_result else '❌ FAIL'}")
    print(f"Token Refresh: {'✅ PASS' if refresh_result else '❌ FAIL'}")
    
    if persistence_result and refresh_result:
        print("\n🎉 ALL TESTS PASSED!")
        print("The discord_agent is ready to use your saved Discord authentication.")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("You may need to run the OAuth flow again or check your configuration.")
    
    return persistence_result and refresh_result

if __name__ == "__main__":
    asyncio.run(main())