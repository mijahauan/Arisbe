"""
Ergasterion (workshop) routes.

Ergasterion is the composition mode in the Organon / Ergasterion / Agon
trio (``docs/PRODUCT_VISION.md``, ``CLAUDE.md``).  It is where a user
*plays*: composes new graphs, or copies any graph from Organon and
transforms / branches it.  Everything here is **regime-1** — drawn but
not asserted.  Rule applications mutate an in-memory
``TransformationChain`` anchored at a chosen base state; each step is
sound (``RuleInteraction`` enforces preconditions) but the chain is not a
public, corpus-grade record, so §3.3 attestation is suspended.

**Leaving the workshop (the mode contract).**  §3.3 attests
*correspondence, not truth*, so it is necessary but not sufficient to
assert a graph into the corpus.  A graph reaches the corpus only by being
a **style-only reprojection** of an already-attested graph, or by being
**tested through Agon** (the dialogical challenge that earns regime-2).
Workshop output therefore goes to **scratch** (a regime-1 holding pen,
``/scratch/`` — ``web_api/services/scratch_store.py``) or is **sent to
Agon**; there is no direct workshop→corpus route.  (See memory
project-mode-contract-ergasterion-output.)

A workshop session always has an explicit base state — composing
without a context is incoherent in Peircean terms (see
``docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md`` §4 and the
project-peircean-assertion-in-context memory).  Base sources: an empty
sheet of assertion, the current EGI of any UoD already in the corpus
(with its worked sequence loaded if it has one), or a saved scratch draft.

V1 scope:
  * Single-shot rule application (one HTTP call per rule, all step
    parameters at once).  Stepwise interaction protocol is exposed
    internally via ``RuleInteraction`` but not yet split across
    multiple endpoints; the route here drives the full
    begin → advance → apply sequence in one call.
  * A session holds a small **forest of branches** (back up + apply →
    fork); navigation steps through any state in the active line.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure src/ is on path (when imported from web_api/routes/)
_src_dir = Path(__file__).parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

from web_api.models.api_models import (
    ApiResponse,
    ChallengeGradeRequest,
    ErgasterionAdjustRequest,
    ErgasterionApplyRequest,
    ErgasterionClosureRequest,
    ErgasterionComposeRequest,
    ErgasterionDefineFoldRequest,
    ErgasterionDefineUnfoldRequest,
    ErgasterionDrawingRequest,
    ErgasterionFixRequest,
    ErgasterionOpenRequest,
    ErgasterionSaveScratchRequest,
    ErgasterionSwitchBranchRequest,
)
from web_api.services.ergasterion_session_manager import (
    WorkshopSession,
    get_ergasterion_session_manager,
    phase_at_state,
    state_ancestry,
)
from web_api.services.introspection import egi_introspection
from web_api.services.scratch_store import ScratchStore
from web_api.services.layout_service import (
    attest_and_render,
    generate_layout,
    layout_dto_to_dict,
    reanchor_ligatures,
)
from web_api.services.linear_forms import linear_forms

from composition_ops import (
    COMPOSE_STEP_PREFIX,
    FIX_CHAIN_STEP,
    FIX_GRAPH_STEP,
    apply_compose,
)
from correspondence_attestation import CorrespondenceViolation
from challenge_mode import get_challenge, grade, list_challenges
from definitions import (
    DefinitionRegistry,
    definition_from_selection,
    expand_at,
    fold_selection,
)
from drawing_to_egi import build_egi_from_drawing
from drawing_validity import validate_drawing
from layout_dto import BoundingBox, LayoutDTO, LigaturePath, Point
from presentation_ops import (
    Regime3Violation,
    move_vertex,
    move_predicate,
    reshape_cut,
    move_cut,
    reroute_ligature,
)
from presentation_deltas import record_delta, deltas_from_list, merge_inherited
from presentation_ops import cut_boundary, resolve_cut_boundaries
from style_loader import load_default_style, load_style
from eg_reader import assign_order_labels
from egif_parser_dau import parse_egif
from subgraph_closure_validator import SubgraphClosureValidator
from rule_interaction import (
    StepKind,
    advance_interaction,
    apply_interaction,
    begin_interaction,
    get_interaction,
)
from tomos_service import TomosService


router = APIRouter(prefix="/ergasterion")

TOMOS_PATH = Path("/Users/mjh/Sync/GitHub/Arisbe/tomos")
SCRATCH_PATH = Path("/Users/mjh/Sync/GitHub/Arisbe/scratch")
VIEWER_DIR = Path(__file__).parent.parent.parent / "web_viewer"

_tomos_service: Optional[TomosService] = None
_scratch_store: Optional[ScratchStore] = None


def _get_tomos() -> TomosService:
    global _tomos_service
    if _tomos_service is None:
        _tomos_service = TomosService(TOMOS_PATH)
    return _tomos_service


def get_scratch_store() -> ScratchStore:
    global _scratch_store
    if _scratch_store is None:
        _scratch_store = ScratchStore(SCRATCH_PATH)
    return _scratch_store


def _egi_summary(egi) -> dict:
    return {
        "vertex_count": len(egi.V),
        "edge_count": len(egi.E),
        "cut_count": len(egi.Cut),
    }


def _chain_summary(session: WorkshopSession) -> dict:
    """Lightweight view of the chain for the UI's step-list panel."""
    return {
        "initial_state_id": session.chain.initial_state_id,
        "current_state_id": session.chain.current_state_id,
        "step_count": session.step_count,
        "steps": [
            {
                "step_id": s.step_id,
                "rule_name": s.rule_name,
                "from_state_id": s.from_state_id,
                "to_state_id": s.to_state_id,
                "timestamp": s.timestamp,
                "user_annotation": s.user_annotation,
            }
            for s in session.chain.steps
        ],
    }


def _branches_summary(session: WorkshopSession) -> dict:
    """The workshop's forest of branches, for the branch switcher.

    Each branch is a line the user has explored; the active one is what
    subsequent moves extend.  A single-branch session is the common case (no
    forking yet).
    """
    return {
        "active_branch": session.active_branch,
        "count": len(session.branches),
        "branches": [
            {
                "index": i,
                "step_count": len(b.steps),
                "tip_rule": b.steps[-1].rule_name if b.steps else None,
                "active": i == session.active_branch,
            }
            for i, b in enumerate(session.branches)
        ],
    }


def _definitions_summary(session: WorkshopSession) -> dict:
    """Session-authored definitions + which current-state edges are defined
    spots — so the client can list abstractions and offer "unfold" on a spot."""
    names = session.definition_registry.names()
    nameset = set(names)
    egi = session.current_egi
    spots = [
        {"edge_id": eid, "name": rel}
        for eid, rel in egi.rel.items()
        if rel in nameset
    ]
    return {"names": names, "spots": spots}


def _session_payload(session: WorkshopSession, svg: str) -> dict:
    """Standard response shape for any endpoint that returns a session state."""
    return {
        "session_id": session.session_id,
        "base_source": session.base_source,
        "base_source_uod_id": session.base_source_uod_id,
        # Which act the user is performing at the active branch's tip:
        # composing (regime-1 clay) | deriving (the six rules) | sealed
        # (read-only).  The UI's phase banner hangs off this.
        "phase": session.phase,
        "svg": svg,
        "layout_dto": layout_dto_to_dict(session.current_layout_dto),
        "egi_summary": _egi_summary(session.current_egi),
        # Per-element area membership + per-area polarity, so a client can
        # tell *where* each element lives and *what polarity* it has without
        # inferring it from geometry.  Unblocks selecting elements for any
        # rule beyond empty-DC+ (dogfood friction #1).
        "introspection": egi_introspection(session.current_egi),
        # Linear form(s) of the current state, beside its drawing — EGIF
        # default, CGIF/CLIF selectable (the picture and the proposition,
        # shown together).
        "linear_forms": linear_forms(session.current_egi),
        "chain": _chain_summary(session),
        "branches": _branches_summary(session),
        # Session-authored definitions (the abstraction layer) + which current
        # spots are unfoldable.
        "definitions": _definitions_summary(session),
        # Recorded regime-3 hand-adjustments for the current state (Settle ④b) —
        # the sparse human overrides that a re-render replays over the base
        # layout.  Tagged with each target's structural description.
        "presentation_deltas": [
            d.to_dict()
            for d in session.presentation_deltas.get(session.chain.current_state_id, [])
        ],
    }


