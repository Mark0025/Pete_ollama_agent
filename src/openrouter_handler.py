#!/usr/bin/env python3
"""
OpenRouter LLM Handler for PeteOllama
Alternative provider to diagnose RunPod serverless truncation issues
Easy model switching for testing and comparison
"""

import requests
import json
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OpenRouterClient:
    """Client for interacting with OpenRouter API for model testing"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.base_url = "https://openrouter.ai/api/v1"
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")
            
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",  # Your app URL
            "X-Title": "PeteOllama AI Phone System"  # Your app name
        }
        
        print(f"🌐 OpenRouter Client initialized")
        print(f"🔑 API Key: {'✅ Set' if self.api_key else '❌ Missing'}")

    def get_models(self) -> Optional[Dict[str, Any]]:
        """Get available models from OpenRouter"""
        url = f"{self.base_url}/models"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            models_data = response.json()
            print(f"📋 Retrieved {len(models_data.get('data', []))} models from OpenRouter")
            return models_data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error getting models: {e}")
            return None

    def chat_completion(self, 
                       message: str, 
                       model: str = "openrouter/auto",
                       max_tokens: int = 1000,
                       temperature: float = 0.7,
                       conversation_history: list = None) -> Optional[Dict[str, Any]]:
        """
        Send chat completion request to OpenRouter
        
        Popular models to test:
        - meta-llama/llama-3.1-8b-instruct:free (Free)
        - openai/gpt-3.5-turbo (Paid but cheap)
        - anthropic/claude-3-haiku (Paid)
        - google/gemini-flash-1.5 (Paid)
        """
        url = f"{self.base_url}/chat/completions"
        
        # Build messages array
        messages = []
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add current message
        messages.append({
            "role": "user",
            "content": message
        })
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False  # We want full responses, not streaming
        }
        
        try:
            print(f"📤 Sending request to OpenRouter")
            print(f"🤖 Model: {model}")
            print(f"💬 Message: {message[:100]}{'...' if len(message) > 100 else ''}")
            print(f"🎛️ Max tokens: {max_tokens}")
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=60)
            response.raise_for_status()
            
            completion_data = response.json()
            
            if 'choices' in completion_data and len(completion_data['choices']) > 0:
                choice = completion_data['choices'][0]
                response_text = choice['message']['content']
                
                # Check for truncation
                finish_reason = choice.get('finish_reason')
                was_truncated = finish_reason == 'length'
                
                print(f"✅ OpenRouter response received")
                print(f"📏 Response length: {len(response_text)} chars")
                print(f"🏁 Finish reason: {finish_reason}")
                if was_truncated:
                    print(f"⚠️ Response was truncated due to max_tokens limit")
                
                return {
                    "status": "success",
                    "response": response_text,
                    "model": model,
                    "finish_reason": finish_reason,
                    "was_truncated": was_truncated,
                    "usage": completion_data.get('usage', {}),
                    "provider": "openrouter"
                }
            else:
                print(f"❌ No choices in OpenRouter response")
                return {"status": "error", "error": "No response choices"}
                
        except requests.exceptions.Timeout:
            print(f"⏰ OpenRouter request timed out")
            return {"status": "error", "error": "Request timeout"}
        except requests.exceptions.RequestException as e:
            print(f"❌ Error with OpenRouter request: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"📄 Response: {e.response.text}")
            return {"status": "error", "error": str(e)}

    def vapi_webhook_response(self, 
                            user_message: str, 
                            call_id: str,
                            model: str = "openrouter/auto",
                            conversation_history: list = None) -> Dict[str, Any]:
        """Handle VAPI webhook with OpenRouter for comparison testing"""
        
        # Add property management context for VAPI calls
        system_prompt = """You are Jamie, a friendly AI property manager assistant. Keep responses conversational, helpful, and under 150 words for phone calls. Focus on property management topics like maintenance, rentals, and tenant services."""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if conversation_history:
            messages.extend(conversation_history)
            
        result = self.chat_completion(
            message=user_message,
            model=model,
            max_tokens=200,  # Keep VAPI responses concise
            temperature=0.7,
            conversation_history=messages
        )
        
        if result and result.get('status') == 'success':
            return {
                "status": "success",
                "response": result['response'],
                "call_id": call_id,
                "model": model,
                "finish_reason": result.get('finish_reason'),
                "was_truncated": result.get('was_truncated', False),
                "provider": "openrouter"
            }
        else:
            return {
                "status": "error",
                "error": result.get('error', 'Unknown error'),
                "call_id": call_id,
                "provider": "openrouter"
            }


class OpenRouterHandler:
    """Main handler that uses OpenRouter as alternative to RunPod for testing"""
    
    def __init__(self):
        try:
            self.openrouter_client = OpenRouterClient()
            self.available = True
        except ValueError as e:
            print(f"⚠️ OpenRouter not available: {e}")
            self.available = False
    
    def chat_completion(self, message: str, model: str = "openai/gpt-3.5-turbo", **kwargs) -> Dict[str, Any]:
        """Handle chat completion requests using OpenRouter"""
        if not self.available:
            return {"error": "OpenRouter not configured", "status": "error"}
            
        from utils.logger import logger
        
        # Extract conversation history if provided
        conversation_history = kwargs.get('conversation_history', [])
        max_tokens = kwargs.get('max_tokens', 1000)
        temperature = kwargs.get('temperature', 0.7)
        
        logger.info(f"🌐 OpenRouter chat completion request")
        logger.info(f"📝 Message: {message[:100]}{'...' if len(message) > 100 else ''}")
        logger.info(f"🤖 Model: {model}")
        logger.info(f"🎛️ Max tokens: {max_tokens}")
        
        result = self.openrouter_client.chat_completion(
            message=message,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            conversation_history=conversation_history
        )
        
        if result and 'response' in result:
            response_text = result['response']
            response_length = len(response_text)
            is_truncated = response_length >= max_tokens
            
            logger.info(f"✅ OpenRouter response received")
            logger.info(f"📏 Response length: {response_length} chars")
            logger.info(f"🎯 Max tokens requested: {max_tokens}")
            logger.info(f"✂️ Truncated: {'YES' if is_truncated else 'NO'}")
            logger.info(f"📄 Response preview: {response_text[:100]}{'...' if response_length > 100 else ''}")
            
            # Add truncation info to result
            result['response_metadata'] = {
                'length': response_length,
                'max_tokens_requested': max_tokens,
                'is_truncated': is_truncated,
                'source': 'openrouter_direct'
            }
        
        return result or {"error": "OpenRouter request failed", "status": "error"}
    
    def vapi_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle VAPI webhook requests using OpenRouter"""
        if not self.available:
            return {"error": "OpenRouter not configured", "status": "error"}
            
        print(f"🌐📞 OpenRouter VAPI webhook request")
        print(f"📋 Webhook data keys: {list(webhook_data.keys())}")
        
        # Extract message from VAPI webhook
        user_message = webhook_data.get('message', '')
        call_id = webhook_data.get('call_id', '')
        model = webhook_data.get('model', 'openrouter/auto')
        
        if not user_message:
            # Try alternative webhook formats
            conversation = webhook_data.get('conversation', {})
            user_message = conversation.get('user_message', '')
        
        if not user_message:
            return {"error": "No user message found in webhook", "status": "error"}
        
        # Get conversation history if available
        conversation_history = webhook_data.get('conversation_history', [])
        
        return self.openrouter_client.vapi_webhook_response(
            user_message=user_message,
            call_id=call_id,
            model=model,
            conversation_history=conversation_history
        )
    
    def get_available_models(self) -> Dict[str, Any]:
        """Get list of available OpenRouter models for testing"""
        if not self.available:
            return {"error": "OpenRouter not configured", "status": "error"}
            
        models_data = self.openrouter_client.get_models()
        if models_data:
            return {"status": "success", "models": models_data}
        else:
            return {"error": "Failed to get models", "status": "error"}


