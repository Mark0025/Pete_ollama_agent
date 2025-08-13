#!/bin/bash

# PeteOllama Agent Startup Script for RunPod
# Robust version with crash prevention

set -e

# Function to handle errors gracefully
handle_error() {
    echo "❌ Error occurred on line $1"
    echo "🔄 Continuing with startup..."
}
trap 'handle_error $LINENO' ERR

# Create log file for debugging
LOG_FILE="/root/.ollama/startup.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "🚀 Starting PeteOllama Agent Setup - $(date)"
echo "📝 Logging to: $LOG_FILE"

# Function to check if we're in a restart loop
check_restart_loop() {
    local restart_count=0
    if [ -f "/root/.ollama/restart_count" ]; then
        restart_count=$(cat /root/.ollama/restart_count)
    fi
    
    if [ "$restart_count" -gt 5 ]; then
        echo "🚨 Too many restarts detected. Starting minimal mode..."
        echo "0" > /root/.ollama/restart_count
        return 1
    fi
    
    echo $((restart_count + 1)) > /root/.ollama/restart_count
    return 0
}

# Function to cleanup on exit
cleanup() {
    echo "🧹 Cleaning up on exit..."
    pkill ollama 2>/dev/null || true
    pkill -f uvicorn 2>/dev/null || true
    pkill -f "src/main.py" 2>/dev/null || true
}

trap cleanup EXIT

