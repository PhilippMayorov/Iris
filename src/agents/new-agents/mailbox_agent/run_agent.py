#!/usr/bin/env python3
"""
Run the Intelligent Mailbox Agent

This script starts the mailbox agent with all intelligent chat capabilities.
"""

import os
import sys

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir))))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import and run the agent
from src.agents.new_agents.mailbox_agent.mailbox_agent import agent

if __name__ == "__main__":
    print("🚀 Starting Intelligent Mailbox Agent...")
    agent.run()
