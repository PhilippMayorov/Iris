# Slack Messaging Agent

A specialized uAgent for managing Slack communications through natural language voice commands and OAuth 2.0 authentication.

## Features

- **OAuth 2.0 Integration**: Full Slack OAuth 2.0 v2 implementation with secure token management
- **ASI:One Integration**: Compatible with ASI:One chat interface for natural language processing
- **Direct Messaging**: Send messages to Slack users by display name or username
- **Message History**: Read and retrieve conversation history from direct messages
- **User Discovery**: Find Slack users in your workspace by name or display name
- **Natural Language Processing**: Understands conversational requests with AI-powered intent analysis
- **Secure Authentication**: Encrypted token storage with automatic refresh handling
- **Real-time Communication**: Live interaction with Slack workspaces and team members
- **Chat Protocol**: Uses standardized chat protocol for seamless communication
- **Expert Assistant**: Specialized knowledge in Slack messaging and team communication

## Supported Commands (Natural Language)

### Send Messages

- "Send Alice a message saying I'll be late"
- "Tell Ben: Meeting moved to 3pm"
- "Message Charlie that the project is done"
- "DM Sarah: Can you review the document?"
- "Send everyone in my team: Great job today!"

### Read Messages

- "Read my last message from Alice"
- "Show messages from Ben"
- "Get my conversation with Charlie"
- "What did Sarah say recently?"
- "Check my DMs from the team"

### Authentication

- "Connect my Slack account"
- "Login to Slack"
- "Authenticate with Slack"
- "Set up Slack integration"

### User Discovery

- "Find user John Smith"
- "Look up @jdoe"
- "Search for team member Alice"

### ASI:One Discovery Queries

- "Connect me to an agent that handles Slack messaging"
- "I need help with team communication"
- "Find an expert for Slack integration"

## Agent Configuration

- **Name**: slack_agent
- **Port**: 8003
- **Endpoint**: http://127.0.0.1:8003/submit

## Message Types

### SendMessageRequest

```python
{
    "action": "send_message",
    "recipient": "Alice",
    "message": "I'll be late to the meeting",
    "request_id": "unique_id"
}
```

### ReadMessagesRequest

```python
{
    "action": "read_messages",
    "target": "Ben",
    "limit": 10,
    "request_id": "unique_id"
}
```

### SlackResponse

```python
{
    "success": true,
    "message": "Message sent successfully",
    "data": {...},
    "request_id": "unique_id"
}
```

## Integration

This agent is designed to work with the Vocal Agent ecosystem and Agentverse:

- **Local Agent**: Runs locally with mailbox integration to Agentverse
- **Agentverse Ready**: Configured with `mailbox=True` and `publish_agent_details=True`
- **Inter-agent Communication**: Receives requests from `vocal_core_agent`
- **Message Processing**: Handles Slack messaging commands via uAgents messaging
- **Response System**: Returns structured responses with message status and data

## Agentverse Deployment

This agent is configured as a Mailbox Agent for Agentverse integration:

1. **Run locally**: `python slack_agent.py`
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

### Send Message

```python
ChatMessage(
    content=[
        TextContent(
            type="text",
            text="Send Alice a message saying I'll be running late"
        )
    ]
)
```

### Read Messages

```python
ChatMessage(
    content=[
        TextContent(
            type="text",
            text="Read my last message from Ben"
        )
    ]
)
```

### Authentication

```python
ChatMessage(
    content=[
        TextContent(
            type="text",
            text="authenticate"
        )
    ]
)
```

## Recent Updates

- ✅ **Slack OAuth 2.0 Integration**: Full OAuth v2 authentication with secure token management
- ✅ **Direct Messaging**: Send messages to Slack users by display name or username
- ✅ **Message History**: Read and retrieve conversation history from DMs
- ✅ **AI-Powered Intent Analysis**: ASI:One integration for intelligent request processing
- ✅ **Enhanced Error Handling**: Graceful handling of OAuth errors and API limitations
- ✅ **User Discovery**: Find team members by name across your workspace

## OAuth 2.0 Setup

### Environment Configuration

```bash
SLACK_CLIENT_ID=your_slack_client_id_here
SLACK_CLIENT_SECRET=your_slack_client_secret_here
SLACK_REDIRECT_URI=https://localhost:8080/callback
ASI_ONE_API_KEY=your_asi_one_api_key_here
```

### Setup Process

1. **Run setup script**: `python setup_slack_agent.py`
2. **Configure Slack App**: Add redirect URI to your Slack app settings
3. **Start agent**: `python slack_agent.py`
4. **Authenticate**: Send "authenticate" to begin OAuth flow

## Future Enhancements

- Channel messaging and management
- File sharing and attachment support
- Slack workflow integration
- Team presence and status updates
- Advanced message formatting and threading
- Direct Agentverse hosted deployment option
