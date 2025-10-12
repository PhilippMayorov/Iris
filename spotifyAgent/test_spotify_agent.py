"""
Test script for Spotify Playlist Agent
Demonstrates how to interact with the agent for playlist creation
"""

import asyncio
from spotify_agent import CreatePlaylistMessage, SearchMusicMessage
import uuid

async def test_playlist_creation():
    """Test playlist creation functionality"""
    
    # Test cases for playlist creation
    test_cases = [
        {
            "playlist_name": "My Pop Hits",
            "genre": "pop",
            "song_count": 15,
            "description": "The best pop songs for any occasion"
        },
        {
            "playlist_name": "Chill Vibes",
            "mood": "chill",
            "song_count": 10,
            "description": "Relaxing songs for studying or working"
        },
        {
            "playlist_name": "Rock Classics",
            "genre": "rock",
            "song_count": 25,
            "description": "Timeless rock anthems"
        },
        {
            "playlist_name": "Hip-Hop Workout",
            "genre": "hip-hop",
            "song_count": 20,
            "description": "High-energy hip-hop for workouts"
        }
    ]
    
    print("🎵 Testing Spotify Playlist Agent")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: Creating '{test_case['playlist_name']}'")
        print(f"Genre/Mood: {test_case.get('genre', test_case.get('mood', 'mixed'))}")
        print(f"Song Count: {test_case['song_count']}")
        
        # Create message
        message = CreatePlaylistMessage(
            playlist_name=test_case["playlist_name"],
            genre=test_case.get("genre"),
            mood=test_case.get("mood"),
            song_count=test_case["song_count"],
            description=test_case["description"],
            request_id=str(uuid.uuid4())
        )
        
        print(f"✓ Test message created: {message.playlist_name}")

async def test_music_search():
    """Test music search functionality"""
    
    search_queries = [
        {"query": "The Weeknd", "search_type": "artist"},
        {"query": "Blinding Lights", "search_type": "track"},
        {"query": "pop music", "search_type": "track"},
        {"query": "Queen", "search_type": "artist"}
    ]
    
    print("\n🔍 Testing Music Search")
    print("=" * 50)
    
    for i, search in enumerate(search_queries, 1):
        print(f"\nSearch {i}: '{search['query']}' (type: {search['search_type']})")
        
        message = SearchMusicMessage(
            query=search["query"],
            search_type=search["search_type"],
            limit=5,
            request_id=str(uuid.uuid4())
        )
        
        print(f"✓ Search message created for: {message.query}")

def print_agent_info():
    """Print information about the Spotify agent"""
    print("🎼 Spotify Playlist Agent Information")
    print("=" * 50)
    print("Purpose: Create and manage Spotify playlists based on user requests")
    print("Port: 8005")
    print("Endpoint: http://127.0.0.1:8005/submit")
    print("\nSupported Genres:")
    print("  • Pop")
    print("  • Rock") 
    print("  • Hip-Hop")
    print("  • Electronic")
    print("  • Chill")
    print("\nCapabilities:")
    print("  • Create custom playlists")
    print("  • Search music catalog")
    print("  • Handle voice commands via vocal_core_agent")
    print("  • Support genre and mood-based selection")

async def main():
    """Main test function"""
    print_agent_info()
    await test_playlist_creation()
    await test_music_search()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")
    print("To run the actual agent:")
    print("python spotify_agent.py")

if __name__ == "__main__":
    asyncio.run(main())