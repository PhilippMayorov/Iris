"""
Spotify Agent - Music Playlist Creation and Management

This agent handles Spotify playlist creation based on user requests:
1. Creates playlists based on genre, mood, or specific requirements
2. Searches for songs matching user criteria
3. Manages playlist content and metadata
4. Integrates with Spotify Web API

Integration Points:
- Receives task requests from vocal_core_agent
- Uses Spotify Web API for playlist and song management
- Sends playlist creation confirmations back to vocal_core_agent
"""

import asyncio
from typing import Dict, Any, List, Optional
from uagents import Agent, Context, Model
from pydantic import BaseModel
from datetime import datetime
import os
import json
import random

# Initialize the spotify agent with Agentverse integration
SEED_PHRASE = "spotify_playlist_agent_unique_seed_2024"

agent = Agent(
    name="spotify_playlist_agent",
    port=8005,
    seed=SEED_PHRASE,
    endpoint=["http://127.0.0.1:8005/submit"],
    mailbox=True,
    publish_agent_details=True,
    readme_path="README.md"
)

# Message Models for inter-agent communication
class CreatePlaylistMessage(Model):
    """Message to create a playlist"""
    playlist_name: str
    genre: Optional[str] = None
    mood: Optional[str] = None
    artists: Optional[List[str]] = None
    song_count: Optional[int] = 20
    description: Optional[str] = None
    request_id: str

class PlaylistResponse(Model):
    """Response after playlist creation"""
    success: bool
    message: str
    playlist_data: Optional[Dict[str, Any]] = None
    request_id: str

class SearchMusicMessage(Model):
    """Message to search for music"""
    query: str
    search_type: str = "track"  # track, artist, album, playlist
    limit: int = 20
    request_id: str

class MusicSearchResponse(Model):
    """Response with search results"""
    success: bool
    message: str
    results: List[Dict[str, Any]]
    request_id: str

# Sample music database for demonstration
SAMPLE_TRACKS = {
    "pop": [
        {"name": "Blinding Lights", "artist": "The Weeknd", "album": "After Hours", "spotify_id": "0VjIjW4GlUZAMYd2vXMi3b"},
        {"name": "Watermelon Sugar", "artist": "Harry Styles", "album": "Fine Line", "spotify_id": "6UelLqGlWMcVH1E5c4H7lY"},
        {"name": "Levitating", "artist": "Dua Lipa", "artist": "Future Nostalgia", "spotify_id": "463CkQjx2Zk1yXoBuierM9"},
        {"name": "Good 4 U", "artist": "Olivia Rodrigo", "album": "Sour", "spotify_id": "4ZtFanR9U6ndgddUvNcjcG"},
        {"name": "Anti-Hero", "artist": "Taylor Swift", "album": "Midnights", "spotify_id": "0V3wPSX9ygBnCm8psDIegu"}
    ],
    "rock": [
        {"name": "Bohemian Rhapsody", "artist": "Queen", "album": "A Night at the Opera", "spotify_id": "4u7EnebtmKWzUH433cf5Qv"},
        {"name": "Hotel California", "artist": "Eagles", "album": "Hotel California", "spotify_id": "40riOy7x9W7GXjyGp4pjAv"},
        {"name": "Stairway to Heaven", "artist": "Led Zeppelin", "album": "Led Zeppelin IV", "spotify_id": "5CQ30WqJwcep0pYcV4AMNc"},
        {"name": "Sweet Child O' Mine", "artist": "Guns N' Roses", "album": "Appetite for Destruction", "spotify_id": "7o2CTH4ctstm8TNelqjb51"},
        {"name": "Smells Like Teen Spirit", "artist": "Nirvana", "album": "Nevermind", "spotify_id": "4CeeEOM32jQcH3eN9Q2dGj"}
    ],
    "hip-hop": [
        {"name": "God's Plan", "artist": "Drake", "album": "Scorpion", "spotify_id": "6DCZcSspjsKoFjzjrWoCdn"},
        {"name": "HUMBLE.", "artist": "Kendrick Lamar", "album": "DAMN.", "spotify_id": "7KXjTSCq5nL1LoYtL7XAwS"},
        {"name": "Sicko Mode", "artist": "Travis Scott", "album": "Astroworld", "spotify_id": "2xLMifQCjDGFmkHkpNLD9h"},
        {"name": "Old Town Road", "artist": "Lil Nas X", "album": "7 EP", "spotify_id": "2YpeDb67231RjR0MgVLzsG"},
        {"name": "Industry Baby", "artist": "Lil Nas X", "album": "Montero", "spotify_id": "27NovPIUIRrOZoCHxABJwK"}
    ],
    "electronic": [
        {"name": "Titanium", "artist": "David Guetta ft. Sia", "album": "Nothing but the Beat", "spotify_id": "0lYBSQXN6rCTvUZLscTBFM"},
        {"name": "Wake Me Up", "artist": "Avicii", "album": "True", "spotify_id": "0nrRP2bk19rLc0orkWPQk2"},
        {"name": "Clarity", "artist": "Zedd ft. Foxes", "album": "Clarity", "spotify_id": "2qSkIjg1o9h3YT9RAgYN75"},
        {"name": "Animals", "artist": "Martin Garrix", "album": "Animals", "spotify_id": "1vrd6UOGamcKNGnSHJQlSt"},
        {"name": "Lean On", "artist": "Major Lazer & DJ Snake ft. MØ", "album": "Peace Is The Mission", "spotify_id": "4B2As7ySbYqz3WenM6Y0xo"}
    ],
    "chill": [
        {"name": "Stay", "artist": "Rihanna", "album": "Talk That Talk", "spotify_id": "4Dvkj6JhhA12EX05fT7y2e"},
        {"name": "Midnight City", "artist": "M83", "album": "Hurry Up, We're Dreaming", "spotify_id": "0F7FA14euOIX8KcbEturGH"},
        {"name": "Flightless Bird, American Mouth", "artist": "Iron & Wine", "album": "The Shepherd's Dog", "spotify_id": "3ASEymlVOQ7JlvKTuMaFnC"},
        {"name": "Holocene", "artist": "Bon Iver", "album": "Bon Iver, Bon Iver", "spotify_id": "5ZWQKFjuTNjdQXc3jNEidd"},
        {"name": "Electric Feel", "artist": "MGMT", "album": "Oracular Spectacular", "spotify_id": "3FVZMg0MHkwJTa8L1hwNfB"}
    ]
}

