"""
PeteOllama V1 - Pete Database Manager
=====================================

Simple SQLite interface for accessing training data from pete.db
"""

import sqlite3
import os
from typing import Dict, List, Optional, Any
from pathlib import Path

class PeteDBManager:
    """Manages access to pete.db training database"""
    
    def __init__(self, db_path: str = None):
        """Initialize database manager"""
        if db_path is None:
            # Allow PETE_DB_PATH env override for flexible deployments
            env_path = os.getenv("PETE_DB_PATH")
            if env_path:
                self.db_path = Path(env_path)
            else:
                # Default to pete.db in app root (RunPod volume mount)
                self.db_path = Path("/app/pete.db")
        else:
            self.db_path = Path(db_path)
        
        self._connection = None
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection (create if needed)"""
        if self._connection is None:
            self._connection = sqlite3.connect(str(self.db_path))
            self._connection.row_factory = sqlite3.Row  # Enable dict-like access
        return self._connection
    
    def is_connected(self) -> bool:
        """Check if database is accessible"""
        try:
            if not self.db_path.exists():
                return False
            
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
            cursor.fetchone()
            return True
        except Exception:
            return False
    
    def get_training_stats(self) -> Dict[str, Any]:
        """Get training data statistics"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get total conversations
            cursor.execute("SELECT COUNT(*) as total FROM communication_logs")
            total = cursor.fetchone()['total']
            
            # Get average duration (estimate from data length)
            cursor.execute("""
                SELECT AVG(LENGTH(Transcription)) as avg_length 
                FROM communication_logs 
                WHERE Transcription IS NOT NULL
            """)
            avg_length = cursor.fetchone()['avg_length'] or 0
            estimated_duration = int(avg_length / 20)  # Rough estimate: 20 chars per second
            
            # Get date range
            cursor.execute("""
                SELECT 
                    MIN(CreationDate) as min_date,
                    MAX(CreationDate) as max_date
                FROM communication_logs
            """)
            dates = cursor.fetchone()
            date_range = f"{dates['min_date']} to {dates['max_date']}" if dates['min_date'] else "No data"
            
            return {
                'total': total,
                'avg_duration': estimated_duration,
                'date_range': date_range
            }
        
        except Exception as e:
            print(f"Error getting training stats: {e}")
            return {
                'total': 0,
                'avg_duration': 0,
                'date_range': 'Error loading'
            }
    
    def get_sample_conversations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get sample conversations for display"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    CreationDate,
                    Data,
                    Transcription,
                    Incoming
                FROM communication_logs 
                WHERE Transcription IS NOT NULL 
                ORDER BY CreationDate DESC 
                LIMIT ?
            """, (limit,))
            
            conversations = []
            for row in cursor.fetchall():
                # Create preview (first 100 characters)
                preview = (row['Transcription'] or '')[:100]
                if len(preview) == 100:
                    preview += "..."
                
                conversations.append({
                    'date': row['CreationDate'][:10] if row['CreationDate'] else 'Unknown',
                    'duration': len(row['Transcription']) // 20 if row['Transcription'] else 0,
                    'type': 'Incoming' if row['Incoming'] else 'Outgoing',
                    'preview': preview
                })
            
            return conversations
        
        except Exception as e:
            print(f"Error getting sample conversations: {e}")
            return []
    
    def get_conversation_by_id(self, conv_id: int) -> Optional[Dict[str, Any]]:
        """Get full conversation details"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM communication_logs WHERE id = ?
            """, (conv_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        
        except Exception as e:
            print(f"Error getting conversation {conv_id}: {e}")
            return None
    
    def search_conversations(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search conversations by transcript content"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    id,
                    CreationDate,
                    Transcription,
                    Incoming
                FROM communication_logs 
                WHERE Transcription LIKE ? 
                ORDER BY CreationDate DESC 
                LIMIT ?
            """, (f"%{query}%", limit))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row['id'],
                    'date': row['CreationDate'],
                    'type': 'Incoming' if row['Incoming'] else 'Outgoing',
                    'transcript': row['Transcription']
                })
            
            return results
        
        except Exception as e:
            print(f"Error searching conversations: {e}")
            return []
    
    def get_training_examples(self, category: str = None) -> List[Dict[str, str]]:
        """Get training examples for model fine-tuning"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Get conversations with good transcriptions
            cursor.execute("""
                SELECT Transcription, Data
                FROM communication_logs 
                WHERE Transcription IS NOT NULL 
                AND LENGTH(Transcription) > 50
                ORDER BY CreationDate DESC
            """)
            
            examples = []
            for row in cursor.fetchall():
                examples.append({
                    'input': row['Transcription'],
                    'context': row['Data'] or '',
                    'category': 'property_management'
                })
            
            return examples
        
        except Exception as e:
            print(f"Error getting training examples: {e}")
            return []
    
    def close(self):
        """Close database connection"""
        if self._connection:
            self._connection.close()
            self._connection = None