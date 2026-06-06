"""
Ergasterion (workshop) routes.

Ergasterion is the composition mode in the Organon / Ergasterion / Agon
trio (``docs/PRODUCT_VISION.md``, ``CLAUDE.md``).  It is the only place
in the system where the correspondence invariant flips on/off:

  * **Regime 1 (in-workshop)**: the user is composing.  Rule
    applications mutate an in-memory ``TransformationChain`` anchored
    at a chosen base state.  Each step is sound (``RuleInteraction``
    enforces preconditions) but the chain has not been asserted as a
    public, corpus-grade record.  §3.3 attestation is suspended.

  * **Regime 2 (promoted)**: the user fires ``POST .../promote`` and
    the chain anchors into the corpus context.  ``save_uod_with_chain``
    runs §3.3 attestation on the final EGI before any disk writes; a
    violation aborts cleanly and the workshop session is preserved.

A workshop session always has an explicit base state — composing
without a context is incoherent in Peircean terms (see
``docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md`` §4 and the
project-peircean-assertion-in-context memory).  V1 supports two base
sources: an empty sheet of assertion, or the current EGI of any UoD
already in the tomos corpus.

V1 scope:
  * Single-shot rule application (one HTTP call per rule, all step
    parameters at once).  Stepwise interaction protocol is exposed
    internally via ``RuleInteraction`` but not yet split across
    multiple endpoints; the route here drives the full
    begin → advance → apply sequence in one call.
  * Linear chains only (no branching / no undo).  The JSONL format
    leaves room for these later.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure src/ is on path (when imported from web_api/routes/)
_src_dir = Path(__file__).parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import FileResponse

from web_api.models.api_models import (
    ApiResponse,
    ErgasterionAdjustRequest,
    ErgasterionApplyRequest,
    ErgasterionClosureRequest,
    ErgasterionOpenRequest,
    ErgasterionPromoteRequest,
    ErgasterionSaveScratchRequest,
    ErgasterionSwitchBranchRequest,
)
from web_api.services.ergasterion_session_manager import (
    WorkshopSession,
    get_ergasterion_session_manager,
)
from web_api.services.introspection import egi_introspection
from web_api.services.scratch_store import ScratchStore
from web_api.services.layout_service import (
    attest_and_render,
    generate_layout,
    layout_dto_to_dict,
)
from web_api.services.linear_forms import linear_forms

from correspondence_attestation import CorrespondenceViolation
from layout_dto import BoundingBox, Point
from presentation_ops import (
    Regime3Violation,
    move_vertex,
    reshape_cut,
    reroute_ligature,
)
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
from universe_of_discourse import (
    UniverseOfDiscourse,
    UoDCategory,
    UoDMetadata,
    UoDType,
)


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


def _session_payload(session: WorkshopSession, svg: str) -> dict:
    """Standard response shape for any endpoint that returns a session state."""
    return {
        "session_id": session.session_id,
        "base_source": session.base_source,
        "base_source_uod_id": session.base_source_uod_id,
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
    }


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
            # If this UoD carries a worked sequence of transformations (any
            # chain — not only "proofs"), load it so the workshop opens with the
            # whole sequence navigable, not just the final graph.  The canvas
            # still opens at the tip; the user can step back through every move.
            loaded_chain = tomos.load_chain(uod_id)
            if loaded_chain is not None:
                initial_egi = loaded_chain.current_egi
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
        # before composition begins).
        dto, svg = generate_layout(initial_egi, style_name=request.style_name)

        manager = get_ergasterion_session_manager()
        session = manager.create_session(
            initial_egi=initial_egi,
            initial_layout_dto=dto,
            base_source=base,
            base_source_uod_id=base_source_uod_id,
            style_name=request.style_name,
            chain=loaded_chain,
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
async def get_session(session_id: str, style: Optional[str] = None):
    """Return the current state of a workshop session.

    Re-renders the current EGI on each call (attests §3.3 at the
    render boundary).  Useful for a fresh page load or for clients
    that lost their local state.

    An optional ``style`` query selects (and remembers, for subsequent
    renders) the visual style the workshop draws in — the first step of
    drawing-in-a-style.  Style changes the *manifest*, not the chain.
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
        dto, svg = generate_layout(session.current_egi, style_name=session.style_name)
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
async def get_session_state(session_id: str, state_id: str, style: Optional[str] = None):
    """Render any state in the session's worked sequence — the workshop's
    move-by-move navigator.

    This lets the workshop step through the whole sequence of moves (a loaded
    UoD's chain, or the one being composed), so a user can *see every graph in
    the series*, not only the last.  It is a **read** of a state already in the
    chain — it does not change the session (the cursor that decides where the
    next rule applies is tracked client-side for now); each state is laid out
    cold and §3.3-attested at the render boundary, like the Organon chain
    player (states in a sequence vary in size → fit-to-content on the client).
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
        dto, svg = generate_layout(egi, style_name=style_name)

        return ApiResponse(
            success=True,
            data={
                "session_id": session.session_id,
                "viewed_state_id": state_id,
                "step_index": _step_index_of_state(session, state_id),
                "step_count": session.step_count,
                "is_tip": state_id == session.chain.current_state_id,
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
        meta = store.save(
            session.chain,
            name=request.name,
            base_source=session.base_source,
            style_name=session.style_name,
            scratch_id=request.scratch_id,
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
        chain, meta = loaded
        style_name = style if style is not None else meta.get("style_name")
        dto, svg = generate_layout(chain.current_egi, style_name=style_name)
        manager = get_ergasterion_session_manager()
        session = manager.create_session(
            initial_egi=chain.current_egi,
            initial_layout_dto=dto,
            base_source=f"scratch:{scratch_id}",
            base_source_uod_id=None,
            style_name=style_name,
            chain=chain,
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
        if op == "move_vertex":
            if not request.vertex_id:
                return _adjust_bad_request("move_vertex requires 'vertex_id'.")
            new_dto = move_vertex(egi, dto, request.vertex_id, request.dx, request.dy)
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
        else:
            return _adjust_bad_request(f"Unknown adjust operation '{op}'.")

        new_dto, svg = attest_and_render(egi, new_dto)
        session.current_layout_dto = new_dto
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


@router.post("/sessions/{session_id}/promote")
async def promote_session(session_id: str, request: ErgasterionPromoteRequest):
    """Promote the workshop's chain into the corpus.

    This is the regime-1 → regime-2 boundary.  The chain anchors into
    the corpus context as a new PRACTICE_SESSION HISTORICAL UoD with
    the workshop's accumulated chain persisted alongside.

    Pipeline:
        1. Refuse if the target uod_id already exists in the corpus
           (we never overwrite — source UoDs are sacrosanct).
        2. Build the new UoD from the session's current EGI + the
           request's metadata.
        3. Call ``save_uod_with_chain``, which delegates to
           ``save_uod`` (firing §3.3 attestation on the final state
           BEFORE any disk writes).
        4. On a §3.3 violation, return a clean
           ``CORRESPONDENCE_VIOLATION`` error and leave the workshop
           session intact so the user can fix and retry.
        5. On success, return the promoted UoD's id and a summary.
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

        tomos = _get_tomos()
        target_uod_id = request.uod_id.strip()
        if not target_uod_id:
            return ApiResponse(
                success=False,
                error={
                    "code": "INVALID_UOD_ID",
                    "message": "uod_id is required for promotion.",
                },
            )

        if tomos.uod_exists(target_uod_id):
            return ApiResponse(
                success=False,
                error={
                    "code": "UOD_ALREADY_EXISTS",
                    "message": (
                        f"UoD '{target_uod_id}' already exists in the corpus. "
                        f"Pick a different id; promotion never overwrites."
                    ),
                },
            )

        now = datetime.now(timezone.utc)
        metadata = UoDMetadata(
            uod_id=target_uod_id,
            uod_type=UoDType.HISTORICAL,
            name=request.name or target_uod_id,
            description=request.description or "",
            category=UoDCategory.PRACTICE_SESSION,
            created=now,
            last_modified=now,
            authors=list(request.authors or []),
            tags=set(request.tags or []),
            total_states=len(session.chain.states),
            total_transformations=session.step_count,
        )
        uod = UniverseOfDiscourse(
            metadata=metadata,
            current_egi=session.current_egi,
        )

        # Promotion: §3.3 attestation fires inside save_uod_with_chain
        # → save_uod → _attest_uod_in_correspondence, BEFORE any disk
        # writes.  A violation here is the regime-1 → regime-2 refusal
        # — we surface it cleanly and leave the session untouched so
        # the user can adjust and retry.
        tomos.save_uod_with_chain(uod, session.chain)

        return ApiResponse(
            success=True,
            data={
                "session_id": session_id,
                "promoted_uod_id": target_uod_id,
                "step_count": session.step_count,
                "state_count": len(session.chain.states),
                "egi_summary": _egi_summary(session.current_egi),
            },
        )

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
                "code": "PROMOTE_ERROR",
                "message": str(exc),
                "type": type(exc).__name__,
            },
        )


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
