#!/usr/bin/env python3
"""
Type Validation Utilities with Beartype
=======================================

Provides type validation decorators and utilities using beartype for
runtime type checking with clear, human-readable error messages.
"""

from typing import Dict, List, Optional, Union, Any, Callable, TypeVar
from functools import wraps
import json

try:
    from beartype import beartype
    from beartype.roar import BeartypeException
    BEARTYPE_AVAILABLE = True
except ImportError:
    BEARTYPE_AVAILABLE = False
    # Fallback decorator when beartype is not available
    def beartype(func):
        """Fallback decorator when beartype is not installed"""
        return func

from src.utils.logger import logger

# Type aliases for common patterns
ConfigDict = Dict[str, Any]
ModelList = List[Dict[str, Any]]
ProviderConfig = Dict[str, Union[str, bool, int, float]]
CacheConfig = Dict[str, Union[bool, int, float]]

# Generic type for functions
F = TypeVar('F', bound=Callable[..., Any])

class TypeValidationError(Exception):
    """Custom exception for type validation errors"""
    
    def __init__(self, message: str, expected_type: str = None, actual_type: str = None, value: Any = None):
        self.expected_type = expected_type
        self.actual_type = actual_type
        self.value = value
        super().__init__(message)

def validate_and_log_types(func: F) -> F:
    """
    Enhanced decorator that combines beartype with custom logging
    
    Usage:
        @validate_and_log_types
        def my_function(param: str) -> bool:
            return len(param) > 0
    """
    if BEARTYPE_AVAILABLE:
        # Apply beartype first
        func = beartype(func)
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except BeartypeException as e:
            # Log beartype errors with context
            logger.error(f"🐻 Type validation error in {func.__name__}: {e}")
            logger.error(f"📋 Function signature: {func.__annotations__}")
            logger.error(f"📥 Arguments: args={args}, kwargs={kwargs}")
            
            # Re-raise with enhanced message
            raise TypeValidationError(
                f"Type validation failed in {func.__name__}: {str(e)}",
                expected_type=getattr(e, 'expected_type', None),
                actual_type=getattr(e, 'actual_type', None),
                value=getattr(e, 'value', None)
            ) from e
        except Exception as e:
            # Log other errors for debugging
            logger.error(f"❌ Error in {func.__name__}: {e}")
            raise
    
    return wrapper

def validate_config_structure(config: ConfigDict, required_keys: List[str]) -> bool:
    """
    Validate configuration dictionary structure
    
    Args:
        config: Configuration dictionary to validate
        required_keys: List of required keys
        
    Returns:
        True if valid
        
    Raises:
        TypeValidationError: If validation fails
    """
    if not isinstance(config, dict):
        raise TypeValidationError(
            f"Expected configuration to be a dictionary, got {type(config).__name__}",
            expected_type="dict",
            actual_type=type(config).__name__,
            value=config
        )
    
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise TypeValidationError(
            f"Missing required configuration keys: {missing_keys}",
            expected_type=f"dict with keys {required_keys}",
            actual_type=f"dict with keys {list(config.keys())}",
            value=config
        )
    
    return True

def validate_provider_config(provider_config: ProviderConfig) -> bool:
    """
    Validate provider configuration structure
    
    Args:
        provider_config: Provider configuration to validate
        
    Returns:
        True if valid
        
    Raises:
        TypeValidationError: If validation fails
    """
    required_keys = ['enabled', 'name']
    optional_keys = ['priority', 'timeout', 'max_retries', 'api_key', 'endpoint']
    
    validate_config_structure(provider_config, required_keys)
    
    # Validate specific field types
    if not isinstance(provider_config.get('enabled'), bool):
        raise TypeValidationError(
            f"Provider 'enabled' must be boolean, got {type(provider_config.get('enabled')).__name__}",
            expected_type="bool",
            actual_type=type(provider_config.get('enabled')).__name__,
            value=provider_config.get('enabled')
        )
    
    if not isinstance(provider_config.get('name'), str):
        raise TypeValidationError(
            f"Provider 'name' must be string, got {type(provider_config.get('name')).__name__}",
            expected_type="str",
            actual_type=type(provider_config.get('name')).__name__,
            value=provider_config.get('name')
        )
    
    return True

