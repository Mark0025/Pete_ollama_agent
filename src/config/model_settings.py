"""
Model Settings Manager for controlling UI visibility and preloading.
"""
import json
import os
from typing import Dict, List, Optional
from pathlib import Path
from loguru import logger
from dataclasses import dataclass, asdict
from datetime import datetime
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.enhanced_model_discovery import enhanced_discovery

@dataclass
class ModelConfig:
    """Configuration for a single model."""
    name: str
    display_name: str
    description: str
    show_in_ui: bool = False
    auto_preload: bool = False
    is_jamie_model: bool = False
    base_model: str = "unknown"
    type: str = "unknown"
    size: str = "unknown"
    status: str = "unknown"
    # Response Control Settings (controlled by admin panel)
    conversational_mode: bool = True      # Only give clean answers, no internal thinking
    max_response_length: int = 200       # Limit response length for VAPI
    include_thinking: bool = False       # Show internal reasoning process
    include_model_info: bool = False     # Show model configuration details
    response_style: str = "concise"      # concise, detailed, or verbose
    created_at: str = ""
    last_updated: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.last_updated = datetime.now().isoformat()

class ModelSettingsManager:
    """Manages model settings and UI visibility."""
    
    def __init__(self, settings_file: str = "config/model_settings.json"):
        self.settings_file = Path(settings_file)
        self.settings_file.parent.mkdir(exist_ok=True)
        self.models: Dict[str, ModelConfig] = {}
        self.load_settings()
        self._init_default_models()
    
    def load_settings(self) -> None:
        """Load model settings from file."""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                    self.models = {}
                    for name, config in data.get('models', {}).items():
                        # Filter out any unexpected fields that aren't in ModelConfig
                        valid_fields = {k: v for k, v in config.items() 
                                      if k in ModelConfig.__annotations__}
                        try:
                            self.models[name] = ModelConfig(**valid_fields)
                        except Exception as e:
                            logger.warning(f"Skipping invalid model config for {name}: {e}")
                            continue
                logger.info(f"Loaded settings for {len(self.models)} models")
            else:
                logger.info("No existing model settings found, will create defaults")
        except Exception as e:
            logger.error(f"Error loading model settings: {e}")
            self.models = {}
    
    def save_settings(self) -> bool:
        """Save model settings to file."""
        try:
            data = {
                'models': {name: asdict(config) for name, config in self.models.items()},
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.settings_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved settings for {len(self.models)} models")
            return True
        except Exception as e:
            logger.error(f"Error saving model settings: {e}")
            return False
    
    def _init_default_models(self) -> None:
        """Initialize default model configurations."""
        default_models = [
            {
                "name": "peteollama:jamie-fixed",
                "display_name": "Jamie Fixed (Latest)",
                "description": "Latest stable Jamie model with bug fixes",
                "show_in_ui": True,
                "auto_preload": True,
                "is_jamie_model": True,
                "base_model": "llama3:latest",
                "type": "jamie",
                "size": "unknown",
                "status": "unknown",
                "conversational_mode": True,
                "max_response_length": 200,
                "include_thinking": False,
                "include_model_info": False,
                "response_style": "concise"
            },
            {
                "name": "peteollama:jamie-voice-complete",
                "display_name": "Jamie Voice Complete",
                "description": "Jamie model optimized for voice interactions",
                "show_in_ui": True,
                "auto_preload": False,
                "is_jamie_model": True,
                "base_model": "llama3:latest",
                "type": "jamie",
                "size": "unknown",
                "status": "unknown"
            },
            {
                "name": "peteollama:jamie-simple",
                "display_name": "Jamie Simple",
                "description": "Lightweight Jamie model for basic tasks",
                "show_in_ui": False,
                "auto_preload": False,
                "is_jamie_model": True,
                "base_model": "llama3:latest",
                "type": "jamie",
                "size": "unknown",
                "status": "unknown"
            },
            {
                "name": "peteollama:jamie-working-working_20250806",
                "display_name": "Jamie Working (Legacy)",
                "description": "Legacy working version of Jamie",
                "show_in_ui": False,
                "auto_preload": False,
                "is_jamie_model": True,
                "base_model": "llama3:latest",
                "type": "jamie",
                "size": "unknown",
                "status": "unknown"
            },
            {
                "name": "llama3:latest",
                "display_name": "Base Model (Llama3)",
                "description": "Base Llama3 model for comparison",
                "show_in_ui": False,
                "auto_preload": False,
                "is_jamie_model": False,
                "base_model": "llama3:latest",
                "type": "llama3",
                "size": "unknown",
                "status": "unknown"
            }
        ]
        
        # Only add models that don't already exist
        added_count = 0
        for model_data in default_models:
            if model_data["name"] not in self.models:
                self.models[model_data["name"]] = ModelConfig(**model_data)
                added_count += 1
        
        if added_count > 0:
            logger.info(f"Added {added_count} default model configurations")
            self.save_settings()
    
    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """Get configuration for a specific model."""
        return self.models.get(model_name)
    
    def update_model_config(self, model_name: str, **kwargs) -> bool:
        """Update configuration for a model."""
        try:
            if model_name in self.models:
                config = self.models[model_name]
                for key, value in kwargs.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
                config.last_updated = datetime.now().isoformat()
            else:
                # Create new model config
                self.models[model_name] = ModelConfig(
                    name=model_name,
                    display_name=kwargs.get('display_name', model_name),
                    description=kwargs.get('description', ''),
                    **{k: v for k, v in kwargs.items() if k not in ['display_name', 'description']}
                )
            
            return self.save_settings()
        except Exception as e:
            logger.error(f"Error updating model config for {model_name}: {e}")
            return False
    
    def get_ui_models(self) -> List[ModelConfig]:
        """Get all models that should be shown in the UI."""
        return [config for config in self.models.values() if config.show_in_ui]
    
    def get_jamie_models(self) -> List[ModelConfig]:
        """Get all Jamie model variants."""
        return [config for config in self.models.values() if config.is_jamie_model]
    
    def get_auto_preload_models(self) -> List[ModelConfig]:
        """Get models that should be auto-preloaded."""
        return [config for config in self.models.values() if config.auto_preload]
    
    def toggle_ui_visibility(self, model_name: str) -> bool:
        """Toggle UI visibility for a model."""
        if model_name in self.models:
            current = self.models[model_name].show_in_ui
            return self.update_model_config(model_name, show_in_ui=not current)
        return False
    
    def toggle_auto_preload(self, model_name: str) -> bool:
        """Toggle auto-preload setting for a model."""
        if model_name in self.models:
            current = self.models[model_name].auto_preload
            return self.update_model_config(model_name, auto_preload=not current)
        return False
    
    def get_all_models(self) -> Dict[str, ModelConfig]:
        """Get all model configurations."""
        return self.models.copy()
    
    def get_stats(self) -> Dict:
        """Get statistics about model configurations."""
        total = len(self.models)
        ui_visible = len(self.get_ui_models())
        jamie_models = len(self.get_jamie_models())
        auto_preload = len(self.get_auto_preload_models())
        
        return {
            "total_models": total,
            "ui_visible": ui_visible,
            "jamie_models": jamie_models,
            "auto_preload": auto_preload,
            "base_models": total - jamie_models
        }
    
    def sync_with_discovered_models(self) -> bool:
        """Sync configuration with models discovered from ollama list"""
        try:
            # Discover available models
            discovered_models = enhanced_discovery.discover_available_models()
            
            if not discovered_models:
                logger.warning("No models discovered from ollama list")
                return False
            
            # Generate current config dict
            current_config = {
                "models": {name: asdict(config) for name, config in self.models.items()},
                "default_model": getattr(self, 'default_model', None)
            }
            
            # Sync with discovered models
            synced_config = enhanced_discovery.sync_with_existing_config(
                current_config, discovered_models
            )
            
            # Update internal models
            for model_name, config_data in synced_config["models"].items():
                if model_name not in self.models:
                    # Create new model config
                    self.models[model_name] = ModelConfig(**config_data)
                else:
                    # Update existing config with new info
                    existing = self.models[model_name]
                    for key, value in config_data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
            
            # Update default model
            if synced_config.get("default_model"):
                self.default_model = synced_config["default_model"]
            
            # Save updated settings
            self.save_settings()
            
            logger.info(f"Synced {len(discovered_models)} discovered models with configuration")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing with discovered models: {e}")
            return False
    
    def refresh_from_ollama(self) -> bool:
        """Refresh model list from ollama list command"""
        return self.sync_with_discovered_models()
    
    def get_provider_settings(self) -> Dict:
        """Get current provider configuration settings."""
        try:
            # Load provider settings from the same config file
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                    provider_settings = data.get('provider_settings', {})
                    
                    # Return with defaults if missing
                    return {
                        "default_provider": provider_settings.get("default_provider", "ollama"),
                        "fallback_provider": provider_settings.get("fallback_provider", "runpod"),
                        "fallback_enabled": provider_settings.get("fallback_enabled", False)
                    }
            
            # Return defaults if file doesn't exist
            return {
                "default_provider": "ollama",
                "fallback_provider": "runpod", 
                "fallback_enabled": False
            }
            
        except Exception as e:
            logger.error(f"Error loading provider settings: {e}")
            # Return safe defaults on error
            return {
                "default_provider": "ollama",
                "fallback_provider": "runpod",
                "fallback_enabled": False
            }
    
    def update_provider_settings(self, settings: Dict) -> bool:
        """Update provider configuration settings."""
        try:
            # Load existing config or create new one
            config_data = {}
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    config_data = json.load(f)
            
            # Update provider settings section
            if 'provider_settings' not in config_data:
                config_data['provider_settings'] = {}
            
            # Update with new settings
            config_data['provider_settings'].update(settings)
            config_data['provider_settings']['last_updated'] = datetime.now().isoformat()
            
            # Validate provider names
            valid_providers = ["ollama", "runpod", "openrouter"]
            default_provider = config_data['provider_settings'].get('default_provider')
            if default_provider and default_provider not in valid_providers:
                logger.error(f"Invalid default provider: {default_provider}")
                return False
            
            fallback_provider = config_data['provider_settings'].get('fallback_provider')
            if fallback_provider and fallback_provider not in valid_providers:
                logger.error(f"Invalid fallback provider: {fallback_provider}")
                return False
            
            # Save updated config
            with open(self.settings_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info(f"Updated provider settings: {settings}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating provider settings: {e}")
            return False

# Global settings manager instance
model_settings = ModelSettingsManager()
