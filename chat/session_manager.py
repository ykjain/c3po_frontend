"""
Session Management
Handles conversation history and session lifecycle.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import threading
import time

from .config import SESSION_TIMEOUT_HOURS, MAX_HISTORY_LENGTH, CLEANUP_INTERVAL_MINUTES


class SessionManager:
    """Manages chat sessions and conversation history."""
    
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        self._cleanup_thread = None
        self._start_cleanup_thread()
    
    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new session or return existing session ID."""
        if session_id and session_id in self.sessions:
            # Update last activity
            with self._lock:
                self.sessions[session_id]['last_activity'] = datetime.now()
            return session_id
        
        # Create new session
        if not session_id:
            session_id = str(uuid.uuid4())
        
        with self._lock:
            self.sessions[session_id] = {
                'created_at': datetime.now(),
                'last_activity': datetime.now(),
                'messages': []
            }
        
        return session_id
    
    def add_message(self, session_id: str, role: str, content: str, context: Optional[Dict] = None):
        """Add a message to the session history."""
        if session_id not in self.sessions:
            self.create_session(session_id)
        
        message = {
            'role': role,
            'content': content,
            'context': context or {},
            'timestamp': datetime.now().isoformat()
        }
        
        with self._lock:
            session = self.sessions[session_id]
            session['messages'].append(message)
            session['last_activity'] = datetime.now()
            
            # Trim history if too long
            if len(session['messages']) > MAX_HISTORY_LENGTH:
                session['messages'] = session['messages'][-MAX_HISTORY_LENGTH:]
    
    def get_messages(self, session_id: str) -> List[Dict]:
        """Get all messages for a session."""
        if session_id not in self.sessions:
            return []
        
        with self._lock:
            return self.sessions[session_id]['messages'].copy()
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        """Get conversation history formatted for Claude API."""
        messages = self.get_messages(session_id)
        
        # Format for Claude API (role + content only)
        history = []
        for msg in messages:
            if msg['role'] in ['user', 'assistant']:
                history.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
        
        return history
    
    def session_exists(self, session_id: str) -> bool:
        """Check if session exists."""
        return session_id in self.sessions
    
    def update_activity(self, session_id: str):
        """Update last activity timestamp."""
        if session_id in self.sessions:
            with self._lock:
                self.sessions[session_id]['last_activity'] = datetime.now()
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions."""
        cutoff_time = datetime.now() - timedelta(hours=SESSION_TIMEOUT_HOURS)
        expired_sessions = []
        
        with self._lock:
            for session_id, session in self.sessions.items():
                if session['last_activity'] < cutoff_time:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.sessions[session_id]
        
        if expired_sessions:
            print(f"Cleaned up {len(expired_sessions)} expired chat sessions")
    
    def get_session_count(self) -> int:
        """Get total number of active sessions."""
        return len(self.sessions)
    
    def _start_cleanup_thread(self):
        """Start background thread for session cleanup."""
        def cleanup_worker():
            while True:
                time.sleep(CLEANUP_INTERVAL_MINUTES * 60)
                self.cleanup_expired_sessions()
        
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()


# Global session manager instance
session_manager = SessionManager()
