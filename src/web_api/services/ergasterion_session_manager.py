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

from composition_ops import FIX_CHAIN_STEP, FIX_GRAPH_STEP
from definitions import DefinitionRegistry
from egi_core_dau import RelationalGraphWithCuts
from layout_dto import LayoutDTO
from tomos_service import ChainStep, TransformationChain
from presentation_deltas import PresentationDelta, merge_inherited


def state_ancestry(chain: TransformationChain, state_id: str) -> List[str]:
    """Ordered state ids from the initial state down to ``state_id`` (inclusive),
    following the chain's step links backward.

    The basis for delta inheritance: a state's effective regime-3 deltas accrue
    along this path.  Returns ``[state_id]`` for the initial state (or an orphan
    with no parent link).  Cycle-guarded, though a well-formed chain is a tree.
    """
    parent = {s.to_state_id: s.from_state_id for s in chain.steps}
    path = [state_id]
    seen = {state_id}
    cur = state_id
    while cur in parent:
        cur = parent[cur]
        if cur in seen:
            break
        path.append(cur)
        seen.add(cur)
    path.reverse()
    return path


def phase_at_state(session: "WorkshopSession", state_id: str) -> str:
    """The workshop phase *in effect at a given state* of the active branch:
    ``composing`` | ``deriving`` | ``sealed``.

    Phase is derivable from the chain itself (spec §4.2): the branch starts at
    the session's ``base_phase`` and each recorded gate crossing —
    ``compose.fix_graph`` (①), ``chain.fix`` (②) — advances it.  The gates
    belong to a *branch*, not the session: forking from a state before gate ①
    re-opens the clay while the fixed line stays fixed, which is why phase is
    asked per-state rather than stored as one session flag.
    """
    phase = session.base_phase
    if state_id == session.chain.initial_state_id:
        return phase
    for step in session.chain.steps:
        if step.rule_name == FIX_GRAPH_STEP:
            phase = "deriving"
        elif step.rule_name == FIX_CHAIN_STEP:
            phase = "sealed"
        if step.to_state_id == state_id:
            return phase
    return phase


