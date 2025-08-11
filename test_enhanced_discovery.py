#!/usr/bin/env python3
"""
Test script for Enhanced Model Discovery System
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.enhanced_model_discovery import enhanced_discovery

def test_discovery():
    """Test the enhanced model discovery system"""
    print("🧪 Testing Enhanced Model Discovery System")
    print("=" * 50)
    
    # Discover available models
    print("\n🔍 Discovering available models...")
    models = enhanced_discovery.discover_available_models()
    
    if not models:
        print("❌ No models discovered")
        return
    
    print(f"✅ Discovered {len(models)} models:")
    for model in models:
        print(f"  - {model['name']} ({model['size']}) - {model['type']} based on {model['base_model']}")
    
    # Generate configurations
    print("\n⚙️ Generating model configurations...")
    configs = enhanced_discovery.generate_model_configs(models)
    
    print(f"✅ Generated {len(configs)} configurations:")
    for name, config in configs.items():
        print(f"  - {name}:")
        print(f"    Display: {config['display_name']}")
        print(f"    Description: {config['description']}")
        print(f"    Show in UI: {config['show_in_ui']}")
        print(f"    Auto-preload: {config['auto_preload']}")
        print(f"    Type: {config['type']}")
        print()
    
    # Get recommended default
    print("\n🎯 Getting recommended default model...")
    default = enhanced_discovery.get_recommended_default_model(models)
    print(f"✅ Recommended default: {default}")
    
    print("\n🎉 Test completed successfully!")

if __name__ == "__main__":
    test_discovery()