# Global handler instance
openrouter_handler = OpenRouterHandler()


# Recommended models for testing truncation issues
RECOMMENDED_TEST_MODELS = {
    "free_models": [
        "meta-llama/llama-3.3-70b-instruct:free",
        "meta-llama/llama-3.1-405b-instruct:free",
        "qwen/qwen-2.5-72b-instruct:free",
        "mistralai/mistral-nemo:free",
        "google/gemma-2-9b-it:free"
    ],
    "paid_cheap": [
        "openai/gpt-3.5-turbo",
        "anthropic/claude-3-haiku",
        "google/gemini-flash-1.5",
        "openai/gpt-4o-mini"
    ],
    "paid_premium": [
        "anthropic/claude-3-sonnet",
        "meta-llama/llama-3.1-70b-instruct",
        "deepseek/deepseek-r1"
    ]
}


def main():
    """Test the OpenRouter handler locally"""
    print("🧪 Testing OpenRouter Handler")
    print("=" * 50)
    
    if not openrouter_handler.available:
        print("❌ OpenRouter not configured. Set OPENROUTER_API_KEY in .env file")
        print("🔗 Get API key from: https://openrouter.ai/keys")
        return
    
    # Test available models
    print("\n📋 Getting available models...")
    models_result = openrouter_handler.get_available_models()
    if models_result.get('status') == 'success':
        models = models_result['models']['data'][:5]  # Show first 5
        print(f"✅ Found {len(models)} models (showing first 5):")
        for model in models:
            print(f"  🤖 {model['id']} - ${model.get('pricing', {}).get('prompt', 'N/A')} per 1M tokens")
    
    # Test chat completion with free model
    print(f"\n💬 Testing chat completion with free model...")
    test_message = "Hello, my name is Mark. I'm having an issue with my rental property - the tenant says the heating isn't working properly. Can you help me understand what steps I should take to address this? Please provide a detailed response about the process."
    
    chat_result = openrouter_handler.chat_completion(
        message=test_message, 
        model="meta-llama/llama-3.1-8b-instruct:free",
        max_tokens=500
    )
    
    if chat_result.get('status') == 'success':
        print(f"✅ Chat completion successful")
        print(f"📏 Response length: {len(chat_result['response'])} chars")
        print(f"🏁 Finish reason: {chat_result.get('finish_reason')}")
        print(f"⚠️ Was truncated: {chat_result.get('was_truncated', False)}")
        print(f"📄 Response preview: {chat_result['response'][:200]}...")
    else:
        print(f"❌ Chat completion failed: {chat_result.get('error')}")
    
    # Test VAPI webhook format
    print(f"\n📞 Testing VAPI webhook...")
    mock_webhook = {
        "message": "My toilet is leaking water all over the bathroom floor. This is an emergency!",
        "call_id": "test-openrouter-123"
    }
    
    vapi_result = openrouter_handler.vapi_webhook(mock_webhook)
    if vapi_result.get('status') == 'success':
        print(f"✅ VAPI webhook successful")
        print(f"📏 Response length: {len(vapi_result['response'])} chars")
        print(f"⚠️ Was truncated: {vapi_result.get('was_truncated', False)}")
        print(f"📄 Response: {vapi_result['response']}")
    else:
        print(f"❌ VAPI webhook failed: {vapi_result.get('error')}")
    
    print(f"\n🎯 Recommended test models:")
    print(f"💰 Free: {', '.join(RECOMMENDED_TEST_MODELS['free_models'])}")
    print(f"💵 Cheap: {', '.join(RECOMMENDED_TEST_MODELS['paid_cheap'])}")


if __name__ == "__main__":
    main()
