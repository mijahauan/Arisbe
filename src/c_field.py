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


CORE = tuple(f"s{i}" for i in range(1, 11))
"""The individuals every domain knows. Overlap lives in the domains' own
individual lists, not in a pool beside them — see `default_spec`."""


def _individuals(prefix: str) -> Tuple[str, ...]:
    """A domain's forty individuals: the ten-strong shared core plus thirty
    private ones. The private names start at 11 so that `a11` and `s5` are
    never two names for one thing, and so the count is readable off the
    range."""
    return CORE + tuple(f"{prefix}{i}" for i in range(11, 41))


def default_spec(seed: int = 20260728) -> FieldSpec:
    """Four domains. `shared` appears in every domain's antecedents — the
    regularity any unit could find and nobody should find twice. Each domain
    additionally carries a local antecedent and its own law.

    OVERLAP IS IN THE INDIVIDUAL LISTS, NOT BESIDE THEM. Each domain's forty
    individuals are the ten-strong core `s1..s10` — known to every domain —
    plus thirty private ones (`a11..a40`, `b11..b40`, ...). Every relation of a
    domain, `shared` included, draws from that one list.

    An earlier design gave `shared` a separate pool of s-individuals disjoint
    from every domain's own. That made cross-domain overlap real but sterile:
    `shared(a20)` could never arrive, so any law of the form
    *domain-relation -> shared* was structurally unsatisfiable and a rival
    holding one had a hit ceiling of exactly zero. Putting the core inside the
    lists restores three things at once — `shared(s5)` and `a_head(s5)` can
    mention the same individual, so a wrong law can genuinely hit AND lose;
    alpha and beta both emit atoms about `s5`, so overlap carries content; and
    accidental regularities are possible again, so a gate can discriminate."""
    return FieldSpec(
        seed=seed,
        domains=(
            Domain("alpha", ("shared", "a_local"), ("a_local", "a_head"),
                   _individuals("a")),
            Domain("beta", ("shared", "b_local"), ("b_local", "b_head"),
                   _individuals("b")),
            Domain("gamma", ("shared", "g_local"), ("g_local", "g_head"),
                   _individuals("g")),
            Domain("delta", ("shared", "d_local"), ("d_local", "d_head"),
                   _individuals("d")),
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
