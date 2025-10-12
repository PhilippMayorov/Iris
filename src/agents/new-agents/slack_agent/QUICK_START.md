# 🚀 Slack Agent - Quick Start Guide

Get your Slack agent up and running in minutes!

## 📋 Prerequisites

- Python 3.8+
- Slack workspace (admin permissions recommended)
- ASI:One API key ([Get one here](https://asi1.ai/dashboard/api-keys))

## ⚡ Quick Setup (5 minutes)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Setup Wizard

```bash
python setup_slack_agent.py
```

The setup wizard will guide you through:

- Creating a Slack app
- Configuring OAuth2 permissions
- Setting up environment variables
- Testing the configuration

### 3. Start the Agent

```bash
python slack_agent.py
```

### 4. Authenticate

Once the agent is running, send it a message:

```
"Connect my Slack account"
```

This will open a browser for OAuth2 authorization.

## 🎯 Test It Out

Try these commands after authentication:

### Send Messages

```
"Send Alice a message saying I'll be late"
"Tell Ben: Meeting moved to 3pm"
"Message Charlie that the project is done"
```

### Read Messages

```
"Read my last message from Alice"
"Show messages from Ben"
```

## 🛠️ Manual Setup (Advanced)

If you prefer manual configuration:

### 1. Create Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Name your app and select workspace

### 2. Configure Permissions

Add these scopes in "OAuth & Permissions":

- `users:read`
- `conversations:read`
- `conversations:history`
- `chat:write`
- `im:read`
- `im:write`
- `channels:read`
- `groups:read`

### 3. Set Redirect URL

Add: `http://localhost:8080/slack/callback`

### 4. Create .env File

```bash
SLACK_CLIENT_ID=your_client_id
SLACK_CLIENT_SECRET=your_client_secret
SLACK_REDIRECT_URI=http://localhost:8080/slack/callback
ASI_ONE_API_KEY=your_asi_one_key
```

## 🧪 Testing

Run the test suite to verify everything works:

```bash
python test_slack_agent.py
```

## 🚨 Common Issues

### "Missing environment variables"

- Run the setup wizard: `python setup_slack_agent.py`
- Check that all variables are in `.env` file

### "User not found"

- Use exact display names from Slack
- Make sure user is in your workspace
- Try with User ID instead of name

### "OAuth server failed"

- Check if port 8080 is available
- Verify redirect URI matches Slack app configuration

## 📚 More Information

- **Full Documentation**: See `README_SLACK.md`
- **Troubleshooting**: Check the test script output
- **Integration**: Works with other agents in the VocalAgent system

## 🎉 You're Ready!

Your Slack agent is now configured and ready to:

- ✅ Send messages to Slack users
- ✅ Read conversation history
- ✅ Process natural language commands
- ✅ Handle OAuth2 authentication securely

**Happy messaging!** 🚀
