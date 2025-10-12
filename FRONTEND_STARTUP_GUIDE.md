# Vocal Agent Frontend Startup Guide

## 🖥️ Desktop App (Recommended)

The default startup creates a standalone desktop application window.

### Quick Start:
```bash
./start_frontend.sh
```

### Manual Start:
```bash
cd frontend
source ../venv/bin/activate
python app.py
```

**Features:**
- ✅ Standalone desktop window
- ✅ No browser required
- ✅ Native app experience
- ✅ Automatic window management

---

## 🌐 Web Interface (Browser)

For users who prefer to use their browser instead of a desktop app.

### Quick Start:
```bash
./start_frontend_web.sh
```

### Manual Start:
```bash
cd frontend
source ../venv/bin/activate
FLASK_APP=app.py FLASK_ENV=development python -m flask run --host=127.0.0.1 --port=5002
```

Then open: http://127.0.0.1:5002

**Features:**
- ✅ Browser-based interface
- ✅ No desktop window
- ✅ Works with any browser
- ✅ Can be accessed remotely

---

## 🎵 Spotify Integration

Both versions support the enhanced Spotify authentication:

1. **Click "Integrate with apps"** button
2. **Click "Spotify"** 
3. **Watch the beautiful success animation**
4. **See the "Connected" status indicator**

### Features:
- ✅ Real Spotify API integration
- ✅ Beautiful success animations
- ✅ Persistent connection status
- ✅ Enhanced UI feedback

---

## 🔧 Troubleshooting

### Port Conflicts:
If you get "Address already in use" errors:
```bash
pkill -f "python app.py"
pkill -f "flask run"
```

### FlaskUI Issues:
If the desktop app has logging errors, use the web version:
```bash
./start_frontend_web.sh
```

### Environment Variables:
Make sure your `.env` file contains:
```bash
ASI_ONE_API_KEY=your_key_here
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

---

## 🚀 Quick Commands

| Command | Description |
|---------|-------------|
| `./start_frontend.sh` | Start desktop app |
| `./start_frontend_web.sh` | Start web interface |
| `./run_spotify_agent_with_env.sh` | Start Spotify agent |

---

## 📱 Access URLs

- **Desktop App**: Opens automatically
- **Web Interface**: http://127.0.0.1:5002
- **Spotify Agent**: http://localhost:8005
- **Health Check**: http://localhost:5002/api/health