def validate_caching_config(cache_config: CacheConfig) -> bool:
    """
    Validate caching configuration structure
    
    Args:
        cache_config: Caching configuration to validate
        
    Returns:
        True if valid
        
    Raises:
        TypeValidationError: If validation fails
    """
    required_keys = ['enabled']
    optional_keys = ['threshold', 'max_cache_age_hours', 'max_responses']
    
    validate_config_structure(cache_config, required_keys)
    
    # Validate specific field types
    if not isinstance(cache_config.get('enabled'), bool):
        raise TypeValidationError(
            f"Cache 'enabled' must be boolean, got {type(cache_config.get('enabled')).__name__}",
            expected_type="bool",
            actual_type=type(cache_config.get('enabled')).__name__,
            value=cache_config.get('enabled')
        )
    
    threshold = cache_config.get('threshold')
    if threshold is not None and not isinstance(threshold, (int, float)):
        raise TypeValidationError(
            f"Cache 'threshold' must be number, got {type(threshold).__name__}",
            expected_type="float",
            actual_type=type(threshold).__name__,
            value=threshold
        )
    
    if threshold is not None and not (0.0 <= threshold <= 1.0):
        raise TypeValidationError(
            f"Cache 'threshold' must be between 0.0 and 1.0, got {threshold}",
            expected_type="float in range [0.0, 1.0]",
            actual_type=f"float({threshold})",
            value=threshold
        )
    
    return True

@validate_and_log_types
def safe_json_parse(json_string: str) -> Union[Dict[str, Any], List[Any]]:
    """
    Safely parse JSON string with type validation
    
    Args:
        json_string: JSON string to parse
        
    Returns:
        Parsed JSON object
        
    Raises:
        TypeValidationError: If parsing fails or result is not dict/list
    """
    try:
        result = json.loads(json_string)
        if not isinstance(result, (dict, list)):
            raise TypeValidationError(
                f"JSON must parse to dict or list, got {type(result).__name__}",
                expected_type="dict or list",
                actual_type=type(result).__name__,
                value=result
            )
        return result
    except json.JSONDecodeError as e:
        raise TypeValidationError(
            f"Invalid JSON format: {str(e)}",
            expected_type="valid JSON string",
            actual_type="invalid JSON",
            value=json_string[:100] + "..." if len(json_string) > 100 else json_string
        ) from e

@validate_and_log_types
def validate_model_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate AI model response structure
    
    Args:
        response: Model response to validate
        
    Returns:
        Validated response
        
    Raises:
        TypeValidationError: If response structure is invalid
    """
    required_keys = ['status']
    optional_keys = ['response', 'error', 'provider', 'model', 'response_metadata']
    
    validate_config_structure(response, required_keys)
    
    status = response.get('status')
    if status not in ['success', 'error']:
        raise TypeValidationError(
            f"Response status must be 'success' or 'error', got '{status}'",
            expected_type="'success' or 'error'",
            actual_type=f"'{status}'",
            value=status
        )
    
    if status == 'success' and 'response' not in response:
        raise TypeValidationError(
            "Successful response must include 'response' field",
            expected_type="dict with 'response' field",
            actual_type="dict without 'response' field",
            value=response
        )
    
    if status == 'error' and 'error' not in response:
        raise TypeValidationError(
            "Error response must include 'error' field",
            expected_type="dict with 'error' field",
            actual_type="dict without 'error' field",
            value=response
        )
    
    return response

def create_type_safe_wrapper(expected_types: Dict[str, type]):
    """
    Create a decorator that validates function arguments against expected types
    
    Args:
        expected_types: Dictionary mapping parameter names to expected types
        
    Returns:
        Decorator function
        
    Example:
        @create_type_safe_wrapper({'name': str, 'age': int, 'active': bool})
        def update_user(name, age, active):
            pass
    """
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function parameter names
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate each argument
            for param_name, expected_type in expected_types.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if not isinstance(value, expected_type):
                        raise TypeValidationError(
                            f"Parameter '{param_name}' expected {expected_type.__name__}, got {type(value).__name__}",
                            expected_type=expected_type.__name__,
                            actual_type=type(value).__name__,
                            value=value
                        )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Export commonly used decorators and validators
__all__ = [
    'beartype',
    'validate_and_log_types',
    'validate_config_structure',
    'validate_provider_config',
    'validate_caching_config',
    'safe_json_parse',
    'validate_model_response',
    'create_type_safe_wrapper',
    'TypeValidationError',
    'ConfigDict',
    'ModelList',
    'ProviderConfig',
    'CacheConfig',
    'BEARTYPE_AVAILABLE'
]
