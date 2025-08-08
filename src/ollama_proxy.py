#!/usr/bin/env python3
"""
Ollama OpenAI Proxy
==================

Converts OpenAI-compatible requests to Ollama format for VAPI integration.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
import json
import os
from loguru import logger

app = FastAPI(title="Ollama OpenAI Proxy", version="1.0.0")

# Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "peteollama:property-manager-v0.0.1")

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = DEFAULT_MODEL
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000
    stream: Optional[bool] = False

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/version")
            if response.status_code == 200:
                return {"status": "healthy", "ollama_version": response.json().get("version")}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Ollama service unavailable")
    
    return {"status": "healthy"}

@app.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """Convert OpenAI chat completion request to Ollama format"""
    
    # Convert messages to Ollama prompt format
    prompt = ""
    for message in request.messages:
        if message.role == "system":
            prompt += f"System: {message.content}\n\n"
        elif message.role == "user":
            prompt += f"User: {message.content}\n"
        elif message.role == "assistant":
            prompt += f"Assistant: {message.content}\n"
    
    prompt += "Assistant: "
    
    # Prepare Ollama request
    ollama_request = {
        "model": request.model,
        "prompt": prompt,
        "stream": request.stream,
        "options": {
            "temperature": request.temperature,
            "num_predict": request.max_tokens
        }
    }
    
    logger.info(f"Converting request for model: {request.model}")
    logger.debug(f"Prompt: {prompt[:100]}...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=ollama_request,
                timeout=30.0
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=500, detail="Ollama service error")
            
            ollama_response = response.json()
            
            # Convert Ollama response to OpenAI format
            content = ollama_response.get("response", "")
            
            chat_response = ChatCompletionResponse(
                id="chatcmpl-" + str(hash(content))[:8],
                created=int(ollama_response.get("created_at", 0)),
                model=request.model,
                choices=[{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "finish_reason": "stop"
                }],
                usage={
                    "prompt_tokens": len(prompt.split()),
                    "completion_tokens": len(content.split()),
                    "total_tokens": len(prompt.split()) + len(content.split())
                }
            )
            
            logger.info(f"Successfully converted response for {request.model}")
            return chat_response
            
    except httpx.TimeoutException:
        logger.error("Ollama request timed out")
        raise HTTPException(status_code=504, detail="Ollama service timeout")
    except Exception as e:
        logger.error(f"Error calling Ollama: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/models")
async def list_models():
    """List available models in OpenAI format"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to fetch models")
            
            models_data = response.json()
            models = []
            
            for model in models_data.get("models", []):
                models.append({
                    "id": model.get("name", "unknown"),
                    "object": "model",
                    "created": 0,
                    "owned_by": "ollama"
                })
            
            return {
                "object": "list",
                "data": models
            }
            
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail="Failed to list models")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 