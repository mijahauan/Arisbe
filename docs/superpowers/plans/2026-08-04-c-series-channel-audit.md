# C-series Channel Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish, for every C-series arm whose figures have been published, whether each
channel it plays actually minted anything and whether its firing moved any figure — then leave
the check standing so a silent channel fails a test instead of printing a null.

**Architecture:** One helper module in `tests/` wraps `Unit`'s eight channel methods to count
calls against mints (`channel_calls()`) and to replace a channel with a typed no-op
(`muted()`). A standalone script under `runs/c_audit/` replays every published arm under both,
producing a calls table and an ablation diff. The same helper then decorates the three
measurement harnesses so every future run asserts its channels minted. `src/` is not touched.

**Tech Stack:** Python 3.12, `uv run pytest`, the existing C-series modules (`c_unit`,
`c_field`, `c_marks`) and their test harnesses.

## Global Constraints

- **`src/` is out of scope.** A `c_unit.py` change alters the C-series' subject matter, not its
  measurement. If the defect lives there, name it, flag the findings it taints, defer it.
- **The harnesses' bodies are not rewritten.** Task 6 adds a decorator line to each; nothing
  else about `_play`, `_play_challenge` or `_play_ask_and_challenge` changes unless Task 5's
  findings require a repair, and then only the specific defect.
- **Priors are already committed** (`9209e2d`, spec §7). Do not edit `P-A1`…`P-A6` after
  running. A refuted prior is written up as refuted.
- **The instrument lives in `tests/`, never `src/`** — same doctrine as `_cost_reading`: putting
  an observer's reading in `src/` hands a unit a faculty it does not have.
- Effect definitions are copied from `runs/d1/channel_probe.py` so the two audits are
  comparable. Any departure is named in the module docstring.
- Spec: `docs/superpowers/specs/2026-08-04-c-series-channel-audit-design.md`.
- Measured cost, so no arm needs to be skipped for time: one seed of `_play` = 0.68 s,
  `_play_challenge` = 1.4 s, `_play_ask_and_challenge` = 1.7 s at four units and 2.2 s at six.
  Eight seeds per arm ≈ 15 s; the whole count pass is a few minutes.

## File Structure

| File | Responsibility |
|---|---|
| `tests/c_channel_probe.py` (create) | The instrument: `channel_calls()`, `muted()`, `audited()`, `ChannelTally`. Not collected by pytest (no `test_` prefix). |
| `tests/test_c_channel_probe.py` (create) | The instrument's own tests — counting, muting, restoration, per-method effect definitions. |
| `runs/c_audit/audit.py` (create) | Replays every published arm: count pass, then ablation pass. Writes `CALLS.txt` and `ABLATION.txt`. |
| `runs/c_audit/CALLS.txt`, `runs/c_audit/ABLATION.txt` (generated) | The audit's artefacts of record. |
| `runs/RUN_C_AUDIT_LOG.md` (create) | The findings, read against `P-A1`…`P-A6`. |
| `tests/test_c_channels.py` (modify: 491, 1711, 2432) | One decorator line per harness; `expect_silent=` at call sites that predict a zero. |
| `tests/test_c_speaker_variance.py` (modify: 41) | `expect_silent=` if the liar arms predict a zero. |
| `CURRENT_PLAN.md`, `docs/CAPABILITY_MAP.md` (modify) | Close-out. |

---

### Task 1: The probe instrument

**Files:**
- Create: `tests/c_channel_probe.py`
- Test: `tests/test_c_channel_probe.py`

**Interfaces:**
- Consumes: `c_unit.Unit`, `c_unit.Disposition`, `c_marks.MarkBoard`, `c_field.default_spec`,
  `c_field.apertures_for`.
