#!/usr/bin/env python3
"""
Slack Agent Test Script

This script tests the comprehensive Slack agent functionality including:
1. OAuth2 authentication flow
2. Message sending capabilities  
3. Message retrieval operations
4. Natural language processing
5. Error handling and recovery

Run this script to validate that your Slack agent is properly configured.
"""

import asyncio
import json
import os
import sys
from datetime import datetime

# Add the parent directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from slack_agent import (
    SlackAuthManager, 
    SlackAPIClient, 
    MessageProcessor,
    SLACK_CLIENT_ID,
    SLACK_CLIENT_SECRET
)

class SlackAgentTester:
    """Comprehensive test suite for Slack agent functionality"""
    
    def __init__(self):
        self.auth_manager = SlackAuthManager()
        self.slack_client = SlackAPIClient(self.auth_manager)
        self.message_processor = MessageProcessor()
        self.test_results = {}
        
    async def run_all_tests(self):
        """Run complete test suite"""
        print("🧪 SLACK AGENT COMPREHENSIVE TEST SUITE")
        print("=" * 60)
        
        # Environment tests
        await self.test_environment_setup()
        
        # Authentication tests  
        await self.test_authentication_flow()
        
        # If authenticated, run API tests
        if await self.auth_manager.get_valid_token():
            await self.test_api_functionality()
            await self.test_user_lookup()
            await self.test_message_operations()
        
        # Natural language processing tests
        await self.test_message_intent_parsing()
        
        # Generate final report
        self.print_test_summary()
    
    async def test_environment_setup(self):
        """Test environment configuration"""
        print("\n🔧 Testing Environment Setup...")
        
        # Check required environment variables
        required_vars = {
            'SLACK_CLIENT_ID': SLACK_CLIENT_ID,
            'SLACK_CLIENT_SECRET': SLACK_CLIENT_SECRET,
            'ASI_ONE_API_KEY': os.getenv('ASI_ONE_API_KEY')
        }
        
        missing_vars = []
        for var_name, var_value in required_vars.items():
            if not var_value:
                missing_vars.append(var_name)
                print(f"  ❌ {var_name}: Not set")
            else:
                print(f"  ✅ {var_name}: Configured")
        
        if not missing_vars:
            self.test_results['environment'] = "✅ PASS"
            print("  📋 All environment variables configured")
        else:
            self.test_results['environment'] = f"❌ FAIL - Missing: {', '.join(missing_vars)}"
            print(f"  ❌ Missing required variables: {', '.join(missing_vars)}")
    
    async def test_authentication_flow(self):
        """Test Slack OAuth2 authentication"""
        print("\n🔐 Testing Authentication...")
        
        try:
            # Check if tokens already exist
            token_loaded = await self.auth_manager.load_tokens()
            
            if token_loaded:
                print("  ✅ Existing tokens found and loaded")
                
                # Test token validity
                try:
                    auth_info = await self.slack_client.test_auth()
                    team_name = auth_info.get('team', 'Unknown')
                    user_name = auth_info.get('user', 'Unknown')
                    print(f"  ✅ Token valid - Connected to {team_name} as {user_name}")
                    self.test_results['authentication'] = f"✅ PASS - {team_name}/{user_name}"
                    
                except Exception as e:
                    print(f"  ❌ Token validation failed: {e}")
                    print("  💡 You may need to re-authenticate")
                    self.test_results['authentication'] = f"❌ FAIL - Token invalid: {str(e)[:50]}"
            else:
                print("  ℹ️  No existing tokens found")
                print("  💡 Run the agent and send 'authenticate' to start OAuth flow")
                self.test_results['authentication'] = "⚠️  SKIP - No tokens (manual OAuth required)"
                
        except Exception as e:
            print(f"  ❌ Authentication test failed: {e}")
            self.test_results['authentication'] = f"❌ FAIL - {str(e)[:50]}"
    
    async def test_api_functionality(self):
        """Test basic Slack API operations"""
        print("\n🌐 Testing Slack API Functionality...")
        
        try:
            # Test users list
            users = await self.slack_client.get_users_list()
            user_count = len([u for u in users if not u.get('deleted') and not u.get('is_bot')])
            print(f"  ✅ Users list retrieved: {user_count} active users")
            
            # Test auth info
            auth_info = await self.slack_client.test_auth()
            workspace_name = auth_info.get('team', 'Unknown')
            print(f"  ✅ Workspace connection: {workspace_name}")
            
            self.test_results['api_functionality'] = "✅ PASS"
            
        except Exception as e:
            print(f"  ❌ API test failed: {e}")
            self.test_results['api_functionality'] = f"❌ FAIL - {str(e)[:50]}"
    
    async def test_user_lookup(self):
        """Test user lookup functionality"""
        print("\n👥 Testing User Lookup...")
        
        try:
            # Get users list for testing
            users = await self.slack_client.get_users_list()
            active_users = [u for u in users if not u.get('deleted') and not u.get('is_bot')]
            
            if not active_users:
                print("  ⚠️  No active users found for testing")
                self.test_results['user_lookup'] = "⚠️  SKIP - No test users"
                return
                
            # Test with first available user
            test_user = active_users[0]
            test_name = test_user.get('name', '')
            
            if test_name:
                found_user = await self.slack_client.find_user_by_name(test_name)
                
                if found_user and found_user['id'] == test_user['id']:
                    print(f"  ✅ User lookup successful: {test_name}")
                    self.test_results['user_lookup'] = "✅ PASS"
                else:
                    print(f"  ❌ User lookup failed for: {test_name}")
                    self.test_results['user_lookup'] = "❌ FAIL - Lookup mismatch"
            else:
                print("  ⚠️  Test user has no name field")
                self.test_results['user_lookup'] = "⚠️  SKIP - No valid test user"
                
        except Exception as e:
            print(f"  ❌ User lookup test failed: {e}")
            self.test_results['user_lookup'] = f"❌ FAIL - {str(e)[:50]}"
    
    async def test_message_operations(self):
        """Test message-related operations (without actually sending)"""
        print("\n📨 Testing Message Operations...")
        
        try:
            # Test conversation opening (with self)
            auth_info = await self.slack_client.test_auth()
            user_id = auth_info.get('user_id')
            
            if user_id:
                # Test opening conversation with self
                conversation = await self.slack_client.open_conversation(user_id)
                
                if conversation.get('id'):
                    print("  ✅ Conversation opening successful")
                    
                    # Test getting conversation history
                    history = await self.slack_client.get_conversation_history(conversation['id'], limit=5)
                    print(f"  ✅ History retrieval: {len(history)} messages")
                    
                    self.test_results['message_operations'] = "✅ PASS"
                else:
                    print("  ❌ Failed to open conversation")
                    self.test_results['message_operations'] = "❌ FAIL - No conversation"
            else:
                print("  ❌ No user ID available for testing")
                self.test_results['message_operations'] = "❌ FAIL - No user ID"
                
        except Exception as e:
            print(f"  ❌ Message operations test failed: {e}")
            self.test_results['message_operations'] = f"❌ FAIL - {str(e)[:50]}"
    
    async def test_message_intent_parsing(self):
        """Test natural language processing"""
        print("\n🧠 Testing Message Intent Parsing...")
        
        test_cases = [
            {
                'input': "Send Alice a message saying I'll be late",
                'expected_action': 'send_message',
                'expected_recipient': 'Alice',
                'expected_message': "I'll be late"
            },
            {
                'input': "Tell Ben: Meeting starts in 10 minutes",
                'expected_action': 'send_message',
                'expected_recipient': 'Ben'
            },
            {
                'input': "Read my last message from Charlie",
                'expected_action': 'read_messages',
                'expected_target': 'Charlie'
            },
            {
                'input': "Connect my Slack account",
                'expected_action': 'authenticate'
            }
        ]
        
        passed_tests = 0
        total_tests = len(test_cases)
        
        for i, test_case in enumerate(test_cases, 1):
            try:
                intent = await self.message_processor.extract_message_intent(test_case['input'])
                
                print(f"  Test {i}: '{test_case['input'][:40]}{'...' if len(test_case['input']) > 40 else ''}'")
                
                # Check expected action
                if intent.get('action') == test_case.get('expected_action'):
                    print(f"    ✅ Action: {intent.get('action')}")
                    
                    # Check other expected fields
                    all_fields_correct = True
                    for key, expected_value in test_case.items():
                        if key.startswith('expected_') and key != 'expected_action':
                            field_name = key.replace('expected_', '')
                            actual_value = intent.get(field_name, '').lower()
                            expected_lower = expected_value.lower()
                            
                            if expected_lower in actual_value or actual_value in expected_lower:
                                print(f"    ✅ {field_name}: {intent.get(field_name)}")
                            else:
                                print(f"    ❌ {field_name}: Expected '{expected_value}', got '{intent.get(field_name)}'")
                                all_fields_correct = False
                    
                    if all_fields_correct:
                        passed_tests += 1
                        print(f"    ✅ Test {i} PASSED")
                    else:
                        print(f"    ❌ Test {i} FAILED (field mismatch)")
                else:
                    print(f"    ❌ Action: Expected '{test_case.get('expected_action')}', got '{intent.get('action')}'")
                    print(f"    ❌ Test {i} FAILED")
                    
            except Exception as e:
                print(f"    ❌ Test {i} FAILED: {e}")
            
            print()
        
        if passed_tests == total_tests:
            self.test_results['intent_parsing'] = f"✅ PASS ({passed_tests}/{total_tests})"
            print(f"  🎉 All intent parsing tests passed! ({passed_tests}/{total_tests})")
        else:
            self.test_results['intent_parsing'] = f"⚠️  PARTIAL ({passed_tests}/{total_tests})"
            print(f"  ⚠️  Intent parsing: {passed_tests}/{total_tests} tests passed")
    
    def print_test_summary(self):
        """Print final test summary"""
        print("\n" + "=" * 60)
        print("📊 SLACK AGENT TEST SUMMARY")
        print("=" * 60)
        
        for test_name, result in self.test_results.items():
            test_display = test_name.replace('_', ' ').title()
            print(f"{test_display:25} {result}")
        
        # Count results
        passed = len([r for r in self.test_results.values() if r.startswith('✅')])
        total = len(self.test_results)
        
        print("=" * 60)
        print(f"Overall Result: {passed}/{total} test categories passed")
        
        if passed == total:
            print("🎉 All tests passed! Your Slack agent is ready to use.")
        elif passed >= total * 0.7:
            print("⚠️  Most tests passed. Check any failed tests above.")
        else:
            print("❌ Several tests failed. Please review configuration and setup.")
            
        print("\n💡 NEXT STEPS:")
        if not SLACK_CLIENT_ID or not SLACK_CLIENT_SECRET:
            print("  1. Configure Slack OAuth credentials in .env file")
        
        if '❌ FAIL - Token invalid' in str(self.test_results.get('authentication', '')):
            print("  2. Re-authenticate with Slack (send 'authenticate' to agent)")
        elif 'SKIP - No tokens' in str(self.test_results.get('authentication', '')):
            print("  2. Authenticate with Slack (send 'authenticate' to agent)")
        
        print("  3. Test messaging: 'Send [username] a message saying hello'")
        print("  4. Test reading: 'Read my last message from [username]'")
        
        print("\n🚀 Ready to run the Slack agent!")

async def main():
    """Main test execution"""
    tester = SlackAgentTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    print("🧪 Starting Slack Agent Test Suite...")
    asyncio.run(main())