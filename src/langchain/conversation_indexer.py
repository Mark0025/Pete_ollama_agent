"""
Conversation Indexer for LangChain Integration

This module processes conversation data to understand:
- Who is speaking (Jamie vs clients)  
- Conversation threading by name/phone
- Temporal flow of conversations
- Context building for training
"""

import os
import re
import json
import sqlite3
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from database.pete_db_manager import PeteDBManager
from utils.logger import logger


class ConversationIndexer:
    """
    Indexes and processes conversations for LangChain training
    
    Key Functions:
    - Identifies Jamie (property manager) vs clients
    - Matches conversations by name/phone over time
    - Creates conversation threads and timelines
    - Builds proper context for model training
    """
    
    def __init__(self):
        self.db_manager = PeteDBManager()
        self.conversations = []
        self.conversation_threads = {}
        self.client_profiles = {}
        self.jamie_responses = []
        
    def load_conversations(self) -> bool:
        """Load FULL PHONE CALLS ONLY from database (no SMS/text truncation)"""
        try:
            if not self.db_manager.is_connected():
                logger.error("Database not connected")
                return False
                
            # Get ONLY phone calls with FULL transcriptions
            connection = sqlite3.connect(self.db_manager.db_path)
            query = """
            SELECT CreationDate, Data, Transcription, Incoming
            FROM communication_logs 
            WHERE Transcription IS NOT NULL 
            AND LENGTH(Transcription) > 500
            AND Transcription NOT LIKE '%SMS%'
            AND Transcription NOT LIKE '%text%message%'
            AND (Transcription LIKE '%Hello%' OR Transcription LIKE '%This is%' OR Transcription LIKE '%Hey%')
            ORDER BY CreationDate ASC
            """
            
            df = pd.read_sql_query(query, connection)
            connection.close()
            
            # Filter for quality phone calls only
            quality_calls = []
            for conv in df.to_dict('records'):
                transcription = conv.get('Transcription', '')
                
                # Skip if transcription looks like SMS or is truncated
                if self._is_quality_phone_call(transcription):
                    quality_calls.append(conv)
            
            self.conversations = quality_calls
            logger.info(f"✅ Loaded {len(self.conversations)} FULL PHONE CALLS for voice agent training")
            logger.info(f"📞 Filtered out SMS/text messages and truncated calls")
            return True
            
        except Exception as e:
            logger.error(f"Error loading conversations: {e}")
            return False
    
    def _is_quality_phone_call(self, transcription: str) -> bool:
        """
        Determine if this is a quality full phone call (not SMS or truncated)
        """
        if not transcription or len(transcription) < 500:
            return False
        
        # Skip SMS indicators
        sms_indicators = [
            'text message', 'sms', 'message sent', 'message received',
            'reply stop', 'opt out', 'shortcode'
        ]
        
        transcription_lower = transcription.lower()
        for indicator in sms_indicators:
            if indicator in transcription_lower:
                return False
        
        # Must have phone call indicators
        call_indicators = [
            'hello', 'hi', 'hey', 'this is', 'calling', 'phone call',
            'how are you', 'what\'s going on', 'good morning', 'good afternoon'
        ]
        
        has_call_indicator = any(indicator in transcription_lower for indicator in call_indicators)
        
        # Must have reasonable conversation length and flow
        sentences = transcription.split('.')
        has_conversation_flow = len(sentences) > 5
        
        # Check for speaker alternation (indicates real conversation)
        has_dialogue = ('jamie' in transcription_lower and 
                       any(word in transcription_lower for word in ['i', 'my', 'we', 'you']))
        
        return has_call_indicator and has_conversation_flow and has_dialogue
    
    def identify_speakers(self, transcription: str) -> Dict[str, List[str]]:
        """
        Identify who is speaking in the conversation
        
        Returns:
        - jamie_parts: What Jamie said
        - client_parts: What the client said
        """
        jamie_indicators = [
            "this is jamie", "jamie here", "jamie speaking",
            "i'll", "let me", "i can", "i will", "i'll send",
            "i'll schedule", "i'll call", "i'll check"
        ]
        
        client_indicators = [
            "hi jamie", "hey jamie", "jamie,", "calling about",
            "my", "i have", "we have", "there's a", "can you",
            "when will", "what about", "is there"
        ]
        
        # Split conversation into segments
        sentences = [s.strip() for s in transcription.split('.') if len(s.strip()) > 10]
        
        jamie_parts = []
        client_parts = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Check for Jamie indicators
            jamie_score = sum(1 for indicator in jamie_indicators 
                            if indicator in sentence_lower)
            
            # Check for client indicators  
            client_score = sum(1 for indicator in client_indicators 
                             if indicator in sentence_lower)
            
            # Classify based on indicators
            if jamie_score > client_score:
                jamie_parts.append(sentence)
            elif client_score > jamie_score:
                client_parts.append(sentence)
            else:
                # Default classification based on position and content
                if any(word in sentence_lower for word in ["i'll", "let me", "i can"]):
                    jamie_parts.append(sentence)
                else:
                    client_parts.append(sentence)
        
        return {
            "jamie_parts": jamie_parts,
            "client_parts": client_parts
        }
    
    def extract_client_info(self, conversation: Dict) -> Dict[str, str]:
        """Extract client information from conversation"""
        # Try to extract from Data field (JSON string)
        data_str = conversation.get('Data', '')
        name = 'Unknown'
        phone = 'Unknown'
        
        # Parse Data field if it contains contact info
        try:
            import json
            if data_str:
                data = json.loads(data_str)
                name = data.get('ContactDisplayName', 'Unknown')
                phone = data.get('ContactPhoneNumber', 'Unknown')
        except:
            pass
        
        # Try to extract name from transcription if not available
        if name == 'Unknown' or not name:
            transcription = conversation.get('Transcription', '')
            name_patterns = [
                r"this is (\w+)",
                r"my name is (\w+)",
                r"i'm (\w+)",
                r"(\w+) calling"
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, transcription.lower())
                if match:
                    name = match.group(1).title()
                    break
        
        return {
            "name": name,
            "phone": phone,
            "key": f"{name}_{phone}"  # Unique identifier
        }
    
    def build_conversation_threads(self) -> Dict[str, List[Dict]]:
        """
        Build conversation threads by grouping calls from same client over time
        """
        threads = {}
        
        for conv in self.conversations:
            client_info = self.extract_client_info(conv)
            client_key = client_info['key']
            
            if client_key not in threads:
                threads[client_key] = {
                    'client_info': client_info,
                    'conversations': [],
                    'total_calls': 0,
                    'date_range': {'first': None, 'last': None}
                }
            
            # Parse conversation
            speakers = self.identify_speakers(conv.get('Transcription', ''))
            
            conversation_data = {
                'date': conv.get('CreationDate'),
                'incoming': conv.get('Incoming', 1),  # 1=incoming, 0=outgoing
                'jamie_said': speakers['jamie_parts'],
                'client_said': speakers['client_parts'],
                'full_transcription': conv.get('Transcription')
            }
            
            threads[client_key]['conversations'].append(conversation_data)
            threads[client_key]['total_calls'] += 1
            
            # Update date range
            call_date = conv.get('CreationDate')
            if threads[client_key]['date_range']['first'] is None:
                threads[client_key]['date_range']['first'] = call_date
            threads[client_key]['date_range']['last'] = call_date
        
        self.conversation_threads = threads
        logger.info(f"✅ Built {len(threads)} conversation threads")
        return threads
    
    def analyze_conversation_patterns(self) -> Dict[str, any]:
        """
        Analyze patterns in Jamie's responses and client interactions
        """
        patterns = {
            'common_client_issues': {},
            'jamie_response_types': {},
            'escalation_patterns': [],
            'resolution_patterns': []
        }
        
        for thread_key, thread in self.conversation_threads.items():
            for conv in thread['conversations']:
                # Analyze client issues
                for client_msg in conv['client_said']:
                    # Extract issue types
                    issue_keywords = {
                        'maintenance': ['repair', 'fix', 'broken', 'not working', 'leak', 'ac', 'plumbing'],
                        'payment': ['rent', 'payment', 'late', 'check', 'money'],
                        'move': ['move', 'transfer', 'address', 'lease', 'lockbox'],
                        'emergency': ['emergency', 'urgent', 'asap', 'immediately']
                    }
                    
                    for issue_type, keywords in issue_keywords.items():
                        if any(keyword in client_msg.lower() for keyword in keywords):
                            patterns['common_client_issues'][issue_type] = \
                                patterns['common_client_issues'].get(issue_type, 0) + 1
                
                # Analyze Jamie's responses
                for jamie_msg in conv['jamie_said']:
                    response_types = {
                        'scheduling': ['i\'ll schedule', 'i\'ll send', 'i\'ll call'],
                        'information': ['let me check', 'i\'ll look into', 'i\'ll find out'],
                        'immediate_action': ['right away', 'today', 'immediately'],
                        'reassurance': ['don\'t worry', 'we\'ll take care', 'i understand']
                    }
                    
                    for response_type, phrases in response_types.items():
                        if any(phrase in jamie_msg.lower() for phrase in phrases):
                            patterns['jamie_response_types'][response_type] = \
                                patterns['jamie_response_types'].get(response_type, 0) + 1
        
        return patterns
    
    def create_full_conversation_examples(self, max_examples: int = 15) -> List[Dict[str, str]]:
        """
        Create FULL conversation examples with complete context and phone number tracking
        
        Instead of fragmented snippets, this creates complete conversation flows:
        - Full transcription analysis for each client (by phone number)
        - Complete conversation context from beginning to end
        - Client history across multiple calls
        - Proper conversation flow understanding
        """
        full_examples = []
        
        # Sort threads by total conversation quality and client interaction depth
        sorted_threads = sorted(
            self.conversation_threads.items(),
            key=lambda x: (len(x[1]['conversations']), 
                          sum(len(conv['full_transcription']) for conv in x[1]['conversations'])),
            reverse=True
        )
        
        for thread_key, thread in sorted_threads[:max_examples]:
            client_info = thread['client_info']
            client_name = client_info['name']
            client_phone = client_info['phone']
            
            # Get all conversations for this client in chronological order
            sorted_convs = sorted(thread['conversations'], 
                                key=lambda x: x.get('date', ''))
            
            # Build complete conversation history
            full_conversation_context = []
            
            for conv_idx, conv in enumerate(sorted_convs):
                full_transcription = conv['full_transcription']
                
                # Parse the FULL conversation flow
                conversation_flow = self._parse_full_conversation_flow(full_transcription)
                
                if conversation_flow and len(conversation_flow['exchanges']) > 0:
                    # Create context with full client history
                    context_info = {
                        'client_name': client_name,
                        'client_phone': client_phone,
                        'conversation_number': conv_idx + 1,
                        'total_calls_with_client': len(sorted_convs),
                        'previous_issues': [h['main_issue'] for h in full_conversation_context],
                        'date': conv.get('date'),
                        'call_history': full_conversation_context[-2:] if full_conversation_context else []
                    }
                    
                    # Take the BEST exchange from this full conversation
                    best_exchange = self._select_best_exchange_from_conversation(conversation_flow)
                    
                    if best_exchange:
                        example = {
                            'user': best_exchange['client_message'],
                            'assistant': best_exchange['jamie_response'],
                            'context': json.dumps(context_info),
                            'thread_id': thread_key,
                            'conversation_flow': conversation_flow,
                            'full_conversation': full_transcription[:500] + "..." if len(full_transcription) > 500 else full_transcription
                        }
                        full_examples.append(example)
                    
                    # Add this conversation to client history
                    full_conversation_context.append({
                        'date': conv.get('date'),
                        'main_issue': conversation_flow.get('main_issue', 'General inquiry'),
                        'resolution': conversation_flow.get('resolution', 'Handled by Jamie'),
                        'call_summary': conversation_flow.get('summary', '')
                    })
        
        logger.info(f"✅ Created {len(full_examples)} FULL conversation examples with complete context")
        return full_examples
    
    def _parse_full_conversation_flow(self, transcription: str) -> Dict:
        """
        Parse the COMPLETE conversation from beginning to end
        
        Instead of fragments, this extracts the FULL conversation flow:
        - Complete client issue description
        - Full Jamie response with context
        - Entire conversation understanding
        """
        if not transcription or len(transcription) < 50:
            return None
        
        # Clean the transcription
        clean_transcription = transcription.replace('\n', ' ').strip()
        
        # Identify the main issue (usually early in conversation)
        main_issue = "General inquiry"
        issue_indicators = {
            'AC/HVAC': ['ac', 'air conditioning', 'hvac', 'heat', 'cooling', 'temperature'],
            'Plumbing': ['leak', 'plumbing', 'water', 'pipe', 'toilet', 'sink', 'shower'],
            'Electrical': ['electric', 'power', 'breaker', 'outlet', 'light'],
            'Maintenance': ['repair', 'fix', 'broken', 'maintenance', 'door', 'window'],
            'Payment': ['rent', 'payment', 'late', 'check', 'money', 'bill'],
            'Move/Transfer': ['move', 'transfer', 'address', 'lease', 'moving'],
            'Emergency': ['emergency', 'urgent', 'asap', 'help', 'immediately'],
            'Inspection': ['inspection', 'move out', 'move in', 'walkthrough']
        }
        
        for issue_type, keywords in issue_indicators.items():
            if any(keyword in clean_transcription.lower() for keyword in keywords):
                main_issue = issue_type
                break
        
        # Extract FULL conversation sections
        # Look for natural conversation boundaries
        conversation_parts = self._split_by_speakers(clean_transcription)
        
        # Find the best complete exchange
        best_exchange = self._extract_complete_conversation_exchange(conversation_parts)
        
        exchanges = [best_exchange] if best_exchange else []
        
        # Determine resolution
        resolution = "Handled by Jamie"
        if any(word in clean_transcription.lower() for word in ["schedule", "send", "call back"]):
            resolution = "Scheduled for follow-up"
        elif any(word in clean_transcription.lower() for word in ["emergency", "asap", "today"]):
            resolution = "Emergency response initiated"
        
        return {
            'main_issue': main_issue,
            'exchanges': exchanges,
            'resolution': resolution,
            'summary': f"{main_issue} - {len(exchanges)} exchanges - {resolution}",
            'full_transcript': clean_transcription[:1000]  # Include more context
        }
    
    def _split_by_speakers(self, transcription: str) -> Dict[str, List[str]]:
        """
        Split transcription by speakers to identify full conversation sections
        """
        # Split into segments at speaker changes
        segments = []
        current_segment = ""
        
        # Split by common conversation markers
        markers = [
            "this is jamie", "jamie here", "jamie speaking",
            "hi jamie", "hey jamie", "hello jamie",
            "hello.", "hi.", "hey."
        ]
        
        # Simple approach: split on periods and group by likely speaker
        sentences = [s.strip() for s in transcription.split('.') if len(s.strip()) > 5]
        
        client_sections = []
        jamie_sections = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Strong Jamie indicators
            if any(phrase in sentence_lower for phrase in [
                "this is jamie", "jamie here", "jamie speaking",
                "i'll schedule", "i'll send", "i'll call", "i'll check",
                "let me schedule", "let me send", "let me call"
            ]):
                jamie_sections.append(sentence)
            
            # Strong client indicators
            elif any(phrase in sentence_lower for phrase in [
                "hi jamie", "hey jamie", "hello jamie", "jamie,",
                "my", "we have", "i have", "can you help", "i need"
            ]):
                client_sections.append(sentence)
            
            # Context-based classification
            elif any(word in sentence_lower for word in ["i'll", "let me", "i can", "i will"]):
                jamie_sections.append(sentence)
            elif any(word in sentence_lower for word in ["my", "our", "we", "i have", "help"]):
                client_sections.append(sentence)
        
        return {
            'client_sections': client_sections,
            'jamie_sections': jamie_sections,
            'all_sentences': sentences
        }
    
    def _extract_complete_conversation_exchange(self, conversation_parts: Dict) -> Dict:
        """
        Extract a COMPLETE conversation exchange (FULL voice conversation, no truncation)
        """
        client_sections = conversation_parts.get('client_sections', [])
        jamie_sections = conversation_parts.get('jamie_sections', [])
        
        if not client_sections or not jamie_sections:
            return None
        
        # For voice agent training, we want SUBSTANTIAL, COMPLETE exchanges
        # Find the longest, most complete client issue description
        best_client_msg = ""
        for section in client_sections:
            # Look for complete issue descriptions (longer is better for voice training)
            if len(section) > len(best_client_msg) and len(section) > 80:
                best_client_msg = section
        
        # Find the longest, most complete Jamie response
        best_jamie_msg = ""
        for section in jamie_sections:
            # Look for complete responses (longer is better for voice training)
            if len(section) > len(best_jamie_msg) and len(section) > 50:
                best_jamie_msg = section
        
        # If we don't have substantial exchanges, combine multiple sections for completeness
        if len(best_client_msg) < 100 and len(client_sections) > 1:
            # Combine multiple client sections to get the full issue description
            combined_sections = []
            total_length = 0
            for section in client_sections:
                if total_length < 300:  # Keep building until we have a complete description
                    combined_sections.append(section)
                    total_length += len(section)
            best_client_msg = ". ".join(combined_sections)
        
        if len(best_jamie_msg) < 80 and len(jamie_sections) > 1:
            # Combine multiple Jamie sections to get the full response
            combined_sections = []
            total_length = 0
            for section in jamie_sections:
                if total_length < 400:  # Keep building until we have a complete response
                    combined_sections.append(section)
                    total_length += len(section)
            best_jamie_msg = ". ".join(combined_sections)
        
        # Clean up the messages but preserve full content
        best_client_msg = best_client_msg.strip()
        best_jamie_msg = best_jamie_msg.strip()
        
        # For voice agent training, require substantial exchanges (no short fragments)
        if len(best_client_msg) > 50 and len(best_jamie_msg) > 40:
            return {
                'client_message': best_client_msg,
                'jamie_response': best_jamie_msg
            }
        
        return None
    
    def _select_best_exchange_from_conversation(self, conversation_flow: Dict) -> Dict:
        """
        Select the best client/Jamie exchange from the full conversation
        """
        exchanges = conversation_flow.get('exchanges', [])
        
        if not exchanges:
            return None
        
        # Score exchanges based on quality
        scored_exchanges = []
        
        for exchange in exchanges:
            client_msg = exchange['client_message']
            jamie_msg = exchange['jamie_response']
            
            score = 0
            
            # Length quality (substantial but not too long)
            if 30 <= len(client_msg) <= 200 and 20 <= len(jamie_msg) <= 300:
                score += 10
            
            # Content quality
            if any(word in jamie_msg.lower() for word in ["i'll", "schedule", "send", "call", "check"]):
                score += 5
            
            if any(word in client_msg.lower() for word in ["help", "problem", "issue", "need", "can you"]):
                score += 5
            
            scored_exchanges.append((score, exchange))
        
        # Return best exchange
        if scored_exchanges:
            scored_exchanges.sort(key=lambda x: x[0], reverse=True)
            return scored_exchanges[0][1]
        
        return None
    
    def create_training_examples(self, max_examples: int = 50) -> List[Dict[str, str]]:
        """
        Legacy method - now calls the full conversation example creator
        """
        return self.create_full_conversation_examples(max_examples)
    
    def export_indexed_data(self, output_path: str = None) -> str:
        """Export all indexed conversation data to JSON"""
        if output_path is None:
            output_path = os.path.join(os.getcwd(), "langchain_indexed_conversations.json")
        
        export_data = {
            'metadata': {
                'total_conversations': len(self.conversations),
                'total_threads': len(self.conversation_threads),
                'processing_date': datetime.now().isoformat(),
                'jamie_model_focus': True
            },
            'conversation_threads': self.conversation_threads,
            'patterns': self.analyze_conversation_patterns(),
            'training_examples': self.create_training_examples()
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"✅ Exported indexed conversation data to {output_path}")
        return output_path
    
    def run_full_indexing(self) -> bool:
        """Run complete conversation indexing process"""
        logger.info("🔍 Starting LangChain Conversation Indexing")
        logger.info("=" * 50)
        
        # Step 1: Load conversations
        if not self.load_conversations():
            return False
        
        # Step 2: Build conversation threads
        self.build_conversation_threads()
        
        # Step 3: Analyze patterns
        patterns = self.analyze_conversation_patterns()
        logger.info(f"📊 Found patterns:")
        logger.info(f"   Client issues: {patterns['common_client_issues']}")
        logger.info(f"   Jamie responses: {patterns['jamie_response_types']}")
        
        # Step 4: Create training examples
        examples = self.create_training_examples()
        logger.info(f"📚 Generated {len(examples)} training examples")
        
        # Step 5: Export data
        export_path = self.export_indexed_data()
        logger.info(f"💾 Data exported to: {export_path}")
        
        logger.success("🎉 Conversation indexing complete!")
        return True


if __name__ == "__main__":
    indexer = ConversationIndexer()
    indexer.run_full_indexing()