# The re-measurement pass — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Retire `net_score` as a gate statistic across the C-series, add the one
missing cost number, guard rate uniformity, and move `corroboration_window` 5 → 8 in a
single re-measurement.

**Architecture:** Three phases in which only the last may move a measured figure.
Phase 1 instruments (one integer on `Unit`, one test-side reader over the board, one
guard). Phase 2 re-expresses assertions. Phase 3 changes the one default and
re-measures. Phases 1 and 2 moving no figure is the verification that separates them —
it is [THE_KYTOS.md](../../THE_KYTOS.md) §1.3's non-interference rule under test.

**Tech Stack:** Python 3.12, `uv`, pytest. No new dependencies. No new `src/` module.

**Design of record:**
[docs/superpowers/specs/2026-07-31-net-score-retirement-and-window-re-measurement-design.md](../specs/2026-07-31-net-score-retirement-and-window-re-measurement-design.md)

## Global Constraints

- Run everything through `uv run` — e.g. `uv run pytest tests/test_c_unit.py -q`.
- Import style is `from c_unit import Unit`, never `from src.c_unit import Unit`.
- **No new module in `src/`.** The only `src/` changes in this whole plan are:
  `Unit.attended` (Task 1), the `net_score` docstring (Task 4),
  `corroboration_window`'s default and docstring (Task 9).
- **`src/c_unit.py` is NOT a protected module** — `tools/core_protection_system.py`
  guards 14 modules and none of the `c_*` series is among them. No
  `.core_modification_authorized` file is needed.
- **The retirement rule** (spec §4), which every Phase-2 task obeys:
  no gate may be decided by comparing hits − misses **between arms**; a cross-arm gate
  is decided on the law components with a **participation clause** (bets placed);
  within one arm, "a held law pays" is stated on `hits` and `misses` directly.
  **Pinning is reporting** — an assertion of an exact measured value stays.
- **Phases 1 and 2 must move no measured figure.** If a figure moves, STOP and report;
  it is a finding, not a nuisance.
- The C suite takes ~14 minutes. Full-suite runs are called out explicitly; everything
  else runs one file or one test.
- Commit after every task.

---

### Task 1: `Unit.attended` — the one number that exists nowhere

**Files:**
- Modify: `src/c_unit.py` (the `Unit` dataclass fields, after `replication_window`'s
  docstring block ending ~line 350; and `Unit.step`, line 830-848)
- Test: `tests/test_c_unit.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `Unit.attended: int` — how many rounds this unit met the field.
  Incremented at the END of `Unit.step`. Read by Task 2's `_cost_reading` and by
  Task 3's tests. Never read inside the round it counts.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_c_unit.py`:

```python
def test_attendance_is_counted_and_written_after_the_act():
    """`Unit.attended` is the denominator of every rate reading, and it is
    written AFTER the step completes — THE_KYTOS §1.3's write-after rule, which
    is what keeps a report from reaching the act it reports on.

    A unit that attends every round of a 20-round run reads 20; a unit stepped
    on even rounds only reads 10. Attendance counts occasions met, never rounds
    elapsed, so bounded attention cannot inflate a rate by shortening its own
    denominator."""
    spec = default_spec(seed=20260728)
    field = Field(spec)
    ap = apertures_for(spec, n_units=4)[0]

    every = Unit("u0", ap)
    assert every.attended == 0               # nothing acted, nothing reported
    for r in range(20):
        every.step(field, r)
    assert every.attended == 20

    staggered = Unit("u1", ap)
    for r in range(20):
        if r % 2 == 0:
            staggered.step(field, r)
    assert staggered.attended == 10
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_c_unit.py::test_attendance_is_counted_and_written_after_the_act -v`
Expected: FAIL with `AttributeError: 'Unit' object has no attribute 'attended'`

- [ ] **Step 3: Add the field**

In `src/c_unit.py`, in the `Unit` dataclass, immediately after the
`replication_window` field and its docstring (before `peers:`), add:

```python
    attended: int = 0
    """How many rounds this unit actually met the field — the denominator of
    every rate reading, and the only act-count that exists nowhere else.

    WRITTEN AFTER THE ACT, NEVER BEFORE (THE_KYTOS §1.3). `step` increments this
    once it has anticipated, observed, been scored and recorded, so no decision
    in the round it counts can read it. Nothing in `src/` reads it at all: it is
    an observer's number, and a unit that consulted its own cost to decide
    whether to act would be the thing the doctrine says does not happen.

    WHY ATTENDANCE AND NOT ROUNDS ELAPSED. Under bounded attention a unit meets
    the field on half the rounds, so rounds elapsed would price a sleeping unit
    the same as a working one and would let a rate be lowered by sleeping. The
    acts a unit performed OUTSIDE the membrane need no counter here — they are
    already reported on the board, attributed and dated, which is where the
    community can read them."""
```

- [ ] **Step 4: Increment it in `step`**

In `src/c_unit.py`, `Unit.step`, change the body's tail from:

```python
        self._record(arrived, round_idx)
        if induce:
            self.induce(round_idx)
```

to:

```python
        self._record(arrived, round_idx)
        if induce:
            self.induce(round_idx)
        self.attended += 1        # AFTER the act — THE_KYTOS §1.3
```

And append to `step`'s docstring, after the closing of the existing final
paragraph:

```
        Attendance is counted last, after the round's work is done, so the
        report of having acted cannot reach the act it reports on.
```

- [ ] **Step 5: Run the test**

