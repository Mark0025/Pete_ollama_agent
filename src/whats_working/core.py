#!/usr/bin/env python3
"""
🎯 WhatsWorking Core - Main Orchestrator

Coordinates all analysis tools to provide comprehensive codebase insights.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from .analyzer import CodebaseAnalyzer
from .feature_tracker import FeatureTracker
from .updater import TestResultsUpdater
from .health_monitor import SystemHealthMonitor

class WhatsWorking:
    """
    Main WhatsWorking orchestrator that coordinates all analysis tools.
    """
    
    def __init__(self, project_root: str = None):
        """Initialize WhatsWorking with project root"""
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.output_dir = self.project_root / "DEV_MAN" / "whats_working"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.analyzer = CodebaseAnalyzer(self.project_root)
        self.feature_tracker = FeatureTracker(self.project_root)
        self.updater = TestResultsUpdater(self.project_root)
        self.health_monitor = SystemHealthMonitor(self.project_root)
        
        print(f"🎯 WhatsWorking initialized for: {self.project_root}")
        print(f"📁 Output directory: {self.output_dir}")
    
    def analyze_codebase(self, include_diagrams: bool = True) -> Dict[str, Any]:
        """
        Run comprehensive codebase analysis
        
        Args:
            include_diagrams: Whether to generate Mermaid diagrams
            
        Returns:
            Analysis results dictionary
        """
        print("🔍 Starting comprehensive codebase analysis...")
        
        try:
            # Run AST-based analysis
            analysis_results = self.analyzer.analyze_all()
            
            # Generate Mermaid diagrams if requested
            if include_diagrams:
                diagrams = self.analyzer.generate_architecture_diagrams()
                analysis_results['diagrams'] = diagrams
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"codebase_analysis_{timestamp}.json"
            
            with open(output_file, 'w') as f:
                json.dump(analysis_results, f, indent=2, default=str)
            
            print(f"✅ Codebase analysis completed and saved to: {output_file}")
            return analysis_results
            
        except Exception as e:
            print(f"❌ Codebase analysis failed: {e}")
            return {"error": str(e)}
    
    def track_features(self) -> Dict[str, Any]:
        """
        Track feature health and usage patterns
        
        Returns:
            Feature tracking results
        """
        print("📊 Tracking feature health...")
        
        try:
            results = self.feature_tracker.track_all_features()
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"feature_health_{timestamp}.json"
            
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            print(f"✅ Feature tracking completed and saved to: {output_file}")
            return results
            
        except Exception as e:
            print(f"❌ Feature tracking failed: {e}")
            return {"error": str(e)}
    
    def update_test_results(self) -> Dict[str, Any]:
        """
        Update and aggregate test results
        
        Returns:
            Test results summary
        """
        print("🧪 Updating test results...")
        
        try:
            results = self.updater.update_all_results()
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"test_results_{timestamp}.json"
            
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            print(f"✅ Test results updated and saved to: {output_file}")
            return results
            
        except Exception as e:
            print(f"❌ Test results update failed: {e}")
            return {"error": str(e)}
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        Get comprehensive system health report
        
        Returns:
            System health status
        """
        print("🏥 Generating system health report...")
        
        try:
            health = self.health_monitor.get_health_report()
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"system_health_{timestamp}.json"
            
            with open(output_file, 'w') as f:
                json.dump(health, f, indent=2, default=str)
            
            print(f"✅ System health report generated and saved to: {output_file}")
            return health
            
        except Exception as e:
            print(f"❌ System health report failed: {e}")
            return {"error": str(e)}
    
    def run_full_analysis(self) -> Dict[str, Any]:
        """
        Run all analysis tools and generate comprehensive report
        
        Returns:
            Complete analysis results
        """
        print("🚀 Running full WhatsWorking analysis...")
        print("=" * 60)
        
        results = {}
        
        # 1. Codebase Analysis
        print("\n1️⃣ Codebase Analysis")
        results['codebase'] = self.analyze_codebase()
        
        # 2. Feature Tracking
        print("\n2️⃣ Feature Health Tracking")
        results['features'] = self.track_features()
        
        # 3. Test Results
        print("\n3️⃣ Test Results Update")
        results['tests'] = self.update_test_results()
        
        # 4. System Health
        print("\n4️⃣ System Health Report")
        results['health'] = self.get_system_health()
        
        # 5. Generate summary
        print("\n5️⃣ Generating Summary Report")
        summary = self._generate_summary_report(results)
        results['summary'] = summary
        
        # Save complete results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"full_analysis_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n🎉 Full analysis completed and saved to: {output_file}")
        print("=" * 60)
        
        return results
    
    def _generate_summary_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of all analysis results"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "analysis_components": list(results.keys()),
            "overall_status": "completed"
        }
        
        # Check for errors
        errors = []
        for component, result in results.items():
            if isinstance(result, dict) and "error" in result:
                errors.append(f"{component}: {result['error']}")
        
        if errors:
            summary["errors"] = errors
            summary["overall_status"] = "completed_with_errors"
        
        return summary
    
    def get_status(self) -> str:
        """Get current WhatsWorking status"""
        return f"🎯 WhatsWorking v1.0.0 - Project: {self.project_root.name}"
