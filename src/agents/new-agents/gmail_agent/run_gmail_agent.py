#!/usr/bin/env python3
"""
Simple script to run the Gmail Agent

This script provides an easy way to start the Gmail agent with proper configuration.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from gmail_agent import agent, PORT

if __name__ == "__main__":
    print("🚀 Starting Gmail Agent...")
    print(f"Agent Address: {agent.address}")
    print(f"Agent Name: {agent.name}")
    print(f"Port: {PORT}")
    print()
    print("Make sure you have:")
    print("✅ Google Cloud credentials set up")
    print("✅ Gmail API enabled")
    print("✅ Authenticated with gcloud auth application-default login")
    print()
    print("Press Ctrl+C to stop the agent")
    print("-" * 50)
    
    try:
        agent.run()
    except KeyboardInterrupt:
        print("\n👋 Gmail Agent stopped by user")
    except Exception as e:
        print(f"\n❌ Error running Gmail Agent: {e}")
        sys.exit(1)