# Memory and disk optimization
echo "🧹 Clearing cache and optimizing memory..."
rm -rf /root/.cache/uv 2>/dev/null || true
rm -rf /root/.cache/pip 2>/dev/null || true
rm -rf /tmp/* 2>/dev/null || true

# Move cache to persistent volume
mkdir -p /root/.ollama/cache
if [ ! -L /root/.cache ]; then
    ln -sf /root/.ollama/cache /root/.cache
fi

# Set environment variables
export PATH="$PATH:/usr/local/bin"
export OLLAMA_HOST=0.0.0.0
export OLLAMA_ORIGINS=*
export OLLAMA_MODELS=/root/.ollama/models
export OLLAMA_BASE_URL=http://localhost:11434
export DEFAULT_MODEL=peteollama:property-manager-v0.0.1
export PROXY_PORT=8001

# Create necessary directories
mkdir -p /root/.ollama/models
mkdir -p /root/.ollama/cache

# Install system dependencies
echo "📦 Installing system dependencies..."
apt-get update -qq || echo "⚠️ apt-get update failed, continuing..."
apt-get install -y tree xsel curl git || echo "⚠️ Some packages failed to install, continuing..."

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv..."
    curl -Ls https://astral.sh/uv/install.sh | sh
    
    # Add uv to PATH
    export PATH="$HOME/.local/bin:$PATH"
    
    # Verify uv installation
    if ! command -v uv &> /dev/null; then
        echo "❌ uv installation failed"
        exit 1
    fi
    
    echo "✅ uv installed successfully"
fi

# Ensure uv is in PATH
export PATH="$HOME/.local/bin:$PATH"

# Change to repo directory and pull latest changes
echo "🔄 Checking for latest code updates..."
cd /root/.ollama/app/Pete_ollama_agent || {
    echo "❌ Failed to change to repo directory"
    exit 1
}

if [ -d ".git" ]; then
    echo "📡 Pulling latest changes from GitHub..."
    git fetch origin main || echo "⚠️ git fetch failed"
    git reset --hard origin/main --quiet || echo "⚠️ git reset failed"
    git clean -fd --quiet || echo "⚠️ git clean failed"
    echo "✅ Updated to latest version"
else
    echo "⚠️ Not a git repository - skipping auto-update"
fi

# Kill any existing processes
echo "🔄 Stopping existing processes..."
pkill ollama 2>/dev/null || echo "⚠️ No ollama processes to stop"
pkill -f uvicorn 2>/dev/null || echo "⚠️ No uvicorn processes to stop"
pkill -f "src/main.py" 2>/dev/null || echo "⚠️ No main.py processes to stop"
echo "✅ Process cleanup completed"
sleep 3

# Install Ollama
echo "🤖 Installing Ollama..."
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.com/install.sh | sh || {
        echo "❌ Ollama installation failed"
        exit 1
    }
fi

# Start Ollama with error handling
echo "🚀 Starting Ollama..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to start with timeout
echo "⏳ Waiting for Ollama to start..."
for i in {1..30}; do
    if curl -s http://localhost:11434/api/version >/dev/null 2>&1; then
        echo "✅ Ollama started successfully"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Ollama failed to start within 30 seconds"
        exit 1
    fi
    sleep 1
done

# Pull base models with error handling
echo "📥 Checking for base models..."
if ! ollama list | grep -q "llama3:latest"; then
    echo "📥 Pulling llama3:latest..."
    ollama pull llama3:latest || echo "⚠️ Failed to pull llama3:latest"
fi

# Only pull qwen3:30b if we have enough memory and not in restart loop
if check_restart_loop; then
    MEMORY_AVAILABLE=$(free -g | awk 'NR==2{print $2}')
    if [ "$MEMORY_AVAILABLE" -gt 20 ]; then
        if ! ollama list | grep -q "qwen3:30b"; then
            echo "📥 Pulling qwen3:30b (sufficient memory available)..."
            ollama pull qwen3:30b || echo "⚠️ Failed to pull qwen3:30b"
        fi
    else
        echo "⚠️ Skipping qwen3:30b - insufficient memory (${MEMORY_AVAILABLE}GB available)"
    fi
else
    echo "⚠️ Skipping qwen3:30b - restart loop detected"
fi

# Create custom model if not exists
echo "🔧 Setting up custom model..."
if ! ollama list | grep -q "peteollama:property-manager-v0.0.1"; then
    echo "📥 Creating peteollama:property-manager-v0.0.1..."
    if [ -f "models/Modelfile.enhanced" ]; then
        ollama create peteollama:property-manager-v0.0.1 -f models/Modelfile.enhanced || echo "⚠️ Failed to create custom model"
    else
        echo "❌ Modelfile.enhanced not found"
    fi
fi

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
if command -v uv &> /dev/null; then
    echo "📦 Using uv to install dependencies..."
    uv sync || {
        echo "❌ uv sync failed - this is required for the application to work"
        exit 1
    }
else
    echo "❌ uv not found - this is required for the application to work"
    exit 1
fi

# Create database
echo "🗄️ Setting up database..."
# Copy pete.db to current directory if it exists in /app
if [ -f "/app/pete.db" ]; then
    cp /app/pete.db . || echo "⚠️ Failed to copy database"
fi
uv run python src/virtual_jamie_extractor.py || echo "⚠️ Database setup failed"

# Start the application in background
echo "🌐 Starting PeteOllama application..."
uv run python src/main.py &
APP_PID=$!

# Wait for app to start
sleep 5

# Verify app is running
if ! ps -p $APP_PID > /dev/null 2>&1; then
    echo "❌ Main app failed to start"
    exit 1
fi

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

# Reset restart count on successful startup
echo "0" > /workspace/restart_count

# Memory monitoring and management
echo "🔄 Starting memory monitoring..."
while true; do
    # Check memory usage
    MEMORY_USAGE=$(free -g | awk 'NR==2{printf "%.0f", $3/$2 * 100}')
    
    if [ "$MEMORY_USAGE" -gt 85 ]; then
        echo "⚠️ High memory usage: ${MEMORY_USAGE}% - unloading large models..."
        
        # Unload qwen3:30b if it's loaded
        if ollama list | grep -q "qwen3:30b"; then
            echo "🗑️ Unloading qwen3:30b to free memory..."
            ollama rm qwen3:30b 2>/dev/null || true
        fi
        
        # Clear cache
        rm -rf /tmp/* 2>/dev/null || true
        rm -rf /root/.cache/uv 2>/dev/null || true
        
        echo "✅ Memory freed - continuing..."
    fi
    
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
