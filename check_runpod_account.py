#!/usr/bin/env python3
"""
RunPod Account Status Checker
Checks your RunPod account and tries different API endpoints
"""

import os
import requests
import json

def check_runpod_account():
    """Check RunPod account status and available endpoints"""
    
    # Get API key from environment
    api_key = os.getenv('RUNPOD_API_KEY')
    if not api_key:
        print("❌ RUNPOD_API_KEY not set in environment")
        return None
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    print("🔍 Checking RunPod account status...")
    print("=" * 50)
    
    # Try different API endpoints to see what's available
    endpoints_to_try = [
        ("Account Info", "https://api.runpod.ai/v2/user"),
        ("Pods", "https://api.runpod.ai/v2/pod"),
        ("Serverless Endpoints", "https://api.runpod.ai/v2"),
        ("Jobs", "https://api.runpod.ai/v2/job"),
        ("Storage", "https://api.runpod.ai/v2/storage"),
    ]
    
    results = {}
    
    for name, url in endpoints_to_try:
        try:
            print(f"\n🔍 Testing: {name}")
            print(f"   URL: {url}")
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Status: 200 OK")
                
                # Show some key info based on endpoint type
                if "user" in url:
                    user_data = data.get('data', {})
                    print(f"   👤 User: {user_data.get('name', 'N/A')}")
                    print(f"   📧 Email: {user_data.get('email', 'N/A')}")
                    print(f"   💰 Credits: {user_data.get('credits', 'N/A')}")
                
                elif "pod" in url:
                    pods = data.get('data', [])
                    print(f"   🖥️  Pods: {len(pods)} found")
                    for pod in pods[:3]:  # Show first 3
                        print(f"      - {pod.get('id', 'N/A')}: {pod.get('desiredStatus', 'N/A')}")
                
                elif "serverless" in url:
                    endpoints = data.get('data', [])
                    print(f"   🚀 Serverless: {len(endpoints)} found")
                    for endpoint in endpoints[:3]:  # Show first 3
                        print(f"      - {endpoint.get('id', 'N/A')}: {endpoint.get('status', 'N/A')}")
                
                results[name] = {"status": 200, "data": data}
                
            elif response.status_code == 404:
                print(f"   ❌ Status: 404 Not Found")
                results[name] = {"status": 404, "data": None}
                
            elif response.status_code == 401:
                print(f"   ❌ Status: 401 Unauthorized")
                results[name] = {"status": 401, "data": None}
                break  # Stop if unauthorized
                
            else:
                print(f"   ⚠️  Status: {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                results[name] = {"status": response.status_code, "data": None}
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout")
            results[name] = {"status": "timeout", "data": None}
        except requests.exceptions.ConnectionError:
            print(f"   🔌 Connection Error")
            results[name] = {"status": "connection_error", "data": None}
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            results[name] = {"status": "error", "data": None}
    
    return results

def main():
    """Main function"""
    print("🔍 RunPod Account Status Checker")
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
    
    # Check account
    results = check_runpod_account()
    
    if results:
        print(f"\n📊 Summary:")
        print(f"   - Check which endpoints are accessible")
        print(f"   - Look for your endpoint ID in the results")
        print(f"   - If serverless endpoints return 404, they may not exist")
        
        # Check if we found any serverless endpoints
        serverless_results = [k for k, v in results.items() if "serverless" in k.lower() and v["status"] == 200]
        if serverless_results:
            print(f"   - Found accessible serverless endpoints: {', '.join(serverless_results)}")
        else:
            print(f"   - No accessible serverless endpoints found")
            print(f"   - You may need to create a new serverless endpoint")
    else:
        print("\n❌ Could not check account status")
        print("Check your API key and try again")

if __name__ == "__main__":
    main()
