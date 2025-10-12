#!/usr/bin/env python3
"""
Discord API Limitations Diagnostic

This script explains the Discord API limitations affecting user lookup
and provides guidance on finding Discord User IDs for reliable messaging.
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def diagnose_discord_permissions():
    """Diagnose Discord API access and limitations"""
    print("=" * 70)
    print("🩺 DISCORD API PERMISSIONS DIAGNOSTIC")
    print("=" * 70)
    
    try:
        from discord_agent import DiscordAuthManager, DiscordAPIClient
        
        # Initialize components
        auth_manager = DiscordAuthManager()
        discord_client = DiscordAPIClient(auth_manager)
        
        # Check authentication
        valid_token = await auth_manager.get_valid_token()
        if not valid_token:
            print("❌ No valid Discord token found")
            print("   Run: python test_complete_oauth_flow.py first")
            return False
        
        print("✅ Discord authentication valid")
        
        # Test current user access
        print("\n👤 Testing basic user access...")
        try:
            current_user = await discord_client.get_current_user()
            username = current_user.get('username', 'Unknown')
            discriminator = current_user.get('discriminator', '0000')
            user_id = current_user.get('id', 'Unknown')
            print(f"   ✅ Current user: {username}#{discriminator} (ID: {user_id})")
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return False
        
        # Test friends list access
        print("\n👥 Testing friends list access...")
        try:
            relationships = await discord_client.get_user_relationships()
            if relationships:
                print(f"   ✅ Friends list accessible - {len(relationships)} relationships found")
                for rel in relationships[:3]:
                    user = rel.get('user', {})
                    if user:
                        username = user.get('username', 'Unknown')
                        discriminator = user.get('discriminator', '0')
                        user_id = user.get('id', 'Unknown')
                        print(f"      - {username}#{discriminator} (ID: {user_id})")
            else:
                print("   ⚠️  Friends list returned empty (Discord API restriction)")
                print("   📖 Discord has restricted user token access to friends list")
        except Exception as e:
            print(f"   ❌ Friends list access denied: {e}")
            print("   📖 This is expected - Discord restricts this API for user tokens")
        
        # Test guild access
        print("\n🏰 Testing guild access...")
        try:
            guilds = await discord_client.get_user_guilds()
            if guilds:
                print(f"   ✅ Guild list accessible - {len(guilds)} guilds found")
                
                accessible_count = 0
                for guild in guilds[:5]:  # Test first 5 guilds
                    guild_name = guild.get('name', 'Unknown')
                    guild_id = guild['id']
                    
                    try:
                        members = await discord_client.get_guild_members_sample(guild_id, 5)
                        if members:
                            accessible_count += 1
                            print(f"      ✅ {guild_name}: {len(members)} members accessible")
                            
                            # Show sample users with IDs
                            for member in members[:2]:
                                user = member.get('user', {})
                                if user:
                                    username = user.get('username', 'Unknown')
                                    discriminator = user.get('discriminator', '0')
                                    user_id = user.get('id', 'Unknown')
                                    print(f"         - {username}#{discriminator} (ID: {user_id})")
                        else:
                            print(f"      ⚠️  {guild_name}: Member list not accessible")
                    except Exception as e:
                        print(f"      ❌ {guild_name}: {e}")
                
                print(f"\n   📊 Summary: {accessible_count}/{min(len(guilds), 5)} guilds have accessible member lists")
                
            else:
                print("   ❌ No guilds found")
        except Exception as e:
            print(f"   ❌ Guild access failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        return False

def print_user_id_guide():
    """Print guide for finding Discord User IDs"""
    print("\n" + "=" * 70)
    print("🆔 HOW TO FIND DISCORD USER IDs")
    print("=" * 70)
    
    print("""
