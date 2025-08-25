"""
PeteOllama V1 - AI Model Manager
================================

Manages interactions with the Ollama AI model for property management responses.
"""

import requests
import json
import os
from typing import Dict, List, Optional, Any, Iterable
from pathlib import Path
import sys

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ ModelManager: Environment variables loaded")
except ImportError:
    print("⚠️ ModelManager: dotenv not available")
except Exception as e:
    print(f"⚠️ ModelManager: Error loading environment: {e}")

# Import RunPod module (but don't initialize yet)
try:
    import runpod
    RUNPOD_AVAILABLE = True
    print("✅ RunPod module imported successfully")
except ImportError:
    print("⚠️ RunPod module not available")
    RUNPOD_AVAILABLE = False

# Import OpenRouter handler for provider switching
try:
    from ..openrouter_handler import OpenRouterHandler
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from openrouter_handler import OpenRouterHandler

# Import conversation similarity system for intelligent instant responses
try:
    from analytics.conversation_similarity import ConversationSimilarityAnalyzer
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from analytics.conversation_similarity import ConversationSimilarityAnalyzer

# Import response cache for fallback caching
try:
    from ai.response_cache import get_instant_response, response_cache
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from response_cache import get_instant_response, response_cache

class ModelManager:
    """Manages AI model interactions and training"""
    
    def __init__(self, system_config_instance: object = None):
        """Initialize model manager with optional system config instance for real-time updates"""
        # Store system config instance for real-time updates
        self.system_config = system_config_instance
        
        # Ollama server configuration
        self.ollama_host = os.getenv('OLLAMA_HOST', 'localhost:11434')
        self.base_url = f"http://{self.ollama_host}"

        # Load model settings
        self.settings_file = Path("config/model_settings.json")
        self.default_model = self._load_default_model()
        
        # Base and fine-tuned model names from system configuration
        try:
            if self.system_config:
                # Use provided instance for real-time updates
                global_settings = self.system_config.get_global_settings()
                self.model_name = global_settings['ollama_model']
                self.custom_model_name = global_settings['jamie_custom_model']
                self.max_tokens = global_settings['max_tokens']
                print(f"✅ Loaded model settings from provided system config")
            else:
                # Fallback to module import
                from src.config.system_config import system_config
                global_settings = system_config.get_global_settings()
                self.model_name = global_settings['ollama_model']
                self.custom_model_name = global_settings['jamie_custom_model']
                self.max_tokens = global_settings['max_tokens']
                print(f"✅ Loaded model settings from module system config")
        except Exception as e:
            print(f"⚠️ Failed to load system config, using fallback: {e}")
            self.model_name = os.getenv('OLLAMA_BASE_MODEL', 'mistral:7b-instruct-q4_K_M')
            self.custom_model_name = os.getenv('OLLAMA_CUSTOM_MODEL', self.default_model or 'peteollama:property-manager')
            self.max_tokens = int(os.getenv('MAX_TOKENS', '4096'))
        
        # Model configuration
        self.temperature = 0.7
        self.context_window = 128000
        
        # Initialize conversation similarity analyzer for intelligent responses
        # Get similarity threshold from system configuration
        try:
            if self.system_config:
                # Use provided instance for real-time updates
                self.similarity_threshold = self.system_config.get_caching_config().threshold
                print(f"✅ Loaded similarity threshold from provided system config: {self.similarity_threshold}")
            else:
                # Fallback to module import
                from src.config.system_config import system_config
                self.similarity_threshold = system_config.get_caching_config().threshold
                print(f"✅ Loaded similarity threshold from module system config: {self.similarity_threshold}")
        except Exception as e:
            print(f"⚠️ Failed to load system config, using fallback: {e}")
            self.similarity_threshold = float(os.getenv('SIMILARITY_THRESHOLD', '0.75'))
        self.similarity_analyzer = None  # Lazy load to avoid startup delays
        
        # Initialize provider handlers
        self.openrouter_handler = None  # Lazy load
        self._current_provider = None  # Cache for current provider
        
        # RunPod client (lazy initialized)
        self._runpod_endpoint = None
    
    def _get_similarity_analyzer(self):
        """Lazy load the conversation similarity analyzer"""
        if self.similarity_analyzer is None:
            try:
                print("🧠 Loading conversation similarity analyzer...")
                self.similarity_analyzer = ConversationSimilarityAnalyzer()
                print(f"✅ Loaded {len(self.similarity_analyzer.conversation_samples)} conversation samples")
            except Exception as e:
                print(f"⚠️ Failed to load similarity analyzer: {e}")
                self.similarity_analyzer = None
        return self.similarity_analyzer
    
    def _get_runpod_endpoint(self):
        """Lazy load the RunPod endpoint with fresh environment variables"""
        if self._runpod_endpoint is None and RUNPOD_AVAILABLE:
            try:
                # Get fresh environment variables
                runpod_api_key = os.getenv('RUNPOD_API_KEY')
                runpod_endpoint_id = os.getenv('RUNPOD_SERVERLESS_ENDPOINT')
                
                print(f"🔍 DEBUG - Fresh RUNPOD_API_KEY: {runpod_api_key[:10] if runpod_api_key else 'None'}...")
                print(f"🔍 DEBUG - Fresh RUNPOD_ENDPOINT_ID: {runpod_endpoint_id}")
                
                if not runpod_api_key:
                    print("❌ RUNPOD_API_KEY not found in environment")
                    return None
                elif not runpod_endpoint_id:
                    print("❌ RUNPOD_SERVERLESS_ENDPOINT not found in environment")
                    return None
                else:
                    # Set the API key BEFORE creating endpoint
                    runpod.api_key = runpod_api_key
                    print(f"✅ RunPod API key set: {runpod_api_key[:10]}...")
                    
                    # Create endpoint with error handling
                    self._runpod_endpoint = runpod.Endpoint(runpod_endpoint_id)
                    print(f"✅ RunPod endpoint object created: {runpod_endpoint_id}")
                    
                    # Test endpoint availability with a simple health check
                    try:
                        print(f"🔍 Testing endpoint availability...")
                        # Try to get endpoint status or health
                        health_result = self._runpod_endpoint.health()
                        print(f"✅ Endpoint health check passed: {health_result}")
                    except Exception as health_error:
                        print(f"⚠️ Endpoint health check failed: {health_error}")
                        print(f"ℹ️ This might be normal - endpoint may not support health checks")
                    
            except Exception as e:
                print(f"⚠️ RunPod client initialization error: {e}")
                print(f"ℹ️ This could mean the endpoint doesn't exist or isn't accessible")
                return None
        
        return self._runpod_endpoint
    
    def _runpod_stream_completion(self, runpod_endpoint, runpod_input: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get complete response from RunPod using streaming to avoid truncation
        
        Follows official RunPod docs pattern:
        1. Submit async job to /run endpoint to get job ID
        2. Use /stream/{job_id} endpoint for incremental streamed results
        3. Poll /status/{job_id} for final completion if needed
        """
        try:
            from utils.logger import logger
            import time
            
            # Step 1: Submit async job to /run endpoint
            logger.info(f"🚀 Submitting async job to RunPod /run endpoint...")
            job_response = runpod_endpoint.run(runpod_input)
            
            if not job_response:
                logger.error("❌ No response from RunPod /run endpoint")
                return None
            
            # Extract job ID from response - RunPod Job object has job_id attribute
            job_id = None
            if isinstance(job_response, dict):
                job_id = job_response.get('id')
            elif hasattr(job_response, 'job_id'):
                job_id = job_response.job_id
                logger.info(f"🎉 Successfully extracted job_id: {job_id}")
            elif hasattr(job_response, 'id'):
                job_id = job_response.id
            elif isinstance(job_response, str):
                job_id = job_response  # Sometimes job ID is returned directly
            else:
                logger.warning(f"⚠️ Unknown job response format: {type(job_response)}")
            
            if not job_id:
                logger.error(f"❌ No job ID found in response: {job_response}")
                return None
                
            logger.info(f"✅ Job submitted successfully - Job ID: {job_id}")
            
            # Step 2: Stream results from /stream/{job_id} endpoint
            complete_response = ""
            updates_received = 0
            max_stream_time = 60  # 60 seconds max for streaming
            stream_start = time.time()
            last_update_length = 0
            
            try:
                logger.info(f"📡 Starting stream from job.stream()...")
                
                for stream_update in job_response.stream():
                    # Check timeout
                    if (time.time() - stream_start) > max_stream_time:
                        logger.warning(f"⏰ Stream timeout after {max_stream_time}s, checking final status...")
                        break
                    
                    if not stream_update:
                        continue
                    
                    updates_received += 1
                    logger.debug(f"📥 Stream update #{updates_received}: {type(stream_update)} - {str(stream_update)[:200]}")
                    
                    # Parse stream update based on RunPod response format
                    current_text = ""
                    job_status = None
                    
                    if isinstance(stream_update, dict):
                        # Check for job status
                        job_status = stream_update.get('status')
                        
                        # Extract text from various possible locations
                        if 'output' in stream_update:
                            output = stream_update['output']
                            if isinstance(output, dict) and 'text' in output:
                                text_data = output['text']
                                current_text = text_data[0] if isinstance(text_data, list) else text_data
                            elif isinstance(output, str):
                                current_text = output
                        elif 'text' in stream_update:
                            text_data = stream_update['text']
                            current_text = text_data[0] if isinstance(text_data, list) else text_data
                    elif isinstance(stream_update, str):
                        current_text = stream_update
                    
                    # Update complete response by accumulating new text
                    if current_text:
                        # For RunPod streaming, each update contains the next token to append
                        if isinstance(current_text, str) and current_text not in complete_response:
                            # Check if this is a new token to append
                            if len(current_text.strip()) > 0:
                                complete_response += current_text
                                logger.debug(f"🔤 Accumulated token: '{current_text}' - Total length: {len(complete_response)}")
                        
                        if updates_received % 5 == 0:  # Log every 5 updates
                            logger.info(f"📈 Update #{updates_received}: {len(complete_response)} chars")
                    
                    # Check for completion status
                    if job_status == 'COMPLETED':
                        logger.info(f"✅ Job completed via stream - Final length: {len(complete_response)} chars")
                        break
                    elif job_status == 'FAILED':
                        error_msg = stream_update.get('error', 'Unknown error')
                        logger.error(f"❌ Job failed via stream: {error_msg}")
                        return None
                        
                logger.info(f"📊 Streaming finished - Updates: {updates_received}, Response length: {len(complete_response)}")
                
            except Exception as stream_error:
                logger.warning(f"⚠️ Streaming failed: {stream_error}")
                logger.info(f"🔄 Falling back to status polling...")
            
            # Step 3: Final status check if we don't have a complete response
            if not complete_response or len(complete_response.strip()) == 0:
                logger.info(f"🔍 Checking final job status via /status/{job_id}...")
                
                max_status_checks = 30  # 30 seconds max for status polling
                status_check_start = time.time()
                
                while (time.time() - status_check_start) < max_status_checks:
                    try:
                        status_response = job_response.status()
                        
                        if status_response:
                            job_status = status_response.get('status')
                            logger.debug(f"📋 Status check: {job_status}")
                            
                            if job_status == 'COMPLETED':
                                # Extract final result
                                output = status_response.get('output', {})
                                if 'text' in output:
                                    text_data = output['text']
                                    complete_response = text_data[0] if isinstance(text_data, list) else text_data
                                    logger.info(f"✅ Final result via status: {len(complete_response)} chars")
                                    break
                                else:
                                    logger.warning(f"⚠️ Status shows COMPLETED but no text in output: {output}")
                                    
                            elif job_status == 'FAILED':
                                error_msg = status_response.get('error', 'Unknown error')
                                logger.error(f"❌ Job failed via status: {error_msg}")
                                return None
                                
                            elif job_status in ['IN_QUEUE', 'IN_PROGRESS']:
                                logger.debug(f"⏳ Job still running: {job_status}")
                                
                        time.sleep(1)  # Wait 1 second between status checks
                        
                    except Exception as status_error:
                        logger.warning(f"⚠️ Status check failed: {status_error}")
                        time.sleep(1)
            
            # Return result if we have a response
            if complete_response and len(complete_response.strip()) > 0:
                response_length = len(complete_response)
                logger.info(f"🎉 RunPod streaming SUCCESS - Length: {response_length} chars")
                logger.info(f"📄 Preview: {complete_response[:150]}{'...' if response_length > 150 else ''}")
                
                return {
                    "status": "success",
                    "response": complete_response.strip(),
                    "model": runpod_input.get('model', 'unknown'),
                    "provider": "runpod_streaming",
                    "input_tokens": 0,  # RunPod doesn't always provide these
                    "output_tokens": len(complete_response.split()),  # Approximate
                    "job_id": job_id,
                    "updates_received": updates_received
                }
            else:
                logger.error(f"❌ No valid response after streaming and status checks")
                return None
                
        except Exception as e:
            from utils.logger import logger
            logger.error(f"❌ RunPod streaming error: {str(e)}")
            logger.error(f"📍 Error type: {type(e).__name__}")
            return None
    
    def _get_openrouter_handler(self):
        """Lazy load the OpenRouter handler"""
        if self.openrouter_handler is None:
            try:
                print("🌐 Loading OpenRouter handler...")
                self.openrouter_handler = OpenRouterHandler()
                print("✅ OpenRouter handler loaded")
            except Exception as e:
                print(f"⚠️ Failed to load OpenRouter handler: {e}")
                self.openrouter_handler = None
        return self.openrouter_handler
    
    def _get_current_provider(self) -> str:
        """Get current provider from system configuration"""
        try:
            if self.system_config:
                # Use provided instance for real-time updates
                provider = self.system_config.config.default_provider
                print(f"🔧 Current provider from provided system config: {provider}")
                return provider
            else:
                # Fallback to module import
                from src.config.system_config import system_config
                provider = system_config.config.default_provider
                print(f"🔧 Current provider from module system config: {provider}")
                return provider
        except Exception as e:
            print(f"⚠️ Error getting current provider from system config: {e}")
            try:
                # Fallback to old model settings
                from src.config.model_settings import model_settings
                settings = model_settings.get_provider_settings()
                provider = settings.get('default_provider', 'ollama')
                print(f"🔧 Fallback provider from model settings: {provider}")
                return provider
            except Exception as e2:
                print(f"⚠️ Fallback failed: {e2}, defaulting to ollama")
                return 'ollama'
    
    def _determine_provider_from_model(self, model_name: str) -> str:
        """Determine which provider should handle this model based on model name patterns"""
        if not model_name:
            return self._get_current_provider()
        
        # Check if this is an Ollama model (local models)
        if ':' in model_name and not model_name.startswith(('openai/', 'anthropic/', 'meta/')):
            # Check if Ollama is available and has this model
            try:
                from src.vapi.services.provider_service import ProviderService
                provider_service = ProviderService()
                ollama_models = provider_service._get_actual_ollama_models()
                if ollama_models and model_name in ollama_models:
                    return 'ollama'
            except Exception as e:
                print(f"⚠️ Could not check Ollama availability: {e}")
        
        # Check if this is a RunPod model (serverless models)
        if model_name in ['llama3:latest', 'mistral:7b-instruct', 'llama3:8b', 'mixtral:latest']:
            # For RunPod models, assume they're available since we can't do async calls here
            # The actual availability check happens in the routing logic
            return 'runpod'
        
        # Check if this is an OpenRouter model
        if model_name.startswith(('openai/', 'anthropic/', 'meta/', 'google/')):
            return 'openrouter'
        
        # Default to OpenRouter for unknown models
        return 'openrouter'
    
    def _route_to_provider(self, prompt: str, model_name: str = None, **kwargs) -> Dict[str, Any]:
        """Route request to appropriate provider based on model name and availability"""
        # Determine provider from model name instead of system config
        provider = self._determine_provider_from_model(model_name)
        
        # Enhanced logging to show actual routing decision
        from utils.logger import logger
        logger.info(f"🚀 ROUTING REQUEST - Provider: {provider}, Requested Model: {model_name}")
        logger.info(f"📝 Prompt length: {len(prompt)} chars")
        
        if provider == 'openrouter':
            logger.info(f"🌐 ROUTING TO OPENROUTER")
            logger.info(f"🎯 Requested model: {model_name}")
            logger.info(f"📝 Prompt length: {len(prompt)} chars")
            
            handler = self._get_openrouter_handler()
            if handler and handler.available:
                # Map Ollama model names to OpenRouter models
                openrouter_model = self._map_to_openrouter_model(model_name)
                logger.info(f"🔄 Mapped to OpenRouter model: {openrouter_model}")
                
                result = handler.chat_completion(prompt, model=openrouter_model, **kwargs)
                
                # Log the response source and metadata
                if result and 'response_metadata' in result:
                    metadata = result['response_metadata']
                    logger.info(f"✅ OpenRouter response completed")
                    logger.info(f"📊 Source: {metadata.get('source', 'unknown')}")
                    logger.info(f"📏 Length: {metadata.get('length', 'unknown')} chars")
                    logger.info(f"✂️ Truncated: {metadata.get('is_truncated', 'unknown')}")
                elif result and 'response' in result:
                    logger.info(f"✅ OpenRouter response completed (no metadata)")
                    logger.info(f"📏 Response length: {len(result['response'])} chars")
                
                return result
            else:
                logger.warning(f"⚠️ OpenRouter not available, falling back to RunPod")
                # Fallback to our RunPod client instead of old pete_handler
                runpod_endpoint = self._get_runpod_endpoint()
                if runpod_endpoint:
                    try:
                        logger.info(f"🚀 OpenRouter fallback to RunPod client for model: {model_name}")
                        
                        runpod_input = {
                            "prompt": prompt,
                            "model": model_name,
                            "max_tokens": kwargs.get('max_tokens', 2048),
                            "temperature": kwargs.get('temperature', 0.7)
                        }
                        
                        if 'stop' in kwargs:
                            runpod_input['stop'] = kwargs['stop']
                        
                        result = runpod_endpoint.run_sync(runpod_input, timeout=60)
                        
                        if result and 'text' in result:
                            response_text = result['text'][0] if isinstance(result['text'], list) else result['text']
                            logger.info(f"✅ RunPod OpenRouter fallback successful - Length: {len(response_text)} chars")
                            
                            return {
                                "status": "success",
                                "response": response_text,
                                "model": model_name,
                                "provider": "runpod_openrouter_fallback",
                                "input_tokens": result.get('input_tokens', 0),
                                "output_tokens": result.get('output_tokens', 0)
                            }
                        else:
                            logger.error(f"❌ RunPod OpenRouter fallback response invalid: {result}")
                            return {"status": "error", "error": "Invalid fallback response from RunPod"}
                            
                    except Exception as e:
                        logger.error(f"❌ RunPod OpenRouter fallback failed: {e}")
                        return {"status": "error", "error": f"RunPod OpenRouter fallback error: {str(e)}"}
                else:
                    logger.error("❌ RunPod endpoint not available for OpenRouter fallback")
                    return {"status": "error", "error": "RunPod not configured for fallback"}
        
        elif provider == 'ollama':
            logger.info(f"🏠 ROUTING TO OLLAMA - Model: {model_name}")
            # Try local Ollama first
            try:
                result = self._ollama_completion(prompt, model_name, **kwargs)
                if result.get('status') == 'success':
                    logger.info(f"✅ Ollama response completed - Model: {result.get('model', 'unknown')}, Provider: {result.get('model', 'unknown')}, Provider: {result.get('provider', 'ollama')}")
                    return result
            except Exception as e:
                logger.warning(f"⚠️ Ollama failed: {e}, falling back to RunPod")
            
            # Fallback to RunPod if Ollama fails
            logger.info(f"🔄 FALLBACK TO RUNPOD - Original model: {model_name}")
            
            # Use official RunPod client for fallback
            runpod_endpoint = self._get_runpod_endpoint()
            if runpod_endpoint:
                try:
                    logger.info(f"🚀 Fallback to RunPod client for model: {model_name}")
                    
                    runpod_input = {
                        "prompt": prompt,
                        "model": model_name,
                        "max_tokens": kwargs.get('max_tokens', 2048),
                        "temperature": kwargs.get('temperature', 0.7)
                    }
                    
                    if 'stop' in kwargs:
                        runpod_input['stop'] = kwargs['stop']
                    
                    result = runpod_endpoint.run_sync(runpod_input, timeout=60)
                    
                    if result and 'text' in result:
                        response_text = result['text'][0] if isinstance(result['text'], list) else result['text']
                        logger.info(f"✅ RunPod fallback successful - Length: {len(response_text)} chars")
                        
                        return {
                            "status": "success",
                            "response": response_text,
                            "model": model_name,
                            "provider": "runpod_fallback",
                            "input_tokens": result.get('input_tokens', 0),
                            "output_tokens": result.get('output_tokens', 0)
                        }
                    else:
                        logger.error(f"❌ RunPod fallback response invalid: {result}")
                        return {"status": "error", "error": "Invalid fallback response from RunPod"}
                        
                except Exception as e:
                    logger.error(f"❌ RunPod fallback failed: {e}")
                    return {"status": "error", "error": f"RunPod fallback error: {str(e)}"}
            else:
                logger.error("❌ RunPod endpoint not available for fallback")
                return {"status": "error", "error": "RunPod not configured"}
        
        else:  # runpod or default
            logger.info(f"☁️ ROUTING TO RUNPOD - Model: {model_name}")
            
            # Use official RunPod client
            runpod_endpoint = self._get_runpod_endpoint()
            if runpod_endpoint:
                try:
                    logger.info(f"🚀 Using official RunPod client for model: {model_name}")
                    
                    # Debug: Check current API key
                    current_api_key = runpod.api_key
                    logger.info(f"🔍 DEBUG - Current RunPod API key: {current_api_key[:10] if current_api_key else 'None'}...")
                    
                    # Prepare the input for RunPod
                    runpod_input = {
                        "prompt": prompt,
                        "model": model_name,
                        "max_tokens": kwargs.get('max_tokens', 2048),
                        "temperature": kwargs.get('temperature', 0.7)
                    }
                    
                    # Add stop sequences if provided
                    if 'stop' in kwargs:
                        runpod_input['stop'] = kwargs['stop']
                    
                    logger.info(f"🔍 DEBUG - RunPod input: {runpod_input}")
                    logger.info(f"🔍 DEBUG - About to call runpod_endpoint.run_sync()")
                    
                    # Try streaming first for complete responses, fallback to sync if needed
                    logger.info(f"📡 Attempting RunPod streaming for complete response...")
                    try:
                        streaming_result = self._runpod_stream_completion(runpod_endpoint, runpod_input)
                        if streaming_result and streaming_result.get('status') == 'success':
                            logger.info(f"✅ RunPod streaming successful - Length: {len(streaming_result.get('response', ''))} chars")
                            return streaming_result
                        else:
                            logger.warning(f"⚠️ RunPod streaming failed or returned no result")
                    except Exception as stream_error:
                        logger.warning(f"⚠️ RunPod streaming exception: {stream_error}")
                    
                    # Fallback to sync method if streaming fails
                    logger.info(f"🔄 Falling back to RunPod sync method")
                    try:
                        result = runpod_endpoint.run_sync(runpod_input, timeout=60)
                        
                        if result and 'text' in result:
                            response_text = result['text'][0] if isinstance(result['text'], list) else result['text']
                            logger.info(f"✅ RunPod sync response successful - Length: {len(response_text)} chars")
                            
                            return {
                                "status": "success",
                                "response": response_text,
                                "model": model_name,
                                "provider": "runpod_sync",
                                "input_tokens": result.get('input_tokens', 0),
                                "output_tokens": result.get('output_tokens', 0)
                            }
                        else:
                            logger.error(f"❌ RunPod sync response invalid: {result}")
                            return {"status": "error", "error": "Invalid response from RunPod sync"}
                    except Exception as sync_error:
                        logger.error(f"❌ RunPod sync also failed: {sync_error}")
                        return {"status": "error", "error": f"Both streaming and sync failed: {sync_error}"}
                        
                except Exception as e:
                    logger.error(f"❌ RunPod request failed: {e}")
                    return {"status": "error", "error": f"RunPod error: {str(e)}"}
            else:
                logger.error("❌ RunPod endpoint not available")
                return {"status": "error", "error": "RunPod not configured"}
    
    def _map_to_openrouter_model(self, ollama_model: str) -> str:
        """Map Ollama model names to OpenRouter model names"""
        if not ollama_model:
            return "openai/gpt-3.5-turbo"  # Use working model as default
        
        # Map to working OpenRouter models
        model_mapping = {
            "llama3:latest": "openai/gpt-3.5-turbo",
            "llama3:8b": "openai/gpt-3.5-turbo",
            "mistral:latest": "anthropic/claude-3-haiku",
            "mixtral:latest": "openai/gpt-4o-mini",
        }
        
        # Default to working models if no mapping found
        working_models = ["openai/gpt-3.5-turbo", "openai/gpt-4o-mini", "anthropic/claude-3-haiku"]
        return model_mapping.get(ollama_model, working_models[0])
    
    def _ollama_completion(self, prompt: str, model_name: str = None, **kwargs) -> Dict[str, Any]:
        """Direct Ollama API completion"""
        try:
            model_to_use = model_name or self.model_name
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model_to_use,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": kwargs.get('temperature', self.temperature),
                        "num_predict": kwargs.get('max_tokens', self.max_tokens)
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "response": data.get('response', ''),
                    "model": model_to_use,
                    "provider": "ollama"
                }
            else:
                return {"status": "error", "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _load_default_model(self) -> Optional[str]:
        """Load the default model from settings file"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                    return data.get('default_model')
        except Exception as e:
            print(f"Error loading default model from settings: {e}")
        return None
    
    def is_available(self) -> bool:
        """Check if Ollama service is available or if we're in serverless mode"""
        try:
            # First check if RunPod proxy is available
            try:
                # If RunPod is available, we have RunPod serverless capability
                if RUNPOD_AVAILABLE:
                    print("🚀 Serverless mode detected via RunPod")
                    return True
            except Exception as proxy_error:
                print(f"RunPod proxy check failed: {proxy_error}")
                
            # Fallback to checking Ollama service
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Model availability check failed: {e}")
            # Still return True if we have RunPod available
            return RUNPOD_AVAILABLE
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                return response.json().get('models', [])
            return []
        except Exception as e:
            print(f"Error listing models: {e}")
            return []

    def train_property_manager(self) -> bool:
        """Train or update the custom property-manager model using conversations in pete.db."""
        try:
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from database.pete_db_manager import PeteDBManager
            db = PeteDBManager()
            examples = db.get_training_examples()
            if not examples:
                print("No training examples found in DB")
                return False
            return self.create_custom_model(examples)
        except Exception as e:
            print(f"Error training property manager model: {e}")
            return False
    
    def is_model_available(self, model_name: str = None) -> bool:
        """Check if specific model is available"""
        if model_name is None:
            model_name = self.custom_model_name
        
        models = self.list_models()
        model_names = [model['name'] for model in models]
        return model_name in model_names
    
    def pull_model(self, model_name: str = None) -> bool:
        """Download/pull a model"""
        if model_name is None:
            model_name = self.custom_model_name
        
        try:
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                stream=True
            )
            
            # Stream the response for progress updates
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if 'status' in data:
                        print(f"Model pull: {data['status']}")
                        if data.get('completed'):
                            return True
            
            return response.status_code == 200
        
        except Exception as e:
            print(f"Error pulling model {model_name}: {e}")
            return False
    
    def generate_response(self, prompt: str, context: str = None, model_name: str | None = None) -> str:
        """Generate AI response using intelligent similarity matching + RunPod serverless fallback"""
        try:
            import time
            
            # STEP 1: Try conversation similarity matching for instant responses
            similarity_start = time.time()
            
            analyzer = self._get_similarity_analyzer()
            if analyzer:
                try:
                    similarity_result = analyzer.calculate_similarity(prompt, context or '')
                    similarity_time = (time.time() - similarity_start) * 1000
                    
                    # Check if similarity is high enough for instant response
                    if similarity_result.similarity_score >= self.similarity_threshold and similarity_result.best_match:
                        response = similarity_result.best_match.agent_response
                        response_length = len(response)
                        
                        from utils.logger import logger
                        logger.info(f"🎯 CONVERSATION SIMILARITY HIT - Using cached response")
                        logger.info(f"📊 Similarity score: {similarity_result.similarity_score:.3f}")
                        logger.info(f"⏱️ Response time: {similarity_time:.0f}ms (instant)")
                        logger.info(f"📏 Response length: {response_length} chars")
                        logger.info(f"📄 Response preview: {response[:100]}{'...' if response_length > 100 else ''}")
                        logger.info(f"🔑 Source: conversation_similarity_analyzer")
                        
                        # Add to fallback cache for future use
                        try:
                            response_cache.add_response_to_cache(prompt, response)
                        except Exception as cache_error:
                            logger.warning(f"⚠️ Cache update failed: {cache_error}")
                        
                        return response
                    else:
                        print(f"📊 Similarity too low ({similarity_time:.0f}ms, {similarity_result.similarity_score:.3f} < {self.similarity_threshold})")
                        
                except Exception as sim_error:
                    similarity_time = (time.time() - similarity_start) * 1000
                    print(f"⚠️ Similarity analysis failed ({similarity_time:.0f}ms): {sim_error}")
            else:
                print("🔧 Similarity analyzer not available, checking fallback cache...")
            
            # STEP 2: Try fallback cache lookup
            cache_start = time.time()
            cached_response = get_instant_response(prompt)
            if cached_response:
                cache_time = (time.time() - cache_start) * 1000
                response_length = len(cached_response)
                
                from utils.logger import logger
                logger.info(f"⚡ FALLBACK CACHE HIT - Using cached response")
                logger.info(f"⏱️ Response time: {cache_time:.1f}ms (instant)")
                logger.info(f"📏 Response length: {response_length} chars")
                logger.info(f"📄 Response preview: {cached_response[:100]}{'...' if response_length > 100 else ''}")
                logger.info(f"🔑 Source: fallback_response_cache")
                
                return cached_response
            
            cache_time = (time.time() - cache_start) * 1000
            from utils.logger import logger
            logger.info(f"🔍 All caches miss ({cache_time:.1f}ms), routing to provider...")
            
            # STEP 3: Route to appropriate provider based on settings
            full_prompt = self._prepare_prompt(prompt, context)
            model_to_use = model_name or "llama3:latest"
            
            provider = self._get_current_provider()
            print(f"🚀 ModelManager routing to {provider.upper()}: {model_to_use}")
            
            provider_start = time.time()
            result = self._route_to_provider(full_prompt, model_to_use, max_tokens=2048, temperature=0.7)
            provider_time = (time.time() - provider_start) * 1000
            
            if result.get('status') == 'success':
                response = result.get('response', 'No response generated.')
                actual_provider = result.get('provider', provider)
                response_length = len(response)
                
                from utils.logger import logger
                logger.info(f"✅ {actual_provider.upper()} response completed")
                logger.info(f"⏱️ Response time: {provider_time:.0f}ms")
                logger.info(f"📏 Response length: {response_length} chars")
                logger.info(f"📄 Response preview: {response[:100]}{'...' if response_length > 100 else ''}")
                logger.info(f"🔑 Source: {actual_provider}_provider")
                
                # STEP 4: Add successful response to cache for future instant replies
                try:
                    response_cache.add_response_to_cache(prompt, response)
                    logger.info(f"💾 Response added to cache for future use")
                except Exception as cache_error:
                    logger.warning(f"⚠️ Cache update failed: {cache_error}")
                
                return response
            else:
                error_msg = result.get('error', 'Unknown error')
                return f"❌ {provider.upper()} Error: {error_msg}"
        
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def generate_stream(self, prompt: str, context: str = None, model_name: str | None = None) -> Iterable[str]:
        """Stream AI response using provider-based routing with simulated streaming"""
        try:
            # Prepare prompt
            full_prompt = self._prepare_prompt(prompt, context)
            model_to_use = model_name or "llama3:latest"
            
            provider = self._get_current_provider()
            print(f"🚀 ModelManager streaming via {provider.upper()}: {model_to_use}")
            
            # Send immediate feedback to user
            yield "[Thinking...]"
            
            # Route to appropriate provider
            result = self._route_to_provider(full_prompt, model_to_use, max_tokens=2048, temperature=0.7)
            
            # Clear the "thinking" message
            yield "\b" * 13 + " " * 13 + "\b" * 13  # Clear "[Thinking...]"
            
            if result.get('status') == 'success':
                response_text = result.get('response', 'No response generated.')
                actual_provider = result.get('provider', provider)
                
                print(f"✅ {actual_provider.upper()} response: {response_text[:100]}...")
                
                # Enhanced streaming simulation with natural pacing
                import time
                import re
                
                # Split by sentences for more natural streaming
                sentences = re.split(r'(?<=[.!?])\s+', response_text)
                
                for i, sentence in enumerate(sentences):
                    if sentence.strip():
                        # Stream each sentence word by word
                        words = sentence.split()
                        for j, word in enumerate(words):
                            if i == 0 and j == 0:
                                yield word
                            else:
                                yield " " + word
                            
                            # Faster streaming with minimal delays
                            if word.endswith(('.', '!', '?')):
                                time.sleep(0.08)  # Reduced sentence pause
                            elif word.endswith((',', ';')):
                                time.sleep(0.05)  # Reduced comma pause  
                            else:
                                time.sleep(0.02)  # Faster word delay
                        
                        # Small pause between sentences
                        if i < len(sentences) - 1:
                            time.sleep(0.1)
            else:
                yield f"❌ {provider.upper()} Error: {result.get('error', 'Unknown error')}"
                
        except Exception as e:
            yield f"❌ Error: {str(e)}"
            return
    
    def _prepare_prompt(self, user_prompt: str, context: str = None) -> str:
        """Prepare the full prompt with property management context"""
        
        system_prompt = """You are Jamie, an AI property manager trained on real phone conversations. 
You help with tenant communications, property management tasks, and real estate questions.

Key guidelines:
- Be helpful, professional, and knowledgeable about property management
- Draw from your training on real property management conversations
- Provide practical, actionable advice
- If you need specific property details, ask clarifying questions
- Keep responses concise but thorough
- You work with Christina and handle property management for various locations
- Always respond directly as Jamie without adding extra conversation elements
- End your response naturally without continuing the conversation

"""
        
        if context:
            system_prompt += f"\nAdditional context: {context}\n"
        
        # Use a cleaner prompt format that doesn't encourage conversation continuation
        return f"{system_prompt}\nMessage from tenant: {user_prompt}\n\nPlease respond as Jamie:"
    
    def create_custom_model(self, training_data: List[Dict[str, str]]) -> bool:
        """Create custom property management model"""
        try:
            # Create Modelfile for custom model
            modelfile_content = self._create_modelfile(training_data)
            
            # Save Modelfile (use local models directory)
            models_dir = Path(os.getcwd()) / "models"
            models_dir.mkdir(exist_ok=True)
            modelfile_path = models_dir / "Modelfile"
            
            with open(modelfile_path, 'w') as f:
                f.write(modelfile_content)
            
            # Create model using Ollama API
            response = requests.post(
                f"{self.base_url}/api/create",
                json={
                    "name": self.custom_model_name,
                    "modelfile": modelfile_content
                },
                stream=True
            )
            
            # Stream response for progress
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if 'status' in data:
                        print(f"Model creation: {data['status']}")
            
            return response.status_code == 200
        
        except Exception as e:
            print(f"Error creating custom model: {e}")
            return False
    
    def _create_modelfile(self, training_data: List[Dict[str, str]]) -> str:
        """Create Modelfile content for custom model"""
        
        # Sample training examples for fine-tuning
        examples = ""
        for i, example in enumerate(training_data[:10]):  # Use first 10 examples
            examples += f"""
Example {i+1}:
Human: {example.get('input', '')}
Assistant: {example.get('output', 'Professional property management response')}

"""
        
        modelfile = f"""FROM {self.model_name}

# Property Management AI System Prompt
SYSTEM \"\"\"You are PeteOllama, an expert AI property manager with extensive experience in:

- Tenant communications and relations
- Property maintenance coordination  
- Lease management and renewals
- Financial calculations and rent collection
- Real estate market knowledge
- Legal compliance and documentation

You have been trained on real property management phone conversations and understand:
- Common tenant concerns and questions
- Professional communication standards
- Property management best practices
- Emergency vs. routine maintenance prioritization

Always respond professionally, helpfully, and with practical solutions.
\"\"\"

# Model Parameters
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1

# Training Examples
TEMPLATE \"\"\"{{ if .System }}{{.System}}

{{ end }}{{ if .Prompt }}Human: {{.Prompt}}

{{ end }}Assistant: {{ .Response }}\"\"\"

{examples}
"""
        
        return modelfile
    
    def get_model_info(self, model_name: str = None) -> Dict[str, Any]:
        """Get information about a model"""
        if model_name is None:
            model_name = self.model_name
        
        try:
            response = requests.post(
                f"{self.base_url}/api/show",
                json={"name": model_name}
            )
            
            if response.status_code == 200:
                return response.json()
            return {}
        
        except Exception as e:
            print(f"Error getting model info: {e}")
            return {}
    
    def test_model_response(self, test_prompt: str = None) -> Dict[str, Any]:
        """Test model with a standard property management prompt"""
        if test_prompt is None:
            test_prompt = "Hi, when is my rent due this month?"
        
        import time
        start_time = time.time()
        
        response = self.generate_response(test_prompt)
        
        end_time = time.time()
        response_time = int((end_time - start_time) * 1000)  # Convert to milliseconds
        
        return {
            'prompt': test_prompt,
            'response': response,
            'response_time_ms': response_time,
            'model_used': self.custom_model_name if self.is_model_available(self.custom_model_name) else self.model_name
        }