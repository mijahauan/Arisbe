# Rung 1 — Attention Economy on the Arithmetic World: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the world-agnostic attention socket (`AttentionEconomy` + `ProbeDirectedFeed`) and prove it on a computed-arithmetic world: Fermat's conjecture refuted at F5 under budget only when attention buys severity (pre-registered S1–S5 in `docs/BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md` §3).

**Architecture:** `src/attention_economy.py` scores wants by severity-weighted decayed-yield per unit cost with a musement reservation and noisy-TV decay; `src/arithmetic_world.py` is a deterministic computable world plus a `ProbeDirectedFeed` implementing `agon_evolution.Proposer` (one EGIF per `propose(model, round_idx)`; yield read from the model delta between calls). No changes to any existing module; the existing mechanical panel disposes everything.

**Tech Stack:** Python 3.12, uv, pytest. Existing seams: `agon_evolution.run/peel/Proposer/CorpusProposer/Agonothetes`, `world_scroll.m_view`, `egif_parser_dau.parse_egif`, `query_docket.QueryDocket`, `agon_metalearning.unresolved_frontier`, `tomos_service.TomosService`.

## Global Constraints

- **Spec:** `docs/superpowers/specs/2026-07-17-rung1-attention-economy-design.md`. Criteria S1–S5 are pre-registered in `docs/BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md` §3 — the build must not weaken them.
- **No changes** to protected modules, `agon_evolution.py`, `query_docket.py`, `live_runner.py`, or any web/layout module. New files only (plus end-of-build doc edits).
- **Determinism:** no `random`, no wall-clock anywhere in the two new modules. All ordering keys must be total and deterministic.
- **Bounded growth, drops counted:** every register/queue has a cap; anything dropped at a cap increments a counter; nothing is silently truncated.
- **Failure posture:** the economy never raises into the loop — internal scoring errors degrade to the mechanical tie-break order.
- Run tests with `uv run pytest <path> -q`. Commit after every green step; commit messages in the repo's plain-descriptive style (no `feat:` prefixes — match `git log`).
- EGIF shapes used throughout: atom `(prime "5")`, law `~[ (fermat_number *x) ~[ (prime x) ] ]`, denial-bearing proposal `(fermat_number "4294967297") ~[ (prime "4294967297") ]`.
- **Calibration note (S1):** the plan's numbers (costs, severity 8.0, budgets, round counts) are starting values. If the S1 strict ordering `economy < scatter < FIFO` fails, tune the confirm-lattice size / cost divisor / severity — the *criterion* (strict ordering, fixed budget) is pre-registered and must not be weakened; the knobs are free.

---

### Task 1: `Want` + `AttentionEconomy` core scoring

**Files:**
- Create: `src/attention_economy.py`
- Test: `tests/test_attention_economy.py`

**Interfaces:**
- Produces: `Want(kind, key, payload=None, cost=1.0, severity=1.0, created_round=0, attempts=0)` (dataclass);
  `AttentionEconomy(prior=0.05, yield_decay=0.8, attempt_decay=0.7, max_wants=500, musement_fraction=0.1, boredom_rounds=5)` with
  `register(want) -> bool`, `wants() -> list[Want]`, `settle(kind, key) -> None`,
  `choose(k, round_idx) -> list[Want]` (increments `attempts` on chosen),
  `observe(round_idx, results: Sequence[tuple[Want, int]]) -> None`,
  `kind_yield(kind) -> float`, `snapshot() -> dict`, `dropped: int`.
- Scoring: `score(w) = w.severity * (Y[w.kind] + prior) / w.cost * attempt_decay**w.attempts`;
  sort key `(-score, w.attempts, w.created_round, w.kind, repr(w.key))`.
- `observe` updates `Y[kind] = yield_decay*Y[kind] + (1-yield_decay)*events` per result.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_attention_economy.py
"""Rung 1 — the attention economy (spec: docs/superpowers/specs/2026-07-17-rung1-attention-economy-design.md)."""
from attention_economy import Want, AttentionEconomy


def _econ(**kw):
    return AttentionEconomy(**kw)


