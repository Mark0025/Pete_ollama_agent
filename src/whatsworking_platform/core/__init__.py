#!/usr/bin/env python3
"""
Core components for the Master WhatsWorking Platform

Contains the central engine, data models, and configuration management
that drives the entire system.
"""

from .engine import WhatsWorkingEngine
from .models import ProjectState, HealthMetrics, GoalStatus
from .config import PlatformConfig

__all__ = [
    'WhatsWorkingEngine',
    'ProjectState',
    'HealthMetrics', 
    'GoalStatus',
    'PlatformConfig'
]
