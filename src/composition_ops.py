"""Regime-1 composition ops — the server half of the Ergasterion palette.

Composition (regime 1, ``docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md`` §4) suspends
*soundness and assertion*, not *coherence*: every state the palette can reach
is a genuine ``RelationalGraphWithCuts``.  Each function here is a pure
``egi → ComposeResult`` rewrite over the public immutable constructors,
enforcing well-formedness (``docs/COMPOSITION_WORKFLOW_SPEC.md`` §3) and
raising ``ValueError`` with a readable message on refusal.  No protected
module is touched and no Dau rule is involved — these are *drawing* acts,
not inferences, which is exactly why they are only ever reachable while a
workshop session is in its ``composing`` phase.

Replay contract: every op accepts explicit ids for whatever it creates and
``apply_compose`` returns the parameters *with the generated ids filled in*
(``ComposeResult.recorded_parameters``), so a recorded compose step re-executes
byte-stably from its parameters (``verify_chain_replay``).
"""

import uuid
from dataclasses import dataclass, field, replace
from typing import Any, Dict, List, Optional, Sequence, Tuple

from frozendict import frozendict

from egi_core_dau import (
    Cut,
    Edge,
    ElementID,
    RelationalGraphWithCuts,
    Vertex,
)
from eg_splice import graft


# --------------------------------------------------------------------------- #
# Result shape                                                                 #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ComposeResult:
    """The outcome of one palette action.

    ``created`` maps a role name (``"cut"``, ``"vertex"``, ``"edge"``,
    ``"placeholders"``, ``"elements"``) to the id(s) the op minted;
    ``removed`` lists ids the op deleted (erase cascade, attach pruning).
    ``recorded_parameters`` is the request parameters with every generated id
    filled in — the dict a chain step should persist so replay is exact.
    """

    egi: RelationalGraphWithCuts
    created: Dict[str, Any] = field(default_factory=dict)
    removed: Tuple[str, ...] = ()
    recorded_parameters: Dict[str, Any] = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Internal helpers                                                             #
# --------------------------------------------------------------------------- #


def _all_ids(egi: RelationalGraphWithCuts) -> set:
    return (
        {v.id for v in egi.V}
        | {e.id for e in egi.E}
        | {c.id for c in egi.Cut}
        | {egi.sheet}
    )


def _fresh_id(egi: RelationalGraphWithCuts, prefix: str) -> ElementID:
    used = _all_ids(egi)
    while True:
        candidate = f"{prefix}_{uuid.uuid4().hex[:8]}"
        if candidate not in used:
            return candidate


def _resolve_area(
    egi: RelationalGraphWithCuts, context_id: Optional[ElementID]
) -> ElementID:
    """Default to the sheet; refuse an unknown area with a readable message."""
    if context_id is None:
        return egi.sheet
    if context_id == egi.sheet or context_id in {c.id for c in egi.Cut}:
        return context_id
    raise ValueError(
        f"Area '{context_id}' does not exist — place into the sheet or an "
        f"existing cut."
    )


def _area_of(egi: RelationalGraphWithCuts, element_id: ElementID) -> ElementID:
    return egi.get_context(element_id)


def _ancestors_or_self(
    egi: RelationalGraphWithCuts, area_id: ElementID
) -> List[ElementID]:
    chain = [area_id]
    current = area_id
    while current != egi.sheet:
        current = egi.get_context(current)
        chain.append(current)
    return chain


def _same_or_enclosing(
    egi: RelationalGraphWithCuts, candidate: ElementID, reference: ElementID
) -> bool:
    """True iff ``candidate`` area is ``reference`` itself or encloses it."""
    return candidate in _ancestors_or_self(egi, reference)


def _check_hook_visibility(
    egi: RelationalGraphWithCuts, vertex_id: ElementID, edge_area: ElementID
) -> None:
    """Dau's context condition for composing (spec §3): an edge's hooks may
    reference only lines in its own or enclosing areas."""
    v_area = _area_of(egi, vertex_id)
    if not _same_or_enclosing(egi, v_area, edge_area):
        raise ValueError(
            f"Cannot wire to line '{vertex_id}': it lives in a sibling or "
            f"deeper cut.  A relation may only reach lines in its own area "
            f"or an enclosing one."
        )


