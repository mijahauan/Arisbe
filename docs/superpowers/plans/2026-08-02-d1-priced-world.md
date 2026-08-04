# D-1: The Priced World — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the C-series' observer-side cost meter into a subtraction, so that units have a reserve, run out, split when rich, and die when poor — with no chooser, no `die()`, and no price set by hand.

**Architecture:** One new module `src/d_world.py` wraps an unmodified C-series community. It owns the reserves (outside every membrane, so no unit can read its own), computes a price `τ = E1 / demand` that clears a bounded source against realised demand, pays a bounded pool pro rata by prediction hits, and settles births and deaths. `src/c_unit.py` is not touched; `src/c_field.py` gains one additive function.

**Tech Stack:** Python 3.12, `uv`, `pytest`. No new dependencies. Deterministic and geometry-free throughout — no `random` outside the field's existing seeded streams, no `Date.now()`-equivalent, no I/O in `src/`.

**Spec:** [2026-08-02-d-series-building-the-stake-design.md](../specs/2026-08-02-d-series-building-the-stake-design.md)

## Global Constraints

- **`src/c_unit.py` MUST NOT be modified.** The whole design rests on the units being unchanged (spec §3.1).
- **No `die()`, no TTL, no lifespan, anywhere in `src/`.** Death is `reserve ≤ 0` and nothing else. Task 7 enforces this with a source scan.
- **`Unit` must never gain a reserve attribute.** The reserve lives in the world (spec §3.1, THE_KYTOS §1.3). Task 7 enforces it.
- **No chooser.** Nothing in `src/d_world.py` may decide *which* act a unit performs, or skip an act, or order acts. The world charges and pays; it never selects.
- **Imports use the bare module name** — `from c_field import Field`, never `from src.c_field import Field` (project convention, CLAUDE.md).
- **Determinism**: identical inputs give identical outputs, including dict iteration. Sort every collection before iterating where the result is observable.
- **`E1 = 1.0`** is the numéraire and is never varied.
- **Birth requires `entry_price > 0`.** The calibration arm does not breed.
- **Run tests with** `uv run pytest tests/test_d_world.py -v`.
- **Commit after every task.** Quality gates run on commit and must pass.

---

### Task 1: An 8-domain field

**Files:**
- Modify: `src/c_field.py` (append one function after `default_spec`, around line 141)
- Test: `tests/test_d_world.py` (create)

**Interfaces:**
- Consumes: `Domain`, `FieldSpec`, `_individuals`, `CORE` from `c_field`
- Produces: `c_field.wide_spec(seed: int = 20260802, n_domains: int = 8) -> FieldSpec`

**Why:** the spec's seat ceiling comes from `apertures_for(..., scheme=PAIRS)`, which yields `C(k,2)` seats over `k` domains. The existing `default_spec` has 4 domains and therefore 6 seats — too close to any equilibrium for `P-D7` to be interpretable (spec §8 item 6). Eight domains give 28.

- [ ] **Step 1: Write the failing test**

Create `tests/test_d_world.py`:

```python
"""The D-series priced world: reserves, a determined price, and a found population."""

from c_field import (CORE, PAIRS, Field, apertures_for, default_spec,
                     units_for_witnesses, wide_spec, witnesses_per_domain)


def test_wide_spec_gives_eight_domains_and_twenty_eight_seats():
    """The seat ceiling must sit well clear of any equilibrium, or the cap
    decides the population and P-D7 is uninterpretable (spec section 8 item 6)."""
    spec = wide_spec()
    assert len(spec.domains) == 8
    # 28 = C(8,2): the world's own ceiling, not a number anyone chose.
    assert len(apertures_for(spec, n_units=28, scheme=PAIRS)) == 28
    # Every domain carries its own law and its own local antecedent.
    assert len({d.law for d in spec.domains}) == 8
    assert all("shared" in d.antecedents for d in spec.domains)


def test_wide_spec_individuals_are_shared_core_plus_private():
    """Same construction as default_spec: the ten-strong core every domain
    knows, plus thirty private names per domain that no other domain uses."""
    spec = wide_spec()
    for d in spec.domains:
        assert set(CORE) <= set(d.individuals)
        assert len(d.individuals) == 40
    private = [set(d.individuals) - set(CORE) for d in spec.domains]
    for i, a in enumerate(private):
        for b in private[i + 1:]:
            assert not (a & b), "private individuals must not collide"


def test_wide_spec_reaches_three_witnesses_per_domain():
    """N0 is DERIVED, not chosen: the smallest community in which every domain
    has the three witnesses the corroboration ruling requires (spec 3.4)."""
    spec = wide_spec()
    n0 = units_for_witnesses(spec, 3, PAIRS)
    counts = witnesses_per_domain(spec, apertures_for(spec, n0, scheme=PAIRS))
    assert min(counts.values()) >= 3
    assert n0 < 28, "N0 must leave room to grow toward the ceiling"


def test_wide_spec_is_deterministic_and_delivers():
    spec = wide_spec()
    assert wide_spec().domains == spec.domains
    field = Field(spec)
    assert field.deliver("dom0", 5) == field.deliver("dom0", 5)
    assert any(field.deliver(f"dom{i}", r) for i in range(8) for r in range(5))


def test_default_spec_is_untouched():
    """The additive guarantee: no existing C-series figure may move."""
    assert len(default_spec().domains) == 4
    assert [d.name for d in default_spec().domains] == [
        "alpha", "beta", "gamma", "delta"]
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_d_world.py -v`
Expected: FAIL — `ImportError: cannot import name 'wide_spec' from 'c_field'`

- [ ] **Step 3: Write the implementation**

Append to `src/c_field.py`, immediately after `default_spec` ends (after the closing `)` of its return, around line 141):

```python
def wide_spec(seed: int = 20260802, n_domains: int = 8) -> FieldSpec:
    """`default_spec`'s construction at a width the D-series needs.

    WHY A WIDER FIELD EXISTS. Under `PAIRS` a field of k domains offers exactly
    C(k, 2) distinct apertures, and `apertures_for` refuses to seat two units on
    one slice — so the field's width IS the population ceiling. At the four
    domains `default_spec` carries, that ceiling is six, which sits close enough
    to any plausible equilibrium that the CAP would decide the population rather
    than the economy, and the D-series' P-D7 would be uninterpretable. Eight
    domains give twenty-eight.

    ADDITIVE, AND `default_spec` IS UNTOUCHED. Every C-series figure was measured
    on the four-domain field and none of them moves.

    Rates and construction are `default_spec`'s exactly — the ten-strong shared
    core plus thirty private individuals per domain, `shared` in every domain's
    antecedents, one hidden unary law each — so the only thing that varies
    between the two is width."""
    domains = []
    for i in range(n_domains):
        prefix = f"x{i}"
        domains.append(Domain(
            f"dom{i}",
            ("shared", f"{prefix}_local"),
            (f"{prefix}_local", f"{prefix}_head"),
            _individuals(prefix),
        ))
    return FieldSpec(
        seed=seed,
        withhold_rate=0.1,
        spurious_rate=0.1,
        domains=tuple(domains),
    )
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_d_world.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add src/c_field.py tests/test_d_world.py
git commit -m "D-1: an 8-domain field, so the seat ceiling clears the equilibrium"
```

---

### Task 2: `Source` and `Reserves`

**Files:**
- Create: `src/d_world.py`
- Test: `tests/test_d_world.py` (append)

**Interfaces:**
- Produces:
  - `Source(pool_per_round: float = 1.0, entry_price: float = 0.0)` — frozen dataclass
  - `Reserves()` with `seed(unit_id: str, amount: float) -> None`, `credit(unit_id, amount) -> None`, `charge(unit_id, amount) -> None`, `balance(unit_id) -> float`, `alive(unit_id) -> bool`, `drop(unit_id) -> None`, `total() -> float`, `living() -> List[str]`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_d_world.py`:

```python
import pytest

