#!/usr/bin/env python3
"""
PeteOllama V1 - Direct Model Training Script
============================================

Simple script to train the property management model directly.
"""

import sys
import os
from pathlib import Path

# Add src to Python path
src_path = str(Path(__file__).parent / "src")
sys.path.insert(0, src_path)

from ai.model_manager import ModelManager
from database.pete_db_manager import PeteDBManager

def main():
    """Train the property management model"""
    print("🤖 PeteOllama V1 - Property Management Model Training")
    print("=" * 60)
    
    # Check database
    print("📊 Checking training database...")
    db = PeteDBManager()
    print(f"📁 Database path: {db.db_path}")
    print(f"🔗 Connected: {db.is_connected()}")
    
    if not db.is_connected():
        print("❌ Cannot connect to database!")
        return False
    
    # Get training stats
    stats = db.get_training_stats()
    print(f"📞 Total conversations: {stats['total']}")
    print(f"📅 Date range: {stats['date_range']}")
    
    # Check Ollama availability
    print("\n🧠 Checking Ollama service...")
    manager = ModelManager()
    print(f"📡 Ollama available: {manager.is_available()}")
    
    if not manager.is_available():
        print("❌ Ollama service not available!")
        print("💡 Please start Ollama: `ollama serve`")
        return False
    
    # Check if base model exists
    print(f"🔍 Checking base model: {manager.model_name}")
    if not manager.is_model_available():
        print(f"📥 Pulling base model: {manager.model_name}")
        if not manager.pull_model():
            print("❌ Failed to pull base model!")
            return False
    
    # Start training
    print(f"\n🎯 Training custom model: {manager.custom_model_name}")
    print("🚀 Starting training process...")
    
    result = manager.train_property_manager()
    
    if result:
        print("\n🎉 SUCCESS! Property management model trained!")
        print(f"✅ Model created: {manager.custom_model_name}")
        
        # Test the model
        print("\n🧪 Testing model response...")
        test_result = manager.test_model_response("Hi, when is my rent due this month?")
        print(f"🤖 Model response: {test_result['response'][:100]}...")
        print(f"⚡ Response time: {test_result['response_time_ms']}ms")
        
        return True
    else:
        print("❌ Training failed!")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)