def _phase_refusal(message: str, *, phase: str) -> JSONResponse:
    """An out-of-phase action — explicit 409 (spec §4.3) so the gate is
    unmistakable, with the same body shape as ApiResponse for the client."""
    return JSONResponse(
        status_code=409,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "PHASE_REFUSED",
                "message": message,
                "phase": phase,
            },
        },
    )


# --------------------------------------------------------------------------- #
# HTML viewer                                                                 #
# --------------------------------------------------------------------------- #


@router.get("", include_in_schema=False)
@router.get("/", include_in_schema=False)
async def ergasterion_index():
    """Serve the Ergasterion workshop HTML page."""
    return FileResponse(str(VIEWER_DIR / "ergasterion.html"))


# --------------------------------------------------------------------------- #
# Session lifecycle                                                           #
# --------------------------------------------------------------------------- #


@router.post("/sessions")
async def open_session(request: ErgasterionOpenRequest):
    """Open a new workshop session at an explicit base state.

    ``base_source`` selects the context to compose against:
      * ``"empty_sheet"`` — start from an empty graph (the most
        primitive Peircean context, the empty universe).
      * ``"uod:<uod_id>"`` — start from the current EGI of an existing
        corpus UoD.  The source UoD is never modified by workshop
        activity; we copy its current EGI as our base state.

    The base state's drawing is rendered through ``layout_service``,
    which attests §3.3 — so opening a workshop confirms the *base
    state* is in correspondence even though subsequent regime-1 draft
    states won't be (until promotion).
    """
    try:
        base = request.base_source.strip()
        base_source_uod_id: Optional[str] = None
        loaded_chain = None
        loaded_deltas: dict = {}
        # Picking a base state IS picking a phase: an empty sheet is clay
        # (composing); a corpus UoD's EGI is already a fixed graph, so the
        # workshop opens deriving against it (spec §4.2).
        base_phase = "composing"

        if base == "empty_sheet":
            initial_egi = parse_egif("")
        elif base.startswith("uod:"):
            uod_id = base[len("uod:"):]
            tomos = _get_tomos()
            uod = tomos.load_uod(uod_id)
            if uod is None or uod.current_egi is None:
                return ApiResponse(
                    success=False,
                    error={
                        "code": "UOD_NOT_FOUND",
                        "message": (
                            f"Cannot open workshop: UoD '{uod_id}' not found "
                            f"or has no current EGI."
                        ),
                    },
                )
            initial_egi = uod.current_egi
            base_source_uod_id = uod_id
            base_phase = "deriving"
            # If this UoD carries a worked sequence of transformations (any
            # chain — not only "proofs"), load it so the workshop opens with the
            # whole sequence navigable, not just the final graph.  The canvas
            # still opens at the tip; the user can step back through every move.
            loaded_chain = tomos.load_chain(uod_id)
            if loaded_chain is not None:
                initial_egi = loaded_chain.current_egi
                # A chain that carries compose steps (or gate ①) began as
                # clay — hydrate from "composing" so the recorded gates land
                # each state's phase where it actually was.
                if any(
                    s.rule_name.startswith(COMPOSE_STEP_PREFIX)
                    for s in loaded_chain.steps
                ):
                    base_phase = "composing"
                # Restore any regime-3 hand-adjustments persisted with the chain
                # so the UoD reopens in the workshop looking as it was saved.
                loaded_deltas = {
                    sid: deltas_from_list(items)
                    for sid, items in tomos.load_chain_deltas(uod_id).items()
                }
        else:
            return ApiResponse(
                success=False,
                error={
                    "code": "INVALID_BASE_SOURCE",
                    "message": (
                        f"base_source must be 'empty_sheet' or 'uod:<id>'; "
                        f"got '{request.base_source}'."
                    ),
                },
            )

        # Render and lay out the base state (attests §3.3 at the
        # render boundary — confirming the *base* is in correspondence
        # before composition begins).  Replay the tip's effective deltas so a
        # UoD that carried hand-adjustments reopens looking as it was saved.
        tip_deltas = None
        if loaded_chain is not None and loaded_deltas:
            tip_deltas = merge_inherited(
                state_ancestry(loaded_chain, loaded_chain.current_state_id),
                loaded_deltas,
            )
        dto, svg = generate_layout(
            initial_egi, style_name=request.style_name, deltas=tip_deltas
        )

        manager = get_ergasterion_session_manager()
        session = manager.create_session(
            initial_egi=initial_egi,
            initial_layout_dto=dto,
            base_source=base,
            base_source_uod_id=base_source_uod_id,
            style_name=request.style_name,
            chain=loaded_chain,
            presentation_deltas=loaded_deltas,
            base_phase=base_phase,
        )

        return ApiResponse(success=True, data=_session_payload(session, svg))

    except CorrespondenceViolation as exc:
        # A §3.3 violation here means even the base state failed
        # render-time attestation — corpus drift or layout bug.  Surface
        # it cleanly rather than 500.
        return ApiResponse(
            success=False,
            error={
                "code": "CORRESPONDENCE_VIOLATION",
                "message": str(exc),
                "context": getattr(exc, "context", None),
            },
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={
                "code": "OPEN_ERROR",
                "message": str(exc),
                "type": type(exc).__name__,
            },
        )


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str, style: Optional[str] = None, extrapolate: bool = False,
    direction: Optional[str] = None, tension: bool = False, engine: str = "elk",
):
    """Return the current state of a workshop session.

    Re-renders the current EGI on each call (attests §3.3 at the
    render boundary).  Useful for a fresh page load or for clients
    that lost their local state.

    An optional ``style`` query selects (and remembers, for subsequent
    renders) the visual style the workshop draws in — the first step of
    drawing-in-a-style.  Style changes the *manifest*, not the chain.

    An optional ``extrapolate=true`` query turns on extrapolation scale 1
    (within-view): the state's sparse ``move_vertex`` nudges are generalized to
    untouched structural siblings before rendering.  Off by default — a research
    view that never mutates the stored deltas (it only changes this render).
    """
    try:
        manager = get_ergasterion_session_manager()
        session = manager.get_session(session_id)
        if session is None:
            return ApiResponse(
                success=False,
                error={
                    "code": "SESSION_NOT_FOUND",
                    "message": f"Workshop session '{session_id}' not found.",
                },
            )

        if style is not None:
            session.style_name = style or None
        # Replay the current state's *effective* regime-3 nudges (its own plus
        # those inherited from ancestor states' survivors) over the freshly built
        # base, so hand-adjustments survive this full re-layout and stay
        # consistent down the worked sequence; non-applying deltas drop.
        deltas = manager.effective_deltas(session, session.chain.current_state_id)
        dto, svg = generate_layout(
            session.current_egi, style_name=session.style_name, deltas=deltas,
            extrapolate=extrapolate, direction=direction, tension=tension,
            engine=engine,
        )
        session.current_layout_dto = dto
        return ApiResponse(success=True, data=_session_payload(session, svg))
    except CorrespondenceViolation as exc:
        return ApiResponse(
            success=False,
            error={"code": "CORRESPONDENCE_VIOLATION", "message": str(exc)},
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "GET_SESSION_ERROR", "message": str(exc)},
        )


def _step_index_of_state(session, state_id: str) -> int:
    """0 for the initial state; k for the state produced by the k-th step."""
    if state_id == session.chain.initial_state_id:
        return 0
    for i, s in enumerate(session.chain.steps):
        if s.to_state_id == state_id:
            return i + 1
    return -1