def _keep_varnames(
    new: RelationalGraphWithCuts, old: RelationalGraphWithCuts
) -> RelationalGraphWithCuts:
    # The with_* constructors rebuild without variable_names; restore them so a
    # composed draft keeps the names its lines already carry.
    if old.variable_names and new.variable_names != old.variable_names:
        return replace(new, variable_names=old.variable_names)
    return new


def _extended_alphabet(egi: RelationalGraphWithCuts, name: str, arity: int):
    """Composing grows the vocabulary: declare a new relation name in the
    alphabet (when one is carried) rather than refusing it."""
    alph = egi.alphabet
    if alph is None or name in (alph.C | alph.F | alph.R):
        return alph
    return replace(
        alph,
        R=alph.R | {name},
        ar=frozendict({**dict(alph.ar), name: arity}),
    )


def _validate_context_condition(egi: RelationalGraphWithCuts) -> None:
    """Whole-graph check that every edge only reaches same-or-enclosing lines.

    Used by the move ops, where a single relocation can break the condition
    for edges far from the moved element (e.g. moving a cut whose interior
    edges reach an ambient line)."""
    for edge_id, seq in egi.nu.items():
        edge_area = _area_of(egi, edge_id)
        for vid in seq:
            if not _same_or_enclosing(egi, _area_of(egi, vid), edge_area):
                raise ValueError(
                    f"Move refused: relation '{egi.rel.get(edge_id, edge_id)}' "
                    f"({edge_id}) would reach line '{vid}' across a cut it "
                    f"does not sit inside."
                )


def _cut_subtree(
    egi: RelationalGraphWithCuts, cut_id: ElementID
) -> Tuple[set, set, set]:
    """All vertex / edge / cut ids inside ``cut_id`` (the cut itself included
    in the cut set)."""
    v_ids = {v.id for v in egi.V}
    e_ids = {e.id for e in egi.E}
    vs, es, cs = set(), set(), {cut_id}
    stack = [cut_id]
    while stack:
        area = stack.pop()
        for eid in egi.area.get(area, frozenset()):
            if eid in v_ids:
                vs.add(eid)
            elif eid in e_ids:
                es.add(eid)
            else:
                cs.add(eid)
                stack.append(eid)
    return vs, es, cs


def _rebuild_without(
    egi: RelationalGraphWithCuts,
    removed_v: set,
    removed_e: set,
    removed_c: set,
) -> RelationalGraphWithCuts:
    """Direct rebuild with the given elements gone — keeps every mapping
    consistent (no dangling ν, ρ, rel, variable_names, or area entries)."""
    removed = removed_v | removed_e | removed_c
    new_area = {}
    for ctx, elems in egi.area.items():
        if ctx in removed_c:
            continue
        new_area[ctx] = frozenset(e for e in elems if e not in removed)
    return RelationalGraphWithCuts(
        V=frozenset(v for v in egi.V if v.id not in removed_v),
        E=frozenset(e for e in egi.E if e.id not in removed_e),
        nu=frozendict(
            {eid: seq for eid, seq in egi.nu.items() if eid not in removed_e}
        ),
        sheet=egi.sheet,
        Cut=frozenset(c for c in egi.Cut if c.id not in removed_c),
        area=frozendict(new_area),
        rel=frozendict(
            {eid: n for eid, n in egi.rel.items() if eid not in removed_e}
        ),
        alphabet=egi.alphabet,
        rho=frozendict(
            {vid: n for vid, n in egi.rho.items() if vid not in removed_v}
        ),
        variable_names=frozendict(
            {
                vid: n
                for vid, n in egi.variable_names.items()
                if vid not in removed_v
            }
        ),
    )