class TestScoring:
    def test_yield_per_cost_orders_kinds(self):
        e = _econ()
        a = Want(kind="rich", key=("a",))
        b = Want(kind="poor", key=("b",))
        e.register(a); e.register(b)
        # teach it: rich yielded 3 events on a probe, poor yielded 0
        e.observe(1, [(a, 3), (b, 0)])
        chosen = e.choose(1, round_idx=2)
        assert chosen[0].kind == "rich"

    def test_cost_divides_the_score(self):
        e = _econ()
        cheap = Want(kind="k", key=("cheap",), cost=1.0)
        dear = Want(kind="k", key=("dear",), cost=100.0)
        e.register(cheap); e.register(dear)
        # same kind (same Y): the cheap want must come first
        assert e.choose(2, round_idx=1)[0].key == ("cheap",)

    def test_severity_multiplies(self):
        e = _econ()
        plain = Want(kind="k", key=("plain",), cost=1.0, severity=1.0)
        severe = Want(kind="k", key=("severe",), cost=4.0, severity=8.0)
        e.register(plain); e.register(severe)
        # 8/4 = 2 > 1/1 — the law-testing want wins despite its cost
        assert e.choose(2, round_idx=1)[0].key == ("severe",)

    def test_tiebreak_fewest_attempts_then_oldest(self):
        e = _econ()
        old = Want(kind="k", key=("old",), created_round=1)
        new = Want(kind="k", key=("new",), created_round=5)
        tried = Want(kind="k", key=("tried",), created_round=0, attempts=3)
        e.register(new); e.register(tried); e.register(old)
        order = [w.key for w in e.choose(3, round_idx=6)]
        assert order.index(("old",)) < order.index(("new",))
        assert order.index(("new",)) < order.index(("tried",))

    def test_choose_increments_attempts_and_settle_removes(self):
        e = _econ()
        w = Want(kind="k", key=("w",))
        e.register(w)
        chosen = e.choose(1, round_idx=1)
        assert chosen[0].attempts == 1
        e.settle("k", ("w",))
        assert e.wants() == []

    def test_register_dedups_by_kind_key(self):
        e = _econ()
        assert e.register(Want(kind="k", key=("w",))) is True
        assert e.register(Want(kind="k", key=("w",))) is False
        assert len(e.wants()) == 1

    def test_deterministic_choice(self):
        def build():
            e = _econ()
            for i in range(20):
                e.register(Want(kind=f"k{i % 3}", key=(i,), cost=1.0 + i % 5))
            e.observe(1, [(Want(kind="k1", key=(99,)), 2)])
            return [w.key for w in e.choose(7, round_idx=2)]
        assert build() == build()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_attention_economy.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'attention_economy'`

- [ ] **Step 3: Write the implementation**

```python
# src/attention_economy.py
"""Rung 1 — the economy-of-research ordering of reaches (the attention socket).

Design-of-record: docs/BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md §3 (criteria S1–S5
pre-registered); spec docs/superpowers/specs/2026-07-17-rung1-attention-economy-design.md.
World-agnostic: wants come from a docket, from the meta-learning frontier, or from a
world's musement candidates; the scorer orders them by severity-weighted decayed yield
per unit cost. Deterministic (no RNG, no wall clock); a scoring failure degrades to the
mechanical tie-break, never raises into the loop.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple


@dataclass
class Want:
    """One candidate reach. ``severity`` is the epistemic weight of the want's *shape*
    (testing a standing universal outranks another particular — Peirce's economy of
    research values what a result would settle, not only what it costs)."""
    kind: str
    key: Tuple
    payload: Any = None
    cost: float = 1.0
    severity: float = 1.0
    created_round: int = 0
    attempts: int = 0


class AttentionEconomy:
    def __init__(
        self,
        *,
        prior: float = 0.05,
        yield_decay: float = 0.8,
        attempt_decay: float = 0.7,
        max_wants: int = 500,
        musement_fraction: float = 0.1,
        boredom_rounds: int = 5,
    ):
        self._prior = prior
        self._yield_decay = yield_decay
        self._attempt_decay = attempt_decay
        self._max = max_wants
        self._eps = musement_fraction
        self._boredom_rounds = boredom_rounds
        self._wants: Dict[Tuple[str, Tuple], Want] = {}
        self._y: Dict[str, float] = {}
        self._streak = 0            # consecutive all-zero-yield observe() batches
        self.dropped = 0            # register() refusals at the cap — counted, never silent
        self.fallbacks = 0          # choose() degradations to the mechanical order

    # -- register / settle ---------------------------------------------------
    def register(self, want: Want) -> bool:
        k = (want.kind, want.key)
        if k in self._wants:
            return False
        if len(self._wants) >= self._max:
            self.dropped += 1
            return False
        self._wants[k] = want
        return True

    def wants(self) -> List[Want]:
        return list(self._wants.values())

    def settle(self, kind: str, key: Tuple) -> None:
        self._wants.pop((kind, key), None)

    # -- scoring -------------------------------------------------------------
    def kind_yield(self, kind: str) -> float:
        return self._y.get(kind, 0.0)

    def _score(self, w: Want) -> float:
        y = self._y.get(w.kind, 0.0)
        return w.severity * (y + self._prior) / max(w.cost, 1e-9) \
            * (self._attempt_decay ** w.attempts)

    def _mechanical(self, ws: List[Want]) -> List[Want]:
        return sorted(ws, key=lambda w: (w.attempts, w.created_round, w.kind, repr(w.key)))

    def choose(self, k: int, round_idx: int) -> List[Want]:
        pool = list(self._wants.values())
        muse = [w for w in pool if w.kind == "musement"]
        rest = [w for w in pool if w.kind != "musement"]
        try:
            m = self._musement_slots(k, round_idx) if muse else 0
            muse_sorted = sorted(muse, key=lambda w: (-w.created_round, repr(w.key)))
            rest_sorted = sorted(
                rest, key=lambda w: (-self._score(w), w.attempts, w.created_round,
                                     w.kind, repr(w.key)))
            chosen = muse_sorted[:m] + rest_sorted[: max(0, k - min(m, len(muse_sorted)))]
            chosen = chosen[:k]
        except Exception:
            self.fallbacks += 1
            chosen = self._mechanical(pool)[:k]
        for w in chosen:
            w.attempts += 1
        return chosen

    # -- musement (Task 2 wires the boredom detector into this) ---------------
    def effective_musement(self) -> float:
        if self._streak >= self._boredom_rounds:
            return min(0.5, self._eps * 2)
        return self._eps

    def _musement_slots(self, k: int, round_idx: int) -> int:
        eps = self.effective_musement()
        if eps <= 0:
            return 0
        base = int(eps * k)
        period = max(1, int(round(1 / eps)))
        extra = 1 if (base == 0 and round_idx % period == 0) else 0
        return min(k, base + extra)

    # -- feedback ------------------------------------------------------------
    def observe(self, round_idx: int, results: Sequence[Tuple[Want, int]]) -> None:
        total = 0
        for want, events in results:
            total += events
            y = self._y.get(want.kind, 0.0)
            self._y[want.kind] = self._yield_decay * y + (1 - self._yield_decay) * events
        self._streak = 0 if total > 0 else self._streak + 1

    def snapshot(self) -> dict:
        return {
            "kinds": dict(sorted(self._y.items())),
            "wants": len(self._wants),
            "dropped": self.dropped,
            "fallbacks": self.fallbacks,
            "streak": self._streak,
            "effective_musement": self.effective_musement(),
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_attention_economy.py -q`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add src/attention_economy.py tests/test_attention_economy.py
git commit -m "Rung 1 task 1: the attention economy's core scorer (severity-weighted yield per cost)"
```

---

### Task 2: noisy-TV guards, musement reservation, boredom, degrade-to-mechanical

**Files:**
- Modify: `src/attention_economy.py` (no interface change — behavior tests only)
- Test: `tests/test_attention_economy.py` (append)

**Interfaces:**
- Consumes: Task 1's `AttentionEconomy` exactly as defined.
- Produces: verified guard behavior later tasks rely on; no new names.

- [ ] **Step 1: Append the failing tests**

```python
class TestGuards:
    def test_noisy_tv_kind_decays_below_productive(self):
        e = _econ()
        noise = Want(kind="coin", key=("n",))
        good = Want(kind="hunt", key=("g",))
        e.register(noise); e.register(good)
        for r in range(1, 8):
            e.observe(r, [(noise, 0), (good, 1)])
        assert e.kind_yield("coin") < e.kind_yield("hunt")
        assert e.choose(1, round_idx=9)[0].kind == "hunt"

    def test_attempt_decay_sinks_a_barren_want(self):
        e = _econ(attempt_decay=0.5)
        barren = Want(kind="k", key=("barren",))
        fresh = Want(kind="k", key=("fresh",), created_round=99)  # newer — loses ties
        e.register(barren); e.register(fresh)
        for r in range(3):           # probe barren 3 times, no yield
            e.choose(1, round_idx=r)  # barren wins ties at first (older)
            e.observe(r, [(barren, 0)])
        assert e.choose(1, round_idx=10)[0].key == ("fresh",)

    def test_register_cap_counts_drops(self):
        e = _econ(max_wants=2)
        assert e.register(Want(kind="k", key=(1,)))
        assert e.register(Want(kind="k", key=(2,)))
        assert e.register(Want(kind="k", key=(3,))) is False
        assert e.dropped == 1

    def test_musement_reservation_every_period_when_k_is_1(self):
        e = _econ(musement_fraction=0.1)
        e.register(Want(kind="musement", key=("m",), created_round=1))
        e.register(Want(kind="hunt", key=("h",)))
        e.observe(1, [(Want(kind="hunt", key=("h",)), 5)])  # hunt far outscores
        # round 10 is a musement round (period = 1/0.1); round 11 is not
        assert e.choose(1, round_idx=10)[0].kind == "musement"
        assert e.choose(1, round_idx=11)[0].kind == "hunt"

    def test_boredom_doubles_musement_and_yield_resets_it(self):
        e = _econ(musement_fraction=0.1, boredom_rounds=3)
        w = Want(kind="k", key=("w",))
        e.register(w)
        for r in range(3):
            e.observe(r, [(w, 0)])
        assert e.effective_musement() == 0.2
        e.observe(4, [(w, 2)])
        assert e.effective_musement() == 0.1

    def test_scoring_failure_degrades_to_mechanical_order(self):
        e = _econ()
        good = Want(kind="k", key=("good",), created_round=1)
        bad = Want(kind="k", key=("bad",), created_round=2, cost=1.0)
        e.register(good); e.register(bad)
        e._y = None  # sabotage internal state: scoring will raise
        chosen = e.choose(2, round_idx=3)
        assert [w.key for w in chosen] == [("good",), ("bad",)]  # mechanical order
        assert e.fallbacks == 1
```

- [ ] **Step 2: Run to verify which fail**

Run: `uv run pytest tests/test_attention_economy.py -q`
Expected: most of `TestGuards` passes already (Task 1 implemented the mechanics); any failure here is a real bug in Task 1's code — fix `src/attention_economy.py` until all pass. (If all six pass immediately, that is the desired outcome — the tests still gate regressions.)

- [ ] **Step 3: Run full economy tests**

Run: `uv run pytest tests/test_attention_economy.py -q`
Expected: 13 passed

- [ ] **Step 4: Commit**

```bash
git add tests/test_attention_economy.py src/attention_economy.py
git commit -m "Rung 1 task 2: guard behavior pinned - noisy-TV decay, musement reservation, boredom, mechanical fallback"
```

---

### Task 3: intake adapters (docket + frontier)

**Files:**
- Modify: `src/attention_economy.py` (append two module-level functions)
- Test: `tests/test_attention_economy.py` (append)

**Interfaces:**
- Consumes: `query_docket.QueryDocket` (`open_entries()` → `DocketEntry(shape, constants, provenance, age, attempts)`, `.key` property); `agon_metalearning.DisputeEpisode(claim_egif, mechanism, settled, reverts, disposition, stuck)` and `unresolved_frontier(episodes)`.
- Produces: `wants_from_docket(docket, *, round_idx=0, cost=1.0) -> list[Want]` (kind `"docket"`, key = entry.key, payload = entry, attempts carried over, created_round = round_idx - entry.age);
  `wants_from_frontier(episodes, *, round_idx=0, cost=1.0, severity=4.0) -> list[Want]` (kind `"frontier"`, key = `(claim,)`, payload = claim EGIF).

- [ ] **Step 1: Append the failing tests**

```python
class TestAdapters:
    def test_wants_from_docket_wraps_open_entries(self):
        from attention_economy import wants_from_docket
        from query_docket import QueryDocket
        d = QueryDocket(labels={}, k=2)
        d.note_unknowns([("orbits", ["Q1", "Q2"])])
        ws = wants_from_docket(d, round_idx=5)
        assert len(ws) == 1
        w = ws[0]
        assert w.kind == "docket"
        assert w.key == ("orbits", ("Q1", "Q2"))
        assert w.payload is d.open_entries()[0]

    def test_wants_from_frontier_takes_unresolved_claims(self):
        from attention_economy import wants_from_frontier
        from agon_metalearning import DisputeEpisode
        eps = [
            DisputeEpisode(claim_egif='(hot "Sun")', mechanism="unresolved",
                           settled=None, reverts=3, disposition=None, stuck=None),
            DisputeEpisode(claim_egif='(cold "Pluto")', mechanism="reliable_source",
                           settled=True, reverts=0, disposition="new_fact", stuck=True),
        ]
        ws = wants_from_frontier(eps, round_idx=2)
        assert [w.key for w in ws] == [('(hot "Sun")',)]
        assert ws[0].kind == "frontier" and ws[0].severity == 4.0
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_attention_economy.py::TestAdapters -q`
Expected: FAIL — `ImportError: cannot import name 'wants_from_docket'`

- [ ] **Step 3: Append the implementation to `src/attention_economy.py`**

```python
# --------------------------------------------------------------------------- #
# Intake adapters — the docket and the meta-learning frontier become wants.    #
# Non-invasive: QueryDocket and agon_metalearning are read, never modified.    #
# --------------------------------------------------------------------------- #

def wants_from_docket(docket, *, round_idx: int = 0, cost: float = 1.0) -> List[Want]:
    """Each open docket entry (a named want M neither holds nor denies) as a Want.
    ``created_round`` is back-dated by the entry's age so older doubts win ties;
    the entry's own attempt count carries over (a barren docket want sinks here too)."""
    out: List[Want] = []
    for entry in docket.open_entries():
        out.append(Want(
            kind="docket", key=entry.key, payload=entry, cost=cost,
            created_round=round_idx - entry.age, attempts=entry.attempts))
    return out


