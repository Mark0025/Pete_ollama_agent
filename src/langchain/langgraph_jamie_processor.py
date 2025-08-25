#!/usr/bin/env python3
"""
LangGraph Jamie Conversation Processor
=====================================

Advanced LangGraph-based system for processing Jamie conversations into 
high-quality test cases for AI training. This system uses a multi-node
graph approach to analyze conversations, identify speakers, extract responses,
and generate structured test cases.

Features:
- Multi-stage conversation analysis using LangGraph nodes
- Advanced speaker identification with confidence scoring
- Context-aware response extraction and quality assessment
- Automated test case generation with validation
- Integration with WhatsWorking MCP for real-time visualization
"""

import os
import sys
import json
import sqlite3
import asyncio
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
import re

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# For now, we'll implement without LangGraph until dependencies are resolved
# from langgraph.graph import StateGraph, START, END
# from langgraph.prebuilt import ToolNode
# from langgraph.checkpoint.memory import MemorySaver
# from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# Local imports
from database.pete_db_manager import PeteDBManager
from utils.logger import logger


@dataclass
class ConversationSegment:
    """Represents a segment of conversation with metadata"""
    speaker: str  # "jamie" or "client"
    text: str
    confidence: float  # 0.0 - 1.0
    timestamp_relative: int  # Position in conversation
    context: Dict[str, Any]


@dataclass
class TestCase:
    """Structured test case for AI training"""
    input_scenario: str  # What the client said/situation
    expected_response: str  # Jamie's actual response
    conversation_context: Dict[str, Any]
    quality_metrics: Dict[str, float]
    issue_category: str  # maintenance, payment, emergency, etc.
    client_info: Dict[str, str]
    

class ConversationState(TypedDict):
    """State for the LangGraph conversation processing workflow"""
    conversation_id: str
    raw_transcription: str
    client_info: Dict[str, str]
    segments: List[ConversationSegment]
    jamie_responses: List[str]
    test_cases: List[TestCase]
    quality_score: float
    processing_errors: List[str]
    metadata: Dict[str, Any]


