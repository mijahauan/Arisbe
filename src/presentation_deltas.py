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


def delta_key(delta: "PresentationDelta") -> tuple:
    """The element-identity a delta addresses — the unit of inheritance/override.

    Two deltas with the same key touch the same element (the same vertex, cut,
    or line of identity), so a *later* state re-authoring that key supersedes
    the ancestor's (re-nudging replaces, it doesn't stack); different keys
    coexist.  Within one state, same-key deltas are kept in order (successive
    drags compose).  See ``merge_inherited``.
    """
    p = delta.params
    if delta.op == MOVE_VERTEX:
        return ("v", p.get("vertex_id"))
    if delta.op == RESHAPE_CUT:
        return ("c", p.get("cut_id"))
    if delta.op == REROUTE_LIGATURE:
        return ("l", p.get("predicate_id"), p.get("vertex_id"), p.get("port_index"))
    return ("?", delta.op)


def merge_inherited(
    ordered_state_ids: List[str],
    authored_by_state: Dict[str, List["PresentationDelta"]],
) -> List["PresentationDelta"]:
    """Resolve the *effective* delta list for the last state in
    ``ordered_state_ids`` (the chain inheritance / extrapolation-scale-2 rule).

    ``ordered_state_ids`` is the ancestry initial → … → target (target last);
    ``authored_by_state`` maps each state id to the deltas *authored at* it.

    The effective list is the authored deltas concatenated in ancestry order,
    **except** that a descendant state which re-authors a given ``delta_key``
    REPLACES every ancestor delta for that key — so a survivor nudged at an
    early state inherits forward, but re-adjusting it later supersedes rather
    than double-applies.  Order is by first key introduction; same-key deltas
    from the winning state stay in their authored order (cumulative drags).

    Inherited deltas whose target element no longer exists downstream are *not*
    filtered here — they are dropped at replay time by ``apply_deltas`` (the
    op raises ``Regime3Violation`` for an unknown id), keeping this resolver a
    pure key-merge with no EGI dependency.
    """
    from collections import OrderedDict

    by_key: "OrderedDict[tuple, List[PresentationDelta]]" = OrderedDict()
    for sid in ordered_state_ids:
        authored = authored_by_state.get(sid) or []
        groups: "OrderedDict[tuple, List[PresentationDelta]]" = OrderedDict()
        for d in authored:
            groups.setdefault(delta_key(d), []).append(d)
        for k, ds in groups.items():
            by_key[k] = ds  # descendant authorship replaces inherited for key k
    out: List["PresentationDelta"] = []
    for ds in by_key.values():
        out.extend(ds)
    return out


def generalization_key(target: Dict[str, Any], fields: Tuple[str, ...]) -> Optional[tuple]:
    """A *coarse* structural key for extrapolation — the handle that groups a
    delta with the untouched elements it should generalize to.

    Unlike ``delta_key`` (element *identity* — the unit of inheritance/override),
    this reads the target's ``describe`` *tags* (kind / area_polarity / depth /
    relation / label) and keeps only ``fields``.  Two elements with the same
    generalization key share a structural description ("a vertex in an
    odd-polarity area"), so an intent sampled on one is a candidate intent for
    the other.  Returns ``None`` when any requested field is absent/unknown on
    this target — an untaggable delta can't be generalized by structure.
    """
    key = []
    for f in fields:
        v = target.get(f)
        if v is None:
            return None
        key.append((f, v))
    return tuple(key)


def extrapolate_deltas(
    egi: RelationalGraphWithCuts,
    deltas: List["PresentationDelta"],
    *,
    key_fields: Tuple[str, ...] = ("kind", "area_polarity"),
) -> List["PresentationDelta"]:
    """Generalize sparse, tagged ``move_vertex`` deltas to the *untouched*
    in-scope vertices that share their structural description — extrapolation
    **scale 1 (within a view)**, the conceptual heart of the projection ladder
    (style = universal default, deltas = sparse exemplars, *extrapolation* =
    the crystallization that turns a few hand-deltas into a regularity).

    The recipe, per ``docs/PRESENTATION_DELTAS_AND_STYLE.md`` §3:

    1. A delta is a **sample of an intent**.  Only ``move_vertex`` generalizes
       cleanly: a move is a *translation* (dx, dy), largely style-robust, so
       "this kind of vertex sits a little lower" copies to a sibling.  Absolute
       ``reshape_cut`` bounds and per-line ``reroute_ligature`` paths are
       geometry-specific and are **not** extrapolated here (they'd need a
       relative encoding first).
    2. Group the move exemplars by their ``generalization_key`` (default:
       kind + area polarity — Peirce's odd/even nesting, the example the design
       names).  Each group's intent is the **mean** translation of its members
       (one exemplar → that exemplar; several → their average — the simplest
       honest aggregation, and the raw signal a future "study" layer reads).
    3. For every vertex in the EGI that (a) has **no explicit delta of its own**
       and (b) matches a group's key, synthesize a tagged ``move_vertex`` delta
       carrying that group's mean translation.

    Returns **only the synthetic deltas** (targeting untouched elements) — the
    caller applies them *after* the explicit ones (the two element-sets are
    disjoint by construction).  Each synthetic delta is replayed through the
    same best-effort, §3.3-attested ``apply_deltas`` path, so an extrapolation
    that doesn't fit (would cross a boundary, overlaps) is silently dropped, not
    forced.
    """
    moves = [d for d in deltas if d.op == MOVE_VERTEX]
    if not moves:
        return []

    # Intent per structural group: accumulate (dx, dy) of the exemplars.
    groups: "Dict[tuple, List[Tuple[float, float]]]" = {}
    for d in moves:
        key = generalization_key(d.target, key_fields)
        if key is None:
            continue
        try:
            dx, dy = float(d.params["dx"]), float(d.params["dy"])
        except (KeyError, TypeError, ValueError):
            continue
        groups.setdefault(key, []).append((dx, dy))
    if not groups:
        return []

    mean_intent = {
        key: (sum(x for x, _ in pts) / len(pts), sum(y for _, y in pts) / len(pts))
        for key, pts in groups.items()
    }

    explicit_vids = {
        d.params.get("vertex_id") for d in moves if d.params.get("vertex_id")
    }

    out: List["PresentationDelta"] = []
    for v in egi.V:
        if v.id in explicit_vids:
            continue  # the user touched this one directly — never override it
        try:
            target = describe(egi, v.id)
        except Exception:
            continue
        key = generalization_key(target, key_fields)
        if key is None or key not in mean_intent:
            continue
        dx, dy = mean_intent[key]
        out.append(
            PresentationDelta(
                op=MOVE_VERTEX,
                params={"vertex_id": v.id, "dx": dx, "dy": dy},
                target=target,
            )
        )
    return out


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
    "delta_key",
    "merge_inherited",
    "generalization_key",
    "extrapolate_deltas",
    "deltas_to_list",
    "deltas_from_list",
]
