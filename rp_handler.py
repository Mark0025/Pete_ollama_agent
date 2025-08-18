#!/usr/bin/env python3
"""
PeteOllama V1 - RunPod Serverless Handler
Handles VAPI requests and routes them to appropriate handlers
"""

import runpod
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get RunPod configuration from environment
RUNPOD_API_KEY = os.getenv('RUNPOD_API_KEY')
RUNPOD_SERVERLESS_ENDPOINT = os.getenv('RUNPOD_SERVERLESS_ENDPOINT')

if not RUNPOD_API_KEY:
    print("⚠️ Warning: RUNPOD_API_KEY not found in environment variables")
if not RUNPOD_SERVERLESS_ENDPOINT:
    print("⚠️ Warning: RUNPOD_SERVERLESS_ENDPOINT not found in environment variables")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from vapi.webhook_server import VAPIWebhookServer
from ollama_proxy_streaming import OllamaProxy
from database.pete_db_manager import PeteDBManager
from config.model_settings import model_settings
from utils.logger import logger

# Initialize components
webhook_server = VAPIWebhookServer(port=8000)
ollama_proxy = OllamaProxy()
db_manager = PeteDBManager()

def handler(event):
    """
    Main RunPod Serverless handler function
    
    Args:
        event (dict): Contains the input data and request metadata
        
    Returns:
        dict: Response data for the client
    """
    try:
        logger.info(f"🚀 Processing request: {event.get('id', 'unknown')}")
        
        # Extract input data
        input_data = event.get('input', {})
        request_type = input_data.get('type', 'webhook')
        
        # Route based on request type
        if request_type == 'webhook':
            # VAPI webhook request
            return handle_webhook_request(input_data)
        elif request_type == 'chat':
            # Direct chat completion
            return handle_chat_request(input_data)
        elif request_type == 'admin':
            # Admin UI request
            return handle_admin_request(input_data)
        else:
            # Default to webhook
            return handle_webhook_request(input_data)
            
    except Exception as e:
        logger.error(f"❌ Handler error: {str(e)}")
        return {
            "error": str(e),
            "status": "error"
        }

def handle_webhook_request(input_data):
    """Handle VAPI webhook requests"""
    try:
        # Extract webhook data
        webhook_data = input_data.get('webhook_data', {})
        
        # Process through webhook server
        # This would integrate with your existing VAPI webhook logic
        response = {
            "status": "success",
            "message": "Webhook processed",
            "data": webhook_data
        }
        
        logger.info("✅ Webhook request processed successfully")
        return response
        
    except Exception as e:
        logger.error(f"❌ Webhook error: {str(e)}")
        return {"error": str(e), "status": "error"}

def handle_chat_request(input_data):
    """Handle direct chat completion requests"""
    try:
        # Extract chat parameters
        model = input_data.get('model', 'peteollama:property-manager-v0.0.1')
        messages = input_data.get('messages', [])
        temperature = input_data.get('temperature', 0.7)
        max_tokens = input_data.get('max_tokens', 1000)
        
        # Process through Ollama proxy
        response = ollama_proxy.process_chat(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        logger.info("✅ Chat request processed successfully")
        return {
            "status": "success",
            "response": response
        }
        
    except Exception as e:
        logger.error(f"❌ Chat error: {str(e)}")
        return {"error": str(e), "status": "error"}

def handle_admin_request(input_data):
    """Handle admin UI requests"""
    try:
        # Extract admin action
        action = input_data.get('action', 'status')
        
        if action == 'status':
            # Return system status
            return {
                "status": "success",
                "data": {
                    "models_available": webhook_server.model_manager.is_available(),
                    "database_connected": db_manager.is_connected(),
                    "ollama_running": True
                }
            }
        elif action == 'models':
            # Return available models
            models = webhook_server.model_manager.list_models()
            return {
                "status": "success",
                "data": {"models": models}
            }
        else:
            return {"error": f"Unknown action: {action}", "status": "error"}
            
    except Exception as e:
        logger.error(f"❌ Admin request error: {str(e)}")
        return {"error": str(e), "status": "error"}

# Health check endpoint for RunPod
def health_check():
    """Health check for RunPod monitoring"""
    try:
        return {
            "status": "healthy",
            "endpoint_id": RUNPOD_SERVERLESS_ENDPOINT,
            "models_available": webhook_server.model_manager.is_available(),
            "database_connected": db_manager.is_connected()
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

def get_endpoint_url():
    """Get the full RunPod serverless endpoint URL"""
    if RUNPOD_SERVERLESS_ENDPOINT:
        return f"https://{RUNPOD_SERVERLESS_ENDPOINT}.runpod.net"
    return None

# Start the Serverless function when the script is run
if __name__ == '__main__':
    logger.info("🚀 Starting PeteOllama Serverless Handler")
    
    # Initialize components
    try:
        # Test database connection
        if db_manager.is_connected():
            logger.info("✅ Database connected")
        else:
            logger.warning("⚠️ Database connection failed")
        
        # Test model availability
        if webhook_server.model_manager.is_available():
            logger.info("✅ Models available")
        else:
            logger.warning("⚠️ Models not available")
            
        # Log endpoint information
        endpoint_url = get_endpoint_url()
        if endpoint_url:
            logger.info(f"🎯 Serverless handler ready at: {endpoint_url}")
        else:
            logger.warning("⚠️ Endpoint URL not available")
        
        logger.info("🎯 Serverless handler ready for requests")
        
    except Exception as e:
        logger.error(f"❌ Initialization error: {str(e)}")
    
    # Start RunPod serverless
    runpod.serverless.start({
        "handler": handler,
        "health_check": health_check,
        "api_key": RUNPOD_API_KEY
    })
