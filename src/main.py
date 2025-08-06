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

# Ensure src directory is on the import path when executed from project root
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import logger
from vapi.webhook_server import VAPIWebhookServer


def main() -> None:
    """Entry point for starting the FastAPI server."""
    port = int(os.getenv("PORT", "8000"))
    logger.info(f"🚀 Starting PeteOllama API server on port {port}")

    server = VAPIWebhookServer(port=port)
    uvicorn.run(server.app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
