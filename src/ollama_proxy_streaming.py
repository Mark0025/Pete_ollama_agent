#!/usr/bin/env python3
"""
Ollama OpenAI Proxy with Streaming Support
=========================================

Converts OpenAI-compatible requests to Ollama format for VAPI integration.
Supports both streaming and non-streaming responses.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
import json
import os
import datetime
import asyncio
from loguru import logger

app = FastAPI(title="Ollama OpenAI Proxy with Streaming", version="1.0.0")

# Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "peteollama:property-manager-v0.0.1")

# Import model settings manager
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from config.model_settings import ModelSettingsManager, ModelConfig

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
    """Convert OpenAI chat completion request to Ollama format with streaming support"""
    
    # Convert messages to Ollama prompt format
    prompt = ""
    for message in request.messages:
        if message.role == "system":
            prompt += f"System: {message.content}\n\n"
        elif message.role == "user":
            prompt += f"User: {message.content}\n"
        elif message.role == "assistant":
            prompt += f"Assistant: {message.content}\n"
    
    # Add conversational mode constraint
    prompt += "System: IMPORTANT - You are in conversational mode. Give ONLY direct, helpful answers. NO internal thinking, NO model configuration details, NO system information. Keep responses concise and focused on the user's question.\n\n"
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
    
    logger.info(f"Converting request for model: {request.model}, stream: {request.stream}")
    logger.debug(f"Prompt: {prompt[:100]}...")
    
    # Handle streaming response
    if request.stream:
        return await handle_streaming_response(ollama_request, request.model, prompt)
    else:
        return await handle_non_streaming_response(ollama_request, request.model, prompt)

async def handle_streaming_response(ollama_request: dict, model: str, prompt: str):
    """Handle streaming responses for VAPI real-time interactions with admin-controlled settings"""
    
    # Get admin settings for this model
    settings_manager = ModelSettingsManager()
    model_config = settings_manager.models.get(model)
    
    async def generate_stream():
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{OLLAMA_BASE_URL}/api/generate",
                    json=ollama_request,
                    timeout=30.0
                ) as response:
                    if response.status_code != 200:
                        logger.error(f"Ollama streaming error: {response.status_code}")
                        yield f"data: {json.dumps({'error': 'Ollama service error'})}\n\n"
                        return
                    
                    full_response = ""
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                data = json.loads(line)
                                if data.get("done", False):
                                    # Process full response based on admin settings
                                    processed_response = process_response_for_vapi(
                                        full_response, model_config, model
                                    )
                                    
                                    # Send final message
                                    final_response = {
                                        "id": f"chatcmpl-{hash(str(data)) % 100000000}",
                                        "object": "chat.completion.chunk",
                                        "created": int(datetime.datetime.now().timestamp()),
                                        "model": model,
                                        "choices": [{
                                            "index": 0,
                                            "delta": {},
                                            "finish_reason": "stop"
                                        }]
                                    }
                                    yield f"data: {json.dumps(final_response)}\n\n"
                                    yield "data: [DONE]\n\n"
                                    break
                                else:
                                    # Accumulate response for processing
                                    chunk_content = data.get("response", "")
                                    full_response += chunk_content
                                    
                                    # Send streaming chunk (raw for now, will be processed at end)
                                    chunk_response = {
                                        "id": f"chatcmpl-{hash(str(data)) % 100000000}",
                                        "object": "chat.completion.chunk",
                                        "created": int(datetime.datetime.now().timestamp()),
                                        "model": model,
                                        "choices": [{
                                            "index": 0,
                                            "delta": {
                                                "content": chunk_content
                                            },
                                            "finish_reason": None
                                        }]
                                    }
                                    yield f"data: {json.dumps(chunk_response)}\n\n"
                            except json.JSONDecodeError:
                                continue
                                
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            error_response = {
                "error": {
                    "message": f"Streaming failed: {str(e)}",
                    "type": "internal_error"
                }
            }
            yield f"data: {json.dumps(error_response)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

def process_response_for_vapi(response: str, model_config: ModelConfig, model_name: str) -> str:
    """Process response based on admin panel settings"""
    if not model_config:
        return response
    
    processed = response
    
    # 1. Conversational Mode: Remove internal thinking
    if model_config.conversational_mode:
        # Remove common thinking patterns
        thinking_patterns = [
            "Let me think about this",
            "I need to consider",
            "Based on my training",
            "As an AI model",
            "My configuration shows",
            "According to my settings"
        ]
        for pattern in thinking_patterns:
            processed = processed.replace(pattern, "")
    
    # 2. Remove Model Info if disabled
    if not model_config.include_model_info:
        # Remove model configuration details
        info_patterns = [
            "Model: ",
            "Configuration: ",
            "Settings: ",
            "Parameters: "
        ]
        for pattern in info_patterns:
            processed = processed.replace(pattern, "")
    
    # 3. Apply Response Style
    if model_config.response_style == "concise":
        # Keep only the direct answer
        lines = processed.split('\n')
        concise_lines = []
        for line in lines:
            if line.strip() and not line.startswith(('Note:', 'Info:', 'Config:')):
                concise_lines.append(line)
        processed = '\n'.join(concise_lines)
    
    # 4. Limit Response Length
    if model_config.max_response_length > 0:
        words = processed.split()
        if len(words) > model_config.max_response_length:
            processed = ' '.join(words[:model_config.max_response_length]) + "..."
    
    # 5. Clean up extra whitespace
    processed = ' '.join(processed.split())
    
    logger.info(f"Processed response for {model_name}: {len(response)} -> {len(processed)} chars")
    return processed

async def handle_non_streaming_response(ollama_request: dict, model: str, prompt: str):
    """Handle non-streaming responses (fallback)"""
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
            content = ollama_response.get("response", "")
            
            # Convert ISO timestamp to Unix timestamp
            created_at = ollama_response.get("created_at", "")
            if created_at:
                try:
                    dt = datetime.datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    created_timestamp = int(dt.timestamp())
                except:
                    created_timestamp = int(datetime.datetime.now().timestamp())
            else:
                created_timestamp = int(datetime.datetime.now().timestamp())
            
            chat_response = ChatCompletionResponse(
                id="chatcmpl-" + str(hash(content))[:8],
                created=created_timestamp,
                model=model,
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
            
            logger.info(f"Successfully converted non-streaming response for {model}")
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
