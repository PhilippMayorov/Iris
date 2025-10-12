# URGENT: Update Your Slack App Redirect URI

## What Happened

The setup script is now working correctly with HTTP localhost, but your Slack app configuration needs to be updated.

## Required Action

1. Go to: https://api.slack.com/apps
2. Select your Slack app
3. Navigate to: **OAuth & Permissions**
4. In the **Redirect URLs** section:
   - Remove: `https://localhost:8080/callback` (if present)
   - Add: `http://localhost:8080/callback`
5. Click **Save URLs**

## Why This Change?

- HTTPS localhost requires SSL certificates which cause "connection refused" errors
- HTTP localhost works perfectly for local development
- Slack allows HTTP for localhost development URLs
- For production, you would use HTTPS with a proper domain

## Test the Setup Again

After updating your Slack app configuration:

```bash
cd src/agents/new-agents/slack_agent
python setup_slack_agent.py
```

Choose option 1 (Complete OAuth flow now) and complete the authorization in your browser.

## What Should Happen

1. Setup script starts HTTP server on localhost:8080 ✅
2. Browser opens Slack authorization page ✅
3. You authorize the app ✅
4. Slack redirects to http://localhost:8080/callback ✅
5. Setup script receives the authorization code ✅
6. Tokens are exchanged and saved securely ✅

## Current Status

Your setup script is now properly configured and working. You just need to update the Slack app's redirect URI to match the HTTP localhost URL.
