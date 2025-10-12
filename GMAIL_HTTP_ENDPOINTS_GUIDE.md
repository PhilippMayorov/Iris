# Gmail Agent HTTP Endpoints Guide

The Gmail Agent now supports HTTP endpoints similar to the Spotify Agent, allowing you to interact with it via REST API calls.

## Available Endpoints

### 1. Health Check
**GET** `/health`

Check the status of the Gmail agent and its connections.

**Response:**
```json
{
  "status": "healthy",
  "agent_address": "agent1...",
  "gmail_api": "connected",
  "timestamp": 1703123456
}
```

### 2. Capabilities
**GET** `/capabilities`

Get information about the Gmail agent's capabilities and available commands.

**Response:**
```json
{
  "agent_name": "Gmail Agent",
  "capabilities": [
    "Send emails via Gmail API",
    "Natural language email composition",
    "OAuth2 authentication",
    "Email validation and formatting",
    "AI-powered email content generation",
    "Multi-recipient email support"
  ],
  "supported_actions": [
    "send email",
    "compose message", 
    "email validation",
    "recipient management"
  ],
  "example_commands": [
    "Send an email to john@example.com about the meeting",
    "Compose a thank you email to the team",
    "Send a reminder about the project deadline",
    "Email the client with the proposal"
  ],
  "endpoints": {
    "chat": "POST /chat - Send natural language email requests",
    "capabilities": "GET /capabilities - Get this information",
    "health": "GET /health - Check agent status"
  }
}
```

### 3. Chat (Natural Language Email)
**POST** `/chat`

Send natural language requests to compose and send emails.

**Request Body:**
```json
{
  "text": "Send an email to john@example.com about the meeting tomorrow"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Email sent successfully to john@example.com",
  "request_id": "uuid-here"
}
```

## Usage Examples

### Using curl

```bash
# Check health
curl -X GET http://localhost:8000/health

# Get capabilities
curl -X GET http://localhost:8000/capabilities

# Send email via natural language
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"text": "Send a test email to test@example.com with subject Test and body Hello World"}'
```

### Using Python requests

```python
import requests

# Check health
response = requests.get("http://localhost:8000/health")
print(response.json())

# Send email
email_request = {
    "text": "Send an email to john@example.com about the project update"
}
response = requests.post("http://localhost:8000/chat", json=email_request)
print(response.json())
```

### Using JavaScript fetch

```javascript
// Check health
fetch('http://localhost:8000/health')
  .then(response => response.json())
  .then(data => console.log(data));

// Send email
fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    text: 'Send an email to team@company.com about the meeting'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

## Testing

Run the test script to verify all endpoints are working:

```bash
python test_gmail_http_endpoints.py
```

## Prerequisites

1. **Gmail Agent Running**: Make sure the Gmail agent is running on port 8000
2. **OAuth Setup**: Ensure Gmail OAuth is properly configured with `token.json`
3. **ASI:One API Key**: Set the `ASI_ONE_API_KEY` environment variable for AI processing

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200`: Success
- `400`: Bad request (missing or invalid data)
- `500`: Internal server error

Error responses include detailed error messages:

```json
{
  "success": false,
  "message": "Error processing request: [error details]",
  "request_id": "uuid-here"
}
```

## Integration with Frontend

These HTTP endpoints can be easily integrated into web frontends, mobile apps, or other services that need to send emails programmatically through natural language processing.
