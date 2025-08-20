#!/bin/bash

# PeteOllama UV-Optimized Docker Build Script
# Fast builds with database included

echo "🚀 Building PeteOllama with UV + Database..."
echo "=============================================="

# Set image name and tag
IMAGE_NAME="pete-ollama-uv"
TAG="latest"

# Build the image
echo "🔨 Building Docker image..."
docker build \
    -f Dockerfile.uv \
    -t ${IMAGE_NAME}:${TAG} \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    .

# Check build result
if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    
    # Show image size
    echo "📊 Image size:"
    docker images ${IMAGE_NAME}:${TAG} --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
    
    # Show what's included
    echo "📁 Contents included:"
    echo "  ✅ Application code (src/)"
    echo "  ✅ Configuration (config/)"
    echo "  ✅ Database (pete.db, training_data.db)"
    echo "  ✅ Conversation cache (langchain_indexed_conversations.json)"
    echo "  ✅ Environment variables (.env*)"
    echo "  ✅ UV-optimized dependencies"
    
    echo ""
    echo "🐳 To run the container:"
    echo "  docker run -p 8000:8000 ${IMAGE_NAME}:${TAG}"
    
    echo ""
    echo "🔍 To inspect the container:"
    echo "  docker run -it --rm ${IMAGE_NAME}:${TAG} /bin/bash"
    
else
    echo "❌ Build failed!"
    exit 1
fi
