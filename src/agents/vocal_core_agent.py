"""
Vocal Core Agent - Central Orchestrator

This is the main coordination agent that:
1. Receives voice commands from the SwiftUI frontend
2. Uses Google Gemini for natural language understanding
3. Delegates tasks to specialized agents (calendar, email, notes, spotify)
4. Manages the overall conversation flow and context

Integration Points:
- Receives HTTP requests from mac-app/ SwiftUI frontend
- Communicates with other agents via Fetch.ai uAgents protocol
- Uses Google Gemini API for intent recognition and reasoning
- Uses ElevenLabs Speech-to-Text API for voice processing
"""

import asyncio
from typing import Dict, Any, Optional
from uagents import Agent, Context, Model
from pydantic import BaseModel
import os
from datetime import datetime

# Initialize the core agent
agent = Agent(
    name="vocal_core_agent",
    port=8000,
    seed="vocal_core_agent_seed",
    endpoint=["http://127.0.0.1:8000/submit"]
)

# Message Models for inter-agent communication
class VoiceCommand(Model):
    """Voice command received from frontend"""
    command: str
    timestamp: datetime
    user_id: str
    request_id: str

class TaskRequest(Model):
    """Request to delegate task to specialized agent"""
    task_type: str  # "calendar", "email", "notes", "spotify"
    intent: str
    parameters: Dict[str, Any]
    request_id: str

class TaskResponse(Model):
    """Response from specialized agent"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]]
    request_id: str

class AgentStatus(Model):
    """Status update from any agent"""
    agent_name: str
    status: str
    message: str
    timestamp: datetime

# Agent addresses for delegation
AGENT_ADDRESSES = {
    "calendar": "agent1qg8p8q8q8q8q8q8q8q8q8q8q8q8q8q8q8q8q8q8q8q8q8q8q8q8",  # TODO: Replace with actual
    "email": "agent1qh9p9q9q9q9q9q9q9q9q9q9q9q9q9q9q9q9q9q9q9q9q9q9q9q9",     # TODO: Replace with actual
    "notes": "agent1qi0p0q0q0q0q0q0q0q0q0q0q0q0q0q0q0q0q0q0q0q0q0q0q0q0",     # TODO: Replace with actual
    "spotify": "agent1qj1p1q1q1q1q1q1q1q1q1q1q1q1q1q1q1q1q1q1q1q1q1q1q1q1"   # TODO: Replace with actual
}

@agent.on_startup
async def startup(ctx: Context):
    """Initialize agent on startup"""
    ctx.logger.info("Vocal Core Agent starting up...")
    ctx.logger.info(f"Agent address: {agent.address}")
    
    # TODO: Initialize Google Gemini API client
    # TODO: Initialize ElevenLabs Speech-to-Text API client
    # TODO: Set up HTTP server for frontend communication

@agent.on_message(model=VoiceCommand)
async def handle_voice_command(ctx: Context, sender: str, msg: VoiceCommand):
    """
    Handle voice command from frontend
    1. Process with Gemini for intent recognition
    2. Delegate to appropriate specialized agent
    """
    ctx.logger.info(f"Received voice command: {msg.command}")
    
    try:
        # TODO: Send to Gemini for intent analysis
        intent_result = await analyze_intent_with_gemini(msg.command)
        
        # Determine which agent should handle this
        target_agent = determine_target_agent(intent_result)
        
        if target_agent and target_agent in AGENT_ADDRESSES:
            # Delegate to specialized agent
            task_request = TaskRequest(
                task_type=target_agent,
                intent=intent_result.get("intent", ""),
                parameters=intent_result.get("parameters", {}),
                request_id=msg.request_id
            )
            
            await ctx.send(AGENT_ADDRESSES[target_agent], task_request)
            ctx.logger.info(f"Delegated task to {target_agent} agent")
        else:
            # Handle directly or send error response
            ctx.logger.warning(f"No suitable agent found for command: {msg.command}")
            
    except Exception as e:
        ctx.logger.error(f"Error processing voice command: {e}")

@agent.on_message(model=TaskResponse)
async def handle_task_response(ctx: Context, sender: str, msg: TaskResponse):
    """Handle response from specialized agent"""
    ctx.logger.info(f"Received task response: {msg.message}")
    
    # TODO: Send response back to frontend via HTTP/WebSocket
    # TODO: Update conversation context
    # TODO: Generate follow-up actions if needed

async def analyze_intent_with_gemini(command: str) -> Dict[str, Any]:
    """
    Use Google Gemini to analyze user intent
    TODO: Implement actual Gemini API call
    """
    # Placeholder implementation
    return {
        "intent": "schedule_meeting",
        "parameters": {
            "title": "Team Meeting",
            "time": "tomorrow 2pm",
            "duration": "1 hour"
        },
        "confidence": 0.95
    }

def determine_target_agent(intent_result: Dict[str, Any]) -> Optional[str]:
    """
    Determine which specialized agent should handle the task
    """
    intent = intent_result.get("intent", "").lower()
    
    if any(keyword in intent for keyword in ["schedule", "calendar", "meeting", "appointment"]):
        return "calendar"
    elif any(keyword in intent for keyword in ["email", "send", "message", "mail"]):
        return "email"
    elif any(keyword in intent for keyword in ["note", "write", "remember", "jot"]):
        return "notes"
    elif any(keyword in intent for keyword in ["music", "play", "song", "spotify"]):
        return "spotify"
    else:
        return None

if __name__ == "__main__":
    print("Starting Vocal Core Agent...")
    print(f"Agent will run on: {agent.address}")
    print("This agent coordinates with:")
    for agent_type, address in AGENT_ADDRESSES.items():
        print(f"  - {agent_type}: {address}")
    
    agent.run()