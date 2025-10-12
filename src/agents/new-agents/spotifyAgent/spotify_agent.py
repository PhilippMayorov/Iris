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
import re
from typing import Dict, Any, List, Optional
from uagents import Agent, Context, Model, Protocol
from pydantic import BaseModel
from datetime import datetime
from uuid import uuid4
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)
import os
import json
import random
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI ASI:One Configuration
from openai import OpenAI

asi_client = OpenAI(
    # Using ASI:One LLM endpoint and model
    base_url='https://api.asi1.ai/v1',
    # Get your API key from https://asi1.ai/dashboard/api-keys
    api_key=os.getenv("ASI_ONE_API_KEY", "your_asi_one_api_key_here"),
)

# Spotify API Configuration
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

# Spotify scopes needed for playlist creation and music search
SPOTIFY_SCOPE = "playlist-modify-public playlist-modify-private playlist-read-private user-library-read"

# Initialize Spotify client (will be set up during agent startup)
spotify_client = None

# Initialize the spotify agent with Agentverse integration
SEED_PHRASE = "spotify_playlist_agent_unique_seed_2024"

agent = Agent(
    name="spotify_playlist_agent",
    port=8005,
    seed=SEED_PHRASE,
    mailbox=True,
    publish_agent_details=True,
    readme_path="README.md"
)

# Create a protocol compatible with ASI:One chat protocol spec
chat_protocol = Protocol(spec=chat_protocol_spec)

# Subject matter for ASI:One discovery
SUBJECT_MATTER = "Spotify playlists, music recommendations, and playlist creation"

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



# Natural Language Processing Functions for ASI:One Chat Integration
def parse_playlist_request(text: str) -> Dict[str, Any]:
    """Parse natural language playlist request with improved logic"""
    text_lower = text.lower()
    
    # Extract playlist name - look for explicit naming patterns
    playlist_name = None
    name_patterns = [
        r"create.*playlist.*called\s+[\"']([^\"']+)[\"']",
        r"make.*playlist.*named\s+[\"']([^\"']+)[\"']",
        r"playlist.*called\s+[\"']([^\"']+)[\"']",
        r"called\s+[\"']([^\"']+)[\"']",
        r"named\s+[\"']([^\"']+)[\"']",
        r"make.*playlist\s+[\"']([^\"']+)[\"']",
        r"create.*[\"']([^\"']+)[\"']\s*playlist",
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text_lower)
        if match:
            playlist_name = match.group(1).title()
            break
    
    # Extract theme/genre - expanded mapping
    theme_genre_mapping = {
        # Genres
        "hip-hop": "hip-hop",
        "hip hop": "hip-hop", 
        "rap": "hip-hop",
        "pop": "pop",
        "rock": "rock",
        "electronic": "electronic",
        "edm": "electronic",
        "chill": "chill",
        "lofi": "chill",
        "lo-fi": "chill",
        
        # Moods/Activities
        "workout": "electronic",
        "gym": "electronic", 
        "exercise": "electronic",
        "fitness": "electronic",
        "study": "chill",
        "studying": "chill",
        "focus": "chill",
        "relax": "chill",
        "relaxing": "chill",
        "ambient": "chill",
        "party": "pop",
        "dance": "electronic",
        "driving": "rock",
        "road trip": "rock",
        "energy": "electronic",
        "upbeat": "pop",
        "mellow": "chill",
        "calm": "chill",
        "peaceful": "chill"
    }
    
    # Find theme/genre
    detected_theme = None
    for keyword, mapped_genre in theme_genre_mapping.items():
        if keyword in text_lower:
            detected_theme = mapped_genre
            break
    
    # Default to hip-hop if no theme is detected
    theme = detected_theme or "hip-hop"
    
    # Extract song count
    song_count = 10  # Default to 10 songs as specified
    count_match = re.search(r'(\d+)\s*songs?', text_lower)
    if count_match:
        song_count = int(count_match.group(1))
        song_count = min(max(song_count, 1), 50)  # Limit between 1-50
    
    # Generate playlist name if not provided
    if not playlist_name:
        theme_names = {
            "hip-hop": "Hip-Hop Vibes",
            "pop": "Pop Hits",
            "rock": "Rock Classics", 
            "electronic": "Electronic Energy",
            "chill": "Chill Vibes"
        }
        
        # Check for specific activity-based names
        if "workout" in text_lower or "gym" in text_lower or "exercise" in text_lower:
            playlist_name = "Workout Vibes"
        elif "study" in text_lower or "focus" in text_lower:
            playlist_name = "Study Flow"
        elif "party" in text_lower:
            playlist_name = "Party Mix"
        elif "relax" in text_lower or "calm" in text_lower:
            playlist_name = "Relaxing Sounds"
        else:
            playlist_name = theme_names.get(theme, "My Playlist")
    
    return {
        "playlist_name": playlist_name,
        "genre": theme,
        "mood": theme,
        "song_count": song_count,
        "original_request": text,
        "theme": theme
    }

