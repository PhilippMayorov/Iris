# Spotify Playlist Agent

A specialized uAgent for creating and managing Spotify playlists based on user voice commands.

## Features

- **ASI:One Integration**: Compatible with ASI:One chat interface and discovery
- **Real Spotify API**: Full integration with Spotify Web API for authentic music data
- **Natural Language Processing**: Understands conversational requests with AI-powered intent analysis
- **Playlist Creation**: Creates custom playlists based on genre, mood, or specific requirements
- **Playlist Retrieval**: View and browse your existing Spotify playlists
- **Random Song Selection**: Get random songs from any playlist (including Liked Songs)
- **Music Search**: Searches music catalog for songs, artists, albums using real Spotify data
- **Music Recommendations**: Provides personalized music suggestions for different activities
- **Genre Support**: Pop, Rock, Hip-Hop, Electronic, Chill, and more
- **Chat Protocol**: Uses standardized chat protocol for seamless communication
- **Expert Assistant**: Specialized knowledge in Spotify playlists and music curation

## Supported Commands (Natural Language)

### Playlist Creation

- "Create a pop playlist with 20 songs"
- "Make a chill playlist for studying"
- "Create a workout playlist with electronic music"
- "Make a playlist called 'Road Trip' with rock music"
- "Build me a party playlist"

### Music Search

- "Search for songs by The Weeknd"
- "Find music by Queen"
- "Look for electronic tracks"

### Music Recommendations

- "Recommend workout music"
- "What should I listen to for studying?"
- "Suggest some party songs"
- "Give me recommendations for driving music"

### Playlist Management

- "Show me my playlists"
- "List my Spotify playlists"
- "What playlists do I have?"

### Random Song Selection

- "Give me a song from Liked Songs"
- "Random song from my workout playlist"
- "Pick a song from my chill playlist"
- "Get me a random track from Road Trip"

### ASI:One Discovery Queries

- "Connect me to an agent that creates Spotify playlists"
- "I need help with music recommendations"
- "Find an expert for playlist creation"

## Agent Configuration

- **Name**: spotify_playlist_agent
- **Port**: 8005
- **Endpoint**: http://127.0.0.1:8005/submit

## Message Types

### CreatePlaylistMessage

```python
{
    "playlist_name": "My Playlist",
    "genre": "pop",
    "mood": "chill",
    "song_count": 20,
    "description": "Custom playlist description",
    "request_id": "unique_id"
}
```

### PlaylistResponse

```python
{
    "success": true,
    "message": "Successfully created playlist",
    "playlist_data": {...},
    "request_id": "unique_id"
}
```

## Integration

This agent is designed to work with the Vocal Agent ecosystem and Agentverse:

- **Local Agent**: Runs locally with mailbox integration to Agentverse
- **Agentverse Ready**: Configured with `mailbox=True` and `publish_agent_details=True`
- **Inter-agent Communication**: Receives requests from `vocal_core_agent`
- **Playlist Processing**: Handles playlist creation commands via uAgents messaging
- **Response System**: Returns structured responses with playlist data

## Agentverse Deployment

This agent is configured as a Mailbox Agent for Agentverse integration:

1. **Run locally**: `python spotify_agent.py`
2. **Copy the agent address** from the console output
3. **Connect to Agentverse** using the Inspector URL provided
4. **Create a Mailbox** in Agentverse to enable cloud communication
5. **Interact with other agents** through Agentverse platform

### Agent Configuration

- **Mailbox**: Enabled (`mailbox=True`)
- **Publishing**: Agent details published to Agentverse
- **README**: Automatically published for documentation

## Usage Examples

Send messages to this agent using the following formats:

### Create Playlist

```python
CreatePlaylistMessage(
    playlist_name="Summer Hits",
    genre="pop",
    song_count=25,
    description="Perfect songs for summer",
    request_id="req_123"
)
```

### Search Music

```python
SearchMusicMessage(
    query="The Weeknd",
    search_type="artist",
    limit=10,
    request_id="req_124"
)
```

## Recent Updates

- ✅ **Real Spotify API Integration**: Full authentication and playlist management
- ✅ **Playlist Retrieval**: Browse and view your existing Spotify playlists
- ✅ **Random Song Selection**: Get random songs from any playlist including Liked Songs
- ✅ **AI-Powered Intent Analysis**: ASI:One integration for intelligent request processing
- ✅ **Enhanced Error Handling**: Graceful handling of API errors and edge cases

## Future Enhancements

- Advanced music recommendation algorithms with user listening history
- Collaborative playlist features and sharing
- Playlist analytics and insights
- Integration with other music services
- Direct Agentverse hosted deployment option
