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
    # The state to apply the move *from*.  Ergasterion is a workshop: every
    # state is editable.  Omitted (or the active line's tip) → the move extends
    # the active line.  An earlier state → the move **forks a new branch** from
    # there, leaving the original line intact.
    from_state_id: Optional[str] = None


class ErgasterionComposeRequest(BaseModel):
    """One palette action in a session's *composing* phase (regime 1).

    ``action`` names a ``composition_ops`` op (with or without the
    ``compose.`` namespace): ``add_cut``, ``add_line``, ``add_relation``,
    ``add_constant``, ``attach``, ``detach``, ``rename``, ``erase``,
    ``move_to_area``, ``graft``.  ``parameters`` is the op's keyword dict
    (see ``src/composition_ops.py``); the recorded chain step persists the
    parameters *with generated ids filled in*, so the step replays exactly.

    Like ``/apply``, an earlier ``from_state_id`` forks a new branch — and
    because the gates belong to a branch, forking from before gate ① re-opens
    the clay.
    """

    action: str
    parameters: Dict[str, Any] = {}
    user_annotation: Optional[str] = None
    from_state_id: Optional[str] = None


class ErgasterionFixRequest(BaseModel):
    """Cross a workshop gate: ① fix the graph (composing → deriving) or
    ② fix the chain (deriving → sealed).  Both fixings are themselves
    recorded chain steps, so the whole episode — including its own
    gate-crossings — replays."""

    user_annotation: Optional[str] = None


class ErgasterionDrawingRequest(BaseModel):
    """A freeform drawing posted from the composing-phase canvas.

    Composition is *draw-then-read*: while composing, marks are ink with no live
    EGI (docs/FREEFORM_COMPOSITION_AND_LEARNING.md, build step 2).  The browser
    owns the ink and posts the whole drawing — to ``read-drawing`` for a non-
    mutating "what does it say" preview, or to ``fix-drawing`` to cross gate ①
    (read it into the fixed EGI).  ``drawing`` is::

        {
          "sheet_id": "sheet",                                  # optional
          "vertices":   [{"id", "x", "y", "label"?}],           # label⇒constant
          "predicates": [{"id", "x", "y", "label"}],            # the relation name
          "cuts":       [{"id", "boundary": [[x, y], …]}],      # closed polyline
          "lines":      [{"predicate_id", "vertex_id",
                          "points": [[x, y], …],
                          "port_index"?, "order_label"?}]       # ν carrier
        }

    The geometry is read into structure (``eg_reader``) and the labels supply the
    content (``drawing_to_egi``); validity is checked first (``drawing_validity``).
    """

    drawing: Dict[str, Any]
    user_annotation: Optional[str] = None
    from_state_id: Optional[str] = None


class ErgasterionSwitchBranchRequest(BaseModel):
    """Make a different workshop branch the active one (its tip becomes the
    state subsequent moves extend)."""

    branch_index: int


class ErgasterionSaveScratchRequest(BaseModel):
    """Save the session's active line as a workshop draft (regime-1 scratch).

    ``scratch_id`` overwrites an existing draft (save-in-place); omit it to
    create a new one."""

    name: str
    scratch_id: Optional[str] = None


class ErgasterionAdjustRequest(BaseModel):
    """Manual Settle ④b: a regime-3 presentation touch-up on a session's layout.

    Pure appearance — the EGI is untouched, no chain step is recorded.  The
    server applies the named ``presentation_ops`` operation to the session's
    current LayoutDTO and re-renders.  A boundary-crossing nudge is refused
    (``Regime3Violation``).  Fields are operation-specific:

        move_vertex      → ``vertex_id``, ``dx``, ``dy``
        move_predicate   → ``predicate_id``, ``dx``, ``dy``
        reshape_cut      → ``cut_id``, ``bounds`` {min_x, min_y, max_x, max_y}
        move_cut         → ``cut_id``, ``dx``, ``dy``
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
    ``GET /export/formats``; ``style_name`` selects the visual style and
    ``engine`` the layout engine for drawn formats (svg / tikz / png / pdf),
    so an export reproduces exactly what the viewer is showing.
    """

    format: str
    uod_id: Optional[str] = None
    text: Optional[str] = None
    notation: str = "egif"
    style_name: Optional[str] = None
    engine: str = "elk"
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
