# Spotify Playlist Agent

A specialized uAgent for creating and managing Spotify playlists based on user voice commands.

## Features

- **Playlist Creation**: Creates custom playlists based on genre, mood, or specific requirements
- **Music Search**: Searches music catalog for songs, artists, albums
- **Genre Support**: Pop, Rock, Hip-Hop, Electronic, Chill, and more
- **Voice Integration**: Responds to natural language commands from the vocal core agent

## Supported Commands

- "Create a pop playlist with 20 songs"
- "Make a chill playlist for studying"
- "Create a workout playlist with electronic music"
- "Search for songs by The Weeknd"
- "Make a playlist called 'Road Trip' with rock music"

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

## Future Enhancements

- Real Spotify Web API integration
- User authentication and personal playlists
- Advanced music recommendation algorithms
- Collaborative playlist features
- Direct Agentverse hosted deployment option
