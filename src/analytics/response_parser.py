"""
Response Parser for separating agent responses from system prompts and analysis.
"""
import re
from typing import Dict, List, Tuple, Optional
from loguru import logger
from dataclasses import dataclass

@dataclass
class ParsedResponse:
    """Structured representation of a parsed model response."""
    agent_response: str  # What Jamie would actually say
    system_content: str  # System prompts, instructions, scenarios
    thinking_process: str  # Any reasoning or analysis
    confidence_score: float  # How confident we are in the parsing
    
class ResponseParser:
    """Parse model responses to separate agent content from system content."""
    
    def __init__(self):
        # Patterns to identify system content vs agent responses
        self.system_patterns = [
            r'Please respond as Jamie would in each scenario:',
            r'Remember, your goal as Jamie is to',
            r'Please respond as Jamie would',
            r'\d+\.\s+[A-Z].*?(?=\n\d+\.|\n\n|$)',  # Numbered scenarios
            r'Your goal.*?response\.',
            r'Remember.*?response\.',
        ]
        
        self.instruction_markers = [
            "Please respond as Jamie",
            "Remember, your goal",
            "Your goal as Jamie",
            "In each scenario:",
            "Please respond as",
        ]
    
    def parse_response(self, raw_response: str, user_message: str = "") -> ParsedResponse:
        """
        Parse a raw model response into structured components.
        
        Args:
            raw_response: The full response from the model
            user_message: The original user message for context
            
        Returns:
            ParsedResponse with separated content
        """
        try:
            # Clean up the response
            cleaned_response = raw_response.strip()
            
            # Find where system instructions start
            system_start_pos = None
            agent_response = cleaned_response
            system_content = ""
            
            # Look for instruction markers
            for marker in self.instruction_markers:
                pos = cleaned_response.find(marker)
                if pos != -1:
                    if system_start_pos is None or pos < system_start_pos:
                        system_start_pos = pos
            
            if system_start_pos is not None:
                # Split the response
                agent_response = cleaned_response[:system_start_pos].strip()
                system_content = cleaned_response[system_start_pos:].strip()
            
            # Remove any trailing system content that leaked into agent response
            agent_response = self._clean_agent_response(agent_response)
            
            # Extract thinking process (for now, we'll use system content)
            thinking_process = self._extract_thinking_process(system_content, user_message)
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence(agent_response, system_content)
            
            logger.info(f"Parsed response - Agent: {len(agent_response)} chars, System: {len(system_content)} chars")
            
            return ParsedResponse(
                agent_response=agent_response,
                system_content=system_content,
                thinking_process=thinking_process,
                confidence_score=confidence_score
            )
            
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            # Return original response as agent response if parsing fails
            return ParsedResponse(
                agent_response=raw_response,
                system_content="",
                thinking_process="Parsing failed",
                confidence_score=0.5
            )
    
    def _clean_agent_response(self, response: str) -> str:
        """Clean agent response of any system content that leaked through."""
        # Remove common system instruction patterns
        for pattern in self.system_patterns:
            response = re.sub(pattern, '', response, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove multiple newlines and clean up
        response = re.sub(r'\n\s*\n\s*\n+', '\n\n', response)
        response = response.strip()
        
        return response
    
    def _extract_thinking_process(self, system_content: str, user_message: str) -> str:
        """Extract or generate thinking process analysis."""
        if not system_content:
            return f"Agent responded directly to: '{user_message}'"
        
        # For now, return formatted system content as thinking process
        thinking = f"User Query: {user_message}\n\n"
        thinking += "System Instructions Found:\n"
        thinking += system_content
        
        return thinking
    
    def _calculate_confidence(self, agent_response: str, system_content: str) -> float:
        """Calculate confidence score for the parsing."""
        if not agent_response:
            return 0.0
        
        # High confidence if we found clear separation
        if system_content:
            return 0.9
        
        # Medium confidence if response looks clean
        if len(agent_response) > 20 and not any(marker in agent_response for marker in self.instruction_markers):
            return 0.7
        
        # Lower confidence otherwise
        return 0.5
    
    def analyze_response_quality(self, parsed: ParsedResponse, user_message: str) -> Dict:
        """Analyze the quality of the parsed response."""
        analysis = {
            "parsing_confidence": parsed.confidence_score,
            "agent_response_length": len(parsed.agent_response),
            "contains_system_bleed": any(marker in parsed.agent_response for marker in self.instruction_markers),
            "response_relevance": self._check_relevance(parsed.agent_response, user_message),
            "professional_tone": self._check_professional_tone(parsed.agent_response),
            "action_oriented": self._check_action_oriented(parsed.agent_response)
        }
        
        return analysis
    
    def _check_relevance(self, response: str, user_message: str) -> float:
        """Check if response is relevant to user message."""
        # Simple keyword matching for now
        user_words = set(user_message.lower().split())
        response_words = set(response.lower().split())
        
        common_words = user_words.intersection(response_words)
        if len(user_words) == 0:
            return 0.0
        
        return len(common_words) / len(user_words)
    
    def _check_professional_tone(self, response: str) -> float:
        """Check if response maintains professional tone."""
        professional_indicators = [
            "please", "thank you", "sorry", "i understand", "let me",
            "i'll", "we'll", "contact", "schedule", "assist"
        ]
        
        response_lower = response.lower()
        found_indicators = sum(1 for indicator in professional_indicators if indicator in response_lower)
        
        return min(found_indicators / 3.0, 1.0)  # Cap at 1.0
    
    def _check_action_oriented(self, response: str) -> float:
        """Check if response provides clear next steps or actions."""
        action_indicators = [
            "will", "should", "can", "need to", "please", "contact",
            "schedule", "send", "check", "call", "visit", "reach out"
        ]
        
        response_lower = response.lower()
        found_actions = sum(1 for action in action_indicators if action in response_lower)
        
        return min(found_actions / 2.0, 1.0)  # Cap at 1.0