def _is_placeholder_line(egi: RelationalGraphWithCuts, vertex_id: ElementID) -> bool:
    """A bare generic dot wired to nothing — the kind ``add_relation`` mints
    for an unfilled hook."""
    v = egi.get_vertex(vertex_id)
    if not v.is_generic or v.label is not None:
        return False
    if egi.rho.get(vertex_id) is not None:
        return False
    return all(vertex_id not in seq for seq in egi.nu.values())


# --------------------------------------------------------------------------- #
# Palette ops                                                                  #
# --------------------------------------------------------------------------- #


def add_cut(
    egi: RelationalGraphWithCuts,
    context_id: Optional[ElementID] = None,
    *,
    cut_id: Optional[ElementID] = None,
) -> ComposeResult:
    """Place an empty cut in an area."""
    area = _resolve_area(egi, context_id)
    new_id = cut_id or _fresh_id(egi, "c")
    if cut_id is not None and cut_id in _all_ids(egi):
        raise ValueError(f"Id '{cut_id}' is already in use.")
    new_egi = _keep_varnames(egi.with_cut(Cut(id=new_id), area), egi)
    return ComposeResult(
        egi=new_egi,
        created={"cut": new_id},
        recorded_parameters={"context_id": area, "cut_id": new_id},
    )


def add_line(
    egi: RelationalGraphWithCuts,
    context_id: Optional[ElementID] = None,
    *,
    vertex_id: Optional[ElementID] = None,
) -> ComposeResult:
    """Place a line of identity (a generic heavy dot) in an area."""
    area = _resolve_area(egi, context_id)
    new_id = vertex_id or _fresh_id(egi, "v")
    if vertex_id is not None and vertex_id in _all_ids(egi):
        raise ValueError(f"Id '{vertex_id}' is already in use.")
    new_egi = _keep_varnames(
        egi.with_vertex_in_context(
            Vertex(id=new_id, label=None, is_generic=True), area
        ),
        egi,
    )
    return ComposeResult(
        egi=new_egi,
        created={"vertex": new_id},
        recorded_parameters={"context_id": area, "vertex_id": new_id},
    )


def add_constant(
    egi: RelationalGraphWithCuts,
    label: str,
    context_id: Optional[ElementID] = None,
    *,
    vertex_id: Optional[ElementID] = None,
) -> ComposeResult:
    """Place a labelled (constant) spot in an area."""
    if not label or not str(label).strip():
        raise ValueError("A constant needs a non-empty label.")
    label = str(label).strip()
    area = _resolve_area(egi, context_id)
    new_id = vertex_id or _fresh_id(egi, "v")
    if vertex_id is not None and vertex_id in _all_ids(egi):
        raise ValueError(f"Id '{vertex_id}' is already in use.")
    new_egi = _keep_varnames(
        egi.with_vertex_in_context(
            Vertex(id=new_id, label=label, is_generic=False), area
        ),
        egi,
    )
    return ComposeResult(
        egi=new_egi,
        created={"vertex": new_id},
        recorded_parameters={
            "label": label,
            "context_id": area,
            "vertex_id": new_id,
        },
    )


