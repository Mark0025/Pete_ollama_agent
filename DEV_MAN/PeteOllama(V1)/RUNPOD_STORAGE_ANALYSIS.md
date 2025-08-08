# RunPod Storage Analysis & Startup/Teardown Strategy

## 📊 **Current Storage Breakdown**

### **Container Disk (30GB) - 87% Full:**

```
Location: / (root filesystem)
Usage: 87% (26.1GB of 30GB)
Contents:
├── /root/.cache/          # Python, pip, uv cache
├── /tmp/                  # Temporary files
├── /var/log/             # System logs
├── /usr/                 # System binaries
└── /opt/                 # Installed software
```

### **Volume Disk (50GB) - 38% Full:**

```
Location: /workspace
Usage: 38% (19GB of 50GB)
Contents:
├── /workspace/.ollama/models/     # Models (persistent)
│   ├── blobs/                     # Model weights
│   └── manifests/                 # Model metadata
├── /workspace/Pete_ollama_agent/  # Your project
├── /workspace/pete.db             # Database (8.2MB)
├── /workspace/cache/              # Moved cache
└── /workspace/pbcopy, pbpaste    # Debug tools
```

## 🎯 **Storage Strategy Benefits**

### **✅ What We Fixed:**

- **Models:** Now stored in Volume (persistent) instead of Container (temporary)
- **Cache:** Moved to Volume for persistence
- **Database:** Moved to Volume for persistence
- **Project:** Already in Volume (survives restarts)

### **✅ Current Status:**

- **Container:** 87% full (temporary files, cache, logs)
- **Volume:** 38% full (persistent data, models, project)
- **Models:** Stored in Volume (survives restarts)

## 🚀 **Startup Process (Automatic)**

### **RunPod Template Configuration:**

```bash
# Startup Command in RunPod Template
/bin/bash -c 'cd /workspace/Pete_ollama_agent && ./runpod_start.sh'
```

### **What runpod_start.sh Does:**

1. **Environment Setup:**

   ```bash
   export OLLAMA_MODELS=/workspace/.ollama/models
   export OLLAMA_HOST=0.0.0.0
   export OLLAMA_ORIGINS=*
   ```

2. **Ollama Service:**

   ```bash
   mkdir -p /workspace/.ollama/models
   ollama serve &
   ```

3. **Model Verification:**

   ```bash
   ollama list  # Checks if models exist
   # If missing: ollama pull llama3:latest
   # If missing: ollama create peteollama:property-manager-v0.0.1
   ```

4. **Proxy Service:**
   ```bash
   uv run python src/ollama_proxy.py &
   ```

## 🔄 **Teardown Process (Automatic)**

### **What Happens on Stop:**

- **Container:** Everything in `/` gets wiped
- **Volume:** Everything in `/workspace` persists
- **Models:** Stay in `/workspace/.ollama/models/`
- **Project:** Stays in `/workspace/Pete_ollama_agent/`
- **Database:** Stays in `/workspace/pete.db`

### **What Gets Lost:**

- ❌ Container cache (`/root/.cache`)
- ❌ Temporary files (`/tmp`)
- ❌ System logs (`/var/log`)
- ❌ Running processes

### **What Persists:**

- ✅ Models in `/workspace/.ollama/models/`
- ✅ Project code in `/workspace/Pete_ollama_agent/`
- ✅ Database in `/workspace/pete.db`
- ✅ Cache in `/workspace/cache/`

## 📈 **Model Installation Impact**

### **Installing qwen3:30b:**

```bash
ollama pull qwen3:30b  # ~18GB
```

**Storage Impact:**

- **Current Volume:** 38% (19GB of 50GB)
- **qwen3:30b:** ~18GB
- **After Install:** ~74% (37GB of 50GB)
- **Remaining:** ~13GB free space

**Location:** `/workspace/.ollama/models/` (persistent)

## 🛠 **Manual Startup Commands**

### **If Auto-Startup Fails:**

```bash
# Navigate to project
cd /workspace/Pete_ollama_agent

# Set environment
export OLLAMA_MODELS=/workspace/.ollama/models
export OLLAMA_HOST=0.0.0.0
export OLLAMA_ORIGINS=*

# Start Ollama
mkdir -p /workspace/.ollama/models
ollama serve &

# Verify models
ollama list

# Start proxy
uv run python src/ollama_proxy.py &

# Test
curl -X POST http://localhost:8001/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "peteollama:property-manager-v0.0.1", "messages": [{"role": "user", "content": "Hello"}]}'
```

## 📋 **Startup/Teardown Checklist**

### **✅ Startup (Automatic):**

- [x] Models load from `/workspace/.ollama/models/`
- [x] Ollama service starts with correct environment
- [x] Proxy starts on port 8001
- [x] Database available at `/workspace/pete.db`
- [x] Project code available at `/workspace/Pete_ollama_agent/`

### **✅ Teardown (Automatic):**

- [x] Container disk wiped (temporary files lost)
- [x] Volume persists (models, code, database saved)
- [x] Processes stopped
- [x] Ready for next session

## 🎯 **Key Benefits**

### **✅ Persistence:**

- Models survive restarts
- Code changes persist
- Database data persists
- No re-downloading needed

### **✅ Space Efficiency:**

- Uses Volume (50GB) for important data
- Container disk only for temporary files
- Better resource utilization

### **✅ Reliability:**

- Consistent environment across sessions
- Automatic startup process
- Models always available

## 🚨 **Troubleshooting**

### **If Container Disk is Full:**

```bash
# Move cache to workspace
mv /root/.cache /workspace/cache
ln -s /workspace/cache /root/.cache

# Clear temporary files
rm -rf /tmp/*
```

### **If Models Missing:**

```bash
# Check environment
echo $OLLAMA_MODELS

# Recreate models
cd /workspace/Pete_ollama_agent
ollama create peteollama:property-manager-v0.0.1 -f models/Modelfile.enhanced
ollama pull llama3:latest
```

### **If Proxy Not Working:**

```bash
# Check if proxy is running
ps aux | grep ollama_proxy

# Restart proxy
pkill -f ollama_proxy
uv run python src/ollama_proxy.py &
```

**Your setup is now fully automated and persistent!** 🚀
