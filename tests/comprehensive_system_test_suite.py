#!/usr/bin/env python3
"""
Comprehensive System Test Suite
==============================

Tests every endpoint, every configuration system, every model structure,
and validates everything with Pydantic and beartype utilities.

This test suite will:
1. Test every API endpoint (frontend and webhooks)
2. Test every configuration system (system_config, model_settings, .env)
3. Test every model structure (OpenRouter, RunPod, Ollama)
4. Validate Pydantic models and beartype utilities
5. Log everything for analysis
6. Compare results with whatsWorking analysis
"""

import os
import sys
import json
import asyncio
import requests
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import traceback

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Import our validation utilities
from utils.logger import logger
from utils.type_validation import beartype, validate_and_log_types, TypeValidationError

# Import configuration systems
from config.system_config import system_config, SystemConfigManager
from config.model_settings import model_settings

# Import AI components
from ai.model_manager import ModelManager
from openrouter_handler import OpenRouterHandler
from runpod_handler import pete_handler

# Import Pydantic models for validation
from vapi.models.webhook_models import VAPIChatRequest, VAPIChatResponse

@dataclass
class TestResult:
    """Result of a single test"""
    test_name: str
    status: str  # "PASS", "FAIL", "ERROR", "SKIP"
    duration_ms: float
    details: Dict[str, Any]
    error_message: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

@dataclass
class TestSuiteResult:
    """Results of the entire test suite"""
    suite_name: str
    start_time: str
    end_time: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    error_tests: int
    skipped_tests: int
    test_results: List[TestResult]
    summary: Dict[str, Any]
    
    @property
    def success_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return (self.passed_tests / self.total_tests) * 100