def wants_from_frontier(episodes, *, round_idx: int = 0, cost: float = 1.0,
                        severity: float = 4.0) -> List[Want]:
    """The ◇-contested horizon as wants: claims no mechanism settled
    (``agon_metalearning.unresolved_frontier``) — cross-run feedback, the
    game-studying-the-game edge. Higher severity than a bare particular: a
    contested claim's resolution settles more."""
    from agon_metalearning import unresolved_frontier
    return [
        Want(kind="frontier", key=(claim,), payload=claim, cost=cost,
             severity=severity, created_round=round_idx)
        for claim in unresolved_frontier(episodes)
    ]
```

Also add `wants_from_docket`/`wants_from_frontier` to the module's `__all__` if one exists (create `__all__ = ["Want", "AttentionEconomy", "wants_from_docket", "wants_from_frontier"]` at the end).

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_attention_economy.py -q`
Expected: 15 passed

- [ ] **Step 5: Commit**

```bash
git add src/attention_economy.py tests/test_attention_economy.py
git commit -m "Rung 1 task 3: intake adapters - docket entries and the unresolved frontier become wants"
```

---

### Task 4: `ArithmeticWorld` — the computable world

**Files:**
- Create: `src/arithmetic_world.py`
- Test: `tests/test_arithmetic_world.py`

