#!/usr/bin/env python3
"""
Interactive Chat with ASI One API

A command-line chat interface for having conversations with the ASI One API.
Supports multi-turn conversations with conversation history.
"""

import os
import sys
import json
import uuid
from typing import List, Dict

# Handle both relative and absolute imports
try:
    from asi_client import ASIOneClient
except ImportError:
    from .asi_client import ASIOneClient


class InteractiveChat:
    """Interactive chat interface for ASI One API with support for agentic models."""
    
    def __init__(self, model: str = "asi1-mini"):
        """
        Initialize the interactive chat.
        
        Args:
            model: Model to use for the conversation
        """
        self.model = model
        self.client = None
        self.conversation_history: List[Dict[str, str]] = []
        self.total_tokens = 0
        self.conversation_id = str(uuid.uuid4())
        self.streaming_enabled = True
        
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
        Get a response from the API for the given user message.
        
        Args:
            user_message: The user's message
            
        Returns:
            The assistant's response
        """
        try:
            # Add user message to history
            self.add_message("user", user_message)
            
            # Check if we need conversation_id for agentic models
            conversation_id = self.conversation_id if self.client.is_agentic_model(self.model) else None
            
            # Get response from API
            if self.streaming_enabled and self.client.is_agentic_model(self.model):
                # Use streaming for agentic models
                print("🤖 Assistant: ", end="", flush=True)
                assistant_message = self.client.stream_chat(
                    user_message, 
                    model=self.model, 
                    conversation_id=conversation_id
                )
            else:
                # Regular response
                response = self.client.chat_completion(
                    messages=self.conversation_history.copy(),
                    model=self.model,
                    conversation_id=conversation_id
                )
                
                # Extract assistant response
                assistant_message = response["choices"][0]["message"]["content"]
                
                # Track token usage
                if "usage" in response:
                    usage = response["usage"]
                    self.total_tokens += usage["total_tokens"]
                    print(f"📊 Tokens used this turn: {usage['total_tokens']} (total: {self.total_tokens})")
            
            # Add assistant response to history
            self.add_message("assistant", assistant_message)
            
            # Check for async agent responses
            if self.client.is_agentic_model(self.model) and "I've sent the message" in assistant_message:
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
    
    def clear_conversation(self):
        """Clear the conversation history and create new conversation ID."""
        self.conversation_history = []
        self.total_tokens = 0
        self.conversation_id = str(uuid.uuid4())
        print("🗑️  Conversation history cleared")
        print(f"🆔 New conversation ID: {self.conversation_id}")
    
    def save_conversation(self, filename: str = None):
        """Save the conversation to a file."""
        if not filename:
            filename = f"asi_chat_{len(self.conversation_history)}_messages.json"
        
        conversation_data = {
            "model": self.model,
            "conversation_id": self.conversation_id,
            "total_tokens": self.total_tokens,
            "is_agentic": self.client.is_agentic_model(self.model) if self.client else False,
            "streaming_enabled": self.streaming_enabled,
            "messages": self.conversation_history
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(conversation_data, f, indent=2)
            print(f"💾 Conversation saved to {filename}")
        except Exception as e:
            print(f"❌ Error saving conversation: {e}")
    
    def load_conversation(self, filename: str):
        """Load a conversation from a file."""
        try:
            with open(filename, 'r') as f:
                conversation_data = json.load(f)
            
            self.conversation_history = conversation_data.get("messages", [])
            self.total_tokens = conversation_data.get("total_tokens", 0)
            self.model = conversation_data.get("model", self.model)
            self.conversation_id = conversation_data.get("conversation_id", str(uuid.uuid4()))
            self.streaming_enabled = conversation_data.get("streaming_enabled", True)
            
            print(f"📂 Conversation loaded from {filename}")
            print(f"   Messages: {len(self.conversation_history)}")
            print(f"   Total tokens: {self.total_tokens}")
            print(f"   Model: {self.model}")
            print(f"   Conversation ID: {self.conversation_id}")
            print(f"   Streaming: {'enabled' if self.streaming_enabled else 'disabled'}")
            
        except Exception as e:
            print(f"❌ Error loading conversation: {e}")
    
    def show_help(self):
        """Show help information."""
        help_text = f"""
🤖 ASI One Interactive Chat Help

Commands:
  /help, /h          - Show this help message
  /clear, /c         - Clear conversation history
  /save [filename]   - Save conversation to file
  /load <filename>   - Load conversation from file
  /history, /hist    - Show conversation history
  /tokens, /t        - Show token usage
  /model [name]      - Change model (current: {self.model})
  /stream, /s        - Toggle streaming (current: {'on' if self.streaming_enabled else 'off'})
  /session, /sid     - Show session information
  /models            - List available models
  /quit, /q, /exit   - Exit the chat

Agentic Models (with Agentverse support):
  asi1-agentic       - General orchestration & prototyping
  asi1-fast-agentic  - Real-time agent coordination (recommended)
  asi1-extended-agentic - Complex multi-stage workflows

Regular Models:
  asi1-mini          - Standard chat model