@router.get("/sessions/{session_id}/states/{state_id}")
async def get_session_state(
    session_id: str, state_id: str, style: Optional[str] = None,
    extrapolate: bool = False, direction: Optional[str] = None,
    tension: bool = False, engine: str = "elk",
):
    """Render any state in the session's worked sequence — the workshop's
    move-by-move navigator.

    This lets the workshop step through the whole sequence of moves (a loaded
    UoD's chain, or the one being composed), so a user can *see every graph in
    the series*, not only the last.  It is a **read** of a state already in the
    chain — it does not change the session (the cursor that decides where the
    next rule applies is tracked client-side for now); each state is laid out
    cold and §3.3-attested at the render boundary, like the Organon chain
    player (states in a sequence vary in size → fit-to-content on the client).

    ``extrapolate=true`` (opt-in) generalizes this state's effective nudges to
    its untouched structural siblings — including the **new** elements a step
    introduced that never had a delta (the scale-1→2 bridge): extrapolation
    iterates *this* state's EGI, so a fresh element matching an inherited
    intent's structural class picks it up.  A research view; stored deltas are
    untouched.
    """
    try:
        manager = get_ergasterion_session_manager()
        session = manager.get_session(session_id)
        if session is None:
            return ApiResponse(
                success=False,
                error={
                    "code": "SESSION_NOT_FOUND",
                    "message": f"Workshop session '{session_id}' not found.",
                },
            )

        egi = session.chain.states.get(state_id)
        if egi is None:
            return ApiResponse(
                success=False,
                error={
                    "code": "STATE_NOT_FOUND",
                    "message": (
                        f"State '{state_id}' is not part of session "
                        f"'{session_id}'."
                    ),
                },
            )

        style_name = style if style is not None else session.style_name
        # Replay this state's *effective* nudges (its own + inherited from
        # ancestor survivors), so stepping the navigator shows each frame the
        # way it was hand-adjusted, consistently down the sequence.
        dto, svg = generate_layout(
            egi, style_name=style_name,
            deltas=manager.effective_deltas(session, state_id),
            extrapolate=extrapolate, direction=direction, tension=tension,
            engine=engine,
        )

        return ApiResponse(
            success=True,
            data={
                "session_id": session.session_id,
                "viewed_state_id": state_id,
                "step_index": _step_index_of_state(session, state_id),
                "step_count": session.step_count,
                "is_tip": state_id == session.chain.current_state_id,
                # The phase *at this state* (gates are recorded steps, so an
                # earlier state may still be clay) — the banner tracks it.
                "phase": phase_at_state(session, state_id),
                "svg": svg,
                "layout_dto": layout_dto_to_dict(dto),
                "egi_summary": _egi_summary(egi),
                "introspection": egi_introspection(egi),
                "linear_forms": linear_forms(egi),
            },
        )
    except CorrespondenceViolation as exc:
        return ApiResponse(
            success=False,
            error={"code": "CORRESPONDENCE_VIOLATION", "message": str(exc)},
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "GET_STATE_ERROR", "message": str(exc)},
        )


@router.post("/sessions/{session_id}/branches/switch")
async def switch_branch(session_id: str, request: ErgasterionSwitchBranchRequest):
    """Make a different workshop branch the active line.

    Subsequent moves then extend the chosen branch.  Pure in-memory bookkeeping
    — no §3.3 here (regime-1 work); the canvas re-renders the newly-active
    line's tip.
    """
    try:
        manager = get_ergasterion_session_manager()
        session = manager.get_session(session_id)
        if session is None:
            return ApiResponse(
                success=False,
                error={
                    "code": "SESSION_NOT_FOUND",
                    "message": f"Workshop session '{session_id}' not found.",
                },
            )
        try:
            session = manager.switch_branch(session_id, request.branch_index)
        except IndexError as exc:
            return ApiResponse(
                success=False,
                error={"code": "BRANCH_NOT_FOUND", "message": str(exc)},
            )
        dto, svg = generate_layout(
            session.current_egi, style_name=session.style_name
        )
        session.current_layout_dto = dto
        return ApiResponse(success=True, data=_session_payload(session, svg))
    except CorrespondenceViolation as exc:
        return ApiResponse(
            success=False,
            error={"code": "CORRESPONDENCE_VIOLATION", "message": str(exc)},
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "SWITCH_BRANCH_ERROR", "message": str(exc)},
        )


@router.post("/sessions/{session_id}/save-to-scratch")
async def save_to_scratch(session_id: str, request: ErgasterionSaveScratchRequest):
    """Save the session's active line to the workshop **scratch** store.

    Scratch is a regime-1 holding pen — fragments and incomplete attempts the
    user wants to return to.  It is deliberately **not the corpus**: saving here
    asserts nothing and runs no §3.3 gate (a draft need not even be in
    correspondence yet).  A new graph reaches the attested corpus only as a
    style-only reprojection of an attested graph, or by being tested in Agon.
    """
    try:
        manager = get_ergasterion_session_manager()
        session = manager.get_session(session_id)
        if session is None:
            return ApiResponse(
                success=False,
                error={
                    "code": "SESSION_NOT_FOUND",
                    "message": f"Workshop session '{session_id}' not found.",
                },
            )
        store = get_scratch_store()
        # Serialize the active line's per-state regime-3 deltas to travel with
        # the draft, restricted to states this branch actually contains.
        line_states = set(session.chain.states.keys())
        serialized_deltas = {
            sid: [d.to_dict() for d in deltas]
            for sid, deltas in session.presentation_deltas.items()
            if sid in line_states and deltas
        }
        meta = store.save(
            session.chain,
            name=request.name,
            base_source=session.base_source,
            style_name=session.style_name,
            scratch_id=request.scratch_id,
            presentation_deltas=serialized_deltas,
        )
        return ApiResponse(success=True, data=meta)
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "SAVE_SCRATCH_ERROR", "message": str(exc)},
        )


@router.get("/scratch")
async def list_scratch():
    """List the workshop's saved drafts (newest first)."""
    try:
        store = get_scratch_store()
        return ApiResponse(success=True, data={"drafts": store.list()})
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "LIST_SCRATCH_ERROR", "message": str(exc)},
        )


@router.post("/scratch/{scratch_id}/open")
async def open_scratch(scratch_id: str, style: Optional[str] = None):
    """Reopen a saved draft as a fresh workshop session (with its whole line
    navigable, just like opening a corpus UoD that carries a sequence)."""
    try:
        store = get_scratch_store()
        loaded = store.load(scratch_id)
        if loaded is None:
            return ApiResponse(
                success=False,
                error={
                    "code": "SCRATCH_NOT_FOUND",
                    "message": f"Draft '{scratch_id}' not found or unreadable.",
                },
            )
        chain, meta, raw_deltas = loaded
        style_name = style if style is not None else meta.get("style_name")
        # Rehydrate the per-state regime-3 deltas the draft carried, and replay
        # the tip state's over its fresh base so the draft reopens *looking* the
        # way it was saved.
        deltas = {
            sid: deltas_from_list(items) for sid, items in raw_deltas.items()
        }
        tip_deltas = merge_inherited(
            state_ancestry(chain, chain.current_state_id), deltas
        )
        dto, svg = generate_layout(
            chain.current_egi, style_name=style_name, deltas=tip_deltas
        )
        manager = get_ergasterion_session_manager()
        session = manager.create_session(
            initial_egi=chain.current_egi,
            initial_layout_dto=dto,
            base_source=f"scratch:{scratch_id}",
            base_source_uod_id=None,
            style_name=style_name,
            chain=chain,
            presentation_deltas=deltas,
            # The draft's own gate steps (recorded in its chain) advance the
            # phase from this base — phase_at_state walks them on demand.
            base_phase=(
                "deriving"
                if str(meta.get("base_source", "")).startswith("uod:")
                else "composing"
            ),
        )
        return ApiResponse(success=True, data=_session_payload(session, svg))
    except CorrespondenceViolation as exc:
        return ApiResponse(
            success=False,
            error={"code": "CORRESPONDENCE_VIOLATION", "message": str(exc)},
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "OPEN_SCRATCH_ERROR", "message": str(exc)},
        )


@router.delete("/scratch/{scratch_id}")
async def delete_scratch(scratch_id: str):
    """Delete a saved draft."""
    store = get_scratch_store()
    found = store.delete(scratch_id)
    if not found:
        return ApiResponse(
            success=False,
            error={
                "code": "SCRATCH_NOT_FOUND",
                "message": f"Draft '{scratch_id}' not found.",
            },
        )
    return ApiResponse(success=True, data={"scratch_id": scratch_id})


@router.delete("/sessions/{session_id}")
async def discard_session(session_id: str):
    """Discard a workshop session and its in-memory chain."""
    manager = get_ergasterion_session_manager()
    found = manager.discard_session(session_id)
    if not found:
        return ApiResponse(
            success=False,
            error={
                "code": "SESSION_NOT_FOUND",
                "message": f"Workshop session '{session_id}' not found.",
            },
        )
    return ApiResponse(success=True, data={"session_id": session_id})


# --------------------------------------------------------------------------- #
# Composition (regime 1) + the two fixings                                    #
# --------------------------------------------------------------------------- #


