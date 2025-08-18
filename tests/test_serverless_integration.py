#!/usr/bin/env python3
"""
Test Serverless Integration
Verifies that the serverless handler can connect to RunPod endpoint
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_serverless_connection():
    """Test the serverless endpoint connection"""
    try:
        from src.serverless_handler import ServerlessHandler
        
        print("🧪 Testing serverless integration...")
        print(f"Endpoint: {os.getenv('RUNPOD_SERVERLESS_ENDPOINT')}")
        print(f"API Key: {'✅ Set' if os.getenv('RUNPOD_API_KEY') else '❌ Missing'}")
        
        async with ServerlessHandler() as handler:
            print("\n📡 Testing health check...")
            health = await handler.health_check()
            print(f"Health: {health}")
            
            print("\n🔥 Testing warmup...")
            warmup = await handler.warmup_endpoint()
            print(f"Warmup: {warmup}")
            
            print("\n💬 Testing chat...")
            chat = await handler.chat_completion("Hi Jamie, how are you?")
            print(f"Chat: {chat}")
            
            print("\n📊 Testing models...")
            models = await handler.get_models()
            print(f"Models: {models}")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_serverless_connection())
