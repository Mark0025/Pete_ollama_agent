#!/usr/bin/env python3
"""
PeteOllama V1 - Main Application Entry Point
============================================

Streamlined property manager AI trained on real phone conversations.
Provides both GUI interface and VAPI webhook endpoint.
"""

import sys
import asyncio
import threading
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

from gui.main_window import PeteOllamaGUI
from vapi.webhook_server import VAPIWebhookServer
from utils.logger import logger

def run_gui():
    """Run the PyQt5 GUI in main thread"""
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    app.setApplicationName("PeteOllama V1")
    app.setApplicationVersion("1.0.0")
    
    # Create and show main window
    window = PeteOllamaGUI()
    window.show()
    
    logger.info("🖥️  PyQt5 GUI started successfully")
    sys.exit(app.exec_())

def run_webhook_server():
    """Run the VAPI webhook server in background thread"""
    async def start_server():
        server = VAPIWebhookServer()
        await server.start()
    
    # Run async server in thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_server())

def main():
    """Main application entry point"""
    logger.info("🚀 Starting PeteOllama V1 - AI Property Manager")
    logger.info("📱 Training data: Real phone conversations")
    logger.info("🤖 Model: Qwen 2.5 7B (Custom trained)")
    logger.info("🎤 Voice: VAPI Integration")
    
    # Start webhook server in background thread
    webhook_thread = threading.Thread(target=run_webhook_server, daemon=True)
    webhook_thread.start()
    logger.info("🌐 VAPI webhook server starting...")
    
    # Run GUI in main thread (required for PyQt5)
    logger.info("🖥️  Starting PyQt5 GUI...")
    run_gui()

if __name__ == "__main__":
    main()