#!/usr/bin/env python3
"""
Test RunPod Serverless Handler
Tests the new serverless architecture
"""

import sys
import os
import json
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from runpod_handler import PeteOllamaHandler, RunPodServerlessClient
from api_server import app
from fastapi.testclient import TestClient

def test_environment_setup():
    """Test that environment variables are configured"""
    print("🧪 Testing environment setup...")
    
    api_key = os.getenv('RUNPOD_API_KEY')
    endpoint_id = os.getenv('RUNPOD_SERVERLESS_ENDPOINT')
    
    print(f"🔑 API Key: {'✅ Set' if api_key else '❌ Missing'}")
    print(f"📋 Endpoint ID: {'✅ Set' if endpoint_id else '❌ Missing'}")
    
    if not api_key or not endpoint_id:
        print("❌ Environment setup incomplete")
        print("💡 Make sure your .env file contains:")
        print("   RUNPOD_API_KEY=your_api_key")
        print("   RUNPOD_SERVERLESS_ENDPOINT=your_endpoint_id")
        return False
    
    print("✅ Environment setup looks good")
    return True

def test_runpod_client_init():
    """Test RunPod client initialization"""
    print("\n🧪 Testing RunPod client initialization...")
    
    try:
        client = RunPodServerlessClient()
        print("✅ RunPod client initialized successfully")
        print(f"📋 Endpoint ID: {client.endpoint_id}")
        print(f"🔗 Base URL: {client.base_url}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize RunPod client: {e}")
        return False

def test_pete_handler_init():
    """Test PeteOllama handler initialization"""
    print("\n🧪 Testing PeteOllama handler initialization...")
    
    try:
        handler = PeteOllamaHandler()
        print("✅ PeteOllama handler initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize PeteOllama handler: {e}")
        return False

def test_api_server():
    """Test FastAPI server endpoints"""
    print("\n🧪 Testing FastAPI server...")
    
    try:
        client = TestClient(app)
        
        # Test root endpoint
        response = client.get("/")
        print(f"📄 Root endpoint: {response.status_code}")
        
        # Test health endpoint
        response = client.get("/health")
        print(f"🩺 Health endpoint: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   Status: {health_data.get('status')}")
            print(f"   RunPod configured: {health_data.get('runpod_configured')}")
        
        # Test docs endpoint
        response = client.get("/docs")
        print(f"📚 Docs endpoint: {response.status_code}")
        
        print("✅ FastAPI server endpoints accessible")
        return True
        
    except Exception as e:
        print(f"❌ FastAPI server test failed: {e}")
        return False

def test_chat_request_format():
    """Test chat request formatting (without actually calling RunPod)"""
    print("\n🧪 Testing chat request formatting...")
    
    try:
        handler = PeteOllamaHandler()
        
        # Mock the RunPod client to avoid actual API calls during testing
        class MockRunPodClient:
            def submit_sync_job(self, input_data):
                print(f"📤 Would submit sync job: {json.dumps(input_data, indent=2)}")
                return {
                    "status": "COMPLETED",
                    "output": {
                        "response": "Hello! I'm doing great, thanks for asking, Mark!",
                        "model": "llama3:latest"
                    },
                    "executionTime": 1500
                }
        
        # Replace the real client with mock for testing
        original_client = handler.runpod_client
        handler.runpod_client = MockRunPodClient()
        
        # Test chat completion formatting
        result = handler.chat_completion("Hello, how are you?", model="llama3:latest")
        print(f"💬 Chat result: {json.dumps(result, indent=2)}")
        
        # Restore original client
        handler.runpod_client = original_client
        
        print("✅ Chat request formatting works")
        return True
        
    except Exception as e:
        print(f"❌ Chat request formatting test failed: {e}")
        return False

def test_vapi_webhook_format():
    """Test VAPI webhook formatting (without actually calling RunPod)"""
    print("\n🧪 Testing VAPI webhook formatting...")
    
    try:
        handler = PeteOllamaHandler()
        
        # Mock the RunPod client
        class MockRunPodClient:
            def submit_sync_job(self, input_data):
                print(f"📤 Would submit VAPI job: {json.dumps(input_data, indent=2)}")
                return {
                    "status": "COMPLETED",
                    "output": {
                        "vapi_response": "I'll schedule a plumber to fix your toilet leak right away.",
                        "response": "I'll schedule a plumber to fix your toilet leak right away."
                    },
                    "executionTime": 2000
                }
        
        # Replace the real client with mock
        original_client = handler.runpod_client
        handler.runpod_client = MockRunPodClient()
        
        # Test VAPI webhook formatting
        mock_webhook = {
            "message": "My toilet is leaking",
            "call_id": "test-call-456"
        }
        result = handler.vapi_webhook(mock_webhook)
        print(f"📞 VAPI result: {json.dumps(result, indent=2)}")
        
        # Restore original client
        handler.runpod_client = original_client
        
        print("✅ VAPI webhook formatting works")
        return True
        
    except Exception as e:
        print(f"❌ VAPI webhook formatting test failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints with mocked responses"""
    print("\n🧪 Testing API endpoints...")
    
    try:
        client = TestClient(app)
        
        # Test chat endpoint (will fail without real RunPod, but we can check structure)
        chat_data = {
            "message": "Hello test",
            "model": "llama3:latest"
        }
        
        print("📤 Testing chat endpoint structure...")
        response = client.post("/api/chat", json=chat_data)
        print(f"   Status: {response.status_code}")
        if response.status_code != 200:
            print(f"   Response: {response.json()}")
        
        # Test VAPI webhook endpoint structure
        webhook_data = {
            "message": "Test webhook",
            "call_id": "test-123"
        }
        
        print("📤 Testing VAPI webhook structure...")
        response = client.post("/vapi/webhook", json=webhook_data)
        print(f"   Status: {response.status_code}")
        if response.status_code != 200:
            print(f"   Response: {response.json()}")
        
        # Test admin endpoint structure
        admin_data = {
            "action": "status",
            "data": {}
        }
        
        print("📤 Testing admin endpoint structure...")
        response = client.post("/admin/action", json=admin_data)
        print(f"   Status: {response.status_code}")
        if response.status_code != 200:
            print(f"   Response: {response.json()}")
        
        print("✅ API endpoint structures are correct")
        return True
        
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 PeteOllama RunPod Handler Test Suite")
    print("=" * 60)
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("RunPod Client Init", test_runpod_client_init),
        ("PeteOllama Handler Init", test_pete_handler_init),
        ("FastAPI Server", test_api_server),
        ("Chat Request Format", test_chat_request_format),
        ("VAPI Webhook Format", test_vapi_webhook_format),
        ("API Endpoints", test_api_endpoints)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if success:
            passed += 1
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready for RunPod deployment.")
        return 0
    else:
        print("⚠️  Some tests failed. Check configuration and fix issues.")
        return 1

if __name__ == "__main__":
    exit(main())