def add_relation(
    egi: RelationalGraphWithCuts,
    name: str,
    context_id: Optional[ElementID] = None,
    hooks: Optional[Sequence[Optional[ElementID]]] = None,
    *,
    arity: Optional[int] = None,
    edge_id: Optional[ElementID] = None,
    placeholder_ids: Optional[Sequence[ElementID]] = None,
) -> ComposeResult:
    """Place a named relation spot with n hooks in an area.

    ``hooks`` gives, per argument position, either an existing line id or
    ``None`` — an unfilled hook, which (since ν must be total) is realized as
    a fresh generic placeholder line in the same area, ready to be welded by
    ``attach``.  ``arity`` alone is shorthand for that many unfilled hooks.
    Existing lines must be visible from the area (same or enclosing).
    """
    if not name or not str(name).strip():
        raise ValueError("A relation needs a non-empty name.")
    name = str(name).strip()
    area = _resolve_area(egi, context_id)
    if hooks is None:
        hooks = [None] * (arity if arity is not None else 1)
    hooks = list(hooks)

    v_ids = {v.id for v in egi.V}
    for h in hooks:
        if h is not None:
            if h not in v_ids:
                raise ValueError(f"Line '{h}' does not exist.")
            _check_hook_visibility(egi, h, area)

    new_edge_id = edge_id or _fresh_id(egi, "e")
    if edge_id is not None and edge_id in _all_ids(egi):
        raise ValueError(f"Id '{edge_id}' is already in use.")

    # Mint placeholder lines for the unfilled hooks, in the relation's area.
    placeholder_ids = list(placeholder_ids or [])
    placeholders: List[ElementID] = []
    work = egi
    sequence: List[ElementID] = []
    for h in hooks:
        if h is not None:
            sequence.append(h)
            continue
        pid = placeholder_ids[len(placeholders)] if len(placeholders) < len(
            placeholder_ids
        ) else _fresh_id(work, "v")
        work = work.with_vertex_in_context(
            Vertex(id=pid, label=None, is_generic=True), area
        )
        placeholders.append(pid)
        sequence.append(pid)

    alph = _extended_alphabet(work, name, len(sequence))
    if alph is not work.alphabet:
        work = replace(work, alphabet=alph)
    work = work.with_edge(Edge(id=new_edge_id), tuple(sequence), name, area)
    work = _keep_varnames(work, egi)

    return ComposeResult(
        egi=work,
        created={"edge": new_edge_id, "placeholders": list(placeholders)},
        recorded_parameters={
            "name": name,
            "context_id": area,
            "hooks": hooks,
            "edge_id": new_edge_id,
            "placeholder_ids": list(placeholders),
        },
    )


def attach(
    egi: RelationalGraphWithCuts,
    edge_id: ElementID,
    hook_index: int,
    vertex_id: ElementID,
    *,
    prune: bool = True,
) -> ComposeResult:
    """Wire a relation hook (0-based ``hook_index``) onto an existing line.

    If the hook previously held a bare placeholder dot (and ``prune`` is on),
    the orphan is removed — dragging a hook onto a real line *moves* it.
    """
    if edge_id not in {e.id for e in egi.E}:
        raise ValueError(f"Relation '{edge_id}' does not exist.")
    if vertex_id not in {v.id for v in egi.V}:
        raise ValueError(f"Line '{vertex_id}' does not exist.")
    seq = list(egi.nu[edge_id])
    if not (0 <= hook_index < len(seq)):
        raise ValueError(
            f"Hook {hook_index} is out of range for '{egi.rel[edge_id]}' "
            f"(arity {len(seq)})."
        )
    edge_area = _area_of(egi, edge_id)
    _check_hook_visibility(egi, vertex_id, edge_area)

    old_vid = seq[hook_index]
    if old_vid == vertex_id:
        return ComposeResult(
            egi=egi,
            recorded_parameters={
                "edge_id": edge_id,
                "hook_index": hook_index,
                "vertex_id": vertex_id,
                "prune": prune,
            },
        )
    seq[hook_index] = vertex_id
    new_nu = dict(egi.nu)
    new_nu[edge_id] = tuple(seq)
    work = replace(egi, nu=frozendict(new_nu))

    removed: Tuple[str, ...] = ()
    if prune and _is_placeholder_line(work, old_vid):
        work = _rebuild_without(work, {old_vid}, set(), set())
        removed = (old_vid,)

    return ComposeResult(
        egi=work,
        removed=removed,
        recorded_parameters={
            "edge_id": edge_id,
            "hook_index": hook_index,
            "vertex_id": vertex_id,
            "prune": prune,
        },
    )


