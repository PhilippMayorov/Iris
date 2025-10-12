#!/bin/bash
# Script to start the frontend without FlaskUI to avoid logging issues

echo "🚀 Starting Vocal Agent Frontend..."
echo "📁 Loading environment variables from .env file..."

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Environment variables loaded from .env file"
else
    echo "❌ .env file not found!"
    echo "Please make sure .env file exists in the current directory"
    exit 1
fi

# Activate virtual environment
echo "🐍 Activating virtual environment..."
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️ Virtual environment not found, continuing without it..."
fi

echo "🌐 Starting Vocal Agent Web Interface..."
echo "📱 Open your browser and go to: http://127.0.0.1:5001"
echo ""

# Change to frontend directory and start the desktop app
cd frontend
python app.py
