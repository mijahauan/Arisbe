# C-Series Stage 3: The Communication Channels — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give a community of units the four channels spec §5 rules — assert · ask · challenge · typify — so that marks cross between units, and so that the structural observable (§7) can be measured: which marks stand, who takes them up, and whether any unit becomes preferentially consulted.

**Architecture:** Two prerequisites, then four channels, then the gates. The prerequisites are not polish: a **challenge channel cannot bite on a noiseless field** (in a world without exceptions a true law never fails, and induction currently yields only true laws — 0 misses at 14/14 seeds), and it **cannot dispose** without a retraction path (nothing in `Unit` retracts today). Building the channels first would produce a challenge channel that never fires — the same defect that already appeared twice in this program's history (E2b's broker that never fired; a gate rival that could never win). So noise and retraction come first, by dependency.

**Tech Stack:** Python 3.12, `uv run pytest`. Builds on `c_field`, `c_unit`, `c_membrane`, `c_use`, `model_materialization`.

## Global Constraints

- **The three premises bind** (spec §1): reality resides inside the unit and **nothing is scored against the field's regime**; a unit may never call `Field.consequent()` or read `Domain.law`. **The commens may not name any data structure** — what units exchange are *marks*, and `MarkBoard`/`Mark` are the permitted names. Apertures stay distinct.
- **Anticipate-before-observe** in `Unit.step` survives every change.
- **Marks are sealed between communities** in this stage (spec §5). Permeability is later.
- **Determinism:** one seed; no module-level `random`; reproducible across `PYTHONHASHSEED`.
- **A failing gate is data.** Never tune a parameter or weaken an assertion to recover a pass; report and stop.
- Do not modify the 14 protected modules. Import style `from module_name import Foo`.

## Deliberately out of scope

- **The maintenance channel** raised in spec §9b (a cheap re-mention that asserts nothing new but refreshes a mark's standing, per B&L's conversation-as-maintenance). §9b marks it **unruled**, and adding it here would be the implementer ruling for the author. Build the four channels §5 rules; leave that one for his ruling.
- Communities, budget, selection, lifecycle (stage 4) and the instrument suite (stage 5).
- **Do not build a cost meter.** The final review's standing recommendation is to replace the per-round EGIF serialize→parse cycle *before* any cost instrument exists, since 58% of inference time is currently string round-tripping and a meter built on that would charge parsing rather than reasoning — the exact defect that invalidated the E-series.

---

## File Structure

| File | Responsibility |
|---|---|
| `src/c_field.py` (modify) | Optional noise: a fraction of consequents withheld, and a fraction spurious. Makes laws refutable. |
| `src/c_unit.py` (modify) | `retract_law`; a rate-based induction tolerance; publish/read/adopt marks; a peer register. |
| `src/c_marks.py` (create) | `Mark` (attributed content) and `MarkBoard` (per-community, append-only, sealed). The exchange medium — never named "commens". |
| `tests/test_c_marks.py` (create) | Board semantics, attribution, uptake. |
| `tests/test_c_channels.py` (create) | The four channels and the stage-3 gates. |
| `tests/test_c_field.py`, `tests/test_c_unit.py` (modify) | Noise and retraction tests. |

---

### Task 1: Field noise — make laws refutable

**Files:** modify `src/c_field.py`, `tests/test_c_field.py`.

**Interfaces:** `FieldSpec` gains `withhold_rate: float = 0.0` and `spurious_rate: float = 0.0`; `default_spec` sets both to `0.1`. `Field.deliver` honours them.

**Why:** with an exception-free field a true law can never miss, so the learner cannot lose and a challenge can never succeed against a true law. Noise is what makes the record fallible, which is what makes induction, challenge, and durability all measurable. It also addresses the final review's finding that the Stage 1 gate rests on one knob.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_c_field.py
def test_noise_withholds_some_consequents_and_adds_some_spurious():
    spec = default_spec(seed=20260728)
    assert spec.withhold_rate > 0 and spec.spurious_rate > 0
    field = Field(spec)
    d = spec.domains[0]
    body_rel, head_rel = d.law

    withheld = spurious = 0
    for r in range(1, 200):
        prev_bodies = {a for rel, a in field._antecedents(d.name, r - 1) if rel == body_rel}
        heads_now = {a for rel, a in field.deliver(d.name, r) if rel == head_rel}
        withheld += len(prev_bodies - heads_now)      # a consequence that did not arrive
        spurious += len(heads_now - prev_bodies)      # a consequent with no antecedent
    assert withheld > 0, "no consequent is ever withheld — the field is exception-free"
    assert spurious > 0, "no spurious consequent ever appears"


