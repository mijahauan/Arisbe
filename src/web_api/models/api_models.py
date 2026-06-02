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
