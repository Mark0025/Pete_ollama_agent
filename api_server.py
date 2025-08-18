#!/usr/bin/env python3
"""
PeteOllama API Server - Serverless-First
Routes all requests through RunPod serverless endpoint
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn
import os
from runpod_handler import pete_handler

# Initialize FastAPI app
app = FastAPI(
    title="PeteOllama Serverless API",
    description="Routes all AI requests through RunPod serverless endpoint",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    model: str = "llama3:latest"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000

class AdminRequest(BaseModel):
    action: str
    data: Optional[Dict[str, Any]] = None

# Routes
@app.get("/")
async def root():
    """Root endpoint with status"""
    return HTMLResponse(content="""
    <html>
        <head><title>PeteOllama Serverless API</title></head>
        <body>
            <h1>🏠 PeteOllama Serverless API</h1>
            <p>All requests are routed through RunPod serverless endpoint</p>
            <h2>Available Endpoints:</h2>
            <ul>
                <li><code>POST /api/chat</code> - Chat completions</li>
                <li><code>POST /vapi/webhook</code> - VAPI webhooks</li>
                <li><code>POST /admin/action</code> - Admin actions</li>
                <li><code>GET /health</code> - Health check</li>
                <li><code>GET /docs</code> - API documentation</li>
            </ul>
            <p><strong>Status:</strong> ✅ Running</p>
        </body>
    </html>
    """)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test RunPod connection by checking environment
        api_key = os.getenv('RUNPOD_API_KEY')
        endpoint_id = os.getenv('RUNPOD_SERVERLESS_ENDPOINT')
        
        return {
            "status": "healthy",
            "service": "PeteOllama Serverless API",
            "runpod_configured": bool(api_key and endpoint_id),
            "endpoint_id": endpoint_id if endpoint_id else "Not configured"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.post("/api/chat")
async def chat_completion(request: ChatRequest):
    """
    Chat completion endpoint
    Routes request through RunPod serverless
    """
    try:
        result = pete_handler.chat_completion(
            message=request.message,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat completion failed: {str(e)}")

@app.post("/vapi/webhook")
async def vapi_webhook_handler(request: Request):
    """
    VAPI webhook endpoint
    Routes webhook through RunPod serverless
    """
    try:
        # Get webhook data from request
        webhook_data = await request.json()
        
        result = pete_handler.vapi_webhook(webhook_data)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"VAPI webhook failed: {str(e)}")

@app.post("/admin/action")
async def admin_action_handler(request: AdminRequest):
    """
    Admin action endpoint
    Routes admin requests through RunPod serverless
    """
    try:
        result = pete_handler.admin_action(
            action=request.action,
            data=request.data
        )
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Admin action failed: {str(e)}")

@app.get("/api/models")
async def list_models():
    """List available models via admin action"""
    try:
        result = pete_handler.admin_action("list_models")
        
        if result.get("status") == "error":
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List models failed: {str(e)}")

@app.get("/api/status")
async def get_status():
    """Get system status via admin action"""
    try:
        result = pete_handler.admin_action("status")
        
        if result.get("status") == "error":
            # Don't fail hard on status checks
            return {
                "status": "partial",
                "message": "RunPod serverless endpoint not fully operational",
                "error": result.get("error")
            }
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "message": "Status check failed",
            "error": str(e)
        }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint not found", 
            "message": f"The endpoint {request.url.path} does not exist",
            "available_endpoints": [
                "/api/chat", 
                "/vapi/webhook", 
                "/admin/action",
                "/health",
                "/docs"
            ]
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "Something went wrong processing your request",
            "suggestion": "Check RunPod serverless endpoint configuration"
        }
    )

def main():
    """Start the API server"""
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"🚀 Starting PeteOllama Serverless API")
    print(f"📍 Running on: http://{host}:{port}")
    print(f"📚 Documentation: http://{host}:{port}/docs")
    print(f"🩺 Health check: http://{host}:{port}/health")
    
    # Check environment
    api_key = os.getenv('RUNPOD_API_KEY')
    endpoint_id = os.getenv('RUNPOD_SERVERLESS_ENDPOINT')
    
    if not api_key or not endpoint_id:
        print(f"⚠️  WARNING: RunPod configuration missing")
        print(f"🔑 API Key: {'✅ Set' if api_key else '❌ Missing'}")
        print(f"📋 Endpoint: {'✅ Set' if endpoint_id else '❌ Missing'}")
        print(f"💡 Make sure .env file is configured properly")
    else:
        print(f"✅ RunPod configuration looks good")
        print(f"📋 Endpoint ID: {endpoint_id}")
    
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    main()
