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

# The discriminating-world false law (Examination IV, panel B, 3(d)): unlike
# FERMAT_LAW its counterexample is NOT pre-labeled with a severity-8 hunt want
# anywhere in the feed — reaching n=9 (the first odd perfect square) is only
# possible through the severity-1.0 confirm/extend probes every world already
# runs. This is what makes the discriminating-world arm actually discriminate
# "the economy learns where yield is" from "the economy obeys a hand-authored
# label" (panel B, Suspect 3).
SQUARE_LAW = '~[ (square *x) ~[ (even x) ] ]'

_KNUTH = 2654435761  # Knuth's multiplicative-hash constant — the coin's grist


class ArithmeticWorld:
    def __init__(self, *, range_cap: int = 200, deny_odd_squares: bool = False):
        self._range_cap = range_cap
        self.probed: set[int] = set()
        self.dropped = 0
        # Opt-in, default off: mirrors the FERMATS composite-denial treatment
        # below but for SQUARE_LAW's counterexample — an odd perfect square
        # carries the *denial* of evenness, the world resolving the law's own
        # instance (``_refuted_law`` in agon_evolution.py needs the negation
        # scribed in the very proposal that carries the positive body atom;
        # it never infers it from ``(odd n)`` alone). Off by default so every
        # existing arm/world/test is bit-identical.
        self._deny_odd_squares = deny_odd_squares

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
        if self._deny_odd_squares and n % 2 == 1 and math.isqrt(n) ** 2 == n:
            parts.append(f'~[ (even {q}) ]')
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


# --------------------------------------------------------------------------- #
# The socket — a Proposer whose next item is chosen by the attention layer.    #
# The generic drain-refill mechanics (AttentionEconomy + the chooser/journal   #
# pattern + the round loop) live in probe_feed.ProbeDirectedFeedBase; this     #
# feed supplies only the arithmetic-specific seeding/refill/dispatch.          #
# --------------------------------------------------------------------------- #
from attention_economy import AttentionEconomy, Want  # noqa: E402
from probe_feed import ProbeDirectedFeedBase           # noqa: E402


class ProbeDirectedFeed(ProbeDirectedFeedBase):
    """agon_evolution.Proposer: one EGIF per propose(); probes chosen by attention."""

    persistent_kinds = frozenset({"confirm"})   # confirms persist — the cheap trap

    def __init__(self, world: ArithmeticWorld, economy: AttentionEconomy, *,
                 chooser=None, probe_budget: int = 1, laws=(FERMAT_LAW,),
                 confirm_lattice: int = 60, musement: bool = True, journal=None,
                 purse: Optional[float] = None):
        super().__init__(economy, chooser=chooser, probe_budget=probe_budget,
                          journal=journal, purse=purse)
        self._world = world
        self._laws = tuple(laws)
        self._lattice = confirm_lattice
        self._musement = musement
        self._extend_next = 0

    # -- intake ---------------------------------------------------------------
    def _seed(self, round_idx: int):
        for n in range(0, self._lattice):
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

    def _refill(self, round_idx: int):
        outstanding = sum(1 for w in self._economy.wants() if w.kind == "extend")
        n = self._extend_next
        for _ in range(64):                      # bounded scan — never spins
            if outstanding >= 3:
                break
            if n not in self._world.probed and n not in FERMATS:
                before = self._economy.dropped
                if self._economy.register(Want(
                        kind="extend", key=("extend", n), payload=n,
                        cost=self._world.probe_cost(n), created_round=round_idx)):
                    outstanding += 1
                elif self._economy.dropped > before:
                    break                        # pool at cap — stop; the drop is counted
            n += 1
        self._extend_next = n

    # -- emission dispatch ------------------------------------------------------
    def _execute(self, w: Want):
        if w.kind in ("extend", "confirm"):
            return self._world.atoms_for(w.payload)
        elif w.kind == "hunt":
            _, n = w.payload
            return self._world.atoms_for(n)
        elif w.kind == "musement":
            return w.payload[1]
        else:                      # docket/frontier kinds: payload is EGIF-ish
            return w.payload if isinstance(w.payload, str) else ""


# Stable import surface for the rung-1 tests (moved into probe_feed.py).
from probe_feed import fifo_chooser, scatter_chooser, replay_choices, _model_signature  # noqa: F401,E402