Just type your message to chat with the AI!
        """
        print(help_text)
    
    def show_history(self):
        """Show the conversation history."""
        if not self.conversation_history:
            print("📝 No conversation history")
            return
        
        print(f"\n📝 Conversation History ({len(self.conversation_history)} messages):")
        print("-" * 50)
        
        for i, message in enumerate(self.conversation_history, 1):
            role = message["role"]
            content = message["content"]
            
            if role == "user":
                print(f"{i}. 👤 You: {content}")
            else:
                print(f"{i}. 🤖 Assistant: {content}")
        
        print("-" * 50)
    
    def show_tokens(self):
        """Show token usage information."""
        print(f"📊 Token Usage:")
        print(f"   Total tokens used: {self.total_tokens}")
        print(f"   Messages in history: {len(self.conversation_history)}")
        if len(self.conversation_history) > 0:
            avg_tokens = self.total_tokens / len(self.conversation_history)
            print(f"   Average tokens per message: {avg_tokens:.1f}")
    
    def change_model(self, new_model: str):
        """Change the model being used."""
        if self.client and new_model not in (self.client.REGULAR_MODELS + self.client.AGENTIC_MODELS):
            print(f"❌ Unknown model: {new_model}")
            print(f"Available models: {self.client.REGULAR_MODELS + self.client.AGENTIC_MODELS}")
            return
        
        self.model = new_model
        print(f"🔄 Model changed to: {self.model}")
        
        # Create new conversation ID for agentic models
        if self.client and self.client.is_agentic_model(self.model):
            self.conversation_id = str(uuid.uuid4())
            print(f"🆔 New conversation ID: {self.conversation_id}")
    
    def toggle_streaming(self):
        """Toggle streaming mode."""
        self.streaming_enabled = not self.streaming_enabled
        print(f"🔄 Streaming {'enabled' if self.streaming_enabled else 'disabled'}")
    
    def show_session_info(self):
        """Show session information."""
        print(f"🆔 Conversation ID: {self.conversation_id}")
        print(f"🤖 Model: {self.model}")
        print(f"📡 Streaming: {'enabled' if self.streaming_enabled else 'disabled'}")
        if self.client:
            print(f"🔗 Agentic: {'Yes' if self.client.is_agentic_model(self.model) else 'No'}")
            print(f"📊 Active sessions: {len(self.client.session_map)}")
    
    def show_models(self):
        """Show available models."""
        if not self.client:
            print("❌ Client not initialized")
            return
        
        print("🤖 Available Models:")
        print("\nRegular Models:")
        for model in self.client.REGULAR_MODELS:
            marker = " (current)" if model == self.model else ""
            print(f"  • {model}{marker}")
        
        print("\nAgentic Models (with Agentverse support):")
        for model in self.client.AGENTIC_MODELS:
            marker = " (current)" if model == self.model else ""
            print(f"  • {model}{marker}")
        
        print(f"\nCurrent model: {self.model}")
        print(f"Agentic: {'Yes' if self.client.is_agentic_model(self.model) else 'No'}")
    
    def process_command(self, user_input: str) -> bool:
        """
        Process special commands.
        
        Args:
            user_input: The user's input
            
        Returns:
            True if the input was a command (and should not be sent to API)
        """
        command = user_input.strip().lower()
        
        if command in ["/help", "/h"]:
            self.show_help()
            return True
        
        elif command in ["/clear", "/c"]:
            self.clear_conversation()
            return True
        
        elif command.startswith("/save"):
            parts = user_input.split()
            filename = parts[1] if len(parts) > 1 else None
            self.save_conversation(filename)
            return True
        
        elif command.startswith("/load"):
            parts = user_input.split()
            if len(parts) < 2:
                print("❌ Please specify a filename: /load <filename>")
                return True
            self.load_conversation(parts[1])
            return True
        
        elif command in ["/history", "/hist"]:
            self.show_history()
            return True
        
        elif command in ["/tokens", "/t"]:
            self.show_tokens()
            return True
        
        elif command.startswith("/model"):
            parts = user_input.split()
            if len(parts) < 2:
                print(f"❌ Current model: {self.model}")
                print("Usage: /model <model_name>")
                return True
            self.change_model(parts[1])
            return True
        
        elif command in ["/stream", "/s"]:
            self.toggle_streaming()
            return True
        
        elif command in ["/session", "/sid"]:
            self.show_session_info()
            return True
        
        elif command == "/models":
            self.show_models()
            return True
        
        elif command in ["/quit", "/q", "/exit"]:
            print("👋 Goodbye!")
            return True
        
        return False
    
    def run(self):
        """Run the interactive chat."""
        print("🤖 ASI One Interactive Chat")
        print("=" * 40)
        
        # Initialize client
        if not self.initialize_client():
            return
        
        # Show initial information
        print(f"🤖 Model: {self.model}")
        print(f"🆔 Conversation ID: {self.conversation_id}")
        if self.client.is_agentic_model(self.model):
            print("🔗 Agentic mode: Enabled (Agentverse support)")
            print("📡 Streaming: Enabled by default for agentic models")
        else:
            print("🔗 Agentic mode: Disabled")
            print(f"📡 Streaming: {'Enabled' if self.streaming_enabled else 'Disabled'}")
        
        # Show initial help
        self.show_help()
        
        print("\n💬 Start chatting! (Type /help for commands)")
        print("-" * 40)
        
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
                
                # Get response from API
                print("🤖 Assistant: ", end="", flush=True)
                response = self.get_response(user_input)
                print(response)
                
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
    
    # Start interactive chat
    chat = InteractiveChat()
    chat.run()


if __name__ == "__main__":
    main()