def test_noise_is_deterministic():
    a, b = Field(default_spec(seed=5)), Field(default_spec(seed=5))
    for r in range(30):
        assert a.deliver("alpha", r) == b.deliver("alpha", r)


def test_zero_rates_restore_the_exception_free_field():
    import dataclasses
    spec = dataclasses.replace(default_spec(seed=5), withhold_rate=0.0, spurious_rate=0.0)
    field = Field(spec)
    d = spec.domains[0]
    body_rel, head_rel = d.law
    for r in range(1, 60):
        prev = {a for rel, a in field._antecedents(d.name, r - 1) if rel == body_rel}
        now = {a for rel, a in field.deliver(d.name, r) if rel == head_rel}
        assert prev == now
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_c_field.py -k noise -v`
Expected: FAIL — `AttributeError`/`TypeError` on the missing `withhold_rate`.

- [ ] **Step 3: Implement**

Add both fields to `FieldSpec` with `0.0` defaults; set `0.1` in `default_spec`. In `Field.deliver`, after computing the lagged consequents, use a **separate** `random.Random` seeded on `f"{seed}:noise:{domain_name}:{round_idx}"` so the noise draw cannot disturb the antecedent stream's rng sequence (determinism constraint). Withhold each licensed consequent with probability `withhold_rate`; then with probability `spurious_rate` add one head atom about a randomly chosen individual of that domain that the law did not license. Keep the sorted return.

- [ ] **Step 4: Verify**

Run: `uv run pytest tests/test_c_field.py tests/test_c_unit.py tests/test_c_stage_gates.py tests/test_c_use.py -v`
**Gate figures will move, and the Stage 1 gate may now genuinely fail** — the learner can lose for the first time. If it fails, REPORT the numbers and stop. Do not lower the rates. Also report: does the learner now miss, and does `induce` still find the planted laws at all?

- [ ] **Step 5: Commit**

```bash
git add src/c_field.py tests/test_c_field.py
git commit -m "feat(c-series): field noise — withheld and spurious consequents make laws refutable"
```

---

### Task 2: Retraction, and a rate-based induction tolerance

**Files:** modify `src/c_unit.py`, `tests/test_c_unit.py`.

**Interfaces:** `Unit.retract_law(law) -> bool`; `induce(min_support=3, max_pending_rate=0.05)` replacing the absolute `max_pending`.

**Why:** the challenge channel must be able to *dispose* — to defeat a held law — and nothing retracts today. Separately, the final review found `max_pending` is an absolute count measured against a monotonically growing fact set, so it silently tightens over a run, and the gate's verdict turns on that one knob. A **rate** is the honest form. Note this pairs with Task 1: noise means a true law will now show some pending cases, so a rate tolerance is what lets a true law survive while a false one still falls.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_c_unit.py
def test_retract_law_removes_it_and_reports_whether_it_was_held():
    _spec, _field, ap = _setup()
    u = Unit("u0", ap)
    u.laws.add(("p1", "q1"))
    assert u.retract_law(("p1", "q1")) is True
    assert ("p1", "q1") not in u.laws
    assert u.retract_law(("p1", "q1")) is False      # already gone


def test_a_retracted_law_stops_licensing_anticipations():
    _spec, _field, ap = _setup()
    u = Unit("u0", ap)
    u.facts.update(_unary("p1", ["x0"]))
    u.laws.add(("p1", "q1"))
    assert u.anticipate()
    u.retract_law(("p1", "q1"))
    assert u.anticipate() == set()


def test_induction_tolerance_is_a_rate_not_a_count():
    """A large body set tolerates proportionally more pending cases; a small one
    does not. An absolute count would treat both alike."""
    _spec, _field, ap = _setup()
    big = Unit("u0", ap)
    big.facts.update(_unary("p1", [f"x{i}" for i in range(100)]))
    big.facts.update(_unary("q1", [f"x{i}" for i in range(97)]))   # 3 pending of 100
    assert ("p1", "q1") in big.induce(min_support=3, max_pending_rate=0.05)

    small = Unit("u1", ap)
    small.facts.update(_unary("p1", [f"y{i}" for i in range(10)]))
    small.facts.update(_unary("q1", [f"y{i}" for i in range(7)]))  # 3 pending of 10
    assert ("p1", "q1") not in small.induce(min_support=3, max_pending_rate=0.05)
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_c_unit.py -k "retract or rate" -v`
Expected: FAIL — no `retract_law`; `induce` has no `max_pending_rate`.

