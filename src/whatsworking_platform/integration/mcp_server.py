#!/usr/bin/env python3
"""
MCP Server Integration for the Master WhatsWorking Platform

Provides MCP resources and tools that enforce the user's problem-solving methodology
and integrate with the existing project_intelligence system.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

import mcp
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

from ..core.engine import WhatsWorkingEngine
from ..core.config import PlatformConfig

logger = logging.getLogger(__name__)

class WhatsWorkingMCPServer:
    """
    MCP Server that enforces Goal-First Thinking, Validation Gates,
    Critical Path Focus, Architectural Decision Tracking, and Health Monitoring
    """
    
    def __init__(self, project_root: str = ".", config: Optional[PlatformConfig] = None):
        self.project_root = Path(project_root).resolve()
        self.config = config or PlatformConfig()
        self.engine = WhatsWorkingEngine(str(self.project_root), self.config)
        
        # Initialize MCP server
        self.server = Server("whatsworking-platform")
        self._register_resources()
        self._register_tools()
    
    def _register_resources(self):
        """Register MCP resources that provide project context"""
        
        @self.server.list_resources()
        async def list_resources() -> List[mcp.types.Resource]:
            """List available resources"""
            return [
                mcp.types.Resource(
                    uri="project://whatsworking/state",
                    name="Project State",
                    description="Current state of the WhatsWorking project",
                    mimeType="application/json"
                ),
                mcp.types.Resource(
                    uri="project://whatsworking/methodology",
                    name="Methodology Compliance",
                    description="Current methodology compliance status",
                    mimeType="application/json"
                ),
                mcp.types.Resource(
                    uri="project://whatsworking/health",
                    name="Project Health",
                    description="Current project health metrics",
                    mimeType="application/json"
                ),
                mcp.types.Resource(
                    uri="project://whatsworking/goals",
                    name="Project Goals",
                    description="Current project goals and milestones",
                    mimeType="application/json"
                ),
                mcp.types.Resource(
                    uri="project://whatsworking/critical-path",
                    name="Critical Path",
                    description="Current critical path items",
                    mimeType="application/json"
                ),
                mcp.types.Resource(
                    uri="project://whatsworking/architecture",
                    name="Architectural Decisions",
                    description="Recent architectural decisions",
                    mimeType="application/json"
                )
            ]
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> mcp.types.ReadResourceResult:
            """Read resource content"""
            try:
                if uri == "project://whatsworking/state":
                    context = self.engine.get_llm_context()
                    content = json.dumps(context, default=str, indent=2)
                    return mcp.types.ReadResourceResult(content=content)
                
                elif uri == "project://whatsworking/methodology":
                    methodology = self.engine.methodology
                    content = json.dumps({
                        "goal_first_thinking": methodology.goal_first_thinking,
                        "validation_gates_passed": methodology.validation_gates_passed,
                        "critical_path_focus": methodology.critical_path_focus,
                        "architectural_tracking": methodology.architectural_tracking,
                        "health_monitoring": methodology.health_monitoring,
                        "compliance_score": methodology.compliance_score
                    }, indent=2)
                    return mcp.types.ReadResourceResult(content=content)
                
                elif uri == "project://whatsworking/health":
                    health = self.engine.project_state.health_metrics
                    content = json.dumps({
                        "overall_score": health.overall_score,
                        "health_level": health.health_level.value,
                        "critical_issues": health.critical_issues,
                        "high_priority_issues": health.high_priority_issues,
                        "medium_priority_issues": health.medium_priority_issues,
                        "low_priority_issues": health.low_priority_issues,
                        "last_updated": health.last_updated.isoformat()
                    }, indent=2)
                    return mcp.types.ReadResourceResult(content=content)
                
                elif uri == "project://whatsworking/goals":
                    content = json.dumps({
                        "current_goal": self.engine.project_state.current_goal,
                        "active_tasks": self.engine.project_state.active_tasks
                    }, indent=2)
                    return mcp.types.ReadResourceResult(content=content)
                
                elif uri == "project://whatsworking/critical-path":
                    content = json.dumps({
                        "critical_path_items": self.engine.project_state.critical_path_items
                    }, indent=2)
                    return mcp.types.ReadResourceResult(content=content)
                
                elif uri == "project://whatsworking/architecture":
                    content = json.dumps({
                        "architectural_decisions": self.engine.project_state.architectural_decisions
                    }, indent=2)
                    return mcp.types.ReadResourceResult(content=content)
                
                else:
                    raise ValueError(f"Unknown resource URI: {uri}")
                    
            except Exception as e:
                logger.error(f"Failed to read resource {uri}: {e}")
                raise
    
    def _register_tools(self):
        """Register MCP tools that enforce methodology compliance"""
        
        @self.server.list_tools()
        async def list_tools() -> List[mcp.types.Tool]:
            """List available tools"""
            return [
                mcp.types.Tool(
                    name="enforce_methodology",
                    description="Enforce methodology compliance for a given action",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "description": "The action to validate"
                            },
                            "context": {
                                "type": "object",
                                "description": "Additional context for validation"
                            }
                        },
                        "required": ["action"]
                    }
                ),
                mcp.types.Tool(
                    name="set_project_goal",
                    description="Set the current project goal",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "goal": {
                                "type": "string",
                                "description": "The goal to set"
                            }
                        },
                        "required": ["goal"]
                    }
                ),
                mcp.types.Tool(
                    name="add_critical_path_item",
                    description="Add item to critical path",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "item": {
                                "type": "string",
                                "description": "The critical path item to add"
                            }
                        },
                        "required": ["item"]
                    }
                ),
                mcp.types.Tool(
                    name="run_project_analysis",
                    description="Run comprehensive project analysis",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                mcp.types.Tool(
                    name="validate_action_gates",
                    description="Validate action through all validation gates",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string",
                                "description": "The action to validate"
                            }
                        },
                        "required": ["action"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> mcp.types.CallToolResult:
            """Execute tool calls"""
            try:
                if name == "enforce_methodology":
                    action = arguments.get("action", "")
                    context = arguments.get("context", {})
                    
                    # Enforce methodology compliance
                    is_valid = self.engine.enforce_methodology(action, context)
                    
                    return mcp.types.CallToolResult(
                        content=[
                            mcp.types.TextContent(
                                type="text",
                                text=f"Methodology validation {'PASSED' if is_valid else 'FAILED'} for action: {action}"
                            )
                        ]
                    )
                
                elif name == "set_project_goal":
                    goal = arguments.get("goal", "")
                    
                    # Set project goal
                    self.engine.project_state.current_goal = goal
                    
                    return mcp.types.CallToolResult(
                        content=[
                            mcp.types.TextContent(
                                type="text",
                                text=f"Project goal set: {goal}"
                            )
                        ]
                    )
                
                elif name == "add_critical_path_item":
                    item = arguments.get("item", "")
                    
                    # Add to critical path
                    self.engine.project_state.add_critical_path_item(item)
                    
                    return mcp.types.CallToolResult(
                        content=[
                            mcp.types.TextContent(
                                type="text",
                                text=f"Added to critical path: {item}"
                            )
                        ]
                    )
                
                elif name == "run_project_analysis":
                    # Run analysis
                    project_state = await self.engine.analyze_project()
                    
                    return mcp.types.CallToolResult(
                        content=[
                            mcp.types.TextContent(
                                type="text",
                                text=f"Project analysis complete. Analyzed {len(project_state.architectural_decisions)} architectural decisions."
                            )
                        ]
                    )
                
                elif name == "validate_action_gates":
                    action = arguments.get("action", "")
                    
                    # Validate through all gates
                    gate_results = {}
                    for gate_name, gate in self.engine.validation_gates.items():
                        # This is a simplified validation - you'd implement your actual logic here
                        gate_results[gate_name] = gate.passed
                    
                    return mcp.types.CallToolResult(
                        content=[
                            mcp.types.TextContent(
                                type="text",
                                text=f"Validation gate results for '{action}': {json.dumps(gate_results, indent=2)}"
                            )
                        ]
                    )
                
                else:
                    raise ValueError(f"Unknown tool: {name}")
                    
            except Exception as e:
                logger.error(f"Tool call failed for {name}: {e}")
                return mcp.types.CallToolResult(
                    content=[
                        mcp.types.TextContent(
                            type="text",
                            text=f"Tool call failed: {str(e)}"
                        )
                    ],
                    isError=True
                )
    
    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read, write):
            await self.server.run(
                read,
                write,
                InitializationOptions(
                    server_name="whatsworking-platform",
                    server_version="1.0.0",
                    capabilities={
                        "resources": {},
                        "tools": {}
                    }
                )
            )

async def main():
    """Main entry point for the MCP server"""
    server = WhatsWorkingMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())
