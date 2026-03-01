"""
Session Manager — Manages user sessions, conversation history, and state.
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from config.settings import settings


@dataclass
class SessionState:
    """State of an active session."""
    session_id: str
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    mode: str = "auto"  # "dev", "user", "auto"
    target_url: str = ""
    pages_visited: list[str] = field(default_factory=list)
    conversation_history: list[dict] = field(default_factory=list)
    analysis_cache: dict[str, Any] = field(default_factory=dict)
    user_preferences: dict[str, Any] = field(default_factory=dict)
    app_context: dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.last_activity) > settings.session_timeout

    def touch(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = time.time()

    def add_page(self, url: str) -> None:
        """Track a visited page."""
        if not self.pages_visited or self.pages_visited[-1] != url:
            self.pages_visited.append(url)

    def add_message(self, role: str, content: str, metadata: dict = None) -> None:
        """Add a message to conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": time.time(),
            "metadata": metadata or {},
        })

    def cache_analysis(self, key: str, data: Any) -> None:
        """Cache analysis results for this session."""
        self.analysis_cache[key] = {
            "data": data,
            "timestamp": time.time(),
        }

    def get_cached(self, key: str, max_age: int = 300) -> Optional[Any]:
        """Get cached analysis result if not too old."""
        cached = self.analysis_cache.get(key)
        if not cached:
            return None
        if (time.time() - cached["timestamp"]) > max_age:
            del self.analysis_cache[key]
            return None
        return cached["data"]

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "mode": self.mode,
            "target_url": self.target_url,
            "pages_visited": self.pages_visited,
            "message_count": len(self.conversation_history),
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "is_expired": self.is_expired,
            "has_app_context": bool(self.app_context),
        }


class SessionManager:
    """Manages active sessions and their lifecycle."""

    def __init__(self):
        self._sessions: dict[str, SessionState] = {}

    def create_session(
        self,
        target_url: str = "",
        mode: str = "auto",
        session_id: Optional[str] = None,
    ) -> SessionState:
        """Create a new session."""
        # Enforce max sessions
        self._cleanup_expired()
        if len(self._sessions) >= settings.max_sessions:
            self._evict_oldest()

        sid = session_id or str(uuid.uuid4())
        session = SessionState(
            session_id=sid,
            target_url=target_url or settings.target_url,
            mode=mode,
        )
        self._sessions[sid] = session
        return session

    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Get a session by ID, returns None if expired or not found."""
        session = self._sessions.get(session_id)
        if not session:
            return None
        if session.is_expired:
            self.destroy_session(session_id)
            return None
        session.touch()
        return session

    def get_or_create(
        self, session_id: Optional[str] = None, target_url: str = ""
    ) -> SessionState:
        """Get existing session or create new one."""
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session
        return self.create_session(target_url=target_url, session_id=session_id)

    def destroy_session(self, session_id: str) -> bool:
        """Destroy a session."""
        return self._sessions.pop(session_id, None) is not None

    def list_sessions(self) -> list[dict]:
        """List all active (non-expired) sessions."""
        self._cleanup_expired()
        return [s.to_dict() for s in self._sessions.values()]

    def get_session_count(self) -> int:
        """Get the number of active sessions."""
        self._cleanup_expired()
        return len(self._sessions)

    def _cleanup_expired(self) -> int:
        """Remove expired sessions. Returns count removed."""
        expired = [sid for sid, s in self._sessions.items() if s.is_expired]
        for sid in expired:
            del self._sessions[sid]
        return len(expired)

    def _evict_oldest(self) -> None:
        """Remove the oldest session to make room."""
        if not self._sessions:
            return
        oldest_sid = min(
            self._sessions, key=lambda sid: self._sessions[sid].last_activity
        )
        del self._sessions[oldest_sid]