async def create_chat_playlist_response(request_data: Dict[str, Any]) -> str:
    """Create a playlist for chat using real Spotify API and return a formatted response"""
    global spotify_client
    
    playlist_name = request_data["playlist_name"]
    genre = request_data["genre"]
    song_count = request_data["song_count"]
    
    if spotify_client is None:
        # Fallback response if Spotify not connected
        return "⚠️ Spotify API not connected. Please authenticate with Spotify to create real playlists."
    
    try:
        # Create real Spotify playlist
        user = spotify_client.current_user()
        user_id = user['id']
        
        # Create the playlist
        playlist_description = f"Auto-generated {genre or 'mixed'} playlist created by Vocal Agent"
        playlist = spotify_client.user_playlist_create(
            user=user_id,
            name=playlist_name,
            public=True,
            description=playlist_description
        )
        
        # Search for tracks based on criteria
        track_uris = []
        search_queries = []
        
        # Build search queries based on theme/genre
        if genre:
            genre_mapping = {
                "hip-hop": "hip hop rap drake kendrick lamar travis scott",
                "electronic": "electronic edm workout gym energy",
                "chill": "chill lofi acoustic relaxing study",
                "pop": "pop mainstream top hits popular",
                "rock": "rock alternative classic rock"
            }
            search_term = genre_mapping.get(genre.lower(), genre)
            search_queries.append(search_term)
            
            # Add additional themed searches for better variety
            if genre.lower() == "hip-hop":
                search_queries.extend(["rap 2020..2024", "hip hop popular"])
            elif genre.lower() == "electronic":
                search_queries.extend(["workout music", "edm hits"])
            elif genre.lower() == "chill":
                search_queries.extend(["lofi hip hop", "acoustic chill"])
            elif genre.lower() == "pop":
                search_queries.extend(["pop hits 2020..2024", "top 40"])
            elif genre.lower() == "rock":
                search_queries.extend(["rock hits", "alternative rock"])
        else:
            # Default to hip-hop searches
            search_queries = ["hip hop rap", "drake kendrick lamar", "popular rap"]
        
        # Search for tracks
        for query in search_queries:
            try:
                results = spotify_client.search(q=query, type='track', limit=song_count)
                for track in results['tracks']['items']:
                    if len(track_uris) < song_count:
                        track_uris.append(track['uri'])
                    else:
                        break
                if len(track_uris) >= song_count:
                    break
            except Exception as e:
                print(f"Search query '{query}' failed: {e}")
                continue
        
        # If we don't have enough tracks, search for popular tracks
        if len(track_uris) < song_count:
            try:
                results = spotify_client.search(q="year:2020-2024", type='track', limit=song_count)
                for track in results['tracks']['items']:
                    if track['uri'] not in track_uris and len(track_uris) < song_count:
                        track_uris.append(track['uri'])
            except Exception as e:
                print(f"Fallback search failed: {e}")
        
        # Add tracks to playlist
        if track_uris:
            spotify_client.playlist_add_items(playlist['id'], track_uris)
        
        # Get detailed track information for response
        playlist_tracks = spotify_client.playlist_tracks(playlist['id'])
        track_details = []
        
        for item in playlist_tracks['items']:
            track = item['track']
            track_details.append({
                "name": track['name'],
                "artist": ", ".join([artist['name'] for artist in track['artists']])
            })
        
        # Format response
        response_parts = [
            f"🎵 I've created your playlist '{playlist['name']}' with {len(track_details)} songs!",
            ""
        ]
        
        if genre:
            response_parts.append(f"Genre: {genre.title()}")
        
        response_parts.extend([
            "",
            "🎶 Tracklist:",
        ])
        
        for i, track in enumerate(track_details[:10], 1):  # Show first 10 tracks
            response_parts.append(f"{i}. {track['name']} - {track['artist']}")
        
        if len(track_details) > 10:
            response_parts.append(f"... and {len(track_details) - 10} more songs!")
        
        response_parts.extend([
            "",
            f"🎧 Playlist URL: {playlist['external_urls']['spotify']}",
            "",
            "Your playlist has been created on your Spotify account! You can now listen to it."
        ])
        
        return "\n".join(response_parts)
        
    except Exception as e:
        print(f"Failed to create real Spotify playlist: {e}")
        # Return error message
        return f"❌ Failed to create playlist: {str(e)}"



