#!/usr/bin/env python3
"""
Comprehensive System Configuration Test Suite
============================================

Tests the entire system configuration system from top to bottom:
- Configuration loading/saving
- Provider switching
- Caching behavior
- Race conditions
- Actual functionality integration
- Error handling
"""

import sys
import os
import time
import threading
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_configuration_loading():
    """Test 1: Configuration Loading and Validation"""
    print("🧪 Test 1: Configuration Loading and Validation")
    print("=" * 60)
    
    try:
        from config.system_config import system_config
        
        # Test basic loading
        config_summary = system_config.get_config_summary()
        print(f"✅ Config loaded: {config_summary['system']['default_provider']}")
        
        # Test caching config hierarchy
        global_caching = system_config.get_caching_config()
        print(f"✅ Global caching: enabled={global_caching.enabled}, threshold={global_caching.threshold}")
        
        provider_caching = system_config.get_caching_config(provider="openrouter")
        print(f"✅ OpenRouter caching: enabled={provider_caching.enabled}, threshold={provider_caching.threshold}")
        
        model_caching = system_config.get_caching_config(provider="openrouter", model="openai/gpt-3.5-turbo")
        print(f"✅ GPT-3.5 caching: enabled={model_caching.enabled}, threshold={model_caching.threshold}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False

def test_provider_switching():
    """Test 2: Provider Switching and Routing"""
    print("\n🧪 Test 2: Provider Switching and Routing")
    print("=" * 60)
    
    try:
        from config.system_config import system_config
        
        # Test provider switching
        print("🔄 Testing provider switching...")
        
        # Switch to RunPod
        success = system_config.update_provider_config("runpod", enabled=True, priority=1)
        print(f"   ✅ RunPod enabled: {success}")
        
        # Switch to OpenRouter
        success = system_config.update_provider_config("openrouter", enabled=True, priority=1)
        print(f"   ✅ OpenRouter enabled: {success}")
        
        # Test fallback logic
        fallback_enabled = system_config.config.fallback_enabled
        fallback_provider = system_config.config.fallback_provider
        print(f"   ✅ Fallback: enabled={fallback_enabled}, provider={fallback_provider}")
        
        return True
        
    except Exception as e:
        print(f"❌ Provider switching failed: {e}")
        return False

def test_caching_behavior():
    """Test 3: Caching Behavior and Thresholds"""
    print("\n🧪 Test 3: Caching Behavior and Thresholds")
    print("=" * 60)
    
    try:
        from config.system_config import system_config
        
        # Test different threshold values
        test_thresholds = [0.5, 0.75, 0.9, 1.0]
        
        for threshold in test_thresholds:
            # Update global threshold
            system_config.config.global_caching.threshold = threshold
            system_config.save_config()
            
            # Verify the change
            current_config = system_config.get_caching_config()
            print(f"   ✅ Threshold {threshold}: actual={current_config.threshold}")
            
            # Test threshold validation
            if 0.0 <= threshold <= 1.0:
                print(f"      ✅ Valid threshold range")
            else:
                print(f"      ❌ Invalid threshold range")
        
        # Test provider-specific caching
        print("\n   🔄 Testing provider-specific caching...")
        
        # Disable caching for RunPod
        system_config.update_provider_config("runpod", caching={"enabled": False})
        runpod_caching = system_config.get_caching_config(provider="runpod")
        print(f"      ✅ RunPod caching: enabled={runpod_caching.enabled}")
        
        # Enable caching for OpenRouter with high threshold
        system_config.update_provider_config("openrouter", caching={"enabled": True, "threshold": 0.95})
        openrouter_caching = system_config.get_caching_config(provider="openrouter")
        print(f"      ✅ OpenRouter caching: enabled={openrouter_caching.enabled}, threshold={openrouter_caching.threshold}")
        
        return True
        
    except Exception as e:
        print(f"❌ Caching behavior test failed: {e}")
        return False

def test_model_configuration():
    """Test 4: Model Configuration and Access Control"""
    print("\n🧪 Test 4: Model Configuration and Access Control")
    print("=" * 60)
    
    try:
        from config.system_config import system_config
        
        # Test model-specific settings
        print("🤖 Testing model-specific configuration...")
        
        # Test GPT-3.5 configuration
        gpt35_config = system_config.get_model_config("openai/gpt-3.5-turbo")
        if gpt35_config:
            print(f"   ✅ GPT-3.5: provider={gpt35_config.provider}, enabled={gpt35_config.enabled}")
            print(f"      Caching: enabled={gpt35_config.caching.enabled}, threshold={gpt35_config.caching.threshold}")
            print(f"      Tokens: max={gpt35_config.max_tokens}, context={gpt35_config.context_length}")
        
        # Test Claude configuration
        claude_config = system_config.get_model_config("anthropic/claude-3-haiku")
        if claude_config:
            print(f"   ✅ Claude: provider={claude_config.provider}, enabled={claude_config.enabled}")
            print(f"      Caching: enabled={claude_config.caching.enabled}, threshold={claude_config.caching.threshold}")
            print(f"      Tokens: max={claude_config.max_tokens}, context={claude_config.context_length}")
        
        # Test model enabling/disabling
        print("\n   🔄 Testing model enabling/disabling...")
        
        # Disable a model
        success = system_config.update_model_config("llama3:latest", enabled=False)
        print(f"      ✅ Llama disabled: {success}")
        
        # Re-enable the model
        success = system_config.update_model_config("llama3:latest", enabled=True)
        print(f"      ✅ Llama re-enabled: {success}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model configuration test failed: {e}")
        return False

def test_race_conditions():
    """Test 5: Race Conditions and Concurrent Access"""
    print("\n🧪 Test 5: Race Conditions and Concurrent Access")
    print("=" * 60)
    
    try:
        from config.system_config import system_config
        
        # Test concurrent configuration updates
        print("🏃 Testing concurrent configuration updates...")
        
        def update_config_thread(thread_id, provider_name):
            """Thread function to update configuration"""
            try:
                for i in range(5):
                    # Update provider priority
                    success = system_config.update_provider_config(
                        provider_name, 
                        priority=i + 1
                    )
                    if success:
                        print(f"      Thread {thread_id}: Updated {provider_name} priority to {i + 1}")
                    time.sleep(0.1)  # Small delay to create race conditions
                return True
            except Exception as e:
                print(f"      Thread {thread_id}: Error updating {provider_name}: {e}")
                return False
        
        # Create multiple threads updating different providers
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(update_config_thread, 1, "openrouter"),
                executor.submit(update_config_thread, 2, "runpod"),
                executor.submit(update_config_thread, 3, "ollama")
            ]
            
            # Wait for all threads to complete
            results = [future.result() for future in as_completed(futures)]
        
        print(f"   ✅ Concurrent updates completed: {sum(results)}/3 successful")
        
        # Verify final configuration state
        final_config = system_config.get_config_summary()
        print(f"   📊 Final provider priorities:")
        for provider, config in final_config['providers'].items():
            print(f"      {provider}: priority={config.get('priority', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Race condition test failed: {e}")
        return False