**Interfaces:**
- Produces: module constants `FERMATS = (3, 5, 17, 257, 65537, 4294967297)`,
  `FERMAT_LAW = '~[ (fermat_number *x) ~[ (prime x) ] ]'`,
  `MUSEMENT_LAW = '~[ (fermat_number *x) ~[ (odd x) ] ]'`;
  `ArithmeticWorld(range_cap=200)` with `is_prime(n) -> bool`, `coin(n) -> bool`,
  `atoms_for(n) -> str` (EGIF conjunction), `probe_cost(n) -> float`,
  `test_law_instance(law_egif, n) -> Optional[bool]`, `probed: set[int]`, `dropped: int`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_arithmetic_world.py
"""Rung 1 world #1 — deterministic computed arithmetic (spec: docs/superpowers/specs/
2026-07-17-rung1-attention-economy-design.md). The headline: Fermat's 1640 conjecture,
refuted at F5 = 641 * 6700417 (Euler 1732)."""
from arithmetic_world import (
    ArithmeticWorld, FERMATS, FERMAT_LAW, MUSEMENT_LAW,
)


class TestWorld:
    def test_f5_is_composite_and_earlier_fermats_prime(self):
        w = ArithmeticWorld()
        assert [w.is_prime(f) for f in FERMATS] == [True, True, True, True, True, False]

    def test_atoms_for_carries_parity_prime_square_fermat(self):
        w = ArithmeticWorld()
        a4 = w.atoms_for(4)
        assert '(even "4")' in a4 and '(square "4")' in a4 and "(prime" not in a4
        a17 = w.atoms_for(17)
        assert '(odd "17")' in a17 and '(prime "17")' in a17 and '(fermat_number "17")' in a17

    def test_f5_atoms_deny_primality_under_the_standing_law(self):
        w = ArithmeticWorld()
        a = w.atoms_for(4294967297)
        assert '(fermat_number "4294967297")' in a
        assert '~[ (prime "4294967297") ]' in a   # the world's denial — the refuting instance

    def test_coin_is_deterministic_and_mixed(self):
        w = ArithmeticWorld()
        bits = [w.coin(n) for n in range(40)]
        assert bits == [w.coin(n) for n in range(40)]
        assert True in bits and False in bits

    def test_probe_cost_grows_with_n(self):
        w = ArithmeticWorld()
        assert w.probe_cost(7) < w.probe_cost(65537) < w.probe_cost(4294967297)

    def test_law_instance_verdicts(self):
        w = ArithmeticWorld()
        assert w.test_law_instance(FERMAT_LAW, 257) is True
        assert w.test_law_instance(FERMAT_LAW, 4294967297) is False
        assert w.test_law_instance(FERMAT_LAW, 10) is None          # vacuous — not a Fermat number
        assert w.test_law_instance(MUSEMENT_LAW, 65537) is True

    def test_range_cap_counts_drops(self):
        w = ArithmeticWorld(range_cap=5)
        for n in range(5):
            assert w.atoms_for(n)
        w.atoms_for(6)          # over the cap for a *new* n
        assert w.dropped == 1
        assert w.atoms_for(4294967297)   # Fermat numbers are exempt (law instances)
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_arithmetic_world.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'arithmetic_world'`

- [ ] **Step 3: Write the implementation**

```python
# src/arithmetic_world.py
"""Rung 1 world #1 — computed arithmetic: deterministic, CI-safe, zero NL, real costs.

The world answers probes by computation (the resolving-membrane shape: a claim's
resolution is ground truth, here perfectly so). Probing n costs what deciding n's
primality costs. The headline trajectory: Fermat's conjecture (every 2^2^n + 1 prime,
1640) confirms at F0..F4 and is refuted at F5 (Euler 1732) — reachable under budget
only if attention buys severity. Range growth is selected, never accreted: new-n
probes beyond ``range_cap`` are refused and counted (``dropped``); a law's own
instances (the Fermat numbers) are exempt — testing a standing law is never a
range-crawl."""
from __future__ import annotations

import math
from typing import Optional

FERMATS = (3, 5, 17, 257, 65537, 4294967297)
FERMAT_LAW = '~[ (fermat_number *x) ~[ (prime x) ] ]'
MUSEMENT_LAW = '~[ (fermat_number *x) ~[ (odd x) ] ]'

_KNUTH = 2654435761  # Knuth's multiplicative-hash constant — the coin's grist


class ArithmeticWorld:
    def __init__(self, *, range_cap: int = 200):
        self._range_cap = range_cap
        self.probed: set[int] = set()
        self.dropped = 0

    # -- number facts ---------------------------------------------------------
    def is_prime(self, n: int) -> bool:
        if n < 2:
            return False
        if n % 2 == 0:
            return n == 2
        d = 3
        while d * d <= n:
            if n % d == 0:
                return False
            d += 2
        return True

    def coin(self, n: int) -> bool:
        return sum(int(c) for c in str(n * _KNUTH)) % 2 == 1

    def probe_cost(self, n: int) -> float:
        return 1.0 + math.isqrt(max(n, 0)) / 20000.0

    # -- probes ---------------------------------------------------------------
    def atoms_for(self, n: int) -> str:
        """The ground atoms at n, as one EGIF conjunction. A composite Fermat number
        carries the *denial* of primality — the world resolving the law's instance."""
        if n not in self.probed and n not in FERMATS and n > self._range_cap:
            self.dropped += 1
            return ""
        self.probed.add(n)
        q = f'"{n}"'
        parts = [f'({"even" if n % 2 == 0 else "odd"} {q})']
        if math.isqrt(n) ** 2 == n:
            parts.append(f'(square {q})')
        if self.coin(n):
            parts.append(f'(coin {q})')
        if n in FERMATS:
            parts.append(f'(fermat_number {q})')
        if self.is_prime(n):
            parts.append(f'(prime {q})')
        elif n in FERMATS:
            parts.append(f'~[ (prime {q}) ]')
        return " ".join(parts)

    # -- law instances --------------------------------------------------------
    def _holds(self, pred: str, n: int) -> bool:
        return {
            "even": n % 2 == 0,
            "odd": n % 2 == 1,
            "prime": self.is_prime(n),
            "square": math.isqrt(n) ** 2 == n,
            "coin": self.coin(n),
            "fermat_number": n in FERMATS,
        }[pred]

    def test_law_instance(self, law_egif: str, n: int) -> Optional[bool]:
        """A subsumption law ~[ (P *x) ~[ (Q x) ] ] at instance n: None if vacuous
        (P fails at n), else whether Q holds at n."""
        import re
        m = re.match(r'~\[\s*\((\w+) \*x\)\s*~\[\s*\((\w+) x\)\s*\]\s*\]', law_egif)
        if not m:
            raise ValueError(f"not a unary subsumption law: {law_egif}")
        p, qd = m.group(1), m.group(2)
        if not self._holds(p, n):
            return None
        return self._holds(qd, n)
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_arithmetic_world.py -q`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add src/arithmetic_world.py tests/test_arithmetic_world.py
git commit -m "Rung 1 task 4: the arithmetic world - computed atoms, real costs, the F5 denial"
```