@router.post("/sessions/{session_id}/compose")
async def compose(session_id: str, request: ErgasterionComposeRequest):
    """One palette action while the clay is soft (spec §2, §4).

    Dispatches to ``composition_ops.apply_compose`` and records the result as
    a typed ``compose.<action>`` chain step whose parameters carry the
    generated ids (``recorded_parameters``), so the step replays exactly.
    Only legal while the from-state's phase is ``composing``; the well-formed
    refusals (Dau context condition, unknown ids, …) come back as
    ``COMPOSE_REFUSED`` with the op's own message.

    Like ``/apply``, ``from_state_id`` defaults to the active line's tip; an
    earlier state forks a new branch — and because gates belong to a branch,
    forking from before gate ① re-opens the clay.
    """
    try:
        manager = get_ergasterion_session_manager()
        session = manager.get_session(session_id)
        if session is None:
            return ApiResponse(
                success=False,
                error={
                    "code": "SESSION_NOT_FOUND",
                    "message": f"Workshop session '{session_id}' not found.",
                },
            )

        from_state_id = request.from_state_id or session.chain.current_state_id
        from_egi = session.chain.states.get(from_state_id)
        if from_egi is None:
            return ApiResponse(
                success=False,
                error={
                    "code": "STATE_NOT_FOUND",
                    "message": (
                        f"Cannot compose from state '{from_state_id}': not "
                        f"part of this session's active branch."
                    ),
                },
            )

        phase = phase_at_state(session, from_state_id)
        if phase != "composing":
            return _phase_refusal(
                "The graph is fixed — step back before the fixing to fork a "
                "new draft, or open a new session to compose.",
                phase=phase,
            )

        try:
            result = apply_compose(from_egi, request.action, request.parameters or {})
        except ValueError as exc:
            return ApiResponse(
                success=False,
                error={
                    "code": "COMPOSE_REFUSED",
                    "message": str(exc),
                    "action": request.action,
                },
            )

        new_dto, svg = generate_layout(
            result.egi,
            previous_layout=session.current_layout_dto,
            style_name=session.style_name,
        )

        # Composition is not a chain: the synchronic graph just changes, no step
        # is recorded, and the order of edits carries no meaning (spec §2.3).
        # The recorded chain begins only at gate ① (fix-graph).
        manager.update_composing_state(
            session_id,
            result_egi=result.egi,
            new_layout_dto=new_dto,
            from_state_id=from_state_id,
        )

        session = manager.get_session(session_id)
        payload = _session_payload(session, svg)
        # What the op minted / removed, so the UI can select the new element
        # for the next palette action without diffing the introspection block.
        payload["compose_result"] = {
            "created": result.created,
            "removed": list(result.removed),
        }
        return ApiResponse(success=True, data=payload)

    except CorrespondenceViolation as exc:
        return ApiResponse(
            success=False,
            error={
                "code": "CORRESPONDENCE_VIOLATION",
                "message": str(exc),
                "context": getattr(exc, "context", None),
            },
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={
                "code": "COMPOSE_ERROR",
                "message": str(exc),
                "type": type(exc).__name__,
            },
        )


# --------------------------------------------------------------------------- #
# Freeform composition canvas — draw-then-read (build step 2)                  #
# docs/FREEFORM_COMPOSITION_AND_LEARNING.md                                    #
# --------------------------------------------------------------------------- #


def _session_style(session: WorkshopSession):
    """The style object the freeform DTO carries (cut shape / corner radius /
    argument-order convention) — what ``read_drawing`` and ``validate_drawing``
    key off.  Mirrors the session's chosen style; default when unset."""
    name = session.style_name
    if not name:
        return load_default_style()
    try:
        return load_style(name)
    except Exception:
        return load_default_style()


def _dto_from_drawing(drawing: Dict[str, Any], style, sheet_id: str):
    """Convert a posted freeform drawing into a ``(LayoutDTO, predicate_labels,
    vertex_labels)`` triple — the ink as the reader/validator/builder consume it.

    The drawing is pure geometry + typed content (see ``ErgasterionDrawingRequest``):
    cut polylines become both ``cut_boundary`` (the literal drawn curve, tested
    point-in-polygon) and ``cut_bounds`` (its extent, for the analytic fallbacks and
    the viewport); labels ride alongside in the two label maps the EGI builder needs.
    """
    verts = drawing.get("vertices", []) or []
    preds = drawing.get("predicates", []) or []
    cuts = drawing.get("cuts", []) or []
    lines = drawing.get("lines", []) or []

    vertex_positions = {v["id"]: Point(float(v["x"]), float(v["y"])) for v in verts}
    predicate_positions = {p["id"]: Point(float(p["x"]), float(p["y"])) for p in preds}
    vertex_labels = {v["id"]: v.get("label") for v in verts}
    predicate_labels = {p["id"]: p.get("label", "?") for p in preds}

    cut_bounds: Dict[str, BoundingBox] = {}
    cut_boundary: Dict[str, tuple] = {}
    for c in cuts:
        poly = [Point(float(x), float(y)) for x, y in c["boundary"]]
        cut_boundary[c["id"]] = tuple(poly)
        xs = [pt.x for pt in poly]
        ys = [pt.y for pt in poly]
        cut_bounds[c["id"]] = BoundingBox(min(xs), min(ys), max(xs), max(ys))

    ligature_paths = []
    for ln in lines:
        pts = tuple(Point(float(x), float(y)) for x, y in ln["points"])
        ligature_paths.append(LigaturePath(
            predicate_id=ln["predicate_id"],
            vertex_id=ln["vertex_id"],
            points=pts,
            port_index=int(ln.get("port_index", 0)),
            order_label=ln.get("order_label"),
        ))

    # Viewport: the extent of everything drawn, padded; a sane default if empty.
    all_pts = (list(vertex_positions.values()) + list(predicate_positions.values())
               + [pt for poly in cut_boundary.values() for pt in poly])
    if all_pts:
        pad = 40.0
        vb = BoundingBox(
            min(p.x for p in all_pts) - pad, min(p.y for p in all_pts) - pad,
            max(p.x for p in all_pts) + pad, max(p.y for p in all_pts) + pad,
        )
    else:
        vb = BoundingBox(-200, -200, 200, 200)

    dto = LayoutDTO(
        vertex_positions=vertex_positions,
        predicate_positions=predicate_positions,
        cut_bounds=cut_bounds,
        ligature_paths=ligature_paths,
        area_hierarchy={sheet_id: set()},
        viewport_bounds=vb,
        sheet_id=sheet_id,
        style=style,
        cut_boundary=cut_boundary or None,
    )
    return dto, predicate_labels, vertex_labels


def _issues_payload(report) -> Dict[str, Any]:
    """The validity report as JSON the canvas can show in EG vocabulary."""
    return {
        "is_well_formed": report.is_well_formed,
        "errors": [
            {"code": i.code, "message": i.message, "elements": list(i.elements)}
            for i in report.errors
        ],
        "warnings": [
            {"code": i.code, "message": i.message, "elements": list(i.elements)}
            for i in report.warnings
        ],
    }


def _drawing_from_egi(egi, style, style_name) -> Dict[str, Any]:
    """Serialize an EGI as a freeform drawing — the inverse of ``_dto_from_drawing``,
    so the canvas can be **seeded** with an existing graph (re-opening a fixed base
    graph to edit its meaning, or starting from a library graph).  Renders the EGI
    to a layout, carries argument order (``assign_order_labels``), and emits the same
    shape the canvas posts back: marks with labels, cut polylines, ordered lines."""
    dto, _svg = generate_layout(egi, style_name=style_name)
    dto = assign_order_labels(egi, dto)
    boundaries = resolve_cut_boundaries(dto)
    shape = getattr(style, "cut_shape", "rounded_rectangle")
    radius = float(getattr(style, "cut_corner_radius", 0) or 0)

    v_by_id = {v.id: v for v in egi.V}
    vertices = [
        {"id": vid, "x": p.x, "y": p.y,
         "label": (v_by_id[vid].label if vid in v_by_id else None)}
        for vid, p in dto.vertex_positions.items()
    ]
    predicates = [
        {"id": pid, "x": p.x, "y": p.y, "label": egi.get_relation_name(pid)}
        for pid, p in dto.predicate_positions.items()
    ]
    cuts = []
    for cid, bounds in dto.cut_bounds.items():
        poly = boundaries.get(cid) or cut_boundary(bounds, shape, radius)
        cuts.append({"id": cid, "boundary": [[pt.x, pt.y] for pt in poly]})
    lines = [
        {"predicate_id": lp.predicate_id, "vertex_id": lp.vertex_id,
         "points": [[pt.x, pt.y] for pt in lp.points],
         "port_index": lp.port_index, "order_label": lp.order_label}
        for lp in dto.ligature_paths
    ]
    return {"sheet_id": dto.sheet_id, "vertices": vertices,
            "predicates": predicates, "cuts": cuts, "lines": lines}


