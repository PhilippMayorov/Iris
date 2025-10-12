# Gmail Agent with ASI:One Integration

An AI agent that enables you to send emails through Gmail using natural language or structured commands. Enhanced with ASI:One LLM for intelligent email processing.

## What It Does

The Gmail Agent allows you to send emails using natural language or structured commands. It handles authentication with your Gmail account and sends emails on your behalf. When ASI:One is enabled, it can understand and process natural language email requests intelligently.

## Key Features

### 🤖 ASI:One AI Integration
- **Natural Language Processing**: Send emails using natural language
- **Intelligent Email Extraction**: ASI:One understands context and extracts email details
- **Enhanced User Experience**: No need to remember specific command formats
- **Fallback Support**: Works with or without ASI:One API key

### 📧 Email Sending
- Send emails through your Gmail account
- Natural language or structured command format
- Optional subject lines (emails can be sent without subjects)
- Automatic validation and error checking

### 🔐 Secure Authentication
- Connects to your Gmail account securely
- One-time setup process
- Your credentials are stored safely

### 💬 Easy to Use
- Works through chat interface
- Clear error messages when something goes wrong
- Real-time feedback on email status

## How to Use

### Getting Started

1. **First Time Setup**
   - The agent will guide you through connecting to your Gmail account
   - You'll need to authenticate once through your browser
   - After setup, you can send emails immediately

2. **ASI:One Setup (Optional but Recommended)**
   - Get your ASI:One API key from [asi1.ai/dashboard/api-keys](https://asi1.ai/dashboard/api-keys)
   - Set the environment variable: `export ASI_ONE_API_KEY="your_api_key_here"`
   - This enables natural language email processing

### Usage Methods

#### Natural Language (ASI:One Enabled)
Just tell the agent what you want to send in ANY way you want! The AI understands casual, formal, incomplete, or even very brief requests:

**Complete Examples:**
- "Send an email to john@example.com about the meeting tomorrow"
- "Email the team about the project update"
- "Write to client@company.com saying we'll deliver on time"
- "Send a thank you email to sarah@business.com for the great meeting"

**Casual/Incomplete Examples (AI will ask for missing info):**
- "email john about the meeting" → AI asks for john's email
- "tell the boss we're done" → AI asks for boss's email
- "quick note to client" → AI asks for client's email and what to write
- "meeting tomorrow 2pm" → AI asks who to send to
- "write to sarah" → AI asks for sarah's email and what to write
- "send something to team@company.com" → AI asks what to send

**Context-Aware Examples (AI remembers previous conversations):**
- After saying "john@company.com" → "email him about the meeting" (AI remembers john's email)
- After mentioning "the project" → "update the team" (AI references the project context)
- After saying "sarah is my manager" → "tell her we're done" (AI uses sarah's context)
- "same person as before" → AI reuses previous recipient information

#### AI-Only Processing
The agent now uses ASI:One AI exclusively for all email parsing. No structured format required - just talk naturally!

### Examples

**Natural Language Examples (ASI:One enabled):**
- "Send an email to john@example.com saying 'Hi John, hope you're doing well!'"
- "Email team@company.com with subject 'Project Update' and tell them we're on track"
- "Write to client@business.com about the proposal review and ask for their thoughts"
- "email john about the meeting" (AI will ask for john's email)
- "tell the boss we're done" (AI will ask for boss's email)
- "quick note to client" (AI will ask for client's email and what to write)

**More Natural Language Examples:**

**Complete requests:**
- "Send an email to john@example.com saying 'Hi John, hope you're doing well!'"
- "Email team@company.com with subject 'Project Update' and tell them we're on track"
- "Write to client@business.com about the proposal review and ask for their thoughts"

**Casual requests (AI will ask for missing info):**
- "email john about the meeting" → AI asks for john's email
- "tell the boss we're done" → AI asks for boss's email
- "quick note to client" → AI asks for client's email and what to write

### Important Notes

**For Natural Language (ASI:One enabled):**
- Just describe what you want to send in ANY way you want
- Be as casual, formal, complete, or incomplete as you like
- ASI:One will understand context and ask for missing information
- Works with conversational language, names, roles, or partial information
- Don't worry about being perfect - the AI will help you complete your request

**For AI Processing:**
- **No format requirements** - just talk naturally
- **AI handles everything** - parsing, validation, suggestions
- **Intelligent reasoning** - understands context and intent
- **Helpful guidance** - asks for missing information with suggestions

### What Happens When You Send

**With ASI:One enabled:**
1. ASI:One processes your natural language request (no matter how casual or incomplete)
2. Uses intelligent reasoning and conversation context to understand your intent
3. Remembers previous conversations and references (names, email addresses, topics)
4. Extracts or suggests recipient, subject, and content based on context
5. Asks for clarification if information is missing
6. Validates the information and sends the email
7. Provides confirmation with message ID and AI reasoning
8. Maintains conversation history for future interactions

**Without ASI:One:**
1. The agent will inform you that ASI:One AI is required
2. Provides instructions to get and set up ASI:One API key
3. No email functionality available without AI integration

### Common Scenarios

**Missing information (AI will ask for clarification):**
```
🤔 I need a bit more information to help you send that email.
What I understood: You want to email john about a meeting
What I need:
- Please specify john's email address (e.g., 'john@example.com')
- Consider adding more details about the meeting
```

**ASI:One not available:**
```
❌ ASI:One AI is required for natural language email processing. 
Please set ASI_ONE_API_KEY environment variable to enable intelligent email parsing.
```

### Rate Limits

- You can send up to 10 emails per hour
- If you exceed this limit, you'll get a clear message
- The limit resets every hour

## Troubleshooting

**Can't send emails?**
- Make sure you've completed the initial Gmail authentication
- Ensure ASI:One API key is set (ASI_ONE_API_KEY environment variable)
- Just talk naturally - no specific format required

**Authentication issues?**
- The agent will provide a link to re-authenticate if needed
- Make sure you're using the same Gmail account you set up initially

**Still having problems?**
- Check the error message for specific guidance
- The AI will ask for any missing information with helpful suggestions
- Just describe what you want to send in your own words

## ASI:One Integration

This Gmail Agent is enhanced with ASI:One LLM integration, providing intelligent natural language processing for email requests.

### Benefits of ASI:One Integration

- **Natural Language Understanding**: Send emails using conversational language
- **Context Awareness**: ASI:One understands the intent behind your requests
- **Intelligent Extraction**: Automatically extracts email details from natural language
- **Enhanced User Experience**: No need to remember specific command formats

### Setup ASI:One

1. **Get API Key**: Visit [asi1.ai/dashboard/api-keys](https://asi1.ai/dashboard/api-keys)
2. **Set Environment Variable**: `export ASI_ONE_API_KEY="your_api_key_here"`
3. **Restart Agent**: The agent will automatically detect and enable ASI:One features

### How It Works

When you send a natural language request like "Send an email to john@example.com about the meeting tomorrow", ASI:One:

1. Analyzes your request
2. Extracts the recipient email address
3. Determines the subject (if mentioned)
4. Extracts the message content
5. Returns structured data for the Gmail API

### AI-Only Processing

The agent now relies exclusively on ASI:One AI for all email parsing and processing. This ensures consistent, intelligent handling of all user requests without the need for strict formatting requirements.

---

*This agent is designed for secure, reliable email sending through Gmail with intelligent AI-powered natural language processing via ASI:One.*