# Gmail Agent HTTP POST Request Guide

This guide shows you how to send HTTP POST requests to the Gmail agent using various methods.

## Prerequisites

1. **Gmail Agent Running**: Make sure the Gmail agent is running on `http://127.0.0.1:8000`
2. **OAuth Authentication**: Authenticate with Gmail via `http://localhost:8080`
3. **ASI:One API Key** (optional but recommended): Set `ASI_ONE_API_KEY` environment variable

## Quick Start

### 1. Start the Gmail Agent
```bash
cd /Users/benpetlach/Desktop/dev/hackathons/hd4/Iris/src/agents/new-agents/gmail_agent
python gmail_agent.py
```

### 2. Authenticate with Gmail
Visit: `http://localhost:8080` and follow the authentication flow.

### 3. Send HTTP Requests
Use any of the methods below to send requests to the agent.

## HTTP Endpoints

- **Agent Endpoint**: `http://127.0.0.1:8000/submit`
- **OAuth Server**: `http://localhost:8080`
- **OAuth Status**: `http://localhost:8080/status`

## Request Types

### 1. Structured Email Request

Send a properly formatted email with all required fields.

**Message Format:**
```json
{
  "type": "EmailSendRequest",
  "data": {
    "to": "recipient@example.com",
    "subject": "Email Subject",
    "body": "Email body content",
    "from_email": "sender@example.com"  // Optional
  },
  "timestamp": "2024-01-01T12:00:00.000Z",
  "msg_id": "unique-message-id"
}
```

### 2. Natural Language Chat Message

Send natural language requests that the AI will process.

**Message Format:**
```json
{
  "type": "ChatMessage",
  "data": {
    "content": [
      {
        "type": "text",
        "text": "Send an email to john@example.com about the meeting tomorrow"
      }
    ],
    "timestamp": "2024-01-01T12:00:00.000Z",
    "msg_id": "unique-message-id"
  }
}
```

### 3. Health Check

Check if the agent is running and healthy.

**Message Format:**
```json
{
  "type": "HealthCheck",
  "data": {},
  "timestamp": "2024-01-01T12:00:00.000Z",
  "msg_id": "unique-message-id"
}
```

## Examples

### Python with requests library

```python
import requests
import json
from datetime import datetime
from uuid import uuid4

# Send structured email
def send_email(to, subject, body):
    message = {
        "type": "EmailSendRequest",
        "data": {
            "to": to,
            "subject": subject,
            "body": body
        },
        "timestamp": datetime.utcnow().isoformat(),
        "msg_id": str(uuid4())
    }
    
    response = requests.post(
        "http://127.0.0.1:8000/submit",
        json=message,
        headers={"Content-Type": "application/json"}
    )
    
    return response.json()

# Send natural language message
def send_chat_message(text):
    message = {
        "type": "ChatMessage",
        "data": {
            "content": [{"type": "text", "text": text}],
            "timestamp": datetime.utcnow().isoformat(),
            "msg_id": str(uuid4())
        }
    }
    
    response = requests.post(
        "http://127.0.0.1:8000/submit",
        json=message,
        headers={"Content-Type": "application/json"}
    )
    
    return response.json()

# Usage examples
send_email("test@example.com", "Test", "Hello from HTTP!")
send_chat_message("Send an email to john@example.com about the meeting")
```

### curl Examples