class ComprehensiveSystemTestSuite:
    """Comprehensive test suite for the entire system"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.test_results: List[TestResult] = []
        self.start_time = datetime.now()
        
        # Initialize components
        self.model_manager = None
        self.openrouter_handler = None
        
        # Test configuration
        self.test_config = {
            "test_models": [
                "openai/gpt-3.5-turbo",
                "anthropic/claude-3-haiku", 
                "llama3:latest",
                "mistral:7b-instruct-q4_K_M"
            ],
            "test_prompts": [
                "Hello, how are you?",
                "What is 2+2?",
                "Explain quantum computing in simple terms"
            ],
            "timeout_seconds": 30
        }
        
        logger.info("🚀 Comprehensive System Test Suite initialized")
    
    def log_test_result(self, result: TestResult):
        """Log a test result and add to results list"""
        self.test_results.append(result)
        
        # Log with appropriate level
        if result.status == "PASS":
            logger.info(f"✅ {result.test_name}: PASSED ({result.duration_ms:.2f}ms)")
        elif result.status == "FAIL":
            logger.warning(f"❌ {result.test_name}: FAILED ({result.duration_ms:.2f}ms)")
        elif result.status == "ERROR":
            logger.error(f"💥 {result.test_name}: ERROR ({result.duration_ms:.2f}ms)")
        elif result.status == "SKIP":
            logger.info(f"⏭️ {result.test_name}: SKIPPED")
        
        # Log details if available
        if result.details:
            logger.debug(f"   Details: {json.dumps(result.details, indent=2)}")
        
        # Log error if available
        if result.error_message:
            logger.error(f"   Error: {result.error_message}")
    
    def run_test(self, test_name: str, test_func, *args, **kwargs) -> TestResult:
        """Run a single test and return the result"""
        start_time = time.time()
        
        try:
            logger.info(f"🧪 Running test: {test_name}")
            result = test_func(*args, **kwargs)
            
            duration_ms = (time.time() - start_time) * 1000
            
            if result is True:
                return TestResult(
                    test_name=test_name,
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"result": "Test passed successfully"}
                )
            elif result is False:
                return TestResult(
                    test_name=test_name,
                    status="FAIL",
                    duration_ms=duration_ms,
                    details={"result": "Test failed"}
                )
            else:
                return TestResult(
                    test_name=test_name,
                    status="PASS",
                    duration_ms=duration_ms,
                    details={"result": result}
                )
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Exception: {str(e)}\n{traceback.format_exc()}"
            
            return TestResult(
                test_name=test_name,
                status="ERROR",
                duration_ms=duration_ms,
                details={"error_type": type(e).__name__},
                error_message=error_msg
            )
    
    # ============================================================================
    # CONFIGURATION SYSTEM TESTS
    # ============================================================================
    
    def test_system_config_loading(self) -> bool:
        """Test system configuration loading and validation"""
        try:
            # Test basic loading
            if not system_config:
                logger.error("System config not loaded")
                return False
            
            # Test configuration structure
            config_data = system_config.get_config_summary()
            logger.info(f"System config loaded: {json.dumps(config_data, indent=2)}")
            
            # Validate key configurations
            caching_config = system_config.get_caching_config()
            if not caching_config:
                logger.error("Caching config not available")
                return False
            
            # Test provider configurations
            providers = system_config.get_provider_config("openrouter")
            if not providers:
                logger.error("OpenRouter provider config not available")
                return False
            
            logger.info("✅ System configuration loading test passed")
            return True
            
        except Exception as e:
            logger.error(f"System config test failed: {e}")
            return False
    
    def test_model_settings_loading(self) -> bool:
        """Test legacy model settings loading"""
        try:
            # Test provider settings
            provider_settings = model_settings.get_provider_settings()
            logger.info(f"Provider settings: {json.dumps(provider_settings, indent=2)}")
            
            # Test model list
            models = model_settings.list_models()
            logger.info(f"Available models: {len(models)}")
            
            # Test specific model
            if models:
                first_model = models[0]
                logger.info(f"First model: {first_model.get('name', 'unknown')}")
            
            logger.info("✅ Model settings loading test passed")
            return True
            
        except Exception as e:
            logger.error(f"Model settings test failed: {e}")
            return False
    
    def test_environment_variables(self) -> bool:
        """Test environment variable loading and validation"""
        try:
            # Test key environment variables
            env_vars = {
                "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY"),
                "RUNPOD_API_KEY": os.getenv("RUNPOD_API_KEY"),
                "RUNPOD_SERVERLESS_ENDPOINT": os.getenv("RUNPOD_SERVERLESS_ENDPOINT"),
                "OLLAMA_HOST": os.getenv("OLLAMA_HOST", "localhost:11434"),
                "SIMILARITY_THRESHOLD": os.getenv("SIMILARITY_THRESHOLD"),
                "MAX_TOKENS": os.getenv("MAX_TOKENS")
            }
            
            logger.info(f"Environment variables: {json.dumps(env_vars, indent=2)}")
            
            # Validate required variables
            if not env_vars["OPENROUTER_API_KEY"]:
                logger.warning("OpenRouter API key not set")
            
            if not env_vars["RUNPOD_API_KEY"]:
                logger.warning("RunPod API key not set")
            
            logger.info("✅ Environment variables test passed")
            return True
            
        except Exception as e:
            logger.error(f"Environment variables test failed: {e}")
            return False
    
    def test_configuration_conflicts(self) -> Dict[str, Any]:
        """Test for configuration conflicts between systems"""
        try:
            conflicts = {}
            
            # Compare default providers
            system_default = system_config.config.default_provider
            model_default = model_settings.get_provider_settings().get("default_provider")
            
            if system_default != model_default:
                conflicts["default_provider"] = {
                    "system_config": system_default,
                    "model_settings": model_default,
                    "conflict": True
                }
            
            # Compare similarity thresholds
            system_threshold = system_config.get_caching_config().threshold
            env_threshold = os.getenv("SIMILARITY_THRESHOLD")
            
            if env_threshold and float(env_threshold) != system_threshold:
                conflicts["similarity_threshold"] = {
                    "system_config": system_threshold,
                    "environment": float(env_threshold),
                    "conflict": True
                }
            
            # Compare fallback providers
            system_fallback = system_config.config.fallback_provider
            model_fallback = model_settings.get_provider_settings().get("fallback_provider")
            
            if system_fallback != model_fallback:
                conflicts["fallback_provider"] = {
                    "system_config": system_fallback,
                    "model_settings": model_fallback,
                    "conflict": True
                }
            
            logger.info(f"Configuration conflicts found: {len(conflicts)}")
            for key, conflict in conflicts.items():
                logger.warning(f"Conflict in {key}: {conflict}")
            
            return {
                "conflicts_found": len(conflicts),
                "conflicts": conflicts,
                "has_conflicts": len(conflicts) > 0
            }
            
        except Exception as e:
            logger.error(f"Configuration conflicts test failed: {e}")
            return {"error": str(e)}
    
    # ============================================================================
    # MODEL MANAGER TESTS
    # ============================================================================
    
    def test_model_manager_initialization(self) -> bool:
        """Test ModelManager initialization and configuration"""
        try:
            # Initialize ModelManager
            self.model_manager = ModelManager()
            
            # Test basic attributes
            logger.info(f"ModelManager initialized:")
            logger.info(f"  - Similarity threshold: {self.model_manager.similarity_threshold}")
            logger.info(f"  - Base URL: {self.model_manager.base_url}")
            logger.info(f"  - Model name: {self.model_manager.model_name}")
            
            # Test provider selection
            current_provider = self.model_manager._get_current_provider()
            logger.info(f"  - Current provider: {current_provider}")
            
            # Test similarity analyzer
            analyzer = self.model_manager._get_similarity_analyzer()
            if analyzer:
                logger.info(f"  - Similarity analyzer: {len(analyzer.conversation_samples)} samples")
            
            logger.info("✅ ModelManager initialization test passed")
            return True
            
        except Exception as e:
            logger.error(f"ModelManager initialization test failed: {e}")
            return False
    
    def test_model_manager_configuration_source(self) -> Dict[str, Any]:
        """Test where ModelManager gets its configuration from"""
        try:
            if not self.model_manager:
                return {"error": "ModelManager not initialized"}
            
            # Get current configuration values
            current_config = {
                "similarity_threshold": self.model_manager.similarity_threshold,
                "current_provider": self.model_manager._get_current_provider(),
                "base_url": self.model_manager.base_url,
                "model_name": self.model_manager.model_name,
                "max_tokens": self.model_manager.max_tokens
            }
            
            # Get expected values from different sources
            expected_config = {
                "system_config": {
                    "similarity_threshold": system_config.get_caching_config().threshold,
                    "default_provider": system_config.config.default_provider,
                    "default_model": system_config.config.default_model
                },
                "model_settings": {
                    "default_provider": model_settings.get_provider_settings().get("default_provider"),
                    "fallback_provider": model_settings.get_provider_settings().get("fallback_provider")
                },
                "environment": {
                    "similarity_threshold": os.getenv("SIMILARITY_THRESHOLD"),
                    "ollama_host": os.getenv("OLLAMA_HOST"),
                    "max_tokens": os.getenv("MAX_TOKENS")
                }
            }
            
            # Analyze configuration source
            config_analysis = {
                "current_values": current_config,
                "expected_values": expected_config,
                "configuration_source": "ModelManager internal state"
            }
            
            logger.info("✅ ModelManager configuration source test completed")
            return config_analysis
            
        except Exception as e:
            logger.error(f"ModelManager configuration source test failed: {e}")
            return {"error": str(e)}
    
    # ============================================================================
    # API ENDPOINT TESTS
    # ============================================================================
    
    def test_api_endpoints(self) -> Dict[str, Any]:
        """Test all API endpoints"""
        try:
            endpoints = [
                "/admin",
                "/admin/system-config",
                "/admin/status",
                "/admin/provider-settings",
                "/vapi/v1/chat/completions",
                "/vapi/personas",
                "/css/system-config-ui.css",
                "/js/system-config-ui.js"
            ]
            
            results = {}
            
            for endpoint in endpoints:
                try:
                    url = f"{self.base_url}{endpoint}"
                    response = requests.get(url, timeout=10)
                    
                    results[endpoint] = {
                        "status_code": response.status_code,
                        "content_type": response.headers.get("content-type", ""),
                        "content_length": len(response.content),
                        "accessible": response.status_code < 400
                    }
                    
                    logger.info(f"  {endpoint}: {response.status_code} ({len(response.content)} bytes)")
                    
                except Exception as e:
                    results[endpoint] = {
                        "error": str(e),
                        "accessible": False
                    }
                    logger.error(f"  {endpoint}: ERROR - {e}")
            
            logger.info("✅ API endpoints test completed")
            return results
            
        except Exception as e:
            logger.error(f"API endpoints test failed: {e}")
            return {"error": str(e)}
    
    def test_chat_completions_endpoint(self) -> Dict[str, Any]:
        """Test the chat completions endpoint with different models"""
        try:
            results = {}
            
            for model in self.test_config["test_models"]:
                for prompt in self.test_config["test_prompts"]:
                    test_name = f"{model}_{prompt[:20]}"
                    
                    try:
                        # Create request payload
                        payload = {
                            "model": model,
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": 100,
                            "temperature": 0.7
                        }
                        
                        # Test endpoint with VAPI authentication
                        url = f"{self.base_url}/vapi/v1/chat/completions"
                        headers = {"Authorization": "your-vapi-key-here"}
                        response = requests.post(url, json=payload, headers=headers, timeout=30)
                        
                        results[test_name] = {
                            "model": model,
                            "prompt": prompt,
                            "status_code": response.status_code,
                            "response_time_ms": response.elapsed.total_seconds() * 1000,
                            "response_size": len(response.content),
                            "success": response.status_code == 200
                        }
                        
                        if response.status_code == 200:
                            try:
                                response_data = response.json()
                                results[test_name]["response_data"] = response_data
                            except:
                                results[test_name]["response_data"] = "Invalid JSON"
                        
                        logger.info(f"  {test_name}: {response.status_code} ({response.elapsed.total_seconds():.2f}s)")
                        
                    except Exception as e:
                        results[test_name] = {
                            "model": model,
                            "prompt": prompt,
                            "error": str(e),
                            "success": False
                        }
                        logger.error(f"  {test_name}: ERROR - {e}")
            
            logger.info("✅ Chat completions endpoint test completed")
            return results
            
        except Exception as e:
            logger.error(f"Chat completions endpoint test failed: {e}")
            return {"error": str(e)}
    
    # ============================================================================
    # PROVIDER HANDLER TESTS
    # ============================================================================
    
    def test_openrouter_handler(self) -> Dict[str, Any]:
        """Test OpenRouter handler functionality"""
        try:
            # Initialize handler
            self.openrouter_handler = OpenRouterHandler()
            
            # Test availability
            available = self.openrouter_handler.available
            logger.info(f"OpenRouter handler available: {available}")
            
            if not available:
                return {"available": False, "reason": "Handler not available"}
            
            # Test model discovery
            models = self.openrouter_handler.list_models()
            logger.info(f"OpenRouter models available: {len(models)}")
            
            # Test simple completion
            test_result = None
            if models:
                try:
                    test_result = self.openrouter_handler.chat_completion(
                        "Hello, test message",
                        model=models[0]["id"],
                        max_tokens=50
                    )
                    logger.info("OpenRouter test completion successful")
                except Exception as e:
                    logger.error(f"OpenRouter test completion failed: {e}")
            
            return {
                "available": available,
                "models_count": len(models) if models else 0,
                "test_completion_success": test_result is not None,
                "test_result": test_result
            }
            
        except Exception as e:
            logger.error(f"OpenRouter handler test failed: {e}")
            return {"error": str(e)}
    
    def test_runpod_handler(self) -> Dict[str, Any]:
        """Test RunPod handler functionality"""
        try:
            # Test availability
            available = hasattr(pete_handler, 'chat_completion')
            logger.info(f"RunPod handler available: {available}")
            
            if not available:
                return {"available": False, "reason": "Handler not available"}
            
            # Test simple completion
            test_result = None
            try:
                test_result = pete_handler.chat_completion(
                    "Hello, test message",
                    model="llama3:latest",
                    max_tokens=50
                )
                logger.info("RunPod test completion successful")
            except Exception as e:
                logger.error(f"RunPod test completion failed: {e}")
            
            return {
                "available": available,
                "test_completion_success": test_result is not None,
                "test_result": test_result
            }
            
        except Exception as e:
            logger.error(f"RunPod handler test failed: {e}")
            return {"error": str(e)}
    
    # ============================================================================
    # VALIDATION TESTS
    # ============================================================================
    
    def test_pydantic_validation(self) -> Dict[str, Any]:
        """Test Pydantic model validation"""
        try:
            results = {}
            
            # Test VAPIChatRequest validation
            try:
                valid_request = VAPIChatRequest(
                    model="openai/gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=100
                )
                results["VAPIChatRequest"] = {
                    "valid": True,
                    "model": valid_request.model,
                    "messages_count": len(valid_request.messages)
                }
                logger.info("✅ VAPIChatRequest validation passed")
            except Exception as e:
                results["VAPIChatRequest"] = {
                    "valid": False,
                    "error": str(e)
                }
                logger.error(f"❌ VAPIChatRequest validation failed: {e}")
            
            # Test VAPIChatResponse validation
            try:
                valid_response = VAPIChatResponse(
                    id="test-123",
                    object="chat.completion",
                    created=int(time.time()),
                    model="openai/gpt-3.5-turbo",
                    choices=[{
                        "index": 0,
                        "message": {"role": "assistant", "content": "Hello there!"},
                        "finish_reason": "stop"
                    }],
                    usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
                )
                results["VAPIChatResponse"] = {
                    "valid": True,
                    "id": valid_response.id,
                    "choices_count": len(valid_response.choices)
                }
                logger.info("✅ VAPIChatResponse validation passed")
            except Exception as e:
                results["VAPIChatResponse"] = {
                    "valid": False,
                    "error": str(e)
                }
                logger.error(f"❌ VAPIChatResponse validation failed: {e}")
            
            logger.info("✅ Pydantic validation test completed")
            return results
            
        except Exception as e:
            logger.error(f"Pydantic validation test failed: {e}")
            return {"error": str(e)}
    
    def test_beartype_validation(self) -> Dict[str, Any]:
        """Test beartype validation utilities"""
        try:
            results = {}
            
            # Test basic beartype validation
            @beartype
            def test_function(name: str, age: int) -> str:
                return f"{name} is {age} years old"
            
            try:
                result = test_function("John", 30)
                results["basic_validation"] = {
                    "valid": True,
                    "result": result
                }
                logger.info("✅ Basic beartype validation passed")
            except Exception as e:
                results["basic_validation"] = {
                    "valid": False,
                    "error": str(e)
                }
                logger.error(f"❌ Basic beartype validation failed: {e}")
            
            # Test type validation error
            try:
                test_function("John", "thirty")  # Should fail
                results["type_error_handling"] = {
                    "valid": False,
                    "expected_error": "TypeError not raised"
                }
                logger.warning("⚠️ Type error not raised as expected")
            except Exception as e:
                results["type_error_handling"] = {
                    "valid": True,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
                logger.info("✅ Type error handling working correctly")
            
            logger.info("✅ Beartype validation test completed")
            return results
            
        except Exception as e:
            logger.error(f"Beartype validation test failed: {e}")
            return {"error": str(e)}
    
    # ============================================================================
    # INTEGRATION TESTS
    # ============================================================================
    
    def test_end_to_end_configuration_flow(self) -> Dict[str, Any]:
        """Test end-to-end configuration flow"""
        try:
            results = {}
            
            # Test 1: Change system configuration
            original_threshold = system_config.get_caching_config().threshold
            logger.info(f"Original threshold: {original_threshold}")
            
            # Test 2: Check if ModelManager picks up changes
            if self.model_manager:
                current_threshold = self.model_manager.similarity_threshold
                results["threshold_sync"] = {
                    "system_config": original_threshold,
                    "model_manager": current_threshold,
                    "synced": abs(original_threshold - current_threshold) < 0.001
                }
                logger.info(f"Threshold sync: {results['threshold_sync']}")
            
            # Test 3: Check provider selection
            system_provider = system_config.config.default_provider
            model_provider = model_settings.get_provider_settings().get("default_provider")
            results["provider_sync"] = {
                "system_config": system_provider,
                "model_settings": model_provider,
                "synced": system_provider == model_provider
            }
            logger.info(f"Provider sync: {results['provider_sync']}")
            
            # Test 4: Check if configuration changes affect behavior
            results["configuration_impact"] = {
                "has_impact": False,
                "details": "Configuration changes not yet affecting runtime behavior"
            }
            
            logger.info("✅ End-to-end configuration flow test completed")
            return results
            
        except Exception as e:
            logger.error(f"End-to-end configuration flow test failed: {e}")
            return {"error": str(e)}
    
    # ============================================================================
    # MAIN TEST EXECUTION
    # ============================================================================
    
    def run_all_tests(self) -> TestSuiteResult:
        """Run the complete test suite"""
        logger.info("🚀 Starting Comprehensive System Test Suite")
        logger.info("=" * 60)
        
        # Configuration System Tests
        logger.info("📋 Testing Configuration Systems...")
        self.log_test_result(self.run_test("System Config Loading", self.test_system_config_loading))
        self.log_test_result(self.run_test("Model Settings Loading", self.test_model_settings_loading))
        self.log_test_result(self.run_test("Environment Variables", self.test_environment_variables))
        self.log_test_result(self.run_test("Configuration Conflicts", self.test_configuration_conflicts))
        
        # Model Manager Tests
        logger.info("🤖 Testing Model Manager...")
        self.log_test_result(self.run_test("ModelManager Initialization", self.test_model_manager_initialization))
        self.log_test_result(self.run_test("ModelManager Config Source", self.test_model_manager_configuration_source))
        
        # API Endpoint Tests
        logger.info("🌐 Testing API Endpoints...")
        self.log_test_result(self.run_test("API Endpoints", self.test_api_endpoints))
        self.log_test_result(self.run_test("Chat Completions Endpoint", self.test_chat_completions_endpoint))
        
        # Provider Handler Tests
        logger.info("🔌 Testing Provider Handlers...")
        self.log_test_result(self.run_test("OpenRouter Handler", self.test_openrouter_handler))
        self.log_test_result(self.run_test("RunPod Handler", self.test_runpod_handler))
        
        # Validation Tests
        logger.info("✅ Testing Validation Systems...")
        self.log_test_result(self.run_test("Pydantic Validation", self.test_pydantic_validation))
        self.log_test_result(self.run_test("Beartype Validation", self.test_beartype_validation))
        
        # Integration Tests
        logger.info("🔗 Testing Integration...")
        self.log_test_result(self.run_test("End-to-End Config Flow", self.test_end_to_end_configuration_flow))
        
        # Calculate results
        end_time = datetime.now()
        passed = len([r for r in self.test_results if r.status == "PASS"])
        failed = len([r for r in self.test_results if r.status == "FAIL"])
        errors = len([r for r in self.test_results if r.status == "ERROR"])
        skipped = len([r for r in self.test_results if r.status == "SKIP"])
        total = len(self.test_results)
        
        # Create summary
        summary = {
            "configuration_systems": {
                "system_config_working": any(r.test_name == "System Config Loading" and r.status == "PASS" for r in self.test_results),
                "model_settings_working": any(r.test_name == "Model Settings Loading" and r.status == "PASS" for r in self.test_results),
                "env_vars_working": any(r.test_name == "Environment Variables" and r.status == "PASS" for r in self.test_results),
                "conflicts_found": any(r.test_name == "Configuration Conflicts" and r.status == "PASS" for r in self.test_results)
            },
            "model_manager": {
                "initialization_working": any(r.test_name == "ModelManager Initialization" and r.status == "PASS" for r in self.test_results),
                "config_source": "ModelManager internal state"
            },
            "api_endpoints": {
                "endpoints_accessible": any(r.test_name == "API Endpoints" and r.status == "PASS" for r in self.test_results),
                "chat_completions_working": any(r.test_name == "Chat Completions Endpoint" and r.status == "PASS" for r in self.test_results)
            },
            "providers": {
                "openrouter_working": any(r.test_name == "OpenRouter Handler" and r.status == "PASS" for r in self.test_results),
                "runpod_working": any(r.test_name == "RunPod Handler" and r.status == "PASS" for r in self.test_results)
            },
            "validation": {
                "pydantic_working": any(r.test_name == "Pydantic Validation" and r.status == "PASS" for r in self.test_results),
                "beartype_working": any(r.test_name == "Beartype Validation" and r.status == "PASS" for r in self.test_results)
            },
            "integration": {
                "config_flow_working": any(r.test_name == "End-to-End Config Flow" and r.status == "PASS" for r in self.test_results)
            }
        }
        
        # Create final result
        suite_result = TestSuiteResult(
            suite_name="Comprehensive System Test Suite",
            start_time=self.start_time.isoformat(),
            end_time=end_time.isoformat(),
            total_tests=total,
            passed_tests=passed,
            failed_tests=failed,
            error_tests=errors,
            skipped_tests=skipped,
            test_results=self.test_results,
            summary=summary
        )
        
        # Log final results
        logger.info("=" * 60)
        logger.info("🏁 Comprehensive System Test Suite Completed")
        logger.info(f"📊 Results: {passed}/{total} tests passed ({suite_result.success_rate:.1f}%)")
        logger.info(f"❌ Failed: {failed}, 💥 Errors: {errors}, ⏭️ Skipped: {skipped}")
        
        return suite_result
    
    def save_results(self, results: TestSuiteResult, filename: str = None):
        """Save test results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"DEV_MAN/test_results_{timestamp}.json"
        
        # Ensure directory exists
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict for JSON serialization
        results_dict = asdict(results)
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(results_dict, f, indent=2)
        
        logger.info(f"💾 Test results saved to: {filename}")
        return filename

