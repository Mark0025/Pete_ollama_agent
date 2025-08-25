#!/usr/bin/env python3
"""
PeteOllama RunPod Serverless Handler
Following RunPod Official Documentation Pattern
Based on: https://docs.runpod.io/tutorials/serverless/run-your-first
"""

import requests
import json
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RunPodServerlessClient:
    """Client for interacting with RunPod serverless endpoints following official docs"""
    
    def __init__(self):
        self.api_key = os.getenv('RUNPOD_API_KEY')
        self.endpoint_id = os.getenv('RUNPOD_SERVERLESS_ENDPOINT')
        self.base_url = "https://api.runpod.ai/v2"
        
        if not self.api_key:
            raise ValueError("RUNPOD_API_KEY not found in environment variables")
        if not self.endpoint_id:
            raise ValueError("RUNPOD_SERVERLESS_ENDPOINT not found in environment variables")
            
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        print(f"🚀 RunPod Client initialized")
        print(f"📋 Endpoint ID: {self.endpoint_id}")
        print(f"🔑 API Key: {'✅ Set' if self.api_key else '❌ Missing'}")
        
        # Cache for available models
        self._available_models = None
        self._models_cache_time = 0
        self._cache_duration = 300  # 5 minutes

    def submit_job(self, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Submit an asynchronous job to RunPod serverless endpoint
        Following official docs Step 2: Submit your first job
        """
        url = f"{self.base_url}/{self.endpoint_id}/run"
        
        payload = {"input": input_data}
        
        try:
            print(f"📤 Submitting job to: {url}")
            print(f"📋 Payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            job_data = response.json()
            print(f"✅ Job submitted successfully")
            print(f"🆔 Job ID: {job_data.get('id')}")
            print(f"📊 Status: {job_data.get('status')}")
            
            return job_data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error submitting job: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"📄 Response: {e.response.text}")
            return None
    
    def get_available_models(self, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get available models from RunPod serverless endpoint
        Uses caching to avoid repeated API calls
        """
        import time
        current_time = time.time()
        
        # Return cached models if still valid
        if (not force_refresh and 
            self._available_models and 
            (current_time - self._models_cache_time) < self._cache_duration):
            print(f"📋 Returning cached RunPod models ({len(self._available_models)} models)")
            return self._available_models
        
        try:
            print(f"🔍 Fetching available models from RunPod...")
            
            # Use the /runsync endpoint to test model availability
            # This is more reliable than trying to get a model list
            test_models = [
                "llama3:latest",
                "mistral:7b-instruct", 
                "llama3:8b",
                "mixtral:latest",
                "codellama:7b",
                "phi3:latest",
                "gemma3:4b",
                "qwen2.5:7b"
            ]
            
            available_models = []
            
            for model in test_models:
                try:
                    # Quick test with minimal prompt
                    test_payload = {
                        "input": {
                            "prompt": "test",
                            "model": model,
                            "max_tokens": 10
                        }
                    }
                    
                    url = f"{self.base_url}/{self.endpoint_id}/runsync"
                    response = requests.post(url, headers=self.headers, json=test_payload, timeout=10)
                    
                    if response.status_code == 200:
                        available_models.append(model)
                        print(f"✅ {model} - Available")
                    else:
                        print(f"❌ {model} - Status {response.status_code}")
                        
                except Exception as e:
                    print(f"⚠️ {model} - Error: {e}")
                    continue
            
            # Cache the results
            self._available_models = available_models
            self._models_cache_time = current_time
            
            print(f"📋 RunPod: Found {len(available_models)} available models")
            return available_models
            
        except Exception as e:
            print(f"❌ Error getting RunPod models: {e}")
            return None

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Check job status using the /status endpoint
        Following official docs Step 3: Monitor job progress
        """
        url = f"{self.base_url}/{self.endpoint_id}/status/{job_id}"
        
        try:
            print(f"🔍 Checking job status: {job_id}")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            job_data = response.json()
            print(f"📊 Job status: {job_data.get('status')}")
            
            if job_data.get('status') == 'COMPLETED':
                print(f"🎉 Job completed successfully!")
                if 'executionTime' in job_data:
                    exec_time = job_data['executionTime'] / 1000  # Convert to seconds
                    print(f"⏱️ Execution time: {exec_time:.2f}s")
            elif job_data.get('status') == 'IN_PROGRESS':
                print(f"⏳ Job still processing...")
            elif job_data.get('status') == 'IN_QUEUE':
                delay_time = job_data.get('delayTime', 0) / 1000  # Convert to seconds
                print(f"⏳ Job waiting in queue (waited: {delay_time:.2f}s)")
            elif job_data.get('status') == 'FAILED':
                print(f"❌ Job failed!")
                if 'error' in job_data:
                    print(f"💥 Error: {job_data['error']}")
            
            return job_data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error getting job status: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"📄 Response: {e.response.text}")
            return None

    def submit_sync_job(self, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Submit a synchronous job to RunPod serverless endpoint
        Using /runsync for immediate responses (when available)
        """
        url = f"{self.base_url}/{self.endpoint_id}/runsync"
        
        payload = {"input": input_data}
        
        try:
            print(f"📤 Submitting sync job to: {url}")
            print(f"📋 Payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=300)  # 5 min timeout
            response.raise_for_status()
            
            job_data = response.json()
            print(f"✅ Sync job completed")
            
            if 'executionTime' in job_data:
                exec_time = job_data['executionTime'] / 1000  # Convert to seconds
                print(f"⏱️ Execution time: {exec_time:.2f}s")
            
            return job_data
            
        except requests.exceptions.Timeout:
            print(f"⏰ Sync job timed out (5 minutes)")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Error with sync job: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"📄 Response: {e.response.text}")
            return None

    def wait_for_completion(self, job_id: str, max_wait_time: int = 600) -> Optional[Dict[str, Any]]:
        """
        Wait for job completion, polling status endpoint
        Following official docs Step 4: Retrieve completed results
        """
        import time
        
        print(f"⏳ Waiting for job completion: {job_id}")
        print(f"⏱️ Max wait time: {max_wait_time} seconds")
        
        start_time = time.time()
        poll_interval = 5  # Check every 5 seconds
        
        while time.time() - start_time < max_wait_time:
            job_status = self.get_job_status(job_id)
            
            if not job_status:
                print(f"❌ Failed to get job status")
                return None
                
            status = job_status.get('status')
            
            if status == 'COMPLETED':
                return job_status
            elif status == 'FAILED':
                print(f"❌ Job failed")
                return job_status
            elif status in ['IN_QUEUE', 'IN_PROGRESS']:
                print(f"⏳ Still processing... waiting {poll_interval}s")
                time.sleep(poll_interval)
            else:
                print(f"❓ Unknown status: {status}")
                time.sleep(poll_interval)
        
        print(f"⏰ Job timed out after {max_wait_time} seconds")
        return None


class PeteOllamaHandler:
    """Main handler that routes all requests through RunPod serverless"""
    
    def __init__(self):
        self.runpod_client = RunPodServerlessClient()
    
    def chat_completion(self, message: str, model: str = "llama3:latest", **kwargs) -> Dict[str, Any]:
        """Handle chat completion requests"""
        print(f"💬 Chat completion request")
        print(f"📝 Message: {message}")
        print(f"🤖 Model: {model}")
        
        # Prepare input for RunPod serverless endpoint (backward compatible)
        input_data = {
            "prompt": message,
            "model": model,
            "max_tokens": kwargs.get("max_tokens", 2048),  # Ensure adequate response length
            "temperature": kwargs.get("temperature", 0.7),
            "stop": kwargs.get("stop", ["\nMessage from tenant:", "\nPlease respond as Jamie:", "USER:", "TENANT:", "\n\n---"]),  # Stop sequences
            **kwargs
        }
        
        # Try sync first, fallback to async
        try:
            result = self.runpod_client.submit_sync_job(input_data)
            if result and result.get('status') != 'FAILED':
                return self._extract_chat_response(result)
        except Exception as e:
            print(f"⚠️ Sync job failed, trying async: {e}")
        
        # Fallback to async
        job = self.runpod_client.submit_job(input_data)
        if not job:
            return {"error": "Failed to submit job", "status": "error"}
        
        job_id = job.get('id')
        if not job_id:
            return {"error": "No job ID received", "status": "error"}
        
        # Wait for completion
        completed_job = self.runpod_client.wait_for_completion(job_id)
        if not completed_job:
            return {"error": "Job failed or timed out", "status": "error"}
        
        return self._extract_chat_response(completed_job)
    
    def vapi_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle VAPI webhook requests"""
        print(f"📞 VAPI webhook request")
        print(f"📋 Webhook data keys: {list(webhook_data.keys())}")
        
        # Extract message from VAPI webhook
        user_message = webhook_data.get('message', '')
        call_id = webhook_data.get('call_id', '')
        
        if not user_message:
            # Try alternative webhook formats
            conversation = webhook_data.get('conversation', {})
            user_message = conversation.get('user_message', '')
        
        if not user_message:
            return {"error": "No user message found in webhook", "status": "error"}
        
        # Prepare input for RunPod serverless endpoint
        input_data = {
            "type": "vapi_webhook", 
            "webhook_data": webhook_data,
            "message": user_message,
            "call_id": call_id,
            "model": "llama3:latest"  # Default model for VAPI
        }
        
        # Try sync first for faster VAPI responses
        try:
            result = self.runpod_client.submit_sync_job(input_data)
            if result and result.get('status') != 'FAILED':
                return self._extract_vapi_response(result, call_id)
        except Exception as e:
            print(f"⚠️ Sync VAPI job failed: {e}")
        
        # Fallback to async (not ideal for VAPI but better than nothing)
        job = self.runpod_client.submit_job(input_data)
        if not job:
            return {"error": "Failed to submit VAPI job", "status": "error"}
        
        job_id = job.get('id')
        completed_job = self.runpod_client.wait_for_completion(job_id, max_wait_time=60)  # Shorter timeout for VAPI
        
        if not completed_job:
            return {"error": "VAPI job failed or timed out", "status": "error"}
        
        return self._extract_vapi_response(completed_job, call_id)
    
    def admin_action(self, action: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle admin panel actions"""
        print(f"⚙️ Admin action: {action}")
        
        # Prepare input for RunPod serverless endpoint
        input_data = {
            "type": "admin",
            "action": action,
            "data": data or {}
        }
        
        # Admin actions can be async
        job = self.runpod_client.submit_job(input_data)
        if not job:
            return {"error": "Failed to submit admin job", "status": "error"}
        
        job_id = job.get('id')
        completed_job = self.runpod_client.wait_for_completion(job_id)
        
        if not completed_job:
            return {"error": "Admin job failed or timed out", "status": "error"}
        
        return self._extract_admin_response(completed_job)
    
    def _extract_chat_response(self, job_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract chat response from RunPod job result"""
        if job_result.get('status') == 'FAILED':
            error = job_result.get('error', 'Unknown error')
            return {"error": error, "status": "error"}
        
        output = job_result.get('output', {})
        
        # Handle different response formats
        if isinstance(output, dict):
            # Try multiple possible response fields
            response_text = (
                output.get('response') or 
                output.get('message') or 
                output.get('text', [''])[0] if output.get('text') and isinstance(output.get('text'), list) else 
                output.get('text', '') or 
                ''
            )
            model = output.get('model', 'unknown')
            
            return {
                "status": "success",
                "response": response_text,
                "model": model,
                "execution_time": job_result.get('executionTime', 0) / 1000,
                "input_tokens": output.get('input_tokens', 0),
                "output_tokens": output.get('output_tokens', 0)
            }
        elif isinstance(output, str):
            return {
                "status": "success", 
                "response": output,
                "model": "unknown",
                "execution_time": job_result.get('executionTime', 0) / 1000
            }
        else:
            return {"error": "Invalid output format", "status": "error"}
    
    def _extract_vapi_response(self, job_result: Dict[str, Any], call_id: str) -> Dict[str, Any]:
        """Extract VAPI webhook response from RunPod job result"""
        if job_result.get('status') == 'FAILED':
            error = job_result.get('error', 'Unknown error')
            return {"error": error, "status": "error", "call_id": call_id}
        
        output = job_result.get('output', {})
        
        # Format for VAPI
        if isinstance(output, dict):
            response_text = output.get('vapi_response', output.get('response', output.get('message', '')))
        elif isinstance(output, str):
            response_text = output
        else:
            response_text = "I'm sorry, I couldn't process your request."
        
        return {
            "status": "success",
            "response": response_text,
            "call_id": call_id,
            "execution_time": job_result.get('executionTime', 0) / 1000
        }
    
    def _extract_admin_response(self, job_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract admin response from RunPod job result"""
        if job_result.get('status') == 'FAILED':
            error = job_result.get('error', 'Unknown error')
            return {"error": error, "status": "error"}
        
        output = job_result.get('output', {})
        
        return {
            "status": "success",
            "data": output,
            "execution_time": job_result.get('executionTime', 0) / 1000
        }


# Global handler instance
pete_handler = PeteOllamaHandler()


def main():
    """Test the handler locally"""
    print("🧪 Testing PeteOllama RunPod Handler")
    print("=" * 50)
    
    # Test chat completion
    print("\n💬 Testing chat completion...")
    chat_result = pete_handler.chat_completion("Hello, my name is Mark. How are you doing today?")
    print(f"📋 Result: {json.dumps(chat_result, indent=2)}")
    
    # Test VAPI webhook (mock data)
    print("\n📞 Testing VAPI webhook...")
    mock_webhook = {
        "message": "My toilet is leaking, can you help?",
        "call_id": "test-call-123"
    }
    vapi_result = pete_handler.vapi_webhook(mock_webhook)
    print(f"📋 Result: {json.dumps(vapi_result, indent=2)}")
    
    # Test admin action
    print("\n⚙️ Testing admin action...")
    admin_result = pete_handler.admin_action("status")
    print(f"📋 Result: {json.dumps(admin_result, indent=2)}")


if __name__ == "__main__":
    main()
