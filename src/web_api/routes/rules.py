"""
Rule-requirements route — what does each Dau rule need as input?

The dogfood (memory ``project-ergasterion-dogfood-findings``, #2)
found that although ``RuleInteraction.steps()`` already declares each
rule's required inputs (the headless protocol's step descriptors),
they were not discoverable over HTTP — a client had to read the source
to know that INS is two-step (content + negative target) while DC- is
a single subgraph selection.

This route is **mode-independent** — Ergasterion and Agon both drive
the same six rules through the same ``RuleInteraction`` protocol, so
the descriptor lives at ``/rules`` rather than under any one mode.

Each step descriptor carries the request *field name* a client should
populate, derived from the same ``StepKind → parameter`` mapping the
apply routes use (``ergasterion._step_input_from_parameters``):

    SELECT_SUBGRAPH → "selected_elements"   (List[str])
    SELECT_AREA     → "target_area"         (str: a cut id or the sheet)
    PROVIDE_EGIF    → "egif_content"        (str: EGIF to insert)

Purely additive and read-only: it reflects the static interaction
protocol; it touches no session and no EGI.
"""

import sys
from pathlib import Path

# Ensure src/ is on path (when imported from web_api/routes/)
_src_dir = Path(__file__).parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from fastapi import APIRouter

from web_api.models.api_models import ApiResponse

from rule_interaction import RULE_INTERACTIONS, StepKind


router = APIRouter(prefix="/rules")


# The request field a client populates for each step kind.  Single source
# of truth, mirrored by ergasterion._step_input_from_parameters.
_STEP_PARAMETER: dict = {
    StepKind.SELECT_SUBGRAPH: "selected_elements",
    StepKind.SELECT_AREA: "target_area",
    StepKind.PROVIDE_EGIF: "egif_content",
}


def _rule_descriptor(rule_name: str, interaction) -> dict:
    """Serialize one rule's interaction steps for HTTP consumers."""
    steps = []
    for step in interaction.steps():
        steps.append(
            {
                "step_id": step.step_id,
                "kind": step.kind.value,
                "prompt": step.prompt,
                "optional": step.optional,
                "parameter": _STEP_PARAMETER.get(step.kind),
            }
        )
    return {"rule": rule_name, "steps": steps}


@router.get("")
@router.get("/")
async def list_rules():
    """Describe every Dau rule's required inputs.

    Returns one descriptor per rule so a selection-driven client knows,
    before acting, exactly which fields to send and in what order the
    inputs are consumed (e.g. INS needs ``egif_content`` then a negative
    ``target_area``; DC+ needs only an optional ``selected_elements``).
    """
    try:
        rules = [
            _rule_descriptor(name, interaction)
            for name, interaction in RULE_INTERACTIONS.items()
        ]
        return ApiResponse(success=True, data=rules)
    except Exception as exc:
        return ApiResponse(
            success=False,
            error={"code": "RULES_LIST_ERROR", "message": str(exc)},
        )


@router.get("/{rule}")
async def get_rule(rule: str):
    """Describe a single rule's required inputs, or refuse if unknown."""
    interaction = RULE_INTERACTIONS.get(rule)
    if interaction is None:
        return ApiResponse(
            success=False,
            error={
                "code": "UNKNOWN_RULE",
                "message": (
                    f"Unknown rule '{rule}'. "
                    f"Valid rules: {sorted(RULE_INTERACTIONS.keys())}."
                ),
            },
        )
    return ApiResponse(success=True, data=_rule_descriptor(rule, interaction))
