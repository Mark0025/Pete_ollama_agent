#!/usr/bin/env python3
"""
Detailed OpenRouter Integration Analysis
======================================

This script provides a deeper analysis of the OpenRouter integration,
examining the actual configuration structure and model separation.
"""

import os
import sys
import json
import asyncio
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def analyze_openrouter_detailed():
    """Detailed analysis of OpenRouter integration"""
    
    print("🔍 Detailed OpenRouter Integration Analysis")
    print("=" * 60)
    
    try:
        # 1. Examine configuration file directly
        print("\n1️⃣ CONFIGURATION FILE ANALYSIS")
        print("-" * 35)
        
        config_file = Path("src/config/model_settings.json")
        if config_file.exists():
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            print(f"✅ Configuration file loaded: {len(config_data)} top-level keys")
            print(f"   Top-level keys: {list(config_data.keys())}")
            
            # Examine providers section
            providers = config_data.get('providers', {})
            print(f"\n   📋 Providers section: {len(providers)} providers")
            for provider_name, provider_data in providers.items():
                print(f"      {provider_name}: {type(provider_data)}")
                if isinstance(provider_data, dict):
                    print(f"        Keys: {list(provider_data.keys())}")
            
            # Examine models section
            models = config_data.get('models', [])
            print(f"\n   🤖 Models section: {len(models)} models")
            
            # Categorize models by provider (models are dict with model names as keys)
            print(f"   Models structure: {type(models)} with {len(models)} entries")
            
            # Show first few models to understand structure
            print(f"   First 5 models:")
            for i, (model_name, model_data) in enumerate(list(models.items())[:5]):
                print(f"      {i+1}. {model_name}")
                if isinstance(model_data, dict):
                    print(f"         Type: {model_data.get('type', 'N/A')}")
                    print(f"         Base: {model_data.get('base_model', 'N/A')}")
                    print(f"         UI: {model_data.get('show_in_ui', 'N/A')}")
            
            # Check for Jamie models
            jamie_models = []
            openrouter_models = []
            ollama_models = []
            
            for model_name, model_data in models.items():
                if isinstance(model_data, dict):
                    if 'jamie' in model_name.lower() or model_data.get('is_jamie_model', False):
                        jamie_models.append(model_name)
                    elif 'openrouter:' in model_name.lower():
                        openrouter_models.append(model_name)
                    elif 'ollama:' in model_name or 'peteollama:' in model_name:
                        ollama_models.append(model_name)
            
            # Examine UI models section
            ui_models = config_data.get('ui_models', [])
            print(f"\n   🖥️ UI Models section: {len(ui_models)} models")
            
            print(f"\n   🏠 Jamie Models: {len(jamie_models)}")
            for model_name in jamie_models:
                print(f"      - {model_name}")
            
            print(f"\n   🌐 OpenRouter Models: {len(openrouter_models)}")
            for model_name in openrouter_models[:5]:
                print(f"      - {model_name}")
            
            print(f"\n   🏠 Ollama Models: {len(ollama_models)}")
            for model_name in ollama_models[:5]:
                print(f"      - {model_name}")
            

            
            print(f"\n   🌐 OpenRouter Models: {len(openrouter_models)}")
            for model_name in openrouter_models[:5]:
                print(f"      - {model_name}")
            
            print(f"\n   🏠 Ollama Models: {len(ollama_models)}")
            for model_name in ollama_models[:5]:
                print(f"      - {model_name}")
            
        else:
            print("❌ Configuration file not found")
        
        # 2. Check provider service methods
        print("\n2️⃣ PROVIDER SERVICE ANALYSIS")
        print("-" * 30)
        
        try:
            from vapi.services.provider_service import ProviderService
            provider_service = ProviderService()
            
            print("✅ Provider service initialized")
            
            # Get available methods
            methods = [method for method in dir(provider_service) if not method.startswith('_')]
            print(f"   Available methods: {methods}")
            
            # Check valid providers
            try:
                valid_providers = provider_service.valid_providers
                print(f"   Valid providers: {valid_providers}")
            except Exception as e:
                print(f"   ❌ Error getting valid providers: {e}")
            
            # Test async methods properly
            print(f"\n   🔄 Testing async methods:")
            
            for provider in ['ollama', 'openrouter', 'runpod']:
                try:
                    personas = await provider_service.get_personas_for_provider(provider)
                    print(f"      {provider}: {len(personas)} personas")
                    
                    # Show first few personas
                    for persona in personas[:2]:
                        print(f"        - {persona.get('name', 'N/A')} ({persona.get('type', 'N/A')})")
                        
                except Exception as e:
                    print(f"      ❌ {provider}: {e}")
                    
        except Exception as e:
            print(f"❌ Error with provider service: {e}")
        
        # 3. Check model settings manager
        print("\n3️⃣ MODEL SETTINGS MANAGER")
        print("-" * 30)
        
        try:
            from config.model_settings import model_settings
            
            print("✅ Model settings manager loaded")
            
            # Check available methods
            methods = [method for method in dir(model_settings) if not method.startswith('_')]
            print(f"   Available methods: {methods}")
            
            # Try to get provider settings
            try:
                provider_settings = model_settings.get_provider_settings()
                print(f"   Provider settings: {type(provider_settings)}")
                if isinstance(provider_settings, dict):
                    print(f"     Keys: {list(provider_settings.keys())}")
            except Exception as e:
                print(f"   ❌ Error getting provider settings: {e}")
            
            # Try to get UI models
            try:
                ui_models = model_settings.get_ui_models()
                print(f"   UI models: {len(ui_models)} models")
            except Exception as e:
                print(f"   ❌ Error getting UI models: {e}")
                
        except Exception as e:
            print(f"❌ Error with model settings manager: {e}")
        
        # 4. Check frontend provider switching
        print("\n4️⃣ FRONTEND PROVIDER SWITCHING")
        print("-" * 35)
        
        frontend_dir = Path("src/frontend")
        if frontend_dir.exists():
            main_ui_js = frontend_dir / "js" / "main-ui.js"
            if main_ui_js.exists():
                with open(main_ui_js, 'r') as f:
                    content = f.read()
                
                print("✅ Main UI JavaScript analyzed")
                
                # Check provider switching logic
                if 'switchProvider' in content:
                    print("   ✅ Provider switching function found")
                    
                    # Look for provider-specific logic
                    if 'openrouter' in content.lower():
                        print("   ✅ OpenRouter references found")
                    else:
                        print("   ❌ No OpenRouter references found")
                    
                    if 'ollama' in content.lower():
                        print("   ✅ Ollama references found")
                    
                    if 'runpod' in content.lower():
                        print("   ✅ RunPod references found")
                    
                    # Check for model filtering logic
                    if 'provider' in content.lower():
                        print("   ✅ Provider-based logic found")
                    else:
                        print("   ❌ No provider-based logic found")
                        
                else:
                    print("   ❌ Provider switching function not found")
            else:
                print("   ❌ main-ui.js not found")
        else:
            print("❌ Frontend directory not found")
        
        # 5. Summary and issues
        print("\n5️⃣ ANALYSIS SUMMARY & ISSUES")
        print("-" * 35)
        
        print("📋 Current State:")
        print("   - Configuration file: ✅ Exists")
        print("   - Provider system: ✅ Basic structure")
        print("   - Model separation: ⚠️ Needs verification")
        print("   - Frontend integration: ✅ Basic structure")
        
        print("\n🚨 Issues Found:")
        print("   1. Provider service methods are async but not properly awaited")
        print("   2. Model filtering by provider may not be working correctly")
        print("   3. Jamie models may appear in wrong provider categories")
        print("   4. OpenRouter models may not be properly separated")
        
        print("\n🎯 Key Questions:")
        print("   1. How are models filtered when switching providers?")
        print("   2. Are Jamie models properly excluded from OpenRouter?")
        print("   3. Does the UI update model lists when switching providers?")
        print("   4. Is there proper validation of model-provider relationships?")
        
        print("\n🔧 Recommendations:")
        print("   1. Fix async method calls in provider service")
        print("   2. Implement proper model filtering by provider")
        print("   3. Add validation to prevent Jamie models in OpenRouter")
        print("   4. Test provider switching end-to-end")
        print("   5. Add logging for model filtering decisions")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function"""
    asyncio.run(analyze_openrouter_detailed())

if __name__ == "__main__":
    main()
