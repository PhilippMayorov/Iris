"""
Spotify Agent - Music Integration

This agent handles all music-related tasks:
1. Playing, pausing, skipping songs
2. Searching for music and playlists
3. Creating and managing playlists
4. Controlling volume and playback
5. Getting music recommendations

Integration Points:
- Receives task requests from vocal_core_agent
- Uses Spotify Web API for music control
- Sends status updates back to vocal_core_agent
"""

import asyncio
from typing import Dict, Any, List, Optional
from uagents import Agent, Context, Model
from pydantic import BaseModel
from datetime import datetime
import os

# Initialize the spotify agent
agent = Agent(
    name="spotify_agent",
    port=8004,
    seed="spotify_agent_seed",
    endpoint=["http://127.0.0.1:8004/submit"]
)

# Message Models
class SpotifyTask(Model):
    """Spotify task from vocal_core_agent"""
    intent: str
    parameters: Dict[str, Any]
    request_id: str

class SpotifyResponse(Model):
    """Response back to vocal_core_agent"""
    success: bool
    message: str
    music_data: Optional[Dict[str, Any]]
    request_id: str

class TrackInfo(BaseModel):
    """Track information"""
    name: str
    artist: str
    album: str
    duration_ms: int
    spotify_id: str

@agent.on_startup
async def startup(ctx: Context):
    """Initialize spotify agent"""
    ctx.logger.info("Spotify Agent starting up...")
    ctx.logger.info(f"Agent address: {agent.address}")
    
    # TODO: Initialize Spotify Web API client
    # TODO: Authenticate with Spotify
    # TODO: Set up playback connection

@agent.on_message(model=SpotifyTask)
async def handle_spotify_task(ctx: Context, sender: str, msg: SpotifyTask):
    """Handle spotify task from vocal_core_agent"""
    ctx.logger.info(f"Received spotify task: {msg.intent}")
    
    try:
        response = None
        
        if msg.intent == "play_music":
            response = await play_music(ctx, msg.parameters)
        elif msg.intent == "pause_music":
            response = await pause_music(ctx, msg.parameters)
        elif msg.intent == "skip_track":
            response = await skip_track(ctx, msg.parameters)
        elif msg.intent == "search_music":
            response = await search_music(ctx, msg.parameters)
        elif msg.intent == "create_playlist":
            response = await create_playlist(ctx, msg.parameters)
        elif msg.intent == "control_volume":
            response = await control_volume(ctx, msg.parameters)
        elif msg.intent == "get_current_track":
            response = await get_current_track(ctx, msg.parameters)
        else:
            response = SpotifyResponse(
                success=False,
                message=f"Unknown spotify intent: {msg.intent}",
                music_data=None,
                request_id=msg.request_id
            )
        
        # Send response back to vocal_core_agent
        await ctx.send(sender, response)
        
    except Exception as e:
        ctx.logger.error(f"Error handling spotify task: {e}")
        error_response = SpotifyResponse(
            success=False,
            message=f"Error processing spotify task: {str(e)}",
            music_data=None,
            request_id=msg.request_id
        )
        await ctx.send(sender, error_response)

async def play_music(ctx: Context, parameters: Dict[str, Any]) -> SpotifyResponse:
    """
    Play music (song, artist, playlist, etc.)
    TODO: Implement actual Spotify Web API call
    """
    ctx.logger.info("Playing music...")
    
    query = parameters.get("query", "")
    
    # TODO: Search for music and start playback
    # TODO: Handle different types (song, artist, album, playlist)
    
    track_data = {
        "track_name": "Example Song",
        "artist": "Example Artist",
        "album": "Example Album",
        "is_playing": True
    }
    
    return SpotifyResponse(
        success=True,
        message=f"Now playing: {track_data['track_name']} by {track_data['artist']}",
        music_data=track_data,
        request_id=parameters.get("request_id", "")
    )

