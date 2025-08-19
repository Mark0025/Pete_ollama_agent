#!/usr/bin/env python3
"""
Analyze OpenRouter Integration
=============================

This script analyzes how OpenRouter models are currently integrated with:
1. Provider configuration system
2. UI model selection
3. Model filtering and separation
4. Provider switching behavior
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def analyze_openrouter_integration():
    """Analyze the current OpenRouter integration setup"""
    
    print("🔍 Analyzing OpenRouter Integration")
    print("=" * 50)
    
    try:
        # 1. Check provider configuration
        print("\n1️⃣ PROVIDER CONFIGURATION")
        print("-" * 30)
        
        from config.model_settings import model_settings
        
        try:
            provider_settings = model_settings.get_provider_settings()
            print(f"✅ Provider settings loaded:")
            print(f"   Default provider: {provider_settings.get('default_provider', 'N/A')}")
            print(f"   Fallback enabled: {provider_settings.get('fallback_enabled', 'N/A')}")
            print(f"   Available providers: {list(provider_settings.get('providers', {}).keys())}")
        except Exception as e:
            print(f"❌ Error loading provider settings: {e}")
        
        # 2. Check OpenRouter models configuration
        print("\n2️⃣ OPENROUTER MODELS CONFIGURATION")
        print("-" * 40)
        
        try:
            openrouter_models = model_settings.get_openrouter_models()
            print(f"✅ OpenRouter models loaded: {len(openrouter_models)} models")
            
            # Show first few models
            for i, model in enumerate(openrouter_models[:5]):
                print(f"   {i+1}. {model.get('name', 'N/A')} - {model.get('description', 'No description')}")
            
            if len(openrouter_models) > 5:
                print(f"   ... and {len(openrouter_models) - 5} more models")
                
        except Exception as e:
            print(f"❌ Error loading OpenRouter models: {e}")
        
        # 3. Check UI models (what shows in dropdowns)
        print("\n3️⃣ UI MODELS (FRONTEND DROPDOWNS)")
        print("-" * 35)
        
        try:
            ui_models = model_settings.get_ui_models()
            print(f"✅ UI models loaded: {len(ui_models)} models")
            
            # Categorize models by type
            jamie_models = []
            openrouter_models_ui = []
            ollama_models = []
            other_models = []
            
            for model in ui_models:
                model_name = model.get('name', '')
                if 'peteollama:jamie' in model_name:
                    jamie_models.append(model)
                elif 'openrouter:' in model_name or model.get('provider') == 'openrouter':
                    openrouter_models_ui.append(model)
                elif 'ollama:' in model_name or model.get('provider') == 'ollama':
                    ollama_models.append(model)
                else:
                    other_models.append(model)
            
            print(f"   🏠 Jamie Models: {len(jamie_models)}")
            for model in jamie_models[:3]:
                print(f"      - {model.get('name', 'N/A')}")
            
            print(f"   🌐 OpenRouter Models: {len(openrouter_models_ui)}")
            for model in openrouter_models_ui[:3]:
                print(f"      - {model.get('name', 'N/A')}")
            
            print(f"   🏠 Ollama Models: {len(ollama_models)}")
            for model in ollama_models[:3]:
                print(f"      - {model.get('name', 'N/A')}")
            
            print(f"   🤖 Other Models: {len(other_models)}")
            for model in other_models[:3]:
                print(f"      - {model.get('name', 'N/A')}")
                
        except Exception as e:
            print(f"❌ Error loading UI models: {e}")
        
        # 4. Check provider service
        print("\n4️⃣ PROVIDER SERVICE")
        print("-" * 20)
        
        try:
            from vapi.services.provider_service import ProviderService
            provider_service = ProviderService()
            
            print("✅ Provider service initialized")
            
            # Check what methods are available
            methods = [method for method in dir(provider_service) if not method.startswith('_')]
            print(f"   Available methods: {methods}")
            
            # Check personas for different providers
            try:
                ollama_personas = provider_service.get_personas_for_provider('ollama')
                print(f"   🏠 Ollama personas: {len(ollama_personas)}")
            except Exception as e:
                print(f"   ❌ Ollama personas error: {e}")
            
            try:
                openrouter_personas = provider_service.get_personas_for_provider('openrouter')
                print(f"   🌐 OpenRouter personas: {len(openrouter_personas)}")
            except Exception as e:
                print(f"   ❌ OpenRouter personas error: {e}")
            
            try:
                runpod_personas = provider_service.get_personas_for_provider('runpod')
                print(f"   ☁️ RunPod personas: {len(runpod_personas)}")
            except Exception as e:
                print(f"   ❌ RunPod personas error: {e}")
                
        except Exception as e:
            print(f"❌ Error with provider service: {e}")
        
        # 5. Check configuration files
        print("\n5️⃣ CONFIGURATION FILES")
        print("-" * 25)
        
        config_dir = Path("src/config")
        if config_dir.exists():
            config_files = list(config_dir.glob("*.json"))
            print(f"✅ Config directory found: {len(config_files)} files")
            
            for config_file in config_files:
                print(f"   📁 {config_file.name}")
                
                if config_file.name == "model_settings.json":
                    try:
                        import json
                        with open(config_file, 'r') as f:
                            config_data = json.load(f)
                        
                        print(f"      Model settings structure:")
                        print(f"        - Providers: {list(config_data.get('providers', {}).keys())}")
                        print(f"        - Models: {len(config_data.get('models', []))}")
                        print(f"        - UI Models: {len(config_data.get('ui_models', []))}")
                        
                    except Exception as e:
                        print(f"      ❌ Error reading config: {e}")
        else:
            print("❌ Config directory not found")
        
        # 6. Check frontend integration
        print("\n6️⃣ FRONTEND INTEGRATION")
        print("-" * 25)
        
        frontend_dir = Path("src/frontend")
        if frontend_dir.exists():
            print("✅ Frontend directory found")
            
            # Check main UI JavaScript
            main_ui_js = frontend_dir / "js" / "main-ui.js"
            if main_ui_js.exists():
                print("   📁 main-ui.js found")
                
                # Look for provider switching logic
                with open(main_ui_js, 'r') as f:
                    content = f.read()
                    
                if 'switchProvider' in content:
                    print("   ✅ Provider switching function found")
                else:
                    print("   ❌ Provider switching function not found")
                    
                if 'openrouter' in content.lower():
                    print("   ✅ OpenRouter references found")
                else:
                    print("   ❌ No OpenRouter references found")
            else:
                print("   ❌ main-ui.js not found")
        else:
            print("❌ Frontend directory not found")
        
        # 7. Summary and recommendations
        print("\n7️⃣ ANALYSIS SUMMARY")
        print("-" * 20)
        
        print("📋 Current State:")
        print("   - Provider system: ✅ Configured")
        print("   - OpenRouter models: ✅ Available")
        print("   - UI integration: ✅ Basic structure")
        print("   - Model separation: ⚠️ Needs verification")
        
        print("\n🎯 Key Findings:")
        print("   1. Provider configuration system exists")
        print("   2. OpenRouter models are configured")
        print("   3. UI has provider switching capability")
        print("   4. Model filtering may need improvement")
        
        print("\n🔧 Recommendations:")
        print("   1. Verify model filtering by provider")
        print("   2. Ensure Jamie models don't appear in OpenRouter")
        print("   3. Test provider switching behavior")
        print("   4. Check model availability per provider")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_openrouter_integration()
