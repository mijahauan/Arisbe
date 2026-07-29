# C-Series Stages 1–2 (Field + Unit, then Provenance) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, law-bearing field that a single kytos meets through an aperture and is scored against at its own membrane, then give materialization provenance so that *use* can mean participating in work rather than arriving again.

**Architecture:** Two new modules and one surgical extension. `c_field.py` generates a seeded world of partially overlapping domains whose hidden unary laws are never stated, though both their antecedents and their consequents are delivered — the consequent lagging its antecedent by one round, so a unit holding the law can anticipate what has not yet arrived while a unit still learning has the material to induce it. `c_membrane.py` scores those anticipations against what actually arrives, reusing the existing three-valued `classify` (hit / miss / abstain) so an open-world abstention is never punished as an error. `model_materialization.py` gains an optional provenance map recording, per derived fact, the support that produced it; `c_use.py` turns that into a work-driven usage clock and demonstrates it retains a different set of atoms than the arrival-driven clock does.

**Tech Stack:** Python 3.12, `uv run pytest`, existing modules `model_materialization` (Horn forward-chaining), `resolving_membrane.classify` (three-valued scoring), `egif_parser_dau` / `egi_core_dau` (EGI construction). No new dependencies.

## Global Constraints

Copied from `docs/superpowers/specs/2026-07-28-community-scaling-experiment-design.md`. Every task's requirements implicitly include this section.

- **Nothing is scored against the field's regime.** The generator's structure is the *field's regime*, never "ground truth." Fitness is scored **at the membrane** — did the unit anticipate what actually arrived? Regime knowledge may be used only in tests and in explicitly labelled modeler diagnostics, and must never reach a scoring path.
- **No data structure may be named "commens."** (THE_COMMENS_AND_THE_COMMUNITY §1.) `commens` must not appear as a class, variable, field, or module name.
- **Divergence by construction:** apertures differ per unit. A shared aperture across units is a defect, not a default.
- **Determinism:** one seed governs all randomness. Any run re-executed with the same seed produces byte-identical output. Never call `random` module-level functions; always use a `random.Random(seed)` instance threaded explicitly.
- **Custody:** run outputs go under `runs/` (already git-ignored). Console output is numbers only — never a note id, title, or path.
- **Protected modules:** `model_materialization.py` is **not** protected (verified 2026-07-28 via `uv run python tools/core_protection_system.py --report`). Do not modify any of the 14 protected modules; if a task appears to require it, stop and report.
- **Existing behavior is frozen:** every change to `model_materialization.py` must be backward compatible — provenance is opt-in via a default-`None` parameter, and the existing test suite must pass untouched.
- **Import style:** `from module_name import Foo` (not `from src.module_name import Foo`).

---

## File Structure

| File | Responsibility |
|---|---|
| `src/c_field.py` (create) | The field's regime: domains, their hidden unary laws, individuals, and the deterministic deliverance stream with its one-round consequent lag. Apertures. Knows nothing about units. |
| `src/c_membrane.py` (create) | Anticipation and membrane-level scoring. A `MembraneLedger` of hits/misses/abstentions keyed on facts. Knows nothing about the regime. |
| `src/c_unit.py` (create) | One kytos: holds facts and laws, materializes, emits anticipations, and performs one inductive step. |
| `src/model_materialization.py` (modify) | Gains an optional provenance map: per derived fact, the support set that produced it. |
| `src/c_use.py` (create) | Work-driven usage: which atoms participated in deriving anything, contrasted with arrival-driven usage. |
| `tests/test_c_field.py` (create) | Field determinism, the consequent lag, aperture distinctness. |
| `tests/test_c_membrane.py` (create) | Scoring semantics, including abstention. |
| `tests/test_c_unit.py` (create) | The Stage 1 gate: a unit that induces a planted law scores better than one that cannot. |
| `tests/test_materialization_provenance.py` (create) | Support recovery, determinism, backward compatibility. |
| `tests/test_c_use.py` (create) | The Stage 2 gate: work-use and arrival-use retain different atoms. |

---

### Task 1: The field's domains and deterministic deliverance

