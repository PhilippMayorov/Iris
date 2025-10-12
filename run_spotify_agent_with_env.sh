#!/bin/bash
# Script to run Spotify Agent with proper environment variable loading

echo "🎵 Starting Spotify Agent with environment variables..."
echo "📁 Loading environment variables from .env file..."

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Environment variables loaded from .env file"
else
    echo "❌ .env file not found!"
    echo "Please make sure .env file exists in the current directory"
    exit 1
fi

# Check if ASI:One API key is loaded
if [ -n "$ASI_ONE_API_KEY" ]; then
    echo "✅ ASI:One API key loaded successfully"
    echo "🔑 API key starts with: ${ASI_ONE_API_KEY:0:10}..."
else
    echo "❌ ASI:One API key not found in .env file"
    echo "Please make sure ASI_ONE_API_KEY is set in your .env file"
    exit 1
fi

# Check if Spotify credentials are loaded
if [ -n "$SPOTIFY_CLIENT_ID" ] && [ -n "$SPOTIFY_CLIENT_SECRET" ]; then
    echo "✅ Spotify API credentials loaded successfully"
    echo "🎧 Client ID starts with: ${SPOTIFY_CLIENT_ID:0:10}..."
    echo "🔐 Client Secret starts with: ${SPOTIFY_CLIENT_SECRET:0:10}..."
else
    echo "⚠️ Spotify API credentials not found in .env file"
    echo "The agent will run with limited functionality (mock data only)"
    echo "To enable full Spotify integration, add these to your .env file:"
    echo "  SPOTIFY_CLIENT_ID=your_spotify_client_id"
    echo "  SPOTIFY_CLIENT_SECRET=your_spotify_client_secret"
    echo "  SPOTIFY_REDIRECT_URI=your_redirect_uri"
    echo ""
fi

# Check if Spotify redirect URI is set
if [ -n "$SPOTIFY_REDIRECT_URI" ]; then
    echo "✅ Spotify redirect URI configured: $SPOTIFY_REDIRECT_URI"
else
    echo "⚠️ SPOTIFY_REDIRECT_URI not set, using default"
fi

# Activate virtual environment
echo "🐍 Activating virtual environment..."
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️ Virtual environment not found, continuing without it..."
fi

echo "🤖 Starting Spotify Agent..."
echo "🌐 Agent will be available at: http://localhost:8005"
echo "📡 HTTP Endpoints:"
echo "  - POST /chat (natural language requests)"
echo "  - GET /capabilities (agent info)"
echo "  - GET /health (status check)"
echo ""

# Change to Spotify agent directory and run it
cd src/agents/new-agents/spotifyAgent
python spotify_agent.py