Run: `uv run pytest tests/test_c_unit.py::test_attendance_is_counted_and_written_after_the_act -v`
Expected: PASS

- [ ] **Step 6: Verify non-interference — no figure moved**

Run: `uv run pytest tests/test_c_unit.py tests/test_c_field.py tests/test_c_membrane.py tests/test_c_stage_gates.py -q`
Expected: all pass, same counts as before the change. A failure here means the
instrument changed the act — STOP and report.

- [ ] **Step 7: Commit**

```bash
git add src/c_unit.py tests/test_c_unit.py
git commit -m "c_unit: Unit.attended, written after the act (THE_KYTOS §1.3)"
```

---

### Task 2: The cost reading — test-side, over residences that already exist

**Files:**
- Modify: `tests/test_c_channels.py` (add helper near `_play_challenge`, line ~1619)
- Test: `tests/test_c_channels.py`

**Interfaces:**
- Consumes: `Unit.attended` (Task 1); `MarkBoard.all_marks()`; `MembraneLedger.hits`,
  `.misses`.
- Produces: `_cost_reading(units, board) -> Dict[str, dict]` — per unit id, a dict with
  keys `attended` (int), `marks` (Dict[kind, int]), `bets` (int),
  `per_round` (Dict[kind, float]). Not consumed by any later task in this plan — it is
  the cost component of the vector, available to any gate that reports cost and to the
  twin control when ruling 2's invariance is next measured.

**Imports are already in place** in `tests/test_c_channels.py`: `Counter` (line 15),
`pytest` (17), `apertures_for` / `default_spec` (19), `MarkBoard` (20), `Unit` (21).
Nothing new to import.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_c_channels.py`, immediately after `_play_challenge`'s definition
ends (after its `return` statement):

```python
def test_the_cost_reading_reads_residences_that_already_exist():
    """COST IS READ, NOT INSTRUMENTED (THE_KYTOS §1.3). An act's effect resides
    in the report inside the membrane, in resources outside it, and in the shared
    reports among kytē — so a private counter beside the act would duplicate two
    of the three and invent the observer the doctrine refuses.

    The board already reports every channel act, attributed and dated; the ledger
    already holds the bets. `Unit.attended` is the only number that existed
    nowhere. This reader composes the three and adds nothing.

    THE TWIN IS THE POINT. Two units with the same aperture and the same rate
    parameters must read the same attendance — that is ruling 2's invariance
    condition made checkable, and it is what a size sweep would have to hold."""
    spec, units, board, *_ = _play_challenge(20260728, 20, channel=True,
                                             stagger=1, seed_laws=True)
    cost = _cost_reading(units, board)

    # Attendance is uniform where attention is: stagger=1 means all four met
    # every round.
    assert {c["attended"] for c in cost.values()} == {20}
    # Every published mark is attributed to the unit that made it, and the
    # reading's per-unit totals account for the whole board.
    assert sum(sum(c["marks"].values()) for c in cost.values()) == \
        len(board.all_marks())
    # The reading is per KIND, never summed across kinds: a board read and a
    # challenge are not the same act and may not be priced alike.
    assert all(isinstance(c["marks"], dict) for c in cost.values())
    # And it is a RATE, with attendance as its denominator.
    for c in cost.values():
        for kind, n in c["marks"].items():
            assert c["per_round"][kind] == n / c["attended"]


def test_the_cost_reading_reads_zero_for_a_unit_that_never_attended():
    """A unit that never met the field has no rate, not a zero one — the same
    discipline `MembraneLedger.accuracy` keeps for an abstainer. Dividing by an
    attendance of zero would fabricate a denominator."""
    spec = default_spec(seed=20260728)
    ap = apertures_for(spec, n_units=4)[0]
    idle = Unit("u0", ap)
    cost = _cost_reading([idle], MarkBoard())
    assert cost["u0"]["attended"] == 0
    assert cost["u0"]["per_round"] == {}
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_c_channels.py::test_the_cost_reading_reads_residences_that_already_exist -v`
Expected: FAIL with `NameError: name '_cost_reading' is not defined`

- [ ] **Step 3: Write the helper**

Add to `tests/test_c_channels.py`, immediately before the two tests just written:

```python
def _cost_reading(units, board):
    """What each unit's acts cost, READ where the acts already reside.

    THE_KYTOS §1.3: an act's effect resides in its report inside the membrane
    (`MembraneLedger`), in resources outside it, and in the shared reports among
    kytē (`MarkBoard`, which carries author, kind and round on every mark). None
    of that needs a counter. Only attendance did, and that is `Unit.attended`.

    KINDS ARE KEPT APART AND NEVER SUMMED. Summing a board read and a challenge
    into one "cost" would price two different acts alike, which is the collision
    `Unit.peers` refuses for (borne out, not borne out).

    INTERNAL WORK THAT LEAVES NO REPORT IS NOT COUNTED, deliberately. An act
    whose effect reaches no report has no channel by which to influence
    anything, so counting it privately would invent one. This reading therefore
    sees channel work and attendance and does NOT see materialization or
    anticipation work — a named limit, not an oversight.

    This lives in the tests because it is an OBSERVER's reading. Putting it in
    `src/` would hand a unit a faculty it does not have.
    """
    authored = Counter((m.author, m.kind) for m in board.all_marks())
    out = {}
    for u in units:
        marks = {kind: n for (author, kind), n in sorted(authored.items())
                 if author == u.unit_id}
        out[u.unit_id] = {
            "attended": u.attended,
            "marks": marks,
            "bets": u.ledger.hits + u.ledger.misses,
            "per_round": ({k: n / u.attended for k, n in marks.items()}
                          if u.attended else {}),
        }
    return out
