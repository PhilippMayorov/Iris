# ASI One API Integration

This directory contains the integration code for the ASI One API, allowing you to interact with their chat completion models.

## Files

- `asi_client.py` - Main client class with support for both regular and agentic models
- `example_usage.py` - Comprehensive examples showing how to use the client
- `interactive_chat.py` - Interactive command-line chat interface with agentic support
- `agentic_chat.py` - Specialized chat interface for agentic models and Agentverse
- `demo_chat.py` - Demo script showing chat functionality
- `test_asi_client.py` - Test suite to verify the client works
- `README.md` - This documentation file

## Setup

### 1. Environment Variables

Set your ASI One API key as an environment variable:

```bash
export ASI_ONE_API_KEY="your_api_key_here"
```

Or add it to your `.env` file:

```
ASI_ONE_API_KEY=your_api_key_here
```

### 2. Dependencies

The required dependencies are already included in the main project's `requirements.txt`:
- `requests>=2.31.0` - For making HTTP requests
- `python-dotenv>=1.0.0` - For environment variable management

## Quick Start

### Basic Usage

```python
from asi_client import ASIOneClient

# Initialize client (will use ASI_ONE_API_KEY from environment)
client = ASIOneClient()

# Simple chat
response = client.simple_chat("Hello! How can you help me today?")
print(response)
```

### Advanced Usage

```python
from asi_client import ASIOneClient

client = ASIOneClient()

# Multi-turn conversation
messages = [
    {"role": "user", "content": "What is machine learning?"}
]

response = client.chat_completion(messages)
print(response["choices"][0]["message"]["content"])

# Continue the conversation
messages.append({"role": "assistant", "content": response["choices"][0]["message"]["content"]})
messages.append({"role": "user", "content": "Can you give me an example?"})

response2 = client.chat_completion(messages)
print(response2["choices"][0]["message"]["content"])
```

## API Response Structure

The ASI One API returns responses with the following structure:

```json
{
  "id": "id_zRgUoZjjcr4yxIG0B",
  "model": "asi1-mini",
  "executable_data": [],
  "intermediate_steps": [],
  "conversation_id": null,
  "thought": ["\n\n"],
  "choices": [
    {
      "index": 0,
      "finish_reason": "stop",
      "message": {
        "role": "assistant",
        "content": "Hey there! 👋 ...",
        "reasoning": "\n\n"
      }
    }
  ],
  "usage": {
    "prompt_tokens": 71,
    "completion_tokens": 105,
    "total_tokens": 176
  }
}
```

### Key Response Fields

- `choices[0].message.content` - The assistant's reply
- `usage` - Token accounting for cost/limits
- `executable_data` - Structured tool calls or agent manifests (empty for basic chat)
- `intermediate_steps` - Debugging breadcrumbs for multi-step plans
- `thought` - Lightweight reasoning trace

## Running Examples

### Interactive Chat

The easiest way to start chatting with the ASI One API:

```bash
# From the project root
python chat.py
```

Or directly:
```bash
python src/asi_integration/interactive_chat.py
```

### Agentic Chat (Agentverse Integration)

For agentic models that can work with the Agentverse marketplace:

```bash
# From the project root
python agentic_chat.py
```

Or with a specific model:
```bash
python agentic_chat.py asi1-fast-agentic
```

Available agentic models:
- `asi1-agentic` - General orchestration & prototyping
- `asi1-fast-agentic` - Real-time agent coordination (recommended)
- `asi1-extended-agentic` - Complex multi-stage workflows

### Demo Script

To see a quick demo without interaction:

```bash
python src/asi_integration/demo_chat.py
```

### Example Usage

To see comprehensive examples:

```bash
python src/asi_integration/example_usage.py
```

### Test Suite

To verify everything is working:

```bash
python src/asi_integration/test_asi_client.py
```

## Interactive Chat Features

The interactive chat (`interactive_chat.py`) provides a full-featured command-line interface:

### Commands
- `/help` or `/h` - Show help information
- `/clear` or `/c` - Clear conversation history
- `/save [filename]` - Save conversation to file
- `/load <filename>` - Load conversation from file
- `/history` or `/hist` - Show conversation history
- `/tokens` or `/t` - Show token usage statistics
- `/model [name]` - Change the AI model
- `/quit`, `/q`, or `/exit` - Exit the chat

### Features
- **Multi-turn conversations** - Maintains context throughout the chat
- **Token tracking** - Monitors API usage and costs
- **Conversation persistence** - Save and load chat sessions
- **Model switching** - Change AI models on the fly
- **Streaming support** - Real-time response streaming
- **Session management** - Automatic session handling for agentic models
- **Error handling** - Graceful handling of API errors
- **Keyboard shortcuts** - Ctrl+C to exit, etc.

## Agentic Models & Agentverse Integration

The updated client now supports ASI One's agentic models that can autonomously discover and coordinate with agents from the Agentverse marketplace.

### Key Features

- **Autonomous Agent Discovery** - Automatically finds relevant agents from Agentverse marketplace
- **Session Persistence** - Maintains conversation context across multiple interactions
- **Asynchronous Processing** - Handles long-running agent workflows
- **Streaming Support** - Real-time response streaming for better UX
- **Multi-Agent Coordination** - Orchestrates complex workflows across multiple agents

### Available Models

| Model | Best For | Latency | Context Window |
|-------|----------|---------|----------------|
| `asi1-agentic` | General orchestration & prototyping | Medium | 32K tokens |
| `asi1-fast-agentic` | Real-time agent coordination | Ultra-fast | 24K tokens |
| `asi1-extended-agentic` | Complex multi-stage workflows | Slower | 64K tokens |

### Usage Examples

```python
from asi_integration.asi_client import ASIOneClient
import uuid

# Initialize client
client = ASIOneClient()

# Create conversation ID for agentic models
conversation_id = str(uuid.uuid4())

# Stream a response from agentic model
response = client.stream_chat(
    "Help me book a restaurant for dinner tonight",
    model="asi1-fast-agentic",
    conversation_id=conversation_id
)

# Handle async agent responses
if "I've sent the message" in response:
    follow_up = client.poll_for_async_reply(
        conversation_id,
        conversation_history,
        model="asi1-fast-agentic"
    )
    if follow_up:
        print(f"Agent completed: {follow_up}")
```

### Best Practices

1. **Session Management** - Always use conversation IDs for agentic models
2. **Streaming** - Use streaming for better user experience
3. **Async Polling** - Poll for deferred agent responses when needed
4. **Error Handling** - Implement timeouts and retry logic
5. **Specific Requests** - Be specific in requests to help agent discovery

## Integration with Vocal Agent

This ASI One integration can be used as an alternative or complement to the existing Google Gemini integration in the vocal agent system. You can:

1. Replace Gemini with ASI One for reasoning
2. Use ASI One for specific tasks while keeping Gemini for others
3. Implement a hybrid approach using both APIs

To integrate with the existing vocal agent system, you would modify the `vocal_core_agent.py` to use the ASI One client instead of or alongside the Gemini client.

## Error Handling

The client includes proper error handling for:
- Missing API keys
- Network errors
- Invalid responses
- Rate limiting

Always wrap API calls in try-catch blocks and handle errors appropriately in your application.

## Models Available

Currently, the client is configured to use the `asi1-mini` model by default. You can specify different models by passing the `model` parameter to the `chat_completion` method.

## Contributing

When adding new features to this integration:
1. Follow the existing code style
2. Add appropriate error handling
3. Update this README with new functionality
4. Add examples for new features
5. Test with various scenarios
