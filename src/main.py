#!/usr/bin/env python3
"""
PeteOllama V1 - API Server (Headless)
-------------------------------------

Run-only FastAPI server suitable for RunPod or any headless deployment.
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


def main() -> None:
    """Entry point for starting the FastAPI server."""
    port = int(os.getenv("PORT", "8000"))
    proxy_port = int(os.getenv("PROXY_PORT", "8001"))
    
    logger.info(f"🚀 Starting PeteOllama API server on port {port}")
    logger.info(f"🔗 Starting Ollama proxy on port {proxy_port} for VAPI integration")

    # Start the Ollama proxy in the background
    proxy_process = subprocess.Popen([
        sys.executable, "src/ollama_proxy.py"
    ])
    
    logger.info(f"✅ Ollama proxy started (PID: {proxy_process.pid})")
    
    # Start the main webhook server
    server = VAPIWebhookServer(port=port)
    uvicorn.run(server.app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
