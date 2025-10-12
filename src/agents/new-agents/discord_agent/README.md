# Discord Agent - Enhanced OAuth2 & Messaging Integration

A comprehensive uAgent for Discord messaging with OAuth2 authentication, direct messaging capabilities, and advanced natural language processing using ASI:One.

## 🚀 Key Features

- **🔐 Discord OAuth2 Authentication**: Secure user account integration with token management
- **💬 Direct Message Sending**: Send DMs to users by username or user ID
- **📨 Message Retrieval**: Fetch conversation history and recent messages
- **🧠 AI-Powered Command Processing**: Natural language interpretation using ASI:One LLM
- **🔒 Secure Token Storage**: Encrypted credential management with auto-refresh
- **⚡ Real-time Communication**: Instant messaging through Discord's REST API

## 🎯 Supported Operations

### Discord Authentication

- OAuth2 flow for user account access
- Secure token storage and automatic refresh
- Multi-user authentication support
- Session management and validation

### Messaging Capabilities

- **Send Direct Messages**: `"Send Ben: I'll be late for the meeting"`
- **Retrieve Message History**: `"Show my last 10 messages from Alice"`
- **Bulk Messaging**: `"Text everyone in my DMs: Meeting canceled"`
- **User Discovery**: Find Discord users by username or ID

### AI-Powered Natural Language Processing

- Intent extraction from conversational requests
- Command parameter parsing (recipient, message content, etc.)
- Context-aware response generation
- Error handling and user guidance

## Agent Configuration

- **Name**: discord_agent
- **Port**: 8005
- **Subject Matter**: "texting users and retrieving messages on discord"
- **Mailbox**: Enabled for Agentverse integration
- **Chat Protocol**: Compatible with ASI:One chat interface

## 🔧 Environment Configuration

Create a `.env` file in the agent directory with the following required variables:

```env
# ASI:One API Configuration (Required for AI processing)
ASI_ONE_API_KEY=your_asi_one_api_key_here

# Discord OAuth2 Configuration (Required for Discord integration)
DISCORD_CLIENT_ID=your_discord_application_client_id
DISCORD_CLIENT_SECRET=your_discord_application_client_secret
DISCORD_REDIRECT_URI=http://localhost:8080/callback

# Security Configuration (Auto-generated if not provided)
ENCRYPTION_KEY=your_32_character_encryption_key_for_tokens
```

### Discord Application Setup

1. **Create Discord Application**:

   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Click "New Application" and give it a name
   - Navigate to "OAuth2" section

2. **Configure OAuth2**:

   - Add redirect URI: `http://localhost:8080/callback`
   - Note down Client ID and Client Secret
   - **Important**: Some scopes require Discord approval:
     - ✅ `identify` - Basic user info (no approval needed)
     - ✅ `guilds` - User's servers (no approval needed)
     - ⚠️ `messages.read` - Read messages (requires Discord approval)
     - ⚠️ `dm_channels.read` - Read DM channels (requires Discord approval)

3. **Security Setup**:
   - Generate encryption key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
   - Add to `.env` file for secure token storage

## 📦 Installation & Setup

### 1. Install Dependencies

```bash
# Navigate to the Discord agent directory
cd src/agents/new-agents/discord_agent

# Install required packages
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
# Create environment file
cp .env.example .env  # or create new .env file

# Edit .env with your credentials
nano .env
```

Required environment variables:

- `ASI_ONE_API_KEY`: Get from [ASI:One Dashboard](https://asi1.ai/dashboard/api-keys)
- `DISCORD_CLIENT_ID`: From Discord Developer Portal
- `DISCORD_CLIENT_SECRET`: From Discord Developer Portal
- `DISCORD_REDIRECT_URI`: OAuth callback URL (default: `http://localhost:8080/callback`)

### 3. Run the Agent

```bash
# Start the Discord agent
python discord_agent.py
```

The agent will:

- ✅ Load environment variables
- 🔐 Initialize OAuth2 authentication
- 🚀 Start listening for chat messages
- 📝 Display authentication URL if needed

## 💬 Usage Examples

### Natural Language Commands

The agent understands conversational requests and automatically extracts intent:

#### Sending Messages

```
"Send Ben a message saying I'll be late"
→ Extracts: recipient="Ben", message="I'll be late"
→ Sends DM to Ben

"Text Alice: Meeting moved to 3pm"
→ Extracts: recipient="Alice", message="Meeting moved to 3pm"
→ Sends DM to Alice

"DM John saying can you call me?"
→ Extracts: recipient="John", message="can you call me?"
→ Sends DM to John
```

#### Retrieving Messages

```
"Show my last message from Ben"
→ Extracts: target="Ben", limit=1
→ Retrieves latest message from Ben

"Get my last 5 messages from Alice"
→ Extracts: target="Alice", limit=5
→ Retrieves 5 recent messages from Alice

"What did Sarah say?"
→ Extracts: target="Sarah", limit=10
→ Retrieves recent messages from Sarah
```

#### General Help

```
"What can you do?"
"Help me with Discord"
"Connect my Discord account"
```

### Authentication Flow

#### First Time Setup

1. **Start the agent**: `python discord_agent.py`
2. **Copy the OAuth URL** from the console output
3. **Visit the URL** in your browser
4. **Authorize the application** with your Discord account
5. **Complete the callback** (tokens are automatically saved)

#### Subsequent Usage

- Tokens are automatically loaded and refreshed
- No re-authentication needed unless tokens expire
- Agent displays current authenticated user on startup

### Agentverse Cloud Deployment

Deploy to Agentverse for 24/7 availability:

1. **Local Testing**: `python discord_agent.py`
2. **Copy Agent Address**: Note the address from console output
3. **Agentverse Upload**: Use the Inspector URL to deploy
4. **Mailbox Configuration**: Set up cloud messaging
5. **Environment Variables**: Configure secrets in Agentverse dashboard

## 🔄 Message Processing Flow

```
User Input: "Send Ben: Running late!"
          ↓
     Chat Protocol Message
          ↓
    ASI:One Intent Parsing
          ↓
    Extract: recipient="Ben", message="Running late!"
          ↓
    Discord OAuth Token Validation
          ↓
    Discord API: Create DM Channel with Ben
          ↓
    Discord API: Send Message
          ↓
    Success Response: "✅ Message sent to Ben"
          ↓
    Natural Language Response Generation
          ↓
    Chat Response to User
```

## Development

### Adding Discord API Integration

To add full Discord API functionality:

1. Install discord.py: `pip install discord.py`
2. Set up Discord bot application at https://discord.com/developers/applications
3. Add Discord API credentials to environment variables
4. Implement Discord client initialization and message handling

### Extending Functionality

The agent can be extended to support:

- Discord server management
- Channel operations
- User role management
- Message moderation
- Discord webhook integration

## Architecture

- **Chat Protocol**: Uses uAgents chat protocol for standardized messaging
- **ASI:One Integration**: Leverages ASI:One for intelligent response generation
- **Agentverse Ready**: Configured with mailbox support for cloud deployment
- **Extensible**: Built for easy integration with Discord API

## 🐛 Troubleshooting

### Common Issues

#### 1. Missing Environment Variables

```bash
# Check if .env file exists and has all required variables
cat .env

# Required variables:
ASI_ONE_API_KEY=your_key_here
DISCORD_CLIENT_ID=your_client_id
DISCORD_CLIENT_SECRET=your_client_secret
DISCORD_REDIRECT_URI=http://localhost:8080/callback
```

#### 2. Discord OAuth2 Errors

- **Invalid Client ID/Secret**: Verify credentials in Discord Developer Portal
- **Redirect URI Mismatch**: Ensure `DISCORD_REDIRECT_URI` matches Discord app settings
- **Scope Issues**: Required scopes: `identify`, `guilds`, `messages.read`, `dm_channels.read`

#### 3. ASI:One API Issues

- **Invalid API Key**: Get new key from [ASI:One Dashboard](https://asi1.ai/dashboard/api-keys)
- **Rate Limiting**: ASI:One has usage limits - check your dashboard
- **Model Errors**: Ensure `asi1-mini` model is available

#### 4. Network & Port Issues

- **Port 8005 in use**: Change agent port in `discord_agent.py`
- **Firewall blocking**: Allow outbound HTTPS connections
- **Local callback server**: Port 8080 must be available for OAuth2

#### 5. Token Storage Issues

- **Encryption errors**: Check `ENCRYPTION_KEY` in `.env` file
- **File permissions**: Ensure write access to agent directory
- **Token expiry**: Agent automatically refreshes tokens

### Debug Mode

Run with debug logging:

```bash
export LOG_LEVEL=DEBUG
python discord_agent.py
```

### Setup Helper

Use the setup script for guided configuration:

```bash
python setup_discord_oauth.py
```

## 🚀 Advanced Features

### Custom Message Processing

- Extend `MessageProcessor` class for domain-specific parsing
- Add custom intent patterns and response templates
- Implement message threading and conversation context

### Multi-User Support

- Store multiple Discord account tokens
- User-specific command routing
- Account switching commands

### Rich Message Support

- Discord embeds and attachments
- Reaction handling and emoji support
- Voice channel integration

### Enterprise Features

- Bulk messaging with rate limiting
- Message analytics and reporting
- Integration with Discord webhooks
- Custom Discord bot deployment

## 🔧 Development

### Testing

```bash
# Run OAuth2 flow test
python setup_discord_oauth.py

# Test message processing
python -c "
from discord_agent import MessageProcessor
import asyncio
async def test():
    result = await MessageProcessor.extract_message_intent('Send Ben: Hello')
    print(result)
asyncio.run(test())
"
```

### Extending Functionality

1. **Add New Message Types**:

   ```python
   # In MessageProcessor.extract_message_intent()
   # Add new action types and parsing logic
   ```

2. **Custom Discord API Methods**:

   ```python
   # In DiscordAPIClient class
   async def custom_discord_operation(self, params):
       # Your Discord API integration
   ```

3. **Enhanced Security**:
   ```python
   # Add token rotation, audit logging, etc.
   ```

### API Reference

#### Key Classes

- `DiscordAuthManager`: OAuth2 and token management
- `DiscordAPIClient`: Discord REST API wrapper
- `MessageProcessor`: Natural language processing
- `OAuthCallbackHandler`: OAuth2 callback server

#### Environment Variables

| Variable                | Required | Default                          | Description                              |
| ----------------------- | -------- | -------------------------------- | ---------------------------------------- |
| `ASI_ONE_API_KEY`       | Yes      | -                                | ASI:One API key for LLM processing       |
| `DISCORD_CLIENT_ID`     | Yes      | -                                | Discord application client ID            |
| `DISCORD_CLIENT_SECRET` | Yes      | -                                | Discord application client secret        |
| `DISCORD_REDIRECT_URI`  | No       | `http://localhost:8080/callback` | OAuth2 callback URL                      |
| `ENCRYPTION_KEY`        | No       | Auto-generated                   | 32-byte encryption key for token storage |

## 📝 Contributing

### Development Guidelines

1. **Code Style**: Follow PEP 8 and use type hints
2. **Error handling**: Always handle Discord API errors gracefully
3. **Security**: Never log or expose sensitive tokens
4. **Testing**: Add tests for new Discord API integrations
5. **Documentation**: Update README for new features

### Pull Request Process

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-functionality`
3. Add tests and documentation
4. Ensure all tests pass
5. Submit pull request with clear description

## 📄 License

This Discord Agent is part of the Vocal Agent ecosystem and follows the same licensing terms. Built with ❤️ using Fetch.ai uAgents framework and ASI:One AI capabilities.
