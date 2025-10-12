# 🎵 Spotify ASI:One Agent Setup Guide

This guide shows you how to set up your Spotify Agent to work with ASI:One's chat interface.

## 🚀 Quick Start

### Prerequisites

1. **ASI:One API Key**: Get one from [asi1.ai](https://asi1.ai/dashboard/api-keys)
2. **Agentverse Account**: Sign up at [agentverse.ai](https://agentverse.ai)
3. **uAgents Library**: Install with `pip install uagents`

### Option 1: ASI:One Compatible Agent (Recommended)

Use the new ASI:One compatible version:

```bash
cd spotifyAgent
python spotify_asi_one_agent.py
```

**Key Features:**

- ✅ Chat protocol integration
- ✅ Natural language processing
- ✅ ASI:One discovery compatibility
- ✅ Conversational playlist creation

### Option 2: Original Agent (Legacy)

Use the original agent for direct communication:

```bash
cd spotifyAgent
python spotify_agent.py
```

## 🔧 Configuration

### Agent Settings

- **Name**: `spotify-playlist-expert`
- **Port**: `8006` (ASI:One version) / `8005` (Original)
- **Mailbox**: Enabled for Agentverse integration
- **Chat Protocol**: Fully compatible with ASI:One

### Connecting to ASI:One

1. **Start the agent**:

   ```bash
   python spotify_asi_one_agent.py
   ```

2. **Copy the agent address** from the console output

3. **Create a mailbox**:

   - Click the Inspector URL in the console
   - Select "Connect" → "Mailbox"
   - Complete the setup wizard

4. **Test with ASI:One Chat**:
   - Go to [ASI:One Chat](https://chat.asi1.ai)
   - Ask: _"Connect me to an agent that creates Spotify playlists"_
   - Enable the "Agents" toggle
   - Look for your agent in the results

## 🎯 ASI:One Discovery

Your agent will be discoverable through queries like:

### Playlist Creation

- _"I need help creating a Spotify playlist"_
- _"Connect me to a playlist expert"_
- _"Find an agent that makes music playlists"_

### Music Recommendations

- _"I want music recommendations"_
- _"Help me find new songs"_
- _"Connect me to a music expert"_

### Genre Specific

- _"I need pop music suggestions"_
- _"Find an agent for electronic music"_
- _"Help with rock playlist creation"_

## 💬 Chat Examples

Once connected through ASI:One, you can have natural conversations:

**User**: _"Create a workout playlist with 15 electronic songs"_

**Agent**: _🎵 I've created your playlist 'My Playlist' with 15 songs!_

_Genre: Electronic_

_🎶 Tracklist:_
_1. Titanium - David Guetta ft. Sia_
_2. Wake Me Up - Avicii_
_3. Clarity - Zedd ft. Foxes_
_..._

**User**: _"Search for songs by The Weeknd"_

**Agent**: _🔍 Found 2 results for 'The Weeknd':_

_1. Blinding Lights - The Weeknd (Pop)_
_2. Save Your Tears - The Weeknd (Pop)_

## 🛠 Technical Details

### Chat Protocol Integration

```python
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

# Protocol setup
protocol = Protocol(spec=chat_protocol_spec)
agent.include(protocol, publish_manifest=True)
```

### Natural Language Processing

The agent parses requests for:

- **Playlist names**: _"playlist called 'Summer Hits'"_
- **Genres**: _"pop"_, _"rock"_, _"electronic"_, etc.
- **Moods/Activities**: _"workout"_, _"study"_, _"party"_, etc.
- **Song counts**: _"20 songs"_, _"15 tracks"_

### Response Format

- Structured text responses with emojis
- Track listings with artist information
- Mock Spotify URLs for playlists
- Session management with `EndSessionContent`

## 🔍 Troubleshooting

### Agent Not Discoverable

1. Ensure agent is running with mailbox enabled
2. Check that `publish_agent_details=True`
3. Verify the README.md is in the same directory
4. Confirm the agent has registered successfully

### Chat Not Working

1. Verify chat protocol imports are correct
2. Check that the protocol is attached: `agent.include(protocol, publish_manifest=True)`
3. Ensure message handlers are properly decorated
4. Look for error messages in the console

### Connection Issues

1. Check your internet connection
2. Verify Agentverse API access
3. Ensure no firewall blocking
4. Try restarting the agent

## 🎉 Success Metrics

Your agent is working correctly when you see:

- ✅ Agent registers successfully with Agentverse
- ✅ Manifest published: `AgentChatProtocol`
- ✅ Mailbox connection established
- ✅ Agent appears in ASI:One search results
- ✅ Natural language conversations work smoothly

## 📚 Next Steps

1. **Customize the music database** with your preferred tracks
2. **Add real Spotify API integration** for live playlist creation
3. **Enhance NLP capabilities** for more complex requests
4. **Monitor usage** through Agentverse dashboard
5. **Scale for production** with proper error handling

Your Spotify Agent is now ready to be discovered and used through ASI:One! 🎵