@router.get("/sessions/{session_id}/state-drawing")
async def state_drawing(session_id: str, state_id: Optional[str] = None):
    """The graph at a state, serialized as a freeform drawing — to **seed** the
    canvas when re-opening a fixed base graph for editing (the Graph↔Argument
    round-trip).  Defaults to the active branch's base (initial) state, which is the
    graph that was fixed at gate ①."""
    manager = get_ergasterion_session_manager()
    session = manager.get_session(session_id)
    if session is None:
        return ApiResponse(success=False, error={
            "code": "SESSION_NOT_FOUND",
            "message": f"Workshop session '{session_id}' not found."})
    sid = state_id or session.chain.initial_state_id
    egi = session.chain.states.get(sid)
    if egi is None:
        return ApiResponse(success=False, error={
            "code": "STATE_NOT_FOUND",
            "message": f"State '{sid}' is not on the active branch."})
    drawing = _drawing_from_egi(egi, _session_style(session), session.style_name)
    return ApiResponse(success=True, data={"state_id": sid, "drawing": drawing})


@router.post("/sessions/{session_id}/read-drawing")
async def read_drawing_preview(session_id: str, request: ErgasterionDrawingRequest):
    """Read the composing-phase ink into a determinate sign — *without committing*.

    The non-mutating "what does it say" preview (the canvas's on-demand button):
    run the validity pass, and when the drawing is well-formed build the EGI it
    denotes and return its linear forms.  Composition stays silent; this is when
    the picture *speaks*, so the author is never flying blind before gate ①.
    """
    try:
        manager = get_ergasterion_session_manager()
        session = manager.get_session(session_id)
        if session is None:
            return ApiResponse(success=False, error={
                "code": "SESSION_NOT_FOUND",
                "message": f"Workshop session '{session_id}' not found."})

        style = _session_style(session)
        sheet_id = request.drawing.get("sheet_id", "sheet")
        dto, predicate_labels, vertex_labels = _dto_from_drawing(
            request.drawing, style, sheet_id)
        report = validate_drawing(
            dto, predicate_labels=predicate_labels, vertex_labels=vertex_labels)
        data: Dict[str, Any] = {"validity": _issues_payload(report)}
        if report.is_well_formed:
            egi = build_egi_from_drawing(dto, predicate_labels, vertex_labels)
            data["egi_summary"] = _egi_summary(egi)
            data["linear_forms"] = linear_forms(egi)
        return ApiResponse(success=True, data=data)
    except Exception as exc:
        return ApiResponse(success=False, error={
            "code": "READ_DRAWING_ERROR", "message": str(exc),
            "type": type(exc).__name__})


@router.post("/sessions/{session_id}/fix-drawing")
async def fix_drawing(session_id: str, request: ErgasterionDrawingRequest):
    """Gate ① for the freeform canvas — *read* the drawing into the fixed graph.

    Composing is draw-then-read: the picture becomes a determinate sign only here.
    Validate the ink (refuse, in EG vocabulary, if it isn't a well-formed EG), build
    the EGI it denotes, install it as the composing state, then cross gate ① exactly
    like the typed path (a recorded ``compose.fix_graph`` step; §3.3 attested at the
    render boundary).  From here the graph is clay no longer — only the six Dau rules
    act on it.
    """
    try:
        manager = get_ergasterion_session_manager()
        session = manager.get_session(session_id)
        if session is None:
            return ApiResponse(success=False, error={
                "code": "SESSION_NOT_FOUND",
                "message": f"Workshop session '{session_id}' not found."})

        # Fixing a *drawing* is valid from any state: the act of reading ink into a
        # graph and fixing it always yields a fixed graph.  In particular, editing a
        # graph pulled from the corpus (whose base state is 'deriving', already
        # asserted) creates an INDEPENDENT new graph — a working copy — never a
        # change to the original (there is no workshop→corpus route; the copy is
        # saved to scratch under a new name).  So there is no composing-only guard
        # here; the freeform-editing precondition is enforced client-side.
        from_state_id = request.from_state_id or session.chain.current_state_id

        style = _session_style(session)
        sheet_id = request.drawing.get("sheet_id", "sheet")
        dto, predicate_labels, vertex_labels = _dto_from_drawing(
            request.drawing, style, sheet_id)

        report = validate_drawing(
            dto, predicate_labels=predicate_labels, vertex_labels=vertex_labels)
        if not report.is_well_formed:
            return JSONResponse(status_code=400, content={
                "success": False, "data": None,
                "error": {
                    "code": "DRAWING_ILL_FORMED",
                    "message": ("The drawing is not a well-formed existential graph "
                                "yet — fix the flagged marks, then fix the graph."),
                    "validity": _issues_payload(report),
                }})

        egi = build_egi_from_drawing(dto, predicate_labels, vertex_labels)
        new_dto, _svg = generate_layout(egi, style_name=session.style_name)
        # Install the read EGI as the composing state (replaces a fresh clay draft;
        # forks a new line when editing an already-fixed/pulled graph), then record
        # gate ① directly — no phase guard, since fixing a drawing is always valid.
        manager.update_composing_state(
            session_id, result_egi=egi, new_layout_dto=new_dto,
            from_state_id=from_state_id)
        session = manager.get_session(session_id)
        tip = session.chain.current_state_id
        gate_dto, svg = generate_layout(
            session.current_egi, previous_layout=session.current_layout_dto,
            style_name=session.style_name)
        manager.add_step(
            session_id, rule_name=FIX_GRAPH_STEP, parameters={},
            result_egi=session.current_egi, new_layout_dto=gate_dto,
            from_state_id=tip, user_annotation=request.user_annotation)
        session = manager.get_session(session_id)
        resp_data = _session_payload(session, svg)
        resp_data["validity"] = _issues_payload(report)
        return ApiResponse(success=True, data=resp_data)

    except CorrespondenceViolation as exc:
        return ApiResponse(success=False, error={
            "code": "CORRESPONDENCE_VIOLATION", "message": str(exc),
            "context": getattr(exc, "context", None)})
    except Exception as exc:
        return ApiResponse(success=False, error={
            "code": "FIX_DRAWING_ERROR", "message": str(exc),
            "type": type(exc).__name__})


# --------------------------------------------------------------------------- #
# Challenge mode — correspondence, learned by doing (build step 4)             #
# docs/FREEFORM_COMPOSITION_AND_LEARNING.md                                    #
# --------------------------------------------------------------------------- #


@router.get("/challenges")
async def list_challenges_route():
    """The challenge bank: a difficulty gradient of linear forms to draw freehand.

    Returns the prompt (the linear form the learner reads and must render) but never
    a drawing — the correspondence has to be reconstructed, not copied.
    """
    return ApiResponse(success=True, data={
        "challenges": [
            {"id": c.id, "title": c.title, "prompt_egif": c.prompt_egif,
             "difficulty": c.difficulty, "hint": c.hint}
            for c in list_challenges()
        ]
    })


@router.post("/sessions/{session_id}/grade-challenge")
async def grade_challenge(session_id: str, request: ChallengeGradeRequest):
    """Grade a freehand drawing against a challenge target — non-mutating.

    Read the drawing into an EGI and compare it to the target with the legible diff.
    If the ink is not yet a well-formed EG, return the validity report instead of a
    grade (the learner fixes the marks first, in EG vocabulary); if it is well-formed
    but denotes a different graph, return ``matches=false`` with the discrepancy
    findings.  The session state is never touched.
    """
    try:
        manager = get_ergasterion_session_manager()
        session = manager.get_session(session_id)
        if session is None:
            return ApiResponse(success=False, error={
                "code": "SESSION_NOT_FOUND",
                "message": f"Workshop session '{session_id}' not found."})

        # Resolve the target: a bank challenge id, or a raw EGIF string.
        target_egif = request.target_egif
        challenge = None
        if request.challenge_id:
            challenge = get_challenge(request.challenge_id)
            if challenge is None:
                return ApiResponse(success=False, error={
                    "code": "CHALLENGE_NOT_FOUND",
                    "message": f"No challenge '{request.challenge_id}'."})
            target_egif = challenge.prompt_egif
        if not target_egif:
            return ApiResponse(success=False, error={
                "code": "NO_TARGET",
                "message": "Provide a challenge_id or a target_egif to grade against."})

        style = _session_style(session)
        sheet_id = request.drawing.get("sheet_id", "sheet")
        dto, predicate_labels, vertex_labels = _dto_from_drawing(
            request.drawing, style, sheet_id)

        # Ill-formed drawing → EG-vocabulary feedback, not a grade.
        report = validate_drawing(
            dto, predicate_labels=predicate_labels, vertex_labels=vertex_labels)
        if not report.is_well_formed:
            return ApiResponse(success=True, data={
                "gradeable": False,
                "validity": _issues_payload(report),
            })

        attempt = build_egi_from_drawing(dto, predicate_labels, vertex_labels)
        diff = grade(target_egif, attempt)
        return ApiResponse(success=True, data={
            "gradeable": True,
            "matches": diff.matches,
            "summary": diff.summary,
            "findings": [
                {"kind": f.kind, "message": f.message, "subject": f.subject}
                for f in diff.findings
            ],
            "validity": _issues_payload(report),
            "target_linear_forms": linear_forms(parse_egif(target_egif)),
        })
    except Exception as exc:
        return ApiResponse(success=False, error={
            "code": "GRADE_CHALLENGE_ERROR", "message": str(exc),
            "type": type(exc).__name__})


