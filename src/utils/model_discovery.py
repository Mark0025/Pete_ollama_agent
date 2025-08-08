#!/usr/bin/env python3
"""
Dynamic Model Discovery System
=============================

Discovers available models in Ollama and syncs with configuration.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List
from loguru import logger


class ModelDiscovery:
    def __init__(self, config_path: str = "config/model_settings.json"):
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load the current model configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            return {"models": {}, "default_model": None}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            return {"models": {}, "default_model": None}
    
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
                logger.info(f"Discovered {len(models)} available models: {models}")
                return models
            else:
                logger.error(f"Ollama list failed: {result.stderr}")
                return []
        except Exception as e:
            logger.error(f"Error discovering models: {e}")
            return []
    
    def sync_config_with_reality(self):
        """Sync configuration with actually available models"""
        available_models = self.discover_available_models()
        
        # Update status for each model in config
        for model_name, model_config in self.config['models'].items():
            if model_name in available_models:
                model_config['status'] = 'available'
                logger.debug(f"Model {model_name} is available")
            else:
                model_config['status'] = 'missing'
                logger.debug(f"Model {model_name} is missing")
        
        # Save updated config
        self.save_config()
        logger.info("Configuration synced with available models")
    
    def create_model_from_config(self, model_name: str) -> bool:
        """Create a model based on configuration"""
        if model_name not in self.config['models']:
            logger.error(f"Model {model_name} not found in configuration")
            return False
        
        model_config = self.config['models'][model_name]
        modelfile_path = model_config.get('modelfile')
        
        if not modelfile_path:
            logger.error(f"No modelfile specified for {model_name}")
            return False
        
        if not Path(modelfile_path).exists():
            logger.error(f"Modelfile not found: {modelfile_path}")
            return False
        
        try:
            logger.info(f"Creating model {model_name} from {modelfile_path}")
            # Create the model using ollama
            result = subprocess.run([
                'ollama', 'create', model_name, '-f', modelfile_path
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                model_config['status'] = 'available'
                self.save_config()
                logger.info(f"Model {model_name} created successfully")
                return True
            else:
                logger.error(f"Error creating model {model_name}: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error creating model {model_name}: {e}")
            return False
    
    def get_model_info(self, model_name: str) -> Dict:
        """Get detailed information about a model"""
        if model_name not in self.config['models']:
            return {}
        
        model_config = self.config['models'][model_name]
        
        # Check if model is actually available
        available_models = self.discover_available_models()
        model_config['status'] = 'available' if model_name in available_models else 'missing'
        
        return model_config
    
    def get_ui_models(self) -> List[Dict]:
        """Get models that should be shown in UI"""
        self.sync_config_with_reality()
        
        ui_models = []
        for model_name, model_config in self.config['models'].items():
            if model_config.get('show_in_ui', False) and model_config.get('status') == 'available':
                ui_models.append({
                    'name': model_name,
                    'display_name': model_config.get('display_name', model_name),
                    'description': model_config.get('description', ''),
                    'version': model_config.get('version', ''),
                    'base_model': model_config.get('base_model', ''),
                    'auto_preload': model_config.get('auto_preload', False)
                })
        
        return ui_models
    
    def save_config(self):
        """Save the updated configuration"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")


def main():
    """Test the model discovery system"""
    discovery = ModelDiscovery()
    
    print("=== Model Discovery Test ===")
    print(f"Available models: {discovery.discover_available_models()}")
    
    discovery.sync_config_with_reality()
    
    print("\n=== UI Models ===")
    ui_models = discovery.get_ui_models()
    for model in ui_models:
        print(f"- {model['display_name']} ({model['name']})")


if __name__ == "__main__":
    main() 