@agent.on_event("startup")
async def startup(ctx: Context):
    """Initialize spotify agent on startup"""
    ctx.logger.info("Spotify Playlist Agent starting up...")
    ctx.logger.info(f"Agent address: {agent.address}")
    ctx.logger.info("Ready to create playlists and manage music!")
    
    # TODO: Initialize Spotify Web API client when real integration is needed
    # spotify_client = spotipy.Spotify(auth_manager=SpotifyOAuth(...))

@agent.on_message(model=CreatePlaylistMessage)
async def handle_create_playlist(ctx: Context, sender: str, msg: CreatePlaylistMessage):
    """Handle playlist creation request"""
    ctx.logger.info(f"Creating playlist: {msg.playlist_name}")
    ctx.logger.info(f"Genre: {msg.genre}, Mood: {msg.mood}, Song count: {msg.song_count}")
    
    try:
        # Create playlist based on user requirements
        playlist_data = await create_playlist_with_songs(
            ctx, msg.playlist_name, msg.genre, msg.mood, 
            msg.artists, msg.song_count, msg.description
        )
        
        response = PlaylistResponse(
            success=True,
            message=f"Successfully created playlist '{msg.playlist_name}' with {len(playlist_data['tracks'])} songs",
            playlist_data=playlist_data,
            request_id=msg.request_id
        )
        
        ctx.logger.info(f"Playlist created successfully: {playlist_data['name']}")
        
    except Exception as e:
        ctx.logger.error(f"Error creating playlist: {e}")
        response = PlaylistResponse(
            success=False,
            message=f"Failed to create playlist: {str(e)}",
            playlist_data=None,
            request_id=msg.request_id
        )
    
    # Send response back to sender
    await ctx.send(sender, response)

@agent.on_message(model=SearchMusicMessage)
async def handle_search_music(ctx: Context, sender: str, msg: SearchMusicMessage):
    """Handle music search request"""
    ctx.logger.info(f"Searching for: {msg.query} (type: {msg.search_type})")
    
    try:
        results = await search_music_catalog(ctx, msg.query, msg.search_type, msg.limit)
        
        response = MusicSearchResponse(
            success=True,
            message=f"Found {len(results)} results for '{msg.query}'",
            results=results,
            request_id=msg.request_id
        )
        
    except Exception as e:
        ctx.logger.error(f"Error searching music: {e}")
        response = MusicSearchResponse(
            success=False,
            message=f"Search failed: {str(e)}",
            results=[],
            request_id=msg.request_id
        )
    
    await ctx.send(sender, response)

