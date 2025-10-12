# Troubleshooting Guide - Mailbox Agent

This guide helps you resolve common issues with the mailbox agent, especially the 400 Bad Request errors you're experiencing.

## 🚨 Current Issue: 400 Bad Request Errors

### Symptoms
```
Error making API request: 400 Client Error: Bad Request for url: https://api.asi1.ai/v1/chat/completions
⚠️ Error in agent routing analysis: 400 Client Error: Bad Request
⚠️ Error in request analysis: 400 Client Error: Bad Request
❌ Error getting intelligent response: 400 Client Error: Bad Request
```

### Root Causes
1. **Invalid API Key**: The ASI_ONE_API_KEY might be incorrect, expired, or not set
2. **API Request Format**: The request format might not match the current API specification
3. **Rate Limiting**: You might be hitting API rate limits
4. **API Changes**: The ASI:One API might have changed its requirements

## 🔧 Solutions

### Solution 1: Use the Fixed Agent (Recommended)

I've created a fixed version that handles API errors gracefully:

```bash
cd src/agents/new-agents/mailbox_agent
source ../../../venv/bin/activate
python run_fixed_agent.py
```

**Benefits:**
- ✅ Handles API errors gracefully
- ✅ Falls back to rule-based responses when API fails
- ✅ Still provides intelligent routing and analysis
- ✅ Works even without ASI:One API

### Solution 2: Verify API Key

1. **Check if API key is set:**
   ```bash
   echo $ASI_ONE_API_KEY
   ```

2. **Set the API key:**
   ```bash
   export ASI_ONE_API_KEY="your_actual_api_key_here"
   ```

3. **Test the API key:**
   ```bash
   cd /Users/benpetlach/Desktop/dev/hackathons/hd4/Iris
   source venv/bin/activate
   python debug_asi_api.py
   ```

### Solution 3: Use CLI Without API Dependencies

The CLI client works independently of the API issues:

```bash
cd src/agents/new-agents/mailbox_agent
source ../../../venv/bin/activate

# Start the fixed agent
python run_fixed_agent.py

# In another terminal, use the CLI
python cli_client.py
```

## 🛠️ Alternative Approaches

### Option 1: Fallback Mode
The fixed agent automatically falls back to rule-based responses when the API fails:

```python
# The agent will still work with responses like:
"Hello! I'm the Intelligent Mailbox Agent. I can help you with various tasks..."
"I'd be happy to help you send an email! However, I need to connect to the Gmail agent..."
```

### Option 2: Direct Gmail Agent Communication
If you just need email functionality, you can use the Gmail agent directly:

```bash
cd src/agents/new-agents/gmail_agent
source ../../../venv/bin/activate
python gmail_agent.py
```

### Option 3: HTTP Endpoint Only
Use the HTTP endpoint without the mailbox protocol:

```bash
cd src/agents/new-agents/mailbox_agent
source ../../../venv/bin/activate
python http_endpoint.py
```

## 🔍 Debugging Steps

### Step 1: Check Environment
```bash
# Check Python environment
which python
python --version

# Check virtual environment
source venv/bin/activate
which python

# Check dependencies
pip list | grep -E "(httpx|rich|uagents)"
```

### Step 2: Test API Connection
```bash
# Test basic API connectivity
curl -H "Authorization: Bearer $ASI_ONE_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model": "asi1-mini", "messages": [{"role": "user", "content": "Hello"}]}' \
     https://api.asi1.ai/v1/chat/completions
```

### Step 3: Check Logs
Look for specific error messages in the agent output:
- Authentication errors
- Rate limiting messages
- Network connectivity issues
- Request format errors

## 📋 Common Error Messages and Solutions

### "ASI_ONE_API_KEY not found"
```bash
export ASI_ONE_API_KEY="your_key_here"
```

### "Failed to initialize ASI:One client"
- Check API key validity
- Verify internet connectivity
- Check API service status

### "400 Client Error: Bad Request"
- Use the fixed agent version
- Check API key format
- Verify request payload structure

### "Connection timeout"
- Check network connectivity
- Try again later (API might be down)
- Use fallback mode

## 🚀 Quick Fix Commands

### Start Fixed Agent
```bash
cd src/agents/new-agents/mailbox_agent
source ../../../venv/bin/activate
python run_fixed_agent.py
```

### Test CLI
```bash
# In another terminal
cd src/agents/new-agents/mailbox_agent
source ../../../venv/bin/activate
python cli_client.py --message "Hello, how are you?"
```

### Check Agent Status
```bash
curl http://localhost:8002/health
```

## 📞 Getting Help

If you continue to experience issues:

1. **Check the logs** for specific error messages
2. **Try the fixed agent** which handles errors gracefully
3. **Use fallback mode** for basic functionality
4. **Contact support** with specific error messages

## 🎯 What Works Right Now

Even with the API issues, you can still:

- ✅ Use the CLI client
- ✅ Send messages to the agent
- ✅ Get rule-based responses
- ✅ Use the HTTP endpoint
- ✅ Access agent routing logic
- ✅ Maintain conversation history

The fixed agent provides a robust fallback system that ensures the mailbox agent continues to work even when the ASI:One API is having issues.

## 🔄 Next Steps

1. **Try the fixed agent**: `python run_fixed_agent.py`
2. **Test the CLI**: `python cli_client.py`
3. **Verify functionality**: Send a test message
4. **Check logs**: Look for any remaining errors

The mailbox agent should now work reliably even with API issues! 🎉