def _record_gate(
    session_id: str,
    *,
    rule_name: str,
    expected_phase: str,
    refusal: str,
    user_annotation: Optional[str],
):
    """Shared body of the two gate routes: a gate crossing is itself a
    recorded chain step on the active line's tip — an identity step on the
    graph that advances the *phase* (spec §4.2), so the whole episode,
    including its own fixings, replays."""
    manager = get_ergasterion_session_manager()
    session = manager.get_session(session_id)
    if session is None:
        return ApiResponse(
            success=False,
            error={
                "code": "SESSION_NOT_FOUND",
                "message": f"Workshop session '{session_id}' not found.",
            },
        )

    tip = session.chain.current_state_id
    phase = phase_at_state(session, tip)
    if phase != expected_phase:
        return _phase_refusal(refusal, phase=phase)

    dto, svg = generate_layout(
        session.current_egi,
        previous_layout=session.current_layout_dto,
        style_name=session.style_name,
    )
    manager.add_step(
        session_id,
        rule_name=rule_name,
        parameters={},
        result_egi=session.current_egi,
        new_layout_dto=dto,
        from_state_id=tip,
        user_annotation=user_annotation,
    )
    session = manager.get_session(session_id)
    return ApiResponse(success=True, data=_session_payload(session, svg))


@router.post("/sessions/{session_id}/fix-graph")
async def fix_graph(session_id: str, request: ErgasterionFixRequest):
    """Gate ① — fix the graph: composing → deriving (spec §4).

    From here the graph is no longer clay; only the six Dau rules act on it.
    Recorded as a ``compose.fix_graph`` identity step, so forking from a state
    before this step re-opens composition on the new branch.
    """
    try:
        return _record_gate(
            session_id,
            rule_name=FIX_GRAPH_STEP,
            expected_phase="composing",
            refusal=(
                "The graph is already fixed — gate ① has been crossed on "
                "this line."
            ),
            user_annotation=request.user_annotation,
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "FIX_GRAPH_ERROR", "message": str(exc),
                   "type": type(exc).__name__},
        )


@router.post("/sessions/{session_id}/fix-chain")
async def fix_chain(session_id: str, request: ErgasterionFixRequest):
    """Gate ② — fix the chain: deriving → sealed (spec §4).

    The derivation is complete; the line becomes read-only (disposition only:
    save to scratch, send to Agon).  Recorded as a ``chain.fix`` identity
    step; forking from before it re-opens derivation on the new branch.
    """
    try:
        return _record_gate(
            session_id,
            rule_name=FIX_CHAIN_STEP,
            expected_phase="deriving",
            refusal=(
                "Gate ② needs a deriving line: fix the graph first (①), "
                "or — if already sealed — fork from an earlier state."
            ),
            user_annotation=request.user_annotation,
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "FIX_CHAIN_ERROR", "message": str(exc),
                   "type": type(exc).__name__},
        )


# --------------------------------------------------------------------------- #
# Rule application                                                            #
# --------------------------------------------------------------------------- #


def _step_input_from_parameters(step_kind: StepKind, parameters: Dict[str, Any]):
    """Pick the right parameter for a given RuleInteraction step kind.

    The route accepts all of a rule's parameters in one request; this
    helper extracts the appropriate input for each declared step.
    """
    if step_kind is StepKind.SELECT_SUBGRAPH:
        return list(parameters.get("selected_elements", []))
    if step_kind is StepKind.SELECT_AREA:
        return parameters.get("target_area")
    if step_kind is StepKind.PROVIDE_EGIF:
        return parameters.get("egif_content", "")
    return None


@router.post("/sessions/{session_id}/apply")
async def apply_rule(session_id: str, request: ErgasterionApplyRequest):
    """Apply one Dau rule to the workshop session's current state.

    Drives the headless ``RuleInteraction`` protocol end-to-end:
    ``begin_interaction → advance_interaction (per declared step) →
    apply_interaction``.  On success, appends a ``ChainStep`` and
    advances the session's current state.  On failure (precondition,
    closure, isomorphism), returns the protocol's error message so
    the UI can surface a useful refusal.

    No §3.3 attestation here — this is regime-1 work.  The chain's
    soundness is attested by ``RuleInteraction`` (the rule's own
    preconditions); the correspondence invariant only re-engages at
    promotion.  We still call ``generate_layout`` on the new state
    because that's how we render it — but the attestation inside
    ``layout_service`` is checking that *this newly produced* (EGI,
    DTO) pair is in correspondence with itself, not making any claim
    about the chain's regime status.
    """
    try:
        manager = get_ergasterion_session_manager()
        session = manager.get_session(session_id)
        if session is None:
            return ApiResponse(
                success=False,
                error={
                    "code": "SESSION_NOT_FOUND",
                    "message": f"Workshop session '{session_id}' not found.",
                },
            )

        rule = request.rule
        parameters = request.parameters or {}

        try:
            interaction = get_interaction(rule)
        except ValueError as exc:
            return ApiResponse(
                success=False,
                error={"code": "UNKNOWN_RULE", "message": str(exc)},
            )

        # The move is applied *from* a chosen state.  Default = the active
        # line's tip (extend it); an earlier state means the user backed up to
        # edit, which forks a new branch (the workshop is editable everywhere).
        from_state_id = request.from_state_id or session.chain.current_state_id
        from_egi = session.chain.states.get(from_state_id)
        if from_egi is None:
            return ApiResponse(
                success=False,
                error={
                    "code": "STATE_NOT_FOUND",
                    "message": (
                        f"Cannot apply from state '{from_state_id}': not part "
                        f"of this session's active branch."
                    ),
                },
            )

        # Phase gate (spec §4.3): the six rules act on a *fixed* graph.
        phase = phase_at_state(session, from_state_id)
        if phase == "composing":
            return _phase_refusal(
                "The graph isn't fixed yet — finish composing and fix the "
                "graph (gate ①) before deriving.",
                phase=phase,
            )
        if phase == "sealed":
            return _phase_refusal(
                "This chain is fixed — step back before the fixing to fork "
                "a new line, or open a new session.",
                phase=phase,
            )

        state = begin_interaction(rule, from_egi)

        # Walk through the declared steps, feeding the matching
        # parameter into each.  ``advance_interaction`` validates the
        # input and records a StepResult on the state.
        for step in interaction.steps():
            step_input = _step_input_from_parameters(step.kind, parameters)
            step_result = advance_interaction(state, step_input)
            if not step_result.valid and not step.optional:
                return ApiResponse(
                    success=False,
                    error={
                        "code": "RULE_PRECONDITION_FAILED",
                        "message": step_result.message,
                        "step_id": step.step_id,
                        "rule": rule,
                    },
                )

        apply_result = apply_interaction(state)
        if not apply_result.success:
            return ApiResponse(
                success=False,
                error={
                    "code": "RULE_APPLY_FAILED",
                    "message": apply_result.message,
                    "rule": rule,
                },
            )

        new_egi = apply_result.result_egi
        previous_layout = session.current_layout_dto
        new_dto, svg = generate_layout(
            new_egi, previous_layout=previous_layout, style_name=session.style_name
        )

        manager.add_step(
            session_id,
            rule_name=rule,
            parameters=parameters,
            result_egi=new_egi,
            new_layout_dto=new_dto,
            from_state_id=from_state_id,
            user_annotation=request.user_annotation,
        )

        # Refresh session reference (manager mutated it in-place).
        session = manager.get_session(session_id)
        return ApiResponse(success=True, data=_session_payload(session, svg))

    except CorrespondenceViolation as exc:
        # An unexpected violation at render time within the workshop
        # — surface it loudly rather than hiding behind a generic 500.
        return ApiResponse(
            success=False,
            error={
                "code": "CORRESPONDENCE_VIOLATION",
                "message": str(exc),
                "context": getattr(exc, "context", None),
            },
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={
                "code": "APPLY_ERROR",
                "message": str(exc),
                "type": type(exc).__name__,
            },
        )