- [ ] **Step 3: Implement**

Add `retract_law(self, law) -> bool` using `discard` semantics but reporting whether the law was held (`law in self.laws` before removing). Change `induce`'s signature to `max_pending_rate: float = 0.05` and its test from `len(body_args - head_args) > max_pending` to `len(body_args - head_args) > max_pending_rate * len(body_args)`. Update the docstring: the tolerance is now proportional, which is what keeps it from tightening as the fact set grows, and what lets a true law survive the field's noise while a false one still falls.

- [ ] **Step 4: Verify**

Run the whole C suite. **Report the learner's hits/misses and which laws it induces across at least 8 seeds under Task 1's noise** — this is the deliverable, since it tells us whether induction still works on a fallible field. If gates fail, report and stop.

- [ ] **Step 5: Commit**

```bash
git add src/c_unit.py tests/test_c_unit.py
git commit -m "feat(c-series): retraction, and a rate-based induction tolerance"
```

---

### Task 3: Marks, the board, and the assert channel

**Files:** create `src/c_marks.py`, `tests/test_c_marks.py`; modify `src/c_unit.py`.

**Interfaces:**
- `Mark(author: str, content: Fact | Tuple[str, str], kind: str, round_idx: int)` where `kind` is `"fact"` or `"law"`.
- `MarkBoard()` with `publish(mark) -> None`, `since(round_idx) -> List[Mark]`, `all_marks() -> List[Mark]`, `record_uptake(mark, adopter) -> None`, `uptake_of(mark) -> Set[str]`.
- `Unit.publish(board, round_idx) -> List[Mark]` (publishes what this unit newly holds), `Unit.read(board, round_idx) -> List[Mark]`, `Unit.adopt(mark, board) -> bool`.

**Why:** this is the exchange medium — the objectivated marks of premise 2. A mark carries its author, so uptake is attributable, which is what makes the structural observable countable. The board is per-community and append-only; nothing about it may be called "commens".

- [ ] **Step 1: Write the failing test**

```python
# tests/test_c_marks.py
from c_marks import Mark, MarkBoard

M1 = Mark(author="u0", content=("p1", (("c", "a1"),)), kind="fact", round_idx=0)


def test_a_mark_carries_its_author_so_uptake_is_attributable():
    board = MarkBoard()
    board.publish(M1)
    assert board.all_marks() == [M1]
    assert M1.author == "u0"


def test_uptake_is_recorded_per_adopter():
    board = MarkBoard()
    board.publish(M1)
    assert board.uptake_of(M1) == set()
    board.record_uptake(M1, "u1")
    board.record_uptake(M1, "u2")
    board.record_uptake(M1, "u1")           # idempotent
    assert board.uptake_of(M1) == {"u1", "u2"}


def test_since_returns_only_marks_from_that_round_onward():
    board = MarkBoard()
    board.publish(M1)
    later = Mark(author="u1", content=("p1", (("c", "a2"),)), kind="fact", round_idx=5)
    board.publish(later)
    assert board.since(5) == [later]
```

- [ ] **Step 2: Run to verify failure**

Run: `uv run pytest tests/test_c_marks.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'c_marks'`.

- [ ] **Step 3: Implement**

`Mark` a frozen dataclass (hashable, so it can key uptake). `MarkBoard` holds an append-only list plus `Dict[Mark, Set[str]]` for uptake; `since` filters by `round_idx >= n`; `record_uptake` uses a set so it is idempotent. Then on `Unit`: `publish` emits a `Mark` for each fact and law this unit holds that it has not already published (track a `_published` set); `read` returns the board's marks **excluding this unit's own**; `adopt(mark, board)` adds the mark's content to `self.facts` or `self.laws`, calls `board.record_uptake(mark, self.unit_id)`, and returns whether anything new was taken up.

