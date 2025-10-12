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
import logging
from datetime import datetime
from typing import List, Dict

# Handle both relative and absolute imports
try:
    from asi_client import ASIOneClient
    from gmail_agent_helper import GmailAgentHelper
except ImportError:
    from .asi_client import ASIOneClient
    from .gmail_agent_helper import GmailAgentHelper


class AgenticChat:
    """Specialized chat interface for agentic models."""
    
    def __init__(self, model: str = "asi1-agentic", personality: str = None, log_file: str = None):
        """
        Initialize the agentic chat.
        
        Args:
            model: Agentic model to use (default: "asi1-agentic")
            personality: System prompt to define the AI's personality and behavior
            log_file: Optional path to log file for saving all responses
        """
        if model not in ASIOneClient.AGENTIC_MODELS:
            raise ValueError(f"Model '{model}' is not an agentic model. Available: {ASIOneClient.AGENTIC_MODELS}")
        
        self.model = model
        self.client = None
        self.conversation_history: List[Dict[str, str]] = []
        self.conversation_id = str(uuid.uuid4())
        self.total_tokens = 0
        
        # Set up logging
        self.log_file = log_file or f"agentic_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self._setup_logging()
        
        # Set the system prompt/personality
        self.system_prompt = personality or self._get_default_personality()
        
        # Add system prompt to conversation history if it's not already there
        if not self.conversation_history or self.conversation_history[0].get("role") != "system":
            self.conversation_history.insert(0, {"role": "system", "content": self.system_prompt})
    
    def _setup_logging(self):
        """Set up logging to capture all responses."""
        # Create logger
        self.logger = logging.getLogger(f"agentic_chat_{self.conversation_id[:8]}")
        self.logger.setLevel(logging.INFO)
        
        # Remove any existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create file handler
        file_handler = logging.FileHandler(self.log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
        
        # Log session start
        self.logger.info(f"=== AGENTIC CHAT SESSION STARTED ===")
        self.logger.info(f"Model: {self.model}")
        self.logger.info(f"Conversation ID: {self.conversation_id}")
        self.logger.info(f"Log file: {self.log_file}")
        self.logger.info("=" * 50)
    
    def _get_default_personality(self) -> str:
        """
        Get the default personality/system prompt for the agentic chat.
        
        Returns:
            Default system prompt string
        """
        return """You are an intelligent AI assistant with access to the Agentverse marketplace. 
You can autonomously discover, understand, and coordinate with specialized agents to help users accomplish their goals.

Your capabilities include:
- Discovering and collaborating with agents from the Agentverse marketplace
- Reading and interpreting each agent’s README or metadata to understand its capabilities, input/output formats, and expected behaviors
- Coordinating multi-agent workflows
- Maintaining context and session state across interactions
- Providing accurate, helpful, and contextually appropriate responses
- Communicating directly with deployed agents

When interacting with any agent:
1. Always read the agent’s README or manifest to understand its purpose and data requirements before sending a request.
2. Format your request exactly as the README specifies.
3. **Never execute actions that could affect users or others (e.g., sending emails, posting data, executing code) without first confirming all key details with the user — such as message content, subject lines, recipients, or parameters.**
4. Clearly present a summary of what you plan to do and wait for explicit user confirmation before proceeding.
5. If the README or user intent is unclear, ask clarifying questions before taking any action.

You should:
- Be helpful, friendly, and professional
- Explain your reasoning briefly when coordinating with agents
- Keep responses concise and clear, but provide detail when necessary
- Ask clarifying questions when user intent or agent requirements are ambiguous
- Maintain a consistent and approachable personality throughout the session
- Strive to leverage the agent ecosystem effectively to deliver the best results

Always aim to be the most capable, context-aware, and cooperative assistant possible while working within the Agentverse."""
        
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
    
    def is_email_request(self, user_message: str) -> bool:
        """Check if the user message is requesting to send an email."""
        return GmailAgentHelper.is_email_request(user_message)
    
    def enhance_email_request(self, user_message: str) -> str:
        """
        Enhance email requests with specific instructions for the Gmail agent.
        
        Args:
            user_message: The user's original message
            
        Returns:
            Enhanced message with Gmail agent instructions
        """
        if not self.is_email_request(user_message):
            return user_message
        
        # Extract email info to validate the request
        is_valid, email_info = GmailAgentHelper.extract_email_info(user_message)
        
        if is_valid and email_info:
            # Create a structured email request
            formatted_request = GmailAgentHelper.format_email_request(
                email_info["to"],
                email_info["subject"],
                email_info["content"]
            )
            
            enhanced_message = f"""I need to send an email using the Gmail Agent. Here's the structured request:

{formatted_request}

Please use the Gmail Agent at address {GmailAgentHelper.GMAIL_AGENT_ADDRESS} to send this email and confirm when it's sent."""
            
            return enhanced_message
        else:
            # If we can't parse the email info, provide guidance
            return f"""I understand you want to send an email. To help you with this, I need:

1. The recipient's email address
2. The subject (optional)
3. The message content

Please provide these details, and I'll use the Gmail Agent to send your email.

For example: "Send an email to john@example.com about the meeting. Tell him we need to reschedule for tomorrow." """
    
    def get_response(self, user_message: str) -> str:
        """
        Get a response from the agentic model.
        
        Args:
            user_message: The user's message
            
        Returns:
            The assistant's response
        """
        try:
            # Log user message
            self.logger.info(f"USER: {user_message}")
            
            # Check if this is an email request and enhance it
            enhanced_message = self.enhance_email_request(user_message)
            if enhanced_message != user_message:
                self.logger.info(f"ENHANCED EMAIL REQUEST: {enhanced_message}")
                print("📧 Detected email request - enhancing for Gmail agent...")
            
            print("🤖 Assistant: ", end="", flush=True)
            
            # Stream the response with conversation history (before adding current user message)
            assistant_message = self.client.stream_chat(
                enhanced_message, 
                model=self.model, 
                conversation_id=self.conversation_id,
                conversation_history=self.conversation_history
            )
            
            # Log the complete assistant response
            self.logger.info(f"ASSISTANT: {assistant_message}")
            
            # Add both user message and assistant response to history
            self.add_message("user", user_message)
            self.add_message("assistant", assistant_message)
            
            # Communication is working fine - no polling needed
            
            return assistant_message
            
        except Exception as e:
            error_msg = f"❌ Error getting response: {e}"
            print(error_msg)
            self.logger.error(f"ERROR: {error_msg}")
            return "Sorry, I encountered an error. Please try again."
    
    def show_session_info(self):
        """Show session information."""
        session_id = self.client.get_session_id(self.conversation_id)
        print(f"🆔 Conversation ID: {self.conversation_id}")
        print(f"🔗 Session ID: {session_id}")
        print(f"🤖 Model: {self.model}")
        print(f"📊 Messages: {len(self.conversation_history)}")
        print(f"🔢 Total tokens: {self.total_tokens}")
        print(f"📝 Log file: {self.log_file}")
    
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
  /personality, /persona - Show current personality/system prompt
  /log, /logfile     - Show log file location and open it
  /quit, /q, /exit   - Exit the chat

Agentic Capabilities:
  • Autonomous agent discovery from Agentverse marketplace
  • Real-time streaming responses
  • Session persistence across interactions
  • Direct agent communication
  • Multi-agent workflow coordination

📧 Gmail Agent Integration:
  • Gmail Agent Address: {GmailAgentHelper.GMAIL_AGENT_ADDRESS}
  • Send emails through natural language requests
  • Automatic email request detection and formatting
  • Direct communication with Gmail agent

Example requests:
  "Send an email to john@example.com about the meeting tomorrow"
  "Email my boss about the project status"
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
            # Preserve the system prompt when clearing conversation
            system_message = self.conversation_history[0] if self.conversation_history and self.conversation_history[0].get("role") == "system" else None
            self.conversation_history = []
            if system_message:
                self.conversation_history.append(system_message)
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
        
        elif command in ["/personality", "/persona"]:
            print("🎭 Current Personality/System Prompt:")
            print("-" * 40)
            print(self.system_prompt)
            return True
        
        elif command in ["/log", "/logfile"]:
            print(f"📝 Log file location: {self.log_file}")
            print(f"📁 Full path: {os.path.abspath(self.log_file)}")
            print("\nTo view the log file:")
            print(f"  cat {self.log_file}")
            print(f"  tail -f {self.log_file}  # Follow live updates")
            print(f"  less {self.log_file}     # Browse with pagination")
            return True
        
        elif command in ["/quit", "/q", "/exit"]:
            print("👋 Goodbye!")
            self.logger.info("=== AGENTIC CHAT SESSION ENDED ===")
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
        print(f"📝 Log file: {self.log_file}")
        
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
                    self.logger.info("=== AGENTIC CHAT SESSION ENDED (Keyboard Interrupt) ===")
                    break
                except EOFError:
                    print("\n\n👋 Goodbye!")
                    self.logger.info("=== AGENTIC CHAT SESSION ENDED (EOF) ===")
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
            self.logger.error(f"=== AGENTIC CHAT SESSION ENDED (Unexpected Error): {e} ===")


def main():
    """Main entry point."""
    # Check for API key
    if not os.getenv('ASI_ONE_API_KEY'):
        print("❌ ASI_ONE_API_KEY environment variable not set")
        print("Please set your API key: export ASI_ONE_API_KEY='your_key_here'")
        sys.exit(1)
    
    # Parse command line arguments for model selection, personality, and log file
    model = "asi1-agentic"  # Default - Change this to your preferred model
    personality = None
    log_file = None
    
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
    if len(sys.argv) > 3:
        log_file = sys.argv[3]
        print(f"📝 Using custom log file: {log_file}")
    
    # Start agentic chat
    chat = AgenticChat(model, personality, log_file)
    chat.run()


if __name__ == "__main__":
    main()
