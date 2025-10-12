#!/bin/bash
# Gmail Agent HTTP POST Examples using curl

# Configuration
GMAIL_AGENT_URL="http://127.0.0.1:8000"
OAUTH_SERVER_URL="http://localhost:8080"

echo "📧 Gmail Agent HTTP POST Examples with curl"
echo "============================================="

# Check OAuth status
echo "1. Checking OAuth status..."
curl -s "$OAUTH_SERVER_URL/status" | jq '.' 2>/dev/null || echo "OAuth server not responding or jq not installed"

echo -e "\n2. Sending structured email request..."

# Structured email request
curl -X POST "$GMAIL_AGENT_URL/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "EmailSendRequest",
    "data": {
      "to": "test@example.com",
      "subject": "Test Email from curl",
      "body": "This is a test email sent via curl HTTP POST request!"
    },
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'",
    "msg_id": "'$(uuidgen)'"
  }' \
  -w "\nHTTP Status: %{http_code}\n"

echo -e "\n3. Sending natural language message..."

# Natural language message
curl -X POST "$GMAIL_AGENT_URL/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "ChatMessage",
    "data": {
      "content": [
        {
          "type": "text",
          "text": "Send an email to john@example.com about the meeting tomorrow"
        }
      ],
      "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'",
      "msg_id": "'$(uuidgen)'"
    }
  }' \
  -w "\nHTTP Status: %{http_code}\n"

echo -e "\n4. Sending another natural language message..."

# Another natural language example
curl -X POST "$GMAIL_AGENT_URL/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "ChatMessage",
    "data": {
      "content": [
        {
          "type": "text",
          "text": "Email the team about the project update"
        }
      ],
      "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'",
      "msg_id": "'$(uuidgen)'"
    }
  }' \
  -w "\nHTTP Status: %{http_code}\n"

echo -e "\n5. Sending health check..."

# Health check
curl -X POST "$GMAIL_AGENT_URL/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "HealthCheck",
    "data": {},
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'",
    "msg_id": "'$(uuidgen)'"
  }' \
  -w "\nHTTP Status: %{http_code}\n"

echo -e "\n✅ curl examples completed!"
echo -e "\nNote: Make sure the Gmail agent is running on $GMAIL_AGENT_URL"
echo -e "and that you're authenticated via $OAUTH_SERVER_URL"