from d_world import Reserves, Source


def test_source_defaults_to_the_numeraire():
    """E1 = 1 fixes the unit of account and nothing else (spec 3.4)."""
    assert Source().pool_per_round == 1.0
    assert Source().entry_price == 0.0


def test_reserves_credit_charge_and_balance():
    r = Reserves()
    r.seed("u0", 10.0)
    r.credit("u0", 2.5)
    r.charge("u0", 4.0)
    assert r.balance("u0") == pytest.approx(8.5)


def test_death_is_reserve_at_or_below_zero():
    """No die(), no TTL, no lifespan -- running out IS death (spec ruling 1)."""
    r = Reserves()
    r.seed("u0", 1.0)
    assert r.alive("u0")
    r.charge("u0", 1.0)
    assert not r.alive("u0"), "exactly zero is dead, not the last breath"
    r.seed("u1", 1.0)
    r.charge("u1", 5.0)
    assert not r.alive("u1")


def test_living_is_sorted_and_excludes_the_dropped():
    r = Reserves()
    for uid in ("u2", "u0", "u1"):
        r.seed(uid, 3.0)
    assert r.living() == ["u0", "u1", "u2"]
    r.charge("u1", 3.0)
    assert r.living() == ["u0", "u2"]
    r.drop("u1")
    assert r.living() == ["u0", "u2"]
    assert r.total() == pytest.approx(6.0)


def test_an_unknown_unit_has_no_balance_and_is_not_alive():
    r = Reserves()
    assert r.balance("ghost") == 0.0
    assert not r.alive("ghost")


def test_seeding_twice_refuses():
    """A unit is endowed once, at entry. Re-seeding would create wealth from
    nothing and break the conservation the whole design rests on."""
    r = Reserves()
    r.seed("u0", 1.0)
    with pytest.raises(ValueError, match="already"):
        r.seed("u0", 1.0)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_d_world.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'd_world'`

- [ ] **Step 3: Write the implementation**

Create `src/d_world.py`:

```python
"""The D-series priced world: where the C-series' cost meter becomes a
subtraction.

THE WHOLE OMISSION THIS CLOSES. The E-series meter charging `sum |M|`, the
`MembraneLedger` scoring hits and misses, `Field.deliver` delivering and
`Unit.anticipate` anticipating -- all of it exists, and all of it is an
observer's scorecard, computed beside the system and affecting nothing.
Nothing was ever subtracted from anything.

WHAT IS DELIBERATELY ABSENT, each refused for a reason recorded in the design
spec's section 9: a chooser, a sense organ for the reserve, a `die()`, a TTL, a
lifespan, a genome, a mutation operator, an attempt-ordering rule, and any price
set by hand.

THE RESERVE IS NOT ON `Unit`. The world holds it, keyed by unit id. That is not
a discipline anyone has to remember -- the architecture enforces it, because a
unit cannot read what it does not have -- and it puts the reserve where
THE_KYTOS section 1.3 says an act's effect resides: in the RESOURCES, outside
the membrane, never in a private field beside the act.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class Source:
    """The world's bounded sustenance, and the price of entering it.

    `pool_per_round` is E1 and is THE NUMERAIRE: it fixes the unit of account
    and nothing else, so it is never varied. Every other quantity in this module
    is a pool-share.

    `entry_price` is E0, MEASURED rather than chosen -- the charge a median unit
    accrues over the rounds it takes the measured baseline learner to induce its
    first law (design spec section 4). It is zero in the calibration arm, where
    it is not yet known, and a zero entry price breeds not at all."""

    pool_per_round: float = 1.0
    entry_price: float = 0.0


class Reserves:
    """Every unit's holdings, held OUTSIDE every membrane.

    Death is `balance <= 0` and nothing else. Exactly zero is dead rather than
    a last breath, so that the boundary is one comparison and not two."""

    def __init__(self) -> None:
        self._amounts: Dict[str, float] = {}

    def seed(self, unit_id: str, amount: float) -> None:
        """Endow a unit at entry. ONCE, EVER -- re-seeding would create wealth
        from nothing, and the conservation property (see `PricedWorld.settle`)
        is what makes the whole measurement readable."""
        if unit_id in self._amounts:
            raise ValueError(
                f"{unit_id} is already endowed at {self._amounts[unit_id]}: "
                f"a unit is endowed once, at entry, and re-seeding would create "
                f"wealth from nothing"
            )
        self._amounts[unit_id] = amount

    def credit(self, unit_id: str, amount: float) -> None:
        self._amounts[unit_id] = self._amounts.get(unit_id, 0.0) + amount

    def charge(self, unit_id: str, amount: float) -> None:
        self._amounts[unit_id] = self._amounts.get(unit_id, 0.0) - amount

    def balance(self, unit_id: str) -> float:
        return self._amounts.get(unit_id, 0.0)

    def alive(self, unit_id: str) -> bool:
        return self._amounts.get(unit_id, 0.0) > 0.0

    def drop(self, unit_id: str) -> None:
        self._amounts.pop(unit_id, None)

    def total(self) -> float:
        """Total wealth. Conservative except on hitless rounds, where the pool
        is charged and nothing is paid back -- which is how a community comes to
        have a lifespan of its own doing."""
        return sum(self._amounts.values())

    def living(self) -> List[str]:
        """Sorted, so anything downstream of it is deterministic."""
        return sorted(u for u, a in self._amounts.items() if a > 0.0)


__all__ = ["Source", "Reserves"]
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_d_world.py -v`
Expected: 11 passed

- [ ] **Step 5: Commit**

```bash
git add src/d_world.py tests/test_d_world.py
git commit -m "D-1: Source and Reserves -- the reserve lives outside the membrane"
```

---

### Task 3: `Seats` — the world's population ceiling

**Files:**
- Modify: `src/d_world.py`
- Test: `tests/test_d_world.py` (append)

**Interfaces:**
- Consumes: `c_field.Aperture`, `c_field.apertures_for`
- Produces:
  - `SeatsFull(Exception)`
  - `Seats(domain_sets: List[Tuple[str, ...]])` with `take(unit_id: str) -> Aperture`, `release(unit_id: str) -> None`, `free() -> int`, `occupied() -> int`
  - `seats_from(spec: FieldSpec, scheme: str = PAIRS) -> Seats`

**Why `take` mints a fresh `Aperture`:** `Field.at` reads `aperture.unit_id` as the observer id, so a newborn taking a vacated slice needs an aperture bearing **its own** id, not the previous occupant's. Handing on the old object would make the newcomer observe the field through the dead unit's noise.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_d_world.py`:

```python
from d_world import Seats, SeatsFull, seats_from


def test_seats_hand_out_the_lowest_free_slice():
    seats = Seats([("a", "b"), ("a", "c"), ("b", "c")])
    assert seats.take("u0").domains == ("a", "b")
    assert seats.take("u1").domains == ("a", "c")
    assert seats.free() == 1
    assert seats.occupied() == 2


def test_a_seat_carries_the_occupant_s_own_id():
    """Field.at reads aperture.unit_id as the OBSERVER, so a newcomer taking a
    vacated slice must observe through its own membrane, not the dead unit's."""
    seats = Seats([("a", "b")])
    first = seats.take("u0")
    assert first.unit_id == "u0"
    seats.release("u0")
    second = seats.take("u9")
    assert second.unit_id == "u9"
    assert second.domains == first.domains


def test_release_frees_the_slice_for_reuse():
    seats = Seats([("a", "b"), ("a", "c")])
    seats.take("u0")
    seats.take("u1")
    assert seats.free() == 0
    seats.release("u0")
    assert seats.free() == 1
    assert seats.take("u2").domains == ("a", "b")


