"""
ASI One API Client

This module provides a Python client for interacting with the ASI One API.
It includes support for both regular chat models and agentic models that can
work with the Agentverse marketplace.
"""

import requests
import os
import json
import uuid
import time
import sys
from typing import Dict, List, Optional, Any, Generator


class ASIOneClient:
    """Client for interacting with the ASI One API with support for agentic models."""
    
    # Available models
    REGULAR_MODELS = ["asi1-mini"]
    AGENTIC_MODELS = ["asi1-agentic", "asi1-fast-agentic", "asi1-extended-agentic"]
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 90):
        """
        Initialize the ASI One client.
        
        Args:
            api_key: API key for ASI One. If not provided, will try to get from environment variable ASI_ONE_API_KEY
            timeout: Request timeout in seconds (default: 90)
        """
        self.api_key = api_key or os.getenv('ASI_ONE_API_KEY')
        if not self.api_key:
            raise ValueError("ASI One API key is required. Set ASI_ONE_API_KEY environment variable or pass api_key parameter.")
        
        self.base_url = "https://api.asi1.ai/v1"
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Session management for agentic models
        self.session_map: Dict[str, str] = {}
    
    def get_session_id(self, conversation_id: str) -> str:
        """
        Get or create a session ID for the given conversation.
        
        Args:
            conversation_id: Unique identifier for the conversation
            
        Returns:
            Session ID for the conversation
        """
        session_id = self.session_map.get(conversation_id)
        if not session_id:
            session_id = str(uuid.uuid4())
            self.session_map[conversation_id] = session_id
        return session_id
    
    def is_agentic_model(self, model: str) -> bool:
        """Check if the model is an agentic model."""
        return model in self.AGENTIC_MODELS
    
    def get_headers(self, conversation_id: Optional[str] = None, model: str = "asi1-mini") -> Dict[str, str]:
        """
        Get headers for API requests, including session ID for agentic models.
        
        Args:
            conversation_id: Conversation ID for session management
            model: Model being used
            
        Returns:
            Headers dictionary
        """
        headers = self.headers.copy()
        
        # Add session ID for agentic models
        if self.is_agentic_model(model) and conversation_id:
            session_id = self.get_session_id(conversation_id)
            headers["x-session-id"] = session_id
        
        return headers
    
    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = "asi1-mini",
        conversation_id: Optional[str] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make a chat completion request to the ASI One API.
        
        Args:
            messages: List of message objects with 'role' and 'content' keys
            model: Model to use for completion (default: "asi1-mini")
            conversation_id: Conversation ID for session management (required for agentic models)
            stream: Whether to stream the response
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            Dictionary containing the API response
            
        Raises:
            requests.RequestException: If the API request fails
        """
        url = f"{self.base_url}/chat/completions"
        
        # Validate conversation_id for agentic models
        if self.is_agentic_model(model) and not conversation_id:
            raise ValueError(f"conversation_id is required for agentic model '{model}'")
        
        body = {
            "model": model,
            "messages": messages,
            "stream": stream,
            **kwargs
        }
        
        # Get appropriate headers
        headers = self.get_headers(conversation_id, model)
        
        try:
            if stream:
                return self._handle_streaming_response(url, headers, body)
            else:
                response = requests.post(url, headers=headers, json=body, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
        except requests.RequestException as e:
            print(f"Error making API request: {e}")
            raise
    
    def _handle_streaming_response(self, url: str, headers: Dict[str, str], body: Dict[str, Any]) -> Generator[str, None, None]:
        """
        Handle streaming response from the API.
        
        Args:
            url: API endpoint URL
            headers: Request headers
            body: Request body
            
        Yields:
            Streaming response chunks
        """
        with requests.post(url, headers=headers, json=body, timeout=self.timeout, stream=True) as response:
            response.raise_for_status()
            
            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    continue
                
                if line.startswith("data: "):
                    line = line[len("data: "):]
                
                if line == "[DONE]":
                    break
                
                try:
                    chunk = json.loads(line)
                    choices = chunk.get("choices")
                    if choices and "content" in choices[0].get("delta", {}):
                        token = choices[0]["delta"]["content"]
                        yield token
                except json.JSONDecodeError:
                    continue
    
    def simple_chat(self, message: str, model: str = "asi1-mini", conversation_id: Optional[str] = None, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Simple method to send a single message and get a response.
        
        Args:
            message: The user message to send
            model: Model to use for completion (default: "asi1-mini")
            conversation_id: Conversation ID for session management (required for agentic models)
            conversation_history: Previous conversation messages for context
            
        Returns:
            The assistant's response content
        """
        # Build messages array with conversation history (copy to avoid modifying original)
        messages = []
        if conversation_history:
            messages.extend(conversation_history.copy())
        messages.append({"role": "user", "content": message})
        
        response = self.chat_completion(messages, model, conversation_id)
        
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            print(f"Error parsing response: {e}")
            print(f"Response: {json.dumps(response, indent=2)}")
            raise
    
    def stream_chat(self, message: str, model: str = "asi1-mini", conversation_id: Optional[str] = None, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Stream a chat response and return the full text.
        
        Args:
            message: The user message to send
            model: Model to use for completion (default: "asi1-mini")
            conversation_id: Conversation ID for session management (required for agentic models)
            conversation_history: Previous conversation messages for context
            
        Returns:
            The complete assistant's response
        """
        # Build messages array with conversation history (copy to avoid modifying original)
        messages = []
        if conversation_history:
            messages.extend(conversation_history.copy())
        messages.append({"role": "user", "content": message})
        
        stream = self.chat_completion(messages, model, conversation_id, stream=True)
        
        full_text = ""
        for token in stream:
            sys.stdout.write(token)
            sys.stdout.flush()
            full_text += token
        
        print()  # New line after streaming
        return full_text
    
    def poll_for_async_reply(
        self, 
        conversation_id: str, 
        messages: List[Dict[str, str]], 
        model: str = "asi1-fast-agentic",
        wait_sec: int = 5, 
        max_attempts: int = 20
    ) -> Optional[str]:
        """
        Poll for asynchronous agent responses from Agentverse.
        
        Args:
            conversation_id: Conversation ID for session management
            messages: Conversation history
            model: Model to use for polling
            wait_sec: Seconds to wait between polling attempts
            max_attempts: Maximum number of polling attempts
            
        Returns:
            The agent's response if available, None if no response after max attempts
        """
        for attempt in range(max_attempts):
            time.sleep(wait_sec)
            print(f"🔄 Polling (attempt {attempt + 1}/{max_attempts})...", flush=True)
            
            try:
                # Create a polling message to check for updates
                polling_messages = messages.copy()
                polling_messages.append({
                    "role": "user", 
                    "content": "Please check if there are any updates from the agents I contacted. Have they completed their tasks?"
                })
                
                response = self.chat_completion(polling_messages, model, conversation_id)
                reply = response["choices"][0]["message"]["content"]
                
                # Check for various response patterns
                no_response_indicators = [
                    "no new message",
                    "no updates",
                    "no response",
                    "still working",
                    "no completion",
                    "nothing new"
                ]
                
                if reply and not any(indicator in reply.lower() for indicator in no_response_indicators):
                    # Check if this looks like a meaningful response
                    if len(reply.strip()) > 10 and not reply.lower().startswith("i don't"):
                        return reply
                    
            except Exception as e:
                print(f"Error during polling: {e}")
                continue
        
        return None


def main():
    """Example usage of the ASI One client with both regular and agentic models."""
    try:
        # Initialize the client
        client = ASIOneClient()
        
        print("🤖 ASI One API Client Demo")
        print("=" * 50)
        
        # Example 1: Regular model
        print("\n1. Regular Model (asi1-mini):")
        print("-" * 30)
        response = client.simple_chat("Hello! How can you help me today?")
        print(f"Response: {response}")
        
        # Example 2: Agentic model with streaming
        print("\n2. Agentic Model with Streaming (asi1-fast-agentic):")
        print("-" * 50)
        conversation_id = str(uuid.uuid4())
        print(f"Conversation ID: {conversation_id}")
        
        print("Streaming response:")
        streamed_response = client.stream_chat(
            "Help me find a good restaurant for dinner tonight", 
            model="asi1-fast-agentic",
            conversation_id=conversation_id
        )
        
        # Example 3: Full conversation with agentic model
        print("\n3. Full Conversation with Agentic Model:")
        print("-" * 45)
        messages = [
            {"role": "user", "content": "I need help planning a weekend trip to San Francisco"}
        ]
        
        response = client.chat_completion(messages, "asi1-fast-agentic", conversation_id)
        assistant_reply = response["choices"][0]["message"]["content"]
        print(f"Assistant: {assistant_reply}")
        
        # Add to conversation history
        messages.append({"role": "assistant", "content": assistant_reply})
        messages.append({"role": "user", "content": "What about hotels in the downtown area?"})
        
        # Continue conversation
        response2 = client.chat_completion(messages, "asi1-fast-agentic", conversation_id)
        assistant_reply2 = response2["choices"][0]["message"]["content"]
        print(f"Assistant: {assistant_reply2}")
        
        # Example 4: Show session management
        print("\n4. Session Management:")
        print("-" * 25)
        session_id = client.get_session_id(conversation_id)
        print(f"Session ID for conversation: {session_id}")
        print(f"Active sessions: {len(client.session_map)}")
        
        # Example 5: Model information
        print("\n5. Available Models:")
        print("-" * 20)
        print(f"Regular models: {client.REGULAR_MODELS}")
        print(f"Agentic models: {client.AGENTIC_MODELS}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure to set your ASI_ONE_API_KEY environment variable.")


if __name__ == "__main__":
    main()
