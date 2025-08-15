#!/bin/bash

# Memory Cleanup Script for RunPod
# Run this when memory usage gets high

echo "🧹 Memory Cleanup Script"
echo "========================"

# Show current memory usage
echo "📊 Current Memory Usage:"
free -h
echo ""

# Show disk usage
echo "💾 Current Disk Usage:"
df -h /workspace
echo ""

# Clear various caches
echo "🧹 Clearing caches..."

# Clear Python cache
find /workspace -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find /workspace -name "*.pyc" -delete 2>/dev/null || true

# Clear uv cache
rm -rf /root/.cache/uv 2>/dev/null || true

# Clear pip cache
rm -rf /root/.cache/pip 2>/dev/null || true

# Clear temporary files
rm -rf /tmp/* 2>/dev/null || true

# Clear Ollama cache (if not using persistent volume)
if [ -d "/root/.ollama" ] && [ ! -L "/root/.ollama" ]; then
    echo "🗑️ Clearing Ollama cache..."
    rm -rf /root/.ollama/cache 2>/dev/null || true
fi

# Restart Ollama if it's using too much memory
echo "🔄 Checking Ollama memory usage..."
OLLAMA_MEMORY=$(ps aux | grep ollama | grep -v grep | awk '{sum+=$6} END {print sum/1024}')
if [ ! -z "$OLLAMA_MEMORY" ] && (( $(echo "$OLLAMA_MEMORY > 10000" | bc -l) )); then
    echo "⚠️ Ollama using ${OLLAMA_MEMORY}MB, restarting..."
    pkill ollama 2>/dev/null || true
    sleep 2
    ollama serve &
    echo "✅ Ollama restarted"
fi

# Show final memory usage
echo ""
echo "📊 Memory Usage After Cleanup:"
free -h
echo ""

echo "✅ Memory cleanup complete!"
echo "💡 If memory is still high, consider:"
echo "   - Restarting the pod"
echo "   - Using smaller models"
echo "   - Reducing auto_preload models" 