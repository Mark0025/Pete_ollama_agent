#!/usr/bin/env python3
"""
Enhanced Dynamic Model Discovery System
======================================

Dynamically discovers available models in Ollama and auto-generates
configurations based on actual model availability.
"""

import json
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from loguru import logger


class EnhancedModelDiscovery:
    """Enhanced model discovery with auto-configuration generation"""
    
    def __init__(self):
        self.ollama_host = "localhost:11434"
        
    def discover_available_models(self) -> List[Dict]:
        """Discover all models available in Ollama with detailed info"""
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            if result.returncode == 0:
                models = []
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                
                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            model_name = parts[0]
                            size = parts[1] if len(parts) > 1 else "Unknown"
                            modified = " ".join(parts[2:]) if len(parts) > 2 else "Unknown"
                            
                            # Determine model type and base
                            model_type, base_model = self._analyze_model_name(model_name)
                            
                            models.append({
                                "name": model_name,
                                "size": size,
                                "modified": modified,
                                "type": model_type,
                                "base_model": base_model,
                                "is_jamie_model": "jamie" in model_name.lower() or "peteollama" in model_name.lower(),
                                "is_base_model": self._is_base_model(model_name),
                                "status": "available"
                            })
                
                logger.info(f"Discovered {len(models)} available models")
                return models
            else:
                logger.error(f"Ollama list failed: {result.stderr}")
                return []
                
        except Exception as e:
            logger.error(f"Error discovering models: {e}")
            return []
    
    def _analyze_model_name(self, model_name: str) -> Tuple[str, str]:
        """Analyze model name to determine type and base model"""
        model_lower = model_name.lower()
        
        # Determine model type
        if "jamie" in model_lower:
            model_type = "jamie"
        elif "vapipmv1" in model_lower:
            model_type = "vapi-pm"
        elif "property-manager" in model_lower:
            model_type = "property-manager"
        elif "llama3" in model_lower:
            model_type = "llama3"
        elif "qwen" in model_lower:
            model_type = "qwen"
        elif "mistral" in model_lower:
            model_type = "mistral"
        elif "codellama" in model_lower:
            model_type = "codellama"
        elif "phi" in model_lower:
            model_type = "phi"
        else:
            model_type = "other"
        
        # Determine base model
        if "llama3" in model_lower:
            base_model = "llama3:latest"
        elif "qwen" in model_lower:
            base_model = "qwen3:30b" if "30b" in model_lower else "qwen"
        elif "mistral" in model_lower:
            base_model = "mistral:7b"
        elif "codellama" in model_lower:
            base_model = "codellama:7b"
        elif "phi" in model_lower:
            base_model = "phi3:latest"
        elif "vapipmv1" in model_lower:
            base_model = "llama2:7b"
        else:
            base_model = "unknown"
        
        return model_type, base_model
    
    def _is_base_model(self, model_name: str) -> bool:
        """Check if model is a base model (not custom trained)"""
        base_models = [
            "llama3:latest",
            "qwen3:30b", 
            "mistral:7b",
            "codellama:7b",
            "phi3:latest"
        ]
        return model_name in base_models
    
    def generate_model_configs(self, models: List[Dict]) -> Dict:
        """Generate model configurations based on discovered models"""
        configs = {}
        
        for model in models:
            model_name = model["name"]
            
            # Generate display name
            display_name = self._generate_display_name(model)
            
            # Generate description
            description = self._generate_description(model)
            
            # Determine UI settings
            show_in_ui = self._should_show_in_ui(model)
            auto_preload = self._should_auto_preload(model)
            
            configs[model_name] = {
                "name": model_name,
                "display_name": display_name,
                "description": description,
                "show_in_ui": show_in_ui,
                "auto_preload": auto_preload,
                "is_jamie_model": model["is_jamie_model"],
                "base_model": model["base_model"],
                "type": model["type"],
                "size": model["size"],
                "status": model["status"],
                "created_at": model.get("modified", datetime.now().isoformat()),
                "last_updated": datetime.now().isoformat()
            }
        
        return configs
    
    def _generate_display_name(self, model: Dict) -> str:
        """Generate a user-friendly display name for the model"""
        name = model["name"]
        model_type = model["type"]
        
        if model_type == "jamie":
            if "v" in name and re.search(r'v\d+\.\d+', name):
                version = re.search(r'v\d+\.\d+', name).group()
                return f"Jamie Property Manager {version}"
            elif "enhanced" in name:
                return "Jamie Enhanced (Legacy)"
            else:
                return "Jamie Property Manager"
        elif model_type == "property-manager":
            if "v" in name and re.search(r'v\d+\.\d+', name):
                version = re.search(r'v\d+\.\d+', name).group()
                return f"Property Manager {version}"
            else:
                return "Property Manager (Legacy)"
        elif model_type == "llama3":
            return "Llama 3 (Base Model)"
        elif model_type == "qwen":
            return "Qwen 3 (Base Model)"
        else:
            return name.replace(":", " - ").title()
    
    def _generate_description(self, model: Dict) -> str:
        """Generate a description for the model"""
        model_type = model["type"]
        base_model = model["base_model"]
        
        if model_type == "jamie":
            return f"AI property manager trained on real conversations, based on {base_model}"
        elif model_type == "vapi-pm":
            return f"Professional property management assistant for Nolen Properties, handles tenant inquiries, maintenance requests, and complaints"
        elif model_type == "property-manager":
            return f"Property management AI model based on {base_model}"
        elif model_type == "llama3":
            return "Meta's Llama 3 base model for AI applications"
        elif model_type == "qwen":
            return "Alibaba's Qwen base model for AI applications"
        else:
            return f"AI model based on {base_model}"
    
    def _should_show_in_ui(self, model: Dict) -> bool:
        """Determine if model should be shown in UI"""
        # Show all jamie/property-manager models
        if model["is_jamie_model"]:
            return True
        
        # Show VAPI PM models specifically
        if "vapipmv1" in model["name"].lower():
            return True
        
        # Show base models for comparison
        if model["is_base_model"]:
            return True
        
        # Hide other models by default
        return False
    
    def _should_auto_preload(self, model: Dict) -> bool:
        """Determine if model should be auto-preloaded"""
        # Auto-preload the latest jamie model
        if model["is_jamie_model"] and "v" in model["name"]:
            return True
        
        # Auto-preload VAPI PM models
        if "vapipmv1" in model["name"].lower():
            return True
        
        # Auto-preload base models
        if model["is_base_model"]:
            return True
        
        return False
    
    def get_recommended_default_model(self, models: List[Dict]) -> Optional[str]:
        """Get the recommended default model for the system"""
        # Priority: latest jamie model, then base llama3
        jamie_models = [m for m in models if m["is_jamie_model"] and "v" in m["name"]]
        
        if jamie_models:
            # Sort by version number and return latest
            sorted_models = sorted(jamie_models, key=lambda x: self._extract_version(x["name"]), reverse=True)
            return sorted_models[0]["name"]
        
        # Fallback to llama3:latest
        for model in models:
            if model["name"] == "llama3:latest":
                return model["name"]
        
        return None
    
    def _extract_version(self, model_name: str) -> Tuple[int, int, int]:
        """Extract version numbers for sorting"""
        version_match = re.search(r'v(\d+)\.(\d+)', model_name)
        if version_match:
            major = int(version_match.group(1))
            minor = int(version_match.group(2))
            return (major, minor, 0)
        return (0, 0, 0)
    
    def sync_with_existing_config(self, existing_config: Dict, discovered_models: List[Dict]) -> Dict:
        """Sync discovered models with existing configuration"""
        # Generate new configs for discovered models
        new_configs = self.generate_model_configs(discovered_models)
        
        # Merge with existing config, preserving user preferences
        merged_configs = {}
        
        for model_name, new_config in new_configs.items():
            if model_name in existing_config.get("models", {}):
                # Preserve user preferences from existing config
                existing = existing_config["models"][model_name]
                merged_configs[model_name] = {
                    **new_config,
                    "show_in_ui": existing.get("show_in_ui", new_config["show_in_ui"]),
                    "auto_preload": existing.get("auto_preload", new_config["auto_preload"]),
                    "created_at": existing.get("created_at", new_config["created_at"])
                }
            else:
                # Use new config for newly discovered models
                merged_configs[model_name] = new_config
        
        # Update default model
        default_model = self.get_recommended_default_model(discovered_models)
        
        return {
            "default_model": default_model,
            "models": merged_configs,
            "last_updated": datetime.now().isoformat()
        }


# Global instance
enhanced_discovery = EnhancedModelDiscovery()
