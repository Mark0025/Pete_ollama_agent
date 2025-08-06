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
uv pip install langchain langchain-community sentence-transformers faiss-cpu

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
  
  echo "📦 Ensuring Ollama model qwen3:30b is present..."
  if ! ollama list 2>/dev/null | grep -q "qwen3:30b"; then
    echo "⬇️  Pulling qwen3:30b model..."
    ollama pull qwen3:30b || echo "⚠️  Unable to pull model; Ollama service may not be running yet."
  else
    echo "✅ qwen3:30b already downloaded."
  fi
else
  echo "⚠️  ollama CLI not found – skipping Ollama setup."
fi

# Copy extracted DB to /app if present and not already there
if [ -f "$REPO_DIR/src/pete.db" ] && [ ! -f /app/pete.db ]; then
  echo "📁 Copying pete.db to /app for ModelManager..."
  cp "$REPO_DIR/src/pete.db" /app/pete.db || true
fi

# Generate conversation index if missing
if [ ! -f "$REPO_DIR/langchain_indexed_conversations.json" ]; then
  echo "📊 Generating conversation index for similarity analysis..."
  python src/langchain/conversation_indexer.py || echo "⚠️  Could not generate conversation index"
fi

# Ensure no previous instance is running
echo "🧹 Ensuring no prior PeteOllama server is running..."
# Kill any python process still running the app
pkill -f uvicorn 2>/dev/null || true
pkill -f "src/main.py" 2>/dev/null || true

echo "🏁 Starting your app..."
python3 src/main.py
