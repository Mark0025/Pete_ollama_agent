#!/usr/bin/env python3
"""
RunPod Endpoint Status Checker
Uses RunPod API to check the status of your serverless endpoint
"""

import os
import requests
import json
from datetime import datetime

def check_runpod_endpoint(endpoint_id):
    """Check RunPod endpoint status using the API"""
    
    # Get API key from environment
    api_key = os.getenv('RUNPOD_API_KEY')
    if not api_key:
        print("❌ RUNPOD_API_KEY not set in environment")
        return None
    
    # RunPod AI API endpoint for serverless endpoints
    api_url = f"https://api.runpod.ai/v2/{endpoint_id}"
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"🔍 Checking RunPod endpoint: {endpoint_id}")
        print(f"🌐 API URL: {api_url}")
        print()
        
        response = requests.get(api_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Endpoint found! Here's the status:")
            print("=" * 50)
            
            # Display key information
            print(f"📋 Endpoint ID: {data.get('id', 'N/A')}")
            print(f"🏷️  Name: {data.get('name', 'N/A')}")
            print(f"📊 Status: {data.get('status', 'N/A')}")
            print(f"🔧 Runtime: {data.get('runtime', 'N/A')}")
            print(f"🌍 Region: {data.get('region', 'N/A')}")
            print(f"💰 GPU Type: {data.get('gpuTypeId', 'N/A')}")
            print(f"📈 Scale: {data.get('scale', 'N/A')}")
            
            # Check if there are any recent errors
            if 'recentErrors' in data and data['recentErrors']:
                print(f"\n❌ Recent Errors: {len(data['recentErrors'])}")
                for error in data['recentErrors'][:3]:  # Show last 3 errors
                    print(f"   - {error}")
            
            # Check network info
            if 'networkVolumeId' in data:
                print(f"💾 Network Volume: {data['networkVolumeId']}")
            
            # Check scaling info
            if 'scaling' in data:
                scaling = data['scaling']
                print(f"📊 Scaling: Min={scaling.get('min', 'N/A')}, Max={scaling.get('max', 'N/A')}")
            
            # Check if endpoint is accessible
            if data.get('status') == 'RUNNING':
                print("\n✅ Endpoint appears to be RUNNING")
                print("🔍 Testing connectivity...")
                
                # Test the actual endpoint URL
                endpoint_url = f"https://{endpoint_id}.runpod.net"
                try:
                    health_response = requests.get(f"{endpoint_url}/health", timeout=10)
                    print(f"✅ Health check: HTTP {health_response.status_code}")
                except requests.exceptions.Timeout:
                    print("⏰ Health check: Timeout")
                except requests.exceptions.ConnectionError:
                    print("🔌 Health check: Connection refused")
                except Exception as e:
                    print(f"❌ Health check: {str(e)}")
            else:
                print(f"\n⚠️ Endpoint status: {data.get('status')}")
                print("This might explain the connectivity issues!")
            
            return data
            
        elif response.status_code == 404:
            print(f"❌ Endpoint {endpoint_id} not found!")
            print("Check if the endpoint ID is correct or if it was deleted.")
            return None
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
        print(f"❌ Error checking endpoint: {str(e)}")
        return None

def main():
    """Main function"""
    print("🔍 RunPod Endpoint Status Checker")
    print("=" * 50)
    
    # Get endpoint ID from environment
    endpoint_id = os.getenv('RUNPOD_SERVERLESS_ENDPOINT')
    if not endpoint_id:
        print("❌ RUNPOD_SERVERLESS_ENDPOINT not set")
        print("Please set this environment variable with your endpoint ID")
        return
    
    print(f"📋 Environment:")
    print(f"   RUNPOD_SERVERLESS_ENDPOINT: {endpoint_id}")
    print(f"   RUNPOD_API_KEY: {'✅ Set' if os.getenv('RUNPOD_API_KEY') else '❌ Not set'}")
    print()
    
    # Check the endpoint
    result = check_runpod_endpoint(endpoint_id)
    
    if result:
        print("\n📊 Summary:")
        print("   - If status is not 'RUNNING', that explains the connectivity issues")
        print("   - Check the RunPod console for more details")
        print("   - You may need to restart or recreate the endpoint")
    else:
        print("\n❌ Could not retrieve endpoint information")
        print("Check your API key and endpoint ID")

if __name__ == "__main__":
    main()