**Files:**
- Create: `src/c_field.py`
- Test: `tests/test_c_field.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `Key = Tuple[str, str]` and `Fact = Tuple[str, Tuple[Key, ...]]` (re-exported from `model_materialization`); `Domain(name: str, antecedents: Tuple[str, ...], law: Tuple[str, str], individuals: Tuple[str, ...])`; `FieldSpec(seed: int, domains: Tuple[Domain, ...])`; `default_spec(seed: int = 20260728) -> FieldSpec`; `Field(spec: FieldSpec)` with `deliver(domain_name: str, round_idx: int) -> List[Fact]` and `consequent(domain_name: str, f: Fact) -> Optional[Fact]`.

A domain's `law` is a pair `(body_rel, head_rel)` meaning `body(x) → head(x)`. The field delivers a round's antecedents together with the consequents licensed by the **previous** round's antecedents. That one-round lag does two jobs at once: it makes anticipation genuinely predictive (the consequent has not arrived yet when the forecast is placed), and it leaves both halves of the law observable, so a unit can induce it from what it has seen.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_c_field.py
from c_field import Field, default_spec


def test_same_seed_delivers_identical_streams():
    a = Field(default_spec(seed=7))
    b = Field(default_spec(seed=7))
    for r in range(5):
        for d in ("alpha", "beta", "gamma", "delta"):
            assert a.deliver(d, r) == b.deliver(d, r)


def test_consequents_lag_their_antecedents_by_one_round():
    spec = default_spec(seed=7)
    field = Field(spec)
    d = spec.domains[0]
    body_rel, head_rel = d.law

    assert not [f for f in field.deliver(d.name, 0) if f[0] == head_rel], \
        "round 0 has no prior round, so no consequent may appear"

    bodies_at_0 = {args for rel, args in field.deliver(d.name, 0) if rel == body_rel}
    heads_at_1 = {args for rel, args in field.deliver(d.name, 1) if rel == head_rel}
    assert bodies_at_0 == heads_at_1, "each consequent follows its antecedent by one round"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_c_field.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'c_field'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/c_field.py
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
                   ("a1", "a2", "a3", "a4", "a5")),
            Domain("beta", ("shared", "b_local"), ("b_local", "b_head"),
                   ("b1", "b2", "b3", "b4", "b5")),
            Domain("gamma", ("shared", "g_local"), ("g_local", "g_head"),
                   ("g1", "g2", "g3", "g4", "g5")),
            Domain("delta", ("shared", "d_local"), ("d_local", "d_head"),
                   ("d1", "d2", "d3", "d4", "d5")),
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_c_field.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/c_field.py tests/test_c_field.py
git commit -m "feat(c-series): the field's regime — four domains, hidden unary laws, deterministic deliverance"
```

---

### Task 2: Apertures over the field

**Files:**
- Modify: `src/c_field.py`
- Test: `tests/test_c_field.py`

**Interfaces:**
- Consumes: `Field`, `FieldSpec`, `Domain` from Task 1.
- Produces: `Aperture(unit_id: str, domains: Tuple[str, ...])`; `apertures_for(spec: FieldSpec, n_units: int) -> List[Aperture]`; `Field.at(aperture: Aperture, round_idx: int) -> List[Fact]`.

`at` is simply what arrives at this unit's membrane in this round — the union of its domains' deliveries. There is no privileged second channel: the unit is scored on anticipating exactly what it will then observe.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_c_field.py
from c_field import Field, default_spec, apertures_for


def test_apertures_differ_between_units():
    spec = default_spec(seed=7)
    aps = apertures_for(spec, n_units=4)
    assert len(aps) == 4
    assert len({a.domains for a in aps}) > 1, "all apertures identical — premise 3 violated"


def test_aperture_delivers_the_union_of_its_domains():
    spec = default_spec(seed=7)
    field = Field(spec)
    ap = apertures_for(spec, n_units=4)[0]
    expected = set()
    for name in ap.domains:
        expected |= set(field.deliver(name, 3))
    assert set(field.at(ap, 3)) == expected
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_c_field.py -v`
Expected: FAIL with `ImportError: cannot import name 'apertures_for'`

- [ ] **Step 3: Write minimal implementation**

```python
# append to src/c_field.py