- Produces: `CHANNELS` (tuple of eight method names) · `ChannelTally` with `.calls: Counter`,
  `.effects: Counter`, `.extra: Counter`, `.muted: frozenset`, `.silent() -> tuple[str, ...]` ·
  `channel_calls()` context manager yielding a `ChannelTally` · `muted(*names)` context manager ·
  `audited(*, expect_silent=())` decorator · `ablating()` context manager · `_effect(name, out)`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_c_channel_probe.py`:

```python
# tests/test_c_channel_probe.py
"""The instrument's own tests. It found a dead channel in D-1 and is about to be
pointed at the C-series' published figures, so it is tested before it is trusted."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest  # noqa: E402

from c_channel_probe import (_effect, ablating, audited, channel_calls,  # noqa: E402
                             muted)
from c_field import apertures_for, default_spec  # noqa: E402
from c_marks import MarkBoard  # noqa: E402
from c_unit import Disposition, Unit  # noqa: E402

A1 = (("c", "a1"),)


def _two_units():
    spec = default_spec(seed=20260728)
    aps = apertures_for(spec, n_units=4)
    return Unit("u0", aps[0]), Unit("u1", aps[1])


def test_a_channel_that_mints_is_counted_as_a_call_and_an_effect():
    u0, _u1 = _two_units()
    u0._record({("p1", A1)}, 0)
    board = MarkBoard()
    with channel_calls() as tally:
        marks = u0.publish(board, 0)
    assert len(marks) == 1
    assert tally.calls["publish"] == 1
    assert tally.effects["publish"] == 1
    assert tally.silent() == ()


def test_a_channel_with_nothing_to_say_is_a_call_with_no_effect():
    """THE WHOLE POINT OF THE INSTRUMENT. A call that mints nothing is invisible
    to every figure a sweep prints, and this is where it becomes visible."""
    u0, _u1 = _two_units()
    board = MarkBoard()
    with channel_calls() as tally:
        assert u0.publish(board, 0) == []
    assert tally.calls["publish"] == 1
    assert tally.effects["publish"] == 0
    assert tally.silent() == ("publish",)


def test_muting_a_channel_puts_no_mark_on_the_board():
    """Replacement, not wrapping: `publish` mints onto the board as a side
    effect, so a counting wrapper would leave the channel running."""
    u0, _u1 = _two_units()
    u0._record({("p1", A1)}, 0)
    board = MarkBoard()
    with muted("publish"):
        assert u0.publish(board, 0) == []
    assert board.all_marks() == []
    assert len(u0.publish(board, 0)) == 1        # restored on exit


def test_a_muted_channel_is_not_reported_silent():
    """A channel the ablation removed on purpose is not a defect, and the two
    must not read alike."""
    u0, _u1 = _two_units()
    board = MarkBoard()
    with muted("publish"), channel_calls() as tally:
        u0.publish(board, 0)
    assert tally.calls["publish"] == 1
    assert tally.silent() == ()


def test_the_originals_are_restored_after_an_exception():
    original = Unit.publish
    with pytest.raises(RuntimeError):
        with channel_calls():
            raise RuntimeError("boom")
    assert Unit.publish is original
    with pytest.raises(RuntimeError):
        with muted("publish"):
            raise RuntimeError("boom")
    assert Unit.publish is original


def test_ask_reports_one_effect_for_a_mark_and_none_for_silence():
    assert _effect("ask", None) == 0
    assert _effect("ask", object()) == 1


def test_adopt_reports_its_boolean():
    assert _effect("adopt", True) == 1
    assert _effect("adopt", False) == 0


def test_dispose_sums_the_five_outcome_lists_and_counts_questions_apart():
    """D-1's definition, kept so the two audits are comparable: the five outcome
    lists are the effect, and the questions an inquiry publishes are reported
    beside it rather than folded in."""
    d = Disposition(suspended=[("p1", "q1")], restored_by_silence=[("p2", "q2")])
    assert _effect("dispose_challenges", d) == 2


def test_the_audited_decorator_refuses_a_silent_channel():
    board = MarkBoard()

    @audited()
    def arm():
        u0, _u1 = _two_units()
        return u0.publish(board, 0)

    with pytest.raises(AssertionError, match="publish"):
        arm()


def test_the_audited_decorator_accepts_a_declared_silence():
    board = MarkBoard()

    @audited()
    def arm():
        u0, _u1 = _two_units()
        return u0.publish(board, 0)

    assert arm(expect_silent=("publish",)) == []


def test_the_audited_decorator_stands_down_while_ablating():
    """An ablation legitimately silences downstream channels, so the standing
    assertion is suspended for the duration rather than worked around."""
    board = MarkBoard()

    @audited()
    def arm():
        u0, _u1 = _two_units()
        return u0.publish(board, 0)

    with ablating():
        assert arm() == []
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_c_channel_probe.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'c_channel_probe'`.

- [ ] **Step 3: Write the instrument**

Create `tests/c_channel_probe.py`:

```python
# tests/c_channel_probe.py
"""Count what each channel call MINTS, and replay an arm with a channel absent.

WHY THIS EXISTS. D-1 found four channels that ran hundreds of times and did
nothing — and no economic figure looked wrong while any of them ran. A call made
hundreds of times that returns an empty list every time is invisible to every
number a sweep prints. This is the instrument that makes it visible, kept
deliberately close to `runs/d1/channel_probe.py` so the two audits compare.

WHY IT LIVES IN tests/. It is an OBSERVER's reading, exactly as `_cost_reading`
is. Putting it in `src/` would hand a unit a faculty it does not have.

TWO KINDS OF DEADNESS, and the second is why counting is not enough. A channel
can mint nothing (`silent()` finds it), or it can mint plenty and change no
figure — D-1's `answer` minted 179 marks and gave byte-identical results.
`muted()` is for the second: it REPLACES a method with a typed no-op so the arm
runs with the channel genuinely absent, which a counting wrapper would not do
since `publish` and `corroborate` mint onto the board as a side effect.