Write a module docstring stating plainly that these are the **objectivated marks** — what units exchange — and that the **commens** is not any of them and names no structure here (spec premise 2).

- [ ] **Step 4: Verify**

Run: `uv run pytest tests/test_c_marks.py tests/test_c_unit.py -v`. Then `grep -rn "commens" src/` and confirm no data structure carries the name.

- [ ] **Step 5: Commit**

```bash
git add src/c_marks.py tests/test_c_marks.py src/c_unit.py
git commit -m "feat(c-series): marks, an attributed board, and the assert channel"
```

---

### Task 4: The ask channel

**Files:** modify `src/c_marks.py`, `src/c_unit.py`; create/extend `tests/test_c_channels.py`.

**Interfaces:** `Mark.kind` gains `"question"`; `Unit.ask(board, round_idx) -> Optional[Mark]` publishes one standing question; `Unit.answer(board, round_idx) -> List[Mark]` answers others' questions from its own holdings.

**Why:** this turns attention *social*. A unit now chooses between probing the field and answering a peer — the first genuine division of labour, and the precondition for typification having anything to learn from.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_c_channels.py
from c_field import Field, apertures_for, default_spec
from c_marks import MarkBoard
from c_unit import Unit


def _two_units():
    spec = default_spec(seed=20260728)
    aps = apertures_for(spec, n_units=4)
    return spec, Field(spec), Unit("u0", aps[0]), Unit("u1", aps[1])


def test_a_unit_asks_about_a_relation_it_has_no_instance_of():
    _spec, _field, u0, _u1 = _two_units()
    board = MarkBoard()
    u0.facts.add(("p1", (("c", "a1"),)))
    u0.laws.add(("p1", "q1"))       # q1 licensed but never observed
    q = u0.ask(board, 0)
    assert q is not None and q.kind == "question"


def test_another_unit_answers_from_its_own_holdings():
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0.facts.add(("p1", (("c", "a1"),)))
    u0.laws.add(("p1", "q1"))
    u0.ask(board, 0)
    u1.facts.add(("q1", (("c", "a1"),)))
    answers = u1.answer(board, 1)
    assert answers, "u1 holds the answer and should have offered it"
    assert all(m.author == "u1" for m in answers)
```

- [ ] **Step 2–5:** run to confirm failure (`AttributeError: ask`), implement, verify, commit.

**Implementation notes.** `ask` picks the unit's most-wanted unknown: a relation appearing in a held law's head for which it holds no instance. Publish it as a `Mark(kind="question")` whose content is the relation name paired with the individual in question. `answer` scans `board`'s open questions from other authors and publishes a `"fact"` mark for each it can satisfy from `self.facts`. A unit never answers its own question.

```bash
git commit -m "feat(c-series): the ask channel — questions published, answered from holdings"
```

---

### Task 5: The challenge channel

**Files:** modify `src/c_marks.py`, `src/c_unit.py`, `tests/test_c_channels.py`.

**Interfaces:** `Mark.kind` gains `"challenge"`; `Unit.challenge(board, round_idx) -> List[Mark]`; `Unit.dispose_challenges(board, round_idx) -> List[Tuple[str, str]]` returning the laws it retracted.

**Why:** this is what finally lets durability read *false* — a held law can be defeated by something other than a decay clock. It depends on Task 1 (a noiseless field yields no counterexamples) and Task 2 (nothing to dispose into without retraction).

**The disposition rule, stated once:** a unit challenges a published **law** mark when its own facts contain a counterexample — an individual holding the law's body without its head. The challenge mark carries that counterexample. The law's author, on reading a challenge against a law it holds, **verifies the counterexample against its own facts** and retracts the law if it cannot rebut it. The calculus decides, not the challenger's authority: a challenge citing an individual the author holds *with* the head is rebutted and the law stands.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_c_channels.py
def test_a_counterexample_holder_challenges_a_published_law():
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z9"),)))       # body without head — a counterexample
    challenges = u1.challenge(board, 1)
    assert challenges and challenges[0].kind == "challenge"


def test_an_unrebutted_challenge_retracts_the_law_from_its_author():
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z9"),)))
    u1.challenge(board, 1)
    retracted = u0.dispose_challenges(board, 2)
    assert ("p1", "q1") in retracted
    assert ("p1", "q1") not in u0.laws


def test_a_rebuttable_challenge_leaves_the_law_standing():
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0.laws.add(("p1", "q1"))
    u0.facts.update({("p1", (("c", "z9"),)), ("q1", (("c", "z9"),))})   # author holds the head
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z9"),)))
    u1.challenge(board, 1)
    retracted = u0.dispose_challenges(board, 2)
    assert ("p1", "q1") not in retracted
    assert ("p1", "q1") in u0.laws
```

