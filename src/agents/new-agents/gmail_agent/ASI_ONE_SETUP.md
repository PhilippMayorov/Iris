# ASI:One Integration Setup Guide

This guide will help you set up ASI:One integration with the Gmail Agent for enhanced natural language email processing.

## What is ASI:One?

ASI:One is an LLM created by Fetch.ai that connects to specialized agents, allowing it to answer domain-specific questions and perform tasks. By integrating ASI:One with the Gmail Agent, you can send emails using natural language instead of structured commands.

## Prerequisites

1. **Gmail Agent Setup**: Complete the basic Gmail agent setup first (see `OAUTH_SETUP_GUIDE.md`)
2. **Internet Connection**: ASI:One requires internet access
3. **Python Environment**: Make sure you have Python 3.8+ installed

## Step 1: Get ASI:One API Key

1. Visit [asi1.ai](https://asi1.ai)
2. Create an account or sign in
3. Go to [API Keys Dashboard](https://asi1.ai/dashboard/api-keys)
4. Create a new API key
5. Copy the API key (you'll need it in the next step)

## Step 2: Set Environment Variable

### On macOS/Linux:
```bash
export ASI_ONE_API_KEY="your_api_key_here"
```

### On Windows:
```cmd
set ASI_ONE_API_KEY=your_api_key_here
```

### Permanent Setup (Recommended):

**On macOS/Linux:**
Add to your `~/.bashrc` or `~/.zshrc`:
```bash
echo 'export ASI_ONE_API_KEY="your_api_key_here"' >> ~/.bashrc
source ~/.bashrc
```

**On Windows:**
Add to your system environment variables through System Properties.

## Step 3: Install Dependencies

Make sure you have the latest requirements installed:

```bash
pip install -r requirements.txt
```

The requirements now include `openai>=1.0.0` for ASI:One integration.

## Step 4: Test the Integration

Run the test script to verify ASI:One integration:

```bash
python test_asi_one_integration.py
```

You should see output like:
```
🧪 Testing ASI:One Integration with Gmail Agent
==================================================
✅ ASI:One client is available

Test 1: Simple email request
Input: Send an email to john@example.com saying hello
✅ Processing successful
   To: john@example.com
   Subject: (no subject)
   Body: hello
✅ All expected fields present
```

## Step 5: Start the Gmail Agent

Start the Gmail agent with ASI:One integration:

```bash
python gmail_agent.py
```

You should see output like:
```
Gmail Agent Address: agent1qw6kgumlfq...
✅ OAuth authentication successful: Authenticated as: your.email@gmail.com
Ready to send emails!

✅ ASI:One AI integration enabled
Enhanced natural language email processing available

Starting agent...
```

## Step 6: Use Natural Language

Now you can send emails using natural language! Here are some examples:

### Via ASI:One Chat
1. Go to [ASI:One Chat](https://chat.asi1.ai)
2. Ask to connect to a Gmail agent
3. Send natural language requests like:
   - "Send an email to john@example.com about the meeting tomorrow"
   - "Email the team about the project update"
   - "Write to client@company.com saying we'll deliver on time"

### Via Direct Agent Communication
Use the example script:
```bash
python example_asi_one_usage.py
```

## Natural Language Examples

The Gmail Agent with ASI:One can understand various natural language patterns:

### Simple Requests
- "Send an email to john@example.com saying hello"
- "Email sarah@company.com about the meeting"
- "Write to team@business.com"

### Requests with Subjects
- "Send an email to client@company.com with subject 'Project Update' and tell them we're on track"
- "Email john@example.com about 'Meeting Tomorrow' and ask if 2 PM works"

### Complex Requests
- "Write to the team about the project status and ask for their feedback on the timeline"
- "Send a thank you email to sarah@company.com for the great meeting yesterday"

## Troubleshooting

### ASI:One Client Not Available
```
❌ ASI:One client not available
Please set ASI_ONE_API_KEY environment variable
```

**Solution**: Make sure you've set the `ASI_ONE_API_KEY` environment variable correctly.

### API Key Invalid
```
❌ Failed to initialize ASI:One client: Incorrect API key provided
```

**Solution**: 
1. Check your API key at [asi1.ai/dashboard/api-keys](https://asi1.ai/dashboard/api-keys)
2. Make sure you copied the key correctly
3. Ensure there are no extra spaces or characters

### Network Issues
```
❌ ASI:One processing failed: Connection error
```

**Solution**:
1. Check your internet connection
2. Verify you can access [api.asi1.ai](https://api.asi1.ai)
3. Check if your firewall is blocking the connection

### Fallback Behavior
If ASI:One is not available or fails, the agent automatically falls back to the structured format:

```
send
to: email@example.com
subject: Email subject (optional)
content: Email content
```

## Benefits of ASI:One Integration

1. **Natural Language**: No need to remember specific command formats
2. **Context Understanding**: ASI:One understands the intent behind your requests
3. **Intelligent Extraction**: Automatically extracts email details from natural language
4. **Enhanced UX**: More conversational and user-friendly experience
5. **Fallback Support**: Always works, even without ASI:One

## Advanced Usage

### Custom Prompts
The agent uses a specialized prompt for email extraction. You can modify the `process_email_request_with_asi_one` function in `gmail_agent.py` to customize the behavior.

### Error Handling
The integration includes comprehensive error handling:
- API key validation
- Network error handling
- Response parsing validation
- Automatic fallback to structured format

### Rate Limiting
ASI:One API calls are subject to rate limits. The agent handles this gracefully and falls back to structured format if needed.

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify your API key and environment setup
3. Test with the provided test script
4. Check the agent logs for detailed error messages

For ASI:One specific issues, visit the [ASI:One documentation](https://docs.asi1.ai) or contact Fetch.ai support.

---

*This integration enhances the Gmail Agent with powerful natural language processing capabilities while maintaining full backward compatibility with the structured format.*
