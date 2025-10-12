# uAgent to uAgent Communication Implementation

## Overview

This document describes the implementation of synchronous uAgent to uAgent communication between the **Mailbox Agent** and **Gmail Agent** using the `ctx.send_and_receive` pattern for request-response communication.

## Key Features Implemented

### 1. Synchronous Communication
- **Pattern**: `ctx.send_and_receive` for request-response communication
- **Behavior**: Mailbox agent waits for Gmail agent response before proceeding
- **Timeout**: Built-in timeout handling from uAgents framework

### 2. Intelligent Request Processing
- **ASI:One Integration**: Gmail agent uses ASI:One to process natural language email requests
- **Clarification Requests**: Gmail agent can request more information when needed
- **Context Awareness**: Maintains conversation history for better understanding

### 3. Proper Error Handling
- **Authentication Checks**: Verifies Gmail OAuth before processing
- **Validation**: Validates email addresses and message content
- **Graceful Fallbacks**: Handles missing information with helpful suggestions

## Communication Models

### AgentEmailRequest
```python
class AgentEmailRequest(Model):
    to: str
    subject: str
    body: str
    from_email: Optional[str] = None
    original_message: str  # Key field for ASI:One processing
```

### AgentEmailResponse
```python
class AgentEmailResponse(Model):
    success: bool
    message_id: Optional[str] = None
    error_message: Optional[str] = None
    status_code: int = 200
    needs_clarification: bool = False
    suggestions: Optional[List[str]] = None
    reasoning: Optional[str] = None
```

## Communication Flow

### 1. User Message Processing
```
User → Mailbox Agent → ASI:One Analysis → Agent Routing Decision
```

### 2. Email Routing
```
Mailbox Agent → AgentEmailRequest → Gmail Agent
```

### 3. Gmail Agent Processing
```
Gmail Agent → ASI:One Processing → Email Validation → Response
```

### 4. Response Handling
```
Gmail Agent → AgentEmailResponse → Mailbox Agent → User
```

## Implementation Details

### Mailbox Agent Changes

#### Enhanced Communication Models
- Added `AgentEmailRequest` and `AgentEmailResponse` models
- Added clarification request models for future extensibility
- Enhanced response handling with clarification support

#### Synchronous Communication Method
```python
async def send_to_gmail_agent(self, ctx: Context, email_request: AgentEmailRequest) -> AgentEmailResponse:
    response, status = await ctx.send_and_receive(
        gmail_agent_address, 
        email_request, 
        response_type=AgentEmailResponse
    )
    return response
```

#### Enhanced Response Handling
- Handles successful email sending with message ID
- Processes clarification requests with suggestions
- Provides detailed error messages and reasoning

### Gmail Agent Changes

#### New Handler for Agent Communication
```python
@proto.on_message(AgentEmailRequest, replies={AgentEmailResponse, ErrorMessage})
async def handle_agent_email_request(ctx: Context, sender: str, msg: AgentEmailRequest):
```

#### ASI:One Integration
- Processes original user message with ASI:One
- Maintains conversation history for context
- Returns structured responses with reasoning

#### Intelligent Validation
- Checks OAuth authentication status
- Validates email addresses and message content
- Returns clarification requests when information is missing

## Example Communication Scenarios

### Scenario 1: Successful Email
```
User: "send an email to john@example.com about the meeting"
Mailbox Agent → Gmail Agent: AgentEmailRequest
Gmail Agent → ASI:One: Process "send an email to john@example.com about the meeting"
Gmail Agent → Mailbox Agent: AgentEmailResponse(success=True, message_id="...")
Mailbox Agent → User: "✅ Email sent successfully! Message ID: ..."
```

### Scenario 2: Missing Information
```
User: "send an email about the meeting"
Mailbox Agent → Gmail Agent: AgentEmailRequest
Gmail Agent → ASI:One: Process "send an email about the meeting"
Gmail Agent → Mailbox Agent: AgentEmailResponse(
    needs_clarification=True,
    error_message="Missing recipient email address",
    suggestions=["Please provide the recipient's email address"]
)
Mailbox Agent → User: "🤔 I need a bit more information... Missing recipient email address"
```

### Scenario 3: Authentication Required
```
User: "send an email to test@example.com"
Mailbox Agent → Gmail Agent: AgentEmailRequest
Gmail Agent → Mailbox Agent: AgentEmailResponse(
    success=False,
    error_message="Gmail authentication required: Please authenticate with Google"
)
Mailbox Agent → User: "❌ Failed to send email: Gmail authentication required"
```

## Benefits of This Implementation

### 1. **Synchronous Communication**
- Mailbox agent waits for Gmail agent response
- No race conditions or timing issues
- Clear request-response pattern

### 2. **Intelligent Processing**
- ASI:One handles natural language understanding
- Context-aware conversation history
- Smart clarification requests

### 3. **Robust Error Handling**
- Authentication validation
- Input validation with helpful suggestions
- Graceful degradation when services are unavailable

### 4. **Extensible Design**
- Easy to add new agent types
- Modular communication models
- Clear separation of concerns

## Testing

The implementation was tested with a comprehensive test suite that verified:

1. ✅ **Successful email requests** - Proper message ID return
2. ✅ **Missing email address handling** - Clarification requests with suggestions
3. ✅ **Missing message content handling** - Appropriate error messages
4. ✅ **Synchronous communication** - Proper request-response timing
5. ✅ **Error handling** - Graceful failure modes

## Usage

### Starting the Agents

1. **Start Gmail Agent** (receiver):
```bash
cd src/agents/new-agents/gmail_agent
python gmail_agent.py
```

2. **Start Mailbox Agent** (sender):
```bash
cd src/agents/new-agents/mailbox_agent
python mailbox_agent.py
```

### Example User Interactions

```
User: "send an email to petlachben@gmail.com saying jeff says hi"
→ Mailbox Agent routes to Gmail Agent
→ Gmail Agent processes with ASI:One
→ Returns success with message ID

User: "send an email about the meeting"
→ Mailbox Agent routes to Gmail Agent  
→ Gmail Agent needs clarification
→ Returns suggestions for missing information
```

## Future Enhancements

1. **Additional Agent Types**: Calendar, web search, file operations
2. **Conversation Persistence**: Store conversation history across sessions
3. **Multi-step Workflows**: Handle complex multi-agent orchestration
4. **Performance Optimization**: Caching and connection pooling
5. **Monitoring**: Add metrics and health checks for agent communication

## Conclusion

The implementation successfully establishes robust uAgent to uAgent communication using the `ctx.send_and_receive` pattern. The system provides intelligent email processing with proper error handling, clarification requests, and synchronous communication that ensures reliable request-response patterns.

The architecture is extensible and can easily accommodate additional agent types while maintaining the same communication patterns and error handling capabilities.
