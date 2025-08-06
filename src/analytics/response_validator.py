"""
Response Validator using Pydantic for continuous model improvement.

This module validates AI responses against Jamie's actual responses and provides
self-correcting feedback for training improvement.
"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, validator, ValidationError
from loguru import logger
import json
from datetime import datetime
from pathlib import Path

from .conversation_similarity import ConversationSimilarityAnalyzer

class JamieResponsePattern(BaseModel):
    """Expected pattern for Jamie's responses based on real conversation data."""
    
    acknowledgment: bool = Field(..., description="Does response acknowledge the issue?")
    action_plan: bool = Field(..., description="Does response provide clear action steps?")
    timeline: bool = Field(..., description="Does response include timeline/expectations?")
    professional_tone: bool = Field(..., description="Is the tone professional but empathetic?")
    contact_info: bool = Field(False, description="Includes contact info when appropriate?")
    
    issue_type: str = Field(..., description="Type of issue being addressed")
    urgency_level: str = Field(..., description="Urgency level (emergency/high/normal)")
    
    response_length: int = Field(..., ge=20, le=500, description="Response length in characters")
    contains_conversation_simulation: bool = Field(False, description="Contains User:/Jamie: patterns")
    contains_system_prompts: bool = Field(False, description="Contains training instructions")
    
    @validator('response_length')
    def validate_length(cls, v):
        if v < 20:
            raise ValueError('Response too short - Jamie provides detailed help')
        if v > 500:
            raise ValueError('Response too long - Jamie is concise but complete')
        return v
    
    @validator('contains_conversation_simulation')
    def no_conversation_simulation(cls, v):
        if v:
            raise ValueError('Response simulates conversation instead of single response')
        return v
    
    @validator('contains_system_prompts') 
    def no_system_bleed(cls, v):
        if v:
            raise ValueError('Response contains training instructions or system prompts')
        return v

class ResponseValidationResult(BaseModel):
    """Result of validating an AI response against Jamie's patterns."""
    
    is_valid: bool
    validation_errors: List[str] = []
    jamie_score: float = Field(..., ge=0.0, le=1.0, description="How Jamie-like the response is")
    
    # What the AI said vs what Jamie would say
    ai_response: str
    jamie_alternative: Optional[str] = None
    similarity_to_jamie: float = 0.0
    
    # Improvement suggestions
    improvement_suggestions: List[str] = []
    corrected_response: Optional[str] = None
    
    # Metadata
    issue_category: str
    urgency_level: str
    validation_timestamp: datetime = Field(default_factory=datetime.now)

