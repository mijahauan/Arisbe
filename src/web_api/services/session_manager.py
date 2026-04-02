"""
In-memory session management for the Arisbe Web API.

Each session tracks the current EGI and layout DTO with undo/redo history.
Sessions expire after 1 hour of inactivity.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


@dataclass
class Session:
    """A user interaction session with an EGI diagram."""

    session_id: str
    current_egi: object  # RelationalGraphWithCuts
    current_layout_dto: object  # LayoutDTO
    history: List[Tuple[object, object]] = field(default_factory=list)
    history_index: int = -1
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    source_diagram_id: str = ""

    def can_undo(self) -> bool:
        return self.history_index > 0

    def can_redo(self) -> bool:
        return self.history_index < len(self.history) - 1


class SessionManager:
    """Manages in-memory user sessions."""

    def __init__(self):
        self._sessions: Dict[str, Session] = {}

    def create_session(
        self,
        egi: object,
        layout_dto: object,
        diagram_id: str = "",
    ) -> str:
        """Create a new session and return its ID."""
        self.cleanup_expired()
        session_id = str(uuid.uuid4())
        session = Session(
            session_id=session_id,
            current_egi=egi,
            current_layout_dto=layout_dto,
            source_diagram_id=diagram_id,
        )
        # Push initial state to history
        session.history.append((egi, layout_dto))
        session.history_index = 0
        self._sessions[session_id] = session
        return session_id

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID, updating last_accessed. Returns None if not found."""
        session = self._sessions.get(session_id)
        if session is not None:
            session.last_accessed = datetime.utcnow()
        return session

    def update_session(
        self,
        session_id: str,
        new_egi: object,
        new_layout_dto: object,
        rule: str = "",
        params: dict = None,
    ) -> bool:
        """Push a new state onto the session history. Returns False if session not found."""
        session = self.get_session(session_id)
        if session is None:
            return False

        # Truncate any redo history beyond current index
        session.history = session.history[: session.history_index + 1]

        # Push new state
        session.history.append((new_egi, new_layout_dto))
        session.history_index = len(session.history) - 1
        session.current_egi = new_egi
        session.current_layout_dto = new_layout_dto
        return True

    def undo(self, session_id: str) -> Optional[Tuple[object, object]]:
        """Move back one step in history. Returns (egi, layout_dto) or None."""
        session = self.get_session(session_id)
        if session is None or not session.can_undo():
            return None
        session.history_index -= 1
        egi, dto = session.history[session.history_index]
        session.current_egi = egi
        session.current_layout_dto = dto
        return egi, dto

    def redo(self, session_id: str) -> Optional[Tuple[object, object]]:
        """Move forward one step in history. Returns (egi, layout_dto) or None."""
        session = self.get_session(session_id)
        if session is None or not session.can_redo():
            return None
        session.history_index += 1
        egi, dto = session.history[session.history_index]
        session.current_egi = egi
        session.current_layout_dto = dto
        return egi, dto

    def cleanup_expired(self, max_age_hours: int = 1) -> int:
        """Remove sessions older than max_age_hours. Returns count removed."""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        expired = [
            sid
            for sid, session in self._sessions.items()
            if session.last_accessed < cutoff
        ]
        for sid in expired:
            del self._sessions[sid]
        return len(expired)


# Module-level singleton
_manager = SessionManager()


def get_session_manager() -> SessionManager:
    """Return the global session manager singleton."""
    return _manager
