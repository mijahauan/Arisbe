"""
Model materialization — make a domain model M as full as our logic allows.

Design-of-record: ``docs/DOMAIN_ORACLE_AND_M.md`` §6.1; the conceptual question it
answers ("what is a model?") is ``docs/GENERATION_AND_TESTING.md`` clarification 1.

A **model** is the facts — the extension over a domain.  **Rules** belong to a
*theory*.  The semantic game (the peel) model-*checks* G against the facts; it does
not run rules.  To honour "make M as full as possible," author M as *facts + rules*
and **materialize** it here: forward-chain the **Horn fragment** to the **least
Herbrand model** (the closure of everything the rules entail over the facts), and
hand *that* extensional model to the peel.  Model-checking stays pure and decidable;
the rules merely fill out the world.

`materialize_egi(egi) → (facts_egi, report)`:

- **Facts** (sheet-level atoms) pass straight through.
- A **Horn rule** is a sheet-level scroll ``~[ B ~[ H ] ]`` (= *B → H*) where B and H
  are conjunctions of atoms and every line of identity in H also occurs in B
  (**range-restricted** — no fresh existential individual in the head).  These are
  forward-chained to a fixpoint (termination guaranteed: function-free,
  range-restricted rules coin no new individuals — Datalog).
- Everything else is **left to the contest/deduction game** and named in the report,
  never silently dropped: a negation in the head (a cut inside H), a disjunctive or
  complex body (≠1 nested cut), an existential head (a head line not bound in the
  body), and a bare denial ``~[ atoms ]`` (a negative fact, not a forward rule).

Soundness: the least Herbrand model is the unique minimal model of the Horn theory,
so model-checking a positive query against it equals the theory's entailment.  For
queries with cuts (negation) this is closed-world / stratified-negation — which is
why materialization pairs with the **closed** regime: materialize, then close, then
peel.

Scope of this first step: sheet-level rules only (a rule nested inside another cut is
reported, not applied).  Generic (anonymous) individuals are named with synthetic
constants in the output, which is semantically transparent to model-checking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

from egi_core_dau import (
    Edge,
    RelationalGraphWithCuts,
    Vertex,
    create_empty_graph,
)

# An individual key: ("c", label) for a named constant, ("g", vertex_id) for a
# generic line of identity (an anonymous-but-distinct individual).
Key = Tuple[str, str]
# An atom in the fact base: (relation_name, (individual_key, ...)).
Fact = Tuple[str, Tuple[Key, ...]]


@dataclass(frozen=True)
class SkippedRule:
    """A rule materialization could not apply, with the reason — left to the
    contest/deduction game."""

    reason: str          # negation_in_head | existential_head | complex_body | denial
    description: str     # a short EGIF-ish rendering of the rule


@dataclass
class MaterializationReport:
    """What materialization did and what it had to leave behind."""

    base_facts: int = 0
    derived_facts: int = 0
    rules_applied: int = 0
    skipped: List[SkippedRule] = field(default_factory=list)

    @property
    def summary(self) -> str:
        parts = [f"{self.base_facts} fact{'' if self.base_facts == 1 else 's'}"]
        if self.rules_applied:
            parts.append(f"{self.rules_applied} Horn rule"
                         f"{'' if self.rules_applied == 1 else 's'} → "
                         f"+{self.derived_facts} derived")
        if self.skipped:
            parts.append(f"{len(self.skipped)} rule"
                         f"{'' if len(self.skipped) == 1 else 's'} left to the contest game")
        return "; ".join(parts)


# ---------------------------------------------------------------------------
# Conjunctive matching of a rule body against the current facts
# ---------------------------------------------------------------------------

def _index(facts) -> Dict[Tuple[str, int], List[Tuple[Key, ...]]]:
    """Facts indexed by (relation, arity) — the match dispatch table."""
    idx: Dict[Tuple[str, int], List[Tuple[Key, ...]]] = {}
    for rel, args in facts:
        idx.setdefault((rel, len(args)), []).append(args)
    return idx


def _match_body_at(
    body: Tuple[Fact, ...], i: int,
    all_idx: Dict[Tuple[str, int], List[Tuple[Key, ...]]],
    delta_idx: Dict[Tuple[str, int], List[Tuple[Key, ...]]],
) -> List[Dict[Key, Key]]:
    """All bindings under which ``body`` holds with atom ``i`` drawn from the
    *delta* facts and every other atom from the full set — the semi-naive
    restriction (a derivation is found in the pass its last supporting fact
    arrives, never re-found).  A constant body key matches only the same
    constant; a generic body key is a variable."""
    order = [i] + [j for j in range(len(body)) if j != i]
    results: List[Dict[Key, Key]] = []

    def rec(pos: int, bind: Dict[Key, Key]) -> None:
        if pos == len(order):
            results.append(dict(bind))
            return
        j = order[pos]
        rel, args = body[j]
        src = delta_idx if j == i else all_idx
        for fargs in src.get((rel, len(args)), ()):
            trial = dict(bind)
            ok = True
            for k, ind in zip(args, fargs):
                if k[0] == "c":            # a constant in the body
                    if ind != k:
                        ok = False
                        break
                elif k in trial:           # a re-used line of identity
                    if trial[k] != ind:
                        ok = False
                        break
                else:
                    trial[k] = ind
            if ok:
                rec(pos + 1, trial)

    rec(0, {})
    return results


def _match_body(
    body: List[Fact], facts_by_key: Dict[Tuple[str, int], List[Tuple[Key, ...]]]
) -> List[Dict[Key, Key]]:
    """All bindings under which the conjunction ``body`` holds in the facts (every
    atom drawn from the full set). Kept for one-shot matching against a closed fact
    set (``dl_reasoning``); the chase itself uses the semi-naive
    :func:`_match_body_at`."""
    if not body:
        return [{}]
    return _match_body_at(tuple(body), 0, facts_by_key, facts_by_key)


def _instantiate(atom: Fact, bind) -> Fact:
    """A body atom under a binding — the same substitution the head uses."""
    rel, args = atom
    return (rel, tuple(k if k[0] == "c" else bind[k] for k in args))


def _chase(facts: Set[Fact], horn, delta: Set[Fact] = None,
           provenance=None) -> None:
    """Forward-chain ``horn`` over ``facts`` to the least fixpoint, in place —
    **semi-naive** (Datalog delta iteration): each pass derives only from
    bindings that touch the previous pass's new facts, so the whole model is
    never re-derived per pass.  Exact same closure as naive evaluation.

    ``delta=None`` evaluates from scratch (empty-body rules — an unconditional
    ``~[ ~[ H ] ]`` head, ground by range-restriction — are seeded first).  A
    caller *extending* an already-closed fact set passes the newly added atoms
    as ``delta``; the rules must be unchanged for that to be sound.

    ``provenance`` is opt-in and purely observational: pass a dict and each
    newly derived fact is recorded against its **support** — the frozen set of
    instantiated body atoms that produced it, which is what lets downstream
    "use" mean *doing work as a premise* rather than merely arriving again.
    Omitted (``None``), the chase behaves exactly as before."""
    rules = sorted(horn)
    if delta is None:
        for body, head in rules:
            if not body:
                facts.update(head)
        delta = set(facts)
    else:
        delta = set(delta)
    while delta:
        all_idx = _index(facts)
        delta_idx = _index(delta)
        new: Set[Fact] = set()
        for body, head in rules:
            for i in range(len(body)):
                for bind in _match_body_at(body, i, all_idx, delta_idx):
                    for hrel, hargs in head:
                        f: Fact = (hrel, tuple(k if k[0] == "c" else bind[k]
                                               for k in hargs))
                        if f not in facts:
                            new.add(f)
                            if provenance is not None:
                                support = frozenset(
                                    _instantiate(atom, bind) for atom in body)
                                prior = provenance.get(f)
                                # Deterministic tie-break: keep the
                                # lexicographically smallest support, so the
                                # record does not depend on iteration order.
                                if prior is None or sorted(support) < sorted(prior):
                                    provenance[f] = support
        facts |= new
        delta = new


# ---------------------------------------------------------------------------
# The materializer
# ---------------------------------------------------------------------------

def _canonical_rule(body: List[Fact], head: List[Fact]) -> Tuple[Tuple[Fact, ...], Tuple[Fact, ...]]:
    """A rule with its generic keys renamed positionally (first occurrence over the
    sorted body, then the sorted head) — so the *same* rule extracted from two parses
    of the same EGIF (fresh vertex ids each time) compares equal.  That equality is
    what lets :class:`IncrementalMaterializer` recognise "rules unchanged" across
    rounds.  Sorting uses a variable-blind atom key, so ties among structurally
    interchangeable atoms stay deterministic within one extraction."""
    def blind(atom: Fact):
        rel, args = atom
        return (rel, len(args), tuple(k if k[0] == "c" else ("g", "?") for k in args))

    sorted_body = sorted(body, key=blind)
    sorted_head = sorted(head, key=blind)
    mapping: Dict[Key, Key] = {}

    def norm(args: Tuple[Key, ...]) -> Tuple[Key, ...]:
        out = []
        for k in args:
            if k[0] == "g":
                if k not in mapping:
                    mapping[k] = ("g", str(len(mapping)))
                out.append(mapping[k])
            else:
                out.append(k)
        return tuple(out)

    nb = tuple((rel, norm(args)) for rel, args in sorted_body)
    nh = tuple((rel, norm(args)) for rel, args in sorted_head)
    return nb, nh


def _extract(
    egi: RelationalGraphWithCuts,
) -> Tuple[Set[Fact], frozenset, MaterializationReport]:
    """Read ``egi`` into (base facts, canonical Horn rules, report-with-skips) —
    the shared front half of :func:`materialize_egi` and
    :class:`IncrementalMaterializer` (``derived_facts`` left for the caller)."""
    from world_scroll import m_view

    # A world-scrolled M (the validity discipline) is read through its
    # antecedent area; a legacy sheet-level M passes through unchanged.
    egi = m_view(egi)
    vmap = {v.id: v for v in egi.V}
    edge_ids = {e.id for e in egi.E}
    cut_ids = {c.id for c in egi.Cut}

    def keyv(vid: str) -> Key:
        v = vmap[vid]
        return ("c", v.label) if (not v.is_generic and v.label) else ("g", vid)

    def atoms_in(area_id: str) -> List[Fact]:
        return [
            (egi.get_relation_name(eid), tuple(keyv(v) for v in egi.nu[eid]))
            for eid in egi.area.get(area_id, ()) if eid in edge_ids
        ]

    facts: Set[Fact] = set(atoms_in(egi.sheet))
    report = MaterializationReport(base_facts=len(facts))

    # Classify sheet-level cuts into Horn rules vs. skipped.
    horn: Set[Tuple[Tuple[Fact, ...], Tuple[Fact, ...]]] = set()
    for c1 in [x for x in egi.area.get(egi.sheet, ()) if x in cut_ids]:
        if c1 in egi.quotation:
            # B-min: a quotation area licenses nothing — the quoted shape
            # (even a law-shaped one) is mentioned, never applied
            report.skipped.append(
                SkippedRule("quotation", _describe_cut(egi, c1, edge_ids, cut_ids))
            )
            continue
        inner_cuts = [x for x in egi.area.get(c1, ()) if x in cut_ids]
        if len(inner_cuts) == 0:
            report.skipped.append(SkippedRule("denial", _describe_cut(egi, c1, edge_ids, cut_ids)))
            continue
        if len(inner_cuts) != 1:
            report.skipped.append(SkippedRule("complex_body", _describe_cut(egi, c1, edge_ids, cut_ids)))
            continue
        c2 = inner_cuts[0]
        if any(x in cut_ids for x in egi.area.get(c2, ())):
            report.skipped.append(SkippedRule("negation_in_head", _describe_cut(egi, c1, edge_ids, cut_ids)))
            continue
        body = [
            (egi.get_relation_name(e), tuple(keyv(v) for v in egi.nu[e]))
            for e in egi.area.get(c1, ()) if e in edge_ids
        ]
        head = atoms_in(c2)
        body_gen = {k for _r, args in body for k in args if k[0] == "g"}
        head_gen = {k for _r, args in head for k in args if k[0] == "g"}
        if not head_gen <= body_gen:
            report.skipped.append(SkippedRule("existential_head", _describe_cut(egi, c1, edge_ids, cut_ids)))
            continue
        horn.add(_canonical_rule(body, head))

    report.rules_applied = len(horn)
    return facts, frozenset(horn), report


def materialize_egi(
    egi: RelationalGraphWithCuts,
    provenance=None,
) -> Tuple[RelationalGraphWithCuts, MaterializationReport]:
    """Forward-chain the Horn fragment of ``egi`` to its least Herbrand model.

    Returns ``(facts_egi, report)`` — a facts-only EGI the peel can model-check
    against, and an honest account of what was derived and what was skipped.

    Pass a dict as ``provenance`` to also collect, per derived fact, the
    support that produced it (see :func:`_chase`); omitted, nothing changes.
    """
    facts, horn, report = _extract(egi)
    closure = set(facts)
    _chase(closure, horn, provenance=provenance)
    report.derived_facts = len(closure) - report.base_facts
    return _facts_to_egi(closure), report


class IncrementalMaterializer:
    """Cross-round materialization cache — the semi-naive rider on the atom-level
    decay rulebook (RUN_4_LOG F2⁗, 2026-07-03).

    The live loop re-materializes M every round, but a round almost always *grows*
    M by juxtaposition (``new_fact``, or a redundant re-delivery): same rules, a
    superset of ground atoms.  This cache exploits exactly that shape: when the new
    state's rules are unchanged (canonical comparison, stable across reparse) and
    its base atoms are a superset of the cached ones, only the truly-new atoms are
    chased (:func:`_chase` with a delta) and the cached facts-EGI is *extended*
    edge-by-edge rather than rebuilt — turning the per-round O(|M|²) rebuild into
    O(|Δ|·|M|).  Anything else — a retraction/decay, a rule change, a generic
    (non-ground) sheet atom whose identity does not survive reparse — falls back to
    one full materialization.  **Exact**: the closure always equals
    :func:`materialize_egi`'s (least-fixpoint extension is sound for monotone
    growth under fixed rules).

    Provenance is **not** collected under the cached path (neither on a hit nor on an
    extension), so a caller that needs per-fact support must call
    :func:`materialize_egi` with a ``provenance`` dict instead of using this cache.

    ``hits`` / ``extensions`` / ``rebuilds`` are observable counters (tests, digests).
    """

    def __init__(self):
        self._atoms: Set[Fact] = None
        self._horn: frozenset = None
        self._closure: Set[Fact] = None
        self._builder: _FactsBuilder = None
        self.hits = 0
        self.extensions = 0
        self.rebuilds = 0

    def materialize(
        self, egi: RelationalGraphWithCuts
    ) -> Tuple[RelationalGraphWithCuts, MaterializationReport]:
        facts, horn, report = _extract(egi)
        if self._atoms is not None and horn == self._horn and self._atoms <= facts:
            if facts == self._atoms:                      # the same M again (an audit re-peel)
                self.hits += 1
                report.derived_facts = len(self._closure) - report.base_facts
                return self._builder.egi, report
            delta = facts - self._atoms                   # monotone growth — the common round
            before = len(self._closure)
            rendered = set(self._closure)
            new_atoms = delta - self._closure
            self._closure |= delta
            if new_atoms:
                _chase(self._closure, horn, delta=new_atoms)
            self._builder.add(self._closure - rendered)
            self._atoms = set(facts)
            self.extensions += 1
            report.derived_facts = len(self._closure) - report.base_facts
            assert len(self._closure) >= before
            return self._builder.egi, report
        # anything else: one full materialization, then cache the new state
        self._atoms = set(facts)
        self._horn = horn
        self._closure = set(facts)
        _chase(self._closure, horn)
        self._builder = _FactsBuilder()
        self._builder.add(self._closure)
        self.rebuilds += 1
        report.derived_facts = len(self._closure) - report.base_facts
        return self._builder.egi, report


def _describe_cut(egi, cut_id, edge_ids, cut_ids) -> str:
    """A short EGIF-ish rendering of a sheet-level cut, for the skip-report."""
    vmap = {v.id: v for v in egi.V}

    def arg(vid: str) -> str:
        v = vmap.get(vid)
        return f'"{v.label}"' if (v is not None and not v.is_generic and v.label) else "*"

    def render_area(area_id) -> str:
        bits = []
        for x in egi.area.get(area_id, ()):
            if x in edge_ids:
                args = " ".join(arg(v) for v in egi.nu[x])
                bits.append(f"({egi.get_relation_name(x)}{' ' + args if args else ''})")
            elif x in cut_ids:
                bits.append("~[ " + render_area(x) + " ]")
        return " ".join(bits)

    return "~[ " + render_area(cut_id) + " ]"


class _FactsBuilder:
    """Incrementally build a facts-only EGI from ground atoms.

    Constructed **directly** through the immutable EGI API rather than by generating
    EGIF text and reparsing: a CLIF/COLORE-imported model may carry relation or
    individual names EGIF text cannot round-trip (e.g. ``Warm-blooded``), and they are
    legal in the graph.  Building structurally keeps any name the source allowed.
    ``add`` may be called repeatedly (the :class:`IncrementalMaterializer` extension
    path); vertex identity and edge numbering carry across calls.
    """

    def __init__(self):
        self.egi = create_empty_graph()      # the blank sheet (an empty model)
        self._vid_of: Dict[Key, str] = {}
        self._gen = 0                        # synthetic names for generic individuals
        self._seq = 0                        # deterministic, collision-free edge ids:
                                             # ``create_edge`` draws a 32-bit random suffix,
                                             # which collides once a closure runs to thousands
                                             # of facts — enumerate instead (also reproducible)
        self._vseq = 0                       # same for vertex ids (RUN_6, the F1ᵇ sibling:
                                             # create_vertex's 32-bit draw collided live in a
                                             # ~thousand-vertex facts graph built every round)

    def add(self, facts) -> RelationalGraphWithCuts:
        g = self.egi
        batch = sorted(facts)
        for _rel, args in batch:
            for k in args:
                if k in self._vid_of:
                    continue
                self._vseq += 1
                if k[0] == "c":
                    v = Vertex(id=f"v_m{self._vseq}", label=k[1], is_generic=False)
                else:
                    self._gen += 1
                    v = Vertex(id=f"v_m{self._vseq}", label=f"_i{self._gen}",
                               is_generic=False)
                g = g.with_vertex(v)
                self._vid_of[k] = v.id
        for rel, args in batch:
            edge = Edge(id=f"e_m{self._seq}")
            self._seq += 1
            g = g.with_edge(edge, tuple(self._vid_of[k] for k in args), rel)
        self.egi = g
        return g


def _facts_to_egi(facts: Set[Fact]) -> RelationalGraphWithCuts:
    """Build a facts-only EGI from the materialized atom set (all ground)."""
    return _FactsBuilder().add(facts)


# --------------------------------------------------------------------------- #
# K3 — the materialization ratio                                              #
# (THE_MEASURE_OF_KNOWLEDGE §2; the compression component of the knowledge    #
# measure, authorized 2026-07-17.)                                            #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class KnowledgeCompression:
    """K3: how much of M's ground extension is *derived* rather than asserted.

    ``ratio`` = derived ÷ (explicit + derived), bounded in ``[0, 1]`` (0.0 when
    the denominator is 0 — a model with no facts at all compresses nothing,
    never an error; 1.0 exactly when every ground fact is derived and none is
    explicit — a model that is pure unconditional law, e.g. a range-restricted
    empty-body rule like ``~[ ~[ (man "Socrates") ] ]``, see
    ``test_k3_ratio_one_when_all_derived_no_explicit``). This is
    **extent-invariant**: the identical law applied over 2 individuals or 200
    reads the same ``ratio`` (both derive exactly one fact per explicit fact
    here), because the denominator is the model's own extent, not its law
    count. The prior formulation (``derived ÷ laws``) confounded compression
    with domain size — the same law over 2/20/200 individuals read
    2.0/20.0/200.0, an unbounded number that grows with N rather than
    measuring how much of the extension is *derived*, so it is kept below as
    ``yield_per_law``, not as ``ratio``.

    ``yield_per_law`` = derived ÷ (horn_laws + skipped_laws) — the mean
    derivational yield per law M carries. It is NOT compression: it scales
    with domain extent (a law over 200 individuals yields 200, the same law
    over 2 yields 2), so it answers "how productive is a law" rather than
    "how much of the model is derived." A law materialization cannot
    evaluate (non-Horn, reported in ``skipped``) earns no yield credit but
    still weighs this denominator — no credit without evaluable evidence,
    the measure's earned-record discipline applied to itself."""

    explicit: int
    derived: int
    horn_laws: int
    skipped_laws: int

    @property
    def ratio(self) -> float:
        """K3, extent-invariant: derived ÷ (explicit + derived), in [0, 1].
        1.0 is reachable (not just approached) when explicit == 0 and
        derived > 0 — a model consisting entirely of unconditional-law
        derivations, e.g. a range-restricted empty-body rule."""
        total = self.explicit + self.derived
        return self.derived / total if total else 0.0

    @property
    def yield_per_law(self) -> float:
        """Mean derivational yield per law (denominator = ``horn_laws +
        skipped_laws``; a skipped law weighs it with no yield credit);
        scales with domain extent — NOT a compression measure."""
        laws = self.horn_laws + self.skipped_laws
        return self.derived / laws if laws else 0.0


def materialization_ratio(egi: RelationalGraphWithCuts) -> KnowledgeCompression:
    """Compute K3 for ``egi`` (resident or bare M — reading via ``m_view``
    inside :func:`materialize_egi`'s shared extraction)."""
    _, report = materialize_egi(egi)
    return KnowledgeCompression(
        explicit=report.base_facts,
        derived=report.derived_facts,
        horn_laws=report.rules_applied,
        skipped_laws=len(report.skipped),
    )
