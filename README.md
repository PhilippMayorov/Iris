# Iris - Voice-Driven AI Assistant

A voice-driven AI assistant that uses **Fetch.ai uAgents** for autonomous task execution and **Google Gemini** for reasoning. It captures voice input via **ElevenLabs Speech-to-Text API**, interprets user intent using Gemini, and executes actions (e.g., sending emails, managing Spotify playlists, Discord messaging, contact lookup).

## 🏗️ Project Structure

```
Iris/
├── src/agents/new-agents/          # Python backend agents
│   ├── gmail_agent/               # Gmail integration with ASI:One
│   │   ├── gmail_agent.py         # Main Gmail agent
│   │   ├── README.md              # Gmail agent documentation
│   │   └── requirements.txt       # Gmail-specific dependencies
│   ├── spotifyAgent/              # Spotify integration
│   │   ├── spotify_agent.py       # Main Spotify agent
│   │   ├── README.md              # Spotify agent documentation
│   │   └── requirements.txt       # Spotify-specific dependencies
│   ├── discord_agent/             # Discord messaging integration
│   │   ├── discord_agent.py       # Main Discord agent
│   │   ├── README.md              # Discord agent documentation
│   │   └── requirements.txt       # Discord-specific dependencies
│   └── mailbox_agent/             # Mailbox communication agent
│       └── TROUBLESHOOTING.md     # Mailbox agent documentation
│
├── frontend/                       # Flask-based desktop/web interface
│   ├── app.py                     # Main Flask application
│   ├── templates/
│   │   └── index.html             # Siri-like voice interface
│   ├── README.md                  # Frontend documentation
│   ├── CONTACTS_INTEGRATION_GUIDE.md
│   ├── CONTEXT_WINDOW_GUIDE.md
│   └── TTS_README.md              # Text-to-Speech documentation
│
├── src/asi_integration/           # ASI:One integration components
│   ├── asi_client.py              # ASI:One API client
│   ├── agentic_chat.py            # Agentic chat implementation
│   └── README.md                  # ASI integration documentation
│
├── tests/                         # Test suites
│   ├── agents/                    # Agent communication tests
│   │   ├── test_agent_communication.py
│   │   └── test_individual_agents.py
│   └── integration/               # End-to-end integration tests
│       ├── test_voice_to_action_flow.py
│       └── test_frontend_backend_integration.py
│
├── personalities/                 # AI personality configurations
│   ├── creative_collaborator.txt
│   ├── formal_butler.txt
│   ├── friendly_assistant.txt
│   └── README.md                  # Personality documentation
│
├── requirements.txt               # Python dependencies
├── FRONTEND_STARTUP_GUIDE.md     # Frontend startup instructions
├── AI_ROUTING_SYSTEM_SUMMARY.md  # AI routing system documentation
└── README.md                      # This file
```

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys (see configuration section)
```

### 2. Frontend Setup (Flask Desktop/Web App)

```bash
# Start the Flask frontend (desktop app)
./start_frontend.sh

# OR start web interface
./start_frontend_web.sh

# OR manual start
cd frontend
source ../venv/bin/activate
python app.py
```

### 3. Backend Agents Setup

```bash
# Start individual agents (in separate terminals)

# Gmail Agent
cd src/agents/new-agents/gmail_agent
python gmail_agent.py

# Spotify Agent  
cd src/agents/new-agents/spotifyAgent
python spotify_agent.py

# Discord Agent
cd src/agents/new-agents/discord_agent
python discord_agent.py

# OR use the provided startup scripts
./run_gmail_agent_with_env.sh
./run_spotify_agent_with_env.sh
```

## 🔧 Configuration

### Required API Keys

1. **ASI:One API Key** (Required for AI processing)

   - Visit [ASI:One Dashboard](https://asi1.ai/dashboard/api-keys)
   - Create a new API key
   - Add to `.env` as `ASI_ONE_API_KEY`

2. **Google Gemini API Key** (Optional, for fallback)

   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Add to `.env` as `GEMINI_API_KEY`

3. **Gmail API Credentials**

   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Gmail API
   - Create OAuth 2.0 credentials
   - Add credentials to `.env`

4. **Spotify Web API Credentials**
   - Visit [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Create a new app
   - Get Client ID and Client Secret
   - Add to `.env`

5. **Discord OAuth2 Credentials**
   - Visit [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Get Client ID and Client Secret
   - Add to `.env`

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key variables to set:

- `ASI_ONE_API_KEY`: Your ASI:One API key (required)
- `GEMINI_API_KEY`: Your Google Gemini API key (optional)
- `GMAIL_CLIENT_ID`: Google OAuth client ID for Gmail
- `GMAIL_CLIENT_SECRET`: Google OAuth client secret for Gmail
- `SPOTIFY_CLIENT_ID`: Spotify app client ID
- `SPOTIFY_CLIENT_SECRET`: Spotify app client secret
- `SPOTIFY_REDIRECT_URI`: Spotify OAuth redirect URI
- `DISCORD_CLIENT_ID`: Discord app client ID
- `DISCORD_CLIENT_SECRET`: Discord app client secret

## 🎯 Features

### Voice Agent Capabilities

- **AI-Powered Request Routing**: Intelligent request analysis and routing using ASI:One
- **Natural Language Understanding**: Powered by ASI:One and Google Gemini
- **Voice Recognition**: Browser-based Speech-to-Text API
- **Multi-Agent Architecture**: Specialized agents for different tasks
- **Real-time Communication**: uAgents protocol for inter-agent messaging

### Supported Integrations

- 📧 **Gmail**: Compose and send emails with natural language processing
- 🎵 **Spotify**: Create playlists, search music, get recommendations
- 💬 **Discord**: Send direct messages, retrieve conversation history
- 📱 **Contacts**: Lookup contact information from macOS Contacts
- 📝 **Text-to-Speech**: Voice feedback for responses

### Flask Frontend Features

- **Siri-like Interface**: Animated voice input indicator with volume detection
- **Desktop/Web App**: Choose between desktop app or browser interface
- **Integration Management**: Easy setup for external services
- **Real-time Feedback**: Visual and audio feedback for voice commands
- **Cross-platform**: Works on macOS, Windows, and Linux

## 🏃‍♂️ Usage Examples

### Voice Commands

```
"Send an email to Sarah about the project update"
→ Routes to Gmail agent, composes and sends email

