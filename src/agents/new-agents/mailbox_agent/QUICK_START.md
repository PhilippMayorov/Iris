# Quick Start Guide - Intelligent Mailbox Agent

## 🚀 Quick Setup & Run

### 1. Set Environment Variable
```bash
export ASI_ONE_API_KEY="your_asi_one_api_key_here"
```

### 2. Run the Agent

**From the project root directory:**
```bash
# Option 1: Use the launcher (recommended)
python run_mailbox_agent.py
```

**From the mailbox_agent directory:**
```bash
cd src/agents/new-agents/mailbox_agent

# Option 2: Simple run (mailbox only)
python simple_run.py

# Option 3: Run with HTTP endpoint
python run_with_http.py

# Option 4: Full setup and run
python setup_and_run.py

# Option 5: Run HTTP endpoint only
python http_endpoint.py
```

## 📡 Access Points

Once running, you can access the agent via:

### Mailbox Protocol
- **Agent Address**: Displayed when starting (e.g., `agent1qw6kgumlfq...`)
- **Port**: 8001 (default)

### HTTP API
- **Base URL**: `http://localhost:8002`
- **API Docs**: `http://localhost:8002/docs` (Swagger UI)
- **Health Check**: `http://localhost:8002/health`
- **Chat Endpoint**: `http://localhost:8002/chat`

## 💬 Usage Examples

### HTTP API Example
```bash
curl -X POST "http://localhost:8002/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Send an email to john@example.com about the meeting",
    "conversation_id": "test_conv_1"
  }'
```

### Python Example
```python
import httpx

async def chat_with_agent():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8002/chat",
            json={
                "message": "Hello, can you help me?",
                "conversation_id": "my_conversation"
            }
        )
        return response.json()

# Run the function
import asyncio
result = asyncio.run(chat_with_agent())
print(result)
```

## 🧪 Testing

Run the test suite:
```bash
python test_mailbox_agent.py
```

## 🔧 Configuration

### Environment Variables
- `ASI_ONE_API_KEY`: Your ASI:One API key (required)
- `AGENT_NAME`: Agent name (default: "Intelligent Mailbox Agent")
- `AGENT_SEED`: Agent seed phrase (default: auto-generated)
- `PORT`: Mailbox agent port (default: 8001)
- `HTTP_PORT`: HTTP endpoint port (default: 8002)
- `HTTP_HOST`: HTTP endpoint host (default: "0.0.0.0")

### Agent Configuration
The agent automatically routes requests to specialized agents:
- **Email tasks** → Gmail agent
- **Calendar tasks** → Calendar agent (when available)
- **Web search** → Search agent (when available)
- **File operations** → File agent (when available)

## 🧠 Intelligent Features

### Automatic Model Selection
- **Regular Chat** (`asi1-mini`): General questions and conversations
- **Agentic Models** (`asi1-fast-agentic`, etc.): Tasks requiring tools or external actions

### Request Analysis
- Analyzes request complexity
- Determines if agentic capabilities are needed
- Routes to appropriate specialized agents
- Maintains conversation context

## 📊 Response Format

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
  "error_message": null,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 🛠️ Troubleshooting

### Common Issues

1. **"ASI_ONE_API_KEY not set"**
   - Set the environment variable: `export ASI_ONE_API_KEY="your_key"`

2. **"Failed to initialize ASI:One client"**
   - Check your API key is valid
   - Verify internet connectivity

3. **"HTTP endpoint not accessible"**
   - Make sure the HTTP server is running
   - Check if port 8002 is available
   - Try accessing `http://localhost:8002/health`

4. **"Agent not responding"**
   - Check the agent is running
   - Verify the agent address is correct
   - Check network connectivity

### Logs
The agent provides detailed logging:
- 🔍 Analysis steps
- 🎯 Agent routing decisions  
- 🤖 Model selection reasoning
- 📊 Request complexity assessment

## 📚 More Information

- **Full Documentation**: See `README.md`
- **API Reference**: Visit `http://localhost:8002/docs` when running
- **Test Suite**: Run `python test_mailbox_agent.py`

## 🎯 What's Next?

1. **Start the agent**: `python setup_and_run.py`
2. **Test it**: Visit `http://localhost:8002/docs`
3. **Send a message**: Use the chat endpoint
4. **Integrate**: Use the agent address or HTTP API in your applications

The agent is now ready to intelligently handle your requests with automatic model selection and agent routing! 🚀
