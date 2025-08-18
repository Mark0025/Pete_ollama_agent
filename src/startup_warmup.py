#!/usr/bin/env python3
"""
PeteOllama V1 - Startup Warmup
Warms up the RunPod serverless endpoint on app startup
"""

import asyncio
import os
from loguru import logger
from serverless_handler import ServerlessHandler

async def warmup_serverless_endpoint():
    """Warm up the serverless endpoint on startup"""
    try:
        logger.info("🚀 Starting serverless endpoint warmup...")
        
        async with ServerlessHandler() as handler:
            # Check if endpoint is accessible
            health = await handler.health_check()
            if health and health.get('status') != 'error':
                logger.info("✅ Serverless endpoint is accessible")
                
                # Warm up with a simple request
                warmup_result = await handler.warmup_endpoint()
                if warmup_result:
                    logger.info("🔥 Serverless endpoint warmed up successfully")
                    return True
                else:
                    logger.warning("⚠️ Serverless endpoint warmup failed")
                    return False
            else:
                logger.error("❌ Serverless endpoint health check failed")
                return False
                
    except Exception as e:
        logger.error(f"❌ Startup warmup failed: {str(e)}")
        return False

def run_warmup():
    """Run the warmup synchronously"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(warmup_serverless_endpoint())
        loop.close()
        return result
    except Exception as e:
        logger.error(f"❌ Warmup execution failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Test warmup
    success = run_warmup()
    if success:
        print("✅ Serverless endpoint warmup successful")
    else:
        print("❌ Serverless endpoint warmup failed")
