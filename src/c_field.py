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
class ObserverNoise:
    """How one observer's membrane distorts what the domain delivered.

    TWO RATES, BECAUSE THEY MAKE DIFFERENT KINDS OF SPEAKER. `withhold` makes a
    unit QUIETER: it meets less than the domain delivered, but everything it
    does meet is true, so its testimony stays sound and it simply has less to
    offer. `spurious` makes a unit UNRELIABLE: it perceives atoms the field
    never delivered and — having no way to tell them from the rest — publishes
    them in good faith.

    The second is the cry-wolf structure the design names (spec 11.2(c)): the
    boy's failure "is not lying — his cry became statistically independent of
    the wolf." Nothing here models deceit, and nothing needs to: a unit that
    reports what it honestly perceived is unreliable exactly insofar as its
    perceptions are uncorrelated with the world.

    Both default to zero, and an observer with no entry gets no distortion at
    all — see `Field.deliver`."""
    withhold: float = 0.0
    spurious: float = 0.0


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
    observers: Tuple[Tuple[str, ObserverNoise], ...] = ()
    """Per-observer distortion, as (unit_id, noise) pairs. EMPTY BY DEFAULT,
    and an absent unit gets no distortion, so every figure measured before this
    existed reads the same.

    WHY THE FIELD GAINED THIS (author's ruling, 2026-07-30). The rates above
    are properties of a DOMAIN: `deliver` drew its noise from
    (seed, domain, round) and never from the unit, so every witness of a domain
    met byte-identical deliverances and no unit could be a more or less
    reliable speaker than any other. Examination VII's VII.4 recorded what that
    cost: alarm reliability, the credential, typification and P-H3 all measure
    a property of speakers, and they were being measured in a world whose
    speakers were interchangeable by construction. A community cannot discover
    whom to trust where there is nothing to discover.

    A TUPLE OF PAIRS rather than a dict because `FieldSpec` is frozen; nothing
    hashes it today, and this keeps that available."""


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
        self._observers: Dict[str, ObserverNoise] = dict(spec.observers)

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

    def _observed(self, domain_name: str, round_idx: int,
                  out: Set[Fact], observer: str) -> Set[Fact]:
        """What ONE observer makes of what the domain delivered.

        Applied after the domain's own noise and drawn from its own RNG, keyed
        on the observer as well as the domain and round. Three consequences,
        all of them load-bearing:

        - AN ABSENT OBSERVER IS NOT A QUIET ONE. `deliver` skips this entirely
          when the id has no entry, so the two-argument call every existing
          measurement makes is byte-identical to what it always was.
        - THE SEPARATE RNG cannot disturb the domain stream, exactly as the
          field's own noise rng cannot disturb the antecedent stream. Naming an
          observer in the spec therefore changes nothing for anyone else.
        - EQUAL RATES ARE NOT EQUAL EXPERIENCE. Keying on the observer id means
          two units carrying the same `ObserverNoise` still meet different
          things, which is what makes reliability a property of a speaker
          rather than of the spec — and so something a peer could discover.

        A mis-observation is shaped like something this domain could have said:
        a relation the domain speaks, about an individual it knows. An invented
        atom that failed that test would be rejectable on shape alone, and the
        channel would carry a tell instead of a falsehood.

        `spurious` is ONE INDEPENDENT CHANCE PER RELATION THIS DOMAIN SPEAKS —
        for each thing the domain could have said, a chance this observer
        believes it said it. That keeps the rate comparable across domains of
        different vocabulary size, where a flat per-round draw would make a
        talkative domain proportionally quieter in error. The withheld set is
        drawn from `sorted(out)` so the sequence is fixed by content rather than
        by set iteration order."""
        d = self._by_name[domain_name]
        noise = self._observers[observer]
        rng = random.Random(f"{self.spec.seed}:obs:{observer}:{domain_name}:{round_idx}")
        seen = {f for f in sorted(out) if rng.random() >= noise.withhold}
        if noise.spurious > 0.0:
            sayable = tuple(d.antecedents) + (d.law[1],)
            for rel in sayable:
                if rng.random() < noise.spurious:
                    seen.add((rel, (("c", rng.choice(d.individuals)),)))
        return seen

    def deliver(self, domain_name: str, round_idx: int,
                observer: Optional[str] = None) -> List[Fact]:
        """What this domain delivers at `round_idx`: this round's antecedents,
        plus the consequents licensed by LAST round's antecedents, passed
        through noise — and, when `observer` names a unit the spec gives an
        `ObserverNoise`, through that unit's membrane as well.

        `observer=None`, and any id the spec does not name, reads the domain
        stream unchanged.

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
        if observer is not None and observer in self._observers:
            out = self._observed(domain_name, round_idx, out, observer)
        return sorted(out)

    def consequent(self, domain_name: str, f: Fact) -> Optional[Fact]:
        """The atom this domain's law licenses from `f`, or None. Modeler-side
        only: used by tests and diagnostics, never by a scoring path."""
        d = self._by_name[domain_name]
        rel, args = f
        body_rel, head_rel = d.law
        return (head_rel, args) if rel == body_rel else None

    def licensed_heads(self, domain_name: str, rounds: int) -> Set[Fact]:
        """Every head atom this domain's law licensed at some round of a
        `rounds`-long run — whether or not `withhold_rate` let it through.

        MODELER-SIDE ONLY, like `consequent`, and for the same reason: it reads
        the regime, so no unit and no scoring path may touch it. What it exists
        for is to tell a FABRICATION from a deliverance in a measurement. A head
        atom outside this set had no antecedent at any round, so the only thing
        that could have produced it is `spurious_rate` — a consequence with no
        cause. An atom inside it may still have arrived spuriously on some
        particular round, which is why this reader answers "could this ever have
        been licensed" rather than "was this delivery licensed": the first
        question is the one a unit's record could in principle bear on, and the
        second is about a round nobody observed."""
        body_rel, head_rel = self._by_name[domain_name].law
        out: Set[Fact] = set()
        for r in range(max(0, rounds - CONSEQUENT_LAG)):
            for rel, args in self._antecedents(domain_name, r):
                if rel == body_rel:
                    out.add((head_rel, args))
        return out

    def at(self, aperture: "Aperture", round_idx: int) -> List[Fact]:
        """What arrives at this unit's membrane this round: the union of its
        domains' deliveries, **as this unit observes them**.

        THE APERTURE CARRIES THE OBSERVER, so this is where speaker-variance
        reaches a unit. Dropping `unit_id` on the way to `deliver` would leave
        `ObserverNoise` reachable only from a test — a mechanism built and never
        connected, which is the failure Examination V named as its V.5.

        A unit the spec does not name reads its domains unchanged, so this is
        the same union it always was."""
        out: Set[Fact] = set()
        for name in aperture.domains:
            out.update(self.deliver(name, round_idx, observer=aperture.unit_id))
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
                  min_witnesses: Optional[int] = None,
                  twin_of: Optional[str] = None) -> List["Aperture"]:
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
    this argument exists to remove, so it is refused rather than degraded.

    `twin_of`, when given, appends ONE extra unit carrying the named unit's
    aperture exactly — THE TWIN CONTROL. The refusal above stays the default and
    a twin has to be asked for by name, so no measurement acquires one by
    accident.

    WHY IT NEEDS NO EXEMPTION FROM PREMISE 3 (author's ruling, 2026-07-30).
    Premise 3 requires units to meet the field through different apertures, or
    "they converge on near-identical models and the apparatus measures nothing"
    — a claim about CONTENT. The twin control holds content and position fixed
    on purpose, in order to ask a different question: whether two units that met
    the same world develop different POLICY. Different axis, so the premise is
    untouched, and the rest of the community still diverges normally.

    WHAT IT IS FOR. Without it, "units with identical rules diverge through
    their own histories" passes by arithmetic — any counter incrementing on a
    unit's own record differs between units of different aperture, and the
    apertures differ by construction. The twin supplies the zero that claim has
    to beat.

    THE CALLER'S OBLIGATION: a twin means something only at MATCHING ATTENDANCE
    PARITY. Under a stagger of 2 the parity is the unit index, so a twin of an
    even-indexed unit must itself land on an even index. This function cannot
    enforce that — it does not own the attendance schedule — so it is stated
    here and the control's own test pins it."""
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
    if twin_of is not None:
        original = next((a for a in out if a.unit_id == twin_of), None)
        if original is None:
            raise ValueError(
                f"cannot twin {twin_of!r}: this community has "
                f"{[a.unit_id for a in out]}"
            )
        out.append(Aperture(f"u{len(out)}", original.domains))
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