@dataclass(frozen=True)
class Aperture:
    """The slice of the field one unit meets. Distinct per unit by
    construction (spec premise 3)."""
    unit_id: str
    domains: Tuple[str, ...]


def apertures_for(spec: FieldSpec, n_units: int) -> List["Aperture"]:
    """Deterministic, overlapping, and pairwise distinct wherever the domain
    count allows: unit i sees domains i and i+1 (mod count), so consecutive
    units share exactly one domain."""
    names = [d.name for d in spec.domains]
    k = len(names)
    out: List[Aperture] = []
    for i in range(n_units):
        first = names[i % k]
        second = names[(i + 1) % k]
        out.append(Aperture(f"u{i}", (first, second)))
    return out
```

and, inside `class Field`:

```python
    def at(self, aperture: "Aperture", round_idx: int) -> List[Fact]:
        """What arrives at this unit's membrane this round: the union of its
        domains' deliveries."""
        out: Set[Fact] = set()
        for name in aperture.domains:
            out.update(self.deliver(name, round_idx))
        return sorted(out)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_c_field.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/c_field.py tests/test_c_field.py
git commit -m "feat(c-series): apertures over the field"
```

---

### Task 3: Membrane scoring

**Files:**
- Create: `src/c_membrane.py`
- Test: `tests/test_c_membrane.py`

**Interfaces:**
- Consumes: `Fact` from `model_materialization`; `classify` from `resolving_membrane`.
- Produces: `MembraneLedger()` with `score(anticipated: Set[Fact], arrived: Set[Fact], round_idx: int) -> None`, properties `hits`, `misses`, `abstentions`, and `accuracy -> float`.

Scoring rule, stated once so later tasks share it: an anticipated fact that arrived is a **hit**; an anticipated fact that did not arrive is a **miss**; a fact that arrived but was not anticipated is an **abstention** — the unit placed no bet, and open-world silence is never punished as error. This is the same three-valued discipline `resolving_membrane.classify` already encodes, and `accuracy` is `hits / (hits + misses)` with abstentions excluded from the denominator.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_c_membrane.py
from c_membrane import MembraneLedger

A = ("a_head", (("c", "a1"),))
B = ("b_head", (("c", "b1"),))
C = ("shared", (("c", "a2"),))


def test_hit_miss_and_abstention():
    led = MembraneLedger()
    led.score(anticipated={A, B}, arrived={A, C}, round_idx=0)
    assert led.hits == 1          # A anticipated and arrived
    assert led.misses == 1        # B anticipated, did not arrive
    assert led.abstentions == 1   # C arrived, no bet placed


def test_accuracy_excludes_abstentions():
    led = MembraneLedger()
    led.score(anticipated={A}, arrived={A, C}, round_idx=0)
    assert led.accuracy == 1.0


def test_accuracy_is_zero_with_no_bets():
    led = MembraneLedger()
    led.score(anticipated=set(), arrived={A}, round_idx=0)
    assert led.accuracy == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_c_membrane.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'c_membrane'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/c_membrane.py
"""Membrane-level scoring for the C-series.

A unit is scored on what it anticipated against what arrived AT ITS OWN
MEMBRANE — never against the field's regime (spec premise 1). Abstention
(arrived but unanticipated) is not an error: open-world silence places no
bet. The three-valued discipline is `resolving_membrane.classify`'s.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import List, Set, Tuple

from model_materialization import Fact
from resolving_membrane import classify


@dataclass(frozen=True)
class MembraneEntry:
    round_idx: int
    fact: Fact
    result: str          # "hit" | "miss" | "abstain"


@dataclass
class MembraneLedger:
    """A unit's own track record — K1, made live."""
    entries: List[MembraneEntry] = dc_field(default_factory=list)

    def score(self, anticipated: Set[Fact], arrived: Set[Fact],
              round_idx: int) -> None:
        for f in sorted(anticipated):
            self.entries.append(
                MembraneEntry(round_idx, f, classify("true", f in arrived)))
        for f in sorted(arrived - anticipated):
            self.entries.append(
                MembraneEntry(round_idx, f, classify("unknown", True)))

    @property
    def hits(self) -> int:
        return sum(1 for e in self.entries if e.result == "hit")

    @property
    def misses(self) -> int:
        return sum(1 for e in self.entries if e.result == "miss")

    @property
    def abstentions(self) -> int:
        return sum(1 for e in self.entries if e.result == "abstain")

    @property
    def accuracy(self) -> float:
        bets = self.hits + self.misses
        return self.hits / bets if bets else 0.0
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_c_membrane.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/c_membrane.py tests/test_c_membrane.py
git commit -m "feat(c-series): membrane-level scoring with open-world abstention"
```

