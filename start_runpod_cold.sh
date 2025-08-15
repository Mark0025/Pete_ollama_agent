#!/bin/bash

# =============================================================================
# PeteOllama Agent - Bulletproof Startup Script
# =============================================================================
# This script will NEVER fail silently and will show ALL errors
# It will keep running until completion or explicit failure
# =============================================================================

# Enable strict error handling
set -euo pipefail
trap 'error_handler $? $LINENO $BASH_LINENO "$BASH_COMMAND" $(printf "::%s" ${FUNCNAME[@]:-})' ERR

# Global variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/root/.ollama/startup.log"
ERROR_LOG="/root/.ollama/startup_errors.log"
STARTUP_PID=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# ERROR HANDLING FUNCTIONS
# =============================================================================

error_handler() {
    local exit_code=$1
    local line_no=$2
    local bash_lineno=$3
    local last_command="$4"
    local func_stack="$5"
    
    echo -e "${RED}❌ CRITICAL ERROR OCCURRED!${NC}" | tee -a "$LOG_FILE" "$ERROR_LOG"
    echo -e "${RED}Exit Code: $exit_code${NC}" | tee -a "$LOG_FILE" "$ERROR_LOG"
    echo -e "${RED}Line Number: $line_no${NC}" | tee -a "$LOG_FILE" "$ERROR_LOG"
    echo -e "${RED}Command: $last_command${NC}" | tee -a "$LOG_FILE" "$ERROR_LOG"
    echo -e "${RED}Function Stack: $func_stack${NC}" | tee -a "$LOG_FILE" "$ERROR_LOG"
    echo -e "${RED}Timestamp: $(date)${NC}" | tee -a "$LOG_FILE" "$ERROR_LOG"
    
    # Show current status
    echo -e "${YELLOW}📊 Current Status:${NC}" | tee -a "$LOG_FILE" "$ERROR_LOG"
    echo -e "${YELLOW}Working Directory: $(pwd)${NC}" | tee -a "$LOG_FILE" "$ERROR_LOG"
    echo -e "${YELLOW}Available Disk Space:${NC}" | tee -a "$LOG_FILE" "$ERROR_LOG"
    df -h | tee -a "$LOG_FILE" "$ERROR_LOG"
    echo -e "${YELLOW}Memory Usage:${NC}" | tee -a "$LOG_FILE" "$ERROR_LOG"
    free -h | tee -a "$LOG_FILE" "$ERROR_LOG"
    
    # Show process status
    echo -e "${YELLOW}Running Processes:${NC}" | tee -a "$LOG_FILE" "$ERROR_LOG"
    ps aux | grep -E "(ollama|python|uv)" | tee -a "$LOG_FILE" "$ERROR_LOG"
    
    echo -e "${RED}❌ SCRIPT FAILED! Check logs above for details.${NC}" | tee -a "$LOG_FILE" "$ERROR_LOG"
    echo -e "${RED}Logs saved to: $LOG_FILE and $ERROR_LOG${NC}" | tee -a "$LOG_FILE" "$ERROR_LOG"
    
    # Keep the terminal open - don't exit
    echo -e "${YELLOW}Press Enter to continue or Ctrl+C to exit...${NC}"
    read -r
    
    # Don't exit - let user decide what to do
    return $exit_code
}

# Function to log with timestamps
log() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[$timestamp] $message" | tee -a "$LOG_FILE"
}

# Function to check command success
check_success() {
    local exit_code=$1
    local command_name="$2"
    local error_message="$3"
    
    if [ $exit_code -ne 0 ]; then
        echo -e "${RED}❌ $command_name FAILED!${NC}" | tee -a "$LOG_FILE" "$ERROR_LOG"
        echo -e "${RED}$error_message${NC}" | tee -a "$LOG_FILE" "$ERROR_LOG"
        echo -e "${RED}Exit Code: $exit_code${NC}" | tee -a "$LOG_FILE" "$ERROR_LOG"
        echo -e "${YELLOW}Continuing anyway...${NC}" | tee -a "$LOG_FILE" "$ERROR_LOG"
        return 1
    else
        echo -e "${GREEN}✅ $command_name completed successfully${NC}" | tee -a "$LOG_FILE"
        return 0
    fi
}

