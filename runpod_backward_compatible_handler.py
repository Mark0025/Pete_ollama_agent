#!/usr/bin/env python3
"""
PeteOllama - Backward Compatible RunPod Serverless Handler
Supports BOTH formats:
1. OLD: {"prompt": "message"} 
2. NEW: {"type": "chat", "message": "message", "model": "llama3:latest"}
"""

import runpod
import json
import requests
import os
from typing import Dict, Any, Optional


def handler(job_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    RunPod serverless handler that supports both old and new formats
    
    OLD FORMAT (backward compatibility):
    {"prompt": "Hello there"}
    
    NEW FORMAT (structured):
    {"type": "chat", "message": "Hello", "model": "llama3:latest"}
    {"type": "vapi_webhook", "message": "Help me", "call_id": "123"}
    {"type": "admin", "action": "status"}
    """
    
    try:
        print(f"📥 Received input: {json.dumps(job_input, indent=2)}")
        
        # OPTION 1: Handle NEW structured format
        if "type" in job_input:
            return handle_structured_format(job_input)
        
        # OPTION 2: Handle OLD prompt format (backward compatibility)
        elif "prompt" in job_input:
            return handle_prompt_format(job_input)
        
        # OPTION 3: Auto-detect based on content
        else:
            # If there's a message field, treat as new format
            if "message" in job_input:
                return handle_structured_format({
                    "type": "chat",
                    "message": job_input["message"],
                    "model": job_input.get("model", "llama3:latest")
                })
            else:
                return {"error": "Invalid request format", "status": "error"}
                
    except Exception as e:
        print(f"❌ Handler error: {str(e)}")
        return {"error": str(e), "status": "error"}


def handle_structured_format(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle new structured format"""
    
    request_type = input_data.get("type", "chat")
    
    if request_type == "chat":
        message = input_data.get("message", "")
        model = input_data.get("model", "llama3:latest")
        
        print(f"💬 Chat request: {message[:50]}...")
        print(f"🤖 Model: {model}")
        
        # Process with Ollama
        response_text = process_with_ollama(message, model)
        
        return {
            "status": "success",
            "response": response_text,
            "model": model,
            "type": "chat"
        }
        
    elif request_type == "vapi_webhook":
        message = input_data.get("message", "")
        call_id = input_data.get("call_id", "")
        
        print(f"📞 VAPI webhook: {message[:50]}...")
        print(f"🆔 Call ID: {call_id}")
        
        # Process VAPI message
        response_text = process_with_ollama(message, "llama3:latest")
        
        return {
            "status": "success", 
            "vapi_response": response_text,
            "call_id": call_id,
            "type": "vapi_webhook"
        }
        
    elif request_type == "admin":
        action = input_data.get("action", "status")
        
        print(f"⚙️ Admin action: {action}")
        
        if action == "status":
            return {
                "status": "success",
                "admin_result": "System is running normally",
                "uptime": "Available",
                "models": ["llama3:latest"],
                "type": "admin"
            }
        else:
            return {
                "status": "success",
                "admin_result": f"Admin action '{action}' completed",
                "type": "admin"
            }
    
    else:
        return {"error": f"Unknown request type: {request_type}", "status": "error"}


def handle_prompt_format(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle old prompt format for backward compatibility"""
    
    prompt = input_data.get("prompt", "")
    model = input_data.get("model", "llama3:latest")
    
    print(f"🔄 Legacy prompt format: {prompt[:50]}...")
    print(f"🤖 Model: {model}")
    
    # Process with Ollama
    response_text = process_with_ollama(prompt, model)
    
    return {
        "status": "success",
        "response": response_text,
        "model": model,
        "format": "legacy_prompt"
    }


def process_with_ollama(message: str, model: str = "llama3:latest") -> str:
    """Process message with local Ollama instance"""
    
    try:
        # Use local Ollama API
        ollama_url = "http://localhost:11434/api/chat"
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": message}],
            "stream": False
        }
        
        print(f"🚀 Sending to Ollama: {ollama_url}")
        response = requests.post(ollama_url, json=payload, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            response_content = result.get("message", {}).get("content", "")
            
            if response_content:
                print(f"✅ Ollama response: {response_content[:100]}...")
                return response_content
            else:
                return "I received your message but couldn't generate a response."
                
        else:
            print(f"❌ Ollama error: {response.status_code} - {response.text}")
            return f"I'm having trouble processing your request right now. (Error {response.status_code})"
            
    except requests.exceptions.Timeout:
        print("⏰ Ollama timeout")
        return "I'm taking longer than usual to respond. Please try again."
        
    except Exception as e:
        print(f"❌ Ollama processing error: {str(e)}")
        return f"I encountered an error while processing your request: {str(e)}"


def template(prompt: str) -> str:
    """Template function for backward compatibility with old handler"""
    return f"You are PeteOllama, a helpful assistant. Respond to: {prompt}"


# Health check for RunPod
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "handler": "backward_compatible",
        "supports": ["prompt", "structured"],
        "models": ["llama3:latest"]
    }


if __name__ == "__main__":
    print("🚀 Starting PeteOllama Backward Compatible Handler")
    print("✅ Supports OLD format: {'prompt': 'message'}")  
    print("✅ Supports NEW format: {'type': 'chat', 'message': 'text'}")
    
    # Start RunPod serverless
    runpod.serverless.start({
        "handler": handler,
        "health_check": health_check
    })
