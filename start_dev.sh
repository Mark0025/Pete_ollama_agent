#!/bin/bash

# Development Server with Auto-Reload
# Uses uvicorn --reload for automatic restarts

echo "🚀 Starting Development Server with Auto-Reload"
echo "================================================"
echo "📁 Server will restart automatically when files change"
echo "🛑 Press Ctrl+C to stop"
echo "================================================"

# Kill any existing server on port 8000
echo "🔍 Checking for existing server on port 8000..."
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "🔄 Found existing server on port 8000, killing it..."
    lsof -ti:8000 | xargs kill -9
    sleep 2
    echo "✅ Existing server killed"
else
    echo "✅ No existing server found on port 8000"
fi

# Load environment variables from .env file
set -a  # Export all variables
source .env
set +a  # Stop exporting

# Change to src directory
cd src

# Start server with auto-reload using uv venv
echo "🔧 Starting server with uvicorn --reload..."
uv run uvicorn main_app:app --host 0.0.0.0 --port 8000 --reload --reload-dir . --reload-dir ../