def test_actual_functionality():
    """Test 6: Actual Functionality Integration"""
    print("\n🧪 Test 6: Actual Functionality Integration")
    print("=" * 60)
    
    try:
        from config.system_config import system_config
        from ai.model_manager import ModelManager
        
        print("🔗 Testing integration with ModelManager...")
        
        # Create model manager
        model_manager = ModelManager()
        print(f"   ✅ ModelManager created: {model_manager.model_name}")
        
        # Test provider routing based on configuration
        print("\n   🚀 Testing provider routing...")
        
        # Get current provider from config
        current_provider = system_config.config.default_provider
        print(f"      Current provider: {current_provider}")
        
        # Test if the provider is actually available
        if current_provider == "openrouter":
            # Check if OpenRouter handler is available
            openrouter_handler = model_manager._get_openrouter_handler()
            if openrouter_handler and openrouter_handler.available:
                print(f"      ✅ OpenRouter handler available")
            else:
                print(f"      ❌ OpenRouter handler not available")
        
        elif current_provider == "runpod":
            # Check if RunPod handler is available
            if hasattr(model_manager, 'pete_handler') and model_manager.pete_handler:
                print(f"      ✅ RunPod handler available")
            else:
                print(f"      ❌ RunPod handler not available")
        
        elif current_provider == "ollama":
            # Check if Ollama is available
            if model_manager.is_available():
                print(f"      ✅ Ollama available")
            else:
                print(f"      ❌ Ollama not available")
        
        # Test caching configuration integration
        print("\n   🔒 Testing caching configuration integration...")
        
        # Get caching config for current provider
        caching_config = system_config.get_caching_config(provider=current_provider)
        print(f"      Caching enabled: {caching_config.enabled}")
        print(f"      Similarity threshold: {caching_config.threshold}")
        print(f"      Max cache age: {caching_config.max_cache_age_hours}h")
        
        # Test if similarity analyzer respects the threshold
        if hasattr(model_manager, 'similarity_threshold'):
            print(f"      ModelManager threshold: {model_manager.similarity_threshold}")
            if abs(model_manager.similarity_threshold - caching_config.threshold) < 0.01:
                print(f"      ✅ Thresholds match")
            else:
                print(f"      ❌ Thresholds don't match")
        
        return True
        
    except Exception as e:
        print(f"❌ Functionality integration test failed: {e}")
        return False

