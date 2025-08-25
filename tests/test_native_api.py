#!/usr/bin/env python3
"""
Test RunPod Native API
Test if the endpoint supports the native RunPod API instead of OpenAI
"""

import os
import requests
import json

def test_native_api():
    """Test the native RunPod API endpoints"""
    
    # Get API key from environment
    api_key = os.getenv('RUNPOD_API_KEY')
    endpoint_id = os.getenv('RUNPOD_SERVERLESS_ENDPOINT')
    
    if not api_key:
        print("❌ RUNPOD_API_KEY not set")
        return
    
    if not endpoint_id:
        print("❌ RUNPOD_SERVERLESS_ENDPOINT not set")
        return
    
    print("🔍 Testing RunPod Native API")
    print("=" * 50)
    print(f"📋 Endpoint ID: {endpoint_id}")
    print(f"🔑 API Key: {'✅ Set' if api_key else '❌ Not set'}")
    print()
    
    # Test different API structures
    api_endpoints = [
        # Native RunPod API
        (f"https://api.runpod.ai/v2/{endpoint_id}", "Native API base"),
        (f"https://api.runpod.ai/v2/{endpoint_id}/run", "Native API run"),
        (f"https://api.runpod.ai/v2/{endpoint_id}/status", "Native API status"),
        
        # Alternative OpenAI paths
        (f"https://api.runpod.ai/v2/{endpoint_id}/v1", "OpenAI v1 base"),
        (f"https://api.runpod.ai/v2/{endpoint_id}/api", "API base"),
        
        # Health check
        (f"https://api.runpod.ai/v2/{endpoint_id}/health", "Health check"),
    ]
    
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    for url, description in api_endpoints:
        print(f"🔍 Testing: {description}")
        print(f"   URL: {url}")
        
        try:
            if 'run' in url:
                # Test POST for run endpoint
                test_data = {
                    'input': {
                        'prompt': 'Hello, test message',
                        'max_tokens': 10
                    }
                }
                response = requests.post(url, headers=headers, json=test_data, timeout=15)
            else:
                # Test GET for other endpoints
                response = requests.get(url, headers=headers, timeout=15)
            
            print(f"   📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ SUCCESS!")
                try:
                    data = response.json()
                    print(f"   📄 Response: {json.dumps(data, indent=4)[:300]}...")
                except Exception as e:
                    print(f"   📄 Response parsing error: {e}")
                    print(f"   📄 Raw response: {response.text[:300]}...")
                    
            elif response.status_code == 404:
                print("   ❌ Not Found")
            elif response.status_code == 405:
                print("   ⚠️  Method Not Allowed")
            elif response.status_code == 500:
                print("   ❌ Internal Server Error")
                try:
                    data = response.json()
                    error_msg = data.get('error', 'Unknown error')
                    print(f"   📄 Error: {error_msg}")
                except Exception as e:
                    print(f"   📄 Error parsing: {e}")
                    print(f"   📄 Raw error: {response.text[:200]}...")
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
    print("   - If native API works, we can use that instead of OpenAI")
    print("   - Check your RunPod console for endpoint configuration issues")

if __name__ == "__main__":
    test_native_api()
