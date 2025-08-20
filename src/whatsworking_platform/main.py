#!/usr/bin/env python3
"""
Main entry point for the Master WhatsWorking Platform

This is the unified interface that consolidates all the best functionality
from the scattered whatsworking implementations into a cohesive system.
"""

import asyncio
import sys
from pathlib import Path

from .cli.main import WhatsWorkingCLI

async def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        # No arguments provided, show help
        cli = WhatsWorkingCLI()
        cli.show_help()
        return
    
    # Create single CLI instance to maintain state
    cli = WhatsWorkingCLI()
    
    try:
        if sys.argv[1] == "init":
            success = await cli.initialize()
            if not success:
                sys.exit(1)
        elif sys.argv[1] == "analyze":
            # Initialize if not already done
            if not cli.engine:
                await cli.initialize()
            await cli.run_analysis()
        elif sys.argv[1] == "status":
            # Initialize if not already done
            if not cli.engine:
                await cli.initialize()
            await cli.show_status()
        elif sys.argv[1] == "goal":
            if len(sys.argv) < 3:
                print("❌ Goal text required")
                sys.exit(1)
            # Initialize if not already done
            if not cli.engine:
                await cli.initialize()
            goal_text = " ".join(sys.argv[2:])
            await cli.set_goal(goal_text)
        elif sys.argv[1] == "critical":
            if len(sys.argv) < 3:
                print("❌ Critical path item required")
                sys.exit(1)
            # Initialize if not already done
            if not cli.engine:
                await cli.initialize()
            item_text = " ".join(sys.argv[2:])
            await cli.add_critical_path_item(item_text)
        elif sys.argv[1] == "help":
            cli.show_help()
        else:
            print(f"❌ Unknown command: {sys.argv[1]}")
            cli.show_help()
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