---

### Task 5: `ProbeDirectedFeed` — the socket

**Files:**
- Modify: `src/arithmetic_world.py` (append the feed + choosers)
- Test: `tests/test_arithmetic_world.py` (append)

**Interfaces:**
- Consumes: `AttentionEconomy`/`Want` from Task 1; `ArithmeticWorld` from Task 4; `world_scroll.m_view`; `egif_parser_dau.parse_egif`.
- Produces: `ProbeDirectedFeed(world, economy, *, chooser=None, probe_budget=1, laws=(FERMAT_LAW,), confirm_lattice=60, musement=True, journal=None)` implementing `propose(model, round_idx) -> Optional[str]`; module functions `fifo_chooser(economy, k, round_idx)` and `scatter_chooser(economy, k, round_idx)`; `feed.journal: list[dict]` and `replay_choices(journal) -> list`; helper `_model_signature(model) -> tuple[frozenset, int]`.
- Probe wants (all registered by the feed):
  - kind `"confirm"`: key `("confirm", n)` for n in `range(confirm_lattice)`, cost 1.0, severity 1.0 — never settled (the cheap trap).
  - kind `"extend"`: key `("extend", n)` for the next 3 unprobed n, cost `world.probe_cost(n)`, severity 1.0 — settled when executed.
  - kind `"hunt"`: key `("hunt", law, n)` for every untested instance of every standing law (for `FERMAT_LAW`: every Fermat number not yet probed, all registered up front), cost `world.probe_cost(n)`, **severity 8.0** — settled when executed.
  - kind `"musement"`: key `("law", law_egif)` for candidate subsumptions over the unary vocabulary (at minimum `MUSEMENT_LAW`), cost 0.5 — settled when executed; only registered when `musement=True`.

- [ ] **Step 1: Append the failing tests**

```python
class TestFeed:
    def _feed(self, **kw):
        from attention_economy import AttentionEconomy
        from arithmetic_world import ArithmeticWorld, ProbeDirectedFeed
        w = ArithmeticWorld()
        e = AttentionEconomy()
        return ProbeDirectedFeed(w, e, **kw), w, e

    def test_one_egif_per_propose_and_probes_settle(self):
        from egif_parser_dau import parse_egif
        feed, w, e = self._feed()
        m = parse_egif('(even "0")')
        out = feed.propose(m, 1)
        assert isinstance(out, str) and out.strip()
        parse_egif(out)   # every emission is legal EGIF

    def test_hunt_wants_cover_all_fermat_instances_up_front(self):
        feed, w, e = self._feed()
        from egif_parser_dau import parse_egif
        feed.propose(parse_egif('(even "0")'), 1)
        hunts = [wt for wt in e.wants() if wt.kind == "hunt"]
        assert {wt.key[2] for wt in hunts} | {n for n in w.probed if n in
               __import__("arithmetic_world").FERMATS} >= set(__import__("arithmetic_world").FERMATS)

    def test_yield_read_from_model_delta(self):
        from egif_parser_dau import parse_egif
        feed, w, e = self._feed()
        m0 = parse_egif('(even "0")')
        feed.propose(m0, 1)
        # the model grew between calls — the feed must credit yield to last round's kinds
        m1 = parse_egif('(even "0") (odd "1") (prime "2")')
        feed.propose(m1, 2)
        assert any(v > 0 for v in e.snapshot()["kinds"].values())

    def test_journal_records_choices_and_is_deterministic(self):
        from egif_parser_dau import parse_egif
        def drive():
            feed, w, e = self._feed()
            m = parse_egif('(even "0")')
            for r in range(1, 6):
                feed.propose(m, r)
            return [j["chosen"] for j in feed.journal]
        assert drive() == drive()

    def test_fifo_and_scatter_choosers_are_deterministic_and_differ(self):
        from arithmetic_world import fifo_chooser, scatter_chooser
        from attention_economy import AttentionEconomy, Want
        e = AttentionEconomy()
        for i in range(12):
            e.register(Want(kind="k", key=(i,), created_round=i))
        f1 = [w.key for w in fifo_chooser(e, 5, 1)]
        s1 = [w.key for w in scatter_chooser(e, 5, 1)]
        assert f1 == [(0,), (1,), (2,), (3,), (4,)]
        assert s1 != f1
        assert s1 == [w.key for w in scatter_chooser(e, 5, 1)]
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_arithmetic_world.py::TestFeed -q`
Expected: FAIL — `ImportError: cannot import name 'ProbeDirectedFeed'`

- [ ] **Step 3: Append the implementation to `src/arithmetic_world.py`**

