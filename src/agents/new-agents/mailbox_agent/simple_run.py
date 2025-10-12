#!/usr/bin/env python3
"""
Simple runner for the Intelligent Mailbox Agent

This script provides a simple way to run the mailbox agent without complex setup.
"""

import os
import sys

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir))))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add the src directory to the Python path
src_dir = os.path.join(project_root, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

def main():
    """Main function"""
    print("🧠 Intelligent Mailbox Agent - Simple Runner")
    print("=" * 50)
    
    # Check for ASI_ONE_API_KEY
    if not os.getenv('ASI_ONE_API_KEY'):
        print("❌ ASI_ONE_API_KEY environment variable not set")
        print("Please set your API key: export ASI_ONE_API_KEY='your_key_here'")
        return
    
    print("✅ ASI_ONE_API_KEY is set")
    print("🚀 Starting mailbox agent...")
    print("💡 Press Ctrl+C to stop the agent")
    print("=" * 50)
    
    try:
        # Import and run the agent
        from mailbox_agent import agent
        print(f"📧 Mailbox Agent Address: {agent.address}")
        print("🤖 Agent is running...")
        agent.run()
    except KeyboardInterrupt:
        print("\n👋 Agent stopped by user")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the mailbox_agent directory")
        print("Current directory:", os.getcwd())
    except Exception as e:
        print(f"❌ Error running agent: {e}")

if __name__ == "__main__":
    main()
