#!/usr/bin/env python3
"""
OpenRouter Model Discovery and Management
Implements proper model routing and discovery based on OpenRouter API docs
"""

import requests
import json
import os
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class OpenRouterModelManager:
    """Manages OpenRouter model discovery, filtering, and routing"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.base_url = "https://openrouter.ai/api/v1"
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
            
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "PeteOllama AI Phone System"
        }
        
        self._models_cache = None
        print(f"🔧 OpenRouter Model Manager initialized")
    
    def get_all_models(self, refresh_cache: bool = False) -> List[Dict[str, Any]]:
        """Get all available models with caching"""
        
        if self._models_cache is None or refresh_cache:
            print("📥 Fetching models from OpenRouter API...")
            
            try:
                url = f"{self.base_url}/models"
                response = requests.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                self._models_cache = data.get('data', [])
                print(f"✅ Cached {len(self._models_cache)} models")
                
            except requests.exceptions.RequestException as e:
                print(f"❌ Error fetching models: {e}")
                return []
        
        return self._models_cache or []
    
    def get_free_models(self) -> List[Dict[str, Any]]:
        """Get all free models (pricing = 0)"""
        
        all_models = self.get_all_models()
        free_models = []
        
        for model in all_models:
            pricing = model.get('pricing', {})
            prompt_price = float(pricing.get('prompt', '1'))
            completion_price = float(pricing.get('completion', '1'))
            
            if prompt_price == 0 and completion_price == 0:
                free_models.append(model)
        
        print(f"🆓 Found {len(free_models)} free models")
        return free_models
    
    def get_cheap_models(self, max_price: float = 0.000001) -> List[Dict[str, Any]]:
        """Get low-cost models under the price threshold"""
        
        all_models = self.get_all_models()
        cheap_models = []
        
        for model in all_models:
            pricing = model.get('pricing', {})
            prompt_price = float(pricing.get('prompt', '1'))
            
            if 0 < prompt_price <= max_price:
                cheap_models.append(model)
        
        print(f"💰 Found {len(cheap_models)} cheap models under ${max_price} per 1M tokens")
        return cheap_models
    
    def search_models(self, 
                     query: str = None,
                     category: str = None,
                     free_only: bool = False,
                     context_length_min: int = None,
                     modalities: List[str] = None) -> List[Dict[str, Any]]:
        """Search and filter models by various criteria"""
        
        if category:
            # Use category filter in API call
            try:
                url = f"{self.base_url}/models"
                params = {"category": category}
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                models = data.get('data', [])
                print(f"📂 Found {len(models)} models in category '{category}'")
                
            except requests.exceptions.RequestException as e:
                print(f"⚠️ Category search failed, using local filter: {e}")
                models = self.get_all_models()
        else:
            models = self.get_all_models()
        
        # Apply filters
        filtered_models = []
        
        for model in models:
            # Free filter
            if free_only:
                pricing = model.get('pricing', {})
                prompt_price = float(pricing.get('prompt', '1'))
                if prompt_price > 0:
                    continue
            
            # Query filter (search in id, name, description)
            if query:
                query_lower = query.lower()
                searchable_text = f"{model.get('id', '')} {model.get('name', '')} {model.get('description', '')}".lower()
                if query_lower not in searchable_text:
                    continue
            
            # Context length filter
            if context_length_min:
                context_length = model.get('context_length', 0)
                if context_length < context_length_min:
                    continue
            
            # Modalities filter
            if modalities:
                arch = model.get('architecture', {})
                input_modalities = arch.get('input_modalities', [])
                if not all(mod in input_modalities for mod in modalities):
                    continue
            
            filtered_models.append(model)
        
        print(f"🔍 Filtered to {len(filtered_models)} models")
        return filtered_models
    
    def get_recommended_models(self) -> Dict[str, List[str]]:
        """Get curated list of recommended models for different use cases"""
        
        free_models = self.get_free_models()
        cheap_models = self.get_cheap_models()
        
        # Extract model IDs and sort by context length
        free_ids = []
        cheap_ids = []
        
        for model in sorted(free_models, key=lambda x: x.get('context_length', 0), reverse=True):
            model_id = model['id']
            context_length = model.get('context_length', 0)
            
            # Prefer models with good context length for property management
            if context_length >= 32000:
                free_ids.insert(0, model_id)  # Put high-context models first
            else:
                free_ids.append(model_id)
        
        for model in sorted(cheap_models[:10], key=lambda x: float(x.get('pricing', {}).get('prompt', '1'))):
            cheap_ids.append(model['id'])
        
        return {
            "free_models": free_ids[:8],  # Top 8 free models
            "cheap_models": cheap_ids[:5],  # Top 5 cheap models
            "property_management": [
                # Best models for property management tasks
                "meta-llama/llama-3.3-70b-instruct:free",
                "qwen/qwen-2.5-72b-instruct:free",
                "mistralai/mistral-nemo:free",
                "openai/gpt-4o-mini",
                "anthropic/claude-3-haiku"
            ],
            "fallback_chain": [
                # Recommended fallback chain
                "meta-llama/llama-3.3-70b-instruct:free",
                "mistralai/mistral-7b-instruct:free",
                "openai/gpt-3.5-turbo"
            ]
        }
    
    def test_model_availability(self, model_id: str) -> Dict[str, Any]:
        """Test if a specific model is available and working"""
        
        print(f"🧪 Testing model availability: {model_id}")
        
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": "Hello, this is a test message."}],
            "max_tokens": 10,
            "temperature": 0.1
        }
        
        headers = {
            **self.headers,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data and len(data['choices']) > 0:
                    return {
                        "available": True,
                        "status": "success",
                        "response_preview": data['choices'][0]['message']['content'][:50],
                        "model_used": data.get('model', model_id)
                    }
                else:
                    return {
                        "available": False,
                        "status": "no_choices",
                        "error": "No response choices returned"
                    }
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                return {
                    "available": False,
                    "status": "error",
                    "status_code": response.status_code,
                    "error": error_data.get('error', {}).get('message', f"HTTP {response.status_code}")
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "available": False,
                "status": "request_error",
                "error": str(e)
            }
    
    def create_model_routing_config(self, 
                                   primary_model: str,
                                   fallback_models: List[str] = None,
                                   auto_route: bool = False) -> Dict[str, Any]:
        """Create OpenRouter model routing configuration"""
        
        if auto_route:
            # Use OpenRouter's auto router
            return {
                "model": "openrouter/auto",
                "description": "OpenRouter auto-routing to best available model"
            }
        
        if fallback_models:
            # Use models array for fallback routing
            return {
                "models": [primary_model] + fallback_models,
                "description": f"Primary: {primary_model}, Fallbacks: {fallback_models}"
            }
        else:
            # Single model
            return {
                "model": primary_model,
                "description": f"Single model: {primary_model}"
            }
    
    def get_model_details(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific model"""
        
        all_models = self.get_all_models()
        
        for model in all_models:
            if model['id'] == model_id:
                return model
        
        print(f"⚠️ Model '{model_id}' not found")
        return None
    
    def print_model_summary(self, model: Dict[str, Any]):
        """Print a formatted summary of a model"""
        
        model_id = model['id']
        name = model.get('name', 'Unknown')
        description = model.get('description', 'No description')
        context_length = model.get('context_length', 0)
        
        pricing = model.get('pricing', {})
        prompt_price = pricing.get('prompt', '0')
        completion_price = pricing.get('completion', '0')
        
        arch = model.get('architecture', {})
        modalities = arch.get('input_modalities', [])
        
        print(f"🤖 {model_id}")
        print(f"   📝 {name}")
        print(f"   📖 {description[:100]}{'...' if len(description) > 100 else ''}")
        print(f"   📏 Context: {context_length:,} tokens")
        print(f"   💰 Pricing: ${prompt_price} prompt, ${completion_price} completion per 1M tokens")
        print(f"   🎭 Modalities: {', '.join(modalities)}")
        print()


