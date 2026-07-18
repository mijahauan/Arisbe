"""The probe-feed socket base — the generic mechanics every world's feed shares
(vault-cycle Task 1; extracted from the rung-1 arithmetic feed per the final
review's carry list). Subclasses supply _seed/_refill/_execute; the base owns
the drain-refill propose loop, model-delta yield reading, the journal, the
baseline choosers, and the count-or-refuse dispatch rule: a chosen want the
feed cannot voice is refused and COUNTED (self.refused), never silently
dropped."""
from __future__ import annotations

import hashlib
from typing import List, Optional

from attention_economy import AttentionEconomy, Want
from eg_navigation import area_of, child_cuts
from world_scroll import m_view


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


def replay_choices(journal):
    """The determinism canary's reading of a journal: the choice sequence alone."""
    return [j["chosen"] for j in journal]


class ProbeDirectedFeedBase:
    """agon_evolution.Proposer: one EGIF per propose(); the generic drain-refill
    loop shared by every world's feed. Subclasses implement _seed/_refill/_execute
    and may set persistent_kinds (wants that legitimately re-propose without
    settling — e.g. arithmetic's ``confirm`` re-probes)."""

    persistent_kinds: frozenset = frozenset()

    def __init__(self, economy: AttentionEconomy, *, chooser=None,
                 probe_budget: int = 1, journal=None):
        self._economy = economy
        self._chooser = chooser
        self._budget = probe_budget
        self._queue: List[str] = []
        self._last_chosen: List[Want] = []
        self._prev_sig = None
        self._seeded = False
        self.refused = 0            # count-or-refuse: an unvoiceable want, counted not dropped
        self.journal: list = [] if journal is None else journal

    # -- world hooks ---------------------------------------------------------
    def _seed(self, round_idx: int) -> None: ...
    def _refill(self, round_idx: int) -> None: ...
    def _execute(self, want: Want) -> Optional[str]: ...

    # -- the round loop -------------------------------------------------------
    def propose(self, model, round_idx: int):
        sig = _model_signature(model)
        if self._prev_sig is not None and self._last_chosen:
            prev_atoms, prev_cuts = self._prev_sig
            atoms, cuts = sig
            # round-granular: the full delta credits every chosen want's kind
            events = len(atoms ^ prev_atoms) + abs(cuts - prev_cuts)
            self._economy.observe(round_idx, [(w, events) for w in self._last_chosen])
            self._last_chosen = []
        self._prev_sig = sig

        if not self._queue:
            if not self._seeded:
                self._seeded = True
                self._seed(round_idx)
            self._refill(round_idx)
            choose = self._chooser or (lambda e, k, r: e.choose(k, r))
            chosen = choose(self._economy, self._budget, round_idx)
            self._last_chosen = list(chosen)
            self.journal.append({
                "round": round_idx,
                "chosen": [(w.kind, repr(w.key)) for w in chosen],
                "snapshot": self._economy.snapshot(),
            })
            for w in chosen:
                egif = self._execute(w)
                if egif:
                    self._queue.append(egif)
                elif w.kind not in self.persistent_kinds:
                    self.refused += 1
                if w.kind not in self.persistent_kinds:
                    self._economy.settle(w.kind, w.key)

        return self._queue.pop(0) if self._queue else None
