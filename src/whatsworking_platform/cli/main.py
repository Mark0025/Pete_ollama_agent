#!/usr/bin/env python3
"""
Command Line Interface for the Master WhatsWorking Platform

Provides a unified CLI for all platform functionality, enforcing
the user's problem-solving methodology.
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from ..core.engine import WhatsWorkingEngine
from ..core.config import PlatformConfig

console = Console()

class WhatsWorkingCLI:
    """Main CLI class for the Master WhatsWorking Platform"""
    
    def __init__(self):
        self.engine: Optional[WhatsWorkingEngine] = None
        self.config: Optional[PlatformConfig] = None
    
    async def initialize(self, project_root: str = "."):
        """Initialize the platform engine"""
        try:
            console.print("🎯 [bold blue]Initializing Master WhatsWorking Platform...[/bold blue]")
            
            # Load configuration
            config_path = Path(project_root) / "whatsworking_platform_config.json"
            self.config = PlatformConfig.from_file(str(config_path))
            
            # Initialize engine
            self.engine = WhatsWorkingEngine(project_root, self.config)
            
            console.print("✅ [bold green]Platform initialized successfully![/bold green]")
            return True
            
        except Exception as e:
            console.print(f"❌ [bold red]Failed to initialize platform: {e}[/bold red]")
            return False
    
    async def run_analysis(self):
        """Run comprehensive project analysis"""
        if not self.engine:
            console.print("❌ [bold red]Platform not initialized. Run 'init' first.[/bold red]")
            return
        
        try:
            console.print("🔍 [bold blue]Running comprehensive project analysis...[/bold blue]")
            
            project_state = await self.engine.analyze_project()
            
            # Display results
            self._display_analysis_results(project_state)
            
        except Exception as e:
            console.print(f"❌ [bold red]Analysis failed: {e}[/bold red]")
    
    def _display_analysis_results(self, project_state):
        """Display analysis results in a rich format"""
        # Project overview
        overview = Panel(
            f"[bold]Project:[/bold] {project_state.project_name}\n"
            f"[bold]Root:[/bold] {project_state.root_directory}\n"
            f"[bold]Last Analysis:[/bold] {project_state.last_analysis.strftime('%Y-%m-%d %H:%M:%S')}",
            title="📊 Project Overview",
            border_style="blue"
        )
        console.print(overview)
        
        # Health metrics
        health = project_state.health_metrics
        health_table = Table(title="🏥 Health Metrics")
        health_table.add_column("Metric", style="cyan")
        health_table.add_column("Value", style="green")
        health_table.add_column("Status", style="yellow")
        
        health_table.add_row("Overall Score", f"{health.overall_score:.2f}", 
                           f"[{'green' if health.overall_score >= 0.8 else 'yellow' if health.overall_score >= 0.6 else 'red'}]{health.health_level.value}[/]")
        health_table.add_row("Critical Issues", str(health.critical_issues), 
                           f"[{'red' if health.critical_issues > 0 else 'green'}]{'⚠️' if health.critical_issues > 0 else '✅'}[/]")
        health_table.add_row("High Priority", str(health.high_priority_issues), 
                           f"[{'yellow' if health.high_priority_issues > 2 else 'green'}]{'⚠️' if health.high_priority_issues > 2 else '✅'}[/]")
        
        console.print(health_table)
        
        # Methodology compliance
        methodology = self.engine.methodology
        compliance_table = Table(title="🎯 Methodology Compliance")
        compliance_table.add_column("Requirement", style="cyan")
        compliance_table.add_column("Status", style="green")
        compliance_table.add_column("Score", style="yellow")
        
        compliance_table.add_row("Goal-First Thinking", 
                               "✅" if methodology.goal_first_thinking else "❌",
                               f"{'100%' if methodology.goal_first_thinking else '0%'}")
        compliance_table.add_row("Validation Gates", 
                               f"✅ ({methodology.validation_gates_passed}/5)" if methodology.validation_gates_passed > 0 else "❌",
                               f"{methodology.validation_gates_passed * 20}%")
        compliance_table.add_row("Critical Path Focus", 
                               "✅" if methodology.critical_path_focus else "❌",
                               f"{'100%' if methodology.critical_path_focus else '0%'}")
        compliance_table.add_row("Architectural Tracking", 
                               "✅" if methodology.architectural_tracking else "❌",
                               f"{'100%' if methodology.architectural_tracking else '0%'}")
        compliance_table.add_row("Health Monitoring", 
                               "✅" if methodology.health_monitoring else "❌",
                               f"{'100%' if methodology.health_monitoring else '0%'}")
        
        console.print(compliance_table)
        
        # Overall compliance score
        overall_score = methodology.compliance_score
        score_color = "green" if overall_score >= 0.8 else "yellow" if overall_score >= 0.6 else "red"
        score_panel = Panel(
            f"[bold]Overall Methodology Compliance:[/bold] [bold {score_color}]{overall_score:.1%}[/bold {score_color}]",
            title="📈 Compliance Summary",
            border_style=score_color
        )
        console.print(score_panel)
    
    async def show_status(self):
        """Show current platform status"""
        if not self.engine:
            console.print("❌ [bold red]Platform not initialized. Run 'init' first.[/bold red]")
            return
        
        try:
            console.print("📊 [bold blue]Current Platform Status[/bold blue]")
            
            # Get LLM context
            context = self.engine.get_llm_context()
            
            # Display current goal
            if context.get("current_goal"):
                goal_panel = Panel(
                    f"[bold]Current Goal:[/bold] {context['current_goal']}",
                    title="🎯 Active Goal",
                    border_style="green"
                )
                console.print(goal_panel)
            else:
                goal_panel = Panel(
                    "[bold red]No current goal set[/bold red]",
                    title="🎯 Active Goal",
                    border_style="red"
                )
                console.print(goal_panel)
            
            # Display critical path
            if context.get("critical_path"):
                path_panel = Panel(
                    "\n".join([f"• {item}" for item in context["critical_path"]]),
                    title="🛤️ Critical Path Items",
                    border_style="yellow"
                )
                console.print(path_panel)
            
            # Display recent architectural decisions
            if context.get("architectural_decisions"):
                decisions_panel = Panel(
                    "\n".join([f"• {decision}" for decision in context["architectural_decisions"][-5:]]),
                    title="🏗️ Recent Architectural Decisions",
                    border_style="blue"
                )
                console.print(decisions_panel)
            
        except Exception as e:
            console.print(f"❌ [bold red]Failed to get status: {e}[/bold red]")
    
    async def set_goal(self, goal: str):
        """Set the current project goal"""
        if not self.engine:
            console.print("❌ [bold red]Platform not initialized. Run 'init' first.[/bold red]")
            return
        
        try:
            self.engine.set_current_goal(goal)
            console.print(f"✅ [bold green]Goal set: {goal}[/bold green]")
            
            # Update methodology compliance
            await self.engine._update_methodology_compliance()
            
        except Exception as e:
            console.print(f"❌ [bold red]Failed to set goal: {e}[/bold red]")
    
    async def add_critical_path_item(self, item: str):
        """Add item to critical path"""
        if not self.engine:
            console.print("❌ [bold red]Platform not initialized. Run 'init' first.[/bold red]")
            return
        
        try:
            self.engine.add_critical_path_item(item)
            console.print(f"✅ [bold green]Added to critical path: {item}[/bold green]")
            
            # Update methodology compliance
            await self.engine._update_methodology_compliance()
            
        except Exception as e:
            console.print(f"❌ [bold red]Failed to add critical path item: {e}[/bold red]")
    
    def show_help(self):
        """Show help information"""
        help_text = """
