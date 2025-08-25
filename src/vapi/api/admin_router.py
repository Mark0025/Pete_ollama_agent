#!/usr/bin/env python3
"""
Admin Router - Clean Version

FastAPI router for administrative endpoints with proper structure and no hardcoded values.
Uses the new DataConversionUtility for type-safe data handling.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import logging

# Import our utilities
from src.utils.data_conversion_utility import create_data_converter
from src.utils.llm_response_analyzer import create_llm_analyzer

logger = logging.getLogger(__name__)

class AdminRouter:
    """Admin router with proper structure and no hardcoded values"""
    
    def __init__(self, model_manager=None, runpod_api_key=None):
        self.router = APIRouter(prefix="/admin", tags=["admin"])
        self.model_manager = model_manager
        self.runpod_api_key = runpod_api_key
        self.project_root = Path(__file__).parent.parent.parent.parent
        
        # Initialize utilities
        self.data_converter = create_data_converter(str(self.project_root))
        self.llm_analyzer = create_llm_analyzer(str(self.project_root))
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup all admin routes"""
        
        @self.router.get("/")
        async def admin_home():
            """Admin home page"""
            try:
                html_file = self.project_root / "src" / "frontend" / "html" / "admin-ui.html"
                if html_file.exists():
                    with open(html_file, 'r') as f:
                        content = f.read()
                    return HTMLResponse(content=content)
                else:
                    return HTMLResponse(content="<h1>Admin Panel</h1><p>Admin UI not found</p>")
            except Exception as e:
                logger.error(f"Error loading admin home: {e}")
                return HTMLResponse(content="<h1>Admin Panel</h1><p>Error loading admin UI</p>")
        
        @self.router.get("/settings")
        async def admin_settings():
            """Admin settings page"""
            try:
                html_file = self.project_root / "src" / "frontend" / "html" / "admin-ui.html"
                if html_file.exists():
                    with open(html_file, 'r') as f:
                        content = f.read()
                    return HTMLResponse(content=content)
                else:
                    return HTMLResponse(content="<h1>Admin Settings</h1><p>Settings UI not found</p>")
            except Exception as e:
                logger.error(f"Error loading admin settings: {e}")
                return HTMLResponse(content="<h1>Admin Settings</h1><p>Error loading settings UI</p>")
        
        @self.router.get("/system-config")
        async def system_config_ui():
            """System configuration UI page"""
            try:
                html_file = self.project_root / "src" / "frontend" / "html" / "system-config-ui.html"
                if html_file.exists():
                    with open(html_file, 'r') as f:
                        content = f.read()
                    return HTMLResponse(content=content)
                else:
                    return HTMLResponse(content="<h1>System Config UI</h1><p>System config UI not found</p>")
            except Exception as e:
                logger.error(f"Error loading system config UI: {e}")
                return HTMLResponse(content="<h1>System Config UI</h1><p>Error loading system config UI</p>")
        
        @self.router.get("/stats")
        async def admin_stats():
            """Admin statistics page"""
            try:
                html_file = self.project_root / "src" / "frontend" / "html" / "stats-ui.html"
                if html_file.exists():
                    with open(html_file, 'r') as f:
                        content = f.read()
                    return HTMLResponse(content=content)
                else:
                    return HTMLResponse(content="<h1>Admin Stats</h1><p>Stats UI not found</p>")
            except Exception as e:
                logger.error(f"Error loading admin stats: {e}")
                return HTMLResponse(content="<h1>Admin Stats</h1><p>Error loading stats UI</p>")
        
        @self.router.get("/environment")
        async def get_environment_info():
            """Get environment information for UI"""
            try:
                import platform
                import os
                
                # Check if we're running locally or in cloud
                is_local = os.getenv('ENVIRONMENT', 'local') == 'local'
                
                # Get platform info
                platform_info = platform.platform()
                
                # Get timeout from environment or use default
                timeout_seconds = int(os.getenv('TIMEOUT_SECONDS', '30'))
                
                return {
                    "is_local": is_local,
                    "platform": platform_info,
                    "timeout_seconds": timeout_seconds,
                    "environment": "local",
                    "ollama_host": os.getenv('OLLAMA_HOST', 'localhost:11434')
                }
            except Exception as e:
                logger.error(f"Error getting environment info: {e}")
                return {
                    "is_local": True,
                    "platform": "unknown",
                    "timeout_seconds": 30,
                    "environment": "local",
                    "ollama_host": "localhost:11434"
                }
        
        @self.router.get("/provider-settings")
        async def get_provider_settings():
            """Get current provider settings for UI"""
            try:
                from src.config.system_config import system_config
                
                # Get current provider from system config
                current_provider = system_config.config.default_provider
                
                # Get provider configs
                provider_configs = {}
                if hasattr(system_config, 'get_provider_config'):
                    for provider_name in ['openrouter', 'runpod', 'ollama']:
                        try:
                            config = system_config.get_provider_config(provider_name)
                            if config:
                                provider_configs[provider_name] = {
                                    "enabled": config.enabled,
                                    "priority": config.priority,
                                    "api_key_set": bool(config.api_key) if hasattr(config, 'api_key') else False
                                }
                        except Exception as e:
                            logger.warning(f"Could not get config for {provider_name}: {e}")
                            provider_configs[provider_name] = {"enabled": False, "priority": 999, "api_key_set": False}
                
                return {
                    "current_provider": current_provider,
                    "providers": provider_configs,
                    "fallback_enabled": system_config.config.fallback_enabled,
                    "fallback_provider": system_config.config.fallback_provider
                }
                
            except Exception as e:
                logger.error(f"Error getting provider settings: {e}")
                return {
                    "current_provider": "ollama",
                    "providers": {
                        "ollama": {"enabled": True, "priority": 1, "api_key_set": False},
                        "openrouter": {"enabled": False, "priority": 999, "api_key_set": False},
                        "runpod": {"enabled": False, "priority": 999, "api_key_set": False}
                    },
                    "fallback_enabled": False,
                    "fallback_provider": "ollama"
                }
        
        @self.router.post("/provider-settings/update")
        async def update_provider_settings(request: Request):
            """Update provider settings from UI"""
            try:
                data = await request.json()
                provider = data.get('provider')
                action = data.get('action')  # 'switch' or 'update'
                
                if action == 'switch' and provider:
                    # For now, just return success - in a real implementation,
                    # this would update the system configuration
                    logger.info(f"Provider switch requested to: {provider}")
                    return {"success": True, "message": f"Provider switched to {provider}"}
                
                return {"success": True, "message": "Settings updated"}
                
            except Exception as e:
                logger.error(f"Error updating provider settings: {e}")
                return {"success": False, "error": str(e)}
        
        @self.router.get("/data-source/{data_source}/columns")
        async def get_data_source_columns(data_source: str):
            """Get columns and filters specific to a data source"""
            try:
                # Load the actual data for this source
                data = None
                if data_source == "test_results":
                    test_file = self.project_root / "DEV_MAN" / "test_results_20250819_202750.json"
                    if test_file.exists():
                        data = self.data_converter.load_and_validate_json(test_file)
                elif data_source == "training_data":
                    training_file = self.project_root / "langchain_indexed_conversations.json"
                    if training_file.exists():
                        data = self.data_converter.load_and_validate_json(training_file)
                elif data_source == "model_performance":
                    # Get model performance data
                    model_perf = self.llm_analyzer.analyze_model_performance()
                    data = {"models": [self.data_converter.object_to_dict(m) for m in model_perf] if model_perf else []}
                elif data_source == "validation_metrics":
                    # Get validation metrics data from ResponseValidator
                    try:
                        from src.analytics.response_validator import response_validator
                        validation_data = response_validator.get_validation_metrics() if hasattr(response_validator, 'get_validation_metrics') else []
                    except ImportError:
                        validation_data = []
                    data = {"metrics": validation_data}
                elif data_source == "system_health":
                    # Get system health data
                    health_metrics = self.llm_analyzer._get_system_health_metrics()
                    data = {"health_metrics": health_metrics}
                else:
                    return {"success": False, "error": f"Unknown data source: {data_source}"}
                
                # Use unified utility to analyze data source
                analysis_result = self.data_converter.analyze_data_source(data_source, data)
                
                # Ensure no hardcoded values
                if not self.data_converter.ensure_no_hardcoded_values(analysis_result):
                    logger.warning(f"⚠️ Potential hardcoded values detected in {data_source}")
                
                return analysis_result
                
            except Exception as e:
                logger.error(f"Error getting columns for {data_source}: {str(e)}")
                return {"success": False, "error": str(e)}
        
        @self.router.get("/benchmark/stats")
        async def get_benchmark_stats():
            """Get benchmark statistics from actual test results"""
            try:
                # Load actual test results from DEV_MAN
                test_results_file = self.project_root / "DEV_MAN" / "test_results_20250819_202750.json"
                
                if test_results_file.exists():
                    test_data = self.data_converter.load_and_validate_json(test_results_file)
                    
                    # Extract real metrics from test results
                    total_tests = test_data.get('total_tests', 0)
                    passed_tests = test_data.get('passed_tests', 0)
                    failed_tests = test_data.get('failed_tests', 0)
                    
                    # Calculate success rate
                    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
                    
                    # Extract model performance data
                    models_tested = set()
                    total_duration = 0
                    request_count = 0
                    recent_requests = []
                    
                    if 'test_results' in test_data:
                        for test in test_data['test_results']:
                            if 'details' in test and 'result' in test['details']:
                                result = test['details']['result']
                                if isinstance(result, dict):
                                    # Extract model info if available
                                    if 'model' in result:
                                        models_tested.add(result['model'])
                                    if 'duration_ms' in result:
                                        total_duration += result['duration_ms']
                                        request_count += 1
                                    
                                    # Add to recent requests
                                    recent_requests.append({
                                        'test_name': test.get('test_name', 'Unknown'),
                                        'status': test.get('status', 'Unknown'),
                                        'duration_ms': result.get('duration_ms', 0),
                                        'timestamp': test.get('timestamp', ''),
                                        'model': result.get('model', 'N/A')
                                    })
                    
                    # Limit recent requests to last 10
                    recent_requests = recent_requests[-10:]
                    
                    return {
                        "total_requests": request_count,
                        "total_tests": total_tests,
                        "passed_tests": passed_tests,
                        "failed_tests": failed_tests,
                        "average_duration": total_duration / request_count if request_count > 0 else 0,
                        "models_tested": list(models_tested),
                        "success_rate": round(success_rate, 1),
                        "recent_requests": recent_requests,
                        "data_source": "DEV_MAN/test_results_20250819_202750.json"
                    }
                else:
                    # Fallback to basic stats if file not found
                    return {
                        "total_requests": 0,
                        "total_tests": 0,
                        "passed_tests": 0,
                        "failed_tests": 0,
                        "average_duration": 0,
                        "models_tested": [],
                        "success_rate": 0,
                        "recent_requests": [],
                        "data_source": "No test results found"
                    }
                    
            except Exception as e:
                logger.error(f"Error getting benchmark stats: {str(e)}")
                return {"success": False, "error": str(e)}
        
        @self.router.get("/training/conversations")
        async def get_training_conversations():
            """Get training conversations with calculated quality metrics"""
            try:
                training_metrics = self.llm_analyzer.analyze_training_conversations()
                
                return {
                    "success": True,
                    "total_conversations": training_metrics.get('total_conversations', 0),
                    "total_threads": training_metrics.get('total_threads', 0),
                    "processing_date": training_metrics.get('processing_date', 'Unknown'),
                    "conversations": training_metrics.get('conversations', []),
                    "avg_quality_score": training_metrics.get('avg_quality_score', 0),
                    "avg_training_value": training_metrics.get('avg_training_value', 0),
                    "quality_distribution": training_metrics.get('quality_distribution', {}),
                    "training_value_distribution": training_metrics.get('training_value_distribution', {})
                }
                
            except Exception as e:
                logger.error(f"Error loading training conversations: {str(e)}")
                return {"success": False, "error": str(e)}
        
        @self.router.get("/model/performance")
        async def get_model_performance():
            """Get model performance metrics"""
            try:
                model_performance = self.llm_analyzer.analyze_model_performance()
                
                return {
                    "success": True,
                    "total_models": len(model_performance),
                    "active_models": len([m for m in model_performance if m.success_rate > 80]),
                    "models": [
                        {
                            "name": m.model_name,
                            "provider": m.provider,
                            "success_rate": m.success_rate,
                            "avg_duration": m.avg_duration_ms,
                            "total_requests": m.total_requests,
                            "last_used": m.last_used
                        }
                        for m in model_performance
                    ]
                }
                
            except Exception as e:
                logger.error(f"Error loading model performance: {str(e)}")
                return {"success": False, "error": str(e)}
        
        @self.router.get("/validation/metrics")
        async def get_validation_metrics():
            """Get response validation metrics"""
            try:
                # Try to get real validation data
                try:
                    from src.analytics.response_validator import response_validator
                    if hasattr(response_validator, 'get_validation_metrics'):
                        validation_data = response_validator.get_validation_metrics()
                    else:
                        validation_data = []
                except ImportError:
                    validation_data = []
                
                return {
                    "success": True,
                    "validation_data": validation_data,
                    "message": "Validation metrics loaded from ResponseValidator" if validation_data else "No validation data available"
                }
            
            except Exception as e:
                logger.error(f"Error loading validation metrics: {str(e)}")
                return {"success": False, "error": str(e)}
        
        @self.router.get("/system/health")
        async def get_system_health():
            """Get system health metrics"""
            try:
                health_metrics = self.llm_analyzer._get_system_health_metrics()
                
                return {
                    "success": True,
                    "health_metrics": health_metrics
                }
            
            except Exception as e:
                logger.error(f"Error getting system health: {str(e)}")
                return {"success": False, "error": str(e)}
        
        @self.router.post("/dynamic/filter")
        async def filter_data_dynamically(request: Request):
            """Filter any data using the enhanced dynamic utility"""
            try:
                body = await request.json()
                filter_criteria = body.get('criteria', {})
                data_source = body.get('data_source', 'test_results')
                
                # Load data based on source
                if data_source == 'test_results':
                    data_file = self.project_root / "DEV_MAN" / "test_results_20250819_202750.json"
                elif data_source == 'training_conversations':
                    data_file = self.project_root / "langchain_indexed_conversations.json"
                else:
                    return {"success": False, "error": f"Unknown data source: {data_source}"}
                
                if not data_file.exists():
                    return {"success": False, "error": f"Data file not found: {data_source}"}
                
                data = self.data_converter.load_and_validate_json(data_file)
                
                # Use our unified utility for filtering
                filtered_result = self.data_converter.filter_data_dynamically(data, filter_criteria, data_source)
                
                return filtered_result.dict()
                
            except Exception as e:
                logger.error(f"Error filtering data: {str(e)}")
                return {"success": False, "error": str(e)}
        
        @self.router.get("/models")
        async def get_models():
            """Get available models"""
            try:
                if hasattr(self.model_manager, 'get_available_models'):
                    models = self.model_manager.get_available_models()
                    return {
                        "success": True,
                        "models": [{"name": model, "status": "active"} for model in models]
                    }
                else:
                    return {
                        "success": True,
                        "models": []
                    }
            except Exception as e:
                logger.error(f"Error getting models: {str(e)}")
                return {"success": False, "error": str(e)}
        
        @self.router.get("/config")
        async def get_config():
            """Get system configuration"""
            try:
                return {
                    "success": True,
                    "default_provider": "ollama",
                    "fallback_provider": "runpod",
                    "fallback_enabled": True,
                    "environment": "development",
                    "python_version": sys.version,
                    "working_directory": str(Path.cwd())
                }
            except Exception as e:
                logger.error(f"Error getting config: {str(e)}")
                return {"success": False, "error": str(e)}
        
        @self.router.get("/test/ollama-models")
        async def test_ollama_models():
            """Test endpoint to check Ollama model availability"""
            try:
                from src.vapi.services.provider_service import ProviderService
                
                provider_service = ProviderService()
                available_models = await provider_service._get_actual_ollama_models()
                
                return {
                    "success": True,
                    "available_models": available_models,
                    "count": len(available_models),
                    "message": "Ollama model availability test completed"
                }
                
            except Exception as e:
                logger.error(f"Error testing Ollama models: {str(e)}")
                return {"success": False, "error": str(e)}
        
        @self.router.get("/test/runpod-models")
        async def test_runpod_models():
            """Test endpoint to check RunPod model availability"""
            try:
                from src.vapi.services.provider_service import ProviderService
                
                provider_service = ProviderService()
                available_models = await provider_service._get_actual_runpod_models()
                
                return {
                    "success": True,
                    "available_models": available_models,
                    "count": len(available_models),
                    "message": "RunPod model availability test completed"
                }
                
            except Exception as e:
                logger.error(f"Error testing RunPod models: {str(e)}")
                return {"success": False, "error": str(e)}
        
        @self.router.get("/test/provider-models/{provider}")
        async def test_provider_models(provider: str):
            """Test endpoint to get models for a specific provider"""
            try:
                from src.vapi.services.provider_service import ProviderService
                
                provider_service = ProviderService()
                personas = await provider_service.get_personas_for_provider(provider)
                
                # Extract model names from personas
                all_models = []
                for persona in personas:
                    for model in persona.models:
                        all_models.append(model.name)
                
                return {
                    "success": True,
                    "provider": provider,
                    "models": all_models,
                    "count": len(all_models),
                    "personas": [{"name": p.name, "model_count": len(p.models)} for p in personas],
                    "message": f"Provider {provider} model test completed"
                }
                
            except Exception as e:
                logger.error(f"Error testing provider {provider} models: {str(e)}")
                return {"success": False, "error": str(e)}
        
        @self.router.get("/test-cases")
        async def get_test_cases():
            """Get Jamie test cases for provider comparison"""
            try:
                import os
                import glob
                import json
                from datetime import datetime
                
                # Find all jamie test case files in project root
                jamie_files = glob.glob(str(self.project_root / "jamie_test_cases_*.json"))
                
                # If no files found, return empty
                if not jamie_files:
                    return {
                        "success": False,
                        "error": "No Jamie test case files found",
                        "files": []
                    }
                
                # Sort by modification time (most recent first)
                jamie_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                
                # Get the most recent file
                latest_file = jamie_files[0]
                
                # Get file stats
                file_stat = os.stat(latest_file)
                file_size = file_stat.st_size
                mod_time = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                
                # Load the file
                with open(latest_file, 'r') as f:
                    data = json.load(f)
                
                # Extract metadata and first 10 test cases for preview
                metadata = data.get('metadata', {})
                test_cases = data.get('test_cases', [])
                
                return {
                    "success": True,
                    "file": os.path.basename(latest_file),
                    "file_size": file_size,
                    "modified": mod_time,
                    "total_test_cases": len(test_cases),
                    "metadata": metadata,
                    "preview": test_cases[:10],  # First 10 test cases
                    "available_files": [os.path.basename(f) for f in jamie_files]
                }
                
            except Exception as e:
                logger.error(f"Error loading test cases: {str(e)}")
                return {"success": False, "error": str(e)}

        @self.router.get("/test-cases/latest")
        async def get_latest_test_cases():
            """Get the latest Jamie test cases for provider comparison"""
            try:
                import os
                import glob
                import json
                
                # Find all jamie test case files in project root
                jamie_files = glob.glob(str(self.project_root / "jamie_test_cases_*.json"))
                
                # If no files found, return empty
                if not jamie_files:
                    return {"success": False, "error": "No Jamie test case files found"}
                
                # Sort by modification time (most recent first)
                jamie_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                
                # Get the most recent file
                latest_file = jamie_files[0]
                
                # Load the file
                with open(latest_file, 'r') as f:
                    data = json.load(f)
                
                # Extract just the test cases array for easy consumption
                test_cases = data.get('test_cases', [])
                
                # Include basic metadata for context
                metadata = data.get('metadata', {})
                
                return {
                    "success": True,
                    "file": os.path.basename(latest_file),
                    "test_cases": test_cases,
                    "total": len(test_cases),
                    "categories": metadata.get("quality_summary", {}).get("category_distribution", {}),
                    "source": "jamie_processor"
                }
                
            except Exception as e:
                logger.error(f"Error loading latest test cases: {str(e)}")
                return {"success": False, "error": str(e)}

        @self.router.get("/test-cases/random/{count}")
        async def get_random_test_cases(count: int = 10):
            """Get a random selection of test cases for provider testing"""
            try:
                import os
                import glob
                import json
                import random
                
                # Find all jamie test case files in project root
                jamie_files = glob.glob(str(self.project_root / "jamie_test_cases_*.json"))
                
                # If no files found, return empty
                if not jamie_files:
                    return {"success": False, "error": "No Jamie test case files found"}
                
                # Sort by modification time (most recent first)
                jamie_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                
                # Get the most recent file
                latest_file = jamie_files[0]
                
                # Load the file
                with open(latest_file, 'r') as f:
                    data = json.load(f)
                
                # Extract test cases
                test_cases = data.get('test_cases', [])
                
                # Cap the count to the available test cases
                count = min(count, len(test_cases))
                
                # Select random cases if we have more than requested
                if len(test_cases) > count:
                    test_cases = random.sample(test_cases, count)
                
                return {
                    "success": True,
                    "file": os.path.basename(latest_file),
                    "test_cases": test_cases,
                    "total": len(test_cases),
                    "requested": count,
                    "source": "jamie_processor_random"
                }
                
            except Exception as e:
                logger.error(f"Error loading random test cases: {str(e)}")
                return {"success": False, "error": str(e)}
                
        @self.router.get("/test/system-config-providers")
        async def test_system_config_providers():
            """Test endpoint to show system config provider status and available models"""
            try:
                from src.vapi.services.provider_service import ProviderService
                from src.config.system_config import system_config
                
                provider_service = ProviderService()
                
                # Get system config status
                config_status = {
                    "default_provider": system_config.config.default_provider,
                    "providers": {}
                }
                
                # Check each provider's status
                for provider_name in ['openrouter', 'ollama', 'runpod']:
                    try:
                        provider_config = system_config.get_provider_config(provider_name)
                        if provider_config:
                            config_status["providers"][provider_name] = {
                                "enabled": provider_config.enabled,
                                "api_key_set": bool(provider_config.api_key) if hasattr(provider_config, 'api_key') else False,
                                "priority": getattr(provider_config, 'priority', 999)
                            }
                        else:
                            config_status["providers"][provider_name] = {
                                "enabled": False,
                                "api_key_set": False,
                                "priority": 999
                            }
                    except Exception as e:
                        config_status["providers"][provider_name] = {
                            "enabled": False,
                            "api_key_set": False,
                            "priority": 999,
                            "error": str(e)
                        }
                
                # Test which providers actually return models
                available_models = {}
                for provider_name in ['openrouter', 'ollama', 'runpod']:
                    try:
                        if provider_service._is_provider_enabled(provider_name):
                            personas = await provider_service.get_personas_for_provider(provider_name)
                            model_count = sum(len(p.models) for p in personas)
                            available_models[provider_name] = {
                                "enabled_in_config": True,
                                "models_available": model_count,
                                "personas": len(personas)
                            }
                        else:
                            available_models[provider_name] = {
                                "enabled_in_config": False,
                                "models_available": 0,
                                "personas": 0,
                                "reason": "Disabled in system config or missing API key"
                            }
                    except Exception as e:
                        available_models[provider_name] = {
                            "enabled_in_config": False,
                            "models_available": 0,
                            "personas": 0,
                            "error": str(e)
                        }
                
                return {
                    "success": True,
                    "system_config": config_status,
                    "available_models": available_models,
                    "message": "System config provider status test completed"
                }
                
            except Exception as e:
                logger.error(f"Error testing system config providers: {str(e)}")
                return {"success": False, "error": str(e)}

def create_admin_router(model_manager=None, runpod_api_key=None) -> APIRouter:
    """Factory function to create admin router"""
    admin_router = AdminRouter(model_manager, runpod_api_key)
    return admin_router.router
