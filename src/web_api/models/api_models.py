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