def test_a_full_world_refuses_rather_than_seating_a_twin():
    """The ceiling is the world's. Seating two units on one slice would defeat
    premise 3's requirement that units meet the field differently -- and the
    candidate reading that would permit it for BORN units is unruled (spec
    section 11.1)."""
    seats = Seats([("a", "b")])
    seats.take("u0")
    with pytest.raises(SeatsFull, match="no free seat"):
        seats.take("u1")


def test_releasing_an_unseated_unit_refuses():
    seats = Seats([("a", "b")])
    with pytest.raises(ValueError, match="not seated"):
        seats.release("ghost")


def test_seats_from_the_wide_spec_gives_twenty_eight():
    seats = seats_from(wide_spec())
    assert seats.free() == 28
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_d_world.py -v`
Expected: FAIL — `ImportError: cannot import name 'Seats' from 'd_world'`

- [ ] **Step 3: Write the implementation**

In `src/d_world.py`, add to the imports at the top:

```python
from typing import Dict, List, Optional, Tuple

from c_field import PAIRS, Aperture, FieldSpec, apertures_for
```

(replacing the existing `from typing import Dict, List` line), then append before `__all__`:

```python
class SeatsFull(Exception):
    """No slice of the field is free. RAISED, NEVER DEGRADED: handing a newcomer
    an occupied aperture would seat a twin, and premise 3 requires units to meet
    the field differently. Whether a unit BORN onto an occupied slice is the same
    case as one SEEDED onto it is the design spec's section 11.1 candidate, and
    it is unruled -- so this refuses until it is."""


class Seats:
    """The slices of the field a community may occupy, and who holds them.

    THE CEILING IS THE WORLD'S, not a parameter. `apertures_for` yields C(k, 2)
    distinct two-domain slices over k domains and refuses to seat two units on
    one, so the field's width is the population ceiling and nobody chose a
    maximum."""

    def __init__(self, domain_sets: List[Tuple[str, ...]]):
        self._domain_sets = list(domain_sets)
        self._occupant: List[Optional[str]] = [None] * len(self._domain_sets)

    def take(self, unit_id: str) -> Aperture:
        """Seat `unit_id` on the lowest free slice and hand back ITS OWN
        aperture.

        Lowest-free rather than next-in-sequence so that a run is a
        deterministic function of who died and when, and not of an allocation
        counter that remembers history nobody can read.

        The aperture is MINTED HERE with the occupant's id, because `Field.at`
        reads `aperture.unit_id` as the observer and a newcomer inheriting the
        previous occupant's object would meet the field through a dead unit's
        membrane."""
        for i, held in enumerate(self._occupant):
            if held is None:
                self._occupant[i] = unit_id
                return Aperture(unit_id=unit_id, domains=self._domain_sets[i])
        raise SeatsFull(
            f"no free seat for {unit_id}: all {len(self._domain_sets)} slices of "
            f"this field are occupied, and seating a twin would defeat premise 3"
        )

    def release(self, unit_id: str) -> None:
        for i, held in enumerate(self._occupant):
            if held == unit_id:
                self._occupant[i] = None
                return
        raise ValueError(f"{unit_id} is not seated in this world")

    def free(self) -> int:
        return sum(1 for held in self._occupant if held is None)

    def occupied(self) -> int:
        return sum(1 for held in self._occupant if held is not None)


def seats_from(spec: FieldSpec, scheme: str = PAIRS) -> Seats:
    """Every distinct slice `scheme` allows over `spec` -- the world's ceiling,
    read off the field rather than declared."""
    k = len(spec.domains)
    ceiling = k if scheme != PAIRS else k * (k - 1) // 2
    return Seats([ap.domains
                  for ap in apertures_for(spec, ceiling, scheme=scheme)])
```

Update `__all__`:

```python
__all__ = ["Source", "Reserves", "Seats", "SeatsFull", "seats_from"]
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_d_world.py -v`
Expected: 17 passed

- [ ] **Step 5: Commit**

```bash
git add src/d_world.py tests/test_d_world.py
git commit -m "D-1: Seats -- the population ceiling is the world's, not a parameter"
```

---

### Task 4: `PricedWorld.settle` — the determined price

**Files:**
- Modify: `src/d_world.py`
- Test: `tests/test_d_world.py` (append)

**Interfaces:**
- Consumes: `Source`, `Reserves`, `Seats`; a unit exposing `unit_id: str`, `facts: set`, `laws: set`, `ledger.entries` (each with `.round_idx`, `.result`); a board exposing `since(round_idx) -> List[Mark]` with `.author` and `.round_idx`
- Produces:
  - `RoundReport(round_idx, demand, tau, charges, incomes, born, died, units)` — frozen dataclass
  - `PricedWorld(source, seats, board, subtract: bool = True)` with `admit(unit) -> None` and `settle(units, round_idx, make_unit=None) -> RoundReport`
  - `demand_of(unit, board, round_idx) -> float`, `hits_of(unit, round_idx) -> int`

This task builds charging and paying only. Birth and death arrive in Task 5, so `born` and `died` are empty tuples here.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_d_world.py`:

```python
from dataclasses import dataclass, field as dc_field
from typing import List, Set, Tuple

from c_marks import FACT, Mark, MarkBoard
from d_world import PricedWorld, RoundReport, demand_of, hits_of


@dataclass
class _Entry:
    round_idx: int
    result: str


@dataclass
class _Ledger:
    entries: List[_Entry] = dc_field(default_factory=list)


@dataclass
class _StubUnit:
    """A unit-shaped stand-in. The world reads only these four things, so the
    stub pins exactly the surface `PricedWorld` depends on -- and if the real
    Unit ever stops offering it, Task 6's integration test says so."""
    unit_id: str
    facts: Set[Tuple[str, tuple]] = dc_field(default_factory=set)
    laws: Set[Tuple[str, str]] = dc_field(default_factory=set)
    ledger: _Ledger = dc_field(default_factory=_Ledger)


def _stub(uid, n_facts=0, n_laws=0, hits=0, round_idx=0):
    u = _StubUnit(uid)
    u.facts = {(f"r{i}", (("c", "a"),)) for i in range(n_facts)}
    u.laws = {(f"b{i}", f"h{i}") for i in range(n_laws)}
    u.ledger.entries = [_Entry(round_idx, "hit") for _ in range(hits)]
    return u


def _world(entry_price=0.0, subtract=True, board=None):
    return PricedWorld(Source(1.0, entry_price),
                       seats_from(wide_spec()),
                       board if board is not None else MarkBoard(),
                       subtract=subtract)


def test_demand_counts_held_content_and_acts_minted_this_round():
    """A held fact-round and a minted act each count 1 -- the NULL choice of
    units, asserting no difference between holding and speaking (spec 3.3)."""
    board = MarkBoard()
    board.publish(Mark(author="u0", content=("p", (("c", "a"),)),
                       kind=FACT, round_idx=7))
    board.publish(Mark(author="u0", content=("q", (("c", "a"),)),
                       kind=FACT, round_idx=7))
    board.publish(Mark(author="u1", content=("z", (("c", "a"),)),
                       kind=FACT, round_idx=7))
    board.publish(Mark(author="u0", content=("old", (("c", "a"),)),
                       kind=FACT, round_idx=6))
    u = _stub("u0", n_facts=3, n_laws=2)
    # 3 facts + 2 laws + 2 acts minted AT ROUND 7 (the round-6 mark is not this
    # round's act, and u1's is not this unit's).
    assert demand_of(u, board, 7) == 7.0


def test_hits_are_this_round_s_only():
    u = _stub("u0")
    u.ledger.entries = [_Entry(4, "hit"), _Entry(5, "hit"),
                        _Entry(5, "miss"), _Entry(5, "abstain")]
    assert hits_of(u, 5) == 1
    assert hits_of(u, 4) == 1
    assert hits_of(u, 6) == 0


def test_tau_is_determined_by_demand_not_set():
    """tau = E1 / demand. Nobody sets it; it is what clears the world's bounded
    supply against what the community actually did (spec ruling 7)."""
    world = _world()
    units = [_stub("u0", n_facts=2), _stub("u1", n_facts=2)]
    for u in units:
        world.admit(u)
    report = world.settle(units, 0)
    assert report.demand == 4.0
    assert report.tau == pytest.approx(0.25)


def test_income_is_pro_rata_by_hits():
    world = _world()
    units = [_stub("u0", n_facts=1, hits=3), _stub("u1", n_facts=1, hits=1)]
    for u in units:
        world.admit(u)
    report = world.settle(units, 0)
    assert report.incomes["u0"] == pytest.approx(0.75)
    assert report.incomes["u1"] == pytest.approx(0.25)


def test_a_hitless_round_pays_nothing_and_burns_the_pool():
    """THE WORLD'S TEETH. A round in which nobody predicted anything correctly
    charges E1 and pays nothing back, so the stock falls -- which is how a
    community comes to have a lifespan of its own doing (spec 3.3)."""
    world = _world()
    units = [_stub("u0", n_facts=2), _stub("u1", n_facts=2)]
    for u in units:
        world.admit(u)
        world.reserves.seed(u.unit_id, 10.0)
    before = world.reserves.total()
    report = world.settle(units, 0)
    assert report.incomes == {}
    assert world.reserves.total() == pytest.approx(before - 1.0)


def test_the_world_is_conservative_whenever_anyone_hits():
    """Total charge equals total income to the last unit of account. The one
    place a rounding bug would silently create or destroy wealth (spec 10)."""
    world = _world()
    units = [_stub("u0", n_facts=3, n_laws=1, hits=2),
             _stub("u1", n_facts=7, hits=1),
             _stub("u2", n_facts=1, n_laws=4)]
    for u in units:
        world.admit(u)
        world.reserves.seed(u.unit_id, 10.0)
    before = world.reserves.total()
    report = world.settle(units, 0)
    assert sum(report.charges.values()) == pytest.approx(
        sum(report.incomes.values()))
    assert world.reserves.total() == pytest.approx(before)


def test_charge_is_proportional_to_a_unit_s_own_demand():
    world = _world()
    units = [_stub("u0", n_facts=3), _stub("u1", n_facts=1)]
    for u in units:
        world.admit(u)
    report = world.settle(units, 0)
    assert report.charges["u0"] == pytest.approx(0.75)
    assert report.charges["u1"] == pytest.approx(0.25)


def test_arm_zero_computes_the_charge_and_does_not_subtract_it():
    """A0 -- the control and the calibration source. The meter READ, which is
    exactly today's system, so the wrapper must change nothing (spec 6)."""
    world = _world(subtract=False)
    units = [_stub("u0", n_facts=2, hits=1), _stub("u1", n_facts=2)]
    for u in units:
        world.admit(u)
        world.reserves.seed(u.unit_id, 5.0)
    report = world.settle(units, 0)
    assert report.charges["u0"] == pytest.approx(0.5)   # reported
    assert world.reserves.balance("u0") == pytest.approx(5.0)   # not subtracted
    assert world.reserves.balance("u1") == pytest.approx(5.0)


def test_a_community_with_no_demand_has_no_price():
    """Nothing held and nothing said: tau would divide by zero, so it is None
    and nothing is charged. Named rather than crashed."""
    world = _world()
    units = [_stub("u0"), _stub("u1")]
    for u in units:
        world.admit(u)
    report = world.settle(units, 0)
    assert report.demand == 0.0
    assert report.tau is None
    assert report.charges == {}


def test_settle_is_deterministic():
    def run():
        world = _world()
        units = [_stub("u1", n_facts=2, hits=1), _stub("u0", n_facts=3)]
        for u in units:
            world.admit(u)
            world.reserves.seed(u.unit_id, 4.0)
        return world.settle(units, 0)
    a, b = run(), run()
    assert a.charges == b.charges and a.incomes == b.incomes
    assert a.tau == b.tau
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_d_world.py -v`
Expected: FAIL — `ImportError: cannot import name 'PricedWorld' from 'd_world'`

- [ ] **Step 3: Write the implementation**

In `src/d_world.py`, add `from dataclasses import dataclass` → `from dataclasses import dataclass, field as dc_field` and `from typing import ... Any, Sequence`. Then append before `__all__`:

```python
def demand_of(unit, board, round_idx: int) -> float:
    """What this unit asks of the world this round: everything it holds, plus
    every mark it minted.

    A HELD FACT-ROUND AND A MINTED ACT EACH COUNT 1. That is a choice of units
    and it is the NULL one -- it asserts no difference between holding and
    speaking. It replaces the design's earlier 50/50 split, which asserted the
    same thing more contrivedly, by equalising totals that depend on how many
    facts and acts happen to occur.

    AN ACT IS A MARK MINTED -- by `publish`, `ask`, `answer`, `challenge` or
    `corroborate`, without distinction between them. Charging the kinds at
    different rates would be a designer's claim about which speech is dear, and
    the design refuses to make one.

    ENCOUNTERING A MARK IS FREE. `Unit.read` returns the whole board with no
    filter and no chooser, so a price per mark READ would make each unit's cost
    proportional to community size by construction -- total cost as N squared,
    an exponent written rather than found. Pricing minted acts leaves per-unit
    cost independent of N, so any superlinearity has to be earned."""
    acts = sum(1 for m in board.since(round_idx)
               if m.round_idx == round_idx and m.author == unit.unit_id)
    return float(len(unit.facts) + len(unit.laws) + acts)


def hits_of(unit, round_idx: int) -> int:
    """This round's matches: anticipated AND arrived.

    Read straight off `MembraneLedger.entries`, so the world introduces no new
    statistic and scores matches and nothing else. No credit for communicating,
    corroborating or typifying -- if those pay, they pay only by producing
    better anticipations."""
    return sum(1 for e in unit.ledger.entries
               if e.round_idx == round_idx and e.result == "hit")


@dataclass(frozen=True)
class RoundReport:
    """What the world did this round. Observability -- no unit reads it."""
    round_idx: int
    demand: float
    tau: Optional[float]
    charges: Dict[str, float]
    incomes: Dict[str, float]
    born: Tuple[Tuple[str, str], ...]
    died: Tuple[str, ...]
    units: Tuple[Any, ...]


class PricedWorld:
    """A bounded source, a price that clears it, and reserves held outside every
    membrane.

    NOTHING IS EVER DECLINED. A unit acts exactly as it would with no world at
    all; the tariff subtracts regardless; running out is death. The alternative
    -- refusing acts a unit cannot afford -- was rejected because whoever fixes
    the ATTEMPT ORDER fixes the priority, and which act gets dropped first is a
    substantive claim a designer would be making on the world's behalf.

    THE PRICE IS DETERMINED, NOT SET. `tau = pool / demand` is whatever clears
    the world's bounded supply against what the community actually did. It is
    not a negotiation: nobody bargains and nobody may refuse, which would need
    the chooser this design excludes.

    CONSERVATIVE, EXCEPT ON HITLESS ROUNDS. tau takes back exactly what the pool
    gives, so total wealth is a fixed stock that birth redistributes and never
    creates. A round in which nobody hits charges the pool and pays nothing,
    burning it -- so a community has a lifespan, and it is its own doing."""

    def __init__(self, source: Source, seats: Seats, board,
                 subtract: bool = True):
        self.source = source
        self.seats = seats
        self.board = board
        self.subtract = subtract
        """False is ARM 0: the charge computed and reported but never applied,
        which is exactly today's system. It is the control and the calibration
        source, and it is the only coherent control now that price is
        determined, since `tau = pool / demand` has no zero."""
        self.reserves = Reserves()
        self._next_id = 0

    def admit(self, unit) -> None:
        """Seat a unit and record its id for newborn naming. It is NOT endowed
        here -- endowment is the caller's, because the calibration arm has no
        entry price yet."""
        self.seats.take(unit.unit_id)
        if unit.unit_id.startswith("u") and unit.unit_id[1:].isdigit():
            self._next_id = max(self._next_id, int(unit.unit_id[1:]) + 1)

    def _mint_id(self) -> str:
        uid = f"u{self._next_id}"
        self._next_id += 1
        return uid

    def settle(self, units: Sequence, round_idx: int,
               make_unit=None) -> RoundReport:
        """Charge, pay, then let the population settle.

        THE ORDER IS THE MEASUREMENT: the round's acts are already done and on
        the board before anything is charged, so no charge can reach the acts it
        prices. Births and deaths come last, so a unit is judged on the round it
        actually played."""
        living = [u for u in units]
        demand = sum(demand_of(u, self.board, round_idx) for u in living)
        tau = (self.source.pool_per_round / demand) if demand > 0 else None

        charges: Dict[str, float] = {}
        if tau is not None:
            for u in living:
                charges[u.unit_id] = tau * demand_of(u, self.board, round_idx)

        total_hits = sum(hits_of(u, round_idx) for u in living)
        incomes: Dict[str, float] = {}
        if total_hits > 0:
            for u in living:
                h = hits_of(u, round_idx)
                if h:
                    incomes[u.unit_id] = (
                        self.source.pool_per_round * h / total_hits)

        if self.subtract:
            for uid, amount in sorted(charges.items()):
                self.reserves.charge(uid, amount)
            for uid, amount in sorted(incomes.items()):
                self.reserves.credit(uid, amount)

        born, died, living = self._settle_population(living, make_unit)
        return RoundReport(round_idx=round_idx, demand=demand, tau=tau,
                           charges=charges, incomes=incomes,
                           born=born, died=died, units=tuple(living))

    def _settle_population(self, living, make_unit):
        """Task 5 fills this in. Until then the population is fixed."""
        return (), (), living
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_d_world.py -v`
Expected: 27 passed

