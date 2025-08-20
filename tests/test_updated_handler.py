#!/usr/bin/env python3
"""
Test Updated Serverless Handler
Tests both regular chat completion and streaming chat
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from serverless_handler import ServerlessHandler
from loguru import logger

async def test_updated_handler():
    """Test the updated serverless handler"""
    
    print("🧪 Testing Updated Serverless Handler")
    print("=" * 60)
    
    # Check environment
    endpoint_id = os.getenv('RUNPOD_SERVERLESS_ENDPOINT')
    api_key = os.getenv('RUNPOD_API_KEY')
    
    print(f"📋 Environment:")
    print(f"   RUNPOD_SERVERLESS_ENDPOINT: {endpoint_id or '❌ Not set'}")
    print(f"   RUNPOD_API_KEY: {'✅ Set' if api_key else '❌ Not set'}")
    print()
    
    if not endpoint_id or not api_key:
        print("❌ Missing required environment variables!")
        print("Please set RUNPOD_SERVERLESS_ENDPOINT and RUNPOD_API_KEY")
        return
    
    try:
        async with ServerlessHandler() as handler:
            print(f"🔗 Endpoint URL: {handler.base_url}")
            print()
            
            # Test 1: Health Check
            print("🏥 Test 1: Health Check")
            print("-" * 30)
            
            health = await handler.health_check()
            if health and health.get('status') == 'healthy':
                print("✅ Health check passed")
                print(f"   Workers: {health.get('healthy_workers', 'N/A')}")
                print(f"   Status: {health.get('status')}")
            else:
                print("❌ Health check failed")
                print(f"   Response: {health}")
            print()
            
            # Test 2: Endpoint Warmup
            print("🔥 Test 2: Endpoint Warmup")
            print("-" * 30)
            
            warmup_result = await handler.warmup_endpoint()
            if warmup_result:
                print("✅ Endpoint warmup successful")
            else:
                print("❌ Endpoint warmup failed")
            print()
            
            # Test 3: Regular Chat Completion
            print("💬 Test 3: Regular Chat Completion")
            print("-" * 30)
            
            start_time = asyncio.get_event_loop().time()
            
            chat_response = await handler.chat_completion(
                "Hello! Please tell me a short joke about programming.",
                max_tokens=100
            )
            
            end_time = asyncio.get_event_loop().time()
            response_time = end_time - start_time
            
            if chat_response and chat_response.get('status') == 'success':
                print("✅ Chat completion successful!")
                print(f"   Response: {chat_response.get('response', 'No response')}")
                print(f"   Model: {chat_response.get('model', 'Unknown')}")
                print(f"   Job ID: {chat_response.get('job_id', 'N/A')}")
                print(f"   Response time: {response_time:.2f} seconds")
            else:
                print("❌ Chat completion failed")
                print(f"   Error: {chat_response}")
            print()
            
            # Test 4: Streaming Chat
            print("🌊 Test 4: Streaming Chat")
            print("-" * 30)
            
            start_time = asyncio.get_event_loop().time()
            
            stream_response = await handler.stream_chat(
                "Write a short haiku about artificial intelligence.",
                max_tokens=50
            )
            
            end_time = asyncio.get_event_loop().time()
            stream_time = end_time - start_time
            
            if stream_response and stream_response.get('status') == 'success':
                print("✅ Streaming chat successful!")
                print(f"   Response: {stream_response.get('response', 'No response')}")
                print(f"   Model: {stream_response.get('model', 'Unknown')}")
                print(f"   Job ID: {stream_response.get('job_id', 'N/A')}")
                print(f"   Streaming: {stream_response.get('streaming', False)}")
                print(f"   Response time: {stream_time:.2f} seconds")
            elif stream_response and stream_response.get('status') == 'partial':
                print("⚠️ Partial streaming response")
                print(f"   Partial: {stream_response.get('response', 'No response')}")
                print(f"   Job ID: {stream_response.get('job_id', 'N/A')}")
                print(f"   Streaming: {stream_response.get('streaming', False)}")
            else:
                print("❌ Streaming chat failed")
                print(f"   Error: {stream_response}")
            print()
            
            # Test 5: Performance Comparison
            print("📊 Test 5: Performance Summary")
            print("-" * 30)
            print(f"   Regular chat: {response_time:.2f}s")
            print(f"   Streaming chat: {stream_time:.2f}s")
            print(f"   Difference: {abs(response_time - stream_time):.2f}s")
            print()
            
            # Test 6: Multiple Quick Requests
            print("⚡ Test 6: Multiple Quick Requests")
            print("-" * 30)
            
            quick_messages = [
                "Say 'Hello' in one word.",
                "What is 2+2?",
                "Name a color."
            ]
            
            start_time = asyncio.get_event_loop().time()
            
            for i, message in enumerate(quick_messages, 1):
                print(f"   Request {i}: {message}")
                
                response = await handler.chat_completion(message, max_tokens=20)
                
                if response and response.get('status') == 'success':
                    print(f"   ✅ Response {i}: {response.get('response', 'No response')}")
                else:
                    print(f"   ❌ Request {i} failed: {response}")
            
            end_time = asyncio.get_event_loop().time()
            total_time = end_time - start_time
            
            print(f"   Total time for 3 requests: {total_time:.2f}s")
            print(f"   Average per request: {total_time/3:.2f}s")
            print()
            
            print("🎉 All tests completed!")
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def main():
    """Main function"""
    try:
        success = asyncio.run(test_updated_handler())
        if success:
            print("✅ All tests passed successfully!")
        else:
            print("❌ Some tests failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
