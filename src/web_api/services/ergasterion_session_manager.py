"""
In-memory session manager for the Ergasterion workshop.

An Ergasterion session is a *Peircean reasoning chain in progress*:
a base state (the context against which moves are made) plus an
ordered, growing chain of rule applications.  Until promoted to the
corpus, the chain is regime-1 — drawn but not asserted as a public
record — and the §3.3 correspondence invariant is suspended.  At
promotion the chain anchors into the corpus context and attestation
fires.

This manager is intentionally separate from
``session_manager.SessionManager`` (used by the legacy transformations
route): that manager tracks a flat ``(egi, layout_dto)`` undo/redo
history with no notion of rule provenance, while Ergasterion tracks a
typed chain whose every step names the rule that produced it.
"""

import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

# Ensure src/ is on path (when imported from web_api/services/)
_src_dir = Path(__file__).parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from egi_core_dau import RelationalGraphWithCuts
from layout_dto import LayoutDTO
from tomos_service import ChainStep, TransformationChain


@dataclass
class WorkshopSession:
    """An in-progress Ergasterion workshop session.

    The chain holds the entire reasoning episode (base state +
    accumulated steps).  ``current_layout_dto`` is the last computed
    layout for the chain's current state — kept to anchor positions on
    re-layout after the next rule application.
    """

    session_id: str
    chain: TransformationChain
    current_layout_dto: LayoutDTO
    base_source: str  # "empty_sheet" or "uod:<uod_id>"
    base_source_uod_id: Optional[str] = None
    created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def current_egi(self) -> RelationalGraphWithCuts:
        return self.chain.current_egi

    @property
    def step_count(self) -> int:
        return len(self.chain.steps)


class ErgasterionSessionManager:
    """Tracks active workshop sessions in memory.

    Sessions are ephemeral: they exist only as long as the user is
    actively composing.  Promotion writes the chain to the corpus and
    leaves the session intact (so the user can continue working post-
    promotion if they want); discard removes it entirely.
    """

    def __init__(self) -> None:
        self._sessions: Dict[str, WorkshopSession] = {}

    def create_session(
        self,
        *,
        initial_egi: RelationalGraphWithCuts,
        initial_layout_dto: LayoutDTO,
        base_source: str,
        base_source_uod_id: Optional[str] = None,
    ) -> WorkshopSession:
        """Open a new workshop session anchored at the given base state.

        The base state IS the Peircean context against which subsequent
        rule applications will get their force.  A workshop without an
        explicit base state would be incoherent (no context), so this
        method requires one.
        """
        self.cleanup_expired()

        session_id = str(uuid.uuid4())
        initial_state_id = f"state-{uuid.uuid4().hex[:8]}"

        chain = TransformationChain(
            initial_state_id=initial_state_id,
            steps=[],
            states={initial_state_id: initial_egi},
        )

        session = WorkshopSession(
            session_id=session_id,
            chain=chain,
            current_layout_dto=initial_layout_dto,
            base_source=base_source,
            base_source_uod_id=base_source_uod_id,
        )
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[WorkshopSession]:
        """Get a session by id, refreshing its last-accessed timestamp."""
        session = self._sessions.get(session_id)
        if session is not None:
            session.last_accessed = datetime.now(timezone.utc)
        return session

    def append_step(
        self,
        session_id: str,
        *,
        rule_name: str,
        parameters: Dict,
        result_egi: RelationalGraphWithCuts,
        new_layout_dto: LayoutDTO,
        user_annotation: Optional[str] = None,
    ) -> Optional[WorkshopSession]:
        """Append a successful rule application to the session's chain.

        Returns the updated session, or ``None`` if the session is not
        found.  Caller is responsible for having already validated and
        applied the rule via ``RuleInteraction``; this method only
        records the resulting step and advances the in-memory chain.
        """
        session = self.get_session(session_id)
        if session is None:
            return None

        from_state_id = session.chain.current_state_id
        to_state_id = f"state-{uuid.uuid4().hex[:8]}"

        step = ChainStep(
            step_id=f"step-{uuid.uuid4().hex[:8]}",
            rule_name=rule_name,
            from_state_id=from_state_id,
            to_state_id=to_state_id,
            parameters=parameters,
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_annotation=user_annotation,
        )

        # Build a new chain with the appended step.  ``states`` grows
        # by one (the new to_state); ``initial_state_id`` is preserved.
        new_states = dict(session.chain.states)
        new_states[to_state_id] = result_egi
        new_chain = TransformationChain(
            initial_state_id=session.chain.initial_state_id,
            steps=session.chain.steps + [step],
            states=new_states,
        )

        session.chain = new_chain
        session.current_layout_dto = new_layout_dto
        return session

    def discard_session(self, session_id: str) -> bool:
        """Remove a session entirely.  Returns False if not found."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def cleanup_expired(self, max_age_hours: int = 4) -> int:
        """Drop sessions older than ``max_age_hours``.  Returns count removed.

        Workshop sessions get a longer default lifetime than the
        legacy transformations sessions — composition is a slower,
        more deliberate activity than transient diagram exploration.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        expired = [
            sid for sid, s in self._sessions.items() if s.last_accessed < cutoff
        ]
        for sid in expired:
            del self._sessions[sid]
        return len(expired)


# Module-level singleton.
_manager = ErgasterionSessionManager()


def get_ergasterion_session_manager() -> ErgasterionSessionManager:
    """Return the global Ergasterion session manager singleton."""
    return _manager
