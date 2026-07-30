"""The field's regime for the C-series: a seeded world of partially
overlapping domains, each carrying one hidden unary law.

The regime is NOT ground truth and is never used to score a unit (spec
premise 1). A round delivers its own antecedents plus the consequents
licensed by the previous round's antecedents — the lag is what makes
anticipation predictive.
"""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

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
    withhold_rate: float = 0.0
    """Probability that a licensed consequent is withheld — the law fires
    but its effect does not arrive. Makes a true law refutable: without
    this, a held law can never miss and a challenge against it can never
    succeed (spec premise: noise is what makes the record fallible)."""
    spurious_rate: float = 0.0
    """Probability that one extra head atom arrives with no antecedent to
    license it — a consequence with no cause. Makes accidental hits
    possible for a law nobody holds, and gives a held law something to be
    wrong about."""


CONSEQUENT_LAG = 1
"""How many rounds a licensed consequent trails its antecedent. `deliver` reads
it, and so does anything that has to know how long to wait before an absent head
means anything: an individual whose body arrived less than this many rounds ago
cannot yet carry its head, so its silence is not evidence.

Named rather than inlined because two modules depend on it and they must not
drift — `Field.deliver` produces the lag and `c_unit.Unit._pending_split`
consumes it."""


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
        withhold_rate=0.1,
        spurious_rate=0.1,
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
        plus the consequents licensed by LAST round's antecedents, passed
        through noise.

        The one-round lag is what makes anticipation predictive. A unit that
        holds the law sees `body(a)` at r and can anticipate `head(a)` at
        r+1; a unit without it cannot. Both are observable, so induction has
        material to work with.

        Noise is drawn from a SEPARATE `random.Random`, seeded on
        `f"{seed}:noise:{domain_name}:{round_idx}"`, so it can never disturb
        the antecedent stream's own call sequence — the same seed still
        delivers the same antecedents whether or not noise is enabled. Each
        licensed consequent is independently withheld with probability
        `withhold_rate`; then, with probability `spurious_rate`, one extra
        head atom arrives about a randomly chosen individual that the law did
        not license — a consequence with no cause."""
        d = self._by_name[domain_name]
        out = set(self._antecedents(domain_name, round_idx))
        licensed = []
        for f in self._antecedents(domain_name, round_idx - CONSEQUENT_LAG):
            c = self.consequent(domain_name, f)
            if c is not None:
                licensed.append(c)

        noise_rng = random.Random(f"{self.spec.seed}:noise:{domain_name}:{round_idx}")
        for c in licensed:
            if noise_rng.random() < self.spec.withhold_rate:
                continue
            out.add(c)
        if noise_rng.random() < self.spec.spurious_rate:
            _, head_rel = d.law
            who = noise_rng.choice(d.individuals)
            out.add((head_rel, (("c", who),)))
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


CYCLIC = "cyclic"
PAIRS = "pairs"
SCHEMES = (CYCLIC, PAIRS)
"""How a community's apertures are laid out over the domains. Both schemes give
every unit TWO domains — width is not the variable, and a stage-3 measurement
says why: three-domain apertures were measured degenerate (all 168 true and 56
converse laws lost, both arms net 0), so the way to put more eyes on a domain is
more units, not wider ones.

`CYCLIC` is the original: unit i sees domains i and i+1 (mod k). It cycles with
period k, so it builds at most k distinct apertures and each domain falls in
exactly two of them.

