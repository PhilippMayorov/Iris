#!/usr/bin/env python3
"""
Test the updated Spotify auth URL generation
"""

import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_updated_auth():
    """Test the updated authentication with correct redirect URI"""
    print("🧪 Testing Updated Spotify Authentication...")
    
    # Get credentials
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    # Use the correct redirect URI for frontend
    redirect_uri = 'http://127.0.0.1:5001/api/spotify/callback'
    
    print(f"Client ID: {client_id[:10] if client_id else 'None'}...")
    print(f"Redirect URI: {redirect_uri}")
    
    try:
        # Create auth manager with correct redirect URI
        scope = "playlist-modify-public playlist-modify-private playlist-read-private user-library-read"
        
        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope,
            cache_path=".spotify_cache"
        )
        
        # Get authorization URL
        auth_url = auth_manager.get_authorize_url()
        
        print(f"✅ Auth URL generated successfully!")
        print(f"URL: {auth_url}")
        
        # Check if URL contains the correct redirect URI
        if "127.0.0.1:5001" in auth_url and "api/spotify/callback" in auth_url:
            print("✅ Redirect URI is correct in the auth URL!")
            return True
        else:
            print("❌ Redirect URI is incorrect in the auth URL!")
            return False
        
    except Exception as e:
        print(f"❌ Error generating auth URL: {e}")
        return False

if __name__ == "__main__":
    test_updated_auth()