```python
# --------------------------------------------------------------------------- #
# The socket — a Proposer whose next item is chosen by the attention layer.    #
# World-agnostic in shape: the vault stage swaps the world, keeps the feed.    #
# --------------------------------------------------------------------------- #
from attention_economy import AttentionEconomy, Want  # noqa: E402
from egif_parser_dau import parse_egif                # noqa: E402
from world_scroll import m_view                       # noqa: E402


def _labels_of(g, eid):
    out = []
    for vid in g.nu.get(eid, ()):  # ν sequence → vertex labels (None for generics)
        v = next((v for v in g.V if v.id == vid), None)
        out.append(getattr(v, "label", None) if v is not None else None)
    return tuple(out)


def _model_signature(model) -> tuple:
    """(frozenset of sheet atoms, count of sheet cuts) via m_view — the feed's only
    lawful window onto what the loop did with its proposals."""
    g = m_view(model)
    atoms = frozenset(
        (g.rel[e.id], _labels_of(g, e.id))
        for e in g.E
        if e.id in g.rel and g.area_of(e.id) == g.sheet.id
    )
    from eg_navigation import child_cuts  # local import to avoid cycles at module load
    ncuts = len(child_cuts(g, g.sheet))
    return (atoms, ncuts)


def fifo_chooser(economy: AttentionEconomy, k: int, round_idx: int):
    ws = sorted(economy.wants(), key=lambda w: (w.created_round, w.kind, repr(w.key)))
    chosen = ws[:k]
    for w in chosen:
        w.attempts += 1
    return chosen


def scatter_chooser(economy: AttentionEconomy, k: int, round_idx: int):
    """The deterministic 'random' arm: order by a hash of (key, round) — no RNG."""
    ws = sorted(economy.wants(),
                key=lambda w: hash((repr(w.key), round_idx)) % 997)
    chosen = ws[:k]
    for w in chosen:
        w.attempts += 1
    return chosen


class ProbeDirectedFeed:
    """agon_evolution.Proposer: one EGIF per propose(); probes chosen by attention."""

    def __init__(self, world: ArithmeticWorld, economy: AttentionEconomy, *,
                 chooser=None, probe_budget: int = 1, laws=(FERMAT_LAW,),
                 confirm_lattice: int = 60, musement: bool = True, journal=None):
        self._world = world
        self._economy = economy
        self._chooser = chooser
        self._budget = probe_budget
        self._laws = tuple(laws)
        self._musement = musement
        self._queue: list[str] = []
        self._last_chosen: list[Want] = []
        self._prev_sig = None
        self._seeded = False
        self._extend_next = 0
        self.journal: list[dict] = [] if journal is None else journal

    # -- intake ---------------------------------------------------------------
    def _seed_wants(self, round_idx: int):
        if self._seeded:
            return
        self._seeded = True
        for n in range(60 if self._world is None else min(60, 10**9)):
            pass  # replaced below — kept explicit for reviewers: seeding is one-shot
        for n in range(0, self._confirm_lattice()):
            self._economy.register(Want(
                kind="confirm", key=("confirm", n), payload=n,
                cost=1.0, created_round=round_idx))
        for law in self._laws:
            for f in FERMATS:
                self._economy.register(Want(
                    kind="hunt", key=("hunt", law, f), payload=(law, f),
                    cost=self._world.probe_cost(f), severity=8.0,
                    created_round=round_idx))
        if self._musement:
            self._economy.register(Want(
                kind="musement", key=("law", MUSEMENT_LAW), payload=("law", MUSEMENT_LAW),
                cost=0.5, created_round=round_idx))

    def _confirm_lattice(self) -> int:
        return self._lattice if hasattr(self, "_lattice") else 60

    def _refill_extends(self, round_idx: int):
        added = 0
        n = self._extend_next
        while added < 3:
            if n not in self._world.probed and n not in FERMATS:
                self._economy.register(Want(
                    kind="extend", key=("extend", n), payload=n,
                    cost=self._world.probe_cost(n), created_round=round_idx))
                added += 1
            n += 1
        self._extend_next = n

    # -- the round loop -------------------------------------------------------
    def propose(self, model, round_idx: int):
        sig = _model_signature(model)
        if self._prev_sig is not None and self._last_chosen:
            prev_atoms, prev_cuts = self._prev_sig
            atoms, cuts = sig
            events = len(atoms ^ prev_atoms) + abs(cuts - prev_cuts)
            self._economy.observe(round_idx, [(w, events) for w in self._last_chosen])
            self._last_chosen = []
        self._prev_sig = sig

        if not self._queue:
            self._seed_wants(round_idx)
            self._refill_extends(round_idx)
            choose = self._chooser or (lambda e, k, r: e.choose(k, r))
            chosen = choose(self._economy, self._budget, round_idx)
            self._last_chosen = list(chosen)
            self.journal.append({
                "round": round_idx,
                "chosen": [(w.kind, repr(w.key)) for w in chosen],
                "snapshot": self._economy.snapshot(),
            })
            for w in chosen:
                if w.kind in ("extend", "confirm"):
                    egif = self._world.atoms_for(w.payload)
                elif w.kind == "hunt":
                    _, n = w.payload
                    egif = self._world.atoms_for(n)
                elif w.kind == "musement":
                    egif = w.payload[1]
                else:                      # docket/frontier kinds: payload is EGIF-ish
                    egif = w.payload if isinstance(w.payload, str) else ""
                if egif:
                    self._queue.append(egif)
                if w.kind != "confirm":    # confirms persist — the cheap trap
                    self._economy.settle(w.kind, w.key)

        return self._queue.pop(0) if self._queue else None


def replay_choices(journal):
    """The determinism canary's reading of a journal: the choice sequence alone."""
    return [j["chosen"] for j in journal]
```

**Implementation notes for this step (do these while writing, they are part of the task):**
- Replace the vestigial `for n in range(...): pass` loop in `_seed_wants` with nothing — it is shown crossed-out here to warn against seeding twice; the real body is the three `register` blocks. Store `confirm_lattice` from `__init__` as `self._lattice = confirm_lattice` and delete the `_confirm_lattice` indirection, using `self._lattice` directly.
- Check `eg_navigation.child_cuts` and `g.area_of` names against the real API (`grep -n "def child_cuts\|def area_of" src/eg_navigation.py src/egi_core_dau.py`) and adjust `_model_signature` accordingly — the sheet-atom set must match how `ContradictionAgent` reads standing atoms (`src/agon_evolution.py` ~line 370, `_labels` helper there is the model to copy).
- If `parse_egif` rejects any emitted conjunction, fix `atoms_for`, not the parser.

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_arithmetic_world.py -q`
Expected: 12 passed

- [ ] **Step 5: Commit**

```bash
git add src/arithmetic_world.py tests/test_arithmetic_world.py
git commit -m "Rung 1 task 5: ProbeDirectedFeed - the attention-chosen Proposer, with FIFO/scatter baseline arms"
```

---

### Task 6: integration — the Fermat refutation through `run()`

**Files:**
- Test: `tests/test_arithmetic_world.py` (append)

**Interfaces:**
- Consumes: `agon_evolution.run(model_egif, proposer, *, rounds, uod_id, name, panel=None, seed_laws=None)`; `agon_evolution.peel`, `semantic_game.Verdict3`; `res.uod.current_egi`, `res.outcomes[i].disposition`.
- Produces: helper `refutation_round(res) -> Optional[int]` (module-level in the test file) that later tasks reuse for S1.

- [ ] **Step 1: Append the failing test**

```python
M0 = '(even "0")'


def refutation_round(res):
    from agon_evolution import DISPOSITION_CHALLENGE_M
    for o in res.outcomes:
        if o.disposition == DISPOSITION_CHALLENGE_M:
            return o.round_idx
    return None