---

### Task 4: The unit — holding a law changes what it anticipates

**Files:**
- Create: `src/c_unit.py`
- Test: `tests/test_c_unit.py`

**Interfaces:**
- Consumes: `Field`, `Aperture` (Tasks 1–2); `MembraneLedger` (Task 3); `Fact` from `model_materialization`.
- Produces: `Unit(unit_id: str, aperture: Aperture)` with attributes `facts: Set[Fact]`, `laws: Set[Tuple[str, str]]`, `ledger: MembraneLedger`; methods `absorb(field, round_idx) -> None`, `anticipate() -> Set[Fact]`, `step(field, round_idx) -> None`.

`anticipate` applies each held law to the unit's own facts and returns only atoms it does **not** already hold — a prediction is about what it has not yet seen. A unit with no laws anticipates nothing, so it scores accuracy 0.0 while never accruing a miss, which is the correct open-world reading: placing no bet is not being wrong.

Order within a round matters and is the point: **anticipate first, then observe.** The forecast is placed before the outcome arrives, which is what makes the ledger a track record rather than a scorecard filled in after the fact.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_c_unit.py
from c_field import Field, default_spec, apertures_for
from c_unit import Unit


def _setup(seed=7):
    spec = default_spec(seed=seed)
    return spec, Field(spec), apertures_for(spec, n_units=4)[0]


def test_lawless_unit_anticipates_nothing():
    _spec, field, ap = _setup()
    u = Unit("u0", ap)
    u.absorb(field, 0)
    assert u.anticipate() == set()


def test_unit_holding_the_law_anticipates_the_consequent():
    spec, field, ap = _setup()
    u = Unit("u0", ap)
    first = spec.domains[0]
    u.laws.add(first.law)
    u.absorb(field, 0)          # now holds round 0's antecedents
    anticipated = u.anticipate()
    assert anticipated, "a held law should license some anticipation"
    head = first.law[1]
    assert all(rel == head for rel, _ in anticipated)


