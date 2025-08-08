# Dynamic Model Management System

## Admin/Settings as Single Source of Truth

### 🎯 **The Problem:**

- Models created from different Modelfiles
- Multiple base models (llama3, qwen3, etc.)
- Need versioning (v1, v2, v3)
- Admin/Settings should be the source of truth
- Dynamic model discovery and friendly naming

### 🚀 **Solution: Dynamic Model Management**

## 📋 **1. Enhanced Model Configuration Structure**

```json
{
  "default_model": "peteollama:property-manager-v1",
  "models": {
    "peteollama:property-manager-v1": {
      "name": "peteollama:property-manager-v1",
      "display_name": "PeteOllama Property Manager v1",
      "description": "Property management model v1 trained on llama3",
      "version": "v1",
      "base_model": "llama3:latest",
      "modelfile": "models/Modelfile.enhanced",
      "show_in_ui": true,
      "auto_preload": true,
      "is_jamie_model": true,
      "created_at": "2025-08-08T20:50:48.000000",
      "last_updated": "2025-08-08T20:50:48.000000",
      "status": "available"
    },
    "peteollama:property-manager-v2": {
      "name": "peteollama:property-manager-v2",
      "display_name": "PeteOllama Property Manager v2",
      "description": "Property management model v2 trained on qwen3",
      "version": "v2",
      "base_model": "qwen3:30b",
      "modelfile": "models/Modelfile.qwen-enhanced",
      "show_in_ui": true,
      "auto_preload": false,
      "is_jamie_model": true,
      "created_at": "2025-08-08T21:00:00.000000",
      "last_updated": "2025-08-08T21:00:00.000000",
      "status": "pending"
    }
  },
  "base_models": {
    "llama3:latest": {
      "display_name": "Llama 3 (Latest)",
      "description": "Meta's Llama 3 base model",
      "size": "4.7 GB",
      "status": "available"
    },
    "qwen3:30b": {
      "display_name": "Qwen 3 (30B)",
      "description": "Alibaba's Qwen 3 30B model",
      "size": "18 GB",
      "status": "available"
    }
  },
  "last_updated": "2025-08-08T21:00:00.000000"
}
```

## 🔧 **2. Dynamic Model Discovery System**

### **Model Discovery Script:**

```python
# src/utils/model_discovery.py
import json
import subprocess
from pathlib import Path
from typing import Dict, List

class ModelDiscovery:
    def __init__(self, config_path: str = "config/model_settings.json"):
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self) -> Dict:
        """Load the current model configuration"""
        with open(self.config_path, 'r') as f:
            return json.load(f)

    def discover_available_models(self) -> List[str]:
        """Discover models actually available in Ollama"""
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                models = []
                for line in lines:
                    if line.strip():
                        model_name = line.split()[0]
                        models.append(model_name)
                return models
            return []
        except Exception as e:
            print(f"Error discovering models: {e}")
            return []

    def sync_config_with_reality(self):
        """Sync configuration with actually available models"""
        available_models = self.discover_available_models()

        # Update status for each model in config
        for model_name, model_config in self.config['models'].items():
            if model_name in available_models:
                model_config['status'] = 'available'
            else:
                model_config['status'] = 'missing'

        # Save updated config
        self.save_config()

    def create_model_from_config(self, model_name: str) -> bool:
        """Create a model based on configuration"""
        if model_name not in self.config['models']:
            return False

        model_config = self.config['models'][model_name]
        modelfile_path = model_config.get('modelfile')

        if not modelfile_path or not Path(modelfile_path).exists():
            return False

        try:
            # Create the model using ollama
            result = subprocess.run([
                'ollama', 'create', model_name, '-f', modelfile_path
            ], capture_output=True, text=True)

            if result.returncode == 0:
                model_config['status'] = 'available'
                self.save_config()
                return True
            else:
                print(f"Error creating model {model_name}: {result.stderr}")
                return False
        except Exception as e:
            print(f"Error creating model {model_name}: {e}")
            return False

    def save_config(self):
        """Save the updated configuration"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
```

## 🎛️ **3. Admin/Settings Management System**

### **Model Management API:**

