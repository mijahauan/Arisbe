"""
Natural layout — the coordinate-free, projection-independent structure
that any faithful drawing of an EGI must realize.

This is the "own the dimensionality" layer (see
``docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md`` §3.1–§3.2 natural vs.
projected representation, and the project memory
``project-render-as-projection-own-dimensionality``).  It holds the
facts that are invariant across *any* projection — 2-D SVG today, 3-D
or Peirce's verso later — and therefore must hold no coordinates,
distances, or orderings.

What it commits to (the starting set):

- the cut-containment tree (``cut_parent``);
- each vertex/edge's area (``element_area``);
- per-ligature **required crossing-sequence**: the ordered cuts whose
  boundary a ligature segment must cross, derived from the unique
  area-tree path between the predicate's area and the vertex's area;
- predicate–vertex incidence with argument order (``port_index``).

The required-crossing-sequence is the rigorous, projection-independent
form of §3.3 *identity fidelity* ("the ligature passes through exactly
the areas given by the ``area`` mapping of its members, and no
others"): stated in terms of boundary **crossings** rather than area
**membership**, which is what makes it checkable as a crossing-multiset
equality against any projection.

DIMENSION-FREE DISCIPLINE: this module must never import ``Point`` /
``BoundingBox`` (``layout_dto``) or any geometry.  A projection (e.g.
``elk_layout_engine``) consumes a ``NaturalLayout`` and *realizes* it
into coordinates; a checker compares a realized drawing's actual
crossings against the required ones.  Keeping geometry out of here is
what makes a future 3-D projection additive rather than a rewrite.
``tests/test_natural_layout.py`` enforces the no-geometry-import rule.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from egi_core_dau import ElementID, RelationalGraphWithCuts
from presentation_ops import crossing_sequence, cut_parents, element_area


@dataclass(frozen=True)
class NaturalLigature:
    """One predicate→vertex incidence and the cuts its line must cross.

    ``required_crossings`` is the ordered tuple of cut IDs whose
    boundary the connecting ligature segment must cross exactly once, as
    the curve travels from the predicate (outward to the meet) and then
    inward to the vertex.  Empty when predicate and vertex share an area.
    """

    predicate_id: ElementID
    vertex_id: ElementID
    port_index: int
    required_crossings: Tuple[ElementID, ...]


@dataclass(frozen=True)
class NaturalLayout:
    """Projection-independent layout structure for an EGI.

    Coordinate-free by construction.  A projection realizes it into a
    ``LayoutDTO``; ``natural_layout_check`` (or a strengthened
    ``correspondence_attestation``) verifies a realization against it.
    """

    sheet: ElementID
    cut_parent: Dict[ElementID, ElementID]       # cut -> enclosing area
    element_area: Dict[ElementID, ElementID]     # vertex/edge -> area
    ligatures: Tuple[NaturalLigature, ...]

    def required_crossings(
        self, predicate_id: ElementID, vertex_id: ElementID, port_index: int
    ) -> Optional[Tuple[ElementID, ...]]:
        """Required crossing-sequence for one incidence, or None if absent."""
        for lig in self.ligatures:
            if (
                lig.predicate_id == predicate_id
                and lig.vertex_id == vertex_id
                and lig.port_index == port_index
            ):
                return lig.required_crossings
        return None


def authorized_crossings(
    pred_area: Optional[ElementID],
    vert_area: Optional[ElementID],
    parent_map: Dict[ElementID, ElementID],
) -> Tuple[ElementID, ...]:
    """Ordered cuts whose boundary a ligature from ``pred_area`` to
    ``vert_area`` must cross.

    These are exactly the cuts on the unique area-tree path between the
    two areas, *excluding* their lowest common ancestor (you do not
    cross the meet's boundary).  Order follows the curve: outward from
    the predicate's area to just below the meet, then inward from just
    below the meet down to the vertex's area.

    Semantic alias for the projection-independent layer.  The
    computation itself lives once in ``presentation_ops.crossing_sequence``
    (sharing its ``_tree_path`` walk with ``area_chain``); this name is
    the projection-independent vocabulary the layout/projection code
    consumes.  ``ELKLayoutEngine._authorized_cuts`` delegates here, so
    the area-tree walk is computed once, not three times.
    """
    return crossing_sequence(pred_area, vert_area, parent_map)


def natural_layout(egi: RelationalGraphWithCuts) -> NaturalLayout:
    """Build the coordinate-free ``NaturalLayout`` for an EGI.

    Pure function of the EGI; no geometry, no layout engine.  One
    ``NaturalLigature`` per (predicate, argument-position) incidence in
    ``ν`` — matching how ``LigaturePath`` is keyed, so a realization can
    be compared one-to-one.
    """
    parent_map = cut_parents(egi)
    elem_area = element_area(egi)

    ligatures = []
    for edge in egi.E:
        nu_seq = egi.nu.get(edge.id, ())
        pred_area = elem_area.get(edge.id, egi.sheet)
        for port_index, v_id in enumerate(nu_seq):
            vert_area = elem_area.get(v_id, egi.sheet)
            crossings = authorized_crossings(pred_area, vert_area, parent_map)
            ligatures.append(
                NaturalLigature(
                    predicate_id=edge.id,
                    vertex_id=v_id,
                    port_index=port_index,
                    required_crossings=crossings,
                )
            )

    return NaturalLayout(
        sheet=egi.sheet,
        cut_parent=dict(parent_map),
        element_area=dict(elem_area),
        ligatures=tuple(ligatures),
    )


__all__ = [
    "NaturalLayout",
    "NaturalLigature",
    "authorized_crossings",
    "natural_layout",
]
