#!/usr/bin/env python3
"""
Simple chat launcher for the Intelligent Mailbox Agent

This provides a simple way to chat with your mailbox agent via CLI.
"""

import os
import sys
import subprocess

def main():
    """Main launcher function"""
    print("🧠 Intelligent Mailbox Agent - CLI Chat")
    print("=" * 50)
    
    # Check if rich is installed
    try:
        import rich
    except ImportError:
        print("📦 Installing CLI dependencies...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "rich", "httpx"], check=True)
            print("✅ Dependencies installed!")
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies. Please run: pip install rich httpx")
            return
    
    # Run the CLI client
    try:
        from cli_client import main as cli_main
        import asyncio
        asyncio.run(cli_main())
    except ImportError as e:
        print(f"❌ Error importing CLI client: {e}")
        print("Make sure you're running this from the mailbox_agent directory")

if __name__ == "__main__":
    main()
