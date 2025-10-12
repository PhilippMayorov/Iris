# CLI Communication Guide - Mailbox Agent

This guide shows you how to communicate with the mailbox agent using the command-line interface instead of the web GUI.

## 🚀 Quick Start

### 1. Start the Mailbox Agent with HTTP Endpoint

First, you need to start the mailbox agent with the HTTP endpoint enabled:

```bash
cd src/agents/new-agents/mailbox_agent

# Set your API key
export ASI_ONE_API_KEY="your_asi_one_api_key_here"

# Start the agent with HTTP endpoint
python run_with_http.py
```

This will start:
- **Mailbox Agent** on port 8001 (for agent-to-agent communication)
- **HTTP API** on port 8002 (for CLI and web access)

### 2. Use the CLI Client

In a new terminal, navigate to the mailbox agent directory and run the CLI:

```bash
cd src/agents/new-agents/mailbox_agent

# Interactive mode (recommended)
python cli_client.py

# Or with specific options
python cli_client.py --interactive
```

## 💬 CLI Usage Examples

### Interactive Mode (Recommended)

```bash
python cli_client.py
```

This starts an interactive chat session where you can:
- Type messages directly to chat with the agent
- Use commands like `/help`, `/models`, `/config`
- See formatted responses with analysis information

### Single Message Mode

```bash
# Send a single message and exit
python cli_client.py --message "Send an email to john@example.com about the meeting"

# Analyze a message without sending it
python cli_client.py --analyze "Create a todo list for my project"
```

### Information Commands

```bash
# Show available models
python cli_client.py --models

# Show agent configuration
python cli_client.py --config
```

## 🎯 CLI Commands

When in interactive mode, you can use these commands:

### Chat Commands
- Just type your message to chat with the agent
- Examples:
  - `Hello, how are you?`
  - `Send an email to john@example.com about the meeting`
  - `What's the weather like?`

### System Commands
- `/help` or `/h` - Show help message
- `/quit` or `/q` or `/exit` - Exit the CLI
- `/models` or `/m` - Show available models
- `/config` or `/c` - Show agent configuration
- `/history` or `/hist` - Show conversation history
- `/clear` - Clear conversation history

### Analysis Commands
- `/analyze <message>` - Analyze a message without sending it
- `/model <name>` - Set model preference for next message

## 📊 CLI Features

### Rich Formatting
The CLI provides beautiful, formatted output with:
- 🎯 Agent routing information
- 🧠 Complexity analysis
- 🤖 Model selection details
- 📝 Conversation history
- ✅/❌ Status indicators

### Example CLI Session

```
🚀 Interactive Mode
Type your messages and press Enter to send.
Type '/help' for commands, '/quit' to exit.

You: Send an email to john@example.com about the meeting

🤖 Thinking...

┌─ 🤖 Agent Response ─────────────────────────────────────────┐
│ Email sent successfully! I've sent an email to             │
│ john@example.com with the subject "Meeting Discussion"     │
│ and included details about our upcoming meeting.           │
└────────────────────────────────────────────────────────────┘

🎯 Agent Routing: email (confidence: 95.0%)
📝 Reason: Request matches email sending pattern
🧠 Complexity: Agentic (confidence: 90.0%)
📝 Reason: Requires external tool usage (email sending)
🤖 Model Used: asi1-fast-agentic
🆔 Conversation ID: cli_client_session
```

## 🔧 Configuration Options

### CLI Client Options

```bash
python cli_client.py [OPTIONS]

Options:
  --url URL              Agent HTTP endpoint URL (default: http://localhost:8002)
  --message, -m TEXT     Send a single message and exit
  --analyze, -a TEXT     Analyze a message and exit
  --models               Show available models and exit
  --config               Show agent configuration and exit
  --interactive, -i      Run in interactive mode (default)
```

### Environment Variables

```bash
# Required
export ASI_ONE_API_KEY="your_asi_one_api_key_here"

# Optional
export HTTP_PORT="8002"        # HTTP endpoint port
export PORT="8001"             # Mailbox agent port
export AGENT_NAME="Intelligent Mailbox Agent"
```

## 🛠️ Troubleshooting

### Common Issues

1. **"Cannot connect to agent"**
   ```bash
   # Make sure the agent is running with HTTP endpoint
   python run_with_http.py
   
   # Check if the HTTP endpoint is accessible
   curl http://localhost:8002/health
   ```

2. **"Missing dependencies"**
   ```bash
   # Install required packages
   pip install httpx rich
   ```

3. **"ASI_ONE_API_KEY not set"**
   ```bash
   # Set your API key
   export ASI_ONE_API_KEY="your_key_here"
   ```

### Testing Connection

```bash
# Test if the agent is running
curl http://localhost:8002/health

# Expected response:
# {"status": "healthy", "agent_address": "agent1...", "timestamp": "..."}
```

## 📱 Advanced Usage

### Custom URL

If your agent is running on a different host/port:

```bash
python cli_client.py --url http://192.168.1.100:8002
```

### Script Integration

You can integrate the CLI into scripts:

```bash
#!/bin/bash
# Send a message and capture response
response=$(python cli_client.py --message "Check my emails" 2>/dev/null)
echo "Agent response: $response"
```

### Batch Processing

```bash
# Process multiple messages
for message in "Send email to alice" "Check calendar" "Search for documents"; do
    echo "Processing: $message"
    python cli_client.py --message "$message"
    echo "---"
done
```

## 🎯 What You Can Do

The CLI gives you full access to all mailbox agent capabilities:

- **Email Management**: Send emails, check inbox, manage drafts
- **Calendar Operations**: Schedule meetings, check availability
- **Web Search**: Search for information online
- **File Operations**: Manage documents and files
- **General Chat**: Ask questions and have conversations
- **Task Automation**: Create and manage todo lists

## 🚀 Next Steps

1. **Start the agent**: `python run_with_http.py`
2. **Open CLI**: `python cli_client.py`
3. **Try commands**: Type `/help` to see all options
4. **Send messages**: Start chatting with the agent!

The CLI provides a powerful, scriptable interface to your intelligent mailbox agent! 🎉