def detach(
    egi: RelationalGraphWithCuts,
    edge_id: ElementID,
    hook_index: int,
    *,
    placeholder_id: Optional[ElementID] = None,
) -> ComposeResult:
    """Unplug a hook from its line: ν must stay total, so the hook gets a
    fresh placeholder dot in the relation's own area."""
    if edge_id not in {e.id for e in egi.E}:
        raise ValueError(f"Relation '{edge_id}' does not exist.")
    seq = list(egi.nu[edge_id])
    if not (0 <= hook_index < len(seq)):
        raise ValueError(
            f"Hook {hook_index} is out of range for '{egi.rel[edge_id]}' "
            f"(arity {len(seq)})."
        )
    area = _area_of(egi, edge_id)
    pid = placeholder_id or _fresh_id(egi, "v")
    if placeholder_id is not None and placeholder_id in _all_ids(egi):
        raise ValueError(f"Id '{placeholder_id}' is already in use.")
    work = egi.with_vertex_in_context(
        Vertex(id=pid, label=None, is_generic=True), area
    )
    seq[hook_index] = pid
    new_nu = dict(work.nu)
    new_nu[edge_id] = tuple(seq)
    work = _keep_varnames(replace(work, nu=frozendict(new_nu)), egi)
    return ComposeResult(
        egi=work,
        created={"vertex": pid},
        recorded_parameters={
            "edge_id": edge_id,
            "hook_index": hook_index,
            "placeholder_id": pid,
        },
    )


def rename(
    egi: RelationalGraphWithCuts, element_id: ElementID, name: str
) -> ComposeResult:
    """Rename a relation, or relabel a constant spot."""
    if not name or not str(name).strip():
        raise ValueError("The new name must be non-empty.")
    name = str(name).strip()

    if element_id in {e.id for e in egi.E}:
        alph = _extended_alphabet(egi, name, len(egi.nu[element_id]))
        new_rel = dict(egi.rel)
        new_rel[element_id] = name
        work = replace(egi, rel=frozendict(new_rel), alphabet=alph)
        return ComposeResult(
            egi=work,
            recorded_parameters={"element_id": element_id, "name": name},
        )

    if element_id in {v.id for v in egi.V}:
        old = egi.get_vertex(element_id)
        if old.is_generic:
            raise ValueError(
                "This is a line of identity, not a constant — lines have no "
                "name to edit."
            )
        new_V = frozenset(v for v in egi.V if v.id != element_id) | {
            Vertex(id=element_id, label=name, is_generic=False)
        }
        new_rho = dict(egi.rho)
        if element_id in new_rho:
            new_rho[element_id] = name
        work = replace(egi, V=new_V, rho=frozendict(new_rho))
        return ComposeResult(
            egi=work,
            recorded_parameters={"element_id": element_id, "name": name},
        )

    raise ValueError(f"Element '{element_id}' does not exist.")


def erase(
    egi: RelationalGraphWithCuts, element_id: ElementID
) -> ComposeResult:
    """Erase any element, cascading to dependents (spec §3):

    * a **line** takes every relation wired to it;
    * a **cut** takes its whole subtree;
    * a **relation** goes alone (its lines are first-class ink and stay).
    """
    v_ids = {v.id for v in egi.V}
    e_ids = {e.id for e in egi.E}
    c_ids = {c.id for c in egi.Cut}

    removed_v: set = set()
    removed_e: set = set()
    removed_c: set = set()

    if element_id in v_ids:
        removed_v.add(element_id)
    elif element_id in e_ids:
        removed_e.add(element_id)
    elif element_id in c_ids:
        vs, es, cs = _cut_subtree(egi, element_id)
        removed_v |= vs
        removed_e |= es
        removed_c |= cs
    else:
        raise ValueError(f"Element '{element_id}' does not exist.")

    # Cascade: any relation wired to a removed line goes with it.
    if removed_v:
        for eid, seq in egi.nu.items():
            if eid not in removed_e and any(vid in removed_v for vid in seq):
                removed_e.add(eid)

    work = _rebuild_without(egi, removed_v, removed_e, removed_c)
    removed = tuple(sorted(removed_v | removed_e | removed_c))
    return ComposeResult(
        egi=work,
        removed=removed,
        recorded_parameters={"element_id": element_id},
    )


