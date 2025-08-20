#!/usr/bin/env python3
"""
Development Server with Auto-Reload
===================================

Automatically restarts the server when Python files change.
Uses watchdog to monitor file changes and restart the server.
"""

import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ServerRestartHandler(FileSystemEventHandler):
    """Handle file system events to restart the server"""
    
    def __init__(self, server_process):
        self.server_process = server_process
        self.last_restart = 0
        self.restart_cooldown = 2  # Minimum seconds between restarts
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        # Only watch Python files
        if not event.src_path.endswith('.py'):
            return
            
        # Ignore temporary files
        if any(x in event.src_path for x in ['__pycache__', '.pyc', '.pyo', '.tmp']):
            return
            
        current_time = time.time()
        if current_time - self.last_restart < self.restart_cooldown:
            return
            
        print(f"\n🔄 File changed: {event.src_path}")
        print("🔄 Restarting server...")
        
        self.last_restart = current_time
        self.restart_server()
    
    def restart_server(self):
        """Restart the server process"""
        try:
            # Kill current server
            if self.server_process and self.server_process.poll() is None:
                print("🔄 Stopping current server...")
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                print("✅ Server stopped")
            
            # Start new server
            print("🚀 Starting new server...")
            self.start_server()
            
        except Exception as e:
            print(f"❌ Error restarting server: {e}")
    
    def start_server(self):
        """Start the server process"""
        try:
            # Set environment variables
            env = os.environ.copy()
            env['RUNPOD_API_KEY'] = "rpa_DPL09BE6U4Z1NUDSXW8TQLR9NVQVSX8TQLR9NVQVSX8TQLR9NVQVSX8TQLR9NVQVSX8TQLR9NVQVSX4UB0S258R51a0e8y"
            env['RUNPOD_SERVERLESS_ENDPOINT'] = "vk7efas3wu5vd7"
            
            # Start server in src directory
            cmd = ["python3", "main.py"]
            self.server_process = subprocess.Popen(
                cmd,
                cwd="src",
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Start output monitoring in background
            threading.Thread(target=self.monitor_output, daemon=True).start()
            
            print("✅ Server started successfully")
            
        except Exception as e:
            print(f"❌ Error starting server: {e}")
    
    def monitor_output(self):
        """Monitor server output"""
        if self.server_process:
            for line in iter(self.server_process.stdout.readline, ''):
                if line:
                    print(f"[SERVER] {line.rstrip()}")
    
    def stop_server(self):
        """Stop the server process"""
        if self.server_process and self.server_process.poll() is None:
            print("🛑 Stopping server...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
                print("✅ Server stopped")
            except subprocess.TimeoutExpired:
                print("⚠️ Force killing server...")
                self.server_process.kill()

def main():
    """Main development server function"""
    print("🚀 Starting Development Server with Auto-Reload")
    print("=" * 50)
    print("📁 Watching for changes in Python files...")
    print("🔄 Server will automatically restart on file changes")
    print("🛑 Press Ctrl+C to stop")
    print("=" * 50)
    
    # Initialize handler
    handler = ServerRestartHandler(None)
    
    # Start initial server
    handler.start_server()
    
    # Set up file watching
    observer = Observer()
    
    # Watch src directory and its subdirectories
    src_path = Path("src")
    if src_path.exists():
        observer.schedule(handler, str(src_path), recursive=True)
        print(f"👀 Watching: {src_path.absolute()}")
    
    # Watch root directory for config changes
    observer.schedule(handler, ".", recursive=False)
    print(f"👀 Watching: {Path('.').absolute()}")
    
    observer.start()
    
    try:
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down development server...")
        observer.stop()
        handler.stop_server()
        observer.join()
        print("✅ Development server stopped")

if __name__ == "__main__":
    main()