NAMED LIMIT. `dispose_challenges` reports the five outcome lists as its effect,
which is D-1's definition; the questions an inquiry publishes are counted apart
as `extra["dispose_asked"]` so a disposal that only asks does not read silent.
"""

from __future__ import annotations

import contextlib
import functools
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterator, Tuple

from c_unit import Disposition, Unit

CHANNELS: Tuple[str, ...] = (
    "publish", "ask", "answer", "adopt", "challenge", "corroborate",
    "dispose_challenges", "settle_credit")

_MUTED: list = []          # the mute stack; innermost wins
_ABLATING: list = []       # non-empty while an ablation run is in progress


def _effect(name, out) -> int:
    """How many marks (or verdicts, or uptakes) one call actually produced."""
    if out is None:
        return 0
    if name == "ask":
        return 1
    if name == "adopt":
        return 1 if out else 0
    if name == "dispose_challenges":
        return (len(out.suspended) + len(out.retracted_internally)
                + len(out.retracted_by_corroboration)
                + len(out.restored_by_rebuttal)
                + len(out.restored_by_silence))
    return len(out)


@dataclass
class ChannelTally:
    calls: Counter = field(default_factory=Counter)
    effects: Counter = field(default_factory=Counter)
    extra: Counter = field(default_factory=Counter)
    muted: frozenset = frozenset()

    def silent(self) -> Tuple[str, ...]:
        """Channels called at least once that minted nothing — muting aside."""
        return tuple(sorted(n for n in CHANNELS
                            if self.calls[n] and not self.effects[n]
                            and n not in self.muted))


@contextlib.contextmanager
def channel_calls() -> Iterator[ChannelTally]:
    """Count calls and mints for the eight channel methods, restoring on exit."""
    tally = ChannelTally(muted=frozenset(_MUTED[-1]) if _MUTED else frozenset())
    originals = {n: getattr(Unit, n) for n in CHANNELS}

    def make(name, original):
        @functools.wraps(original)
        def wrapped(self, *a, **k):
            out = original(self, *a, **k)
            tally.calls[name] += 1
            tally.effects[name] += _effect(name, out)
            if name == "dispose_challenges":
                tally.extra["dispose_asked"] += len(out.asked)
            return out
        return wrapped

    for name, original in originals.items():
        setattr(Unit, name, make(name, original))
    try:
        yield tally
    finally:
        for name, original in originals.items():
            setattr(Unit, name, original)


_NOTHING = {
    "publish": list, "answer": list, "challenge": list, "corroborate": list,
    "settle_credit": list, "ask": lambda: None, "adopt": lambda: False,
    "dispose_challenges": Disposition,
}


@contextlib.contextmanager
def muted(*names: str) -> Iterator[None]:
    """Replace each named channel with a typed no-op for the duration."""
    unknown = [n for n in names if n not in CHANNELS]
    if unknown:
        raise ValueError(f"not channels: {unknown}")
    originals = {n: getattr(Unit, n) for n in names}

    def make(name):
        empty = _NOTHING[name]

        def silent(self, *a, **k):
            return empty()
        return silent

    for name in names:
        setattr(Unit, name, make(name))
    _MUTED.append(frozenset(names) | (_MUTED[-1] if _MUTED else frozenset()))
    try:
        yield
    finally:
        _MUTED.pop()
        for name, original in originals.items():
            setattr(Unit, name, original)


@contextlib.contextmanager
def ablating() -> Iterator[None]:
    """Suspend the standing assertion: an ablation silences downstream channels
    on purpose, and a guard that fired on that would only teach people to
    disable it."""
    _ABLATING.append(True)
    try:
        yield
    finally:
        _ABLATING.pop()


def audited(*, expect_silent: Tuple[str, ...] = ()):
    """Make a measurement harness assert that the channels it plays minted.

    A finding of "no effect" from a mechanism that never ran is worth nothing at
    all. Call sites where a zero is PREDICTED — a mute control, or corroboration
    in a community below its witness threshold — pass `expect_silent=(...)`, so
    a predicted zero and a defect never read alike.
    """
    def decorate(fn):
        @functools.wraps(fn)
        def wrapper(*a, **k):
            declared = set(expect_silent) | set(k.pop("expect_silent", ()))
            with channel_calls() as tally:
                out = fn(*a, **k)
            if _ABLATING:
                return out
            unexpected = [n for n in tally.silent() if n not in declared]
            assert not unexpected, (
                f"{fn.__name__}{a[:2]}: channel(s) {unexpected} were called "
                f"{[tally.calls[n] for n in unexpected]} times and minted "
                f"nothing. Either the arm is broken or the silence is expected "
                f"— if expected, declare it with expect_silent=.")
            return out
        return wrapper
    return decorate
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_c_channel_probe.py -q`
Expected: PASS, 10 tests.

- [ ] **Step 5: Verify pytest does not collect the helper**

Run: `uv run pytest tests/c_channel_probe.py -q 2>&1 | tail -3`
Expected: no tests collected (the file has no `test_` prefix and defines no test functions).

- [ ] **Step 6: Commit**

```bash
git add tests/c_channel_probe.py tests/test_c_channel_probe.py
git commit -m "The channel probe: count what a call mints, and run an arm without it

D-1's instrument generalized and given its own tests before it is trusted with
the C-series' published figures. muted() REPLACES rather than wraps, because
publish and corroborate mint onto the board as a side effect."
```

---

### Task 2: The count pass

**Files:**
- Create: `runs/c_audit/audit.py`
- Generates: `runs/c_audit/CALLS.txt`

**Interfaces:**
- Consumes: `c_channel_probe.channel_calls`, `c_channel_probe.CHANNELS`; the harnesses
  `test_c_channels._play`, `._play_challenge`, `._play_ask_and_challenge`, `.C_SEEDS`,
  `.C_ROUNDS`, `.SEEDS`, `.ROUNDS`; `test_c_speaker_variance.ONE_LIAR`, `.ALL_LIARS`;
  `c_field.CYCLIC`, `c_field.PAIRS`.
- Produces: `ARMS` (the arm inventory, consumed by Task 3) as a list of
  `Arm(name, harness, seeds, rounds, kwargs)`; `count_pass(arms) -> dict[str, ChannelTally]`.

The arm inventory is every shape whose figures have been published. Each row is copied from a
call site, so the audit measures what the gates measure:

| Arm | Harness | Call site | kwargs |
|---|---|---|---|
| `P1` | `_play` | :592 | `channel=True, stagger=2` (14 seeds, 60 rounds) |
| `P2` | `_play` | :698 | `channel=True, stagger=1` (14 seeds, 40 rounds) |
| `C1` | `_play_challenge` | :1970 | `channel=True` |
| `C2` | `_play_challenge` | :2080 | `channel=True, wrong_laws=True` |
| `C3` | `_play_challenge` | :2171 / `_witness_arm(4, CYCLIC)` | `channel=True, stagger=2, seed_laws=True, wrong_laws=True, induce=False` |
| `C4` | `_play_challenge` | `_witness_arm(4, PAIRS)` | `C3` + `n_units=4, scheme=PAIRS` |
| `C5` | `_play_challenge` | `_witness_arm(6, PAIRS)` | `C3` + `n_units=6, scheme=PAIRS` |
| `C6` | `_play_challenge` | `_witness_arm(6, PAIRS, witnesses=3)` | `C5` + `witnesses=3` |
| `C7` | `_play_challenge` | `_witness_induce_arm(6, PAIRS)` | `channel=True, n_units=6, scheme=PAIRS` |
| `C8` | `_play_challenge` | `_witness_induce_arm(6, PAIRS, witnesses=3)` | `C7` + `witnesses=3` |
| `K1` | `_play_ask_and_challenge` | :3217 | `ask=True` (4 CYCLIC) |
| `K2` | `_play_ask_and_challenge` | :3524 | `ask=False` |
| `K3` | `_play_ask_and_challenge` | :3522 | `ask=False, mute=True` |
| `K4` | `_play_ask_and_challenge` | :3136 | `ask=True, typify="prefer"` |
| `K5` | `_play_ask_and_challenge` | :3295 | `ask=True, typify="distrust"` |
| `K6` | `_play_ask_and_challenge` | :3218 | `ask=True, n_units=6, scheme=PAIRS` |
| `K7` | `_play_ask_and_challenge` | :3138 | `ask=True, typify="prefer", n_units=6, scheme=PAIRS` |
| `K8` | `_play_ask_and_challenge` | :2956 | `ask=True, window=3` (4 CYCLIC) |
| `K9` | `_play_ask_and_challenge` | :2956 | `ask=True, window=8` (4 CYCLIC) |
| `K10` | `_play_ask_and_challenge` | :2957 | `ask=True, window=8, n_units=6, scheme=PAIRS` |
| `L1` | `_play_ask_and_challenge` | `test_c_speaker_variance._arm` | `ask=True, liars=ONE_LIAR` |
| `L2` | `_play_ask_and_challenge` | `_arm` | `ask=True, typify="prefer", liars=ONE_LIAR` |
| `L3` | `_play_ask_and_challenge` | `_arm` | `ask=True, typify="prefer", liars=ALL_LIARS` |

`_witness_arm` and `_aggregate_ask` are NOT called: `_aggregate_ask` memoizes into a
module-level `_ARMS` cache, which would serve a stale result to the second pass. The audit calls
the harnesses directly, at the same seeds the aggregators use.

- [ ] **Step 1: Write the script**

Create `runs/c_audit/audit.py`:

```python
"""Did the C-series' channels mint anything when its figures were taken?

