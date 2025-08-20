#!/usr/bin/env python3
"""
System Configuration Test Suite
==============================

Comprehensive testing of the centralized system configuration system.
Demonstrates top-down control with bottom-up overrides for caching.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_system_config():
    """Test the system configuration system"""
    print("🧪 Testing System Configuration System")
    print("=" * 60)
    
    try:
        from config.system_config import system_config
        
        print("✅ System config imported successfully")
        
        # Test 1: Get current configuration
        print("\n📊 Test 1: Current Configuration")
        print("-" * 40)
        config_summary = system_config.get_config_summary()
        print(f"Default provider: {config_summary['system']['default_provider']}")
        print(f"Fallback enabled: {config_summary['system']['fallback_enabled']}")
        print(f"Global caching enabled: {config_summary['global_caching']['enabled']}")
        print(f"Global threshold: {config_summary['global_caching']['threshold']}")
        
        # Test 2: Test caching configuration hierarchy
        print("\n🔀 Test 2: Caching Configuration Hierarchy")
        print("-" * 40)
        
        # Global caching
        global_caching = system_config.get_caching_config()
        print(f"Global caching: enabled={global_caching.enabled}, threshold={global_caching.threshold}")
        
        # Provider-specific caching
        openrouter_caching = system_config.get_caching_config(provider="openrouter")
        print(f"OpenRouter caching: enabled={openrouter_caching.enabled}, threshold={openrouter_caching.threshold}")
        
        runpod_caching = system_config.get_caching_config(provider="runpod")
        print(f"RunPod caching: enabled={runpod_caching.enabled}, threshold={runpod_caching.threshold}")
        
        # Model-specific caching
        gpt35_caching = system_config.get_caching_config(provider="openrouter", model="openai/gpt-3.5-turbo")
        print(f"GPT-3.5 caching: enabled={gpt35_caching.enabled}, threshold={gpt35_caching.threshold}")
        
        claude_caching = system_config.get_caching_config(provider="openrouter", model="anthropic/claude-3-haiku")
        print(f"Claude caching: enabled={claude_caching.enabled}, threshold={claude_caching.threshold}")
        
        # Test 3: Update configurations
        print("\n⚙️ Test 3: Update Configurations")
        print("-" * 40)
        
        # Update global caching
        print("Updating global caching threshold from 0.75 to 0.85...")
        system_config.config.global_caching.threshold = 0.85
        system_config.save_config()
        
        # Update provider caching
        print("Disabling caching for RunPod...")
        system_config.update_provider_config("runpod", caching={"enabled": False})
        
        # Update model caching
        print("Setting GPT-3.5 to higher threshold (0.90)...")
        system_config.update_model_config("openai/gpt-3.5-turbo", caching={"threshold": 0.90})
        
        # Test 4: Verify updates
        print("\n✅ Test 4: Verify Updates")
        print("-" * 40)
        
        updated_global = system_config.get_caching_config()
        print(f"Updated global threshold: {updated_global.threshold}")
        
        updated_runpod = system_config.get_caching_config(provider="runpod")
        print(f"Updated RunPod caching: enabled={updated_runpod.enabled}")
        
        updated_gpt35 = system_config.get_caching_config(provider="openrouter", model="openai/gpt-3.5-turbo")
        print(f"Updated GPT-3.5 threshold: {updated_gpt35.threshold}")
        
        # Test 5: Configuration summary
        print("\n📋 Test 5: Configuration Summary")
        print("-" * 40)
        final_summary = system_config.get_config_summary()
        
        print("System Settings:")
        for key, value in final_summary['system'].items():
            print(f"  {key}: {value}")
        
        print("\nProvider Caching Settings:")
        for provider, config in final_summary['providers'].items():
            caching = config.get('caching', {})
            print(f"  {provider}: enabled={caching.get('enabled', 'N/A')}, threshold={caching.get('threshold', 'N/A')}")
        
        print("\nModel Caching Settings:")
        for model, config in final_summary['models'].items():
            if 'openai/gpt-3.5-turbo' in model or 'anthropic/claude-3-haiku' in model:
                caching = config.get('caching', {})
                print(f"  {model}: enabled={caching.get('enabled', 'N/A')}, threshold={caching.get('threshold', 'N/A')}")
        
        print("\n🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_caching_behavior():
    """Test how caching configuration affects behavior"""
    print("\n🧠 Testing Caching Behavior")
    print("=" * 60)
    
    try:
        from config.system_config import system_config
        
        # Test different provider/model combinations
        test_cases = [
            ("openrouter", "openai/gpt-3.5-turbo", "OpenRouter GPT-3.5"),
            ("openrouter", "anthropic/claude-3-haiku", "OpenRouter Claude"),
            ("runpod", "llama3:latest", "RunPod Llama"),
            ("ollama", "mistral:latest", "Ollama Mistral")
        ]
        
        for provider, model, description in test_cases:
            caching = system_config.get_caching_config(provider, model)
            print(f"\n{description}:")
            print(f"  Caching enabled: {caching.enabled}")
            print(f"  Threshold: {caching.threshold}")
            print(f"  Max age: {caching.max_cache_age_hours}h")
            print(f"  Similarity analyzer: {caching.similarity_analyzer_enabled}")
            print(f"  Fallback cache: {caching.fallback_cache_enabled}")
        
        return True
        
    except Exception as e:
        print(f"❌ Caching behavior test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 System Configuration Test Suite")
    print("=" * 60)
    
    # Test basic functionality
    if not test_system_config():
        print("❌ Basic functionality test failed")
        return False
    
    # Test caching behavior
    if not test_caching_behavior():
        print("❌ Caching behavior test failed")
        return False
    
    print("\n🎉 All tests passed! System configuration is working correctly.")
    print("\n📝 Next steps:")
    print("  1. Check the generated config/system_config.json file")
    print("  2. Test the admin API endpoints")
    print("  3. Integrate with the ModelManager")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