async def search_music_chat_response(query: str) -> str:
    """Search for music using real Spotify API and return formatted results for chat"""
    global spotify_client
    
    if spotify_client is None:
        return "⚠️ Spotify API not connected. Please authenticate with Spotify to search for music."
    
    try:
        # Search using Spotify API
        results = spotify_client.search(q=query, type='track', limit=8)
        tracks = results['tracks']['items']
        
        if not tracks:
            return f"🔍 Sorry, I couldn't find any songs matching '{query}'. Try searching for different artists or song titles!"
        
        response_parts = [
            f"🔍 Found {len(tracks)} results for '{query}':",
            ""
        ]
        
        # Show up to 8 results
        for i, track in enumerate(tracks[:8], 1):
            artist_names = ", ".join([artist['name'] for artist in track['artists']])
            response_parts.append(
                f"{i}. {track['name']} - {artist_names}"
            )
        
        return "\n".join(response_parts)
        
    except Exception as e:
        return f"❌ Failed to search for music: {str(e)}"

async def process_user_request_with_ai(ctx: Context, text: str) -> str:
    """Use ASI:One AI to intelligently process user requests and route to appropriate functions"""
    
    try:
        # Use ASI:One to analyze the user's intent and extract structured information
        r = asi_client.chat.completions.create(
            model="asi1-mini",
            messages=[
                {"role": "system", "content": f"""
You are an intelligent music assistant that analyzes user requests and determines what action to take.

Your job is to analyze the user's message and respond with EXACTLY one of these JSON formats:

For PLAYLIST CREATION requests:
{{"action": "create_playlist", "playlist_name": "extracted or generated name", "genre": "hip-hop/pop/rock/electronic/chill", "song_count": number, "theme": "detected theme"}}

For MUSIC SEARCH requests:
{{"action": "search_music", "query": "search terms", "search_type": "track"}}

For MUSIC RECOMMENDATIONS requests:
{{"action": "recommend_music", "context": "workout/study/party/general", "genre": "preferred genre"}}

For PLAYLIST RETRIEVAL requests:
{{"action": "get_playlists", "limit": number, "offset": number}}

For RANDOM SONG FROM PLAYLIST requests:
{{"action": "random_song", "playlist_name": "extracted playlist name"}}

For GENERAL MUSIC HELP:
{{"action": "general_help"}}

For NON-MUSIC topics:
{{"action": "not_music"}}

RULES:
- Default genre is "hip-hop" if none specified
- Default song count is 10 if none specified
- Default playlist limit is 20 if none specified
- Extract playlist names from quotes or recognize "Liked Songs"
- Detect themes: workout→electronic, study→chill, party→pop, etc.
- Only respond with valid JSON, no other text

Examples:
"Create a workout playlist with 15 songs" → {{"action": "create_playlist", "playlist_name": "Workout Vibes", "genre": "electronic", "song_count": 15, "theme": "workout"}}
"Show me my playlists" → {{"action": "get_playlists", "limit": 20, "offset": 0}}
"Give me a song from Liked Songs" → {{"action": "random_song", "playlist_name": "Liked Songs"}}  
"Random song from my rock playlist" → {{"action": "random_song", "playlist_name": "rock playlist"}}
"Find songs by Drake" → {{"action": "search_music", "query": "Drake", "search_type": "track"}}
                """},
                {"role": "user", "content": text},
            ],
            max_tokens=200,
        )
        
        ai_response = str(r.choices[0].message.content).strip()
        ctx.logger.info(f"AI Response: {ai_response}")
        
        # Parse the AI response as JSON
        import json
        try:
            intent = json.loads(ai_response)
        except json.JSONDecodeError:
            ctx.logger.error(f"Failed to parse AI response as JSON: {ai_response}")
            return "I encountered an error processing your request. Please try again!"
        
        # Route to appropriate function based on AI decision
        action = intent.get("action")
        
        if action == "create_playlist":
            # Extract playlist details from AI response
            request_data = {
                "playlist_name": intent.get("playlist_name", "My Playlist"),
                "genre": intent.get("genre", "hip-hop"), 
                "song_count": intent.get("song_count", 10),
                "theme": intent.get("theme", "hip-hop"),
                "original_request": text
            }
            return await create_chat_playlist_response(request_data)
            
        elif action == "search_music":
            search_query = intent.get("query", text)
            return search_music_chat_response(search_query)
            
        elif action == "recommend_music":
            context = intent.get("context", "general")
            genre = intent.get("genre", "hip-hop")
            return await get_music_recommendations_chat_ai(context, genre)
            
        elif action == "get_playlists":
            limit = intent.get("limit", 20)
            offset = intent.get("offset", 0)
            try:
                playlists = await get_user_playlists(ctx, limit=limit, offset=offset)
                return format_playlists_response(playlists)
            except Exception as e:
                return f"❌ Failed to retrieve playlists: {str(e)}"
                
        elif action == "random_song":
            playlist_name = intent.get("playlist_name", "Liked Songs")
            try:
                song_info = await get_random_song_from_playlist(ctx, playlist_name)
                if "error" in song_info:
                    return f"❌ {song_info['error']}"
                else:
                    return format_random_song_response(song_info)
            except Exception as e:
                return f"❌ Failed to get random song: {str(e)}"
            
        elif action == "general_help":
            return """🎵 I'm your Spotify playlist expert! I can help you with:

• 🎼 **Create playlists** - "Create a pop playlist with 20 songs"
• 🔍 **Search music** - "Search for songs by The Weeknd"  
• 💡 **Get recommendations** - "Recommend workout music"
• 📋 **Show playlists** - "Show me my playlists"
• 🎲 **Random songs** - "Give me a song from Liked Songs"

I specialize in genres like Pop, Rock, Hip-Hop, Electronic, and Chill music.

What would you like me to help you with?"""
            
        elif action == "not_music":
            return f"""I am a helpful assistant who only answers questions about {SUBJECT_MATTER}. If you have questions about other topics, I do not know about them.

I can help you create custom playlists, search for music, and provide recommendations across various genres like Pop, Rock, Hip-Hop, Electronic, and Chill.

What music-related task can I help you with today?"""
            
        else:
            return "I'm not sure how to help with that. Could you ask me about creating playlists, searching for music, or getting recommendations?"
            
    except Exception as e:
        ctx.logger.error(f"Error in AI processing: {e}")
        return "I encountered an error processing your request. Please try again!"

