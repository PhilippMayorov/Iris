#!/usr/bin/env python3
"""
Save Discord OAuth2 Tokens

This script saves OAuth2 tokens obtained from the test flow to the Discord agent's
secure token storage system. This allows the agent to authenticate users without 
requiring them to go through the OAuth flow again.
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import sys

# Add the current directory to the path so we can import the agent modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from discord_agent import DiscordAuthManager

# Load environment variables
load_dotenv()

async def save_tokens_from_test_results():
    """Save tokens from the successful OAuth2 test flow"""
    
    print("=" * 60)
    print("🔐 SAVING DISCORD OAUTH2 TOKENS")
    print("=" * 60)
    
    # Get the tokens from your test results
    # You'll need to replace these with the actual tokens from your test output
    print("📝 Please enter the tokens from your successful OAuth2 test:")
    print()
    
    # Interactive token input
    access_token = input("🔑 Enter Access Token (starts with MTQyNjgxNzM3OTcwMjI4...): ").strip()
    if not access_token:
        print("❌ Access token is required!")
        return False
    
    refresh_token = input("🔄 Enter Refresh Token (starts with oISGBOWKrAJIMHkLXLoZ...): ").strip()
    if not refresh_token:
        print("❌ Refresh token is required!")
        return False
    
    # Based on your test results
    token_type = "Bearer"
    expires_in = 604800  # 7 days in seconds
    scope = "guilds identify"
    
    # Create token data structure matching Discord's response format
    token_data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": token_type,
        "expires_in": expires_in,
        "scope": scope,
        "timestamp": datetime.now().isoformat()  # For our records
    }
    
    print("\n🔧 Token data prepared:")
    print(f"   Token Type: {token_type}")
    print(f"   Expires In: {expires_in} seconds ({expires_in // 3600} hours)")
    print(f"   Scope: {scope}")
    print(f"   Access Token: {access_token[:20]}...")
    print(f"   Refresh Token: {refresh_token[:20]}...")
    
    # Initialize the auth manager
    auth_manager = DiscordAuthManager()
    
    try:
        print("\n💾 Saving tokens to encrypted storage...")
        await auth_manager.save_tokens(token_data)
        print("✅ Tokens saved successfully!")
        
        # Verify the tokens were saved correctly
        print("\n🔍 Verifying saved tokens...")
        if await auth_manager.load_tokens():
            print("✅ Tokens loaded successfully from storage!")
            
            # Test token validity
            print("\n🧪 Testing token validity...")
            valid_token = await auth_manager.get_valid_token()
            if valid_token:
                print("✅ Token is valid and ready to use!")
                print(f"   Valid Token: {valid_token[:20]}...")
                
                # Test with Discord API to verify it works
                print("\n👤 Testing with Discord API...")
                import aiohttp
                
                headers = {
                    'Authorization': f'Bearer {valid_token}',
                    'User-Agent': 'VocalAgent Discord Bot'
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get('https://discord.com/api/v10/users/@me', headers=headers) as resp:
                        if resp.status == 200:
                            user_data = await resp.json()
                            username = user_data.get('username', 'Unknown')
                            discriminator = user_data.get('discriminator', '0')
                            print(f"✅ API test successful! Authenticated as: {username}#{discriminator}")
                            
                            return True
                        else:
                            print(f"⚠️  API test failed: {resp.status}")
                            print(f"   Response: {await resp.text()}")
                            return False
            else:
                print("❌ Token validation failed!")
                return False
        else:
            print("❌ Failed to load saved tokens!")
            return False
            
    except Exception as e:
        print(f"❌ Error saving tokens: {e}")
        return False

async def main():
    """Main function"""
    print("This script will save the Discord OAuth2 tokens from your successful test")
    print("to the Discord agent's secure storage system.\n")
    
    try:
        success = await save_tokens_from_test_results()
        
        print("\n" + "=" * 60)
        if success:
            print("🎉 TOKENS SAVED SUCCESSFULLY!")
            print("   Your Discord agent can now authenticate automatically!")
            print("   You can now start the discord_agent.py and it will use these tokens.")
            print("\n🚀 Next steps:")
            print("   1. Run: python discord_agent.py")
            print("   2. Test messaging with the agent")
            print("   3. The agent will automatically use your saved authentication")
        else:
            print("❌ TOKEN SAVING FAILED!")
            print("   Please check the errors above and try again.")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main())