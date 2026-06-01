"""
Area + polarity introspection for the web API.

The dogfood of the Ergasterion promotion boundary (memory
``project-ergasterion-dogfood-findings``, 2026-06-01) surfaced the
single highest-leverage gap for selection-driven UIs: to select
elements for any rule beyond an empty DC+, a client must know *which
area* each element lives in and that area's *polarity* (recto/verso).
On-canvas the picture shows it; over HTTP it had to be inferred by
bounds-containment.  Agon (the selection-heavy arena) needs this most.

This helper exposes the projection-independent facts — area membership
and polarity — that the client otherwise reconstructs by guesswork.
It reads only public structure:

  * ``presentation_ops.element_area`` / ``cut_parents`` — the area-tree
    (the single source of truth shared with layout/attestation);
  * ``egi.area_polarity`` — canonical polarity + nesting depth (O(1)
    via the hierarchical index).

Purely additive: it derives from the EGI, never mutates it, and makes
no claim about correspondence (that is §3.3's job at the render/corpus
boundaries).
"""

import sys
from pathlib import Path

# Ensure src/ is on path (when imported from web_api/services/)
_src_dir = Path(__file__).parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from presentation_ops import cut_parents, element_area


def egi_introspection(egi) -> dict:
    """Per-element area membership + per-area polarity for an EGI.

    Returns a JSON-compatible dict::

        {
          "areas": {
            <area_id>: {
              "polarity": "positive" | "negative",
              "depth":    int,            # 0 = sheet
              "parent":   <area_id> | None,
              "is_sheet": bool,
            },
            ...                            # the sheet and every cut
          },
          "elements": {
            <element_id>: {
              "type":     "vertex" | "edge" | "cut",
              "area":     <area_id>,       # the area that *contains* it
              "polarity": "positive" | "negative",   # polarity of that area
              "depth":    int,             # nesting depth of that area
            },
            ...                            # every vertex, edge, and cut
          },
        }

    For a cut, ``area`` / ``polarity`` / ``depth`` describe where the
    cut *sits* (its parent area) — i.e. the polarity an element would
    experience standing where the cut stands.  The cut's own *interior*
    polarity is the entry for that cut in ``areas``.
    """
    parents = cut_parents(egi)            # cut_id -> enclosing area
    elem_to_area = element_area(egi)      # vertex/edge id -> containing area

    # --- areas: sheet + every cut --------------------------------------- #
    areas: dict = {}

    def _area_record(area_id: str, parent, is_sheet: bool) -> dict:
        polarity, depth = egi.area_polarity(area_id)
        return {
            "polarity": polarity.value,
            "depth": depth,
            "parent": parent,
            "is_sheet": is_sheet,
        }

    areas[egi.sheet] = _area_record(egi.sheet, None, is_sheet=True)
    for cut in egi.Cut:
        areas[cut.id] = _area_record(
            cut.id, parents.get(cut.id), is_sheet=False
        )

    # --- elements: vertices, edges, cuts -------------------------------- #
    elements: dict = {}

    def _element_record(area_id) -> dict:
        # Reuse the area's polarity/depth — the element experiences the
        # polarity of the area that contains it.
        rec = areas.get(area_id)
        if rec is None:
            polarity, depth = egi.area_polarity(area_id)
            polarity_val, depth_val = polarity.value, depth
        else:
            polarity_val, depth_val = rec["polarity"], rec["depth"]
        return {"area": area_id, "polarity": polarity_val, "depth": depth_val}

    for vertex in egi.V:
        area_id = elem_to_area.get(vertex.id)
        elements[vertex.id] = {"type": "vertex", **_element_record(area_id)}
    for edge in egi.E:
        area_id = elem_to_area.get(edge.id)
        elements[edge.id] = {"type": "edge", **_element_record(area_id)}
    for cut in egi.Cut:
        # A cut-as-element sits in its parent area.
        area_id = parents.get(cut.id)
        elements[cut.id] = {"type": "cut", **_element_record(area_id)}

    return {"areas": areas, "elements": elements}
