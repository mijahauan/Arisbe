# C-Series Foundation Repairs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair the four defects the stage 1–2 build exposed (spec §9a), so stage 3's communication channels are built on a foundation where units genuinely reason, the field does not go silent, overlap carries content, and the scoring statistic is stable.

**Architecture:** Four independent repairs, ordered so each is testable alone. The load-bearing one is Task 1: the unit stops hand-rolling inference and derives through `model_materialization.materialize_egi`, rendering its held facts and laws as a real EGI (laws as cuts, per `model_revision.add_rule`'s idiom). That single change makes provenance real, makes work-use real, and puts the unit on the same representation as `world_scroll`/`agon_evolution`.

**Tech Stack:** Python 3.12, `uv run pytest`. Existing modules: `model_materialization`, `model_revision` (for the EGIF idiom), `egif_parser_dau`, `egif_generator_dau`, `resolving_membrane`.

## Global Constraints

- **The three premises still bind** (spec §1): reality resides inside the unit and **nothing is scored against the field's regime** — a unit may never call `Field.consequent()` or read `Domain.law`; the commens may not name any data structure; apertures stay distinct.
- **Determinism:** one seed governs all randomness; never call `random` module-level functions; runs must be reproducible across `PYTHONHASHSEED`.
- **Anticipate-before-observe** ordering in `Unit.step` is load-bearing and must survive every change.
- **Do not modify the 14 protected modules.** `model_materialization.py` is not among them.
- **Import style:** `from module_name import Foo`.
- Existing suite must stay green apart from tests this plan deliberately updates.

---

## File Structure

| File | Change |
|---|---|
| `src/c_unit.py` | Unit renders its facts+laws to an EGI and derives via `materialize_egi(provenance=…)`; keeps a per-round provenance map. |
| `src/c_field.py` | More individuals per domain (kills saturation); a shared individual pool (makes overlap content, not just naming). |
| `src/c_membrane.py` | Adds `net_score`; `accuracy` returns `None` with no bets rather than a fabricated `0.0`. |
| `tests/test_c_unit.py`, `tests/test_c_field.py`, `tests/test_c_membrane.py`, `tests/test_c_stage_gates.py` | Updated for the above; new tests per task. |

---

### Task 1: The unit derives through the real forward-chainer

**Files:** Modify `src/c_unit.py`; modify `tests/test_c_unit.py`.

**Interfaces:**
- Consumes: `materialize_egi(egi, provenance=None) -> (facts_egi, report)` from `model_materialization`; `parse_egif` from `egif_parser_dau`.
- Produces: `Unit.as_egi() -> RelationalGraphWithCuts`; `Unit.last_provenance: Dict[Fact, FrozenSet[Fact]]`; `anticipate()` unchanged in signature but now backed by real forward-chaining.

**Why:** today `anticipate()` hand-matches tuples, so stage 2's provenance is unused and the unit shares no representation with the rest of Arisbe. This is the repair that stops the C-series repeating the E-series' "units never reasoned" failure.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_c_unit.py
from egi_core_dau import RelationalGraphWithCuts


def test_unit_renders_its_state_as_an_egi():
    _spec, _field, ap = _setup()
    u = Unit("u0", ap)
    u.facts.update(_unary("p1", ["x0", "x1"]))
    u.laws.add(("p1", "q1"))
    egi = u.as_egi()
    assert isinstance(egi, RelationalGraphWithCuts)
    names = {egi.get_relation_name(e.id) for e in egi.E}
    assert {"p1", "q1"} <= names          # the law's body and head both appear
    assert len(egi.Cut) >= 2               # a law is drawn as nested cuts


def test_anticipation_comes_from_real_forward_chaining_with_provenance():
    _spec, _field, ap = _setup()
    u = Unit("u0", ap)
    u.facts.update(_unary("p1", ["x0"]))
    u.laws.add(("p1", "q1"))
    anticipated = u.anticipate()
    assert ("q1", (("c", "x0"),)) in anticipated
    # the derivation's support is now recoverable — provenance is no longer unused
    assert u.last_provenance
    assert u.last_provenance[("q1", (("c", "x0"),))] == frozenset({("p1", (("c", "x0"),))})
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_c_unit.py -k "egi or forward_chaining" -v`
Expected: FAIL — `AttributeError: 'Unit' object has no attribute 'as_egi'`

- [ ] **Step 3: Implement**

Add to `src/c_unit.py` (imports first: `from egif_parser_dau import parse_egif`, `from model_materialization import Fact, materialize_egi`, `from egi_core_dau import RelationalGraphWithCuts`, plus `Dict`/`FrozenSet` from typing):

```python
    def as_egi(self) -> RelationalGraphWithCuts:
        """Render this unit's held content as a real EGI: each fact an atom on
        the sheet, each law a Horn cut ``~[ (body *x) ~[ (head x) ] ]``.

        This is the same EGIF idiom `model_revision.add_rule` uses, so a unit's
        model is the same kind of object the rest of Arisbe reasons over."""
        parts: List[str] = []
        for rel, args in sorted(self.facts):
            labels = " ".join(f'"{a[1]}"' for a in args)
            parts.append(f"({rel} {labels})")
        for body_rel, head_rel in sorted(self.laws):
            parts.append(f"~[ ({body_rel} *x) ~[ ({head_rel} x) ] ]")
        return parse_egif(" ".join(parts) if parts else "")

    def anticipate(self) -> Set[Fact]:
        """Forward-chain the unit's own model and keep what it does not already
        hold. The chaining is the project's real materializer, so the support of
        every anticipation is recorded in ``last_provenance``."""
        if not self.laws or not self.facts:
            self.last_provenance = {}
            return set()
        provenance: Dict[Fact, FrozenSet[Fact]] = {}
        facts_egi, _report = materialize_egi(self.as_egi(), provenance=provenance)
        self.last_provenance = provenance
        derived = set(provenance.keys())
        return {f for f in derived if f not in self.facts}
```

and add `last_provenance: Dict[Fact, FrozenSet[Fact]] = dc_field(default_factory=dict)` to the dataclass fields.

- [ ] **Step 4: Run to verify pass, then the whole C suite**

Run: `uv run pytest tests/test_c_unit.py tests/test_c_stage_gates.py -v`
Expected: all pass. **If a stage gate now fails, that is data** — report the numbers, do not tune.

- [ ] **Step 5: Commit**

```bash
git add src/c_unit.py tests/test_c_unit.py
git commit -m "fix(c-series): the unit derives through the real forward-chainer, with provenance"
```

---

### Task 2: Kill the field's saturation

**Files:** Modify `src/c_field.py`; modify `tests/test_c_field.py`.

**Interfaces:** `Domain.individuals` grows; `default_spec` unchanged in signature.

**Why:** a unit currently holds every atom of its aperture by ~round 18 and then places no bets for 42 rounds. Anticipation must stay live for a 60-round run to mean anything.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_c_field.py
from c_unit import Unit


def test_anticipation_stays_live_late_in_a_run():
    """Saturation check: a lawful unit must still be placing bets after round 40."""
    spec = default_spec(seed=20260728)
    field = Field(spec)
    ap = apertures_for(spec, n_units=4)[0]
    u = Unit("u0", ap)
    u.laws.add(spec.domains[0].law)
    early = late = 0
    for r in range(60):
        bets = len(u.anticipate())
        if r < 20:
            early += bets
        elif r >= 40:
            late += bets
        u.step(field, r)
    assert early > 0
    assert late > 0, "the field saturated — no bets placed after round 40"
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_c_field.py -k saturat -v`
Expected: FAIL on the `late > 0` assertion.

- [ ] **Step 3: Implement**

In `default_spec`, replace each domain's 5-individual tuple with **40** individuals, generated as a tuple comprehension so the file stays readable — e.g. for alpha: `tuple(f"a{i}" for i in range(1, 41))`, and likewise `b`, `g`, `d`. Change nothing else.

- [ ] **Step 4: Run to verify pass, then the whole C suite**

Run: `uv run pytest tests/test_c_field.py tests/test_c_unit.py tests/test_c_stage_gates.py -v`
Expected: pass. Gate numbers will shift; **record the new hit/miss/accuracy figures in your report.** If a gate fails, report rather than tune.

- [ ] **Step 5: Commit**

```bash
git add src/c_field.py tests/test_c_field.py
git commit -m "fix(c-series): 40 individuals per domain — anticipation stays live past round 40"
```

---

### Task 3: Make overlap content, not naming

> **CORRECTED IN EXECUTION (2026-07-29).** This task as specified below was
> **wrong**: a *separate* `shared_individuals` namespace (`s1…s20`), disjoint
> from domain individuals, gives cross-domain coincidence but makes any
> *domain-relation → shared* law structurally unsatisfiable — silently
> reintroducing the zero-ceiling rival defect an earlier fix wave had removed.
> The shipped correction (commit `bc95912`) instead puts the overlap in the
> domains' **own individual lists**: a core `s1…s10` every domain knows, plus 30
> private each, with `shared` drawing from the domain's own list. `FieldSpec.
> shared_individuals` was removed rather than left as a vestige. Read the task
> below as history; the spec's §9a-bis records what actually shipped.

**Files:** Modify `src/c_field.py`; modify `tests/test_c_field.py`.

**Interfaces:** `FieldSpec` gains `shared_individuals: Tuple[str, ...]`; `Field._antecedents` draws the `shared` relation's argument from that pool.

**Why:** domains currently have disjoint individuals, so there is **zero** cross-domain atom overlap — `shared` is shared in name only, and stage 3's marks would have nothing transferable to carry.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_c_field.py
def test_domains_share_individuals_so_atoms_can_overlap():
    spec = default_spec(seed=20260728)
    field = Field(spec)
    seen = {}
    for d in spec.domains:
        args = set()
        for r in range(40):
            args |= {a for rel, a in field.deliver(d.name, r) if rel == "shared"}
        seen[d.name] = args
    alpha, beta = seen["alpha"], seen["beta"]
    assert alpha & beta, "no individual is shared across domains — overlap is naming only"
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_c_field.py -k share -v`
Expected: FAIL — the intersection is empty.

- [ ] **Step 3: Implement**

Add `shared_individuals: Tuple[str, ...] = ()` to `FieldSpec`. In `default_spec`, set it to `tuple(f"s{i}" for i in range(1, 21))`. In `Field._antecedents`, when the relation being emitted is `"shared"`, draw the individual from `self.spec.shared_individuals` (falling back to the domain's own list if that pool is empty, so an old spec still works); otherwise draw from the domain's own individuals as now. Keep the same `rng` and draw order so determinism holds.

- [ ] **Step 4: Run to verify pass, then the whole C suite**

Run: `uv run pytest tests/test_c_field.py tests/test_c_unit.py tests/test_c_use.py tests/test_c_stage_gates.py -v`
Expected: pass. Report any shifted gate figures.

- [ ] **Step 5: Commit**

```bash
git add src/c_field.py tests/test_c_field.py
git commit -m "fix(c-series): a shared individual pool — cross-domain overlap now carries content"
```

---

### Task 4: A stable scoring statistic

**Files:** Modify `src/c_membrane.py`; modify `tests/test_c_membrane.py` and any test asserting `accuracy == 0.0`.

**Interfaces:** `MembraneLedger` gains `net_score -> int` (hits − misses); `accuracy` returns `Optional[float]`, `None` when no bets were placed.

**Why:** accuracy as a bare ratio is unstable at low bet volumes — a rival winning 1 of 1 outranks a learner winning 5 of 7, which is what made a stage gate flip across seeds. And returning `0.0` for a unit that never bet fabricates a score for an abstainer; `resolving_membrane.PredictionLedger` returns `None` there for exactly this reason.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_c_membrane.py
def test_no_bets_yields_no_accuracy_not_a_fabricated_zero():
    led = MembraneLedger()
    led.score(anticipated=set(), arrived={A}, round_idx=0)
    assert led.accuracy is None
    assert led.net_score == 0


def test_net_score_is_stable_where_a_ratio_is_not():
    """A 1-of-1 rival must not outrank a 5-of-7 learner."""
    lucky, solid = MembraneLedger(), MembraneLedger()
    lucky.score(anticipated={A}, arrived={A}, round_idx=0)
    for i, hit in enumerate([True] * 5 + [False] * 2):
        f = ("r", (("c", f"x{i}"),))
        solid.score(anticipated={f}, arrived={f} if hit else set(), round_idx=i)
    assert lucky.accuracy > solid.accuracy      # the ratio's pathology, shown
    assert solid.net_score > lucky.net_score    # the stable statistic, fixed
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_c_membrane.py -k "fabricated or stable" -v`
Expected: FAIL — `accuracy` returns `0.0`, and `net_score` does not exist.

- [ ] **Step 3: Implement**

In `src/c_membrane.py` add `Optional` to the typing import, add:

```python
    @property
    def net_score(self) -> int:
        """Hits minus misses — stable at low bet volumes, where a bare ratio is
        not (one lucky hit reads as a perfect score)."""
        return self.hits - self.misses
```

and change `accuracy` to return `Optional[float]`, yielding `None` when `bets == 0` rather than `0.0`, with a docstring saying an abstainer has no accuracy rather than a zero one.

Then update every existing assertion that expected `0.0` for a no-bet ledger — in `tests/test_c_membrane.py`, `tests/test_c_unit.py`, and `tests/test_c_stage_gates.py`. **Where a gate compared accuracies against a non-betting arm, compare `net_score` instead**, since that is the statistic that survives the comparison honestly. Do not delete the seed-fragility or saturation docstrings; update them to say which statistic the gate now uses.

- [ ] **Step 4: Verify**

Run: `uv run pytest tests/test_c_field.py tests/test_c_membrane.py tests/test_c_unit.py tests/test_c_use.py tests/test_c_stage_gates.py tests/test_materialization_provenance.py -v`
Expected: all pass. **Re-check the Stage 1 gate across several seeds and report whether `net_score` is stable where accuracy flipped** — that is the point of this task.

- [ ] **Step 5: Commit**

```bash
git add src/c_membrane.py tests/
git commit -m "fix(c-series): net_score, and no fabricated accuracy for an abstainer"
```

---

## Notes for the implementer

- **If a gate fails after a repair, that is data.** Report the numbers; never tune a parameter or weaken an assertion to make a gate pass. The whole series exists because a previous one reported what its instruments could not support.
- Task 1 is the load-bearing repair. If it cannot be made to work, stop and report rather than proceeding to Tasks 2–4 on a foundation that still hand-rolls inference.
- Stage 3's four channels are **out of scope**. Do not add a coordinator, a mark ledger, or a second community.
