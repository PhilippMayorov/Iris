#!/usr/bin/env python3
"""
Quick launcher for ASI One Interactive Chat with Intelligent Model Selection

This script provides a convenient way to start the interactive chat
from the project root directory. It includes pre-processing to automatically
determine if a request requires agentic capabilities and switches models accordingly.
"""

import sys
import os
import json
import uuid

# Get the directory containing this script
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, 'src')

# Add the src directory to the Python path
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Import and run the interactive chat
try:
    from asi_integration.interactive_chat import InteractiveChat
    from asi_integration.asi_client import ASIOneClient
    
    class IntelligentChat(InteractiveChat):
        """Enhanced Interactive Chat with intelligent model selection and agent routing."""
        
        def __init__(self, model: str = "asi1-mini", agent_config: dict = None):
            """Initialize the intelligent chat."""
            super().__init__(model)
            self.analysis_client = None
            self.original_model = model
            
            # Agent routing configuration
            self.agent_config = agent_config or self._get_default_agent_config()
            
        def _get_default_agent_config(self) -> dict:
            """Get default agent configuration."""
            return {
                "email": {
                    "keywords": ["email", "send email", "mail", "message", "correspondence"],
                    "agent_address": "better-gmail-agent",
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
        
        def get_response(self, user_message: str) -> str:
            """
            Enhanced get_response with intelligent model selection and agent routing.
            
            Args:
                user_message: The user's message
                
            Returns:
                The assistant's response
            """
            # First, check for agent routing
            print("🔍 Analyzing agent routing...")
            routing = self.analyze_agent_routing(user_message)
            
            # Debug: Show routing results
            print(f"🔍 Routing result: {routing}")
            
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
                if not self.client.is_agentic_model(self.model):
                    print(f"🔄 Switching to agentic model: asi1-fast-agentic")
                    self.change_model("asi1-fast-agentic")
            else:
                # No agent routing, proceed with complexity analysis
                print("🔍 Analyzing request complexity...")
                analysis = self.analyze_request_complexity(user_message)
                
                # Debug: Show analysis results
                print(f"🔍 Analysis result: {analysis}")
                
                # Check if we need to switch models
                if analysis["needs_agentic"] and not self.client.is_agentic_model(self.model):
                    suggested_model = analysis.get("suggested_model", "asi1-fast-agentic")
                    
                    # Validate the suggested model
                    valid_models = ["asi1-mini", "asi1-agentic", "asi1-fast-agentic", "asi1-extended-agentic"]
                    if suggested_model not in valid_models:
                        print(f"⚠️  Invalid model suggested: {suggested_model}, using asi1-fast-agentic")
                        suggested_model = "asi1-fast-agentic"
                    
                    print(f"🤖 Request requires agentic capabilities (confidence: {analysis['confidence']:.1%})")
                    print(f"📝 Reason: {analysis['reason']}")
                    print(f"🔄 Switching to agentic model: {suggested_model}")
                    self.change_model(suggested_model)
                elif not analysis["needs_agentic"] and self.client.is_agentic_model(self.model):
                    print(f"💬 Request suitable for regular chat (confidence: {analysis['confidence']:.1%})")
                    print(f"📝 Reason: {analysis['reason']}")
                    print(f"🔄 Switching to regular model: {self.original_model}")
                    self.change_model(self.original_model)
                else:
                    print(f"✅ Model selection confirmed (confidence: {analysis['confidence']:.1%})")
            
            # Proceed with the original response logic using the modified message
            return super().get_response(modified_message)
    
    def main():
        """Main entry point."""
        # Check for API key
        if not os.getenv('ASI_ONE_API_KEY'):
            print("❌ ASI_ONE_API_KEY environment variable not set")
            print("Please set your API key: export ASI_ONE_API_KEY='your_key_here'")
            sys.exit(1)
        
        print("🧠 Starting Intelligent ASI One Chat")
        print("   - Automatic model selection based on request complexity")
        print("   - Pre-processing to determine agentic capabilities needed")
        print("   - Seamless switching between regular and agentic models")
        print()
        
        # Start intelligent chat
        chat = IntelligentChat()
        chat.run()
    
    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("Make sure you're running this from the project root directory.")
    print("Alternative: python src/asi_integration/interactive_chat.py")
    sys.exit(1)
