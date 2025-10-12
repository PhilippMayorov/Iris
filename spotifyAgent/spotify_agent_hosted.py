"""
Spotify Playlist Agent - Agentverse Hosted Version

This is a simplified version optimized for Agentverse Hosted Agents.
It uses only supported libraries and follows Agentverse best practices.

Features:
- Create playlists based on genre/mood
- Search music catalog
- Handle natural language requests
- Inter-agent communication via uAgents protocol
"""

from uagents import Agent, Context, Model
from typing import Dict, Any, List, Optional
from datetime import datetime
import random

# Agent configuration for Agentverse
agent = Agent(
    name="spotify_playlist_agent_hosted",
    seed="spotify_agentverse_seed_2024",
    port=8000,
    endpoint=["http://localhost:8000/submit"]
)

# Message Models
class CreatePlaylistRequest(Model):
    """Request to create a playlist"""
    playlist_name: str
    genre: Optional[str] = None
    mood: Optional[str] = None
    song_count: Optional[int] = 20
    description: Optional[str] = None

class PlaylistCreatedResponse(Model):
    """Response after playlist creation"""
    success: bool
    message: str
    playlist_name: str
    track_count: int
    spotify_url: Optional[str] = None

class MusicSearchRequest(Model):
    """Request to search music"""
    query: str
    search_type: str = "track"
    limit: int = 10

class MusicSearchResponse(Model):
    """Response with search results"""
    success: bool
    query: str
    results_count: int
    results: List[Dict[str, str]]

# Sample music database (simplified for Agentverse)
MUSIC_DB = {
    "pop": [
        {"name": "Blinding Lights", "artist": "The Weeknd"},
        {"name": "Watermelon Sugar", "artist": "Harry Styles"},
        {"name": "Levitating", "artist": "Dua Lipa"},
        {"name": "Good 4 U", "artist": "Olivia Rodrigo"},
        {"name": "Anti-Hero", "artist": "Taylor Swift"}
    ],
    "rock": [
        {"name": "Bohemian Rhapsody", "artist": "Queen"},
        {"name": "Hotel California", "artist": "Eagles"},
        {"name": "Stairway to Heaven", "artist": "Led Zeppelin"},
        {"name": "Sweet Child O' Mine", "artist": "Guns N' Roses"},
        {"name": "Smells Like Teen Spirit", "artist": "Nirvana"}
    ],
    "hip-hop": [
        {"name": "God's Plan", "artist": "Drake"},
        {"name": "HUMBLE.", "artist": "Kendrick Lamar"},
        {"name": "Sicko Mode", "artist": "Travis Scott"},
        {"name": "Old Town Road", "artist": "Lil Nas X"},
        {"name": "Industry Baby", "artist": "Lil Nas X"}
    ],
    "electronic": [
        {"name": "Titanium", "artist": "David Guetta ft. Sia"},
        {"name": "Wake Me Up", "artist": "Avicii"},
        {"name": "Clarity", "artist": "Zedd ft. Foxes"},
        {"name": "Animals", "artist": "Martin Garrix"},
        {"name": "Lean On", "artist": "Major Lazer & DJ Snake ft. MØ"}
    ],
    "chill": [
        {"name": "Stay", "artist": "Rihanna"},
        {"name": "Midnight City", "artist": "M83"},
        {"name": "Flightless Bird, American Mouth", "artist": "Iron & Wine"},
        {"name": "Holocene", "artist": "Bon Iver"},
        {"name": "Electric Feel", "artist": "MGMT"}
    ]
}

@agent.on_event("startup")
async def startup_handler(ctx: Context):
    """Agent startup handler"""
    ctx.logger.info(f"🎵 Spotify Playlist Agent started!")
    ctx.logger.info(f"Agent address: {agent.address}")
    ctx.logger.info("Ready to create playlists and search music!")

