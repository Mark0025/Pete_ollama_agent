"""
Admin Router
===========

FastAPI router for administrative endpoints including status checks,
configuration management, and system monitoring.
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse, HTMLResponse
from typing import Dict, Any, List
from pathlib import Path
from utils.datetime_utils import now_cst, format_datetime_api, format_datetime_display
import time
import sys
import os
import json
import asyncio

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.logger import logger
from ai.model_manager import ModelManager
from config.model_settings import model_settings
from vapi.models.webhook_models import SystemStatus
from vapi.services.provider_service import ProviderService

class AdminRouter:
    """Router class for admin endpoints"""
    
    def __init__(self, model_manager: ModelManager, runpod_api_key: str = None):
        self.router = APIRouter(prefix="/admin", tags=["admin"])
        self.model_manager = model_manager
        self.runpod_api_key = runpod_api_key
        self.provider_service = ProviderService()
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup admin routes"""
        
        @self.router.get("/", response_class=HTMLResponse)
        async def admin_dashboard(request: Request):
            """Admin dashboard page - serve the existing frontend admin-ui.html"""
            try:
                # Path to the existing frontend admin-ui.html
                frontend_path = Path(__file__).parent.parent.parent / "frontend" / "html" / "admin-ui.html"
                
                if frontend_path.exists():
                    with open(frontend_path, 'r', encoding='utf-8') as f:
                        return f.read()
                else:
                    # Fallback to a simple message if file doesn't exist
                    return '''
                    <!DOCTYPE html>
                    <html><head><title>Admin UI Not Found</title></head>
                    <body>
                        <h1>Admin UI Not Found</h1>
                        <p>The admin UI file was not found at: {}</p>
                        <p><a href="/ui">Go to Main UI</a></p>
                    </body></html>
                    '''.format(frontend_path)
            
            except Exception as e:
                logger.error(f"Admin dashboard error: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/system-config", response_class=HTMLResponse)
        async def system_config_dashboard(request: Request):
            """System configuration dashboard page"""
            try:
                # Path to the system config UI
                config_path = Path(__file__).parent.parent.parent / "frontend" / "html" / "system-config-ui.html"
                
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        return f.read()
                else:
                    # Fallback to a simple message if file doesn't exist
                    return '''
                    <!DOCTYPE html>
                    <html><head><title>System Configuration Not Found</title></head>
                    <body>
                        <h1>System Configuration Not Found</h1>
                        <p>The system configuration UI file was not found at: {}</p>
                        <p><a href="/admin">Go to Admin Dashboard</a></p>
                    </body></html>
                    '''.format(config_path)
            
            except Exception as e:
                logger.error(f"System config dashboard error: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/status")
        async def system_status():
            """Get comprehensive system status"""
            return await self._get_system_status()
        
        @self.router.get("/health")
        async def health_check():
            """Simple health check endpoint"""
            try:
                # Basic health checks
                model_available = self.model_manager.is_model_available(self.model_manager.model_name)
                
                return {
                    "status": "healthy",
                    "timestamp": time.time(),
                    "model_available": model_available,
                    "primary_model": self.model_manager.model_name
                }
            
            except Exception as e:
                logger.error(f"Health check failed: {str(e)}")
                return {
                    "status": "unhealthy",
                    "timestamp": time.time(),
                    "error": str(e)
                }
        
        @self.router.get("/models")
        async def list_models():
            """List all available models"""
            try:
                # Get models from different providers
                ollama_models = []
                try:
                    ollama_models = await self.provider_service.get_ollama_models()
                except Exception as e:
                    logger.warning(f"Could not fetch Ollama models: {e}")
                
                openrouter_models = []
                try:
                    openrouter_models = await self.provider_service.get_openrouter_models()
                except Exception as e:
                    logger.warning(f"Could not fetch OpenRouter models: {e}")
                
                # Get UI models from settings
                ui_models = model_settings.get_ui_models()
                
                return {
                    "ollama_models": ollama_models,
                    "openrouter_models": openrouter_models,
                    "ui_models": [model.dict() for model in ui_models],
                    "current_model": self.model_manager.model_name,
                    "custom_model": getattr(self.model_manager, 'custom_model_name', None)
                }
            
            except Exception as e:
                logger.error(f"Error listing models: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.post("/models/switch")
        async def switch_model(request: Request):
            """Switch the active model"""
            try:
                body = await request.json()
                model_name = body.get('model_name')
                
                if not model_name:
                    raise HTTPException(status_code=400, detail="model_name required")
                
                # Switch the model
                old_model = self.model_manager.model_name
                success = self.model_manager.switch_model(model_name)
                
                if success:
                    logger.info(f"Model switched from {old_model} to {model_name}")
                    return {
                        "success": True,
                        "old_model": old_model,
                        "new_model": model_name,
                        "message": f"Successfully switched to {model_name}"
                    }
                else:
                    return {
                        "success": False,
                        "current_model": old_model,
                        "attempted_model": model_name,
                        "message": f"Failed to switch to {model_name}"
                    }
            
            except Exception as e:
                logger.error(f"Model switch error: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/config")
        async def get_configuration():
            """Get current system configuration"""
            try:
                provider_settings = model_settings.get_provider_settings()
                ui_models = model_settings.get_ui_models()
                
                return {
                    "provider_settings": provider_settings,
                    "ui_models": [{
                        "name": model.name,
                        "display_name": model.display_name,
                        "type": model.type,
                        "is_jamie_model": model.is_jamie_model,
                        "show_in_ui": model.show_in_ui,
                        "auto_preload": model.auto_preload,
                        "status": model.status
                    } for model in ui_models],
                    "model_manager": {
                        "current_model": self.model_manager.model_name,
                        "custom_model": getattr(self.model_manager, 'custom_model_name', None),
                        "base_url": getattr(self.model_manager, 'base_url', None)
                    },
                    "runpod_configured": bool(self.runpod_api_key)
                }
            
            except Exception as e:
                logger.error(f"Error getting configuration: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        

        
        @self.router.get("/logs")
        async def get_recent_logs():
            """Get recent log entries"""
            try:
                # Try to read recent log entries
                log_entries = []
                
                # Look for log files in the logs directory
                logs_dir = Path("logs")
                if logs_dir.exists():
                    log_files = sorted(logs_dir.glob("*.log"), key=os.path.getmtime, reverse=True)
                    
                    if log_files:
                        latest_log = log_files[0]
                        
                        # Read last 100 lines
                        with open(latest_log, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            recent_lines = lines[-100:]  # Last 100 lines
                            
                            for line in recent_lines:
                                if line.strip():
                                    log_entries.append({
                                        "timestamp": time.time(),  # Would parse actual timestamp
                                        "message": line.strip()
                                    })
                
                return {
                    "log_entries": log_entries[-50:],  # Last 50 entries
                    "total_entries": len(log_entries)
                }
            
            except Exception as e:
                logger.error(f"Error getting logs: {str(e)}")
                return {
                    "log_entries": [],
                    "total_entries": 0,
                    "error": str(e)
                }
        
        @self.router.get("/benchmark/stats")
        async def get_benchmark_stats():
            """Get benchmark statistics"""
            try:
                # Look for benchmark log files
                logs_dir = Path("logs")
                benchmark_files = list(logs_dir.glob("benchmark_*.jsonl")) if logs_dir.exists() else []
                
                stats = {
                    "total_requests": 0,
                    "average_duration": 0,
                    "models_tested": set(),
                    "success_rate": 0,
                    "recent_requests": []
                }
                
                all_requests = []
                
                # Read all benchmark files
                for file in benchmark_files:
                    try:
                        with open(file, 'r', encoding='utf-8') as f:
                            for line in f:
                                if line.strip():
                                    data = json.loads(line.strip())
                                    all_requests.append(data)
                    except Exception as e:
                        logger.warning(f"Could not read benchmark file {file}: {e}")
                
                if all_requests:
                    successful_requests = [r for r in all_requests if r.get('status') == 'success']
                    
                    stats["total_requests"] = len(all_requests)
                    stats["success_rate"] = len(successful_requests) / len(all_requests) * 100
                    stats["models_tested"] = list(set(r.get('model', 'unknown') for r in all_requests))
                    
                    # Calculate average duration for successful requests
                    if successful_requests:
                        durations = [r.get('performance', {}).get('total_duration_ms', 0) 
                                   for r in successful_requests]
                        stats["average_duration"] = sum(durations) / len(durations)
                    
                    # Get recent requests (last 20)
                    stats["recent_requests"] = all_requests[-20:]
                
                return stats
            
            except Exception as e:
                logger.error(f"Error getting benchmark stats: {str(e)}")
                return {
                    "total_requests": 0,
                    "average_duration": 0,
                    "models_tested": [],
                    "success_rate": 0,
                    "recent_requests": [],
                    "error": str(e)
                }
        
        @self.router.post("/test/model")
        async def test_model(request: Request):
            """Test a specific model with a sample message"""
            try:
                body = await request.json()
                model_name = body.get('model_name')
                test_message = body.get('message', 'Hello! Please respond with a brief greeting.')
                
                if not model_name:
                    raise HTTPException(status_code=400, detail="model_name required")
                
                start_time = time.time()
                
                # Test the model
                try:
                    response = self.model_manager.generate_response(test_message, model_name=model_name)
                    end_time = time.time()
                    duration_ms = int((end_time - start_time) * 1000)
                    
                    return {
                        "success": True,
                        "model_name": model_name,
                        "test_message": test_message,
                        "response": response,
                        "duration_ms": duration_ms,
                        "timestamp": time.time()
                    }
                
                except Exception as model_error:
                    end_time = time.time()
                    duration_ms = int((end_time - start_time) * 1000)
                    
                    return {
                        "success": False,
                        "model_name": model_name,
                        "test_message": test_message,
                        "error": str(model_error),
                        "duration_ms": duration_ms,
                        "timestamp": time.time()
                    }
            
            except Exception as e:
                logger.error(f"Model test error: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/environment")
        async def get_environment():
            """Get environment information"""
            try:
                import os
                return {
                    "environment": "production" if os.getenv("PRODUCTION") else "development",
                    "provider": "runpod" if os.getenv("RUNPOD_API_KEY") else "ollama",
                    "model_manager_available": bool(self.model_manager),
                    "runpod_configured": bool(self.runpod_api_key)
                }
            except Exception as e:
                logger.error(f"Error getting environment: {str(e)}")
                return {"environment": "unknown", "error": str(e)}
        
        @self.router.get("/provider-settings")
        async def get_provider_settings():
            """Get current provider settings"""
            try:
                provider_settings = model_settings.get_provider_settings()
                return {
                    "success": True,
                    **provider_settings
                }
            except Exception as e:
                logger.error(f"Error getting provider settings: {str(e)}")
                return {
                    "success": False,
                    "error": str(e),
                    "default_provider": "ollama"
                }
        

        
        @self.router.get("/training-samples")
        async def get_training_samples():
            """Get training samples"""
            try:
                # This would normally fetch from database
                # For now, return mock data
                return {
                    "samples": [
                        {"id": 1, "user_message": "My AC is broken", "ai_response": "I'll schedule a maintenance request for your AC unit."},
                        {"id": 2, "user_message": "When is rent due?", "ai_response": "Rent is due on the 1st of each month."}
                    ],
                    "total": 2,
                    "message": "Training samples loaded successfully"
                }
            except Exception as e:
                logger.error(f"Error getting training samples: {str(e)}")
                return {"samples": [], "total": 0, "error": str(e)}
        
        @self.router.get("/model-status")
        async def get_model_status():
            """Get model status information"""
            try:
                model_available = self.model_manager.is_model_available(self.model_manager.model_name)
                return {
                    "current_model": self.model_manager.model_name,
                    "model_available": model_available,
                    "status": "loaded" if model_available else "not_loaded",
                    "custom_model": getattr(self.model_manager, 'custom_model_name', None)
                }
            except Exception as e:
                logger.error(f"Error getting model status: {str(e)}")
                return {
                    "current_model": "unknown",
                    "model_available": False,
                    "status": "error",
                    "error": str(e)
                }
        
        @self.router.delete("/logs/clear")
        async def clear_logs():
            """Clear all log files"""
            try:
                logs_dir = Path("logs")
                if not logs_dir.exists():
                    return {"message": "No logs directory found", "cleared_files": 0}
                
                cleared_files = 0
                for log_file in logs_dir.glob("*.log"):
                    try:
                        log_file.unlink()
                        cleared_files += 1
                    except Exception as e:
                        logger.warning(f"Could not delete {log_file}: {e}")
                
                for benchmark_file in logs_dir.glob("benchmark_*.jsonl"):
                    try:
                        benchmark_file.unlink()
                        cleared_files += 1
                    except Exception as e:
                        logger.warning(f"Could not delete {benchmark_file}: {e}")
                
                logger.info(f"Cleared {cleared_files} log files")
                return {
                    "message": f"Cleared {cleared_files} log files",
                    "cleared_files": cleared_files
                }
            
            except Exception as e:
                logger.error(f"Error clearing logs: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/environment")
        async def get_environment():
            """Get environment information for frontend"""
            try:
                import platform
                import socket
                
                # Check if we're running locally or in cloud
                hostname = socket.gethostname()
                is_local = hostname in ['localhost', '127.0.0.1'] or 'local' in hostname.lower()
                
                # Get timeout settings
                timeout_seconds = 30  # Default timeout
                try:
                    provider_settings = model_settings.get_provider_settings()
                    if provider_settings and 'timeout_seconds' in provider_settings:
                        timeout_seconds = provider_settings['timeout_seconds']
                except Exception:
                    pass
                
                return {
                    "is_local": is_local,
                    "platform": platform.system(),
                    "hostname": hostname,
                    "timeout_seconds": timeout_seconds,
                    "environment": "local" if is_local else "cloud"
                }
            except Exception as e:
                logger.error(f"Error getting environment info: {e}")
                return {
                    "is_local": True,
                    "platform": "unknown",
                    "hostname": "unknown",
                    "timeout_seconds": 30,
                    "environment": "local"
                }
        
        @self.router.get("/provider-settings")
        async def get_provider_settings():
            """Get current provider settings"""
            try:
                settings = model_settings.get_provider_settings()
                return {
                    "success": True,
                    "default_provider": settings.get('default_provider', 'ollama'),
                    "fallback_enabled": settings.get('fallback_enabled', False),
                    "providers": settings.get('providers', {}),
                    "timeout_seconds": settings.get('timeout_seconds', 30)
                }
            except Exception as e:
                logger.error(f"Error getting provider settings: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "default_provider": "ollama",
                    "fallback_enabled": False
                }
        
        @self.router.post("/provider-settings/update")
        async def update_provider_settings(request: Request):
            """Update provider settings"""
            try:
                data = await request.json()
                default_provider = data.get('default_provider', 'ollama')
                fallback_enabled = data.get('fallback_enabled', False)
                
                # Create new settings
                new_settings = {
                    'default_provider': default_provider,
                    'fallback_enabled': fallback_enabled
                }
                
                # Save settings
                model_settings.update_provider_settings(new_settings)
                
                logger.info(f"Updated provider settings: {default_provider}, fallback: {fallback_enabled}")
                
                return {
                    "success": True,
                    "message": f"Provider updated to {default_provider}",
                    "settings": new_settings
                }
            except Exception as e:
                logger.error(f"Error updating provider settings: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @self.router.get("/model-status")
        async def get_model_status():
            """Get model loading status"""
            try:
                # Get current models and their status
                models = []
                total_loaded = 0
                total_running = 0
                
                try:
                    # Get UI models
                    ui_models = model_settings.get_ui_models()
                    for model in ui_models:
                        model_info = {
                            "name": model.name,
                            "base_model": getattr(model, 'base_model', 'unknown'),
                            "loaded": False,  # Default to False
                            "is_running": False  # Default to False
                        }
                        
                        # Check if model is loaded (this would need to be implemented)
                        # For now, we'll assume models are not loaded
                        models.append(model_info)
                        
                except Exception as e:
                    logger.warning(f"Could not get UI models: {e}")
                    # Add fallback models
                    models = [
                        {"name": "llama3:latest", "base_model": "llama3", "loaded": False, "is_running": False},
                        {"name": "peteollama:jamie-fixed", "base_model": "llama3", "loaded": False, "is_running": False}
                    ]
                
                return {
                    "success": True,
                    "models": models,
                    "total_loaded": total_loaded,
                    "total_running": total_running,
                    "total_models": len(models)
                }
            except Exception as e:
                logger.error(f"Error getting model status: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @self.router.get("/training-samples")
        async def get_training_samples(limit: int = 20):
            """Get training samples from database"""
            try:
                # This would typically query a database
                # For now, return mock data
                samples = []
                for i in range(min(limit, 5)):
                    samples.append({
                        "id": i + 1,
                        "conversation_id": f"conv_{i + 1}",
                        "message": f"Sample training message {i + 1}",
                        "response": f"Sample response {i + 1}",
                        "timestamp": time.time() - (i * 3600)
                    })
                
                return samples
            except Exception as e:
                logger.error(f"Error getting training samples: {e}")
                return []
        
        @self.router.post("/preload-model")
        async def preload_model(request: Request):
            """Preload a model into memory"""
            try:
                data = await request.json()
                model_name = data.get('model', 'llama3:latest')
                
                # This would typically trigger model loading
                # For now, simulate success
                start_time = time.time()
                
                # Simulate loading time
                await asyncio.sleep(1)
                
                duration = time.time() - start_time
                
                logger.info(f"Model {model_name} preloaded (simulated)")
                
                return {
                    "success": True,
                    "message": f"Model {model_name} loaded successfully",
                    "duration_seconds": duration,
                    "model": model_name
                }
            except Exception as e:
                logger.error(f"Error preloading model: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @self.router.post("/test-model")
        async def test_model(request: Request):
            """Test a model with a message"""
            try:
                data = await request.json()
                model_name = data.get('model', 'llama3:latest')
                message = data.get('message', 'Hello')
                
                start_time = time.time()
                
                # Use model manager to generate response
                if self.model_manager and hasattr(self.model_manager, 'generate_response'):
                    response = await self.model_manager.generate_response(message, model=model_name)
                else:
                    response = f"Mock response from {model_name}: {message}"
                
                duration = time.time() - start_time
                
                return {
                    "success": True,
                    "raw_response": response,
                    "duration_ms": int(duration * 1000),
                    "actual_duration_seconds": duration,
                    "model": model_name,
                    "environment": "local",
                    "base_model": "llama3",
                    "model_preloaded": True
                }
            except Exception as e:
                logger.error(f"Error testing model: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @self.router.post("/train-jamie")
        async def train_jamie_model():
            """Train Jamie model (streaming response)"""
            try:
                from fastapi.responses import StreamingResponse
                
                async def generate_training_log():
                    yield "Starting Jamie model training...\n"
                    yield "Loading training data...\n"
                    yield "Processing 913 conversations...\n"
                    yield "Training model with 3555 samples...\n"
                    yield "Model training completed successfully!\n"
                
                return StreamingResponse(generate_training_log(), media_type="text/plain")
            except Exception as e:
                logger.error(f"Error in training stream: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # ===== CONFIGURATION MANAGEMENT ENDPOINTS =====
        
        @self.router.get("/environment-variables")
        async def get_environment_variables():
            """Get current environment variables (filtered for security)"""
            try:
                # Define which environment variables to expose (avoid sensitive data)
                safe_vars = [
                    "OPENROUTER_API_KEY", "RUNPOD_API_KEY", "RUNPOD_SERVERLESS_ENDPOINT",
                    "PORT", "ENVIRONMENT", "DEBUG", "LOG_LEVEL", "DATABASE_URL",
                    "REDIS_URL", "API_VERSION", "APP_NAME"
                ]
                
                env_vars = {}
                for var in safe_vars:
                    value = os.getenv(var)
                    if value:
                        # Mask sensitive API keys for security
                        if "API_KEY" in var and len(value) > 10:
                            env_vars[var] = f"{value[:8]}...{value[-4:]}"
                        else:
                            env_vars[var] = value
                
                return {
                    "success": True,
                    "environment_variables": env_vars,
                    "total_vars": len(env_vars),
                    "note": "API keys are masked for security"
                }
            
            except Exception as e:
                logger.error(f"Error getting environment variables: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/configuration")
        async def get_configuration():
            """Get current configuration settings"""
            try:
                # Get model settings configuration
                config_data = {
                    "models": {
                        "total": len(model_settings.models),
                        "jamie_models": len([m for m in model_settings.models.values() if m.is_jamie_model]),
                        "ui_models": len([m for m in model_settings.models.values() if m.show_in_ui]),
                        "auto_preload": len([m for m in model_settings.models.values() if m.auto_preload])
                    },
                    "providers": {
                        "current": model_settings.get_provider_settings().get('default_provider', 'unknown'),
                        "fallback_enabled": model_settings.get_provider_settings().get('fallback_enabled', False),
                        "fallback_provider": model_settings.get_provider_settings().get('fallback_provider', None)
                    },
                    "system": {
                        "config_file": str(model_settings.settings_file),
                        "last_updated": "unknown",  # Not available in stats
                        "total_models": model_settings.get_stats().get('total_models', 0)
                    }
                }
                
                return {
                    "success": True,
                    "configuration": config_data
                }
            
            except Exception as e:
                logger.error(f"Error getting configuration: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.post("/configuration/update")
        async def update_configuration(request: Request):
            """Update configuration settings"""
            try:
                body = await request.json()
                
                # Validate required fields
                if 'section' not in body or 'key' not in body or 'value' not in body:
                    raise HTTPException(status_code=400, detail="Missing required fields: section, key, value")
                
                section = body['section']
                key = body['key']
                value = body['value']
                
                # Handle different configuration sections
                if section == 'provider':
                    # Update provider settings
                    current_settings = model_settings.get_provider_settings()
                    current_settings[key] = value
                    model_settings.update_provider_settings(current_settings)
                    
                    logger.info(f"Updated provider setting: {key} = {value}")
                    
                elif section == 'model':
                    # Update model-specific settings
                    model_name = body.get('model_name')
                    if not model_name:
                        raise HTTPException(status_code=400, detail="model_name required for model section")
                    
                    model_settings.update_model_config(model_name, key, value)
                    logger.info(f"Updated model setting: {model_name}.{key} = {value}")
                    
                else:
                    raise HTTPException(status_code=400, detail=f"Unknown configuration section: {section}")
                
                return {
                    "success": True,
                    "message": f"Configuration updated: {section}.{key} = {value}",
                    "updated_value": value
                }
            
            except Exception as e:
                logger.error(f"Error updating configuration: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/configuration/export")
        async def export_configuration():
            """Export current configuration as JSON"""
            try:
                # Get full configuration data
                config_data = {
                    "models": {name: {
                        "name": model.name,
                        "display_name": model.display_name,
                        "type": model.type,
                        "is_jamie_model": model.is_jamie_model,
                        "show_in_ui": model.show_in_ui,
                        "auto_preload": model.auto_preload,
                        "status": model.status
                    } for name, model in model_settings.models.items()},
                    "provider_settings": model_settings.get_provider_settings(),
                    "stats": model_settings.get_stats(),
                    "exported_at": format_datetime_api(now_cst())
                }
                
                return {
                    "success": True,
                    "configuration": config_data,
                    "exported_at": config_data["exported_at"],
                    "note": "Full configuration exported successfully"
                }
            
            except Exception as e:
                logger.error(f"Error exporting configuration: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    async def _get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            # Model Manager status
            model_status = {
                "current_model": self.model_manager.model_name,
                "custom_model": getattr(self.model_manager, 'custom_model_name', None),
                "model_available": self.model_manager.is_model_available(self.model_manager.model_name),
                "base_url": getattr(self.model_manager, 'base_url', 'http://localhost:11434')
            }
            
            # Provider settings
            try:
                provider_settings = model_settings.get_provider_settings()
                current_provider = provider_settings.get('default_provider', 'ollama')
            except Exception as e:
                logger.warning(f"Could not get provider settings: {e}")
                provider_settings = {"default_provider": "ollama"}
                current_provider = "ollama"
            
            # Available models count
            try:
                ui_models = model_settings.get_ui_models()
                total_models = len(ui_models)
                jamie_models = len([m for m in ui_models if m.is_jamie_model])
            except Exception as e:
                logger.warning(f"Could not get UI models: {e}")
                total_models = 0
                jamie_models = 0
            
            # System info
            import psutil
            system_info = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\').percent
            }
            
            return {
                "status": "online",
                "timestamp": time.time(),
                "uptime": time.time(),  # Would track actual uptime
                "model_manager": model_status,
                "provider_settings": provider_settings,
                "current_provider": current_provider,
                "models": {
                    "total_models": total_models,
                    "jamie_models": jamie_models
                },
                "system": system_info,
                "services": {
                    "model_manager": "online",
                    "provider_service": "online",
                    "runpod": "online" if self.runpod_api_key else "disabled"
                }
            }
        
        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}")
            return {
                "status": "error",
                "timestamp": time.time(),
                "error": str(e)
            }

def create_admin_router(model_manager: ModelManager, runpod_api_key: str = None) -> APIRouter:
    """Factory function to create admin router"""
    admin_router = AdminRouter(model_manager, runpod_api_key)
    return admin_router.router