- [ ] **Step 5: Commit**

```bash
git add src/d_world.py tests/test_d_world.py
git commit -m "D-1: PricedWorld.settle -- the price is determined, not set"
```

---

### Task 5: Birth and death

**Files:**
- Modify: `src/d_world.py` (replace `_settle_population`)
- Test: `tests/test_d_world.py` (append)

**Interfaces:**
- Consumes: `PricedWorld`, `Reserves`, `Seats`, `SeatsFull`
- Produces: `PricedWorld._settle_population(living, make_unit) -> (born, died, living)`, and `settle`'s `make_unit` parameter with signature `make_unit(unit_id: str, aperture: Aperture) -> unit`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_d_world.py`:

```python
def _maker(created):
    def make_unit(unit_id, aperture):
        u = _stub(unit_id)
        created.append((unit_id, aperture))
        return u
    return make_unit


def test_a_unit_that_runs_out_leaves_and_frees_its_seat():
    """Mortality is a CONSEQUENCE: no die(), no TTL, no lifespan (spec P-D1)."""
    world = _world(entry_price=1.0)
    units = [_stub("u0", n_facts=1, hits=1), _stub("u1", n_facts=99)]
    for u in units:
        world.admit(u)
        world.reserves.seed(u.unit_id, 0.5)
    seated = world.seats.occupied()
    report = world.settle(units, 0)
    assert "u1" in report.died
    assert [u.unit_id for u in report.units] == ["u0"]
    assert world.seats.occupied() == seated - 1


def test_a_rich_unit_splits_and_the_split_is_conservative():
    """Each takes HALF the parent's reserve, so wealth is redistributed and
    never created -- a parent at 3*E0 yields two at 1.5*E0, not two at E0 with
    the remainder burned (spec 3.4)."""
    created = []
    world = _world(entry_price=1.0)
    parent = _stub("u0", n_facts=1, hits=1)
    world.admit(parent)
    world.reserves.seed("u0", 6.0)
    before = world.reserves.total()
    report = world.settle([parent], 0, make_unit=_maker(created))
    assert len(report.born) == 1
    parent_id, child_id = report.born[0]
    assert parent_id == "u0"
    assert world.reserves.total() == pytest.approx(before)
    assert world.reserves.balance(parent_id) == pytest.approx(
        world.reserves.balance(child_id))
    assert world.reserves.balance(child_id) >= world.source.entry_price
    assert len(created) == 1 and created[0][0] == child_id


def test_a_newborn_takes_a_free_seat_and_inherits_nothing_but_the_board():
    """It arrives with no facts, no laws and no standing, and is socialized by
    marks it never made -- Berger and Luckmann's secondary socialization, and
    already built (spec 3.3)."""
    created = []
    world = _world(entry_price=1.0)
    parent = _stub("u0", n_facts=1, n_laws=2, hits=1)
    world.admit(parent)
    world.reserves.seed("u0", 8.0)
    report = world.settle([parent], 0, make_unit=_maker(created))
    child = [u for u in report.units if u.unit_id != "u0"][0]
    assert child.facts == set() and child.laws == set()
    _, aperture = created[0]
    assert aperture.unit_id == child.unit_id
    assert len(aperture.domains) == 2
    assert child.unit_id != parent.unit_id


def test_birth_needs_a_positive_entry_price():
    """The calibration arm does not breed: E0 is not yet known there, so a zero
    threshold would make every unit split every round (spec 3.4)."""
    created = []
    world = _world(entry_price=0.0)
    parent = _stub("u0", n_facts=1, hits=1)
    world.admit(parent)
    world.reserves.seed("u0", 100.0)
    report = world.settle([parent], 0, make_unit=_maker(created))
    assert report.born == ()
    assert created == []


def test_birth_needs_a_maker():
    """Without one the world cannot construct a unit, and it says so rather than
    silently declining to reproduce."""
    world = _world(entry_price=1.0)
    parent = _stub("u0", n_facts=1, hits=1)
    world.admit(parent)
    world.reserves.seed("u0", 9.0)
    report = world.settle([parent], 0)          # no make_unit
    assert report.born == ()


def test_a_full_world_simply_does_not_breed():
    """SeatsFull is a refusal at the seat, but a world with no room is a world
    where births do not happen -- not an error the run should die on."""
    created = []
    world = PricedWorld(Source(1.0, 1.0), Seats([("a", "b")]), MarkBoard())
    parent = _stub("u0", n_facts=1, hits=1)
    world.admit(parent)
    world.reserves.seed("u0", 9.0)
    report = world.settle([parent], 0, make_unit=_maker(created))
    assert report.born == ()
    assert created == []


def test_death_is_settled_before_birth():
    """A seat freed this round is available this round: the world settles who
    left before it asks who may arrive, so a community at the ceiling can still
    turn over."""
    created = []
    world = PricedWorld(Source(1.0, 1.0), Seats([("a", "b"), ("a", "c")]),
                        MarkBoard())
    rich = _stub("u0", n_facts=1, hits=1)
    poor = _stub("u1", n_facts=50)
    for u, amount in ((rich, 9.0), (poor, 0.01)):
        world.admit(u)
        world.reserves.seed(u.unit_id, amount)
    report = world.settle([rich, poor], 0, make_unit=_maker(created))
    assert report.died == ("u1",)
    assert len(report.born) == 1


def test_a_newborn_id_is_never_reused():
    created = []
    world = _world(entry_price=1.0)
    parent = _stub("u0", n_facts=1, hits=1)
    world.admit(parent)
    world.reserves.seed("u0", 40.0)
    seen = set()
    units = [parent]
    for r in range(4):
        report = world.settle(units, r, make_unit=_maker(created))
        for _, child_id in report.born:
            assert child_id not in seen
            seen.add(child_id)
        units = list(report.units)
    assert len(seen) == len(created)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_d_world.py -v`
