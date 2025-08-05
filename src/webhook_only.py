#!/usr/bin/env python3
"""
PeteOllama V1 - Webhook Server Only
===================================

Run only the VAPI webhook server (no GUI) for Docker container.
"""

import sys
import asyncio
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

from vapi.webhook_server import VAPIWebhookServer
from utils.logger import logger

async def main():
    """Main webhook server entry point"""
    logger.info("🏠 PeteOllama V1 - AI Property Manager (Webhook Server)")
    logger.info("📱 Training data: Real phone conversations")
    logger.info("🤖 Model: Qwen 2.5 7B (Custom trained)")
    logger.info("🎤 Voice: VAPI Integration")
    logger.info("")
    
    # Start webhook server
    server = VAPIWebhookServer()
    logger.info("🌐 Starting VAPI webhook server...")
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())