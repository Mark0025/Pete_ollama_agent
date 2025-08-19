#!/usr/bin/env python3
"""
List All RunPod Serverless Endpoints
Shows all serverless endpoints in your RunPod account
"""

import os
import requests
import json

def list_runpod_endpoints():
    """List all RunPod serverless endpoints"""
    
    # Get API key from environment
    api_key = os.getenv('RUNPOD_API_KEY')
    if not api_key:
        print("❌ RUNPOD_API_KEY not set in environment")
        return None
    
    # RunPod AI API endpoint for listing serverless endpoints
    api_url = "https://api.runpod.ai/v2"
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        print("🔍 Listing all RunPod serverless endpoints...")
        print(f"🌐 API URL: {api_url}")
        print()
        
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            endpoints = data.get('data', [])
            
            if not endpoints:
                print("📭 No serverless endpoints found in your account")
                return []
            
            print(f"✅ Found {len(endpoints)} serverless endpoint(s):")
            print("=" * 60)
            
            for i, endpoint in enumerate(endpoints, 1):
                print(f"\n{i}. Endpoint Details:")
                print(f"   📋 ID: {endpoint.get('id', 'N/A')}")
                print(f"   🏷️  Name: {endpoint.get('name', 'N/A')}")
                print(f"   📊 Status: {endpoint.get('status', 'N/A')}")
                print(f"   🔧 Runtime: {endpoint.get('runtime', 'N/A')}")
                print(f"   🌍 Region: {endpoint.get('region', 'N/A')}")
                print(f"   💰 GPU Type: {endpoint.get('gpuTypeId', 'N/A')}")
                
                # Check if this matches your expected endpoint
                if endpoint.get('id') == 'vk7efas3wu5vd7':
                    print("   🎯 ← This matches your RUNPOD_SERVERLESS_ENDPOINT!")
                
                # Show recent errors if any
                if 'recentErrors' in endpoint and endpoint['recentErrors']:
                    print(f"   ❌ Recent Errors: {len(endpoint['recentErrors'])}")
                    for error in endpoint['recentErrors'][:2]:
                        print(f"      - {error}")
                
                print("   " + "-" * 40)
            
            return endpoints
            
        elif response.status_code == 401:
            print("❌ Unauthorized! Check your RUNPOD_API_KEY")
            return None
        else:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out")
        return None
    except requests.exceptions.ConnectionError:
        print("🔌 Connection error to RunPod API")
        return None
    except Exception as e:
        print(f"❌ Error listing endpoints: {str(e)}")
        return None

def main():
    """Main function"""
    print("🔍 RunPod Serverless Endpoints Lister")
    print("=" * 50)
    
    # Get API key from environment
    api_key = os.getenv('RUNPOD_API_KEY')
    if not api_key:
        print("❌ RUNPOD_API_KEY not set")
        print("Please set this environment variable")
        return
    
    print(f"📋 Environment:")
    print(f"   RUNPOD_API_KEY: {'✅ Set' if api_key else '❌ Not set'}")
    print(f"   Expected Endpoint: vk7efas3wu5vd7")
    print()
    
    # List all endpoints
    endpoints = list_runpod_endpoints()
    
    if endpoints is not None:
        if endpoints:
            print(f"\n📊 Summary:")
            print(f"   - Found {len(endpoints)} endpoint(s) in your account")
            print(f"   - Check if any match your expected endpoint ID")
            print(f"   - If none match, you may need to create a new endpoint")
        else:
            print(f"\n📊 Summary:")
            print(f"   - No endpoints found in your account")
            print(f"   - You may need to create a new serverless endpoint")
    else:
        print("\n❌ Could not retrieve endpoint list")
        print("Check your API key and try again")

if __name__ == "__main__":
    main()