def _define_state(session, request):
    """Resolve and phase-gate the state a define-fold/unfold acts from.

    Returns ``(from_state_id, from_egi, None)`` on success, or
    ``(None, None, ApiResponse)`` carrying the refusal."""
    from_state_id = request.from_state_id or session.chain.current_state_id
    from_egi = session.chain.states.get(from_state_id)
    if from_egi is None:
        return None, None, ApiResponse(
            success=False,
            error={
                "code": "STATE_NOT_FOUND",
                "message": (
                    f"Cannot act from state '{from_state_id}': not part of this "
                    "session's active branch."
                ),
            },
        )
    phase = phase_at_state(session, from_state_id)
    if phase == "composing":
        return None, None, _phase_refusal(
            "The graph isn't fixed yet — fix the graph (gate ①) before "
            "abstracting a definition.",
            phase=phase,
        )
    if phase == "sealed":
        return None, None, _phase_refusal(
            "This chain is fixed — step back before the fixing to fork a new "
            "line, or open a new session.",
            phase=phase,
        )
    return from_state_id, from_egi, None


@router.post("/sessions/{session_id}/define-fold")
async def define_fold(session_id: str, request: ErgasterionDefineFoldRequest):
    """Author a definition from a selection and fold the selection under it.

    The **abstraction** move: name *this drawn subgraph* ``name(ports) := body``
    and replace it with a single spot.  Meaning-preserving (a conservative
    definitional abbreviation — ``docs/DEFINITION_NODE.md``), reversible via
    ``/define-unfold``, and recorded as a ``definition.fold`` chain step (an
    earlier ``from_state_id`` forks a branch).  The definition's legitimacy comes
    from its body + the two soundness gates in ``fold_selection``, not its name.
    """
    try:
        manager = get_ergasterion_session_manager()
        session = manager.get_session(session_id)
        if session is None:
            return ApiResponse(
                success=False,
                error={
                    "code": "SESSION_NOT_FOUND",
                    "message": f"Workshop session '{session_id}' not found.",
                },
            )

        from_state_id, from_egi, refusal = _define_state(session, request)
        if refusal is not None:
            return refusal

        name = request.name.strip()
        if not name:
            return ApiResponse(
                success=False,
                error={"code": "BAD_DEFINITION", "message": "A definition needs a name."},
            )
        registry = session.definition_registry
        if name in registry:
            return ApiResponse(
                success=False,
                error={
                    "code": "DEFINITION_EXISTS",
                    "message": f"A definition named '{name}' already exists in this session.",
                },
            )

        try:
            defn = definition_from_selection(
                from_egi, request.selection, request.ports, name
            )
            # Fold against a throwaway registry; only commit the definition to
            # the session on success (no half-registered name on refusal).
            folded = fold_selection(
                from_egi, DefinitionRegistry([defn]), name,
                request.selection, request.ports,
            )
        except ValueError as exc:
            return ApiResponse(
                success=False,
                error={"code": "FOLD_REFUSED", "message": str(exc)},
            )

        registry.add(defn)
        new_dto, svg = generate_layout(
            folded, previous_layout=session.current_layout_dto,
            style_name=session.style_name,
        )
        manager.add_step(
            session_id,
            rule_name="definition.fold",
            parameters={
                "name": name,
                "ports": list(request.ports),
                "selection": list(request.selection),
            },
            result_egi=folded,
            new_layout_dto=new_dto,
            from_state_id=from_state_id,
            user_annotation=request.user_annotation,
        )
        session = manager.get_session(session_id)
        return ApiResponse(success=True, data=_session_payload(session, svg))

    except CorrespondenceViolation as exc:
        return ApiResponse(
            success=False,
            error={
                "code": "CORRESPONDENCE_VIOLATION",
                "message": str(exc),
                "context": getattr(exc, "context", None),
            },
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "DEFINE_FOLD_ERROR", "message": str(exc), "type": type(exc).__name__},
        )


@router.post("/sessions/{session_id}/define-unfold")
async def define_unfold(session_id: str, request: ErgasterionDefineUnfoldRequest):
    """Unfold a defined spot back to its body — the inverse of ``/define-fold``
    (``definitions.expand_at``).  Recorded as a ``definition.unfold`` step."""
    try:
        manager = get_ergasterion_session_manager()
        session = manager.get_session(session_id)
        if session is None:
            return ApiResponse(
                success=False,
                error={
                    "code": "SESSION_NOT_FOUND",
                    "message": f"Workshop session '{session_id}' not found.",
                },
            )

        from_state_id, from_egi, refusal = _define_state(session, request)
        if refusal is not None:
            return refusal

        spot_id = request.spot_id
        rel = from_egi.rel.get(spot_id)
        registry = session.definition_registry
        if rel is None or rel not in registry:
            return ApiResponse(
                success=False,
                error={
                    "code": "NOT_A_DEFINED_SPOT",
                    "message": (
                        f"Element '{spot_id}' is not a defined spot in this "
                        "session (no session definition for it to unfold)."
                    ),
                },
            )

        try:
            unfolded = expand_at(from_egi, registry, spot_id)
        except ValueError as exc:
            return ApiResponse(
                success=False,
                error={"code": "UNFOLD_REFUSED", "message": str(exc)},
            )

        new_dto, svg = generate_layout(
            unfolded, previous_layout=session.current_layout_dto,
            style_name=session.style_name,
        )
        manager.add_step(
            session_id,
            rule_name="definition.unfold",
            parameters={"spot_id": spot_id, "name": rel},
            result_egi=unfolded,
            new_layout_dto=new_dto,
            from_state_id=from_state_id,
            user_annotation=request.user_annotation,
        )
        session = manager.get_session(session_id)
        return ApiResponse(success=True, data=_session_payload(session, svg))

    except CorrespondenceViolation as exc:
        return ApiResponse(
            success=False,
            error={
                "code": "CORRESPONDENCE_VIOLATION",
                "message": str(exc),
                "context": getattr(exc, "context", None),
            },
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "DEFINE_UNFOLD_ERROR", "message": str(exc), "type": type(exc).__name__},
        )