```

`Counter` is already imported at line 15 of this file. Nothing new to import.

- [ ] **Step 4: Run both tests**

Run: `uv run pytest tests/test_c_channels.py -k cost_reading -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add tests/test_c_channels.py
git commit -m "c tests: the cost reading, read from board + ledger + attendance"
```

---

### Task 3: The rate-uniformity guard

**Files:**
- Modify: `tests/test_c_channels.py` — `_play_challenge` (line 1619) and
  `_play_ask_and_challenge` (line 2132)
- Test: `tests/test_c_channels.py`

**Interfaces:**
- Consumes: `Unit.corroboration_window`, `.corroborating_witnesses`,
  `.replication_window`. Imports already in place (`pytest` line 17,
  `apertures_for`/`default_spec` line 19, `Unit` line 21).
- Produces: `_assert_uniform_rate(units) -> None` — raises `ValueError` if the units
  disagree on any of the three rate parameters. Called by both community builders after
  their unit-construction loop.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_c_channels.py` after Task 2's tests:

```python
def test_a_community_of_mixed_rates_is_refused():
    """RULING 2 (2026-07-31): the disposition knobs ARE the terminal unit's rate
    parameter, so a community whose units disagree on them is not a community of
    terminal units and any West-shaped reading off it is void. Nothing enforced
    this before — `corroboration_window` is a per-unit dataclass field any caller
    could set individually.

    The refusal names what disagreed, in the style `apertures_for`'s
    `min_witnesses` already uses: a silent mixed-rate run is the failure mode,
    not a loud one."""
    spec = default_spec(seed=20260728)
    aps = apertures_for(spec, n_units=4)
    units = [Unit(f"u{i}", aps[i]) for i in range(4)]
    _assert_uniform_rate(units)                     # uniform by construction

    units[2].corroboration_window = 3
    with pytest.raises(ValueError) as exc:
        _assert_uniform_rate(units)
    assert "rate" in str(exc.value)
    assert "u2" in str(exc.value)


def test_a_sweep_still_varies_the_window_for_the_whole_community():
    """The guard forbids a MIXED community, never a swept one. A sweep sets the
    window for every unit at once, which is what a sweep should always have been
    doing — and `test_the_silence_window_at_three_five_and_eight` is exactly such
    a sweep, so it must keep passing untouched."""
    spec, units, *_ = _play_challenge(20260728, 10, channel=True, window=3)
    assert {u.corroboration_window for u in units} == {3}
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_c_channels.py -k mixed_rates -v`
Expected: FAIL with `NameError: name '_assert_uniform_rate' is not defined`

- [ ] **Step 3: Write the guard**

Add to `tests/test_c_channels.py` immediately before `_play_challenge`:

```python
def _assert_uniform_rate(units):
    """Every unit in one community must carry the same rate parameters.

    RULING 2 (2026-07-31) made the disposition knobs part of the terminal unit's
    RATE. West's question asks whether capacity and rate stay invariant as a
    community grows; a community whose units already disagree about their own
    rate cannot answer it, and a sweep that changed the window for some units
    would measure the window rather than the scaling.
    """
    rates = {u.unit_id: (u.corroboration_window, u.corroborating_witnesses,
                         u.replication_window) for u in units}
    distinct = set(rates.values())
    if len(distinct) > 1:
        raise ValueError(
            "mixed rate parameters across a community: the terminal unit's "
            "(corroboration_window, corroborating_witnesses, replication_window) "
            f"must be uniform, got {dict(sorted(rates.items()))}")
```

- [ ] **Step 4: Call it from both builders**

In `_play_challenge`, after the unit-construction loop — the line `units.append(u)`
followed by `board = MarkBoard()` — insert between them:

```python
    _assert_uniform_rate(units)
```

In `_play_ask_and_challenge`, the same: after its `units.append(u)` and before
`board = MarkBoard()`, insert:

```python
    _assert_uniform_rate(units)
```

- [ ] **Step 5: Run the new tests**

Run: `uv run pytest tests/test_c_channels.py -k "mixed_rates or sweep_still_varies" -v`
Expected: 2 passed

- [ ] **Step 6: Verify non-interference across the whole C suite**

Run: `uv run pytest tests/test_c_channels.py tests/test_c_unit.py tests/test_c_field.py tests/test_c_marks.py tests/test_c_membrane.py tests/test_c_stage_gates.py tests/test_c_speaker_variance.py tests/test_c_use.py -q`
Expected: all pass. **No measured figure may have moved.** If the guard fires
anywhere in the existing suite, that is a real finding — a measurement was running on
a mixed-rate community — so STOP, record which test and which units, and report before
changing anything.

- [ ] **Step 7: Commit**

```bash
git add tests/test_c_channels.py
git commit -m "c tests: refuse a community of mixed rate parameters (ruling 2)"
```

---

### Task 4: Demote `net_score`, and re-express the five within-arm assertions

**Files:**
- Modify: `src/c_membrane.py:102-108` (the `net_score` docstring)
- Modify: `tests/test_c_unit.py:448`
- Modify: `tests/test_c_stage_gates.py:179-181`, `:237`, `:241`
- Modify: `tests/test_c_field.py:268`
- Modify: `tests/test_c_channels.py:646`