async def pause_music(ctx: Context, parameters: Dict[str, Any]) -> SpotifyResponse:
    """
    Pause current playback
    TODO: Implement actual Spotify Web API call
    """
    ctx.logger.info("Pausing music...")
    
    # TODO: Pause current playback
    
    return SpotifyResponse(
        success=True,
        message="Music paused",
        music_data={"is_playing": False},
        request_id=parameters.get("request_id", "")
    )

async def skip_track(ctx: Context, parameters: Dict[str, Any]) -> SpotifyResponse:
    """
    Skip to next or previous track
    TODO: Implement actual Spotify Web API call
    """
    ctx.logger.info("Skipping track...")
    
    direction = parameters.get("direction", "next")  # "next" or "previous"
    
    # TODO: Skip track in specified direction
    
    return SpotifyResponse(
        success=True,
        message=f"Skipped to {direction} track",
        music_data=None,
        request_id=parameters.get("request_id", "")
    )

async def search_music(ctx: Context, parameters: Dict[str, Any]) -> SpotifyResponse:
    """
    Search for music
    TODO: Implement actual Spotify Web API search
    """
    ctx.logger.info("Searching music...")
    
    query = parameters.get("query", "")
    search_type = parameters.get("type", "track")  # track, artist, album, playlist
    
    # TODO: Search Spotify catalog
    
    search_results = [
        {"name": "Example Song 1", "artist": "Artist 1", "type": "track"},
        {"name": "Example Song 2", "artist": "Artist 2", "type": "track"}
    ]
    
    return SpotifyResponse(
        success=True,
        message=f"Found {len(search_results)} results for '{query}'",
        music_data={"results": search_results},
        request_id=parameters.get("request_id", "")
    )

async def create_playlist(ctx: Context, parameters: Dict[str, Any]) -> SpotifyResponse:
    """
    Create a new playlist
    TODO: Implement actual Spotify Web API call
    """
    ctx.logger.info("Creating playlist...")
    
    name = parameters.get("name", "New Playlist")
    description = parameters.get("description", "")
    
    # TODO: Create playlist on Spotify
    
    playlist_data = {
        "playlist_id": "mock_playlist_123",
        "name": name,
        "description": description,
        "url": "https://open.spotify.com/playlist/mock123"
    }
    
    return SpotifyResponse(
        success=True,
        message=f"Created playlist '{name}'",
        music_data=playlist_data,
        request_id=parameters.get("request_id", "")
    )

async def control_volume(ctx: Context, parameters: Dict[str, Any]) -> SpotifyResponse:
    """
    Control playback volume
    TODO: Implement actual Spotify Web API call
    """
    ctx.logger.info("Controlling volume...")
    
    volume = parameters.get("volume", 50)  # 0-100
    
    # TODO: Set playback volume
    
    return SpotifyResponse(
        success=True,
        message=f"Volume set to {volume}%",
        music_data={"volume": volume},
        request_id=parameters.get("request_id", "")
    )

async def get_current_track(ctx: Context, parameters: Dict[str, Any]) -> SpotifyResponse:
    """
    Get currently playing track
    TODO: Implement actual Spotify Web API call
    """
    ctx.logger.info("Getting current track...")
    
    # TODO: Get current playback state
    
    current_track = {
        "track_name": "Current Song",
        "artist": "Current Artist",
        "album": "Current Album",
        "is_playing": True,
        "progress_ms": 120000,
        "duration_ms": 240000
    }
    
    return SpotifyResponse(
        success=True,
        message="Retrieved current track info",
        music_data=current_track,
        request_id=parameters.get("request_id", "")
    )

if __name__ == "__main__":
    print("Starting Spotify Agent...")
    print(f"Agent will run on: {agent.address}")
    print("This agent handles:")
    print("  - Playing and controlling music")
    print("  - Searching Spotify catalog")
    print("  - Creating and managing playlists")
    print("  - Volume and playback control")
    
    agent.run()