# Vocal Agent Frontend

A simple Flask-based web interface for the Vocal Agent voice-driven AI assistant.

## Features

- **Hello World Interface**: Clean, modern web interface for testing
- **API Testing**: Built-in buttons to test backend connectivity
- **Voice Command Simulation**: Test voice command processing
- **Health Check Endpoint**: Monitor frontend status

## Quick Start

1. **Install Dependencies**:

   ```bash
   pip install flask>=3.0.0
   ```

2. **Run the Frontend**:

   ```bash
   python frontend/app.py
   ```

3. **Access the Interface**:
   Open your browser to: http://127.0.0.1:5000

## API Endpoints

- `GET /` - Main interface (Hello World page)
- `GET /api/health` - Health check endpoint
- `POST /api/process_voice` - Process voice commands (placeholder)

## Next Steps

- [ ] Connect to `vocal_core_agent.py` backend
- [ ] Implement real voice recording functionality
- [ ] Add authentication and session management
- [ ] Create dedicated pages for each agent (Calendar, Email, Notes, Spotify)

## Project Structure

```
frontend/
├── app.py              # Main Flask application
├── templates/
│   └── index.html      # Main interface template
└── static/             # Static assets (CSS, JS, images)
```