**Interfaces:**
- Consumes: `MembraneLedger.hits`, `.misses` (both already exist).
- Produces: nothing new. `MembraneLedger.net_score` keeps its signature and value.

- [ ] **Step 1: Rewrite the `net_score` docstring**

In `src/c_membrane.py`, replace the `net_score` property's docstring with:

```python
    @property
    def net_score(self) -> int:
        """Hits minus misses. **OBSERVABILITY, NEVER A GATE** — the standing
        `restaked` and `late_arrivals` already carry, retired from the gate role
        by author ruling on 2026-07-31.

        WHY IT WAS RETIRED. Five measured inversions, each with its outcome
        recorded beside it: the score rose 988 while the channels destroyed 64 of
        the 64 true laws the field carried, then rose a further 327 while 28 of
        them were restored. A statistic that rises in both directions of the
        thing under study cannot gate it. (The other three:
        `tests/test_c_channels.py::test_gate_one_...` names them all.)

        REPORT IT, NEVER ASSERT A VERDICT ON IT. No gate may be decided by
        comparing this number BETWEEN ARMS; a cross-arm gate is decided on the
        law components — true laws held, converses held — and must carry a
        participation clause, because an arm can improve this number by very
        nearly ceasing to forecast, and one did. Within a single arm, whether a
        held law pays is stated on `hits` and `misses` directly. Pinning an exact
        measured value is reporting, and stays.

        It remains computed and remains read: GATE 1's whole argument is that
        this number rose while the community learned less, which needs the number
        legible. `resolving_membrane.PredictionLedger.net_score` is a different
        class and is unaffected."""
        return self.hits - self.misses
```

- [ ] **Step 2: Re-express `tests/test_c_unit.py:448`**

Replace:

```python
    # And with the re-charges gone, a record holding only true laws PAYS.
    assert u.ledger.net_score > 0
```

with:

```python
    # And with the re-charges gone, a record holding only true laws PAYS —
    # stated on the bets themselves rather than on the retired scalar
    # (src/c_membrane.py's `net_score`, observability only since 2026-07-31).
    assert u.ledger.hits > u.ledger.misses
```

- [ ] **Step 3: Re-express `tests/test_c_stage_gates.py:179-181`**

Replace:

```python
            assert led.net_score > 0, (
                f"seed {seed}: the planted law {domain.law} held alone LOSES "
                f"money — {led.hits}h/{led.misses}m net {led.net_score}")
```

with:

```python
            assert led.hits > led.misses, (
                f"seed {seed}: the planted law {domain.law} held alone LOSES "
                f"money — {led.hits}h/{led.misses}m (net {led.net_score}, "
                f"reported not asserted)")
```

- [ ] **Step 4: Re-express `tests/test_c_stage_gates.py:237` and `:241`**

Replace:

```python
    # And it loses: a converse held is a converse that costs.
    assert conv_arm.ledger.misses > conv_arm.ledger.hits
    assert conv_arm.ledger.net_score < 0
```

with:

```python
    # And it loses: a converse held is a converse that costs. One clause, on the
    # bets; `net_score < 0` said the same thing in retired vocabulary.
    assert conv_arm.ledger.misses > conv_arm.ledger.hits
```

Replace:

```python
    assert lawless.ledger.accuracy is None
    assert lawless.ledger.net_score == 0
    assert conv_arm.ledger.net_score < lawless.ledger.net_score
```

with:

```python
    assert lawless.ledger.accuracy is None
    # THE CROSS-ARM CLAUSE, RE-EXPRESSED. The old form compared two net scores.
    # What it meant is that one arm bet and lost while the other never played —
    # and BOTH halves are already asserted above (`:236` the converse arm bets,
    # `:240` the abstainer does not), so the claim now stands on those and the
    # scalar comparison is simply deleted rather than restated.
```

**Add no new assertion here.** The two lines above already carry the claim; the
correct edit is to delete `assert lawless.ledger.net_score == 0` and
`assert conv_arm.ledger.net_score < lawless.ledger.net_score` and leave the
comment in their place. Do not duplicate `:236` or `:240`.

- [ ] **Step 5: Re-express `tests/test_c_field.py:268`**

Replace:

```python
    assert rival.ledger.net_score < 0, "the wrong law must still lose overall"
```

with:

```python
    assert rival.ledger.misses > rival.ledger.hits, (
        "the wrong law must still lose overall — "
        f"{rival.ledger.hits}h/{rival.ledger.misses}m")
```

- [ ] **Step 6: Re-express `tests/test_c_channels.py:646`**

Replace:

```python
            assert asking.ledger.net_score > 0     # full attention makes money
```

with:

```python
            # Full attention makes money. Within one arm, and safe: the line
            # above has just pinned the two arms' hits and misses EQUAL, so no
            # cross-arm reading is being taken from a scalar here.
            assert asking.ledger.hits > asking.ledger.misses
```

- [ ] **Step 7: Run the touched files**

Run: `uv run pytest tests/test_c_membrane.py tests/test_c_unit.py tests/test_c_field.py tests/test_c_stage_gates.py -q`
Expected: all pass, counts unchanged.

Run: `uv run pytest tests/test_c_channels.py -k full_attention -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add src/c_membrane.py tests/test_c_unit.py tests/test_c_field.py tests/test_c_stage_gates.py tests/test_c_channels.py
git commit -m "Retire net_score from the gate role; the five within-arm clauses re-expressed"
```

---