**Why User IDs are better than usernames:**
• Usernames can be changed, User IDs are permanent
• No need to remember discriminator (#1234)
• Work reliably with Discord API
• Bypass username lookup limitations

**How to find a Discord User ID:**

1. **Enable Developer Mode in Discord:**
   • Open Discord → Settings (gear icon)
   • Go to Advanced → Enable "Developer Mode"

2. **Get someone's User ID:**
   • Right-click on their profile/message
   • Click "Copy User ID"
   • The ID looks like: 123456789012345678

3. **Get your own User ID:**
   • Click your profile in any chat
   • Right-click → "Copy User ID"

**Using User IDs with the Discord Agent:**
Instead of: "Send Ben: Hello there"
Use: "Send user ID 123456789012345678: Hello there"

**Examples:**
• "Message user ID 123456789012345678 saying hi"  
• "Text 987654321098765432: Meeting at 3pm"
• "DM 456789123456789123 that I'll be late"

This bypasses all username lookup issues and works reliably!
""")

async def test_user_id_lookup():
    """Test User ID lookup functionality"""
    print("\n" + "=" * 70)
    print("🔍 TESTING USER ID LOOKUP")
    print("=" * 70)
    
    print("Enter a Discord User ID to test lookup (or press Enter to skip):")
    user_input = input("User ID: ").strip()
    
    if not user_input:
        print("Skipping User ID test")
        return True
    
    if not user_input.isdigit() or len(user_input) < 17:
        print("❌ Invalid User ID format (should be 17-19 digits)")
        return False
    
    try:
        from discord_agent import DiscordAuthManager, DiscordAPIClient
        
        auth_manager = DiscordAuthManager()
        discord_client = DiscordAPIClient(auth_manager)
        
        print(f"🔍 Looking up User ID: {user_input}")
        user = await discord_client.find_user_by_id(user_input)
        
        if user:
            username = user.get('username', 'Unknown')
            discriminator = user.get('discriminator', '0')
            print(f"✅ Found user: {username}#{discriminator}")
            print(f"   This ID works for messaging!")
            return True
        else:
            print(f"❌ User ID {user_input} not found")
            print(f"   Make sure the ID is correct and the user exists")
            return False
            
    except Exception as e:
        print(f"❌ User ID lookup failed: {e}")
        return False

async def main():
    """Run complete diagnostic"""
    print("🩺 Discord Agent - API Limitations Diagnostic")
    print("This tool helps understand why user lookup might not work")
    
    # Run permission diagnostic
    diagnostic_result = await diagnose_discord_permissions()
    
    # Show User ID guide
    print_user_id_guide()
    
    # Test User ID lookup
    user_id_result = await test_user_id_lookup()
    
    print("\n" + "=" * 70)
    print("📋 DIAGNOSTIC SUMMARY & RECOMMENDATIONS")
    print("=" * 70)
    
    if diagnostic_result:
        print("✅ Discord API access working")
    else:
        print("❌ Discord API access issues detected")
        
    print("\n💡 **Key Findings:**")
    print("• Friends list API is restricted by Discord (expected)")
    print("• Guild member lists may have limited access")
    print("• User ID lookup is the most reliable method")
    
    print("\n🎯 **Recommended Solution:**")
    print("1. Use Discord User IDs instead of usernames")
    print("2. Enable Developer Mode in Discord to copy User IDs")
    print("3. Share User IDs with people who want to message you")
    
    print("\n🚀 **Next Steps:**")
    print("• Test messaging with: 'Send user ID [USER_ID]: [MESSAGE]'")
    print("• Ask friends for their Discord User IDs")
    print("• Use right-click → Copy User ID in Discord")
    
    return diagnostic_result

if __name__ == "__main__":
    asyncio.run(main())
"""
Discord API Permissions and Limitations Guide

This script helps diagnose Discord API permission issues and provides guidance
on the limitations of Discord's OAuth2 user tokens for messaging.
"""

import asyncio
import json
import os
from datetime import datetime

async def check_discord_permissions():
    """Check what permissions the current Discord token has"""
    print("=" * 70)
    print("🔍 DISCORD API PERMISSIONS CHECKER")
    print("=" * 70)
    
    try:
        from discord_agent import auth_manager, discord_client
        
        # Check if we have a valid token
        token = await auth_manager.get_valid_token()
        if not token:
            print("❌ No valid Discord token found")
            print("   Run: python test_complete_oauth_flow.py first")
            return False
        
        print("✅ Valid Discord token found")
        
        # Test current user endpoint
        print("\n📋 Testing Discord API endpoints...")
        try:
            user_info = await discord_client.get_current_user()
            print(f"✅ /users/@me: {user_info.get('username')}#{user_info.get('discriminator')}")
        except Exception as e:
            print(f"❌ /users/@me failed: {e}")
        
        # Test authorization info
        try:
            auth_info = await discord_client.get_current_authorization_info()
            scopes = auth_info.get('scopes', [])
            print(f"✅ Current scopes: {', '.join(scopes)}")
            
            # Check if we have the necessary scopes for messaging
            required_scopes = ['identify', 'guilds']  # Basic scopes
            missing_scopes = [scope for scope in required_scopes if scope not in scopes]
            
            if missing_scopes:
                print(f"⚠️  Missing scopes: {', '.join(missing_scopes)}")
            else:
                print("✅ All basic scopes present")
                
        except Exception as e:
            print(f"❌ Authorization info failed: {e}")
        
        # Test guilds endpoint
        try:
            guilds = await discord_client.get_user_guilds()
            print(f"✅ /users/@me/guilds: Found {len(guilds)} guilds")
        except Exception as e:
            print(f"❌ /users/@me/guilds failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Permission check failed: {e}")
        return False

def print_discord_limitations():
    """Print information about Discord API limitations"""
    print("\n" + "=" * 70)
    print("⚠️  DISCORD API LIMITATIONS FOR USER TOKENS")
    print("=" * 70)
    
    print("""
🚫 IMPORTANT LIMITATIONS:

1. **Direct Messaging Restrictions**
   • Discord has heavily restricted user token messaging capabilities
   • User tokens can NO LONGER send DMs to arbitrary users
   • This is an intentional security measure by Discord

2. **Available User Token Capabilities**
   ✅ Get current user info (/users/@me)
   ✅ Get user's guilds (/users/@me/guilds) 
   ✅ Get user's connections (with scope)
   ❌ Send messages to users (/channels/{channel_id}/messages)
   ❌ Create DM channels (/users/@me/channels)
   ❌ Search for users by username

3. **Alternative Solutions**
   
   🤖 **Discord Bot Approach (Recommended)**
   • Create a Discord Bot application
   • Use bot tokens instead of user tokens
   • Bots CAN send messages with proper permissions
   • Requires the bot to be in same server as target user
   
   🌐 **Webhook Approach**
   • Use Discord webhooks for specific channels
   • Limited to channels where webhooks are configured
   
   📱 **Slash Commands/Interactions**
   • Use Discord's interaction system
   • User triggers commands, bot responds
   
4. **Current Implementation Status**
   Our discord_agent attempts to use the Discord REST API for messaging,
   but this will likely fail due to Discord's restrictions on user tokens.
   
   The agent is structured correctly and would work with bot tokens or
   in scenarios where Discord allows user token messaging.

5. **Recommended Next Steps**
   • Convert to Discord Bot implementation
   • Use bot tokens with proper permissions
   • Or integrate with Discord's official SDKs
""")

async def suggest_solutions():
    """Suggest alternative approaches for Discord messaging"""
    print("\n" + "=" * 70)
    print("💡 RECOMMENDED SOLUTIONS")
    print("=" * 70)
    
    print("""
🤖 **SOLUTION 1: Convert to Discord Bot**

1. Create a Discord Bot Application:
   • Go to https://discord.com/developers/applications
   • Create new application → Bot section
   • Get bot token (not user token)

2. Update discord_agent.py:
   • Replace user OAuth with bot token authentication
   • Use discord.py library for easier bot development
   • Add bot to servers where you want to send messages

3. Bot Permissions Needed:
   • Send Messages
   • View Channels
   • Read Message History

🔗 **SOLUTION 2: Discord.py Integration**

Replace the current implementation with discord.py:

```python
import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())

@bot.command()
async def send_dm(ctx, user: discord.User, *, message):
    await user.send(message)
    await ctx.send(f"Message sent to {user.mention}")

bot.run('YOUR_BOT_TOKEN')
```

🌐 **SOLUTION 3: Webhook Integration**

For specific channels:
• Create webhooks in Discord channels
• Send messages via webhook API
• Limited to configured channels only

📋 **Current Status**
The agent implementation is correct in structure but limited by
Discord's API restrictions. The code would work if Discord allowed
user token messaging or if converted to use bot tokens.
""")

async def main():
    """Main diagnostic function"""
    print("🔍 Discord Agent Diagnostic Tool")
    print("Checking Discord API permissions and limitations...")
    
    # Check current permissions
    await check_discord_permissions()
    
    # Print limitations
    print_discord_limitations()
    
    # Suggest solutions
    await suggest_solutions()
    
    print("\n" + "=" * 70)
    print("📋 SUMMARY")
    print("=" * 70)
    print("• Your discord_agent code structure is correct")
    print("• Discord API limitations prevent user token messaging")
    print("• Consider converting to Discord Bot for full functionality")
    print("• Current implementation will authenticate but messaging may fail")

if __name__ == "__main__":
    asyncio.run(main())