@agent.on_message(model=CreatePlaylistRequest)
async def handle_create_playlist(ctx: Context, sender: str, msg: CreatePlaylistRequest):
    """Handle playlist creation requests"""
    ctx.logger.info(f"Creating playlist: {msg.playlist_name}")
    
    try:
        # Select tracks based on genre/mood
        selected_tracks = []
        
        if msg.genre and msg.genre.lower() in MUSIC_DB:
            tracks = MUSIC_DB[msg.genre.lower()]
            selected_tracks.extend(tracks)
            ctx.logger.info(f"Added {len(tracks)} {msg.genre} tracks")
        elif msg.mood and msg.mood.lower() in MUSIC_DB:
            tracks = MUSIC_DB[msg.mood.lower()]
            selected_tracks.extend(tracks)
            ctx.logger.info(f"Added {len(tracks)} {msg.mood} tracks")
        else:
            # Mix from all genres
            for genre_tracks in MUSIC_DB.values():
                selected_tracks.extend(genre_tracks)
            ctx.logger.info("Added mixed tracks from all genres")
        
        # Shuffle and limit
        random.shuffle(selected_tracks)
        final_tracks = selected_tracks[:msg.song_count]
        
        # Create mock Spotify URL
        playlist_id = hash(msg.playlist_name) % 100000
        spotify_url = f"https://open.spotify.com/playlist/mock_{playlist_id}"
        
        # Send response
        response = PlaylistCreatedResponse(
            success=True,
            message=f"Created playlist '{msg.playlist_name}' with {len(final_tracks)} songs",
            playlist_name=msg.playlist_name,
            track_count=len(final_tracks),
            spotify_url=spotify_url
        )
        
        await ctx.send(sender, response)
        ctx.logger.info(f"✅ Playlist '{msg.playlist_name}' created successfully")
        
    except Exception as e:
        ctx.logger.error(f"❌ Error creating playlist: {e}")
        error_response = PlaylistCreatedResponse(
            success=False,
            message=f"Failed to create playlist: {str(e)}",
            playlist_name=msg.playlist_name,
            track_count=0
        )
        await ctx.send(sender, error_response)

@agent.on_message(model=MusicSearchRequest)
async def handle_music_search(ctx: Context, sender: str, msg: MusicSearchRequest):
    """Handle music search requests"""
    ctx.logger.info(f"Searching for: {msg.query}")
    
    try:
        results = []
        query_lower = msg.query.lower()
        
        # Search through music database
        for genre, tracks in MUSIC_DB.items():
            for track in tracks:
                if (query_lower in track['name'].lower() or 
                    query_lower in track['artist'].lower()):
                    
                    result = {
                        "name": track['name'],
                        "artist": track['artist'],
                        "genre": genre
                    }
                    results.append(result)
                    
                    if len(results) >= msg.limit:
                        break
            
            if len(results) >= msg.limit:
                break
        
        # Send response
        response = MusicSearchResponse(
            success=True,
            query=msg.query,
            results_count=len(results),
            results=results
        )
        
        await ctx.send(sender, response)
        ctx.logger.info(f"✅ Found {len(results)} results for '{msg.query}'")
        
    except Exception as e:
        ctx.logger.error(f"❌ Error searching music: {e}")
        error_response = MusicSearchResponse(
            success=False,
            query=msg.query,
            results_count=0,
            results=[]
        )
        await ctx.send(sender, error_response)

@agent.on_interval(period=60.0)
async def heartbeat(ctx: Context):
    """Periodic heartbeat"""
    ctx.logger.info("🎵 Spotify Agent is alive and ready for requests")

if __name__ == "__main__":
    print("🎵 Starting Spotify Playlist Agent (Agentverse Hosted Version)")
    print(f"Your agent's address is: {agent.address}")
    print("\n🎯 Supported features:")
    print("  • Create playlists by genre/mood")
    print("  • Search music catalog")
    print("  • Inter-agent messaging")
    print(f"\n🎼 Available genres: {list(MUSIC_DB.keys())}")
    print("\n🚀 Starting agent...")
    
    agent.run()