"""
PeteOllama V1 - AI Model Manager
================================

Manages interactions with the Ollama AI model for property management responses.
"""

import requests
import json
import os
from typing import Dict, List, Optional, Any, Iterable
from pathlib import Path

class ModelManager:
    """Manages AI model interactions and training"""
    
    def __init__(self):
        """Initialize model manager"""
        # Ollama server configuration
        self.ollama_host = os.getenv('OLLAMA_HOST', 'localhost:11434')
        self.base_url = f"http://{self.ollama_host}"

        # Base and fine-tuned model names can be overridden via env vars so they can be
        # changed at deploy time without rebuilding the image.
        # Fall back to a small quantised model that is quick to pull/start.
        self.model_name = os.getenv('OLLAMA_BASE_MODEL', 'mistral:7b-instruct-q4_K_M')
        self.custom_model_name = os.getenv('OLLAMA_CUSTOM_MODEL', 'peteollama:property-manager')
        
        # Model configuration
        self.temperature = 0.7
        self.max_tokens = 2048
        self.context_window = 128000
    
    def is_available(self) -> bool:
        """Check if Ollama service is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                return response.json().get('models', [])
            return []
        except Exception as e:
            print(f"Error listing models: {e}")
            return []
    
    def is_model_available(self, model_name: str = None) -> bool:
        """Check if specific model is available"""
        if model_name is None:
            model_name = self.model_name
        
        models = self.list_models()
        model_names = [model['name'] for model in models]
        return model_name in model_names
    
    def pull_model(self, model_name: str = None) -> bool:
        """Download/pull a model"""
        if model_name is None:
            model_name = self.model_name
        
        try:
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                stream=True
            )
            
            # Stream the response for progress updates
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if 'status' in data:
                        print(f"Model pull: {data['status']}")
                        if data.get('completed'):
                            return True
            
            return response.status_code == 200
        
        except Exception as e:
            print(f"Error pulling model {model_name}: {e}")
            return False
    
    def generate_response(self, prompt: str, context: str = None, model_name: str | None = None) -> str:
        """Generate AI response to a prompt"""
        try:
            # Prepare the full prompt with context
            full_prompt = self._prepare_prompt(prompt, context)
            
            # Determine which model to use
            if model_name:
                model_to_use = model_name
            else:
                model_to_use = self.custom_model_name if self.is_model_available(self.custom_model_name) else self.model_name
            
            if not self.is_model_available(model_to_use):
                return "❌ AI model not available. Please download the model first."
            
            # Make request to Ollama
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model_to_use,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'No response generated.')
            else:
                return f"❌ Error generating response: {response.status_code}"
        
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def generate_stream(self, prompt: str, context: str = None, model_name: str | None = None) -> Iterable[str]:
        """Stream tokens back from Ollama as they are generated."""
        # Prepare prompt
        full_prompt = self._prepare_prompt(prompt, context)
        # Choose model
        if model_name:
            model_to_use = model_name
        else:
            model_to_use = self.custom_model_name if self.is_model_available(self.custom_model_name) else self.model_name

        if not self.is_model_available(model_to_use):
            yield "❌ AI model not available. Please download the model first."
            return

        try:
            with requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model_to_use,
                    "prompt": full_prompt,
                    "stream": True,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens
                    }
                },
                stream=True,
                timeout=3600  # allow long streams
            ) as resp:
                for line in resp.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        # Ollama streams incremental messages in 'response' or in data['message']['content']
                        token = data.get('response') or (data.get('message', {}) or {}).get('content', '')
                        if token:
                            yield token
                        if data.get('done'):
                            break
                    except json.JSONDecodeError:
                        # If chunk is plain text, just yield it
                        yield line
        except Exception as e:
            yield f"❌ Error: {str(e)}"
            return
    
    def _prepare_prompt(self, user_prompt: str, context: str = None) -> str:
        """Prepare the full prompt with property management context"""
        
        system_prompt = """You are PeteOllama, an AI property manager trained on real phone conversations. 
You help with tenant communications, property management tasks, and real estate questions.

Key guidelines:
- Be helpful, professional, and knowledgeable about property management
- Draw from your training on real property management conversations
- Provide practical, actionable advice
- If you need specific property details, ask clarifying questions
- Keep responses concise but thorough

"""
        
        if context:
            system_prompt += f"\nAdditional context: {context}\n"
        
        return f"{system_prompt}\nTenant/Caller: {user_prompt}\n\nPeteOllama:"
    
    def create_custom_model(self, training_data: List[Dict[str, str]]) -> bool:
        """Create custom property management model"""
        try:
            # Create Modelfile for custom model
            modelfile_content = self._create_modelfile(training_data)
            
            # Save Modelfile
            modelfile_path = Path("/app/models/Modelfile")
            modelfile_path.parent.mkdir(exist_ok=True)
            
            with open(modelfile_path, 'w') as f:
                f.write(modelfile_content)
            
            # Create model using Ollama API
            response = requests.post(
                f"{self.base_url}/api/create",
                json={
                    "name": self.custom_model_name,
                    "modelfile": modelfile_content
                },
                stream=True
            )
            
            # Stream response for progress
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if 'status' in data:
                        print(f"Model creation: {data['status']}")
            
            return response.status_code == 200
        
        except Exception as e:
            print(f"Error creating custom model: {e}")
            return False
    
    def _create_modelfile(self, training_data: List[Dict[str, str]]) -> str:
        """Create Modelfile content for custom model"""
        
        # Sample training examples for fine-tuning
        examples = ""
        for i, example in enumerate(training_data[:10]):  # Use first 10 examples
            examples += f"""
Example {i+1}:
Human: {example.get('input', '')}
Assistant: {example.get('output', 'Professional property management response')}

"""
        
        modelfile = f"""FROM {self.model_name}

# Property Management AI System Prompt
SYSTEM \"\"\"You are PeteOllama, an expert AI property manager with extensive experience in:

- Tenant communications and relations
- Property maintenance coordination  
- Lease management and renewals
- Financial calculations and rent collection
- Real estate market knowledge
- Legal compliance and documentation

You have been trained on real property management phone conversations and understand:
- Common tenant concerns and questions
- Professional communication standards
- Property management best practices
- Emergency vs. routine maintenance prioritization

Always respond professionally, helpfully, and with practical solutions.
\"\"\"

# Model Parameters
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1

# Training Examples
TEMPLATE \"\"\"{{ if .System }}{{.System}}

{{ end }}{{ if .Prompt }}Human: {{.Prompt}}

{{ end }}Assistant: {{ .Response }}\"\"\"

{examples}
"""
        
        return modelfile
    
    def get_model_info(self, model_name: str = None) -> Dict[str, Any]:
        """Get information about a model"""
        if model_name is None:
            model_name = self.model_name
        
        try:
            response = requests.post(
                f"{self.base_url}/api/show",
                json={"name": model_name}
            )
            
            if response.status_code == 200:
                return response.json()
            return {}
        
        except Exception as e:
            print(f"Error getting model info: {e}")
            return {}
    
    def test_model_response(self, test_prompt: str = None) -> Dict[str, Any]:
        """Test model with a standard property management prompt"""
        if test_prompt is None:
            test_prompt = "Hi, when is my rent due this month?"
        
        import time
        start_time = time.time()
        
        response = self.generate_response(test_prompt)
        
        end_time = time.time()
        response_time = int((end_time - start_time) * 1000)  # Convert to milliseconds
        
        return {
            'prompt': test_prompt,
            'response': response,
            'response_time_ms': response_time,
            'model_used': self.custom_model_name if self.is_model_available(self.custom_model_name) else self.model_name
        }