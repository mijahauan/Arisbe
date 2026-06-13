"""
In-memory session manager for **automated-Grapheus contests** (the interpretation
register played move-by-move — ``src/grapheus.py``, ``docs/AUTOMATED_GRAPHEUS.md``).

Where ``agon_session_manager`` wraps the *transformation* game (the hot-seat Dau
proof contest), this wraps the *semantic* game driven as an extensive-form play: a
live ``GrapheusContest`` (the driver, holding its descending cursor + the ``Play``
record) plus the inning's framing (M, G, regime) so a finished contest can be
interpreted and — later (increment 4) — warranted.

Contests are ephemeral, exactly like the Agon and Ergasterion sessions: they live
only while the inning is being played; nothing here touches the corpus.
"""

import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure src/ is on path (when imported from web_api/services/)
_src_dir = Path(__file__).parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from grapheus import GrapheusContest


@dataclass
class GrapheusSession:
    """A live automated-Grapheus contest plus its inning framing.

    ``setup`` records how the contest was framed (model source, regime, whether M
    was materialized) for the payload + a future warrant; ``materialization`` is the
    materialization report (when ``materialize`` was set) so the client can show the
    derived facts the Grapheus is armed with.
    """

    contest_id: str
    contest: GrapheusContest
    setup: Dict[str, Any]
    materialization: Optional[Dict[str, Any]] = None
    created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class GrapheusSessionManager:
    """Tracks active automated-Grapheus contests in memory."""

    def __init__(self) -> None:
        self._sessions: Dict[str, GrapheusSession] = {}

    def create(
        self,
        *,
        contest: GrapheusContest,
        setup: Dict[str, Any],
        materialization: Optional[Dict[str, Any]] = None,
    ) -> GrapheusSession:
        self.cleanup_expired()
        contest_id = str(uuid.uuid4())
        session = GrapheusSession(
            contest_id=contest_id,
            contest=contest,
            setup=setup,
            materialization=materialization,
        )
        self._sessions[contest_id] = session
        return session

    def get(self, contest_id: str) -> Optional[GrapheusSession]:
        session = self._sessions.get(contest_id)
        if session is not None:
            session.last_accessed = datetime.now(timezone.utc)
        return session

    def discard(self, contest_id: str) -> bool:
        if contest_id in self._sessions:
            del self._sessions[contest_id]
            return True
        return False

    def cleanup_expired(self, max_age_hours: int = 4) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        expired = [
            cid for cid, s in self._sessions.items() if s.last_accessed < cutoff
        ]
        for cid in expired:
            del self._sessions[cid]
        return len(expired)


# Module-level singleton.
_manager = GrapheusSessionManager()


def get_grapheus_session_manager() -> GrapheusSessionManager:
    """Return the global automated-Grapheus contest session manager singleton."""
    return _manager
