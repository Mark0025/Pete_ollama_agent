#!/bin/bash
# PeteOllama V1 - Build and Deploy Serverless Image

echo "🚀 Building PeteOllama Serverless Docker Image"
echo "=============================================="

# Configuration
IMAGE_NAME="peteollama-serverless"
TAG="v1.0.0"
REGISTRY="mark0025"  # Your Docker Hub username

# Build the image
echo "🔨 Building Docker image..."
docker build -f Dockerfile.serverless -t ${IMAGE_NAME}:${TAG} .

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully"
else
    echo "❌ Docker build failed"
    exit 1
fi

# Tag for registry
echo "🏷️ Tagging image for registry..."
docker tag ${IMAGE_NAME}:${TAG} ${REGISTRY}/${IMAGE_NAME}:${TAG}
docker tag ${IMAGE_NAME}:${TAG} ${REGISTRY}/${IMAGE_NAME}:latest

# Push to registry
echo "📤 Pushing to registry..."
docker push ${REGISTRY}/${IMAGE_NAME}:${TAG}
docker push ${REGISTRY}/${IMAGE_NAME}:latest

if [ $? -eq 0 ]; then
    echo "✅ Image pushed successfully"
    echo ""
    echo "🎯 Next Steps:"
    echo "1. Go to RunPod Serverless Console"
    echo "2. Create new endpoint"
    echo "3. Use image: ${REGISTRY}/${IMAGE_NAME}:${TAG}"
    echo "4. Configure endpoint settings"
    echo "5. Deploy and test!"
else
    echo "❌ Push failed"
    exit 1
fi
