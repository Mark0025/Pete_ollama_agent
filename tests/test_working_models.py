#!/usr/bin/env python3
"""
Test Working OpenRouter Models
==============================

Test which OpenRouter models are actually accessible with our API key.
"""

import requests
import json
import time

def test_model_accessibility():
    """Test which models are actually accessible"""
    
    api_key = "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"
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Models to test (mix of different types)
    test_models = [
        "openai/gpt-3.5-turbo",
        "openai/gpt-4o-mini", 
        "anthropic/claude-3-haiku",
        "google/gemini-flash-1.5",
        "mistralai/mistral-7b-instruct",
        "meta-llama/llama-3.1-8b-instruct",
        "meta-llama/llama-3.1-70b-instruct",
        "microsoft/phi-3-mini-4k-instruct",
        "google/gemma-2-9b-it",
        "nousresearch/nous-hermes-2-mixtral-8x7b-dpo",
        "openai/gpt-oss-20b:free",
        "z-ai/glm-4.5-air:free",
        "qwen/qwen3-coder:free"
    ]
    
    print("🧪 Testing OpenRouter Model Accessibility")
    print("=" * 50)
    
    working_models = []
    failed_models = []
    
    for i, model in enumerate(test_models):
        print(f"Testing {i+1}/{len(test_models)}: {model}")
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Say 'test'"}],
            "max_tokens": 10
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if 'choices' in data and data['choices']:
                    print(f"   ✅ SUCCESS: {data['choices'][0]['message']['content']}")
                    working_models.append(model)
                else:
                    print(f"   ⚠️  PARTIAL: API call succeeded but no response")
                    failed_models.append(model)
            else:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                print(f"   ❌ FAILED: {response.status_code} - {error_msg}")
                failed_models.append(model)
                
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            failed_models.append(model)
        
        # Small delay between requests
        time.sleep(1)
        print()
    
    # Summary
    print("📊 TESTING SUMMARY")
    print("=" * 20)
    print(f"✅ Working models: {len(working_models)}")
    print(f"❌ Failed models: {len(failed_models)}")
    print(f"📊 Success rate: {len(working_models)/len(test_models)*100:.1f}%")
    
    print("\n🎯 WORKING MODELS:")
    for model in working_models:
        print(f"   ✅ {model}")
    
    print("\n🚫 FAILED MODELS:")
    for model in failed_models:
        print(f"   ❌ {model}")
    
    # Save results
    results = {
        "working_models": working_models,
        "failed_models": failed_models,
        "total_tested": len(test_models),
        "success_rate": len(working_models)/len(test_models)*100
    }
    
    with open("working_openrouter_models.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: working_openrouter_models.json")
    
    return working_models

if __name__ == "__main__":
    test_model_accessibility()
