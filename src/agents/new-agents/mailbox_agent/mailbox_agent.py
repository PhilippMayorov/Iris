#!/usr/bin/env python3
"""
Intelligent Mailbox Agent - ASI One Interactive Chat with Intelligent Model Selection

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

# Memory cleanup function
def clear_memory_file():
    """Clear the memory data file"""
    try:
        memory_file = "mailbox_agent_data.json"
        if os.path.exists(memory_file):
            with open(memory_file, 'w') as f:
                f.write("{}")
            print(f"✅ Cleared memory file: {memory_file}")
        else:
            print(f"ℹ️ Memory file not found: {memory_file}")
    except Exception as e:
        print(f"❌ Error clearing memory file: {e}")

# Signal handler for graceful shutdown
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

# Agent-to-Agent Communication Models
class AgentEmailRequest(Model):
    """Request from mailbox agent to gmail agent for email sending"""
    to: str
    subject: str
    body: str
    from_email: Optional[str] = None
    original_message: str  # The original user message for context
    conversation_history: Optional[List[Dict[str, str]]] = None  # Full conversation context

class AgentEmailResponse(Model):
    """Response from gmail agent to mailbox agent"""
    success: bool
    message_id: Optional[str] = None
    error_message: Optional[str] = None
    status_code: int = 200
    needs_clarification: bool = False
    suggestions: Optional[List[str]] = None
    reasoning: Optional[str] = None

class AgentEmailClarificationRequest(Model):
    """Request for clarification from Gmail agent to mailbox agent"""
    needs_clarification: bool = True
    error_message: str
    suggestions: List[str]
    reasoning: str
    partial_email_info: Optional[Dict] = None

class AgentEmailClarificationResponse(Model):
    """Response from mailbox agent to Gmail agent with clarification"""
    clarified_message: str
    conversation_context: Optional[List[Dict]] = None

class HealthCheck(Model):
    """Health check request"""
    pass

class HealthStatus(str, Enum):
    """Health status options"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"

class AgentHealth(Model):
    """Agent health response"""
    agent_name: str
    status: HealthStatus
    message: str = "Intelligent Mailbox Agent is running"

# Quota protocol for rate limiting
proto = QuotaProtocol(
    storage_reference=agent.storage,
    name="Intelligent-Chat-Protocol",
    version="0.1.0",
    default_rate_limit=RateLimit(window_size_minutes=60, max_requests=100),
)

# Health check protocol
health_protocol = QuotaProtocol(
    storage_reference=agent.storage, 
    name="HealthProtocol", 
    version="0.1.0"
)