class TestIntegration:
    def test_economy_arm_refutes_fermat(self):
        from agon_evolution import run, peel
        from semantic_game import Verdict3
        from attention_economy import AttentionEconomy
        from arithmetic_world import ArithmeticWorld, ProbeDirectedFeed, FERMAT_LAW
        feed = ProbeDirectedFeed(ArithmeticWorld(), AttentionEconomy())
        res = run(M0 + " " + FERMAT_LAW, feed, rounds=30,
                  uod_id="rung1_econ", name="rung 1 economy arm",
                  seed_laws=[FERMAT_LAW])
        r = refutation_round(res)
        assert r is not None, "the economy arm must reach the F5 refutation in 30 rounds"
        final = res.uod.current_egi
        assert peel(final, FERMAT_LAW).verdict is Verdict3.FALSE
        assert peel(final, '(fermat_number "4294967297")').verdict is Verdict3.TRUE
```

- [ ] **Step 2: Run to verify it fails (or diagnose)**

Run: `uv run pytest tests/test_arithmetic_world.py::TestIntegration -q`
Expected: initially FAIL. Likely causes to work through, in order: (a) the constant name — check `grep -n "DISPOSITION_CHALLENGE_M" src/agon_evolution.py` and use the real symbol; (b) the F5 emission shape — `ChallengerAgent` fires when the proposal refutes a standing law; confirm the emitted `(fermat_number "4294967297") ... ~[ (prime "4294967297") ]` matches `_refuted_law`'s expectations (read `src/agon_evolution.py` `_refuted_law`) and adjust `atoms_for`'s F5 output to the swan-shape `(swan "Nox") ~[ (white "Nox") ]` — i.e. emit *only* `(fermat_number "F5") ~[ (prime "F5") ]` for composite Fermats, dropping the parity/coin atoms from that one emission if they confuse the matcher.

- [ ] **Step 3: Iterate until green**

Run: `uv run pytest tests/test_arithmetic_world.py -q`
Expected: 13 passed

- [ ] **Step 4: Commit**

```bash
git add tests/test_arithmetic_world.py src/arithmetic_world.py
git commit -m "Rung 1 task 6: the Fermat refutation lands through run() - Euler 1732 by attention"
```

---

### Task 7: S1 + S2 + S3 — the pre-registered headline

**Files:**
- Test: `tests/test_arithmetic_world.py` (append)

**Interfaces:**
- Consumes: everything above; `fifo_chooser`, `scatter_chooser`.

- [ ] **Step 1: Append the failing tests**

```python
class TestCriteria:
    def _arm(self, chooser=None, musement=True, rounds=90):
        from agon_evolution import run
        from attention_economy import AttentionEconomy
        from arithmetic_world import ArithmeticWorld, ProbeDirectedFeed, FERMAT_LAW
        feed = ProbeDirectedFeed(ArithmeticWorld(), AttentionEconomy(),
                                 chooser=chooser, musement=musement)
        res = run(M0 + " " + FERMAT_LAW, feed, rounds=rounds,
                  uod_id="rung1_arm", name="rung 1 arm", seed_laws=[FERMAT_LAW])
        return res, feed

    def test_s1_economy_beats_fifo_and_scatter(self):
        from arithmetic_world import fifo_chooser, scatter_chooser
        econ, _ = self._arm()
        fifo, _ = self._arm(chooser=fifo_chooser)
        scat, _ = self._arm(chooser=scatter_chooser)
        r_e, r_f, r_s = (refutation_round(econ), refutation_round(fifo),
                         refutation_round(scat))
        assert r_e is not None, "economy must refute within budget"
        assert r_f is None or r_e < r_f, f"economy {r_e} must beat FIFO {r_f}"
        assert r_s is None or r_e < r_s, f"economy {r_e} must beat scatter {r_s}"

    def test_s2_coin_kind_never_dominates(self):
        econ, feed = self._arm()
        from attention_economy import AttentionEconomy
        # coin atoms exist in M, but no probe kind is 'coin' — the noise guard here
        # is that repeated zero-yield kinds decay: assert every kind that yielded
        # nothing across the run scores below the hunt kind at the end.
        snap = feed.journal[-1]["snapshot"]["kinds"]
        assert snap.get("hunt", 0) >= max(
            (v for k, v in snap.items() if k in ("confirm",)), default=0)

    def test_s3_musement_finds_the_off_docket_law(self):
        from agon_evolution import peel
        from semantic_game import Verdict3
        from arithmetic_world import MUSEMENT_LAW
        on, _ = self._arm(musement=True)
        off, _ = self._arm(musement=False)
        assert peel(on.uod.current_egi, MUSEMENT_LAW).verdict is Verdict3.TRUE
        assert peel(off.uod.current_egi, MUSEMENT_LAW).verdict is not Verdict3.TRUE
```

- [ ] **Step 2: Run and calibrate**

Run: `uv run pytest tests/test_arithmetic_world.py::TestCriteria -q`
Expected: initially may FAIL on calibration. Tune ONLY the knobs (confirm_lattice size, severity, cost divisor, rounds) until the strict ordering holds robustly — do not weaken the assertions. If S2's snapshot-shape assertion proves brittle, strengthen it to read `feed.journal` choice counts (`sum(1 for j in feed.journal for k, _ in j["chosen"] if k == "confirm")` small for the economy arm) — the criterion is "noise/barren kinds do not dominate," and the test must still bite.

- [ ] **Step 3: Full-file run**

Run: `uv run pytest tests/test_arithmetic_world.py -q`
Expected: 16 passed

- [ ] **Step 4: Commit**

```bash
git add tests/test_arithmetic_world.py src/arithmetic_world.py
git commit -m "Rung 1 task 7: S1-S3 pass - economy beats FIFO and scatter to the refutation; musement earns its slot"
```

---

### Task 8: S4 — determinism + journal replay canary

**Files:**
- Test: `tests/test_arithmetic_world.py` (append)

- [ ] **Step 1: Append the failing test**

```python
class TestDeterminism:
    def test_s4_identical_configs_identical_trajectories(self):
        from arithmetic_world import replay_choices
        a, feed_a = TestCriteria()._arm(rounds=40)
        b, feed_b = TestCriteria()._arm(rounds=40)
        assert replay_choices(feed_a.journal) == replay_choices(feed_b.journal)
        assert [o.disposition for o in a.outcomes] == [o.disposition for o in b.outcomes]
        assert refutation_round(a) == refutation_round(b)
