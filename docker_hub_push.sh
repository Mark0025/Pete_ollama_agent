#!/bin/bash

# Docker Hub Push Script for PeteOllama
# Usage: ./docker_hub_push.sh

set -e

echo "🐳 Docker Hub Push Script for PeteOllama"
echo "========================================"

# Your Docker Hub username
DOCKER_USERNAME="mark0025"

echo "📋 Step 1: Login to Docker Hub"
docker login

echo "📋 Step 2: List current images"
docker images | grep -E "(peteollama|ollama)"

echo "📋 Step 3: Build and tag the app image"
echo "Building peteollama_app..."
docker build -t ${DOCKER_USERNAME}/peteollama-app:latest .

echo "📋 Step 4: Tag Ollama image (if needed)"
# Pull official Ollama image and retag for consistency
docker pull ollama/ollama:latest
docker tag ollama/ollama:latest ${DOCKER_USERNAME}/peteollama-ollama:latest

echo "📋 Step 5: Push images to Docker Hub"
echo "Pushing peteollama-app..."
docker push ${DOCKER_USERNAME}/peteollama-app:latest

echo "Pushing peteollama-ollama..."
docker push ${DOCKER_USERNAME}/peteollama-ollama:latest

echo "✅ Push complete!"
echo ""
echo "🔗 Your images are now available at:"
echo "   https://hub.docker.com/r/${DOCKER_USERNAME}/peteollama-app"
echo "   https://hub.docker.com/r/${DOCKER_USERNAME}/peteollama-ollama"
echo ""
echo "📝 Next: Update Colab notebook to use these images"