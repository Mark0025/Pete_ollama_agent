#!/usr/bin/env python3
"""
CodebaseAnalyzer - Individual module interface
Delegates to the main whatsworking_platform collector
"""

from ..whatsworking_platform.collectors.codebase_analyzer import CodebaseAnalyzer as PlatformCodebaseAnalyzer

class CodebaseAnalyzer:
    """Analyzer wrapper that uses the platform's codebase analyzer"""
    
    def __init__(self, project_root):
        self.platform_analyzer = PlatformCodebaseAnalyzer(str(project_root))
        self.project_root = project_root
    
    def analyze_all(self):
        """Run comprehensive analysis"""
        self.platform_analyzer.analyze_codebase()
        return self.platform_analyzer.generate_summary_stats()
    
    def generate_architecture_diagrams(self):
        """Generate Mermaid architecture diagrams"""
        # Basic diagram generation - can be enhanced
        return {
            "architecture": "graph TD\n    A[Project Root] --> B[Source Code]\n    B --> C[Components]",
            "dependencies": "graph LR\n    A[Dependencies] --> B[External]\n    A --> C[Internal]"
        }