@router.post("/sessions/{session_id}/adjust")
async def adjust_presentation(session_id: str, request: ErgasterionAdjustRequest):
    """Settle ④b — a manual regime-3 presentation touch-up.

    The user has nudged the drawing (moved a vertex, reshaped a cut, rerouted
    a ligature) to tidy appearance after a transformation.  This is *pure
    presentation*: the EGI is untouched, no chain step is recorded, and the
    operation is logic-preserving by construction — ``presentation_ops``
    refuses any boundary-crossing nudge (``Regime3Violation``).

    The adjusted LayoutDTO is rendered directly (no ELK pass, so the nudge
    survives) and still §3.3-attested before it leaves the service — the
    runtime guarantee that the move preserved correspondence.
    """
    try:
        manager = get_ergasterion_session_manager()
        session = manager.get_session(session_id)
        if session is None:
            return ApiResponse(
                success=False,
                error={
                    "code": "SESSION_NOT_FOUND",
                    "message": f"Workshop session '{session_id}' not found.",
                },
            )

        egi = session.current_egi
        dto = session.current_layout_dto
        if dto is None:
            return ApiResponse(
                success=False,
                error={
                    "code": "NO_LAYOUT",
                    "message": "Session has no current layout to adjust. Render it first.",
                },
            )

        op = request.operation
        # Params recorded with the delta mirror what presentation_ops consumed —
        # the same shape apply_deltas replays.  Built per-op so the recorded
        # delta is self-contained (independent of this request object).
        params: dict
        if op == "move_vertex":
            if not request.vertex_id:
                return _adjust_bad_request("move_vertex requires 'vertex_id'.")
            new_dto = move_vertex(egi, dto, request.vertex_id, request.dx, request.dy)
            params = {"vertex_id": request.vertex_id, "dx": request.dx, "dy": request.dy}
        elif op == "move_predicate":
            if not request.predicate_id:
                return _adjust_bad_request("move_predicate requires 'predicate_id'.")
            new_dto = move_predicate(egi, dto, request.predicate_id, request.dx, request.dy)
            params = {"predicate_id": request.predicate_id, "dx": request.dx, "dy": request.dy}
        elif op == "move_cut":
            if not request.cut_id:
                return _adjust_bad_request("move_cut requires 'cut_id'.")
            new_dto = move_cut(egi, dto, request.cut_id, request.dx, request.dy)
            params = {"cut_id": request.cut_id, "dx": request.dx, "dy": request.dy}
        elif op == "reshape_cut":
            if not request.cut_id or not request.bounds:
                return _adjust_bad_request("reshape_cut requires 'cut_id' and 'bounds'.")
            b = request.bounds
            try:
                new_bounds = BoundingBox(
                    min_x=float(b["min_x"]), min_y=float(b["min_y"]),
                    max_x=float(b["max_x"]), max_y=float(b["max_y"]),
                )
            except (KeyError, TypeError, ValueError):
                return _adjust_bad_request(
                    "reshape_cut 'bounds' needs numeric min_x, min_y, max_x, max_y."
                )
            new_dto = reshape_cut(egi, dto, request.cut_id, new_bounds)
            params = {
                "cut_id": request.cut_id,
                "bounds": {
                    "min_x": new_bounds.min_x, "min_y": new_bounds.min_y,
                    "max_x": new_bounds.max_x, "max_y": new_bounds.max_y,
                },
            }
        elif op == "reroute_ligature":
            if not request.predicate_id or not request.vertex_id or request.interior is None:
                return _adjust_bad_request(
                    "reroute_ligature requires 'predicate_id', 'vertex_id', 'interior'."
                )
            try:
                interior = [Point(x=float(p["x"]), y=float(p["y"])) for p in request.interior]
            except (KeyError, TypeError, ValueError):
                return _adjust_bad_request("reroute_ligature 'interior' needs {x, y} points.")
            new_dto = reroute_ligature(
                egi, dto, request.predicate_id, request.vertex_id,
                request.port_index, interior,
            )
            params = {
                "predicate_id": request.predicate_id,
                "vertex_id": request.vertex_id,
                "port_index": request.port_index,
                "interior": [{"x": p.x, "y": p.y} for p in interior],
            }
        else:
            return _adjust_bad_request(f"Unknown adjust operation '{op}'.")

        # A move only translates the moved element's ligature endpoints; re-derive
        # them so the predicate attachment follows the line's new incident
        # direction (idempotent on unmoved lines; preserves an explicit reroute).
        if op in ("move_vertex", "move_predicate", "move_cut"):
            new_dto = reanchor_ligatures(egi, new_dto)

        new_dto, svg = attest_and_render(egi, new_dto)
        session.current_layout_dto = new_dto
        # Record the act as a tagged, replayable delta keyed by the current
        # state id.  Pure presentation: no chain step, EGI untouched — this is
        # the persistence seed (a re-render replays it; cf. GET /sessions/{id}).
        state_id = session.chain.current_state_id
        session.presentation_deltas.setdefault(state_id, []).append(
            record_delta(egi, op, params)
        )
        return ApiResponse(success=True, data=_session_payload(session, svg))

    except Regime3Violation as exc:
        # A boundary-crossing nudge — refused.  This is the regime-3 guarantee
        # working: appearance is free, but it may not change the logic.
        return ApiResponse(
            success=False,
            error={"code": "REGIME3_VIOLATION", "message": str(exc)},
        )
    except CorrespondenceViolation as exc:
        return ApiResponse(
            success=False,
            error={"code": "CORRESPONDENCE_VIOLATION", "message": str(exc)},
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={
                "code": "ADJUST_ERROR",
                "message": str(exc),
                "type": type(exc).__name__,
            },
        )


def _adjust_bad_request(message: str) -> ApiResponse:
    return ApiResponse(
        success=False,
        error={"code": "ADJUST_BAD_REQUEST", "message": message},
    )


@router.post("/sessions/{session_id}/closure")
async def preview_closure(session_id: str, request: ErgasterionClosureRequest):
    """Preview the closed sub-graph a Subject selection expands to.

    A rule acts on a *closed* sub-graph: selecting a cut pulls in **all its
    contents**, selecting an edge pulls in its incident vertices, etc.  This
    read-only endpoint runs ``SubgraphClosureValidator.analyze_closure`` on the
    session's current state and returns the closure plus the elements it added,
    so the workshop can show what the selection really covers *before* applying
    a rule — the "your selection closed up to …" feedback (no state change).

    (DC- is the exception the caller handles: its selected cut-pair is removed
    while the enclosed contents stay, so the UI does not treat the closure as
    the acted-on set for DC-.)
    """
    try:
        manager = get_ergasterion_session_manager()
        session = manager.get_session(session_id)
        if session is None:
            return ApiResponse(
                success=False,
                error={
                    "code": "SESSION_NOT_FOUND",
                    "message": f"Workshop session '{session_id}' not found.",
                },
            )
        selection = frozenset(request.selected_elements or [])
        validator = SubgraphClosureValidator(session.current_egi)
        analysis = validator.analyze_closure(
            selection, allow_expansion=True, for_erasure=request.for_erasure
        )
        return ApiResponse(
            success=True,
            data={
                "selection": sorted(selection),
                "closed_subgraph": sorted(analysis.closed_subgraph),
                "added_elements": sorted(analysis.added_elements),
                "is_closed": analysis.is_closed,
            },
        )
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "CLOSURE_ERROR", "message": str(exc),
                   "type": type(exc).__name__},
        )


@router.post("/sessions/{session_id}/deiteration-original")
async def deiteration_original(session_id: str, request: ErgasterionClosureRequest):
    """Find the *governing original* that licenses deiterating a candidate.

    IT- (deiteration) is the least obvious rule: a copy may be erased only
    because an identical sub-graph exists in an enclosing area.  This read-only
    endpoint runs the IT- interaction's own validation on the selection and
    returns the matched original's element ids, so the workshop can *highlight
    why* the move is legal (the Removing family's justification dialect) — no
    state change, no reimplementation of the protected rule logic.
    """
    try:
        manager = get_ergasterion_session_manager()
        session = manager.get_session(session_id)
        if session is None:
            return ApiResponse(
                success=False,
                error={"code": "SESSION_NOT_FOUND",
                       "message": f"Workshop session '{session_id}' not found."},
            )
        sel = list(request.selected_elements or [])
        if not sel:
            return ApiResponse(success=True, data={
                "found": False, "valid": False, "original_elements": [],
                "message": "Select a candidate copy first."})
        state = begin_interaction("IT-", session.current_egi)
        step_result = advance_interaction(state, sel)
        matches = (step_result.data or {}).get("original_matches") if step_result.data else None
        original = sorted(matches[0][1]) if matches else []
        return ApiResponse(success=True, data={
            "found": bool(original),
            "valid": step_result.valid,
            "original_elements": original,
            "message": step_result.message,
        })
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "DEITERATION_ORIGINAL_ERROR", "message": str(exc),
                   "type": type(exc).__name__},
        )


# --------------------------------------------------------------------------- #
# Promotion                                                                   #
# --------------------------------------------------------------------------- #


# NOTE — the direct workshop "promote to corpus" route has been **retired**
# (2026-06-06).  It forked a corpus UoD on §3.3 attestation alone, which proves
# *correspondence, not truth* — and so bypassed the mode contract: a graph
# leaves Ergasterion for the corpus only by being a style-only reprojection of
# an attested graph, or by being **tested through Agon** (the dialogical
# challenge that earns regime-2).  Workshop output now goes to **scratch**
# (regime-1, ``/scratch/``) or is **sent to Agon**.  The underlying mechanism
# survives where it belongs: Agon's asserting disposition anchors a withstood
# chain into the corpus via ``tomos_service.save_uod_with_chain`` (whose §3.3
# refusal is covered by ``tests/test_chain_persistence.py``).  See memory
# project-mode-contract-ergasterion-output.


# --------------------------------------------------------------------------- #
# Corpus browsing helper                                                      #
# --------------------------------------------------------------------------- #


@router.get("/corpus/uods")
async def list_corpus_uods():
    """Lightweight corpus listing for the base-state picker in the UI.

    This is a thin convenience wrapper around the same data the
    Organon route serves; we duplicate the endpoint under
    ``/ergasterion/`` so the workshop frontend doesn't need to know
    about the Organon route.  Both views read from the same
    ``TomosService.list_uods``.
    """
    try:
        tomos = _get_tomos()
        entries = tomos.list_uods()
        items = [
            {
                "uod_id": e.get("uod_id", ""),
                "name": e.get("name", "Untitled"),
                "category": e.get("category", ""),
            }
            for e in entries
        ]
        return ApiResponse(success=True, data=items)
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "LIST_ERROR", "message": str(exc)},
        )
