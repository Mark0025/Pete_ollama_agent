"""
VAPI Webhook Models
==================

Pydantic models for VAPI webhook system including request/response schemas
and error handling models.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# ========== VAPI Core Models ==========

class VAPIMessage(BaseModel):
    """Individual message in a VAPI conversation"""
    role: str
    content: str

class VAPIChatRequest(BaseModel):
    """VAPI chat completion request model"""
    model: Optional[str] = None
    messages: List[VAPIMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000
    stream: Optional[bool] = False

class VAPIChatResponse(BaseModel):
    """VAPI chat completion response model"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

# ========== Error Handling Models ==========

class ProviderError(BaseModel):
    """Structured error for provider-specific issues"""
    error_type: str = Field(..., description="Type of error (api_key_missing, network_error, etc.)")
    provider: str = Field(..., description="Provider name (ollama, openrouter, runpod)")
    message: str = Field(..., description="Human readable error message")
    details: Optional[str] = Field(None, description="Additional error details")
    timestamp: str = Field(..., description="ISO timestamp when error occurred")

class ModelAvailabilityError(BaseModel):
    """Structured error for model availability issues"""
    error_type: str = "model_not_available"
    provider: str = Field(..., description="Provider name")
    requested_models: List[str] = Field(..., description="Models that were requested but not available")
    available_models: List[str] = Field(default_factory=list, description="Models that are available")
    message: str = Field(..., description="Error message")
    suggested_action: str = Field(..., description="Suggested action to resolve the issue")
    timestamp: str = Field(..., description="ISO timestamp when error occurred")

# ========== Model Management Models ==========

class ModelInfo(BaseModel):
    """Information about a model"""
    name: str
    display_name: str
    description: str
    auto_preload: bool = False
    type: str = "unknown"
    base_model: str = "unknown"
    size: Optional[str] = None
    is_jamie_model: bool = False
    show_in_ui: bool = False

class PersonaModel(BaseModel):
    """Model information within a persona"""
    name: str
    display_name: str
    description: str
    auto_preload: bool
    type: str
    base_model: str
    context_length: Optional[int] = None
    is_free: Optional[bool] = None
    pricing: Optional[Dict[str, float]] = None

class Persona(BaseModel):
    """UI persona containing grouped models"""
    name: str
    icon: str
    type: str  # primary, generic, premium
    models: List[PersonaModel]
    description: str

# ========== Provider Settings Models ==========

class ProviderSettings(BaseModel):
    """Provider configuration settings"""
    default_provider: str = "ollama"
    fallback_provider: str = "runpod"
    fallback_enabled: bool = False

class ProviderStatus(BaseModel):
    """Status of a specific provider"""
    available: bool
    message: str

# ========== Request/Response Models ==========

class TestModelRequest(BaseModel):
    """Request to test a model"""
    model: str
    message: str
    conversation_id: Optional[str] = None

class ModelPreloadRequest(BaseModel):
    """Request to preload a model"""
    model: str

class ConversationStreamRequest(BaseModel):
    """Request for conversation streaming"""
    model: str
    message: str
    conversation_id: str
    conversation_history: List[Dict[str, Any]] = []

# ========== Admin Models ==========

class ModelSettingsUpdate(BaseModel):
    """Update model configuration"""
    model_name: str
    show_in_ui: Optional[bool] = None
    auto_preload: Optional[bool] = None
    display_name: Optional[str] = None
    description: Optional[str] = None

class ProviderTestRequest(BaseModel):
    """Request to test a provider"""
    provider: str

# ========== Benchmark and Analytics Models ==========

class PerformanceMetrics(BaseModel):
    """Performance metrics for a request"""
    total_duration_ms: int
    first_token_latency_ms: Optional[int] = None
    tokens_per_second: Optional[float] = None
    token_count: Optional[int] = None
    response_length_chars: int
    word_count: int

class QualityMetrics(BaseModel):
    """Quality metrics for a response"""
    response_relevance: str
    response_completeness: str
    estimated_quality_score: float
    has_error: Optional[bool] = False
    is_on_topic: Optional[bool] = True

class BenchmarkRecord(BaseModel):
    """Complete benchmark record"""
    request_id: str
    timestamp: str
    model: str
    user_message: str
    ai_response: str
    performance: PerformanceMetrics
    quality_metrics: QualityMetrics
    source: str
    status: str

# ========== System Status Models ==========

class SystemStatus(BaseModel):
    """Overall system status"""
    status: str
    timestamp: float
    uptime: Optional[float] = None
    model_manager: Dict[str, Any]
    provider_settings: Dict[str, Any]
    current_provider: str
    models: Dict[str, Any]
    system: Optional[Dict[str, Any]] = None
    services: Dict[str, Any]

# ========== Utility Functions ==========

def create_error_response(error_type: str, provider: str, message: str, details: str = None) -> ProviderError:
    """Helper to create standardized error responses"""
    return ProviderError(
        error_type=error_type,
        provider=provider,
        message=message,
        details=details,
        timestamp=datetime.now().isoformat()
    )

def create_model_availability_error(provider: str, requested_models: List[str], 
                                   available_models: List[str] = None, 
                                   message: str = None, 
                                   suggested_action: str = None) -> ModelAvailabilityError:
    """Helper to create model availability errors"""
    return ModelAvailabilityError(
        provider=provider,
        requested_models=requested_models,
        available_models=available_models or [],
        message=message or f"Requested models not available on {provider}",
        suggested_action=suggested_action or f"Try a different provider or check {provider} model availability",
        timestamp=datetime.now().isoformat()
    )
