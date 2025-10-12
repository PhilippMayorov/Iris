# Spotify Authentication Endpoints Guide

This guide explains how to use the new Spotify authentication endpoints added to the Flask frontend application.

## Overview

The Flask app now includes three new endpoints for Spotify authentication:

1. **`POST /api/spotify/auth`** - Initiate Spotify authentication
2. **`GET /api/spotify/auth-status`** - Check authentication status
3. **`GET /api/spotify/callback`** - Handle OAuth callback (used by Spotify)

## Prerequisites

1. **Environment Variables**: Make sure your `.env` file contains:
   ```
   SPOTIFY_CLIENT_ID=your_spotify_client_id
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
   SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/api/spotify/callback
   ```

2. **Dependencies**: Install required packages:
   ```bash
   pip install spotipy
   ```

3. **Spotify App Setup**: 
   - Create a Spotify app at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Set the redirect URI to: `http://127.0.0.1:8888/api/spotify/callback`
   - Copy the Client ID and Client Secret to your `.env` file

## API Endpoints

### 1. Initiate Authentication

**Endpoint**: `POST /api/spotify/auth`

**Description**: Generates a Spotify authorization URL for user authentication.

**Request**:
```bash
curl -X POST http://127.0.0.1:8888/api/spotify/auth
```

**Response**:
```json
{
  "success": true,
  "auth_url": "https://accounts.spotify.com/authorize?client_id=...",
  "message": "Please visit the auth_url to authenticate with Spotify"
}
```

**Usage**: 
1. Call this endpoint to get the authorization URL
2. Open the URL in a browser
3. User logs in to Spotify and authorizes the app
4. Spotify redirects to the callback endpoint

### 2. Check Authentication Status

**Endpoint**: `GET /api/spotify/auth-status`

**Description**: Checks if the user is currently authenticated with Spotify.

**Request**:
```bash
curl http://127.0.0.1:8888/api/spotify/auth-status
```

**Response (Authenticated)**:
```json
{
  "success": true,
  "authenticated": true,
  "user": {
    "display_name": "John Doe",
    "email": "john@example.com",
    "followers": 42
  },
  "message": "Successfully authenticated with Spotify"
}
```

**Response (Not Authenticated)**:
```json
{
  "success": true,
  "authenticated": false,
  "message": "Not authenticated with Spotify"
}
```

### 3. OAuth Callback

**Endpoint**: `GET /api/spotify/callback`

**Description**: Handles the OAuth callback from Spotify (automatically called by Spotify).

**Request**: This endpoint is called automatically by Spotify after user authorization.

**Response**:
```json
{
  "success": true,
  "message": "Spotify authentication successful!",
  "user": {
    "display_name": "John Doe",
    "email": "john@example.com",
    "followers": 42
  }
}
```

## Testing the Endpoints

Use the provided test script to verify the endpoints work correctly:

```bash
python test_spotify_auth_endpoints.py
```

This script will:
1. Check if the Flask app is running
2. Test the authentication status
3. If not authenticated, initiate authentication
4. Guide you through the authentication process

## Integration with Spotify Agent

Once authenticated, the Spotify agent can use the cached credentials to:
- Create playlists
- Search for music
- Access user's library
- Modify playlists

The authentication is cached in `.spotify_cache` file and will persist between sessions.

## Error Handling

The endpoints include comprehensive error handling for:
- Missing environment variables
- Invalid Spotify credentials
- Network connectivity issues
- Expired tokens
- Missing dependencies

## Security Notes

- Credentials are stored in environment variables, not in code
- Tokens are cached locally in `.spotify_cache`
- The callback endpoint validates the authorization code
- All endpoints include proper error handling and logging

## Troubleshooting

1. **"Spotify dependencies not available"**: Install spotipy with `pip install spotipy`
2. **"Spotify credentials not configured"**: Check your `.env` file has all required variables
3. **"Failed to exchange authorization code"**: Verify redirect URI matches in Spotify app settings
4. **Connection errors**: Ensure Flask app is running on port 8888

## Next Steps

After successful authentication, you can integrate with the Spotify agent to:
- Create playlists based on voice commands
- Search and add songs to playlists
- Access user's music library
- Manage existing playlists
