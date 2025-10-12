#!/bin/bash
# Script to run Gmail Agent with proper environment variable loading

echo "🚀 Starting Gmail Agent with environment variables..."
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

# Check if API key is loaded
if [ -n "$ASI_ONE_API_KEY" ]; then
    echo "✅ ASI:One API key loaded successfully"
    echo "🔑 API key starts with: ${ASI_ONE_API_KEY:0:10}..."
else
    echo "❌ ASI:One API key not found in .env file"
    echo "Please make sure ASI_ONE_API_KEY is set in your .env file"
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

echo "🤖 Starting Gmail Agent..."
echo ""

# Change to Gmail agent directory and run it
cd src/agents/new-agents/gmail_agent
python gmail_agent.py
