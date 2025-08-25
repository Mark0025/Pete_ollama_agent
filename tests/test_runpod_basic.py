#!/usr/bin/env python3
"""
Simple RunPod Serverless Test
Back to basics with the official Python client
"""

import runpod
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_runpod_basic():
    """Test RunPod serverless with official client"""
    print("🧪 Testing RunPod Serverless - Back to Basics")
    print("=" * 50)
    
    # Get API key and endpoint from environment
    api_key = os.getenv('RUNPOD_API_KEY')
    endpoint_id = os.getenv('RUNPOD_SERVERLESS_ENDPOINT')
    
    print(f"🔑 API Key: {api_key[:10]}..." if api_key else "❌ No API key found")
    print(f"📋 Endpoint ID: {endpoint_id}" if endpoint_id else "❌ No endpoint ID found")
    
    if not api_key or not endpoint_id:
        print("❌ Missing required environment variables")
        return
    
    try:
        # Set API key
        runpod.api_key = api_key
        print("✅ API key set")
        
        # Create endpoint instance
        endpoint = runpod.Endpoint(endpoint_id)
        print("✅ Endpoint instance created")
        
        # Test basic request
        print("\n🚀 Testing basic request...")
        run_request = endpoint.run_sync(
            {
                "prompt": "Hello, world!",
                "model": "llama3:latest",
                "max_tokens": 50
            },
            timeout=60
        )
        
        print("✅ Request successful!")
        print(f"📊 Response: {run_request}")
        
        # Test with different model
        print("\n🚀 Testing with llama3:latest...")
        run_request2 = endpoint.run_sync(
            {
                "prompt": "Say hello in Spanish",
                "model": "llama3:latest",
                "max_tokens": 50
            },
            timeout=60
        )
        
        print("✅ Second request successful!")
        print(f"📊 Response: {run_request2}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"📋 Error type: {type(e).__name__}")
        
        # Try to get more details about the error
        if hasattr(e, 'response'):
            print(f"📄 Response status: {e.response.status_code}")
            print(f"📄 Response text: {e.response.text}")

if __name__ == "__main__":
    test_runpod_basic()
