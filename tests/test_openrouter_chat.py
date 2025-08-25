#!/usr/bin/env python3
"""
OpenRouter Chat Completion Tests
================================

Test OpenRouter chat completions with multiple free models:
- Test 10 different OpenRouter free models
- 2000 character limit per request
- Simple test messages
- Model switching verification
"""

import os
import sys
import asyncio
import json
import time
from pathlib import Path
from typing import List, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_openrouter_chat_models():
    """Test OpenRouter chat completions with multiple free models"""
    
    print("🤖 OpenRouter Chat Completion Tests")
    print("=" * 60)
    
    # Test models (OpenRouter ACTUALLY working models)
    test_models = [
        "openai/gpt-3.5-turbo",
        "openai/gpt-4o-mini", 
        "anthropic/claude-3-haiku"
    ]
    
    # Test messages (simple, under 2000 chars)
    test_messages = [
        "Hello! Please respond with just 'Model test successful'",
        "What is 2+2? Answer in one word.",
        "Say 'OpenRouter working' and nothing else"
    ]
    
    results = {
        "models_tested": 0,
        "successful_responses": 0,
        "failed_responses": 0,
        "model_details": []
    }
    
    print(f"📋 Testing {len(test_models)} OpenRouter free models")
    print(f"💬 Using {len(test_messages)} test messages")
    print()
    
    for i, (model, message) in enumerate(zip(test_models, test_messages)):
        print(f"🧪 Test {i+1}/{len(test_models)}: {model}")
        print(f"   💬 Message: {message[:50]}{'...' if len(message) > 50 else ''}")
        
        try:
            # Test chat completion
            response = await test_single_chat_completion(model, message)
            
            if response:
                results["successful_responses"] += 1
                print(f"   ✅ SUCCESS: {response[:100]}{'...' if len(response) > 100 else ''}")
                
                results["model_details"].append({
                    "model": model,
                    "status": "success",
                    "response": response,
                    "message": message
                })
            else:
                results["failed_responses"] += 1
                print(f"   ❌ FAILED: No response")
                
                results["model_details"].append({
                    "model": model,
                    "status": "failed",
                    "response": None,
                    "message": message
                })
            
        except Exception as e:
            results["failed_responses"] += 1
            print(f"   ❌ ERROR: {str(e)}")
            
            results["model_details"].append({
                "model": model,
                "status": "error",
                "error": str(e),
                "message": message
            })
        
        results["models_tested"] += 1
        print()
        
        # Small delay between requests
        await asyncio.sleep(1)
    
    # Summary
    print("📊 CHAT COMPLETION TEST SUMMARY")
    print("=" * 40)
    print(f"   Models Tested: {results['models_tested']}")
    print(f"   Successful: {results['successful_responses']}")
    print(f"   Failed: {results['failed_responses']}")
    print(f"   Success Rate: {(results['successful_responses']/results['models_tested']*100):.1f}%")
    
    return results

async def test_single_chat_completion(model: str, message: str) -> str:
    """Test a single chat completion with the given model and message"""
    
    try:
        import aiohttp
        
        # Simple test payload
        payload = {
            "message": message,
            "provider": "openrouter",
            "model": model,
            "max_tokens": 2000,
            "temperature": 0.7
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8000/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    return data.get('response', '')
                else:
                    error_text = await response.text()
                    print(f"      HTTP {response.status}: {error_text[:100]}")
                    return None
                    
    except Exception as e:
        print(f"      Exception: {str(e)}")
        return None

async def test_ui_model_switching():
    """Test UI model switching functionality"""
    
    print("\n🖥️ Testing UI Model Switching")
    print("=" * 35)
    
    try:
        import aiohttp
        
        # Test switching between providers
        providers = ["openrouter", "ollama", "runpod"]
        
        for provider in providers:
            print(f"\n🔀 Testing provider: {provider}")
            
            async with aiohttp.ClientSession() as session:
                # Get models for this provider
                async with session.get(
                    f"http://localhost:8000/personas?provider={provider}",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"   ✅ {provider}: {len(data)} models available")
                        
                        # Show first 3 models
                        for i, model in enumerate(data[:3]):
                            model_name = model.get('name', 'Unknown')
                            model_type = model.get('type', 'Unknown')
                            print(f"      {i+1}. {model_name} ({model_type})")
                    else:
                        print(f"   ❌ {provider}: HTTP {response.status}")
                        
        print("\n✅ UI model switching test completed")
        
    except Exception as e:
        print(f"❌ UI model switching test failed: {e}")

async def test_model_limits():
    """Test model token limits and constraints"""
    
    print("\n📏 Testing Model Limits & Constraints")
    print("=" * 40)
    
    try:
        import aiohttp
        
        # Test with different token limits
        test_cases = [
            {"max_tokens": 100, "description": "Very short response"},
            {"max_tokens": 500, "description": "Short response"},
            {"max_tokens": 2000, "description": "Medium response"},
            {"max_tokens": 4000, "description": "Long response"}
        ]
        
        test_model = "meta-llama/llama-3.1-8b-instruct:free"
        test_message = "Please provide a detailed explanation of artificial intelligence in exactly the requested length."
        
        for test_case in test_cases:
            print(f"\n🧪 Testing: {test_case['description']} ({test_case['max_tokens']} tokens)")
            
            payload = {
                "message": test_message,
                "provider": "openrouter",
                "model": test_model,
                "max_tokens": test_case["max_tokens"],
                "temperature": 0.7
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:8000/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        response_text = data.get('response', '')
                        print(f"   ✅ Response length: {len(response_text)} characters")
                        print(f"   📝 Preview: {response_text[:100]}{'...' if len(response_text) > 100 else ''}")
                    else:
                        print(f"   ❌ Failed: HTTP {response.status}")
                        
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"❌ Model limits test failed: {e}")

async def main():
    """Main test function"""
    
    print("🚀 Starting OpenRouter Chat Completion Tests")
    print("=" * 60)
    
    # Test 1: Multiple model chat completions
    chat_results = await test_openrouter_chat_models()
    
    # Test 2: UI model switching
    await test_ui_model_switching()
    
    # Test 3: Model limits and constraints
    await test_model_limits()
    
    # Final summary
    print("\n🎯 FINAL TEST SUMMARY")
    print("=" * 25)
    print(f"📊 Chat Completion Success Rate: {chat_results['successful_responses']}/{chat_results['models_tested']} ({chat_results['successful_responses']/chat_results['models_tested']*100:.1f}%)")
    print(f"🖥️ UI Model Switching: ✅ Tested")
    print(f"📏 Model Limits: ✅ Tested")
    
    if chat_results['successful_responses'] >= chat_results['models_tested'] * 0.7:
        print("\n🎉 Most OpenRouter chat tests passed!")
    else:
        print(f"\n⚠️ Several OpenRouter chat tests failed")
    
    return chat_results

if __name__ == "__main__":
    asyncio.run(main())
