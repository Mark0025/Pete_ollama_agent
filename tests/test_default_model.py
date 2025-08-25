#!/usr/bin/env python3
"""
Test RunPod AI with Default Model
Test chat completions using common default model names
"""

import os
import requests
import json

def test_default_models():
    """Test chat completions with default model names"""
    
    # Get API key from environment
    api_key = os.getenv('RUNPOD_API_KEY')
    endpoint_id = os.getenv('RUNPOD_SERVERLESS_ENDPOINT')
    
    if not api_key:
        print("❌ RUNPOD_API_KEY not set")
        return
    
    if not endpoint_id:
        print("❌ RUNPOD_SERVERLESS_ENDPOINT not set")
        return
    
    print("🔍 Testing RunPod AI with Default Models")
    print("=" * 60)
    print(f"📋 Endpoint ID: {endpoint_id}")
    print(f"🔑 API Key: {'✅ Set' if api_key else '❌ Not set'}")
    print()
    
    base_url = f"https://api.runpod.ai/v2/{endpoint_id}/openai/v1"
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    print(f"🌐 Base URL: {base_url}")
    print()
    
    # Common default model names that RunPod might use
    default_models = [
        'default',
        'model',
        'gpt-3.5-turbo',
        'gpt-4',
        'llama2',
        'mistral',
        'codellama',
        'neural-chat',
        'vicuna',
        'wizardlm',
        'peteollama:jamie-fixed',  # Try the original one too
    ]
    
    # Test each model name
    for model_name in default_models:
        print(f"🔍 Testing model: {model_name}")
        print(f"   URL: {base_url}/chat/completions")
        
        try:
            test_data = {
                'model': model_name,
                'messages': [
                    {'role': 'user', 'content': 'Hello! Please respond with just "Hi there!"'}
                ],
                'max_tokens': 20,
                'temperature': 0.1
            }
            
            response = requests.post(f"{base_url}/chat/completions", headers=headers, json=test_data, timeout=15)
            print(f"   📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ SUCCESS!")
                try:
                    data = response.json()
                    content = data.get('choices', [{}])[0].get('message', {}).get('content', 'No content')
                    print(f"   📄 Response: {content}")
                    print(f"   🎯 Model used: {data.get('model', 'Unknown')}")
                    print(f"   📊 Usage: {data.get('usage', {})}")
                    
                    # If this works, we found our working model!
                    print(f"\n🎉 WORKING MODEL FOUND: {model_name}")
                    print("   You can now use this model name in your serverless handler!")
                    
                except Exception as e:
                    print(f"   📄 Response parsing error: {e}")
                    print(f"   📄 Raw response: {response.text}")
                    
            elif response.status_code == 400:
                print("   ⚠️  Bad Request - model name issue")
                try:
                    data = response.json()
                    error_msg = data.get('error', {}).get('message', 'Unknown error')
                    print(f"   📄 Error: {error_msg}")
                except Exception as e:
                    print(f"   📄 Error parsing: {e}")
                    print(f"   📄 Raw error: {response.text}")
                    
            elif response.status_code == 500:
                print("   ❌ Internal Server Error")
                try:
                    data = response.json()
                    error_msg = data.get('error', 'Unknown error')
                    print(f"   📄 Error: {error_msg}")
                except Exception as e:
                    print(f"   📄 Error parsing: {e}")
                    print(f"   📄 Raw error: {response.text}")
                    
            else:
                print(f"   ❌ Failed with status {response.status_code}")
                print(f"   📄 Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("   " + "-" * 50)
        
        # If we found a working model, we can stop testing
        if response.status_code == 200:
            break
    
    print("\n📊 Summary:")
    print("   - If any model worked (200 status), use that model name")
    print("   - Update your serverless handler to use the working model")
    print("   - We can address the peteollama:jamie-fixed model later")

if __name__ == "__main__":
    test_default_models()
