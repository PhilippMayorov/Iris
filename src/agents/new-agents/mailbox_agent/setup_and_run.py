#!/usr/bin/env python3
"""
Setup and Run Script for Intelligent Mailbox Agent

This script helps set up and run the mailbox agent with all necessary configurations.
"""

import os
import sys
import subprocess
import time

def check_environment():
    """Check if the environment is properly set up"""
    print("🔍 Checking environment...")
    
    # Check for ASI_ONE_API_KEY
    if not os.getenv('ASI_ONE_API_KEY'):
        print("❌ ASI_ONE_API_KEY environment variable not set")
        print("Please set your API key: export ASI_ONE_API_KEY='your_key_here'")
        return False
    
    print("✅ ASI_ONE_API_KEY is set")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    
    print(f"✅ Python version: {sys.version}")
    
    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True, capture_output=True, text=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print(f"Error output: {e.stderr}")
        return False

def run_agent():
    """Run the mailbox agent"""
    print("🚀 Starting Intelligent Mailbox Agent...")
    
    try:
        # Import and run the agent
        from run_with_http import main
        main()
    except KeyboardInterrupt:
        print("\n👋 Agent stopped by user")
    except Exception as e:
        print(f"❌ Error running agent: {e}")
        return False
    
    return True

def main():
    """Main setup and run function"""
    print("🧠 Intelligent Mailbox Agent Setup & Run")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed. Please fix the issues above.")
        return
    
    print()
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Dependency installation failed. Please fix the issues above.")
        return
    
    print()
    
    # Run the agent
    print("🎯 Starting the agent...")
    print("💡 Press Ctrl+C to stop the agent")
    print("=" * 50)
    
    run_agent()

if __name__ == "__main__":
    main()
