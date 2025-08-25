"""
Provider Service
===============

Service class to handle provider management, switching, and OpenRouter API operations.
"""

import os
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.logger import logger
from config.model_settings import model_settings
from vapi.models.webhook_models import (
    ProviderError, ModelAvailabilityError, PersonaModel, Persona,
    create_error_response, create_model_availability_error
)

class ProviderService:
    """Service for managing AI providers (Ollama, OpenRouter, RunPod)"""
    
    def __init__(self):
        self.valid_providers = ["ollama", "runpod", "openrouter"]
    
    async def get_personas_for_provider(self, provider: str) -> List[Persona]:
        """Get personas for the specified provider - respecting system configuration"""
        try:
            # Check if provider is enabled in system configuration
            if not self._is_provider_enabled(provider):
                logger.warning(f"Provider {provider} is disabled in system configuration")
                return []
            
            if provider == 'openrouter':
                return await self._get_openrouter_personas()
            elif provider == 'ollama':
                return await self._get_ollama_personas()
            elif provider == 'runpod':
                return await self._get_runpod_personas()
            else:
                logger.warning(f"Unknown provider {provider}, defaulting to Ollama")
                return await self._get_ollama_personas()
        except Exception as e:
            logger.error(f"Error getting personas for provider {provider}: {e}")
            return self._get_fallback_personas()
    
    async def get_all_available_personas(self) -> List[Persona]:
        """Get personas from all enabled providers - respecting system configuration"""
        try:
            all_personas = []
            
            # Get current default provider from system config
            from src.config.system_config import system_config
            current_provider = system_config.config.default_provider
            
            # Get personas for current provider first (priority)
            if self._is_provider_enabled(current_provider):
                current_personas = await self.get_personas_for_provider(current_provider)
                all_personas.extend(current_personas)
                logger.info(f"✅ Added {len(current_personas)} personas from current provider: {current_provider}")
            
            # Get personas from other enabled providers
            for provider in ['openrouter', 'ollama', 'runpod']:
                if provider != current_provider and self._is_provider_enabled(provider):
                    try:
                        provider_personas = await self.get_personas_for_provider(provider)
                        all_personas.extend(provider_personas)
                        logger.info(f"✅ Added {len(provider_personas)} personas from provider: {provider}")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to get personas from {provider}: {e}")
                        continue
            
            if not all_personas:
                logger.warning("⚠️ No personas available from any enabled provider, using fallback")
                return self._get_fallback_personas()
            
            logger.info(f"🎯 Total personas available: {len(all_personas)} from enabled providers")
            return all_personas
            
        except Exception as e:
            logger.error(f"Error getting all available personas: {e}")
            return self._get_fallback_personas()
    
    def _is_provider_enabled(self, provider: str) -> bool:
        """Check if a provider is enabled in system configuration"""
        try:
            from src.config.system_config import system_config
            
            # Get provider config from system configuration
            provider_config = system_config.get_provider_config(provider)
            if provider_config:
                enabled = provider_config.enabled
                api_key_set = bool(provider_config.api_key) if hasattr(provider_config, 'api_key') else False
                
                # Provider must be enabled AND have API key (except Ollama which doesn't need one)
                if provider == 'ollama':
                    return enabled  # Ollama is local, no API key needed
                else:
                    return enabled and api_key_set
            else:
                logger.warning(f"Provider {provider} not found in system configuration")
                return False
                
        except Exception as e:
            logger.error(f"Error checking provider {provider} status: {e}")
            return False
    
    async def _get_ollama_personas(self) -> List[Persona]:
        """Get Ollama model personas using the new model controller"""
        try:
            # Try to use the new model controller first
            from src.config.model_controller import model_controller
            
            if model_controller.is_control_enabled():
                logger.info("📋 Using Model Controller for Ollama personas")
                visible_models = model_controller.get_visible_models()
                
                if visible_models:
                    # Convert to Persona format
                    personas = []
                    for model in visible_models:
                        persona = Persona(
                            name=model.get('display_name', model.get('name')),
                            description=model.get('description', ''),
                            type='primary' if model.get('priority', 999) <= 2 else 'secondary',
                            models=[PersonaModel(
                                name=model.get('name'),
                                display_name=model.get('display_name', model.get('name')),
                                description=model.get('description', ''),
                                auto_preload=model.get('auto_preload', False),
                                type=model.get('type', 'unknown'),
                                base_model=model.get('base_model', 'unknown')
                            )]
                        )
                        personas.append(persona)
                    
                    logger.info(f"📋 Model Controller: Created {len(personas)} personas from {len(visible_models)} visible models")
                    return personas
                else:
                    logger.warning("📋 Model Controller: No visible models found")
            
            # Fallback to old method if controller is disabled or no models
            logger.info("📋 Falling back to old Ollama personas method")
            model_settings.refresh_from_ollama()
            ui_models = model_settings.get_ui_models()
            
            if not ui_models:
                logger.warning("No models enabled for UI display")
                return []
            
            # Check which models are actually available in Ollama
            available_models = await self._get_actual_ollama_models()
            logger.info(f"📋 Ollama: {len(available_models)} models actually available")
            
            # Filter UI models to only show those that are actually available
            filtered_models = []
            for model_config in ui_models:
                if model_config.name in available_models:
                    filtered_models.append(model_config)
                else:
                    logger.info(f"⚠️ Model {model_config.name} configured but not available in Ollama")
            
            if not filtered_models:
                logger.warning("No configured models are actually available in Ollama")
                # Fallback to showing all configured models (old behavior)
                filtered_models = ui_models
            
            # Process filtered models into personas
            persona_list = []
            jamie_models = []
            generic_models = []
            
            for model_config in filtered_models:
                model_data = PersonaModel(
                    name=model_config.name,
                    display_name=model_config.display_name,
                    description=model_config.description,
                    auto_preload=model_config.auto_preload,
                    type=getattr(model_config, 'type', 'unknown'),
                    base_model=getattr(model_config, 'base_model', 'unknown')
                )
                
                if model_config.is_jamie_model:
                    jamie_models.append(model_data)
                else:
                    generic_models.append(model_data)
            
            # Create Jamie persona if we have Jamie models
            if jamie_models:
                persona_list.append(Persona(
                    name="Jamie (Property Manager)",
                    icon="/public/Jamie.png",
                    type="primary",
                    models=jamie_models,
                    description="Professional property manager AI trained on real conversations"
                ))
            
            # Add generic models
            for model in generic_models:
                persona_list.append(Persona(
                    name=model.display_name,
                    icon="/public/pete.png",
                    type="generic",
                    models=[model],
                    description=model.description
                ))
            
            return persona_list
            
        except Exception as e:
            logger.error(f"Error in _get_ollama_personas: {e}")
            # Return fallback personas
            return self._get_fallback_personas()
    
    async def _get_openrouter_personas(self) -> List[Persona]:
        """Get OpenRouter model personas - dynamically fetched from OpenRouter API"""
        try:
            # Try to fetch models dynamically from OpenRouter API
            openrouter_models = await self._fetch_openrouter_models()
            
            # If dynamic fetch failed, raise a validation error
            if not openrouter_models:
                logger.error("OpenRouter API unavailable or API key missing")
                error = create_model_availability_error(
                    provider="openrouter",
                    requested_models=["all_openrouter_models"],
                    available_models=[],
                    message="OpenRouter models are not currently available. Please check API key configuration or try a different provider.",
                    suggested_action="Switch to Local Ollama or RunPod provider, or verify OpenRouter API key is configured correctly."
                )
                raise Exception(f"OpenRouter unavailable: {error.message}")
            
            # Create persona list for OpenRouter
            persona_list = []
            
            # Group models by type
            free_models = [m for m in openrouter_models if m.type == "base"]
            premium_models = [m for m in openrouter_models if m.type == "premium"]
            
            # Add free models persona
            if free_models:
                persona_list.append(Persona(
                    name="OpenRouter Free Models",
                    icon="/public/pete.png",
                    type="primary",
                    models=free_models,
                    description="Free OpenRouter models for testing and development"
                ))
            
            # Add premium models persona
            if premium_models:
                persona_list.append(Persona(
                    name="OpenRouter Premium Models",
                    icon="/public/pete.png",
                    type="premium",
                    models=premium_models,
                    description="High-quality OpenRouter models for production use"
                ))
            
            logger.info(f"Serving {len(openrouter_models)} OpenRouter models to UI")
            return persona_list
            
        except Exception as e:
            logger.error(f"Error getting OpenRouter personas: {e}")
            # Return fallback personas instead of raising
            return self._get_fallback_openrouter_personas()
    
    async def _get_actual_ollama_models(self) -> List[str]:
        """Check which models are actually available in Ollama (safe method)"""
        try:
            import requests
            import os
            
            # Get Ollama host from environment
            ollama_host = os.getenv('OLLAMA_HOST', 'localhost:11434')
            
            # Try to get actual model list from Ollama
            try:
                response = requests.get(f"http://{ollama_host}/api/tags", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    models = [model['name'] for model in data.get('models', [])]
                    logger.info(f"✅ Ollama: Successfully fetched {len(models)} available models")
                    return models
                else:
                    logger.warning(f"⚠️ Ollama: API returned status {response.status_code}")
                    return []
            except requests.RequestException as e:
                logger.warning(f"⚠️ Ollama: Could not connect to {ollama_host}: {e}")
                return []
            except Exception as e:
                logger.warning(f"⚠️ Ollama: Error parsing response: {e}")
                return []
                
        except Exception as e:
            logger.warning(f"⚠️ Ollama: Error checking model availability: {e}")
            return []
    
    async def _get_actual_runpod_models(self) -> List[str]:
        """Get actual available RunPod models using the serverless handler's method"""
        try:
            logger.info("🔍 RunPod: Getting available models from serverless handler...")
            
            # Import and use the serverless handler's method
            from src.serverless_handler import serverless_handler
            
            if hasattr(serverless_handler, 'get_available_models'):
                available_models = await serverless_handler.get_available_models()
                if available_models:
                    logger.info(f"✅ RunPod: Serverless handler returned {len(available_models)} models")
                    return available_models
                else:
                    logger.warning("⚠️ RunPod: Serverless handler returned no models, using fallback")
            else:
                logger.warning("⚠️ RunPod: Serverless handler missing get_available_models method, using fallback")
            
            # Fallback to known models if handler fails
            return ["llama3:latest", "mistral:7b-instruct"]
            
        except Exception as e:
            logger.warning(f"⚠️ RunPod: Error getting actual models: {e}")
            # Safe fallback
            return ["llama3:latest", "mistral:7b-instruct"]
    
    async def _get_runpod_personas(self) -> List[Persona]:
        """Get RunPod model personas - using actual available models"""
        try:
            # Get actual available models from RunPod
            available_models = await self._get_actual_runpod_models()
            
            if not available_models:
                logger.warning("⚠️ RunPod: No models available, using fallback")
                return self._get_fallback_runpod_personas()
            
            # Create persona list for RunPod
            persona_list = []
            
            # Group models by type (all RunPod models are typically premium/cloud)
            cloud_models = []
            
            for model_name in available_models:
                model_data = PersonaModel(
                    name=model_name,
                    display_name=f"RunPod: {model_name}",
                    description=f"Cloud-hosted {model_name} model via RunPod serverless",
                    auto_preload=False,
                    type="cloud",
                    base_model=model_name.split(':')[0] if ':' in model_name else model_name
                )
                cloud_models.append(model_data)
            
            # Add cloud models persona
            if cloud_models:
                persona_list.append(Persona(
                    name="RunPod Cloud Models",
                    icon="/public/pete.png",
                    type="premium",
                    models=cloud_models,
                    description="High-performance cloud models hosted on RunPod serverless infrastructure"
                ))
            
            logger.info(f"Serving {len(available_models)} RunPod models to UI: {available_models}")
            return persona_list
            
        except Exception as e:
            logger.error(f"Error getting RunPod personas: {e}")
            # Return fallback personas instead of raising
            return self._get_fallback_runpod_personas()
    
    def _get_fallback_runpod_personas(self) -> List[Persona]:
        """Get fallback RunPod personas when API is unavailable"""
        fallback_models = [
            PersonaModel(
                name="llama3:latest",
                display_name="RunPod: Llama 3 Latest",
                description="Meta's Llama 3 model hosted on RunPod",
                auto_preload=False,
                type="cloud",
                base_model="llama3"
            ),
            PersonaModel(
                name="mistral:7b-instruct",
                display_name="RunPod: Mistral 7B Instruct",
                description="Mistral's 7B instruction-tuned model",
                auto_preload=False,
                type="cloud",
                base_model="mistral"
            )
        ]
        
        return [Persona(
            name="RunPod Models (Fallback)",
            icon="/public/pete.png",
            type="premium",
            models=fallback_models,
            description="RunPod models (using fallback data)"
        )]
    
    async def _fetch_openrouter_models(self) -> List[PersonaModel]:
        """Fetch available models from OpenRouter API"""
        try:
            # Get API key from environment
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                logger.error("OPENROUTER_API_KEY not configured")
                return []
            
            # Set up headers for OpenRouter API
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://peteollama.com",
                "X-Title": "PeteOllama Property Manager"
            }
            
            logger.info("Fetching models from OpenRouter API...")
            
            # Fetch models from OpenRouter API
            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"OpenRouter API returned status {response.status_code}: {response.text}")
                return []
            
            api_data = response.json()
            raw_models = api_data.get("data", [])
            
            if not raw_models:
                logger.error("OpenRouter API returned no models")
                return []
            
            logger.info(f"Successfully fetched {len(raw_models)} models from OpenRouter API")
            
            # Process and filter models suitable for property management
            return self._process_openrouter_api_models(raw_models)
            
        except requests.RequestException as e:
            logger.error(f"Network error fetching OpenRouter models: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching OpenRouter models: {e}")
            return []
    
    def _process_openrouter_api_models(self, raw_models: List[Dict]) -> List[PersonaModel]:
        """Process raw OpenRouter API models into our format"""
        try:
            processed_models = []
            
            # Define preferred models for property management (in order of preference)
            preferred_models = [
                # Free models
                "meta-llama/llama-3.1-8b-instruct:free",
                "microsoft/wizardlm-2-8x22b:nitro",
                "google/gemma-2-9b-it:free",
                
                # Premium models that work well for property management
                "meta-llama/llama-3.1-70b-instruct:nitro",
                "meta-llama/llama-3.1-405b-instruct:nitro",
                "anthropic/claude-3-haiku",
                "anthropic/claude-3-sonnet",
                "openai/gpt-3.5-turbo",
                "openai/gpt-4o-mini",
                "openai/gpt-4o",
                "google/gemini-pro-1.5",
                "mistralai/mistral-7b-instruct:free",
                "mistralai/mixtral-8x7b-instruct:nitro",
            ]
            
            # Create lookup for preferred models
            preferred_set = set(preferred_models)
            
            # First, add preferred models in order
            for preferred_model in preferred_models:
                for raw_model in raw_models:
                    model_id = raw_model.get("id", "")
                    if model_id == preferred_model:
                        processed_model = self._convert_api_model_to_our_format(raw_model)
                        if processed_model:
                            processed_models.append(processed_model)
                        break
            
            # Then add any other suitable models not in preferred list
            for raw_model in raw_models:
                model_id = raw_model.get("id", "")
                
                # Skip if already added as preferred
                if model_id in preferred_set:
                    continue
                
                # Only include models that seem suitable for property management
                if self._is_suitable_for_property_management(raw_model):
                    processed_model = self._convert_api_model_to_our_format(raw_model)
                    if processed_model:
                        processed_models.append(processed_model)
            
            # Limit to reasonable number of models to avoid overwhelming UI
            max_models = 25
            if len(processed_models) > max_models:
                logger.info(f"Limiting OpenRouter models to {max_models} (found {len(processed_models)})")
                processed_models = processed_models[:max_models]
            
            return processed_models
            
        except Exception as e:
            logger.error(f"Error processing OpenRouter API models: {e}")
            return []
    
    def _convert_api_model_to_our_format(self, raw_model: Dict) -> Optional[PersonaModel]:
        """Convert OpenRouter API model to our internal format"""
        try:
            model_id = raw_model.get("id", "")
            model_name = raw_model.get("name", model_id)
            
            # Determine if free or premium
            pricing = raw_model.get("pricing", {})
            prompt_cost = float(pricing.get("prompt", "0"))
            completion_cost = float(pricing.get("completion", "0"))
            is_free = prompt_cost == 0 and completion_cost == 0
            
            # Create display name
            display_name = self._create_display_name(model_name, model_id, is_free)
            
            # Create description
            description = self._create_model_description(raw_model, is_free)
            
            # Determine base model type
            base_model = self._determine_base_model(model_id)
            
            return PersonaModel(
                name=model_id,
                display_name=display_name,
                description=description,
                auto_preload=False,
                type="base" if is_free else "premium",
                base_model=base_model,
                context_length=raw_model.get("context_length", 4096),
                is_free=is_free,
                pricing={
                    "prompt": prompt_cost,
                    "completion": completion_cost
                }
            )
            
        except Exception as e:
            logger.error(f"Error converting model {raw_model.get('id', 'unknown')}: {e}")
            return None
    
    def _is_suitable_for_property_management(self, raw_model: Dict) -> bool:
        """Determine if a model is suitable for property management use"""
        try:
            model_id = raw_model.get("id", "").lower()
            model_name = raw_model.get("name", "").lower()
            description = raw_model.get("description", "").lower()
            
            # Skip models that are explicitly not suitable
            exclude_patterns = [
                "vision", "image", "coding", "code", "math", "reasoning",
                "function", "tool", "nsfw", "uncensored", "roleplay",
                "experimental", "beta", "alpha", "deprecated"
            ]
            
            combined_text = f"{model_id} {model_name} {description}"
            
            for pattern in exclude_patterns:
                if pattern in combined_text:
                    return False
            
            # Prefer general-purpose conversation models
            include_patterns = [
                "instruct", "chat", "turbo", "haiku", "sonnet", "pro",
                "llama", "claude", "gpt", "gemini", "mistral", "wizard"
            ]
            
            for pattern in include_patterns:
                if pattern in combined_text:
                    return True
            
            # Default to suitable if no specific exclusions found
            return True
            
        except Exception:
            return False
    
    def _create_display_name(self, model_name: str, model_id: str, is_free: bool) -> str:
        """Create a user-friendly display name for the model"""
        try:
            # Try to create a nice display name from model name or ID
            name = model_name if model_name != model_id else model_id
            
            # Clean up common patterns
            name = name.replace("-instruct", "")
            name = name.replace("-chat", "")
            name = name.replace("meta-llama/", "")
            name = name.replace("anthropic/", "")
            name = name.replace("openai/", "")
            name = name.replace("google/", "")
            name = name.replace("mistralai/", "")
            name = name.replace("microsoft/", "")
            
            # Capitalize and format nicely
            name = name.replace("-", " ").replace("_", " ")
            name = " ".join(word.capitalize() for word in name.split())
            
            # Add free/premium indicator
            if is_free:
                name += " (Free)"
            else:
                name += " (Premium)"
            
            return name
            
        except Exception:
            return f"{model_id} ({'Free' if is_free else 'Premium'})"
    
    def _create_model_description(self, raw_model: Dict, is_free: bool) -> str:
        """Create a description for the model"""
        try:
            original_desc = raw_model.get("description", "")
            
            # If there's a good original description, use it
            if original_desc and len(original_desc) > 20:
                desc = original_desc[:100]  # Truncate if too long
                if len(original_desc) > 100:
                    desc += "..."
            else:
                # Create a generic description based on model type
                model_id = raw_model.get("id", "")
                
                if "llama" in model_id.lower():
                    desc = "Open-source language model optimized for instruction following"
                elif "claude" in model_id.lower():
                    desc = "Anthropic's AI assistant known for helpful and harmless responses"
                elif "gpt" in model_id.lower():
                    desc = "OpenAI's language model for conversational AI"
                elif "gemini" in model_id.lower():
                    desc = "Google's advanced language model"
                elif "mistral" in model_id.lower():
                    desc = "Efficient language model with strong performance"
                else:
                    desc = "Advanced language model for property management tasks"
            
            # Add context about cost
            if is_free:
                desc += " - Free to use"
            else:
                desc += " - Premium model with high quality responses"
            
            return desc
            
        except Exception:
            return f"OpenRouter model ({'free' if is_free else 'premium'}) for property management"
    
    def _determine_base_model(self, model_id: str) -> str:
        """Determine the base model family"""
        model_lower = model_id.lower()
        
        if "llama" in model_lower:
            return "llama"
        elif "claude" in model_lower:
            return "claude"
        elif "gpt" in model_lower:
            return "gpt"
        elif "gemini" in model_lower:
            return "gemini"
        elif "mistral" in model_lower:
            return "mistral"
        elif "wizard" in model_lower:
            return "wizard"
        else:
            return "unknown"
    
    def _get_fallback_openrouter_personas(self) -> List[Persona]:
        """Get hardcoded fallback personas for OpenRouter"""
        fallback_models = [
            PersonaModel(
                name="meta-llama/llama-3.1-8b-instruct:free",
                display_name="Llama 3.1 8B (Free)",
                description="Fast, reliable model for property management tasks - Free to use",
                auto_preload=False,
                type="base",
                base_model="llama",
                is_free=True
            ),
            PersonaModel(
                name="anthropic/claude-3-haiku",
                display_name="Claude 3 Haiku (Premium)",
                description="Fast and efficient for quick property responses - Premium model with high quality responses",
                auto_preload=False,
                type="premium",
                base_model="claude",
                is_free=False
            )
        ]
        
        free_models = [m for m in fallback_models if m.is_free]
        premium_models = [m for m in fallback_models if not m.is_free]
        
        personas = []
        if free_models:
            personas.append(Persona(
                name="OpenRouter Free Models",
                icon="/public/pete.png",
                type="primary",
                models=free_models,
                description="Free OpenRouter models (fallback)"
            ))
        
        if premium_models:
            personas.append(Persona(
                name="OpenRouter Premium Models",
                icon="/public/pete.png",
                type="premium",
                models=premium_models,
                description="Premium OpenRouter models (fallback)"
            ))
        
        return personas
    
    def _get_fallback_personas(self) -> List[Persona]:
        """Get fallback personas when all else fails"""
        fallback_model = PersonaModel(
            name="llama3:latest",
            display_name="Llama 3 Latest",
            description="General purpose language model",
            auto_preload=False,
            type="base",
            base_model="llama3"
        )
        
        return [Persona(
            name="Default Model",
            icon="/public/pete.png",
            type="primary",
            models=[fallback_model],
            description="Fallback model"
        )]
