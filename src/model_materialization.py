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
    RelationalGraphWithCuts,
    create_edge,
    create_empty_graph,
    create_vertex,
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

def _match_body(
    body: List[Fact], facts_by_key: Dict[Tuple[str, int], List[Tuple[Key, ...]]]
) -> List[Dict[Key, Key]]:
    """All bindings (generic body key → individual key) under which the conjunction
    ``body`` holds in the facts.  A constant body key matches only the same constant;
    a generic body key is a variable that may bind to any individual."""
    results: List[Dict[Key, Key]] = []

    def rec(i: int, bind: Dict[Key, Key]) -> None:
        if i == len(body):
            results.append(dict(bind))
            return
        rel, args = body[i]
        for fargs in facts_by_key.get((rel, len(args)), ()):
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
                rec(i + 1, trial)

    rec(0, {})
    return results


# ---------------------------------------------------------------------------
# The materializer
# ---------------------------------------------------------------------------

def materialize_egi(
    egi: RelationalGraphWithCuts,
) -> Tuple[RelationalGraphWithCuts, MaterializationReport]:
    """Forward-chain the Horn fragment of ``egi`` to its least Herbrand model.

    Returns ``(facts_egi, report)`` — a facts-only EGI the peel can model-check
    against, and an honest account of what was derived and what was skipped.
    """
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
    horn: List[Tuple[List[Fact], List[Fact]]] = []
    for c1 in [x for x in egi.area.get(egi.sheet, ()) if x in cut_ids]:
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
        horn.append((body, head))

    report.rules_applied = len(horn)

    # Forward-chain to a fixpoint.
    changed = True
    while changed:
        changed = False
        facts_by_key: Dict[Tuple[str, int], List[Tuple[Key, ...]]] = {}
        for rel, args in facts:
            facts_by_key.setdefault((rel, len(args)), []).append(args)
        for body, head in horn:
            for bind in _match_body(body, facts_by_key):
                for hrel, hargs in head:
                    new: Fact = (hrel, tuple(k if k[0] == "c" else bind[k] for k in hargs))
                    if new not in facts:
                        facts.add(new)
                        changed = True

    report.derived_facts = len(facts) - report.base_facts
    return _facts_to_egi(facts), report


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


def _facts_to_egi(facts: Set[Fact]) -> RelationalGraphWithCuts:
    """Build a facts-only EGI from the materialized atom set (all ground).

    Constructed **directly** through the immutable EGI API rather than by generating
    EGIF text and reparsing: a CLIF/COLORE-imported model may carry relation or
    individual names EGIF text cannot round-trip (e.g. ``Warm-blooded``), and they are
    legal in the graph.  Building structurally keeps any name the source allowed.
    """
    if not facts:
        return create_empty_graph()  # the blank sheet (an empty model)

    g = create_empty_graph()
    vid_of: Dict[Key, str] = {}
    counter = 0
    for _rel, args in sorted(facts):
        for k in args:
            if k in vid_of:
                continue
            if k[0] == "c":
                v = create_vertex(label=k[1], is_generic=False)
            else:
                counter += 1
                v = create_vertex(label=f"_i{counter}", is_generic=False)
            g = g.with_vertex(v)
            vid_of[k] = v.id

    for rel, args in sorted(facts):
        edge = create_edge()
        g = g.with_edge(edge, tuple(vid_of[k] for k in args), rel)
    return g
