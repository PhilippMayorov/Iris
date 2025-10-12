#!/usr/bin/env python3
"""
Fixed Intelligent Mailbox Agent - ASI One Interactive Chat with Intelligent Model Selection

This agent provides a mailbox endpoint that incorporates the intelligent chat functionality
from chat.py, including automatic model selection and agent routing capabilities.
"""

import os
import sys
import json
import uuid
import signal
import threading
import time
from datetime import datetime
from typing import Optional, Dict, List
from enum import Enum

# Add the src directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir))))
src_dir = os.path.join(project_root, 'src')

if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

try:
    from uagents import Agent, Context, Model, Protocol
    from uagents.experimental.quota import QuotaProtocol, RateLimit
    from uagents_core.models import ErrorMessage
    from uagents_core.contrib.protocols.chat import (
        AgentContent,
        ChatAcknowledgement,
        ChatMessage,
        EndSessionContent,
        TextContent,
        chat_protocol_spec,
    )
    from asi_integration.asi_client import ASIOneClient
    from asi_integration.interactive_chat import InteractiveChat
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("Make sure you're running this from the project root directory.")
    print("Current working directory:", os.getcwd())
    print("Script directory:", script_dir)
    print("Project root:", project_root)
    print("Src directory:", src_dir)
    sys.exit(1)

# Configuration
AGENT_NAME = os.getenv("AGENT_NAME", "Intelligent Mailbox Agent")
AGENT_SEED = os.getenv("AGENT_SEED", "intelligent_mailbox_agent_seed_phrase_here")
PORT = int(os.getenv("PORT", "8001"))

# ASI:One Configuration
ASI_ONE_API_KEY = os.getenv("ASI_ONE_API_KEY")
ASI_ONE_BASE_URL = "https://api.asi1.ai/v1"

# Global OAuth server instance
oauth_server = None
oauth_server_thread = None

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\n🛑 Received signal {signum} - shutting down gracefully...")
    print("👋 Intelligent Mailbox Agent shutdown complete")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

# Initialize the agent
agent = Agent(
    name=AGENT_NAME,
    seed=AGENT_SEED,
    port=PORT,
    mailbox=True,
    publish_agent_details=True,
)

# Initialize ASI:One client
asi_one_client = None
if ASI_ONE_API_KEY:
    try:
        asi_one_client = ASIOneClient()
        print("✅ ASI:One client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize ASI:One client: {e}")
        asi_one_client = None
else:
    print("⚠️ ASI_ONE_API_KEY not found - ASI:One features will be disabled")

# Models for communication
class ChatRequest(Model):
    """Request for chat interaction"""
    message: str
    conversation_id: Optional[str] = None
    model: Optional[str] = None

class ChatResponse(Model):
    """Response from chat interaction"""
    response: str
    conversation_id: str
    model_used: str
    agent_routing: Optional[Dict] = None
    complexity_analysis: Optional[Dict] = None
    success: bool = True
    error_message: Optional[str] = None
    timestamp: str

class HealthCheck(Model):
    """Health check request"""
    pass

class HealthResponse(Model):
    """Health check response"""
    status: str
    agent_address: str
    timestamp: str

