#!/usr/bin/env python3
"""
Debug script for Spotify authentication issue
"""

import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def debug_spotify_auth():
    """Debug the Spotify authentication setup"""
    print("🔍 Debugging Spotify Authentication...")
    
    # Check environment variables
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')
    
    print(f"Client ID: {client_id[:10] if client_id else 'None'}...")
    print(f"Client Secret: {'*' * 10 if client_secret else 'None'}")
    print(f"Redirect URI: {redirect_uri}")
    
    if not all([client_id, client_secret, redirect_uri]):
        print("❌ Missing environment variables!")
        return False
    
    try:
        # Create auth manager
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
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating auth URL: {e}")
        return False

if __name__ == "__main__":
    debug_spotify_auth()
