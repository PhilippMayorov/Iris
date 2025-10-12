# Spotify Agent HTTP Endpoints Guide

## Overview

The Spotify Agent now supports HTTP endpoints for natural language interaction. You can send requests directly to the agent using REST API calls.

## Base URL

```
http://localhost:8005
```

## Available Endpoints

### 1. Chat Endpoint (Natural Language)

**POST** `/chat`

Send natural language requests to the Spotify agent.

#### Request Body
```json
{
  "text": "Create a pop playlist with 20 songs"
}
```

#### Response
```json
{
  "success": true,
  "message": "🎵 I've created your playlist 'Pop Hits' with 20 songs!\n\nGenre: Pop\n\n🎶 Tracklist:\n1. Song Name - Artist Name\n2. Another Song - Another Artist\n...\n\n🎧 Playlist URL: https://open.spotify.com/playlist/...",
  "request_id": "unique-request-id"
}
```

#### Example cURL Commands

```bash
# Create a playlist
curl -X POST http://localhost:8005/chat \
  -H "Content-Type: application/json" \
  -d '{"text": "Create a workout playlist with 15 songs"}'

# Search for music
curl -X POST http://localhost:8005/chat \
  -H "Content-Type: application/json" \
  -d '{"text": "Search for songs by The Weeknd"}'

# Get recommendations
curl -X POST http://localhost:8005/chat \
  -H "Content-Type: application/json" \
  -d '{"text": "Recommend study music"}'

# Show playlists
curl -X POST http://localhost:8005/chat \
  -H "Content-Type: application/json" \
  -d '{"text": "Show me my playlists"}'

# Get random song
curl -X POST http://localhost:8005/chat \
  -H "Content-Type: application/json" \
  -d '{"text": "Give me a song from Liked Songs"}'
```

### 2. Capabilities Endpoint

**GET** `/capabilities`

Get information about the agent's capabilities and supported commands.

#### Response
```json
{
  "agent_name": "Spotify Playlist Agent",
  "capabilities": [
    "Create custom playlists based on genre/mood",
    "Search music catalog",
    "Get music recommendations",
    "Retrieve user playlists",
    "Get random songs from playlists",
    "Natural language processing"
  ],
  "supported_genres": ["hip-hop", "pop", "rock", "electronic", "chill"],
  "example_commands": [
    "Create a pop playlist with 20 songs",
    "Search for songs by The Weeknd",
    "Recommend workout music",
    "Show me my playlists",
    "Give me a song from Liked Songs"
  ],
  "endpoints": {
    "chat": "POST /chat - Send natural language requests",
    "capabilities": "GET /capabilities - Get this information",
    "health": "GET /health - Check agent status"
  }
}
```

#### Example cURL Command

```bash
curl -X GET http://localhost:8005/capabilities
```

### 3. Health Check Endpoint

**GET** `/health`

Check the agent's status and Spotify API connection.

#### Response
```json
{
  "status": "healthy",
  "agent_address": "agent1q...",
  "spotify_api": "connected",
  "timestamp": 1703123456
}
```

#### Example cURL Command

```bash
curl -X GET http://localhost:8005/health
```

## Natural Language Commands

The agent understands these types of natural language requests:

### 🎵 Playlist Creation
- "Create a pop playlist with 20 songs"
- "Make a chill playlist for studying"
- "Create a workout playlist with electronic music"
- "Make a playlist called 'Road Trip' with rock music"
- "Build me a party playlist"

### 🔍 Music Search
- "Search for songs by The Weeknd"
- "Find music by Queen"
- "Look for electronic tracks"
- "Search for Drake songs"

### 💡 Music Recommendations
- "Recommend workout music"
- "What should I listen to for studying?"
- "Suggest some party songs"
- "Give me recommendations for driving music"

### 📋 Playlist Management
- "Show me my playlists"
- "List my Spotify playlists"
- "What playlists do I have?"

### 🎲 Random Song Selection
- "Give me a song from Liked Songs"
- "Random song from my workout playlist"
- "Pick a song from my chill playlist"
- "Get me a random track from Road Trip"

## Supported Genres

- **Hip-Hop**: "hip-hop", "rap", "hip hop"
- **Pop**: "pop", "mainstream", "top hits"
- **Rock**: "rock", "alternative", "classic rock"
- **Electronic**: "electronic", "edm", "workout", "gym music"
- **Chill**: "chill", "lofi", "acoustic", "relaxing", "study"

## Error Handling

If an error occurs, the response will include:

```json
{
  "success": false,
  "message": "Error processing request: [error details]",
  "request_id": "unique-request-id"
}
```

## Authentication

The agent requires Spotify API credentials to be configured in your environment:

```bash
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=your_redirect_uri
```

## Running the Agent

1. Start the agent:
```bash
cd /Users/benpetlach/Desktop/dev/hackathons/hd4/Iris/src/agents/new-agents/spotifyAgent
python spotify_agent.py
```

2. The agent will start on port 8005 and display the endpoints:
```
🎵 Starting Spotify Playlist Agent...
Your agent's address is: agent1q...
Spotify Integration: 🟢 REAL Spotify API
Starting agent server...
```

3. Test the endpoints using the cURL commands above.

## Integration Examples

### Python Client
```python
import requests

# Send a natural language request
response = requests.post(
    "http://localhost:8005/chat",
    json={"text": "Create a pop playlist with 10 songs"}
)

result = response.json()
print(result["message"])
```

### JavaScript/Node.js Client
```javascript
const response = await fetch('http://localhost:8005/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    text: 'Create a workout playlist with 15 songs'
  })
});

const result = await response.json();
console.log(result.message);
```

## Notes

- The agent uses AI-powered natural language processing to understand requests
- All playlist operations use the real Spotify API (when authenticated)
- Responses include Spotify URLs for direct access to created playlists
- The agent supports both specific and general music requests
- Error messages are user-friendly and provide guidance