### Task 5: The four cross-arm gates — decided on laws and participation

**Files:**
- Modify: `tests/test_c_unit.py:72` and `:531-532` (and the function name at `:520`-ish)
- Modify: `tests/test_c_stage_gates.py:141-142` (and the function name)

**Interfaces:**
- Consumes: `MembraneLedger.hits`, `.misses`; `Unit.laws`.
- Produces: nothing new. Two test functions are RENAMED — see Step 5.

- [ ] **Step 1: Re-express `tests/test_c_unit.py:72`**

In `test_held_law_beats_a_wrong_law_over_a_run`, replace:

```python
    assert lawful.ledger.net_score > misled.ledger.net_score
```

with:

```python
    # THE VERDICT, ON THE LAW COMPONENTS AND THE BETS — not on a cross-arm
    # scalar. The lawful arm holds a law the field carries and its bets pay; the
    # rival holds one it does not and its bets lose. That is the whole claim, and
    # it cannot be satisfied by an arm that improved a score by not betting,
    # which is how `net_score` passed five gates it should have failed.
    assert lawful.laws & {d.law for d in spec.domains}
    assert not (misled.laws & {d.law for d in spec.domains})
    assert lawful.ledger.hits > lawful.ledger.misses
    assert misled.ledger.misses > misled.ledger.hits
    # PARTICIPATION: neither arm won by falling silent.
    assert lawful.ledger.hits + lawful.ledger.misses > 0
```

- [ ] **Step 2: Verify `spec` is in scope at that point**

Run: `uv run pytest tests/test_c_unit.py::test_held_law_beats_a_wrong_law_over_a_run -v`
Expected: PASS. If it raises `NameError: spec`, read the top of the test function and
use the local name the fixture bound (the test builds `spec` via `default_spec` around
line 50).

- [ ] **Step 3: Re-express `tests/test_c_unit.py:531-532`**

Replace:

```python
    assert learner.ledger.net_score > fixed.ledger.net_score
    assert learner.ledger.net_score > misled.ledger.net_score
```

with:

```python
    # THE VERDICT, ON THE LAW COMPONENTS AND THE BETS. The learner induced a law
    # the field carries and its bets pay; the rival holds one it does not and its
    # bets lose; the abstainer never played. Three within-arm readings decide it,
    # so no arm can pass by improving a scalar while forecasting less.
    assert learner.ledger.hits > learner.ledger.misses
    assert misled.ledger.misses > misled.ledger.hits
    assert fixed.ledger.hits + fixed.ledger.misses == 0
    # PARTICIPATION: the learner is still betting, not merely surviving.
    assert learner.ledger.hits + learner.ledger.misses > 0
```

- [ ] **Step 4: Re-express `tests/test_c_stage_gates.py:141-142`**

Replace:

```python
    # And the learner beats it, and beats abstention — on `net_score`, the
    # statistic that is stable at low bet volumes and that an abstainer can
    # share a scale with (its `accuracy` is None, not 0.0).
    assert learner.ledger.net_score > misled.ledger.net_score
    assert learner.ledger.net_score > fixed.ledger.net_score
    assert fixed.ledger.accuracy is None      # it never bet; no ratio exists
```

with:

```python
    # THE VERDICT, RE-EXPRESSED 2026-07-31. It used to read on `net_score`, and
    # the retirement is why it no longer does: that statistic rose 988 while the
    # channels destroyed every true law the field carried, so a gate decided by
    # comparing it across arms is decided by a number that moves both ways.
    # The claim, stated where it is actually made — in the laws held and in the
    # bets each arm placed on them:
    assert learner.laws & {d.law for d in spec.domains}      # holds a true law
    assert not (misled.laws & {d.law for d in spec.domains})  # holds a false one
    assert learner.ledger.hits > learner.ledger.misses        # and it pays
    assert misled.ledger.misses > misled.ledger.hits          # and it costs
    assert fixed.ledger.hits + fixed.ledger.misses == 0       # and it never bet
    assert fixed.ledger.accuracy is None      # no bet placed, so no ratio exists
    # PARTICIPATION: the learner did not win by falling silent.
    assert learner.ledger.hits + learner.ledger.misses > 0
```

- [ ] **Step 5: Rename the two tests whose names name the retired statistic**

The claim is no longer that a score rises. Rename, in both the `def` line and any
reference to it elsewhere:

- `tests/test_c_unit.py`: `test_inducing_unit_learns_the_planted_law_and_its_score_rises`
  → `test_inducing_unit_learns_the_planted_law_and_its_bets_pay`
- `tests/test_c_stage_gates.py`: `test_stage_1_gate_a_unit_learns_a_planted_law_and_its_score_rises`
  → `test_stage_1_gate_a_unit_learns_a_planted_law_and_its_bets_pay`

Find references with:

```bash
grep -rn "_and_its_score_rises" tests src docs tasks
```

and update every hit, including any docstring that names the test.

- [ ] **Step 6: Update the docstring paragraph that argues for `net_score`**

In `tests/test_c_stage_gates.py`, the docstring block at lines 65-72 begins
`THE STATISTIC IS \`net_score\` (hits − misses), not \`accuracy\`.` Replace that whole
paragraph with:

