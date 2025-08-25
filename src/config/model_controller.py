#!/usr/bin/env python3
"""
Model Controller - Full Control Over Model Visibility and Behavior
================================================================

This controller gives you complete control over which models appear in the UI,
bypassing auto-discovery when needed and enforcing your manual settings.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger
import subprocess

class ModelController:
    """Full control over model visibility and behavior"""
    
    def __init__(self, control_file: str = "src/config/model_control.json"):
        self.control_file = Path(control_file)
        self.control_config = self._load_control_config()
        self.ollama_models = self._get_ollama_models()
        
    def _load_control_config(self) -> Dict:
        """Load the model control configuration"""
        try:
            if self.control_file.exists():
                with open(self.control_file, 'r') as f:
                    config = json.load(f)
                    logger.info(f"📋 Model Controller: Loaded control config with {len(config.get('models', {}))} models")
                    return config
            else:
                logger.warning(f"📋 Model Controller: Control file not found: {self.control_file}")
                return {"model_control": {"enabled": False}, "models": {}}
        except Exception as e:
            logger.error(f"📋 Model Controller: Error loading control config: {e}")
            return {"model_control": {"enabled": False}, "models": {}}
    
    def _get_ollama_models(self) -> List[str]:
        """Get list of available models from Ollama"""
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                models = [line.split()[0] for line in lines if line.strip()]
                logger.info(f"📋 Model Controller: Found {len(models)} models in Ollama")
                return models
            else:
                logger.error(f"📋 Model Controller: Ollama list failed: {result.stderr}")
                return []
        except Exception as e:
            logger.error(f"📋 Model Controller: Error getting Ollama models: {e}")
            return []
    
    def is_control_enabled(self) -> bool:
        """Check if manual model control is enabled"""
        return self.control_config.get("model_control", {}).get("enabled", False)
    
    def get_visible_models(self) -> List[Dict[str, Any]]:
        """Get models that should be visible in the UI"""
        if not self.is_control_enabled():
            logger.info("📋 Model Controller: Control disabled, using auto-discovery")
            return self._get_auto_discovery_models()
        
        logger.info("📋 Model Controller: Using manual control settings")
        visible_models = []
        
        for model_name, config in self.control_config.get("models", {}).items():
            # Check if model exists in Ollama
            if model_name not in self.ollama_models:
                logger.warning(f"📋 Model Controller: Model {model_name} not found in Ollama, skipping")
                continue
            
            # Check if model should be visible
            if config.get("show_in_ui", False) or config.get("force_visible", False):
                # Merge with current Ollama info
                model_info = {
                    **config,
                    "status": "available" if model_name in self.ollama_models else "unavailable",
                    "last_updated": datetime.now().isoformat()
                }
                visible_models.append(model_info)
                logger.info(f"📋 Model Controller: Model {model_name} marked as visible")
        
        # Sort by priority
        visible_models.sort(key=lambda x: x.get("priority", 999))
        
        logger.info(f"📋 Model Controller: Returning {len(visible_models)} visible models")
        return visible_models
    
    def _get_auto_discovery_models(self) -> List[Dict[str, Any]]:
        """Fallback to auto-discovery when control is disabled"""
        try:
            from ..utils.enhanced_model_discovery import enhanced_discovery
            discovered_models = enhanced_discovery.discover_available_models()
            
            # Filter to only show UI models
            ui_models = []
            for model in discovered_models:
                if model.get("show_in_ui", False):
                    ui_models.append(model)
            
            return ui_models
        except Exception as e:
            logger.error(f"📋 Model Controller: Auto-discovery failed: {e}")
            return []
    
    def get_model_config(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific model"""
        if not self.is_control_enabled():
            return None
        
        return self.control_config.get("models", {}).get(model_name)
    
    def update_model_config(self, model_name: str, **kwargs) -> bool:
        """Update configuration for a model"""
        if not self.is_control_enabled():
            logger.warning("📋 Model Controller: Cannot update config when control is disabled")
            return False
        
        try:
            if "models" not in self.control_config:
                self.control_config["models"] = {}
            
            if model_name not in self.control_config["models"]:
                self.control_config["models"][model_name] = {}
            
            # Update the model config
            for key, value in kwargs.items():
                self.control_config["models"][model_name][key] = value
            
            # Update timestamp
            self.control_config["models"][model_name]["last_updated"] = datetime.now().isoformat()
            self.control_config["last_updated"] = datetime.now().isoformat()
            
            # Save the updated config
            with open(self.control_file, 'w') as f:
                json.dump(self.control_config, f, indent=2)
            
            logger.info(f"📋 Model Controller: Updated config for {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"📋 Model Controller: Error updating config for {model_name}: {e}")
            return False
    
    def force_model_visible(self, model_name: str, visible: bool = True) -> bool:
        """Force a model to be visible or hidden"""
        return self.update_model_config(model_name, force_visible=visible, show_in_ui=visible)
    
    def get_default_model(self) -> Optional[str]:
        """Get the default model from control config"""
        if not self.is_control_enabled():
            return None
        
        return self.control_config.get("ui_settings", {}).get("default_model")
    
    def refresh_ollama_models(self) -> List[str]:
        """Refresh the list of available Ollama models"""
        self.ollama_models = self._get_ollama_models()
        return self.ollama_models

# Global instance
model_controller = ModelController()