Expected: FAIL — several, since `_settle_population` returns the population unchanged

- [ ] **Step 3: Write the implementation**

Replace `_settle_population` in `src/d_world.py` with:

```python
    def _settle_population(self, living, make_unit):
        """Who left, then who arrived.

        DEATH FIRST, so a seat freed this round is available this round and a
        community at the ceiling can still turn over.

        BIRTH SPLITS THE RESERVE IN HALF rather than issuing each unit the entry
        price, which keeps it CONSERVATIVE: a parent at three times the entry
        price yields two units at one and a half times it, not two at the entry
        price with the remainder burned. Wealth is redistributed and never
        created or destroyed, which is what makes the conservation reading
        meaningful.

        THE THRESHOLD IS NOT A CHOSEN MULTIPLE. The entry price IS what it costs
        to enter this world, so `2 * entry_price` reads: you may reproduce when
        you can pay a newcomer's entry and remain viable yourself. A world with
        no entry price -- the calibration arm, where it is not yet measured --
        does not breed at all, since a zero threshold would split every unit
        every round.

        A FULL WORLD SIMPLY DOES NOT BREED. `SeatsFull` is the right refusal
        when someone asks for a seat, but a world with no room is a fact about
        the world and not an error the run should die on."""
        died = []
        for u in list(living):
            if not self.reserves.alive(u.unit_id):
                self.seats.release(u.unit_id)
                self.reserves.drop(u.unit_id)
                died.append(u.unit_id)
        survivors = [u for u in living if u.unit_id not in set(died)]

        born = []
        if make_unit is not None and self.source.entry_price > 0.0:
            threshold = 2.0 * self.source.entry_price
            for u in list(survivors):
                if self.reserves.balance(u.unit_id) < threshold:
                    continue
                if self.seats.free() == 0:
                    break
                child_id = self._mint_id()
                aperture = self.seats.take(child_id)
                half = self.reserves.balance(u.unit_id) / 2.0
                self.reserves.charge(u.unit_id, half)
                self.reserves.seed(child_id, half)
                survivors.append(make_unit(child_id, aperture))
                born.append((u.unit_id, child_id))

        return tuple(born), tuple(died), survivors
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_d_world.py -v`
Expected: 35 passed

- [ ] **Step 5: Commit**

```bash
git add src/d_world.py tests/test_d_world.py
git commit -m "D-1: birth and death -- population is found, not set"
```

---

### Task 6: The driver — four arms and the `E0` calibration

**Files:**
- Create: `tools/run_d1.py`
- Test: `tests/test_d_world.py` (append)

**Interfaces:**
- Consumes: everything above, plus `c_unit.Unit`, `c_marks.MarkBoard`, `c_field.Field`, `c_field.units_for_witnesses`
- Produces:
  - `tools/run_d1.py`: `ARMS = ("A0", "A1", "A2a", "A2b")`, `play(arm, seed, rounds, source) -> ArmResult`, `calibrate(seed_list, rounds) -> float`, `main()`
  - `ArmResult(arm, seed, rounds, survivors, born, died, final_units, charges_by_unit, first_law_round, world)`

**The four arms** (spec §6): `A0` charge computed, not subtracted · `A1` subtracted · `A2a` subtracted with the channel off entirely · `A2b` subtracted with acts still minted and charged but peers receiving nothing.

**A2b's mechanism:** units publish/ask/challenge to a `mint_board` (so their acts are counted and charged) but read and answer from a permanently empty `void_board` (so nothing reaches anyone). That holds cost fixed while removing the sign, which is the honest ablation; `A2a` removes both and is reported beside it to expose the mute-and-cheaper confound.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_d_world.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from run_d1 import ARMS, ArmResult, calibrate, play   # noqa: E402


def test_all_four_arms_run_and_report():
    for arm in ARMS:
        result = play(arm, seed=1, rounds=8, source=Source(1.0, 0.05))
        assert isinstance(result, ArmResult)
        assert result.arm == arm
        assert result.survivors >= 0


def test_arm_zero_never_subtracts_so_nobody_dies():
    """A0 is the control: the meter READ. Reserves must not move at all."""
    result = play("A0", seed=1, rounds=12, source=Source(1.0, 0.0))
    assert result.died == 0
    assert result.born == 0
    balances = {uid: result.world.reserves.balance(uid)
                for uid in result.world.reserves.living()}
    assert balances, "A0 must still seat and endow its units"
    assert len(set(round(b, 9) for b in balances.values())) == 1, \
        "every A0 balance is its untouched endowment"


def test_a_founder_is_endowed_at_the_entry_price_and_must_double_to_breed():
    """The endowment is E0 exactly, so a founder starts ON the entry price and
    has to double before it may breed. An endowment floored at 1.0 would put
    every founder above the threshold whenever the measured E0 fell below 1.0,
    and round 0 would be a birth wave that measured the endowment rather than
    the world."""
    source = Source(1.0, 0.05)
    result = play("A1", seed=1, rounds=1, source=source)
    seeded = [result.world.reserves.balance(uid)
              for uid in result.world.reserves.living()]
    assert seeded, "the arm must seat and endow its founders"
    # Nobody can have started at or above 2*E0, so no birth is an artefact of
    # the endowment. (Balances have moved by one round of settling, so this
    # checks the threshold rather than the seed value itself.)
    assert result.born == 0


def test_the_real_unit_offers_the_surface_the_world_reads():
    """The stub in the unit tests pins a surface; this pins that the REAL Unit
    still offers it, so the two cannot drift apart."""
    result = play("A1", seed=1, rounds=6, source=Source(1.0, 0.05))
    for u in result.final_units:
        assert isinstance(u.unit_id, str)
        assert isinstance(u.facts, set) and isinstance(u.laws, set)
        assert hasattr(u.ledger, "entries")


def test_a2b_mints_and_is_charged_while_nothing_reaches_anyone():
    """The honest ablation: cost held, sign removed."""
    a2b = play("A2b", seed=1, rounds=10, source=Source(1.0, 0.05))
    a2a = play("A2a", seed=1, rounds=10, source=Source(1.0, 0.05))
    assert sum(a2b.charges_by_unit.values()) > 0
    # A2a mints nothing at all; A2b mints and pays for it.
    assert a2b.acts_minted > 0
    assert a2a.acts_minted == 0


def test_calibrate_returns_a_positive_entry_price():
    """E0 is MEASURED -- the charge a median unit accrues through t*, the median
    round at which a unit induces its first planted law (spec 4)."""
    e0 = calibrate([1, 2], rounds=25)
    assert e0 > 0.0


def test_two_runs_of_one_arm_agree():
    """The determinism canary."""
    a = play("A1", seed=7, rounds=10, source=Source(1.0, 0.05))
    b = play("A1", seed=7, rounds=10, source=Source(1.0, 0.05))
    assert (a.survivors, a.born, a.died) == (b.survivors, b.born, b.died)
    assert a.charges_by_unit == b.charges_by_unit
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_d_world.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'run_d1'`

- [ ] **Step 3: Write the implementation**

Create `tools/run_d1.py`:

```python
"""D-1: run the priced world across its four arms.

Design spec: docs/superpowers/specs/2026-08-02-d-series-building-the-stake-design.md

Usage:
    uv run python tools/run_d1.py                  # calibrate, then all arms
    uv run python tools/run_d1.py --rounds 60
"""

from __future__ import annotations

import argparse
import statistics
import sys
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from c_field import (PAIRS, Aperture, Field, apertures_for,  # noqa: E402
                     units_for_witnesses, wide_spec)
from c_marks import MarkBoard                                # noqa: E402
from c_unit import Unit                                      # noqa: E402
from d_world import PricedWorld, Source, seats_from          # noqa: E402

ARMS = ("A0", "A1", "A2a", "A2b")
SEEDS = (1, 2, 3, 4, 5, 7, 42, 99)
ROUNDS = 60
MIN_WITNESSES = 3


