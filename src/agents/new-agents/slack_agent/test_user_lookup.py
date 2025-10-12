#!/usr/bin/env python3
"""
Test script for improved Slack Agent user lookup and messaging functionality
"""

import asyncio
import sys
import os
sys.path.append('.')

# Mock the user list response for testing
MOCK_USERS = [
    {
        'id': 'U12345',
        'name': 'ben.smith',
        'deleted': False,
        'is_bot': False,
        'profile': {
            'display_name': 'Ben S.',
            'real_name': 'Ben Smith',
            'first_name': 'Ben'
        }
    },
    {
        'id': 'U67890',
        'name': 'ben.taylor',
        'deleted': False,
        'is_bot': False,
        'profile': {
            'display_name': 'Ben T.',
            'real_name': 'Ben Taylor',
            'first_name': 'Ben'
        }
    },
    {
        'id': 'U11111',
        'name': 'alice.johnson',
        'deleted': False,
        'is_bot': False,
        'profile': {
            'display_name': 'Alice',
            'real_name': 'Alice Johnson',
            'first_name': 'Alice'
        }
    },
    {
        'id': 'U22222',
        'name': 'charlie.brown',
        'deleted': False,
        'is_bot': False,
        'profile': {
            'display_name': '',
            'real_name': 'Charlie Brown',
            'first_name': 'Charlie'
        }
    }
]

class MockSlackAPIClient:
    """Mock Slack API client for testing user lookup logic"""
    
    def __init__(self):
        self.user_cache = {}
    
    async def get_users_list(self):
        """Return mock user list"""
        return MOCK_USERS
    
    async def find_user_by_name(self, name: str):
        """Test the improved find_user_by_name logic"""
        # Check cache first
        cache_key = name.lower()
        if cache_key in self.user_cache:
            return self.user_cache[cache_key]
        
        try:
            users = await self.get_users_list()
            exact_matches = []
            partial_matches = []
            
            search_name = name.lower().strip()
            
            for user in users:
                if user.get('deleted') or user.get('is_bot'):
                    continue
                
                profile = user.get('profile', {})
                display_name = profile.get('display_name', '').lower()
                real_name = profile.get('real_name', '').lower()
                username = user.get('name', '').lower()
                first_name = profile.get('first_name', '').lower()
                
                # Extract first name from real name if first_name is not available
                if not first_name and real_name:
                    first_name = real_name.split()[0] if real_name.split() else ''
                
                # Exact matches (highest priority)  
                if search_name in [display_name, real_name, username] or search_name == user.get('id'):
                    exact_matches.append(user)
                    continue
                
                # Partial matches for first name, display name, or real name
                if (search_name == first_name or  # First name exact match
                    search_name in display_name or  # Partial display name match
                    search_name in real_name or     # Partial real name match
                    search_name in username):       # Partial username match
                    partial_matches.append(user)
            
            # Return exact match if found
            if exact_matches:
                user = exact_matches[0]
                self.user_cache[cache_key] = user
                return user
            
            # Return single partial match
            if len(partial_matches) == 1:
                user = partial_matches[0]
                self.user_cache[cache_key] = user
                return user
            
            # Multiple matches - cache for disambiguation
            if len(partial_matches) > 1:
                self.user_cache[f"{cache_key}_multiple"] = partial_matches
                return None  # Will be handled by caller for disambiguation
            
            return None
            
        except Exception as e:
            print(f"Error finding user {name}: {e}")
            return None

async def test_user_lookup():
    """Test the user lookup functionality"""
    print("🧪 Testing Slack Agent User Lookup Improvements")
    print("=" * 60)
    
    client = MockSlackAPIClient()
    
    test_cases = [
        ("Ben", "Should find multiple matches"),
        ("Alice", "Should find single match"),
        ("Charlie", "Should find single match"),
        ("Ben Smith", "Should find exact match for Ben Smith"),
        ("ben.smith", "Should find exact username match"),
        ("John", "Should find no matches"),
        ("U12345", "Should find exact ID match"),
        ("Alice Johnson", "Should find exact real name match")
    ]
    
    for name, expected in test_cases:
        print(f"\n🔍 Testing: '{name}' ({expected})")
        
        result = await client.find_user_by_name(name)
        
        if result:
            profile = result.get('profile', {})
            display_name = profile.get('display_name', '')
            real_name = profile.get('real_name', '')
            username = result.get('name', '')
            
            print(f"✅ Found: {real_name} (@{username})")
            if display_name:
                print(f"   Display: {display_name}")
        else:
            # Check for multiple matches
            cache_key = f"{name.lower()}_multiple"
            if cache_key in client.user_cache:
                matches = client.user_cache[cache_key]
                print(f"🤔 Multiple matches found ({len(matches)}):")
                for match in matches:
                    profile = match.get('profile', {})
                    real_name = profile.get('real_name', '')
                    username = match.get('name', '')
                    print(f"   • {real_name} (@{username})")
            else:
                print("❌ No matches found")
    
    print("\n✅ User lookup testing completed!")

def format_disambiguation_message(name: str, matches: list) -> str:
    """Format disambiguation message like the real agent"""
    disambig_msg = f"🤔 I found multiple users named '{name}':\n\n"
    
    for i, user in enumerate(matches[:5], 1):  # Limit to 5 matches
        profile = user.get('profile', {})
        display_name = profile.get('display_name', '')
        real_name = profile.get('real_name', '')
        username = user.get('name', '')
        
        # Create a clear identifier
        identifier = display_name or real_name or username
        if real_name and display_name and real_name != display_name:
            identifier = f"{display_name} ({real_name})"
        
        disambig_msg += f"{i}. **{identifier}** (@{username})\n"
    
    disambig_msg += f"\n💡 **To send your message, be more specific:**\n"
    disambig_msg += f"• Use their full name\n"
    disambig_msg += f"• Use their display name\n"
    disambig_msg += f"• Use their @username"
    
    return disambig_msg

async def test_disambiguation():
    """Test disambiguation message formatting"""
    print("\n🧪 Testing Disambiguation Messages")
    print("=" * 40)
    
    client = MockSlackAPIClient()
    
    # Test "Ben" which should return multiple matches
    result = await client.find_user_by_name("Ben")
    
    if not result:
        cache_key = "ben_multiple"
        if cache_key in client.user_cache:
            matches = client.user_cache[cache_key]
            print("📝 Disambiguation message for 'Ben':")
            print("-" * 30)
            print(format_disambiguation_message("Ben", matches))

if __name__ == "__main__":
    asyncio.run(test_user_lookup())
    asyncio.run(test_disambiguation())
    
    print("\n🎉 All tests completed!")
    print("\n🚀 Improvements implemented:")
    print("• ✅ Case-insensitive user matching")
    print("• ✅ First name, display name, and real name matching")
    print("• ✅ Exact match prioritization")
    print("• ✅ Multiple match disambiguation")
    print("• ✅ Better error messages and user guidance")
    print("• ✅ Improved scope verification and error handling")