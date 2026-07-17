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
