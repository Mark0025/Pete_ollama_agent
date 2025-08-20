#!/usr/bin/env python3
"""
🎯 WhatsWorking - Unified Codebase Analysis & Documentation Module

A comprehensive module that provides real-time analysis of what's working
in your codebase, generates documentation, and tracks system health.

Features:
- AST-based codebase analysis with Mermaid diagrams
- Feature health tracking and reporting  
- Test results aggregation and documentation
- System health monitoring
- Real-time documentation generation

Usage:
    from whats_working import WhatsWorking
    
    # Initialize the system
    ww = WhatsWorking()
    
    # Generate comprehensive analysis
    ww.analyze_codebase()
    
    # Track feature health
    ww.track_features()
    
    # Update test results
    ww.update_test_results()
    
    # Get system health report
    health = ww.get_system_health()
"""

from .core import WhatsWorking
from .analyzer import CodebaseAnalyzer
from .feature_tracker import FeatureTracker
from .updater import TestResultsUpdater
from .health_monitor import SystemHealthMonitor

__version__ = "1.0.0"
__author__ = "Ollama Agent Team"
__all__ = [
    "WhatsWorking",
    "CodebaseAnalyzer", 
    "FeatureTracker",
    "TestResultsUpdater",
    "SystemHealthMonitor"
]

# Create a default instance for easy access
whats_working = WhatsWorking()
