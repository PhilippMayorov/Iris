# My First uAgent

This is a simple uAgent implementation using the Fetch.ai uAgents framework.

## Agent Details

- **Name**: alice
- **Type**: Local Agent
- **Purpose**: Basic demonstration of uAgent functionality

## Features

- Startup event handling
- Agent registration and communication
- Message model support
- Mailbox integration for Agentverse connectivity

## Files

- `my_first_agent.py` - Basic agent with startup handler
- `local_agent.py` - Local agent with message model
- `mailbox_agent.py` - Mailbox agent for Agentverse integration

## Usage

1. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

2. Run any of the agent scripts:
   ```bash
   python my_first_agent.py
   python local_agent.py
   python mailbox_agent.py
   ```

## Agent Address

Each agent will display its unique address when started. This address can be used for inter-agent communication.