async def get_music_recommendations_chat_ai(context: str, genre: str) -> str:
    """Provide music recommendations based on AI-determined context and genre using real Spotify API"""
    global spotify_client
    
    if spotify_client is None:
        return "⚠️ Spotify API not connected. Please authenticate with Spotify to get recommendations."
    
    try:
        # Map context to genre if needed
        context_genre_mapping = {
            "workout": "electronic",
            "study": "chill", 
            "party": "pop",
            "general": genre
        }
        
        final_genre = context_genre_mapping.get(context, genre)
        
        # Search for tracks in the specified genre
        search_query = f"genre:{final_genre}" if final_genre != "general" else "year:2020-2024"
        results = spotify_client.search(q=search_query, type='track', limit=5)
        tracks = results['tracks']['items']
        
        if not tracks:
            return f"🎵 No recommendations found for {context}. Try a different genre or context!"
        
        response_parts = [
            f"🎵 Here are some great {final_genre} recommendations for {context}:",
            ""
        ]
        
        for i, track in enumerate(tracks, 1):
            artist_names = ", ".join([artist['name'] for artist in track['artists']])
            response_parts.append(f"{i}. {track['name']} - {artist_names}")
        
        response_parts.extend([
            "",
            "Would you like me to create a playlist with these songs?"
        ])
        
        return "\n".join(response_parts)
        
    except Exception as e:
        return f"❌ Failed to get recommendations: {str(e)}"


