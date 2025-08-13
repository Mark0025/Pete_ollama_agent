#!/bin/bash
# PeteOllama V1 - RunPod Startup Script
# Pulls latest code and starts the app directly (no Docker)

echo "🚀 PeteOllama V1 - RunPod Quick Startup"
echo "========================================"
echo ""

# Function to check network connectivity
check_network() {
    echo "🔍 Checking network connectivity..."
    
    # Test basic connectivity
    if curl -s --connect-timeout 5 https://httpbin.org/ip >/dev/null 2>&1; then
        echo "✅ Basic internet connectivity working"
        return 0
    else
        echo "❌ Basic internet connectivity failed"
        return 1
    fi
}

# Function to test GitHub access
test_github() {
    echo "🐙 Testing GitHub access..."
    
    if curl -s --connect-timeout 10 https://github.com >/dev/null 2>&1; then
        echo "✅ GitHub access working"
        return 0
    else
        echo "❌ GitHub access failed"
        return 1
    fi
}

# Function to fix network issues
fix_network() {
    echo "🔧 Attempting to fix network issues..."
    
    # Try to fix DNS
    if [ -f "fix_network.sh" ]; then
        echo "🔄 Running network fix script..."
        bash fix_network.sh
    else
        echo "⚠️ Network fix script not found, trying manual DNS fix..."
        
        # Backup and try Google DNS
        cp /etc/resolv.conf /etc/resolv.conf.backup 2>/dev/null || true
        echo "nameserver 8.8.8.8" > /etc/resolv.conf
        echo "nameserver 8.8.4.4" >> /etc/resolv.conf
        
        # Test if it worked
        if check_network; then
            echo "✅ Manual DNS fix successful"
            return 0
        else
            echo "❌ Manual DNS fix failed, restoring original"
            cp /etc/resolv.conf.backup /etc/resolv.conf 2>/dev/null || true
            return 1
        fi
    fi
}

# Function to start with existing code
start_existing() {
    echo "📁 Starting with existing local code..."
    
    # Check if we have the main application
    if [ -f "src/main.py" ]; then
        echo "✅ Found main.py, starting application..."
        
        # Try to install dependencies if possible
        if command -v uv &> /dev/null; then
            echo "📦 Installing dependencies with uv..."
            uv sync 2>/dev/null || echo "⚠️ uv sync failed, continuing..."
        else
            echo "⚠️ uv not available, trying pip..."
            pip install -r requirements.txt 2>/dev/null || echo "⚠️ pip install failed, continuing..."
        fi
        
        # Start the app
        echo "🌐 Starting PeteOllama..."
        if command -v uv &> /dev/null; then
            uv run python src/main.py
        else
            python3 src/main.py
        fi
    else
        echo "❌ main.py not found in src directory"
        echo "💡 Check your file structure or restart the pod"
        exit 1
    fi
}

# Main execution
echo "🔍 Starting network diagnostics..."

# Check network connectivity
if check_network; then
    echo "✅ Network is working!"
    
    # Test GitHub access
    if test_github; then
        echo "✅ GitHub access confirmed!"
        
        # Pull latest changes from GitHub
        echo "📡 Pulling latest code from GitHub..."
        if [ -d ".git" ]; then
            git pull origin main
            echo "✅ Code updated to latest version"
        else
            echo "⚠️ Not a git repository - using existing code"
        fi
        
        # Install/update dependencies
        echo "📦 Installing Python dependencies..."
        if command -v uv &> /dev/null; then
            uv sync
        else
            echo "⚠️ uv not available, trying pip..."
            pip install -r requirements.txt
        fi
        
        # Start the app
        echo "🌐 Starting PeteOllama..."
        if command -v uv &> /dev/null; then
            uv run python src/main.py
        else
            python3 src/main.py
        fi
        
    else
        echo "⚠️ GitHub access failed but basic connectivity works"
        echo "🔧 This might be a firewall issue"
        echo "💡 Starting with existing code..."
        start_existing
    fi
    
else
    echo "❌ Network connectivity issues detected"
    
    # Try to fix network
    if fix_network; then
        echo "✅ Network fixed! Retrying GitHub access..."
        
        if test_github; then
            echo "✅ GitHub access restored! Pulling latest code..."
            git pull origin main
            echo "📦 Installing dependencies..."
            uv sync
            echo "🌐 Starting PeteOllama..."
            uv run python src/main.py
        else
            echo "⚠️ GitHub still blocked, using existing code..."
            start_existing
        fi
        
    else
        echo "❌ Could not fix network issues"
        echo "💡 Starting with existing local code as fallback..."
        start_existing
    fi
fi
