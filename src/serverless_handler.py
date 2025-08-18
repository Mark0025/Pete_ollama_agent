#!/usr/bin/env python3
"""
PeteOllama V1 - Serverless-First Handler
Routes all requests to RunPod serverless endpoint with warmup
"""

import os
import asyncio
import aiohttp
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

class ServerlessHandler:
    """Handles all AI requests through RunPod serverless endpoint"""
    
    def __init__(self):
        self.endpoint_id = os.getenv('RUNPOD_SERVERLESS_ENDPOINT')
        self.api_key = os.getenv('RUNPOD_API_KEY')
        self.base_url = f"https://{self.endpoint_id}.runpod.net"
        self.warmed_up = False
        self.session: Optional[aiohttp.ClientSession] = None
        
        if not self.endpoint_id:
            raise ValueError("RUNPOD_SERVERLESS_ENDPOINT not configured")
        if not self.api_key:
            raise ValueError("RUNPOD_API_KEY not configured")
            
        logger.info(f"🚀 Serverless handler initialized for endpoint: {self.base_url}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with proper cleanup"""
        if self.session:
            try:
                await self.session.close()
                # Give time for underlying connections to close
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.warning(f"⚠️ Session cleanup warning: {e}")
            finally:
                self.session = None
    
    async def warmup_endpoint(self) -> bool:
        """Warm up the serverless endpoint to reduce cold start latency"""
        try:
            logger.info("🔥 Warming up serverless endpoint...")
            
            # Send a simple health check to warm up the container
            warmup_response = await self._make_request(
                'POST',
                '/api/chat',
                {
                    'message': 'Warmup test',
                    'model': 'peteollama:jamie-fixed'
                }
            )
            
            if warmup_response and warmup_response.get('status') != 'error':
                self.warmed_up = True
                logger.info("✅ Serverless endpoint warmed up successfully")
                return True
            else:
                logger.warning("⚠️ Warmup response indicates endpoint not ready")
                return False
                
        except Exception as e:
            logger.error(f"❌ Warmup failed: {str(e)}")
            return False
    
    async def chat_completion(self, message: str, model: str = 'peteollama:jamie-fixed', **kwargs) -> Dict[str, Any]:
        """Handle chat completion through serverless endpoint"""
        try:
            # Ensure endpoint is warmed up
            if not self.warmed_up:
                await self.warmup_endpoint()
            
            response = await self._make_request(
                'POST',
                '/api/chat',
                {
                    'message': message,
                    'model': model,
                    **kwargs
                }
            )
            
            return response or {'error': 'No response from serverless endpoint'}
            
        except Exception as e:
            logger.error(f"❌ Chat completion failed: {str(e)}")
            return {'error': str(e), 'status': 'error'}
    
    async def stream_chat(self, message: str, model: str = 'peteollama:jamie-fixed', **kwargs):
        """Handle streaming chat through serverless endpoint"""
        try:
            # Ensure endpoint is warmed up
            if not self.warmed_up:
                await self.warmup_endpoint()
            
            response = await self._make_request(
                'POST',
                '/api/chat/stream',
                {
                    'message': message,
                    'model': model,
                    'stream': True,
                    **kwargs
                }
            )
            
            return response or {'error': 'No response from serverless endpoint'}
            
        except Exception as e:
            logger.error(f"❌ Stream chat failed: {str(e)}")
            return {'error': str(e), 'status': 'error'}
    
    async def admin_action(self, action: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle admin actions through serverless endpoint"""
        try:
            response = await self._make_request(
                'POST',
                '/admin/action',
                {
                    'action': action,
                    'data': data or {}
                }
            )
            
            return response or {'error': 'No response from serverless endpoint'}
            
        except Exception as e:
            logger.error(f"❌ Admin action failed: {str(e)}")
            return {'error': str(e), 'status': 'error'}
    
    async def get_models(self) -> Dict[str, Any]:
        """Get available models from serverless endpoint"""
        try:
            response = await self._make_request('GET', '/admin/models')
            return response or {'error': 'No response from serverless endpoint'}
        except Exception as e:
            logger.error(f"❌ Get models failed: {str(e)}")
            return {'error': str(e), 'status': 'error'}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check serverless endpoint health"""
        try:
            response = await self._make_request('GET', '/health')
            return response or {'error': 'No response from serverless endpoint'}
        except Exception as e:
            logger.error(f"❌ Health check failed: {str(e)}")
            return {'error': str(e), 'status': 'error'}
    
    async def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Make HTTP request to serverless endpoint"""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                async with self.session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"❌ GET {url} failed with status {response.status}")
                        return None
            else:
                async with self.session.post(url, json=data) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"❌ POST {url} failed with status {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Request to {url} failed: {str(e)}")
            return None

# Global instance for easy access
serverless_handler = ServerlessHandler()