```python
# src/admin/model_manager.py
from fastapi import APIRouter, HTTPException
from typing import Dict, List
import json

router = APIRouter(prefix="/admin/models", tags=["admin"])

class ModelManager:
    def __init__(self, config_path: str = "config/model_settings.json"):
        self.config_path = config_path
        self.discovery = ModelDiscovery(config_path)

    def get_all_models(self) -> Dict:
        """Get all models with their status"""
        self.discovery.sync_config_with_reality()
        return self.discovery.config

    def create_model(self, model_name: str) -> Dict:
        """Create a model from configuration"""
        success = self.discovery.create_model_from_config(model_name)
        if success:
            return {"status": "success", "message": f"Model {model_name} created successfully"}
        else:
            raise HTTPException(status_code=400, detail=f"Failed to create model {model_name}")

    def update_model_config(self, model_name: str, updates: Dict) -> Dict:
        """Update model configuration"""
        if model_name not in self.discovery.config['models']:
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found")

        self.discovery.config['models'][model_name].update(updates)
        self.discovery.save_config()
        return {"status": "success", "message": f"Model {model_name} updated"}

    def add_new_model(self, model_config: Dict) -> Dict:
        """Add a new model to configuration"""
        model_name = model_config['name']
        self.discovery.config['models'][model_name] = model_config
        self.discovery.save_config()
        return {"status": "success", "message": f"Model {model_name} added to configuration"}

@router.get("/")
async def get_models():
    """Get all models"""
    manager = ModelManager()
    return manager.get_all_models()

@router.post("/create/{model_name}")
async def create_model(model_name: str):
    """Create a model from configuration"""
    manager = ModelManager()
    return manager.create_model(model_name)

@router.put("/{model_name}")
async def update_model(model_name: str, updates: Dict):
    """Update model configuration"""
    manager = ModelManager()
    return manager.update_model_config(model_name, updates)

@router.post("/add")
async def add_model(model_config: Dict):
    """Add new model to configuration"""
    manager = ModelManager()
    return manager.add_new_model(model_config)
```

## 🔄 **4. Dynamic Model Creation Workflow**

### **Step 1: Define New Model in Admin**

```json
{
  "name": "peteollama:property-manager-v2",
  "display_name": "PeteOllama Property Manager v2",
  "description": "Property management model v2 trained on qwen3",
  "version": "v2",
  "base_model": "qwen3:30b",
  "modelfile": "models/Modelfile.qwen-enhanced",
  "show_in_ui": true,
  "auto_preload": false,
  "is_jamie_model": true,
  "status": "pending"
}
```

### **Step 2: Create Modelfile**

```dockerfile
# models/Modelfile.qwen-enhanced
FROM qwen3:30b

# Set the system prompt
SYSTEM """
You are PeteOllama, an expert property manager trained on real property management conversations.
You help tenants and property managers with maintenance requests, rent payments, lease questions,
and other property-related issues. Always be professional, helpful, and accurate.
"""

# Add training data
TEMPLATE """
{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
<|im_start|>assistant
{{ .Response }}<|im_end|>
{{ end }}
"""

# Add conversation data
PARAMETER stop "<|im_start|>"
PARAMETER stop "<|im_end|>"
PARAMETER temperature 0.7
```

### **Step 3: Create Model**

```bash
# Via API
curl -X POST http://localhost:8000/admin/models/create/peteollama:property-manager-v2

# Or via CLI
ollama create peteollama:property-manager-v2 -f models/Modelfile.qwen-enhanced
```

## 🎯 **5. Versioning Strategy**

### **Version Naming Convention:**

```
peteollama:property-manager-v1    # Llama3 base
peteollama:property-manager-v2    # Qwen3 base
peteollama:property-manager-v3    # Llama3 with more data
peteollama:property-manager-v4    # Qwen3 with more data
```

### **Base Model Strategy:**

- **v1, v3, v5...** → Llama3 base (faster, smaller)
- **v2, v4, v6...** → Qwen3 base (better quality, larger)

## 🔧 **6. Integration with Frontend**

### **Frontend Model Selection:**

```javascript
// Get available models from admin
const models = await fetch('/admin/models').then((r) => r.json());

// Filter for UI-visible models
const uiModels = models.models.filter(
  (m) => m.show_in_ui && m.status === 'available'
);

// Display with friendly names
uiModels.forEach((model) => {
  console.log(`${model.display_name} (${model.version})`);
});
```

### **Dynamic Proxy Integration:**

```python
# src/ollama_proxy.py - Enhanced
@app.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    # Validate model exists in config
    config = load_model_config()
    if request.model not in config['models']:
        raise HTTPException(status_code=400, detail=f"Model {request.model} not configured")

    # Check if model is available
    model_config = config['models'][request.model]
    if model_config['status'] != 'available':
        raise HTTPException(status_code=503, detail=f"Model {request.model} not available")

    # Proceed with request
    # ... existing code ...
```

## 📊 **7. Benefits of This System**

### **✅ Single Source of Truth:**

- Admin/Settings controls all model configuration
- Dynamic discovery syncs with reality
- Versioning and friendly names managed centrally

### **✅ Flexibility:**

- Easy to add new base models
- Simple versioning system
- Multiple Modelfiles supported

### **✅ Automation:**

- Models created from configuration
- Status automatically updated
- Frontend dynamically updates

### **✅ Scalability:**

- Easy to add v3, v4, v5...
- Support for new base models
- Configuration-driven approach

**This system gives you complete control over model management with dynamic discovery and friendly naming!** 🚀
