#!/bin/bash
# Render deployment start script
echo "🚀 Starting Jamie AI Property Manager..."
echo "📍 Working directory: $(pwd)"
echo "🐍 Python version: $(python --version)"
echo "🔧 Environment variables:"
echo "  PORT: $PORT"
echo "  RUNPOD_API_KEY: ${RUNPOD_API_KEY:+Set} ${RUNPOD_API_KEY:-Not set}"
echo "  RUNPOD_SERVERLESS_ENDPOINT: ${RUNPOD_SERVERLESS_ENDPOINT:+Set} ${RUNPOD_SERVERLESS_ENDPOINT:-Not set}"

# Set Python path
export PYTHONPATH=/opt/render/project/src:$PYTHONPATH

# Start the application
exec python src/main.py
