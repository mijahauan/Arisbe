"""One streaming pass per mode: every move applied once, every layer's check
run on it, only failures and counts kept (spec 2026-09-10 §6)."""
from __future__ import annotations

import functools
import itertools
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional, Set, Tuple

from calculus_apply import Outcome, apply_move
from calculus_classifiers import claims
from calculus_enum import DEFAULT_BOUNDS, EXHAUSTIVE_BOUNDS, Bounds, tier_a, tier_b
from calculus_layers import LAYERS
from calculus_ledger import Failure, instance_key, ledgered
from calculus_rules import IMPLEMENTED, Move, expand, legal, moves
from canonical_signature import compute_canonical_signatures


@dataclass(frozen=True)
class SemanticsBudget:
    sizes: Tuple[int, ...]
    tuple_cap: int
    sample_n: int
    seed: int
    max_elements: int     # larger source graphs are counted, not evaluated
    # Tier B only (spec §5.3: "a seeded, counted sample, stated as a sample"):
    # universe() enumerates every constant assignment when the tuple bits fit
    # under tuple_cap, so a corpus vocabulary with five constants gives 995,328
    # structures at domain size 3. Above this many, a tier-B universe is the
    # seeded sample of sample_n instead (labelled "sampled"). None = no cap.
    tier_b_max_structures: Optional[int] = None


@dataclass(frozen=True)
class Mode:
    name: str
    bounds: Bounds
    tier_b: str           # "none" | "current-units" | "all"
    tier_b_budget: int
    sem: SemanticsBudget


MODES: Dict[str, Mode] = {
    # tier_b_budget 200 -> 100 (Task 10, the brief's two-minute rule): run("default")
    # took 97.8 s at 200, 86.4 s at 150, 69.8 s at 100; with the rest of the
    # calculus files only 100 keeps the default slice under two minutes.
    "default": Mode("default", DEFAULT_BOUNDS, "current-units", 100,
                    SemanticsBudget((1, 2), 6, 64, 20260910, 40)),
    # tier_b_budget 2000 -> 500 (Task 10, the brief's 3-hour rule, first knob):
    # a 1-in-20 sample of every tier-B move put tier-B soundness at ~8,040 s
    # at 2000, ~6,990 s at 1000, ~5,440 s at 500 — with tier A's ~3,730 s,
    # only 500 brings the whole exhaustive suite under three hours.
    "exhaustive": Mode("exhaustive", EXHAUSTIVE_BOUNDS, "all", 500,
                       # 36,864 = the largest exhaustive universe any exhaustive
                       # tier-A graph has on its own vocabulary (Task 10), so a
                       # tier-B graph is never held to less than tier A is.
                       SemanticsBudget((1, 2, 3), 12, 512, 20260910, 80, 36864)),
}


@dataclass(frozen=True)
class Record:
    tier: str
    gname: str
    g: object
    move: Move
    key: str
    outcome: Outcome
    verdict: Optional[bool]
    why: str


@dataclass
class LayerResult:
    failures: List[Failure] = field(default_factory=list)
    evaluated_ledgered: Set[str] = field(default_factory=set)
    counts: Counter = field(default_factory=Counter)


@dataclass
class Run:
    mode: Mode
    graphs: Counter = field(default_factory=Counter)
    moves: Counter = field(default_factory=Counter)
    skipped: Counter = field(default_factory=Counter)
    layers: Dict[str, LayerResult] = field(default_factory=dict)

    def extent(self) -> dict:
        return {"graphs": dict(sorted(self.graphs.items())),
                "moves": dict(sorted(self.moves.items())),
                "skipped": dict(sorted(self.skipped.items()))}


def graphs_for(mode: Mode, tier: str):
    if tier == "A":
        return tier_a(mode.bounds).graphs
    return tier_b(include_chains=(mode.tier_b == "all")).graphs


def _tiers(mode: Mode):
    return ("A",) if mode.tier_b == "none" else ("A", "B")


# Engine entry points that do not finish on large patterns, measured in Task 10
# (a per-move alarm over every tier-B move, under nine hash seeds): IT-'s search
# for the original (rule_interaction.validate_step ->
# graph_isomorphism_engine.find_isomorphic_subgraphs, a VF2 subgraph search)
# ran past 5 s under every seed — and past 45 s when left alone — on each move
# whose selection expands to 124 elements or more (bfo_core, colore_field,
# sumo_upper). Below that its time depends on the hash seed with a heavy tail:
# skos_core's two whole-scroll deiterations (patterns 70-71) took 0.5 s, 2.7 s
# and 28 s under three seeds and stalled a default run past 16 minutes under a
# fourth, while no pattern of 64 or fewer took more than ~4.3 s under any seed.
# A wall-clock timeout would make the extent machine-dependent, so a move whose
# expanded selection exceeds the ceiling is not applied, and is counted under
# ``skipped["<tier>:<rule>:engine-does-not-finish"]``.
ENGINE_PATTERN_CEILING = {"IT-": 64}


def records(mode_name: str, tally: Optional["Run"] = None) -> Iterator[Tuple[Record, dict]]:
    """Every move of the mode, applied and judged once, with its source graph's
    cache — the one enumeration both the run and the adjudication scripts
    walk, so a script's figures cover exactly the extent the tests pin.
    ``tally`` (a Run) receives the graph, move and skip counts."""
    mode = MODES[mode_name]
    for tier in _tiers(mode):
        budget = None if tier == "A" else mode.tier_b_budget
        units_only = tier == "B" and mode.tier_b == "current-units"
        for gname, g in graphs_for(mode, tier):
            if tally is not None:
                tally.graphs[tier] += 1
            sigs = compute_canonical_signatures(g)
            cache: dict = {"_sem": mode.sem}
            for rule in IMPLEMENTED:
                gen = moves(rule.name, g, tier, units_only=units_only)
                ceiling = ENGINE_PATTERN_CEILING.get(rule.name)
                taken = list(gen) if budget is None else list(itertools.islice(gen, budget))
                if budget is not None and tally is not None:
                    tally.skipped[f"{tier}:{rule.name}"] += sum(1 for _ in gen)
                for m in taken:
                    if ceiling is not None and len(expand(g, m.selection)) > ceiling:
                        if tally is not None:
                            tally.skipped[f"{tier}:{rule.name}:engine-does-not-finish"] += 1
                        continue
                    if tally is not None:
                        tally.moves[f"{tier}:{rule.name}"] += 1
                    verdict, why = legal(g, m)
                    yield Record(tier, gname, g, m, instance_key(tier, gname, g, m, sigs),
                                 apply_move(g, m), verdict, why), cache


@functools.lru_cache(maxsize=None)
def run(mode_name: str) -> Run:
    mode = MODES[mode_name]
    result = Run(mode, layers={name: LayerResult() for name in LAYERS})
    known = {name: ledgered(name) for name in LAYERS}
    for rec, cache in records(mode_name, result):
        for name, check in LAYERS.items():
            label, detail = check(rec, cache)
            lr = result.layers[name]
            lr.counts[f"{rec.tier}:{label}"] += 1
            if not label.startswith("not:") and rec.key in known[name]:
                lr.evaluated_ledgered.add(rec.key)
            if detail is not None:
                lr.failures.append(Failure(name, rec.key, detail, claims(name, rec, detail)))
    return result
