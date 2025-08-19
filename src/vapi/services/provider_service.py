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
        """Get personas for the specified provider"""
        try:
            if provider == 'openrouter':
                return await self._get_openrouter_personas()
            elif provider in ['ollama', 'runpod']:
                return await self._get_ollama_personas()
            else:
                logger.warning(f"Unknown provider {provider}, defaulting to Ollama")
                return await self._get_ollama_personas()
        except Exception as e:
            logger.error(f"Error getting personas for provider {provider}: {e}")
            return self._get_fallback_personas()
    
    async def _get_ollama_personas(self) -> List[Persona]:
        """Get Ollama model personas"""
        # Refresh models from ollama list first
        model_settings.refresh_from_ollama()
        
        # Get only models that are enabled for UI display
        ui_models = model_settings.get_ui_models()
        
        if not ui_models:
            logger.warning("No models enabled for UI display")
            return []
        
        persona_list = []
        jamie_models = []
        generic_models = []
        
        for model_config in ui_models:
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
        
        logger.info(f"Serving {len(ui_models)} Ollama models to UI: {[m.name for m in ui_models]}")
        return persona_list
    
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
