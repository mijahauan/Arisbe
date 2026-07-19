"""Examination IV pilot — cluster: rung-1 S1 robustness + yield attribution.

Arms (all deterministic, offline, existing modules only):
  A0 economy (as shipped)            — reproduce the round-6 headline
  A1 severity-flattened economy      — severity=1.0 on every want; does yield-learning alone refute in 90?
  A2 severity-greedy chooser         — sort by (-severity, cost); no yield, no decay, no learning
  A3 round-robin FIFO (skip-tried)   — FIFO repaired one line: fewest-attempts-first
  A4 scatter with confirm_lattice=6  — chaff dial turned down; does scatter's margin collapse?
  A5 scatter with confirm_lattice=60 — as shipped (reference)
"""
import sys, time
sys.path.insert(0, "/Users/mjh/Sync/GitHub/Arisbe/src")

from agon_evolution import run, DISPOSITION_CHALLENGE_M
from attention_economy import AttentionEconomy, Want
from arithmetic_world import (ArithmeticWorld, ProbeDirectedFeed, FERMAT_LAW,
                              fifo_chooser, scatter_chooser)

M0 = '(even "0")'


def refutation_round(res):
    for o in res.outcomes:
        if o.disposition == DISPOSITION_CHALLENGE_M:
            return o.round_idx
    return None


class FlatSeverityFeed(ProbeDirectedFeed):
    """A1: identical feed, severity flattened to 1.0 at registration."""
    def _seed(self, round_idx):
        super()._seed(round_idx)
        for w in self._economy.wants():
            w.severity = 1.0


def severity_greedy(economy, k, round_idx):
    """A2: a two-line 'prioritize at all' baseline — no yield, no cost learning."""
    ws = sorted(economy.wants(),
                key=lambda w: (-w.severity, w.cost, w.attempts, repr(w.key)))
    chosen = ws[:k]
    for w in chosen:
        w.attempts += 1
    return chosen


def round_robin(economy, k, round_idx):
    """A3: FIFO repaired one line — fewest attempts first, then FIFO order."""
    ws = sorted(economy.wants(),
                key=lambda w: (w.attempts, w.created_round, w.kind, repr(w.key)))
    chosen = ws[:k]
    for w in chosen:
        w.attempts += 1
    return chosen


def arm(name, *, feed_cls=ProbeDirectedFeed, chooser=None, lattice=60, rounds=90):
    t0 = time.time()
    feed = feed_cls(ArithmeticWorld(), AttentionEconomy(), chooser=chooser,
                    confirm_lattice=lattice)
    res = run(M0 + " " + FERMAT_LAW, feed, rounds=rounds,
              uod_id=f"exam4_{name}", name=name, seed_laws=[FERMAT_LAW])
    r = refutation_round(res)
    print(f"{name:34s} refutation_round={r}   ({time.time()-t0:.1f}s, rounds={rounds})")
    return r


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all", "a0"):
        arm("A0_economy_shipped")
    if which in ("all", "a2"):
        arm("A2_severity_greedy", chooser=severity_greedy)
    if which in ("all", "a3"):
        arm("A3_round_robin_fifo", chooser=round_robin)
    if which in ("all", "a4"):
        arm("A4_scatter_lattice6", chooser=scatter_chooser, lattice=6)
    if which in ("all", "a1"):
        arm("A1_flat_severity", feed_cls=FlatSeverityFeed)
    if which in ("all", "a5"):
        arm("A5_scatter_lattice60", chooser=scatter_chooser)
