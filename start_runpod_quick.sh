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
        
        # Install ODBC drivers for SQL Server database connection
        echo "🗄️ Installing ODBC drivers for database connection..."
        apt-get update -qq || echo "⚠️ apt-get update failed, continuing..."
        
        if ! dpkg -l | grep -q "unixodbc-dev"; then
            echo "📥 Installing unixodbc-dev..."
            apt-get install -y unixodbc-dev || echo "⚠️ Failed to install unixodbc-dev"
        else
            echo "✅ unixodbc-dev already installed"
        fi
        
        if ! dpkg -l | grep -q "unixodbc"; then
            echo "📥 Installing unixodbc..."
            apt-get install -y unixodbc || echo "⚠️ Failed to install unixodbc"
        else
            echo "✅ unixodbc already installed"
        fi
        
        # Install additional database dependencies
        echo "📊 Installing database connection dependencies..."
        if ! dpkg -l | grep -q "python3-dev"; then
            echo "📥 Installing python3-dev..."
            apt-get install -y python3-dev || echo "⚠️ Failed to install python3-dev"
        else
            echo "✅ python3-dev already installed"
        fi
        
        if ! dpkg -l | grep -q "gcc"; then
            echo "📥 Installing gcc..."
            apt-get install -y gcc g++ || echo "⚠️ Failed to install gcc"
        else
            echo "✅ gcc already installed"
        fi
        
        # Create database and extract real data FIRST
        echo "🗄️ Setting up database and extracting real conversation data..."
        # Copy pete.db to current directory if it exists in /app
        if [ -f "/app/pete.db" ]; then
            cp /app/pete.db . || echo "⚠️ Failed to copy database"
        fi
        
        # Run the database extractor to get real property management conversations
        echo "📊 Extracting real property management conversations from database..."
        if command -v uv &> /dev/null; then
            uv run python src/virtual_jamie_extractor.py || echo "⚠️ Database extraction failed"
        else
            python3 src/virtual_jamie_extractor.py || echo "⚠️ Database extraction failed"
        fi
        
        # Generate enhanced Modelfile from real data
        echo "🔧 Generating Modelfile from real conversation data..."
        if command -v uv &> /dev/null; then
            uv run python enhanced_model_trainer.py || echo "⚠️ Failed to generate enhanced Modelfile"
        else
            python3 enhanced_model_trainer.py || echo "⚠️ Failed to generate enhanced Modelfile"
        fi
        
        # Create latest Jamie model if Ollama is available
        if command -v ollama &> /dev/null; then
            echo "🔧 Creating latest Jamie model from real data..."
            if [ -f "models/Modelfile.enhanced" ]; then
                # Create property-manager model if not exists
                if ! ollama list | grep -q "peteollama:property-manager-v0.0.1"; then
                    echo "📥 Creating peteollama:property-manager-v0.0.1..."
                    ollama create peteollama:property-manager-v0.0.1 -f models/Modelfile.enhanced 2>/dev/null || echo "⚠️ Failed to create property-manager model"
                else
                    echo "✅ peteollama:property-manager-v0.0.1 already exists"
                fi
                
                # Create jamie-fixed model if not exists
                if ! ollama list | grep -q "peteollama:jamie-fixed"; then
                    echo "📥 Creating peteollama:jamie-fixed..."
                    ollama create peteollama:jamie-fixed -f models/Modelfile.enhanced 2>/dev/null || echo "⚠️ Failed to create jamie-fixed model"
                else
                    echo "✅ peteollama:jamie-fixed already exists"
                fi
                
                # Create jamie-voice-complete model if not exists
                if ! ollama list | grep -q "peteollama:jamie-voice-complete"; then
                    echo "📥 Creating peteollama:jamie-voice-complete..."
                    ollama create peteollama:jamie-voice-complete -f models/Modelfile.enhanced 2>/dev/null || echo "⚠️ Failed to create jamie-voice-complete model"
                else
                    echo "✅ peteollama:jamie-voice-complete already exists"
                fi
                
                echo "✅ All required models created successfully"
            else
                echo "❌ Modelfile.enhanced not found - cannot create models"
            fi
        fi
        
        # Wait for models to be fully loaded before starting app
        echo "⏳ Waiting for models to be fully loaded..."
        for i in {1..30}; do
            if ollama list | grep -q "peteollama:property-manager-v0.0.1" && \
               ollama list | grep -q "peteollama:jamie-fixed" && \
               ollama list | grep -q "peteollama:jamie-voice-complete"; then
                echo "✅ All Jamie models are loaded and ready!"
                break
            fi
            if [ $i -eq 30 ]; then
                echo "⚠️ Timeout waiting for models - starting app anyway"
                break
            fi
            echo "⏳ Waiting for models... (${i}/30)"
            sleep 2
        done
        
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
            
            # Install/update dependencies
            echo "📦 Installing Python dependencies..."
            if command -v uv &> /dev/null; then
                uv sync
            else
                echo "⚠️ uv not available, trying pip..."
                pip install -r requirements.txt
            fi
            
            # Install ODBC drivers for SQL Server database connection
            echo "🗄️ Installing ODBC drivers for database connection..."
            apt-get update -qq || echo "⚠️ apt-get update failed, continuing..."
            
            if ! dpkg -l | grep -q "unixodbc-dev"; then
                echo "📥 Installing unixodbc-dev..."
                apt-get install -y unixodbc-dev || echo "⚠️ Failed to install unixodbc-dev"
            else
                echo "✅ unixodbc-dev already installed"
            fi
            
            if ! dpkg -l | grep -q "unixodbc"; then
                echo "📥 Installing unixodbc..."
                apt-get install -y unixodbc || echo "⚠️ Failed to install unixodbc"
            else
                echo "✅ unixodbc already installed"
            fi
            
            # Install additional database dependencies
            echo "📊 Installing database connection dependencies..."
            if ! dpkg -l | grep -q "python3-dev"; then
                echo "📥 Installing python3-dev..."
                apt-get install -y python3-dev || echo "⚠️ Failed to install python3-dev"
            else
                echo "✅ python3-dev already installed"
            fi
            
            if ! dpkg -l | grep -q "gcc"; then
                echo "📥 Installing gcc..."
                apt-get install -y gcc g++ || echo "⚠️ Failed to install gcc"
            else
                echo "✅ gcc already installed"
            fi
            
            # Create database and extract real data FIRST
            echo "🗄️ Setting up database and extracting real conversation data..."
            # Copy pete.db to current directory if it exists in /app
            if [ -f "/app/pete.db" ]; then
                cp /app/pete.db . || echo "⚠️ Failed to copy database"
            fi
            
            # Run the database extractor to get real property management conversations
            echo "📊 Extracting real property management conversations from database..."
            if command -v uv &> /dev/null; then
                uv run python src/virtual_jamie_extractor.py || echo "⚠️ Database extraction failed"
            else
                python3 src/virtual_jamie_extractor.py || echo "⚠️ Database extraction failed"
            fi
            
            # Generate enhanced Modelfile from real data
            echo "🔧 Generating Modelfile from real conversation data..."
            if command -v uv &> /dev/null; then
                uv run python enhanced_model_trainer.py || echo "⚠️ Failed to generate enhanced Modelfile"
            else
                python3 enhanced_model_trainer.py || echo "⚠️ Failed to generate enhanced Modelfile"
            fi
            
            # Create latest Jamie model if Ollama is available
            if command -v ollama &> /dev/null; then
                echo "🔧 Creating latest Jamie model from real data..."
                if [ -f "models/Modelfile.enhanced" ]; then
                    # Create property-manager model if not exists
                    if ! ollama list | grep -q "peteollama:property-manager-v0.0.1"; then
                        echo "📥 Creating peteollama:property-manager-v0.0.1..."
                        ollama create peteollama:property-manager-v0.0.1 -f models/Modelfile.enhanced 2>/dev/null || echo "⚠️ Failed to create property-manager model"
                    else
                        echo "✅ peteollama:property-manager-v0.0.1 already exists"
                    fi
                    
                    # Create jamie-fixed model if not exists
                    if ! ollama list | grep -q "peteollama:jamie-fixed"; then
                        echo "📥 Creating peteollama:jamie-fixed..."
                        ollama create peteollama:jamie-fixed -f models/Modelfile.enhanced 2>/dev/null || echo "⚠️ Failed to create jamie-fixed model"
                    else
                        echo "✅ peteollama:jamie-fixed already exists"
                    fi
                    
                    # Create jamie-voice-complete model if not exists
                    if ! ollama list | grep -q "peteollama:jamie-voice-complete"; then
                        echo "📥 Creating peteollama:jamie-voice-complete..."
                        ollama create peteollama:jamie-voice-complete -f models/Modelfile.enhanced 2>/dev/null || echo "⚠️ Failed to create jamie-voice-complete model"
                    else
                        echo "✅ peteollama:jamie-voice-complete already exists"
                    fi
                    
                    echo "✅ All required models created successfully"
                else
                    echo "❌ Modelfile.enhanced not found - cannot create models"
                fi
            fi
            
            # Wait for models to be fully loaded before starting app
            echo "⏳ Waiting for models to be fully loaded..."
            for i in {1..30}; do
                if ollama list | grep -q "peteollama:property-manager-v0.0.1" && \
                   ollama list | grep -q "peteollama:jamie-fixed" && \
                   ollama list | grep -q "peteollama:jamie-voice-complete"; then
                    echo "✅ All Jamie models are loaded and ready!"
                    break
                fi
                if [ $i -eq 30 ]; then
                    echo "⚠️ Timeout waiting for models - starting app anyway"
                    break
                fi
                echo "⏳ Waiting for models... (${i}/30)"
                sleep 2
            done
            
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
