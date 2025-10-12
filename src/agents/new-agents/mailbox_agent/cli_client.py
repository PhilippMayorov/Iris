#!/usr/bin/env python3
"""
CLI Client for Intelligent Mailbox Agent

A command-line interface for interacting with the mailbox agent via HTTP.
"""

import os
import sys
import json
import asyncio
import argparse
from typing import Optional, Dict, Any
from datetime import datetime

try:
    import httpx
    import rich
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.syntax import Syntax
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("Please install: pip install httpx rich")
    sys.exit(1)

# Configuration
DEFAULT_BASE_URL = "http://localhost:8002"
console = Console()

class MailboxAgentCLI:
    """CLI client for the Intelligent Mailbox Agent"""
    
    def __init__(self, base_url: str = DEFAULT_BASE_URL):
        self.base_url = base_url
        # Use a consistent conversation ID for the CLI client
        self.conversation_id = "cli_client_session"
        self.conversation_history = []
        
    async def test_connection(self) -> bool:
        """Test connection to the agent"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health", timeout=5.0)
                if response.status_code == 200:
                    health_data = response.json()
                    console.print(f"✅ Connected to agent at {self.base_url}")
                    console.print(f"📧 Agent Address: {health_data.get('agent_address', 'Unknown')}")
                    return True
                else:
                    console.print(f"❌ Health check failed: {response.status_code}")
                    return False
        except Exception as e:
            console.print(f"❌ Connection failed: {e}")
            return False
    
    async def send_message(self, message: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Send a message to the agent"""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "message": message,
                    "conversation_id": self.conversation_id
                }
                if model:
                    payload["model"] = model
                
                response = await client.post(
                    f"{self.base_url}/chat",
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "success": False,
                        "error_message": f"HTTP {response.status_code}: {response.text}"
                    }
        except Exception as e:
            return {
                "success": False,
                "error_message": f"Request failed: {e}"
            }
    
    async def analyze_request(self, message: str) -> Dict[str, Any]:
        """Analyze a request without sending it"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/analyze",
                    json={"message": message},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": f"Request failed: {e}"}
    
    async def get_models(self) -> Dict[str, Any]:
        """Get available models"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/models", timeout=5.0)
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": f"Request failed: {e}"}
    
    async def get_agent_config(self) -> Dict[str, Any]:
        """Get agent configuration"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/agent-config", timeout=5.0)
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"HTTP {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": f"Request failed: {e}"}
    
    def display_response(self, result: Dict[str, Any]):
        """Display the agent response in a nice format"""
        if not result.get("success", True):
            console.print(f"❌ Error: {result.get('error_message', 'Unknown error')}")
            return
        
        # Main response
        response_text = result.get("response", "")
        console.print(Panel(
            Text(response_text, style="white"),
            title="🤖 Agent Response",
            border_style="blue"
        ))
        
        # Analysis information
        if result.get("agent_routing"):
            routing = result["agent_routing"]
            console.print(f"🎯 [bold blue]Agent Routing:[/bold blue] {routing.get('matched_agent', 'None')} (confidence: {routing.get('confidence', 0):.1%})")
            console.print(f"📝 [dim]Reason:[/dim] {routing.get('reason', 'N/A')}")
        
        if result.get("complexity_analysis"):
            analysis = result["complexity_analysis"]
            model_type = "Agentic" if analysis.get("needs_agentic") else "Regular"
            console.print(f"🧠 [bold green]Complexity:[/bold green] {model_type} (confidence: {analysis.get('confidence', 0):.1%})")
            console.print(f"📝 [dim]Reason:[/dim] {analysis.get('reason', 'N/A')}")
        
        # Model used
        model_used = result.get("model_used", "Unknown")
        console.print(f"🤖 [bold yellow]Model Used:[/bold yellow] {model_used}")
        
        # Conversation ID
        conv_id = result.get("conversation_id", "Unknown")
        console.print(f"🆔 [dim]Conversation ID:[/dim] {conv_id}")
    
    def display_analysis(self, analysis: Dict[str, Any]):
        """Display request analysis"""
        if "error" in analysis:
            console.print(f"❌ Analysis failed: {analysis['error']}")
            return
        
        message = analysis.get("message", "")
        console.print(Panel(
            Text(f"Analyzing: {message}", style="cyan"),
            title="🔍 Request Analysis",
            border_style="cyan"
        ))
        
        # Agent routing
        if analysis.get("agent_routing"):
            routing = analysis["agent_routing"]
            console.print(f"🎯 [bold blue]Agent Routing:[/bold blue] {routing.get('matched_agent', 'None')} (confidence: {routing.get('confidence', 0):.1%})")
            console.print(f"📝 [dim]Reason:[/dim] {routing.get('reason', 'N/A')}")
        
        # Complexity analysis
        if analysis.get("complexity_analysis"):
            complexity = analysis["complexity_analysis"]
            model_type = "Agentic" if complexity.get("needs_agentic") else "Regular"
            console.print(f"🧠 [bold green]Complexity:[/bold green] {model_type} (confidence: {complexity.get('confidence', 0):.1%})")
            console.print(f"📝 [dim]Reason:[/dim] {complexity.get('reason', 'N/A')}")
    
    def display_models(self, models: Dict[str, Any]):
        """Display available models"""
        if "error" in models:
            console.print(f"❌ Failed to get models: {models['error']}")
            return
        
        table = Table(title="🤖 Available Models")
        table.add_column("Type", style="cyan")
        table.add_column("Models", style="white")
        
        table.add_row("Regular", ", ".join(models.get("regular_models", [])))
        table.add_row("Agentic", ", ".join(models.get("agentic_models", [])))
        table.add_row("Recommended", models.get("recommended", "N/A"))
        table.add_row("Default", models.get("default", "N/A"))
        
        console.print(table)
    
    def display_agent_config(self, config: Dict[str, Any]):
        """Display agent configuration"""
        if "error" in config:
            console.print(f"❌ Failed to get config: {config['error']}")
            return
        
        console.print(Panel(
            "Agent Routing Configuration",
            title="⚙️ Agent Config",
            border_style="green"
        ))
        
        categories = config.get("agent_categories", {})
        for category, details in categories.items():
            console.print(f"📧 [bold]{category.title()}:[/bold] {details.get('description', 'N/A')}")
            if details.get("agent_address"):
                console.print(f"   🔗 Address: {details['agent_address']}")
            console.print(f"   🏷️ Keywords: {', '.join(details.get('keywords', []))}")
            console.print()
    
    async def interactive_mode(self):
        """Run in interactive mode"""
        console.print(Panel(
            "Intelligent Mailbox Agent CLI\nType your messages and press Enter to send.\nType '/help' for commands, '/quit' to exit.",
            title="🚀 Interactive Mode",
            border_style="green"
        ))
        
        while True:
            try:
                message = Prompt.ask("\n[bold blue]You[/bold blue]")
                
                if not message.strip():
                    continue
                
                # Handle commands
                if message.startswith('/'):
                    await self.handle_command(message)
                    continue
                
                # Send message
                console.print("🤖 [dim]Thinking...[/dim]")
                result = await self.send_message(message)
                self.display_response(result)
                
                # Store in history
                self.conversation_history.append({
                    "user": message,
                    "agent": result.get("response", ""),
                    "timestamp": datetime.now().isoformat()
                })
                
            except KeyboardInterrupt:
                console.print("\n👋 Goodbye!")
                break
            except Exception as e:
                console.print(f"❌ Error: {e}")
    
    async def handle_command(self, command: str):
        """Handle CLI commands"""
        cmd = command.lower().strip()
        
        if cmd in ['/help', '/h']:
            self.show_help()
        elif cmd in ['/quit', '/q', '/exit']:
            console.print("👋 Goodbye!")
            sys.exit(0)
        elif cmd in ['/models', '/m']:
            models = await self.get_models()
            self.display_models(models)
        elif cmd in ['/config', '/c']:
            config = await self.get_agent_config()
            self.display_agent_config(config)
        elif cmd in ['/history', '/hist']:
            self.show_history()
        elif cmd in ['/clear']:
            self.conversation_history = []
            # Keep the same conversation ID for consistency
            console.print("🗑️ Local conversation history cleared (server memory preserved)")
        elif cmd.startswith('/analyze '):
            message = command[9:].strip()
            if message:
                analysis = await self.analyze_request(message)
                self.display_analysis(analysis)
            else:
                console.print("❌ Please provide a message to analyze")
        elif cmd.startswith('/model '):
            model = command[7:].strip()
            console.print(f"🔄 Model preference set to: {model}")
            console.print("💡 This will be used for the next message")
        else:
            console.print(f"❌ Unknown command: {cmd}")
            console.print("Type '/help' for available commands")
    
    def show_help(self):
        """Show help information"""
        help_text = """