class LangGraphJamieProcessor:
    """
    Advanced LangGraph-based processor for Jamie conversations
    
    This system uses a workflow graph to process conversations through
    multiple specialized nodes, each handling a specific aspect of the
    analysis and test case generation process.
    """
    
    def __init__(self):
        self.db_manager = PeteDBManager()
        self.graph = self._build_processing_graph()
        self.processed_conversations = []
        self.generated_test_cases = []
        
        # Statistics tracking
        self.stats = {
            "total_processed": 0,
            "quality_conversations": 0,
            "test_cases_generated": 0,
            "jamie_responses_extracted": 0,
            "processing_errors": 0
        }
    
    def _build_processing_graph(self):
        """Build the processing workflow (simplified version without LangGraph)"""
        # For now, return None - we'll implement direct sequential processing
        return None
    
    async def _load_conversation_node(self, state: ConversationState) -> ConversationState:
        """Load and preprocess conversation data"""
        try:
            logger.info(f"📥 Loading conversation: {state['conversation_id']}")
            
            # Extract client info from transcription or data field
            client_info = self._extract_enhanced_client_info(
                state['raw_transcription'], 
                state.get('metadata', {})
            )
            
            state["client_info"] = client_info
            state["segments"] = []
            state["processing_errors"] = []
            
            logger.info(f"✅ Loaded conversation for client: {client_info.get('name', 'Unknown')}")
            
        except Exception as e:
            logger.error(f"❌ Error loading conversation: {e}")
            state["processing_errors"].append(f"Load error: {str(e)}")
            
        return state
    
    async def _analyze_quality_node(self, state: ConversationState) -> ConversationState:
        """Analyze conversation quality and determine if suitable for processing"""
        try:
            transcription = state["raw_transcription"]
            
            # Multi-factor quality analysis
            quality_metrics = {
                "length_score": self._score_conversation_length(transcription),
                "dialogue_score": self._score_dialogue_quality(transcription),
                "jamie_presence_score": self._score_jamie_presence(transcription),
                "coherence_score": self._score_conversation_coherence(transcription),
                "property_relevance_score": self._score_property_relevance(transcription)
            }
            
            # Weighted overall quality score
            weights = {
                "length_score": 0.15,
                "dialogue_score": 0.25,
                "jamie_presence_score": 0.30,
                "coherence_score": 0.20,
                "property_relevance_score": 0.10
            }
            
            quality_score = sum(
                quality_metrics[metric] * weights[metric] 
                for metric in quality_metrics
            )
            
            state["quality_score"] = quality_score
            state["metadata"]["quality_metrics"] = quality_metrics
            
            logger.info(f"📊 Quality analysis complete: {quality_score:.3f}")
            
        except Exception as e:
            logger.error(f"❌ Error analyzing quality: {e}")
            state["processing_errors"].append(f"Quality analysis error: {str(e)}")
            state["quality_score"] = 0.0
            
        return state
    
    async def _identify_speakers_node(self, state: ConversationState) -> ConversationState:
        """Advanced speaker identification with confidence scoring"""
        try:
            transcription = state["raw_transcription"]
            
            # Enhanced speaker identification
            segments = self._identify_speakers_advanced(transcription)
            
            state["segments"] = segments
            
            jamie_segments = [s for s in segments if s.speaker == "jamie"]
            client_segments = [s for s in segments if s.speaker == "client"]
            
            logger.info(f"🗣️ Identified {len(jamie_segments)} Jamie segments, {len(client_segments)} client segments")
            
        except Exception as e:
            logger.error(f"❌ Error identifying speakers: {e}")
            state["processing_errors"].append(f"Speaker identification error: {str(e)}")
            state["segments"] = []
            
        return state
    
    async def _extract_jamie_responses_node(self, state: ConversationState) -> ConversationState:
        """Extract and analyze Jamie's responses"""
        try:
            segments = state["segments"]
            jamie_segments = [s for s in segments if s.speaker == "jamie" and s.confidence > 0.4]
            
            # Process Jamie responses
            jamie_responses = []
            for segment in jamie_segments:
                # Clean and enhance response
                cleaned_response = self._clean_response_text(segment.text)
                if self._is_quality_response(cleaned_response):
                    jamie_responses.append(cleaned_response)
            
            state["jamie_responses"] = jamie_responses
            self.stats["jamie_responses_extracted"] += len(jamie_responses)
            
            logger.info(f"📝 Extracted {len(jamie_responses)} quality Jamie responses")
            
        except Exception as e:
            logger.error(f"❌ Error extracting Jamie responses: {e}")
            state["processing_errors"].append(f"Response extraction error: {str(e)}")
            state["jamie_responses"] = []
            
        return state
    
    async def _generate_test_cases_node(self, state: ConversationState) -> ConversationState:
        """Generate structured test cases from conversation"""
        try:
            segments = state["segments"]
            jamie_responses = state["jamie_responses"]
            
            test_cases = []
            
            # Create test cases by pairing client inputs with Jamie responses
            for i, segment in enumerate(segments):
                if segment.speaker == "client":
                    # Find corresponding Jamie response
                    jamie_response = self._find_corresponding_jamie_response(
                        segment, segments[i:], jamie_responses
                    )
                    
                    if jamie_response:
                        test_case = TestCase(
                            input_scenario=self._format_input_scenario(segment.text),
                            expected_response=jamie_response,
                            conversation_context=self._build_context(state, i),
                            quality_metrics=self._calculate_test_case_quality(
                                segment.text, jamie_response
                            ),
                            issue_category=self._categorize_issue(segment.text),
                            client_info=state["client_info"]
                        )
                        test_cases.append(test_case)
            
            state["test_cases"] = test_cases
            self.stats["test_cases_generated"] += len(test_cases)
            
            logger.info(f"🧪 Generated {len(test_cases)} test cases")
            
        except Exception as e:
            logger.error(f"❌ Error generating test cases: {e}")
            state["processing_errors"].append(f"Test case generation error: {str(e)}")
            state["test_cases"] = []
            
        return state
    
    async def _validate_test_cases_node(self, state: ConversationState) -> ConversationState:
        """Validate and filter test cases for quality"""
        try:
            test_cases = state["test_cases"]
            validated_cases = []
            
            for test_case in test_cases:
                if self._validate_test_case(test_case):
                    validated_cases.append(test_case)
                    
            state["test_cases"] = validated_cases
            
            logger.info(f"✅ Validated {len(validated_cases)}/{len(test_cases)} test cases")
            
        except Exception as e:
            logger.error(f"❌ Error validating test cases: {e}")
            state["processing_errors"].append(f"Validation error: {str(e)}")
            
        return state
    
    async def _save_results_node(self, state: ConversationState) -> ConversationState:
        """Save processed results and update statistics"""
        try:
            # Save to processed conversations
            self.processed_conversations.append({
                "conversation_id": state["conversation_id"],
                "quality_score": state["quality_score"],
                "jamie_responses": state["jamie_responses"],
                "test_cases": state["test_cases"],
                "client_info": state["client_info"],
                "processing_errors": state["processing_errors"]
            })
            
            # Update statistics
            self.stats["total_processed"] += 1
            if state["quality_score"] > 0.7:
                self.stats["quality_conversations"] += 1
            if state["processing_errors"]:
                self.stats["processing_errors"] += 1
            
            logger.info(f"💾 Saved results for conversation {state['conversation_id']}")
            
        except Exception as e:
            logger.error(f"❌ Error saving results: {e}")
            
        return state
    
    def _should_continue_processing(self, state: ConversationState) -> str:
        """Determine if conversation quality is sufficient for continued processing"""
        quality_threshold = 0.5
        return "continue" if state["quality_score"] >= quality_threshold else "skip"
    
    def _extract_enhanced_client_info(self, transcription: str, metadata: Dict) -> Dict[str, str]:
        """Enhanced client information extraction"""
        client_info = {"name": "Unknown", "phone": "Unknown", "key": "unknown"}
        
        # Try to extract from transcription
        name_patterns = [
            r"this is (\w+)",
            r"my name is (\w+)",
            r"i'm (\w+)",
            r"(\w+) calling",
            r"hi jamie,?\s*(?:this is\s*)?(\w+)",
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, transcription.lower())
            if match:
                client_info["name"] = match.group(1).title()
                break
        
        # Extract phone patterns
        phone_patterns = [
            r"(\d{3}[-.]?\d{3}[-.]?\d{4})",
            r"\((\d{3})\)\s*(\d{3})\s*(\d{4})"
        ]
        
        for pattern in phone_patterns:
            match = re.search(pattern, transcription)
            if match:
                client_info["phone"] = match.group(0)
                break
        
        client_info["key"] = f"{client_info['name']}_{client_info['phone']}"
        return client_info
    
    def _score_conversation_length(self, transcription: str) -> float:
        """Score based on conversation length (optimal range)"""
        length = len(transcription)
        if 500 <= length <= 3000:
            return 1.0
        elif 200 <= length < 500:
            return 0.7
        elif length > 3000:
            return max(0.5, 1.0 - (length - 3000) / 5000)
        else:
            return 0.2
    
    def _score_dialogue_quality(self, transcription: str) -> float:
        """Score based on dialogue indicators and turn-taking"""
        dialogue_indicators = [
            "jamie", "hi", "hello", "thank you", "i'll", "let me",
            "can you", "what", "when", "how", "where", "?"
        ]
        
        score = 0.0
        text_lower = transcription.lower()
        
        for indicator in dialogue_indicators:
            if indicator in text_lower:
                score += 0.1
        
        # Check for turn-taking patterns
        turns = transcription.count(". ") + transcription.count("? ") + transcription.count("! ")
        turn_score = min(1.0, turns / 10.0)
        
        return min(1.0, score + turn_score)
    
    def _score_jamie_presence(self, transcription: str) -> float:
        """Score based on Jamie's presence and involvement"""
        jamie_indicators = [
            "this is jamie", "jamie here", "jamie speaking",
            "i'll", "let me", "i can", "i will", "i'll schedule",
            "i'll call", "i'll send", "i'll check"
        ]
        
        text_lower = transcription.lower()
        jamie_score = sum(1 for indicator in jamie_indicators if indicator in text_lower)
        
        # Normalize score
        return min(1.0, jamie_score / 5.0)
    
    def _score_conversation_coherence(self, transcription: str) -> float:
        """Score based on conversation coherence and structure"""
        sentences = [s.strip() for s in transcription.split('.') if len(s.strip()) > 5]
        
        if len(sentences) < 3:
            return 0.2
        
        # Check for greeting/closing patterns
        has_greeting = any(word in transcription.lower() for word in ["hello", "hi", "hey"])
        has_closing = any(word in transcription.lower() for word in ["thank", "bye", "talk"])
        
        coherence_score = 0.5  # Base score
        if has_greeting:
            coherence_score += 0.25
        if has_closing:
            coherence_score += 0.25
        
        return coherence_score
    
    def _score_property_relevance(self, transcription: str) -> float:
        """Score based on property management relevance"""
        property_keywords = [
            "rent", "lease", "maintenance", "repair", "ac", "air conditioning",
            "plumbing", "apartment", "unit", "property", "tenant", "landlord",
            "payment", "emergency", "broken", "fix", "schedule", "contractor"
        ]
        
        text_lower = transcription.lower()
        relevance_score = sum(1 for keyword in property_keywords if keyword in text_lower)
        
        return min(1.0, relevance_score / 8.0)
    
    def _identify_speakers_advanced(self, transcription: str) -> List[ConversationSegment]:
        """Advanced speaker identification with confidence scoring"""
        segments = []
        sentences = [s.strip() for s in transcription.split('.') if len(s.strip()) > 10]
        
        for i, sentence in enumerate(sentences):
            speaker, confidence = self._classify_speaker_with_confidence(sentence, i, sentences)
            
            segment = ConversationSegment(
                speaker=speaker,
                text=sentence,
                confidence=confidence,
                timestamp_relative=i,
                context={"total_sentences": len(sentences)}
            )
            segments.append(segment)
        
        return segments
    
    def _classify_speaker_with_confidence(self, sentence: str, position: int, all_sentences: List[str]) -> tuple[str, float]:
        """Classify speaker with confidence score"""
        sentence_lower = sentence.lower()
        
        # Strong Jamie indicators (Jamie is often the maintenance person)
        strong_jamie_indicators = [
            "this is jamie", "jamie here", "jamie speaking",
            "i'll schedule", "i'll call", "i'll send", "i'll check",
            "i was able to fix", "i figured", "i could do", "i told him"
        ]
        
        # Moderate Jamie indicators 
        moderate_jamie_indicators = [
            "i'll", "let me", "i can", "i will", "okay", "yeah", "alright",
            "perfect", "sounds good", "that sounds great", "awesome", "thanks"
        ]
        
        # Strong client/caller indicators (often Kelly or other staff)
        strong_client_indicators = [
            "hey jamie", "hi jamie", "calling about", "this is kelly",
            "how are you", "i just went to", "did she send", "what was wrong"
        ]
        
        # Moderate client indicators
        moderate_client_indicators = [
            "so", "well", "and then", "what about", "did you", "can you",
            "we need", "you can", "if you", "do you want"
        ]
        
        # Calculate scores
        jamie_score = 0.0
        client_score = 0.0
        
        for indicator in strong_jamie_indicators:
            if indicator in sentence_lower:
                jamie_score += 0.9
        
        for indicator in moderate_jamie_indicators:
            if indicator in sentence_lower:
                jamie_score += 0.2
        
        for indicator in strong_client_indicators:
            if indicator in sentence_lower:
                client_score += 0.9
        
        for indicator in moderate_client_indicators:
            if indicator in sentence_lower:
                client_score += 0.2
        
        # Context-based adjustments
        if position == 0 and "this is jamie" in sentence_lower:
            jamie_score += 0.3
        
        # Work-related responses tend to be Jamie
        work_keywords = ["repair", "fix", "replace", "door", "shower", "drywall", "materials"]
        if any(keyword in sentence_lower for keyword in work_keywords):
            if any(pronoun in sentence_lower for pronoun in ["i'll", "i can", "i could"]):
                jamie_score += 0.4
        
        # Determine speaker and confidence
        if jamie_score > client_score:
            return "jamie", min(1.0, jamie_score)
        elif client_score > jamie_score:
            return "client", min(1.0, client_score)
        else:
            # Default heuristic - alternate speakers
            if position % 2 == 0:
                return "jamie" if "jamie" in all_sentences[0].lower() else "client", 0.4
            else:
                return "client" if "jamie" in all_sentences[0].lower() else "jamie", 0.4
    
    def _clean_response_text(self, text: str) -> str:
        """Clean and standardize response text"""
        # Remove excessive whitespace
        cleaned = " ".join(text.split())
        
        # Remove common transcription artifacts
        artifacts = ["um", "uh", "you know", "like"]
        for artifact in artifacts:
            cleaned = re.sub(f"\\b{artifact}\\b", "", cleaned, flags=re.IGNORECASE)
        
        # Fix common punctuation issues
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Multiple spaces
        cleaned = re.sub(r'([.!?])\s*([a-zA-Z])', r'\1 \2', cleaned)  # Sentence spacing
        
        return cleaned.strip()
    
    def _is_quality_response(self, response: str) -> bool:
        """Determine if a response is of sufficient quality"""
        if len(response) < 5 or len(response) > 500:
            return False
        
        # Must contain actionable content or professional responses
        action_indicators = [
            "i'll", "let me", "i can", "i will", "schedule", "call", "send", "check",
            "okay", "yeah", "that sounds", "perfect", "good", "alright", "yes",
            "we'll", "i need", "let's", "sure", "absolutely", "definitely"
        ]
        
        response_lower = response.lower()
        has_action = any(indicator in response_lower for indicator in action_indicators)
        
        # Must be conversational (not system artifacts)
        system_artifacts = [
            "please respond as", "system:", "user:", "assistant:"
        ]
        
        has_artifacts = any(artifact in response_lower for artifact in system_artifacts)
        
        # Also accept responses that seem conversational
        is_conversational = any(word in response_lower for word in [
            "how", "what", "when", "where", "why", "thanks", "thank you", "bye"
        ])
        
        return (has_action or is_conversational) and not has_artifacts
    
    def _find_corresponding_jamie_response(self, client_segment: ConversationSegment, 
                                         following_segments: List[ConversationSegment],
                                         jamie_responses: List[str]) -> Optional[str]:
        """Find Jamie's response to a client input"""
        # Look for Jamie response in next few segments
        for segment in following_segments[:3]:  # Check next 3 segments
            if segment.speaker == "jamie" and segment.confidence > 0.4:
                cleaned_response = self._clean_response_text(segment.text)
                if cleaned_response in jamie_responses:
                    return cleaned_response
        
        return None
    
    def _format_input_scenario(self, client_text: str) -> str:
        """Format client input into a clean scenario description"""
        cleaned = self._clean_response_text(client_text)
        
        # Add context prefixes if needed
        if not cleaned.lower().startswith(("hi", "hello", "hey")):
            cleaned = f"Client says: {cleaned}"
        
        return cleaned
    
    def _build_context(self, state: ConversationState, position: int) -> Dict[str, Any]:
        """Build contextual information for test case"""
        return {
            "client_name": state["client_info"]["name"],
            "conversation_position": position,
            "total_segments": len(state["segments"]),
            "conversation_quality": state["quality_score"],
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_test_case_quality(self, input_text: str, response_text: str) -> Dict[str, float]:
        """Calculate quality metrics for a test case"""
        return {
            "input_clarity": self._score_input_clarity(input_text),
            "response_quality": self._score_response_quality(response_text),
            "relevance": self._score_relevance(input_text, response_text),
            "completeness": self._score_completeness(response_text)
        }
    
    def _categorize_issue(self, input_text: str) -> str:
        """Categorize the type of issue from client input"""
        text_lower = input_text.lower()
        
        categories = {
            "maintenance": ["repair", "fix", "broken", "ac", "air conditioning", "plumbing", "leak"],
            "payment": ["rent", "payment", "late", "check", "money", "bill"],
            "emergency": ["emergency", "urgent", "asap", "immediately", "help"],
            "move": ["move", "transfer", "address", "lease", "keys", "lockbox"],
            "general": []
        }
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return "general"
    
    def _validate_test_case(self, test_case: TestCase) -> bool:
        """Validate test case quality and completeness"""
        # Check minimum length requirements (more lenient)
        if len(test_case.input_scenario) < 5 or len(test_case.expected_response) < 3:
            return False
        
        # Check quality metrics (more lenient)
        quality_avg = sum(test_case.quality_metrics.values()) / len(test_case.quality_metrics)
        if quality_avg < 0.3:
            return False
        
        # Allow all categories including general
        return True
    
    def _score_input_clarity(self, input_text: str) -> float:
        """Score input clarity"""
        # Simple heuristic based on length and question structure
        if 10 <= len(input_text) <= 200:
            return 0.8
        return 0.5
    
    def _score_response_quality(self, response_text: str) -> float:
        """Score response quality"""
        # Check for action words and professional tone
        action_words = ["i'll", "let me", "i can", "schedule", "call"]
        score = sum(0.2 for word in action_words if word in response_text.lower())
        return min(1.0, score)
    
    def _score_relevance(self, input_text: str, response_text: str) -> float:
        """Score relevance between input and response"""
        # Simple keyword overlap scoring
        input_words = set(input_text.lower().split())
        response_words = set(response_text.lower().split())
        
        common_words = input_words & response_words
        relevance = len(common_words) / max(len(input_words), 1)
        
        return min(1.0, relevance * 2)  # Amplify the score
    
    def _score_completeness(self, response_text: str) -> float:
        """Score response completeness"""
        # Check for complete sentences and action plans
        if len(response_text) > 50 and ("." in response_text or "!" in response_text):
            return 0.8
        return 0.4
    
    async def process_conversation(self, conversation_id: str, raw_transcription: str, 
                                 metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Process a single conversation through the sequential workflow"""
        state = {
            "conversation_id": conversation_id,
            "raw_transcription": raw_transcription,
            "client_info": {},
            "segments": [],
            "jamie_responses": [],
            "test_cases": [],
            "quality_score": 0.0,
            "processing_errors": [],
            "metadata": metadata or {}
        }
        
        # Process through each node sequentially
        try:
            state = await self._load_conversation_node(state)
            state = await self._analyze_quality_node(state)
            
            # Check if we should continue processing
            if self._should_continue_processing(state) == "continue":
                state = await self._identify_speakers_node(state)
                state = await self._extract_jamie_responses_node(state)
                state = await self._generate_test_cases_node(state)
                state = await self._validate_test_cases_node(state)
            
            state = await self._save_results_node(state)
            
        except Exception as e:
            logger.error(f"Error processing conversation: {e}")
            state["processing_errors"].append(f"Processing error: {str(e)}")
        
        return {
            "conversation_id": state["conversation_id"],
            "quality_score": state["quality_score"],
            "test_cases_generated": len(state["test_cases"]),
            "jamie_responses_extracted": len(state["jamie_responses"]),
            "processing_errors": state["processing_errors"],
            "test_cases": state["test_cases"]
        }
    
    async def process_batch_conversations(self, limit: int = 100) -> Dict[str, Any]:
        """Process a batch of conversations from the database"""
        logger.info(f"🚀 Starting batch processing of {limit} conversations")
        
        try:
            # Load conversations from database
            if not self.db_manager.is_connected():
                logger.error("❌ Database not connected")
                return {"error": "Database not connected"}
            
            connection = sqlite3.connect(self.db_manager.db_path)
            query = """
            SELECT CreationDate, Data, Transcription
            FROM communication_logs 
            WHERE Transcription IS NOT NULL 
            AND LENGTH(Transcription) > 200
            AND Transcription LIKE '%jamie%'
            ORDER BY CreationDate DESC
            LIMIT ?
            """
            
            cursor = connection.cursor()
            cursor.execute(query, (limit,))
            conversations = cursor.fetchall()
            connection.close()
            
            logger.info(f"📞 Loaded {len(conversations)} conversations from database")
            
            # Process each conversation
            results = []
            for i, (date, data, transcription) in enumerate(conversations):
                conversation_id = f"conv_{i}_{date.replace(' ', '_').replace(':', '-')}"
                
                try:
                    result = await self.process_conversation(
                        conversation_id=conversation_id,
                        raw_transcription=transcription,
                        metadata={"date": date, "data": data}
                    )
                    results.append(result)
                    
                    if (i + 1) % 10 == 0:
                        logger.info(f"📊 Processed {i + 1}/{len(conversations)} conversations")
                        
                except Exception as e:
                    logger.error(f"❌ Error processing conversation {conversation_id}: {e}")
                    continue
            
            # Compile final statistics
            total_test_cases = sum(r.get("test_cases_generated", 0) for r in results)
            total_jamie_responses = sum(r.get("jamie_responses_extracted", 0) for r in results)
            
            summary = {
                "conversations_processed": len(results),
                "total_test_cases_generated": total_test_cases,
                "total_jamie_responses_extracted": total_jamie_responses,
                "average_quality_score": sum(r.get("quality_score", 0) for r in results) / len(results) if results else 0,
                "processing_statistics": self.stats,
                "results": results
            }
            
            logger.info(f"🎉 Batch processing complete!")
            logger.info(f"📊 Generated {total_test_cases} test cases from {total_jamie_responses} Jamie responses")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Batch processing error: {e}")
            return {"error": str(e)}
    
    def export_test_cases(self, output_path: str = "generated_test_cases.json") -> bool:
        """Export generated test cases to JSON file"""
        try:
            # Collect all test cases from processed conversations
            all_test_cases = []
            
            for conversation in self.processed_conversations:
                for test_case in conversation["test_cases"]:
                    # Convert TestCase dataclass to dict for JSON serialization
                    test_case_dict = {
                        "input_scenario": test_case.input_scenario,
                        "expected_response": test_case.expected_response,
                        "conversation_context": test_case.conversation_context,
                        "quality_metrics": test_case.quality_metrics,
                        "issue_category": test_case.issue_category,
                        "client_info": test_case.client_info,
                        "source_conversation": conversation["conversation_id"]
                    }
                    all_test_cases.append(test_case_dict)
            
            # Create export data
            export_data = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "total_test_cases": len(all_test_cases),
                    "processing_statistics": self.stats,
                    "quality_summary": self._generate_quality_summary(all_test_cases)
                },
                "test_cases": all_test_cases
            }
            
            # Write to file
            output_file = Path(output_path)
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"📄 Exported {len(all_test_cases)} test cases to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error exporting test cases: {e}")
            return False
    
    def _generate_quality_summary(self, test_cases: List[Dict]) -> Dict[str, Any]:
        """Generate quality summary of test cases"""
        if not test_cases:
            return {}
        
        # Category distribution
        categories = {}
        quality_scores = []
        
        for tc in test_cases:
            category = tc.get("issue_category", "unknown")
            categories[category] = categories.get(category, 0) + 1
            
            metrics = tc.get("quality_metrics", {})
            if metrics:
                avg_quality = sum(metrics.values()) / len(metrics)
                quality_scores.append(avg_quality)
        
        return {
            "category_distribution": categories,
            "average_quality_score": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            "quality_distribution": {
                "high_quality": len([q for q in quality_scores if q > 0.8]),
                "medium_quality": len([q for q in quality_scores if 0.6 <= q <= 0.8]),
                "low_quality": len([q for q in quality_scores if q < 0.6])
            }
        }


async def main():
    """Main function for testing the LangGraph Jamie Processor"""
    logger.info("🚀 Testing LangGraph Jamie Processor")
    
    processor = LangGraphJamieProcessor()
    
    # Process a batch of conversations
    results = await processor.process_batch_conversations(limit=20)
    
    if "error" not in results:
        logger.info("📊 Processing Results:")
        logger.info(f"  Conversations processed: {results['conversations_processed']}")
        logger.info(f"  Test cases generated: {results['total_test_cases_generated']}")
        logger.info(f"  Jamie responses extracted: {results['total_jamie_responses_extracted']}")
        logger.info(f"  Average quality score: {results['average_quality_score']:.3f}")
        
        # Export test cases
        if processor.export_test_cases():
            logger.info("✅ Test cases exported successfully")
        
    else:
        logger.error(f"❌ Processing failed: {results['error']}")


if __name__ == "__main__":
    asyncio.run(main())