def test_held_law_beats_no_law_over_a_run():
    spec, field, ap = _setup()
    lawful, lawless = Unit("u0", ap), Unit("u1", ap)
    lawful.laws.add(spec.domains[0].law)
    for r in range(20):
        lawful.step(field, r)
        lawless.step(field, r)
    assert lawful.ledger.hits > 0
    assert lawless.ledger.hits == 0
    assert lawful.ledger.accuracy > lawless.ledger.accuracy
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_c_unit.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'c_unit'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/c_unit.py
"""One kytos, for C-series stage 1: it observes through its aperture,
anticipates from the laws it holds, and is scored at its own membrane.

It never reads the field's regime and never sees another unit. Communication
arrives in stage 3.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Dict, Set, Tuple

from c_field import Aperture, Field
from c_membrane import MembraneLedger
from model_materialization import Fact, Key


@dataclass
class Unit:
    unit_id: str
    aperture: Aperture
    facts: Set[Fact] = dc_field(default_factory=set)
    laws: Set[Tuple[str, str]] = dc_field(default_factory=set)
    ledger: MembraneLedger = dc_field(default_factory=MembraneLedger)

    def absorb(self, field: Field, round_idx: int) -> None:
        """Take in everything that arrived this round."""
        self.facts.update(field.at(self.aperture, round_idx))

    def anticipate(self) -> Set[Fact]:
        """Apply every held law to held facts; keep only what is not already
        held. A prediction concerns what this unit has not yet seen."""
        out: Set[Fact] = set()
        for body_rel, head_rel in self.laws:
            for rel, args in self.facts:
                if rel == body_rel:
                    candidate: Fact = (head_rel, args)
                    if candidate not in self.facts:
                        out.add(candidate)
        return out

    def step(self, field: Field, round_idx: int) -> None:
        """One round: anticipate from what is already held, then observe what
        arrives and be scored on the forecast. The bet is placed before the
        outcome is seen."""
        anticipated = self.anticipate()
        arrived = set(field.at(self.aperture, round_idx))
        self.ledger.score(anticipated, arrived, round_idx)
        self.facts.update(arrived)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_c_unit.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/c_unit.py tests/test_c_unit.py
git commit -m "feat(c-series): the unit — anticipate from held laws, then observe and be scored at the membrane"
```

---

### Task 5: Induction — the Stage 1 gate

**Files:**
- Modify: `src/c_unit.py`
- Test: `tests/test_c_unit.py`

**Interfaces:**
- Consumes: `Unit` from Task 4.
- Produces: `Unit.induce(min_support: int = 3, max_pending: int = 1) -> Set[Tuple[str, str]]`, which adds newly-induced laws to `self.laws` and returns them; `Unit.step` gains a keyword `induce: bool = False`.

Induction rule: propose `body → head` when at least `min_support` individuals are held with both `body(x)` and `head(x)`, and **at most `max_pending`** individuals are held with `body(x)` but not `head(x)`.

Why a tolerance rather than zero: the field's one-round lag means the antecedent just delivered has not yet had its consequent delivered. At any moment there is therefore exactly **one** legitimately pending individual per body relation, and a strict no-counterexample rule would misread that timing artifact as a refutation and block every true law forever. `max_pending=1` is the lag's exact width, not a fudge factor.

**Expect over-general laws, and do not suppress them.** In this field every individual eventually receives every head, so a unit will also induce true-but-accidental regularities (e.g. `shared → a_head`). That is correct behavior for induction from a finite record, and defeating such laws is precisely what the challenge channel is for in stage 3. Stage 1 asserts only that a *planted* law is among those induced.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_c_unit.py

def _unary(rel, names):
    return {(rel, (("c", n),)) for n in names}


def test_induction_needs_enough_support():
    _spec, _field, ap = _setup()
    u = Unit("u0", ap)
    u.facts.update(_unary("p", ["x0", "x1", "x2"]))
    u.facts.update(_unary("q", ["x0", "x1", "x2"]))
    assert ("p", "q") in u.induce(min_support=3)

    v = Unit("u1", ap)
    v.facts.update(_unary("p", ["y0", "y1"]))
    v.facts.update(_unary("q", ["y0", "y1"]))
    assert ("p", "q") not in v.induce(min_support=3)


def test_one_pending_antecedent_is_tolerated_two_are_not():
    """The lag leaves exactly one antecedent awaiting its consequent."""
    _spec, _field, ap = _setup()
    lagging = Unit("u0", ap)
    lagging.facts.update(_unary("p", ["x0", "x1", "x2", "x3"]))
    lagging.facts.update(_unary("q", ["x0", "x1", "x2"]))       # x3 pending
    assert ("p", "q") in lagging.induce(min_support=3, max_pending=1)

    refuted = Unit("u1", ap)
    refuted.facts.update(_unary("p", ["y0", "y1", "y2", "y3", "y4"]))
    refuted.facts.update(_unary("q", ["y0", "y1", "y2"]))       # y3, y4 refute
    assert ("p", "q") not in refuted.induce(min_support=3, max_pending=1)


def test_inducing_unit_learns_the_planted_law_and_its_score_rises():
    """The Stage 1 gate: a unit that may induce ends up holding a law the
    regime actually planted, and outperforms one that may not."""
    spec, field, ap = _setup()
    learner, fixed = Unit("u0", ap), Unit("u1", ap)
    for r in range(60):
        learner.step(field, r, induce=True)
        fixed.step(field, r, induce=False)
    planted = {d.law for d in spec.domains}
    assert learner.laws & planted, "no planted law was induced"
    assert learner.ledger.hits > 0
    assert learner.ledger.accuracy > fixed.ledger.accuracy
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_c_unit.py -v`
Expected: FAIL with `TypeError: step() got an unexpected keyword argument 'induce'`

- [ ] **Step 3: Write minimal implementation**

Add to `class Unit` in `src/c_unit.py`:

```python
    def induce(self, min_support: int = 3,
               max_pending: int = 1) -> Set[Tuple[str, str]]:
        """Propose body -> head where enough individuals carry both and at
        most `max_pending` carry body without head.

        The tolerance is the field's one-round lag: the antecedent just
        delivered has not had its consequent delivered yet, so exactly one
        individual per body relation is legitimately pending. Zero tolerance
        would read that timing artifact as a refutation and block every true
        law permanently."""
        holders: Dict[str, Set[Tuple[Key, ...]]] = {}
        for rel, args in self.facts:
            holders.setdefault(rel, set()).add(args)
        found: Set[Tuple[str, str]] = set()
        for body_rel, body_args in sorted(holders.items()):
            for head_rel, head_args in sorted(holders.items()):
                if body_rel == head_rel:
                    continue
                if len(body_args & head_args) < min_support:
                    continue
                if len(body_args - head_args) > max_pending:
                    continue
                law = (body_rel, head_rel)
                if law not in self.laws:
                    found.add(law)
        self.laws.update(found)
        return found
```

and replace `step` with:

```python
    def step(self, field: Field, round_idx: int, induce: bool = False) -> None:
        """One round: anticipate from what is held, observe what arrives, be
        scored on the forecast, then optionally induce from the enlarged
        record. Inducing last means a law never scores the round that taught
        it."""
        anticipated = self.anticipate()
        arrived = set(field.at(self.aperture, round_idx))
        self.ledger.score(anticipated, arrived, round_idx)
        self.facts.update(arrived)
        if induce:
            self.induce()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_c_unit.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/c_unit.py tests/test_c_unit.py
git commit -m "feat(c-series): inductive step — the stage 1 gate, a unit learns a planted law and outscores one that cannot"
```

---

### Task 6: Provenance in forward-chaining

**Files:**
- Modify: `src/model_materialization.py` (the `_chase` function, and `materialize_egi`)
- Test: `tests/test_materialization_provenance.py`

**Interfaces:**
- Consumes: `Fact`, `_chase`, `_extract`, `materialize_egi` (existing).
- Produces: `_chase(facts, horn, delta=None, provenance=None)` where `provenance: Optional[Dict[Fact, FrozenSet[Fact]]]`; `materialize_egi(egi, provenance=None)` threading the same map.

Determinism rule: a fact may be derivable several ways in one round, and set iteration order is not guaranteed. Keep the support whose **sorted tuple is lexicographically smallest**, so the recorded provenance is identical across runs regardless of iteration order.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_materialization_provenance.py
from egif_parser_dau import parse_egif
from model_materialization import materialize_egi

# A law (p x -> q x) plus one ground fact.
EGIF = '~[ (p *x) ~[ (q x) ] ] (p "a")'


def test_provenance_records_the_support_of_a_derived_fact():
    egi = parse_egif(EGIF)
    prov = {}
    _facts_egi, report = materialize_egi(egi, provenance=prov)
    assert report.derived_facts == 1
    derived = ("q", (("c", "a"),))
    assert derived in prov
    assert prov[derived] == frozenset({("p", (("c", "a"),))})


def test_provenance_is_optional_and_backward_compatible():
    egi = parse_egif(EGIF)
    _facts_egi, report = materialize_egi(egi)
    assert report.derived_facts == 1


def test_provenance_is_deterministic_across_repeated_runs():
    seen = []
    for _ in range(5):
        prov = {}
        materialize_egi(parse_egif(EGIF), provenance=prov)
        seen.append({k: tuple(sorted(v)) for k, v in prov.items()})
    assert all(s == seen[0] for s in seen)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_materialization_provenance.py -v`
Expected: FAIL with `TypeError: materialize_egi() got an unexpected keyword argument 'provenance'`

- [ ] **Step 3: Write minimal implementation**

In `src/model_materialization.py`, add a module-level helper above `_chase`:

```python
def _instantiate(atom: Fact, bind) -> Fact:
    """A body atom under a binding — the same substitution the head uses."""
    rel, args = atom
    return (rel, tuple(k if k[0] == "c" else bind[k] for k in args))
```

Change `_chase`'s signature to accept `provenance=None` and, inside the derivation branch, replace

```python
                        if f not in facts:
                            new.add(f)
```

with

```python
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
```

Then thread it through `materialize_egi`:

```python
def materialize_egi(
    egi: RelationalGraphWithCuts,
    provenance=None,
) -> Tuple[RelationalGraphWithCuts, MaterializationReport]:
```

and pass `provenance=provenance` at its internal `_chase(...)` call.

- [ ] **Step 4: Run tests to verify they pass, including the existing suite**

Run: `uv run pytest tests/test_materialization_provenance.py tests/test_model_materialization.py -v`
Expected: 3 passed (new) and the existing materialization tests all still passing

- [ ] **Step 5: Commit**

```bash
git add src/model_materialization.py tests/test_materialization_provenance.py
git commit -m "feat(c-series): optional provenance in forward-chaining — a derived fact's support, deterministically recorded"
```

---

### Task 7: Work-use versus arrival-use — the Stage 2 gate

**Files:**
- Create: `src/c_use.py`
- Test: `tests/test_c_use.py`

**Interfaces:**
- Consumes: provenance map from Task 6; `Fact`.
- Produces: `work_used(provenance: Dict[Fact, FrozenSet[Fact]]) -> Set[Fact]`; `WorkUsageLedger(ttl: int)` with `touch_work(provenance, round_idx)`, `touch_arrival(delivered: Set[Fact], round_idx)`, and `stale(round_idx, mode: str) -> List[Fact]` where `mode` is `"work"` or `"arrival"`.

This is the honest definition the E-series lacked: an atom counts as used when it appears in the support of something derived, not when the feed announced it again.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_c_use.py
from c_use import WorkUsageLedger, work_used

P_A = ("p", (("c", "a"),))
Q_A = ("q", (("c", "a"),))
NOISE = ("noise", (("c", "z"),))


def test_work_used_reads_supports_not_conclusions():
    prov = {Q_A: frozenset({P_A})}
    assert work_used(prov) == {P_A}


def test_work_and_arrival_clocks_retain_different_atoms():
    """The Stage 2 gate. P_A does work every round but is delivered only
    once; NOISE is delivered every round and does no work. The two clocks
    must therefore keep different atoms."""
    led = WorkUsageLedger(ttl=3)
    prov = {Q_A: frozenset({P_A})}
    led.touch_arrival({P_A, NOISE}, 0)
    for r in range(1, 10):
        led.touch_work(prov, r)
        led.touch_arrival({NOISE}, r)

    work_stale = set(led.stale(9, mode="work"))
    arrival_stale = set(led.stale(9, mode="arrival"))

    assert NOISE in work_stale and NOISE not in arrival_stale
    assert P_A in arrival_stale and P_A not in work_stale
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_c_use.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'c_use'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/c_use.py
"""Use as participation in work.

