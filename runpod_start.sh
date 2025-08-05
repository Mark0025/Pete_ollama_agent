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
echo "Ensure core build tools (curl, git, pip) exist on minimal images"
echo "---------------------------"
missing_pkgs=""
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
    apt-get update -y && apt-get install -y $missing_pkgs
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

# Ensure no previous instance is running
echo "🧹 Ensuring no prior PeteOllama server is running..."
pkill -f uvicorn 2>/dev/null || true

echo "🏁 Starting your app..."
python3 src/main.py
