#!/usr/bin/env python3
"""
HTTP Endpoint Wrapper for Intelligent Mailbox Agent

This provides an HTTP API wrapper around the mailbox agent for easy external access.
"""

import os
import sys
import json
import asyncio
import threading
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import uuid4

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir))))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import uvicorn
    from mailbox_agent import intelligent_handler
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("Please install required dependencies: pip install fastapi uvicorn")
    sys.exit(1)

# HTTP API Configuration
HTTP_PORT = int(os.getenv("HTTP_PORT", "8002"))
HTTP_HOST = os.getenv("HTTP_HOST", "0.0.0.0")

# Initialize FastAPI app
app = FastAPI(
    title="Intelligent Mailbox Agent API",
    description="HTTP API wrapper for the Intelligent Mailbox Agent with ASI:One integration",
    version="1.0.0"
)

# Request/Response Models
class ChatRequest(BaseModel):
    """HTTP request model for chat interactions"""
    message: str
    conversation_id: Optional[str] = None
    model: Optional[str] = None

class ChatResponse(BaseModel):
    """HTTP response model for chat interactions"""
    response: str
    conversation_id: str
    model_used: str
    agent_routing: Optional[Dict[str, Any]] = None
    complexity_analysis: Optional[Dict[str, Any]] = None
    success: bool = True
    error_message: Optional[str] = None
    timestamp: str = None

class HealthResponse(BaseModel):
    """HTTP response model for health checks"""
    status: str
    message: str
    timestamp: str
    agent_address: Optional[str] = None

# Global agent reference (will be set when agent starts)
agent_instance = None

def set_agent_instance(agent):
    """Set the agent instance for health checks"""
    global agent_instance
    agent_instance = agent

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint with basic information"""
    return HealthResponse(
        status="healthy",
        message="Intelligent Mailbox Agent HTTP API is running",
        timestamp=datetime.utcnow().isoformat(),
        agent_address=agent_instance.address if agent_instance else None
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="Intelligent Mailbox Agent is running with ASI:One integration",
        timestamp=datetime.utcnow().isoformat(),
        agent_address=agent_instance.address if agent_instance else None
    )

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint for intelligent interactions
    
    Args:
        request: Chat request with message and optional parameters
        
    Returns:
        Chat response with AI-generated content and analysis
    """
    try:
        # Validate request
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message content is required")
        
        # Get intelligent response
        result = intelligent_handler.get_intelligent_response(
            user_message=request.message,
            conversation_id=request.conversation_id,
            requested_model=request.model
        )
        
        # Create response
        response = ChatResponse(
            response=result["response"],
            conversation_id=result["conversation_id"],
            model_used=result["model_used"],
            agent_routing=result.get("agent_routing"),
            complexity_analysis=result.get("complexity_analysis"),
            success=result["success"],
            error_message=result.get("error_message"),
            timestamp=datetime.utcnow().isoformat()
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error_message"])
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/models")
async def get_available_models():
    """Get list of available ASI:One models"""
    return {
        "regular_models": ["asi1-mini"],
        "agentic_models": ["asi1-agentic", "asi1-fast-agentic", "asi1-extended-agentic"],
        "recommended": "asi1-fast-agentic",
        "default": "asi1-mini"
    }

@app.get("/agent-config")
async def get_agent_config():
    """Get current agent routing configuration"""
    return {
        "agent_categories": intelligent_handler.agent_config,
        "description": "Available agent categories for routing"
    }

@app.post("/analyze")
async def analyze_request(request: ChatRequest):
    """
    Analyze a request without generating a response
    
    Args:
        request: Request to analyze
        
    Returns:
        Analysis results including routing and complexity assessment
    """
    try:
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message content is required")
        
        # Get routing analysis
        routing = intelligent_handler.analyze_agent_routing(request.message)
        
        # Get complexity analysis
        complexity = intelligent_handler.analyze_request_complexity(request.message)
        
        return {
            "message": request.message,
            "agent_routing": routing,
            "complexity_analysis": complexity,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

def start_http_server():
    """Start the HTTP server"""
    print(f"🌐 Starting HTTP endpoint server on {HTTP_HOST}:{HTTP_PORT}")
    print(f"📡 API Documentation: http://{HTTP_HOST}:{HTTP_PORT}/docs")
    print(f"🔍 Health Check: http://{HTTP_HOST}:{HTTP_PORT}/health")
    print(f"💬 Chat Endpoint: http://{HTTP_HOST}:{HTTP_PORT}/chat")
    
    uvicorn.run(
        app,
        host=HTTP_HOST,
        port=HTTP_PORT,
        log_level="info"
    )

def run_http_server_in_thread():
    """Run the HTTP server in a separate thread"""
    def run_server():
        start_http_server()
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    return server_thread

if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv('ASI_ONE_API_KEY'):
        print("❌ ASI_ONE_API_KEY environment variable not set")
        print("Please set your API key: export ASI_ONE_API_KEY='your_key_here'")
        sys.exit(1)
    
    print("🚀 Starting Intelligent Mailbox Agent HTTP Endpoint...")
    start_http_server()
