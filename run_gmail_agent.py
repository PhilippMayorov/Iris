#!/usr/bin/env python3
"""
Script to run Gmail Agent with proper environment variable loading
"""

import os
import sys
from pathlib import Path

def load_env_file(env_path=".env"):
    """Load environment variables from .env file"""
    if not os.path.exists(env_path):
        print(f"❌ {env_path} file not found!")
        return False
    
    print(f"📁 Loading environment variables from {env_path}...")
    
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    
    print("✅ Environment variables loaded successfully")
    return True

def check_asi_one_key():
    """Check if ASI:One API key is loaded"""
    api_key = os.getenv('ASI_ONE_API_KEY')
    if api_key:
        print(f"✅ ASI:One API key loaded successfully")
        print(f"🔑 API key starts with: {api_key[:10]}...")
        return True
    else:
        print("❌ ASI:One API key not found!")
        print("Please make sure ASI_ONE_API_KEY is set in your .env file")
        return False

def main():
    print("🚀 Starting Gmail Agent with environment variables...")
    
    # Load environment variables
    if not load_env_file():
        sys.exit(1)
    
    # Check ASI:One API key
    if not check_asi_one_key():
        sys.exit(1)
    
    # Change to Gmail agent directory
    gmail_agent_dir = Path(__file__).parent / "src" / "agents" / "new-agents" / "gmail_agent"
    if not gmail_agent_dir.exists():
        print(f"❌ Gmail agent directory not found: {gmail_agent_dir}")
        sys.exit(1)
    
    print(f"📂 Changing to Gmail agent directory: {gmail_agent_dir}")
    os.chdir(gmail_agent_dir)
    
    print("🤖 Starting Gmail Agent...")
    print("")
    
    # Import and run the Gmail agent
    try:
        import gmail_agent
        # The gmail_agent module will run when imported
    except ImportError as e:
        print(f"❌ Failed to import Gmail agent: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running Gmail agent: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
