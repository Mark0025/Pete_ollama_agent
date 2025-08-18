#!/usr/bin/env python3
"""
PeteOllama V1 - API Server (Serverless-First)
---------------------------------------------

FastAPI server that routes all requests to RunPod serverless endpoint.
"""

import os
import sys
from pathlib import Path
import uvicorn
import asyncio
import subprocess

# Ensure src directory is on the import path when executed from project root
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import logger
from vapi.webhook_server import VAPIWebhookServer
from startup_warmup import run_warmup


def main() -> None:
    """Entry point for starting the FastAPI server."""
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"🚀 Starting PeteOllama API server on port {port}")
    logger.info("🔥 Warming up RunPod serverless endpoint...")
    
    # Warm up the serverless endpoint on startup
    warmup_success = run_warmup()
    if warmup_success:
        logger.info("✅ Serverless endpoint warmed up successfully")
    else:
        logger.warning("⚠️ Serverless endpoint warmup failed - continuing anyway")
    
    logger.info("🔗 Starting VAPI webhook server with serverless backend")
    
    # Start the main webhook server (now serverless-first)
    server = VAPIWebhookServer(port=port)
    uvicorn.run(server.app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
