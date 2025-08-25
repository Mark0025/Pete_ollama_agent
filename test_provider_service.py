#!/usr/bin/env python3
"""
Test Provider Service Integration
================================

This script tests if the provider service is properly using the model controller.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_provider_service():
    """Test the provider service integration"""
    print("🧪 Testing Provider Service Integration...")
    print("=" * 60)
    
    try:
        # Test model controller directly
        from src.config.model_controller import model_controller
        print("✅ Model Controller imported successfully")
        
        # Test provider service import
        from src.vapi.services.provider_service import ProviderService
        print("✅ Provider Service imported successfully")
        
        # Create provider service instance
        provider_service = ProviderService()
        print("✅ Provider Service instance created")
        
        # Test Ollama personas
        print("\n📋 Testing Ollama Personas...")
        ollama_personas = await provider_service._get_ollama_personas()
        
        print(f"📋 Ollama Personas: {len(ollama_personas)} found")
        
        for i, persona in enumerate(ollama_personas, 1):
            print(f"\n{i}. {persona.name} ({persona.type})")
            print(f"   Description: {persona.description}")
            print(f"   Models: {len(persona.models)}")
            
            for j, model in enumerate(persona.models, 1):
                print(f"     {j}. {model.name} ({model.display_name})")
                print(f"        Type: {model.type}")
                print(f"        Base: {model.base_model}")
        
        # Check if vapipmv1 is in any persona
        vapipmv1_found = False
        for persona in ollama_personas:
            for model in persona.models:
                if "vapipmv1" in model.name:
                    vapipmv1_found = True
                    print(f"\n🎯 VAPI PM Model Found in persona: {persona.name}")
                    break
            if vapipmv1_found:
                break
        
        if not vapipmv1_found:
            print("\n❌ VAPI PM Model NOT found in any persona!")
        
        print("\n" + "=" * 60)
        print("🧪 Provider Service Test Complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_provider_service())

