#!/bin/bash
# PeteOllama V1 - Start Script for RunPod (head-less version)
# Place this file at the repo root and set it as the container command, e.g.:
#   /bin/bash /workspace/ollama_agent/runpod_start.sh
set -euo pipefail

echo "📁 Ensuring /.ollama directory exists and is writeable..."
mkdir -p /.ollama/bin
chmod -R 755 /.ollama

echo "📍 Setting up local bin directory..."
export PATH="/.ollama/bin:$PATH"
if ! grep -qE "^export PATH=\"/.ollama/bin:\$PATH\"" ~/.bashrc 2>/dev/null; then
  echo 'export PATH="/.ollama/bin:$PATH"' >> ~/.bashrc
fi

echo "---------------------------"
echo "Ensure core build tools (curl, git, gpg, pip) exist on minimal images"
echo "---------------------------"
# Install curl git gpg python3-pip early because we need them for repo setup
for basepkg in curl git gpg python3-pip; do
  if ! command -v "$basepkg" >/dev/null 2>&1; then
    echo "📦 Installing $basepkg ...";
    DEBIAN_FRONTEND=noninteractive apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "$basepkg"
  fi
done
missing_pkgs="msodbcsql18 libodbc2 unixodbc unixodbc-dev"
if ! command -v curl >/dev/null 2>&1; then
  missing_pkgs="$missing_pkgs curl"
fi
if ! command -v git >/dev/null 2>&1; then
  missing_pkgs="$missing_pkgs git"
fi
# system pip is required only for the uv fallback
if ! command -v pip >/dev/null 2>&1 && ! command -v pip3 >/dev/null 2>&1; then
  missing_pkgs="$missing_pkgs python3-pip"
fi
if [ -n "$missing_pkgs" ]; then
  if [ "$(id -u)" = "0" ]; then
    echo "📦 Installing missing packages:$missing_pkgs"
    # Add Microsoft repository for ODBC driver
    echo "🔑 Adding Microsoft APT repo for msodbcsql18..."
    curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor --yes -o /usr/share/keyrings/microsoft.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/ubuntu/24.04/prod noble main" > /etc/apt/sources.list.d/mssql-release.list

    DEBIAN_FRONTEND=noninteractive apt-get update -y && ACCEPT_EULA=Y DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends $missing_pkgs
  else
    echo "❌ Missing required tools ($missing_pkgs) and not running as root." >&2
    exit 1
  fi
fi

echo "💡 Checking for uv..."
if ! command -v uv &> /dev/null; then
    echo "📦 uv not found. Installing uv into /.ollama/bin..."
    curl -Ls https://astral.sh/uv/install.sh | sh -s -- --bin-dir /.ollama/bin || pip install --break-system-packages -U uv
else
    echo "✅ uv is already installed."
fi

echo "🚀 Switching to app directory..."
# Change to repo directory (assumes this script is at repo root)
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR"

# ------------------------------------------------------------------
#  Auto-update repo from GitHub (git pull)
# ------------------------------------------------------------------
echo "🔄 Checking for latest code updates..."
if [ -d ".git" ]; then
  echo "📡 Pulling latest changes from GitHub..."
  git fetch origin main
  
  # Check if we're behind
  LOCAL=$(git rev-parse HEAD)
  REMOTE=$(git rev-parse origin/main)
  
  if [ "$LOCAL" != "$REMOTE" ]; then
    echo "🆙 New changes detected, pulling updates..."
    git reset --hard origin/main
    echo "✅ Updated to latest version: $(git log -1 --oneline)"
  else
    echo "✅ Already up to date with latest version"
  fi
else
  echo "⚠️  Not a git repository - skipping auto-update"
fi