class IntelligentChatHandler:
    """Enhanced chat handler with intelligent model selection and agent routing.
    
    This handler serves as the central conversation context manager. It maintains
    all conversation history and passes it to other agents so they can make
    informed decisions without maintaining their own persistent memory.
    """
    
    def __init__(self):
        """Initialize the intelligent chat handler."""
        self.analysis_client = None
        self.original_model = "asi1-mini"
        
        # Agent routing configuration
        self.agent_config = self._get_default_agent_config()
        
    def _get_default_agent_config(self) -> dict:
        """Get default agent configuration."""
        return {
            "email": {
                "keywords": ["email", "send email", "mail", "message", "correspondence"],
                "agent_address": "agent1qw6kgumlfqp9drr54qsfngdkz50vgues3u7sewg2fgketekqk8hz500ytg3",
                "description": "Email sending and management tasks",
                "examples": ["send an email", "email my friend", "send a message", "mail someone"]
            },
            "calendar": {
                "keywords": ["calendar", "schedule", "meeting", "appointment", "book time"],
                "agent_address": None,  # Add agent address when available
                "description": "Calendar and scheduling tasks",
                "examples": ["schedule a meeting", "book an appointment", "check my calendar"]
            },
            "web_search": {
                "keywords": ["search", "find", "look up", "research", "google"],
                "agent_address": None,  # Add agent address when available
                "description": "Web search and information gathering",
                "examples": ["search for restaurants", "find information about", "look up"]
            },
            "file_operations": {
                "keywords": ["file", "document", "download", "upload", "save", "create file"],
                "agent_address": None,  # Add agent address when available
                "description": "File and document operations",
                "examples": ["create a file", "download something", "save document"]
            }
        }
    
    def initialize_analysis_client(self) -> bool:
        """Initialize a separate client for request analysis."""
        try:
            self.analysis_client = ASIOneClient()
            return True
        except Exception as e:
            print(f"❌ Failed to initialize analysis client: {e}")
            return False
    
    def analyze_agent_routing(self, user_message: str) -> dict:
        """
        Analyze if the request should be routed to a specific agent.
        
        Args:
            user_message: The user's message to analyze
            
        Returns:
            Dictionary with routing results including matched agent and model
        """
        if not self.analysis_client:
            if not self.initialize_analysis_client():
                return {"matched_agent": None, "confidence": 0.0, "reason": "Analysis client unavailable"}
        
        # Create agent routing prompt
        agent_categories = []
        for category, config in self.agent_config.items():
            if config["agent_address"]:  # Only include agents with addresses
                agent_categories.append(f"- {category}: {config['description']} (examples: {', '.join(config['examples'])})")
        
        routing_prompt = f"""
        Analyze the following user request to determine if it should be routed to a specific agent category.
        
        User Request: "{user_message}"
        
        Available Agent Categories:
        {chr(10).join(agent_categories)}
        
        Consider these factors:
        1. Does the request match the description and examples of any agent category?
        2. Does it require specialized capabilities that a specific agent provides?
        3. Is the request clearly within the scope of a defined agent category?
        
        Respond with a JSON object containing:
        - "matched_agent": string (the agent category name if matched, null if no match)
        - "confidence": float (0.0 to 1.0, confidence in the match)
        - "reason": string (brief explanation of why this agent was or wasn't matched)
        - "suggested_model": string (always "asi1-fast-agentic" if matched, null if no match)
        
        IMPORTANT: Only match if the request clearly falls under one of the defined categories.
        If uncertain or if the request could be handled by general chat, set matched_agent to null.
        """
        
        try:
            # Use a separate conversation for analysis
            analysis_conversation_id = str(uuid.uuid4())
            
            # Make the analysis call
            response = self.analysis_client.simple_chat(
                routing_prompt,
                model="asi1-mini",  # Use regular model for analysis
                conversation_id=analysis_conversation_id
            )
            
            # Try to parse JSON response
            try:
                # Extract JSON from response
                start_idx = response.find('{')
                end_idx = response.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = response[start_idx:end_idx]
                    routing_result = json.loads(json_str)
                    
                    # Validate the response structure
                    required_fields = ["matched_agent", "confidence", "reason"]
                    if all(field in routing_result for field in required_fields):
                        # Validate matched_agent if present
                        if routing_result["matched_agent"] and routing_result["matched_agent"] not in self.agent_config:
                            print(f"⚠️  Invalid agent category: {routing_result['matched_agent']}")
                            routing_result["matched_agent"] = None
                            routing_result["suggested_model"] = None
                        elif routing_result["matched_agent"]:
                            # Set the suggested model and agent address
                            routing_result["suggested_model"] = "asi1-fast-agentic"
                            routing_result["agent_address"] = self.agent_config[routing_result["matched_agent"]]["agent_address"]
                        
                        return routing_result
                    else:
                        print(f"⚠️  Routing response missing required fields: {routing_result}")
                else:
                    print(f"⚠️  Could not extract JSON from routing response: {response}")
                    
            except json.JSONDecodeError as e:
                print(f"⚠️  Failed to parse routing response as JSON: {e}")
                print(f"Raw response: {response}")
            
            # Fallback: keyword-based routing
            return self._fallback_agent_routing(user_message)
            
        except Exception as e:
            print(f"⚠️  Error in agent routing analysis: {e}")
            return self._fallback_agent_routing(user_message)
    
    def _fallback_agent_routing(self, user_message: str) -> dict:
        """Fallback agent routing using keyword matching."""
        message_lower = user_message.lower()
        best_match = None
        best_score = 0
        
        for category, config in self.agent_config.items():
            if not config["agent_address"]:  # Skip agents without addresses
                continue
                
            score = 0
            for keyword in config["keywords"]:
                if keyword.lower() in message_lower:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_match = category
        
        if best_score > 0:
            return {
                "matched_agent": best_match,
                "confidence": min(0.8, best_score * 0.3),  # Cap at 0.8 for fallback
                "reason": f"Fallback routing: matched {best_score} keywords for {best_match}",
                "suggested_model": "asi1-fast-agentic",
                "agent_address": self.agent_config[best_match]["agent_address"]
            }
        else:
            return {
                "matched_agent": None,
                "confidence": 0.0,
                "reason": "Fallback routing: no keyword matches found",
                "suggested_model": None,
                "agent_address": None
            }
    
    def analyze_request_complexity(self, user_message: str) -> dict:
        """
        Analyze if the user request requires agentic capabilities.
        
        Args:
            user_message: The user's message to analyze
            
        Returns:
            Dictionary with analysis results including whether agentic model is needed
        """
        if not self.analysis_client:
            if not self.initialize_analysis_client():
                return {"needs_agentic": False, "confidence": 0.0, "reason": "Analysis client unavailable"}
        
        # Create analysis prompt
        analysis_prompt = f"""
        Analyze the following user request to determine if it requires agentic capabilities (tools, external actions, or complex multi-step tasks).
        
        User Request: "{user_message}"
        
        Consider these factors:
        1. Does it require external tool usage (email, web search, file operations, etc.)?
        2. Does it involve multi-step workflows or task orchestration?
        3. Does it need real-time data or external API calls?
        4. Does it require complex reasoning with multiple sub-tasks?
        5. Does it involve automation or system interactions?
        
        Respond with a JSON object containing:
        - "needs_agentic": boolean (true if agentic capabilities are needed)
        - "confidence": float (0.0 to 1.0, confidence in the assessment)
        - "reason": string (brief explanation of why agentic is or isn't needed)
        - "suggested_model": string (MUST be one of: "asi1-mini", "asi1-agentic", "asi1-fast-agentic", "asi1-extended-agentic")
        
        IMPORTANT: The suggested_model field MUST be exactly one of these valid model names:
        - "asi1-mini" (for regular chat)
        - "asi1-fast-agentic" (recommended for most agentic tasks)
        - "asi1-agentic" (for general orchestration)
        - "asi1-extended-agentic" (for complex multi-stage workflows)
        
        Examples of requests that NEED agentic:
        - "Send an email to john@example.com about the meeting"
        - "Can you send my friend an email?"
        - "Email someone about the project"
        - "Search for restaurants near me and make a reservation"
        - "Create a todo list and set reminders"
        - "Analyze my calendar and suggest optimal meeting times"
        - "Find and download the latest version of Python"
        - "Book a flight to New York"
        - "Order food delivery"
        - "Schedule a meeting with the team"
        
        Examples that DON'T need agentic:
        - "What is the capital of France?"
        - "Explain how photosynthesis works"
        - "Write a poem about nature"
        - "Help me understand this code snippet"
        - "What are the benefits of exercise?"
        """
        
        try:
            # Use a separate conversation for analysis
            analysis_conversation_id = str(uuid.uuid4())
            
            # Make the analysis call
            response = self.analysis_client.simple_chat(
                analysis_prompt,
                model="asi1-mini",  # Use regular model for analysis
                conversation_id=analysis_conversation_id
            )
            
            # Try to parse JSON response
            try:
                # Extract JSON from response (handle cases where response includes extra text)
                start_idx = response.find('{')
                end_idx = response.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = response[start_idx:end_idx]
                    analysis_result = json.loads(json_str)
                    
                    # Validate the response structure
                    required_fields = ["needs_agentic", "confidence", "reason"]
                    if all(field in analysis_result for field in required_fields):
                        # Validate and fix the suggested_model if needed
                        valid_models = ["asi1-mini", "asi1-agentic", "asi1-fast-agentic", "asi1-extended-agentic"]
                        suggested_model = analysis_result.get("suggested_model", "asi1-fast-agentic")
                        
                        if suggested_model not in valid_models:
                            print(f"⚠️  Invalid model suggested: {suggested_model}, defaulting to asi1-fast-agentic")
                            analysis_result["suggested_model"] = "asi1-fast-agentic"
                        
                        return analysis_result
                    else:
                        print(f"⚠️  Analysis response missing required fields: {analysis_result}")
                else:
                    print(f"⚠️  Could not extract JSON from analysis response: {response}")
                    
            except json.JSONDecodeError as e:
                print(f"⚠️  Failed to parse analysis response as JSON: {e}")
                print(f"Raw response: {response}")
            
            # Fallback: simple keyword-based analysis
            return self._fallback_analysis(user_message)
            
        except Exception as e:
            print(f"⚠️  Error in request analysis: {e}")
            return self._fallback_analysis(user_message)
    
    def _fallback_analysis(self, user_message: str) -> dict:
        """Fallback analysis using keyword matching."""
        agentic_keywords = [
            "send", "email", "emails", "search", "find", "download", "create", "schedule", 
            "book", "reserve", "order", "buy", "purchase", "call", "message", "messages",
            "remind", "alert", "notify", "update", "sync", "connect", "integrate",
            "automate", "workflow", "task", "todo", "calendar", "meeting", "meetings",
            "reservation", "booking", "purchase", "payment", "api", "webhook", "friend"
        ]
        
        message_lower = user_message.lower()
        agentic_score = sum(1 for keyword in agentic_keywords if keyword in message_lower)
        
        # Special check for email-related requests
        email_phrases = ["send", "email", "friend", "someone", "message"]
        email_score = sum(1 for phrase in email_phrases if phrase in message_lower)
        
        # If multiple email-related words are present, it's likely an agentic request
        if email_score >= 2:
            needs_agentic = True
            confidence = 0.9
        else:
            needs_agentic = agentic_score > 0
            confidence = min(0.8, agentic_score * 0.2)  # Cap at 0.8 for fallback
        
        return {
            "needs_agentic": needs_agentic,
            "confidence": confidence,
            "reason": f"Fallback analysis: found {agentic_score} potential agentic keywords",
            "suggested_model": "asi1-fast-agentic" if needs_agentic else "asi1-mini"
        }
    
    def _extract_email_info_from_response(self, response_text: str, original_message: str) -> dict:
        """
        Extract email information from ASI:One response
        
        Args:
            response_text: The response from ASI:One
            original_message: The original user message
            
        Returns:
            dict: Extracted email information or None if no email found
        """
        import re
        
        # Try to extract email address from original message first
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, original_message)
        
        if not email_match:
            # Try to extract from response
            email_match = re.search(email_pattern, response_text)
        
        if email_match:
            email_address = email_match.group(0)
            
            # Try to extract subject and body from response
            # This is a simplified extraction - in practice, you'd want more robust parsing
            subject = ""
            body = ""
            
            # Look for common patterns in the response
            if "subject:" in response_text.lower():
                subject_match = re.search(r'subject[:\s]+([^\n]+)', response_text, re.IGNORECASE)
                if subject_match:
                    subject = subject_match.group(1).strip()
            
            # Extract body content (everything after the email address)
            body_start = original_message.find(email_address) + len(email_address)
            if body_start < len(original_message):
                body = original_message[body_start:].strip()
                # Clean up common prefixes
                body = re.sub(r'^(saying|about|that|,)\s*', '', body, flags=re.IGNORECASE)
            
            return {
                "to": email_address,
                "subject": subject,
                "body": body or "Email sent via intelligent mailbox agent"
            }
        
        return None

    async def send_to_gmail_agent(self, ctx: Context, email_request: AgentEmailRequest) -> AgentEmailResponse:
        """
        Send email request to Gmail agent using synchronous communication.
        
        This method always passes the full conversation history to the Gmail agent
        so it can make context-aware decisions without maintaining its own memory.
        
        Args:
            ctx: Agent context
            email_request: Email request to send to Gmail agent (includes conversation_history)
            
        Returns:
            AgentEmailResponse: Response from Gmail agent
        """
        try:
            # Get the Gmail agent address from config
            gmail_agent_address = self.agent_config["email"]["agent_address"]
            
            ctx.logger.info(f"📧 Sending email request to Gmail agent: {gmail_agent_address}")
            ctx.logger.info(f"📧 Email details - To: {email_request.to}, Subject: {email_request.subject}")
            
            # Use ctx.send_and_receive for synchronous communication
            response, status = await ctx.send_and_receive(
                gmail_agent_address, 
                email_request, 
                response_type=AgentEmailResponse
            )
            
            if isinstance(response, AgentEmailResponse):
                ctx.logger.info(f"📧 Received response from Gmail agent: success={response.success}")
                if response.needs_clarification:
                    ctx.logger.info(f"📧 Gmail agent needs clarification: {response.error_message}")
                return response
            else:
                ctx.logger.error(f"📧 Failed to receive proper response from Gmail agent: {status}")
                return AgentEmailResponse(
                    success=False,
                    error_message=f"Failed to receive response from Gmail agent: {status}",
                    status_code=500
                )
                
        except Exception as e:
            ctx.logger.error(f"📧 Error communicating with Gmail agent: {str(e)}")
            return AgentEmailResponse(
                success=False,
                error_message=f"Error communicating with Gmail agent: {str(e)}",
                status_code=500
            )

    def get_intelligent_response(self, user_message: str, conversation_id: str = None, requested_model: str = None, conversation_history: List[Dict[str, str]] = None) -> dict:
        """
        Get an intelligent response with automatic model selection and agent routing.
        
        Args:
            user_message: The user's message
            conversation_id: Optional conversation ID for context
            requested_model: Optional specific model to use
            conversation_history: Optional conversation history for context
            
        Returns:
            Dictionary with response and analysis information
        """
        try:
            # Initialize client if needed
            if not self.analysis_client:
                if not self.initialize_analysis_client():
                    return {
                        "response": "Sorry, I'm having trouble connecting to the AI service. Please try again later.",
                        "conversation_id": conversation_id or str(uuid.uuid4()),
                        "model_used": "error",
                        "agent_routing": None,
                        "complexity_analysis": None,
                        "success": False,
                        "error_message": "Failed to initialize analysis client"
                    }
            
            # First, check for agent routing
            print("🔍 Analyzing agent routing...")
            routing = self.analyze_agent_routing(user_message)
            
            # Debug: Show routing results
            print(f"🔍 Routing result: {routing}")
            
            # Determine the model to use
            model_to_use = requested_model or self.original_model
            
            # Modify the user message if agent routing is needed
            modified_message = user_message
            if routing["matched_agent"]:
                agent_address = routing["agent_address"]
                modified_message = f"@{agent_address} {user_message}"
                print(f"🎯 Routing to {routing['matched_agent']} agent (confidence: {routing['confidence']:.1%})")
                print(f"📝 Reason: {routing['reason']}")
                print(f"🔗 Agent address: {agent_address}")
                print(f"📝 Modified message: {modified_message}")
                
                # Switch to agentic model for agent routing
                model_to_use = "asi1-fast-agentic"
            else:
                # No agent routing, proceed with complexity analysis
                print("🔍 Analyzing request complexity...")
                analysis = self.analyze_request_complexity(user_message)
                
                # Debug: Show analysis results
                print(f"🔍 Analysis result: {analysis}")
                
                # Check if we need to switch models
                if analysis["needs_agentic"]:
                    suggested_model = analysis.get("suggested_model", "asi1-fast-agentic")
                    
                    # Validate the suggested model
                    valid_models = ["asi1-mini", "asi1-agentic", "asi1-fast-agentic", "asi1-extended-agentic"]
                    if suggested_model not in valid_models:
                        print(f"⚠️  Invalid model suggested: {suggested_model}, using asi1-fast-agentic")
                        suggested_model = "asi1-fast-agentic"
                    
                    print(f"🤖 Request requires agentic capabilities (confidence: {analysis['confidence']:.1%})")
                    print(f"📝 Reason: {analysis['reason']}")
                    print(f"🔄 Switching to agentic model: {suggested_model}")
                    model_to_use = suggested_model
                else:
                    print(f"💬 Request suitable for regular chat (confidence: {analysis['confidence']:.1%})")
                    print(f"📝 Reason: {analysis['reason']}")
                    model_to_use = self.original_model
                
                # Store analysis for response
                routing = analysis
            
            # Use provided conversation_id or generate a new one
            final_conversation_id = conversation_id or str(uuid.uuid4())
            
            # Get response from ASI:One
            response = self.analysis_client.simple_chat(
                modified_message,
                model=model_to_use,
                conversation_id=final_conversation_id,
                conversation_history=conversation_history
            )
            
            return {
                "response": response,
                "conversation_id": final_conversation_id,
                "model_used": model_to_use,
                "agent_routing": routing if routing.get("matched_agent") else None,
                "complexity_analysis": routing if not routing.get("matched_agent") else None,
                "success": True,
                "error_message": None
            }
            
        except Exception as e:
            print(f"❌ Error getting intelligent response: {e}")
            return {
                "response": "Sorry, I encountered an error processing your request. Please try again.",
                "conversation_id": conversation_id or str(uuid.uuid4()),
                "model_used": "error",
                "agent_routing": None,
                "complexity_analysis": None,
                "success": False,
                "error_message": str(e)
            }