class ResponseValidator:
    """Validates AI responses against Jamie's actual response patterns."""
    
    def __init__(self):
        self.similarity_analyzer = ConversationSimilarityAnalyzer()
        self.validation_log_path = Path("logs/response_validation.jsonl")
        self.validation_log_path.parent.mkdir(exist_ok=True)
        
        logger.info("🔍 Response Validator initialized with Jamie's conversation patterns")
    
    def analyze_response_pattern(self, user_message: str, ai_response: str) -> JamieResponsePattern:
        """Analyze if AI response follows Jamie's patterns."""
        
        # Categorize the conversation
        category = self.similarity_analyzer.categorize_conversation(user_message, ai_response)
        
        # Check for conversation simulation patterns
        contains_simulation = any(pattern in ai_response for pattern in [
            "User:", "Jamie:", "\nUser:", "\nJamie:", 
            "user:", "jamie:", "Client:", "Tenant:"
        ])
        
        # Check for system prompt leakage
        contains_system = any(pattern in ai_response.lower() for pattern in [
            "please respond", "remember you're", "as jamie", "property manager",
            "system:", "instruction:", "respond as if", "your role is"
        ])
        
        # Analyze response structure (Jamie's typical patterns)
        acknowledgment = any(pattern in ai_response.lower() for pattern in [
            "sorry to hear", "understand", "i see", "got it", "absolutely"
        ])
        
        action_plan = any(pattern in ai_response.lower() for pattern in [
            "i'll", "i will", "calling", "contact", "schedule", "send", "get someone"
        ])
        
        timeline = any(pattern in ai_response.lower() for pattern in [
            "today", "hour", "within", "tomorrow", "asap", "right now", "this afternoon"
        ])
        
        professional_tone = not any(pattern in ai_response.lower() for pattern in [
            "hey", "yo", "sup", "gonna", "wanna", "lol", "omg"
        ])
        
        contact_info = any(pattern in ai_response for pattern in [
            "405", "call me", "reach me", "contact me", "phone"
        ])
        
        return JamieResponsePattern(
            acknowledgment=acknowledgment,
            action_plan=action_plan,
            timeline=timeline,
            professional_tone=professional_tone,
            contact_info=contact_info,
            issue_type=category["issue_type"],
            urgency_level=category["urgency_level"],
            response_length=len(ai_response),
            contains_conversation_simulation=contains_simulation,
            contains_system_prompts=contains_system
        )
    
    def validate_response(self, user_message: str, ai_response: str) -> ResponseValidationResult:
        """
        Validate AI response against Jamie's patterns.
        
        This is the core "self-correcting validation" - if the AI response doesn't
        match Jamie's patterns, we provide the correct Jamie-style response.
        """
        
        try:
            # Try to validate the response pattern
            pattern = self.analyze_response_pattern(user_message, ai_response)
            
            # Calculate similarity to actual Jamie responses
            similarity_result = self.similarity_analyzer.calculate_similarity(user_message, ai_response)
            
            # Find what Jamie actually said for similar issues
            jamie_alternatives = self.similarity_analyzer.find_similar_issue_responses(
                user_message, pattern.issue_type, limit=3
            )
            
            jamie_alternative = None
            if jamie_alternatives:
                # Use the best matching Jamie response
                jamie_alternative = jamie_alternatives[0].agent_response
            
            # Calculate Jamie-likeness score
            jamie_score = self._calculate_jamie_score(pattern, similarity_result.similarity_score)
            
            # Generate improvement suggestions
            suggestions = self._generate_improvement_suggestions(pattern, jamie_alternatives)
            
            # Generate corrected response if needed
            corrected_response = None
            if jamie_score < 0.7:  # Threshold for "needs improvement"
                corrected_response = self._generate_corrected_response(
                    user_message, ai_response, jamie_alternatives, pattern
                )
            
            result = ResponseValidationResult(
                is_valid=jamie_score >= 0.7,
                validation_errors=[],
                jamie_score=jamie_score,
                ai_response=ai_response,
                jamie_alternative=jamie_alternative,
                similarity_to_jamie=similarity_result.similarity_score,
                improvement_suggestions=suggestions,
                corrected_response=corrected_response,
                issue_category=pattern.issue_type,
                urgency_level=pattern.urgency_level
            )
            
            # Log the validation result
            self._log_validation_result(user_message, result)
            
            return result
            
        except ValidationError as e:
            # This is the "self-correcting" part - validation errors become training data
            validation_errors = [str(error) for error in e.errors()]
            
            logger.warning(f"❌ Response validation failed: {validation_errors}")
            
            # Find what Jamie would have said instead
            similarity_result = self.similarity_analyzer.calculate_similarity(user_message, ai_response)
            category = self.similarity_analyzer.categorize_conversation(user_message, ai_response)
            
            jamie_alternatives = self.similarity_analyzer.find_similar_issue_responses(
                user_message, category["issue_type"], limit=3
            )
            
            # Generate the correct response based on Jamie's patterns
            corrected_response = self._generate_corrected_response(
                user_message, ai_response, jamie_alternatives, None
            )
            
            result = ResponseValidationResult(
                is_valid=False,
                validation_errors=validation_errors,
                jamie_score=0.2,  # Low score due to validation failure
                ai_response=ai_response,
                jamie_alternative=jamie_alternatives[0].agent_response if jamie_alternatives else None,
                similarity_to_jamie=similarity_result.similarity_score,
                improvement_suggestions=self._validation_errors_to_suggestions(validation_errors),
                corrected_response=corrected_response,
                issue_category=category["issue_type"],
                urgency_level=category["urgency_level"]
            )
            
            # Log the validation failure and correction
            self._log_validation_result(user_message, result)
            
            return result
    
    def _calculate_jamie_score(self, pattern: JamieResponsePattern, similarity_score: float) -> float:
        """Calculate how Jamie-like a response is."""
        
        # Base score from similarity to actual Jamie responses
        base_score = similarity_score
        
        # Bonus points for following Jamie's patterns
        pattern_score = 0
        if pattern.acknowledgment:
            pattern_score += 0.15
        if pattern.action_plan:
            pattern_score += 0.20
        if pattern.timeline:
            pattern_score += 0.15
        if pattern.professional_tone:
            pattern_score += 0.10
        
        # Penalty for bad patterns
        if pattern.contains_conversation_simulation:
            pattern_score -= 0.30
        if pattern.contains_system_prompts:
            pattern_score -= 0.25
        
        # Combine scores
        final_score = (base_score * 0.6) + (pattern_score * 0.4)
        
        return max(0.0, min(1.0, final_score))
    
    def _generate_improvement_suggestions(self, pattern: JamieResponsePattern, jamie_examples: List) -> List[str]:
        """Generate specific improvement suggestions."""
        suggestions = []
        
        if pattern.contains_conversation_simulation:
            suggestions.append("❌ Remove conversation simulation (User:/Jamie: patterns) - respond as Jamie directly")
        
        if pattern.contains_system_prompts:
            suggestions.append("❌ Remove system prompt leakage - no training instructions in response")
        
        if not pattern.acknowledgment:
            suggestions.append("✅ Add acknowledgment of the issue (e.g., 'Sorry to hear about that')")
        
        if not pattern.action_plan:
            suggestions.append("✅ Include clear action steps (e.g., 'I'll call our contractor')")
        
        if not pattern.timeline:
            suggestions.append("✅ Provide timeline expectations (e.g., 'within the hour', 'today')")
        
        if pattern.response_length < 50:
            suggestions.append("✅ Provide more detail - Jamie gives complete, helpful responses")
        
        if jamie_examples:
            suggestions.append(f"📝 Reference Jamie's actual response style from {len(jamie_examples)} similar cases")
        
        return suggestions
    
    def _validation_errors_to_suggestions(self, errors: List[str]) -> List[str]:
        """Convert Pydantic validation errors to improvement suggestions."""
        suggestions = []
        
        for error in errors:
            if "conversation simulation" in error:
                suggestions.append("❌ Stop simulating conversations - respond as Jamie only")
            elif "system prompts" in error:
                suggestions.append("❌ Remove training instructions from response")
            elif "too short" in error:
                suggestions.append("✅ Provide more detailed, helpful response")
            elif "too long" in error:
                suggestions.append("✅ Be more concise while staying complete")
            else:
                suggestions.append(f"⚠️ {error}")
        
        return suggestions
    
    def _generate_corrected_response(self, user_message: str, ai_response: str, 
                                   jamie_examples: List, pattern: Optional[JamieResponsePattern]) -> str:
        """Generate a corrected response based on Jamie's actual patterns."""
        
        if not jamie_examples:
            return "I understand your concern. Let me look into this and get back to you right away with a solution."
        
        # Use the best Jamie example as a template
        best_jamie_response = jamie_examples[0].agent_response
        
        # Categorize the issue for context
        category = self.similarity_analyzer.categorize_conversation(user_message, ai_response)
        
        # Generate corrected response based on issue type
        if category["issue_type"] == "hvac":
            return f"I understand this is urgent, especially with the weather. I'm calling our HVAC contractor right now to get someone out there today. They should contact you within the next hour to schedule an appointment."
        
        elif category["issue_type"] == "plumbing":
            return f"Sorry to hear about the plumbing issue. I'm sending a plumber out today to fix this. Please place towels around the area to prevent water damage until they arrive."
        
        elif category["issue_type"] == "payment":
            return f"I can help you with that. Let me check your account and get this resolved. I'll call you back within 30 minutes with the details."
        
        else:
            # Use Jamie's actual response as template
            return best_jamie_response
    
    def _log_validation_result(self, user_message: str, result: ResponseValidationResult):
        """Log validation results for training improvement."""
        
        log_entry = {
            "timestamp": result.validation_timestamp.isoformat(),
            "user_message": user_message,
            "ai_response": result.ai_response,
            "is_valid": result.is_valid,
            "jamie_score": result.jamie_score,
            "validation_errors": result.validation_errors,
            "improvement_suggestions": result.improvement_suggestions,
            "jamie_alternative": result.jamie_alternative,
            "corrected_response": result.corrected_response,
            "issue_category": result.issue_category,
            "urgency_level": result.urgency_level
        }
        
        try:
            with open(self.validation_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Failed to log validation result: {e}")
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get statistics about validation results."""
        
        if not self.validation_log_path.exists():
            return {"total_validations": 0}
        
        stats = {
            "total_validations": 0,
            "valid_responses": 0,
            "invalid_responses": 0,
            "average_jamie_score": 0.0,
            "common_errors": [],
            "improvement_trends": []
        }
        
        try:
            jamie_scores = []
            errors = []
            
            with open(self.validation_log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        stats["total_validations"] += 1
                        
                        if entry["is_valid"]:
                            stats["valid_responses"] += 1
                        else:
                            stats["invalid_responses"] += 1
                        
                        jamie_scores.append(entry["jamie_score"])
                        errors.extend(entry["validation_errors"])
                        
                    except json.JSONDecodeError:
                        continue
            
            if jamie_scores:
                stats["average_jamie_score"] = sum(jamie_scores) / len(jamie_scores)
            
            # Count common errors
            from collections import Counter
            error_counts = Counter(errors)
            stats["common_errors"] = error_counts.most_common(5)
            
        except Exception as e:
            logger.error(f"Error calculating validation stats: {e}")
        
        return stats

# Global validator instance
response_validator = ResponseValidator()