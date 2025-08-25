#!/usr/bin/env python3
"""
Test Provider API Endpoints
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config.model_settings import model_settings

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Provider API Test Server", "status": "running"}

@app.get("/provider-settings")
async def get_provider_settings():
    """Get current provider settings"""
    try:
        settings = model_settings.get_provider_settings()
        return {
            "success": True,
            "default_provider": settings.get("default_provider", "ollama"),
            "fallback_provider": settings.get("fallback_provider", "runpod"),
            "fallback_enabled": settings.get("fallback_enabled", False)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "default_provider": "ollama",
            "fallback_provider": "runpod", 
            "fallback_enabled": False
        }

@app.post("/provider-settings/update")
async def update_provider_settings(request: dict):
    """Update provider settings"""
    try:
        default_provider = request.get("default_provider")
        fallback_provider = request.get("fallback_provider")
        fallback_enabled = request.get("fallback_enabled", False)
        
        if not default_provider:
            return {"success": False, "error": "Default provider is required"}
        
        # Validate provider names
        valid_providers = ["ollama", "runpod", "openrouter"]
        if default_provider not in valid_providers:
            return {"success": False, "error": f"Invalid default provider. Must be one of: {', '.join(valid_providers)}"}
        
        success = model_settings.update_provider_settings({
            "default_provider": default_provider,
            "fallback_provider": fallback_provider or "runpod",
            "fallback_enabled": fallback_enabled
        })
        
        if success:
            return {
                "success": True,
                "message": f"Provider settings updated successfully. Default provider is now {default_provider.upper()}",
                "settings": {
                    "default_provider": default_provider,
                    "fallback_provider": fallback_provider or "runpod",
                    "fallback_enabled": fallback_enabled
                }
            }
        else:
            return {"success": False, "error": "Failed to update provider settings"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    print("🧪 Starting Provider API Test Server on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