"Create a workout playlist with electronic music"
→ Routes to Spotify agent, creates custom playlist

"Send Ben a message saying I'll be late"
→ Routes to Discord agent, sends direct message

"Find Philip's email address"
→ Routes to Contacts service, looks up contact info

"Play some jazz music for focus"
→ Routes to Spotify agent, provides music recommendations
```

### Frontend Usage

1. **Launch the app**: Run `./start_frontend.sh` for desktop app or `./start_frontend_web.sh` for web interface
2. **Start listening**: Click the animated Siri ball
3. **Speak your command**: The AI routing system will determine the best service
4. **Manage integrations**: Click "Integrate with apps" to connect services
5. **View responses**: See real-time feedback and responses in the interface

### AI-Powered Request Routing

The system uses intelligent AI routing to analyze your requests and determine the most appropriate service:

- **Context Awareness**: Understands the intent behind your request
- **Service Selection**: Automatically routes to the right agent (Gmail, Spotify, Discord, Contacts)
- **Fallback Support**: Uses keyword-based detection if AI routing fails
- **Transparent Decisions**: Provides reasoning for routing choices

## 🧪 Testing

### Run Agent Tests

```bash
# Test individual agents
python -m pytest tests/agents/ -v

# Test agent communication
python -m pytest tests/agents/test_agent_communication.py -v
```

### Run Integration Tests

```bash
# Test end-to-end workflows
python -m pytest tests/integration/ -v

# Test frontend-backend integration
python -m pytest tests/integration/test_frontend_backend_integration.py -v
```

## 🏗️ Architecture

### Agent Communication Flow

```
Flask Frontend (Desktop/Web)
    ↓ HTTP/WebSocket
AI Routing System (ASI:One)
    ↓ uAgents Protocol
┌─ gmail_agent.py (Port 8001)
├─ spotify_agent.py (Port 8002) 
├─ discord_agent.py (Port 8005)
└─ mailbox_agent.py (Port 8003)
```

### Key Components

1. **AI Routing System**: Intelligent request analysis using ASI:One to determine the most appropriate service for each request

2. **Specialized Agents**: Handle specific integrations (Gmail, Spotify, Discord, Contacts) with ASI:One natural language processing

3. **Flask Frontend**: Cross-platform desktop/web app with Siri-like voice interface, integration management, and real-time feedback

4. **uAgents Protocol**: Enables secure, decentralized communication between agents

5. **ASI:One Integration**: Provides natural language understanding and intelligent request processing across all agents

## 🚧 Development Status

### ✅ Completed

- [x] Project structure setup
- [x] uAgents framework implementation
- [x] Flask frontend with Siri-like interface
- [x] AI-powered request routing system
- [x] Gmail agent with ASI:One integration
- [x] Spotify agent with playlist management
- [x] Discord agent with OAuth2 messaging
- [x] Contacts integration for macOS
- [x] Text-to-Speech functionality
- [x] Cross-platform desktop/web app
- [x] Integration management system
- [x] Environment configuration
- [x] Startup scripts and automation

### 🔄 In Progress

- [ ] Enhanced error handling and recovery
- [ ] Performance optimization
- [ ] Advanced voice recognition features
- [ ] Multi-user authentication support

### 📋 TODO

- [ ] Calendar integration (Google Calendar)
- [ ] Notes integration (Apple Notes)
- [ ] Advanced voice feedback features
- [ ] Mobile app companion
- [ ] Advanced analytics and monitoring
- [ ] Plugin system for custom integrations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow Python PEP 8 for backend code
- Follow SwiftUI best practices for frontend code
- Add tests for new features
- Update documentation
- Use descriptive commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Fetch.ai** for the uAgents framework
- **ASI:One** for AI-powered natural language processing
- **Google** for Gemini AI and Gmail APIs
- **Spotify** for Web API
- **Discord** for messaging API
- **Apple** for macOS Contacts integration
- **Flask** for the web framework
- **ElevenLabs** for Text-to-Speech capabilities
