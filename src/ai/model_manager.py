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
import sys

# Import our working RunPod handler
# Try multiple paths for different deployment environments
try:
    from runpod_handler import pete_handler
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from runpod_handler import pete_handler

# Import OpenRouter handler for provider switching
try:
    from openrouter_handler import OpenRouterHandler
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from openrouter_handler import OpenRouterHandler

# Import conversation similarity system for intelligent instant responses
try:
    from analytics.conversation_similarity import ConversationSimilarityAnalyzer
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from analytics.conversation_similarity import ConversationSimilarityAnalyzer

# Import response cache for fallback caching
try:
    from ai.response_cache import get_instant_response, response_cache
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from response_cache import get_instant_response, response_cache

class ModelManager:
    """Manages AI model interactions and training"""
    
    def __init__(self):
        """Initialize model manager"""
        # Ollama server configuration
        self.ollama_host = os.getenv('OLLAMA_HOST', 'localhost:11434')
        self.base_url = f"http://{self.ollama_host}"

        # Load model settings
        self.settings_file = Path("config/model_settings.json")
        self.default_model = self._load_default_model()
        
        # Base and fine-tuned model names can be overridden via env vars so they can be
        # changed at deploy time without rebuilding the image.
        # Fall back to a small quantised model that is quick to pull/start.
        self.model_name = os.getenv('OLLAMA_BASE_MODEL', 'mistral:7b-instruct-q4_K_M')
        self.custom_model_name = os.getenv('OLLAMA_CUSTOM_MODEL', self.default_model or 'peteollama:property-manager')
        
        # Model configuration
        self.temperature = 0.7
        self.max_tokens = int(os.getenv('MAX_TOKENS', '4096'))  # Increased for longer responses
        self.context_window = 128000
        
        # Initialize conversation similarity analyzer for intelligent responses
        # Set similarity threshold for instant responses (0.75 = 75% similarity)
        self.similarity_threshold = float(os.getenv('SIMILARITY_THRESHOLD', '0.75'))
        self.similarity_analyzer = None  # Lazy load to avoid startup delays
        
        # Initialize provider handlers
        self.openrouter_handler = None  # Lazy load
        self._current_provider = None  # Cache for current provider
    
    def _get_similarity_analyzer(self):
        """Lazy load the conversation similarity analyzer"""
        if self.similarity_analyzer is None:
            try:
                print("🧠 Loading conversation similarity analyzer...")
                self.similarity_analyzer = ConversationSimilarityAnalyzer()
                print(f"✅ Loaded {len(self.similarity_analyzer.conversation_samples)} conversation samples")
            except Exception as e:
                print(f"⚠️ Failed to load similarity analyzer: {e}")
                self.similarity_analyzer = None
        return self.similarity_analyzer
    
    def _get_openrouter_handler(self):
        """Lazy load the OpenRouter handler"""
        if self.openrouter_handler is None:
            try:
                print("🌐 Loading OpenRouter handler...")
                self.openrouter_handler = OpenRouterHandler()
                print("✅ OpenRouter handler loaded")
            except Exception as e:
                print(f"⚠️ Failed to load OpenRouter handler: {e}")
                self.openrouter_handler = None
        return self.openrouter_handler
    
    def _get_current_provider(self) -> str:
        """Get current provider from settings"""
        try:
            # Import model settings to get current provider
            from config.model_settings import model_settings
            settings = model_settings.get_provider_settings()
            provider = settings.get('default_provider', 'ollama')
            print(f"🔧 Current provider: {provider}")
            return provider
        except Exception as e:
            print(f"⚠️ Error getting current provider: {e}, defaulting to ollama")
            return 'ollama'
    
    def _route_to_provider(self, prompt: str, model_name: str = None, **kwargs) -> Dict[str, Any]:
        """Route request to appropriate provider based on settings"""
        provider = self._get_current_provider()
        
        if provider == 'openrouter':
            print(f"🌐 Routing to OpenRouter")
            handler = self._get_openrouter_handler()
            if handler and handler.available:
                # Map Ollama model names to OpenRouter models
                openrouter_model = self._map_to_openrouter_model(model_name)
                return handler.chat_completion(prompt, model=openrouter_model, **kwargs)
            else:
                print(f"⚠️ OpenRouter not available, falling back to RunPod")
                return pete_handler.chat_completion(prompt, model=model_name, **kwargs)
        
        elif provider == 'ollama':
            print(f"🏠 Routing to Ollama")
            # Try local Ollama first
            try:
                result = self._ollama_completion(prompt, model_name, **kwargs)
                if result.get('status') == 'success':
                    return result
            except Exception as e:
                print(f"⚠️ Ollama failed: {e}, falling back to RunPod")
            
            # Fallback to RunPod if Ollama fails
            return pete_handler.chat_completion(prompt, model=model_name, **kwargs)
        
        else:  # runpod or default
            print(f"☁️ Routing to RunPod")
            return pete_handler.chat_completion(prompt, model=model_name, **kwargs)
    
    def _map_to_openrouter_model(self, ollama_model: str) -> str:
        """Map Ollama model names to OpenRouter model names"""
        if not ollama_model:
            return "meta-llama/llama-3.1-8b-instruct:free"
        
        # Simple mapping - can be expanded
        model_mapping = {
            "llama3:latest": "meta-llama/llama-3.1-8b-instruct:free",
            "llama3:8b": "meta-llama/llama-3.1-8b-instruct:free",
            "mistral:latest": "mistralai/mistral-7b-instruct:free",
            "mixtral:latest": "mistralai/mixtral-8x7b-instruct:free",
        }
        
        # Default to a good free model if no mapping found
        return model_mapping.get(ollama_model, "meta-llama/llama-3.1-8b-instruct:free")
    
    def _ollama_completion(self, prompt: str, model_name: str = None, **kwargs) -> Dict[str, Any]:
        """Direct Ollama API completion"""
        try:
            model_to_use = model_name or self.model_name
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model_to_use,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": kwargs.get('temperature', self.temperature),
                        "num_predict": kwargs.get('max_tokens', self.max_tokens)
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "response": data.get('response', ''),
                    "model": model_to_use,
                    "provider": "ollama"
                }
            else:
                return {"status": "error", "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _load_default_model(self) -> Optional[str]:
        """Load the default model from settings file"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                    return data.get('default_model')
        except Exception as e:
            print(f"Error loading default model from settings: {e}")
        return None
    
    def is_available(self) -> bool:
        """Check if Ollama service is available or if we're in serverless mode"""
        try:
            # First check if RunPod proxy is available
            try:
                # If pete_handler is imported, we have RunPod serverless capability
                if 'pete_handler' in globals() or 'pete_handler' in sys.modules:
                    print("🚀 Serverless mode detected via RunPod")
                    return True
            except Exception as proxy_error:
                print(f"RunPod proxy check failed: {proxy_error}")
                
            # Fallback to checking Ollama service
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Model availability check failed: {e}")
            # Still return True if we have pete_handler available
            return 'pete_handler' in globals() or 'pete_handler' in sys.modules
    
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

    def train_property_manager(self) -> bool:
        """Train or update the custom property-manager model using conversations in pete.db."""
        try:
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from database.pete_db_manager import PeteDBManager
            db = PeteDBManager()
            examples = db.get_training_examples()
            if not examples:
                print("No training examples found in DB")
                return False
            return self.create_custom_model(examples)
        except Exception as e:
            print(f"Error training property manager model: {e}")
            return False
    
    def is_model_available(self, model_name: str = None) -> bool:
        """Check if specific model is available"""
        if model_name is None:
            model_name = self.custom_model_name
        
        models = self.list_models()
        model_names = [model['name'] for model in models]
        return model_name in model_names
    
    def pull_model(self, model_name: str = None) -> bool:
        """Download/pull a model"""
        if model_name is None:
            model_name = self.custom_model_name
        
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
        """Generate AI response using intelligent similarity matching + RunPod serverless fallback"""
        try:
            import time
            
            # STEP 1: Try conversation similarity matching for instant responses
            similarity_start = time.time()
            
            analyzer = self._get_similarity_analyzer()
            if analyzer:
                try:
                    similarity_result = analyzer.calculate_similarity(prompt, context or '')
                    similarity_time = (time.time() - similarity_start) * 1000
                    
                    # Check if similarity is high enough for instant response
                    if similarity_result.similarity_score >= self.similarity_threshold and similarity_result.best_match:
                        response = similarity_result.best_match.agent_response
                        print(f"🎯 SIMILARITY HIT ({similarity_time:.0f}ms, {similarity_result.similarity_score:.3f}): {prompt[:50]}...")
                        print(f"   📝 Response: {response[:80]}...")
                        
                        # Add to fallback cache for future use
                        try:
                            response_cache.add_response_to_cache(prompt, response)
                        except Exception as cache_error:
                            print(f"⚠️ Cache update failed: {cache_error}")
                        
                        return response
                    else:
                        print(f"📊 Similarity too low ({similarity_time:.0f}ms, {similarity_result.similarity_score:.3f} < {self.similarity_threshold})")
                        
                except Exception as sim_error:
                    similarity_time = (time.time() - similarity_start) * 1000
                    print(f"⚠️ Similarity analysis failed ({similarity_time:.0f}ms): {sim_error}")
            else:
                print("🔧 Similarity analyzer not available, checking fallback cache...")
            
            # STEP 2: Try fallback cache lookup
            cache_start = time.time()
            cached_response = get_instant_response(prompt)
            if cached_response:
                cache_time = (time.time() - cache_start) * 1000
                print(f"⚡ FALLBACK CACHE HIT ({cache_time:.1f}ms): {prompt[:50]}...")
                return cached_response
            
            cache_time = (time.time() - cache_start) * 1000
            print(f"🔍 All caches miss ({cache_time:.1f}ms), routing to RunPod...")
            
            # STEP 3: Fallback to RunPod serverless
            full_prompt = self._prepare_prompt(prompt, context)
            model_to_use = model_name or "llama3:latest"
            
            print(f"🚀 ModelManager routing to RunPod: {model_to_use}")
            
            runpod_start = time.time()
            result = pete_handler.chat_completion(full_prompt, model=model_to_use)
            runpod_time = (time.time() - runpod_start) * 1000
            
            if result.get('status') == 'success':
                response = result.get('response', 'No response generated.')
                print(f"✅ RunPod response ({runpod_time:.0f}ms): {response[:50]}...")
                
                # STEP 4: Add successful response to cache for future instant replies
                try:
                    response_cache.add_response_to_cache(prompt, response)
                except Exception as cache_error:
                    print(f"⚠️ Cache update failed: {cache_error}")
                
                return response
            else:
                return f"❌ RunPod Error: {result.get('error', 'Unknown error')}"
        
        except Exception as e:
            return f"❌ Error: {str(e)}"

    def generate_stream(self, prompt: str, context: str = None, model_name: str | None = None) -> Iterable[str]:
        """Stream AI response using provider-based routing with simulated streaming"""
        try:
            # Prepare prompt
            full_prompt = self._prepare_prompt(prompt, context)
            model_to_use = model_name or "llama3:latest"
            
            provider = self._get_current_provider()
            print(f"🚀 ModelManager streaming via {provider.upper()}: {model_to_use}")
            
            # Send immediate feedback to user
            yield "[Thinking...]"
            
            # Route to appropriate provider
            result = self._route_to_provider(full_prompt, model_to_use, max_tokens=2048, temperature=0.7)
            
            # Clear the "thinking" message
            yield "\b" * 13 + " " * 13 + "\b" * 13  # Clear "[Thinking...]"
            
            if result.get('status') == 'success':
                response_text = result.get('response', 'No response generated.')
                actual_provider = result.get('provider', provider)
                
                print(f"✅ {actual_provider.upper()} response: {response_text[:100]}...")
                
                # Enhanced streaming simulation with natural pacing
                import time
                import re
                
                # Split by sentences for more natural streaming
                sentences = re.split(r'(?<=[.!?])\s+', response_text)
                
                for i, sentence in enumerate(sentences):
                    if sentence.strip():
                        # Stream each sentence word by word
                        words = sentence.split()
                        for j, word in enumerate(words):
                            if i == 0 and j == 0:
                                yield word
                            else:
                                yield " " + word
                            
                            # Faster streaming with minimal delays
                            if word.endswith(('.', '!', '?')):
                                time.sleep(0.08)  # Reduced sentence pause
                            elif word.endswith((',', ';')):
                                time.sleep(0.05)  # Reduced comma pause  
                            else:
                                time.sleep(0.02)  # Faster word delay
                        
                        # Small pause between sentences
                        if i < len(sentences) - 1:
                            time.sleep(0.1)
            else:
                yield f"❌ {provider.upper()} Error: {result.get('error', 'Unknown error')}"
                
        except Exception as e:
            yield f"❌ Error: {str(e)}"
            return
    
    def _prepare_prompt(self, user_prompt: str, context: str = None) -> str:
        """Prepare the full prompt with property management context"""
        
        system_prompt = """You are Jamie, an AI property manager trained on real phone conversations. 
You help with tenant communications, property management tasks, and real estate questions.

Key guidelines:
- Be helpful, professional, and knowledgeable about property management
- Draw from your training on real property management conversations
- Provide practical, actionable advice
- If you need specific property details, ask clarifying questions
- Keep responses concise but thorough
- You work with Christina and handle property management for various locations
- Always respond directly as Jamie without adding extra conversation elements
- End your response naturally without continuing the conversation

"""
        
        if context:
            system_prompt += f"\nAdditional context: {context}\n"
        
        # Use a cleaner prompt format that doesn't encourage conversation continuation
        return f"{system_prompt}\nMessage from tenant: {user_prompt}\n\nPlease respond as Jamie:"
    
    def create_custom_model(self, training_data: List[Dict[str, str]]) -> bool:
        """Create custom property management model"""
        try:
            # Create Modelfile for custom model
            modelfile_content = self._create_modelfile(training_data)
            
            # Save Modelfile (use local models directory)
            models_dir = Path(os.getcwd()) / "models"
            models_dir.mkdir(exist_ok=True)
            modelfile_path = models_dir / "Modelfile"
            
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