def move_to_area(
    egi: RelationalGraphWithCuts,
    element_id: ElementID,
    context_id: ElementID,
) -> ComposeResult:
    """Logically relocate an element to another area — the composing-phase
    boundary-crossing drag (spec §2.2).  Refuses a relocation that would let
    any relation reach a line across a cut it does not sit inside, or nest a
    cut into its own interior."""
    area = _resolve_area(egi, context_id)
    v_ids = {v.id for v in egi.V}
    e_ids = {e.id for e in egi.E}
    c_ids = {c.id for c in egi.Cut}

    if element_id in v_ids:
        work = egi.with_vertex_moved_to_context(element_id, area)
        work = _keep_varnames(work, egi)
    elif element_id in e_ids:
        old_area = _area_of(egi, element_id)
        if old_area == area:
            work = egi
        else:
            new_area_map = dict(egi.area)
            new_area_map[old_area] = new_area_map[old_area] - {element_id}
            new_area_map[area] = new_area_map.get(area, frozenset()) | {
                element_id
            }
            work = replace(
                egi, area=frozendict(new_area_map), hierarchical_index=None
            )
    elif element_id in c_ids:
        if area == element_id or element_id in _ancestors_or_self(egi, area):
            raise ValueError(
                "Cannot move a cut into itself or its own interior."
            )
        old_area = _area_of(egi, element_id)
        if old_area == area:
            work = egi
        else:
            new_area_map = dict(egi.area)
            new_area_map[old_area] = new_area_map[old_area] - {element_id}
            new_area_map[area] = new_area_map.get(area, frozenset()) | {
                element_id
            }
            work = replace(
                egi, area=frozendict(new_area_map), hierarchical_index=None
            )
    else:
        raise ValueError(f"Element '{element_id}' does not exist.")

    _validate_context_condition(work)
    return ComposeResult(
        egi=work,
        recorded_parameters={"element_id": element_id, "context_id": area},
    )


def graft_fragment(
    egi: RelationalGraphWithCuts,
    egif: str,
    context_id: Optional[ElementID] = None,
) -> ComposeResult:
    """The power-user Fragment tool: parse EGIF text and graft it into an
    area (disjoint, α-renamed — ``eg_splice.graft``)."""
    if not egif or not egif.strip():
        raise ValueError("Fragment needs non-empty EGIF text.")
    area = _resolve_area(egi, context_id)
    from egif_parser_dau import parse_egif

    try:
        fragment = parse_egif(egif)
    except Exception as exc:
        raise ValueError(f"EGIF did not parse: {exc}") from exc
    work = graft(egi, fragment, context=area)
    created = sorted(_all_ids(work) - _all_ids(egi))
    return ComposeResult(
        egi=work,
        created={"elements": created},
        recorded_parameters={"egif": egif, "context_id": area},
    )


# --------------------------------------------------------------------------- #
# Dispatcher + replay                                                          #
# --------------------------------------------------------------------------- #

# Chain steps namespace compose actions as ``compose.<action>``.
COMPOSE_STEP_PREFIX = "compose."

# Gate steps (recorded but graph-identity): the two fixings.
FIX_GRAPH_STEP = "compose.fix_graph"
FIX_CHAIN_STEP = "chain.fix"


