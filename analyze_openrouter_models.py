#!/usr/bin/env python3
"""
OpenRouter Model Availability Analyzer
=====================================

Analyze which OpenRouter models are actually available and accessible
with our API key, then update our system configuration accordingly.
"""

import requests
import json
import os
from typing import List, Dict, Any

def analyze_openrouter_models():
    """Analyze OpenRouter models to determine availability"""
    
    api_key = "***REDACTED***"
    url = "https://openrouter.ai/api/v1/models"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    print("🔍 Analyzing OpenRouter models...")
    print("=" * 50)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        models = data.get('data', [])
        
        print(f"📊 Total models found: {len(models)}")
        print()
        
        # Categorize models by availability
        free_models = []
        paid_models = []
        testable_models = []
        
        for model in models:
            model_id = model.get('id', '')
            pricing = model.get('pricing', {})
            
            # Get pricing info
            prompt_cost = float(pricing.get('prompt', '999'))
            completion_cost = float(pricing.get('completion', '999'))
            
            # Check if model is free
            if prompt_cost == 0 and completion_cost == 0:
                free_models.append({
                    'id': model_id,
                    'name': model.get('name', 'Unknown'),
                    'description': model.get('description', ''),
                    'context_length': model.get('context_length', 0),
                    'pricing': pricing
                })
            else:
                paid_models.append({
                    'id': model_id,
                    'name': model.get('name', 'Unknown'),
                    'prompt_cost': prompt_cost,
                    'completion_cost': completion_cost
                })
        
        print(f"🆓 FREE MODELS: {len(free_models)}")
        print(f"💰 PAID MODELS: {len(paid_models)}")
        print()
        
        # Show first 10 free models
        print("📋 FIRST 10 FREE MODELS:")
        print("-" * 30)
        for i, model in enumerate(free_models[:10]):
            print(f"{i+1:2d}. {model['id']}")
            print(f"    Name: {model['name']}")
            print(f"    Context: {model['context_length']:,} tokens")
            print()
        
        # Test a few models to see which ones actually work
        print("🧪 TESTING MODEL ACCESSIBILITY...")
        print("-" * 35)
        
        test_models = free_models[:5]  # Test first 5 free models
        
        for i, model in enumerate(test_models):
            print(f"Testing {i+1}/{len(test_models)}: {model['id']}")
            
            # Test if we can actually use this model
            test_url = "https://openrouter.ai/api/v1/chat/completions"
            test_payload = {
                "model": model['id'],
                "messages": [{"role": "user", "content": "Say 'test'"}],
                "max_tokens": 10
            }
            
            try:
                test_response = requests.post(test_url, headers=headers, json=test_payload, timeout=30)
                
                if test_response.status_code == 200:
                    test_data = test_response.json()
                    if 'choices' in test_data and test_data['choices']:
                        print(f"   ✅ SUCCESS: Model accessible")
                        testable_models.append(model['id'])
                    else:
                        print(f"   ⚠️  PARTIAL: API call succeeded but no response")
                else:
                    error_msg = test_response.json().get('error', {}).get('message', 'Unknown error')
                    print(f"   ❌ FAILED: {test_response.status_code} - {error_msg}")
                    
            except Exception as e:
                print(f"   ❌ ERROR: {str(e)}")
            
            print()
        
        # Summary
        print("📊 ANALYSIS SUMMARY")
        print("=" * 20)
        print(f"✅ Total models: {len(models)}")
        print(f"🆓 Free models: {len(free_models)}")
        print(f"🧪 Testable models: {len(testable_models)}")
        print(f"💰 Paid models: {len(paid_models)}")
        
        # Save results for our system
        results = {
            "total_models": len(models),
            "free_models": len(free_models),
            "testable_models": len(testable_models),
            "paid_models": len(paid_models),
            "working_free_models": testable_models,
            "all_free_models": [m['id'] for m in free_models]
        }
        
        with open("openrouter_model_analysis.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: openrouter_model_analysis.json")
        
        return results
        
    except Exception as e:
        print(f"❌ Error analyzing models: {e}")
        return None

if __name__ == "__main__":
    analyze_openrouter_models()