@dataclass
class ArmResult:
    arm: str
    seed: int
    rounds: int
    survivors: int
    born: int
    died: int
    acts_minted: int
    final_units: List[Unit] = dc_field(default_factory=list)
    charges_by_unit: Dict[str, float] = dc_field(default_factory=dict)
    first_law_round: Dict[str, int] = dc_field(default_factory=dict)
    world: Optional[PricedWorld] = None


def _planted(spec) -> set:
    return {d.law for d in spec.domains}


def play(arm: str, seed: int, rounds: int, source: Source) -> ArmResult:
    """One community, one seed, one arm.

    THE ROUND ORDER matters and is the C-series' own: adopt, attend, then the
    channel acts, then the world settles. Settling LAST means the round's acts
    are already on the board before anything is charged, so no charge can reach
    the acts it prices.

    THERE IS NO STAGGER. The C-series' bounded attention was a schedule imposed
    from outside; under a priced world every living unit attends every round and
    pays for it -- fix the price, let the quantum fall out."""
    if arm not in ARMS:
        raise ValueError(f"arm must be one of {ARMS}, got {arm!r}")
    spec = wide_spec(seed=seed)
    field = Field(spec)
    n0 = units_for_witnesses(spec, MIN_WITNESSES, PAIRS)

    mint_board = MarkBoard()
    void_board = MarkBoard()
    # A2a: no channel at all. A2b: mint (and pay) but nothing reaches anyone.
    speak_board = None if arm == "A2a" else mint_board
    hear_board = {"A0": mint_board, "A1": mint_board,
                  "A2a": None, "A2b": void_board}[arm]

    world = PricedWorld(source, seats_from(spec), mint_board,
                        subtract=(arm != "A0"))

    def make_unit(unit_id: str, aperture: Aperture) -> Unit:
        """A newborn inherits NOTHING but the board -- no facts, no laws, no
        standing -- and is socialized by marks it never made."""
        return Unit(unit_id, aperture)

    units: List[Unit] = []
    for i in range(n0):
        uid = f"u{i}"
        aperture = world.seats.take(uid)
        unit = Unit(uid, aperture)
        world._next_id = max(world._next_id, i + 1)
        # A FOUNDER IS ENDOWED AT THE WORLD'S ENTRY PRICE, exactly. It must
        # then DOUBLE before it may breed (threshold 2*E0), which is the rule
        # reading "pay a newcomer's entry and remain viable yourself".
        #
        # `max(..., 1.0)` would break that: with a measured E0 below 1.0 every
        # founder would start above the breeding threshold and split in round
        # 0, an artefact of the endowment rather than a finding. The fallback
        # applies ONLY to the calibration arm, where the entry price is not yet
        # known -- a zero endowment there would read as dead at round 0, since
        # `alive` is `balance > 0`.
        world.reserves.seed(uid, source.entry_price
                            if source.entry_price > 0.0 else 1.0)
        units.append(unit)

    planted = _planted(spec)
    first_law: Dict[str, int] = {}
    charges: Dict[str, float] = {}
    born = died = 0
    asked: Dict[str, list] = {}

    for r in range(rounds):
        if hear_board is not None:                       # (a) adopt replies
            for u in units:
                for q in list(asked.get(u.unit_id, [])):
                    reply = hear_board.answer_to(q)
                    if reply is not None and reply.author != u.unit_id:
                        u.adopt(reply, hear_board, r)
                        asked[u.unit_id].remove(q)
        for u in units:                                   # (b) attend
            u.step(field, r, induce=True)
            if u.unit_id not in first_law and (u.laws & planted):
                first_law[u.unit_id] = r
        if speak_board is not None:                       # (c) speak
            for u in units:
                u.publish(speak_board, r)
                mark = u.ask(speak_board, r)
                if mark is not None:
                    asked.setdefault(u.unit_id, []).append(mark)
                u.challenge(speak_board, r)
        if hear_board is not None:                        # (d) hear
            for u in units:
                u.answer(hear_board, r)

        # (e) the world. A0 NEVER BREEDS: it does not subtract, so a reserve
        # never falls and every unit would split every round until the seats ran
        # out -- an artefact of the control, not a finding. The control's job is
        # to leave the community exactly as it would have been.
        report = world.settle(units, r,
                              make_unit=None if arm == "A0" else make_unit)
        for uid, amount in report.charges.items():
            charges[uid] = charges.get(uid, 0.0) + amount
        born += len(report.born)
        died += len(report.died)
        units = list(report.units)
        if not units:
            break

    return ArmResult(
        arm=arm, seed=seed, rounds=rounds, survivors=len(units),
        born=born, died=died,
        acts_minted=len(mint_board.all_marks()),
        final_units=units, charges_by_unit=charges,
        first_law_round=first_law, world=world)


def calibrate(seed_list=SEEDS, rounds: int = ROUNDS) -> float:
    """E0 -- the world's entry price, MEASURED and not chosen.

    Arm 0 at the reference configuration supplies `t*`, the MEDIAN over units
    and seeds of the round at which a unit induces its first planted law; E0 is
    the charge a median unit has accrued by then.

    MEDIAN AT BOTH STEPS, so one lucky unit does not set the world's entry
    price. WHY t* AND NOT A HORIZON: an austere endowment kills every unit
    before induction can happen and the run is empty, while a horizon chosen by
    hand is a free parameter wearing a law's clothes. Read off t*, the claim is
    sharp -- a unit that learns slower than the recorded baseline dies before it
    learns."""
    rounds_to_law: List[int] = []
    per_round_charge: List[float] = []
    for seed in seed_list:
        result = play("A0", seed=seed, rounds=rounds, source=Source(1.0, 0.0))
        rounds_to_law.extend(result.first_law_round.values())
        for uid, total in result.charges_by_unit.items():
            per_round_charge.append(total / result.rounds)
    if not rounds_to_law:
        raise RuntimeError(
            f"no unit induced a planted law in {rounds} rounds over seeds "
            f"{list(seed_list)}: t* is undefined and E0 cannot be measured"
        )
    t_star = statistics.median(rounds_to_law)
    return statistics.median(per_round_charge) * (t_star + 1)


