#!/usr/bin/env python3
"""
Test RunPod AI API Endpoints
Tests different endpoint paths to find the correct chat endpoint
"""

import os
import requests
import json

def test_runpod_ai_endpoints():
    """Test different RunPod AI API endpoints"""
    
    # Get API key from environment
    api_key = os.getenv('RUNPOD_API_KEY')
    endpoint_id = os.getenv('RUNPOD_SERVERLESS_ENDPOINT')
    
    if not api_key:
        print("❌ RUNPOD_API_KEY not set")
        return
    
    if not endpoint_id:
        print("❌ RUNPOD_SERVERLESS_ENDPOINT not set")
        return
    
    print("🔍 Testing RunPod AI API Endpoints")
    print("=" * 50)
    print(f"📋 Endpoint ID: {endpoint_id}")
    print(f"🔑 API Key: {'✅ Set' if api_key else '❌ Not set'}")
    print()
    
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    # Test different endpoint paths
    endpoints_to_test = [
        ('/health', 'GET'),
        ('/chat/completions', 'POST'),
        ('/chat', 'POST'),
        ('/api/chat', 'POST'),
        ('/completions', 'POST'),
        ('/generate', 'POST'),
        ('/infer', 'POST'),
        ('/predict', 'POST'),
        ('/', 'GET'),
    ]
    
    for path, method in endpoints_to_test:
        url = f'https://api.runpod.ai/v2/{endpoint_id}{path}'
        print(f"🔍 Testing: {method} {path}")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=15)
            else:
                # For POST requests, send a simple test payload
                test_data = {
                    'messages': [{'role': 'user', 'content': 'Hello'}],
                    'model': 'test'
                }
                response = requests.post(url, headers=headers, json=test_data, timeout=15)
            
            print(f"   📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ SUCCESS!")
                try:
                    data = response.json()
                    print(f"   📄 Response: {json.dumps(data, indent=4)[:200]}...")
                except:
                    print(f"   📄 Response: {response.text[:200]}...")
            elif response.status_code == 404:
                print("   ❌ Not Found")
            elif response.status_code == 405:
                print("   ⚠️  Method Not Allowed")
            elif response.status_code == 400:
                print("   ⚠️  Bad Request")
                try:
                    data = response.json()
                    print(f"   📄 Error: {json.dumps(data, indent=4)[:200]}...")
                except:
                    print(f"   📄 Error: {response.text[:200]}...")
            else:
                print(f"   ⚠️  Status {response.status_code}")
                print(f"   📄 Response: {response.text[:200]}...")
                
        except requests.exceptions.Timeout:
            print("   ⏰ Timeout")
        except requests.exceptions.ConnectionError as e:
            print(f"   🔌 Connection error: {e}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("   " + "-" * 40)
    
    print("\n📊 Summary:")
    print("   - Look for endpoints that return 200 OK")
    print("   - 404 means endpoint doesn't exist")
    print("   - 405 means wrong HTTP method")
    print("   - 400 means endpoint exists but request format is wrong")

if __name__ == "__main__":
    test_runpod_ai_endpoints()
