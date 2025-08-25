#!/usr/bin/env python3
"""
Test RunPod AI Health Endpoint
Tests the exact API format shown by the user
"""

import os
import requests

def test_runpod_ai_health():
    """Test RunPod AI health endpoint"""
    
    # Get API key from environment
    api_key = os.getenv('RUNPOD_API_KEY')
    endpoint_id = os.getenv('RUNPOD_SERVERLESS_ENDPOINT')
    
    if not api_key:
        print("❌ RUNPOD_API_KEY not set")
        return
    
    if not endpoint_id:
        print("❌ RUNPOD_SERVERLESS_ENDPOINT not set")
        return
    
    print("🔍 Testing RunPod AI Health Endpoint")
    print("=" * 50)
    print(f"📋 Endpoint ID: {endpoint_id}")
    print(f"🔑 API Key: {'✅ Set' if api_key else '❌ Not set'}")
    print()
    
    # Test the exact format from the user's example
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    health_url = f'https://api.runpod.ai/v2/{endpoint_id}/health'
    print(f"🌐 Testing: {health_url}")
    print()
    
    try:
        response = requests.get(health_url, headers=headers, timeout=30)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        print()
        
        if response.status_code == 200:
            print("✅ Health check successful!")
            try:
                data = response.json()
                print(f"📄 Response Data: {json.dumps(data, indent=2)}")
            except:
                print(f"📄 Response Text: {response.text}")
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out")
    except requests.exceptions.ConnectionError as e:
        print(f"🔌 Connection error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Also test the base endpoint
    print(f"\n🔍 Testing base endpoint...")
    base_url = f'https://api.runpod.ai/v2/{endpoint_id}'
    print(f"🌐 Base URL: {base_url}")
    
    try:
        response = requests.get(base_url, headers=headers, timeout=30)
        print(f"📊 Base Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Base endpoint accessible!")
            try:
                data = response.json()
                print(f"📄 Base Response: {json.dumps(data, indent=2)}")
            except:
                print(f"📄 Base Response Text: {response.text}")
        else:
            print(f"❌ Base endpoint failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Base endpoint error: {e}")

if __name__ == "__main__":
    import json
    test_runpod_ai_health()