Two passes. COUNT: replay every published arm and report calls against mints per
channel. ABLATE: replay it again with each firing channel absent and diff the
figures the arm itself returns. See
docs/superpowers/specs/2026-08-04-c-series-channel-audit-design.md.

    uv run python runs/c_audit/audit.py --pass count
    uv run python runs/c_audit/audit.py --pass ablate
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Sequence

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from c_channel_probe import CHANNELS, ablating, channel_calls, muted  # noqa: E402
from c_field import CYCLIC, PAIRS                                     # noqa: E402
from test_c_channels import (C_ROUNDS, C_SEEDS, ROUNDS, SEEDS, _play,  # noqa: E402
                             _play_ask_and_challenge, _play_challenge)
from test_c_speaker_variance import ALL_LIARS, ONE_LIAR               # noqa: E402

OUT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Arm:
    name: str
    harness: Callable
    seeds: Sequence[int]
    rounds: int
    kwargs: Dict[str, Any]

    def play(self, seed):
        return self.harness(seed, self.rounds, **self.kwargs)


_C3 = dict(channel=True, stagger=2, seed_laws=True, wrong_laws=True,
           induce=False)

ARMS = [
    Arm("P1", _play, SEEDS, ROUNDS, dict(channel=True, stagger=2)),
    Arm("P2", _play, SEEDS, 40, dict(channel=True, stagger=1)),
    Arm("C1", _play_challenge, C_SEEDS, C_ROUNDS, dict(channel=True)),
    Arm("C2", _play_challenge, C_SEEDS, C_ROUNDS,
        dict(channel=True, wrong_laws=True)),
    Arm("C3", _play_challenge, C_SEEDS, C_ROUNDS, dict(_C3)),
    Arm("C4", _play_challenge, C_SEEDS, C_ROUNDS,
        dict(_C3, n_units=4, scheme=PAIRS)),
    Arm("C5", _play_challenge, C_SEEDS, C_ROUNDS,
        dict(_C3, n_units=6, scheme=PAIRS)),
    Arm("C6", _play_challenge, C_SEEDS, C_ROUNDS,
        dict(_C3, n_units=6, scheme=PAIRS, witnesses=3)),
    Arm("C7", _play_challenge, C_SEEDS, C_ROUNDS,
        dict(channel=True, n_units=6, scheme=PAIRS)),
    Arm("C8", _play_challenge, C_SEEDS, C_ROUNDS,
        dict(channel=True, n_units=6, scheme=PAIRS, witnesses=3)),
    Arm("K1", _play_ask_and_challenge, C_SEEDS, C_ROUNDS, dict(ask=True)),
    Arm("K2", _play_ask_and_challenge, C_SEEDS, C_ROUNDS, dict(ask=False)),
    Arm("K3", _play_ask_and_challenge, C_SEEDS, C_ROUNDS,
        dict(ask=False, mute=True)),
    Arm("K4", _play_ask_and_challenge, C_SEEDS, C_ROUNDS,
        dict(ask=True, typify="prefer")),
    Arm("K5", _play_ask_and_challenge, C_SEEDS, C_ROUNDS,
        dict(ask=True, typify="distrust")),
    Arm("K6", _play_ask_and_challenge, C_SEEDS, C_ROUNDS,
        dict(ask=True, n_units=6, scheme=PAIRS)),
    Arm("K7", _play_ask_and_challenge, C_SEEDS, C_ROUNDS,
        dict(ask=True, typify="prefer", n_units=6, scheme=PAIRS)),
    Arm("K8", _play_ask_and_challenge, C_SEEDS, C_ROUNDS,
        dict(ask=True, window=3)),
    Arm("K9", _play_ask_and_challenge, C_SEEDS, C_ROUNDS,
        dict(ask=True, window=8)),
    Arm("K10", _play_ask_and_challenge, C_SEEDS, C_ROUNDS,
        dict(ask=True, window=8, n_units=6, scheme=PAIRS)),
    Arm("L1", _play_ask_and_challenge, C_SEEDS, C_ROUNDS,
        dict(ask=True, liars=ONE_LIAR)),
    Arm("L2", _play_ask_and_challenge, C_SEEDS, C_ROUNDS,
        dict(ask=True, typify="prefer", liars=ONE_LIAR)),
    Arm("L3", _play_ask_and_challenge, C_SEEDS, C_ROUNDS,
        dict(ask=True, typify="prefer", liars=ALL_LIARS)),
]