- [ ] **Step 2–5:** confirm failure, implement per the disposition rule, verify, commit.

```bash
git commit -m "feat(c-series): the challenge channel — a law defeated by a counterexample, not by authority"
```

---

### Task 6: The typify channel

**Files:** modify `src/c_unit.py`, `tests/test_c_channels.py`.

**Interfaces:** `Unit.peers: Dict[str, Dict[str, int]]` — per peer, per relation, a count of answers that proved out; `Unit.credit(mark, proved: bool) -> None`; `Unit.whom_to_ask(relation) -> Optional[str]`.

**Why:** Berger & Luckmann's reciprocal typification, made operational — a unit learns *whom to ask* about what. This cannot exist in an individual, which is why it is the sharpest test of whether a community exists at all.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_c_channels.py
def test_a_unit_learns_whom_to_ask_from_answers_that_proved_out():
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    good = Mark(author="u1", content=("q1", (("c", "a1"),)), kind="fact", round_idx=0)
    bad = Mark(author="u2", content=("q1", (("c", "a2"),)), kind="fact", round_idx=0)
    u0.credit(good, proved=True)
    u0.credit(good, proved=True)
    u0.credit(bad, proved=False)
    assert u0.whom_to_ask("q1") == "u1"


def test_whom_to_ask_is_none_before_any_evidence():
    _spec, _field, u0, _u1 = _two_units()
    assert u0.whom_to_ask("q1") is None
```

(add `from c_marks import Mark` to the test file's imports)

- [ ] **Step 2–5:** confirm failure, implement, verify, commit.

**Implementation notes.** `credit` increments `peers[author][relation]` on `proved=True` and decrements on `False`. `whom_to_ask` returns the peer with the highest count for that relation, `None` if no peer has a positive score. Ties break on peer id, for determinism.

```bash
git commit -m "feat(c-series): the typify channel — a unit learns whom to ask"
```

---

### Task 7: The stage-3 gates

**Files:** `tests/test_c_channels.py`.

**Why:** spec §7 pre-registers what *nothing* looks like. These gates assert the two things that would make a community real, and they must be able to fail.

- [ ] **Step 1: Write the gates**

Two runs over the same seed and field, a live world and a mute twin (channels off), each with four units:

1. **Communication buys something.** The live world's aggregate membrane `net_score` exceeds the mute twin's. Measure and report both; if they are indistinguishable, that is the pre-registered null and a real result — report it, do not tune.
2. **Consultation departs from uniform.** After a run, at least one unit's `whom_to_ask` is non-`None`, and the who-asks-whom distribution is not uniform. Report the matrix.

- [ ] **Step 2–5:** run, measure, commit. **If either gate reads null, report the numbers and stop.** Spec §7 names these outcomes as results worth having, including the finding that four communicating units under this field learn nothing from each other.

```bash
git commit -m "test(c-series): the stage-3 gates — communication's value, and consultation's departure from uniform"
```

---

## Notes for the implementer

- **A failing gate is data.** Several of this program's most useful findings came from refusing to smooth one.
- **Do not add the maintenance channel** (§9b) — it is deliberately unruled by the author.
- **Do not build a cost meter** — see "out of scope" above; the reason is specific and load-bearing.
- Tasks 1 and 2 will move the existing Stage 1/2 gate figures. Update the narrated numbers in those docstrings as you go, so the record stays true.
