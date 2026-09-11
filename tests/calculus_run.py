"""One streaming pass per mode: every move applied once, every layer's check
run on it, only failures and counts kept (spec 2026-09-10 §6)."""
from __future__ import annotations

import functools
import itertools
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from calculus_apply import Outcome, apply_move
from calculus_enum import DEFAULT_BOUNDS, EXHAUSTIVE_BOUNDS, Bounds, tier_a
from calculus_layers import LAYERS
from calculus_ledger import Failure, instance_key, ledgered
from calculus_rules import IMPLEMENTED, Move, legal, moves
from canonical_signature import compute_canonical_signatures


@dataclass(frozen=True)
class SemanticsBudget:
    sizes: Tuple[int, ...]
    tuple_cap: int
    sample_n: int
    seed: int
    max_elements: int     # larger source graphs are counted, not evaluated


@dataclass(frozen=True)
class Mode:
    name: str
    bounds: Bounds
    tier_b: str           # "none" | "current-units" | "all"
    tier_b_budget: int
    sem: SemanticsBudget


MODES: Dict[str, Mode] = {
    "default": Mode("default", DEFAULT_BOUNDS, "none", 200,
                    SemanticsBudget((1, 2), 6, 64, 20260910, 40)),
    "exhaustive": Mode("exhaustive", EXHAUSTIVE_BOUNDS, "none", 2000,
                       SemanticsBudget((1, 2, 3), 12, 512, 20260910, 80)),
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
    raise ValueError(f"tier {tier!r} is wired in Task 10")


def _tiers(mode: Mode):
    return ("A",) if mode.tier_b == "none" else ("A", "B")


@functools.lru_cache(maxsize=None)
def run(mode_name: str) -> Run:
    mode = MODES[mode_name]
    result = Run(mode, layers={name: LayerResult() for name in LAYERS})
    known = {name: ledgered(name) for name in LAYERS}
    for tier in _tiers(mode):
        budget = None if tier == "A" else mode.tier_b_budget
        units_only = tier == "B" and mode.tier_b == "current-units"
        for gname, g in graphs_for(mode, tier):
            result.graphs[tier] += 1
            sigs = compute_canonical_signatures(g)
            cache: dict = {}
            for rule in IMPLEMENTED:
                gen = moves(rule.name, g, tier, units_only=units_only)
                taken = list(gen) if budget is None else list(itertools.islice(gen, budget))
                if budget is not None:
                    result.skipped[f"{tier}:{rule.name}"] += sum(1 for _ in gen)
                for m in taken:
                    result.moves[f"{tier}:{rule.name}"] += 1
                    verdict, why = legal(g, m)
                    rec = Record(tier, gname, g, m, instance_key(tier, gname, g, m, sigs),
                                 apply_move(g, m), verdict, why)
                    for name, check in LAYERS.items():
                        label, detail = check(rec, cache)
                        lr = result.layers[name]
                        lr.counts[f"{tier}:{label}"] += 1
                        if not label.startswith("not:") and rec.key in known[name]:
                            lr.evaluated_ledgered.add(rec.key)
                        if detail is not None:
                            lr.failures.append(Failure(name, rec.key, detail))
    return result
