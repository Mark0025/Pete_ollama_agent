#!/usr/bin/env python3
"""
Full WhatsWorking Platform Analysis for Ollama Agent
===================================================

Uses the complete whatsWorking platform to analyze the ollama_agent project
and generate comprehensive documentation, architecture diagrams, and health reports.
"""

import asyncio
import sys
from pathlib import Path

# Import the full whatsWorking platform
from whatsworking_platform.core.engine import WhatsWorkingEngine
from whatsworking_platform.core.config import PlatformConfig
from whatsworking_platform.collectors.codebase_analyzer import CodebaseAnalyzer, InfrastructureAnalyzer
from whatsworking_platform.collectors.feature_tracker import StatusReporter, ReportGenerator
from whatsworking_platform.collectors.infrastructure_monitor import CodeFinder

class OllamaAgentWhatsWorkingAnalyzer:
    """Full whatsWorking analysis for the Ollama Agent project"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.engine = None
        self.config = None
        
    async def initialize_platform(self):
        """Initialize the whatsWorking platform"""
        print("🎯 Initializing Master WhatsWorking Platform...")
        
        try:
            # Create a basic configuration
            self.config = PlatformConfig(
                project_name="Ollama Agent System Configuration",
                debug_mode=True,
                codebase_analysis_enabled=True,
                feature_tracking_enabled=True,
                infrastructure_monitoring_enabled=True,
                test_aggregation_enabled=True,
                reports_directory="docs/whats_working_analysis",
                output_format="markdown"
            )
            
            # Initialize the engine
            self.engine = WhatsWorkingEngine(str(self.project_root), self.config)
            
            print("✅ Platform initialized successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize platform: {e}")
            return False
    
    async def run_full_analysis(self):
        """Run the complete whatsWorking analysis"""
        if not self.engine:
            print("❌ Platform not initialized")
            return None
        
        try:
            print("🔍 Running comprehensive project analysis...")
            
            # Run the full analysis
            project_state = await self.engine.analyze_project()
            
            print("✅ Analysis completed successfully!")
            return project_state
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            return None
    
    async def generate_documentation(self, project_state):
        """Generate comprehensive documentation"""
        if not project_state:
            print("❌ No project state to document")
            return
        
        try:
            print("📚 Generating comprehensive documentation...")
            
            # Generate different output formats
            outputs = await self.engine.generate_outputs(project_state)
            
            # Save documentation files
            docs_dir = self.project_root / "docs" / "whats_working_analysis"
            docs_dir.mkdir(parents=True, exist_ok=True)
            
            for output_format, content in outputs.items():
                if output_format == "markdown":
                    file_path = docs_dir / "system_analysis.md"
                    with open(file_path, 'w') as f:
                        f.write(content)
                    print(f"✅ Markdown report: {file_path}")
                
                elif output_format == "json":
                    file_path = docs_dir / "system_analysis.json"
                    with open(file_path, 'w') as f:
                        f.write(content)
                    print(f"✅ JSON report: {file_path}")
                
                elif output_format == "mermaid":
                    file_path = docs_dir / "architecture_diagram.md"
                    with open(file_path, 'w') as f:
                        f.write(content)
                    print(f"✅ Mermaid diagram: {file_path}")
            
            print("📚 Documentation generation completed!")
            
        except Exception as e:
            print(f"❌ Documentation generation failed: {e}")
    
    async def show_analysis_summary(self, project_state):
        """Display analysis summary"""
        if not project_state:
            return
        
        try:
            print("\n" + "=" * 80)
            print("📊 WHATSWORKING ANALYSIS SUMMARY")
            print("=" * 80)
            
            # Project overview
            print(f"🏗️ Project: {project_state.project_name}")
            print(f"📁 Root: {project_state.root_directory}")
            print(f"⏰ Last Analysis: {project_state.last_analysis}")
            
            # Health metrics
            health = project_state.health_metrics
            print(f"\n🏥 Health Metrics:")
            print(f"   Overall Score: {health.overall_score:.2f}")
            print(f"   Health Level: {health.health_level.value}")
            print(f"   Critical Issues: {health.critical_issues}")
            print(f"   High Priority Issues: {health.high_priority_issues}")
            
            # Methodology compliance
            methodology = self.engine.methodology
            print(f"\n🎯 Methodology Compliance:")
            for requirement, status in methodology.compliance.items():
                print(f"   {requirement}: {status}")
            
            # Critical path items
            if hasattr(project_state, 'critical_path_items'):
                print(f"\n🚨 Critical Path Items:")
                for item in project_state.critical_path_items:
                    print(f"   - {item.description}")
            
            print("\n" + "=" * 80)
            
        except Exception as e:
            print(f"❌ Summary display failed: {e}")
    
    async def run_complete_analysis(self):
        """Run the complete analysis workflow"""
        print("🚀 Starting Full WhatsWorking Analysis")
        print("=" * 80)
        
        # Initialize platform
        if not await self.initialize_platform():
            return False
        
        # Run analysis
        project_state = await self.run_full_analysis()
        if not project_state:
            return False
        
        # Show summary
        await self.show_analysis_summary(project_state)
        
        # Generate documentation
        await self.generate_documentation(project_state)
        
        print("\n🎉 Full WhatsWorking analysis completed!")
        print("📚 Check the docs/whats_working_analysis/ directory for reports")
        
        return True

async def main():
    """Main entry point"""
    analyzer = OllamaAgentWhatsWorkingAnalyzer()
    success = await analyzer.run_complete_analysis()
    
    if success:
        print("✅ Analysis completed successfully!")
    else:
        print("❌ Analysis failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
