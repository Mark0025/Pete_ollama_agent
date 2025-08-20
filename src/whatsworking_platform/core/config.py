#!/usr/bin/env python3
"""
Configuration management for the Master WhatsWorking Platform

Centralized configuration for all platform components and behavior.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class PlatformConfig:
    """Configuration for the Master WhatsWorking Platform"""
    
    # Core settings
    project_name: str = "WhatsWorking Platform"
    version: str = "1.0.0"
    debug_mode: bool = False
    
    # Methodology enforcement settings
    strict_methodology_enforcement: bool = True
    require_goal_alignment: bool = True
    require_validation_gates: bool = True
    require_critical_path_focus: bool = True
    require_architectural_tracking: bool = True
    require_health_monitoring: bool = True
    
    # Analysis settings
    codebase_analysis_enabled: bool = True
    feature_tracking_enabled: bool = True
    infrastructure_monitoring_enabled: bool = True
    test_aggregation_enabled: bool = True
    
    # Output settings
    reports_directory: str = "DEV_MAN/whatsworking"
    log_level: str = "INFO"
    output_format: str = "markdown"
    
    # Integration settings
    project_intelligence_integration: bool = True
    mcp_server_enabled: bool = True
    llm_context_providers: list = field(default_factory=lambda: ["project_intelligence", "local"])
    
    # Validation gate thresholds
    validation_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "goal_alignment": 0.8,
        "validation_gates": 0.7,
        "critical_path_focus": 0.8,
        "architectural_tracking": 0.6,
        "health_monitoring": 0.9
    })
    
    @classmethod
    def from_file(cls, config_path: str) -> "PlatformConfig":
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            return cls(**config_data)
        except FileNotFoundError:
            return cls()
        except json.JSONDecodeError:
            return cls()
    
    def save_to_file(self, config_path: str):
        """Save configuration to JSON file"""
        config_data = {
            "project_name": self.project_name,
            "version": self.version,
            "debug_mode": self.debug_mode,
            "strict_methodology_enforcement": self.strict_methodology_enforcement,
            "require_goal_alignment": self.require_goal_alignment,
            "require_validation_gates": self.require_validation_gates,
            "require_critical_path_focus": self.require_critical_path_focus,
            "require_architectural_tracking": self.require_architectural_tracking,
            "require_health_monitoring": self.require_health_monitoring,
            "codebase_analysis_enabled": self.codebase_analysis_enabled,
            "feature_tracking_enabled": self.feature_tracking_enabled,
            "infrastructure_monitoring_enabled": self.infrastructure_monitoring_enabled,
            "test_aggregation_enabled": self.test_aggregation_enabled,
            "reports_directory": self.reports_directory,
            "log_level": self.log_level,
            "output_format": self.output_format,
            "project_intelligence_integration": self.project_intelligence_integration,
            "mcp_server_enabled": self.mcp_server_enabled,
            "llm_context_providers": self.llm_context_providers,
            "validation_thresholds": self.validation_thresholds
        }
        
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    def get_validation_threshold(self, gate_name: str) -> float:
        """Get validation threshold for a specific gate"""
        return self.validation_thresholds.get(gate_name, 0.7)
    
    def is_methodology_requirement_enabled(self, requirement: str) -> bool:
        """Check if a specific methodology requirement is enabled"""
        requirement_map = {
            "goal_alignment": self.require_goal_alignment,
            "validation_gates": self.require_validation_gates,
            "critical_path_focus": self.require_critical_path_focus,
            "architectural_tracking": self.require_architectural_tracking,
            "health_monitoring": self.require_health_monitoring
        }
        return requirement_map.get(requirement, True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "project_name": self.project_name,
            "version": self.version,
            "debug_mode": self.debug_mode,
            "methodology_enforcement": {
                "strict": self.strict_methodology_enforcement,
                "goal_alignment": self.require_goal_alignment,
                "validation_gates": self.require_validation_gates,
                "critical_path_focus": self.require_critical_path_focus,
                "architectural_tracking": self.require_architectural_tracking,
                "health_monitoring": self.require_health_monitoring
            },
            "analysis_modules": {
                "codebase": self.codebase_analysis_enabled,
                "features": self.feature_tracking_enabled,
                "infrastructure": self.infrastructure_monitoring_enabled,
                "tests": self.test_aggregation_enabled
            },
            "output": {
                "reports_directory": self.reports_directory,
                "log_level": self.log_level,
                "format": self.output_format
            },
            "integration": {
                "project_intelligence": self.project_intelligence_integration,
                "mcp_server": self.mcp_server_enabled,
                "llm_providers": self.llm_context_providers
            },
            "validation_thresholds": self.validation_thresholds
        }
