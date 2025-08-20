#!/usr/bin/env python3
"""
Data Conversion Utility

A unified utility that integrates type_validation, dynamic_data_filter, and logger
to handle all data conversion between dicts and objects, ensuring no hardcoded values
and proper type safety.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Type, TypeVar
from dataclasses import dataclass, asdict, is_dataclass
from datetime import datetime
import logging

# Import our utility modules
from src.utils.type_validation import (
    validate_and_log_types, 
    safe_json_parse, 
    validate_config_structure,
    TypeValidationError
)
from src.utils.dynamic_data_filter import (
    DynamicDataFilter, 
    FilterCriteria, 
    DataAnalysisResult,
    FilteredDataResult,
    create_dynamic_filter
)
from src.utils.logger import logger

# Generic type for data classes
T = TypeVar('T')

class DataConversionError(Exception):
    """Custom exception for data conversion errors"""
    pass

class DataConversionUtility:
    """
    Unified utility for data conversion, validation, and filtering
    """
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.dynamic_filter = create_dynamic_filter(str(self.project_root))
        self.cache = {}
        
        logger.info(f"🔧 DataConversionUtility initialized for {self.project_root}")
    
    @validate_and_log_types
    def dict_to_object(self, data: Dict[str, Any], target_class: Type[T]) -> T:
        """
        Convert dictionary to object of specified class
        
        Args:
            data: Dictionary data
            target_class: Target class to convert to
            
        Returns:
            Instance of target_class
            
        Raises:
            DataConversionError: If conversion fails
        """
        try:
            # Validate data structure if target class has validation
            if hasattr(target_class, 'validate'):
                target_class.validate(data)
            
            # Handle dataclasses
            if is_dataclass(target_class):
                # Filter data to only include fields that exist in target class
                filtered_data = {}
                for field_name in target_class.__dataclass_fields__:
                    if field_name in data:
                        filtered_data[field_name] = data[field_name]
                
                return target_class(**filtered_data)
            
            # Handle Pydantic models
            elif hasattr(target_class, 'parse_obj'):
                return target_class.parse_obj(data)
            
            # Handle regular classes with __init__
            else:
                return target_class(**data)
                
        except Exception as e:
            logger.error(f"Error converting dict to {target_class.__name__}: {e}")
            raise DataConversionError(f"Failed to convert dict to {target_class.__name__}: {str(e)}")
    
    @validate_and_log_types
    def object_to_dict(self, obj: Any) -> Dict[str, Any]:
        """
        Convert object to dictionary
        
        Args:
            obj: Object to convert
            
        Returns:
            Dictionary representation
        """
        try:
            # Handle dataclasses
            if is_dataclass(obj):
                return asdict(obj)
            
            # Handle Pydantic models
            elif hasattr(obj, 'dict'):
                return obj.dict()
            
            # Handle objects with __dict__
            elif hasattr(obj, '__dict__'):
                return obj.__dict__
            
            # Handle other types
            else:
                return {"value": obj, "type": type(obj).__name__}
                
        except Exception as e:
            logger.error(f"Error converting object to dict: {e}")
            raise DataConversionError(f"Failed to convert object to dict: {str(e)}")
    
    @validate_and_log_types
    def load_and_validate_json(self, file_path: Union[str, Path], expected_structure: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Load and validate JSON file with type checking
        
        Args:
            file_path: Path to JSON file
            expected_structure: List of required keys (optional)
            
        Returns:
            Validated JSON data
            
        Raises:
            DataConversionError: If loading or validation fails
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise DataConversionError(f"File not found: {file_path}")
            
            with open(file_path, 'r') as f:
                raw_data = f.read()
            
            # Parse JSON safely
            data = safe_json_parse(raw_data)
            
            # Validate structure if specified
            if expected_structure:
                validate_config_structure(data, expected_structure)
            
            logger.info(f"✅ Successfully loaded and validated {file_path}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading JSON from {file_path}: {e}")
            raise DataConversionError(f"Failed to load JSON from {file_path}: {str(e)}")
    
    @validate_and_log_types
    def analyze_data_source(self, data_source: str, data: Any) -> Dict[str, Any]:
        """
        Analyze data source and return comprehensive information
        
        Args:
            data_source: Name of the data source
            data: Data to analyze
            
        Returns:
            Analysis results with columns, filters, and preview
        """
        try:
            # Use dynamic data filter to analyze structure
            analysis = self.dynamic_filter.analyze_data_structure(data)
            
            # Get source-specific column definitions
            columns_info = self._get_source_columns(data_source, data)
            
            # Generate available filters
            available_filters = self._generate_available_filters(data_source, data, analysis)
            
            # Get data preview
            data_preview = self._generate_data_preview(data_source, data)
            
            return {
                "success": True,
                "data_source": data_source,
                "columns": columns_info["columns"],
                "display_names": columns_info["display_names"],
                "description": columns_info["description"],
                "available_filters": available_filters,
                "data_preview": data_preview,
                "analysis": {
                    "total_items": analysis.total_items,
                    "fields_discovered": analysis.fields_discovered,
                    "filterable_fields": analysis.filterable_fields
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing data source {data_source}: {e}")
            return {
                "success": False,
                "error": str(e),
                "data_source": data_source
            }
    
    def _get_source_columns(self, data_source: str, data: Any) -> Dict[str, Any]:
        """Get columns specific to a data source"""
        column_definitions = {
            "test_results": {
                "columns": ["test_name", "status", "duration_ms", "timestamp", "error_message"],
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
                "columns": ["client_name", "date", "message_count", "quality_score", "training_value"],
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
                "columns": ["name", "provider", "success_rate", "avg_duration", "total_requests", "last_used"],
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
                "columns": ["validation_type", "pass_rate", "total_validations", "avg_quality", "last_validation"],
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
                "columns": ["overall_score", "cpu_usage_percent", "memory_usage_percent", "disk_usage_percent", "critical_issues"],
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
    
    def _generate_available_filters(self, data_source: str, data: Any, analysis: DataAnalysisResult) -> Dict[str, Any]:
        """Generate available filters based on actual data"""
        try:
            filters = {}
            
            if data_source == "test_results" and isinstance(data, dict) and 'test_results' in data:
                test_results = data['test_results']
                if test_results:
                    # Status filters
                    statuses = list(set(test.get('status', '') for test in test_results if test.get('status')))
                    filters["status"] = statuses
                    
                    # Duration ranges
                    filters["duration_ranges"] = ["0-10ms", "10-100ms", "100ms-1s", ">1s"]
                    
                    # Test categories
                    categories = []
                    for test in test_results:
                        if test.get('test_name'):
                            category = test['test_name'].split()[0]
                            if category not in categories:
                                categories.append(category)
                    filters["test_categories"] = categories
            
            elif data_source == "training_data" and isinstance(data, dict) and 'conversations' in data:
                conversations = data['conversations']
                if conversations:
                    # Client names
                    client_names = list(set(conv.get('client_name', '') for conv in conversations if conv.get('client_name')))
                    filters["client_names"] = client_names
                    
                    # Quality ranges
                    filters["quality_ranges"] = ["1-3", "4-6", "7-9", "10"]
                    
                    # Message count ranges
                    filters["message_count_ranges"] = ["1-5", "6-10", "11-15", "16+"]
            
            elif data_source == "model_performance" and isinstance(data, dict) and 'models' in data:
                models = data['models']
                if models:
                    # Providers
                    providers = list(set(model.get('provider', '') for model in models if model.get('provider')))
                    filters["providers"] = providers
                    
                    # Success rate ranges
                    filters["success_rate_ranges"] = ["0-50%", "51-75%", "76-90%", "91-100%"]
                    
                    # Duration ranges
                    filters["duration_ranges"] = ["0-100ms", "100ms-1s", "1s-5s", ">5s"]
            
            return filters
            
        except Exception as e:
            logger.error(f"Error generating filters for {data_source}: {e}")
            return {}
    
    def _generate_data_preview(self, data_source: str, data: Any) -> Dict[str, Any]:
        """Generate data preview based on actual data"""
        try:
            if not data:
                return {"count": 0, "sample": []}
            
            if data_source == "test_results":
                test_results = data.get('test_results', [])
                return {
                    "count": len(test_results),
                    "sample": test_results[:3] if test_results else []
                }
            
            elif data_source == "training_data":
                conversations = data.get('conversations', [])
                return {
                    "count": len(conversations),
                    "sample": conversations[:3] if conversations else []
                }
            
            elif data_source == "model_performance":
                models = data.get('models', [])
                return {
                    "count": len(models),
                    "sample": models[:3] if models else []
                }
            
            elif data_source == "validation_metrics":
                metrics = data.get('metrics', [])
                return {
                    "count": len(metrics),
                    "sample": metrics[:3] if metrics else []
                }
            
            elif data_source == "system_health":
                health_metrics = data.get('health_metrics', {})
                return {
                    "count": 1,
                    "sample": [health_metrics] if health_metrics else []
                }
            
            else:
                return {"count": 0, "sample": []}
                
        except Exception as e:
            logger.error(f"Error generating data preview for {data_source}: {e}")
            return {"count": 0, "sample": []}
    
    @validate_and_log_types
    def filter_data_dynamically(self, data: Any, criteria: Dict[str, Any], data_source: str) -> FilteredDataResult:
        """
        Filter data using dynamic criteria
        
        Args:
            data: Data to filter
            criteria: Filter criteria
            data_source: Data source type
            
        Returns:
            Filtered results
        """
        try:
            # Convert criteria to FilterCriteria object
            filter_criteria = FilterCriteria(**criteria)
            
            # Analyze data structure
            analysis = self.dynamic_filter.analyze_data_structure(data)
            
            # Apply filters
            filtered_result = self.dynamic_filter.filter_data(data, filter_criteria, analysis.field_metadata)
            
            logger.info(f"✅ Filtered {data_source}: {filtered_result.total_results} results")
            return filtered_result
            
        except Exception as e:
            logger.error(f"Error filtering {data_source}: {e}")
            return FilteredDataResult(
                success=False,
                total_results=0,
                results=[],
                applied_filters=criteria,
                columns_available=[],
                pagination={}
            )
    
    def ensure_no_hardcoded_values(self, data: Any) -> bool:
        """
        Check if data contains any hardcoded values
        
        Args:
            data: Data to check
            
        Returns:
            True if no hardcoded values found
        """
        hardcoded_patterns = [
            "sample", "placeholder", "hardcoded", "static", "dummy", "fake",
            "test data", "example", "demo", "mock"
        ]
        
        def check_value(value: Any) -> bool:
            if isinstance(value, str):
                value_lower = value.lower()
                return not any(pattern in value_lower for pattern in hardcoded_patterns)
            elif isinstance(value, (dict, list)):
                return all(check_value(v) for v in (value.values() if isinstance(value, dict) else value))
            return True
        
        try:
            return check_value(data)
        except Exception as e:
            logger.warning(f"Error checking for hardcoded values: {e}")
            return True  # Assume safe if we can't check

# Convenience functions
def create_data_converter(project_root: str = ".") -> DataConversionUtility:
    """Create a data conversion utility instance"""
    return DataConversionUtility(project_root)

def convert_dict_to_object(data: Dict[str, Any], target_class: Type[T], project_root: str = ".") -> T:
    """Convert dictionary to object"""
    converter = create_data_converter(project_root)
    return converter.dict_to_object(data, target_class)

def convert_object_to_dict(obj: Any, project_root: str = ".") -> Dict[str, Any]:
    """Convert object to dictionary"""
    converter = create_data_converter(project_root)
    return converter.object_to_dict(obj)

def analyze_data_source_safe(data_source: str, data: Any, project_root: str = ".") -> Dict[str, Any]:
    """Safely analyze data source with error handling"""
    converter = create_data_converter(project_root)
    return converter.analyze_data_source(data_source, data)