def apply_compose(
    egi: RelationalGraphWithCuts, action: str, parameters: Dict[str, Any]
) -> ComposeResult:
    """Execute one palette action by name — the single dispatch shared by the
    ``/compose`` route and chain replay.  ``action`` may carry the
    ``compose.`` namespace or not."""
    if action.startswith(COMPOSE_STEP_PREFIX):
        action = action[len(COMPOSE_STEP_PREFIX):]
    p = parameters or {}
    if action == "add_cut":
        return add_cut(egi, p.get("context_id"), cut_id=p.get("cut_id"))
    if action == "add_line":
        return add_line(egi, p.get("context_id"), vertex_id=p.get("vertex_id"))
    if action == "add_constant":
        return add_constant(
            egi,
            p.get("label", ""),
            p.get("context_id"),
            vertex_id=p.get("vertex_id"),
        )
    if action == "add_relation":
        return add_relation(
            egi,
            p.get("name", ""),
            p.get("context_id"),
            p.get("hooks"),
            arity=p.get("arity"),
            edge_id=p.get("edge_id"),
            placeholder_ids=p.get("placeholder_ids"),
        )
    if action == "attach":
        return attach(
            egi,
            p.get("edge_id", ""),
            int(p.get("hook_index", 0)),
            p.get("vertex_id", ""),
            prune=bool(p.get("prune", True)),
        )
    if action == "detach":
        return detach(
            egi,
            p.get("edge_id", ""),
            int(p.get("hook_index", 0)),
            placeholder_id=p.get("placeholder_id"),
        )
    if action == "rename":
        return rename(egi, p.get("element_id", ""), p.get("name", ""))
    if action == "erase":
        return erase(egi, p.get("element_id", ""))
    if action == "move_to_area":
        return move_to_area(
            egi, p.get("element_id", ""), p.get("context_id", "")
        )
    if action == "graft":
        return graft_fragment(egi, p.get("egif", ""), p.get("context_id"))
    raise ValueError(f"Unknown compose action '{action}'.")


def _same_state(
    a: RelationalGraphWithCuts, b: RelationalGraphWithCuts
) -> bool:
    """Exact (id-level) state equality — the byte-stable replay check."""
    return (
        a.V == b.V
        and a.E == b.E
        and a.nu == b.nu
        and a.sheet == b.sheet
        and a.Cut == b.Cut
        and a.area == b.area
        and a.rel == b.rel
        and a.rho == b.rho
    )


def verify_chain_replay(chain) -> int:
    """Re-execute every step of a persisted chain from its stored ``from``
    snapshot and require it to reproduce the stored ``to`` snapshot.

    Compose steps replay through :func:`apply_compose` (exact, id-stable —
    generated ids are recorded in the step's parameters).  Gate steps are
    graph-identity.  The six Dau rules replay through
    ``proof_authoring.replay_step`` and are compared by isomorphism
    (``eg_navigation.same_graph``), since the engine mints fresh ids.

    Returns the number of steps verified; raises ``ValueError`` naming the
    first step that fails to reproduce its state.
    """
    from eg_navigation import same_graph
    from proof_authoring import replay_step

    verified = 0
    for step in chain.steps:
        from_egi = chain.states[step.from_state_id]
        to_egi = chain.states[step.to_state_id]
        name = step.rule_name
        if name in (FIX_GRAPH_STEP, FIX_CHAIN_STEP):
            ok = _same_state(from_egi, to_egi)
        elif name.startswith(COMPOSE_STEP_PREFIX):
            result = apply_compose(from_egi, name, step.parameters)
            ok = _same_state(result.egi, to_egi)
        else:
            params = dict(step.parameters or {})
            replayed = replay_step(
                from_egi,
                {
                    "rule": name,
                    "selection": params.get(
                        "selection", params.get("selected_elements")
                    ),
                    "egif_content": params.get("egif_content"),
                    "target_area": params.get("target_area"),
                },
            )
            ok = same_graph(replayed, to_egi)
        if not ok:
            raise ValueError(
                f"Replay diverged at step '{step.step_id}' ({name}): the "
                f"recorded parameters do not reproduce state "
                f"'{step.to_state_id}'."
            )
        verified += 1
    return verified


__all__ = [
    "ComposeResult",
    "COMPOSE_STEP_PREFIX",
    "FIX_GRAPH_STEP",
    "FIX_CHAIN_STEP",
    "add_cut",
    "add_line",
    "add_constant",
    "add_relation",
    "attach",
    "detach",
    "rename",
    "erase",
    "move_to_area",
    "graft_fragment",
    "apply_compose",
    "verify_chain_replay",
]
