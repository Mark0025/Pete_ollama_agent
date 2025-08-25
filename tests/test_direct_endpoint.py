#!/usr/bin/env python3
"""
Test Direct RunPod AI Endpoint
Tests different chat endpoints on the working direct API structure
"""

import os
import requests
import json

def test_direct_endpoint():
    """Test different chat endpoints on the direct RunPod AI API"""
    
    # Get API key from environment
    api_key = os.getenv('RUNPOD_API_KEY')
    endpoint_id = os.getenv('RUNPOD_SERVERLESS_ENDPOINT')
    
    if not api_key:
        print("❌ RUNPOD_API_KEY not set")
        return
    
    if not endpoint_id:
        print("❌ RUNPOD_SERVERLESS_ENDPOINT not set")
        return
    
    print("🔍 Testing Direct RunPod AI Endpoint")
    print("=" * 50)
    print(f"📋 Endpoint ID: {endpoint_id}")
    print(f"🔑 API Key: {'✅ Set' if api_key else '❌ Not set'}")
    print()
    
    base_url = f"https://api.runpod.ai/v2/{endpoint_id}"
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    print(f"🌐 Base URL: {base_url}")
    print()
    
    # Test different chat endpoints and request formats
    test_cases = [
        # Test 1: Standard chat completions
        {
            'path': '/chat/completions',
            'method': 'POST',
            'data': {
                'messages': [{'role': 'user', 'content': 'Hello'}],
                'model': 'peteollama:jamie-fixed'
            },
            'description': 'Standard chat completions'
        },
        
        # Test 2: Simple chat
        {
            'path': '/chat',
            'method': 'POST',
            'data': {
                'message': 'Hello',
                'model': 'peteollama:jamie-fixed'
            },
            'description': 'Simple chat format'
        },
        
        # Test 3: Ollama-style chat
        {
            'path': '/api/chat',
            'method': 'POST',
            'data': {
                'message': 'Hello',
                'model': 'peteollama:jamie-fixed'
            },
            'description': 'Ollama-style chat'
        },
        
        # Test 4: Generate endpoint
        {
            'path': '/generate',
            'method': 'POST',
            'data': {
                'prompt': 'Hello',
                'model': 'peteollama:jamie-fixed'
            },
            'description': 'Generate endpoint'
        },
        
        # Test 5: RunPod style
        {
            'path': '/run',
            'method': 'POST',
            'data': {
                'input': {
                    'message': 'Hello',
                    'model': 'peteollama:jamie-fixed'
                }
            },
            'description': 'RunPod style input'
        },
        
        # Test 6: Different content type
        {
            'path': '/chat',
            'method': 'POST',
            'data': 'Hello',
            'headers': {'Content-Type': 'text/plain'},
            'description': 'Plain text input'
        },
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"🔍 Test {i}: {test_case['description']}")
        print(f"   Path: {test_case['path']}")
        print(f"   Method: {test_case['method']}")
        
        url = base_url + test_case['path']
        test_headers = headers.copy()
        
        # Use custom headers if specified
        if 'headers' in test_case:
            test_headers.update(test_case['headers'])
        
        try:
            if test_case['method'] == 'GET':
                response = requests.get(url, headers=test_headers, timeout=15)
            else:
                response = requests.post(url, headers=test_headers, json=test_case['data'], timeout=15)
            
            print(f"   📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ SUCCESS!")
                try:
                    data = response.json()
                    print(f"   📄 Response: {json.dumps(data, indent=4)[:300]}...")
                except:
                    print(f"   📄 Response: {response.text[:300]}...")
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
            elif response.status_code == 422:
                print("   ⚠️  Unprocessable Entity")
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
        
        print("   " + "-" * 50)
    
    print("\n📊 Summary:")
    print("   - Look for endpoints that return 200 OK")
    print("   - 400/422 errors might mean endpoint exists but format is wrong")
    print("   - Check the console to see which requests are actually reaching the endpoint")

if __name__ == "__main__":
    test_direct_endpoint()
