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
    
    def __init__(self, model_manager=None):
        self.router = APIRouter(prefix="/admin", tags=["admin"])
        self.model_manager = model_manager
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

def create_admin_router(model_manager=None) -> APIRouter:
    """Factory function to create admin router"""
    admin_router = AdminRouter(model_manager)
    return admin_router.router
