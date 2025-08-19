#!/usr/bin/env python3
"""
PeteOllama V1 - API Server (Serverless-First)
---------------------------------------------

FastAPI server that routes all requests to RunPod serverless endpoint.
"""

import os
import sys
import signal
import atexit
from pathlib import Path
import uvicorn
import asyncio
import subprocess

# Ensure src directory is on the import path when executed from project root
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import logger
from vapi.modular_server import ModularVAPIServer
from startup_warmup import run_warmup


def cleanup_resources():
    """Clean up resources on shutdown"""
    try:
        logger.info("🧹 Cleaning up resources...")
        
        # Clean up model preloader
        try:
            from ai.model_preloader import model_preloader
            model_preloader.shutdown()
        except Exception as e:
            logger.warning(f"⚠️ Model preloader cleanup warning: {e}")
        
        # Clean up any remaining asyncio tasks
        try:
            loop = asyncio.get_event_loop()
            if loop and not loop.is_closed():
                tasks = [task for task in asyncio.all_tasks(loop) if not task.done()]
                if tasks:
                    logger.info(f"🔄 Cancelling {len(tasks)} pending tasks...")
                    for task in tasks:
                        task.cancel()
                    
                    # Wait briefly for tasks to cancel
                    try:
                        loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
                    except Exception:
                        pass  # Ignore exceptions during cleanup
        except RuntimeError:
            pass  # No event loop running
        
        logger.info("✅ Resource cleanup completed")
    except Exception as e:
        logger.warning(f"⚠️ Resource cleanup warning: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"📡 Received signal {signum}, shutting down gracefully...")
    cleanup_resources()
    sys.exit(0)

def main() -> None:
    """Entry point for starting the FastAPI server."""
    port = int(os.getenv("PORT", "8000"))
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup_resources)
    
    logger.info(f"🚀 Starting PeteOllama API server on port {port}")
    
    # Start warmup in background - don't block server startup
    logger.info("🔥 Starting RunPod warmup in background...")
    import threading
    def background_warmup():
        try:
            warmup_success = run_warmup()
            if warmup_success:
                logger.info("✅ Background serverless endpoint warmup completed successfully")
            else:
                logger.warning("⚠️ Background serverless endpoint warmup failed")
        except Exception as e:
            logger.warning(f"⚠️ Background warmup exception: {e}")
    
    # Start warmup thread
    warmup_thread = threading.Thread(target=background_warmup, daemon=True)
    warmup_thread.start()
    
    logger.info("🔗 Starting VAPI webhook server with serverless backend")
    
    try:
        # Start the modular webhook server (now serverless-first)
        server = ModularVAPIServer()
        server.run(host="0.0.0.0", port=port, debug=False)
    except KeyboardInterrupt:
        logger.info("🛑 Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
    finally:
        cleanup_resources()


if __name__ == "__main__":
    main()
