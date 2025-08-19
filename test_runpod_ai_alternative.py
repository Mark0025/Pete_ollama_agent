#!/usr/bin/env python3
"""
Test Alternative RunPod AI API Structures
Tries different API formats to find the correct endpoint
"""

import os
import requests
import json

def test_alternative_apis():
    """Test alternative RunPod AI API structures"""
    
    # Get API key from environment
    api_key = os.getenv('RUNPOD_API_KEY')
    endpoint_id = os.getenv('RUNPOD_SERVERLESS_ENDPOINT')
    
    if not api_key:
        print("❌ RUNPOD_API_KEY not set")
        return
    
    if not endpoint_id:
        print("❌ RUNPOD_SERVERLESS_ENDPOINT not set")
        return
    
    print("🔍 Testing Alternative RunPod AI API Structures")
    print("=" * 60)
    print(f"📋 Endpoint ID: {endpoint_id}")
    print(f"🔑 API Key: {'✅ Set' if api_key else '❌ Not set'}")
    print()
    
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    # Test different API structures
    api_structures = [
        # Structure 1: Direct endpoint
        (f"https://api.runpod.ai/v2/{endpoint_id}", "Direct endpoint"),
        
        # Structure 2: Serverless endpoint format
        (f"https://api.runpod.ai/v2/serverless/endpoint/{endpoint_id}", "Serverless endpoint"),
        
        # Structure 3: Old RunPod format with .ai domain
        (f"https://{endpoint_id}.runpod.ai", "Old format with .ai domain"),
        
        # Structure 4: API with different version
        (f"https://api.runpod.ai/v1/{endpoint_id}", "API v1"),
        
        # Structure 5: Different base path
        (f"https://api.runpod.ai/serverless/{endpoint_id}", "Serverless base path"),
        
        # Structure 6: Check if endpoint exists in list
        ("https://api.runpod.ai/v2/serverless/endpoint", "List endpoints"),
    ]
    
    for url, description in api_structures:
        print(f"🔍 Testing: {description}")
        print(f"   URL: {url}")
        
        try:
            if "List endpoints" in description:
                # This is a GET request to list endpoints
                response = requests.get(url, headers=headers, timeout=15)
            else:
                # Test health endpoint on each structure
                health_url = f"{url}/health"
                response = requests.get(health_url, headers=headers, timeout=15)
            
            print(f"   📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ SUCCESS!")
                try:
                    data = response.json()
                    if "List endpoints" in description:
                        print(f"   📄 Found endpoints: {len(data.get('data', []))}")
                        endpoints = data.get('data', [])
                        for ep in endpoints[:3]:
                            print(f"      - {ep.get('id', 'N/A')}: {ep.get('status', 'N/A')}")
                    else:
                        print(f"   📄 Response: {json.dumps(data, indent=4)[:200]}...")
                except:
                    print(f"   📄 Response: {response.text[:200]}...")
            elif response.status_code == 404:
                print("   ❌ Not Found")
            elif response.status_code == 401:
                print("   ❌ Unauthorized")
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
    print("   - If 'List endpoints' works, we can see what endpoints exist")
    print("   - The working structure will show us the correct format")

if __name__ == "__main__":
    test_alternative_apis()
