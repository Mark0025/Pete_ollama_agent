#!/usr/bin/env python3
"""
Comprehensive LLM Response Analysis Utility

This utility analyzes LLM test results, training conversations, and model performance
to provide real benchmark metrics and insights. It replaces hardcoded values with
actual data analysis.
"""

import json
import os
import psutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
import logging
from collections import defaultdict, Counter
import statistics

logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Individual test result data"""
    test_name: str
    status: str
    duration_ms: float
    timestamp: str
    details: Dict[str, Any]
    error_message: Optional[str] = None

@dataclass
class TrainingConversation:
    """Training conversation data"""
    client_name: str
    date: str
    message_count: int
    quality_score: Optional[float] = None
    training_value: Optional[float] = None

@dataclass
class ModelPerformance:
    """Model performance metrics"""
    model_name: str
    provider: str
    total_requests: int
    success_rate: float
    avg_duration_ms: float
    total_tokens: int
    last_used: str
    quality_scores: List[float] = field(default_factory=list)

@dataclass
class BenchmarkMetrics:
    """Comprehensive benchmark metrics"""
    total_tests: int
    passed_tests: int
    failed_tests: int
    success_rate: float
    avg_duration_ms: float
    total_duration_ms: float
    models_tested: List[str]
    test_categories: Dict[str, int]
    performance_distribution: Dict[str, int]
    quality_metrics: Dict[str, float]

class LLMResponseAnalyzer:
    """
    Comprehensive analyzer for LLM responses, test results, and training data
    """
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.test_results_file = self.project_root / "DEV_MAN" / "test_results_20250819_202750.json"
        self.training_file = self.project_root / "langchain_indexed_conversations.json"
        
        # Cache for analysis results
        self._test_results_cache = None
        self._training_cache = None
        self._last_analysis = None
    
    def analyze_test_results(self) -> BenchmarkMetrics:
        """Analyze test results and generate comprehensive metrics"""
        if not self.test_results_file.exists():
            logger.warning(f"Test results file not found: {self.test_results_file}")
            return self._create_empty_metrics()
        
        try:
            with open(self.test_results_file, 'r') as f:
                data = json.load(f)
            
            test_results = data.get('test_results', [])
            if not test_results:
                return self._create_empty_metrics()
            
            # Extract metrics
            total_tests = len(test_results)
            passed_tests = sum(1 for t in test_results if t.get('status') == 'PASS')
            failed_tests = total_tests - passed_tests
            success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            # Duration analysis
            durations = [t.get('duration_ms', 0) for t in test_results]
            avg_duration = statistics.mean(durations) if durations else 0
            total_duration = sum(durations)
            
            # Model analysis
            models_tested = self._extract_models_from_tests(test_results)
            
            # Test categories
            test_categories = self._categorize_tests(test_results)
            
            # Performance distribution
            performance_distribution = self._analyze_performance_distribution(durations)
            
            # Quality metrics
            quality_metrics = self._calculate_quality_metrics(test_results)
            
            return BenchmarkMetrics(
                total_tests=total_tests,
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                success_rate=success_rate,
                avg_duration_ms=avg_duration,
                total_duration_ms=total_duration,
                models_tested=models_tested,
                test_categories=test_categories,
                performance_distribution=performance_distribution,
                quality_metrics=quality_metrics
            )
            
        except Exception as e:
            logger.error(f"Error analyzing test results: {e}")
            return self._create_empty_metrics()
    
    def analyze_training_conversations(self) -> Dict[str, Any]:
        """Analyze training conversations and calculate quality metrics"""
        if not self.training_file.exists():
            logger.warning(f"Training file not found: {self.training_file}")
            return self._create_empty_training_metrics()
        
        try:
            with open(self.training_file, 'r') as f:
                data = json.load(f)
            
            # Extract conversations from the nested structure
            enhanced_conversations = []
            total_messages = 0
            
            if 'conversation_threads' in data:
                for thread_key, thread_data in data['conversation_threads'].items():
                    if 'conversations' in thread_data:
                        for conv in thread_data['conversations']:
                            # Calculate message count from jamie_said and client_said arrays
                            jamie_messages = len(conv.get('jamie_said', []))
                            client_messages = len(conv.get('client_said', []))
                            message_count = jamie_messages + client_messages
                            total_messages += message_count
                            
                            # Calculate quality score based on conversation patterns
                            quality_score = self._calculate_conversation_quality(conv, message_count)
                            training_value = self._calculate_training_value(conv, message_count)
                            
                            enhanced_conv = TrainingConversation(
                                client_name=thread_data.get('client_info', {}).get('name', 'Unknown'),
                                date=conv.get('date', 'Unknown'),
                                message_count=message_count,
                                quality_score=quality_score,
                                training_value=training_value
                            )
                            enhanced_conversations.append(enhanced_conv)
            
            if not enhanced_conversations:
                return self._create_empty_training_metrics()
            
            # Aggregate metrics
            total_conversations = len(enhanced_conversations)
            avg_messages = total_messages / total_conversations if total_conversations > 0 else 0
            
            # Quality distribution
            quality_scores = [c.quality_score for c in enhanced_conversations if c.quality_score is not None]
            avg_quality = statistics.mean(quality_scores) if quality_scores else 0
            
            # Training value distribution
            training_values = [c.training_value for c in enhanced_conversations if c.training_value is not None]
            avg_training_value = statistics.mean(training_values) if training_values else 0
            
            return {
                "total_conversations": total_conversations,
                "total_threads": data.get('metadata', {}).get('total_threads', 0),
                "total_messages": total_messages,
                "avg_messages_per_conversation": avg_messages,
                "avg_quality_score": avg_quality,
                "avg_training_value": avg_training_value,
                "conversations": enhanced_conversations,
                "quality_distribution": self._analyze_quality_distribution(quality_scores),
                "training_value_distribution": self._analyze_quality_distribution(training_values),
                "processing_date": data.get('metadata', {}).get('processing_date', 'Unknown')
            }
            
        except Exception as e:
            logger.error(f"Error analyzing training conversations: {e}")
            return self._create_empty_training_metrics()
    
    def analyze_model_performance(self) -> List[ModelPerformance]:
        """Analyze model performance from test results"""
        if not self.test_results_file.exists():
            return []
        
        try:
            with open(self.test_results_file, 'r') as f:
                data = json.load(f)
            
            test_results = data.get('test_results', [])
            
            # Group by model/provider
            model_groups = defaultdict(list)
            for test in test_results:
                # Extract model info from test details
                model_info = self._extract_model_info(test)
                if model_info:
                    model_groups[model_info['key']].append({
                        'test': test,
                        'model_name': model_info['model_name'],
                        'provider': model_info['provider']
                    })
            
            # Calculate performance metrics for each model
            performance_data = []
            for model_key, tests in model_groups.items():
                if not tests:
                    continue
                
                # Calculate metrics
                total_requests = len(tests)
                success_count = sum(1 for t in tests if t['test'].get('status') == 'PASS')
                success_rate = (success_count / total_requests * 100) if total_requests > 0 else 0
                
                durations = [t['test'].get('duration_ms', 0) for t in tests]
                avg_duration = statistics.mean(durations) if durations else 0
                
                # Estimate total tokens (if available in test details)
                total_tokens = self._estimate_total_tokens(tests)
                
                # Get last used timestamp
                timestamps = [t['test'].get('timestamp') for t in tests]
                last_used = max(timestamps) if timestamps else 'Unknown'
                
                # Calculate quality scores
                quality_scores = self._extract_quality_scores(tests)
                
                performance = ModelPerformance(
                    model_name=tests[0]['model_name'],
                    provider=tests[0]['provider'],
                    total_requests=total_requests,
                    success_rate=success_rate,
                    avg_duration_ms=avg_duration,
                    total_tokens=total_tokens,
                    last_used=last_used,
                    quality_scores=quality_scores
                )
                
                performance_data.append(performance)
            
            return performance_data
            
        except Exception as e:
            logger.error(f"Error analyzing model performance: {e}")
            return []
    
    def get_comprehensive_analysis(self) -> Dict[str, Any]:
        """Get comprehensive analysis of all data sources"""
        logger.info("Starting comprehensive LLM response analysis")
        
        # Analyze test results
        test_metrics = self.analyze_test_results()
        
        # Analyze training conversations
        training_metrics = self.analyze_training_conversations()
        
        # Analyze model performance
        model_performance = self.analyze_model_performance()
        
        # System health metrics
        system_health = self._get_system_health_metrics()
        
        # Generate summary
        analysis_summary = {
            "timestamp": datetime.now().isoformat(),
            "data_sources": {
                "test_results": str(self.test_results_file),
                "training_data": str(self.training_file),
                "exists": {
                    "test_results": self.test_results_file.exists(),
                    "training_data": self.training_file.exists()
                }
            },
            "test_metrics": {
                "total_tests": test_metrics.total_tests,
                "success_rate": test_metrics.success_rate,
                "avg_duration_ms": test_metrics.avg_duration_ms,
                "models_tested": test_metrics.models_tested,
                "test_categories": test_metrics.test_categories
            },
            "training_metrics": {
                "total_conversations": training_metrics.get("total_conversations", 0),
                "total_messages": training_metrics.get("total_messages", 0),
                "avg_quality_score": training_metrics.get("avg_quality_score", 0),
                "avg_training_value": training_metrics.get("avg_training_value", 0)
            },
            "model_performance": {
                "total_models": len(model_performance),
                "models": [
                    {
                        "name": m.model_name,
                        "provider": m.provider,
                        "success_rate": m.success_rate,
                        "avg_duration_ms": m.avg_duration_ms,
                        "total_requests": m.total_requests
                    }
                    for m in model_performance
                ]
            },
            "system_health": system_health,
            "recommendations": self._generate_recommendations(test_metrics, training_metrics, model_performance)
        }
        
        self._last_analysis = analysis_summary
        return analysis_summary
    
    def get_data_source_columns(self, data_source: str) -> Dict[str, List[str]]:
        """Get relevant columns for a specific data source"""
        column_definitions = {
            "test_results": {
                "columns": [
                    "test_name",
                    "status", 
                    "duration_ms",
                    "timestamp",
                    "error_message"
                ],
                "display_names": {
                    "test_name": "Test Name",
                    "status": "Status",
                    "duration_ms": "Duration (ms)",
                    "timestamp": "Timestamp",
                    "error_message": "Error Message"
                },
                "description": "Test execution results and performance metrics"
            },
            "training_data": {
                "columns": [
                    "client_name",
                    "date",
                    "message_count", 
                    "quality_score",
                    "training_value"
                ],
                "display_names": {
                    "client_name": "Client Name",
                    "date": "Date",
                    "message_count": "Message Count",
                    "quality_score": "Quality Score",
                    "training_value": "Training Value"
                },
                "description": "Training conversation data with quality metrics"
            },
            "model_performance": {
                "columns": [
                    "name",
                    "provider",
                    "success_rate",
                    "avg_duration",
                    "total_requests",
                    "last_used"
                ],
                "display_names": {
                    "name": "Model Name",
                    "provider": "Provider",
                    "success_rate": "Success Rate (%)",
                    "avg_duration": "Avg Duration (ms)",
                    "total_requests": "Total Requests",
                    "last_used": "Last Used"
                },
                "description": "Model performance and usage statistics"
            },
            "validation_metrics": {
                "columns": [
                    "validation_type",
                    "pass_rate",
                    "total_validations",
                    "avg_quality",
                    "last_validation"
                ],
                "display_names": {
                    "validation_type": "Validation Type",
                    "pass_rate": "Pass Rate (%)",
                    "total_validations": "Total Validations",
                    "avg_quality": "Avg Quality",
                    "last_validation": "Last Validation"
                },
                "description": "Response validation and quality metrics"
            },
            "system_health": {
                "columns": [
                    "overall_score",
                    "cpu_usage_percent",
                    "memory_usage_percent",
                    "disk_usage_percent",
                    "critical_issues"
                ],
                "display_names": {
                    "overall_score": "Overall Score",
                    "cpu_usage_percent": "CPU Usage (%)",
                    "memory_usage_percent": "Memory Usage (%)",
                    "disk_usage_percent": "Disk Usage (%)",
                    "critical_issues": "Critical Issues"
                },
                "description": "System health and resource monitoring"
            }
        }
        
        return column_definitions.get(data_source, {
            "columns": [],
            "display_names": {},
            "description": "Unknown data source"
        })
    
    def get_filtered_columns_for_data_source(self, data_source: str, data: Any) -> Dict[str, Any]:
        """Get columns and filters specific to a data source with actual data validation"""
        base_columns = self.get_data_source_columns(data_source)
        
        # Validate columns against actual data
        if data_source == "test_results":
            return self._get_test_results_columns(data)
        elif data_source == "training_data":
            return self._get_training_data_columns(data)
        elif data_source == "model_performance":
            return self._get_model_performance_columns(data)
        elif data_source == "validation_metrics":
            return self._get_validation_columns(data)
        elif data_source == "system_health":
            return self._get_system_health_columns(data)
        else:
            return base_columns
    
    def _get_test_results_columns(self, data: Any) -> Dict[str, Any]:
        """Get test results columns with actual data validation"""
        if not data or 'test_results' not in data:
            return self.get_data_source_columns("test_results")
        
        # Analyze actual test data to find available fields
        available_fields = set()
        if data.get('test_results'):
            for test in data['test_results']:
                available_fields.update(test.keys())
                if 'details' in test and isinstance(test['details'], dict):
                    available_fields.update(test['details'].keys())
                    if 'result' in test['details'] and isinstance(test['details']['result'], dict):
                        available_fields.update(test['details']['result'].keys())
        
        # Filter columns to only those that exist in the data
        base_columns = self.get_data_source_columns("test_results")
        valid_columns = [col for col in base_columns["columns"] if col in available_fields]
        
        return {
            "columns": valid_columns,
            "display_names": {col: base_columns["display_names"].get(col, col) for col in valid_columns},
            "description": base_columns["description"],
            "available_filters": {
                "status": list(set(test.get('status', '') for test in data.get('test_results', []) if test.get('status'))),
                "duration_ranges": ["0-10ms", "10-100ms", "100ms-1s", ">1s"],
                "test_categories": list(set(test.get('test_name', '').split()[0] for test in data.get('test_results', []) if test.get('test_name')))
            }
        }
    
    def _get_training_data_columns(self, data: Any) -> Dict[str, Any]:
        """Get training data columns with actual data validation"""
        if not data or 'conversations' not in data:
            return self.get_data_source_columns("training_data")
        
        base_columns = self.get_data_source_columns("training_data")
        
        # Validate columns exist in actual data
        if data['conversations']:
            sample_conv = data['conversations'][0]
            valid_columns = [col for col in base_columns["columns"] if col in sample_conv]
        else:
            valid_columns = base_columns["columns"]
        
        return {
            "columns": valid_columns,
            "display_names": {col: base_columns["display_names"].get(col, col) for col in valid_columns},
            "description": base_columns["description"],
            "available_filters": {
                "client_names": list(set(conv.get('client_name', '') for conv in data.get('conversations', []) if conv.get('client_name'))),
                "quality_ranges": ["1-3", "4-6", "7-9", "10"],
                "message_count_ranges": ["1-5", "6-10", "11-15", "16+"]
            }
        }
    
    def _get_model_performance_columns(self, data: Any) -> Dict[str, Any]:
        """Get model performance columns with actual data validation"""
        if not data or 'models' not in data:
            return self.get_data_source_columns("model_performance")
        
        base_columns = self.get_data_source_columns("model_performance")
        
        # Validate columns exist in actual data
        if data['models']:
            sample_model = data['models'][0]
            valid_columns = [col for col in base_columns["columns"] if col in sample_model]
        else:
            valid_columns = base_columns["columns"]
        
        return {
            "columns": valid_columns,
            "display_names": {col: base_columns["display_names"].get(col, col) for col in valid_columns},
            "description": base_columns["description"],
            "available_filters": {
                "providers": list(set(model.get('provider', '') for model in data.get('models', []) if model.get('provider'))),
                "success_rate_ranges": ["0-50%", "51-75%", "76-90%", "91-100%"],
                "duration_ranges": ["0-100ms", "100ms-1s", "1s-5s", ">5s"]
            }
        }
    
    def _get_validation_columns(self, data: Any) -> Dict[str, Any]:
        """Get validation metrics columns with actual data validation"""
        if not data or 'metrics' not in data:
            return self.get_data_source_columns("validation_metrics")
        
        base_columns = self.get_data_source_columns("validation_metrics")
        
        # Validate columns exist in actual data
        if data['metrics']:
            sample_metric = data['metrics'][0]
            valid_columns = [col for col in base_columns["columns"] if col in sample_metric]
        else:
            valid_columns = base_columns["columns"]
        
        return {
            "columns": valid_columns,
            "display_names": {col: base_columns["display_names"].get(col, col) for col in valid_columns},
            "description": base_columns["description"],
            "available_filters": {
                "validation_types": list(set(metric.get('validation_type', '') for metric in data.get('metrics', []) if metric.get('validation_type'))),
                "pass_rate_ranges": ["0-50%", "51-75%", "76-90%", "91-100%"]
            }
        }
    
    def _get_system_health_columns(self, data: Any) -> Dict[str, Any]:
        """Get system health columns with actual data validation"""
        if not data or 'health_metrics' not in data:
            return self.get_data_source_columns("system_health")
        
        base_columns = self.get_data_source_columns("system_health")
        
        # Validate columns exist in actual data
        health_metrics = data.get('health_metrics', {})
        valid_columns = [col for col in base_columns["columns"] if col in health_metrics]
        
        return {
            "columns": valid_columns,
            "display_names": {col: base_columns["display_names"].get(col, col) for col in valid_columns},
            "description": base_columns["description"],
            "available_filters": {
                "health_levels": ["Critical", "Warning", "Healthy", "Optimal"],
                "resource_types": ["CPU", "Memory", "Disk", "Network"]
            }
        }
    
    def _extract_models_from_tests(self, test_results: List[Dict]) -> List[str]:
        """Extract unique models from test results"""
        models = set()
        for test in test_results:
            model_info = self._extract_model_info(test)
            if model_info:
                models.add(f"{model_info['provider']}:{model_info['model_name']}")
        return list(models)
    
    def _extract_model_info(self, test: Dict) -> Optional[Dict[str, str]]:
        """Extract model information from test details"""
        details = test.get('details', {})
        result = details.get('result', {})
        
        # Look for model info in various places
        model_name = None
        provider = None
        
        # Check direct model field
        if 'model' in result:
            model_name = result['model']
            provider = self._infer_provider_from_model(model_name)
        
        # Check configuration results
        elif 'current_values' in result:
            current = result['current_values']
            if 'model_name' in current:
                model_name = current['model_name']
                provider = current.get('current_provider', 'unknown')
        
        # Check expected values
        elif 'expected_values' in result:
            expected = result['expected_values']
            if 'system_config' in expected:
                provider = expected['system_config'].get('default_provider', 'unknown')
        
        if model_name and provider:
            return {
                'key': f"{provider}:{model_name}",
                'model_name': model_name,
                'provider': provider
            }
        
        return None
    
    def _infer_provider_from_model(self, model_name: str) -> str:
        """Infer provider from model name"""
        model_lower = model_name.lower()
        
        if any(x in model_lower for x in ['gpt', 'claude', 'anthropic']):
            return 'openai/anthropic'
        elif any(x in model_lower for x in ['llama', 'qwen', 'mistral']):
            return 'ollama'
        elif any(x in model_lower for x in ['runpod', 'pod']):
            return 'runpod'
        else:
            return 'unknown'
    
    def _categorize_tests(self, test_results: List[Dict]) -> Dict[str, int]:
        """Categorize tests by type"""
        categories = defaultdict(int)
        
        for test in test_results:
            test_name = test.get('test_name', '').lower()
            
            if 'config' in test_name or 'setting' in test_name:
                categories['Configuration'] += 1
            elif 'model' in test_name:
                categories['Model Management'] += 1
            elif 'api' in test_name or 'endpoint' in test_name:
                categories['API'] += 1
            elif 'auth' in test_name or 'security' in test_name:
                categories['Security'] += 1
            elif 'performance' in test_name or 'benchmark' in test_name:
                categories['Performance'] += 1
            else:
                categories['Other'] += 1
        
        return dict(categories)
    
    def _analyze_performance_distribution(self, durations: List[float]) -> Dict[str, int]:
        """Analyze performance distribution"""
        if not durations:
            return {}
        
        # Categorize by duration ranges
        distribution = {
            "Fast (<10ms)": 0,
            "Medium (10-100ms)": 0,
            "Slow (100ms-1s)": 0,
            "Very Slow (>1s)": 0
        }
        
        for duration in durations:
            if duration < 10:
                distribution["Fast (<10ms)"] += 1
            elif duration < 100:
                distribution["Medium (10-100ms)"] += 1
            elif duration < 1000:
                distribution["Slow (100ms-1s)"] += 1
            else:
                distribution["Very Slow (>1s)"] += 1
        
        return distribution
    
    def _calculate_quality_metrics(self, test_results: List[Dict]) -> Dict[str, float]:
        """Calculate quality metrics from test results"""
        if not test_results:
            return {}
        
        # Calculate various quality indicators
        total_tests = len(test_results)
        passed_tests = sum(1 for t in test_results if t.get('status') == 'PASS')
        
        # Duration-based quality (faster is better, up to a point)
        durations = [t.get('duration_ms', 0) for t in test_results]
        avg_duration = statistics.mean(durations) if durations else 0
        
        # Error rate
        error_rate = sum(1 for t in test_results if t.get('error_message')) / total_tests if total_tests > 0 else 0
        
        # Consistency (standard deviation of durations)
        duration_std = statistics.stdev(durations) if len(durations) > 1 else 0
        
        return {
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "avg_duration_ms": avg_duration,
            "error_rate": error_rate * 100,
            "duration_consistency": max(0, 100 - (duration_std / avg_duration * 100)) if avg_duration > 0 else 0
        }
    
    def _calculate_conversation_quality(self, conv: Dict, message_count: int) -> float:
        """Calculate quality score for a training conversation"""
        date_str = conv.get('date', '')
        
        # Base quality on message count (more messages = higher quality)
        base_quality = min(10.0, message_count * 0.5)
        
        # Adjust for recency (newer conversations get bonus)
        try:
            conv_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            days_old = (datetime.now() - conv_date).days
            recency_bonus = max(0, (365 - days_old) / 365 * 2)  # Up to 2 points for recency
            base_quality += recency_bonus
        except:
            pass
        
        return min(10.0, max(1.0, base_quality))
    
    def _calculate_training_value(self, conv: Dict, message_count: int) -> float:
        """Training value based on message count and complexity"""
        # Training value based on message count and complexity
        if message_count >= 20:
            return 10.0
        elif message_count >= 15:
            return 8.5
        elif message_count >= 10:
            return 7.0
        elif message_count >= 5:
            return 5.0
        else:
            return 3.0
    
    def _analyze_quality_distribution(self, scores: List[float]) -> Dict[str, int]:
        """Analyze distribution of quality scores"""
        if not scores:
            return {}
        
        distribution = {
            "Excellent (9-10)": 0,
            "Good (7-8.9)": 0,
            "Average (5-6.9)": 0,
            "Below Average (3-4.9)": 0,
            "Poor (1-2.9)": 0
        }
        
        for score in scores:
            if score >= 9:
                distribution["Excellent (9-10)"] += 1
            elif score >= 7:
                distribution["Good (7-8.9)"] += 1
            elif score >= 5:
                distribution["Average (5-6.9)"] += 1
            elif score >= 3:
                distribution["Below Average (3-4.9)"] += 1
            else:
                distribution["Poor (1-2.9)"] += 1
        
        return distribution
    
    def _estimate_total_tokens(self, tests: List[Dict]) -> int:
        """Estimate total tokens from test results"""
        total_tokens = 0
        
        for test_data in tests:
            test = test_data['test']
            details = test.get('details', {})
            result = details.get('result', {})
            
            # Look for token usage in various places
            if 'usage' in result:
                usage = result['usage']
                if 'total_tokens' in usage:
                    total_tokens += usage['total_tokens']
                elif 'prompt_tokens' in usage and 'completion_tokens' in usage:
                    total_tokens += usage['prompt_tokens'] + usage['completion_tokens']
            
            # Estimate based on test name length if no usage data
            else:
                test_name = test.get('test_name', '')
                # Rough estimate: 1 token ≈ 4 characters
                estimated_tokens = len(test_name) // 4
                total_tokens += estimated_tokens
        
        return total_tokens
    
    def _extract_quality_scores(self, tests: List[Dict]) -> List[float]:
        """Extract quality scores from test results"""
        scores = []
        
        for test_data in tests:
            test = test_data['test']
            details = test.get('details', {})
            result = details.get('result', {})
            
            # Look for quality metrics
            if 'quality_score' in result:
                scores.append(float(result['quality_score']))
            elif 'estimated_quality_score' in result:
                scores.append(float(result['estimated_quality_score']))
            else:
                # Estimate quality based on test success and duration
                status = test.get('status', 'FAIL')
                duration = test.get('duration_ms', 0)
                
                if status == 'PASS':
                    # Faster tests get higher quality scores
                    quality = max(5.0, 10.0 - (duration / 100))
                    scores.append(quality)
                else:
                    scores.append(3.0)  # Failed tests get lower scores
        
        return scores
    
    def _get_system_health_metrics(self) -> Dict[str, Any]:
        """Get system health metrics using psutil"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Process info
            current_process = psutil.Process()
            process_memory = current_process.memory_info()
            
            return {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_usage_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "process_memory_mb": round(process_memory.rss / (1024**2), 2),
                "overall_score": self._calculate_health_score(cpu_percent, memory.percent, disk.percent),
                "critical_issues": 0 if cpu_percent < 90 and memory.percent < 90 else 1,
                "recommendations": self._generate_health_recommendations(cpu_percent, memory.percent, disk.percent)
            }
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {
                "overall_score": 0,
                "critical_issues": 1,
                "error": str(e)
            }
    
    def _calculate_health_score(self, cpu: float, memory: float, disk: float) -> float:
        """Calculate overall health score"""
        # Lower usage = higher score
        cpu_score = max(0, 100 - cpu)
        memory_score = max(0, 100 - memory)
        disk_score = max(0, 100 - disk)
        
        # Weighted average
        return (cpu_score * 0.4 + memory_score * 0.4 + disk_score * 0.2)
    
    def _generate_health_recommendations(self, cpu: float, memory: float, disk: float) -> List[str]:
        """Generate health recommendations"""
        recommendations = []
        
        if cpu > 80:
            recommendations.append("High CPU usage detected - consider optimizing processes")
        if memory > 80:
            recommendations.append("High memory usage - consider freeing up memory")
        if disk > 90:
            recommendations.append("Disk space critical - clean up unnecessary files")
        
        if not recommendations:
            recommendations.append("System health is good")
        
        return recommendations
    
    def _generate_recommendations(self, test_metrics: BenchmarkMetrics, 
                                training_metrics: Dict, 
                                model_performance: List[ModelPerformance]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Test-related recommendations
        if test_metrics.success_rate < 95:
            recommendations.append(f"Test success rate is {test_metrics.success_rate:.1f}% - investigate failures")
        
        if test_metrics.avg_duration_ms > 1000:
            recommendations.append(f"Average test duration is {test_metrics.avg_duration_ms:.1f}ms - optimize slow tests")
        
        # Training-related recommendations
        avg_quality = training_metrics.get("avg_quality_score", 0)
        if avg_quality < 7.0:
            recommendations.append(f"Training quality score is {avg_quality:.1f}/10 - improve conversation quality")
        
        # Model performance recommendations
        for model in model_performance:
            if model.success_rate < 90:
                recommendations.append(f"Model {model.model_name} has low success rate ({model.success_rate:.1f}%)")
            if model.avg_duration_ms > 5000:
                recommendations.append(f"Model {model.model_name} is slow ({model.avg_duration_ms:.1f}ms avg)")
        
        if not recommendations:
            recommendations.append("All systems performing well - continue monitoring")
        
        return recommendations
    
    def _create_empty_metrics(self) -> BenchmarkMetrics:
        """Create empty metrics when data is not available"""
        return BenchmarkMetrics(
            total_tests=0,
            passed_tests=0,
            failed_tests=0,
            success_rate=0.0,
            avg_duration_ms=0.0,
            total_duration_ms=0.0,
            models_tested=[],
            test_categories={},
            performance_distribution={},
            quality_metrics={}
        )
    
    def _create_empty_training_metrics(self) -> Dict[str, Any]:
        """Create empty training metrics when data is not available"""
        return {
            "total_conversations": 0,
            "total_threads": 0,
            "total_messages": 0,
            "avg_messages_per_conversation": 0,
            "avg_quality_score": 0,
            "avg_training_value": 0,
            "conversations": [],
            "quality_distribution": {},
            "training_value_distribution": {},
            "processing_date": "Unknown"
        }

# Convenience functions for easy use
def create_llm_analyzer(project_root: str = ".") -> LLMResponseAnalyzer:
    """Create an LLM response analyzer instance"""
    return LLMResponseAnalyzer(project_root)

def analyze_llm_responses(project_root: str = ".") -> Dict[str, Any]:
    """Quick analysis of LLM responses"""
    analyzer = LLMResponseAnalyzer(project_root)
    return analyzer.get_comprehensive_analysis()

def get_test_metrics(project_root: str = ".") -> BenchmarkMetrics:
    """Get test metrics quickly"""
    analyzer = LLMResponseAnalyzer(project_root)
    return analyzer.analyze_test_results()

def get_training_metrics(project_root: str = ".") -> Dict[str, Any]:
    """Get training metrics quickly"""
    analyzer = LLMResponseAnalyzer(project_root)
    return analyzer.analyze_training_conversations()
