# Vocal Agent

A voice-driven AI assistant that uses **Fetch.ai uAgents** for autonomous task execution and **Google Gemini** for reasoning. It captures voice input via **ElevenLabs Speech-to-Text API**, interprets user intent using Gemini, and executes actions (e.g., scheduling events, sending emails, creating notes).

## 🏗️ Project Structure

```
VocalAgent/
├── src/agents/                     # Python backend agents
│   ├── vocal_core_agent.py        # Central orchestrator
│   ├── calendar_agent.py          # Google Calendar integration
│   ├── email_agent.py             # Gmail integration
│   ├── notes_agent.py             # Notes integration
│   └── spotify_agent.py           # Spotify integration
│
├── mac-app/                        # SwiftUI native macOS app
│   ├── VocalAgent.xcodeproj/       # Xcode project
│   ├── App.swift                   # Main app entry point
│   ├── ContentView.swift           # Main interface
│   ├── SiriAnimatedBall.swift      # Animated voice component
│   ├── IntegrationsPopover.swift   # Integration selector
│   ├── VoiceAgentManager.swift     # Voice processing manager
│   ├── IntegrationManager.swift    # Integration management
│   └── README.md                   # SwiftUI app documentation
│
├── tests/                          # Test suites
│   ├── agents/                     # Agent communication tests
│   │   ├── test_agent_communication.py
│   │   └── test_individual_agents.py
│   └── integration/                # End-to-end integration tests
│       ├── test_voice_to_action_flow.py
│       └── test_frontend_backend_integration.py
│
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment configuration template
└── README.md                       # This file
```

## 🚀 Quick Start

### 1. Backend Setup (Python Agents)

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys (see configuration section)

# Start the central orchestrator
python src/agents/vocal_core_agent.py

# In separate terminals, start specialized agents
python src/agents/calendar_agent.py
python src/agents/email_agent.py
python src/agents/notes_agent.py
python src/agents/spotify_agent.py
```

### 2. Frontend Setup (SwiftUI Mac App)

```bash
# Open the Xcode project
open mac-app/VocalAgent.xcodeproj

# Build and run the app in Xcode
# Or use command line:
xcodebuild -project mac-app/VocalAgent.xcodeproj -scheme VocalAgent -configuration Debug
```

## 🔧 Configuration

### Required API Keys

1. **Google Gemini API Key**

   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Add to `.env` as `GEMINI_API_KEY`

2. **ElevenLabs Speech-to-Text API Key**

   - Sign up at [ElevenLabs](https://elevenlabs.io/)
   - Get your API key from the dashboard
   - Add to `.env` as `ELEVENLABS_API_KEY`

3. **Google Calendar/Gmail API Credentials**

   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Calendar API and Gmail API
   - Create OAuth 2.0 credentials
   - Add credentials to `.env`

4. **Spotify Web API Credentials**
   - Visit [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Create a new app
   - Get Client ID and Client Secret
   - Add to `.env`

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key variables to set:

- `GEMINI_API_KEY`: Your Google Gemini API key
- `ELEVENLABS_API_KEY`: Your ElevenLabs API key
- `GOOGLE_CALENDAR_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CALENDAR_CLIENT_SECRET`: Google OAuth client secret
- `SPOTIFY_CLIENT_ID`: Spotify app client ID
- `SPOTIFY_CLIENT_SECRET`: Spotify app client secret

## 🎯 Features

### Voice Agent Capabilities

- **Natural Language Understanding**: Powered by Google Gemini
- **Voice Recognition**: ElevenLabs Speech-to-Text API
- **Multi-Agent Architecture**: Specialized agents for different tasks
- **Real-time Communication**: uAgents protocol for inter-agent messaging

### Supported Integrations

- 🗓️ **Google Calendar**: Schedule meetings, check availability, manage events
- 📧 **Gmail**: Compose and send emails, read inbox, organize messages
- 📝 **Notes**: Create, search, and organize notes (Apple Notes integration)
- 🎵 **Spotify**: Control music playback, search tracks, manage playlists

### SwiftUI Mac App Features

- **Siri-like Interface**: Animated voice input indicator
- **Integration Management**: Easy setup for external services
- **Real-time Feedback**: Visual and audio feedback for voice commands
- **Native macOS Experience**: Optimized for Mac with system integrations

## 🏃‍♂️ Usage Examples

### Voice Commands

```
"Schedule a meeting with John tomorrow at 2 PM"
→ Creates calendar event via calendar_agent

"Send an email to Sarah about the project update"
→ Composes and sends email via email_agent

"Create a note about today's brainstorming session"
→ Creates note via notes_agent

"Play some jazz music for focus"
→ Starts Spotify playback via spotify_agent
```

### Mac App Usage

1. **Launch the app**: Click the app icon or use Spotlight
2. **Start listening**: Click the animated Siri ball or use Cmd+Space
3. **Speak your command**: The app will process and execute your request
4. **Manage integrations**: Click "Integrate with apps" to connect services

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
Mac App (SwiftUI)
    ↓ HTTP/WebSocket
vocal_core_agent.py (Port 8000)
    ↓ uAgents Protocol
┌─ calendar_agent.py (Port 8001)
├─ email_agent.py (Port 8002)
├─ notes_agent.py (Port 8003)
└─ spotify_agent.py (Port 8004)
```

### Key Components

1. **vocal_core_agent**: Central orchestrator that receives voice commands, uses Gemini for intent recognition, and delegates tasks to specialized agents

2. **Specialized Agents**: Handle specific integrations (calendar, email, notes, Spotify) and communicate back with results

3. **SwiftUI Frontend**: Native Mac app with voice interface, integration management, and real-time feedback

4. **uAgents Protocol**: Enables secure, decentralized communication between agents

## 🚧 Development Status

### ✅ Completed

- [x] Project structure setup
- [x] Agent framework implementation
- [x] SwiftUI app with Siri-like interface
- [x] Integration management system
- [x] Test suite structure
- [x] Environment configuration

### 🔄 In Progress

- [ ] Google Gemini integration
- [ ] ElevenLabs Speech-to-Text integration
- [ ] Google Calendar API implementation
- [ ] Gmail API implementation
- [ ] Spotify Web API integration

### 📋 TODO

- [ ] Apple Notes integration
- [ ] Voice feedback (Text-to-Speech)
- [ ] Authentication flows
- [ ] Error handling and recovery
- [ ] Performance optimization
- [ ] Documentation and tutorials

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
- **Google** for Gemini AI and Calendar/Gmail APIs
- **ElevenLabs** for Speech-to-Text API
- **Spotify** for Web API
- **Apple** for SwiftUI and macOS integration capabilities