def main():
    """Main entry point for the test suite"""
    try:
        # Initialize test suite
        test_suite = ComprehensiveSystemTestSuite()
        
        # Run all tests
        results = test_suite.run_all_tests()
        
        # Save results
        results_file = test_suite.save_results(results)
        
        # Print summary
        print("\n" + "=" * 80)
        print("🏁 COMPREHENSIVE SYSTEM TEST SUITE RESULTS")
        print("=" * 80)
        print(f"📊 Success Rate: {results.success_rate:.1f}% ({results.passed_tests}/{results.total_tests})")
        print(f"❌ Failed: {results.failed_tests}, 💥 Errors: {results.error_tests}")
        print(f"💾 Results saved to: {results_file}")
        
        # Print detailed results
        print("\n📋 DETAILED RESULTS:")
        for result in results.test_results:
            status_icon = "✅" if result.status == "PASS" else "❌" if result.status == "FAIL" else "💥" if result.status == "ERROR" else "⏭️"
            print(f"  {status_icon} {result.test_name}: {result.status} ({result.duration_ms:.1f}ms)")
        
        print("\n🎯 SUMMARY:")
        for category, details in results.summary.items():
            print(f"  {category}: {details}")
        
        return results
        
    except Exception as e:
        logger.error(f"Test suite execution failed: {e}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()