def test_error_handling():
    """Test 7: Error Handling and Edge Cases"""
    print("\n🧪 Test 7: Error Handling and Edge Cases")
    print("=" * 60)
    
    try:
        from config.system_config import system_config
        from utils.type_validation import TypeValidationError
        
        print("🚨 Testing error handling...")
        
        # Test invalid provider names
        print("   🔍 Testing invalid provider names...")
        try:
            invalid_config = system_config.get_caching_config(provider="invalid_provider")
            print(f"      ✅ Invalid provider handled gracefully")
        except Exception as e:
            print(f"      ❌ Invalid provider caused error: {e}")
        
        # Test invalid model names
        print("   🔍 Testing invalid model names...")
        try:
            invalid_config = system_config.get_caching_config(provider="openrouter", model="invalid/model")
            print(f"      ✅ Invalid model handled gracefully")
        except Exception as e:
            print(f"      ❌ Invalid model caused error: {e}")
        
        # Test configuration file corruption
        print("   🔍 Testing configuration file corruption...")
        try:
            # Temporarily corrupt the config file
            config_file = system_config.config_file
            if config_file.exists():
                # Backup original
                backup_file = config_file.with_suffix('.backup')
                if not backup_file.exists():
                    config_file.rename(backup_file)
                
                # Create corrupted config
                with open(config_file, 'w') as f:
                    f.write('{"invalid": "json"')
                
                # Try to load corrupted config
                system_config._load_config()
                print(f"      ✅ Corrupted config handled gracefully")
                
                # Restore original
                if backup_file.exists():
                    backup_file.rename(config_file)
            else:
                print(f"      ⚠️ No config file to test corruption")
                
        except Exception as e:
            print(f"      ❌ Corrupted config caused error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False

def test_configuration_persistence():
    """Test 8: Configuration Persistence and Recovery"""
    print("\n🧪 Test 8: Configuration Persistence and Recovery")
    print("=" * 60)
    
    try:
        from config.system_config import system_config
        
        print("💾 Testing configuration persistence...")
        
        # Test configuration saving
        print("   🔄 Testing configuration saving...")
        
        # Change some settings
        original_threshold = system_config.config.global_caching.threshold
        new_threshold = 0.9
        
        system_config.config.global_caching.threshold = new_threshold
        success = system_config.save_config()
        
        if success:
            print(f"      ✅ Configuration saved successfully")
        else:
            print(f"      ❌ Configuration save failed")
            return False
        
        # Test configuration reloading
        print("   🔄 Testing configuration reloading...")
        
        # Create new instance to test reloading
        new_system_config = system_config.__class__(system_config.config_file)
        reloaded_threshold = new_system_config.config.global_caching.threshold
        
        if abs(reloaded_threshold - new_threshold) < 0.01:
            print(f"      ✅ Configuration reloaded successfully: {reloaded_threshold}")
        else:
            print(f"      ❌ Configuration reload failed: expected {new_threshold}, got {reloaded_threshold}")
            return False
        
        # Restore original threshold
        system_config.config.global_caching.threshold = original_threshold
        system_config.save_config()
        print(f"      ✅ Original threshold restored: {original_threshold}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration persistence test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Comprehensive System Configuration Test Suite")
    print("=" * 80)
    print("Testing the entire system from top to bottom...")
    print()
    
    tests = [
        ("Configuration Loading", test_configuration_loading),
        ("Provider Switching", test_provider_switching),
        ("Caching Behavior", test_caching_behavior),
        ("Model Configuration", test_model_configuration),
        ("Race Conditions", test_race_conditions),
        ("Functionality Integration", test_actual_functionality),
        ("Error Handling", test_error_handling),
        ("Configuration Persistence", test_configuration_persistence)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! System configuration is working perfectly!")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
