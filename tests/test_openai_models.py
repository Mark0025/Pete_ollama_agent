#!/usr/bin/env python3
"""
Test RunPod AI OpenAI Models Endpoint
Check what models are available on the OpenAI-compatible endpoint
"""

import os
import requests
import json

def test_openai_models():
    """Test the OpenAI models endpoint"""
    
    # Get API key from environment
    api_key = os.getenv('RUNPOD_API_KEY')
    endpoint_id = os.getenv('RUNPOD_SERVERLESS_ENDPOINT')
    
    if not api_key:
        print("❌ RUNPOD_API_KEY not set")
        return
    
    if not endpoint_id:
        print("❌ RUNPOD_SERVERLESS_ENDPOINT not set")
        return
    
    print("🔍 Testing RunPod AI OpenAI Models Endpoint")
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
    
    # Test 1: Get models list
    print("🔍 Test 1: Get available models")
    print(f"   URL: {base_url}/models")
    
    try:
        response = requests.get(f"{base_url}/models", headers=headers, timeout=15)
        print(f"   📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ SUCCESS!")
            try:
                data = response.json()
                print(f"   📄 Response: {json.dumps(data, indent=4)}")
                
                # Check what models are available
                if 'data' in data and data['data']:
                    print(f"\n   📋 Available Models:")
                    for model in data['data']:
                        print(f"      - {model.get('id', 'N/A')}")
                        print(f"        Object: {model.get('object', 'N/A')}")
                        print(f"        Created: {model.get('created', 'N/A')}")
                        print(f"        Owned by: {model.get('owned_by', 'N/A')}")
                        print()
                else:
                    print("   ⚠️  No models found in response")
                    
            except Exception as e:
                print(f"   📄 Response parsing error: {e}")
                print(f"   📄 Raw response: {response.text}")
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            print(f"   📄 Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("   " + "-" * 50)
    
    # Test 2: Try a simple chat completion with a generic model name
    print("\n🔍 Test 2: Try chat completion with generic model")
    print(f"   URL: {base_url}/chat/completions")
    
    try:
        # Try with a generic model name that might exist
        test_data = {
            'model': 'gpt-3.5-turbo',  # Try a generic OpenAI model name
            'messages': [
                {'role': 'user', 'content': 'Hello'}
            ],
            'max_tokens': 10
        }
        
        response = requests.post(f"{base_url}/chat/completions", headers=headers, json=test_data, timeout=15)
        print(f"   📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ SUCCESS!")
            try:
                data = response.json()
                print(f"   📄 Response: {json.dumps(data, indent=4)}")
            except Exception as e:
                print(f"   📄 Response parsing error: {e}")
                print(f"   📄 Raw response: {response.text}")
        elif response.status_code == 400:
            print("   ⚠️  Bad Request - might be model name issue")
            try:
                data = response.json()
                print(f"   📄 Error: {json.dumps(data, indent=4)}")
            except Exception as e:
                print(f"   📄 Error parsing: {e}")
                print(f"   📄 Raw error: {response.text}")
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            print(f"   📄 Response: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("   " + "-" * 50)
    
    print("\n📊 Summary:")
    print("   - Check what models are actually available")
    print("   - The model name in your config might not match what's deployed")
    print("   - You may need to update the MODEL_NAME environment variable")

if __name__ == "__main__":
    test_openai_models()
