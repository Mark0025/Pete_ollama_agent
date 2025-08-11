#!/usr/bin/env python3
"""
Script to pull missing models that are referenced in configuration but don't exist locally.
Run this on RunPod to ensure all referenced models are available.
"""

import subprocess
import json
import sys
from pathlib import Path

def run_command(cmd):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def get_available_models():
    """Get list of available models from ollama list"""
    success, output, error = run_command("ollama list")
    if not success:
        print(f"❌ Error running 'ollama list': {error}")
        return []
    
    models = []
    lines = output.strip().split('\n')[1:]  # Skip header
    for line in lines:
        if line.strip():
            parts = line.split()
            if len(parts) >= 2:
                model_name = parts[0]
                models.append(model_name)
    
    return models

def get_referenced_models():
    """Get models referenced in the configuration"""
    config_file = Path("src/config/model_settings.json")
    if not config_file.exists():
        print("❌ Model settings file not found")
        return []
    
    try:
        with open(config_file, 'r') as f:
            data = json.load(f)
            return list(data.get('models', {}).keys())
    except Exception as e:
        print(f"❌ Error reading config file: {e}")
        return []

def pull_model(model_name):
    """Pull a specific model"""
    print(f"🔄 Pulling model: {model_name}")
    success, output, error = run_command(f"ollama pull {model_name}")
    
    if success:
        print(f"✅ Successfully pulled: {model_name}")
        return True
    else:
        print(f"❌ Failed to pull {model_name}: {error}")
        return False

def main():
    print("🚀 Model Puller for PeteOllama")
    print("=" * 40)
    
    # Get available models
    print("📋 Checking available models...")
    available_models = get_available_models()
    print(f"Found {len(available_models)} available models")
    
    # Get referenced models
    print("📋 Checking referenced models...")
    referenced_models = get_referenced_models()
    print(f"Found {len(referenced_models)} referenced models")
    
    # Find missing models
    missing_models = [model for model in referenced_models if model not in available_models]
    
    if not missing_models:
        print("✅ All referenced models are available!")
        return
    
    print(f"\n❌ Found {len(missing_models)} missing models:")
    for model in missing_models:
        print(f"  - {model}")
    
    # Ask user if they want to pull
    response = input(f"\n🤔 Pull {len(missing_models)} missing models? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Aborted")
        return
    
    # Pull missing models
    print("\n🔄 Starting model pulls...")
    success_count = 0
    for model in missing_models:
        if pull_model(model):
            success_count += 1
        print()  # Empty line for readability
    
    print(f"✅ Successfully pulled {success_count}/{len(missing_models)} models")
    
    if success_count < len(missing_models):
        print("⚠️  Some models failed to pull. Check the errors above.")

if __name__ == "__main__":
    main()
