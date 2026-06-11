"""Build an EGI from a freeform drawing — the construction half of *fix = read*.

``eg_reader.read_drawing`` recovers an EG's **structure** from a drawing by geometry
alone: the area tree (inside/outside the cut curves) and each predicate's incidence
in argument order (tracing the ligatures).  But a structure is not yet a determinate
sign: a drawing also carries **content** — what each predicate *says* (its relation
name) and which vertices are constants (a named individual) versus generics (a bare
line of identity).  In the engine→drawing direction that content lives in the EGI and
the renderer reads it off; in the drawing→EGI direction (freeform composition) it has
to come *from the drawing itself*, so the freeform canvas carries a label per
predicate mark and an optional constant label per vertex mark.

This module joins the two — recovered structure + carried labels — into a real
``RelationalGraphWithCuts``.  It is the piece gate ① runs to turn the composing
phase's ink into the fixed utterance (docs/FREEFORM_COMPOSITION_AND_LEARNING.md,
build step 2): once the drawing reads into an EGI, the normal pipeline takes over —
linear forms, §3.3 attestation, Dau rules.

The drawing must be **well-formed** first (run ``drawing_validity.validate_drawing``):
overlapping cuts make ``read_drawing`` produce a non-tree area map, which is not a
legal EGI.  ``build_egi_from_drawing`` builds from the reading as given; the caller
gates on validity (the route does, before calling this).
"""

from typing import Dict, Optional

from eg_reader import read_drawing
from egi_core_dau import (
    Cut,
    Edge,
    RelationalGraphWithCuts,
    Vertex,
    create_empty_graph,
)
from layout_dto import LayoutDTO


def _cut_topo_order(reading) -> list:
    """Cut ids ordered parents-before-children, by breadth-first descent from the
    sheet through the recovered area tree — so each cut is added to a context that
    already exists."""
    order: list = []
    frontier = [reading.sheet_id]
    seen = {reading.sheet_id}
    while frontier:
        nxt = []
        for area_id in frontier:
            for child in reading.area.get(area_id, set()):
                # A child that is itself an area (has its own entry) is a cut.
                if child in reading.area and child not in seen:
                    order.append(child)
                    seen.add(child)
                    nxt.append(child)
        frontier = nxt
    return order


def build_egi_from_drawing(
    dto: LayoutDTO,
    predicate_labels: Dict[str, str],
    vertex_labels: Optional[Dict[str, Optional[str]]] = None,
) -> RelationalGraphWithCuts:
    """Construct an EGI from a freeform drawing and its carried labels.

    ``dto`` supplies the geometry (mark positions, cut bounds/boundaries, ligature
    paths); ``read_drawing`` recovers the area tree and ordered incidence from it.
    ``predicate_labels`` maps each predicate mark id to its drawn relation name;
    ``vertex_labels`` maps a vertex mark id to a constant label (a named individual)
    or ``None``/absent for a generic vertex (a bare line of identity).

    The built EGI preserves the drawing's mark ids as element ids (so the result can
    be related straight back to the picture), with the sheet remapped to a fresh
    sheet id.  Assumes a well-formed drawing (the area map is a tree); the caller
    runs ``drawing_validity.validate_drawing`` first.
    """
    vertex_labels = vertex_labels or {}
    reading = read_drawing(dto)

    graph = create_empty_graph()
    sheet = graph.sheet

    def ctx(area_id: Optional[str]) -> str:
        # The reading's sheet maps to the new graph's sheet; a cut id is preserved
        # as-is (cuts are added with their drawn ids).
        if area_id is None or area_id == reading.sheet_id:
            return sheet
        return area_id

    # 1. Cuts, parents before children.
    for cid in _cut_topo_order(reading):
        parent = reading.container(cid)
        graph = graph.with_cut(Cut(id=cid), context_id=ctx(parent))

    # 2. Vertices, each in its recovered area.  A carried label makes it a constant;
    #    its absence makes it generic.
    for vid in dto.vertex_positions:
        label = vertex_labels.get(vid)
        vertex = Vertex(id=vid, label=label, is_generic=(label is None))
        graph = graph.with_vertex_in_context(vertex, ctx(reading.container(vid)))

    # 3. Predicates, with their ordered incidence and drawn relation name.  Vertices
    #    all exist now, so the vertex sequence validates.
    for pid in dto.predicate_positions:
        seq = tuple(reading.incidence.get(pid, []))
        name = predicate_labels.get(pid, "?")
        graph = graph.with_edge(
            Edge(id=pid),
            vertex_sequence=seq,
            relation_name=name,
            context_id=ctx(reading.container(pid)),
        )

    return graph


__all__ = ["build_egi_from_drawing"]
