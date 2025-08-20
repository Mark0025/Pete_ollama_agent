#!/usr/bin/env python3
"""
PeteOllama V1 - Intelligent Response Cache
==========================================

Uses langchain_indexed_conversations.json to provide near-instant responses
for common property management queries by caching Jamie's actual responses.
"""

import json
import re
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from loguru import logger
import time


class ResponseCache:
    """Intelligent caching system for property management responses"""
    
    def __init__(self, conversations_file: str = None):
        if conversations_file is None:
            conversations_file = "langchain_indexed_conversations.json"
        
        self.conversations_file = conversations_file
        self.cache: Dict[str, Dict] = {}
        self.patterns: List[Tuple[str, str, str]] = []
        self.load_cache()
        
    def load_cache(self):
        """Load and process conversation data into intelligent cache"""
        try:
            if not os.path.exists(self.conversations_file):
                logger.warning(f"Conversations file not found: {self.conversations_file}")
                self._create_fallback_cache()
                return
            
            logger.info(f"📚 Loading conversation cache from: {self.conversations_file}")
            
            with open(self.conversations_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._extract_patterns(data)
            logger.info(f"✅ Loaded {len(self.patterns)} response patterns for instant replies")
            
        except Exception as e:
            logger.error(f"Error loading conversation cache: {e}")
            self._create_fallback_cache()
    
    def _extract_patterns(self, data: Dict):
        """Extract common query-response patterns from conversation data"""
        conversation_threads = data.get('conversation_threads', {})
        
        # Common property management topics to extract
        topic_keywords = {
            'rent_payment': ['rent', 'payment', 'due', 'pay', 'monthly'],
            'maintenance': ['fix', 'repair', 'broken', 'maintenance', 'not working'],
            'hvac': ['ac', 'air', 'heat', 'heating', 'cooling', 'hvac', 'temperature'],
            'plumbing': ['toilet', 'leak', 'water', 'plumbing', 'drain', 'faucet'],
            'lease': ['lease', 'agreement', 'contract', 'term', 'renewal'],
            'move_out': ['move out', 'moving', 'leaving', 'deposit', 'security'],
            'emergency': ['emergency', 'urgent', 'asap', 'immediate', 'help'],
            'contact': ['contact', 'call', 'phone', 'reach', 'number'],
            'schedule': ['schedule', 'appointment', 'visit', 'time', 'when'],
            'property': ['property', 'house', 'apartment', 'unit', 'address']
        }
        
        for thread_id, thread_data in conversation_threads.items():
            conversations = thread_data.get('conversations', [])
            
            for conv in conversations:
                jamie_responses = conv.get('jamie_said', [])
                client_messages = conv.get('client_said', [])
                
                # Extract high-quality Jamie responses
                for response in jamie_responses:
                    if response and self._is_quality_response(response):  # Better quality check
                        # Classify response by topic
                        topic = self._classify_response_topic(response, topic_keywords)
                        
                        # Find matching client context if available
                        context = self._find_matching_context(response, client_messages)
                        
                        # Create cache entry
                        cache_key = self._generate_cache_key(response, topic)
                        
                        # Skip if this key already exists with higher confidence
                        if cache_key in self.cache:
                            continue
                        
                        confidence = self._calculate_confidence(response, context)
                        
                        # Only cache high-confidence responses
                        if confidence >= 0.6:
                            self.cache[cache_key] = {
                                'response': response.strip(),
                                'topic': topic,
                                'context': context,
                                'confidence': confidence,
                                'keywords': self._extract_keywords(response + ' ' + context)
                            }
                            
                            # Create pattern for matching
                            self.patterns.append((
                                topic,
                                self._create_pattern(response, context),
                                cache_key
                            ))
    
    def _classify_response_topic(self, response: str, topic_keywords: Dict[str, List[str]]) -> str:
        """Classify Jamie's response by topic"""
        response_lower = response.lower()
        topic_scores = {}
        
        for topic, keywords in topic_keywords.items():
            score = sum(1 for keyword in keywords if keyword in response_lower)
            if score > 0:
                topic_scores[topic] = score
        
        if topic_scores:
            return max(topic_scores, key=topic_scores.get)
        return 'general'
    
    def _find_matching_context(self, response: str, client_messages: List[str]) -> str:
        """Find client message that likely prompted this Jamie response"""
        if not client_messages:
            return ""
        
        # Simple heuristic: find client message with overlapping keywords
        response_words = set(response.lower().split())
        
        best_match = ""
        best_score = 0
        
        for message in client_messages:
            if len(message.strip()) < 10:  # Skip very short messages
                continue
                
            message_words = set(message.lower().split())
            overlap = len(response_words.intersection(message_words))
            
            if overlap > best_score:
                best_score = overlap
                best_match = message.strip()
        
        return best_match[:200]  # Limit context length
    
    def _generate_cache_key(self, response: str, topic: str) -> str:
        """Generate unique cache key"""
        # Use first few words + topic as key
        words = response.split()[:5]
        key = f"{topic}_{' '.join(words)}"
        return re.sub(r'[^a-zA-Z0-9_\s]', '', key).replace(' ', '_').lower()
    
    def _is_quality_response(self, response: str) -> bool:
        """Check if response is high quality and suitable for caching"""
        response_lower = response.lower().strip()
        
        # Minimum length check
        if len(response) < 30:
            return False
        
        # Must be complete sentences (professional responses)
        if not any(response.endswith(punct) for punct in ['.', '!', '?']):
            return False
        
        # Skip partial responses or conversation fragments
        skip_patterns = [
            'um,', 'uh,', 'like,', 'you know,',  # Conversation fillers
            'and then', 'so anyway', 'but um',    # Mid-conversation transitions
            'hold on', 'one sec', 'give me',      # Process interruptions
        ]
        
        if any(pattern in response_lower for pattern in skip_patterns):
            return False
        
        # Prefer action-oriented, helpful responses
        positive_patterns = [
            'i will', 'i\'ll', 'let me', 'i can',
            'schedule', 'contact', 'send', 'call',
            'repair', 'fix', 'maintenance', 'check'
        ]
        
        has_action = any(pattern in response_lower for pattern in positive_patterns)
        
        # Must have action words for short responses
        if len(response) < 60 and not has_action:
            return False
            
        return True
    
    def _calculate_confidence(self, response: str, context: str) -> float:
        """Calculate confidence score for cached response"""
        confidence = 0.5  # Base confidence
        
        # Factors that increase confidence
        if len(response) > 50:  # Detailed responses
            confidence += 0.2
        if context and len(context) > 20:  # Has context
            confidence += 0.1
        if any(word in response.lower() for word in ['i will', 'i\'ll', 'contact', 'schedule']):
            confidence += 0.1  # Action-oriented responses
        if any(word in response.lower() for word in ['professional', 'maintenance', 'contractor']):
            confidence += 0.1  # Professional language
        
        return min(confidence, 1.0)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract key terms from response and context"""
        # Remove common stop words and extract meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]
        return list(set(keywords))[:10]  # Top 10 unique keywords
    
    def _create_pattern(self, response: str, context: str) -> str:
        """Create matching pattern for queries"""
        # Combine response and context keywords for pattern matching
        all_text = (response + ' ' + context).lower()
        
        # Extract key phrases that indicate this type of query
        key_phrases = []
        
        # Common patterns
        patterns = [
            r'\b(rent|payment|due|pay)\b',
            r'\b(fix|repair|broken|maintenance)\b', 
            r'\b(ac|air|heat|heating|cooling)\b',
            r'\b(toilet|leak|water|plumbing)\b',
            r'\b(lease|agreement|contract)\b',
            r'\b(move|moving|deposit|security)\b',
            r'\b(emergency|urgent|asap)\b',
            r'\b(contact|call|phone|reach)\b',
            r'\b(schedule|appointment|visit)\b'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, all_text)
            if matches:
                key_phrases.extend(matches)
        
        return '|'.join(set(key_phrases)) if key_phrases else 'general'
    
    def find_cached_response(self, user_query: str) -> Optional[Dict]:
        """Find cached response for user query with near-instant lookup"""
        start_time = time.time()
        
        if not self.patterns:
            return None
        
        user_query_lower = user_query.lower()
        user_words = set(re.findall(r'\b\w+\b', user_query_lower))
        
        best_match = None
        best_score = 0
        
        # Quick pattern matching
        for topic, pattern, cache_key in self.patterns:
            # Check if pattern keywords appear in query
            pattern_words = set(pattern.split('|'))
            overlap = len(user_words.intersection(pattern_words))
            
            if overlap > 0 and cache_key in self.cache:
                cached_item = self.cache[cache_key]
                
                # Calculate match score
                keyword_overlap = len(user_words.intersection(set(cached_item['keywords'])))
                score = overlap + keyword_overlap * 0.5
                
                if score > best_score:
                    best_score = score
                    best_match = {
                        **cached_item,
                        'cache_key': cache_key,
                        'match_score': score,
                        'lookup_time_ms': (time.time() - start_time) * 1000
                    }
        
        # Only return if we have a decent match
        if best_match and best_score >= 1.0:
            response_text = best_match['response']
            response_length = len(response_text)
            
            logger.info(f"⚡ CACHE HIT - Using conversation similarity response")
            logger.info(f"🔑 Cache key: {best_match['cache_key']}")
            logger.info(f"📊 Similarity score: {best_score:.2f}")
            logger.info(f"📏 Response length: {response_length} chars")
            logger.info(f"📄 Response preview: {response_text[:100]}{'...' if response_length > 100 else ''}")
            logger.info(f"⚡ Response time: {best_match['lookup_time_ms']:.1f}ms (cached)")
            
            # Add metadata to show this came from cache
            best_match['response_metadata'] = {
                'length': response_length,
                'source': 'conversation_similarity_cache',
                'similarity_score': best_score,
                'cache_key': best_match['cache_key'],
                'response_time_ms': best_match['lookup_time_ms']
            }
            
            return best_match
        
        logger.info(f"🔍 No cache match found for: {user_query[:50]}...")
        return None
    
    def add_response_to_cache(self, user_query: str, response: str, topic: str = 'general'):
        """Add new response to cache for future use"""
        cache_key = self._generate_cache_key(response, topic)
        
        self.cache[cache_key] = {
            'response': response.strip(),
            'topic': topic,
            'context': user_query[:200],
            'confidence': 0.8,  # High confidence for manually added
            'keywords': self._extract_keywords(response + ' ' + user_query)
        }
        
        # Add pattern
        pattern = self._create_pattern(response, user_query)
        self.patterns.append((topic, pattern, cache_key))
        
        logger.info(f"✅ Added new cached response: {cache_key}")
    
    def _create_fallback_cache(self):
        """Create fallback cache with common property management responses"""
        fallback_responses = [
            {
                'query_pattern': 'rent due payment when',
                'response': "Rent is due on the 1st of each month. You can pay through the online portal or drop off a check at the office.",
                'topic': 'rent_payment'
            },
            {
                'query_pattern': 'ac heat hvac broken repair',
                'response': "I'll contact our HVAC contractor right away to schedule a repair visit. They should reach out within the next hour.",
                'topic': 'hvac'
            },
            {
                'query_pattern': 'toilet leak plumbing water',
                'response': "I'll send a plumber out today. Please place towels around the area to prevent any water damage.",
                'topic': 'plumbing'
            },
            {
                'query_pattern': 'maintenance repair fix broken',
                'response': "I'll schedule a maintenance visit to take care of that issue. Someone should be able to come out within 24 hours.",
                'topic': 'maintenance'
            },
            {
                'query_pattern': 'emergency urgent help asap',
                'response': "I understand this is urgent. I'm contacting our emergency maintenance team right now and they'll be out as soon as possible.",
                'topic': 'emergency'
            },
            {
                'query_pattern': 'lease agreement renewal contract',
                'response': "I'll review your lease terms and get back to you with renewal options by tomorrow. Feel free to call if you have any questions.",
                'topic': 'lease'
            },
            {
                'query_pattern': 'move out moving deposit security',
                'response': "I'll need 30 days written notice for move-out. Once I receive that, I'll schedule a walkthrough and explain the deposit return process.",
                'topic': 'move_out'
            },
            {
                'query_pattern': 'contact call phone reach',
                'response': "You can reach me at this number or send a text. I typically respond within a few hours during business days.",
                'topic': 'contact'
            }
        ]
        
        for item in fallback_responses:
            cache_key = f"fallback_{item['topic']}"
            self.cache[cache_key] = {
                'response': item['response'],
                'topic': item['topic'], 
                'context': '',
                'confidence': 0.7,
                'keywords': item['query_pattern'].split()
            }
            
            self.patterns.append((
                item['topic'],
                item['query_pattern'].replace(' ', '|'),
                cache_key
            ))
        
        logger.info(f"✅ Created fallback cache with {len(fallback_responses)} responses")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            'total_responses': len(self.cache),
            'total_patterns': len(self.patterns),
            'topics': list(set(item['topic'] for item in self.cache.values())),
            'avg_confidence': sum(item['confidence'] for item in self.cache.values()) / len(self.cache) if self.cache else 0,
            'cache_file': self.conversations_file
        }


# Global cache instance
response_cache = ResponseCache()


def get_instant_response(user_query: str) -> Optional[str]:
    """Quick lookup for instant cached response"""
    cached = response_cache.find_cached_response(user_query)
    if cached and cached['confidence'] >= 0.6:
        return cached['response']
    return None


if __name__ == "__main__":
    # Test the cache system
    print("🧪 Testing Response Cache System")
    print("=" * 50)
    
    test_queries = [
        "When is my rent due?",
        "My AC is broken can you help?",
        "I have a toilet leak",
        "Need maintenance for my unit",
        "This is an emergency!",
        "How do I contact you?",
        "I want to move out next month",
        "Can you fix my garbage disposal?"
    ]
    
    for query in test_queries:
        start_time = time.time()
        response = get_instant_response(query)
        lookup_time = (time.time() - start_time) * 1000
        
        if response:
            print(f"✅ Query: {query}")
            print(f"⚡ Response ({lookup_time:.1f}ms): {response}")
        else:
            print(f"❌ Query: {query}")
            print(f"🔍 No cached response found ({lookup_time:.1f}ms)")
        print()
    
    # Show cache stats
    stats = response_cache.get_cache_stats()
    print("📊 Cache Statistics:")
    print(f"   Total responses: {stats['total_responses']}")
    print(f"   Total patterns: {stats['total_patterns']}")
    print(f"   Topics: {', '.join(stats['topics'])}")
    print(f"   Avg confidence: {stats['avg_confidence']:.2f}")
