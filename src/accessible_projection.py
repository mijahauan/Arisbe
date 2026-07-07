"""
Accessible projection — a non-visual, screen-reader-native projection of an
Existential Graph.

Arisbe owns the *coordinate-free* ground truth of an EG in
``natural_layout(egi)`` (``src/natural_layout.py``): the containment tree, each
element's area, and the per-ligature required crossing-sequences, with no
geometry.  Every *visual* drawing is a projection of that structure.  This
module adds a projection that is **not visual at all** — a traversable
sheet → cut → area → ligature structure plus a spoken "reading" of the graph —
so an EG is legible to a screen-reader user, or anyone reading rather than
seeing (see ``docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md`` §3.1–§3.2 on natural vs.
projected representation).

Because the projection is a **pure function of the EGI + its natural layout**,
it *is* the ground truth — there is no picture in between, so there is no
correspondence gap to attest (like the modal and audit lenses, it is
geometry-free and adds no §3.3 obligation).

DIMENSION-FREE DISCIPLINE (inherited from ``natural_layout``): this module must
never import ``layout_dto`` (``Point`` / ``BoundingBox``) or any geometry.  It
reads the coordinate-free layer and the EGI content only.
``tests/test_accessible_projection.py`` enforces the rule.

Faithfulness (asserted by the tests):
- *totality / injectivity*: every vertex, edge, and cut appears in the tree
  exactly once — the accessibility analogue of §7's totality shape;
- *crossing fidelity*: each narrated incidence's required crossings equal
  ``natural_layout(egi)``'s ``required_crossings`` for that
  (predicate, vertex, port).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from egi_core_dau import ElementID, RelationalGraphWithCuts
from eg_navigation import child_cuts, child_edges, child_vertices
from natural_layout import natural_layout


# --------------------------------------------------------------------------- #
# Spoken structures (coordinate-free by construction)                         #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class SpokenIncidence:
    """One predicate→vertex incidence, spoken.

    ``crossings`` is the required crossing-sequence copied from the natural
    layout — the ordered cut boundaries the line must cross between predicate
    and vertex.  ``crossing_phrase`` narrates it.
    """

    port: int                       # 1-based argument position, for speech
    vertex_id: ElementID
    vertex_phrase: str              # 'the individual "Socrates"' / 'the line x'
    crossings: Tuple[ElementID, ...]
    crossing_phrase: str


@dataclass(frozen=True)
class PredicateNode:
    edge_id: ElementID
    relation: str
    arity: int
    arguments: Tuple[SpokenIncidence, ...]
    heading: str                    # 'Predicate "man" — man holds of x'


@dataclass(frozen=True)
class LineNode:
    """A vertex — a line of identity (generic) or a named individual (constant)."""

    vertex_id: ElementID
    is_generic: bool
    label: Optional[str]            # constant name, or None for a generic line
    reading_name: str               # 'x' for a generic line; the label for a constant
    heading: str
    incident_predicates: Tuple[ElementID, ...]


@dataclass(frozen=True)
class AreaNode:
    """The sheet or a cut, with its direct contents in reading order."""

    area_id: ElementID
    is_sheet: bool
    polarity: str                   # 'positive' | 'negative'
    stance: str                     # 'asserted' | 'denied'
    depth: int                      # 0 = sheet
    heading: str
    lines: Tuple[LineNode, ...]
    predicates: Tuple[PredicateNode, ...]
    cuts: Tuple["AreaNode", ...]


@dataclass(frozen=True)
class AccessibleProjection:
    sheet: AreaNode                 # the root area (the sheet of assertion)
    reading: str                    # the outside-in spoken reading (see spoken_reading)


# --------------------------------------------------------------------------- #
# Vocabulary                                                                   #
# --------------------------------------------------------------------------- #

# The "asserted"/"denied" stance vocabulary this module introduces, keyed off
# canonical polarity (positive = recto = even depth; negative = verso = odd
# depth — see egi_core_dau.AreaPolarity, lines 35-36).
_STANCE = {"positive": "asserted", "negative": "denied"}

# Reading names for generic lines of identity, assigned deterministically.
_LETTERS = "xyzwvutsrqponmlkjihgfedcba"


def _incidences(egi: RelationalGraphWithCuts, vid: ElementID) -> Tuple[Tuple[str, int], ...]:
    """The (relation-name, argument-port) incidences of a vertex — an
    id-independent structural signature (two parses of one graph agree)."""
    out = []
    for e in egi.E:
        for port, v in enumerate(egi.nu.get(e.id, ())):
            if v == vid:
                out.append((egi.rel.get(e.id) or "", port))
    return tuple(sorted(out))


def _reading_names(egi: RelationalGraphWithCuts) -> Dict[ElementID, str]:
    """Deterministic reading name per *generic* vertex (``x``, ``y``, …).

    Ordered by (home-area depth, incidence signature) — all **id-independent**,
    so two parses of the same graph read identically (the reading is not at the
    mercy of fresh vertex ids or set-iteration order).  A raw-id tiebreak
    applies only to genuinely symmetric lines, where either assignment is
    equally faithful.  Constant vertices keep their label and are not named here.
    """
    from presentation_ops import element_area

    elem_area = element_area(egi)
    generics = [v for v in egi.V if v.is_generic]

    def _key(v):
        area = elem_area.get(v.id, egi.sheet)
        _, depth = egi.area_polarity(area)
        return (depth, _incidences(egi, v.id), str(v.id))

    names: Dict[ElementID, str] = {}
    for i, v in enumerate(sorted(generics, key=_key)):
        names[v.id] = _LETTERS[i] if i < len(_LETTERS) else f"x{i}"
    return names


def _term(egi: RelationalGraphWithCuts, names: Dict[ElementID, str], vid: ElementID) -> str:
    """The bare reading term for a vertex: its reading name if generic, else its
    constant label (used inside atom phrases)."""
    v = next((v for v in egi.V if v.id == vid), None)
    if v is None:
        return "?"
    if v.is_generic:
        return names.get(vid, "?")
    return f'"{v.label}"' if v.label else "an individual"


def _vertex_phrase(egi: RelationalGraphWithCuts, names: Dict[ElementID, str], vid: ElementID) -> str:
    """A referring phrase for a vertex, for an incidence heading."""
    v = next((v for v in egi.V if v.id == vid), None)
    if v is None:
        return "an unknown vertex"
    if v.is_generic:
        return f"the line {names.get(vid, '?')}"
    return f'the individual "{v.label}"' if v.label else "an unnamed individual"


def _atom_phrase(relation: str, terms: List[str]) -> str:
    """Speak an atom: ``man holds of x`` / ``loves relates x to "Mary"`` /
    ``between holds of x, y, and z``."""
    rel = relation or "an unnamed relation"
    if len(terms) == 0:
        return f"{rel} holds"
    if len(terms) == 1:
        return f"{rel} holds of {terms[0]}"
    if len(terms) == 2:
        return f"{rel} relates {terms[0]} to {terms[1]}"
    head = ", ".join(terms[:-1])
    return f"{rel} holds of {head}, and {terms[-1]}"


def _crossing_phrase(crossings: Tuple[ElementID, ...]) -> str:
    n = len(crossings)
    if n == 0:
        return "in the same area as the predicate"
    if n == 1:
        return "its line crosses 1 cut boundary to reach the predicate"
    return f"its line crosses {n} cut boundaries to reach the predicate"


# --------------------------------------------------------------------------- #
# Ordering (deterministic, hash-seed independent)                             #
# --------------------------------------------------------------------------- #

# All three keys are id-independent up to a final raw-id tiebreak that only
# resolves genuinely symmetric elements — so ordering (hence the reading and
# the reading order) is stable across parses of the same graph.

def _sorted_vertices(egi, ids: List[ElementID], names):
    def _key(vid):
        v = next((v for v in egi.V if v.id == vid), None)
        if v is None:
            return (2, "", str(vid))
        if not v.is_generic:            # constants first, by label
            return (0, v.label or "", str(vid))
        return (1, names.get(vid, ""), str(vid))
    return sorted(ids, key=_key)


def _sorted_edges(egi, ids: List[ElementID], names):
    def _key(e):
        rel = egi.rel.get(e) or ""
        terms = tuple(_term(egi, names, v) for v in egi.nu.get(e, ()))
        return (rel, terms, str(e))
    return sorted(ids, key=_key)


def _area_sig(egi, area: ElementID, names) -> str:
    """An id-independent canonical string of an area's contents — the ordering
    key for sibling cuts (structurally identical cuts collapse together;
    different ones order stably by content, not by fresh ids)."""
    vs = sorted(_term(egi, names, v) for v in child_vertices(egi, area))
    es = sorted(
        (egi.rel.get(e) or "") + "(" +
        ",".join(_term(egi, names, v) for v in egi.nu.get(e, ())) + ")"
        for e in child_edges(egi, area)
    )
    cs = sorted(_area_sig(egi, c, names) for c in child_cuts(egi, area))
    return f"V[{'|'.join(vs)}]E[{'|'.join(es)}]C[{'|'.join(cs)}]"


def _sorted_cuts(egi, ids: List[ElementID], names):
    return sorted(ids, key=lambda c: (_area_sig(egi, c, names), str(c)))


# --------------------------------------------------------------------------- #
# Build                                                                        #
# --------------------------------------------------------------------------- #

def accessible_projection(egi: RelationalGraphWithCuts) -> AccessibleProjection:
    """Build the coordinate-free ``AccessibleProjection`` for an EGI.

    Pure function of the EGI; no geometry.  One ``LineNode`` per vertex, one
    ``PredicateNode`` per edge, one ``AreaNode`` per sheet/cut — each appearing
    exactly once (totality/injectivity).  Per-incidence crossing data is copied
    from ``natural_layout(egi)`` so the spoken crossings and the drawn ones are
    the same object.
    """
    names = _reading_names(egi)

    # Index the natural layout's required crossings by incidence, so the spoken
    # reading and any drawing agree on the crossing-sequence (crossing fidelity).
    nl = natural_layout(egi)
    crossings_of: Dict[Tuple[ElementID, ElementID, int], Tuple[ElementID, ...]] = {
        (lig.predicate_id, lig.vertex_id, lig.port_index): lig.required_crossings
        for lig in nl.ligatures
    }

    def _predicate_node(eid: ElementID) -> PredicateNode:
        relation = egi.rel.get(eid) or ""
        nu_seq = egi.nu.get(eid, ())
        args: List[SpokenIncidence] = []
        for port_index, vid in enumerate(nu_seq):
            crossings = crossings_of.get((eid, vid, port_index), ())
            args.append(SpokenIncidence(
                port=port_index + 1,
                vertex_id=vid,
                vertex_phrase=_vertex_phrase(egi, names, vid),
                crossings=crossings,
                crossing_phrase=_crossing_phrase(crossings),
            ))
        terms = [_term(egi, names, vid) for vid in nu_seq]
        heading = f'Predicate "{relation}" — {_atom_phrase(relation, terms)}' if relation \
            else f"Predicate — {_atom_phrase(relation, terms)}"
        return PredicateNode(
            edge_id=eid,
            relation=relation,
            arity=len(nu_seq),
            arguments=tuple(args),
            heading=heading,
        )

    def _line_node(vid: ElementID) -> LineNode:
        v = next((v for v in egi.V if v.id == vid), None)
        is_generic = bool(getattr(v, "is_generic", True))
        label = getattr(v, "label", None)
        incident = tuple(_sorted_edges(
            egi, [e.id for e in egi.E if vid in egi.nu.get(e.id, ())], names))
        if is_generic:
            name = names.get(vid, "?")
            heading = f"Line of identity {name} — an unnamed individual"
        else:
            name = label or ""
            heading = f'Individual "{label}"' if label else "An unnamed individual"
        return LineNode(
            vertex_id=vid,
            is_generic=is_generic,
            label=label,
            reading_name=name,
            heading=heading,
            incident_predicates=incident,
        )

    def _area_node(area_id: ElementID, is_sheet: bool) -> AreaNode:
        polarity_enum, depth = egi.area_polarity(area_id)
        polarity = polarity_enum.value
        stance = _STANCE.get(polarity, polarity)
        if is_sheet:
            heading = "Sheet of assertion"
        else:
            heading = f"Cut — its interior is {stance} (depth {depth})"

        lines = tuple(_line_node(vid)
                      for vid in _sorted_vertices(egi, child_vertices(egi, area_id), names))
        predicates = tuple(_predicate_node(eid)
                           for eid in _sorted_edges(egi, child_edges(egi, area_id), names))
        cuts = tuple(_area_node(cid, is_sheet=False)
                     for cid in _sorted_cuts(egi, child_cuts(egi, area_id), names))
        return AreaNode(
            area_id=area_id,
            is_sheet=is_sheet,
            polarity=polarity,
            stance=stance,
            depth=depth,
            heading=heading,
            lines=lines,
            predicates=predicates,
            cuts=cuts,
        )

    root = _area_node(egi.sheet, is_sheet=True)
    return AccessibleProjection(sheet=root, reading=spoken_reading(egi, names=names))


# --------------------------------------------------------------------------- #
# Spoken reading (outside-in narration)                                        #
# --------------------------------------------------------------------------- #

def spoken_reading(egi: RelationalGraphWithCuts,
                   names: Optional[Dict[ElementID, str]] = None) -> str:
    """A single structural, outside-in reading of the whole graph.

    Clones the recursion shape of ``egi_to_fol._Reader.read_area`` (generic
    vertex → existential, atom → relation applied, nested cut → negation) but
    emits prose.  Structural-faithful, not idiomatic English: it never
    rephrases scope, so the reading and the picture denote the same graph.

    Example (``~[ (man *x) ~[ (mortal x) ] ]``)::

        The sheet asserts: there is something, x; man holds of x; it is not
        the case that: mortal holds of x.
    """
    if names is None:
        names = _reading_names(egi)

    def _read_area(area_id: ElementID) -> str:
        parts: List[str] = []
        # Existentials: generic lines whose home is this area.
        for vid in _sorted_vertices(egi, child_vertices(egi, area_id), names):
            v = next((v for v in egi.V if v.id == vid), None)
            if v is not None and v.is_generic:
                parts.append(f"there is something, {names.get(vid, '?')}")
            elif v is not None and not any(vid in egi.nu.get(e.id, ()) for e in egi.E):
                # An isolated constant vertex asserts a named individual exists.
                parts.append(f'the individual {_term(egi, names, vid)} exists')
        # Atoms directly in this area.
        for eid in _sorted_edges(egi, child_edges(egi, area_id), names):
            relation = egi.rel.get(eid) or ""
            terms = [_term(egi, names, vid) for vid in egi.nu.get(eid, ())]
            parts.append(_atom_phrase(relation, terms))
        # Nested cuts → negations.
        for cid in _sorted_cuts(egi, child_cuts(egi, area_id), names):
            parts.append(f"it is not the case that: {_read_area(cid)}")
        return "; ".join(parts) if parts else "nothing"

    body = _read_area(egi.sheet)
    return f"The sheet asserts: {body}."


# --------------------------------------------------------------------------- #
# Reading order (flat, depth-annotated — the screen-reader traversal)         #
# --------------------------------------------------------------------------- #

def reading_lines(projection: AccessibleProjection) -> List[str]:
    """The flat, ordered spoken lines — the screen-reader reading order.

    Depth-indented headings for every area, line of identity, and predicate, in
    the same order the ARIA tree presents them.
    """
    lines: List[str] = []

    def _walk(area: AreaNode, depth: int) -> None:
        pad = "  " * depth
        lines.append(f"{pad}{area.heading}")
        for ln in area.lines:
            lines.append(f"{pad}  {ln.heading}")
        for pr in area.predicates:
            lines.append(f"{pad}  {pr.heading}")
            for arg in pr.arguments:
                if arg.crossings:
                    lines.append(f"{pad}    argument {arg.port}: {arg.vertex_phrase} "
                                 f"({arg.crossing_phrase})")
        for cut in area.cuts:
            _walk(cut, depth + 1)

    _walk(projection.sheet, 0)
    return lines


# --------------------------------------------------------------------------- #
# Serialization (JSON-friendly, for the HTTP boundary / the ARIA-tree lens)    #
# --------------------------------------------------------------------------- #

def _area_to_dict(area: AreaNode) -> dict:
    return {
        "id": area.area_id,
        "kind": "sheet" if area.is_sheet else "cut",
        "polarity": area.polarity,
        "stance": area.stance,
        "depth": area.depth,
        "heading": area.heading,
        "lines": [
            {
                "id": ln.vertex_id,
                "kind": "line" if ln.is_generic else "individual",
                "is_generic": ln.is_generic,
                "label": ln.label,
                "reading_name": ln.reading_name,
                "heading": ln.heading,
                "incident_predicates": list(ln.incident_predicates),
            }
            for ln in area.lines
        ],
        "predicates": [
            {
                "id": pr.edge_id,
                "relation": pr.relation,
                "arity": pr.arity,
                "heading": pr.heading,
                "arguments": [
                    {
                        "port": arg.port,
                        "vertex_id": arg.vertex_id,
                        "vertex_phrase": arg.vertex_phrase,
                        "crossings": list(arg.crossings),
                        "crossing_phrase": arg.crossing_phrase,
                    }
                    for arg in pr.arguments
                ],
            }
            for pr in area.predicates
        ],
        "cuts": [_area_to_dict(c) for c in area.cuts],
    }


def projection_to_dict(projection: AccessibleProjection) -> dict:
    """JSON-compatible view of the projection: the nested area tree plus the
    flat reading order and the outside-in reading."""
    return {
        "tree": _area_to_dict(projection.sheet),
        "reading": projection.reading,
        "reading_lines": reading_lines(projection),
    }


__all__ = [
    "SpokenIncidence",
    "PredicateNode",
    "LineNode",
    "AreaNode",
    "AccessibleProjection",
    "accessible_projection",
    "spoken_reading",
    "reading_lines",
    "projection_to_dict",
]