# Function to wait for service with timeout
wait_for_service() {
    local service_name="$1"
    local service_url="$2"
    local max_attempts="${3:-30}"
    local delay="${4:-2}"
    
    log "⏳ Waiting for $service_name to be ready..."
    
    for i in $(seq 1 $max_attempts); do
        if curl -s "$service_url" >/dev/null 2>&1; then
            log "✅ $service_name is ready!"
            return 0
        fi
        
        if [ $i -eq $max_attempts ]; then
            log "⚠️ Timeout waiting for $service_name after ${max_attempts} attempts"
            return 1
        fi
        
        log "⏳ Waiting for $service_name... ($i/$max_attempts)"
        sleep $delay
    done
}

# =============================================================================
# MAIN STARTUP SEQUENCE
# =============================================================================

main() {
    log "🚀 Starting PeteOllama Agent Setup - $(date)"
    log "📝 Logging to: $LOG_FILE"
    log "🔍 Script directory: $SCRIPT_DIR"
    
    # Create log directories
    mkdir -p "$(dirname "$LOG_FILE")"
    mkdir -p "$(dirname "$ERROR_LOG")"
    
    # Clear previous logs
    > "$LOG_FILE"
    > "$ERROR_LOG"
    
    # Log system info
    log "📊 System Information:"
    log "OS: $(uname -a)"
    log "Memory: $(free -h | grep Mem | awk '{print $2}')"
    log "Disk: $(df -h / | tail -1 | awk '{print $4}') available"
    
    # Step 1: Check and fix network connectivity
    log "🔍 Checking network connectivity..."
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        log "✅ Network connectivity confirmed"
    else
        log "❌ Network connectivity failed - attempting to fix..."
        
        # Try to fix DNS issues
        if [ -f "/etc/resolv.conf" ]; then
            log "🔧 Fixing DNS configuration..."
            cp /etc/resolv.conf /etc/resolv.conf.backup 2>/dev/null || true
            echo "nameserver 8.8.8.8" > /etc/resolv.conf
            echo "nameserver 8.8.4.4" >> /etc/resolv.conf
            echo "nameserver 1.1.1.1" >> /etc/resolv.conf
            
            # Test if DNS fix worked
            if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
                log "✅ DNS fix successful - network now working"
            else
                log "⚠️ DNS fix failed - trying alternative DNS"
                echo "nameserver 208.67.222.222" > /etc/resolv.conf
                echo "nameserver 208.67.220.220" >> /etc/resolv.conf
                
                if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
                    log "✅ Alternative DNS fix successful"
                else
                    log "❌ Network connectivity still failed - continuing anyway"
                fi
            fi
        else
            log "⚠️ No resolv.conf found - continuing anyway"
        fi
    fi
    
    # Step 2: Clear cache and optimize memory
    log "🧹 Clearing cache and optimizing memory..."
    sync
    echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || log "⚠️ Could not clear cache (normal if not root)"
    
    # Step 3: Install system dependencies
    echo "📦 Installing system dependencies..."
    apt-get update -qq || echo "⚠️ apt-get update failed, continuing..."
    apt-get install -y tree xsel curl git || echo "⚠️ Some packages failed to install, continuing..."
    
    # Install ODBC drivers for SQL Server database connection
    echo "🗄️ Installing ODBC drivers for database connection..."
    apt-get install -y unixodbc-dev unixodbc || echo "⚠️ ODBC installation failed, continuing..."
    
    # Install additional database dependencies
    echo "📊 Installing database connection dependencies..."
    apt-get install -y python3-dev gcc g++ || echo "⚠️ Some build dependencies failed to install, continuing..."
    
    # Step 4: Check for uv (prefer existing virtual environment)
    log "📦 Checking uv installation..."
    
    # First, try to use existing uv from virtual environment
    if [ -f ".venv/bin/uv" ]; then
        log "🔧 Found uv in virtual environment - using it"
        export PATH="$(pwd)/.venv/bin:$PATH"
        log "✅ uv is available from virtual environment at: $(which uv)"
    elif command -v uv &> /dev/null; then
        log "✅ uv is available in PATH at: $(which uv)"
    else
        log "📥 Installing uv using pip..."
        if command -v pip3 &> /dev/null; then
            pip3 install uv || {
                log "❌ pip3 installation of uv failed"
                return 1
            }
            export PATH="$HOME/.local/bin:$PATH"
        elif command -v pip &> /dev/null; then
            pip install uv || {
                log "❌ pip installation of uv failed"
                return 1
            }
            export PATH="$HOME/.local/bin:$PATH"
        else
            log "❌ No pip available - cannot install uv"
            return 1
        fi
        
        # Verify uv is now available
        if ! command -v uv &> /dev/null; then
            log "❌ uv still not available after pip installation"
            return 1
        fi
    fi
    
    log "✅ uv is available at: $(which uv)"
    
    # Step 5: Update code from GitHub
    log "🔄 Checking for latest code updates..."
    cd "$SCRIPT_DIR" || {
        log "❌ Failed to change to script directory"
        return 1
    }
    
    if [ -d ".git" ]; then
        log "📡 Pulling latest changes from GitHub..."
        git fetch origin main || log "⚠️ git fetch failed"
        git reset --hard origin/main --quiet || log "⚠️ git reset failed"
        git clean -fd --quiet || log "⚠️ git clean failed"
        log "✅ Updated to latest version"
    else
        log "⚠️ Not a git repository - using existing code"
    fi
    
    # Step 6: Stop existing processes
    log "🔄 Stopping existing processes..."
    pkill ollama 2>/dev/null || log "⚠️ No ollama processes to stop"
    pkill -f uvicorn 2>/dev/null || log "⚠️ No uvicorn processes to stop"
    pkill -f "src/main.py" 2>/dev/null || log "⚠️ No main.py processes to stop"
    log "✅ Process cleanup completed"
    sleep 3
    
    # Step 7: Install Ollama
    log "🤖 Installing Ollama..."
    if ! command -v ollama &> /dev/null; then
        log "📥 Installing Ollama..."
        curl -fsSL https://ollama.com/install.sh | sh || {
            log "❌ Ollama installation failed - this is critical!"
            return 1
        }
    fi
    
    # Step 8: Start Ollama
    log "🚀 Starting Ollama..."
    ollama serve &
    local OLLAMA_PID=$!
    log "✅ Ollama started with PID: $OLLAMA_PID"
    
    # Wait for Ollama to be ready
    if ! wait_for_service "Ollama" "http://localhost:11434/api/version" 30 1; then
        log "❌ Ollama failed to start within 30 seconds"
        return 1
    fi
    
    # Step 9: Pull base models
    log "📥 Checking for base models..."
    if ! ollama list | grep -q "llama3:latest"; then
        log "📥 Pulling llama3:latest..."
        ollama pull llama3:latest || log "⚠️ Failed to pull llama3:latest"
    fi
    
    # Step 10: Install Python dependencies
    log "🐍 Installing Python dependencies..."
    
    # Try to use uv from virtual environment if available
    if [ -f ".venv/bin/uv" ]; then
        log "🔧 Using uv from virtual environment"
        export PATH="$(pwd)/.venv/bin:$PATH"
    fi
    
    # Try to install dependencies
    if uv sync; then
        log "✅ Python dependencies installed successfully"
    else
        log "❌ Failed to install Python dependencies with uv"
        log "🔍 uv is required - no fallback available"
        return 1
    fi
    
    # Step 11: Set up database and extract real data
    log "🗄️ Setting up database and extracting real conversation data..."
    if [ -f "/app/pete.db" ]; then
        cp /app/pete.db . || log "⚠️ Failed to copy database"
    fi
    
    log "📊 Extracting real property management conversations from database..."
    uv run python src/virtual_jamie_extractor.py || {
        log "❌ Database extraction failed - this is critical for Jamie models!"
        return 1
    }
    
    # Step 12: Generate enhanced Modelfile from real data
    log "🔧 Generating Modelfile from real conversation data..."
    uv run python enhanced_model_trainer.py || {
        log "⚠️ Failed to generate enhanced Modelfile, using fallback"
    }
    
    # Step 13: Create custom models from real data
    log "🔧 Setting up custom models from real conversation data..."
    if [ -f "models/Modelfile.enhanced" ]; then
        local models=("peteollama:property-manager-v0.0.1" "peteollama:jamie-fixed" "peteollama:jamie-voice-complete")
        
        for model in "${models[@]}"; do
            if ! ollama list | grep -q "$model"; then
                log "📥 Creating $model from real data..."
                ollama create "$model" -f models/Modelfile.enhanced || {
                    log "❌ Failed to create $model - this is critical!"
                    return 1
                }
            else
                log "✅ $model already exists"
            fi
        done
        
        log "✅ All required models created successfully from real data"
    else
        log "❌ Modelfile.enhanced not found - cannot create custom models"
        return 1
    fi
    
    # Step 14: Wait for models to be fully loaded
    log "⏳ Waiting for models to be fully loaded..."
    local model_check_attempts=0
    local max_model_checks=60  # 2 minutes with 2-second intervals
    
    while [ $model_check_attempts -lt $max_model_checks ]; do
        if ollama list | grep -q "peteollama:property-manager-v0.0.1" && \
           ollama list | grep -q "peteollama:jamie-fixed" && \
           ollama list | grep -q "peteollama:jamie-voice-complete"; then
            log "✅ All Jamie models are loaded and ready!"
            break
        fi
        
        model_check_attempts=$((model_check_attempts + 1))
        if [ $model_check_attempts -eq $max_model_checks ]; then
            log "⚠️ Timeout waiting for models - starting app anyway"
            break
        fi
        
        log "⏳ Waiting for models... ($model_check_attempts/$max_model_checks)"
        sleep 2
    done
    
    # Step 15: Start the app
    log "🌐 Starting PeteOllama..."
    uv run python src/main.py &
    STARTUP_PID=$!
    log "✅ Main app started with PID: $STARTUP_PID"
    
    # Wait for app to start
    sleep 5
    
    # Verify app is running
    if ! ps -p $STARTUP_PID > /dev/null 2>&1; then
        log "❌ Main app failed to start"
        return 1
    fi
    
    # Step 16: Show final status
    log "📊 System Status:"
    log "=================="
    df -h /workspace | tee -a "$LOG_FILE"
    free -h | tee -a "$LOG_FILE"
    ollama list | tee -a "$LOG_FILE"
    
    log "✅ PeteOllama Agent is ready!"
    log "🌐 Frontend: http://localhost:8000"
    log "🔗 Proxy: http://localhost:8001"
    log "🤖 Ollama: http://localhost:11434"
    log "📝 Logs: $LOG_FILE"
    log "🚨 Error Logs: $ERROR_LOG"
    
    # Reset restart count on successful startup
    echo "0" > /workspace/restart_count 2>/dev/null || log "⚠️ Could not reset restart count"
    
    # Step 17: Memory monitoring loop
    log "🔄 Starting memory monitoring..."
    while true; do
        # Check memory usage
        local memory_usage=$(free -g | awk 'NR==2{printf "%.0f", $3/$2 * 100}')
        
        if [ "$memory_usage" -gt 85 ]; then
            log "⚠️ High memory usage: ${memory_usage}% - unloading large models..."
            
            # Unload qwen3:30b if it's loaded
            if ollama list | grep -q "qwen3:30b"; then
                log "🗑️ Unloading qwen3:30b to free memory..."
                ollama rm qwen3:30b 2>/dev/null || true
            fi
            
            # Clear cache
            rm -rf /tmp/* 2>/dev/null || true
            rm -rf /root/.cache/uv 2>/dev/null || true
            
            log "✅ Memory freed - continuing..."
        fi
        
        # Check if main app is still running
        if ! ps -p $STARTUP_PID > /dev/null 2>&1; then
            log "⚠️ Main app stopped, restarting..."
            uv run python src/main.py &
            STARTUP_PID=$!
        fi
        
        # Check if Ollama is still running
        if ! ps -p $OLLAMA_PID > /dev/null 2>&1; then
            log "⚠️ Ollama stopped, restarting..."
            ollama serve &
            OLLAMA_PID=$!
        fi
        
        sleep 30
    done
}

# =============================================================================
# SCRIPT EXECUTION
# =============================================================================

# Run main function and capture any errors
if main "$@"; then
    log "🎉 Startup completed successfully!"
else
    log "❌ Startup failed! Check error logs above."
    log "Press Enter to exit or Ctrl+C to force quit..."
    read -r
fi
