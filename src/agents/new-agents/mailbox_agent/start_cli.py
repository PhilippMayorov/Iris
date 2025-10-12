#!/usr/bin/env python3
"""
Simple CLI Launcher for Mailbox Agent

This script provides an easy way to start the CLI client for the mailbox agent.
It handles common setup tasks and provides helpful guidance.
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def check_environment():
    """Check if required environment variables are set"""
    if not os.getenv('ASI_ONE_API_KEY'):
        print("❌ ASI_ONE_API_KEY environment variable not set")
        print("Please set your API key: export ASI_ONE_API_KEY='your_key_here'")
        return False
    return True

def check_agent_running(url="http://localhost:8002"):
    """Check if the mailbox agent is running"""
    try:
        response = requests.get(f"{url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Agent is running at {url}")
            print(f"📧 Agent Address: {data.get('agent_address', 'Unknown')}")
            return True
    except requests.exceptions.RequestException:
        pass
    
    print(f"❌ Agent is not running at {url}")
    return False

def start_agent_if_needed():
    """Start the agent if it's not running"""
    print("🚀 Starting mailbox agent with HTTP endpoint...")
    print("💡 This will start both the mailbox agent and HTTP API")
    print("=" * 60)
    
    # Start the agent in the background
    try:
        process = subprocess.Popen([
            sys.executable, "run_with_http.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a bit for the agent to start
        print("⏳ Waiting for agent to start...")
        time.sleep(5)
        
        # Check if it's running now
        if check_agent_running():
            print("✅ Agent started successfully!")
            return process
        else:
            print("❌ Failed to start agent")
            process.terminate()
            return None
            
    except Exception as e:
        print(f"❌ Error starting agent: {e}")
        return None

def run_cli():
    """Run the CLI client"""
    print("🎯 Starting CLI client...")
    print("=" * 60)
    
    try:
        # Run the CLI client
        subprocess.run([sys.executable, "cli_client.py", "--interactive"])
    except KeyboardInterrupt:
        print("\n👋 CLI client stopped")
    except Exception as e:
        print(f"❌ Error running CLI: {e}")

def main():
    """Main function"""
    print("🧠 Mailbox Agent CLI Launcher")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        return
    
    # Check if agent is running
    if not check_agent_running():
        print("\n🤔 Agent is not running. Would you like to start it?")
        response = input("Start agent now? (y/n): ").lower().strip()
        
        if response in ['y', 'yes']:
            agent_process = start_agent_if_needed()
            if not agent_process:
                print("❌ Cannot start agent. Please start it manually:")
                print("   python run_with_http.py")
                return
        else:
            print("❌ Agent must be running to use CLI")
            print("Start it manually with: python run_with_http.py")
            return
    
    print("\n" + "=" * 60)
    print("🎉 Ready to use CLI!")
    print("💡 Type '/help' in the CLI for available commands")
    print("💡 Type '/quit' to exit the CLI")
    print("=" * 60)
    
    # Run the CLI
    run_cli()

if __name__ == "__main__":
    main()
