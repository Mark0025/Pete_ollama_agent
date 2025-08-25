#!/usr/bin/env python3
"""
Simple Test Server
Test basic route registration without complex dependencies
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def create_simple_server():
    """Create a simple FastAPI server with basic routes"""
    
    app = FastAPI(title="Simple Test Server")
    
    @app.get("/")
    async def root():
        return {"message": "Simple test server running"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    @app.get("/ui", response_class=HTMLResponse)
    async def ui():
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Test UI</title></head>
        <body>
            <h1>Test UI Route</h1>
            <p>If you can see this, the UI route is working!</p>
        </body>
        </html>
        """
    
    @app.get("/test")
    async def test():
        return {"message": "Test route working"}
    
    return app

def main():
    """Main function"""
    print("🧪 Creating simple test server...")
    
    app = create_simple_server()
    
    print("✅ Server created successfully")
    print("🔗 Routes registered:")
    for route in app.routes:
        if hasattr(route, 'path'):
            print(f"   {route.methods} {route.path}")
    
    print("\n🚀 Starting server on port 8001...")
    print("📱 Test these URLs:")
    print("   http://localhost:8001/")
    print("   http://localhost:8001/health")
    print("   http://localhost:8001/ui")
    print("   http://localhost:8001/test")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")

if __name__ == "__main__":
    main()
