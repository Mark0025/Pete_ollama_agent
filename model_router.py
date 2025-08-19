#!/usr/bin/env python3
"""
Multi-Provider LLM Router for PeteOllama
Routes requests between Ollama, RunPod, and OpenRouter based on configuration
Enables easy model switching and provider fallbacks for testing
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

# Import handlers
try:
    from runpod_handler import runpod_handler
except ImportError:
    runpod_handler = None
    print("⚠️ runpod_handler not available")

try:
    from openrouter_handler import openrouter_handler
except ImportError:
    openrouter_handler = None
    print("⚠️ openrouter_handler not available")

try:
    import requests
    import ollama
    ollama_available = True
except ImportError:
    ollama_available = False
    print("⚠️ Ollama client not available")


class ModelRouter:
    """Routes LLM requests to appropriate providers"""
    
    def __init__(self, config_path: str = None):
        # Load configuration
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), 'config', 'model_settings.json')
        
        self.config_path = config_path
        self.config = self._load_config()
        self.provider_settings = self.config.get('provider_settings', {})
        self.default_provider = self.provider_settings.get('default_provider', 'ollama')
        self.fallback_provider = self.provider_settings.get('fallback_provider', 'openrouter')
        
        print(f"🔀 ModelRouter initialized")
        print(f"⚙️ Default provider: {self.default_provider}")
        print(f"🔄 Fallback provider: {self.fallback_provider}")
        
        # Initialize provider availability
        self.provider_status = {
            'ollama': ollama_available,
            'runpod': runpod_handler is not None and runpod_handler.available if runpod_handler else False,
            'openrouter': openrouter_handler is not None and openrouter_handler.available if openrouter_handler else False
        }
        
        print(f"📊 Provider Status:")
        for provider, status in self.provider_status.items():
            status_emoji = "✅" if status else "❌"
            print(f"  {status_emoji} {provider}")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load model configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ Config file not found: {self.config_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"⚠️ Invalid JSON in config file: {e}")
            return {}
    
    def get_provider_for_model(self, model_name: str) -> str:
        """Determine which provider to use for a given model"""
        # Check if it's an OpenRouter test model
        openrouter_models = self.config.get('openrouter_test_models', {})
        if model_name in openrouter_models:
            return 'openrouter'
        
        # Check regular models for provider hints
        models = self.config.get('models', {})
        if model_name in models:
            model_config = models[model_name]
            if 'provider' in model_config:
                return model_config['provider']
        
        # Check if model name suggests a specific provider
        if 'runpod-' in model_name.lower() or 'serverless' in model_name.lower():
            return 'runpod'
        
        if 'openai/' in model_name or 'anthropic/' in model_name or 'meta-llama/' in model_name:
            return 'openrouter'
        
        # Default to configured default provider
        return self.default_provider
    
    def route_chat_completion(self, 
                             message: str, 
                             model: str = None, 
                             provider: str = None,
                             **kwargs) -> Dict[str, Any]:
        """Route chat completion to appropriate provider"""
        
        # Determine provider
        if provider is None:
            provider = self.get_provider_for_model(model or "default")
        
        # Use default model if none specified
        if model is None:
            model = self._get_default_model(provider)
        
        print(f"🔀 Routing chat completion")
        print(f"🤖 Model: {model}")
        print(f"🏠 Provider: {provider}")
        print(f"💬 Message: {message[:100]}{'...' if len(message) > 100 else ''}")
        
        # Check provider availability and route
        if provider == 'openrouter' and self.provider_status['openrouter']:
            return self._route_to_openrouter(message, model, **kwargs)
        elif provider == 'runpod' and self.provider_status['runpod']:
            return self._route_to_runpod(message, model, **kwargs)
        elif provider == 'ollama' and self.provider_status['ollama']:
            return self._route_to_ollama(message, model, **kwargs)
        else:
            # Try fallback provider
            fallback = self.fallback_provider
            print(f"⚠️ Provider {provider} not available, trying fallback: {fallback}")
            
            if fallback == 'openrouter' and self.provider_status['openrouter']:
                return self._route_to_openrouter(message, model, **kwargs)
            elif fallback == 'runpod' and self.provider_status['runpod']:
                return self._route_to_runpod(message, model, **kwargs)
            elif fallback == 'ollama' and self.provider_status['ollama']:
                return self._route_to_ollama(message, model, **kwargs)
            else:
                return {
                    "status": "error",
                    "error": f"No available providers for model {model}",
                    "requested_provider": provider,
                    "attempted_fallback": fallback,
                    "provider_status": self.provider_status
                }
    
    def route_vapi_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Route VAPI webhook to appropriate provider"""
        
        # Extract model from webhook data or use default
        model = webhook_data.get('model', self._get_default_jamie_model())
        provider = self.get_provider_for_model(model)
        
        print(f"🔀📞 Routing VAPI webhook")
        print(f"🤖 Model: {model}")
        print(f"🏠 Provider: {provider}")
        print(f"📋 Webhook keys: {list(webhook_data.keys())}")
        
        # Add provider-specific optimizations for VAPI
        webhook_data['model'] = model
        
        # Route to provider
        if provider == 'openrouter' and self.provider_status['openrouter']:
            return openrouter_handler.vapi_webhook(webhook_data)
        elif provider == 'runpod' and self.provider_status['runpod']:
            return runpod_handler.vapi_webhook(webhook_data)
        elif provider == 'ollama' and self.provider_status['ollama']:
            return self._route_ollama_vapi(webhook_data)
        else:
            # Try fallback provider
            fallback = self.fallback_provider
            print(f"⚠️ Provider {provider} not available, trying fallback: {fallback}")
            
            if fallback == 'openrouter' and self.provider_status['openrouter']:
                return openrouter_handler.vapi_webhook(webhook_data)
            elif fallback == 'runpod' and self.provider_status['runpod']:
                return runpod_handler.vapi_webhook(webhook_data)
            else:
                return {
                    "status": "error",
                    "error": f"No available providers for VAPI webhook",
                    "requested_provider": provider,
                    "attempted_fallback": fallback
                }
    
    def _route_to_openrouter(self, message: str, model: str, **kwargs) -> Dict[str, Any]:
        """Route to OpenRouter"""
        print(f"🌐 Routing to OpenRouter")
        return openrouter_handler.chat_completion(message, model, **kwargs)
    
    def _route_to_runpod(self, message: str, model: str, **kwargs) -> Dict[str, Any]:
        """Route to RunPod"""
        print(f"☁️ Routing to RunPod")
        return runpod_handler.chat_completion(message, model, **kwargs)
    
    def _route_to_ollama(self, message: str, model: str, **kwargs) -> Dict[str, Any]:
        """Route to local Ollama"""
        print(f"🏠 Routing to Ollama")
        try:
            # Convert kwargs to Ollama format
            options = {
                'temperature': kwargs.get('temperature', 0.7),
                'num_predict': kwargs.get('max_tokens', 200)
            }
            
            response = ollama.chat(
                model=model,
                messages=[{'role': 'user', 'content': message}],
                options=options
            )
            
            return {
                "status": "success",
                "response": response['message']['content'],
                "model": model,
                "provider": "ollama",
                "finish_reason": "stop",
                "was_truncated": False
            }
            
        except Exception as e:
            print(f"❌ Ollama error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "provider": "ollama"
            }
    
    def _route_ollama_vapi(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Route VAPI webhook to Ollama"""
        user_message = webhook_data.get('message', '')
        model = webhook_data.get('model', self._get_default_jamie_model())
        call_id = webhook_data.get('call_id', '')
        
        if not user_message:
            return {"status": "error", "error": "No user message found in webhook"}
        
        result = self._route_to_ollama(user_message, model, max_tokens=200, temperature=0.7)
        
        if result.get('status') == 'success':
            return {
                "status": "success",
                "response": result['response'],
                "call_id": call_id,
                "model": model,
                "provider": "ollama"
            }
        else:
            return {
                "status": "error",
                "error": result.get('error', 'Ollama request failed'),
                "call_id": call_id,
                "provider": "ollama"
            }
    
    def _get_default_model(self, provider: str) -> str:
        """Get default model for provider"""
        if provider == 'openrouter':
            return "meta-llama/llama-3.1-8b-instruct:free"
        elif provider == 'runpod':
            return "peteollama:jamie-fixed"  # RunPod endpoint
        elif provider == 'ollama':
            return "peteollama:jamie-fixed"
        else:
            return "llama3:latest"
    
    def _get_default_jamie_model(self) -> str:
        """Get default Jamie property manager model"""
        # Look for Jamie models in order of preference
        models = self.config.get('models', {})
        jamie_models = [
            "peteollama:property-manager-v0.0.1",
            "peteollama:jamie-fixed",
            "peteollama:jamie-voice-complete"
        ]
        
        for model in jamie_models:
            if model in models and models[model].get('is_jamie_model', False):
                return model
        
        return "peteollama:jamie-fixed"  # fallback
    
    def get_available_models(self, provider: str = None) -> Dict[str, Any]:
        """Get available models for provider(s)"""
        if provider:
            if provider == 'openrouter' and openrouter_handler:
                return openrouter_handler.get_available_models()
            else:
                # Return configured models for the provider
                all_models = self.config.get('models', {})
                provider_models = {
                    name: config for name, config in all_models.items()
                    if config.get('provider', self.default_provider) == provider
                }
                return {"status": "success", "models": provider_models}
        else:
            # Return all configured models
            return {
                "status": "success", 
                "models": self.config.get('models', {}),
                "openrouter_test_models": self.config.get('openrouter_test_models', {}),
                "provider_status": self.provider_status
            }
    
    def test_providers(self) -> Dict[str, Any]:
        """Test all available providers with a simple message"""
        test_message = "Hello, this is a test message for provider health check."
        results = {}
        
        print(f"🧪 Testing all providers")
        
        for provider, available in self.provider_status.items():
            if not available:
                results[provider] = {
                    "status": "error",
                    "error": "Provider not available"
                }
                continue
            
            print(f"\n🧪 Testing {provider}...")
            try:
                model = self._get_default_model(provider)
                result = self.route_chat_completion(
                    message=test_message,
                    model=model,
                    provider=provider,
                    max_tokens=50
                )
                
                results[provider] = {
                    "status": result.get('status', 'unknown'),
                    "model": model,
                    "response_length": len(result.get('response', '')),
                    "finish_reason": result.get('finish_reason'),
                    "was_truncated": result.get('was_truncated', False),
                    "error": result.get('error')
                }
                
                status_emoji = "✅" if result.get('status') == 'success' else "❌"
                print(f"  {status_emoji} {provider}: {result.get('status')}")
                
            except Exception as e:
                print(f"  ❌ {provider}: Exception - {e}")
                results[provider] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return results


# Global router instance
model_router = ModelRouter()


def main():
    """Test the model router"""
    print("🧪 Testing Model Router")
    print("=" * 50)
    
    # Show provider status
    print(f"\n📊 Provider Status:")
    for provider, status in model_router.provider_status.items():
        status_emoji = "✅" if status else "❌"
        print(f"  {status_emoji} {provider}")
    
    # Test providers
    print(f"\n🧪 Running provider tests...")
    test_results = model_router.test_providers()
    
    print(f"\n📋 Test Results Summary:")
    for provider, result in test_results.items():
        status = result['status']
        status_emoji = "✅" if status == 'success' else "❌"
        print(f"  {status_emoji} {provider}: {status}")
        if status == 'success':
            print(f"    📏 Response length: {result.get('response_length', 0)} chars")
        elif result.get('error'):
            print(f"    ⚠️ Error: {result['error']}")
    
    # Test model routing logic
    print(f"\n🔀 Testing model routing logic:")
    test_models = [
        "peteollama:jamie-fixed",
        "meta-llama/llama-3.1-8b-instruct:free",
        "openai/gpt-3.5-turbo",
        "unknown-model"
    ]
    
    for model in test_models:
        provider = model_router.get_provider_for_model(model)
        print(f"  🤖 {model} → 🏠 {provider}")
    
    # Test VAPI webhook routing
    print(f"\n📞 Testing VAPI webhook routing:")
    mock_webhook = {
        "message": "Test VAPI message",
        "call_id": "test-123"
    }
    
    # Route to default Jamie model
    jamie_model = model_router._get_default_jamie_model()
    jamie_provider = model_router.get_provider_for_model(jamie_model)
    print(f"  🤖 Default Jamie model: {jamie_model} → 🏠 {jamie_provider}")


if __name__ == "__main__":
    main()