def main() -> None:
    parser = argparse.ArgumentParser(description="D-1: the priced world")
    parser.add_argument("--rounds", type=int, default=ROUNDS)
    parser.add_argument("--seeds", type=int, nargs="*", default=list(SEEDS))
    args = parser.parse_args()

    e0 = calibrate(args.seeds, args.rounds)
    print(f"calibration: E0 = {e0:.6f}  (measured, not chosen)")
    source = Source(pool_per_round=1.0, entry_price=e0)

    print(f"\n{'arm':>5} {'seed':>5} {'survivors':>10} {'born':>6} "
          f"{'died':>6} {'acts':>7}")
    for arm in ARMS:
        for seed in args.seeds:
            r = play(arm, seed=seed, rounds=args.rounds, source=source)
            print(f"{arm:>5} {seed:>5} {r.survivors:>10} {r.born:>6} "
                  f"{r.died:>6} {r.acts_minted:>7}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_d_world.py -v`
Expected: 41 passed

Then check the driver runs end to end (short, for speed):

Run: `uv run python tools/run_d1.py --rounds 12 --seeds 1 2`
Expected: an `E0 = …` line, then 8 rows

- [ ] **Step 5: Commit**

```bash
git add tools/run_d1.py tests/test_d_world.py
git commit -m "D-1: the driver -- four arms and the measured entry price"
```

---

### Task 7: The guards

**Files:**
- Test: `tests/test_d_world.py` (append)

**Interfaces:**
- Consumes: everything above

These are the spec §10 checks. They test the *design*, not a behaviour, and each one fails loudly if a future change quietly reintroduces what the design refused.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_d_world.py`:

```python
import ast


SRC = Path(__file__).resolve().parents[1] / "src"


def test_no_die_no_ttl_no_lifespan_in_the_d_world():
    """P-D1 is worthless if something installs mortality. Death must be
    `reserve <= 0` and nothing else (spec ruling 1).

    THE GUARD READS THE CODE, NOT THE PROSE. A regex over the file text would
    fire on the module docstring, which names `die()`, TTL and lifespan
    precisely to say they are absent -- and a guard that punishes a design for
    documenting its own refusals teaches the next author to stop documenting
    them. Walking the AST for IDENTIFIERS asks the question actually worth
    asking: does any name in this module install mortality?"""
    tree = ast.parse((SRC / "d_world.py").read_text())
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
    banned = ("die", "ttl", "lifespan", "max_age", "age", "expires")
    for name in sorted(names):
        assert name.lower() not in banned, \
            f"{name!r} installs the mortality P-D1 predicts must emerge"


def test_the_unit_never_gains_a_reserve():
    """The architecture enforces the ruling: a unit cannot read what it does not
    have (spec 3.1, THE_KYTOS 1.3)."""
    spec = wide_spec()
    unit = Unit("u0", apertures_for(spec, 1, scheme=PAIRS)[0])
    for banned in ("reserve", "reserves", "balance", "wealth", "budget"):
        assert not hasattr(unit, banned), \
            f"Unit.{banned} would give a future chooser something to read"


def test_c_unit_is_not_modified_by_this_series():
    """The whole design rests on the units being unchanged."""
    import subprocess
    changed = subprocess.run(
        ["git", "log", "--oneline", "-n", "50", "--", "src/c_unit.py"],
        capture_output=True, text=True,
        cwd=str(SRC.parent)).stdout
    assert "D-1:" not in changed, "no D-1 commit may touch src/c_unit.py"


def test_the_wrapper_is_inert_when_it_does_not_subtract():
    """ARM 0 changes nothing. This is a claim about the WRAPPER, not a claim to
    reproduce published C-series figures, which were measured on a different
    field, a different aperture scheme and an imposed stagger (spec 10)."""
    spec = wide_spec(seed=3)
    aps = apertures_for(spec, 3, scheme=PAIRS)

    bare = [Unit(a.unit_id, a) for a in aps]
    for r in range(15):
        for u in bare:
            u.step(Field(spec), r, induce=True)

    wrapped = [Unit(a.unit_id, a) for a in aps]
    world = PricedWorld(Source(1.0, 0.0), seats_from(spec), MarkBoard(),
                        subtract=False)
    for u in wrapped:
        world.admit(u)
        world.reserves.seed(u.unit_id, 1.0)
    units = wrapped
    for r in range(15):
        for u in units:
            u.step(Field(spec), r, induce=True)
        units = list(world.settle(units, r).units)

    assert [u.unit_id for u in units] == [u.unit_id for u in bare]
    for a, b in zip(sorted(units, key=lambda u: u.unit_id),
                    sorted(bare, key=lambda u: u.unit_id)):
        assert a.facts == b.facts
        assert a.laws == b.laws
        assert a.ledger.hits == b.ledger.hits
        assert a.ledger.misses == b.ledger.misses


def test_the_world_holds_no_chooser():
    """Nothing in d_world may decide WHICH act a unit performs, skip one, or
    order them. The world charges and pays; it never selects."""
    text = (SRC / "d_world.py").read_text()
    for banned in ("def choose", "def select", "def prioriti", "def decline",
                   "def refuse_act"):
        assert banned not in text, f"{banned} is the chooser the design refuses"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_d_world.py -v -k "guard or die or reserve or inert or chooser or c_unit"`
Expected: FAIL — the imports `Unit`, `re`, `SRC` are not yet in the file's namespace if the earlier appends omitted them; add `from c_unit import Unit` to the test file's imports and re-run.

- [ ] **Step 3: Make them pass**

Add to the imports at the top of `tests/test_d_world.py`:

```python
from c_unit import Unit
```

No `src/` change should be needed — if any guard fails, the *source* is wrong, not the guard. Fix the source.

- [ ] **Step 4: Run the whole suite**

Run: `uv run pytest tests/test_d_world.py -v`
Expected: 46 passed

Then confirm nothing else moved:

Run: `uv run pytest tests/test_c_field.py tests/test_c_unit.py tests/test_c_marks.py tests/test_c_membrane.py -q`
Expected: all pass, same counts as before this plan began

- [ ] **Step 5: Commit**

```bash
git add tests/test_d_world.py
git commit -m "D-1: the guards -- no die(), no reserve on Unit, no chooser, wrapper inert"
```

---

### Task 8: The pre-registered reading

**Files:**
- Create: `runs/RUN_D1_LOG.md`
- Modify: `CURRENT_PLAN.md` (prepend a dated arc entry)

**Interfaces:**
- Consumes: `tools/run_d1.py`

The priors are `P-D1` … `P-D7` in spec §7. They were committed **before** any of this was built; this task reads the run against them and records what happened, **including the ones that failed.**

- [ ] **Step 1: Run the full measurement**

Run: `uv run python tools/run_d1.py --rounds 60 2>&1 | tee /tmp/d1.txt`
Expected: an `E0 = …` line then 32 rows (4 arms × 8 seeds)

- [ ] **Step 2: Write the log**

Create `runs/RUN_D1_LOG.md` with, at minimum:

- The measured `E0`, the derived `N₀`, and the seat ceiling.
- A table of the 32 rows.
- **One section per prior**, `P-D1` through `P-D7`, each stating **held / refuted / not reached** with the figure it was read on. `P-D5` and `P-D6` are findings-in-advance and are recorded as such rather than as run outcomes.
- **The escalation check (spec §8 item 6):** if any arm's equilibrium population reached **80% of the 28-seat ceiling**, the result is *not* reported as an equilibrium — the field must grow and every figure be re-measured. State the highest population observed against that threshold either way.

- [ ] **Step 3: Record the arc in CURRENT_PLAN.md**

Prepend a `**Last Updated**: 2026-08-XX` block above the existing one, following the file's established shape: what was built, what the priors said, what actually happened, and what is next. **Report failed priors as prominently as held ones** — a run log that only records confirmations is not a record.

- [ ] **Step 4: Commit**

```bash
git add runs/RUN_D1_LOG.md CURRENT_PLAN.md
git commit -m "D-1: the run read against its pre-registered priors"
```

---

## Self-review notes

**Spec coverage.** §3.1 reserve-outside-membrane → Task 2 + Task 7. §3.2 module → Tasks 2–5. §3.3 round, demand, τ, income, conservation, hitless burn, newborn-takes-free-seat → Task 4 + Task 5. §3.4 the five quantities → Task 1 (`N₀`, seats), Task 2 (`E1`, `E0`), Task 5 (birth threshold). §4 calibration → Task 6 `calibrate`. §6 four arms and no stagger → Task 6 `play`. §7 priors → Task 8. §10 testing → Task 7. §5.1 D-3 and §5.2 D-0 are deferred by design and correctly have no task.

**Known gaps, stated rather than hidden.**

1. **`P-D2` (law lineages) and `P-D4` (typification) have no dedicated instrument in this plan.** Both are read off `MarkBoard` and `Unit.peers` against the reserves, and both need an analysis pass that Task 8 performs by hand. If the hand pass proves awkward, a `d_lineage.py` reader is the honest follow-up rather than a scope creep into Task 6.
2. **`world._next_id` is poked directly in `play`** when seating the founders. That is a private attribute crossing a boundary. It is tolerable because `play` is the only constructor of founding populations, but if a second driver appears, `PricedWorld` should gain a public `found(units)` instead.
3. **`test_c_unit_is_not_modified_by_this_series` reads git log**, so it is a weak guard — it catches a commit message convention, not the edit. The real guarantee is review.
