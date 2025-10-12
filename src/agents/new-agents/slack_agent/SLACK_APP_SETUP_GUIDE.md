# Slack App Configuration Guide

This guide walks you through setting up your Slack app for OAuth 2.0 authentication following Slack's official documentation.

## Prerequisites

1. A Slack workspace where you have permission to install apps
2. A Slack app created at https://api.slack.com/apps

## Step 1: Create Slack App (if not done already)

1. Go to https://api.slack.com/apps
2. Click "Create New App"
3. Choose "From scratch"
4. Enter app name (e.g., "Vocal Agent")
5. Select your development workspace
6. Click "Create App"

## Step 2: Configure OAuth & Permissions

### Redirect URLs

1. In your app settings, go to **OAuth & Permissions**
2. Scroll to **Redirect URLs** section
3. Click **Add New Redirect URL**
4. Add: `http://localhost:8080/callback`
5. Click **Save URLs**

**Important**: The redirect URL must match exactly what's in your `.env` file.

### Bot Token Scopes

In the **Scopes** section under **Bot Token Scopes**, add these scopes:

- `chat:write` - Send messages to channels and DMs
- `im:write` - Send direct messages
- `im:read` - Read direct messages
- `channels:read` - View basic info about public channels
- `im:history` - View messages in direct messages
- `users:read` - View people in workspace

### User Token Scopes (Optional)

Under **User Token Scopes**, add if you want the agent to act as the user:

- `chat:write` - Send messages as user

## Step 3: Get App Credentials

1. In your app settings, go to **Basic Information**
2. Under **App Credentials**, copy:
   - **Client ID** → Add to `.env` as `SLACK_CLIENT_ID`
   - **Client Secret** → Add to `.env` as `SLACK_CLIENT_SECRET`

## Step 4: Update .env File

Your `.env` file should have:

```bash
# Slack Integration
SLACK_CLIENT_ID=your_client_id_here
SLACK_CLIENT_SECRET=your_client_secret_here
SLACK_REDIRECT_URI=http://localhost:8080/callback
ENCRYPTION_KEY=your_encryption_key_here
```

## Step 5: Run Setup

```bash
cd src/agents/new-agents/slack_agent
python setup_slack_agent.py
```

## OAuth Flow Overview

Following Slack's OAuth 2.0 documentation:

1. **Authorization Request**: User is directed to Slack's authorization URL
2. **User Authorization**: User approves the app in their browser
3. **Authorization Code**: Slack redirects back with temporary code
4. **Token Exchange**: App exchanges code for access tokens
5. **Token Storage**: Tokens are saved securely for future use

## Troubleshooting

### "redirect_uri did not match"

- Ensure redirect URI in Slack app settings matches exactly: `http://localhost:8080/callback`
- Check for typos, extra spaces, or protocol mismatches

### "This site can't be reached" during setup

- This is normal when manually testing - no server is running yet
- The setup script starts its own server during automated OAuth flow

### "invalid_client_id" or "invalid_client_secret"

- Double-check your credentials in `.env` file
- Ensure no extra spaces or quotes around the values

### Scopes not working

- Verify all required scopes are added in Slack app settings
- Re-run the OAuth flow after adding new scopes

## Security Notes

- Keep your Client Secret secure and never commit it to version control
- Use HTTPS redirect URIs for production applications
- The setup script encrypts tokens before storing them locally

## References

- [Slack OAuth 2.0 Documentation](https://api.slack.com/authentication/oauth-v2)
- [Slack API Scopes](https://api.slack.com/scopes)
- [Slack App Management](https://api.slack.com/apps)
