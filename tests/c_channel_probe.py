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
