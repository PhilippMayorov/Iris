"""
ASI One API Example Usage

This file demonstrates how to use the ASI One API client with various examples.
"""

import os
import json

# Handle both relative and absolute imports
try:
    from asi_client import ASIOneClient
except ImportError:
    from .asi_client import ASIOneClient


def example_basic_chat():
    """Example of basic chat functionality."""
    print("=== Basic Chat Example ===")
    
    try:
        client = ASIOneClient()
        
        # Simple question
        response = client.simple_chat("What is artificial intelligence?")
        print(f"AI Question Response: {response}")
        
    except Exception as e:
        print(f"Error in basic chat: {e}")


def example_conversation():
    """Example of a multi-turn conversation."""
    print("\n=== Conversation Example ===")
    
    try:
        client = ASIOneClient()
        
        # Start a conversation
        messages = [
            {"role": "user", "content": "Hi, I'm learning about machine learning. Can you help me?"}
        ]
        
        # First response
        response1 = client.chat_completion(messages)
        assistant_response1 = response1["choices"][0]["message"]["content"]
        print(f"Assistant: {assistant_response1}")
        
        # Continue conversation
        messages.append({"role": "assistant", "content": assistant_response1})
        messages.append({"role": "user", "content": "What's the difference between supervised and unsupervised learning?"})
        
        response2 = client.chat_completion(messages)
        assistant_response2 = response2["choices"][0]["message"]["content"]
        print(f"Assistant: {assistant_response2}")
        
    except Exception as e:
        print(f"Error in conversation: {e}")


def example_response_analysis():
    """Example of analyzing the full API response structure."""
    print("\n=== Response Analysis Example ===")
    
    try:
        client = ASIOneClient()
        
        messages = [{"role": "user", "content": "Explain quantum computing in simple terms."}]
        response = client.chat_completion(messages)
        
        print("Full API Response Structure:")
        print(json.dumps(response, indent=2))
        
        # Extract different parts of the response
        print("\n--- Response Analysis ---")
        
        # Basic response content
        if "choices" in response and len(response["choices"]) > 0:
            choice = response["choices"][0]
            print(f"Content: {choice['message']['content']}")
            print(f"Role: {choice['message']['role']}")
            print(f"Finish Reason: {choice['finish_reason']}")
            
            # Check for reasoning (if available)
            if "reasoning" in choice["message"]:
                print(f"Reasoning: {choice['message']['reasoning']}")
        
        # Token usage
        if "usage" in response:
            usage = response["usage"]
            print(f"Token Usage:")
            print(f"  - Prompt tokens: {usage['prompt_tokens']}")
            print(f"  - Completion tokens: {usage['completion_tokens']}")
            print(f"  - Total tokens: {usage['total_tokens']}")
        
        # Agent-specific fields
        if "executable_data" in response:
            print(f"Executable Data: {response['executable_data']}")
        
        if "intermediate_steps" in response:
            print(f"Intermediate Steps: {response['intermediate_steps']}")
        
        if "thought" in response:
            print(f"Thought: {response['thought']}")
        
        # Model and ID information
        print(f"Model: {response.get('model', 'N/A')}")
        print(f"Response ID: {response.get('id', 'N/A')}")
        print(f"Conversation ID: {response.get('conversation_id', 'N/A')}")
        
    except Exception as e:
        print(f"Error in response analysis: {e}")


def example_error_handling():
    """Example of proper error handling."""
    print("\n=== Error Handling Example ===")
    
    try:
        # Test with invalid API key
        client = ASIOneClient(api_key="invalid_key")
        response = client.simple_chat("Hello")
        print(f"Response with invalid key: {response}")
        
    except Exception as e:
        print(f"Expected error with invalid API key: {e}")
    
    try:
        # Test with valid client but network issue simulation
        client = ASIOneClient()
        # This should work if API key is valid
        response = client.simple_chat("Hello")
        print(f"Valid response: {response}")
        
    except Exception as e:
        print(f"Error with valid setup: {e}")


def main():
    """Run all examples."""
    print("ASI One API Examples")
    print("=" * 50)
    
    # Check if API key is set
    if not os.getenv('ASI_ONE_API_KEY'):
        print("Warning: ASI_ONE_API_KEY environment variable not set.")
        print("Please set your API key to run these examples.")
        print("Example: export ASI_ONE_API_KEY='your_api_key_here'")
        return
    
    # Run examples
    example_basic_chat()
    example_conversation()
    example_response_analysis()
    example_error_handling()
    
    print("\n" + "=" * 50)
    print("Examples completed!")


if __name__ == "__main__":
    main()