The E-series defined use as re-delivery: an atom survived because the feed
announced it again, whether or not anything was ever done with it. Here an
atom counts as used when it appears in the SUPPORT of something derived.
Both clocks are kept side by side so their difference is measurable.
"""

from __future__ import annotations

from typing import Dict, FrozenSet, List, Set

from model_materialization import Fact


def work_used(provenance: Dict[Fact, FrozenSet[Fact]]) -> Set[Fact]:
    """The atoms that did work: every atom appearing in any support. The
    derived conclusions themselves are not counted — doing work means being
    a premise."""
    out: Set[Fact] = set()
    for support in provenance.values():
        out.update(support)
    return out


class WorkUsageLedger:
    """Two clocks over the same atoms: one driven by work, one by arrival."""

    def __init__(self, ttl: int):
        self.ttl = ttl
        self._work: Dict[Fact, int] = {}
        self._arrival: Dict[Fact, int] = {}

    def touch_work(self, provenance: Dict[Fact, FrozenSet[Fact]],
                   round_idx: int) -> None:
        for f in work_used(provenance):
            self._work[f] = round_idx
            self._arrival.setdefault(f, round_idx)

    def touch_arrival(self, delivered: Set[Fact], round_idx: int) -> None:
        for f in delivered:
            self._arrival[f] = round_idx
            self._work.setdefault(f, round_idx)

    def stale(self, round_idx: int, mode: str) -> List[Fact]:
        if mode not in ("work", "arrival"):
            raise ValueError(f"mode must be 'work' or 'arrival', got {mode!r}")
        clock = self._work if mode == "work" else self._arrival
        return sorted(f for f, last in clock.items()
                      if round_idx - last >= self.ttl)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_c_use.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/c_use.py tests/test_c_use.py
git commit -m "feat(c-series): work-use vs arrival-use — the stage 2 gate, two clocks retain different atoms"
```

---

### Task 8: Stage gates verified together

**Files:**
- Create: `tests/test_c_stage_gates.py`

**Interfaces:**
- Consumes: everything from Tasks 1–7.
- Produces: nothing; this task exists to assert the two stage gates from the spec in one place, so a reviewer can check them without reading five files.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_c_stage_gates.py
"""The two gates the spec sets for stages 1 and 2."""

from c_field import Field, default_spec, apertures_for
from c_unit import Unit
from c_use import WorkUsageLedger
from egif_parser_dau import parse_egif
from model_materialization import materialize_egi


def test_stage_1_gate_a_unit_learns_a_planted_law_and_its_score_rises():
    spec = default_spec(seed=20260728)
    field = Field(spec)
    ap = apertures_for(spec, n_units=4)[0]
    learner, fixed = Unit("u0", ap), Unit("u1", ap)
    for r in range(60):
        learner.step(field, r, induce=True)
        fixed.step(field, r, induce=False)
    assert learner.laws & {d.law for d in spec.domains}
    assert learner.ledger.accuracy > fixed.ledger.accuracy


def test_stage_2_gate_support_is_recoverable_and_changes_what_survives():
    prov = {}
    materialize_egi(parse_egif('~[ (p *x) ~[ (q x) ] ] (p "a")'),
                    provenance=prov)
    assert prov, "no support recorded"

    p_a = ("p", (("c", "a"),))
    noise = ("noise", (("c", "z"),))
    led = WorkUsageLedger(ttl=3)
    led.touch_arrival({p_a, noise}, 0)
    for r in range(1, 10):
        led.touch_work(prov, r)
        led.touch_arrival({noise}, r)
    assert set(led.stale(9, mode="work")) != set(led.stale(9, mode="arrival"))


def test_determinism_canary_two_runs_agree():
    def run():
        spec = default_spec(seed=20260728)
        field = Field(spec)
        ap = apertures_for(spec, n_units=4)[0]
        u = Unit("u0", ap)
        for r in range(30):
            u.step(field, r, induce=True)
        return sorted(u.laws), u.ledger.hits, u.ledger.misses

    assert run() == run()
```

- [ ] **Step 2: Run test to verify it fails or passes**

Run: `uv run pytest tests/test_c_stage_gates.py -v`
Expected: PASS if Tasks 1–7 are complete. If any gate fails, that is a real finding about the design — stop and report rather than adjusting the test to fit.

- [ ] **Step 3: Run the full suite for regressions**

Run: `uv run pytest tests/ -q`
Expected: no new failures against the pre-existing baseline (~3900 passing)

- [ ] **Step 4: Commit**

```bash
git add tests/test_c_stage_gates.py
git commit -m "test(c-series): the stage 1 and stage 2 gates, plus a determinism canary"
```

---

## Notes for the implementer

- **If a gate fails, that is data.** The spec pre-registers what "nothing" looks like precisely so a negative result can be reported rather than engineered away. Do not weaken a gate's assertion to make it pass; stop and report what happened.
- **Stages 3–5** (communication, community and selection, instruments) are deliberately out of scope. Do not add a coordinator, a mark ledger, or a second community — those need their own plan against spec §5–§7.
- **`west_coordinator.py` is not touched here.** Its deletion belongs to the stage-3 plan, when there is a replacement.
