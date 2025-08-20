#!/usr/bin/env python3
"""
Main App Entry Point for Uvicorn
================================

This file provides the FastAPI app object that uvicorn needs.
"""

from vapi.modular_server import create_app

# Create the FastAPI app instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
