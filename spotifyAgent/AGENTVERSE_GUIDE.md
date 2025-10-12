# Spotify Agent - Agentverse Deployment Guide

This directory contains two versions of the Spotify Playlist Agent optimized for different deployment scenarios on Agentverse.

## 📁 Files Overview

- **`spotify_agent.py`** - Mailbox Agent (runs locally, connects to Agentverse)
- **`spotify_agent_hosted.py`** - Hosted Agent (runs entirely on Agentverse)
- **`README.md`** - Main documentation
- **`AGENTVERSE_GUIDE.md`** - This deployment guide

## 🚀 Deployment Options

### Option 1: Mailbox Agent (Recommended)

**Best for**: Local development with Agentverse integration

1. **Run locally**:
   ```bash
   cd spotifyAgent
   python spotify_agent.py
   ```

2. **Copy the agent address** from console output

3. **Connect to Agentverse**:
   - Click the Inspector URL in the console
   - Click "Connect" → "Mailbox"
   - Follow the setup wizard

4. **Agent Benefits**:
   - ✅ Full Python library access
   - ✅ Local debugging and development
   - ✅ Agentverse integration via mailbox
   - ✅ Can interact with other Agentverse agents

### Option 2: Hosted Agent

**Best for**: Production deployment on Agentverse cloud

1. **Go to Agentverse**: https://agentverse.ai

2. **Create New Agent**:
   - Navigate to "Agents" tab
   - Click "+ Launch an Agent"
   - Choose "Create an Agentverse hosted Agent"
   - Select "Blank Agent"

3. **Copy the code**:
   - Copy content from `spotify_agent_hosted.py`
   - Paste into the Agentverse code editor

4. **Configure Agent**:
   - Set name: `spotify_playlist_agent_hosted`
   - Click "Start" to deploy

5. **Agent Benefits**:
   - ✅ Always running (no uptime management)
   - ✅ Cloud-hosted and scalable
   - ✅ Easy to share and collaborate
   - ✅ Integrated with Agentverse ecosystem

## 🎵 Using the Agent

### Create Playlist Message
```python
{
    "playlist_name": "My Summer Playlist",
    "genre": "pop",
    "song_count": 20,
    "description": "Perfect summer vibes"
}
```

### Search Music Message
```python
{
    "query": "The Weeknd",
    "search_type": "artist",
    "limit": 10
}
```

## 🔗 Integration with Other Agents

Both versions support inter-agent communication:

```python
# From another agent, send a message:
from uagents import Context

async def request_playlist(ctx: Context):
    playlist_request = CreatePlaylistRequest(
        playlist_name="Workout Mix",
        genre="electronic",
        song_count=15
    )
    
    # Replace with actual agent address
    spotify_agent_address = "agent1q..."
    await ctx.send(spotify_agent_address, playlist_request)
```

## 🛠 Supported Libraries

### Mailbox Agent (`spotify_agent.py`)
- All Python built-in libraries
- Custom imports and dependencies
- Full uAgents framework features

### Hosted Agent (`spotify_agent_hosted.py`)
- Python built-in library
- Agentverse supported packages:
  - `uagents`
  - `pydantic` 
  - `requests`
  - And others listed in Agentverse documentation

## 🎯 Supported Genres

Both agents support:
- **Pop**: Mainstream hits and chart-toppers
- **Rock**: Classic and modern rock anthems
- **Hip-Hop**: Rap and hip-hop tracks
- **Electronic**: EDM, house, and electronic music
- **Chill**: Relaxing and ambient tracks

## 🔍 Testing

Test locally before deploying:

```bash
# Test the mailbox version
python spotify_agent.py

# Test the hosted version locally
python spotify_agent_hosted.py

# Run test suite
python test_spotify_agent.py
```

## 📱 Next Steps

1. **Choose your deployment method** (Mailbox or Hosted)
2. **Deploy the agent** following the steps above
3. **Get the agent address** from console/Agentverse
4. **Integrate with your vocal core agent** by updating the agent addresses
5. **Test playlist creation** with voice commands

## 🎉 Success!

Your Spotify Agent is now ready to:
- ✅ Create playlists from voice commands
- ✅ Search music catalogs
- ✅ Integrate with Agentverse ecosystem
- ✅ Communicate with other agents

For support, check the Agentverse documentation or the main README.md file.