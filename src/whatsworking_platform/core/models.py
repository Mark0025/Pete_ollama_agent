#!/usr/bin/env python3
"""
Core data models for the Master WhatsWorking Platform

These models integrate with the existing project_intelligence system
to provide a unified view of project state and health.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Any
from pathlib import Path

class GoalStatus(Enum):
    """Status of project goals and milestones"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class HealthLevel(Enum):
    """Health status levels"""
    CRITICAL = "critical"
    WARNING = "warning"
    HEALTHY = "healthy"
    OPTIMAL = "optimal"

@dataclass
class HealthMetrics:
    """Comprehensive health metrics for the project"""
    overall_score: float = 0.0
    critical_issues: int = 0
    high_priority_issues: int = 0
    medium_priority_issues: int = 0
    low_priority_issues: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    
    @property
    def health_level(self) -> HealthLevel:
        """Determine overall health level based on metrics"""
        if self.critical_issues > 0:
            return HealthLevel.CRITICAL
        elif self.high_priority_issues > 2:
            return HealthLevel.WARNING
        elif self.overall_score >= 0.8:
            return HealthLevel.OPTIMAL
        else:
            return HealthLevel.HEALTHY

@dataclass
class ProjectState:
    """Current state of the entire project"""
    project_name: str
    root_directory: Path
    current_goal: Optional[str] = None
    health_metrics: HealthMetrics = field(default_factory=HealthMetrics)
    active_tasks: List[str] = field(default_factory=list)
    critical_path_items: List[str] = field(default_factory=list)
    architectural_decisions: List[str] = field(default_factory=list)
    last_analysis: datetime = field(default_factory=datetime.now)
    
    def update_health(self, metrics: HealthMetrics):
        """Update project health metrics"""
        self.health_metrics = metrics
        self.last_analysis = datetime.now()
    
    def add_critical_path_item(self, item: str):
        """Add item to critical path"""
        if item not in self.critical_path_items:
            self.critical_path_items.append(item)
    
    def add_architectural_decision(self, decision: str):
        """Add architectural decision"""
        if decision not in self.architectural_decisions:
            self.architectural_decisions.append(decision)
    
    def set_current_goal(self, goal: str):
        """Set the current project goal"""
        self.current_goal = goal

@dataclass
class ValidationGate:
    """Validation gate for enforcing methodology compliance"""
    name: str
    description: str
    required_checks: List[str]
    passed: bool = False
    last_validated: Optional[datetime] = None
    validation_notes: List[str] = field(default_factory=list)
    
    def validate(self, checks: Dict[str, bool]) -> bool:
        """Validate that all required checks pass"""
        self.passed = all(checks.get(check, False) for check in self.required_checks)
        self.last_validated = datetime.now()
        return self.passed

@dataclass
class MethodologyEnforcement:
    """Enforces the user's problem-solving methodology"""
    goal_first_thinking: bool = False
    validation_gates_passed: int = 0
    critical_path_focus: bool = False
    architectural_tracking: bool = False
    health_monitoring: bool = False
    
    @property
    def compliance_score(self) -> float:
        """Calculate overall methodology compliance score"""
        total_checks = 5
        passed_checks = sum([
            self.goal_first_thinking,
            self.validation_gates_passed > 0,
            self.critical_path_focus,
            self.architectural_tracking,
            self.health_monitoring
        ])
        return passed_checks / total_checks
