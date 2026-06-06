"""
Presentation deltas (regime-3) — recorded, tagged, replayable hand-adjustments.

A *style* (``styles/*.json``) is the universal, named projection setting that
applies to any graph at any viewing scope.  A *delta* is a sparse, individual
override on top of a (style + base layout): the user nudged this vertex,
reshaped that cut, rerouted this line.  Deltas are recorded as the *acts*
themselves — the ``presentation_ops`` vocabulary — each tagged with the
structural *description* of its target (kind / area / polarity / depth /
relation / label, from ``eg_navigation.describe``).  A delta is therefore a
**sample of an intent**, not a one-off pixel fact: the tag is the handle a
future extrapolator uses to generalize a few exemplars to the untouched
elements in view, forward through a diachronic chain, and (when stable across
the corpus) up into a new named style.

This module owns:

- ``PresentationDelta`` — one recorded regime-3 act + its target's tags.
- ``record_delta`` — build a tagged delta from an op + params against an EGI.
- ``apply_deltas`` — replay a delta list over a base ``LayoutDTO`` via
  ``presentation_ops``, **dropping** (not failing on) any delta that no longer
  applies.  Each applied op preserves §3.3 by construction *and* is re-attested
  here as a backstop — the same two-gate discipline as the Settle ④b route, and
  the same best-effort-with-fallback discipline as the Settle ④a incremental
  builders.
- ``to_dict`` / ``from_dict`` — JSON round-trip for persistence.

See ``docs/PRESENTATION_DELTAS_AND_STYLE.md``.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from egi_core_dau import ElementID, RelationalGraphWithCuts
from layout_dto import BoundingBox, LayoutDTO, Point
from eg_navigation import describe
from presentation_ops import (
    Regime3Violation,
    move_vertex,
    reshape_cut,
    reroute_ligature,
)
from correspondence_attestation import attest_correspondence, CorrespondenceViolation

MOVE_VERTEX = "move_vertex"
RESHAPE_CUT = "reshape_cut"
REROUTE_LIGATURE = "reroute_ligature"
_OPS = (MOVE_VERTEX, RESHAPE_CUT, REROUTE_LIGATURE)


@dataclass(frozen=True)
class PresentationDelta:
    """One recorded regime-3 act + the structural description of its target.

    ``op`` is one of the three ``presentation_ops`` verbs.  ``params`` carries
    the operation-specific arguments — the same shape the ``/adjust`` route
    accepts:

        move_vertex      → {vertex_id, dx, dy}
        reshape_cut      → {cut_id, bounds: {min_x, min_y, max_x, max_y}}
        reroute_ligature → {predicate_id, vertex_id, port_index, interior: [{x,y}]}

    ``target`` is ``eg_navigation.describe()`` of the *primary* element the act
    addresses (the moved vertex / reshaped cut / the line's vertex) — kind /
    area / area_polarity / area_depth / relation / label.  It is the handle for
    generalization: an extrapolator groups deltas by target description.  It is
    descriptive metadata only; replay reads ``op`` and ``params``.
    """

    op: str
    params: Dict[str, Any]
    target: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"op": self.op, "params": dict(self.params), "target": dict(self.target)}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PresentationDelta":
        return cls(
            op=d["op"],
            params=dict(d.get("params", {})),
            target=dict(d.get("target", {})),
        )


def _target_element(op: str, params: Dict[str, Any]) -> Optional[ElementID]:
    """The primary element an op addresses — the one we tag with ``describe``."""
    if op == MOVE_VERTEX:
        return params.get("vertex_id")
    if op == RESHAPE_CUT:
        return params.get("cut_id")
    if op == REROUTE_LIGATURE:
        # The line of identity's vertex end; the predicate is the other end.
        return params.get("vertex_id")
    return None


def record_delta(
    egi: RelationalGraphWithCuts, op: str, params: Dict[str, Any]
) -> PresentationDelta:
    """Build a tagged delta from an op + its params, against the current EGI.

    Tags the target element with ``eg_navigation.describe`` when it can be
    resolved; an unresolvable target (already-removed element) yields an empty
    tag, which is still a valid delta (it just can't be generalized by
    structure).
    """
    if op not in _OPS:
        raise ValueError(f"record_delta: unknown op {op!r}")
    elem = _target_element(op, params)
    target: Dict[str, Any] = {}
    if elem is not None:
        try:
            target = describe(egi, elem)
        except Exception:
            target = {"id": elem}
    return PresentationDelta(op=op, params=dict(params), target=target)


def _apply_one(
    egi: RelationalGraphWithCuts, dto: LayoutDTO, delta: PresentationDelta
) -> LayoutDTO:
    """Apply one delta via ``presentation_ops``; raise on any malformed input."""
    p = delta.params
    if delta.op == MOVE_VERTEX:
        return move_vertex(egi, dto, p["vertex_id"], float(p["dx"]), float(p["dy"]))
    if delta.op == RESHAPE_CUT:
        b = p["bounds"]
        new_bounds = BoundingBox(
            min_x=float(b["min_x"]), min_y=float(b["min_y"]),
            max_x=float(b["max_x"]), max_y=float(b["max_y"]),
        )
        return reshape_cut(egi, dto, p["cut_id"], new_bounds)
    if delta.op == REROUTE_LIGATURE:
        interior = [Point(x=float(q["x"]), y=float(q["y"])) for q in p["interior"]]
        return reroute_ligature(
            egi, dto, p["predicate_id"], p["vertex_id"],
            int(p.get("port_index", 0)), interior,
        )
    raise Regime3Violation(f"apply_deltas: unknown delta op {delta.op!r}")


def apply_deltas(
    egi: RelationalGraphWithCuts,
    base_dto: LayoutDTO,
    deltas: List[PresentationDelta],
    *,
    attest: bool = True,
) -> Tuple[LayoutDTO, List[PresentationDelta]]:
    """Replay ``deltas`` over ``base_dto`` via ``presentation_ops``.

    Returns ``(dto, dropped)``.  A delta is **dropped** (and the fold continues
    from the prior good DTO) when:

      - its target element is absent from this (EGI, DTO) — ``presentation_ops``
        raises ``Regime3Violation`` for an unknown id;
      - the op would cross a regime boundary (``Regime3Violation``);
      - with ``attest`` (default), the result no longer corresponds
        (``CorrespondenceViolation``) — e.g. a reshape that satisfies the local
        membership guards yet makes a ligature newly cross a cut;
      - the params are malformed (``KeyError`` / ``TypeError`` / ``ValueError``).

    This is best-effort by design: deltas are sparse human exemplars layered
    over a regenerated base, so one that no longer fits the new base is skipped,
    not fatal — the same fallback discipline as the Settle ④a builders.  Each
    *surviving* op preserves §3.3 (by construction, and re-attested here as the
    backstop), so the returned DTO is in correspondence with ``egi``.
    """
    dto = base_dto
    dropped: List[PresentationDelta] = []
    for delta in deltas:
        try:
            candidate = _apply_one(egi, dto, delta)
            if attest:
                attest_correspondence(
                    egi, candidate, context="presentation_deltas.apply_deltas"
                )
            dto = candidate
        except (Regime3Violation, CorrespondenceViolation, KeyError, TypeError, ValueError):
            dropped.append(delta)
    return dto, dropped


def deltas_to_list(deltas: List[PresentationDelta]) -> List[Dict[str, Any]]:
    """Serialize a delta list to JSON-ready dicts."""
    return [d.to_dict() for d in deltas]


def deltas_from_list(items: List[Dict[str, Any]]) -> List[PresentationDelta]:
    """Rehydrate a delta list from JSON dicts."""
    return [PresentationDelta.from_dict(d) for d in items]


__all__ = [
    "PresentationDelta",
    "MOVE_VERTEX",
    "RESHAPE_CUT",
    "REROUTE_LIGATURE",
    "record_delta",
    "apply_deltas",
    "deltas_to_list",
    "deltas_from_list",
]