```bash
# Structured email request
curl -X POST "http://127.0.0.1:8000/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "EmailSendRequest",
    "data": {
      "to": "test@example.com",
      "subject": "Test Email",
      "body": "Hello from curl!"
    },
    "timestamp": "2024-01-01T12:00:00.000Z",
    "msg_id": "test-123"
  }'

# Natural language message
curl -X POST "http://127.0.0.1:8000/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "ChatMessage",
    "data": {
      "content": [
        {
          "type": "text",
          "text": "Send an email to john@example.com about the meeting"
        }
      ],
      "timestamp": "2024-01-01T12:00:00.000Z",
      "msg_id": "test-456"
    }
  }'
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

async function sendEmail(to, subject, body) {
  const message = {
    type: "EmailSendRequest",
    data: {
      to: to,
      subject: subject,
      body: body
    },
    timestamp: new Date().toISOString(),
    msg_id: Math.random().toString(36).substr(2, 9)
  };
  
  try {
    const response = await axios.post('http://127.0.0.1:8000/submit', message);
    return response.data;
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}

async function sendChatMessage(text) {
  const message = {
    type: "ChatMessage",
    data: {
      content: [{ type: "text", text: text }],
      timestamp: new Date().toISOString(),
      msg_id: Math.random().toString(36).substr(2, 9)
    }
  };
  
  try {
    const response = await axios.post('http://127.0.0.1:8000/submit', message);
    return response.data;
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}

// Usage
sendEmail("test@example.com", "Test", "Hello from Node.js!");
sendChatMessage("Send an email to john@example.com about the meeting");
```

## Response Format

### Successful Email Response
```json
{
  "status_code": 200,
  "message_id": "gmail-message-id",
  "success": true
}
```

### Error Response
```json
{
  "status_code": 500,
  "error_message": "Error description",
  "success": false
}
```

### Chat Response
```json
{
  "timestamp": "2024-01-01T12:00:00.000Z",
  "msg_id": "response-id",
  "content": [
    {
      "type": "text",
      "text": "Response text from the agent"
    }
  ]
}
```

## Natural Language Examples

The Gmail agent with ASI:One can understand various natural language requests:

### Complete Requests
- "Send an email to john@example.com about the meeting tomorrow"
- "Email team@company.com with subject 'Project Update' and tell them we're on track"
- "Write to client@business.com saying we'll deliver on time"

### Casual/Incomplete Requests (AI will ask for missing info)
- "email john about the meeting" → AI asks: "What's john's email address?"
- "tell the boss we're done" → AI asks: "What's your boss's email address?"
- "quick note to client" → AI asks: "What's the client's email and what should I write?"

### Very Brief Requests (AI helps complete)
- "boss" → AI asks: "What about your boss? Do you want to send them an email?"
- "meeting" → AI asks: "What about the meeting? Who should I notify?"

## Error Handling

Common error scenarios and how to handle them:

### Authentication Errors
```json
{
  "error": "Authentication required: OAuth token not found"
}
```
**Solution**: Visit `http://localhost:8080` to authenticate.

### Rate Limiting
```json
{
  "error": "Rate limit exceeded"
}
```
**Solution**: Wait before sending more requests (default: 10 requests per hour).

### Missing Fields
```json
{
  "error": "Missing required fields: recipient email address"
}
```
**Solution**: Ensure all required fields are provided.

## Testing

### 1. Check OAuth Status
```bash
curl "http://localhost:8080/status"
```

### 2. Send Test Email
```python
# Use the provided example files
python simple_gmail_http_example.py
```

### 3. Run Full Test Suite
```python
python gmail_agent_http_client.py
```

## Files in This Guide

- `gmail_agent_http_client.py` - Full-featured HTTP client class
- `simple_gmail_http_example.py` - Simple examples with requests library
- `gmail_agent_curl_examples.sh` - curl command examples
- `GMAIL_AGENT_HTTP_GUIDE.md` - This comprehensive guide

## Troubleshooting

### Agent Not Responding
1. Check if the agent is running: `ps aux | grep gmail_agent`
2. Check the port: `netstat -an | grep 8000`
3. Check logs for errors

### Authentication Issues
1. Visit `http://localhost:8080` to authenticate
2. Check if `credentials.json` exists
3. Verify Gmail API is enabled in Google Cloud Console

### ASI:One Not Working
1. Set `ASI_ONE_API_KEY` environment variable
2. Get API key from https://asi1.ai/dashboard/api-keys
3. Restart the agent after setting the key

## Advanced Usage

### Custom Headers
```python
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer your-token",  # If needed
    "User-Agent": "MyApp/1.0"
}
```

### Timeout Configuration
```python
response = requests.post(
    url,
    json=message,
    timeout=30  # 30 seconds timeout
)
```

### Retry Logic
```python
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)
```

This guide provides everything you need to send HTTP POST requests to the Gmail agent successfully!