# ------------------------------------------------------------------
#  Write .env file for extractor (if DB vars are present)
# ------------------------------------------------------------------
if [ -n "${PROD_DB_USERNAME:-}" ] && [ -n "${PROD_DB_PASSWORD:-}" ] && [ -n "${PROD_DB_HOST:-}" ] && [ -n "${PROD_DB_DATABASE:-}" ]; then
  ENV_FILE="$REPO_DIR/src/.env"
  cat > "$ENV_FILE" <<EOF
PROD_DB_USERNAME="${PROD_DB_USERNAME}"
PROD_DB_PASSWORD="${PROD_DB_PASSWORD}"
PROD_DB_HOST="${PROD_DB_HOST}"
PROD_DB_DATABASE="${PROD_DB_DATABASE}"
PROD_DB_DRIVER="${PROD_DB_DRIVER:-ODBC Driver 18 for SQL Server}"
EOF
  echo "✅ Wrote DB credentials to src/.env for extractor"
fi

# ------------------------------------------------------------------
#  Load variables from .env back into the environment (for scripts)
# ------------------------------------------------------------------
if [ -f "$REPO_DIR/src/.env" ]; then
  set -a  # export all sourced vars
  source "$REPO_DIR/src/.env"
  set +a
  echo "✅ Loaded variables from src/.env"
fi

# ------------------------------------------------------------------
#  Create / activate project virtual-env using uv
# ------------------------------------------------------------------
if [ ! -d .venv ]; then
  echo "📦 Creating project virtual-env with uv..."
  uv venv .venv
fi
source .venv/bin/activate

echo "📦 Installing dependencies with uv..."
if [ -f requirements.txt ]; then
  uv pip install -r requirements.txt
else
  echo "⚠️  requirements.txt not found – installing project itself"
  uv pip install .
fi

echo "📦 Installing LangChain dependencies for full similarity analysis..."
uv pip install langchain langchain-community sentence-transformers faiss-cpu torch transformers

echo "🚀 Starting Ollama service..."
if command -v ollama >/dev/null 2>&1; then
  # Check if Ollama is already running
  if ! curl -s http://localhost:11434/api/version >/dev/null 2>&1; then
    echo "📡 Starting Ollama service in background..."
    ollama serve &
    sleep 10  # Give Ollama time to start
    
    # Verify it started
    if curl -s http://localhost:11434/api/version >/dev/null 2>&1; then
      echo "✅ Ollama service started successfully"
    else
      echo "⚠️  Ollama service may not have started properly"
    fi
  else
    echo "✅ Ollama service already running"
  fi
  
  echo "📦 Ensuring base models are present..."
  
  # Ensure llama3:latest is available (for Jamie models)
  if ! ollama list 2>/dev/null | grep -q "llama3:latest"; then
    echo "⬇️  Pulling llama3:latest model..."
    ollama pull llama3:latest || echo "⚠️  Unable to pull llama3:latest"
  else
    echo "✅ llama3:latest already downloaded."
  fi
  
  # Ensure qwen3:30b is available (for comparison/testing)
  if ! ollama list 2>/dev/null | grep -q "qwen3:30b"; then
    echo "⬇️  Pulling qwen3:30b model..."
    ollama pull qwen3:30b || echo "⚠️  Unable to pull qwen3:30b"
  else
    echo "✅ qwen3:30b already downloaded."
  fi
else
  echo "⚠️  ollama CLI not found – skipping Ollama setup."
fi

# Create /app directory if it doesn't exist
if [ ! -d "/app" ]; then
  echo "📁 Creating /app directory..."
  mkdir -p /app
fi

# Copy extracted DB to /app if present and not already there
if [ -f "$REPO_DIR/pete.db" ] && [ ! -f /app/pete.db ]; then
  echo "📁 Copying pete.db to /app for ModelManager..."
  cp "$REPO_DIR/pete.db" /app/pete.db || true
elif [ -f "$REPO_DIR/src/pete.db" ] && [ ! -f /app/pete.db ]; then
  echo "📁 Copying src/pete.db to /app for ModelManager..."
  cp "$REPO_DIR/src/pete.db" /app/pete.db || true
