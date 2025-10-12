# Slack OAuth Redirect URI Fix Guide

## 🚨 Problem

Getting error: `redirect_uri did not match any configured URIs. Passed URI: https://localhost:8080/callback`

## ✅ Solution Steps

### Step 1: Update Slack App Configuration

1. **Go to Slack App Management**

   - Visit: https://api.slack.com/apps
   - Select your "Demo App" (or your app name)

2. **Navigate to OAuth & Permissions**

   - In left sidebar, click "OAuth & Permissions"

3. **Configure Redirect URLs**
   - Find the "Redirect URLs" section
   - **Remove any old redirect URIs** (like `https://localhost:8080/slack/callback`)
   - **Add the exact URI**: `https://localhost:8080/callback`
   - Click "Save URLs"

### Step 2: Verify Environment Configuration

Your `.env` file should have:

```bash
SLACK_REDIRECT_URI=https://localhost:8080/callback
```

✅ **This is already correctly configured in your project!**

### Step 3: HTTPS Local Development Setup

Since Slack requires HTTPS, you have these options:

#### Option A: Use ngrok (Recommended)

```bash
# Install ngrok if you haven't
brew install ngrok  # or download from ngrok.com

# Start tunnel
ngrok http 8080

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Update your .env file:
SLACK_REDIRECT_URI=https://abc123.ngrok.io/callback

# Update Slack App settings with the same ngrok URL
```

#### Option B: Use localhost.run

```bash
# Start tunnel
ssh -R 80:localhost:8080 nokey@localhost.run

# Copy the provided HTTPS URL
# Update .env and Slack App settings accordingly
```

#### Option C: Accept Browser HTTPS Warning

- Keep `https://localhost:8080/callback`
- Your browser will show a security warning
- Click "Advanced" → "Proceed to localhost (unsafe)"

### Step 4: Verify Configuration

Run the setup script to verify everything is correct:

```bash
cd /Users/philippmayorov/Desktop/WesternUniversity/Hackathons/VocalAgentTest2/src/agents/new-agents/slack_agent
python setup_slack_agent.py
```

Look for:

- ✅ Valid HTTPS redirect URI
- ✅ Redirect URI in URL matches environment variable

### Step 5: Test OAuth Flow

1. **Start the setup script** and choose to open the OAuth URL
2. **In the browser**, you should see the Slack authorization page
3. **Click "Allow"** to authorize your app
4. **You should be redirected** to your callback URL
5. **The URL should contain** a `code` parameter

### Step 6: Common Issues & Solutions

#### "This site can't be reached" / "ERR_CONNECTION_REFUSED"

- **Cause**: No server running at the callback URL during setup
- **Solution**: This is COMPLETELY NORMAL! ✅
- **What it means**: OAuth authorization was successful
- **Next step**: Start the agent with `python slack_agent.py`
- **Details**: See CONNECTION_REFUSED_GUIDE.md for full explanation

#### "Your connection is not private" HTTPS warning

- **Cause**: Self-signed certificate for localhost
- **Solution**: Click "Advanced" → "Proceed to localhost"

#### Still getting redirect_uri mismatch

- **Double-check**: Slack App settings have EXACT URI: `https://localhost:8080/callback`
- **Case-sensitive**: Make sure it's exactly the same
- **No extra slashes**: Should end with `/callback` not `/callback/`

## 🎯 Final Verification

After configuration, your OAuth URL should look like:

```
https://slack.com/oauth/v2/authorize?client_id=9667019145591.9667097284167&scope=users%3Aread%2Cconversations%3Aread%2Cconversations%3Ahistory%2Cchat%3Awrite%2Cim%3Aread%2Cim%3Awrite%2Cchannels%3Aread%2Cgroups%3Aread&user_scope=chat%3Awrite&redirect_uri=https%3A%2F%2Flocalhost%3A8080%2Fcallback&response_type=code
```

And when you click it, Slack should show the authorization page without any redirect URI errors!

## 🚀 Next Steps

Once OAuth is working:

1. Start the agent: `python slack_agent.py`
2. Send "authenticate" to begin OAuth flow
3. Test messaging: "Send [username] a message saying hello"