class IntelligentChatHandler:
    """Enhanced chat handler with intelligent model selection and agent routing"""
    
    def __init__(self):
        self.asi_client = asi_one_client
        self.conversation_histories: Dict[str, List[Dict[str, str]]] = {}
        
        # Agent configuration for routing
        self.agent_config = {
            "email": {
                "keywords": ["email", "send email", "mail", "message", "send", "friend", "someone"],
                "agent_address": "better-gmail-agent",  # This should be the actual Gmail agent address
                "description": "Email sending and management tasks",
                "examples": ["send an email", "email my friend", "send a message"]
            },
            "calendar": {
                "keywords": ["calendar", "schedule", "meeting", "appointment", "book", "reserve"],
                "agent_address": "calendar-agent",  # Placeholder
                "description": "Calendar and scheduling tasks",
                "examples": ["schedule a meeting", "book an appointment"]
            },
            "search": {
                "keywords": ["search", "find", "look up", "google", "web search"],
                "agent_address": "search-agent",  # Placeholder
                "description": "Web search and information retrieval",
                "examples": ["search for restaurants", "find information about"]
            },
            "file": {
                "keywords": ["file", "document", "download", "upload", "create", "save"],
                "agent_address": "file-agent",  # Placeholder
                "description": "File operations and document management",
                "examples": ["create a document", "download a file"]
            }
        }
    
    def analyze_agent_routing(self, user_message: str) -> dict:
        """Analyze which agent should handle the request"""
        print("🔍 Analyzing agent routing...")
        
        # Enhanced keyword-based routing with better matching
        message_lower = user_message.lower()
        
        # Check each agent category
        best_match = None
        best_score = 0
        
        for category, config in self.agent_config.items():
            score = 0
            keywords = config["keywords"]
            
            # Count keyword matches
            for keyword in keywords:
                if keyword in message_lower:
                    score += 1
            
            # Special scoring for email-related requests
            if category == "email":
                email_phrases = ["send", "email", "friend", "someone", "message", "mail"]
                email_score = sum(1 for phrase in email_phrases if phrase in message_lower)
                if email_score >= 2:  # Multiple email-related words
                    score += 3
            
            if score > best_score:
                best_score = score
                best_match = category
        
        if best_match and best_score > 0:
            confidence = min(best_score / 5.0, 1.0)  # Normalize to 0-1
            return {
                "matched_agent": best_match,
                "confidence": confidence,
                "reason": f"Request matches {best_match} keywords (score: {best_score})",
                "suggested_model": "asi1-fast-agentic",
                "agent_address": self.agent_config[best_match]["agent_address"]
            }
        
        return {
            "matched_agent": None,
            "confidence": 0.0,
            "reason": "No specific agent routing needed",
            "suggested_model": "asi1-mini",
            "agent_address": None
        }
    
    def analyze_request_complexity(self, user_message: str) -> dict:
        """Analyze if the request needs agentic capabilities"""
        print("🔍 Analyzing request complexity...")
        
        # Enhanced keyword-based analysis
        agentic_keywords = [
            "send", "email", "emails", "search", "find", "download", "create", "schedule", 
            "book", "reserve", "order", "buy", "purchase", "call", "message", "messages",
            "remind", "alert", "notify", "update", "sync", "connect", "integrate",
            "automate", "workflow", "task", "todo", "calendar", "meeting", "meetings",
            "reservation", "booking", "purchase", "payment", "api", "webhook", "friend",
            "someone", "help me", "can you", "please", "would you"
        ]
        
        message_lower = user_message.lower()
        agentic_score = sum(1 for keyword in agentic_keywords if keyword in message_lower)
        
        # Special scoring for action-oriented phrases
        action_phrases = ["send an email", "email my friend", "help me", "can you", "would you"]
        action_score = sum(1 for phrase in action_phrases if phrase in message_lower)
        
        total_score = agentic_score + (action_score * 2)  # Weight action phrases higher
        
        if total_score >= 2:
            needs_agentic = True
            confidence = min(total_score / 8.0, 1.0)
            suggested_model = "asi1-fast-agentic"
            reason = f"Request contains {total_score} agentic indicators"
        else:
            needs_agentic = False
            confidence = 1.0 - (total_score / 8.0)
            suggested_model = "asi1-mini"
            reason = f"Request appears to be general conversation (score: {total_score})"
        
        return {
            "needs_agentic": needs_agentic,
            "confidence": confidence,
            "reason": reason,
            "suggested_model": suggested_model
        }
    
    def get_intelligent_response(self, user_message: str, conversation_id: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> dict:
        """Get an intelligent response with model selection and agent routing"""
        
        # Analyze agent routing
        routing_result = self.analyze_agent_routing(user_message)
        print(f"🔍 Routing result: {routing_result}")
        
        # Analyze request complexity
        complexity_result = self.analyze_request_complexity(user_message)
        print(f"🔍 Analysis result: {complexity_result}")
        
        # Determine final model
        if routing_result["matched_agent"]:
            final_model = routing_result["suggested_model"]
        else:
            final_model = complexity_result["suggested_model"]
        
        print(f"💬 Request suitable for {'agentic' if complexity_result['needs_agentic'] else 'regular'} chat (confidence: {complexity_result['confidence']:.1%})")
        print(f"📝 Reason: {complexity_result['reason']}")
        
        # Generate response
        if self.asi_client:
            try:
                response = self.asi_client.simple_chat(
                    user_message,
                    model=final_model,
                    conversation_id=conversation_id,
                    conversation_history=conversation_history
                )
                
                return {
                    "response": response,
                    "conversation_id": conversation_id,
                    "model_used": final_model,
                    "agent_routing": routing_result,
                    "complexity_analysis": complexity_result,
                    "success": True,
                    "error_message": None,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                print(f"❌ Error getting intelligent response: {e}")
                # Fallback to simple response
                return self._get_fallback_response(user_message, conversation_id, routing_result, complexity_result)
        else:
            # No ASI client available, use fallback
            return self._get_fallback_response(user_message, conversation_id, routing_result, complexity_result)
    
    def _get_fallback_response(self, user_message: str, conversation_id: str, routing_result: dict, complexity_result: dict) -> dict:
        """Generate a fallback response when ASI:One is not available"""
        
        # Simple rule-based responses
        message_lower = user_message.lower()
        
        if "email" in message_lower or "send" in message_lower:
            response = "I'd be happy to help you send an email! However, I need to connect to the Gmail agent to do this. Please make sure the Gmail agent is running and accessible."
        elif "hello" in message_lower or "hi" in message_lower:
            response = "Hello! I'm the Intelligent Mailbox Agent. I can help you with various tasks including sending emails, managing your calendar, and more. What would you like me to help you with?"
        elif "help" in message_lower:
            response = "I can help you with:\n- Sending emails\n- Managing your calendar\n- Searching for information\n- File operations\n- General conversations\n\nWhat would you like me to do?"
        else:
            response = f"I understand you're asking: '{user_message}'. I'm currently running in fallback mode without ASI:One integration. For full functionality, please ensure your ASI_ONE_API_KEY is set correctly."
        
        return {
            "response": response,
            "conversation_id": conversation_id,
            "model_used": "fallback",
            "agent_routing": routing_result,
            "complexity_analysis": complexity_result,
            "success": True,
            "error_message": "ASI:One not available, using fallback response",
            "timestamp": datetime.utcnow().isoformat()
        }

# Initialize the intelligent chat handler
intelligent_handler = IntelligentChatHandler()

# Chat protocol
chat_protocol = Protocol("chat", chat_protocol_spec)

@chat_protocol.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handle incoming chat messages"""
    
    # Extract text content
    text = ""
    for content in msg.content:
        if isinstance(content, TextContent):
            text += content.text + " "
    
    text = text.strip()
    if not text:
        await ctx.send(sender, ChatAcknowledgement())
        return
    
    print(f"💬 Received message from {sender}: {text}")
    
    # Get or create conversation history
    conversation_history = intelligent_handler.conversation_histories.get(sender, [])
    
    # Add user message to history
    conversation_history.append({"role": "user", "content": text})
    
    # Generate consistent conversation ID
    consistent_conversation_id = f"direct_chat_{sender.replace(':', '_').replace('/', '_')}"
    
    # Get intelligent response
    result = intelligent_handler.get_intelligent_response(
        user_message=text,
        conversation_id=consistent_conversation_id,
        conversation_history=conversation_history
    )
    
    # Add assistant response to history
    conversation_history.append({"role": "assistant", "content": result["response"]})
    intelligent_handler.conversation_histories[sender] = conversation_history
    
    # Send response
    response_content = [TextContent(type="text", text=result["response"])]
    response_msg = ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid.uuid4(),
        content=response_content
    )
    
    await ctx.send(sender, response_msg)
    await ctx.send(sender, ChatAcknowledgement())

# Custom protocol for structured requests
custom_protocol = Protocol("custom")

@custom_protocol.on_message(ChatRequest)
async def handle_chat_request(ctx: Context, sender: str, msg: ChatRequest):
    """Handle structured chat requests"""
    
    print(f"💬 Received structured request from {sender}: {msg.message}")
    
    # Get or create conversation history
    conversation_history = intelligent_handler.conversation_histories.get(sender, [])
    
    # Add user message to history
    conversation_history.append({"role": "user", "content": msg.message})
    
    # Use provided conversation ID or generate one
    conversation_id = msg.conversation_id or f"structured_chat_{sender.replace(':', '_').replace('/', '_')}"
    
    # Get intelligent response
    result = intelligent_handler.get_intelligent_response(
        user_message=msg.message,
        conversation_id=conversation_id,
        conversation_history=conversation_history
    )
    
    # Add assistant response to history
    conversation_history.append({"role": "assistant", "content": result["response"]})
    intelligent_handler.conversation_histories[sender] = conversation_history
    
    # Send structured response
    response = ChatResponse(**result)
    await ctx.send(sender, response)

@custom_protocol.on_message(HealthCheck)
async def handle_health_check(ctx: Context, sender: str, msg: HealthCheck):
    """Handle health check requests"""
    
    response = HealthResponse(
        status="healthy",
        agent_address=agent.address,
        timestamp=datetime.utcnow().isoformat()
    )
    
    await ctx.send(sender, response)

# Include protocols
agent.include(chat_protocol)
agent.include(custom_protocol)

if __name__ == "__main__":
    print("🧠 Intelligent Mailbox Agent - Fixed Version")
    print("=" * 60)
    print(f"📧 Agent Address: {agent.address}")
    print(f"🔗 Agent Name: {AGENT_NAME}")
    print(f"🌐 Port: {PORT}")
    
    if asi_one_client:
        print("✅ ASI:One integration enabled")
    else:
        print("⚠️ ASI:One integration disabled (fallback mode)")
    
    print("=" * 60)
    print("🤖 Agent is running...")
    print("💡 Press Ctrl+C to stop the agent")
    print("=" * 60)
    
    try:
        agent.run()
    except KeyboardInterrupt:
        print("\n👋 Agent stopped by user")
    except Exception as e:
        print(f"❌ Error running agent: {e}")
