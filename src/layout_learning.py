"""
The drawing→EGI **learning loop** (ROADMAP #14 (d)).

The Peirce-Edition "replica-then-parse" journey: a scholar draws a graph in
Peirce's own hand (the freeform canvas), it is parsed back to an EGI
(``eg_reader.read_drawing`` / ``drawing_to_egi``), and the *arrangement* of that
drawing very likely differs from what Arisbe would have produced canonically
(``generate_layout``).  That difference is a **learning signal**: it records how
a human (Peirce) actually places the marks.

This module turns the difference into the codebase's existing currency — a list
of regime-3 ``presentation_deltas.PresentationDelta`` carrying the *canonical*
layout to the *drawn* one — so it plugs straight into the presentation-deltas →
style ladder (``docs/PRESENTATION_DELTAS_AND_STYLE.md``):

    drawn DTO  ──arrangement_deltas──▶  sparse tagged deltas
                                          │
                       extrapolate_deltas │  (crystallise to siblings)
                                          ▼
                        a refined "this kind of element sits here" regularity

The deltas are the inverse of ``presentation_deltas.apply_deltas``: that replays
deltas onto a base layout; this *recovers* the deltas between two layouts of the
same EGI.  Only logic-indifferent (regime-3) facts are read — positions and cut
bounds — so feeding them back is correspondence-safe by construction (every move
re-attests §3.3 inside ``apply_deltas`` / ``extrapolate_deltas``).
"""

from typing import List, Tuple

from egi_core_dau import RelationalGraphWithCuts
from layout_dto import LayoutDTO
from presentation_deltas import (
    PresentationDelta, record_delta, extrapolate_deltas,
    MOVE_VERTEX, MOVE_PREDICATE, MOVE_CUT, RESHAPE_CUT,
)


def arrangement_deltas(
    egi: RelationalGraphWithCuts,
    canonical_dto: LayoutDTO,
    drawn_dto: LayoutDTO,
    *,
    eps: float = 0.5,
) -> List[PresentationDelta]:
    """The regime-3 deltas carrying *canonical_dto* to *drawn_dto* for *egi* — the
    arrangement a human chose, expressed relative to Arisbe's default.

    Per element kind: a moved vertex → ``move_vertex``; a moved predicate →
    ``move_predicate``; a resized cut → ``reshape_cut`` (else a translated cut →
    ``move_cut``).  Elements within ``eps`` of canonical contribute nothing.
    Each delta is tagged by ``record_delta`` (``eg_navigation.describe``) so the
    style ladder can generalise it by structure.

    Only elements present in *both* DTOs are compared (the two are layouts of the
    *same* EGI, so this is normally every element).  Note: a human who moved a
    *cut* also moved its contents — this records both the ``move_cut`` and the
    per-content moves, which compound on replay; callers that want the cut move
    alone should diff leaf elements relative to their cut.  (A future refinement
    could subtract a parent cut's translation from its contents.)
    """
    out: List[PresentationDelta] = []

    for vid, dpos in drawn_dto.vertex_positions.items():
        cpos = canonical_dto.vertex_positions.get(vid)
        if cpos is None:
            continue
        dx, dy = dpos.x - cpos.x, dpos.y - cpos.y
        if abs(dx) > eps or abs(dy) > eps:
            out.append(record_delta(egi, MOVE_VERTEX,
                                    {"vertex_id": vid, "dx": dx, "dy": dy}))

    for pid, dpos in drawn_dto.predicate_positions.items():
        cpos = canonical_dto.predicate_positions.get(pid)
        if cpos is None:
            continue
        dx, dy = dpos.x - cpos.x, dpos.y - cpos.y
        if abs(dx) > eps or abs(dy) > eps:
            out.append(record_delta(egi, MOVE_PREDICATE,
                                    {"predicate_id": pid, "dx": dx, "dy": dy}))

    for cid, db in drawn_dto.cut_bounds.items():
        cb = canonical_dto.cut_bounds.get(cid)
        if cb is None or cid == drawn_dto.sheet_id:
            continue
        d_w = (db.max_x - db.min_x) - (cb.max_x - cb.min_x)
        d_h = (db.max_y - db.min_y) - (cb.max_y - cb.min_y)
        d_cx = (db.min_x + db.max_x) / 2.0 - (cb.min_x + cb.max_x) / 2.0
        d_cy = (db.min_y + db.max_y) / 2.0 - (cb.min_y + cb.max_y) / 2.0
        if abs(d_w) > eps or abs(d_h) > eps:
            out.append(record_delta(egi, RESHAPE_CUT, {
                "cut_id": cid,
                "bounds": {"min_x": db.min_x, "min_y": db.min_y,
                           "max_x": db.max_x, "max_y": db.max_y},
            }))
        elif abs(d_cx) > eps or abs(d_cy) > eps:
            out.append(record_delta(egi, MOVE_CUT,
                                    {"cut_id": cid, "dx": d_cx, "dy": d_cy}))

    return out


def generalize_arrangement(
    egi: RelationalGraphWithCuts,
    deltas: List[PresentationDelta],
    *,
    key_fields: Tuple[str, ...] = ("kind", "area_polarity"),
) -> List[PresentationDelta]:
    """Close the loop: crystallise the learned arrangement into a regularity.

    A thin pass-through to ``presentation_deltas.extrapolate_deltas`` — the
    learned ``move_vertex`` / ``move_predicate`` exemplars are generalised to the
    *untouched* in-scope elements that share their structural description, so a
    few hand placements become "this kind of element sits here" (the projection
    ladder's crystallisation step, ``docs/PRESENTATION_DELTAS_AND_STYLE.md`` §3).
    Returns only the synthetic deltas (targeting untouched elements).
    """
    return extrapolate_deltas(egi, deltas, key_fields=key_fields)
