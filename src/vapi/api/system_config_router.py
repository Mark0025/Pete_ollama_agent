#!/usr/bin/env python3
"""
System Configuration Router
==========================

Admin API endpoints for managing the centralized system configuration.
Provides full control over caching, providers, and models from a single interface.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import HTMLResponse
from typing import Dict, Any, Optional
from pydantic import BaseModel
from pathlib import Path
from utils.logger import logger

# Import the system config manager
from config.system_config import system_config, CachingConfig, ProviderConfig, ModelConfig

class CachingConfigUpdate(BaseModel):
    """Model for updating caching configuration"""
    enabled: Optional[bool] = None
    threshold: Optional[float] = None
    max_cache_age_hours: Optional[int] = None
    max_responses: Optional[int] = None
    similarity_analyzer_enabled: Optional[bool] = None
    fallback_cache_enabled: Optional[bool] = None

class ProviderConfigUpdate(BaseModel):
    """Model for updating provider configuration"""
    enabled: Optional[bool] = None
    priority: Optional[int] = None
    caching: Optional[CachingConfigUpdate] = None
    timeout: Optional[int] = None
    max_retries: Optional[int] = None

class ModelConfigUpdate(BaseModel):
    """Model for updating model configuration"""
    enabled: Optional[bool] = None
    caching: Optional[CachingConfigUpdate] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    context_length: Optional[int] = None

class SystemConfigUpdate(BaseModel):
    """Model for updating system configuration"""
    default_provider: Optional[str] = None
    fallback_enabled: Optional[bool] = None
    fallback_provider: Optional[str] = None
    auto_switch: Optional[bool] = None
    debug: Optional[bool] = None
    log_level: Optional[str] = None

def create_system_config_router() -> APIRouter:
    """Create the system configuration router"""
    router = APIRouter(prefix="/admin/system-config", tags=["System Configuration"])
    
    @router.get("/ui", response_class=HTMLResponse)
    async def system_config_ui():
        """Serve the system configuration UI"""
        try:
            html_file = Path(__file__).parent.parent.parent / "frontend" / "html" / "system-config-ui.html"
            if html_file.exists():
                with open(html_file, 'r') as f:
                    content = f.read()
                return HTMLResponse(content=content)
            else:
                return HTMLResponse(content="<h1>System Config UI</h1><p>System config UI not found</p>")
        except Exception as e:
            logger.error(f"Error loading system config UI: {e}")
            return HTMLResponse(content="<h1>System Config UI</h1><p>Error loading system config UI</p>")
    
    @router.get("/")
    async def get_system_config():
        """Get the complete system configuration"""
        try:
            config_summary = system_config.get_config_summary()
            return {
                "success": True,
                "configuration": config_summary,
                "message": "System configuration retrieved successfully"
            }
        except Exception as e:
            logger.error(f"Error getting system configuration: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/caching")
    async def get_caching_config(provider: Optional[str] = None, model: Optional[str] = None):
        """Get caching configuration for a specific provider/model combination"""
        try:
            caching_config = system_config.get_caching_config(provider, model)
            return {
                "success": True,
                "caching_config": {
                    "enabled": caching_config.enabled,
                    "threshold": caching_config.threshold,
                    "max_cache_age_hours": caching_config.max_cache_age_hours,
                    "max_responses": caching_config.max_responses,
                    "similarity_analyzer_enabled": caching_config.similarity_analyzer_enabled,
                    "fallback_cache_enabled": caching_config.fallback_cache_enabled
                },
                "context": {
                    "provider": provider,
                    "model": model,
                    "note": "Configuration merges global → provider → model settings"
                }
            }
        except Exception as e:
            logger.error(f"Error getting caching configuration: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.put("/global-caching")
    async def update_global_caching(config: CachingConfigUpdate):
        """Update global caching configuration"""
        try:
            # Update global caching settings
            global_caching = system_config.config.global_caching
            for key, value in config.dict(exclude_unset=True).items():
                if hasattr(global_caching, key):
                    setattr(global_caching, key, value)
            
            # Save configuration
            if system_config.save_config():
                logger.info(f"✅ Updated global caching configuration: {config.dict(exclude_unset=True)}")
                return {
                    "success": True,
                    "message": "Global caching configuration updated successfully",
                    "updated_settings": config.dict(exclude_unset=True)
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to save configuration")
                
        except Exception as e:
            logger.error(f"Error updating global caching configuration: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.put("/providers/{provider_name}")
    async def update_provider_config(provider_name: str, config: ProviderConfigUpdate):
        """Update provider configuration"""
        try:
            if provider_name not in system_config.config.providers:
                raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")
            
            # Update provider configuration
            if system_config.update_provider_config(provider_name, **config.dict(exclude_unset=True)):
                logger.info(f"✅ Updated provider configuration for {provider_name}: {config.dict(exclude_unset=True)}")
                return {
                    "success": True,
                    "message": f"Provider '{provider_name}' configuration updated successfully",
                    "updated_settings": config.dict(exclude_unset=True)
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to save configuration")
                
        except Exception as e:
            logger.error(f"Error updating provider configuration: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.put("/models/{model_name}")
    async def update_model_config(model_name: str, config: ModelConfigUpdate):
        """Update model configuration"""
        try:
            if model_name not in system_config.config.models:
                raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
            
            # Update model configuration
            if system_config.update_model_config(model_name, **config.dict(exclude_unset=True)):
                logger.info(f"✅ Updated model configuration for {model_name}: {config.dict(exclude_unset=True)}")
                return {
                    "success": True,
                    "message": f"Model '{model_name}' configuration updated successfully",
                    "updated_settings": config.dict(exclude_unset=True)
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to save configuration")
                
        except Exception as e:
            logger.error(f"Error updating model configuration: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.put("/system")
    async def update_system_config(config: SystemConfigUpdate):
        """Update system-level configuration"""
        try:
            # Update system settings
            for key, value in config.dict(exclude_unset=True).items():
                if hasattr(system_config.config, key):
                    setattr(system_config.config, key, value)
            
            # Save configuration
            if system_config.save_config():
                logger.info(f"✅ Updated system configuration: {config.dict(exclude_unset=True)}")
                return {
                    "success": True,
                    "message": "System configuration updated successfully",
                    "updated_settings": config.dict(exclude_unset=True)
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to save configuration")
                
        except Exception as e:
            logger.error(f"Error updating system configuration: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/reset")
    async def reset_to_defaults():
        """Reset configuration to defaults"""
        try:
            # Reinitialize with defaults
            system_config.__init__()
            logger.info("✅ Reset system configuration to defaults")
            return {
                "success": True,
                "message": "System configuration reset to defaults successfully"
            }
        except Exception as e:
            logger.error(f"Error resetting system configuration: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.get("/export")
    async def export_config():
        """Export current configuration as JSON"""
        try:
            config_data = system_config.get_config_summary()
            return {
                "success": True,
                "configuration": config_data,
                "exported_at": "2025-08-19T17:20:00Z",  # TODO: Use proper datetime
                "format": "JSON",
                "note": "This configuration can be imported or used for backup"
            }
        except Exception as e:
            logger.error(f"Error exporting configuration: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @router.post("/import")
    async def import_config(config_data: Dict[str, Any]):
        """Import configuration from JSON"""
        try:
            # TODO: Implement configuration import with validation
            logger.info("⚠️ Configuration import not yet implemented")
            return {
                "success": False,
                "message": "Configuration import not yet implemented",
                "note": "This endpoint will allow importing configuration from JSON files"
            }
        except Exception as e:
            logger.error(f"Error importing configuration: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return router
