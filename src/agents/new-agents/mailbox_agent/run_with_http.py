#!/usr/bin/env python3
"""
Run Intelligent Mailbox Agent with HTTP Endpoint

This script starts both the mailbox agent and the HTTP endpoint server.
"""

import os
import sys
import threading
import time
import signal

# Add the project root to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir))))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from mailbox_agent import agent
    from http_endpoint import run_http_server_in_thread, set_agent_instance
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("Make sure you're running this from the mailbox_agent directory.")
    sys.exit(1)

# Configuration
HTTP_PORT = int(os.getenv("HTTP_PORT", "8002"))
AGENT_PORT = int(os.getenv("PORT", "8001"))

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\n🛑 Received signal {signum} - shutting down gracefully...")
    print("👋 Intelligent Mailbox Agent with HTTP endpoint shutdown complete")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

def main():
    """Main entry point"""
    # Check for required environment variables
    if not os.getenv('ASI_ONE_API_KEY'):
        print("❌ ASI_ONE_API_KEY environment variable not set")
        print("Please set your API key: export ASI_ONE_API_KEY='your_key_here'")
        sys.exit(1)
    
    print("🚀 Starting Intelligent Mailbox Agent with HTTP Endpoint...")
    print("=" * 60)
    
    # Set the agent instance for HTTP endpoint
    set_agent_instance(agent)
    
    # Start HTTP server in a separate thread
    print("🌐 Starting HTTP endpoint server...")
    http_thread = run_http_server_in_thread()
    
    # Give HTTP server time to start
    time.sleep(2)
    
    print("🤖 Starting mailbox agent...")
    print(f"📧 Mailbox Agent Address: {agent.address}")
    print(f"🔗 HTTP Endpoint: http://localhost:{HTTP_PORT}")
    print(f"📡 API Documentation: http://localhost:{HTTP_PORT}/docs")
    print(f"🔍 Health Check: http://localhost:{HTTP_PORT}/health")
    print(f"💬 Chat Endpoint: http://localhost:{HTTP_PORT}/chat")
    print("=" * 60)
    print("✅ Both services are running!")
    print("💡 You can now access the agent via:")
    print("   - Mailbox protocol (agent address)")
    print("   - HTTP API (REST endpoints)")
    print("   - Interactive documentation (Swagger UI)")
    print("=" * 60)
    
    try:
        # Start the mailbox agent (this will block)
        agent.run()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    except Exception as e:
        print(f"\n❌ Error running agent: {e}")
    finally:
        print("👋 Shutdown complete")

if __name__ == "__main__":
    main()
