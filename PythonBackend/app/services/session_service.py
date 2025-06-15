from typing import List, Dict, Any
from app.core.database import cassandra_conn
from app.models.cassandra_history import CassandraChatMessageHistory
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class SessionService:
    def __init__(self):
        self._history_store = {}
    
    def get_session_history_manager(self, session_id: str) -> CassandraChatMessageHistory:
        """Get or create session history manager"""
        if session_id not in self._history_store:
            self._history_store[session_id] = CassandraChatMessageHistory(
                cass_session=cassandra_conn.get_session(),
                table_name="chat_history",
                session_id=session_id,
                message_limit=10
            )
        return self._history_store[session_id]
    
    def get_session_history(self, session_id: str):
        """Get messages for a session"""
        history_manager = self.get_session_history_manager(session_id)
        return history_manager.messages
    
    def clear_session(self, session_id: str):
        """Clear session history"""
        if session_id in self._history_store:
            self._history_store[session_id].clear()
            del self._history_store[session_id]
    
    def list_active_sessions(self) -> List[str]:
        """Get list of active sessions"""
        return list(self._history_store.keys())
    
    def export_session(self, session_id: str) -> Dict[str, Any]:
        """Export session data"""
        messages = self.get_session_history(session_id)
        return {
            "session_id": session_id,
            "exported_at": datetime.utcnow().isoformat(),
            "message_count": len(messages),
            "messages": [
                {
                    "type": msg.type,
                    "content": msg.content,
                    "timestamp": datetime.utcnow().isoformat()  # Add proper timestamp
                }
                for msg in messages
            ]
        }

# Singleton instance
session_service = SessionService()