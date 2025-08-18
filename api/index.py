#!/usr/bin/env python3
"""
PeteOllama V1 - Vercel Serverless Entry Point (Lightweight)
RunPod serverless backend with graceful fallbacks
"""

import os
import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    from vapi.webhook_server import VAPIWebhookServer
    
    # Create the server instance
    server = VAPIWebhookServer(port=int(os.getenv("PORT", "8000")))
    
    # Export the FastAPI app for Vercel
    app = server.app
    
except Exception as e:
    # Fallback minimal FastAPI app for debugging
    from fastapi import FastAPI
    
    app = FastAPI(title="PeteOllama V1 - Lightweight", version="1.0")
    
    @app.get("/")
    async def root():
        return {
            "service": "PeteOllama V1 - Lightweight", 
            "status": "fallback_mode",
            "message": "Running on Vercel with lightweight requirements", 
            "error": str(e)
        }
    
    @app.get("/health")
    async def health():
        return {
            "status": "ok", 
            "service": "peteollama-lightweight",
            "deployment": "vercel",
            "mode": "fallback"
        }
