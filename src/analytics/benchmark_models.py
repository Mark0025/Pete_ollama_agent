"""
Pydantic models for benchmark analytics and data validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import pendulum


class PerformanceMetrics(BaseModel):
    """Performance metrics for model responses"""
    total_duration_ms: int = Field(..., description="Total response time in milliseconds")
    first_token_latency_ms: Optional[int] = Field(None, description="Time to first token in milliseconds")
    tokens_per_second: Optional[float] = Field(None, description="Tokens generated per second")
    token_count: Optional[int] = Field(None, description="Total number of tokens generated")
    response_length_chars: int = Field(..., description="Length of response in characters")
    word_count: int = Field(..., description="Number of words in response")
    environment: Optional[str] = Field(None, description="Environment (Local/Cloud)")
    timeout_used: Optional[int] = Field(None, description="Timeout setting used")


class QualityMetrics(BaseModel):
    """Quality assessment metrics"""
    response_relevance: Optional[str] = Field(None, description="Relevance assessment")
    response_completeness: str = Field(..., description="Completeness (complete/brief/truncated)")
    estimated_quality_score: float = Field(..., ge=1, le=10, description="Quality score 1-10")
    has_error: bool = Field(False, description="Whether response contains errors")
    is_on_topic: bool = Field(True, description="Whether response is on topic")


class BenchmarkRecord(BaseModel):
    """Complete benchmark record for a model interaction"""
    request_id: str = Field(..., description="Unique request identifier")
    timestamp: str = Field(..., description="ISO timestamp of request")
    model: str = Field(..., description="Model name used")
    user_message: str = Field(..., description="Input message from user")
    ai_response: str = Field(..., description="AI model response")
    performance: PerformanceMetrics = Field(..., description="Performance metrics")
    quality_metrics: QualityMetrics = Field(..., description="Quality assessment")
    source: str = Field(default="ui", description="Source of request (ui/admin_test)")
    status: str = Field(default="success", description="Request status")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    @property
    def pendulum_timestamp(self) -> pendulum.DateTime:
        """Convert timestamp to Pendulum datetime"""
        return pendulum.parse(self.timestamp)
    
    @property
    def response_rate_chars_per_second(self) -> float:
        """Calculate characters per second"""
        if self.performance.total_duration_ms == 0:
            return 0
        return (self.performance.response_length_chars * 1000) / self.performance.total_duration_ms
    
    @property
    def is_fast_response(self) -> bool:
        """Determine if response is considered fast (< 3s)"""
        return self.performance.total_duration_ms < 3000
    
    @property
    def is_quality_response(self) -> bool:
        """Determine if response is high quality (> 7/10)"""
        return self.quality_metrics.estimated_quality_score > 7.0


class BenchmarkSummary(BaseModel):
    """Summary statistics for a collection of benchmarks"""
    total_requests: int = Field(..., description="Total number of requests")
    successful_requests: int = Field(..., description="Number of successful requests")
    failed_requests: int = Field(..., description="Number of failed requests")
    avg_response_time_ms: float = Field(..., description="Average response time")
    median_response_time_ms: float = Field(..., description="Median response time")
    min_response_time_ms: int = Field(..., description="Minimum response time")
    max_response_time_ms: int = Field(..., description="Maximum response time")
    avg_quality_score: float = Field(..., description="Average quality score")
    success_rate: float = Field(..., ge=0, le=100, description="Success rate percentage")
    fast_responses_count: int = Field(..., description="Number of fast responses (<3s)")
    quality_responses_count: int = Field(..., description="Number of quality responses (>7/10)")
    models_tested: List[str] = Field(..., description="List of models tested")
    time_range: Dict[str, str] = Field(..., description="Time range of data")
    
    @property
    def fast_response_rate(self) -> float:
        """Percentage of fast responses"""
        if self.total_requests == 0:
            return 0
        return (self.fast_responses_count / self.total_requests) * 100
    
    @property
    def quality_response_rate(self) -> float:
        """Percentage of quality responses"""
        if self.total_requests == 0:
            return 0
        return (self.quality_responses_count / self.total_requests) * 100


class ModelComparison(BaseModel):
    """Comparison metrics between different models"""
    model_name: str = Field(..., description="Name of the model")
    request_count: int = Field(..., description="Number of requests for this model")
    avg_response_time_ms: float = Field(..., description="Average response time")
    avg_quality_score: float = Field(..., description="Average quality score")
    success_rate: float = Field(..., description="Success rate percentage")
    fast_response_rate: float = Field(..., description="Fast response rate percentage")
    recommendation: str = Field(..., description="Recommendation based on performance")
    base_model: str = Field(default="unknown", description="Base model (llama3, qwen, etc.)")
    preload_rate: float = Field(default=0.0, description="Percentage of requests with preloaded model")
    
    @property
    def performance_grade(self) -> str:
        """Overall performance grade A-F"""
        score = (
            (min(self.avg_response_time_ms / 1000, 5) / 5 * 25) +  # Response time (25%)
            (self.avg_quality_score * 10) +  # Quality (25%)
            (self.success_rate * 0.25) +  # Success rate (25%)
            (self.fast_response_rate * 0.25)  # Fast response rate (25%)
        )
        
        if score >= 90: return "A"
        elif score >= 80: return "B"
        elif score >= 70: return "C"
        elif score >= 60: return "D"
        else: return "F"