```
    THE STATISTIC WAS `net_score` UNTIL 2026-07-31, AND IS NOT ANY LONGER. The
    reasons it was chosen still hold — a ratio over few bets is unstable, and the
    `fixed` arm never bets so its `accuracy` is `None` rather than 0.0 — but the
    retirement is about a different failure: compared ACROSS ARMS the score rose
    988 while the channels destroyed 64 of 64 true laws, then rose a further 327
    while 28 were restored. So this gate now reads the laws each arm holds and
    the bets each arm placed on them, and reports net without asserting on it.
    Abstention is still an honest zero: the `fixed` arm places no bets, which the
    gate now says directly.
```

- [ ] **Step 7: Run the touched files**

Run: `uv run pytest tests/test_c_unit.py tests/test_c_stage_gates.py -q`
Expected: all pass, counts unchanged.

- [ ] **Step 8: Commit**

```bash
git add tests/test_c_unit.py tests/test_c_stage_gates.py
git commit -m "The four cross-arm gates decided on laws + participation, not on net"
```

---

### Task 6: `test_asking_and_answering_beats_being_mute` — the arm where no law can move

**Files:**
- Modify: `tests/test_c_channels.py:588-600` (inside
  `test_asking_and_answering_beats_being_mute_at_equal_run_length`)

**Interfaces:**
- Consumes: `MembraneLedger.hits`, `.misses`.
- Produces: nothing new.

**Why this one is different, and must not be copied from Task 5.** `_play` seeds the
law and runs no challenge channel, so **no law can be lost in either arm**. The law
components cannot move, so there is nothing for a law clause to say. What the arm
actually measures is that the channel makes units *shed losing stakes* — which is the
same behaviour GATE 1 flags as suspicious. So the re-expression must state what
happened and let the docstring carry the reading, rather than celebrate a rising score.

- [ ] **Step 1: Replace the per-arm assertion**

Replace:

```python
        # Per-arm, so a single losing seed fails the gate and names itself.
        for asking, silent in zip(live, mute):
            assert asking.ledger.net_score > silent.ledger.net_score, (
                f"seed {seed} {asking.unit_id}: asking "
                f"({asking.ledger.net_score:+d}) did not beat mute "
                f"({silent.ledger.net_score:+d})")
```

with:

```python
        # Per-arm, so a single losing seed fails the gate and names itself.
        # RE-EXPRESSED 2026-07-31: the old form compared two net scores across
        # arms, which is the comparison the retirement forbids. In THIS arm no
        # law can be lost — `_play` seeds the law and runs no challenge channel —
        # so the score cannot be bought by destroying knowledge, and what the
        # channel actually does is shed losing stakes. That is stated directly,
        # and the shedding is made visible rather than folded into a scalar.
        for asking, silent in zip(live, mute):
            assert asking.ledger.misses < silent.ledger.misses, (
                f"seed {seed} {asking.unit_id}: asking shed no losing stake "
                f"({asking.ledger.misses} misses vs mute's "
                f"{silent.ledger.misses})")
            shed_misses = silent.ledger.misses - asking.ledger.misses
            shed_hits = silent.ledger.hits - asking.ledger.hits
            assert shed_misses > shed_hits, (
                f"seed {seed} {asking.unit_id}: the channel shed {shed_hits} "
                f"hits against {shed_misses} misses — it cost more than it saved")
            # PARTICIPATION, REPORTED: what the shedding cost in forecasts made.
            # Not asserted, because ceasing to forecast is exactly the behaviour
            # GATE 1 flags, and this gate must not reward it.
            assert asking.ledger.hits + asking.ledger.misses >= 0
```

- [ ] **Step 2: Add the reason to the docstring**

Insert as a new paragraph at the end of that test's docstring, before the closing
`"""`:

```
    WHY A NET COMPARISON WAS SAFE HERE AND IS STILL RETIRED. This arm seeds the
    law and runs no challenge channel, so no law can be lost in either arm and
    the inversion mechanism — buying a better score by destroying knowledge — is
    structurally absent. The comparison was therefore trustworthy here in a way
    it was not in GATE 1. It is retired anyway, because a gate that reads
    correctly only because of a property of its arm is a gate whose next reader
    has to rediscover that property. What the arm measures is stated instead:
    the channel sheds more losing stakes than winning ones.
```

- [ ] **Step 3: Run it**

Run: `uv run pytest tests/test_c_channels.py::test_asking_and_answering_beats_being_mute_at_equal_run_length -v`
Expected: PASS. If the `shed_misses > shed_hits` clause fails at some seed, STOP —
that is a real finding about the channel and must be reported, not tuned.

- [ ] **Step 4: Commit**

```bash
git add tests/test_c_channels.py
git commit -m "The ask-vs-mute gate says what it measures: stakes shed, not a score risen"
```

---

### Task 7: GATE 1 — demote the verdict clause, keep the inversion clause

**Files:**
- Modify: `tests/test_c_channels.py:3046` and its comment at `:3045`

**Interfaces:**
- Consumes: the existing `_aggregate_ask(...)` tallies.
- Produces: nothing new.

- [ ] **Step 1: Demote line 3046**

Replace:

```python
    # THE GATE'S OWN CLAUSE, AND IT PASSES.
    assert four_live["net"] > four_mute["net"]
    assert (four_mute["net"], four_live["net"]) == (-1421, -106)
```

with:

```python
    # THE GATE'S OWN CLAUSE, DEMOTED 2026-07-31. It passed, and passing meant the
    # opposite of what it looked like, which is why `net_score` was retired from
    # the gate role. The figures are PINNED — pinning is reporting, with teeth —
    # and the verdict is carried by the law and participation clauses below.
    assert (four_mute["net"], four_live["net"]) == (-1421, -106)
```

