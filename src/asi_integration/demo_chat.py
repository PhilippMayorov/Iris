#!/usr/bin/env python3
"""
Demo script showing the interactive chat functionality

This script demonstrates the key features of the interactive chat
without requiring user input.
"""

import os
import sys

# Handle both relative and absolute imports
try:
    from interactive_chat import InteractiveChat
except ImportError:
    from .interactive_chat import InteractiveChat


def demo_chat():
    """Demonstrate the interactive chat features."""
    print("🤖 ASI One Interactive Chat Demo")
    print("=" * 50)
    
    # Check for API key
    if not os.getenv('ASI_ONE_API_KEY'):
        print("❌ ASI_ONE_API_KEY environment variable not set")
        print("Please set your API key to run this demo")
        return
    
    # Initialize chat
    chat = InteractiveChat()
    
    if not chat.initialize_client():
        return
    
    print("\n📝 Demo Conversation:")
    print("-" * 30)
    
    # Demo conversation
    demo_messages = [
        "Hello! Can you tell me a short joke?",
        "That's funny! Can you explain what artificial intelligence is in simple terms?",
        "Thanks! What are some practical applications of AI?"
    ]
    
    for i, message in enumerate(demo_messages, 1):
        print(f"\n{i}. 👤 You: {message}")
        print("🤖 Assistant: ", end="", flush=True)
        
        response = chat.get_response(message)
        print(response)
    
    # Show conversation features
    print("\n" + "=" * 50)
    print("📊 Demo Features:")
    
    # Show history
    chat.show_history()
    
    # Show token usage
    chat.show_tokens()
    
    # Save conversation
    chat.save_conversation("demo_conversation.json")
    
    print("\n✅ Demo completed!")
    print("💡 Try running the full interactive chat with: python chat.py")


if __name__ == "__main__":
    demo_chat()
