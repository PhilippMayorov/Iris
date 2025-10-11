"""
Vocal Agent - Multi-Agent System

This package contains the backend agent system for the Vocal Agent project.
It includes specialized agents for different tasks coordinated by a central orchestrator.

Agents:
- vocal_core_agent: Central orchestrator and intent recognition
- calendar_agent: Google Calendar integration
- email_agent: Gmail integration  
- notes_agent: Notes creation and management
- spotify_agent: Spotify music control

Usage:
    python src/agents/vocal_core_agent.py  # Start main orchestrator
    python src/agents/calendar_agent.py   # Start calendar service
    python src/agents/email_agent.py      # Start email service
    python src/agents/notes_agent.py      # Start notes service
    python src/agents/spotify_agent.py    # Start music service
"""

__version__ = "0.1.0"
__author__ = "Vocal Agent Team"
__description__ = "Multi-agent system for voice-driven task automation"