fi

# Also copy the conversation index if it exists
if [ -f "$REPO_DIR/langchain_indexed_conversations.json" ] && [ ! -f /app/langchain_indexed_conversations.json ]; then
  echo "📁 Copying langchain_indexed_conversations.json to /app..."
  cp "$REPO_DIR/langchain_indexed_conversations.json" /app/langchain_indexed_conversations.json || true
fi

# If no pete.db exists, extract data from production DB (if credentials available)
if [ ! -f /app/pete.db ] && [ -n "${PROD_DB_USERNAME:-}" ]; then
  echo "🔄 No pete.db found, extracting from production database..."
  python src/virtual_jamie_extractor.py || echo "⚠️  Could not extract from production DB"
fi

# Generate conversation index if missing (only if we have a database)
if [ ! -f /app/langchain_indexed_conversations.json ] && [ -f /app/pete.db ]; then
  echo "📊 Generating conversation index for similarity analysis..."
  cd "$REPO_DIR" && python src/langchain/conversation_indexer.py || echo "⚠️  Could not generate conversation index"
elif [ ! -f /app/pete.db ]; then
  echo "⚠️  No pete.db found - skipping conversation index generation"
  echo "💡 To enable full similarity analysis, provide PROD_DB_* environment variables"
fi

echo "🔍 DEBUG: Conversation index section completed, moving to model creation..."

# ------------------------------------------------------------------
#  Auto-create Jamie models if they don't exist
# ------------------------------------------------------------------
echo "🤖 STEP 1: Checking for Jamie AI models..."
echo "🔍 DEBUG: Starting model creation section..."

# List of Jamie models that should exist
JAMIE_MODELS=(
  "peteollama:jamie-fixed"
  "peteollama:jamie-voice-complete"
  "peteollama:jamie-simple"
)

echo "📋 DEBUG: Checking ${#JAMIE_MODELS[@]} models: ${JAMIE_MODELS[*]}"

MODELS_TO_CREATE=()

# Check which models are missing
echo "🔍 DEBUG: Checking existing models..."
for model in "${JAMIE_MODELS[@]}"; do
  echo "🔍 DEBUG: Checking model: $model"
  if ! ollama list 2>/dev/null | grep -q "$model"; then
    echo "❌ Model $model not found"
    MODELS_TO_CREATE+=("$model")
  else
    echo "✅ Model $model already exists"
  fi
done

echo "📊 DEBUG: Found ${#MODELS_TO_CREATE[@]} models to create: ${MODELS_TO_CREATE[*]}"

