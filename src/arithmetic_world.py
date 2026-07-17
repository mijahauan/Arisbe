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


# --------------------------------------------------------------------------- #
# The socket — a Proposer whose next item is chosen by the attention layer.    #
# World-agnostic in shape: the vault stage swaps the world, keeps the feed.    #
# --------------------------------------------------------------------------- #
import hashlib                                        # noqa: E402

from attention_economy import AttentionEconomy, Want  # noqa: E402
from egif_parser_dau import parse_egif                # noqa: E402
from eg_navigation import area_of, child_cuts         # noqa: E402
from world_scroll import m_view                       # noqa: E402


def _labels_of(g, eid):
    """ν sequence → vertex labels (None for generics) — the idiom
    ``ContradictionAgent``/``_labels`` use in agon_evolution.py, copied so the
    feed's reading of standing atoms matches the panel's."""
    return tuple(g.get_vertex(v).label for v in g.nu.get(eid, ()))


def _model_signature(model) -> tuple:
    """(frozenset of sheet atoms, count of sheet cuts) via m_view — the feed's only
    lawful window onto what the loop did with its proposals."""
    g = m_view(model)
    atoms = frozenset(
        (g.rel[e.id], _labels_of(g, e.id))
        for e in g.E
        if e.id in g.rel and area_of(g, e.id) == g.sheet
    )
    ncuts = len(child_cuts(g, g.sheet))
    return (atoms, ncuts)


def fifo_chooser(economy: AttentionEconomy, k: int, round_idx: int):
    ws = sorted(economy.wants(), key=lambda w: (w.created_round, w.kind, repr(w.key)))
    chosen = ws[:k]
    for w in chosen:
        w.attempts += 1
    return chosen


def scatter_chooser(economy: AttentionEconomy, k: int, round_idx: int):
    """The deterministic 'random' arm: order by a stable digest of (key, round) —
    no RNG, and no ``hash()`` (salted per-process, so it would vary run to run)."""
    def _digest(key) -> int:
        h = hashlib.sha1(f"{key}{round_idx}".encode()).hexdigest()[:8]
        return int(h, 16) % 997

    ws = sorted(economy.wants(), key=lambda w: (_digest(repr(w.key)), repr(w.key)))
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
        self._lattice = confirm_lattice
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

    def _refill_extends(self, round_idx: int):
        outstanding = sum(1 for w in self._economy.wants() if w.kind == "extend")
        n = self._extend_next
        while outstanding < 3:
            if n not in self._world.probed and n not in FERMATS:
                if self._economy.register(Want(
                        kind="extend", key=("extend", n), payload=n,
                        cost=self._world.probe_cost(n), created_round=round_idx)):
                    outstanding += 1
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
