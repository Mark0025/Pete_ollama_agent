#!/usr/bin/env python3
"""
PeteOllama Provider Control Demo
Simple script to show current provider settings and demonstrate easy switching
"""

import json
import os
from pathlib import Path

def load_current_config():
    """Load current provider configuration"""
    config_path = Path("config/model_settings.json")
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
            return config.get('provider_settings', {})
    return {}

def show_current_status():
    """Display current provider configuration"""
    config = load_current_config()
    
    print("🔧 CURRENT PROVIDER CONFIGURATION")
    print("=" * 50)
    
    default_provider = config.get('default_provider', 'Not set')
    fallback_provider = config.get('fallback_provider', 'Not set')
    fallback_enabled = config.get('enable_fallback', False)
    
    print(f"🎯 Default Provider: {default_provider.upper()}")
    print(f"🔄 Fallback Provider: {fallback_provider.upper()}")
    print(f"🔀 Fallback Enabled: {'✅ YES' if fallback_enabled else '❌ NO'}")
    
    print("\n📊 PROVIDER STATUS:")
    providers = config.get('providers', {})
    for name, settings in providers.items():
        enabled = "✅ ENABLED" if settings.get('enabled', False) else "❌ DISABLED"
        priority = settings.get('priority', '?')
        desc = settings.get('description', 'No description')
        model = settings.get('default_model', 'No default model')
        print(f"  {name.upper()}: {enabled} (Priority: {priority})")
        print(f"    Description: {desc}")
        print(f"    Default Model: {model}")
        print()

def show_switch_options():
    """Show how to switch providers easily"""
    print("🔀 EASY PROVIDER SWITCHING")
    print("=" * 50)
    print("To switch your default provider, you have 3 options:")
    print()
    
    print("1️⃣ CONFIG FILE METHOD (Permanent):")
    print('   Edit config/model_settings.json:')
    print('   "provider_settings": {')
    print('     "default_provider": "runpod",    // Change this')
    print('     "fallback_provider": "openrouter" // Or this')
    print('   }')
    print()
    
    print("2️⃣ UI METHOD (Coming Soon):")
    print("   In /admin/settings - Provider Settings section:")
    print("   • Radio buttons: ○ RunPod ● OpenRouter ○ Local")
    print("   • Immediate effect on all new chat requests")
    print("   • Save settings automatically")
    print()
    
    print("3️⃣ API METHOD (Per Request):")
    print("   Send provider in each request:")
    print('   POST /v1/chat/completions')
    print('   {')
    print('     "model": "peteollama:jamie-fixed",')
    print('     "provider": "openrouter",  // Override default')
    print('     "messages": [...]')
    print('   }')

def demonstrate_switching():
    """Show what happens when you switch providers"""
    print("\n🎯 PROVIDER ROUTING LOGIC")
    print("=" * 50)
    
    scenarios = [
        {
            "name": "🏠 Local Development",
            "provider": "ollama", 
            "model": "peteollama:jamie-fixed",
            "description": "Fastest, private, no API costs"
        },
        {
            "name": "☁️ Production (RunPod)",
            "provider": "runpod",
            "model": "peteollama:jamie-fixed", 
            "description": "Serverless, scalable, consistent performance"
        },
        {
            "name": "🌐 Testing (OpenRouter)",
            "provider": "openrouter",
            "model": "meta-llama/llama-3.1-8b-instruct:free",
            "description": "300+ models, comparison testing, fallback"
        }
    ]
    
    for scenario in scenarios:
        print(f"{scenario['name']}:")
        print(f"  Provider: {scenario['provider']}")
        print(f"  Model: {scenario['model']}")
        print(f"  Use Case: {scenario['description']}")
        print()

def check_environment_vars():
    """Check which providers are properly configured"""
    print("🔍 ENVIRONMENT CHECK")
    print("=" * 50)
    
    # Check RunPod
    runpod_key = os.getenv('RUNPOD_API_KEY')
    runpod_endpoint = os.getenv('RUNPOD_SERVERLESS_ENDPOINT')
    print(f"RunPod API Key: {'✅ SET' if runpod_key else '❌ MISSING'}")
    print(f"RunPod Endpoint: {'✅ SET (' + runpod_endpoint + ')' if runpod_endpoint else '❌ MISSING'}")
    
    # Check OpenRouter
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    print(f"OpenRouter API Key: {'✅ SET' if openrouter_key else '❌ MISSING'}")
    
    # Check Ollama (test connection)
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=2)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"Local Ollama: ✅ RUNNING ({len(models)} models available)")
        else:
            print("Local Ollama: ❌ NOT RESPONDING")
    except:
        print("Local Ollama: ❌ NOT AVAILABLE")
    
    print()

def main():
    """Main demo function"""
    print("🏠 PeteOllama Provider Control Demo")
    print("==================================")
    print()
    
    # Show current status
    show_current_status()
    
    # Check environment
    check_environment_vars()
    
    # Show switching options
    show_switch_options()
    
    # Demonstrate routing
    demonstrate_switching()
    
    print("🎯 WHAT YOU NEED:")
    print("================")
    print("✅ Add 'Provider Settings' section to /admin/settings")
    print("✅ Simple radio buttons: RunPod | OpenRouter | Local")
    print("✅ Save button updates config/model_settings.json")
    print("✅ Immediate effect on model_router.py routing logic")
    print("✅ Shows current provider status in UI")
    print()
    print("This gives you one-click switching between all providers!")

if __name__ == "__main__":
    main()