# Initialize the intelligent chat handler
intelligent_handler = IntelligentChatHandler()

@proto.on_message(ChatRequest, replies={ChatResponse, ErrorMessage})
async def handle_chat_request(ctx: Context, sender: str, msg: ChatRequest):
    """
    Handle chat requests with intelligent model selection and agent routing
    
    Args:
        ctx: Agent context
        sender: Address of the requesting agent
        msg: Chat request
    """
    ctx.logger.info(f"Received chat request from {sender}")
    ctx.logger.info(f"Message: {msg.message}")
    
    # Validate required fields
    if not msg.message or not msg.message.strip():
        error_message = "Message content is required"
        response = ChatResponse(
            response="",
            conversation_id=msg.conversation_id or str(uuid.uuid4()),
            model_used="error",
            success=False,
            error_message=error_message
        )
        ctx.logger.error(f"Chat request failed: {error_message}")
        await ctx.send(sender, response)
        return
    
    # Get intelligent response
    result = intelligent_handler.get_intelligent_response(
        user_message=msg.message,
        conversation_id=msg.conversation_id,
        requested_model=msg.model,
        conversation_history=None  # ChatRequest doesn't have conversation history
    )
    
    # Create response
    response = ChatResponse(
        response=result["response"],
        conversation_id=result["conversation_id"],
        model_used=result["model_used"],
        agent_routing=result["agent_routing"],
        complexity_analysis=result["complexity_analysis"],
        success=result["success"],
        error_message=result["error_message"]
    )
    
    if result["success"]:
        ctx.logger.info(f"Chat response generated successfully using model: {result['model_used']}")
        if result["agent_routing"]:
            ctx.logger.info(f"Agent routing: {result['agent_routing']}")
        if result["complexity_analysis"]:
            ctx.logger.info(f"Complexity analysis: {result['complexity_analysis']}")
    else:
        ctx.logger.error(f"Failed to generate chat response: {result['error_message']}")
    
    await ctx.send(sender, response)

