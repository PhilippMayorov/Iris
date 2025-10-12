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

def setup_spotify_auth():
    """Set up Spotify authentication and test the connection"""
    
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