- [ ] **Step 2: Leave line 3068 alone, and say why**

The clause `four_mute["net"] < four_chal["net"] < four_live["net"]` **stays**. Add
above it, replacing its existing comment:

```python
    # THE DECOMPOSITION, AND THIS COMPARISON IS KEPT ON PURPOSE. Its content is
    # that the score rose in BOTH directions — the first step by destroying every
    # true law, the second by restoring 28 — so it asserts the inversion itself
    # rather than deciding anything by it. Retiring it would delete the evidence
    # the retirement rests on.
```

- [ ] **Step 3: Update the docstring's opening line**

The test's docstring opens `**GATE 1 PASSES ON \`net_score\` AND THE PASS MEANS THE
OPPOSITE OF WHAT IT LOOKS LIKE.**` Replace that sentence with:

```
    **GATE 1 PASSED ON `net_score`, THE PASS MEANT THE OPPOSITE OF WHAT IT LOOKED
    LIKE, AND ON 2026-07-31 THE STATISTIC WAS RETIRED FROM THE GATE ROLE FOR IT.**
    The figures below are pinned and reported; the verdict is carried by the laws
    held and the bets placed.
```

- [ ] **Step 4: Run GATE 1**

Run: `uv run pytest tests/test_c_channels.py::test_gate_one_the_score_improves_thirteenfold_while_the_community_learns_less -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_c_channels.py
git commit -m "GATE 1: the net clause demoted to a pin, the inversion clause kept"
```

---

### Task 8: Phase-2 verification — no figure has moved

**Files:** none modified.

**Interfaces:** none.

- [ ] **Step 1: Confirm no cross-arm net comparison survives**

Run:

```bash
grep -rn "net_score" tests/test_c_*.py | grep -v "test_c_membrane.py"
grep -rn '\["net' tests/test_c_channels.py
```

Expected: every surviving hit is either (a) an f-string reporting a figure, (b) an
equality pin, (c) `test_c_membrane.py`'s five arithmetic pins, or (d) GATE 1's
kept inversion clause at ~3068. **Any surviving `>` or `<` between two arms' net
values outside (d) is a miss — go back and fix it.**

- [ ] **Step 2: Full C suite**

Run: `uv run pytest tests/test_c_channels.py tests/test_c_unit.py tests/test_c_field.py tests/test_c_marks.py tests/test_c_membrane.py tests/test_c_stage_gates.py tests/test_c_speaker_variance.py tests/test_c_use.py -q`
Expected: all pass. Record the count — it should be 199 plus the 5 tests added by
Tasks 1-3 = **204**.

- [ ] **Step 3: Core suite**

Run: `uv run python tools/core_protection_system.py --report`
Expected: core protection passes, no `c_*` module listed as protected.

Run: `uv run pytest tests/ -q -x --ignore=tests/test_c_channels.py`
Expected: no regressions outside the C series.

- [ ] **Step 4: Record the phase-2 canary in the plan**

Append to this file, under Task 8, the line: `Phase 2 complete: <N> C tests pass, no
measured figure moved.` with the real N.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/plans/2026-07-31-net-score-retirement-and-window-re-measurement.md
git commit -m "Phase 2 complete: the retirement lands with no figure moved"
```

---

### Task 9: The window at 8 — the single re-measurement

**Files:**
- Modify: `src/c_unit.py:226` (the default) and its docstring
- Modify: whichever test docstrings and pinned figures the suite reports as moved —
  expected to include `tests/test_c_channels.py` (the `_aggregate_ask` pins at 2050-2052,
  2090, 2094, 2557, 2906, 2907, 3047, 3066, 3075) and `src/c_unit.py`'s own
  `corroboration_window` / `replication_window` docstring tables.

**Interfaces:**
- Consumes: everything above.
- Produces: the re-measured figures.

**This is the only task allowed to move a number.**

- [ ] **Step 1: Change the default**

In `src/c_unit.py`, change:

```python
    corroboration_window: int = 5
```

to:

```python
    corroboration_window: int = 8
```

- [ ] **Step 2: Rewrite the head of its docstring**

Replace the paragraph beginning `THE RATIONALE IS THE RULING'S OWN.` down to (but not
including) `3, 5 AND 8 ARE NOW MEASURED, AND THE DEFAULT WAS LEFT ALONE` with:

```
    THE RATIONALE IS THE RULING'S OWN. A challenge that gathers no support has
    failed, and "do not eliminate until corroboration" means silence cannot
    eliminate — so the window must end in restoration, not in retraction.

    EIGHT SINCE 2026-07-31, BY AUTHOR RULING, ON THE MEASURED TRADE BELOW: at six
    units, 3 → 8 saves 49 true laws (96 lost to 47) while sparing only 3
    converses (20 to 17). A true law's missing head is the thing a peer can
    actually supply and a converse's is not, so waiting longer helps the true law
    disproportionately. The entire visible price of the patience landed in
    `net_score`, which was retired from the gate role in the same ruling — so the
    trade is read on the laws, and 8 dominates.

    IT IS PART OF THE TERMINAL UNIT'S RATE (ruling 2), which carries two riders.
    It must stay UNIFORM across a community — enforced since 2026-07-31 by
    `tests/test_c_channels.py::_assert_uniform_rate`, which refuses a mixed-rate
    community outright. And it must be held CONSTANT across any size sweep, or
    the sweep measures the window instead of the scaling.

    THE PRICE OF PATIENCE IS STILL UNMEASURED IN ONE RESPECT: a longer window
    makes every unit do more work per doubt, and the cost reading sees channel
    acts and attendance but not the internal work a standing doubt occasions.
    Named, not closed.
```