BY_NAME = {a.name: a for a in ARMS}


def count_pass(arms, out=sys.stdout):
    """Calls against mints, aggregated over the arm's own seeds."""
    tallies = {}
    for arm in arms:
        with channel_calls() as tally:
            for seed in arm.seeds:
                arm.play(seed)
        tallies[arm.name] = tally
        print(f"\n{arm.name}  {arm.harness.__name__}  "
              f"{len(arm.seeds)} seeds x {arm.rounds} rounds  {arm.kwargs}",
              file=out)
        for name in CHANNELS:
            if not tally.calls[name]:
                continue
            verdict = "SILENT" if not tally.effects[name] else ""
            print(f"   {name:<20} calls={tally.calls[name]:>7}  "
                  f"mints={tally.effects[name]:>7}  {verdict}", file=out)
        if tally.extra["dispose_asked"]:
            print(f"   {'(dispose asked)':<20} "
                  f"{tally.extra['dispose_asked']:>26}", file=out)
        silent = tally.silent()
        print(f"   -> silent: {silent if silent else 'none'}", file=out)
    return tallies


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pass", dest="which", choices=["count", "ablate"],
                   default="count")
    p.add_argument("--arms", nargs="*", default=None)
    args = p.parse_args()
    arms = [BY_NAME[n] for n in args.arms] if args.arms else ARMS
    if args.which == "count":
        path = OUT / "CALLS.txt"
        with path.open("w") as fh:
            count_pass(arms, out=fh)
        count_pass(arms)
        print(f"\nwritten: {path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke it on one cheap arm**

Run: `uv run python runs/c_audit/audit.py --pass count --arms C3`
Expected: a table with non-zero `calls` for `publish`, `challenge`, `corroborate`,
`dispose_challenges`, and a `-> silent:` line. Do not interpret it yet; confirm only that the
script runs and the counts are non-zero somewhere.

- [ ] **Step 3: Run the full count pass**

Run: `uv run python runs/c_audit/audit.py --pass count 2>&1 | tail -40`
Expected: 23 arm blocks, `runs/c_audit/CALLS.txt` written. Takes a few minutes.

- [ ] **Step 4: Read the table against `P-A1`, `P-A2`, `P-A3`**

Write down, in the commit message, for each of the three: held / refuted / not reached, with
the numbers. Do not adjust the priors. Specifically check:
- `settle_credit` mints in K1/K4/K6/K7 (`P-A1`'s precondition),
- `corroborate` mints in C5 and is zero in C3 (`P-A2`),
- `answer` mints in P1 and in K1 (`P-A3`).

- [ ] **Step 5: Commit**

```bash
git add runs/c_audit/audit.py runs/c_audit/CALLS.txt
git commit -m "The C-series count pass: calls against mints in 23 published arms

<one line per prior: what the table says>"
```

---

### Task 3: The ablation pass

**Files:**
- Modify: `runs/c_audit/audit.py`
- Generates: `runs/c_audit/ABLATION.txt`

**Interfaces:**
- Consumes: `ARMS`, `count_pass` from Task 2; `muted`, `ablating`.
- Produces: `figures(arm, result) -> dict[str, int]` (the arm's own comparable numbers) and
  `ablate_pass(arms, tallies)`.

Each harness returns something different, so the diff needs one reader per harness. Every number
below is one the harness already computes; none is invented.

- [ ] **Step 1: Add the figure readers and the ablation pass**

Insert into `runs/c_audit/audit.py` above `main()`:

```python
def figures(arm, result) -> Dict[str, int]:
    """The arm's OWN numbers, reduced to a comparable dict of ints.

    Nothing here is computed by the audit: every value is one the harness
    already returns, or a count of something it returns.
    """
    if arm.harness is _play:
        units, _board, answers, uptakes = result
        return dict(answers=answers, uptakes=uptakes,
                    hits=sum(u.ledger.hits for u in units),
                    misses=sum(u.ledger.misses for u in units),
                    abstentions=sum(u.ledger.abstentions for u in units),
                    laws=sum(len(u.laws) for u in units))
    if arm.harness is _play_challenge:
        _spec, units, board, raised, events, tally = result
        out = {f"disp_{k}": v for k, v in tally.items()}
        out.update(raised=raised, events=len(events),
                   marks=len(board.all_marks()),
                   laws=sum(len(u.laws) for u in units),
                   suspended=sum(len(u.suspended) for u in units))
        return out
    # _play_ask_and_challenge: the tally dict, minus the non-scalar entries.
    skip = {"consult", "prefs", "could", "voices", "voices_by_rel", "units"}
    return {k: v for k, v in result.items() if k not in skip}


def ablate_pass(arms, tallies, out=sys.stdout):
    """For each channel that FIRED in an arm, replay the arm without it."""
    for arm in arms:
        tally = tallies[arm.name]
        base = {}
        for seed in arm.seeds:
            for k, v in figures(arm, arm.play(seed)).items():
                base[k] = base.get(k, 0) + v
        firing = [c for c in CHANNELS if tally.effects[c]]
        print(f"\n{arm.name}  fired: {firing}", file=out)
        for channel in firing:
            got = {}
            with ablating(), muted(channel):
                for seed in arm.seeds:
                    for k, v in figures(arm, arm.play(seed)).items():
                        got[k] = got.get(k, 0) + v
            moved = {k: (base[k], got[k]) for k in base if base[k] != got.get(k)}
            if not moved:
                print(f"   -{channel:<18} INERT: not one figure moved",
                      file=out)
            else:
                shown = sorted(moved.items(),
                               key=lambda kv: -abs(kv[1][0] - kv[1][1]))[:8]
                print(f"   -{channel:<18} moved {len(moved)}/{len(base)}: "
                      + ", ".join(f"{k} {a}->{b}" for k, (a, b) in shown),
                      file=out)
```

And extend `main()`:

```python
    else:
        tallies = count_pass(arms, out=open(OUT / "CALLS.txt", "w"))
        path = OUT / "ABLATION.txt"
        with path.open("w") as fh:
            ablate_pass(arms, tallies, out=fh)
        print(path.read_text())
        print(f"\nwritten: {path}")
```

- [ ] **Step 2: Smoke it on one arm**

Run: `uv run python runs/c_audit/audit.py --pass ablate --arms P1`
Expected: one block naming the channels that fired in `P1`, and for each either `INERT` or a
list of moved figures. `answer` should move figures here — `_play` has no other fact channel.

- [ ] **Step 3: Run the full ablation pass**

Run: `uv run python runs/c_audit/audit.py --pass ablate 2>&1 | tail -60`
Expected: `runs/c_audit/ABLATION.txt` written, one block per arm.

- [ ] **Step 4: Check `P-A4` and `P-A5` explicitly**

`P-A4`: compare K1 with `answer` muted against arm K2 (`ask=False`) in `CALLS.txt`/the K2 base
figures — the prediction is that muting `answer` under `ask=True` moves K1's figures toward K2's.
Run `uv run python runs/c_audit/audit.py --pass ablate --arms K1 K2` and read the two blocks
together.

`P-A5`: in K1, muting `settle_credit` should move nothing (the untargeted control does not read
`peers`); in K4 it should move the preference figures. Run
`uv run python runs/c_audit/audit.py --pass ablate --arms K1 K4`.

- [ ] **Step 5: Commit**

```bash
git add runs/c_audit/audit.py runs/c_audit/ABLATION.txt
git commit -m "The C-series ablation pass: which firings actually moved a figure

<one line per prior P-A4, P-A5: what moved and what did not>"
```

---

### Task 4: The log, read against the priors

**Files:**
- Create: `runs/RUN_C_AUDIT_LOG.md`

- [ ] **Step 1: Classify every channel in every arm**

From `CALLS.txt` and `ABLATION.txt`, build the classification table — one row per (arm, channel)
that made a call: **dead** (mints 0) · **live but inert** (mints, ablation moves nothing) ·
**live and consequential** (ablation moves figures, with the largest movers named).

- [ ] **Step 2: Scan the harnesses for unchecked liveness claims**

Run: `grep -n "mechanism-is-exercised\|actually happened\|the channel carried\|assert answers\|assert agg\[" tests/test_c_channels.py tests/test_c_speaker_variance.py`

For each measurement gate, record whether its docstring **asserts** a channel fired or the test
**checks** it. D-1's lesson — a docstring that asserts a property instead of checking it is how
a defect survives four fix rounds — is what this list is for. Name the gates that assert without
checking; they become Task 6's targets.

- [ ] **Step 3: Write the log**

Create `runs/RUN_C_AUDIT_LOG.md` with:
1. **What was audited** — the 23 arms, the two passes, the instrument, and the pointer to the
   spec and to `9209e2d` (priors committed before the run).
2. **The classification table** from Step 1.
3. **`P-A1`…`P-A6`, each read in its own words** — held / refuted / not reached, with the
   numbers that decide it, in the spec's stated failure-condition terms.
4. **Which published findings this touches** — for every dead or inert channel, the specific
   C-series claim that rested on it, quoted from the gate's docstring, and whether it survives.
5. **Unchecked liveness claims** from Step 2.
6. **What is deferred to `src/`**, per the spec's §9 boundary, with the findings each defect
   taints.

Write it in the run-log voice the other `runs/*_LOG.md` files use: figures first, no smoothing,
a refuted prior stated as refuted.

- [ ] **Step 4: Commit**

```bash
git add runs/RUN_C_AUDIT_LOG.md
git commit -m "RUN_C_AUDIT: the C-series' channels read against P-A1..P-A6

<the headline finding in one line>"
```

---

### Task 5: Test-side repairs (conditional)

**Files:**
- Modify: `tests/test_c_channels.py` and/or `tests/test_c_speaker_variance.py` — only the
  specific defect.
- Modify: `runs/RUN_C_AUDIT_LOG.md`

**Run this task only if Task 4 found a defect confined to a harness** — a phase order, an
uncalled method, an arm that never reaches the state it claims to measure. If every finding is
in `src/`, skip to Task 6 and record the deferral.

- [ ] **Step 1: Write the failing test for the defect**

In `tests/test_c_channels.py`, beside the harness, write a test that fails **because of the
defect** — the shape D-1 used: assert the channel mints under the arm's own conditions.

```python
def test_the_<channel>_channel_mints_in_the_arm_that_measures_it():
    """A finding of "no effect" from a mechanism that never ran is worth
    nothing. <name what the audit found>."""
    with channel_calls() as tally:
        _play_...(1, C_ROUNDS, ...)
    assert tally.effects["<channel>"] > 0, tally.calls["<channel>"]
```

- [ ] **Step 2: Run it and watch it fail**

Run: `uv run pytest tests/test_c_channels.py::test_the_<channel>_channel_mints_in_the_arm_that_measures_it -q`
Expected: FAIL, with the call count in the message and the mint count zero.

- [ ] **Step 3: Repair the harness**

Make the smallest change that makes the channel mint. **Do not touch `src/`.** If the repair
cannot be made without a `c_unit.py` change, revert the attempt, delete the test, and record the
defect as deferred in the log instead.

- [ ] **Step 4: Re-run the affected arms and the new test**

Run: `uv run pytest tests/test_c_channels.py -q -k "<the affected gates>"`
Expected: PASS, with new figures.

- [ ] **Step 5: Rewrite the figures the repair moved**

Every docstring table in the affected gates is now wrong. Rewrite each from the new run, and add
one line naming the repair and the date, in the file's existing voice. D-1's precedent: the
pre-fix artefacts were deleted rather than left beside the new ones.

- [ ] **Step 6: Re-run the audit on the repaired arms**

Run: `uv run python runs/c_audit/audit.py --pass ablate --arms <the affected arms>`
Then update `runs/RUN_C_AUDIT_LOG.md` with the post-repair reading, marked as such.

- [ ] **Step 7: Commit**

```bash
git add tests/ runs/
git commit -m "C-series: <the channel> was <dead|inert>, repaired and the arms re-run

<what changed in the figures, stated plainly>"
```

---

### Task 6: The standing discipline

**Files:**
- Modify: `tests/test_c_channels.py:491, 1711, 2432` (one decorator line each) and the call
  sites that predict a zero.
- Modify: `tests/test_c_speaker_variance.py:41` if its arms predict a zero.
- Test: `tests/test_c_channel_probe.py` (the bite demonstration).

**Interfaces:**
- Consumes: `c_channel_probe.audited`, `c_channel_probe.muted`.
- Produces: the three harnesses now accept `expect_silent=(...)` as a keyword and refuse an
  undeclared silent channel.

- [ ] **Step 1: Decorate the three harnesses**

At the top of `tests/test_c_channels.py`, after the existing imports:

```python
from c_channel_probe import audited, channel_calls  # noqa: E402
```

`tests/test_c_channels.py` imports its C-series modules bare (pytest's `pythonpath` covers
`src`), so add the tests directory to `sys.path` the way `test_c_speaker_variance.py` already
does, above the imports:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
```

Then decorate each harness, with the silences its own parameters make legitimate declared in the
decorator rather than at every call site:

```python
@audited()
def _play(seed, rounds, *, channel, stagger):
```

```python
@audited()
def _play_challenge(seed, rounds, *, channel, stagger=1, seed_laws=False, ...):
```

```python
@audited()
def _play_ask_and_challenge(seed, rounds, *, ask, stagger=2, ...):
```

- [ ] **Step 2: Run the C-series suite and let it name every legitimate silence**

Run: `uv run pytest tests/test_c_channels.py tests/test_c_speaker_variance.py -q -x 2>&1 | tail -30`
Expected: FAILURES naming channels and arms. Each one is either a legitimate silence (the
`channel=False` control, the `mute=True` arm, `ask=False`, corroboration below its witness
threshold) or a finding Task 4 already recorded.

- [ ] **Step 3: Declare each legitimate silence at its call site**

For each failure that is a *predicted* zero, pass it explicitly, e.g.:

```python
        mute, *_ = _play(seed, ROUNDS, channel=False, stagger=2,
                         expect_silent=("ask", "answer", "adopt"))
```

```python
        _s, mute, _b, _r, _e, _t = _play_challenge(
            seed, C_ROUNDS, channel=False,
            expect_silent=("challenge", "corroborate", "dispose_challenges"))
```

```python
    four_mute = _aggregate_ask(4, CYCLIC, ask=False, mute=True, keys=_GATE_KEYS)
    # inside _aggregate_ask, thread expect_silent through to the harness
```

Where a control silences a channel by construction, add a one-line comment saying **why the zero
is predicted** — the point of the allowlist is that a predicted zero and a defect never read
alike. For `_aggregate_ask`, add an `expect_silent=()` parameter, include it in the `arm` cache
key, and pass it through to `_play_ask_and_challenge`.

- [ ] **Step 4: Demonstrate the guard bites**

Add to `tests/test_c_channel_probe.py`:

```python
def test_the_guard_bites_on_a_real_harness():
    """The guard is verified by muting a channel the arm depends on and watching
    the arm refuse to report. A guard nobody has seen fail is a guard nobody
    knows the shape of — D-1's mortality guard passed a fully installed TTL."""
    from test_c_channels import _play

    with muted("answer"):
        with pytest.raises(AssertionError, match="answer"):
            _play(1, 10, channel=True, stagger=2)
```

Run: `uv run pytest tests/test_c_channel_probe.py -q`
Expected: PASS. (Note `muted()` alone does not suspend the guard — only `ablating()` does, which
is exactly what makes this demonstration possible.)

- [ ] **Step 5: Run the whole C-series suite green**

Run: `uv run pytest tests/test_c_channels.py tests/test_c_speaker_variance.py tests/test_c_unit.py tests/test_c_field.py tests/test_c_marks.py tests/test_c_membrane.py tests/test_c_stage_gates.py tests/test_c_use.py tests/test_c_channel_probe.py -q 2>&1 | tail -5`
Expected: all pass. Record the count and the wall time.

- [ ] **Step 6: Commit**

```bash
git add tests/
git commit -m "Every C-series arm now asserts its channels minted

Generalizes the assertion _play's gate already carried to all three harnesses.
A predicted zero is declared with expect_silent= and says why; anything else
fails the arm instead of printing a null. Demonstrated by muting answer and
watching the arm refuse to report."
```

---

### Task 7: Close-out

**Files:**
- Modify: `CURRENT_PLAN.md` (the `▶▶▶ NEXT SESSION` block and a new dated arc entry)
- Modify: `docs/CAPABILITY_MAP.md` (the C-series row)
- Modify: `docs/superpowers/plans/2026-08-04-c-series-channel-audit.md` (check the boxes)

- [ ] **Step 1: Write the arc entry**

At the top of `CURRENT_PLAN.md`, in the house style: what was audited, the headline finding,
each prior's verdict in a line, what was repaired and what was deferred to `src/`, and the state
at close (test counts, artefact paths).

- [ ] **Step 2: Re-head the next-session block**

Replace the current `▶▶▶ NEXT SESSION` block. If findings invalidated published figures, the
next session's first item is whatever the log says needs re-running or re-deciding; otherwise it
is the D-series list the current block already carries (`P-D7`'s coupling, `whom_to_ask`'s
missing consumer, D-1b / D-2 / D-3), with the audit's result recorded as the reason those may
now proceed on the C-series' figures.

- [ ] **Step 3: Update `CAPABILITY_MAP.md`**

Add the standing discipline to the C-series row: every arm asserts its channels minted, the
instrument is `tests/c_channel_probe.py`, the audit of record is `runs/RUN_C_AUDIT_LOG.md`.

- [ ] **Step 4: Run the full suite**

Run: `uv run pytest tests/ -q 2>&1 | tail -5`
Expected: no new failures against the pre-audit baseline. Record the numbers.

- [ ] **Step 5: Commit**

```bash
git add CURRENT_PLAN.md docs/ runs/
git commit -m "Plan: the C-series channel audit, and what it found

<headline>"
```

---

## Self-Review

**Spec coverage.** §2's two-class classification → Tasks 3–4. §3's arm inventory → Task 2's
table (23 arms; `_arm` appears as L1–L3, its three configurations). §4's instrument → Task 1.
§5's audit run → Tasks 2–3. §6's standing discipline → Task 6, including the bite demonstration
and the docstring scan (Task 4 Step 2). §7's priors → Task 2 Step 4, Task 3 Step 4, Task 4
Step 3. §8's six success criteria → Tasks 2–7. §9's repair boundary → Task 5's Step 3 escape
hatch and Task 4's deferral section. §10's limits → recorded in the instrument's docstring and
the log. §11's cost → the measured figures in Global Constraints, which are ~30× cheaper than
the spec's estimate.

**Placeholders.** The `<...>` marks in Tasks 4–7 commit messages and in Task 5 are
findings-dependent by construction — the audit has not run, so the numbers do not exist yet.
Every step that can be written concretely is.

**Type consistency.** `channel_calls()` yields `ChannelTally` (`.calls`, `.effects`, `.extra`,
`.muted`, `.silent()`), used under those names in Tasks 2, 3, 5 and 6. `muted(*names)` and
`ablating()` take no keyword arguments anywhere they are called. `audited(*, expect_silent=())`
returns a decorator whose wrapper pops `expect_silent` from the call's kwargs — matching the
call sites in Task 6 Step 3. `figures(arm, result)` returns `dict[str, int]` and is called only
inside `ablate_pass`. `Arm.play(seed)` is the only place a harness is invoked in the script.
