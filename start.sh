#!/bin/bash
# PeteOllama V1 - Quick Start Script
# Starts all containers and launches the GUI

echo "🏠 PeteOllama V1 - AI Property Manager"
echo "====================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "🐳 Starting all containers..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service status..."

# Check Ollama
if curl -s http://localhost:11435/api/health > /dev/null; then
    echo "✅ Ollama: Ready"
else
    echo "⚠️  Ollama: Starting up..."
fi

# Check PostgreSQL
if docker exec peteollama_postgres pg_isready -U pete > /dev/null 2>&1; then
    echo "✅ PostgreSQL: Ready"
else
    echo "⚠️  PostgreSQL: Starting up..."
fi

# Check App Container
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ App Container: Ready"
else
    echo "⚠️  App Container: Starting up..."
fi

echo ""
echo "🎯 Next Steps:"
echo "1. Extract training data: python extract_jamie_data.py"
echo "2. Download model: docker exec -it peteollama_ollama ollama pull qwen2.5:7b"
echo "3. Access GUI: http://localhost:8080 (or run docker exec -it peteollama_app python src/main.py)"
echo "4. Test webhook: http://localhost:8000"
echo ""
echo "📊 Container Status:"
docker-compose ps

echo ""
echo "🚀 PeteOllama V1 is starting up!"
echo "🎤 Ready for VAPI integration and AI training"