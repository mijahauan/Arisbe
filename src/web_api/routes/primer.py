"""
Primer route — the newcomer's "first graph" examples, drawn by the real engine.

The in-app primer (``web_viewer/js/primer.js``, the guided front door to
``docs/FIELD_GUIDE_AND_DRAGONS.md``) teaches the four marks of Existential
Graphs.  Its prose lives in the client; its *worked examples* are served from
here so the learner sees the **actual** picture Arisbe draws for each linear
form — the picture↔proposition correspondence demonstrated, not described.

Each example is rendered through the ordinary ``generate_layout`` path (the same
engine every mode uses, §3.3-attested), so the primer can never drift from what
Arisbe really draws.  Read-only, mode-independent: it derives from a fixed set of
canonical first graphs, mutates nothing, asserts nothing as true.
"""

import sys
from pathlib import Path

# Ensure src/ is on path (when imported from web_api/routes/)
_src_dir = Path(__file__).parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from fastapi import APIRouter

from web_api.models.api_models import ApiResponse
from web_api.services.layout_service import generate_layout

from egif_parser_dau import parse_egif


router = APIRouter(prefix="/primer")


# The newcomer's first graphs — chosen straight from the Field Guide's
# "marks in plain sight" key and its first two dragons: a posited contingent
# fact, the scroll (implication), and the empty cut (false).  Each pairs a
# linear form the learner can type with the plain-English reading.
_FIRST_GRAPHS = [
    {
        "egif": "(Cat *x) (On x *y) (Mat y)",
        "meaning": "“a cat is on a mat” — three predicates joined by lines of identity.",
        "teaches": "A heavy line says “something exists”; the same line threaded "
                   "through two spots says “the same one.”",
    },
    {
        "egif": "~[ (Human *x) ~[ (Mortal x) ] ]",
        "meaning": "“if something is human, then it is mortal” — the scroll, "
                   "EG's picture of “if … then …”.",
        "teaches": "A conditional always lives inside an outer cut, with the "
                   "conclusion nested one deeper. The one line crosses the boundary "
                   "so it is the *same* individual in both.",
    },
    {
        "egif": "~[ ]",
        "meaning": "“false” — a cut drawn around nothing is the strongest claim "
                   "you can make: this is impossible.",
        "teaches": "A blank sheet means *true*; an empty cut means *false*. "
                   "“Nothing drawn” and “a cut around nothing” are opposites.",
    },
]


@router.get("/examples")
async def primer_examples():
    """The worked first graphs, each drawn by the real layout engine.

    Returns, for each canonical first graph, its linear form, plain-English
    reading, the one mark it teaches, and the rendered SVG — so the primer can
    show the actual drawing beside the words.
    """
    out = []
    for ex in _FIRST_GRAPHS:
        try:
            egi = parse_egif(ex["egif"])
            # Render cuts as closed curves (ovals) — the primer teaches "a cut is
            # a closed curve," so the default boxy rounded-rectangle (Dau) style
            # would contradict the words. Sowa's oval cuts read cleanly with a
            # legible font (vs Peirce-authentic's cursive).
            _dto, svg = generate_layout(egi, style_name="sowa-compliant@1.0")
        except Exception as exc:  # fail soft — a primer is never a hard error
            out.append({**ex, "svg": None, "error": str(exc)})
            continue
        out.append({**ex, "svg": svg})
    return ApiResponse(success=True, data={"examples": out})
