"""
UI Router
=========

FastAPI router for user interface endpoints including the main UI page,
static files, and UI-specific API endpoints.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import Dict, Any, List
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.logger import logger
from ai.model_manager import ModelManager
from config.model_settings import model_settings
from vapi.services.provider_service import ProviderService

class UIRouter:
    """Router class for UI endpoints"""
    
    def __init__(self, model_manager: ModelManager):
        self.router = APIRouter(tags=["ui"])
        self.model_manager = model_manager
        self.provider_service = ProviderService()
        
        # Get paths to frontend assets
        self.frontend_dir = Path(__file__).parent.parent.parent / "frontend"
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup UI routes"""
        
        @self.router.get("/", response_class=HTMLResponse)
        async def root(request: Request):
            """Root endpoint - redirect to main UI"""
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/ui", status_code=302)
        
        @self.router.get("/ui", response_class=HTMLResponse)
        @self.router.get("/ui/", response_class=HTMLResponse)
        async def ui_page(request: Request):
            """Main UI page - serve the existing frontend main-ui.html"""
            try:
                # Path to the existing frontend main-ui.html
                frontend_path = Path(__file__).parent.parent.parent / "frontend" / "html" / "main-ui.html"
                
                if frontend_path.exists():
                    with open(frontend_path, 'r', encoding='utf-8') as f:
                        return f.read()
                else:
                    # Fallback to a simple message if file doesn't exist
                    return '''
                    <!DOCTYPE html>
                    <html><head><title>UI Not Found</title></head>
                    <body>
                        <h1>Frontend UI Not Found</h1>
                        <p>The main UI file was not found at: {}</p>
                        <p><a href="/admin">Go to Admin</a></p>
                    </body></html>
                    '''.format(frontend_path)
            
            except Exception as e:
                logger.error(f"UI page error: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/personas")
        async def get_personas():
            """Get personas for the current provider (for UI) - NOW PROVIDER-AWARE!"""
            try:
                # Get current provider from system configuration (authoritative source)
                try:
                    from src.config.system_config import system_config
                    current_provider = system_config.config.default_provider
                    logger.info(f"📋 UI: Using provider from system_config: {current_provider}")
                except Exception as e:
                    logger.warning(f"Failed to get provider from system_config: {e}, falling back to model_settings")
                    try:
                        provider_settings = model_settings.get_provider_settings()
                        current_provider = provider_settings.get('default_provider', 'ollama')
                    except Exception as e2:
                        logger.warning(f"Fallback also failed: {e2}, defaulting to ollama")
                        current_provider = 'ollama'
                
                logger.info(f"📋 UI: Serving models for provider: {current_provider}")
                
                # Use provider service to get personas - NOW RESPECTS PROVIDER FILTERING!
                personas = await self.provider_service.get_personas_for_provider(current_provider)
                
                if not personas:
                    logger.warning(f"⚠️ No personas available for provider {current_provider}, using fallback")
                    return self.provider_service._get_fallback_personas()
                
                logger.info(f"✅ UI: Served {len(personas)} personas for provider {current_provider}")
                return personas
                
            except Exception as e:
                logger.error(f"Error getting personas for UI: {e}")
                # Return fallback personas
                return self.provider_service._get_fallback_personas()
        
        @self.router.get("/models")
        async def get_models():
            """Get available models for UI dropdowns - NOW PROVIDER-AWARE!"""
            try:
                # Get current provider from system configuration (authoritative source)
                try:
                    from src.config.system_config import system_config
                    current_provider = system_config.config.default_provider
                    logger.info(f"📋 UI Models: Using provider from system_config: {current_provider}")
                except Exception as e:
                    logger.warning(f"Failed to get provider from system_config: {e}, falling back to model_settings")
                    try:
                        provider_settings = model_settings.get_provider_settings()
                        current_provider = provider_settings.get('default_provider', 'ollama')
                    except Exception as e2:
                        logger.warning(f"Fallback also failed: {e2}, defaulting to ollama")
                        current_provider = 'ollama'
                
                # Get provider-specific models instead of all UI models
                try:
                    provider_personas = await self.provider_service.get_personas_for_provider(current_provider)
                    
                    # Extract models from provider-specific personas
                    provider_models = []
                    for persona in provider_personas:
                        for model in persona.models:
                            provider_models.append(model)
                    
                    logger.info(f"📋 UI Models: Found {len(provider_models)} models for provider {current_provider}")
                    
                except Exception as e:
                    logger.warning(f"Failed to get provider models: {e}, falling back to UI models")
                    provider_models = model_settings.get_ui_models()
                
                # Get current model info
                current_model = self.model_manager.model_name
                custom_model = getattr(self.model_manager, 'custom_model_name', None)
                
                # Filter jamie models based on current provider
                if current_provider == 'ollama':
                    # Only show jamie models for Ollama (local custom models)
                    jamie_models = [model.dict() for model in provider_models if 'jamie' in model.name.lower()]
                    regular_models = [model.dict() for model in provider_models if 'jamie' not in model.name.lower()]
                else:
                    # For cloud providers (OpenRouter, RunPod), no jamie models
                    jamie_models = []
                    regular_models = [model.dict() for model in provider_models]
                
                return {
                    "models": [model.dict() for model in provider_models],
                    "current_model": current_model,
                    "custom_model": custom_model,
                    "current_provider": current_provider,
                    "jamie_models": jamie_models,
                    "regular_models": regular_models
                }
            
            except Exception as e:
                logger.error(f"Error getting models for UI: {str(e)}")
                return {
                    "models": [],
                    "current_model": "unknown",
                    "custom_model": None,
                    "current_provider": "ollama",
                    "jamie_models": [],
                    "regular_models": []
                }
        
        @self.router.get("/status")
        async def ui_status():
            """Get system status for UI"""
            try:
                # Get basic status info for the UI
                model_available = self.model_manager.is_model_available(self.model_manager.model_name)
                
                # Get provider info
                try:
                    provider_settings = model_settings.get_provider_settings()
                    current_provider = provider_settings.get('default_provider', 'ollama')
                except Exception:
                    current_provider = 'ollama'
                
                # Get model counts
                try:
                    ui_models = model_settings.get_ui_models()
                    total_models = len(ui_models)
                    jamie_models = len([m for m in ui_models if m.is_jamie_model])
                except Exception:
                    total_models = 0
                    jamie_models = 0
                
                return {
                    "status": "online",
                    "model_available": model_available,
                    "current_model": self.model_manager.model_name,
                    "current_provider": current_provider,
                    "total_models": total_models,
                    "jamie_models": jamie_models
                }
            
            except Exception as e:
                logger.error(f"Error getting UI status: {str(e)}")
                return {
                    "status": "error",
                    "error": str(e),
                    "model_available": False,
                    "current_model": "unknown",
                    "current_provider": "ollama",
                    "total_models": 0,
                    "jamie_models": 0
                }
        
        @self.router.post("/chat")
        async def ui_chat(request: Request):
            """Chat endpoint for UI - direct message to AI"""
            try:
                body = await request.json()
                message = body.get('message', '')
                model_name = body.get('model')  # optional specific model
                
                if not message:
                    raise HTTPException(status_code=400, detail="Message required")
                
                logger.info(f"💬 UI Chat: Model: {model_name or 'default'}, Message: {message[:50]}...")
                
                # Generate AI response (model_name can be None)
                response = self.model_manager.generate_response(message, model_name=model_name)
                model_used = model_name or (
                    self.model_manager.custom_model_name 
                    if hasattr(self.model_manager, 'custom_model_name') and 
                       self.model_manager.is_model_available(self.model_manager.custom_model_name) 
                    else self.model_manager.model_name
                )
                
                return {
                    "user_message": message,
                    "ai_response": response,
                    "model_used": model_used,
                    "success": True
                }
            
            except Exception as e:
                logger.error(f"UI chat error: {str(e)}")
                return {
                    "user_message": body.get('message', '') if 'body' in locals() else '',
                    "ai_response": f"Error: {str(e)}",
                    "model_used": "error",
                    "success": False,
                    "error": str(e)
                }
        
        @self.router.post("/switch-provider")
        async def switch_provider(request: Request):
            """Switch the current AI provider"""
            try:
                body = await request.json()
                provider = body.get('provider')
                
                if not provider:
                    raise HTTPException(status_code=400, detail="Provider required")
                
                # Update provider settings
                provider_settings = {
                    'default_provider': provider,
                    'provider_updated': True
                }
                
                model_settings.update_provider_settings(provider_settings)
                
                logger.info(f"🔄 Provider switched to: {provider}")
                
                # Get updated personas for new provider
                personas = await self.provider_service.get_personas_for_provider(provider)
                
                return {
                    "success": True,
                    "new_provider": provider,
                    "message": f"Switched to {provider}",
                    "personas": personas
                }
            
            except Exception as e:
                logger.error(f"Provider switch error: {str(e)}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": f"Failed to switch provider: {str(e)}"
                }
        
        @self.router.post("/test/stream")
        async def test_stream(request: Request):
            """Stream AI response token-by-token for testing"""
            import json
            import time
            
            start_time = time.time()
            request_id = f"req_{int(start_time)}_{hash(time.time()) % 10000}"
            
            try:
                from fastapi.responses import StreamingResponse
                
                body = await request.json()
                message = body.get('message', '')
                model_name = body.get('model')
                
                if not message:
                    raise HTTPException(status_code=400, detail="Message required")

                logger.info(f"🔄 UI STREAM [{request_id}] Starting - Model: {model_name}, Message: {message[:50]}...")
                
                # Check if model manager supports streaming
                if hasattr(self.model_manager, 'generate_stream'):
                    # Use streaming if available
                    def token_iter():
                        full_response = ""
                        token_count = 0
                        first_token_time = None
                        
                        for token in self.model_manager.generate_stream(message, model_name=model_name):
                            if first_token_time is None:
                                first_token_time = time.time()
                            
                            full_response += token
                            token_count += 1
                            yield token
                        
                        # Log completion
                        end_time = time.time()
                        total_duration = end_time - start_time
                        first_token_latency = (first_token_time - start_time) if first_token_time else 0
                        tokens_per_second = token_count / total_duration if total_duration > 0 else 0
                        
                        logger.info(f"📊 UI STREAM [{request_id}] Complete - Duration: {total_duration:.2f}s, Tokens: {token_count}, TPS: {tokens_per_second:.2f}")
                    
                    return StreamingResponse(token_iter(), media_type='text/plain')
                else:
                    # Fallback to regular response if streaming not available
                    response = self.model_manager.generate_response(message, model_name=model_name)
                    
                    # Simulate streaming by yielding chunks
                    def simulate_stream():
                        words = response.split()
                        for i, word in enumerate(words):
                            if i == 0:
                                yield word
                            else:
                                yield " " + word
                            # Small delay to simulate streaming
                            import time
                            time.sleep(0.05)
                    
                    return StreamingResponse(simulate_stream(), media_type='text/plain')
                    
            except Exception as e:
                end_time = time.time()
                error_duration = end_time - start_time
                logger.error(f"❌ UI STREAM [{request_id}] Error after {error_duration:.2f}s: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))

def create_ui_router(model_manager: ModelManager) -> APIRouter:
    """Factory function to create UI router"""
    ui_router = UIRouter(model_manager)
    return ui_router.router
