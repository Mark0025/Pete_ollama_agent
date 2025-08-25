#!/usr/bin/env python3
"""
Modular VAPI Server
==================

Refactored webhook server using modular routers and services.
This replaces the monolithic webhook_server.py with a clean, modular structure.
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Load from project root
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment variables from {env_path}")
    else:
        print(f"⚠️ .env file not found at {env_path}")
except ImportError:
    print("⚠️ python-dotenv not installed, environment variables may not load")

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import logger
from ai.model_manager import ModelManager
from vapi.api.vapi_router import create_vapi_router
from vapi.api.admin_router import create_admin_router
from vapi.api.ui_router import create_ui_router
from vapi.api.system_config_router import create_system_config_router

class ModularVAPIServer:
    """Modular VAPI Server with clean separation of concerns"""
    
    def __init__(self):
        # Initialize FastAPI app
        self.app = FastAPI(
            title="VAPI AI Assistant - Modular",
            version="2.0.0",
            description="Modular VAPI webhook server with clean architecture"
        )
        
        # Initialize SystemConfigManager for unified configuration
        try:
            from src.config.system_config import system_config
            self.config = system_config
            logger.info("✅ SystemConfigManager initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize SystemConfigManager: {e}")
            self.config = None
        
        # Initialize services with configuration
        self.model_manager = None
        self.vapi_api_key = self._get_config_value("VAPI_API_KEY", "your-vapi-key-here")
        self.runpod_api_key = self._get_config_value("RUNPOD_API_KEY", "")
        
        # Setup server
        self._setup_services()
        self._setup_static_files()
        self._setup_routers()
        self._setup_core_routes()
        
        logger.info("🚀 Modular VAPI Server initialized successfully")
    
    def _get_config_value(self, key: str, default: str = "") -> str:
        """Get configuration value with fallback to environment variables"""
        try:
            if self.config:
                # Try to get from system config first
                if key == "RUNPOD_API_KEY" and hasattr(self.config, 'get_provider_config'):
                    runpod_config = self.config.get_provider_config("runpod")
                    if runpod_config and runpod_config.api_key:
                        return runpod_config.api_key
                
                # Try to get from system config environment settings
                if hasattr(self.config.config, 'environment') and hasattr(self.config.config, 'ollama_host'):
                    # Map common keys to system config values
                    if key == "OLLAMA_HOST" and self.config.config.ollama_host:
                        return self.config.config.ollama_host
                    if key == "MAX_TOKENS" and self.config.config.max_tokens:
                        return str(self.config.config.max_tokens)
            
            # Fallback to environment variables
            return os.getenv(key, default)
        except Exception as e:
            logger.warning(f"⚠️ Error getting config value for {key}: {e}, using environment variable")
            return os.getenv(key, default)
    
    def _setup_services(self):
        """Initialize core services"""
        try:
            # Initialize Model Manager with system config instance for real-time updates
            self.model_manager = ModelManager(system_config_instance=self.config)
            logger.info("✅ Model Manager initialized with system config instance")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Model Manager: {e}")
            self.model_manager = None
    
    def _setup_static_files(self):
        """Setup static file serving for frontend assets"""
        try:
            # Path to frontend directory
            frontend_dir = Path(__file__).parent.parent / "frontend"
            
            if frontend_dir.exists():
                # Mount CSS and JS directories
                css_dir = frontend_dir / "css"
                js_dir = frontend_dir / "js"
                
                if css_dir.exists():
                    self.app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")
                    logger.info(f"📁 Mounted CSS files from {css_dir}")
                
                if js_dir.exists():
                    self.app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")
                    logger.info(f"📁 Mounted JS files from {js_dir}")
                
                # Mount public assets if they exist
                public_dir = Path(__file__).parent.parent / "public"
                if public_dir.exists():
                    self.app.mount("/public", StaticFiles(directory=str(public_dir)), name="public")
                    logger.info(f"📁 Mounted public files from {public_dir}")
            
        except Exception as e:
            logger.warning(f"⚠️ Could not setup static files: {e}")
    
    def _setup_routers(self):
        """Setup modular routers"""
        try:
            if not self.model_manager:
                logger.warning("⚠️ Model Manager not available, routers may have limited functionality")
                # Create a mock model manager for basic functionality
                from unittest.mock import Mock
                self.model_manager = Mock()
                self.model_manager.model_name = "mock-model"
                self.model_manager.generate_response = lambda x, **kwargs: "Mock response (Model Manager not available)"
                self.model_manager.is_model_available = lambda x: False
            
            # Create and include routers
            ui_router = create_ui_router(self.model_manager)
            admin_router = create_admin_router(self.model_manager, self.runpod_api_key)
            vapi_router = create_vapi_router(self.model_manager, self.vapi_api_key)
            system_config_router = create_system_config_router()
            
            # Include routers
            self.app.include_router(ui_router)
            self.app.include_router(admin_router)
            self.app.include_router(vapi_router)
            self.app.include_router(system_config_router)
            
            logger.info("✅ All routers included successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup routers: {e}")
    
    def _setup_core_routes(self):
        """Setup core routes that don't belong to specific routers"""
        
        @self.app.get("/favicon.ico")
        async def favicon():
            """Serve pete.png as favicon"""
            try:
                # Try different locations for the favicon
                favicon_paths = [
                    Path(__file__).parent.parent / "public" / "pete.png",
                    Path(__file__).parent.parent / "frontend" / "pete.png",
                    Path(__file__).parent / "public" / "pete.png"
                ]
                
                for favicon_path in favicon_paths:
                    if favicon_path.exists():
                        return FileResponse(favicon_path, media_type="image/png")
                
                # If no favicon found, return 404
                from fastapi import HTTPException
                raise HTTPException(status_code=404, detail="Favicon not found")
                
            except Exception as e:
                logger.warning(f"⚠️ Favicon error: {e}")
                from fastapi import HTTPException
                raise HTTPException(status_code=404, detail="Favicon not found")
        
        @self.app.get("/health")
        async def health_check():
            """Overall system health check"""
            try:
                model_available = False
                if self.model_manager and hasattr(self.model_manager, 'is_model_available'):
                    model_available = self.model_manager.is_model_available(self.model_manager.model_name)
                
                return {
                    "status": "healthy",
                    "server": "modular",
                    "version": "2.0.0",
                    "model_manager": "available" if self.model_manager else "unavailable",
                    "model_available": model_available,
                    "timestamp": str(Path(__file__).stat().st_mtime)  # Server start time
                }
            except Exception as e:
                return {
                    "status": "unhealthy",
                    "error": str(e),
                    "server": "modular",
                    "version": "2.0.0"
                }
        
        @self.app.get("/")
        async def root():
            """Root endpoint - redirect to UI"""
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/ui", status_code=302)
    
    def run(self, host: str = "0.0.0.0", port: int = 8000, debug: bool = False):
        """Run the server"""
        logger.info(f"🚀 Starting Modular VAPI Server on {host}:{port}")
        logger.info("📍 Available endpoints:")
        logger.info("   🏠 Root: http://localhost:8000/")
        logger.info("   💬 UI: http://localhost:8000/ui")
        logger.info("   🔧 Admin: http://localhost:8000/admin")
        logger.info("   🤖 VAPI: http://localhost:8000/vapi/*")
        logger.info("   ❤️ Health: http://localhost:8000/health")
        
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info" if not debug else "debug",
            reload=debug
        )

def create_app():
    """Factory function to create the FastAPI app"""
    server = ModularVAPIServer()
    return server.app

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Modular VAPI Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    try:
        server = ModularVAPIServer()
        server.run(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