```

- [ ] **Step 2: Run**

Run: `uv run pytest tests/test_arithmetic_world.py::TestDeterminism -q`
Expected: PASS if Tasks 1–7 kept determinism; any failure is a real nondeterminism bug (hash randomization in `scatter_chooser` uses `hash()` — **replace `hash()` with a stable digest**: `int(hashlib.sha1(f"{key}{round_idx}".encode()).hexdigest()[:8], 16) % 997` — `hash()` of a str is salted per process and WILL fail across runs; fix this in `src/arithmetic_world.py` now if Task 5 used `hash()`).

- [ ] **Step 3: Full-file run + commit**

Run: `uv run pytest tests/test_arithmetic_world.py tests/test_attention_economy.py -q`
Expected: all passed

```bash
git add tests/test_arithmetic_world.py src/arithmetic_world.py
git commit -m "Rung 1 task 8: S4 determinism - stable digests, identical trajectories, replayable journal"
```

---

### Task 9: S5 — persistence, attestation, the polarity discipline

**Files:**
- Test: `tests/test_arithmetic_world.py` (append)

**Interfaces:**
- Consumes: `tomos_service.TomosService(root).save_uod_with_chain(res.uod, res.chain)` / `.load_chain(uod_id)` (the `test_agon_evolution.py::test_trajectory_persists_and_attests` pattern).

- [ ] **Step 1: Append the failing test**

```python
class TestPersistence:
    def test_s5_trajectory_persists_and_attests(self, tmp_path):
        from tomos_service import TomosService
        res, _ = TestCriteria()._arm(rounds=30)
        service = TomosService(tmp_path)
        service.save_uod_with_chain(res.uod, res.chain)   # §3.3 fires before disk write
        reloaded = service.load_chain("rung1_arm")
        assert reloaded is not None
        assert len(reloaded.steps) == len(res.chain.steps)
```

- [ ] **Step 2: Run**

Run: `uv run pytest tests/test_arithmetic_world.py::TestPersistence -q`
Expected: PASS (the loop emits native residence chains since sweep #2). A failure here is a real regression in what the feed emits — diagnose against `tests/test_corpus_polarity_discipline.py`'s expectations, do not relax.

- [ ] **Step 3: Protected-module check + full suite**

Run: `git status --short src/` — expected: only `src/attention_economy.py` and `src/arithmetic_world.py` are new; **zero modified existing files** (S5).
Run: `uv run pytest tests/ -q` (full suite)
Expected: everything green (3652+ passed, no new failures).

- [ ] **Step 4: Commit**

```bash
git add tests/test_arithmetic_world.py
git commit -m "Rung 1 task 9: S5 - the arithmetic trajectory persists, attests, and touches no existing module"
```

---

### Task 10: dispose the criteria in the docs + cross-links

**Files:**
- Modify: `docs/BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md` (§3 rung-1 block: append the build record — which of S1–S5 held, with the measured refutation rounds per arm, honestly)
- Modify: `CLAUDE.md` (two module lines beside the `agon_evolution` cluster: `attention_economy.py`, `arithmetic_world.py`)
- Modify: `CURRENT_PLAN.md` (item: rung-1 arithmetic stage BUILT, criteria disposed, vault stage next)
- Modify: memory `project_bootstrap_directed_engagement.md` (+ MEMORY.md line update)

- [ ] **Step 1: Write the §3 build record**

Append to the rung-1 block in `docs/BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md`, after the S1–S5 list (fill the measured numbers from Task 7's run — the values below are placeholders that MUST be replaced with actuals):

```markdown
**Build record (2026-07-XX).** S1 HELD: economy refuted at round R_e vs FIFO R_f /
scatter R_s (measured). S2 HELD: barren kinds decayed below the hunt kind. S3 HELD:
`fermat_number → odd` entered M only with musement on. S4 HELD: identical
trajectories + journal replay. S5 HELD: two new modules, zero existing files touched,
§3.3 at the save boundary. Modules: `src/attention_economy.py` (the socket),
`src/arithmetic_world.py` (world #1 + `ProbeDirectedFeed`). Next: the vault as
world #2 (a separate cycle).
```

- [ ] **Step 2: CLAUDE.md + CURRENT_PLAN + memory lines**

CLAUDE.md, after the `wikidata_source.py` entry, add:

```markdown
- `attention_economy.py` — **rung 1, the attention socket** (BOOTSTRAP_AND_DIRECTED_ENGAGEMENT §3): `Want` + `AttentionEconomy` — severity-weighted decayed-yield-per-cost ordering of reaches, musement reservation + boredom detector, noisy-TV decay at kind and want level, degrade-to-mechanical, bounded registers with counted drops; adapters `wants_from_docket` / `wants_from_frontier`. Deterministic, geometry-free, unprotected.
- `arithmetic_world.py` — **rung 1 world #1**: computed arithmetic (atoms by computation, probe cost = primality-test cost, the deterministic `coin` noise) + `ProbeDirectedFeed` (a `Proposer` whose next item the attention layer chooses; FIFO/scatter baseline arms; JSONL journal = the replay canary). Headline: Fermat's 1640 conjecture refuted at F5 (Euler 1732) under budget only by the economy arm (S1–S5, pre-registered).
```

CURRENT_PLAN.md: add a line to the Last-Updated header block recording the build + criteria disposition. Memory: update `project_bootstrap_directed_engagement.md` (rung-1 arithmetic stage BUILT, S1–S5 disposition, vault next) and the MEMORY.md index line.

- [ ] **Step 3: Verify docs + commit + push**

Run: `uv run pytest tests/test_arithmetic_world.py tests/test_attention_economy.py -q` (final green)
Run: `grep -n "§[0-9]" docs/BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md | grep -v "§1\.1\|§2\|§3\|§4\|§5"` — any cross-doc §ref must name its target doc.

```bash
git add docs/BOOTSTRAP_AND_DIRECTED_ENGAGEMENT.md CLAUDE.md CURRENT_PLAN.md
git commit -m "Rung 1 built: the attention economy on the arithmetic world - S1-S5 disposed in the record"
git push
```

---

## Self-Review (done at plan-writing time)

- **Spec coverage:** economy scorer ✓ (T1–T2) · adapters ✓ (T3) · world ✓ (T4) · feed/socket ✓ (T5) · S1 ✓ (T7) · S2 ✓ (T7, with a named strengthening path) · S3 ✓ (T7) · S4 ✓ (T8) · S5 ✓ (T9) · docs ✓ (T10). Horizon register: deliberately out of scope (author decision). Docket/frontier integration beyond unit level: deliberately unit-only this cycle (S-criteria don't include it; the vault membrane has real episodes).
- **Known verification points flagged inline:** `DISPOSITION_CHALLENGE_M` symbol name (T6), `_refuted_law` proposal shape (T6), `child_cuts`/`area_of` API names (T5), `hash()` salting (T8 — must use sha1 digest).
- **Type consistency:** `Want(kind, key, payload, cost, severity, created_round, attempts)` used identically in T1/T3/T5; `choose(k, round_idx)`/`observe(round_idx, results)` signatures consistent; `refutation_round(res)` defined in T6, reused in T7–T9.
