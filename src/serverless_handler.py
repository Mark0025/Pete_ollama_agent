#!/usr/bin/env python3
"""
PeteOllama V1 - Serverless-First Handler
Routes all requests to RunPod AI OpenAI-compatible endpoint
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
    """Handles all AI requests through RunPod AI OpenAI-compatible endpoint"""
    
    def __init__(self):
        self.endpoint_id = os.getenv('RUNPOD_SERVERLESS_ENDPOINT')
        self.api_key = os.getenv('RUNPOD_API_KEY')
        # Use RunPod AI native API structure (not OpenAI compatible)
        self.base_url = f"https://api.runpod.ai/v2/{self.endpoint_id}"
        self.warmed_up = False
        self.session: Optional[aiohttp.ClientSession] = None
        
        if not self.endpoint_id:
            raise ValueError("RUNPOD_SERVERLESS_ENDPOINT not configured")
        if not self.api_key:
            raise ValueError("RUNPOD_API_KEY not configured")
            
        logger.info(f"🚀 Serverless handler initialized for RunPod AI native API: {self.base_url}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        # Configure timeout settings for better reliability
        timeout = aiohttp.ClientTimeout(
            total=60,  # 60 seconds total timeout
            connect=10,  # 10 seconds connection timeout
            sock_read=30  # 30 seconds socket read timeout
        )
        
        # Configure SSL context for RunPod AI API
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        self.session = aiohttp.ClientSession(
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            },
            timeout=timeout,
            connector=connector
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
            
            # Send a simple test request to warm up the container
            warmup_response = await self._make_request(
                'POST',
                '/run',
                {
                    'input': {
                        'prompt': 'Warmup test',
                        'model': 'peteollama:jamie-fixed'
                    }
                }
            )
            
            if warmup_response and warmup_response.get('id'):
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
        """Handle chat completion through native RunPod API"""
        try:
            # Ensure endpoint is warmed up
            if not self.warmed_up:
                await self.warmup_endpoint()
            
            # Submit job to RunPod AI native API
            job_response = await self._make_request(
                'POST',
                '/run',
                {
                    'input': {
                        'prompt': message,
                        'model': model,
                        **kwargs
                    }
                }
            )
            
            if not job_response or 'id' not in job_response:
                return {'error': 'Failed to submit job to RunPod AI'}
            
            job_id = job_response['id']
            logger.info(f"🚀 Job submitted: {job_id}")
            
            # Poll for job completion
            result = await self._poll_job_completion(job_id)
            return result
            
        except Exception as e:
            logger.error(f"❌ Chat completion failed: {str(e)}")
            return {'error': str(e), 'status': 'error'}
    
    async def stream_chat(self, message: str, model: str = 'peteollama:jamie-fixed', **kwargs) -> Dict[str, Any]:
        """Handle streaming chat through native RunPod API with streaming support"""
        try:
            # Ensure endpoint is warmed up
            if not self.warmed_up:
                await self.warmup_endpoint()
            
            # Submit streaming job to RunPod AI native API
            job_response = await self._make_request(
                'POST',
                '/run',
                {
                    'input': {
                        'prompt': message,
                        'model': model,
                        'stream': True,  # Enable streaming
                        **kwargs
                    }
                }
            )
            
            if not job_response or 'id' not in job_response:
                return {'error': 'Failed to submit streaming job to RunPod AI'}
            
            job_id = job_response['id']
            logger.info(f"🚀 Streaming job submitted: {job_id}")
            
            # For streaming, we need to handle the response differently
            # RunPod streaming jobs return chunks as they're generated
            result = await self._poll_streaming_job(job_id)
            return result
            
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
        """Get available models from OpenAI-compatible endpoint"""
        try:
            response = await self._make_request('GET', '/models')
            return response or {'error': 'No response from serverless endpoint'}
        except Exception as e:
            logger.error(f"❌ Get models failed: {str(e)}")
            return {'error': str(e), 'status': 'error'}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check serverless endpoint health using health endpoint"""
        try:
            # Use the health endpoint that we know works
            response = await self._make_request('GET', '/health')
            if response and response.get('workers'):
                workers = response.get('workers', {})
                healthy_workers = workers.get('ready', 0) + workers.get('idle', 0)
                return {
                    'status': 'healthy' if healthy_workers > 0 else 'unhealthy',
                    'workers': workers,
                    'healthy_workers': healthy_workers
                }
            else:
                return {'status': 'unhealthy', 'error': 'No worker information'}
        except Exception as e:
            logger.error(f"❌ Health check failed: {str(e)}")
            return {'error': str(e), 'status': 'error'}
    
    async def check_endpoint_accessibility(self) -> Dict[str, Any]:
        """Check if the RunPod AI endpoint is accessible and provide diagnostics"""
        try:
            import socket
            import ssl
            
            # Parse the hostname from the URL
            hostname = "api.runpod.ai"  # RunPod AI API hostname
            
            # Check DNS resolution
            try:
                ip_address = socket.gethostbyname(hostname)
                dns_status = "✅ Resolved"
            except socket.gaierror:
                ip_address = "❌ Failed"
                dns_status = "❌ DNS resolution failed"
            
            # Check port connectivity (HTTPS = 443)
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((hostname, 443))
                sock.close()
                port_status = "✅ Open" if result == 0 else "❌ Closed"
            except Exception as e:
                port_status = f"❌ Error: {str(e)}"
            
            # Try a simple HTTP request to the models endpoint
            try:
                import aiohttp
                timeout = aiohttp.ClientTimeout(total=10, connect=5)
                async with aiohttp.ClientSession(timeout=timeout) as test_session:
                    async with test_session.get(f"{self.base_url}/models") as response:
                        http_status = f"✅ HTTP {response.status}"
            except Exception as e:
                http_status = f"❌ HTTP error: {str(e)}"
            
            return {
                "endpoint": self.base_url,
                "hostname": hostname,
                "dns_resolution": dns_status,
                "ip_address": ip_address,
                "port_443": port_status,
                "http_health": http_status,
                "timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            return {
                "error": f"Diagnostic failed: {str(e)}",
                "endpoint": self.base_url
            }
    
    async def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Make HTTP request to serverless endpoint with improved error handling"""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        url = f"{self.base_url}{endpoint}"
        max_retries = 2
        retry_delay = 1.0
        
        for attempt in range(max_retries + 1):
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
                            
            except asyncio.TimeoutError:
                logger.error(f"⏰ Request to {url} timed out (attempt {attempt + 1}/{max_retries + 1})")
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                return None
            except aiohttp.ClientConnectorError as e:
                logger.error(f"🔌 Connection error to {url}: {str(e)} (attempt {attempt + 1}/{max_retries + 1})")
                if attempt < max_retries:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                return None
            except Exception as e:
                logger.error(f"❌ Request to {url} failed: {str(e)}")
                return None
        
        return None

    async def _poll_job_completion(self, job_id: str, max_wait_time: int = 60) -> Dict[str, Any]:
        """Poll for job completion on RunPod AI native API"""
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < max_wait_time:
            try:
                # Check job status using the job ID
                status_response = await self._make_request('GET', f'/status/{job_id}')
                
                if not status_response:
                    await asyncio.sleep(1)
                    continue
                
                status = status_response.get('status')
                
                if status == 'COMPLETED':
                    # Job completed successfully
                    output = status_response.get('output', {})
                    logger.info(f"✅ Job {job_id} completed successfully")
                    return {
                        'status': 'success',
                        'response': output.get('response', output.get('text', '')),
                        'model': output.get('model', ''),
                        'job_id': job_id,
                        'raw_output': output
                    }
                
                elif status == 'FAILED':
                    # Job failed
                    error = status_response.get('error', 'Unknown error')
                    logger.error(f"❌ Job {job_id} failed: {error}")
                    return {
                        'status': 'error',
                        'error': error,
                        'job_id': job_id
                    }
                
                elif status in ['IN_QUEUE', 'IN_PROGRESS']:
                    # Job still running, wait and retry
                    await asyncio.sleep(1)
                    continue
                
                else:
                    # Unknown status
                    logger.warning(f"⚠️ Job {job_id} has unknown status: {status}")
                    await asyncio.sleep(1)
                    continue
                    
            except Exception as e:
                logger.error(f"❌ Error polling job {job_id}: {str(e)}")
                await asyncio.sleep(1)
                continue
        
        # Timeout
        logger.error(f"⏰ Job {job_id} timed out after {max_wait_time} seconds")
        return {
            'status': 'error',
            'error': f'Job timed out after {max_wait_time} seconds',
            'job_id': job_id
        }

    async def _poll_streaming_job(self, job_id: str, max_wait_time: int = 60) -> Dict[str, Any]:
        """Poll for streaming job completion with partial results"""
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < max_wait_time:
            try:
                # Check job status
                status_response = await self._make_request('GET', f'/status/{job_id}')
                
                if not status_response:
                    await asyncio.sleep(0.5)  # Faster polling for streaming
                    continue
                
                status = status_response.get('status')
                
                if status == 'COMPLETED':
                    # Job completed successfully
                    output = status_response.get('output', {})
                    logger.info(f"✅ Streaming job {job_id} completed successfully")
                    return {
                        'status': 'success',
                        'response': output.get('response', output.get('text', '')),
                        'model': output.get('model', ''),
                        'job_id': job_id,
                        'raw_output': output,
                        'streaming': True
                    }
                
                elif status == 'FAILED':
                    # Job failed
                    error = status_response.get('error', 'Unknown error')
                    logger.error(f"❌ Streaming job {job_id} failed: {error}")
                    return {
                        'status': 'error',
                        'error': error,
                        'job_id': job_id
                    }
                
                elif status in ['IN_QUEUE', 'IN_PROGRESS']:
                    # Job still running, check for partial output
                    if 'output' in status_response and status_response['output']:
                        partial_output = status_response['output']
                        # Return partial result for streaming
                        return {
                            'status': 'partial',
                            'response': partial_output.get('response', partial_output.get('text', '')),
                            'job_id': job_id,
                            'partial': True,
                            'streaming': True
                        }
                    
                    # No partial output yet, wait and retry
                    await asyncio.sleep(0.5)  # Faster polling for streaming
                    continue
                
                else:
                    # Unknown status
                    logger.warning(f"⚠️ Streaming job {job_id} has unknown status: {status}")
                    await asyncio.sleep(0.5)
                    continue
                    
            except Exception as e:
                logger.error(f"❌ Error polling streaming job {job_id}: {str(e)}")
                await asyncio.sleep(0.5)
                continue
        
        # Timeout
        logger.error(f"⏰ Streaming job {job_id} timed out after {max_wait_time} seconds")
        return {
            'status': 'error',
            'error': f'Streaming job timed out after {max_wait_time} seconds',
            'job_id': job_id
        }

# Global instance for easy access
serverless_handler = ServerlessHandler()