@health_protocol.on_message(HealthCheck, replies={AgentHealth})
async def handle_health_check(ctx: Context, sender: str, msg: HealthCheck):
    """Handle health check requests"""
    await ctx.send(
        sender, 
        AgentHealth(
            agent_name=AGENT_NAME, 
            status=HealthStatus.HEALTHY,
            message="Intelligent Mailbox Agent is running with ASI:One integration"
        )
    )

# Chat Protocol for natural language interactions
chat_protocol = Protocol(spec=chat_protocol_spec)

@chat_protocol.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    """
    Handle chat messages for natural language interactions with intelligent routing
    
    Args:
        ctx: Agent context
        sender: Address of the requesting agent
        msg: Chat message containing natural language request
    """
    # Send acknowledgement
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id),
    )
    
    # Collect text content from message
    text = ''
    for item in msg.content:
        if isinstance(item, TextContent):
            text += item.text
    
    ctx.logger.info(f"Received chat message: {text}")
    
    # Get conversation history for this sender
    conversation_key = f"conversation_{sender}"
    try:
        conversation_history = ctx.storage.get(conversation_key)
        if conversation_history is None:
            conversation_history = []
        ctx.logger.info(f"Retrieved conversation history for {sender}: {len(conversation_history)} messages")
    except Exception as e:
        ctx.logger.warning(f"Failed to retrieve conversation history for {sender}: {e}")
        conversation_history = []
    
    # Check if this is an empty or very short message (likely initialization)
    if not text or len(text.strip()) < 3:
        response_text = f"""👋 Hello! I'm your intelligent mailbox agent with advanced AI capabilities.

🧠 **Intelligent Features:**
- Automatic model selection based on request complexity
- Smart agent routing for specialized tasks
- Pre-processing to determine agentic capabilities needed
- Seamless switching between regular and agentic models

🎯 **I can help you with:**
- General chat and questions
- Email sending (routes to Gmail agent)
- Complex multi-step tasks
- Agentic workflows and automation
- And much more!

💡 **Just talk to me naturally** - I'll automatically determine the best approach for your request.

What would you like to do today?"""
        
        # Update conversation history for greeting responses
        conversation_history.append({"role": "user", "content": text})
        conversation_history.append({"role": "assistant", "content": response_text})
        
        # Keep only last 20 messages to prevent context from growing too large
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]
        
        # Store updated conversation history
        try:
            ctx.storage.set(conversation_key, conversation_history)
            ctx.logger.info(f"Stored conversation history for {sender}: {len(conversation_history)} messages")
        except Exception as e:
            ctx.logger.warning(f"Failed to store conversation history for {sender}: {e}")
        
        await ctx.send(sender, ChatMessage(
            timestamp=datetime.utcnow(),
            msg_id=uuid.uuid4(),
            content=[
                TextContent(type="text", text=response_text),
            ]
        ))
        return
    
    # Use a consistent conversation ID based on sender for memory persistence
    consistent_conversation_id = f"direct_chat_{sender.replace(':', '_').replace('/', '_')}"
    
    # Get intelligent response
    result = intelligent_handler.get_intelligent_response(
        user_message=text,
        conversation_id=consistent_conversation_id,
        conversation_history=conversation_history
    )
    
    # Check if we need to route to Gmail agent
    if result["agent_routing"] and result["agent_routing"]["matched_agent"] == "email":
        # For email routing, we'll send the original message to the Gmail agent
        # and let it handle the ASI:One processing and email extraction
        
        # Try to extract basic email info for the request, but let Gmail agent do the heavy lifting
        email_info = intelligent_handler._extract_email_info_from_response(result["response"], text)
        
        # Create email request for Gmail agent with original message and conversation history
        # The Gmail agent will use ASI:One to process the original message with full context
        email_request = AgentEmailRequest(
            to=email_info.get("to", "") if email_info else "",
            subject=email_info.get("subject", "") if email_info else "",
            body=email_info.get("body", "") if email_info else "",
            original_message=text,  # This is the key - send the original user message
            conversation_history=conversation_history  # Pass the full conversation context
        )
        
        # Send to Gmail agent and wait for response
        gmail_response = await intelligent_handler.send_to_gmail_agent(ctx, email_request)
        
        if gmail_response.success:
            response_text = f"✅ Email sent successfully!\n\nMessage ID: {gmail_response.message_id}"
            if gmail_response.reasoning:
                response_text += f"\n\n🧠 **AI Understanding:** {gmail_response.reasoning}"
        elif gmail_response.needs_clarification:
            # Handle clarification request from Gmail agent
            response_text = f"🤔 I need a bit more information to send that email:\n\n{gmail_response.error_message}"
            if gmail_response.suggestions:
                response_text += "\n\n💡 **Suggestions:**\n" + "\n".join([f"- {s}" for s in gmail_response.suggestions])
            if gmail_response.reasoning:
                response_text += f"\n\n🧠 **What I understood:** {gmail_response.reasoning}"
        else:
            response_text = f"❌ Failed to send email: {gmail_response.error_message}"
        
        # Update conversation history with the email interaction
        conversation_history.append({"role": "user", "content": text})
        conversation_history.append({"role": "assistant", "content": response_text})
        
        # Keep only last 20 messages to prevent context from growing too large
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]
        
        # Store updated conversation history
        try:
            ctx.storage.set(conversation_key, conversation_history)
            ctx.logger.info(f"Stored conversation history for {sender}: {len(conversation_history)} messages")
        except Exception as e:
            ctx.logger.warning(f"Failed to store conversation history for {sender}: {e}")
    else:
        if result["success"]:
            response_text = result["response"]
            
            # Add analysis information if available
            if result["agent_routing"]:
                routing_info = result["agent_routing"]
                response_text += f"\n\n🔍 **Agent Routing:** {routing_info['reason']} (confidence: {routing_info['confidence']:.1%})"
            
            if result["complexity_analysis"]:
                analysis_info = result["complexity_analysis"]
                response_text += f"\n\n🧠 **Analysis:** {analysis_info['reason']} (confidence: {analysis_info['confidence']:.1%})"
            
            response_text += f"\n\n🤖 **Model Used:** {result['model_used']}"
        else:
            response_text = f"❌ {result['error_message']}"
    
    # Update conversation history (only for non-email routing cases)
    if not (result["agent_routing"] and result["agent_routing"]["matched_agent"] == "email"):
        conversation_history.append({"role": "user", "content": text})
        conversation_history.append({"role": "assistant", "content": response_text})
        
        # Keep only last 20 messages to prevent context from growing too large
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]
        
        # Store updated conversation history
        try:
            ctx.storage.set(conversation_key, conversation_history)
            ctx.logger.info(f"Stored conversation history for {sender}: {len(conversation_history)} messages")
        except Exception as e:
            ctx.logger.warning(f"Failed to store conversation history for {sender}: {e}")
    
    # Send response back
    await ctx.send(sender, ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid.uuid4(),
        content=[
            TextContent(type="text", text=response_text),
        ]
    ))

