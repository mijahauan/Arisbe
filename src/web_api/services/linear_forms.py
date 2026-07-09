"""
Linear-form rendering for diagram views.

Every view of an EGI's *diagram* form should be able to show its *linear*
form too — and in whichever notation the reader prefers (EGIF by default,
CGIF, CLIF, …).  Picture and proposition denote the same mathematical
object (see ``docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md``); surfacing the
linear form beside the drawing makes that identity visible and lets a
reader cross-check the two.

This is the single source of truth for "EGI → linear text in format X".
It is a thin registry over the format generators (`egif_generator_dau`,
`cgif_generator_dau`, `clif_generator_dau`) so adding a format later is
one line here and it appears automatically in every payload and every
data-driven format selector.

Each format is generated defensively: a graph that round-trips in EGIF
may not (yet) generate cleanly in CGIF/CLIF, and one failing notation
must not break the diagram view or the others.  A failure is reported in
that format's entry, not raised.
"""

import sys
from pathlib import Path
from typing import Callable, Dict, List

# Ensure src/ is on path (when imported from web_api/services/)
_src_dir = Path(__file__).parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from cgif_generator_dau import generate_cgif
from chapter18_fopl_translation import egi_to_fopl
from clif_generator_dau import generate_clif
from egif_generator_dau import generate_egif


# Ordered registry — the first entry is the default the UI selects.  Add a
# (key, label, generator) row to extend; payloads and selectors follow.
# FOPL is Dau's Φ translation (Chapter 18), not a naïve conversion; it is
# generated defensively like the rest, so a graph it cannot yet render cleanly
# reports in its own entry rather than breaking the other notations.
_FORMATS: List[Dict[str, object]] = [
    {"key": "egif", "label": "EGIF", "generator": generate_egif},
    {"key": "cgif", "label": "CGIF", "generator": generate_cgif},
    {"key": "clif", "label": "CLIF", "generator": generate_clif},
    {"key": "fopl", "label": "FOPL", "generator": egi_to_fopl},
]

_DEFAULT_FORMAT = _FORMATS[0]["key"]


def linear_formats() -> List[Dict[str, str]]:
    """The available formats as ``[{key, label}]``, in display order."""
    return [{"key": f["key"], "label": f["label"]} for f in _FORMATS]


def default_format() -> str:
    """The format the UI should select by default (EGIF)."""
    return _DEFAULT_FORMAT


def _generate_one(egi, generator: Callable) -> Dict[str, object]:
    try:
        return {"ok": True, "text": generator(egi), "error": None}
    except Exception as exc:  # defensive — one notation must not break others
        return {"ok": False, "text": None, "error": f"{type(exc).__name__}: {exc}"}


def linear_forms(egi) -> Dict[str, object]:
    """All linear renderings of *egi*, keyed by format.

    Returns a JSON-compatible dict::

        {
          "default": "egif",
          "formats": [ {"key": "egif", "label": "EGIF"}, ... ],   # display order
          "forms": {
            "egif": {"label": "EGIF", "ok": true,  "text": "...", "error": null},
            "cgif": {"label": "CGIF", "ok": false, "text": null,  "error": "..."},
            ...
          }
        }

    A client renders ``forms[selected].text`` and builds its selector from
    ``formats`` — so a new notation appears with no frontend change.

    ``reading`` carries the natural-language **gloss** (``eg_to_english``) in two
    registers (``idiomatic`` / ``literal``). It is *not* a linear form — English
    is lossy and does not round-trip, so it is offered beside the notations as a
    reading, never as an editable fifth notation. Defensive: a failure leaves
    ``reading`` absent rather than breaking the forms.
    """
    forms: Dict[str, object] = {}
    for f in _FORMATS:
        result = _generate_one(egi, f["generator"])
        forms[f["key"]] = {"label": f["label"], **result}
    out: Dict[str, object] = {
        "default": _DEFAULT_FORMAT,
        "formats": linear_formats(),
        "forms": forms,
    }
    try:
        from eg_to_english import english_readings
        out["reading"] = english_readings(egi)
    except Exception:
        pass  # the gloss is a convenience; never let it break the linear forms
    return out
