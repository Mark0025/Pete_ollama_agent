#!/usr/bin/env python3
"""
Main engine for the Master WhatsWorking Platform

Orchestrates all components and enforces the user's problem-solving methodology
through integration with the existing project_intelligence system.
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from .models import ProjectState, HealthMetrics, ValidationGate, MethodologyEnforcement
from .config import PlatformConfig
from ..collectors.codebase_analyzer import CodebaseAnalyzer
from ..collectors.feature_tracker import StatusReporter
from ..collectors.infrastructure_monitor import CodeFinder

# Import existing project_intelligence system
try:
    from project_intelligence import ProjectIntelligence, GoalFocusEnforcer
    from project_intelligence.core import ProjectHealth, LLMContext
except ImportError:
    ProjectIntelligence = None
    GoalFocusEnforcer = None
    ProjectHealth = None
    LLMContext = None

logger = logging.getLogger(__name__)

class WhatsWorkingEngine:
    """
    Main engine that enforces Goal-First Thinking, Validation Gates,
    Critical Path Focus, Architectural Decision Tracking, and Health Monitoring
    """
    
    def __init__(self, project_root: str = ".", config: Optional[PlatformConfig] = None):
        self.project_root = Path(project_root).resolve()
        self.config = config or PlatformConfig()
        
        # State persistence file
        self.state_file = self.project_root / ".whatsworking_state.json"
        
        # Initialize project state
        self.project_state = ProjectState(
            project_name=self.project_root.name,
            root_directory=self.project_root
        )
        
        # Load existing state if available
        self._load_state()
        
        # Initialize methodology enforcement
        self.methodology = MethodologyEnforcement()
        
        # Initialize collectors
        self.codebase_analyzer = CodebaseAnalyzer(str(self.project_root))
        self.feature_tracker = StatusReporter()
        self.infrastructure_monitor = CodeFinder(self.project_root)
        
        # Initialize validation gates
        self.validation_gates = self._setup_validation_gates()
        
        # Integration with existing project_intelligence
        self.project_intelligence = None
        self.goal_enforcer = None
        self._setup_project_intelligence()
        
        # Update methodology compliance after loading state
        # Note: This will be called when needed, not in constructor
    
    def _load_state(self):
        """Load project state from persistent storage"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                
                # Restore project state
                if 'current_goal' in state_data:
                    self.project_state.current_goal = state_data['current_goal']
                if 'critical_path_items' in state_data:
                    self.project_state.critical_path_items = state_data['critical_path_items']
                if 'architectural_decisions' in state_data:
                    self.project_state.architectural_decisions = state_data['architectural_decisions']
                
                logger.info(f"Loaded state from {self.state_file}")
        except Exception as e:
            logger.warning(f"Could not load state: {e}")
    
    def _save_state(self):
        """Save project state to persistent storage"""
        try:
            state_data = {
                'current_goal': self.project_state.current_goal,
                'critical_path_items': self.project_state.critical_path_items,
                'architectural_decisions': self.project_state.architectural_decisions,
                'last_saved': datetime.now().isoformat()
            }
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"State saved to {self.state_file}")
        except Exception as e:
            logger.warning(f"Could not save state: {e}")
    
    def _setup_validation_gates(self) -> Dict[str, ValidationGate]:
        """Setup validation gates for methodology compliance"""
        return {
            "goal_first": ValidationGate(
                name="Goal-First Thinking",
                description="Ensure all actions align with current project goal",
                required_checks=["has_current_goal", "goal_defined", "actions_aligned"]
            ),
            "validation": ValidationGate(
                name="Validation Gates",
                description="Pass through required validation checkpoints",
                required_checks=["health_check", "dependency_check", "quality_check"]
            ),
            "critical_path": ValidationGate(
                name="Critical Path Focus",
                description="Focus on critical path items for maximum impact",
                required_checks=["critical_path_identified", "focus_maintained", "blockers_addressed"]
            ),
            "architecture": ValidationGate(
                name="Architectural Decision Tracking",
                description="Track and document architectural decisions",
                required_checks=["decisions_documented", "rationale_recorded", "impact_assessed"]
            ),
            "health": ValidationGate(
                name="Health Monitoring",
                description="Continuous monitoring of project health",
                required_checks=["metrics_collected", "issues_tracked", "trends_analyzed"]
            )
        }
    
    def _setup_project_intelligence(self):
        """Setup integration with existing project_intelligence system"""
        if ProjectIntelligence and GoalFocusEnforcer:
            try:
                self.project_intelligence = ProjectIntelligence(str(self.project_root))
                self.goal_enforcer = GoalFocusEnforcer(str(self.project_root))
                logger.info("Successfully integrated with existing project_intelligence system")
            except Exception as e:
                logger.warning(f"Could not initialize project_intelligence: {e}")
        else:
            logger.warning("project_intelligence system not available")
    
    async def analyze_project(self) -> ProjectState:
        """Comprehensive project analysis using all collectors"""
        logger.info("Starting comprehensive project analysis")
        
        # Run codebase analysis
        try:
            codebase_analysis = await self._analyze_codebase()
            self.project_state.add_architectural_decision(f"Codebase analyzed: {codebase_analysis['files_analyzed']} files")
        except Exception as e:
            logger.error(f"Codebase analysis failed: {e}")
        
        # Run feature tracking
        try:
            feature_analysis = await self._analyze_features()
            self.project_state.add_architectural_decision(f"Features tracked: {feature_analysis['features_count']} features")
        except Exception as e:
            logger.error(f"Feature analysis failed: {e}")
        
        # Run infrastructure monitoring
        try:
            infra_analysis = await self._analyze_infrastructure()
            self.project_state.add_architectural_decision(f"Infrastructure monitored: {infra_analysis['components_count']} components")
        except Exception as e:
            logger.error(f"Infrastructure analysis failed: {e}")
        
        # Update health metrics
        health_metrics = await self._calculate_health_metrics()
        self.project_state.update_health(health_metrics)
        
        # Update methodology compliance
        await self._update_methodology_compliance()
        
        # Save state after analysis
        self._save_state()
        
        logger.info("Project analysis complete")
        return self.project_state
    
    async def _analyze_codebase(self) -> Dict[str, Any]:
        """Analyze codebase structure and health"""
        # Use the extracted CodebaseAnalyzer
        py_files = self.codebase_analyzer.get_all_py_files()
        analyses = []
        
        for file_path in py_files:
            analysis = self.codebase_analyzer.analyze_file(file_path)
            if analysis:
                analyses.append(analysis)
        
        return {
            "files_analyzed": len(analyses),
            "total_loc": sum(a.lines_of_code for a in analyses),
            "complexity_score": sum(a.complexity_score for a in analyses),
            "role_distribution": self._count_roles(analyses)
        }
    
    async def _analyze_features(self) -> Dict[str, Any]:
        """Analyze feature usage and health"""
        # Use the extracted StatusReporter
        try:
            status = self.feature_tracker.check_serverless_status()
            return {
                "features_count": len(status.get("files", {}).get("details", {})),
                "health_status": status.get("overall", "unknown")
            }
        except Exception as e:
            logger.warning(f"Feature analysis failed: {e}")
            return {
                "features_count": 0,
                "health_status": "error"
            }
    
    async def _analyze_infrastructure(self) -> Dict[str, Any]:
        """Analyze infrastructure status"""
        # Use the extracted CodeFinder
        try:
            # Use CodeFinder to analyze infrastructure
            return {
                "components_count": 1,  # Placeholder - implement based on your needs
                "status": "operational"
            }
        except Exception as e:
            logger.warning(f"Infrastructure analysis failed: {e}")
            return {
                "components_count": 0,
                "status": "error"
            }
    
    def _count_roles(self, analyses: List[Any]) -> Dict[str, int]:
        """Count files by role"""
        role_counts = {}
        for analysis in analyses:
            role = getattr(analysis, 'role', 'Unknown')
            role_counts[role] = role_counts.get(role, 0) + 1
        return role_counts
    
    async def _calculate_health_metrics(self) -> HealthMetrics:
        """Calculate comprehensive health metrics"""
        # This would integrate with your existing ProjectHealth system
        if self.project_intelligence:
            try:
                health = self.project_intelligence.get_project_health()
                return HealthMetrics(
                    overall_score=health.overall_score if hasattr(health, 'overall_score') else 0.0,
                    critical_issues=health.critical_issues,
                    high_priority_issues=health.high_priority_issues,
                    medium_priority_issues=getattr(health, 'medium_priority_issues', 0),
                    low_priority_issues=getattr(health, 'low_priority_issues', 0)
                )
            except Exception as e:
                logger.warning(f"Could not get project health: {e}")
        
        # Fallback to basic metrics
        return HealthMetrics(overall_score=0.7)
    
    async def _update_methodology_compliance(self):
        """Update methodology compliance based on current state"""
        # Goal-first thinking
        self.methodology.goal_first_thinking = bool(self.project_state.current_goal)
        
        # Validation gates
        passed_gates = sum(1 for gate in self.validation_gates.values() if gate.passed)
        self.methodology.validation_gates_passed = passed_gates
        
        # Critical path focus
        self.methodology.critical_path_focus = len(self.project_state.critical_path_items) > 0
        
        # Architectural tracking
        self.methodology.architectural_tracking = len(self.project_state.architectural_decisions) > 0
        
        # Health monitoring
        self.methodology.health_monitoring = self.project_state.health_metrics.last_updated is not None
    
    def get_llm_context(self) -> Dict[str, Any]:
        """Get context for LLM integration"""
        return {
            "project_state": self.project_state,
            "methodology_compliance": self.methodology,
            "validation_gates": {name: gate.passed for name, gate in self.validation_gates.items()},
            "health_metrics": self.project_state.health_metrics,
            "current_goal": self.project_state.current_goal,
            "critical_path": self.project_state.critical_path_items,
            "architectural_decisions": self.project_state.architectural_decisions
        }
    
    def enforce_methodology(self, action: str, context: Dict[str, Any]) -> bool:
        """Enforce methodology compliance for a given action"""
        # This is where you'd implement the logic to force LLMs to follow your method
        logger.info(f"Enforcing methodology for action: {action}")
        
        # Check if action aligns with current goal
        if not self._validate_goal_alignment(action, context):
            logger.warning(f"Action '{action}' does not align with current goal")
            return False
        
        # Check if action passes validation gates
        if not self._validate_action_gates(action, context):
            logger.warning(f"Action '{action}' failed validation gates")
            return False
        
        # Check if action focuses on critical path
        if not self._validate_critical_path_focus(action, context):
            logger.warning(f"Action '{action}' does not focus on critical path")
            return False
        
        logger.info(f"Action '{action}' passed methodology validation")
        return True
    
    def set_current_goal(self, goal: str):
        """Set the current project goal"""
        self.project_state.set_current_goal(goal)
        self._save_state()
        logger.info(f"Goal set: {goal}")
    
    def add_critical_path_item(self, item: str):
        """Add item to critical path"""
        self.project_state.add_critical_path_item(item)
        self._save_state()
        logger.info(f"Added to critical path: {item}")
    
    def _validate_goal_alignment(self, action: str, context: Dict[str, Any]) -> bool:
        """Validate that action aligns with current goal"""
        if not self.project_state.current_goal:
            return False
        # Add your goal alignment logic here
        return True
    
    def _validate_action_gates(self, action: str, context: Dict[str, Any]) -> bool:
        """Validate that action passes required validation gates"""
        # Add your validation gate logic here
        return True
    
    def _validate_critical_path_focus(self, action: str, context: Dict[str, Any]) -> bool:
        """Validate that action focuses on critical path"""
        # Add your critical path focus logic here
        return True