@chat_protocol.on_message(ChatAcknowledgement)
async def handle_chat_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
    """Handle chat acknowledgements"""
    ctx.logger.info(f"Received chat acknowledgement from {sender}")

# Include protocols in agent
agent.include(proto)
agent.include(health_protocol, publish_manifest=True)
agent.include(chat_protocol, publish_manifest=True)

@agent.on_event("startup")
async def startup(ctx: Context):
    """Agent startup event"""
    ctx.logger.info(f"Intelligent Mailbox Agent started: {agent.address}")
    
    # Keep memory file for conversation persistence
    ctx.logger.info("💾 Preserving conversation memory for continuity...")
    
    # Initialize intelligent chat handler
    if intelligent_handler.initialize_analysis_client():
        ctx.logger.info("✅ Intelligent chat handler initialized successfully")
        ctx.logger.info("🧠 Automatic model selection enabled")
        ctx.logger.info("🎯 Agent routing enabled")
        ctx.logger.info("📊 Request complexity analysis enabled")
    else:
        ctx.logger.warning("❌ Failed to initialize intelligent chat handler")
        ctx.logger.warning("⚠️ Set ASI_ONE_API_KEY environment variable to enable full functionality")
    
    ctx.logger.info("Chat protocol enabled for natural language interactions")
    ctx.logger.info("Mailbox endpoint ready for external access")

@agent.on_event("shutdown")
async def shutdown(ctx: Context):
    """Agent shutdown event"""
    ctx.logger.info("Intelligent Mailbox Agent shutting down...")
    ctx.logger.info("👋 Intelligent Mailbox Agent shutdown complete")

if __name__ == "__main__":
    print(f"Intelligent Mailbox Agent Address: {agent.address}")
    
    # Show ASI:One status
    if asi_one_client:
        print("\n✅ ASI:One AI integration enabled")
        print("Enhanced intelligent chat processing available")
        print("🧠 Automatic model selection enabled")
        print("🎯 Agent routing enabled")
        print("📊 Request complexity analysis enabled")
    else:
        print("\n⚠️ ASI:One AI integration disabled")
        print("Set ASI_ONE_API_KEY environment variable to enable")
        print("Get your API key at: https://asi1.ai/dashboard/api-keys")
    
    print("\n🚀 Starting Intelligent Mailbox Agent...")
    print("📧 Mailbox endpoint ready for external access")
    print("🔗 Agent address:", agent.address)
    agent.run()