@agent.on_event("startup")
async def startup(ctx: Context):
    """Initialize spotify agent on startup"""
    global spotify_client
    
    ctx.logger.info("Spotify Playlist Agent starting up...")
    ctx.logger.info(f"Agent address: {agent.address}")
    
    # Initialize Spotify Web API client
    try:
        if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
            # Try to use cached credentials first
            auth_manager = SpotifyOAuth(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                redirect_uri=SPOTIFY_REDIRECT_URI,
                scope=SPOTIFY_SCOPE,
                cache_path=".spotify_cache",
                open_browser=False  # Don't open browser automatically in server mode
            )
            
            # Check if we have cached credentials
            token_info = auth_manager.cache_handler.get_cached_token()
            
            if token_info:
                spotify_client = spotipy.Spotify(auth_manager=auth_manager)
                # Test the connection
                user_info = spotify_client.current_user()
                ctx.logger.info(f"Connected to Spotify account: {user_info['display_name']}")
                ctx.logger.info("✅ Real Spotify API integration active!")
            else:
                ctx.logger.warning("No cached Spotify credentials found")
                ctx.logger.info("⚠️  Run Spotify authentication setup first")
                ctx.logger.info("💡 You can use mock data for now, or set up authentication")
                spotify_client = None
            
        else:
            ctx.logger.warning("Spotify credentials not found in environment variables")
            ctx.logger.info("⚠️  Using mock data for demonstrations")
            spotify_client = None
            
    except Exception as e:
        ctx.logger.error(f"Failed to initialize Spotify client: {e}")
        ctx.logger.info("⚠️  Falling back to mock data")
        spotify_client = None
    
    ctx.logger.info("Ready to create playlists and manage music!")




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
    """Create a playlist with songs based on criteria using real Spotify API"""
    
    global spotify_client
    
    if spotify_client is None:
        ctx.logger.warning("Spotify client not initialized")
        raise Exception("Spotify API not available. Please authenticate with Spotify.")
    
    try:
        # Get current user
        user = spotify_client.current_user()
        user_id = user['id']
        
        # Create the playlist
        playlist_description = description or f"Auto-generated playlist with {genre or 'mixed'} music"
        playlist = spotify_client.user_playlist_create(
            user=user_id,
            name=name,
            public=True,
            description=playlist_description
        )
        
        ctx.logger.info(f"Created Spotify playlist: {playlist['name']} (ID: {playlist['id']})")
        
        # Search for tracks based on criteria
        track_uris = []
        search_queries = []
        
        # Build search queries based on genre, mood, and artists
        if genre:
            genre_search_mapping = {
                "hip-hop": ["hip hop", "rap", "drake", "kendrick lamar"],
                "electronic": ["electronic", "edm", "workout", "gym music"],
                "chill": ["chill", "lofi", "acoustic", "relaxing"],
                "pop": ["pop", "mainstream", "top hits", "popular"],
                "rock": ["rock", "alternative", "classic rock"]
            }
            genre_searches = genre_search_mapping.get(genre.lower(), [genre])
            search_queries.extend(genre_searches)
            
        if mood and mood != genre:
            # Map moods to search terms
            mood_terms = {
                "chill": "chill acoustic",
                "workout": "workout high energy",
                "party": "party dance",
                "focus": "instrumental focus",
                "relaxing": "relaxing ambient"
            }
            search_queries.append(mood_terms.get(mood.lower(), mood))
            
        if artists:
            for artist in artists[:3]:  # Limit to 3 artists
                search_queries.append(f"artist:{artist}")
        
        # If no specific criteria, default to hip-hop
        if not search_queries:
            search_queries = ["hip hop", "rap", "popular rap"]
        
        # Search for tracks
        for query in search_queries:
            try:
                results = spotify_client.search(q=query, type='track', limit=max(10, song_count // len(search_queries)))
                for track in results['tracks']['items']:
                    if len(track_uris) < song_count:
                        track_uris.append(track['uri'])
                    else:
                        break
                if len(track_uris) >= song_count:
                    break
            except Exception as e:
                ctx.logger.warning(f"Search query '{query}' failed: {e}")
                continue
        
        # If we don't have enough tracks, search for popular tracks
        if len(track_uris) < song_count:
            try:
                results = spotify_client.search(q="year:2020-2024", type='track', limit=song_count)
                for track in results['tracks']['items']:
                    if track['uri'] not in track_uris and len(track_uris) < song_count:
                        track_uris.append(track['uri'])
            except Exception as e:
                ctx.logger.warning(f"Fallback search failed: {e}")
        
        # Add tracks to playlist in batches (Spotify allows max 100 per batch)
        if track_uris:
            batch_size = 100
            for i in range(0, len(track_uris), batch_size):
                batch = track_uris[i:i + batch_size]
                spotify_client.playlist_add_items(playlist['id'], batch)
            
            ctx.logger.info(f"Added {len(track_uris)} tracks to playlist {name}")
        
        # Get detailed track information for response
        playlist_tracks = spotify_client.playlist_tracks(playlist['id'])
        track_details = []
        
        for item in playlist_tracks['items']:
            track = item['track']
            track_details.append({
                "name": track['name'],
                "artist": ", ".join([artist['name'] for artist in track['artists']]),
                "album": track['album']['name'],
                "spotify_id": track['id'],
                "uri": track['uri']
            })
        
        # Create response data
        playlist_data = {
            "name": playlist['name'],
            "description": playlist['description'],
            "tracks": track_details,
            "total_tracks": len(track_details),
            "genre": genre,
            "mood": mood,
            "created_at": datetime.now().isoformat(),
            "spotify_url": playlist['external_urls']['spotify'],
            "playlist_id": playlist['id'],
            "real_spotify_playlist": True
        }
        
        ctx.logger.info(f"✅ Real Spotify playlist created successfully: {playlist['external_urls']['spotify']}")
        return playlist_data
        
    except Exception as e:
        ctx.logger.error(f"Failed to create Spotify playlist: {e}")
        # Return error information instead of mock data
        raise Exception(f"Spotify playlist creation failed: {str(e)}")



async def search_music_catalog(
    ctx: Context, 
    query: str, 
    search_type: str = "track", 
    limit: int = 20
) -> List[Dict[str, Any]]:
    """Search for music using real Spotify API or fallback to mock data"""
    
    global spotify_client
    
    if spotify_client is None:
        ctx.logger.warning("Spotify client not initialized")
        raise Exception("Spotify API not available. Please authenticate with Spotify.")
    
    try:
        # Search using Spotify API
        results = []
        
        # Perform the search
        search_results = spotify_client.search(q=query, type=search_type, limit=limit)
        
        if search_type == "track":
            for track in search_results['tracks']['items']:
                result = {
                    "type": "track",
                    "name": track['name'],
                    "artist": ", ".join([artist['name'] for artist in track['artists']]),
                    "album": track['album']['name'],
                    "spotify_id": track['id'],
                    "uri": track['uri'],
                    "preview_url": track.get('preview_url'),
                    "external_url": track['external_urls']['spotify'],
                    "popularity": track.get('popularity', 0),
                    "duration_ms": track.get('duration_ms', 0),
                    "real_spotify_result": True
                }
                results.append(result)
        
        elif search_type == "artist":
            for artist in search_results['artists']['items']:
                result = {
                    "type": "artist", 
                    "name": artist['name'],
                    "spotify_id": artist['id'],
                    "uri": artist['uri'],
                    "external_url": artist['external_urls']['spotify'],
                    "followers": artist['followers']['total'],
                    "genres": artist.get('genres', []),
                    "popularity": artist.get('popularity', 0),
                    "real_spotify_result": True
                }
                results.append(result)
        
        elif search_type == "album":
            for album in search_results['albums']['items']:
                result = {
                    "type": "album",
                    "name": album['name'],
                    "artist": ", ".join([artist['name'] for artist in album['artists']]),
                    "spotify_id": album['id'],
                    "uri": album['uri'],
                    "external_url": album['external_urls']['spotify'],
                    "release_date": album.get('release_date'),
                    "total_tracks": album.get('total_tracks', 0),
                    "real_spotify_result": True
                }
                results.append(result)
        
        ctx.logger.info(f"✅ Found {len(results)} real Spotify results for query: {query}")
        return results
        
    except Exception as e:
        ctx.logger.error(f"Spotify search failed: {e}")
        raise Exception(f"Music search failed: {str(e)}")

async def get_user_playlists(ctx: Context, user_id: Optional[str] = None, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    """Retrieve user's playlists using Spotify Web API"""
    global spotify_client
    
    if spotify_client is None:
        ctx.logger.warning("Spotify client not initialized")
        raise Exception("Spotify API not available. Please authenticate with Spotify.")
    
    try:
        # Get current user if user_id not provided
        if user_id is None:
            current_user = spotify_client.current_user()
            user_id = current_user['id']
        
        # Get user's playlists
        playlists_result = spotify_client.user_playlists(user=user_id, limit=limit, offset=offset)
        
        playlists = []
        for playlist in playlists_result['items']:
            playlist_data = {
                "name": playlist['name'],
                "id": playlist['id'],
                "href": playlist['href'],
                "images": playlist.get('images', []),
                "tracks_total": playlist['tracks']['total'],
                "owner_id": playlist['owner']['id'],
                "public": playlist.get('public', True),
                "description": playlist.get('description', ''),
                "external_url": playlist['external_urls']['spotify']
            }
            playlists.append(playlist_data)
        
        ctx.logger.info(f"Retrieved {len(playlists)} playlists for user {user_id}")
        return playlists
        
    except Exception as e:
        ctx.logger.error(f"Failed to retrieve playlists: {e}")
        raise Exception(f"Playlist retrieval failed: {str(e)}")

async def get_random_song_from_playlist(ctx: Context, playlist_identifier: str) -> Dict[str, Any]:
    """
    Retrieve a random song from a playlist.
    
    Args:
        playlist_identifier: Either playlist name or playlist ID
        
    Returns:
        Dict containing song information
    """
    global spotify_client
    
    if spotify_client is None:
        ctx.logger.warning("Spotify client not initialized")
        raise Exception("Spotify API not available. Please authenticate with Spotify.")
    
    try:
        playlist_id = None
        
        # Handle special case for "Liked Songs"
        if playlist_identifier.lower() in ["liked songs", "liked", "saved songs", "saved"]:
            # Get user's saved tracks (Liked Songs)
            saved_tracks = spotify_client.current_user_saved_tracks(limit=50, offset=0)
            
            if not saved_tracks['items']:
                return {
                    "error": "Your Liked Songs playlist is empty!"
                }
            
            # Get total count and select random offset
            total_tracks = saved_tracks['total']
            if total_tracks == 0:
                return {
                    "error": "Your Liked Songs playlist is empty!"
                }
            
            # Select random track from saved tracks
            random_offset = random.randint(0, min(total_tracks - 1, 49))  # Limit to first 50 for simplicity
            if random_offset > 0:
                saved_tracks = spotify_client.current_user_saved_tracks(limit=1, offset=random_offset)
            
            if saved_tracks['items']:
                track = saved_tracks['items'][0]['track']
                artist_names = ", ".join([artist['name'] for artist in track['artists']])
                
                return {
                    "song_name": track['name'],
                    "artist": artist_names,
                    "album": track['album']['name'],
                    "playlist_name": "Liked Songs",
                    "spotify_url": track['external_urls']['spotify'],
                    "preview_url": track.get('preview_url'),
                    "duration_ms": track.get('duration_ms', 0)
                }
        
        # Check if identifier is a playlist ID (starts with alphanumeric and is long)
        if len(playlist_identifier) > 15 and playlist_identifier.replace('_', '').replace('-', '').isalnum():
            playlist_id = playlist_identifier
        else:
            # Search for playlist by name in user's playlists
            user_playlists = await get_user_playlists(ctx, limit=50)
            
            for playlist in user_playlists:
                if playlist['name'].lower() == playlist_identifier.lower():
                    playlist_id = playlist['id']
                    break
            
            if playlist_id is None:
                return {
                    "error": f"Playlist '{playlist_identifier}' not found in your playlists."
                }
        
        # Get playlist tracks
        playlist_tracks = spotify_client.playlist_tracks(playlist_id, limit=100)
        
        if not playlist_tracks['items']:
            return {
                "error": f"The playlist '{playlist_identifier}' is empty!"
            }
        
        # Filter out None tracks (deleted/unavailable songs)
        valid_tracks = [item for item in playlist_tracks['items'] if item['track'] is not None]
        
        if not valid_tracks:
            return {
                "error": f"No available songs found in playlist '{playlist_identifier}'."
            }
        
        # Select random track
        random_track_item = random.choice(valid_tracks)
        track = random_track_item['track']
        
        # Get playlist info for response
        playlist_info = spotify_client.playlist(playlist_id, fields="name")
        
        artist_names = ", ".join([artist['name'] for artist in track['artists']])
        
        return {
            "song_name": track['name'],
            "artist": artist_names,
            "album": track['album']['name'],
            "playlist_name": playlist_info['name'],
            "spotify_url": track['external_urls']['spotify'],
            "preview_url": track.get('preview_url'),
            "duration_ms": track.get('duration_ms', 0)
        }
        
    except Exception as e:
        ctx.logger.error(f"Failed to get random song from playlist: {e}")
        raise Exception(f"Random song retrieval failed: {str(e)}")

def format_playlists_response(playlists: List[Dict[str, Any]]) -> str:
    """Format playlists list into a readable chat response"""
    if not playlists:
        return "📋 You don't have any playlists yet. Create your first playlist!"
    
    response_parts = [
        f"📋 Here are your playlists ({len(playlists)} found):",
        ""
    ]
    
    for i, playlist in enumerate(playlists[:10], 1):  # Show first 10 playlists
        track_count = playlist['tracks_total']
        response_parts.append(
            f"{i}. **{playlist['name']}** - {track_count} songs"
        )
    
    if len(playlists) > 10:
        response_parts.append(f"... and {len(playlists) - 10} more playlists!")
    
    response_parts.extend([
        "",
        "💡 Ask me to get a random song from any playlist by saying:",
        "\"Give me a song from [playlist name]\""
    ])
    
    return "\n".join(response_parts)

def format_random_song_response(song_info: Dict[str, Any]) -> str:
    """Format random song information into a readable chat response"""
    response_parts = [
        f"🎲 Here's a random song from **{song_info['playlist_name']}**:",
        "",
        f"🎵 **{song_info['song_name']}**",
        f"🎤 by {song_info['artist']}",
        f"💿 from {song_info['album']}"
    ]
    
    if song_info.get('duration_ms'):
        duration_seconds = song_info['duration_ms'] // 1000
        minutes = duration_seconds // 60
        seconds = duration_seconds % 60
        response_parts.append(f"⏱️ Duration: {minutes}:{seconds:02d}")
    
    response_parts.extend([
        "",
        f"🎧 [Listen on Spotify]({song_info['spotify_url']})"
    ])
    
    if song_info.get('preview_url'):
        response_parts.append(f"🔊 [Preview]({song_info['preview_url']})")
    
    return "\n".join(response_parts)

# ASI:One Chat Protocol Message Handlers



# ASI:One Chat Protocol Message Handlers
@chat_protocol.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handle chat messages from ASI:One or other agents"""
    # Send acknowledgement for receiving the message
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id),
    )
    
    # Collect up all the text chunks
    text = ''
    for item in msg.content:
        if isinstance(item, TextContent):
            text += item.text
    
    ctx.logger.info(f"Received chat message: {text}")
    
    # Process the request based on Spotify expertise
    response_text = 'I am afraid something went wrong and I am unable to answer your question at the moment'
    
    try:
        # Use AI to intelligently process the user request
        response_text = await process_user_request_with_ai(ctx, text)
    
    except Exception as e:
        ctx.logger.exception('Error processing chat message')
        response_text = "I encountered an error processing your request. Please try again!"
    
    # Send the response back to the user
    await ctx.send(sender, ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=[
            # We send the contents back in the chat message
            TextContent(type="text", text=response_text),
            # We also signal that the session is over
            EndSessionContent(type="end-session"),
        ]
    ))

@chat_protocol.on_message(ChatAcknowledgement)
async def handle_chat_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    """Handle chat acknowledgements"""
    # We are not interested in the acknowledgements for this example, but they can be useful to
    # implement read receipts, for example.
    ctx.logger.info(f"Received acknowledgement from {sender} for message {msg.acknowledged_msg_id}")

# HTTP endpoint handlers for testing (optional)
@agent.on_interval(period=300.0)  # Every 5 minutes
async def log_status(ctx: Context):
    """Periodic status log"""
    ctx.logger.info("Spotify Playlist Agent is running and ready for requests")

# Attach the chat protocol to the agent for ASI:One compatibility
agent.include(chat_protocol, publish_manifest=True)

if __name__ == "__main__":
    print("🎵 Starting Spotify Playlist Agent...")
    print(f"Your agent's address is: {agent.address}")
    
    # Check Spotify credentials
    spotify_status = "🟢 REAL Spotify API" if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET else "🟡 Mock Data Only"
    print(f"Spotify Integration: {spotify_status}")
    
    print("\nAgent capabilities:")
    print("  ✓ Create custom playlists based on genre/mood")
    print("  ✓ Search music catalog")
    print("  ✓ Handle playlist requests from vocal core agent") 
    print("  ✓ Support for multiple music genres and moods")
    print("  ✓ Agentverse integration with mailbox support")
    print("  ✓ ASI:One chat protocol for LLM integration")
    if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
        print("  ✅ Real Spotify API integration enabled!")
    else:
        print("  ⚠️  Using mock data (add Spotify credentials to .env for real integration)")
    print("\nSupported genres: hip-hop, pop, rock, electronic, chill")
    print("\nStarting agent server...")
    print("📱 Connect to Agentverse using the Inspector URL that will appear below:")
    
    agent.run()