[bold]Available Commands:[/bold]

[cyan]Chat Commands:[/cyan]
  Just type your message to chat with the agent

[cyan]System Commands:[/cyan]
  /help, /h          - Show this help message
  /quit, /q, /exit   - Exit the CLI
  /models, /m        - Show available models
  /config, /c        - Show agent configuration
  /history, /hist    - Show conversation history
  /clear             - Clear conversation history

[cyan]Analysis Commands:[/cyan]
  /analyze <message> - Analyze a message without sending it
  /model <name>      - Set model preference for next message

[cyan]Examples:[/cyan]
  Hello, how are you?
  Send an email to john@example.com about the meeting
  /analyze Create a todo list for my project
  /models
        """
        console.print(Panel(help_text, title="📚 Help", border_style="blue"))
    
    def show_history(self):
        """Show conversation history"""
        if not self.conversation_history:
            console.print("📝 No conversation history")
            return
        
        console.print(f"📝 Conversation History ({len(self.conversation_history)} messages):")
        for i, entry in enumerate(self.conversation_history, 1):
            console.print(f"\n[bold]{i}.[/bold] [blue]You:[/blue] {entry['user']}")
            console.print(f"    [green]Agent:[/green] {entry['agent'][:100]}{'...' if len(entry['agent']) > 100 else ''}")

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="CLI client for Intelligent Mailbox Agent")
    parser.add_argument("--url", default=DEFAULT_BASE_URL, help="Agent HTTP endpoint URL")
    parser.add_argument("--message", "-m", help="Send a single message and exit")
    parser.add_argument("--analyze", "-a", help="Analyze a message and exit")
    parser.add_argument("--models", action="store_true", help="Show available models and exit")
    parser.add_argument("--config", action="store_true", help="Show agent configuration and exit")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    
    args = parser.parse_args()
    
    cli = MailboxAgentCLI(args.url)
    
    # Test connection
    if not await cli.test_connection():
        console.print("❌ Cannot connect to agent. Make sure it's running.")
        sys.exit(1)
    
    # Handle single commands
    if args.message:
        result = await cli.send_message(args.message)
        cli.display_response(result)
    elif args.analyze:
        analysis = await cli.analyze_request(args.analyze)
        cli.display_analysis(analysis)
    elif args.models:
        models = await cli.get_models()
        cli.display_models(models)
    elif args.config:
        config = await cli.get_agent_config()
        cli.display_agent_config(config)
    else:
        # Default to interactive mode
        await cli.interactive_mode()

if __name__ == "__main__":
    asyncio.run(main())
