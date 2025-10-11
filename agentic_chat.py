#!/usr/bin/env python3
"""
Quick launcher for ASI One Agentic Chat

This script provides a convenient way to start the agentic chat
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

# Import and run the agentic chat
try:
    from asi_integration.agentic_chat import AgenticChat
    from asi_integration.asi_client import ASIOneClient
    
    def main():
        """Main entry point."""
        # Check for API key
        if not os.getenv('ASI_ONE_API_KEY'):
            print("❌ ASI_ONE_API_KEY environment variable not set")
            print("Please set your API key: export ASI_ONE_API_KEY='your_key_here'")
            sys.exit(1)
        
        # Parse command line arguments for model selection and personality
        model = "asi1-agentic"  # Default - Change this to your preferred model
        
        # Quick personality switcher - uncomment one of these lines to set default:
        # personality = "personalities/ridiculous_pirate.txt"    # 🏴‍☠️ Pirate
        # personality = "personalities/formal_butler.txt"        # 🎩 Butler  
        # personality = "personalities/hyperactive_puppy.txt"    # 🐕 Puppy
        # personality = "personalities/friendly_assistant.txt"   # 😊 Friendly
        # personality = "personalities/professional_expert.txt"  # 👔 Professional
        # personality = "personalities/creative_collaborator.txt" # 🎨 Creative
        personality = None  # Default: uses built-in professional personality
        
        if len(sys.argv) > 1:
            model = sys.argv[1]
            if model not in ASIOneClient.AGENTIC_MODELS:
                print(f"❌ Invalid agentic model: {model}")
                print(f"Available models: {ASIOneClient.AGENTIC_MODELS}")
                sys.exit(1)
        
        # Check for custom personality file
        if len(sys.argv) > 2:
            personality_file = sys.argv[2]
            try:
                with open(personality_file, 'r') as f:
                    personality = f.read().strip()
                print(f"📝 Loaded custom personality from: {personality_file}")
            except FileNotFoundError:
                print(f"❌ Personality file not found: {personality_file}")
                sys.exit(1)
            except Exception as e:
                print(f"❌ Error reading personality file: {e}")
                sys.exit(1)
        
        # Check for custom log file
        log_file = None
        if len(sys.argv) > 3:
            log_file = sys.argv[3]
            print(f"📝 Using custom log file: {log_file}")
        
        # Start agentic chat
        chat = AgenticChat(model, personality, log_file)
        chat.run()
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("Make sure you're running this from the project root directory.")
    print("Alternative: python src/asi_integration/agentic_chat.py")
    sys.exit(1)
