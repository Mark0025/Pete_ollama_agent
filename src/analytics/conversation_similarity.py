"""
Conversation similarity analyzer using LangChain for comparing responses against DB conversations.
"""
import json
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from loguru import logger
import sys
import os
import sqlite3
from dataclasses import dataclass
import re

# Try to import LangChain components (graceful fallback if not available)
try:
    from langchain.embeddings import HuggingFaceEmbeddings
    from langchain.vectorstores import FAISS
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.schema import Document
    LANGCHAIN_AVAILABLE = True
except ImportError:
    logger.warning("LangChain not available, using fallback similarity methods")
    LANGCHAIN_AVAILABLE = False

@dataclass
class ConversationSample:
    """A conversation sample from the database."""
    user_message: str
    agent_response: str
    context: str
    conversation_id: str
    timestamp: str

@dataclass
class SimilarityResult:
    """Result of similarity comparison."""
    similarity_score: float  # 0.0 to 1.0
    best_match: Optional[ConversationSample]
    explanation: str
    confidence: float

class ConversationSimilarityAnalyzer:
    """Analyzes conversation similarity using embeddings and semantic search."""
    
    def __init__(self, indexed_conversations_path: str = "/app/langchain_indexed_conversations.json"):
        self.indexed_conversations_path = indexed_conversations_path
        self.conversation_samples: List[ConversationSample] = []
        self.embeddings = None
        self.vectorstore = None
        
        # Load conversation data from indexed JSON
        self._load_indexed_conversations()
        
        # Initialize embeddings if LangChain is available
        if LANGCHAIN_AVAILABLE:
            self._initialize_embeddings()
        else:
            logger.info("Using keyword-based similarity analysis (LangChain not available)")
    
    def _load_indexed_conversations(self) -> None:
        """Load conversation samples from the indexed JSON file."""
        try:
            if not os.path.exists(self.indexed_conversations_path):
                logger.warning(f"Indexed conversations file not found: {self.indexed_conversations_path}")
                self._create_fallback_samples()
                return
            
            logger.info(f"Loading indexed conversations from: {self.indexed_conversations_path}")
            
            with open(self.indexed_conversations_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract metadata
            metadata = data.get('metadata', {})
            total_conversations = metadata.get('total_conversations', 0)
            total_threads = metadata.get('total_threads', 0)
            
            logger.info(f"📊 Found {total_conversations} conversations across {total_threads} threads")
            
            # Process conversation threads
            conversation_threads = data.get('conversation_threads', {})
            samples_created = 0
            
            for thread_id, thread_data in conversation_threads.items():
                client_info = thread_data.get('client_info', {})
                conversations = thread_data.get('conversations', [])
                
                for conv in conversations:
                    # Extract Jamie's responses and client queries
                    jamie_responses = conv.get('jamie_said', [])
                    client_messages = conv.get('client_said', [])
                    date = conv.get('date', '')
                    incoming = conv.get('incoming', 0)
                    
                    # Create training samples from Jamie's responses
                    for i, jamie_response in enumerate(jamie_responses):
                        if jamie_response and len(jamie_response.strip()) > 10:
                            # Try to pair with relevant client message
                            client_message = ""
                            if i < len(client_messages):
                                client_message = client_messages[i]
                            elif client_messages:
                                # Use the most relevant client message
                                client_message = client_messages[0]
                            
                            # Create conversation sample
                            sample = ConversationSample(
                                user_message=client_message or "General inquiry",
                                agent_response=jamie_response,
                                context=f"Thread: {thread_id}, Date: {date}, Type: {'Incoming' if incoming else 'Outgoing'}",
                                conversation_id=f"{thread_id}_{date}_{i}",
                                timestamp=date
                            )
                            
                            self.conversation_samples.append(sample)
                            samples_created += 1
            
            logger.info(f"✅ Created {samples_created} conversation samples from indexed data")
            
        except Exception as e:
            logger.error(f"Error loading indexed conversations: {e}")
            self._create_fallback_samples()
    
    def _create_fallback_samples(self) -> None:
        """Create fallback samples if indexed conversations aren't available."""
        fallback_samples = [
            ("My AC stopped working", "I'll contact our HVAC contractor to schedule a repair visit. They should reach out within the next hour.", "HVAC emergency"),
            ("Toilet is leaking", "I'll send a plumber out today. Please place towels around the area to prevent water damage.", "Plumbing emergency"),
            ("When is rent due?", "Rent is due on the 1st of each month. You can pay through the online portal or drop off a check.", "Rent payment"),
            ("Garbage disposal broken", "I'll schedule a maintenance visit. In the meantime, please avoid using the disposal.", "Appliance repair"),
            ("Neighbor too loud", "I'll speak with them about the noise levels. Property quiet hours are 10 PM to 7 AM.", "Noise complaint"),
            ("Can't access payment portal", "I'll send you the direct link and your login credentials. The portal was recently updated.", "Portal access"),
            ("Heat not working", "This is a priority repair. I'm calling our HVAC contractor right now to get someone out there today.", "HVAC emergency"),
            ("Water pressure low", "I'll have maintenance check the water system. This could be a building-wide issue.", "Plumbing maintenance"),
            ("Smoke detector beeping", "That usually means the battery needs replacing. I'll have maintenance come by today with new batteries.", "Safety maintenance"),
            ("Lease renewal question", "I'll review your lease terms and get back to you with renewal options by tomorrow.", "Lease administration")
        ]
        
        for user_msg, agent_resp, context in fallback_samples:
            sample = ConversationSample(
                user_message=user_msg,
                agent_response=agent_resp,
                context=context,
                conversation_id=f"fallback_{len(self.conversation_samples)}",
                timestamp="2025-01-01"
            )
            self.conversation_samples.append(sample)
        
        logger.info(f"Created {len(fallback_samples)} fallback conversation samples")


    
    def _initialize_embeddings(self) -> None:
        """Initialize the embedding model and vector store."""
        try:
            if not LANGCHAIN_AVAILABLE:
                return
            
            # Use a lightweight embedding model
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            
            # Create documents from conversation samples
            documents = []
            for i, sample in enumerate(self.conversation_samples):
                # Create a document that combines user message and expected response
                content = f"User: {sample.user_message}\nAgent: {sample.agent_response}"
                doc = Document(
                    page_content=content,
                    metadata={
                        "sample_id": i,
                        "user_message": sample.user_message,
                        "agent_response": sample.agent_response,
                        "context": sample.context
                    }
                )
                documents.append(doc)
            
            if documents:
                # Create vector store
                self.vectorstore = FAISS.from_documents(documents, self.embeddings)
                logger.info(f"Created vector store with {len(documents)} documents")
            
        except Exception as e:
            logger.error(f"Error initializing embeddings: {e}")
            self.embeddings = None
            self.vectorstore = None
    
    def calculate_similarity(self, user_message: str, agent_response: str) -> SimilarityResult:
        """
        Calculate similarity between a new conversation and existing samples.
        
        Args:
            user_message: The user's input
            agent_response: The agent's response
            
        Returns:
            SimilarityResult with similarity score and best match
        """
        
        # First categorize the conversation
        conversation_category = self.categorize_conversation(user_message, agent_response)
        issue_type = conversation_category["issue_type"]
        urgency_level = conversation_category["urgency_level"]
        
        # Find similar responses from Jamie for the same issue type
        similar_issue_responses = self.find_similar_issue_responses(user_message, issue_type)
        
        if LANGCHAIN_AVAILABLE and self.vectorstore:
            result = self._calculate_semantic_similarity(user_message, agent_response)
            
            # Enhance with issue-specific analysis
            if similar_issue_responses:
                result.explanation += f" | Issue type: {issue_type} ({urgency_level}) | Found {len(similar_issue_responses)} similar Jamie responses"
            
            return result
        else:
            result = self._calculate_keyword_similarity(user_message, agent_response)
            
            # Enhance with issue-specific analysis
            if similar_issue_responses:
                # Compare against issue-specific responses
                issue_similarity_scores = []
                for similar_sample in similar_issue_responses:
                    response_tokens = set(agent_response.lower().split())
                    jamie_tokens = set(similar_sample.agent_response.lower().split())
                    
                    intersection = response_tokens.intersection(jamie_tokens)
                    union = response_tokens.union(jamie_tokens)
                    similarity = len(intersection) / len(union) if union else 0
                    issue_similarity_scores.append(similarity)
                
                # Use the best issue-specific similarity
                best_issue_similarity = max(issue_similarity_scores) if issue_similarity_scores else 0
                
                # Combine general and issue-specific similarity
                combined_similarity = (result.similarity_score * 0.6) + (best_issue_similarity * 0.4)
                
                result.similarity_score = combined_similarity
                result.explanation += f" | Issue type: {issue_type} ({urgency_level}) | Issue-specific similarity: {best_issue_similarity:.2f}"
            
            return result
    
    def _calculate_semantic_similarity(self, user_message: str, agent_response: str) -> SimilarityResult:
        """Calculate similarity using semantic embeddings."""
        try:
            # Create query from the new conversation
            query = f"User: {user_message}\nAgent: {agent_response}"
            
            # Find similar conversations
            similar_docs = self.vectorstore.similarity_search_with_score(query, k=3)
            
            if not similar_docs:
                return SimilarityResult(
                    similarity_score=0.0,
                    best_match=None,
                    explanation="No similar conversations found",
                    confidence=0.0
                )
            
            # Get the best match
            best_doc, distance = similar_docs[0]
            
            # Convert distance to similarity (FAISS returns distances, lower is better)
            similarity_score = max(0, 1.0 - (distance / 2.0))  # Normalize to 0-1
            
            # Get the conversation sample
            sample_id = best_doc.metadata["sample_id"]
            best_match = self.conversation_samples[sample_id]
            
            # Calculate confidence based on how much better the best match is vs others
            if len(similar_docs) > 1:
                second_distance = similar_docs[1][1]
                confidence = min(1.0, abs(second_distance - distance) / 0.5)
            else:
                confidence = similarity_score
            
            explanation = f"Best match similarity: {similarity_score:.2f}, found similar conversation about '{best_match.context}'"
            
            return SimilarityResult(
                similarity_score=similarity_score,
                best_match=best_match,
                explanation=explanation,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error in semantic similarity calculation: {e}")
            return self._calculate_keyword_similarity(user_message, agent_response)
    
    def _calculate_keyword_similarity(self, user_message: str, agent_response: str) -> SimilarityResult:
        """Fallback similarity calculation using keyword matching."""
        
        if not self.conversation_samples:
            return SimilarityResult(
                similarity_score=0.0,
                best_match=None,
                explanation="No conversation samples available",
                confidence=0.0
            )
        
        # Normalize and tokenize the input
        user_tokens = set(re.findall(r'\w+', user_message.lower()))
        response_tokens = set(re.findall(r'\w+', agent_response.lower()))
        
        best_score = 0.0
        best_match = None
        
        for sample in self.conversation_samples:
            # Compare user messages
            sample_user_tokens = set(re.findall(r'\w+', sample.user_message.lower()))
            sample_response_tokens = set(re.findall(r'\w+', sample.agent_response.lower()))
            
            # Calculate Jaccard similarity for user messages
            user_intersection = user_tokens.intersection(sample_user_tokens)
            user_union = user_tokens.union(sample_user_tokens)
            user_similarity = len(user_intersection) / len(user_union) if user_union else 0
            
            # Calculate Jaccard similarity for responses
            response_intersection = response_tokens.intersection(sample_response_tokens)
            response_union = response_tokens.union(sample_response_tokens)
            response_similarity = len(response_intersection) / len(response_union) if response_union else 0
            
            # Combined similarity (weighted toward user message matching)
            combined_similarity = (user_similarity * 0.7) + (response_similarity * 0.3)
            
            if combined_similarity > best_score:
                best_score = combined_similarity
                best_match = sample
        
        # Adjust confidence based on score
        confidence = min(1.0, best_score * 2)  # Scale up for keyword matching
        
        explanation = f"Keyword similarity: {best_score:.2f}, matched conversation about '{best_match.context if best_match else 'unknown'}'"
        
        return SimilarityResult(
            similarity_score=best_score,
            best_match=best_match,
            explanation=explanation,
            confidence=confidence
        )
    
    def categorize_conversation(self, user_message: str, agent_response: str) -> Dict[str, str]:
        """
        Categorize a conversation by issue type and urgency.
        
        Args:
            user_message: The user's input
            agent_response: The agent's response
            
        Returns:
            Dictionary with issue_type, urgency_level, and property_context
        """
        user_lower = user_message.lower()
        response_lower = agent_response.lower()
        
        # Issue type classification
        issue_type = "general_inquiry"
        if any(keyword in user_lower for keyword in ["ac", "air condition", "hvac", "heat", "cool"]):
            issue_type = "hvac"
        elif any(keyword in user_lower for keyword in ["toilet", "leak", "plumb", "water", "drain"]):
            issue_type = "plumbing"
        elif any(keyword in user_lower for keyword in ["electric", "power", "outlet", "light"]):
            issue_type = "electrical"
        elif any(keyword in user_lower for keyword in ["rent", "payment", "portal", "late", "due"]):
            issue_type = "payment"
        elif any(keyword in user_lower for keyword in ["noise", "neighbor", "loud", "complaint"]):
            issue_type = "noise_complaint"
        elif any(keyword in user_lower for keyword in ["appliance", "disposal", "dishwasher", "washer"]):
            issue_type = "appliance"
        elif any(keyword in user_lower for keyword in ["lease", "renew", "move", "evict"]):
            issue_type = "lease_administration"
        elif any(keyword in user_lower for keyword in ["maintenance", "repair", "fix", "broken"]):
            issue_type = "maintenance"
        
        # Urgency classification
        urgency_level = "normal"
        emergency_keywords = ["emergency", "urgent", "asap", "immediately", "flooding", "no heat", "no ac"]
        if any(keyword in user_lower for keyword in emergency_keywords):
            urgency_level = "emergency"
        elif any(keyword in user_lower for keyword in ["soon", "today", "quickly"]):
            urgency_level = "high"
        
        # Extract property context if available
        property_context = "unknown"
        # Look for apartment numbers, addresses, or unit references
        import re
        apt_match = re.search(r'(?:apt|apartment|unit)\s*(\d+)', user_lower)
        if apt_match:
            property_context = f"Unit {apt_match.group(1)}"
        
        return {
            "issue_type": issue_type,
            "urgency_level": urgency_level,
            "property_context": property_context
        }
    
    def find_similar_issue_responses(self, user_message: str, issue_type: str, limit: int = 5) -> List[ConversationSample]:
        """
        Find similar responses from Jamie for the same issue type.
        
        Args:
            user_message: The current user query
            issue_type: The classified issue type
            limit: Maximum number of similar responses to return
            
        Returns:
            List of similar conversation samples
        """
        similar_responses = []
        
        for sample in self.conversation_samples:
            # Check if this sample relates to the same issue type
            sample_category = self.categorize_conversation(sample.user_message, sample.agent_response)
            
            if sample_category["issue_type"] == issue_type:
                # Calculate basic similarity for ranking
                user_tokens = set(user_message.lower().split())
                sample_tokens = set(sample.user_message.lower().split())
                
                intersection = user_tokens.intersection(sample_tokens)
                union = user_tokens.union(sample_tokens)
                similarity = len(intersection) / len(union) if union else 0
                
                similar_responses.append((similarity, sample))
        
        # Sort by similarity and return top matches
        similar_responses.sort(key=lambda x: x[0], reverse=True)
        return [sample for _, sample in similar_responses[:limit]]

    def get_success_rate(self, similarity_score: float, response_length: int = 0) -> float:
        """
        Convert similarity score to a success rate percentage.
        
        Args:
            similarity_score: Similarity score (0.0 to 1.0)
            response_length: Length of response for additional scoring
            
        Returns:
            Success rate as percentage (0.0 to 100.0)
        """
        
        # Base success rate from similarity
        base_rate = similarity_score * 100
        
        # Bonus points for appropriate response length
        length_bonus = 0
        if 50 <= response_length <= 500:  # Good length range
            length_bonus = 5
        elif response_length < 20:  # Too short
            length_bonus = -10
        elif response_length > 1000:  # Too long
            length_bonus = -5
        
        # Cap at 100%
        success_rate = min(100.0, base_rate + length_bonus)
        
        return max(0.0, success_rate)
    
    def analyze_conversation_batch(self, conversations: List[Dict]) -> Dict:
        """
        Analyze a batch of conversations for similarity metrics.
        
        Args:
            conversations: List of conversation dicts with 'user_message' and 'agent_response'
            
        Returns:
            Summary statistics
        """
        
        results = []
        total_similarity = 0
        total_success = 0
        
        for conv in conversations:
            user_msg = conv.get('user_message', '')
            agent_resp = conv.get('agent_response', '')
            
            if user_msg and agent_resp:
                similarity_result = self.calculate_similarity(user_msg, agent_resp)
                success_rate = self.get_success_rate(
                    similarity_result.similarity_score, 
                    len(agent_resp)
                )
                
                results.append({
                    'similarity_score': similarity_result.similarity_score,
                    'success_rate': success_rate,
                    'confidence': similarity_result.confidence,
                    'explanation': similarity_result.explanation
                })
                
                total_similarity += similarity_result.similarity_score
                total_success += success_rate
        
        if results:
            avg_similarity = total_similarity / len(results)
            avg_success = total_success / len(results)
        else:
            avg_similarity = 0
            avg_success = 0
        
        return {
            'total_conversations': len(results),
            'average_similarity': avg_similarity,
            'average_success_rate': avg_success,
            'results': results
        }