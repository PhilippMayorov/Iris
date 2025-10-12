# Intelligent Mailbox Agent

A mailbox agent that incorporates the intelligent chat functionality from `chat.py`, including automatic model selection and agent routing capabilities.

## Features

- **Intelligent Model Selection**: Automatically determines whether to use regular or agentic models based on request complexity
- **Agent Routing**: Routes requests to specialized agents (like Gmail agent) when appropriate
- **Request Analysis**: Pre-processes requests to understand intent and complexity
- **Mailbox Endpoint**: Accessible via HTTP endpoint for external integrations
- **Conversation History**: Maintains context across interactions
- **ASI:One Integration**: Full integration with ASI:One API for advanced AI capabilities

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**:
   ```bash
   export ASI_ONE_API_KEY="your_asi_one_api_key_here"
   export AGENT_NAME="Intelligent Mailbox Agent"  # Optional
   export AGENT_SEED="your_seed_phrase_here"      # Optional
   export PORT="8001"                             # Optional, defaults to 8001
   ```

3. **Run the Agent**:
   ```bash
   python run_agent.py
   ```

## Usage

### Via Mailbox Endpoint

The agent provides a mailbox endpoint that can be accessed by other agents or external systems.

**Agent Address**: The agent will display its address when started, e.g., `agent1qw6kgumlfq...`

### Chat Protocol

The agent supports the standard chat protocol for natural language interactions:

```python
from uagents_core.contrib.protocols.chat import ChatMessage, TextContent
from datetime import datetime
from uuid import uuid4

# Send a chat message
message = ChatMessage(
    timestamp=datetime.utcnow(),
    msg_id=uuid4(),
    content=[
        TextContent(type="text", text="Hello, can you help me send an email?")
    ]
)

# Send to agent address
await ctx.send(agent_address, message)
```

### Structured Chat Request

For more control over the interaction:

```python
from mailbox_agent import ChatRequest

# Create a chat request
request = ChatRequest(
    message="Send an email to john@example.com about the meeting",
    conversation_id="optional_conversation_id",
    model="asi1-fast-agentic"  # Optional, will auto-select if not provided
)

# Send to agent
await ctx.send(agent_address, request)
```

## Intelligent Features

### Automatic Model Selection

The agent automatically analyzes requests and selects the appropriate model:

- **Regular Chat** (`asi1-mini`): For general questions and conversations
- **Agentic Models** (`asi1-fast-agentic`, `asi1-agentic`, `asi1-extended-agentic`): For tasks requiring tools or external actions

### Agent Routing

When a request matches a specialized agent category, it automatically routes to the appropriate agent:

- **Email Tasks**: Routes to Gmail agent for email sending
- **Calendar Tasks**: Routes to calendar agent (when available)
- **Web Search**: Routes to search agent (when available)
- **File Operations**: Routes to file agent (when available)

### Request Analysis

The agent performs intelligent analysis of requests to:

1. **Determine Complexity**: Analyzes if the request needs agentic capabilities
2. **Extract Intent**: Understands what the user wants to accomplish
3. **Route Appropriately**: Sends requests to the right agent or model
4. **Provide Context**: Maintains conversation history for better responses

## Configuration

### Agent Configuration

The agent can be configured with different specialized agents:

```python
agent_config = {
    "email": {
        "keywords": ["email", "send email", "mail", "message"],
        "agent_address": "better-gmail-agent",
        "description": "Email sending and management tasks",
        "examples": ["send an email", "email my friend"]
    },
    # Add more agent categories as needed
}
```

### Model Selection

The agent supports all ASI:One models:

- `asi1-mini`: Standard chat model
- `asi1-agentic`: General orchestration
- `asi1-fast-agentic`: Real-time agent coordination (recommended)
- `asi1-extended-agentic`: Complex multi-stage workflows

## API Response Format

The agent returns structured responses with analysis information:

```json
{
    "response": "Email sent successfully!",
    "conversation_id": "uuid-string",
    "model_used": "asi1-fast-agentic",
    "agent_routing": {
        "matched_agent": "email",
        "confidence": 0.95,
        "reason": "Request matches email sending pattern",
        "agent_address": "better-gmail-agent"
    },
    "complexity_analysis": null,
    "success": true,
    "error_message": null
}
```

## Health Check

The agent provides a health check endpoint:

```python
from mailbox_agent import HealthCheck

# Check agent health
await ctx.send(agent_address, HealthCheck())
```

## Troubleshooting

### Common Issues

1. **ASI:One API Key Not Set**:
   - Ensure `ASI_ONE_API_KEY` environment variable is set
   - Get your API key from https://asi1.ai/dashboard/api-keys

2. **Agent Not Responding**:
   - Check that the agent is running and accessible
   - Verify the agent address is correct
   - Check network connectivity

3. **Model Selection Issues**:
   - The agent will fall back to keyword-based analysis if AI analysis fails
   - Check ASI:One API connectivity and rate limits

### Logs

The agent provides detailed logging for debugging:

- 🔍 Analysis steps
- 🎯 Agent routing decisions
- 🤖 Model selection reasoning
- 📊 Request complexity assessment

## Integration Examples

### With Gmail Agent

```python
# The mailbox agent will automatically route email requests to the Gmail agent
message = "Send an email to john@example.com about the meeting tomorrow"
# This will be routed to the Gmail agent automatically
```

### With External Systems

```python
# External system can send requests to the mailbox agent
import httpx

async def send_to_mailbox_agent(message: str):
    # Use the agent's HTTP endpoint (if available)
    # or integrate via the agent protocol
    pass
```

## Development

### Adding New Agent Categories

1. Update the `agent_config` in the `IntelligentChatHandler` class
2. Add the new agent's address and keywords
3. Test the routing with sample requests

### Customizing Analysis

1. Modify the analysis prompts in `analyze_request_complexity()` and `analyze_agent_routing()`
2. Adjust the fallback analysis logic in `_fallback_analysis()` and `_fallback_agent_routing()`
3. Test with various request types

## License

This agent is part of the Iris project and follows the same licensing terms.
