# Gmail Agent Communication Troubleshooting Guide

This guide helps you troubleshoot communication issues between your `agentic_chat.py` and the `@better-gmail-agent` deployed on Agentverse.

## Quick Fix Summary

The main issues have been addressed with the following improvements:

1. **Enhanced System Prompt**: Added specific Gmail agent address and instructions
2. **Email Request Detection**: Automatic detection and formatting of email requests
3. **Improved Async Polling**: Better handling of agent responses
4. **Gmail Agent Helper**: Specialized functions for email communication

## Gmail Agent Details

- **Agent Address**: `agent1qw6kgumlfqp9drr54qsfngdkz50vgues3u7sewg2fgketekqk8hz500ytg3`
- **Protocol**: Chat Protocol with structured email format
- **Authentication**: OAuth2 with Google Gmail API

## Testing Your Setup

### 1. Run the Test Suite

```bash
python test_gmail_agent_communication.py
```

This will test:
- Email request detection
- Email parsing and formatting
- Agentic chat integration
- Actual communication with Gmail agent

### 2. Test with Agentic Chat

```bash
python agentic_chat.py
```

Then try these commands:
- `Send an email to test@example.com about testing the integration`
- `Email my boss about the project status`
- `Send a message to john@example.com regarding the meeting`

## Common Issues and Solutions

### Issue 1: "No response from Gmail agent"

**Symptoms:**
- Agentic chat says it's sending email but no confirmation
- No email actually sent
- Polling times out

**Solutions:**
1. **Check Gmail Agent Status**: Verify the agent is running on Agentverse
2. **Verify OAuth Setup**: The Gmail agent needs proper Google OAuth credentials
3. **Check Agent Address**: Ensure the address is correct: `agent1qw6kgumlfqp9drr54qsfngdkz50vgues3u7sewg2fgketekqk8hz500ytg3`
4. **Review Logs**: Check the agentic chat logs for detailed error messages

### Issue 2: "Email request not detected"

**Symptoms:**
- Natural language email requests not recognized
- No automatic formatting applied

**Solutions:**
1. **Use Clear Language**: Try "Send an email to..." or "Email someone about..."
2. **Include Email Address**: Make sure to include a valid email address
3. **Check Detection**: Run the test suite to verify email detection is working

### Issue 3: "Authentication required"

**Symptoms:**
- Gmail agent responds with authentication error
- OAuth setup required message

**Solutions:**
1. **Set up OAuth**: Follow the Gmail agent's OAuth setup guide
2. **Check Credentials**: Ensure `credentials.json` and `token.json` are present
3. **Verify Scopes**: Make sure Gmail API scopes are properly configured

### Issue 4: "Agent not found"

**Symptoms:**
- Agentic chat can't find the Gmail agent
- Communication timeout

**Solutions:**
1. **Verify Agent Address**: Double-check the agent address in the system prompt
2. **Check Agentverse**: Ensure the agent is deployed and running
3. **Network Issues**: Check if there are any network connectivity problems

## Debugging Steps

### Step 1: Check Logs

The agentic chat creates detailed logs. Check the log file for:
- User messages
- Enhanced email requests
- Assistant responses
- Async polling attempts
- Error messages

### Step 2: Test Gmail Helper Functions

```python
from src.asi_integration.gmail_agent_helper import GmailAgentHelper

# Test email detection
text = "Send an email to test@example.com about testing"
is_email = GmailAgentHelper.is_email_request(text)
print(f"Is email request: {is_email}")

# Test email parsing
is_valid, email_info = GmailAgentHelper.extract_email_info(text)
print(f"Email info: {email_info}")
```

### Step 3: Verify Agentic Model Response

Check if the agentic model is properly:
1. Detecting email requests
2. Formatting them correctly
3. Using the Gmail agent address
4. Waiting for responses

### Step 4: Test Direct Communication

You can test the Gmail agent directly using the example usage script:

```bash
cd src/agents/new-agents/gmail_agent/
python example_usage.py
```

## Expected Communication Flow

1. **User Request**: "Send an email to john@example.com about the meeting"
2. **Detection**: Agentic chat detects this as an email request
3. **Enhancement**: Request is formatted for Gmail agent
4. **Agentic Model**: Processes the enhanced request
5. **Gmail Agent**: Receives structured email request
6. **Email Sent**: Gmail agent sends email via Gmail API
7. **Confirmation**: Status returned to agentic chat
8. **User Feedback**: Confirmation shown to user

## Monitoring and Logs

### Agentic Chat Logs
- Location: `agentic_chat_YYYYMMDD_HHMMSS.log`
- Contains: All user messages, assistant responses, and async polling

### Gmail Agent Logs
- Check Agentverse dashboard for agent logs
- Look for OAuth authentication status
- Monitor email sending attempts

## Advanced Troubleshooting

### Custom Email Format

If the automatic formatting doesn't work, you can manually format requests:

```
send
to: recipient@example.com
subject: Email subject
content: Email content
```

### Direct Agent Communication

For testing, you can communicate directly with the Gmail agent using the uAgents protocol:

```python
from uagents import Agent, Context, Model

class EmailSendRequest(Model):
    to: str
    subject: str
    body: str

# Send directly to Gmail agent
await ctx.send("agent1qw6kgumlfqp9drr54qsfngdkz50vgues3u7sewg2fgketekqk8hz500ytg3", 
               EmailSendRequest(to="test@example.com", subject="Test", body="Test message"))
```

## Getting Help

If you're still experiencing issues:

1. **Check the test suite output** for specific error messages
2. **Review the logs** for detailed communication flow
3. **Verify Gmail agent setup** on Agentverse
4. **Test with simple email requests** first
5. **Check OAuth authentication** status

## Success Indicators

You'll know the communication is working when:

✅ Email requests are automatically detected  
✅ Requests are properly formatted for Gmail agent  
✅ Agentic chat shows "Agent is working on your request..."  
✅ Email sending confirmation is received  
✅ User gets clear feedback about email status  

The system is now configured to handle Gmail agent communication more reliably with improved detection, formatting, and response handling.
