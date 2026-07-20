"""The quotation overlay — **Stage ⓪ of mention-ascent**.

**Additive. Touches no protected module.** Design of record:
``docs/SECOND_ORDER_CORE_OPENING.md`` §5 step 1 (the overlay stratum) under the
crossing verdicts of 2026-07-16 (``docs/CROSSING_DECISION_BRIEFS.md``): decision A
ratified the predicative comprehension floor with the enclosure escape; decision B
crossed the frontier *exemplar-first*, staged overlay → B-min → B-full. This module
is the overlay rung — the strict prefix B-min promotes; nothing here is thrown away
at the core opening.

A *quotation* is Peirce's second-order device — a proposition-sorted line that
names a whole graph (the dotted oval's contents) — modelled exactly as
``reference_node`` models a reference: an ordinary first-order element in the host
graph (the name's line of identity) plus an **overlay record**
(:class:`QuotationMark`) kept *beside* the EGI, the way annotations and layout
deltas are, so the protected data model is untouched. The law it must satisfy is
:mod:`second_order_check`'s S1–S5; this module supplies the production shapes —
mark, resolver seam, candidate bridge, boundary hooks, glyph feed — and leaves the
harness the single source of the law.

What Stage ⓪ honestly is and is not:

* **Is:** drawable (the host carries real ink for the *name*; the glyph decorates
  it), resolvable (the quoted graph recovers, S2), stratified (S1 reads the drawn
  enclosure of the name's line), trajectory-honest (S5 per state), horizon-honest
  (S4). The quoted graph itself attests full first-order §3.3 one level down.
* **Is not:** asserted second-order ink. The sort lives in the overlay, not the
  drawing, so S3 (read-back one order up) stays **skip-named** — the harness
  reports it as an honest limit, never a silent pass. S3 flips to checked at
  stage ① (B-min: sort-on-incidence + the second-order reader).

Mention, not use: resolving a quotation only *produces* the quoted graph for
checking — it never splices it into the host (contrast ``reference_node``, whose
resolution is co-assertion). A quotation asserts nothing about its object beyond
what the host's ordinary first-order ink says; the quoted graph is present
*without force* (the third tense of docs/M_RESIDENCE_AND_THE_VALIDITY_DISCIPLINE
§5). That is why the overlay is safe cross-UoD where increment-2 *use* is not.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol, Sequence, runtime_checkable

import eg_navigation as nav
from eg_navigation import same_graph
from egi_core_dau import ElementID, RelationalGraphWithCuts, create_empty_graph
from egif_parser_dau import parse_egif
from presentation_ops import element_area
from second_order_check import (
    SORT_PROPOSITION,
    Quotation,
    QuotationReport,
    TrajectoryQuotationReport,
    attest_quotation,
    attest_quotation_trajectory,
    run_quotation,
    run_quotation_trajectory,
)
from world_scroll import _copy_area, m_view


# --------------------------------------------------------------------------- #
# The overlay record — quotation-ness + provenance, kept beside the EGI.
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class QuotationMark:
    """One quotation, recorded as an overlay on a host EGI's element.

    ``element_id`` is the proposition-sorted *name* in the host — the line of
    identity (vertex) whose label names the quoted graph (a predicate spot works
    too; the glyph decorates whichever it is). ``sort`` is the second-order sort
    the line carries (:data:`second_order_check.SORT_PROPOSITION` /
    ``SORT_ABSTRACTION``). ``kind`` is the target family a resolver serves
    (``"egif"`` / ``"chain-step"`` / ``"uod"``); ``target`` names the quoted
    graph in that family's address form. ``origin`` locates the target's home
    for provenance, and ``warrant`` defaults to ``"low"`` — a quotation is a
    *mention*, not a truth-claim about its object. ``impredicative`` is the
    explicit S1 override for the transitive reach-back case (``None`` = let the
    harness detect the direct self-quote structurally).

    The mark is *not* part of the EGI — it serialises (``to_dict``/``from_dict``)
    so a UoD can persist its quotations the way it persists annotations
    (``quotations.json``), with no change to the protected data model. Whether
    the name is drawn *enclosed* (S1's stratification input) is **never stored**:
    it is read off the host's drawn area at check time — the picture, not a
    field, decides (the honest-picture principle).
    """

    element_id: ElementID
    target: str
    sort: str = SORT_PROPOSITION
    kind: str = "egif"
    origin: Optional[str] = None
    warrant: str = "low"
    impredicative: Optional[bool] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "element_id": self.element_id,
            "target": self.target,
            "sort": self.sort,
            "kind": self.kind,
            "origin": self.origin,
            "warrant": self.warrant,
            "impredicative": self.impredicative,
            "extra": dict(self.extra),
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "QuotationMark":
        return cls(
            element_id=d["element_id"],
            target=d["target"],
            sort=d.get("sort", SORT_PROPOSITION),
            kind=d.get("kind", "egif"),
            origin=d.get("origin"),
            warrant=d.get("warrant", "low"),
            impredicative=d.get("impredicative"),
            extra=dict(d.get("extra", {})),
        )


def quotation_marks_to_list(marks: Sequence[QuotationMark]) -> List[Dict[str, Any]]:
    """Serialise marks for ``quotations.json`` (mirror of ``annotations_to_list``)."""
    return [m.to_dict() for m in marks]


def quotation_marks_from_list(items: Sequence[Dict[str, Any]]) -> List[QuotationMark]:
    """Rehydrate marks from ``quotations.json`` (mirror of ``annotations_from_list``)."""
    return [QuotationMark.from_dict(d) for d in items]


# --------------------------------------------------------------------------- #
# Reading the drawn host — enclosure and subgraph lifting.
# --------------------------------------------------------------------------- #

def is_enclosed(egi: RelationalGraphWithCuts, element_id: ElementID) -> bool:
    """Whether ``element_id`` is drawn under ≥ 1 cut in ``egi`` — S1's
    stratification input, read off the drawing, never stored. Raises
    ``ValueError`` for an element the host does not contain (a mark must
    decorate real ink)."""
    cut_ids = {c.id for c in egi.Cut}
    if element_id in cut_ids:
        # a cut's own residence is its parent area
        for area_id, contents in egi.area.items():
            if element_id in contents:
                return area_id != egi.sheet
        return False
    area = element_area(egi).get(element_id)
    if area is None:
        raise ValueError(f"element {element_id!r} is not in the host graph")
    return area != egi.sheet


def lift_cut(egi: RelationalGraphWithCuts, cut_id: ElementID) -> RelationalGraphWithCuts:
    """The cut's whole subtree as a standalone graph — the quoted object a
    dotted oval holds, recovered structurally (ids preserved; the same copy
    machinery ``world_scroll.m_view`` trusts)."""
    cut = next((c for c in egi.Cut if c.id == cut_id), None)
    if cut is None:
        raise ValueError(f"cut {cut_id!r} is not in the graph")
    view = create_empty_graph()
    view = view.with_cut(cut, context_id=view.sheet)
    return _copy_area(egi, view, cut_id, cut_id)


def lift_quotation(
    egi: RelationalGraphWithCuts, cut_id: ElementID
) -> RelationalGraphWithCuts:
    """The quoted graph a quotation oval holds — the oval's *contents* as a
    standalone graph (ids preserved). Contrast :func:`lift_cut`, which keeps
    the cut itself as the root: right for recovering a law-shaped *negation*,
    wrong for an oval, whose dotted curve is the quotation device itself, not
    part of the quoted object."""
    if cut_id not in egi.quotation:
        raise ValueError(f"cut {cut_id!r} is not a quotation area")
    view = create_empty_graph()
    return _copy_area(egi, view, cut_id, view.sheet)


def find_cut_matching(
    egi: RelationalGraphWithCuts, shape: RelationalGraphWithCuts
) -> Optional[ElementID]:
    """The first cut (deterministic id order) whose lifted subtree is
    ``same_graph`` to ``shape`` — how a law-shaped quotation finds its object
    on a drawn sheet. ``None`` when the shape is not scribed (the caller's
    honest horizon). A cut whose subtree is not self-contained (an edge
    reaching a sibling-area vertex) simply never matches."""
    for cut_id in sorted(c.id for c in egi.Cut):
        try:
            if same_graph(lift_cut(egi, cut_id), shape):
                return cut_id
        except Exception:
            continue
    return None


# --------------------------------------------------------------------------- #
# The resolver seam — target family → quoted graph (mirrors reference_node's).
# --------------------------------------------------------------------------- #

@runtime_checkable
class QuotationResolver(Protocol):
    """Resolves a mark's ``target`` to the quoted graph. ``kind`` names the
    target family served, so :class:`ChainQuotationResolver` can dispatch.
    Resolution *produces* the graph for checking — it never splices it into
    the host (mention, not use)."""

    kind: str

    def can_resolve(self, mark: QuotationMark) -> bool: ...

    def resolve(self, mark: QuotationMark) -> RelationalGraphWithCuts: ...


class EGIFQuotationResolver:
    """``target`` is EGIF text — the quoted graph inline (the harness's own
    candidate idiom, and the forcing exemplar's φ)."""

    kind = "egif"

    def can_resolve(self, mark: QuotationMark) -> bool:
        try:
            parse_egif(mark.target)
            return True
        except Exception:
            return False

    def resolve(self, mark: QuotationMark) -> RelationalGraphWithCuts:
        return parse_egif(mark.target)


class ChainStepQuotationResolver:
    """``target`` is ``"uod_id#step_id"`` — the quoted graph is what the named
    chain step *records* (its ``subgraph_egif`` / ``fact_egif`` / ``rule_egif``,
    the audit lens's coalesce order). The swan exhibit's resolver: the
    withdrawal step names exactly what it withdrew, so the quotation resolves
    against the record — checkable forever against the states themselves."""

    kind = "chain-step"
    _FIELDS = ("subgraph_egif", "fact_egif", "rule_egif")

    def __init__(self, tomos):
        self.tomos = tomos

    def _step_egif(self, mark: QuotationMark) -> Optional[str]:
        uod_id, sep, step_id = mark.target.partition("#")
        if not sep:
            return None
        chain = self.tomos.load_chain(uod_id)
        if chain is None:
            return None
        for step in chain.steps:
            if step.step_id == step_id:
                prm = step.parameters or {}
                for f in self._FIELDS:
                    if prm.get(f):
                        return prm[f]
        return None

    def can_resolve(self, mark: QuotationMark) -> bool:
        egif = self._step_egif(mark)
        if egif is None:
            return False
        try:
            parse_egif(egif)
            return True
        except Exception:
            return False

    def resolve(self, mark: QuotationMark) -> RelationalGraphWithCuts:
        egif = self._step_egif(mark)
        if egif is None:
            raise ValueError(
                f"chain step {mark.target!r} not found or carries no recorded EGIF")
        return parse_egif(egif)


class UoDQuotationResolver:
    """``target`` is ``"uod_id"`` (the current graph) or ``"uod_id@state_id"``
    (one state of its chain) — the cross-UoD **mention** side of the
    increment-2 fork, exercised overlay-first: naming a corpus graph as object
    without importing a single element of it."""

    kind = "uod"

    def __init__(self, tomos):
        self.tomos = tomos

    def _graph(self, mark: QuotationMark) -> Optional[RelationalGraphWithCuts]:
        uod_id, sep, state_id = mark.target.partition("@")
        if sep:
            chain = self.tomos.load_chain(uod_id)
            return None if chain is None else chain.states.get(state_id)
        uod = self.tomos.load_uod(uod_id)
        return None if uod is None else uod.current_egi

    def can_resolve(self, mark: QuotationMark) -> bool:
        return self._graph(mark) is not None

    def resolve(self, mark: QuotationMark) -> RelationalGraphWithCuts:
        g = self._graph(mark)
        if g is None:
            raise ValueError(f"UoD target {mark.target!r} did not resolve")
        return g


class ChainQuotationResolver:
    """Dispatch by mark ``kind`` first, then by ``can_resolve`` — the seam that
    lets new target families drop in without touching callers (mirrors
    ``reference_node.ChainReferenceResolver``)."""

    kind = "chain"

    def __init__(self, *resolvers: QuotationResolver):
        self.resolvers = resolvers

    def _pick(self, mark: QuotationMark) -> Optional[QuotationResolver]:
        for r in self.resolvers:
            if getattr(r, "kind", None) == mark.kind and r.can_resolve(mark):
                return r
        for r in self.resolvers:
            if r.can_resolve(mark):
                return r
        return None

    def can_resolve(self, mark: QuotationMark) -> bool:
        return self._pick(mark) is not None

    def resolve(self, mark: QuotationMark) -> RelationalGraphWithCuts:
        r = self._pick(mark)
        if r is None:
            raise ValueError(f"no resolver can resolve quotation {mark.target!r}")
        return r.resolve(mark)


# --------------------------------------------------------------------------- #
# Scribing a quotation into the core (stage ① B-min) and projecting it away.
# --------------------------------------------------------------------------- #

def scribe_quotation(
    host: RelationalGraphWithCuts,
    name_label: str,
    quoted: RelationalGraphWithCuts,
    *,
    context_id: Optional[ElementID] = None,
    sort: str = SORT_PROPOSITION,
    target: Optional[str] = None,
    kind: str = "egif",
    origin: Optional[str] = None,
    warrant: str = "low",
    **extra: Any,
) -> tuple:
    """Draw a full quotation into ``host``: a sorted name vertex + a
    quotation-flagged oval holding ``quoted``'s ink (ids preserved via the
    same ``_copy_area`` machinery ``m_view`` trusts).

    The core half is ``with_quotation`` (the B-min constructor); this helper
    adds the ink filling and the Stage-⓪ provenance mark (``target`` defaults
    to the quoted graph's own EGIF, so every scribed quotation stays
    resolvable). Returns ``(new_host, mark, quotation_cut_id)``.

    Contrast :func:`mark_quotation`, which decorates *existing* ink; and note
    the cross-UoD mention case does not scribe at all — a whole other
    universe cannot inline, so its name gets ``with_sort`` only and the oval
    stays a named horizon (S4)."""
    from egi_core_dau import create_vertex
    from egif_generator_dau import generate_egif

    name = create_vertex(label=name_label, is_generic=False)
    new_host = host.with_quotation(
        name,
        context_id=context_id if context_id is not None else host.sheet,
        sort_name=sort,
    )
    cut_id = next(cid for cid, vid in new_host.quotation.items() if vid == name.id)
    new_host = _copy_area(quoted, new_host, quoted.sheet, cut_id)
    mark = QuotationMark(
        element_id=name.id,
        target=target if target is not None else generate_egif(quoted).strip(),
        sort=sort,
        kind=kind,
        origin=origin,
        warrant=warrant,
        extra=dict(extra),
    )
    return new_host, mark, cut_id


def quote_existing_name(
    host: RelationalGraphWithCuts,
    name_vid: ElementID,
    quoted: RelationalGraphWithCuts,
    *,
    sort: str = SORT_PROPOSITION,
) -> tuple:
    """The conversion form of :func:`scribe_quotation`: an *existing* drawn
    name (typically a constant argument of a host relation) gains the sort
    and a quotation oval holding ``quoted``'s ink, drawn in the name's own
    area (the core's same-area attachment invariant). Returns
    ``(new_host, quotation_cut_id)``."""
    from egi_core_dau import create_cut

    area = element_area(host).get(name_vid)
    if area is None:
        raise ValueError(f"vertex {name_vid!r} is not in the host graph")
    cut = create_cut()
    g = host.with_cut(cut, area)
    g = g.with_quotation_binding(name_vid, cut.id, sort_name=sort)
    return _copy_area(quoted, g, quoted.sheet, cut.id), cut.id


# The explicit chain step for scribing a quotation (B-min). Registered
# NEUTRAL in proof_character: a mention adds no asserted content — the oval
# exhibits its ink without force, the way a PEEL records an act, not an
# inference.
QUOTE = "QUOTE"


def quote_step(
    pc,
    name_label: str,
    quoted_egif: str,
    *,
    sort: str = SORT_PROPOSITION,
    note: Optional[str] = None,
    branch: Optional[str] = None,
):
    """Scribe a quotation onto the chain's current state as an explicit
    ``QUOTE`` step: the labeled constant (already drawn) gains the sort and a
    dotted oval holding ``quoted_egif``'s ink — present without force. The
    locator resolves against the current state, ``proof_authoring``'s idiom."""
    quoted = parse_egif(quoted_egif)

    def transform(g):
        vid = nav.vertex_by_label(g, name_label)
        new_g, _cut_id = quote_existing_name(g, vid, quoted, sort=sort)
        return new_g

    params = {
        "act": "quotation",
        "earned": True,
        "derivation": ["with_quotation_binding"],
        "name_label": name_label,
        "sort": sort,
        "quoted_egif": quoted_egif,
    }
    return pc.apply_derived(
        QUOTE, transform, note=note or f"quote ⌜{name_label}⌝", params=params,
        branch=branch)


def sort_step(
    pc,
    name_label: str,
    *,
    sort: str = SORT_PROPOSITION,
    target: Optional[str] = None,
    note: Optional[str] = None,
    branch: Optional[str] = None,
):
    """The oval-less half of ``QUOTE`` — a cross-UoD mention's name gains the
    core sort but no quotation area (a whole other universe cannot inline;
    the quoted graph stays a resolver-served, S4-named horizon)."""

    def transform(g):
        return g.with_sort(nav.vertex_by_label(g, name_label), sort)

    params = {
        "act": "quotation",
        "earned": True,
        "derivation": ["with_sort"],
        "name_label": name_label,
        "sort": sort,
    }
    if target is not None:
        params["cross_uod_target"] = target
    return pc.apply_derived(
        QUOTE, transform, note=note or f"sort ⌜{name_label}⌝ (mention by name)",
        params=params, branch=branch)


def project_first_order(egi: RelationalGraphWithCuts) -> RelationalGraphWithCuts:
    """Strip the quotation layer: every quotation removed atomically
    (``without_quotation``), every residual sort dropped — what the graph
    asserts *first-order*. The A3 erasure projection: the conservativity gate
    demands the projection's verdicts equal the quotation-bearing graph's
    (the quoted layer licenses nothing)."""
    g = egi
    while g.quotation:
        g = g.without_quotation(sorted(g.quotation)[0])
    if g.sort:
        import dataclasses

        from frozendict import frozendict

        g = dataclasses.replace(g, sort=frozendict())
    return g


# --------------------------------------------------------------------------- #
# Authoring, bridging, and attesting a quotation.
# --------------------------------------------------------------------------- #

def mark_quotation(
    host: RelationalGraphWithCuts,
    element_id: ElementID,
    target: str,
    resolver: QuotationResolver,
    *,
    sort: str = SORT_PROPOSITION,
    kind: Optional[str] = None,
    origin: Optional[str] = None,
    warrant: str = "low",
    impredicative: Optional[bool] = None,
    **extra: Any,
) -> QuotationMark:
    """Record ``element_id`` (real ink in ``host``) as a quotation of ``target``.

    Refuses an element the host does not draw, and a target the resolver cannot
    resolve (no silent dangling quotation — the S4 honest-horizon floor, exactly
    as ``mark_reference`` refuses)."""
    mark = QuotationMark(
        element_id=element_id,
        target=target,
        sort=sort,
        kind=kind if kind is not None else getattr(resolver, "kind", "egif"),
        origin=origin,
        warrant=warrant,
        impredicative=impredicative,
        extra=dict(extra),
    )
    is_enclosed(host, element_id)  # raises if the element is not drawn in host
    if not resolver.can_resolve(mark):
        raise ValueError(
            f"target {target!r} is not resolvable by "
            f"{getattr(resolver, 'kind', '?')!r} resolver")
    return mark


def quotation_candidate(
    host: RelationalGraphWithCuts,
    mark: QuotationMark,
    resolver: QuotationResolver,
    *,
    quoted_ground: Optional[RelationalGraphWithCuts] = None,
    read_back: Optional[Callable] = None,
    unresolved: Sequence[str] = (),
) -> Quotation:
    """Build the :class:`second_order_check.Quotation` for ``mark`` so the law
    can be attested.

    ``enclosed`` is read off the *drawn* host (never a stored field). Pass
    ``quoted_ground`` (an *independently obtained* quoted graph) for the full
    S2 check — the offline correctness proof, used by tests and builders against
    ground truth. At a production boundary there is no independent path, so it
    defaults to the resolved graph (S2's structural half trivially holds) and
    the meaningful runtime teeth are S1 (stratification off the drawing) + S2's
    §3.3 half (the quoted graph attests one level down). ``read_back`` stays
    ``None`` at Stage ⓪ — S3 is the frontier; the harness names the skip."""
    resolved = resolver.resolve(mark)
    return Quotation(
        name=mark.target,
        sort=mark.sort,
        host=host,
        resolve=lambda r=resolved: r,
        quoted_ground=quoted_ground if quoted_ground is not None else resolved,
        enclosed=is_enclosed(host, mark.element_id),
        impredicative=mark.impredicative,
        read_back=read_back,
        unresolved=tuple(unresolved),
    )


def attest_quotation_mark(
    host: RelationalGraphWithCuts,
    mark: QuotationMark,
    resolver: QuotationResolver,
    *,
    layout_fn=None,
    attest_fn=None,
    quoted_ground: Optional[RelationalGraphWithCuts] = None,
    read_back: Optional[Callable] = None,
    context: Optional[str] = None,
) -> None:
    """Boundary hook: raise ``SecondOrderViolation`` if the marked quotation
    breaks the law (S2's §3.3 half needs ``layout_fn``; S3 runs iff
    ``read_back`` is supplied — ``second_order_reader.read_quotation_back``
    for a core-carried quotation), else None. The quotation analogue of
    ``attest_reference``."""
    cand = quotation_candidate(host, mark, resolver, quoted_ground=quoted_ground,
                               read_back=read_back)
    attest_quotation(cand, layout_fn=layout_fn, attest_fn=attest_fn,
                     context=context or mark.target)


def run_quotation_mark(
    host: RelationalGraphWithCuts,
    mark: QuotationMark,
    resolver: QuotationResolver,
    *,
    layout_fn=None,
    attest_fn=None,
    quoted_ground: Optional[RelationalGraphWithCuts] = None,
    read_back: Optional[Callable] = None,
) -> QuotationReport:
    """Non-raising measurement form — a structured report for a marked
    quotation (S3 runs iff ``read_back`` is supplied; its skip is otherwise
    named in ``honest_limits``)."""
    cand = quotation_candidate(host, mark, resolver, quoted_ground=quoted_ground,
                               read_back=read_back)
    return run_quotation(cand, layout_fn=layout_fn, attest_fn=attest_fn)


# --------------------------------------------------------------------------- #
# S5 — a law-shaped quotation over a diachronic trajectory.
# --------------------------------------------------------------------------- #

def trajectory_candidates(
    host: RelationalGraphWithCuts,
    mark: QuotationMark,
    shape_egif: str,
    states: Dict[str, RelationalGraphWithCuts],
) -> Dict[str, Optional[Quotation]]:
    """Per-state candidates for a quotation whose object is a *drawn law* on a
    diachronic trajectory (Cohen's R_G: the name's reference value per state).

    At each state the quoted object is recovered **structurally** — the cut in
    that state's M-view whose lifted subtree matches ``shape_egif`` — and
    checked against the independently parsed shape (two genuine paths, so S2
    has teeth at every state). A state not scribing the law maps to ``None``:
    the named horizon, never a failure (S4 one order up the trajectory).
    Feed the result to :func:`second_order_check.check_quotation_at_states` /
    the wrappers below."""
    shape = parse_egif(shape_egif)
    enclosed = is_enclosed(host, mark.element_id)
    out: Dict[str, Optional[Quotation]] = {}
    for sid, egi in states.items():
        view = m_view(egi)
        cut_id = find_cut_matching(view, shape)
        if cut_id is None:
            out[sid] = None
            continue
        lifted = lift_cut(view, cut_id)
        out[sid] = Quotation(
            name=f"{mark.target}@{sid}",
            sort=mark.sort,
            host=host,
            resolve=lambda g=lifted: g,
            quoted_ground=shape,
            enclosed=enclosed,
            impredicative=mark.impredicative,
        )
    return out


def attest_quotation_mark_trajectory(
    host: RelationalGraphWithCuts,
    mark: QuotationMark,
    shape_egif: str,
    states: Dict[str, RelationalGraphWithCuts],
    *,
    layout_fn=None,
    attest_fn=None,
    context: Optional[str] = None,
) -> None:
    """S5 boundary hook: raise ``SecondOrderViolation`` if the law-shaped
    quotation breaks S1–S3 at any state where it resolves; non-resolving
    states are horizon, not failures."""
    per_state = trajectory_candidates(host, mark, shape_egif, states)
    attest_quotation_trajectory(
        mark.target, per_state, layout_fn=layout_fn, attest_fn=attest_fn,
        context=context or mark.target)


def run_quotation_mark_trajectory(
    host: RelationalGraphWithCuts,
    mark: QuotationMark,
    shape_egif: str,
    states: Dict[str, RelationalGraphWithCuts],
    *,
    layout_fn=None,
    attest_fn=None,
) -> TrajectoryQuotationReport:
    """Non-raising S5 measurement form — ``checked_states`` are where the law
    stood, ``unresolved_states`` the named horizon."""
    per_state = trajectory_candidates(host, mark, shape_egif, states)
    return run_quotation_trajectory(
        mark.target, per_state, layout_fn=layout_fn, attest_fn=attest_fn)


# --------------------------------------------------------------------------- #
# The glyph feed — what the renderer's ``quotation_marks=`` consumes.
# --------------------------------------------------------------------------- #

def quotation_horizon(mark: QuotationMark, resolver: QuotationResolver) -> int:
    """How many elements the dotted oval holds *beyond the view* — the quoted
    graph's element count, shown as the glyph's ``⌜+N⌝`` badge (the reference
    glyph's horizon idiom, one order up)."""
    g = resolver.resolve(mark)
    return len(g.V) + len(g.E) + len(g.Cut)


def render_quotation_marks(
    marks: Sequence[QuotationMark], resolver: QuotationResolver
) -> Dict[ElementID, Dict[str, Any]]:
    """Build the ``{element_id: {"sort", "horizon"}}`` map
    ``simple_svg_renderer``'s ``quotation_marks`` parameter consumes — one
    entry per quoting name. Pure chrome: reads the overlay, never the EGI,
    changes no DTO geometry."""
    return {
        m.element_id: {"sort": m.sort, "horizon": quotation_horizon(m, resolver)}
        for m in marks
    }


__all__ = [
    "QuotationMark",
    "quotation_marks_to_list",
    "quotation_marks_from_list",
    "is_enclosed",
    "lift_cut",
    "lift_quotation",
    "find_cut_matching",
    "scribe_quotation",
    "quote_existing_name",
    "QUOTE",
    "quote_step",
    "sort_step",
    "project_first_order",
    "QuotationResolver",
    "EGIFQuotationResolver",
    "ChainStepQuotationResolver",
    "UoDQuotationResolver",
    "ChainQuotationResolver",
    "mark_quotation",
    "quotation_candidate",
    "attest_quotation_mark",
    "run_quotation_mark",
    "trajectory_candidates",
    "attest_quotation_mark_trajectory",
    "run_quotation_mark_trajectory",
    "quotation_horizon",
    "render_quotation_marks",
]
