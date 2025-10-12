#!/usr/bin/env python3
"""
Launcher for Intelligent Mailbox Agent

This script runs the mailbox agent from the project root directory to avoid import issues.
"""

import os
import sys
import subprocess
import time

def main():
    """Main launcher function"""
    print("🧠 Intelligent Mailbox Agent Launcher")
    print("=" * 50)
    
    # Check for ASI_ONE_API_KEY
    if not os.getenv('ASI_ONE_API_KEY'):
        print("❌ ASI_ONE_API_KEY environment variable not set")
        print("Please set your API key: export ASI_ONE_API_KEY='your_key_here'")
        return
    
    # Get the mailbox agent directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mailbox_agent_dir = os.path.join(script_dir, 'src', 'agents', 'new-agents', 'mailbox_agent')
    
    if not os.path.exists(mailbox_agent_dir):
        print(f"❌ Mailbox agent directory not found: {mailbox_agent_dir}")
        return
    
    print(f"📁 Mailbox agent directory: {mailbox_agent_dir}")
    
    # Change to the mailbox agent directory
    original_cwd = os.getcwd()
    os.chdir(mailbox_agent_dir)
    
    try:
        print("🚀 Starting Intelligent Mailbox Agent...")
        print("💡 Press Ctrl+C to stop the agent")
        print("=" * 50)
        
        # Run the setup and run script
        subprocess.run([sys.executable, "setup_and_run.py"], check=True)
        
    except KeyboardInterrupt:
        print("\n👋 Agent stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running agent: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        # Restore original working directory
        os.chdir(original_cwd)

if __name__ == "__main__":
    main()
