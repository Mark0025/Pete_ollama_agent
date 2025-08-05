"""
PeteOllama V1 - Logging Configuration with Loguru
==================================================

Centralized loguru logging setup for the application.
"""

import sys
from pathlib import Path
from loguru import logger
import os

def setup_logger(name: str = None, log_level: str = "INFO") -> None:
    """
    Setup loguru logger with console and file output
    
    Args:
        name: Logger name (ignored for loguru, but kept for compatibility)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    
    # Remove default handler
    logger.remove()
    
    # Console handler with colors and nice formatting
    logger.add(
        sys.stdout,
        level=log_level.upper(),
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>",
        colorize=True
    )
    
    # File handler with rotation
    try:
        log_dir = Path("/app/logs")
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / "peteollama.log"
        
        logger.add(
            str(log_file),
            level=log_level.upper(),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            rotation="5 MB",
            retention="10 days",
            compression="zip"
        )
        
    except Exception as e:
        logger.warning(f"Could not setup file logging: {e}")

def get_logger(name: str = None):
    """Get loguru logger (always returns the same instance)"""
    return logger

# Setup the logger when module is imported - only if not already setup
if not logger._core.handlers:
    setup_logger()

# Make logger available as default export
__all__ = ["logger", "setup_logger", "get_logger"]