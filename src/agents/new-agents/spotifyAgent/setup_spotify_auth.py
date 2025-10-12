"""
Spotify Authentication Setup Script

Run this script once to authenticate your Spotify agent with your account.
After successful authentication, the agent will use cached credentials.
"""

import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Spotify API Configuration
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

# Spotify scopes needed for playlist creation and music search
SPOTIFY_SCOPE = "playlist-modify-public playlist-modify-private playlist-read-private user-library-read"

def setup_spotify_auth_with_params(client_id=None, client_secret=None, redirect_uri=None, auth_code=None, cache_path=".spotify_cache"):
    """
    Set up Spotify authentication with provided parameters (for frontend integration)
    
    Args:
        client_id: Spotify client ID
        client_secret: Spotify client secret
        redirect_uri: Spotify redirect URI
        auth_code: Authorization code from OAuth callback
        cache_path: Path to cache file
    
    Returns:
        dict: Result with success status and user info
    """
    
    # Use provided parameters or fall back to environment variables
    spotify_client_id = client_id or SPOTIFY_CLIENT_ID
    spotify_client_secret = client_secret or SPOTIFY_CLIENT_SECRET
    spotify_redirect_uri = redirect_uri or SPOTIFY_REDIRECT_URI
    
    if not all([spotify_client_id, spotify_client_secret, spotify_redirect_uri]):
        return {
            'success': False,
            'error': 'Missing required Spotify credentials'
        }
    
    try:
        # Create auth manager
        auth_manager = SpotifyOAuth(
            client_id=spotify_client_id,
            client_secret=spotify_client_secret,
            redirect_uri=spotify_redirect_uri,
            scope=SPOTIFY_SCOPE,
            cache_path=cache_path,
            open_browser=False  # Don't open browser for programmatic auth
        )
        
        # If we have an auth code, use it to get tokens
        if auth_code:
            token_info = auth_manager.get_access_token(auth_code)
            if not token_info:
                return {
                    'success': False,
                    'error': 'Failed to exchange authorization code for access token'
                }
        
        # Create Spotify client
        spotify = spotipy.Spotify(auth_manager=auth_manager)
        
        # Test the connection
        user_info = spotify.current_user()
        
        # Test playlist creation capability
        playlists = spotify.current_user_playlists(limit=5)
        
        # Copy cache file to Spotify agent directory if it's not already there
        try:
            import shutil
            agent_cache_path = os.path.join(os.path.dirname(__file__), '.spotify_cache')
            
            # If the cache file doesn't exist in the agent directory, copy it from the current location
            if not os.path.exists(agent_cache_path) and os.path.exists(cache_path):
                shutil.copy2(cache_path, agent_cache_path)
                print(f"✅ Copied cache file to Spotify agent directory: {agent_cache_path}")
            elif os.path.exists(agent_cache_path):
                print(f"✅ Cache file already exists in Spotify agent directory: {agent_cache_path}")
            else:
                print(f"⚠️ Cache file not found at {cache_path}")
        except Exception as copy_error:
            print(f"⚠️ Failed to copy cache file: {copy_error}")
        
        return {
            'success': True,
            'user': {
                'display_name': user_info['display_name'],
                'email': user_info.get('email', 'N/A'),
                'followers': user_info['followers']['total'],
                'playlists_count': playlists['total']
            },
            'message': f'Successfully connected to Spotify as {user_info["display_name"]}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Authentication failed: {str(e)}'
        }

def setup_spotify_auth():
    """Set up Spotify authentication and test the connection (original function for CLI use)"""
    
    print("🎵 Setting up Spotify Authentication...")
    print(f"Client ID: {SPOTIFY_CLIENT_ID[:10]}...")
    print(f"Redirect URI: {SPOTIFY_REDIRECT_URI}")
    
    try:
        # Create auth manager
        auth_manager = SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=SPOTIFY_REDIRECT_URI,
            scope=SPOTIFY_SCOPE,
            cache_path=".spotify_cache",
            open_browser=True  # This will open browser for authentication
        )
        
        # Create Spotify client
        spotify = spotipy.Spotify(auth_manager=auth_manager)
        
        # Test the connection
        user_info = spotify.current_user()
        
        print(f"✅ Successfully connected to Spotify!")
        print(f"   User: {user_info['display_name']}")
        print(f"   Email: {user_info.get('email', 'N/A')}")
        print(f"   Followers: {user_info['followers']['total']}")
        
        # Test playlist creation capability
        playlists = spotify.current_user_playlists(limit=5)
        print(f"   Current playlists: {playlists['total']}")
        
        print("\n🎉 Authentication setup complete!")
        print("Your Spotify agent can now create real playlists on your account.")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check your .env file has correct Spotify credentials")
        print("2. Verify redirect URI matches in Spotify Developer Dashboard")
        print("3. Make sure your Spotify app is not in development mode restrictions")
        return False

if __name__ == "__main__":
    setup_spotify_auth()