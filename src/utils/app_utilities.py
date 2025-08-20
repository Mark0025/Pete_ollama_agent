#!/usr/bin/env python3
"""
App Utilities - Master Utility Module
====================================

Comprehensive utility system for the entire Ollama Agent application.
Provides type safety, validation, and common functionality that can be
imported and used across all modules.
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import (
    Dict, List, Optional, Any, Union, TypeVar, 
    Callable, Type, get_type_hints, get_args
)
from datetime import datetime
from functools import wraps
import traceback

# Import our existing utilities
from utils.logger import logger
from utils.type_validation import beartype, TypeValidationError

# Type variables for generic functions
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])

class AppUtilities:
    """Master utility class providing common functionality across the app"""
    
    # ============================================================================
    # TYPE SAFETY UTILITIES
    # ============================================================================
    
    @staticmethod
    def safe_type_check(value: Any, expected_type: Type[T], default: T = None) -> T:
        """
        Safely check if a value matches expected type, return default if not
        
        Args:
            value: Value to check
            expected_type: Expected type
            default: Default value if type check fails
            
        Returns:
            Value if type matches, default otherwise
        """
        try:
            if isinstance(value, expected_type):
                return value
            else:
                logger.warning(f"Type mismatch: expected {expected_type.__name__}, got {type(value).__name__}")
                return default
        except Exception as e:
            logger.error(f"Type check error: {e}")
            return default
    
    @staticmethod
    def safe_dict_access(data: Dict[str, Any], key: str, default: Any = None, expected_type: Type[T] = None) -> Any:
        """
        Safely access dictionary values with type checking
        
        Args:
            data: Dictionary to access
            key: Key to look up
            default: Default value if key doesn't exist
            expected_type: Expected type for the value
            
        Returns:
            Value if found and type matches, default otherwise
        """
        try:
            if key not in data:
                return default
            
            value = data[key]
            
            if expected_type and not isinstance(value, expected_type):
                logger.warning(f"Type mismatch for key '{key}': expected {expected_type.__name__}, got {type(value).__name__}")
                return default
            
            return value
        except Exception as e:
            logger.error(f"Dictionary access error for key '{key}': {e}")
            return default
    
    # ============================================================================
    # VALIDATION UTILITIES
    # ============================================================================
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> bool:
        """
        Validate that required fields exist in data
        
        Args:
            data: Data to validate
            required_fields: List of required field names
            
        Returns:
            True if all required fields exist, False otherwise
        """
        try:
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                logger.error(f"Missing required fields: {missing_fields}")
                return False
            return True
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
    
    @staticmethod
    def validate_field_types(data: Dict[str, Any], field_types: Dict[str, Type]) -> bool:
        """
        Validate that fields match expected types
        
        Args:
            data: Data to validate
            field_types: Dictionary mapping field names to expected types
            
        Returns:
            True if all fields match expected types, False otherwise
        """
        try:
            for field, expected_type in field_types.items():
                if field in data and not isinstance(data[field], expected_type):
                    logger.error(f"Field '{field}' type mismatch: expected {expected_type.__name__}, got {type(data[field]).__name__}")
                    return False
            return True
        except Exception as e:
            logger.error(f"Type validation error: {e}")
            return False
    
    # ============================================================================
    # CONFIGURATION UTILITIES
    # ============================================================================
    
    @staticmethod
    def load_config_file(file_path: Union[str, Path], default_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Safely load configuration file with fallback
        
        Args:
            file_path: Path to configuration file
            default_data: Default data if file doesn't exist or fails to load
            
        Returns:
            Configuration data dictionary
        """
        try:
            file_path = Path(file_path)
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"✅ Loaded configuration from {file_path}")
                    return data
            else:
                logger.warning(f"⚠️ Configuration file not found: {file_path}")
                if default_data:
                    logger.info("📝 Using default configuration")
                    return default_data
                return {}
        except Exception as e:
            logger.error(f"❌ Error loading configuration from {file_path}: {e}")
            if default_data:
                logger.info("📝 Using default configuration due to error")
                return default_data
            return {}
    
    @staticmethod
    def save_config_file(file_path: Union[str, Path], data: Dict[str, Any]) -> bool:
        """
        Safely save configuration file
        
        Args:
            file_path: Path to save configuration file
            data: Configuration data to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Configuration saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Error saving configuration to {file_path}: {e}")
            return False
    
    # ============================================================================
    # ERROR HANDLING UTILITIES
    # ============================================================================
    
    @staticmethod
    def safe_execute(func: Callable[..., T], *args, default: T = None, **kwargs) -> T:
        """
        Safely execute a function with error handling
        
        Args:
            func: Function to execute
            *args: Function arguments
            default: Default value if function fails
            **kwargs: Function keyword arguments
            
        Returns:
            Function result or default value if execution fails
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"❌ Function execution failed: {func.__name__}: {e}")
            if default is not None:
                return default
            raise
    
    @staticmethod
    def error_boundary(func: F) -> F:
        """
        Decorator to add error boundary to functions
        
        Args:
            func: Function to wrap
            
        Returns:
            Wrapped function with error handling
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"❌ Error in {func.__name__}: {e}")
                logger.debug(f"Traceback: {traceback.format_exc()}")
                raise
        return wrapper
    
    # ============================================================================
    # PERFORMANCE UTILITIES
    # ============================================================================
    
    @staticmethod
    def timing_decorator(func: F) -> F:
        """
        Decorator to measure function execution time
        
        Args:
            func: Function to wrap
            
        Returns:
            Wrapped function with timing
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.debug(f"⏱️ {func.__name__} executed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"❌ {func.__name__} failed after {duration:.3f}s: {e}")
                raise
        return wrapper
    
    # ============================================================================
    # ENVIRONMENT UTILITIES
    # ============================================================================
    
    @staticmethod
    def get_env_var(key: str, default: Any = None, expected_type: Type[T] = None) -> Any:
        """
        Safely get environment variable with type conversion
        
        Args:
            key: Environment variable name
            default: Default value if not set
            expected_type: Expected type for the value
            
        Returns:
            Environment variable value or default
        """
        try:
            value = os.getenv(key, default)
            
            if value is None:
                return default
            
            # Type conversion based on expected type
            if expected_type:
                if expected_type == bool:
                    return str(value).lower() in ('true', '1', 'yes', 'on')
                elif expected_type == int:
                    return int(value)
                elif expected_type == float:
                    return float(value)
                elif expected_type == list:
                    return value.split(',') if value else []
                elif expected_type == dict:
                    return json.loads(value) if value else {}
            
            return value
        except Exception as e:
            logger.error(f"❌ Error getting environment variable {key}: {e}")
            return default
    
    # ============================================================================
    # IMPORT UTILITIES
    # ============================================================================
    
    @staticmethod
    def safe_import(module_name: str, default: Any = None) -> Any:
        """
        Safely import a module with fallback
        
        Args:
            module_name: Name of module to import
            default: Default value if import fails
            
        Returns:
            Imported module or default value
        """
        try:
            module = __import__(module_name)
            logger.debug(f"✅ Successfully imported {module_name}")
            return module
        except ImportError as e:
            logger.warning(f"⚠️ Failed to import {module_name}: {e}")
            return default
        except Exception as e:
            logger.error(f"❌ Unexpected error importing {module_name}: {e}")
            return default
    
    # ============================================================================
    # VALIDATION DECORATORS
    # ============================================================================
    
    @staticmethod
    def validate_inputs(*validators: Callable[[Any], bool]):
        """
        Decorator to validate function inputs
        
        Args:
            *validators: Validation functions to apply
            
        Returns:
            Decorator function
        """
        def decorator(func: F) -> F:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Apply validators to arguments
                for validator in validators:
                    if not validator(args):
                        raise ValueError(f"Input validation failed for {func.__name__}")
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def validate_output(expected_type: Type[T]):
        """
        Decorator to validate function output
        
        Args:
            expected_type: Expected return type
            
        Returns:
            Decorator function
        """
        def decorator(func: F) -> F:
            @wraps(func)
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                if not isinstance(result, expected_type):
                    raise TypeError(f"Output validation failed for {func.__name__}: expected {expected_type.__name__}, got {type(result).__name__}")
                return result
            return wrapper
        return decorator

# Create global instance for easy access
app_utils = AppUtilities()

# Export commonly used functions for direct import
safe_type_check = app_utils.safe_type_check
safe_dict_access = app_utils.safe_dict_access
validate_required_fields = app_utils.validate_required_fields
validate_field_types = app_utils.validate_field_types
load_config_file = app_utils.load_config_file
save_config_file = app_utils.save_config_file
safe_execute = app_utils.safe_execute
error_boundary = app_utils.error_boundary
timing_decorator = app_utils.timing_decorator
get_env_var = app_utils.get_env_var
safe_import = app_utils.safe_import

# Export decorators
validate_inputs = app_utils.validate_inputs
validate_output = app_utils.validate_output

# Export the main class for advanced usage
__all__ = [
    'AppUtilities', 'app_utils',
    'safe_type_check', 'safe_dict_access',
    'validate_required_fields', 'validate_field_types',
    'load_config_file', 'save_config_file',
    'safe_execute', 'error_boundary', 'timing_decorator',
    'get_env_var', 'safe_import',
    'validate_inputs', 'validate_output'
]
