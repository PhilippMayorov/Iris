#!/usr/bin/env python3
"""
Agentic Chat with ASI One API

A specialized chat interface for ASI One's agentic models that can work with
the Agentverse marketplace. This script demonstrates the full capabilities
of agentic models including streaming, session management, and async polling.
"""

import os
import sys
import json
import uuid
import time
from typing import List, Dict

# Handle both relative and absolute imports
try:
    from asi_client import ASIOneClient
except ImportError:
    from .asi_client import ASIOneClient


class AgenticChat:
    """Specialized chat interface for agentic models."""
    
    def __init__(self, model: str = "asi1-agentic", personality: str = None):
        """
        Initialize the agentic chat.
        
        Args:
            model: Agentic model to use (default: "asi1-agentic")
            personality: System prompt to define the AI's personality and behavior
        """
        if model not in ASIOneClient.AGENTIC_MODELS:
            raise ValueError(f"Model '{model}' is not an agentic model. Available: {ASIOneClient.AGENTIC_MODELS}")
        
        self.model = model
        self.client = None
        self.conversation_history: List[Dict[str, str]] = []
        self.conversation_id = str(uuid.uuid4())
        self.total_tokens = 0
        
        # Set the system prompt/personality
        self.system_prompt = personality or self._get_default_personality()
        
        # Add system prompt to conversation history if it's not already there
        if not self.conversation_history or self.conversation_history[0].get("role") != "system":
            self.conversation_history.insert(0, {"role": "system", "content": self.system_prompt})
        
    def initialize_client(self) -> bool:
        """Initialize the ASI One client."""
        try:
            self.client = ASIOneClient()
            print("✅ Connected to ASI One API")
            return True
        except ValueError as e:
            print(f"❌ Failed to initialize client: {e}")
            print("Please set your ASI_ONE_API_KEY environment variable")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
    
    def add_message(self, role: str, content: str):
        """Add a message to the conversation history."""
        self.conversation_history.append({"role": role, "content": content})
    
    def get_response(self, user_message: str) -> str:
        """
        Get a response from the agentic model.
        
        Args:
            user_message: The user's message
            
        Returns:
            The assistant's response
        """
        try:
            print("🤖 Assistant: ", end="", flush=True)
            
            # Stream the response with conversation history (before adding current user message)
            assistant_message = self.client.stream_chat(
                user_message, 
                model=self.model, 
                conversation_id=self.conversation_id,
                conversation_history=self.conversation_history
            )
            
            # Add both user message and assistant response to history
            self.add_message("user", user_message)
            self.add_message("assistant", assistant_message)
            
            # Check for async agent responses
            if "I've sent the message" in assistant_message or "working on" in assistant_message.lower():
                print("\n🔄 Agent is working on your request...")
                follow_up = self.client.poll_for_async_reply(
                    self.conversation_id, 
                    self.conversation_history.copy(),
                    model=self.model
                )
                if follow_up:
                    print(f"\n🤖 Agent completed: {follow_up}")
                    self.add_message("assistant", follow_up)
                    assistant_message += f"\n\n[Agent completed]: {follow_up}"
            
            return assistant_message
            
        except Exception as e:
            print(f"❌ Error getting response: {e}")
            return "Sorry, I encountered an error. Please try again."
    
    def show_session_info(self):
        """Show session information."""
        session_id = self.client.get_session_id(self.conversation_id)
        print(f"🆔 Conversation ID: {self.conversation_id}")
        print(f"🔗 Session ID: {session_id}")
        print(f"🤖 Model: {self.model}")
        print(f"📊 Messages: {len(self.conversation_history)}")
        print(f"🔢 Total tokens: {self.total_tokens}")
    
    def show_help(self):
        """Show help information."""
        help_text = f"""
🤖 ASI One Agentic Chat Help

You're using: {self.model}
This model can autonomously discover and coordinate with agents from the Agentverse marketplace.

Commands:
  /help, /h          - Show this help message
  /session, /sid     - Show session information
  /clear, /c         - Clear conversation and start new session
  /save [filename]   - Save conversation to file
  /load <filename>   - Load conversation from file
  /history, /hist    - Show conversation history
  /models            - Show available agentic models
  /quit, /q, /exit   - Exit the chat

Agentic Capabilities:
  • Autonomous agent discovery from Agentverse marketplace
  • Real-time streaming responses
  • Session persistence across interactions
  • Asynchronous agent task processing
  • Multi-agent workflow coordination

Example requests:
  "Help me book a restaurant for dinner tonight"
  "Find me a flight from NYC to LA next week"
  "Create a meeting agenda for our team standup"
  "Research the latest AI trends and summarize them"

Just type your message to start working with agents!
        """
        print(help_text)
    
    def process_command(self, user_input: str) -> bool:
        """Process special commands."""
        command = user_input.strip().lower()
        
        if command in ["/help", "/h"]:
            self.show_help()
            return True
        
        elif command in ["/session", "/sid"]:
            self.show_session_info()
            return True
        
        elif command in ["/clear", "/c"]:
            self.conversation_history = []
            self.conversation_id = str(uuid.uuid4())
            print("🗑️  Conversation cleared, new session started")
            print(f"🆔 New conversation ID: {self.conversation_id}")
            return True
        
        elif command == "/models":
            print("🤖 Available Agentic Models:")
            for model in ASIOneClient.AGENTIC_MODELS:
                marker = " (current)" if model == self.model else ""
                print(f"  • {model}{marker}")
            return True
        
        elif command in ["/quit", "/q", "/exit"]:
            print("👋 Goodbye!")
            return True
        
        return False
    
    def run(self):
        """Run the agentic chat."""
        print("🤖 ASI One Agentic Chat")
        print("=" * 50)
        print(f"Model: {self.model}")
        print("🔗 Agentverse marketplace integration enabled")
        print("📡 Real-time streaming enabled")
        print(f"🆔 Conversation ID: {self.conversation_id}")
        
        # Initialize client
        if not self.initialize_client():
            return
        
        # Show help
        self.show_help()
        
        print("\n💬 Start chatting with agents! (Type /help for commands)")
        print("-" * 50)
        
        try:
            while True:
                # Get user input
                try:
                    user_input = input("\n👤 You: ").strip()
                except KeyboardInterrupt:
                    print("\n\n👋 Goodbye!")
                    break
                except EOFError:
                    print("\n\n👋 Goodbye!")
                    break
                
                # Skip empty input
                if not user_input:
                    continue
                
                # Process commands
                if self.process_command(user_input):
                    continue
                
                # Get response from agentic model
                response = self.get_response(user_input)
                
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            print("Chat session ended.")


def main():
    """Main entry point."""
    # Check for API key
    if not os.getenv('ASI_ONE_API_KEY'):
        print("❌ ASI_ONE_API_KEY environment variable not set")
        print("Please set your API key: export ASI_ONE_API_KEY='your_key_here'")
        sys.exit(1)
    
    # Parse command line arguments for model selection
    model = "asi1-agentic"  # Default - Change this to your preferred model
    if len(sys.argv) > 1:
        model = sys.argv[1]
        if model not in ASIOneClient.AGENTIC_MODELS:
            print(f"❌ Invalid agentic model: {model}")
            print(f"Available models: {ASIOneClient.AGENTIC_MODELS}")
            sys.exit(1)
    
    # Start agentic chat
    chat = AgenticChat(model)
    chat.run()


if __name__ == "__main__":
    main()
