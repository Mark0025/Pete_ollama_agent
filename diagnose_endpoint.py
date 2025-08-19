#!/usr/bin/env python3
"""
RunPod Endpoint Diagnostic Tool
Helps troubleshoot connectivity issues with RunPod serverless endpoints
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from serverless_handler import ServerlessHandler
except ImportError:
    print("❌ Could not import serverless_handler. Please ensure you're running from the project root.")
    sys.exit(1)

from loguru import logger

async def diagnose_endpoint():
    """Run comprehensive endpoint diagnostics"""
    print("🔍 RunPod Endpoint Diagnostic Tool")
    print("=" * 50)
    
    # Check environment variables
    endpoint_id = os.getenv('RUNPOD_SERVERLESS_ENDPOINT')
    api_key = os.getenv('RUNPOD_API_KEY')
    
    print(f"📋 Environment Check:")
    print(f"   RUNPOD_SERVERLESS_ENDPOINT: {endpoint_id or '❌ Not set'}")
    print(f"   RUNPOD_API_KEY: {'✅ Set' if api_key else '❌ Not set'}")
    print()
    
    if not endpoint_id or not api_key:
        print("❌ Missing required environment variables!")
        print("Please set RUNPOD_SERVERLESS_ENDPOINT and RUNPOD_API_KEY")
        return False
    
    try:
        async with ServerlessHandler() as handler:
            print(f"🔗 Endpoint URL: {handler.base_url}")
            print()
            
            # Run accessibility diagnostics
            print("🌐 Running connectivity diagnostics...")
            diagnostics = await handler.check_endpoint_accessibility()
            
            print("📊 Diagnostic Results:")
            for key, value in diagnostics.items():
                if key != "timestamp":
                    print(f"   {key.replace('_', ' ').title()}: {value}")
            print()
            
            # Test health check
            print("🏥 Testing health check...")
            health = await handler.health_check()
            if health and health.get('status') != 'error':
                print("✅ Health check passed")
            else:
                print("❌ Health check failed")
                if health:
                    print(f"   Response: {health}")
            print()
            
            # Test warmup
            print("🔥 Testing endpoint warmup...")
            warmup_result = await handler.warmup_endpoint()
            if warmup_result:
                print("✅ Endpoint warmup successful")
            else:
                print("❌ Endpoint warmup failed")
            print()
            
            # Test simple chat
            print("💬 Testing chat functionality...")
            chat_response = await handler.chat_completion("Hello, this is a test message")
            if chat_response and chat_response.get('status') != 'error':
                print("✅ Chat test passed")
                print(f"   Response length: {len(str(chat_response))} characters")
            else:
                print("❌ Chat test failed")
                if chat_response:
                    print(f"   Error: {chat_response}")
            
            return True
            
    except Exception as e:
        print(f"❌ Diagnostic failed: {str(e)}")
        return False

def main():
    """Main entry point"""
    try:
        success = asyncio.run(diagnose_endpoint())
        if success:
            print("\n✅ Diagnostics completed successfully")
        else:
            print("\n❌ Diagnostics failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️ Diagnostics interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