@dataclass
class WorkshopSession:
    """An in-progress Ergasterion workshop session.

    The workshop is a place to *play*: every state is editable.  A session
    therefore holds not one line but a small **forest of branches** — each a
    linear ``TransformationChain`` sharing a common base state (and, where they
    diverge from a common point, sharing the prefix's ``ChainStep`` objects).
    ``active_branch`` indexes the line subsequent moves extend; ``chain`` is a
    view onto it (with a setter so existing append code keeps working).
    Backing up through a sequence and applying a move *forks* a new branch from
    that point, leaving the original line untouched.

    ``current_layout_dto`` is the last computed layout for the active line's
    current state — kept to anchor positions on re-layout after the next move.
    """

    session_id: str
    branches: List[TransformationChain]
    current_layout_dto: LayoutDTO
    base_source: str  # "empty_sheet" or "uod:<uod_id>"
    base_source_uod_id: Optional[str] = None
    active_branch: int = 0
    # The visual style the workshop draws in (Dau / Peirce / Sowa). None =
    # default. Composition is style-independent (the EGI is the same); this
    # only chooses how the current state is *drawn* — the first step toward
    # drawing-in-a-style.
    style_name: Optional[str] = None
    # The phase the active branch's *initial state* is in: "composing" for an
    # empty sheet or a reopened draft (any recorded gate crossings then advance
    # it — see phase_at_state); "deriving" for a corpus-UoD base (an asserted
    # graph is already fixed).  Spec: docs/COMPOSITION_WORKFLOW_SPEC.md §4.2.
    base_phase: str = "composing"
    # Recorded regime-3 hand-adjustments (Settle ④b), keyed by the state id they
    # were authored at.  Sparse human overrides on top of (style + base layout);
    # replayed on re-render so a nudge survives a re-layout.  Per-state keying is
    # the seed for diachronic inheritance (effective = surviving-id parent deltas
    # ⊕ authored-here).  See docs/PRESENTATION_DELTAS_AND_STYLE.md.
    presentation_deltas: Dict[str, List[PresentationDelta]] = field(default_factory=dict)
    # Session-scoped definitions the user has authored from selections (the
    # abstraction layer — `definitions.definition_from_selection`).  Held in
    # memory for the session's life so a folded spot can be unfolded later and
    # the same name reused.  Ephemeral like the session itself.
    definition_registry: DefinitionRegistry = field(default_factory=DefinitionRegistry)
    created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def chain(self) -> TransformationChain:
        """The active line — the one subsequent moves extend."""
        return self.branches[self.active_branch]

    @chain.setter
    def chain(self, value: TransformationChain) -> None:
        self.branches[self.active_branch] = value

    @property
    def current_egi(self) -> RelationalGraphWithCuts:
        return self.chain.current_egi

    @property
    def phase(self) -> str:
        """The phase at the active branch's tip."""
        return phase_at_state(self, self.chain.current_state_id)

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
        style_name: Optional[str] = None,
        chain: Optional[TransformationChain] = None,
        presentation_deltas: Optional[Dict[str, List[PresentationDelta]]] = None,
        base_phase: str = "composing",
    ) -> WorkshopSession:
        """Open a new workshop session anchored at the given base state.

        The base state IS the Peircean context against which subsequent
        rule applications will get their force.  A workshop without an
        explicit base state would be incoherent (no context), so this
        method requires one.

        If *chain* is given, the session opens with that whole sequence of
        moves already in hand — the workshop loads an existing UoD's worked
        sequence so the user can navigate (and, later, branch from) any state,
        not just see the final one.  ``initial_egi`` / ``initial_layout_dto``
        then describe the state the canvas opens *at* (the chain's tip).  When
        *chain* is ``None`` the session starts as a fresh single-state chain at
        ``initial_egi`` (composition from scratch).
        """
        self.cleanup_expired()

        session_id = str(uuid.uuid4())

        if chain is None:
            initial_state_id = f"state-{uuid.uuid4().hex[:8]}"
            chain = TransformationChain(
                initial_state_id=initial_state_id,
                steps=[],
                states={initial_state_id: initial_egi},
            )

        session = WorkshopSession(
            session_id=session_id,
            branches=[chain],
            current_layout_dto=initial_layout_dto,
            base_source=base_source,
            base_source_uod_id=base_source_uod_id,
            style_name=style_name,
            base_phase=base_phase,
            presentation_deltas=presentation_deltas or {},
        )
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[WorkshopSession]:
        """Get a session by id, refreshing its last-accessed timestamp."""
        session = self._sessions.get(session_id)
        if session is not None:
            session.last_accessed = datetime.now(timezone.utc)
        return session

    @staticmethod
    def effective_deltas(
        session: WorkshopSession, state_id: str
    ) -> List[PresentationDelta]:
        """The regime-3 deltas *in effect* when drawing ``state_id`` — the
        state's own authored deltas plus those inherited from its ancestors
        (survivor elements), resolved by ``merge_inherited``.

        Used by the cold-render paths (GET session/state, reopen): a nudge made
        at an early state stays applied as the worked sequence advances, until
        the survivor is removed (then replay drops it) or re-adjusted (then the
        later authorship supersedes).  The apply path keeps using
        ``previous_layout`` pinning, which already carries the nudge forward, so
        inheritance is not layered on top of it (that would double the offset).
        """
        order = state_ancestry(session.chain, state_id)
        return merge_inherited(order, session.presentation_deltas)

    def add_step(
        self,
        session_id: str,
        *,
        rule_name: str,
        parameters: Dict,
        result_egi: RelationalGraphWithCuts,
        new_layout_dto: LayoutDTO,
        from_state_id: Optional[str] = None,
        user_annotation: Optional[str] = None,
    ) -> Optional[WorkshopSession]:
        """Record a successful rule application, extending or **forking** a line.

        ``from_state_id`` is the state the move was applied *from*:
          * ``None`` or the active line's tip → the move **extends** the active
            line (the common case).
          * an earlier state on the active line → the move **forks a new
            branch** from that point (the original line is left intact, and the
            new branch becomes active).  The shared prefix reuses the original's
            ``ChainStep`` objects, so branches that diverge from a common point
            share that history.

        Returns the updated session, ``None`` if the session is missing, or
        raises ``ValueError`` if ``from_state_id`` is not a state on the active
        line.  Caller is responsible for having already validated + applied the
        rule via ``RuleInteraction``; this only records the resulting step.
        """
        session = self.get_session(session_id)
        if session is None:
            return None

        active = session.chain
        if from_state_id is None:
            from_state_id = active.current_state_id

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

        if from_state_id == active.current_state_id:
            # Extend the active line.
            new_states = dict(active.states)
            new_states[to_state_id] = result_egi
            session.chain = TransformationChain(
                initial_state_id=active.initial_state_id,
                steps=active.steps + [step],
                states=new_states,
            )
        else:
            # Fork a new branch from from_state_id: keep the active line's
            # prefix up to (and including) that state, then add this step.
            prefix: List[ChainStep] = []
            if from_state_id != active.initial_state_id:
                found = False
                for s in active.steps:
                    prefix.append(s)
                    if s.to_state_id == from_state_id:
                        found = True
                        break
                if not found:
                    raise ValueError(
                        f"Cannot fork: state '{from_state_id}' is not on the "
                        f"active branch."
                    )
            new_steps = prefix + [step]
            needed = {active.initial_state_id}
            for s in prefix:
                needed.add(s.from_state_id)
                needed.add(s.to_state_id)
            new_states = {
                sid: active.states[sid] for sid in needed if sid in active.states
            }
            new_states[to_state_id] = result_egi
            session.branches.append(
                TransformationChain(
                    initial_state_id=active.initial_state_id,
                    steps=new_steps,
                    states=new_states,
                )
            )
            session.active_branch = len(session.branches) - 1

        session.current_layout_dto = new_layout_dto
        return session

    def update_composing_state(
        self,
        session_id: str,
        *,
        result_egi: RelationalGraphWithCuts,
        new_layout_dto: LayoutDTO,
        from_state_id: Optional[str] = None,
    ) -> Optional[WorkshopSession]:
        """Mutate the **single synchronic graph** of the composing phase in place.

        Composition is not a chain: placing, arranging, and removing elements
        just change the configuration of one graph that will become the fixed
        utterance, and the *order* of those edits carries no logical meaning, so
        nothing is recorded as a step (spec §2.3).  This replaces the live graph
        rather than appending a ``ChainStep`` — the recorded, diachronic chain
        begins only at gate ① (fix-graph).

        Behaviour:
          * the active branch's base, with no steps yet (a clay draft) → the base
            EGI is replaced in place; still ``steps == []``;
          * an earlier state of a branch that has since been fixed (re-opening the
            clay before gate ①) → a fresh single-state composing draft is forked
            and made active.

        Returns the updated session, or ``None`` if the session is missing.
        """
        session = self.get_session(session_id)
        if session is None:
            return None

        active = session.chain
        if from_state_id is None:
            from_state_id = active.current_state_id

        pure_clay = from_state_id == active.initial_state_id and not active.steps
        if pure_clay:
            # Replace the live graph; the synchronic object simply changes.
            session.chain = TransformationChain(
                initial_state_id=active.initial_state_id,
                steps=[],
                states={active.initial_state_id: result_egi},
            )
        else:
            # Re-opening the clay from before a fixing: a fresh composing draft.
            new_id = f"state-{uuid.uuid4().hex[:8]}"
            session.branches.append(
                TransformationChain(
                    initial_state_id=new_id,
                    steps=[],
                    states={new_id: result_egi},
                )
            )
            session.active_branch = len(session.branches) - 1

        session.current_layout_dto = new_layout_dto
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
        """Extend the active line at its tip (back-compat shim over add_step)."""
        return self.add_step(
            session_id,
            rule_name=rule_name,
            parameters=parameters,
            result_egi=result_egi,
            new_layout_dto=new_layout_dto,
            from_state_id=None,
            user_annotation=user_annotation,
        )

    def switch_branch(
        self, session_id: str, branch_index: int
    ) -> Optional[WorkshopSession]:
        """Make ``branch_index`` the active line.  Returns ``None`` if the
        session is missing; raises ``IndexError`` for an out-of-range index."""
        session = self.get_session(session_id)
        if session is None:
            return None
        if not (0 <= branch_index < len(session.branches)):
            raise IndexError(
                f"Branch {branch_index} out of range "
                f"(0..{len(session.branches) - 1})."
            )
        session.active_branch = branch_index
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
