#!/usr/bin/env python3
"""
Simple chat client to interact with the Gmail agent
"""

import asyncio
import sys
from uagents import Agent, Context
from uagents_core.contrib.protocols.chat import ChatMessage, TextContent

# Gmail agent address (from the logs)
GMAIL_AGENT_ADDRESS = "agent1qw6kgumlfqp9drr54qsfngdkz50vgues3u7sewg2fgketekqk8hz500ytg3"

# Create a simple chat client
chat_client = Agent(
    name="gmail_chat_client",
    seed="chat_client_seed_phrase_here"
)

@chat_client.on_message(ChatMessage)
async def handle_chat_response(ctx: Context, sender: str, msg: ChatMessage):
    """Handle responses from the Gmail agent"""
    if msg.content:
        if hasattr(msg.content, 'text'):
            print(f"\n📧 Gmail Agent: {msg.content.text}")
        else:
            print(f"\n📧 Gmail Agent: {msg.content}")
    else:
        print(f"\n📧 Gmail Agent: {msg}")

async def send_message_to_gmail_agent(message: str):
    """Send a message to the Gmail agent"""
    try:
        # Create a chat message
        chat_msg = ChatMessage(
            content=TextContent(text=message)
        )
        
        # Send to Gmail agent
        await chat_client.send(GMAIL_AGENT_ADDRESS, chat_msg)
        print(f"📤 Sent: {message}")
        
    except Exception as e:
        print(f"❌ Error sending message: {e}")

async def interactive_chat():
    """Interactive chat loop"""
    print("🤖 Gmail Agent Chat Client")
    print("=" * 50)
    print("Type your email requests in natural language!")
    print("Examples:")
    print("  - 'Send an email to john@example.com about the meeting'")
    print("  - 'Compose a thank you email to the team'")
    print("  - 'Email the client with the project update'")
    print("\nType 'quit' to exit")
    print("=" * 50)
    
    while True:
        try:
            # Get user input
            user_input = input("\n💬 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            # Send message to Gmail agent
            await send_message_to_gmail_agent(user_input)
            
            # Wait a bit for response
            await asyncio.sleep(1)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Starting Gmail Agent Chat Client...")
    print("Make sure the Gmail agent is running!")
    print()
    
    try:
        asyncio.run(interactive_chat())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