async def create_playlist_with_songs(
    ctx: Context, 
    name: str, 
    genre: Optional[str] = None,
    mood: Optional[str] = None,
    artists: Optional[List[str]] = None,
    song_count: int = 20,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Create a playlist with songs based on criteria"""
    
    # Determine which songs to include
    selected_tracks = []
    
    if genre and genre.lower() in SAMPLE_TRACKS:
        # Use genre-specific tracks
        genre_tracks = SAMPLE_TRACKS[genre.lower()]
        selected_tracks.extend(genre_tracks)
        ctx.logger.info(f"Added {len(genre_tracks)} {genre} tracks")
    
    if mood and mood.lower() in SAMPLE_TRACKS:
        # Use mood-specific tracks
        mood_tracks = SAMPLE_TRACKS[mood.lower()]
        selected_tracks.extend(mood_tracks)
        ctx.logger.info(f"Added {len(mood_tracks)} {mood} tracks")
    
    # If no specific genre/mood, mix from all categories
    if not selected_tracks:
        for category_tracks in SAMPLE_TRACKS.values():
            selected_tracks.extend(category_tracks)
        ctx.logger.info("Added mixed tracks from all genres")
    
    # Remove duplicates and limit to requested count
    unique_tracks = []
    seen_ids = set()
    
    for track in selected_tracks:
        if track['spotify_id'] not in seen_ids:
            unique_tracks.append(track)
            seen_ids.add(track['spotify_id'])
            
            if len(unique_tracks) >= song_count:
                break
    
    # Shuffle for variety
    random.shuffle(unique_tracks)
    final_tracks = unique_tracks[:song_count]
    
    # Create playlist data structure
    playlist_data = {
        "name": name,
        "description": description or f"Auto-generated playlist with {len(final_tracks)} tracks",
        "tracks": final_tracks,
        "total_tracks": len(final_tracks),
        "genre": genre,
        "mood": mood,
        "created_at": datetime.now().isoformat(),
        "spotify_url": f"https://open.spotify.com/playlist/mock_{hash(name)}",
        "playlist_id": f"playlist_{hash(name)}"
    }
    
    ctx.logger.info(f"Created playlist with {len(final_tracks)} tracks")
    return playlist_data

async def search_music_catalog(
    ctx: Context, 
    query: str, 
    search_type: str = "track", 
    limit: int = 20
) -> List[Dict[str, Any]]:
    """Search for music in the catalog"""
    
    results = []
    query_lower = query.lower()
    
    # Search through all tracks in our sample database
    for category, tracks in SAMPLE_TRACKS.items():
        for track in tracks:
            # Simple search matching
            if (query_lower in track['name'].lower() or 
                query_lower in track['artist'].lower() or
                query_lower in track.get('album', '').lower()):
                
                result = {
                    "type": "track",
                    "name": track['name'],
                    "artist": track['artist'],
                    "album": track.get('album', ''),
                    "spotify_id": track['spotify_id'],
                    "category": category,
                    "preview_url": f"https://p.scdn.co/mp3-preview/{track['spotify_id']}",
                    "external_url": f"https://open.spotify.com/track/{track['spotify_id']}"
                }
                results.append(result)
                
                if len(results) >= limit:
                    break
        
        if len(results) >= limit:
            break
    
    ctx.logger.info(f"Found {len(results)} results for query: {query}")
    return results

# HTTP endpoint handlers for testing (optional)
@agent.on_interval(period=300.0)  # Every 5 minutes
async def log_status(ctx: Context):
    """Periodic status log"""
    ctx.logger.info("Spotify Playlist Agent is running and ready for requests")

if __name__ == "__main__":
    print("🎵 Starting Spotify Playlist Agent...")
    print(f"Your agent's address is: {agent.address}")
    print("\nAgent capabilities:")
    print("  ✓ Create custom playlists based on genre/mood")
    print("  ✓ Search music catalog")
    print("  ✓ Handle playlist requests from vocal core agent")
    print("  ✓ Support for multiple music genres and moods")
    print("  ✓ Agentverse integration with mailbox support")
    print("\nSupported genres:", list(SAMPLE_TRACKS.keys()))
    print("\nStarting agent server...")
    print("📱 Connect to Agentverse using the Inspector URL that will appear below:")
    
    agent.run()