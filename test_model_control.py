#!/usr/bin/env python3
"""
Test Script for Model Controller
================================

This script tests the new model controller to ensure your vapipmv1 model appears correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.model_controller import model_controller

def test_model_controller():
    """Test the model controller functionality"""
    print("🧪 Testing Model Controller...")
    print("=" * 50)
    
    # Check if control is enabled
    control_enabled = model_controller.is_control_enabled()
    print(f"📋 Control Enabled: {control_enabled}")
    
    # Get visible models
    visible_models = model_controller.get_visible_models()
    print(f"📋 Visible Models: {len(visible_models)}")
    
    # Show each model
    for i, model in enumerate(visible_models, 1):
        print(f"\n{i}. {model.get('display_name', model.get('name', 'Unknown'))}")
        print(f"   Name: {model.get('name')}")
        print(f"   Type: {model.get('type')}")
        print(f"   Show in UI: {model.get('show_in_ui')}")
        print(f"   Force Visible: {model.get('force_visible')}")
        print(f"   Priority: {model.get('priority')}")
        print(f"   Status: {model.get('status')}")
    
    # Check if vapipmv1 is visible
    vapipmv1_found = any("vapipmv1" in model.get('name', '') for model in visible_models)
    print(f"\n🎯 VAPI PM Model Found: {vapipmv1_found}")
    
    if vapipmv1_found:
        vapipmv1_model = next(model for model in visible_models if "vapipmv1" in model.get('name', ''))
        print(f"✅ VAPI PM Model Details:")
        print(f"   Display Name: {vapipmv1_model.get('display_name')}")
        print(f"   Description: {vapipmv1_model.get('description')}")
        print(f"   Show in UI: {vapipmv1_model.get('show_in_ui')}")
    else:
        print("❌ VAPI PM Model NOT found in visible models!")
    
    # Get default model
    default_model = model_controller.get_default_model()
    print(f"\n🏆 Default Model: {default_model}")
    
    print("\n" + "=" * 50)
    print("🧪 Test Complete!")

if __name__ == "__main__":
    test_model_controller()
