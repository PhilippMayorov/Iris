# Vocal Agent Frontend

A Flask-based desktop application for the Vocal Agent voice-driven AI assistant, featuring a native desktop GUI experience.

## Quick Start

1. **Install Dependencies**:

   ```bash
   pip install flask>=3.0.0 flaskwebgui>=1.1.7
   ```

2. **Run the Desktop App**:

   ```bash
   # Activate virtual environment
   source .venv/bin/activate

   # Launch desktop GUI
   python frontend/app.py
   ```

3. **Desktop Experience**:
   - 🚀 **Automatic Launch**: App opens in a dedicated desktop window
   - 📏 **Window Size**: 1200x800 pixels, resizable
   - 🔄 **Fallback**: If desktop mode fails, falls back to browser at http://127.0.0.1:5000

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
