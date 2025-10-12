#!/bin/bash
# Startup script for ASI One Chat with automatic environment loading

echo "🚀 Starting ASI One Chat..."
echo "📁 Loading environment variables from .env file..."

# Load environment variables from .env file
export $(cat .env | grep -v '^#' | xargs)

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Check if API key is loaded
if [ -n "$ASI_ONE_API_KEY" ]; then
    echo "✅ API key loaded successfully"
    echo "🔑 API key starts with: ${ASI_ONE_API_KEY:0:10}..."
else
    echo "❌ API key not found in .env file"
    echo "Please make sure ASI_ONE_API_KEY is set in your .env file"
    exit 1
fi

echo "🤖 Starting chat application..."
echo ""

# Start the chat application
python chat.py
