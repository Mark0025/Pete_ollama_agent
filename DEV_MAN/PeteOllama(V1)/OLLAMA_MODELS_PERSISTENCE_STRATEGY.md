# Ollama Models in Ephemeral RunPod Environments

## Understanding Model Persistence and Setup Strategy

### 🎯 **The Problem with Ephemeral Containers**

RunPod containers are **ephemeral** - they start fresh each session. This means:

- ❌ **Models downloaded to default locations are lost** on restart
- ❌ **Container disk space is limited** (30GB) and fills up quickly
- ❌ **No persistence** between sessions unless properly configured

### 📁 **How Ollama Stores Models**

#### **Default Behavior (Problematic for RunPod):**

```
/root/.ollama/models/  # Default location - LOST on restart
├── blobs/             # Model weights and layers
├── manifests/         # Model metadata and configurations
└── registry.ollama.ai/
    └── library/
        ├── llama3/
        └── peteollama/
```

#### **Our Solution (Persistent for RunPod):**

```
/workspace/.ollama/models/  # Persistent location - SURVIVES restarts
├── blobs/                  # Model weights and layers
├── manifests/              # Model metadata and configurations
└── registry.ollama.ai/
    └── library/
        ├── llama3/
        └── peteollama/
            └── property-manager-v0.0.1/  # Your custom model
```

### 🔧 **Our Persistence Strategy**

#### **1. Environment Variable Configuration**

```bash
# Set Ollama to use /workspace for model storage
export OLLAMA_MODELS=/workspace/.ollama/models
```

#### **2. Startup Script Configuration**

```bash
# In runpod_start.sh
export OLLAMA_MODELS=/workspace/.ollama/models
mkdir -p /workspace/.ollama/models
ollama serve &
```

#### **3. Model Creation Process**

```bash
# Create custom model from local Modelfile
ollama create peteollama:property-manager-v0.0.1 -f models/Modelfile.enhanced

# Pull base models to persistent location
ollama pull llama3:latest
ollama pull qwen3:30b
```

### 📊 **Current Model Status**

#### **✅ Successfully Created Models:**

1. **`llama3:latest`** (4.7 GB)

   - Location: `/workspace/.ollama/models/blobs/`
   - Status: ✅ Available and persistent
   - Purpose: Base model for custom training

2. **`peteollama:property-manager-v0.0.1`** (Custom)
   - Location: `/workspace/.ollama/models/manifests/registry.ollama.ai/library/peteollama/`
   - Status: ✅ Created and persistent
   - Purpose: Your trained property manager model

#### **📋 Model File Structure:**

```
/workspace/.ollama/models/
├── blobs/
│   ├── sha256-6a0746a1ec1a... (llama3 base model)
│   ├── sha256-054c7e01d6f6... (custom model layers)
│   └── sha256-459867dd2dca... (custom model layers)
└── manifests/
    └── registry.ollama.ai/
        └── library/
            ├── llama3/
            │   └── latest
            └── peteollama/
                └── property-manager-v0.0.1
```

### 🚀 **Consistent Setup Strategy**

#### **For Any RunPod Session:**

1. **Environment Setup:**

   ```bash
   export OLLAMA_MODELS=/workspace/.ollama/models
   export OLLAMA_HOST=0.0.0.0
   export OLLAMA_ORIGINS=*
   ```

2. **Start Ollama:**

   ```bash
   mkdir -p /workspace/.ollama/models
   ollama serve &
   ```

3. **Verify Models:**

   ```bash
   ollama list
   # Should show:
   # - llama3:latest
   # - peteollama:property-manager-v0.0.1
   ```

4. **Start Proxy:**
   ```bash
   cd /workspace/Pete_ollama_agent
   uv run python src/ollama_proxy.py &
   ```

### 🔄 **Model Lifecycle in RunPod**

#### **First Session:**

1. ✅ Models downloaded to `/workspace/.ollama/models`
2. ✅ Custom model created from Modelfile
3. ✅ Models persist in `/workspace` volume

#### **Subsequent Sessions:**

1. ✅ Models already exist in `/workspace/.ollama/models`
2. ✅ No re-download needed
3. ✅ Instant availability

#### **Model Updates:**

1. ✅ Update Modelfile in `/workspace/Pete_ollama_agent/models/`
2. ✅ Recreate model: `ollama create peteollama:property-manager-v0.0.1 -f models/Modelfile.enhanced`
3. ✅ New model persists in `/workspace`

### 📈 **Benefits of This Strategy**

#### **✅ Persistence:**

- Models survive RunPod restarts
- No re-downloading between sessions
- Consistent environment across sessions

#### **✅ Space Efficiency:**

- Uses `/workspace` (50GB) instead of container disk (30GB)
- Avoids "No space left on device" errors
- Better resource utilization

#### **✅ Portability:**

- Same setup works on any RunPod instance
- Models can be shared between sessions
- Easy to replicate on new instances

#### **✅ Performance:**

- Models load faster on subsequent sessions
- GPU memory utilization optimized
- Reduced startup time

### 🛠 **Troubleshooting**

#### **If Models Don't Persist:**

```bash
# Check environment variable
echo $OLLAMA_MODELS

# Verify models directory
ls -la /workspace/.ollama/models/

# Restart with correct configuration
pkill ollama
export OLLAMA_MODELS=/workspace/.ollama/models
ollama serve &
```

#### **If Container Disk is Full:**

```bash
# Move cache to workspace
mv /root/.cache /workspace/cache
ln -s /workspace/cache /root/.cache

# Clear temporary files
rm -rf /tmp/*
```

#### **If Custom Model Missing:**

```bash
# Recreate from Modelfile
cd /workspace/Pete_ollama_agent
ollama create peteollama:property-manager-v0.0.1 -f models/Modelfile.enhanced
```

### 🎯 **Best Practices**

1. **Always use `/workspace` for persistence**
2. **Set `OLLAMA_MODELS` environment variable**
3. **Create models from local Modelfiles**
4. **Verify models exist before starting proxy**
5. **Monitor disk usage in RunPod console**

### 📋 **Quick Setup Commands**

```bash
# Complete setup for any RunPod session
cd /workspace/Pete_ollama_agent
git pull
export OLLAMA_MODELS=/workspace/.ollama/models
export OLLAMA_HOST=0.0.0.0
export OLLAMA_ORIGINS=*
mkdir -p /workspace/.ollama/models
ollama serve &
sleep 10
ollama list
uv run python src/ollama_proxy.py &
```

**This strategy ensures your models are always available and persistent across RunPod sessions!** 🚀
