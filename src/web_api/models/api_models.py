"""
Pydantic request/response models for the Arisbe Web API.
"""

from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class ApiResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


class TransformApplyRequest(BaseModel):
    session_id: str
    rule: str  # "ERA" | "INS" | "IT+" | "IT-" | "DC+" | "DC-"
    parameters: Dict[str, Any]  # rule-specific


class TransformValidateRequest(BaseModel):
    session_id: str
    rule: str
    parameters: Dict[str, Any]


class SubgraphValidateRequest(BaseModel):
    session_id: str
    selected_elements: List[str]
    context_area: Optional[str] = None


class AreaAtPointRequest(BaseModel):
    session_id: str
    x: float
    y: float


class UndoRedoRequest(BaseModel):
    session_id: str


# --------------------------------------------------------------------------- #
# Ergasterion (workshop) requests                                             #
# --------------------------------------------------------------------------- #


class ErgasterionOpenRequest(BaseModel):
    """Open a new workshop session.

    ``base_source`` is either ``"empty_sheet"`` (start from an empty
    universe — the most primitive Peircean context) or
    ``"uod:<uod_id>"`` (compose against the current EGI of an existing
    corpus UoD).  Picking a base state IS picking a context; the
    workshop refuses to open without one.
    """

    base_source: str
    style_name: Optional[str] = None


class ErgasterionApplyRequest(BaseModel):
    """Apply one rule to the current state of a workshop session.

    Parameters are rule-specific and mirror the ``RuleInteraction``
    step inputs (see ``src/rule_interaction.py``):

        DC+ / DC- / ERA / IT-  → ``selected_elements: List[str]``
        INS                    → ``egif_content: str``, ``target_area: str``
        IT+                    → ``selected_elements: List[str]``,
                                  ``target_area: str`` (the destination)
    """

    rule: str
    parameters: Dict[str, Any]
    user_annotation: Optional[str] = None


class ErgasterionAdjustRequest(BaseModel):
    """Manual Settle ④b: a regime-3 presentation touch-up on a session's layout.

    Pure appearance — the EGI is untouched, no chain step is recorded.  The
    server applies the named ``presentation_ops`` operation to the session's
    current LayoutDTO and re-renders.  A boundary-crossing nudge is refused
    (``Regime3Violation``).  Fields are operation-specific:

        move_vertex      → ``vertex_id``, ``dx``, ``dy``
        reshape_cut      → ``cut_id``, ``bounds`` {min_x, min_y, max_x, max_y}
        reroute_ligature → ``predicate_id``, ``vertex_id``, ``port_index``,
                           ``interior`` [{x, y}, …]
    """

    operation: str
    vertex_id: Optional[str] = None
    cut_id: Optional[str] = None
    predicate_id: Optional[str] = None
    port_index: int = 0
    dx: float = 0.0
    dy: float = 0.0
    bounds: Optional[Dict[str, float]] = None
    interior: Optional[List[Dict[str, float]]] = None


class ErgasterionClosureRequest(BaseModel):
    """Preview the closed sub-graph a selection expands to (read-only).

    A selection is acted on as a *closed* sub-graph: selecting a cut pulls in
    all its contents, selecting an edge pulls in its incident vertices, etc.
    This lets the workshop show what a selection really covers before applying
    a rule.  ``for_erasure`` tightens the closure for ERA/IT- (a selected
    vertex requires every edge referencing it).
    """

    selected_elements: List[str]
    for_erasure: bool = False


class ExportRequest(BaseModel):
    """Export an EGI in a chosen format and style.

    The source is either a corpus UoD (``uod_id``) or an inline linear
    form (``text`` + ``notation``).  ``format`` is one of the keys from
    ``GET /export/formats``; ``style_name`` selects the visual style for
    drawn formats (svg / tikz / png / pdf), defaulting to dau-compliant.
    """

    format: str
    uod_id: Optional[str] = None
    text: Optional[str] = None
    notation: str = "egif"
    style_name: Optional[str] = None
    standalone: bool = True