[bold blue]Master WhatsWorking Platform CLI[/bold blue]

[bold]Commands:[/bold]
  init                    Initialize the platform
  analyze                 Run comprehensive project analysis
  status                  Show current platform status
  goal <text>            Set current project goal
  critical <item>        Add item to critical path
  help                    Show this help message

[bold]Methodology Enforcement:[/bold]
  • Goal-First Thinking
  • Validation Gates
  • Critical Path Focus
  • Architectural Decision Tracking
  • Health Monitoring

[bold]Examples:[/bold]
  python -m whatsworking_platform.cli.main init
  python -m whatsworking_platform.cli.main analyze
  python -m whatsworking_platform.cli.main goal "Implement MCP server integration"
  python -m whatsworking_platform.cli.main critical "Fix authentication bug"
        """
        
        help_panel = Panel(help_text, title="📚 Help", border_style="blue")
        console.print(help_panel)

async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Master WhatsWorking Platform CLI")
    parser.add_argument("command", nargs="?", default="help", 
                       help="Command to execute")
    parser.add_argument("args", nargs="*", help="Command arguments")
    parser.add_argument("--project-root", default=".", 
                       help="Project root directory")
    
    args = parser.parse_args()
    
    cli = WhatsWorkingCLI()
    
    if args.command == "init":
        success = await cli.initialize(args.project_root)
        if not success:
            sys.exit(1)
    
    elif args.command == "analyze":
        await cli.run_analysis()
    
    elif args.command == "status":
        await cli.show_status()
    
    elif args.command == "goal":
        if not args.args:
            console.print("❌ [bold red]Goal text required[/bold red]")
            sys.exit(1)
        goal_text = " ".join(args.args)
        await cli.set_goal(goal_text)
    
    elif args.command == "critical":
        if not args.args:
            console.print("❌ [bold red]Critical path item required[/bold red]")
            sys.exit(1)
        item_text = " ".join(args.args)
        await cli.add_critical_path_item(item_text)
    
    elif args.command == "help":
        cli.show_help()
    
    else:
        console.print(f"❌ [bold red]Unknown command: {args.command}[/bold red]")
        cli.show_help()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
