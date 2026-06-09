"""The graph splice — the shared primitive under both the definition layer and
the graph-with-holes (schema) node.

One operation serves both:

* **Definition expansion** (`src/definitions.py`) — the placeholder is a
  defined-relation edge ``(subset z x)``; the filler is the definition's fixed
  body; the body's ports are welded onto the edge's incident lines.
* **Schema instantiation** (`src/schema.py`) — the placeholder is a *hole* edge
  ``⟨φ: x⟩``; the filler is a user-supplied graph ``g``; for **each** occurrence
  of the hole a fresh copy of ``g`` is welded onto that occurrence's ports
  (which is exactly what makes ZFC Replacement's per-occurrence port relabeling
  fall out for free).

The splice is a **definitional / structural rewrite**, not a Dau inference step:
it substitutes equals and is meaning-preserving *by construction*, so it is built
as a pure rebuild on ``egi_core_dau``'s immutable public constructors rather than
through the transformation rules.  (Whether a given *use* of the splice is sound —
e.g. asserting a schema instance — is the caller's concern; expansion of a defined
relation is not an inference at all.)

The welding trick: a filler **port** vertex is id-mapped *directly onto* the host
argument vertex it plugs into, so every filler edge incident to that port comes
out referencing the host line — welded, with no separate merge step.  Every
**non-port** filler element is mapped to a fresh id (the α-rename), so the
filler's own ``*``-lines can never accidentally fuse onto host lines.

See ``docs/MATH_FIXTURES_ZFC_PEIRCE_1881.md`` Part III + III-bis (the consistency
contract).  Touches no protected module.
"""

from typing import Dict, Optional, Sequence

from frozendict import frozendict

from egi_core_dau import (
    Cut,
    Edge,
    ElementID,
    RelationalGraphWithCuts,
    Vertex,
)


def _all_ids(egi: RelationalGraphWithCuts) -> set:
    return (
        {v.id for v in egi.V}
        | {e.id for e in egi.E}
        | {c.id for c in egi.Cut}
        | {egi.sheet}
    )


class _FreshId:
    """A collision-free id factory: never returns an id already live in the host,
    the filler, or one it has already handed out."""

    def __init__(self, *used_sets: set, prefix: str = "s"):
        self._used = set()
        for s in used_sets:
            self._used |= s
        self._prefix = prefix
        self._n = 0

    def __call__(self) -> ElementID:
        while True:
            self._n += 1
            candidate = f"{self._prefix}_{self._n}"
            if candidate not in self._used:
                self._used.add(candidate)
                return candidate


