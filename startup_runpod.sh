#!/bin/bash
# Bootstraps a fresh RunPod instance: installs docker, starts dockerd with a
# persistent data-root, pulls/updates the repo, then launches the stack.
# This file is meant to be invoked as the pod Container Command:
#   /bin/bash /workspace/Pete_ollama_agent/startup_runpod.sh
set -euo pipefail

apt-get update
apt-get install -y git curl docker.io docker-compose nvidia-container-toolkit

# Start Docker daemon with data under /workspace so images & volumes persist
mkdir -p /workspace/docker-data
nohup dockerd --data-root /workspace/docker-data \
      >/var/log/dockerd.log 2>&1 &

# Wait for the daemon to respond (max 30s)
for i in {1..30}; do
  if docker info >/dev/null 2>&1; then break; fi
  sleep 1
done

if ! docker info >/dev/null 2>&1; then
  echo "❌ Docker daemon failed to start" >&2
  tail -n 40 /var/log/dockerd.log || true
  exit 1
fi

echo "✅ Docker daemon ready"

# Clone or update repo
cd /workspace
if [ ! -d Pete_ollama_agent ]; then
  git clone https://github.com/Mark0025/Pete_ollama_agent.git
fi
cd Pete_ollama_agent
git pull --ff-only

# Ensure execution bit and launch
chmod +x start.sh
./start.sh
