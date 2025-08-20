#!/usr/bin/env python3
"""
🎯 Master WhatsWorking Platform

A unified system that enforces Goal-First Thinking, Validation Gates, 
Critical Path Focus, Architectural Decision Tracking, and Health Monitoring
for LLMs through MCP integration.

This platform consolidates the best functionality from scattered whatsworking
implementations into a cohesive, methodology-driven system.
"""

__version__ = "1.0.0"
__author__ = "WhatsWorking Team"

from .core.engine import WhatsWorkingEngine
from .core.models import ProjectState, HealthMetrics, GoalStatus
from .collectors.codebase_analyzer import CodebaseAnalyzer
from .collectors.feature_tracker import StatusReporter
from .collectors.infrastructure_monitor import CodeFinder
from .cli.main import WhatsWorkingCLI

__all__ = [
    'WhatsWorkingEngine',
    'ProjectState', 
    'HealthMetrics',
    'GoalStatus',
    'CodebaseAnalyzer',
    'StatusReporter',
    'CodeFinder',
    'WhatsWorkingCLI'
]
