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
    ErgasterionApplyRequest,
    ErgasterionOpenRequest,
    ErgasterionPromoteRequest,
)
from web_api.services.ergasterion_session_manager import (
    WorkshopSession,
    get_ergasterion_session_manager,
)
from web_api.services.introspection import egi_introspection
from web_api.services.layout_service import generate_layout, layout_dto_to_dict
from web_api.services.linear_forms import linear_forms

from correspondence_attestation import CorrespondenceViolation
from egif_parser_dau import parse_egif
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
VIEWER_DIR = Path(__file__).parent.parent.parent / "web_viewer"

_tomos_service: Optional[TomosService] = None


def _get_tomos() -> TomosService:
    global _tomos_service
    if _tomos_service is None:
        _tomos_service = TomosService(TOMOS_PATH)
    return _tomos_service


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
        dto, svg = generate_layout(initial_egi)

        manager = get_ergasterion_session_manager()
        session = manager.create_session(
            initial_egi=initial_egi,
            initial_layout_dto=dto,
            base_source=base,
            base_source_uod_id=base_source_uod_id,
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
async def get_session(session_id: str):
    """Return the current state of a workshop session.

    Re-renders the current EGI on each call (attests §3.3 at the
    render boundary).  Useful for a fresh page load or for clients
    that lost their local state.
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

        dto, svg = generate_layout(session.current_egi)
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

        state = begin_interaction(rule, session.current_egi)

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
        new_dto, svg = generate_layout(new_egi, previous_layout=previous_layout)

        manager.append_step(
            session_id,
            rule_name=rule,
            parameters=parameters,
            result_egi=new_egi,
            new_layout_dto=new_dto,
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
