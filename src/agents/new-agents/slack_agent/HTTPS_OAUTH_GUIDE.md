# Slack HTTPS OAuth Setup Guide

## Important: Slack Requires HTTPS

Slack **requires HTTPS for all OAuth redirect URIs**, including `localhost` for development. This is a security requirement that cannot be bypassed.

## What the Setup Script Does

1. **Creates Self-Signed SSL Certificate**: Automatically generates `localhost.crt` and `localhost.key`
2. **Starts HTTPS Server**: Runs secure server on `https://localhost:8080`
3. **Handles Browser Security Warnings**: Provides guidance on bypassing browser warnings

## Browser Security Warning

When you authorize the app, your browser will show a security warning because we're using a self-signed certificate:

### Chrome/Edge:

1. Click **"Advanced"**
2. Click **"Proceed to localhost (unsafe)"**

### Firefox:

1. Click **"Advanced"**
2. Click **"Accept the Risk and Continue"**

### Safari:

1. Click **"Show Details"**
2. Click **"visit this website"**
3. Click **"Visit Website"**

**This is completely safe** - it's your own local server with a certificate you just created.

## Files Created

The setup script creates these SSL files in the slack_agent directory:

- `localhost.crt` - SSL certificate
- `localhost.key` - Private key

These files are **automatically generated** and valid for 1 year.

## Troubleshooting

### "ERR_SSL_PROTOCOL_ERROR"

- **Cause**: Server not running HTTPS properly
- **Fix**: Script now creates proper SSL certificate and HTTPS server

### "NET::ERR_CERT_AUTHORITY_INVALID"

- **Cause**: Self-signed certificate (expected)
- **Fix**: Click "Advanced" → "Proceed to localhost" in browser

### "This site can't provide a secure connection"

- **Cause**: SSL certificate issue
- **Fix**: Delete `localhost.crt` and `localhost.key`, run setup again

### Connection Refused

- **Cause**: HTTPS server not started
- **Fix**: Ensure setup script is running and shows "HTTPS callback server running"

## Security Notes

- ✅ Self-signed certificates are **safe for localhost development**
- ✅ SSL files are created locally on your machine only
- ✅ Private key never leaves your computer
- ✅ This follows industry standard practices for local HTTPS development

## Production Deployment

For production apps, use a proper SSL certificate from a Certificate Authority (CA) like:

- Let's Encrypt (free)
- DigiCert
- Cloudflare

## Quick Start

1. **Update Slack App**: Set redirect URI to `https://localhost:8080/callback`
2. **Run Setup**: `python setup_slack_agent.py`
3. **Choose Option 1**: Complete OAuth flow now
4. **Accept Browser Warning**: Click "Advanced" → "Proceed to localhost"
5. **Authorize App**: Complete Slack authorization
6. **Done**: Tokens saved securely

The script handles all SSL certificate creation automatically!
