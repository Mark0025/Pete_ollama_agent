#!/usr/bin/env python3
"""
OpenRouter Setup Script
Helps configure OpenRouter API key and test basic functionality
"""

import os
import requests
from dotenv import load_dotenv, set_key


def setup_openrouter_api_key():
    """Interactive setup for OpenRouter API key"""
    
    print("🌐 OpenRouter Setup")
    print("=" * 40)
    
    # Check if .env file exists
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    
    if not os.path.exists(env_file):
        print(f"📄 Creating .env file at: {env_file}")
        with open(env_file, 'w') as f:
            f.write("# OpenRouter API Configuration\n")
    
    # Load existing environment
    load_dotenv(env_file)
    existing_key = os.getenv('OPENROUTER_API_KEY')
    
    if existing_key:
        print(f"🔑 Found existing OpenRouter API key: {existing_key[:8]}...")
        choice = input("Do you want to replace it? (y/n): ").strip().lower()
        if choice not in ['y', 'yes']:
            print("✅ Keeping existing API key")
            return existing_key
    
    print("\n🔗 To get an OpenRouter API key:")
    print("1. Visit: https://openrouter.ai/keys")
    print("2. Sign up or log in")
    print("3. Create a new API key")
    print("4. Copy the key and paste it below")
    
    while True:
        api_key = input("\n🔑 Enter your OpenRouter API key: ").strip()
        
        if not api_key:
            print("❌ API key cannot be empty")
            continue
        
        if not api_key.startswith('sk-'):
            print("⚠️ OpenRouter API keys typically start with 'sk-'")
            confirm = input("Continue anyway? (y/n): ").strip().lower()
            if confirm not in ['y', 'yes']:
                continue
        
        # Test the API key
        print("🧪 Testing API key...")
        if test_api_key(api_key):
            print("✅ API key is valid!")
            
            # Save to .env file
            set_key(env_file, 'OPENROUTER_API_KEY', api_key)
            print(f"💾 API key saved to {env_file}")
            
            return api_key
        else:
            print("❌ API key test failed")
            retry = input("Try a different key? (y/n): ").strip().lower()
            if retry not in ['y', 'yes']:
                break
    
    return None


def test_api_key(api_key: str) -> bool:
    """Test if the OpenRouter API key is valid"""
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "PeteOllama Setup Test"
    }
    
    # Test with models endpoint (doesn't use credits)
    url = "https://openrouter.ai/api/v1/models"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        models_data = response.json()
        if 'data' in models_data and len(models_data['data']) > 0:
            print(f"📋 Found {len(models_data['data'])} available models")
            return True
        else:
            print("⚠️ No models returned - key might be invalid")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ API test failed: {e}")
        return False


def show_recommended_models():
    """Show recommended models for testing"""
    
    print("\n🤖 Recommended Models for Testing:")
    print("=" * 40)
    
    free_models = [
        "meta-llama/llama-3.1-8b-instruct:free",
        "huggingface/zephyr-7b-beta:free", 
        "openchat/openchat-7b:free"
    ]
    
    paid_cheap = [
        "openai/gpt-3.5-turbo",
        "anthropic/claude-3-haiku",
        "google/gemini-flash-1.5"
    ]
    
    print("💰 Free Models (no cost):")
    for model in free_models:
        print(f"  • {model}")
    
    print("\n💵 Low-Cost Models (~$0.001-0.01 per 1K tokens):")
    for model in paid_cheap:
        print(f"  • {model}")
    
    print("\n💡 Tips:")
    print("  • Start with free models to test functionality")
    print("  • Free models have rate limits but are great for development")
    print("  • Paid models offer better performance and fewer limits")


def test_model_request(api_key: str):
    """Test a simple model request"""
    
    print("\n🧪 Testing Model Request")
    print("=" * 30)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "PeteOllama Setup Test"
    }
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    payload = {
        "model": "meta-llama/llama-3.1-8b-instruct:free",
        "messages": [
            {"role": "user", "content": "Hello! This is a test message for the OpenRouter integration setup. Please respond with a brief greeting."}
        ],
        "max_tokens": 50,
        "temperature": 0.7,
        "stream": False
    }
    
    try:
        print("📤 Sending test request to Llama 3.1 8B (Free)...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        completion_data = response.json()
        
        if 'choices' in completion_data and len(completion_data['choices']) > 0:
            choice = completion_data['choices'][0]
            response_text = choice['message']['content']
            finish_reason = choice.get('finish_reason')
            
            print("✅ Test request successful!")
            print(f"📄 Response: {response_text}")
            print(f"🏁 Finish reason: {finish_reason}")
            
            usage = completion_data.get('usage', {})
            if usage:
                print(f"📊 Tokens used: {usage.get('total_tokens', 'unknown')}")
            
            return True
        else:
            print("❌ No response choices received")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Test request failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"📄 Error response: {e.response.text}")
        return False


def check_current_setup():
    """Check current OpenRouter setup status"""
    
    print("🔍 Current Setup Status")
    print("=" * 30)
    
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    
    # Check .env file
    if os.path.exists(env_file):
        print(f"✅ .env file exists: {env_file}")
        
        load_dotenv(env_file)
        api_key = os.getenv('OPENROUTER_API_KEY')
        
        if api_key:
            print(f"✅ OPENROUTER_API_KEY is set: {api_key[:8]}...")
            
            # Test the key
            if test_api_key(api_key):
                print("✅ API key is valid and working")
                return True
            else:
                print("❌ API key test failed - may need to replace")
                return False
        else:
            print("❌ OPENROUTER_API_KEY not found in .env file")
            return False
    else:
        print(f"❌ .env file not found: {env_file}")
        return False


def main():
    """Main setup routine"""
    
    print("🚀 OpenRouter Integration Setup")
    print("Setting up OpenRouter as alternative LLM provider")
    print("=" * 50)
    
    # Check current setup
    if check_current_setup():
        print("\n✅ OpenRouter is already configured and working!")
        
        choice = input("\nDo you want to run a full test? (y/n): ").strip().lower()
        if choice in ['y', 'yes']:
            api_key = os.getenv('OPENROUTER_API_KEY')
            test_model_request(api_key)
        
        show_recommended_models()
        return
    
    # Interactive setup
    print("\n🔧 Starting interactive setup...")
    api_key = setup_openrouter_api_key()
    
    if api_key:
        print("\n🎉 OpenRouter setup complete!")
        
        # Test a model request
        choice = input("Run a test model request? (y/n): ").strip().lower()
        if choice in ['y', 'yes']:
            test_model_request(api_key)
        
        show_recommended_models()
        
        print(f"\n🔧 Next Steps:")
        print(f"1. Run: python openrouter_handler.py")
        print(f"2. Run: python model_router.py") 
        print(f"3. Run: python test_provider_comparison.py")
        print(f"4. Integration is ready for use in your applications!")
        
    else:
        print("\n❌ OpenRouter setup failed")
        print("You can run this script again later to retry setup")


if __name__ == "__main__":
    main()
