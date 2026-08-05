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

TWO MORE, ABOUT `audited()` ITSELF. Its guard is a bare `assert`, so `python -O`
strips it and every arm reports as it did before Task 6 — the discipline is only
standing under an unoptimized interpreter. And `functools.wraps` leaves
`__wrapped__` on every decorated harness, which is a DELIBERATE bypass rather
than an oversight: `test_the_corroborate_declarations_still_have_something_to_
declare` uses it to re-decorate a harness with its allowlist removed, which is
the only way to watch a channel an allowlist is covering.
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
_DECLARED: list = []       # one slot per active audit; None until declared


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


def declares(*names: str) -> None:
    """Say, from inside a harness, which channels THIS configuration plays.

    THE RULE IS R3 OF THE TENABILITY ASSESSMENT (2026-08-05 §8b): *an arm
    declares the channels it plays.* It closes the first of the two blind spots
    `RUN_C_AUDIT_LOG.md` names in the guard installed beside it — `silent()`
    requires `calls[n] > 0`, so **a channel nobody invokes reads clean**, which
    is D-1's own defect (4): `settle_credit` was never called, `Unit.peers` was
    empty everywhere, and `P-D4` had no instrument at all while every figure the
    sweep printed looked healthy.

    WHY IT IS SAID HERE AND NOT ON THE DECORATOR. Which channels an arm plays is
    a function of its ARGUMENTS — `_play(channel=False)` plays none of the three
    it otherwise plays, `_play_ask_and_challenge(mute=True)` skips five — so a
    static per-harness list would either fire on legitimate configurations or be
    widened until it asserted nothing. The declaration belongs where the
    configuration is known, which is inside the body.

    An empty declaration is a real declaration: a mute control that plays
    nothing says `declares()` and passes. Saying nothing at all is what fails.

    A no-op when no audit is active, so calling a harness through `__wrapped__`
    still works — the deliberate bypass this module's header records.
    """
    unknown = [n for n in names if n not in CHANNELS]
    if unknown:
        raise ValueError(f"not channels: {unknown}")
    if _DECLARED:
        _DECLARED[-1] = frozenset(names)


def audited(*, expect_silent: Tuple[str, ...] = ()):
    """Make a measurement harness assert that the channels it plays ran and minted.

    A finding of "no effect" from a mechanism that never ran is worth nothing at
    all. Three ways that can happen, and this guard now catches two of them:

    - **called and minted nothing** — the original check. Call sites where a
      zero is PREDICTED (a mute control, or corroboration in a community below
      its witness threshold) pass `expect_silent=(...)`, so a predicted zero and
      a defect never read alike.
    - **declared and never called** — D-1's defect (4), added 2026-08-05 with
      `declares()`. A harness must say what it plays; a channel it names that
      logged no calls fails the arm.
    - **called and never declared** — the same check from the other side, which
      is what keeps a declaration from being narrowed until it covers nothing.

    The third kind of deadness, LIVE-BUT-INERT (`Unit.answer`: 668 mints, no
    figure moved), is **still not caught here and cannot be** — it needs the
    ablation pass, which costs about 45 minutes and cannot stand in a suite.
    R1 of the same assessment is the discipline that covers it: no sentence
    credits a mechanism for a figure unless a muted arm moved that figure.
    """
    def decorate(fn):
        @functools.wraps(fn)
        def wrapper(*a, **k):
            declared = set(expect_silent) | set(k.pop("expect_silent", ()))
            _DECLARED.append(None)
            try:
                with channel_calls() as tally:
                    out = fn(*a, **k)
            finally:
                played = _DECLARED.pop()
            if _ABLATING:
                return out
            where = f"{fn.__name__}{a[:2]}"
            assert played is not None, (
                f"{where}: this harness declared no channels. Call "
                f"`declares(...)` in its body with the channels this "
                f"configuration plays — `declares()` if it plays none.")
            # THE ORDER IS THE DIAGNOSIS, AND IT WAS FOUND BY RUNNING (2026-08-05).
            # A dead channel STARVES the ones downstream of it: with `answer`
            # returning nothing, `_play` finds no reply on the board and never
            # calls `adopt` at all. Checked never-called-first, the arm reports
            # "adopt never ran" — the symptom — and the cause goes unnamed. So
            # the silence check runs first and the starvation check second.
            unexpected = [n for n in tally.silent() if n not in declared]
            assert not unexpected, (
                f"{where}: channel(s) {unexpected} were called "
                f"{[tally.calls[n] for n in unexpected]} times and minted "
                f"nothing. Either the arm is broken or the silence is expected "
                f"— if expected, declare it with expect_silent=.")
            never_called = sorted(n for n in played if not tally.calls[n])
            assert not never_called, (
                f"{where}: channel(s) {never_called} were declared and never "
                f"called. A mechanism that never ran cannot have had an effect, "
                f"and no figure this arm prints would show it.")
            undeclared = sorted(n for n in CHANNELS
                                if tally.calls[n] and n not in played)
            assert not undeclared, (
                f"{where}: channel(s) {undeclared} ran "
                f"{[tally.calls[n] for n in undeclared]} times undeclared. "
                f"Add them to this configuration's `declares(...)`.")
            return out
        return wrapper
    return decorate
