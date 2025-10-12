#!/usr/bin/env python3
"""
Quick launcher for ASI One Interactive Chat

This script provides a convenient way to start the interactive chat
from the project root directory.
"""

import sys
import os

# Get the directory containing this script
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, 'src')

# Add the src directory to the Python path
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Import and run the interactive chat
try:
    from asi_integration.interactive_chat import InteractiveChat
    
    def main():
        """Main entry point."""
        # Check for API key
        if not os.getenv('ASI_ONE_API_KEY'):
            print("❌ ASI_ONE_API_KEY environment variable not set")
            print("Please set your API key: export ASI_ONE_API_KEY='your_key_here'")
            sys.exit(1)
        
        # Start interactive chat
        chat = InteractiveChat()
        chat.run()
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("Make sure you're running this from the project root directory.")
    print("Alternative: python src/asi_integration/interactive_chat.py")
    sys.exit(1)
