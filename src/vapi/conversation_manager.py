#!/usr/bin/env python3
"""
Conversation Manager for VAPI Integration
========================================

Manages conversation isolation, thread management, and response cleaning
to prevent multiple conversation threads and response overlap.
"""

import threading
import re
import time
import uuid
from typing import Dict, List, Optional, Any
from loguru import logger
from dataclasses import dataclass, field
from datetime import datetime, timedelta

@dataclass
class ConversationSession:
    """Represents a single conversation session"""
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    context: List[Dict[str, str]] = field(default_factory=list)
    response_buffer: List[str] = field(default_factory=list)
    is_active: bool = True
    model_name: str = ""
    max_context_length: int = 10
    lock: threading.Lock = field(default_factory=threading.Lock)

class ConversationManager:
    """Manages conversation isolation and thread management"""
    
    def __init__(self):
        self.active_conversations: Dict[str, ConversationSession] = {}
        self.session_locks: Dict[str, threading.Lock] = {}
        self.cleanup_interval = 300  # 5 minutes
        self.max_session_age = 3600  # 1 hour
        self._cleanup_thread = None
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        def cleanup_loop():
            while True:
                try:
                    self._cleanup_old_sessions()
                    time.sleep(self.cleanup_interval)
                except Exception as e:
                    logger.error(f"Cleanup thread error: {e}")
                    time.sleep(60)  # Wait 1 minute on error
        
        self._cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        self._cleanup_thread.start()
    
    def create_conversation(self, session_id: str, model_name: str = "") -> ConversationSession:
        """Create a new isolated conversation session"""
        with threading.Lock():
            if session_id in self.active_conversations:
                # Stop existing conversation
                self.stop_conversation(session_id)
            
            session = ConversationSession(
                session_id=session_id,
                model_name=model_name,
                lock=threading.Lock()
            )
            
            self.active_conversations[session_id] = session
            self.session_locks[session_id] = session.lock
            
            logger.info(f"Created conversation session: {session_id}")
            return session
    
    def get_conversation(self, session_id: str) -> Optional[ConversationSession]:
        """Get existing conversation session"""
        return self.active_conversations.get(session_id)
    
    def add_to_context(self, session_id: str, role: str, content: str):
        """Add message to conversation context"""
        session = self.get_conversation(session_id)
        if not session:
            return
        
        with session.lock:
            session.context.append({
                'role': role,
                'content': content,
                'timestamp': datetime.now()
            })
            
            # Cleanup old context if too long
            if len(session.context) > session.max_context_length:
                session.context = session.context[-session.max_context_length:]
            
            session.last_activity = datetime.now()
    
    def get_context(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation context"""
        session = self.get_conversation(session_id)
        if not session:
            return []
        
        with session.lock:
            return session.context.copy()
    
    def add_to_buffer(self, session_id: str, content: str):
        """Add content to response buffer"""
        session = self.get_conversation(session_id)
        if not session:
            return
        
        with session.lock:
            session.response_buffer.append(content)
            session.last_activity = datetime.now()
    
    def get_buffer(self, session_id: str) -> List[str]:
        """Get response buffer content"""
        session = self.get_conversation(session_id)
        if not session:
            return []
        
        with session.lock:
            return session.response_buffer.copy()
    
    def clear_buffer(self, session_id: str):
        """Clear response buffer"""
        session = self.get_conversation(session_id)
        if not session:
            return
        
        with session.lock:
            session.response_buffer.clear()
    
    def stop_conversation(self, session_id: str):
        """Stop and cleanup conversation session"""
        if session_id in self.active_conversations:
            session = self.active_conversations[session_id]
            with session.lock:
                session.is_active = False
            
            del self.active_conversations[session_id]
            if session_id in self.session_locks:
                del self.session_locks[session_id]
            
            logger.info(f"Stopped conversation session: {session_id}")
    
    def is_conversation_active(self, session_id: str) -> bool:
        """Check if conversation is active"""
        session = self.get_conversation(session_id)
        return session is not None and session.is_active
    
    def _cleanup_old_sessions(self):
        """Cleanup old inactive sessions"""
        current_time = datetime.now()
        sessions_to_remove = []
        
        for session_id, session in self.active_conversations.items():
            if not session.is_active:
                sessions_to_remove.append(session_id)
            elif current_time - session.last_activity > timedelta(seconds=self.max_session_age):
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            self.stop_conversation(session_id)
        
        if sessions_to_remove:
            logger.info(f"Cleaned up {len(sessions_to_remove)} old sessions")

class ResponseCleaner:
    """Cleans and sanitizes responses to prevent overlap and corruption"""
    
    @staticmethod
    def clean_response(response_text: str) -> str:
        """Clean response text by removing system prompts and duplicates"""
        if not response_text:
            return ""
        
        # Remove system prompts
        cleaned = ResponseCleaner._remove_system_prompts(response_text)
        
        # Remove duplicate content
        cleaned = ResponseCleaner._remove_duplicates(cleaned)
        
        # Clean up formatting
        cleaned = ResponseCleaner._clean_formatting(cleaned)
        
        return cleaned.strip()
    
    @staticmethod
    def _remove_system_prompts(text: str) -> str:
        """Remove system prompts and user/assistant prefixes"""
        patterns = [
            r'System:.*?Assistant:',
            r'User:.*?Assistant:',
            r'System important.*?Assistant:',
            r'System\. Please help.*?Assistant:',
            r'System:.*?User\?',
            r'User\? Assistant:'
        ]
        
        cleaned = text
        for pattern in patterns:
            cleaned = re.sub(pattern, 'Assistant:', cleaned, flags=re.DOTALL | re.IGNORECASE)
        
        return cleaned
    
    @staticmethod
    def _remove_duplicates(text: str) -> str:
        """Remove duplicate lines and content"""
        lines = text.split('\n')
        seen = set()
        cleaned_lines = []
        
        for line in lines:
            line_clean = line.strip()
            if line_clean and line_clean not in seen:
                seen.add(line_clean)
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    @staticmethod
    def _clean_formatting(text: str) -> str:
        """Clean up formatting issues"""
        # Remove multiple "Assistant:" prefixes
        cleaned = re.sub(r'Assistant:\s*Assistant:', 'Assistant:', text)
        cleaned = re.sub(r'Assistant:\s*Assistant\.', 'Assistant:', cleaned)
        
        # Remove trailing "●" characters
        cleaned = re.sub(r'●+$', '', cleaned)
        
        # Clean up multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned

class ThreadManager:
    """Manages thread isolation for streaming responses"""
    
    def __init__(self):
        self.active_streams: Dict[str, Dict[str, Any]] = {}
        self.stream_locks: Dict[str, threading.Lock] = {}
    
    def start_stream(self, session_id: str, model_name: str) -> bool:
        """Start a new streaming response for a session"""
        if session_id in self.active_streams:
            # Stop existing stream
            self.stop_stream(session_id)
        
        stream_lock = threading.Lock()
        self.stream_locks[session_id] = stream_lock
        
        with stream_lock:
            self.active_streams[session_id] = {
                'active': True,
                'model_name': model_name,
                'started_at': datetime.now(),
                'buffer': [],
                'completed': False
            }
            
            logger.info(f"Started stream for session: {session_id}")
            return True
    
    def stop_stream(self, session_id: str):
        """Stop streaming response for a session"""
        if session_id in self.active_streams:
            with self.stream_locks.get(session_id, threading.Lock()):
                self.active_streams[session_id]['active'] = False
                self.active_streams[session_id]['completed'] = True
            
            logger.info(f"Stopped stream for session: {session_id}")
    
    def is_stream_active(self, session_id: str) -> bool:
        """Check if stream is active for a session"""
        if session_id not in self.active_streams:
            return False
        
        with self.stream_locks.get(session_id, threading.Lock()):
            return self.active_streams[session_id]['active']
    
    def add_to_stream_buffer(self, session_id: str, content: str):
        """Add content to stream buffer"""
        if session_id not in self.active_streams:
            return
        
        with self.stream_locks.get(session_id, threading.Lock()):
            if self.active_streams[session_id]['active']:
                self.active_streams[session_id]['buffer'].append(content)
    
    def get_stream_buffer(self, session_id: str) -> List[str]:
        """Get stream buffer content"""
        if session_id not in self.active_streams:
            return []
        
        with self.stream_locks.get(session_id, threading.Lock()):
            return self.active_streams[session_id]['buffer'].copy()
    
    def clear_stream_buffer(self, session_id: str):
        """Clear stream buffer"""
        if session_id not in self.active_streams:
            return
        
        with self.stream_locks.get(session_id, threading.Lock()):
            self.active_streams[session_id]['buffer'].clear()

# Global instances
conversation_manager = ConversationManager()
thread_manager = ThreadManager()
response_cleaner = ResponseCleaner()

