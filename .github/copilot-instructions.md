<!-- .github/copilot-instructions.md
     Purpose: Give AI coding agents the minimal, actionable repo-specific knowledge
     needed to be productive. This file is intentionally short and focused.
-->

# Copilot / AI Agent Instructions (short)

This repository contains the **Vocal Agent** project — a voice-driven AI assistant that
uses **Fetch.ai uAgents** for autonomous task execution and **Google Gemini** for reasoning.
It captures voice input via **ElevenLabs Speech-to-Text API**, interprets user intent using
Gemini, and executes actions (e.g., scheduling events, sending emails, creating notes).

The project is composed of:

- A **Python-based front-end UI** Flask GUI
- A **Python back-end** containing multiple uAgents:
  - `vocal_core_agent`: Which uses Fetch.ai's interprets user intent and delegates tasks
  - `calendar_agent`, `email_agent`, etc.: execute app-specific actions

## Frontend to Backend Workflow

```
User (voice)
  ↓
Speech-to-Text (Whisper)
  ↓
Vocal Core Agent
  - Uses ASI:One for intent parsing
  - Decides this is a "create_event" task
  ↓
Sends CreateEventMessage to calendar_agent
  ↓
calendar_agent
  - Integrates with Google Calendar API
  - Creates the event
  - Sends confirmation back
  ↓
Vocal Core → Flask UI → "Meeting created with Ben at 8 PM."
```

---

## Quick reconnaissance (run these in order)

1. Check for language/manifests (look for):

   - `pyproject.toml`, `requirements.txt` → Python project manifests
   - `.env`, `.env.example` → environment configuration
   - `src/`, `frontend/`, or `backend/` folders for core modules
   - `uagents/`, `src/agents/`, `src/ui/` → main agent and UI directories

2. Install dependencies and run backend:

   ```bash
   python3 -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   python -m uagents run src/agents/vocal_core_agent.py
   ```

3. Run the frontend Flask GUI:

   ```bash
   # Activate virtual environment first
   source .venv/bin/activate

   # Start the Flask frontend
   python frontend/app.py
   ```

   Access at: http://127.0.0.1:5000

4. Identify runtime entrypoints and services:

- **frontend/app.py** → Flask web interface (start for UI testing)

- **src/agents/vocal_core_agent.py** → main orchestrator (start this before others)

- **src/agents/calendar_agent.py, src/agents/email_agent.py** → service-specific task executors

- **tests/agents/** → sample message flow and uAgent communication tests

- **tests/integration/** → end-to-end voice-to-action test flows
