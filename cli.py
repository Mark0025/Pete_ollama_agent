#!/usr/bin/env python3
"""
PeteOllama V1 - Command Line Interface
======================================

CLI launcher for the AI Property Manager application.
"""

import sys
import subprocess
import argparse
import time
import requests
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.logger import logger

def check_docker_running():
    """Check if Docker is running"""
    try:
        result = subprocess.run(
            ["docker", "info"], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def check_service_health(url: str, timeout: int = 5) -> bool:
    """Check if a service is healthy"""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except:
        return False

def start_containers():
    """Start all Docker containers"""
    logger.info("🐳 Starting Docker containers...")
    
    result = subprocess.run(
        ["docker-compose", "up", "-d"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        logger.success("✅ Containers started successfully")
        return True
    else:
        logger.error(f"❌ Failed to start containers: {result.stderr}")
        return False

def stop_containers():
    """Stop all Docker containers"""
    logger.info("🛑 Stopping Docker containers...")
    
    result = subprocess.run(
        ["docker-compose", "down"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        logger.success("✅ Containers stopped successfully")
        return True
    else:
        logger.error(f"❌ Failed to stop containers: {result.stderr}")
        return False

def wait_for_services():
    """Wait for services to be ready"""
    services = {
        "Ollama": "http://localhost:11435/api/health",
        "App": "http://localhost:8000/health",
    }
    
    logger.info("⏳ Waiting for services to be ready...")
    
    max_wait = 60  # 60 seconds max wait
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        all_ready = True
        
        for service_name, health_url in services.items():
            if check_service_health(health_url):
                logger.success(f"✅ {service_name}: Ready")
            else:
                logger.info(f"⏳ {service_name}: Starting...")
                all_ready = False
        
        if all_ready:
            logger.success("🎉 All services are ready!")
            return True
        
        time.sleep(3)
    
    logger.warning("⚠️  Some services may still be starting up...")
    return False

def launch_gui():
    """Launch the PyQt5 GUI"""
    logger.info("🖥️  Launching PyQt5 GUI...")
    
    try:
        # Run inside Docker container
        result = subprocess.run([
            "docker", "exec", "-it", "peteollama_app", 
            "uv", "run", "python", "src/main.py"
        ])
        return result.returncode == 0
    except KeyboardInterrupt:
        logger.info("👋 GUI application closed by user")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to launch GUI: {e}")
        return False

def show_status():
    """Show current system status"""
    logger.info("📊 PeteOllama V1 Status")
    logger.info("=" * 40)
    
    # Check Docker
    if check_docker_running():
        logger.success("✅ Docker: Running")
    else:
        logger.error("❌ Docker: Not running")
        return
    
    # Check containers
    result = subprocess.run(
        ["docker-compose", "ps", "--format", "table"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        logger.info("🐳 Container Status:")
        print(result.stdout)
    
    # Check services
    services = {
        "Ollama API": "http://localhost:11435/api/health",
        "App Health": "http://localhost:8000/health",
    }
    
    logger.info("🌐 Service Health:")
    for service_name, health_url in services.items():
        if check_service_health(health_url):
            logger.success(f"  ✅ {service_name}")
        else:
            logger.error(f"  ❌ {service_name}")

def extract_training_data():
    """Extract training data from production database"""
    logger.info("📊 Extracting training data...")
    
    try:
        result = subprocess.run(
            ["python", "extract_jamie_data.py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.success("✅ Training data extracted successfully")
            print(result.stdout)
            return True
        else:
            logger.error(f"❌ Failed to extract training data: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"❌ Error extracting training data: {e}")
        return False

def download_model():
    """Download the base AI model"""
    logger.info("📥 Downloading Qwen 2.5 7B model...")
    
    try:
        result = subprocess.run([
            "docker", "exec", "-it", "peteollama_ollama",
            "ollama", "pull", "qwen2.5:7b"
        ])
        
        if result.returncode == 0:
            logger.success("✅ Model downloaded successfully")
            return True
        else:
            logger.error("❌ Failed to download model")
            return False
    except Exception as e:
        logger.error(f"❌ Error downloading model: {e}")
        return False

def test_model():
    """Test the AI model with a sample prompt"""
    logger.info("🧪 Testing AI model...")
    
    test_data = {
        "message": "Hi, when is my rent due this month?"
    }
    
    try:
        response = requests.post(
            "http://localhost:8000/test/message",
            json=test_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.success("✅ Model test successful!")
            logger.info(f"   Prompt: {result['user_message']}")
            logger.info(f"   Response: {result['ai_response']}")
            logger.info(f"   Model: {result['model_used']}")
            return True
        else:
            logger.error(f"❌ Model test failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Error testing model: {e}")
        return False

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="PeteOllama V1 - AI Property Manager CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py start          # Start the complete system
  python cli.py gui            # Launch GUI only
  python cli.py status         # Show system status
  python cli.py extract        # Extract training data
  python cli.py download       # Download AI model
  python cli.py test           # Test AI model
  python cli.py stop           # Stop all containers
        """
    )
    
    parser.add_argument(
        'command',
        choices=['start', 'stop', 'gui', 'status', 'extract', 'download', 'test'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--wait',
        action='store_true',
        help='Wait for services to be ready before launching GUI'
    )
    
    args = parser.parse_args()
    
    # Show header
    logger.info("🏠 PeteOllama V1 - AI Property Manager")
    logger.info("📱 Trained on Real Phone Conversations")
    logger.info("🤖 Powered by Qwen 2.5 7B + VAPI")
    logger.info("")
    
    # Check Docker first (except for status command)
    if args.command != 'status' and not check_docker_running():
        logger.error("❌ Docker is not running. Please start Docker Desktop first.")
        sys.exit(1)
    
    # Execute command
    success = True
    
    if args.command == 'start':
        success = start_containers()
        if success and args.wait:
            wait_for_services()
        if success:
            logger.info("🚀 PeteOllama V1 is ready!")
            logger.info("   • GUI: python cli.py gui")
            logger.info("   • Status: python cli.py status")
            logger.info("   • Webhook: http://localhost:8000")
    
    elif args.command == 'stop':
        success = stop_containers()
    
    elif args.command == 'gui':
        success = launch_gui()
    
    elif args.command == 'status':
        show_status()
    
    elif args.command == 'extract':
        success = extract_training_data()
    
    elif args.command == 'download':
        success = download_model()
    
    elif args.command == 'test':
        success = test_model()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()