def splice(
    host: RelationalGraphWithCuts,
    placeholder_edge_id: ElementID,
    filler: RelationalGraphWithCuts,
    *,
    ports: Sequence[ElementID],
    weld: Optional[Dict[ElementID, ElementID]] = None,
) -> RelationalGraphWithCuts:
    """Replace ``placeholder_edge_id`` in ``host`` with a fresh copy of ``filler``,
    welding ``filler``'s ordered ``ports`` onto the placeholder edge's incident
    lines.

    Args:
        host: the graph containing the placeholder edge.
        placeholder_edge_id: the edge to expand/instantiate (a defined relation or
            a hole occurrence).  Its ``ν`` gives the host argument lines, in order.
        filler: the graph spliced in (a definition body, or a schema filler ``g``).
        ports: the filler's free lines, **in the order matching the placeholder
            edge's arguments**.  ``len(ports)`` must equal the placeholder's arity.
            Each filler port vertex is identified with the corresponding host
            argument vertex; every other filler element is α-renamed fresh.
        weld: optional *additional* identifications ``{filler_vertex: host_vertex}``
            beyond the positional ports — the channel for schema **parameters**
            (lines a filler shares with the host's ambient, identical across every
            occurrence because the host target id is stable).  These vertices are
            welded, not α-renamed.

    Returns the host graph with the placeholder gone and the filler welded in.
    Raises ``ValueError`` on arity mismatch or an unknown placeholder/port/weld.
    """
    if placeholder_edge_id not in {e.id for e in host.E}:
        raise ValueError(f"Placeholder edge {placeholder_edge_id} not in host")
    host_args = host.nu[placeholder_edge_id]
    if len(ports) != len(host_args):
        raise ValueError(
            f"Arity mismatch: placeholder {placeholder_edge_id} has "
            f"{len(host_args)} arguments but filler declares {len(ports)} ports"
        )
    filler_vids = {v.id for v in filler.V}
    for p in ports:
        if p not in filler_vids:
            raise ValueError(f"Port {p} is not a vertex of the filler")

    # The full filler→host weld: positional ports + the explicit parameter welds.
    weld_map: Dict[ElementID, ElementID] = {
        p: host_args[i] for i, p in enumerate(ports)
    }
    host_vids = {v.id for v in host.V}
    for fvid, hvid in (weld or {}).items():
        if fvid not in filler_vids:
            raise ValueError(f"Weld source {fvid} is not a vertex of the filler")
        if hvid not in host_vids:
            raise ValueError(f"Weld target {hvid} is not a vertex of the host")
        weld_map[fvid] = hvid

    target_ctx = host.get_context(placeholder_edge_id)
    port_set = set(weld_map)

    fresh = _FreshId(_all_ids(host), _all_ids(filler))

    # --- id mapping for every filler element ---------------------------------
    # welded lines → the host line they plug into; all else → fresh (α-rename).
    vmap: Dict[ElementID, ElementID] = {}
    for v in filler.V:
        vmap[v.id] = weld_map[v.id] if v.id in port_set else fresh()
    emap: Dict[ElementID, ElementID] = {e.id: fresh() for e in filler.E}
    cmap: Dict[ElementID, ElementID] = {c.id: fresh() for c in filler.Cut}

    def map_ctx(ctx: ElementID) -> ElementID:
        # The filler's sheet content lands in the host's target context; the
        # filler's own cuts become fresh cuts nested there (and below).
        return target_ctx if ctx == filler.sheet else cmap[ctx]

    def map_elem(eid: ElementID) -> ElementID:
        if eid in vmap:
            return vmap[eid]
        if eid in emap:
            return emap[eid]
        if eid in cmap:
            return cmap[eid]
        return eid  # the filler sheet, if it ever appears as an element

    # --- remapped filler components (ports excluded from V/area: they stay in
    #     the host where they already live) ------------------------------------
    new_vertices = {
        Vertex(id=vmap[v.id], label=v.label, is_generic=v.is_generic)
        for v in filler.V
        if v.id not in port_set
    }
    new_edges = {Edge(id=emap[e.id]) for e in filler.E}
    new_cuts = {Cut(id=cmap[c.id]) for c in filler.Cut}

    filler_nu = {
        emap[eid]: tuple(vmap[vid] for vid in seq) for eid, seq in filler.nu.items()
    }
    filler_rel = {emap[eid]: name for eid, name in filler.rel.items()}
    filler_rho = {
        vmap[vid]: const
        for vid, const in filler.rho.items()
        if vid not in port_set
    }
    filler_varnames = {
        vmap[vid]: name
        for vid, name in filler.variable_names.items()
        if vid not in port_set
    }

    # --- merge into the host -------------------------------------------------
    new_V = host.V | new_vertices
    new_E = frozenset(e for e in host.E if e.id != placeholder_edge_id) | new_edges
    new_Cut = host.Cut | new_cuts

    new_nu = {eid: seq for eid, seq in host.nu.items() if eid != placeholder_edge_id}
    new_nu.update(filler_nu)
    new_rel = {eid: n for eid, n in host.rel.items() if eid != placeholder_edge_id}
    new_rel.update(filler_rel)

    new_rho = dict(host.rho)
    new_rho.update(filler_rho)
    new_varnames = dict(host.variable_names)
    new_varnames.update(filler_varnames)

    # area: drop the placeholder from its context, then fold in the filler areas
    # (ports omitted, so host argument lines never move).
    new_area = {ctx: set(elems) for ctx, elems in host.area.items()}
    new_area[target_ctx].discard(placeholder_edge_id)
    for ctx, elems in filler.area.items():
        dest = map_ctx(ctx)
        mapped = {map_elem(e) for e in elems if e not in port_set}
        new_area.setdefault(dest, set())
        new_area[dest] |= mapped
    new_area = {ctx: frozenset(elems) for ctx, elems in new_area.items()}

    return RelationalGraphWithCuts(
        V=new_V,
        E=new_E,
        nu=frozendict(new_nu),
        sheet=host.sheet,
        Cut=new_Cut,
        area=frozendict(new_area),
        rel=frozendict(new_rel),
        alphabet=host.alphabet,
        rho=frozendict(new_rho),
        variable_names=frozendict(new_varnames),
    )


__all__ = ["splice"]
