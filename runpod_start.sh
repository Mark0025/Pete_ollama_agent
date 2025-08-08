#!/bin/bash

# PeteOllama Agent Startup Script for RunPod
# Optimized for memory and disk space management

set -e

echo "🚀 Starting PeteOllama Agent Setup..."

# Memory and disk optimization
echo "🧹 Clearing cache and optimizing memory..."
rm -rf /root/.cache/uv 2>/dev/null || true
rm -rf /root/.cache/pip 2>/dev/null || true
rm -rf /tmp/* 2>/dev/null || true

# Move cache to persistent volume
mkdir -p /workspace/cache
if [ ! -L /root/.cache ]; then
    ln -sf /workspace/cache /root/.cache
fi

# Set environment variables
export PATH="$PATH:/usr/local/bin"
export OLLAMA_HOST=0.0.0.0
export OLLAMA_ORIGINS=*
export OLLAMA_MODELS=/workspace/.ollama/models
export OLLAMA_BASE_URL=http://localhost:11434
export DEFAULT_MODEL=peteollama:property-manager-v0.0.1
export PROXY_PORT=8001

# Create necessary directories
mkdir -p /workspace/.ollama/models
mkdir -p /workspace/cache

# Install system dependencies
echo "📦 Installing system dependencies..."
apt-get update -qq
apt-get install -y tree xsel curl git

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -Ls https://astral.sh/uv/install.sh | sh
fi

# Change to repo directory and pull latest changes
echo "🔄 Checking for latest code updates..."
cd /workspace/Pete_ollama_agent
if [ -d ".git" ]; then
    echo "📡 Pulling latest changes from GitHub..."
    git fetch origin main
    git reset --hard origin/main --quiet
    git clean -fd --quiet
    echo "✅ Updated to latest version"
else
    echo "⚠️ Not a git repository - skipping auto-update"
fi

# Kill any existing Ollama processes
echo "🔄 Stopping existing Ollama processes..."
pkill ollama 2>/dev/null || true
pkill -f uvicorn 2>/dev/null || true
pkill -f "src/main.py" 2>/dev/null || true
sleep 2

# Install Ollama
echo "🤖 Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama with optimized settings
echo "🚀 Starting Ollama..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to start
echo "⏳ Waiting for Ollama to start..."
sleep 10

# Pull base models (only if not already present)
echo "📥 Checking for base models..."
if ! ollama list | grep -q "llama3:latest"; then
    echo "📥 Pulling llama3:latest..."
    ollama pull llama3:latest
fi

if ! ollama list | grep -q "qwen3:30b"; then
    echo "📥 Pulling qwen3:30b..."
    ollama pull qwen3:30b
fi

# Create custom model if not exists
echo "🔧 Setting up custom model..."
if ! ollama list | grep -q "peteollama:property-manager-v0.0.1"; then
    echo "📥 Creating peteollama:property-manager-v0.0.1..."
    ollama create peteollama:property-manager-v0.0.1 -f models/Modelfile.enhanced
fi

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
uv sync

# Create database
echo "🗄️ Setting up database..."
python src/virtual_jamie_extractor.py

# Start the application in background
echo "🌐 Starting PeteOllama application..."
uv run python src/main.py &
APP_PID=$!

# Wait for services to start
sleep 5

# Show status
echo "📊 System Status:"
echo "=================="
df -h /workspace
echo ""
free -h
echo ""
ollama list
echo ""
echo "✅ PeteOllama Agent is ready!"
echo "🌐 Frontend: http://localhost:8000"
echo "🔗 Proxy: http://localhost:8001"
echo "🤖 Ollama: http://localhost:11434"
echo ""
echo "🔄 Services are running in background..."
echo "💡 To stop services: pkill -f 'python src/main.py' && pkill ollama"

# Keep the script alive without blocking
echo "🔄 Keeping startup script alive..."
while true; do
    # Check if main app is still running
    if ! ps -p $APP_PID > /dev/null 2>&1; then
        echo "⚠️ Main app stopped, restarting..."
        uv run python src/main.py &
        APP_PID=$!
    fi
    
    # Check if Ollama is still running
    if ! ps -p $OLLAMA_PID > /dev/null 2>&1; then
        echo "⚠️ Ollama stopped, restarting..."
        ollama serve &
        OLLAMA_PID=$!
    fi
    
    sleep 30
done