class IntrospectRequest(BaseModel):
    """Introspect a graph's area/polarity + content for selection.

    The source is either a corpus UoD (``uod_id``) or an inline linear
    form (``text`` + ``notation``).  Read-only: returns the
    ``egi_introspection`` block (areas + elements with relation/label/
    incidence) and makes no §3.3 claim.
    """

    uod_id: Optional[str] = None
    text: Optional[str] = None
    notation: str = "egif"


class ImportCheckRequest(BaseModel):
    """Inspect a linear form without persisting it.

    ``notation`` is ``"egif"`` (default), ``"cgif"``, or ``"clif"``.
    Returns parse / round-trip / §3.3 results and a rendering, so the
    importer can confirm the drawing matches what they meant.
    """

    text: str
    notation: str = "egif"


class FormatCitationRequest(BaseModel):
    """Live-preview a formatted citation from a structured record."""

    record: Dict[str, Any]


class ImportAdmitRequest(BaseModel):
    """Admit a linear form into the corpus as a low-warrant import.

    Creates a standalone ``LITERATURE_EXAMPLE`` UoD attributed from the
    structured (CSL-compatible) ``bibliography`` record.  §3.3 fires at
    the corpus boundary; never overwrites an existing id.
    """

    text: str
    notation: str = "egif"
    bibliography: Dict[str, Any]
    uod_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class AgonNewGameRequest(BaseModel):
    """Start an Endoporeutic Game contest.

    The contest is framed in one of three ways (checked in this order):

      * ``initial_egif`` — a raw starting graph (the Agonothetes has
        already constructed the interpretive frame).
      * ``model_egif`` + ``proposal_egif`` — build the canonical frame
        ``~[ M ~[ G ] ]`` (= M → G) from a domain model M and proposal G.
      * ``base_source = "uod:<id>"`` + ``proposal_egif`` — take M from a
        corpus UoD's current EGI and frame the proposal against it.

    ``goal_egif`` is the engine's (proxy) win target; ``first_player`` is
    ``"Proposer"`` (Graphist) or ``"Skeptic"`` (Grapheus).  V1 is
    hot-seat: one user drives both roles.
    """

    initial_egif: Optional[str] = None
    model_egif: Optional[str] = None
    proposal_egif: Optional[str] = None
    base_source: Optional[str] = None
    goal_egif: Optional[str] = None
    first_player: Optional[str] = "Proposer"


class AgonMoveRequest(BaseModel):
    """One move in a contest.

    ``parameters`` mirrors the Ergasterion / ``/rules`` shape:
    ``selected_elements: List[str]``, ``target_area: str``,
    ``egif_content: str`` (for INS).  The engine enforces territory and
    polarity by the current player's role.
    """

    rule: str
    parameters: Dict[str, Any] = {}


class AgonDispositionRequest(BaseModel):
    """The Agonothetes' post-contest judgment (open taxonomy choice).

    ``disposition`` is a key from the outcome taxonomy (see
    ``web_api.services.agonothetes.DISPOSITIONS``).  An *asserting*
    disposition writes a corpus record and requires ``target_uod_id``;
    a non-asserting one is recorded on the episode only.  Nothing
    auto-asserts — this is reached only by explicit choice.
    """

    disposition: str
    target_uod_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    authors: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class ErgasterionPromoteRequest(BaseModel):
    """Promote the workshop's chain into the corpus.

    Promotion creates a NEW UoD (PRACTICE_SESSION category, HISTORICAL
    type) and writes both the final EGI and the full chain via
    ``TomosService.save_uod_with_chain``.  §3.3 attestation fires on
    the final state; a violation aborts the save with no half-written
    artefacts.  The source UoD (if any) is never overwritten.
    """

    uod_id: str
    name: str
    description: Optional[str] = ""
    authors: Optional[List[str]] = None
    tags: Optional[List[str]] = None
