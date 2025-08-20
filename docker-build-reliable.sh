#!/bin/bash

# PeteOllama Reliable Docker Build Script
# Handles UV gracefully with pip fallback

echo "🚀 Building PeteOllama with Reliable Dependencies..."
echo "=================================================="

# Set image name and tag
IMAGE_NAME="pete-ollama-reliable"
TAG="latest"

# Check if we have the right files
echo "🔍 Checking dependencies..."
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found!"
    exit 1
fi

if [ ! -f "pyproject.toml" ]; then
    echo "❌ pyproject.toml not found!"
    exit 1
fi

echo "✅ Dependencies found"

# Build the image
echo "🔨 Building Docker image..."
docker build \
    -f Dockerfile.reliable \
    -t ${IMAGE_NAME}:${TAG} \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    --progress=plain \
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
    echo "  ✅ Dependencies (UV or pip fallback)"
    
    echo ""
    echo "🐳 To run the container:"
    echo "  docker run -p 8000:8000 ${IMAGE_NAME}:${TAG}"
    
    echo ""
    echo "🔍 To inspect the container:"
    echo "  docker run -it --rm ${IMAGE_NAME}:${TAG} /bin/bash"
    
    echo ""
    echo "📝 To check logs:"
    echo "  docker logs <container_id>"
    
else
    echo "❌ Build failed!"
    echo "💡 Troubleshooting tips:"
    echo "  - Check if all required files exist"
    echo "  - Verify Docker is running"
    echo "  - Check available disk space"
    exit 1
fi