`PAIRS` gives each unit a DISTINCT 2-domain combination, taken in the domains'
own declared order. It reaches C(k, 2) units, and at the full count each domain
is witnessed by exactly k−1 of them. The two schemes agree on unit 0 and
disagree from unit 1 on, so a measurement that changes scheme changes what it
measures; `apertures_for` therefore keeps CYCLIC as its default rather than
switching anything silently."""


def apertures_for(spec: FieldSpec, n_units: int, *, scheme: str = CYCLIC,
                  min_witnesses: Optional[int] = None) -> List["Aperture"]:
    """Deterministic, overlapping, and pairwise distinct apertures — one per
    unit, two domains each.

    `CYCLIC` (the default, unchanged): unit i sees domains i and i+1 (mod
    count), so consecutive units share exactly one domain. The scheme cycles
    with period `len(spec.domains)`, so it can only build distinct apertures for
    at most that many units. Asking for more raises rather than silently handing
    two units the same slice — divergence by construction (spec premise 3) is
    the premise, not a nicety.

    `PAIRS`: each unit gets a distinct 2-domain combination, generated in the
    domains' declared order (`itertools.combinations`, which preserves input
    order — nothing here reads a set). It reaches C(k, 2) units, and the whole
    set gives every domain exactly k−1 witnesses.

    WHY A SECOND SCHEME EXISTS, AND WHAT IT COSTS. The author ruled that
    corroboration takes at least two independent witnesses, which — with the
    holder never counting as one of them — means a domain must be witnessed by
    at least THREE units: the holder, the challenger, and one corroborator. The
    cyclic scheme puts every domain in exactly two apertures at any community
    size, so three witnesses are arithmetically unreachable under it and
    elimination-by-corroboration was measured firing 0 times in 66 doubts. The
    disposition rule was correct; the field was what failed it. `PAIRS` at the
    spec's four domains needs six units and gives every domain exactly three
    witnesses — the minimum the ruling requires, with nothing to spare.

    The schemes agree on unit 0 (both hand it the first two domains) and diverge
    from unit 1 on, so they are NOT interchangeable in a measurement: at four
    domains, cyclic gives 2/2/2/2 witnesses and the first four pairs give
    3/2/2/1. Every measurement written before this scheme existed keeps the
    default, so none of them moved.

    `min_witnesses`, when given, refuses a community too small for each domain to
    reach that many witnesses, naming the shortfall and the size that would
    satisfy it. Handing back a community that cannot corroborate is the failure
    this argument exists to remove, so it is refused rather than degraded."""
    names = [d.name for d in spec.domains]
    k = len(names)
    if scheme not in SCHEMES:
        raise ValueError(f"aperture scheme {scheme!r} is not one of {SCHEMES}")
    out: List[Aperture] = []
    if scheme == CYCLIC:
        if n_units > k:
            raise ValueError(
                f"cannot build {n_units} distinct apertures from {k} domains: "
                f"unit i sees domains i and i+1 (mod {k}), so the assignment "
                f"cycles after {k} units and units would share an aperture "
                f"(scheme={PAIRS!r} reaches {_n_pairs(k)} distinct apertures "
                f"at the same width)"
            )
        for i in range(n_units):
            out.append(Aperture(f"u{i}", (names[i % k], names[(i + 1) % k])))
    else:
        pairs = list(itertools.combinations(names, 2))
        if n_units > len(pairs):
            raise ValueError(
                f"cannot build {n_units} distinct apertures from {k} domains: "
                f"there are only {len(pairs)} distinct 2-domain combinations, "
                f"and widening an aperture was measured degenerate rather than "
                f"helpful"
            )
        for i, pair in enumerate(pairs[:n_units]):
            out.append(Aperture(f"u{i}", pair))
    if min_witnesses is not None:
        _require_witnesses(spec, out, min_witnesses, scheme)
    return out


def _n_pairs(k: int) -> int:
    return k * (k - 1) // 2


def witnesses_per_domain(spec: FieldSpec, apertures: List["Aperture"]
                         ) -> Dict[str, int]:
    """How many of these units meet each domain — INCLUDING the ones no unit
    meets, which read 0 rather than going missing.

    This is the quantity the corroboration ruling is about. A doubt about a law
    of domain D can only ever be corroborated by a unit that meets D, and the
    holder is not one of the voices, so `witnesses_per_domain(...)[D]` is the
    ceiling on (holder + challenger + corroborators) for every law of D."""
    counts = {d.name: 0 for d in spec.domains}
    for ap in apertures:
        for name in ap.domains:
            counts[name] = counts.get(name, 0) + 1
    return counts


def units_for_witnesses(spec: FieldSpec, witnesses: int,
                        scheme: str = PAIRS) -> int:
    """The smallest community under `scheme` in which EVERY domain is met by at
    least `witnesses` units, or a raise if the scheme cannot reach it at any
    size.

    Read by `_require_witnesses` so a refusal can say what would have worked,
    and by anything else that has to size a community rather than guess one. It
    counts by construction — building each prefix and reading it — rather than
    by an arithmetic shortcut, so it cannot drift from what `apertures_for`
    actually hands back."""
    k = len(spec.domains)
    ceiling = k if scheme == CYCLIC else _n_pairs(k)
    for n in range(1, ceiling + 1):
        counts = witnesses_per_domain(spec, apertures_for(spec, n, scheme=scheme))
        if min(counts.values()) >= witnesses:
            return n
    raise ValueError(
        f"scheme {scheme!r} over {k} domains cannot witness every domain "
        f"{witnesses} times at any community size: its largest community is "
        f"{ceiling} units and reaches "
        f"{min(witnesses_per_domain(spec, apertures_for(spec, ceiling, scheme=scheme)).values())}"
    )


def _require_witnesses(spec: FieldSpec, apertures: List["Aperture"],
                       min_witnesses: int, scheme: str) -> None:
    counts = witnesses_per_domain(spec, apertures)
    short = {name: n for name, n in sorted(counts.items()) if n < min_witnesses}
    if not short:
        return
    try:
        enough = f"{units_for_witnesses(spec, min_witnesses, scheme)} units"
    except ValueError:
        enough = f"no community under scheme {scheme!r}"
    raise ValueError(
        f"{len(apertures)} units under scheme {scheme!r} leave "
        f"{short} witnessed fewer than {min_witnesses} times: a doubt about a "
        f"law of such a domain cannot be corroborated, because the holder is "
        f"never one of the voices — {enough} would satisfy it"
    )