def main():
    """Test the model manager"""
    print("🚀 OpenRouter Model Manager Test")
    print("=" * 50)
    
    try:
        manager = OpenRouterModelManager()
        
        # Test basic model listing
        print("\n📋 Getting all models...")
        all_models = manager.get_all_models()
        print(f"✅ Total models: {len(all_models)}")
        
        # Get free models
        print("\n🆓 Getting free models...")
        free_models = manager.get_free_models()
        print(f"✅ Free models: {len(free_models)}")
        
        if free_models:
            print("\n🔝 Top 5 free models:")
            for model in free_models[:5]:
                manager.print_model_summary(model)
        
        # Get recommendations
        print("\n🎯 Getting recommendations...")
        recommendations = manager.get_recommended_models()
        
        print("💰 Recommended free models:")
        for model_id in recommendations['free_models'][:3]:
            print(f"  • {model_id}")
        
        print("\n📞 Property management models:")
        for model_id in recommendations['property_management'][:3]:
            print(f"  • {model_id}")
        
        # Test model availability
        print("\n🧪 Testing model availability...")
        if recommendations['free_models']:
            test_model = recommendations['free_models'][0]
            result = manager.test_model_availability(test_model)
            
            if result['available']:
                print(f"✅ {test_model} is available")
                print(f"📄 Test response: {result['response_preview']}")
            else:
                print(f"❌ {test_model} failed: {result['error']}")
        
        # Search models
        print("\n🔍 Searching for 'llama' models...")
        llama_models = manager.search_models(query="llama", free_only=True)
        print(f"Found {len(llama_models)} free Llama models:")
        for model in llama_models[:3]:
            print(f"  • {model['id']} - {model.get('context_length', 0):,} tokens")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
