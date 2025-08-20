#!/usr/bin/env python3
"""
Integration modules for the Master WhatsWorking Platform

Provides integration with external systems like MCP servers and LLMs.
"""

from .mcp_server import WhatsWorkingMCPServer

__all__ = ['WhatsWorkingMCPServer']
