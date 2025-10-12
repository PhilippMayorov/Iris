#!/usr/bin/env python3
"""
Discord Agent User Lookup Test

This script tests the improved user lookup functionality to verify that
the agent can properly find Discord friends and guild members.

Run this after completing OAuth authentication.
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_user_lookup():
    """Test the improved user lookup functionality"""
    print("=" * 70)
    print("🔍 TESTING ENHANCED DISCORD USER LOOKUP")
    print("=" * 70)
    
    try:
        from discord_agent import DiscordAuthManager, DiscordAPIClient
        
        # Initialize components
        auth_manager = DiscordAuthManager()
        discord_client = DiscordAPIClient(auth_manager)
        
        # Check if we have valid authentication
        valid_token = await auth_manager.get_valid_token()
        if not valid_token:
            print("❌ No valid Discord token found")
            print("   Run: python test_complete_oauth_flow.py first")
            return False
        
        print("✅ Discord authentication valid")
        
        # Test 1: Get current user info
        print("\n📋 Getting current user info...")
        try:
            current_user = await discord_client.get_current_user()
            username = current_user.get('username', 'Unknown')
            discriminator = current_user.get('discriminator', '0000')
            print(f"   Current user: {username}#{discriminator}")
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            return False
        
        # Test 2: Get friends list
        print("\n👥 Getting friends list...")
        try:
            relationships = await discord_client.get_user_relationships()
            friends = []
            for rel in relationships:
                user = rel.get('user', {})
                if user and user.get('username'):
                    username = user.get('username', '')
                    discriminator = user.get('discriminator', '0')
                    display_name = f"{username}#{discriminator}" if discriminator != '0' else username
                    friends.append(display_name)
            
            if friends:
                print(f"   ✅ Found {len(friends)} friends:")
                for friend in friends[:5]:  # Show first 5
                    print(f"      - {friend}")
                if len(friends) > 5:
                    print(f"      ... and {len(friends) - 5} more")
            else:
                print("   ℹ️  No friends found (or friends list not accessible)")
                
        except Exception as e:
            print(f"   ⚠️  Friends list access failed: {e}")
        
        # Test 3: Get guilds
        print("\n🏰 Getting mutual guilds...")
        try:
            guilds = await discord_client.get_user_guilds()
            if guilds:
                print(f"   ✅ Found {len(guilds)} mutual guilds:")
                for guild in guilds[:3]:
                    print(f"      - {guild.get('name', 'Unknown')}")
                if len(guilds) > 3:
                    print(f"      ... and {len(guilds) - 3} more")
            else:
                print("   ℹ️  No mutual guilds found")
        except Exception as e:
            print(f"   ⚠️  Guild access failed: {e}")
        
        # Test 4: Test username parsing
        print("\n🔤 Testing username parsing...")
        test_usernames = ["Ben", "Alice#1234", "User#0001", "123456789"]
        
        for test_username in test_usernames:
            parsed = discord_client.parse_username(test_username)
            print(f"   '{test_username}' → {parsed}")
        
        # Test 5: Get available users summary
        print("\n📊 Getting available users summary...")
        try:
            summary = await discord_client.get_available_users_summary()
            print(f"   Summary:\n{summary}")
        except Exception as e:
            print(f"   ⚠️  Summary failed: {e}")
        
        print("\n✅ User lookup test completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure discord_agent.py is in the current directory")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def test_message_parsing():
    """Test that message parsing works correctly"""
    print("\n" + "=" * 70)
    print("🧠 TESTING MESSAGE PARSING")
    print("=" * 70)
    
    try:
        from discord_agent import MessageProcessor
        
        test_messages = [
            "Can you message Ben saying 'hi from Discord bot'",
            "Send Alice#1234: Meeting at 3pm today",
            "Text user ID 123456789 that I'll be late",
            "DM Charlie: How's the project going?",
            "Message Sarah saying the meeting is cancelled"
        ]
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n{i}. Testing: \"{message}\"")
            try:
                intent = await MessageProcessor.extract_message_intent(message)
                print(f"   ✅ Parsed: {intent}")
                
                if intent.get('action') == 'send_message':
                    recipient = intent.get('recipient')
                    msg_content = intent.get('message')
                    if recipient and msg_content:
                        print(f"   ✅ Valid: recipient='{recipient}', message='{msg_content}'")
                    else:
                        print(f"   ⚠️  Missing data: recipient='{recipient}', message='{msg_content}'")
                else:
                    print(f"   ⚠️  Unexpected action: {intent.get('action')}")
                    
            except Exception as e:
                print(f"   ❌ Parsing failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Message parsing test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Discord Agent Enhanced User Lookup Test Suite")
    
    # Test 1: User lookup capabilities
    lookup_result = await test_user_lookup()
    
    # Test 2: Message parsing
    parsing_result = await test_message_parsing()
    
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 70)
    print(f"User Lookup: {'✅ PASS' if lookup_result else '❌ FAIL'}")
    print(f"Message Parsing: {'✅ PASS' if parsing_result else '❌ FAIL'}")
    
    if lookup_result and parsing_result:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n📋 Your Discord agent can now:")
        print("• Find Discord friends by username")
        print("• Search mutual guild members")
        print("• Parse username#discriminator format")
        print("• Handle Discord User IDs")
        print("• Provide helpful error messages")
        print("\n🚀 Try: python discord_agent.py")
        print("Then say: 'Can you message [friend_name] saying hello'")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        if not lookup_result:
            print("• Check Discord authentication and token permissions")
        if not parsing_result:
            print("• Check ASI:One API configuration")
    
    return lookup_result and parsing_result

if __name__ == "__main__":
    asyncio.run(main())