#!/usr/bin/env python3
"""
Frontend Server for PeteOllama
Serves the decoupled frontend files for testing
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def create_frontend_server():
    """Create a FastAPI server for the frontend"""
    
    app = FastAPI(title="PeteOllama Frontend", version="1.0.0")
    
    # Get the frontend directory
    frontend_dir = Path(__file__).parent
    
    # Mount static files
    app.mount("/css", StaticFiles(directory=str(frontend_dir / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(frontend_dir / "js")), name="js")
    
    # Serve HTML files
    @app.get("/", response_class=HTMLResponse)
    async def root():
        """Serve the main index"""
        index_path = frontend_dir / "index.html"
        if index_path.exists():
            with open(index_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            raise HTTPException(status_code=404, detail="Index not found")
    
    @app.get("/main-ui", response_class=HTMLResponse)
    async def main_ui():
        """Serve the main UI"""
        ui_path = frontend_dir / "html" / "main-ui.html"
        if ui_path.exists():
            with open(ui_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            raise HTTPException(status_code=404, detail="Main UI not found")
    
    @app.get("/admin-ui", response_class=HTMLResponse)
    async def admin_ui():
        """Serve the admin UI"""
        admin_path = frontend_dir / "html" / "admin-ui.html"
        if admin_path.exists():
            with open(admin_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            raise HTTPException(status_code=404, detail="Admin UI not found")
    
    @app.get("/health")
    async def health():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "frontend_dir": str(frontend_dir),
            "available_files": {
                "index": (frontend_dir / "index.html").exists(),
                "main_ui": (frontend_dir / "html" / "main-ui.html").exists(),
                "admin_ui": (frontend_dir / "html" / "admin-ui.html").exists(),
                "css_files": len(list((frontend_dir / "css").glob("*.css"))),
                "js_files": len(list((frontend_dir / "js").glob("*.js")))
            }
        }
    
    return app

def main():
    """Main function"""
    print("🧪 Creating PeteOllama Frontend Server...")
    
    app = create_frontend_server()
    
    print("✅ Frontend server created successfully")
    print("🔗 Available routes:")
    print("   / - Main index")
    print("   /main-ui - Main UI")
    print("   /admin-ui - Admin UI")
    print("   /health - Health check")
    print("   /css/* - CSS files")
    print("   /js/* - JavaScript files")
    
    print("\n🚀 Starting frontend server on port 8006...")
    print("📱 Test these URLs:")
    print("   http://localhost:8006/")
    print("   http://localhost:8006/main-ui")
    print("   http://localhost:8006/admin-ui")
    print("   http://localhost:8006/health")
    
    uvicorn.run(app, host="0.0.0.0", port=8006, log_level="info")

if __name__ == "__main__":
    main()