# Create missing models if any
if [ ${#MODELS_TO_CREATE[@]} -gt 0 ]; then
  echo "🔧 STEP 2: Creating ${#MODELS_TO_CREATE[@]} missing Jamie models..."
  echo "🔍 DEBUG: Models to create: ${MODELS_TO_CREATE[*]}"
  
  # Ensure we have the base model
  echo "🔍 DEBUG: Checking for base model llama3:latest..."
  if ! ollama list 2>/dev/null | grep -q "llama3:latest"; then
    echo "📥 Pulling base model llama3:latest..."
    ollama pull llama3:latest || echo "❌ ERROR: Failed to pull llama3:latest"
  else
    echo "✅ Base model llama3:latest already exists"
  fi
  
  # Create models using the enhanced trainer
  echo "🔍 DEBUG: Checking for training data files..."
  echo "🔍 DEBUG: /app/pete.db exists: $([ -f /app/pete.db ] && echo "YES" || echo "NO")"
  echo "🔍 DEBUG: /app/langchain_indexed_conversations.json exists: $([ -f /app/langchain_indexed_conversations.json ] && echo "YES" || echo "NO")"
  echo "🔍 DEBUG: $REPO_DIR/enhanced_model_trainer.py exists: $([ -f "$REPO_DIR/enhanced_model_trainer.py" ] && echo "YES" || echo "NO")"
  
  if [ -f /app/pete.db ] && [ -f /app/langchain_indexed_conversations.json ] && [ -f "$REPO_DIR/enhanced_model_trainer.py" ]; then
    echo "🎯 STEP 3A: Using enhanced trainer with full conversation data..."
    echo "🔍 DEBUG: Running enhanced_model_trainer.py --auto-create-missing"
    cd "$REPO_DIR" && python enhanced_model_trainer.py --auto-create-missing || echo "⚠️  Enhanced trainer failed, using fallback method"
  else
    echo "🔄 STEP 3B: Using basic model creation (no full training data)..."
    echo "🔍 DEBUG: Will create basic models with Modelfiles"
    
    # Create basic Jamie models with simple Modelfiles
    echo "🔍 DEBUG: Starting basic model creation loop..."
    for model in "${MODELS_TO_CREATE[@]}"; do
      echo "🏗️  STEP 4: Creating $model..."
      echo "🔍 DEBUG: Processing model: $model"
      
      # Determine model type and create appropriate Modelfile
      case "$model" in
        "*jamie-fixed")
          MODEL_TYPE="comprehensive"
          MODEL_DESC="Complete Jamie model with full conversation training"
          ;;
        "*jamie-voice-complete")
          MODEL_TYPE="voice"
          MODEL_DESC="Jamie model optimized for voice interactions"
          ;;
        "*jamie-simple")
          MODEL_TYPE="basic"
          MODEL_DESC="Simple Jamie model for basic interactions"
          ;;
        *)
          MODEL_TYPE="basic"
          MODEL_DESC="Jamie property manager model"
          ;;
      esac
      
      # Create temporary Modelfile
      cat > "/tmp/${model//[:\/]/_}_modelfile" << EOF
FROM llama3:latest

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1

SYSTEM You are Jamie, a professional property manager at Nolen Properties. You help tenants with maintenance requests, payment issues, and general inquiries. Always:
- Acknowledge the tenant's concern with empathy
- Provide clear, specific next steps
- Include realistic timeline expectations
- Maintain a professional but friendly tone
- Offer your contact information when appropriate

Examples of your responses:
- For maintenance: "I understand this is urgent. I'm calling our contractor right now to get someone out there today. They should contact you within the next hour."
- For payments: "I can help you with that. Let me check your account and get this resolved. I'll call you back within 30 minutes."
- For emergencies: "This sounds like an emergency. I'm dispatching someone immediately and they'll call you within 15 minutes."

TEMPLATE """{{ if .System }}{{ .System }}

{{ end }}{{ if .Prompt }}{{ .Prompt }}{{ end }}"""
EOF
      
      # Create the model
      echo "🔍 DEBUG: Creating model with Modelfile: /tmp/${model//[:\/]/_}_modelfile"
      ollama create "$model" -f "/tmp/${model//[:\/]/_}_modelfile" && echo "✅ Created $model" || echo "❌ Failed to create $model"
      
      # Clean up temporary file
      echo "🔍 DEBUG: Cleaning up temporary Modelfile"
      rm -f "/tmp/${model//[:\/]/_}_modelfile"
    done
  fi
  
  echo "🎉 STEP 5: Model creation complete!"
  echo "🔍 DEBUG: Final model list:"
  ollama list 2>/dev/null | grep -E "(peteollama|llama3)" || echo "❌ No models found"
else
  echo "✅ STEP 5: All Jamie models already exist"
  echo "🔍 DEBUG: Current model list:"
  ollama list 2>/dev/null | grep -E "(peteollama|llama3)" || echo "❌ No models found"
fi

# Ensure no previous instance is running
echo "🧹 Ensuring no prior PeteOllama server is running..."
# Kill any python process still running the app
pkill -f uvicorn 2>/dev/null || true
pkill -f "src/main.py" 2>/dev/null || true

echo "🏁 Starting your app..."
python3 src/main.py
