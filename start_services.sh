#!/bin/bash
# Startup script for PeteOllama on RunPod
# This script handles ollama service conflicts and starts the application

set -e

echo "🚀 Starting PeteOllama Services..."

# Change to the project directory
cd /root/.ollama/app/Pete_ollama_agent

# Check if ollama is already running
if pgrep -f "ollama serve" > /dev/null; then
    echo "⚠️  Ollama service already running, stopping it..."
    pkill -f "ollama serve" || true
    sleep 2
fi

# Start ollama service in background
echo "🔄 Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!
sleep 5

# Check if ollama started successfully
if ! pgrep -f "ollama serve" > /dev/null; then
    echo "❌ Failed to start Ollama service"
    exit 1
fi

echo "✅ Ollama service started (PID: $OLLAMA_PID)"

# Wait a bit more for ollama to be ready
sleep 3

# Check if ollama is responding
if ! ollama list > /dev/null 2>&1; then
    echo "⚠️  Ollama not responding yet, waiting..."
    sleep 5
fi

# Start the main application
echo "🔄 Starting PeteOllama application..."
cd src
uv run main.py

# If we get here, the application stopped
echo "🔄 Application stopped, cleaning up..."
kill $OLLAMA_PID 2>/dev/null || true
echo "✅ Cleanup complete"
