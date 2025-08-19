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

from vapi.modular_server import ModularVAPIServer
from utils.logger import logger

def main():
    """Main webhook server entry point"""
    logger.info("🏠 PeteOllama V1 - AI Property Manager (Modular Webhook Server)")
    logger.info("📱 Training data: Real phone conversations")
    logger.info("🤖 Model: Qwen 2.5 7B (Custom trained)")
    logger.info("🎤 Voice: VAPI Integration")
    logger.info("")
    
    # Start modular webhook server
    server = ModularVAPIServer()
    logger.info("🌐 Starting modular VAPI webhook server...")
    server.run(host="0.0.0.0", port=8000, debug=False)

if __name__ == "__main__":
    main()