Keep the measured table that follows (the 3/5/8 sweep) unchanged — it is the evidence
for the ruling.

- [ ] **Step 3: Run the C suite and collect every failure**

Run: `uv run pytest tests/test_c_channels.py tests/test_c_unit.py tests/test_c_field.py tests/test_c_marks.py tests/test_c_membrane.py tests/test_c_stage_gates.py tests/test_c_speaker_variance.py tests/test_c_use.py -q --tb=line > /private/tmp/claude-501/-Users-mjh-Sync-GitHub-Arisbe/b84493fe-b004-40b1-8c3d-72342cd9ec50/scratchpad/window8-run1.txt 2>&1; tail -60 /private/tmp/claude-501/-Users-mjh-Sync-GitHub-Arisbe/b84493fe-b004-40b1-8c3d-72342cd9ec50/scratchpad/window8-run1.txt`

Expected: a set of failures, each an equality pin whose expected value was measured at
window 5. **Read every one.** Each is a figure that must be re-measured, not a bug.

- [ ] **Step 4: Sanity-check the two tests that must NOT move**

Run: `uv run pytest tests/test_c_channels.py::test_the_silence_window_at_three_five_and_eight -v`
Expected: PASS unchanged — it sets the window explicitly for the whole community, so
the default cannot reach it. If it fails, the default leaked into a place that should
have been explicit; STOP and report.

Run: `uv run pytest tests/test_c_channels.py -k cost_reading -v`
Expected: PASS unchanged.

- [ ] **Step 5: Update each moved figure, keeping both readings**

For each failing assertion, update the pinned value to the newly measured one AND
update the docstring that narrates it, following this shape exactly:

```
    RE-MEASURED AT WINDOW 8 (the ruled default, 2026-07-31):

        four units                mute twin      live world
        net score                     <new>          <new>
        bets placed                   <new>          <new>
        true laws held at the end     <new>          <new>
        converses held at the end     <new>          <new>

    AT WINDOW 5, the previous default, for comparison — this is the reading the
    ruling was made on and it is kept for that reason:

        four units                mute twin      live world
        net score                     -1421           -106
        bets placed                    1497            110
        true laws held at the end     64/64          28/64
        converses held at the end     32/32          32/32
```

Never delete a window-5 figure. Label every retained table with the window it was
taken under.

- [ ] **Step 6: Re-run until green**

Run: `uv run pytest tests/test_c_channels.py tests/test_c_unit.py tests/test_c_field.py tests/test_c_marks.py tests/test_c_membrane.py tests/test_c_stage_gates.py tests/test_c_speaker_variance.py tests/test_c_use.py -q`
Expected: all pass. Iterate steps 5-6 until it does. Each iteration is ~14 minutes, so
update every figure a run reports before re-running.

- [ ] **Step 7: Full suite**

Run: `uv run pytest tests/ -q`
Expected: no regressions. `src/c_unit.py` is not imported by anything outside the C
series, so nothing else should move; if something does, that is a finding.

- [ ] **Step 8: Commit**

```bash
git add src/c_unit.py tests/test_c_*.py
git commit -m "corroboration_window 5 -> 8 (ruling 2), and the suite re-measured"
```

---

### Task 10: Close the pass

**Files:**
- Modify: `tasks/todo.md`
- Modify: `CURRENT_PLAN.md`
- Modify: `docs/CAPABILITY_MAP.md` (the C-series row, if the guard or attendance
  belongs in it — check §J.1 for the row added by the 2026-07-31 West corrections)

- [ ] **Step 1: Tick the two rulings in `tasks/todo.md`**

Move both `- [ ]` items under "Remaining, with honest sizing" to the "Done" section
with a one-line result each, and fill in the "Review" section with: what moved, what
did not, and the phase-1/2 canary result.

- [ ] **Step 2: Update `CURRENT_PLAN.md`**

Add the arc entry: the doctrine recorded at THE_KYTOS §1.3, the design refused and
redrafted, the retirement as a rule, the window at 8, and the re-measured headline
figures. Set the `▶ NEXT SESSION` block to the remaining order: the credential build
(which unblocks weighted witnesses), then the scarcity test.

- [ ] **Step 3: Run the book render check**

Run: `cd docs && quarto render --to html 2>&1 | tail -5`
Expected: 48/48, no errors. (The PDF format fails on a pre-existing YAML-alias error
unrelated to this work — do not attempt to fix it here.)

- [ ] **Step 4: Commit**

```bash
git add tasks/todo.md CURRENT_PLAN.md docs/CAPABILITY_MAP.md
git commit -m "Close the re-measurement pass: both rulings executed, next session set"
```

---

## What this plan deliberately does not do

- **Make a report influence further thought** (THE_KYTOS §1.3's other half). Nothing
  reads `MembraneLedger`; making a unit's own report downstream-effective *and only
  downstream* is a real change to what a kytos is, and its home is the scarcity test.
- **Weight witnesses rather than count them** (`src/c_unit.py:1759-1766`). Blocked on
  the credential, which is ruled and unbuilt.
- **Count internal work.** An act whose effect reaches no report has no channel by
  which to influence anything; counting it privately would invent one.
- **Fix the PDF book format.** Pre-existing, flagged in the spec.
