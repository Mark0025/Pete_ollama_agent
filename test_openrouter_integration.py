#!/usr/bin/env python3
"""
OpenRouter Integration Tests
===========================

Comprehensive tests for OpenRouter integration including:
- API key validation
- Model fetching
- Model filtering  
- Provider separation
- Chat completions
- Error handling
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_openrouter_integration():
    """Run comprehensive OpenRouter integration tests"""
    
    print("🌐 OpenRouter Integration Tests")
    print("=" * 60)
    
    results = {
        "api_key_test": False,
        "model_fetching": False,
        "model_filtering": False,
        "provider_separation": False,
        "chat_completion": False,
        "error_handling": False
    }
    
    try:
        # Test 1: API Key Validation
        print("\n1️⃣ Testing API Key Configuration")
        print("-" * 40)
        
        # Check environment variable
        api_key = os.getenv("OPENROUTER_API_KEY")
        if api_key:
            print(f"✅ API Key found: {api_key[:8]}...{api_key[-4:]}")
            results["api_key_test"] = True
        else:
            print("❌ API Key not found in environment")
            return results
        
        # Test 2: Model Fetching
        print("\n2️⃣ Testing Model Fetching")
        print("-" * 30)
        
        from vapi.services.provider_service import ProviderService
        provider_service = ProviderService()
        
        try:
            # Fetch OpenRouter models
            openrouter_personas = await provider_service.get_personas_for_provider('openrouter')
            print(f"✅ Fetched {len(openrouter_personas)} OpenRouter models")
            
            # Show first 5 models
            print("   📋 First 5 models:")
            for i, persona in enumerate(openrouter_personas[:5]):
                print(f"      {i+1}. {persona.name} ({persona.type})")
            
            results["model_fetching"] = True
            
        except Exception as e:
            print(f"❌ Model fetching failed: {e}")
            return results
        
        # Test 3: Model Filtering and Provider Separation
        print("\n3️⃣ Testing Model Filtering & Provider Separation")
        print("-" * 50)
        
        try:
            # Test different providers
            ollama_personas = await provider_service.get_personas_for_provider('ollama')
            runpod_personas = await provider_service.get_personas_for_provider('runpod')
            
            print(f"✅ Ollama models: {len(ollama_personas)}")
            print(f"✅ OpenRouter models: {len(openrouter_personas)}")
            print(f"✅ RunPod models: {len(runpod_personas)}")
            
            # Check for model separation
            ollama_names = {p.name for p in ollama_personas}
            openrouter_names = {p.name for p in openrouter_personas}
            runpod_names = {p.name for p in runpod_personas}
            
            # Check for Jamie models in wrong providers
            jamie_in_openrouter = [name for name in openrouter_names if 'jamie' in name.lower()]
            openrouter_in_ollama = [name for name in ollama_names if 'openrouter:' in name.lower()]
            
            if jamie_in_openrouter:
                print(f"⚠️ Found Jamie models in OpenRouter: {jamie_in_openrouter}")
            else:
                print("✅ No Jamie models found in OpenRouter (correct separation)")
                results["provider_separation"] = True
            
            if openrouter_in_ollama:
                print(f"⚠️ Found OpenRouter models in Ollama: {openrouter_in_ollama}")
            else:
                print("✅ No OpenRouter models found in Ollama (correct separation)")
            
            results["model_filtering"] = True
            
        except Exception as e:
            print(f"❌ Model filtering test failed: {e}")
        
        # Test 4: API Endpoints
        print("\n4️⃣ Testing API Endpoints")
        print("-" * 25)
        
        import requests
        
        try:
            # Test personas endpoint with OpenRouter
            response = requests.get("http://localhost:8000/personas?provider=openrouter", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Personas endpoint: {len(data)} models returned")
                
                # Check if models have required fields
                if data and all('name' in model and 'provider' in model for model in data):
                    print("✅ Model data structure is correct")
                else:
                    print("⚠️ Model data structure may be incomplete")
            else:
                print(f"❌ Personas endpoint failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ API endpoint test failed: {e}")
        
        # Test 5: Chat Completion (if available)
        print("\n5️⃣ Testing OpenRouter Chat Completion")
        print("-" * 40)
        
        try:
            # Test chat completion with OpenRouter
            chat_data = {
                "message": "Hello! Please respond with just 'OpenRouter working'",
                "provider": "openrouter",
                "model": openrouter_personas[0].name if openrouter_personas else "meta-llama/llama-3.1-8b-instruct:free"
            }
            
            print(f"   Testing with model: {chat_data['model']}")
            
            response = requests.post(
                "http://localhost:8000/chat", 
                json=chat_data, 
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Chat completion successful")
                print(f"   Response: {result.get('response', 'No response field')[:100]}...")
                results["chat_completion"] = True
            else:
                print(f"❌ Chat completion failed: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Chat completion test failed: {e}")
        
        # Test 6: Error Handling
        print("\n6️⃣ Testing Error Handling")
        print("-" * 25)
        
        try:
            # Test with invalid model
            invalid_chat_data = {
                "message": "Test",
                "provider": "openrouter", 
                "model": "invalid-model-name"
            }
            
            response = requests.post(
                "http://localhost:8000/chat",
                json=invalid_chat_data,
                timeout=10
            )
            
            if response.status_code in [400, 422, 500]:
                print("✅ Error handling works for invalid models")
                results["error_handling"] = True
            else:
                print(f"⚠️ Unexpected response for invalid model: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
        
        # Test 7: Configuration Integration
        print("\n7️⃣ Testing Configuration Integration")
        print("-" * 35)
        
        try:
            # Test environment variables endpoint
            response = requests.get("http://localhost:8000/admin/environment-variables", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "OPENROUTER_API_KEY" in data.get("environment_variables", {}):
                    print("✅ OpenRouter API key visible in admin configuration")
                else:
                    print("❌ OpenRouter API key not found in admin configuration")
            else:
                print(f"❌ Environment variables endpoint failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Configuration integration test failed: {e}")
        
    except Exception as e:
        print(f"❌ OpenRouter integration test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n8️⃣ TEST SUMMARY")
    print("-" * 15)
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"📊 Results: {passed}/{total} tests passed")
    print()
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    if passed == total:
        print(f"\n🎉 All OpenRouter integration tests passed!")
    elif passed >= total * 0.7:
        print(f"\n✅ Most OpenRouter tests passed ({passed}/{total})")
    else:
        print(f"\n⚠️ Several OpenRouter tests failed ({passed}/{total})")
    
    return results

def main():
    """Main function"""
    return asyncio.run(test_openrouter_integration())

if __name__ == "__main__":
    main()
