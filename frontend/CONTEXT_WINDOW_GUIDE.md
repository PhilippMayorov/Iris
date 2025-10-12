# Gemini Agent Context Window Guide

## Overview

The Gemini agent in the frontend now includes a context window that keeps track of conversation history and provides relevant context for more personalized and coherent responses.

## Features

### 1. Conversation Memory
- Tracks up to 10 recent conversation turns by default
- Remembers user preferences and interests
- Maintains context across different types of interactions (general, music, refinement)

### 2. Context-Aware Responses
- Gemini uses previous conversation context to provide more relevant responses
- Builds upon previous topics and user preferences
- Maintains conversation flow and continuity

### 3. Session Management
- Each conversation session has a unique ID
- Context persists throughout a session
- Can start new sessions to reset context

## API Endpoints

### Context Management

#### Start New Session
```http
POST /api/context/start-session
Content-Type: application/json

{
  "session_id": "optional_custom_session_id"
}
```

#### Get Context Status
```http
GET /api/context/status
```

Returns:
```json
{
  "success": true,
  "context": {
    "session_id": "session_20241201_143022",
    "interaction_count": 5,
    "recent_types": ["general", "music", "general"],
    "user_preferences": {
      "music_genre": "rock",
      "name": "John"
    }
  }
}
```

#### Clear Context
```http
POST /api/context/clear
```

#### Get Context History
```http
GET /api/context/history
```

Returns:
```json
{
  "success": true,
  "history": [
    {
      "timestamp": "2024-12-01T14:30:22.123456",
      "type": "general",
      "user_input": "Hello, my name is John",
      "assistant_response": "Hello John! Nice to meet you..."
    }
  ],
  "count": 1
}
```

#### Manage User Preferences
```http
GET /api/context/preferences
POST /api/context/preferences
Content-Type: application/json

{
  "preferences": {
    "music_genre": "rock",
    "name": "John",
    "interests": ["AI", "music"]
  }
}
```

## How It Works

### 1. Automatic Context Tracking
- Every interaction with the Gemini agent is automatically added to the context
- Different interaction types are tracked (general, music, refinement, error)
- Context is included in prompts sent to Gemini

### 2. Context Building
- Recent interactions (last 5 by default) are included in prompts
- Long messages are truncated to prevent token overflow
- User preferences are maintained and can influence responses

### 3. Context Usage
- Context is automatically included in:
  - Direct Gemini responses (`/api/gemini-direct-response`)
  - Music request processing
  - Speech refinement (tracked but not included in main conversation flow)

## Configuration

### Context Manager Settings
```python
# In app.py, you can modify these settings:
context_manager = ChatContextManager(
    max_context_length=10,        # Max conversation turns to keep
    max_tokens_per_message=500    # Max tokens per message for context
)
```

### Context Inclusion
```python
# Number of recent interactions to include in prompts
context_string = context_manager.get_context_for_prompt(
    current_input, 
    include_recent=5  # Adjust this number as needed
)
```

## Testing

Run the test script to verify context functionality:

```bash
cd frontend
python test_context_window.py
```

This will test:
- Session management
- Context building
- Context-aware responses
- User preferences
- Context clearing

## Example Usage

### Building Context
1. User: "Hello, my name is John and I love rock music"
2. Assistant: "Hello John! Nice to meet you. I'd be happy to help you with rock music..."
3. User: "What's the weather like today?"
4. Assistant: "I don't have access to real-time weather data, but I can help you with other things..."
5. User: "Can you find me some good rock songs?"
6. Assistant: "Since you mentioned you love rock music, let me help you find some great rock songs..."

### Context-Aware Responses
- The assistant remembers the user's name (John)
- It recalls the user's music preference (rock)
- It builds upon previous conversation topics

## Benefits

1. **Personalized Responses**: The agent remembers user preferences and builds upon them
2. **Conversation Continuity**: Responses feel more natural and connected
3. **Better User Experience**: Users don't need to repeat information
4. **Contextual Music Recommendations**: Music suggestions are more relevant based on previous preferences
5. **Improved Understanding**: The agent can reference previous topics and provide more relevant help

## Limitations

1. **Memory Limit**: Only keeps the last 10 interactions by default
2. **Token Limits**: Long messages are truncated to prevent API token overflow
3. **Session-Based**: Context is lost when the server restarts (not persisted to disk)
4. **Single User**: Currently designed for single-user sessions

## Future Enhancements

- Persistent context storage (database/file)
- Multi-user context management
- Context summarization for longer conversations
- Context-based user preference learning
- Integration with other agents for cross-agent context sharing
