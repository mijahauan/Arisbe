"""The field's regime for the C-series: a seeded world of partially
overlapping domains, each carrying one hidden unary law.

The regime is NOT ground truth and is never used to score a unit (spec
premise 1). A round delivers its own antecedents plus the consequents
licensed by the previous round's antecedents — the lag is what makes
anticipation predictive.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Optional, Set, Tuple

from model_materialization import Fact, Key  # noqa: F401  (re-exported)


@dataclass(frozen=True)
class Domain:
    name: str
    antecedents: Tuple[str, ...]      # relations the field may deliver here
    law: Tuple[str, str]              # (body_rel, head_rel): body(x) -> head(x)
    individuals: Tuple[str, ...]


@dataclass(frozen=True)
class FieldSpec:
    seed: int
    domains: Tuple[Domain, ...]


def default_spec(seed: int = 20260728) -> FieldSpec:
    """Four domains. `shared` appears in every domain's antecedents — the
    regularity any unit could find and nobody should find twice. Each domain
    additionally carries a local antecedent and its own law."""
    return FieldSpec(
        seed=seed,
        domains=(
            Domain("alpha", ("shared", "a_local"), ("a_local", "a_head"),
                   tuple(f"a{i}" for i in range(1, 41))),
            Domain("beta", ("shared", "b_local"), ("b_local", "b_head"),
                   tuple(f"b{i}" for i in range(1, 41))),
            Domain("gamma", ("shared", "g_local"), ("g_local", "g_head"),
                   tuple(f"g{i}" for i in range(1, 41))),
            Domain("delta", ("shared", "d_local"), ("d_local", "d_head"),
                   tuple(f"d{i}" for i in range(1, 41))),
        ),
    )


class Field:
    """Deterministic deliverance. `deliver` is a pure function of
    (seed, domain, round) — it holds no mutable state, so any unit may read
    any round in any order without disturbing another unit's stream."""

    def __init__(self, spec: FieldSpec):
        self.spec = spec
        self._by_name = {d.name: d for d in spec.domains}

    def domain(self, domain_name: str) -> Domain:
        return self._by_name[domain_name]

    def _antecedents(self, domain_name: str, round_idx: int) -> List[Fact]:
        """The raw antecedent atoms for one round — a pure function of
        (seed, domain, round). `random.Random` seeds deterministically from a
        string across runs, so no PYTHONHASHSEED dependence."""
        if round_idx < 0:
            return []
        d = self._by_name[domain_name]
        rng = random.Random(f"{self.spec.seed}:{domain_name}:{round_idx}")
        out: List[Fact] = []
        for rel in d.antecedents:
            who = rng.choice(d.individuals)
            out.append((rel, (("c", who),)))
        return sorted(out)

    def deliver(self, domain_name: str, round_idx: int) -> List[Fact]:
        """What this domain delivers at `round_idx`: this round's antecedents,
        plus the consequents licensed by LAST round's antecedents.

        The one-round lag is what makes anticipation predictive. A unit that
        holds the law sees `body(a)` at r and can anticipate `head(a)` at
        r+1; a unit without it cannot. Both are observable, so induction has
        material to work with."""
        out = set(self._antecedents(domain_name, round_idx))
        for f in self._antecedents(domain_name, round_idx - 1):
            c = self.consequent(domain_name, f)
            if c is not None:
                out.add(c)
        return sorted(out)

    def consequent(self, domain_name: str, f: Fact) -> Optional[Fact]:
        """The atom this domain's law licenses from `f`, or None. Modeler-side
        only: used by tests and diagnostics, never by a scoring path."""
        d = self._by_name[domain_name]
        rel, args = f
        body_rel, head_rel = d.law
        return (head_rel, args) if rel == body_rel else None

    def at(self, aperture: "Aperture", round_idx: int) -> List[Fact]:
        """What arrives at this unit's membrane this round: the union of its
        domains' deliveries."""
        out: Set[Fact] = set()
        for name in aperture.domains:
            out.update(self.deliver(name, round_idx))
        return sorted(out)


@dataclass(frozen=True)
class Aperture:
    """The slice of the field one unit meets. Distinct per unit by
    construction (spec premise 3)."""
    unit_id: str
    domains: Tuple[str, ...]


def apertures_for(spec: FieldSpec, n_units: int) -> List["Aperture"]:
    """Deterministic, overlapping, and pairwise distinct: unit i sees domains
    i and i+1 (mod count), so consecutive units share exactly one domain.

    The scheme cycles with period `len(spec.domains)`, so it can only build
    distinct apertures for at most that many units.  Asking for more raises
    rather than silently handing two units the same slice — divergence by
    construction (spec premise 3) is the premise, not a nicety.  Widening the
    scheme (more domains, or apertures of other sizes) is a stage-3 design
    decision, deliberately not made here."""
    names = [d.name for d in spec.domains]
    k = len(names)
    if n_units > k:
        raise ValueError(
            f"cannot build {n_units} distinct apertures from {k} domains: "
            f"unit i sees domains i and i+1 (mod {k}), so the assignment "
            f"cycles after {k} units and units would share an aperture"
        )
    out: List[Aperture] = []
    for i in range(n_units):
        first = names[i % k]
        second = names[(i + 1) % k]
        out.append(Aperture(f"u{i}", (first, second)))
    return out
