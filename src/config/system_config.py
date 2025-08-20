#!/usr/bin/env python3
"""
System Configuration Manager
===========================

Centralized configuration system that controls all aspects of the application
from a single, top-level configuration file. Implements top-down control with
bottom-up overrides for caching, providers, and models.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from utils.logger import logger
from utils.type_validation import beartype, validate_and_log_types, validate_config_structure, TypeValidationError

@dataclass
class CachingConfig:
    """Caching configuration for a specific provider or model"""
    enabled: bool = True
    threshold: float = 0.75
    max_cache_age_hours: int = 24
    max_responses: int = 1000
    similarity_analyzer_enabled: bool = True
    fallback_cache_enabled: bool = True

@dataclass
class ProviderConfig:
    """Provider-specific configuration"""
    name: str
    enabled: bool = True
    priority: int = 1
    caching: CachingConfig = None
    api_key: str = ""
    endpoint: str = ""
    timeout: int = 30
    max_retries: int = 3
    
    def __post_init__(self):
        if self.caching is None:
            self.caching = CachingConfig()

@dataclass
class ModelConfig:
    """Model-specific configuration"""
    name: str
    provider: str
    enabled: bool = True
    caching: CachingConfig = None
    max_tokens: int = 2048
    temperature: float = 0.7
    context_length: int = 8192
    
    def __post_init__(self):
        if self.caching is None:
            self.caching = CachingConfig()

@dataclass
class SystemConfig:
    """Top-level system configuration"""
    # Global caching settings
    global_caching: CachingConfig = None
    
    # Provider management
    providers: Dict[str, ProviderConfig] = None
    default_provider: str = "openrouter"
    fallback_enabled: bool = True
    fallback_provider: str = "runpod"
    auto_switch: bool = True
    
    # Model management
    models: Dict[str, ModelConfig] = None
    default_model: str = "openai/gpt-3.5-turbo"
    
    # System settings
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    
    # Global system settings (moved from .env)
    ollama_host: str = "localhost:11434"
    ollama_model: str = "qwen2.5:7b"
    jamie_custom_model: str = "peteollama:property-manager"
    max_tokens: int = 4096
    
    def __post_init__(self):
        if self.global_caching is None:
            self.global_caching = CachingConfig()
        if self.providers is None:
            self.providers = {}
        if self.models is None:
            self.models = {}

class SystemConfigManager:
    """Manages the centralized system configuration"""
    
    def __init__(self, config_file: str = "config/system_config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_default_config()
        self._load_config()
        self._setup_default_providers()
        self._setup_default_models()
    
    def _load_default_config(self) -> SystemConfig:
        """Load default configuration"""
        return SystemConfig(
            global_caching=CachingConfig(
                enabled=True,
                threshold=0.75,
                max_cache_age_hours=24,
                max_responses=1000,
                similarity_analyzer_enabled=True,
                fallback_cache_enabled=True
            ),
            default_provider="openrouter",
            fallback_enabled=True,
            fallback_provider="runpod",
            auto_switch=True,
            environment=os.getenv("ENVIRONMENT", "development"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            # Global system settings from .env
            ollama_host=os.getenv("OLLAMA_HOST", "localhost:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "qwen2.5:7b"),
            jamie_custom_model=os.getenv("JAMIE_CUSTOM_MODEL", "peteollama:property-manager"),
            max_tokens=int(os.getenv("MAX_TOKENS", "4096"))
        )
    
    def _setup_default_providers(self):
        """Setup default provider configurations"""
        # OpenRouter
        self.config.providers["openrouter"] = ProviderConfig(
            name="openrouter",
            enabled=True,
            priority=1,
            caching=CachingConfig(
                enabled=True,
                threshold=0.80,
                max_cache_age_hours=24
            ),
            api_key=os.getenv("OPENROUTER_API_KEY", ""),
            timeout=30,
            max_retries=3
        )
        
        # RunPod
        self.config.providers["runpod"] = ProviderConfig(
            name="runpod",
            enabled=True,
            priority=2,
            caching=CachingConfig(
                enabled=False,  # Disable caching for RunPod by default
                threshold=0.70,
                max_cache_age_hours=12
            ),
            api_key=os.getenv("RUNPOD_API_KEY", ""),
            endpoint=os.getenv("RUNPOD_SERVERLESS_ENDPOINT", ""),
            timeout=60,
            max_retries=5
        )
        
        # Ollama
        self.config.providers["ollama"] = ProviderConfig(
            name="ollama",
            enabled=True,
            priority=3,
            caching=CachingConfig(
                enabled=True,
                threshold=0.75,
                max_cache_age_hours=48
            ),
            timeout=30,
            max_retries=2
        )
    
    def _setup_default_models(self):
        """Setup default model configurations"""
        # OpenRouter Models
        self.config.models["openai/gpt-3.5-turbo"] = ModelConfig(
            name="openai/gpt-3.5-turbo",
            provider="openrouter",
            enabled=True,
            caching=CachingConfig(
                enabled=True,
                threshold=0.80,
                max_cache_age_hours=24
            ),
            max_tokens=2048,
            temperature=0.7,
            context_length=16385
        )
        
        self.config.models["anthropic/claude-3-haiku"] = ModelConfig(
            name="anthropic/claude-3-haiku",
            provider="openrouter",
            enabled=True,
            caching=CachingConfig(
                enabled=True,
                threshold=0.85,  # Higher threshold for premium model
                max_cache_age_hours=12
            ),
            max_tokens=4000,
            temperature=0.7,
            context_length=200000
        )
        
        # RunPod Models
        self.config.models["llama3:latest"] = ModelConfig(
            name="llama3:latest",
            provider="runpod",
            enabled=True,
            caching=CachingConfig(
                enabled=False,  # No caching for RunPod models
                threshold=0.70,
                max_cache_age_hours=6
            ),
            max_tokens=4096,
            temperature=0.7,
            context_length=8192
        )
    
    def _load_config(self):
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self._merge_config(data)
                    logger.info(f"✅ Loaded system configuration from {self.config_file}")
            else:
                logger.info(f"📝 No system config file found, using defaults")
        except Exception as e:
            logger.error(f"❌ Error loading system config: {e}")
    
    def _merge_config(self, data: Dict[str, Any]):
        """Merge loaded configuration with defaults"""
        # Merge global caching
        if 'global_caching' in data:
            for key, value in data['global_caching'].items():
                if hasattr(self.config.global_caching, key):
                    setattr(self.config.global_caching, key, value)
        
        # Merge providers
        if 'providers' in data:
            for provider_name, provider_data in data['providers'].items():
                if provider_name in self.config.providers:
                    for key, value in provider_data.items():
                        if key == 'caching' and isinstance(provider_data.get('caching'), dict):
                            # Ensure caching is a CachingConfig object
                            if not isinstance(self.config.providers[provider_name].caching, CachingConfig):
                                self.config.providers[provider_name].caching = CachingConfig()
                            for cache_key, cache_value in provider_data['caching'].items():
                                if hasattr(self.config.providers[provider_name].caching, cache_key):
                                    setattr(self.config.providers[provider_name].caching, cache_key, cache_value)
                        elif hasattr(self.config.providers[provider_name], key):
                            setattr(self.config.providers[provider_name], key, value)
        
        # Merge models
        if 'models' in data:
            for model_name, model_data in data['models'].items():
                if model_name in self.config.models:
                    for key, value in model_data.items():
                        if key == 'caching' and isinstance(model_data.get('caching'), dict):
                            # Ensure caching is a CachingConfig object
                            if not isinstance(self.config.models[model_name].caching, CachingConfig):
                                self.config.models[model_name].caching = CachingConfig()
                            for cache_key, cache_value in model_data['caching'].items():
                                if hasattr(self.config.models[model_name].caching, cache_key):
                                    setattr(self.config.models[model_name].caching, cache_key, cache_value)
                        elif hasattr(self.config.models[model_name], key):
                            setattr(self.config.models[model_name], key, value)
        
        # Merge top-level settings
        for key, value in data.items():
            if key not in ['global_caching', 'providers', 'models'] and hasattr(self.config, key):
                setattr(self.config, key, value)
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(asdict(self.config), f, indent=2)
            logger.info(f"✅ Saved system configuration to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"❌ Error saving system config: {e}")
            return False
    
    def get_global_settings(self) -> Dict[str, Any]:
        """Get global system settings"""
        return {
            "ollama_host": self.config.ollama_host,
            "ollama_model": self.config.ollama_model,
            "jamie_custom_model": self.config.jamie_custom_model,
            "max_tokens": self.config.max_tokens
        }
    
    @beartype
    def get_caching_config(self, provider: Optional[str] = None, model: Optional[str] = None) -> CachingConfig:
        """Get caching configuration for a specific provider/model combination"""
        # Start with global settings
        caching = CachingConfig(
            enabled=self.config.global_caching.enabled,
            threshold=self.config.global_caching.threshold,
            max_cache_age_hours=self.config.global_caching.max_cache_age_hours,
            max_responses=self.config.global_caching.max_responses,
            similarity_analyzer_enabled=self.config.global_caching.similarity_analyzer_enabled,
            fallback_cache_enabled=self.config.global_caching.fallback_cache_enabled
        )
        
        # Override with provider settings
        if provider and provider in self.config.providers:
            provider_config = self.config.providers[provider]
            if provider_config.caching:
                # Handle both CachingConfig objects and dictionaries
                if hasattr(provider_config.caching, 'enabled'):
                    if provider_config.caching.enabled is not None:
                        caching.enabled = provider_config.caching.enabled
                elif isinstance(provider_config.caching, dict) and 'enabled' in provider_config.caching:
                    caching.enabled = provider_config.caching['enabled']
                
                if hasattr(provider_config.caching, 'threshold'):
                    if provider_config.caching.threshold is not None:
                        caching.threshold = provider_config.caching.threshold
                elif isinstance(provider_config.caching, dict) and 'threshold' in provider_config.caching:
                    caching.threshold = provider_config.caching['threshold']
                
                if hasattr(provider_config.caching, 'max_cache_age_hours'):
                    if provider_config.caching.max_cache_age_hours is not None:
                        caching.max_cache_age_hours = provider_config.caching.max_cache_age_hours
                elif isinstance(provider_config.caching, dict) and 'max_cache_age_hours' in provider_config.caching:
                    caching.max_cache_age_hours = provider_config.caching['max_cache_age_hours']
        
        # Override with model settings
        if model and model in self.config.models:
            model_config = self.config.models[model]
            if model_config.caching:
                # Handle both CachingConfig objects and dictionaries
                if hasattr(model_config.caching, 'enabled'):
                    if model_config.caching.enabled is not None:
                        caching.enabled = model_config.caching.enabled
                elif isinstance(model_config.caching, dict) and 'enabled' in model_config.caching:
                    caching.enabled = model_config.caching['enabled']
                
                if hasattr(model_config.caching, 'threshold'):
                    if model_config.caching.threshold is not None:
                        caching.threshold = model_config.caching.threshold
                elif isinstance(model_config.caching, dict) and 'threshold' in model_config.caching:
                    caching.threshold = model_config.caching['threshold']
                
                if hasattr(model_config.caching, 'max_cache_age_hours'):
                    if model_config.caching.max_cache_age_hours is not None:
                        caching.max_cache_age_hours = model_config.caching.max_cache_age_hours
                elif isinstance(model_config.caching, dict) and 'max_cache_age_hours' in model_config.caching:
                    caching.max_cache_age_hours = model_config.caching['max_cache_age_hours']
        
        return caching
    
    def get_provider_config(self, provider: str) -> Optional[ProviderConfig]:
        """Get configuration for a specific provider"""
        return self.config.providers.get(provider)
    
    def get_model_config(self, model: str) -> Optional[ModelConfig]:
        """Get configuration for a specific model"""
        return self.config.models.get(model)
    
    @beartype
    def update_provider_config(self, provider: str, **kwargs) -> bool:
        """Update provider configuration"""
        if provider not in self.config.providers:
            return False
        
        provider_config = self.config.providers[provider]
        for key, value in kwargs.items():
            if hasattr(provider_config, key):
                setattr(provider_config, key, value)
            elif key == 'caching' and isinstance(value, dict):
                for cache_key, cache_value in value.items():
                    if hasattr(provider_config.caching, cache_key):
                        setattr(provider_config.caching, cache_key, cache_value)
        
        return self.save_config()
    
    @beartype
    def update_model_config(self, model: str, **kwargs) -> bool:
        """Update model configuration"""
        if model not in self.config.models:
            return False
        
        model_config = self.config.models[model]
        for key, value in kwargs.items():
            if hasattr(model_config, key):
                setattr(model_config, key, value)
            elif key == 'caching' and isinstance(value, dict):
                for cache_key, cache_value in value.items():
                    if hasattr(model_config.caching, cache_key):
                        setattr(model_config.caching, cache_key, cache_value)
        
        return self.save_config()
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration"""
        def safe_asdict(obj):
            """Safely convert object to dict, handling both dataclass instances and dicts"""
            if hasattr(obj, '__dataclass_fields__'):
                return asdict(obj)
            elif isinstance(obj, dict):
                return obj
            else:
                return {}
        
        return {
            "system": {
                "environment": self.config.environment,
                "default_provider": self.config.default_provider,
                "fallback_enabled": self.config.fallback_enabled,
                "fallback_provider": self.config.fallback_provider
            },
            "global_caching": safe_asdict(self.config.global_caching),
            "providers": {
                name: {
                    "enabled": config.enabled,
                    "priority": config.priority,
                    "caching": safe_asdict(config.caching)
                }
                for name, config in self.config.providers.items()
            },
            "models": {
                name: {
                    "provider": config.provider,
                    "enabled": config.enabled,
                    "caching": safe_asdict(config.caching),
                    "max_tokens": config.max_tokens
                }
                for name, config in self.config.models.items()
            }
        }

# Global instance
system_config = SystemConfigManager()
