#!/usr/bin/env python3
"""Examination IV disposal harness — rung-1 S1 robustness + yield attribution
(``runs/EXAMINATION_IV_BRIEFS/panel_B_rung1_empirics.md``, Suspect 3(d) and
Suspect 11(d).1-2). Promotes the panel's scratchpad pilot
(``runs/EXAMINATION_IV_BRIEFS/ablation_pilot.py``, arms A0-A5) into a
committed, deterministic, offline CLI and adds three arms the pilot did not
have time to run:

  --arm discriminating   economy vs severity-greedy vs scatter on a world
                          where the counterexample is NOT pre-labeled with a
                          severity-8 hunt want (tests whether the economy
                          LEARNS where yield is, or merely obeys the label —
                          panel B Suspect 3).
  --arm cost_purse        arms (1)(2)(4)(5) re-run under a real 30-unit cost
                          purse (cumulative Want.cost, arm stops when spent) —
                          "under budget" as an actual resource claim, not a
                          round count (panel B Suspect 3(b)/x3).
  --arm churn_pump        the noisy-TV guard test (panel B Suspect 11(d).2):
                          ttl=8 disuse-decay on, 120 rounds, a persistent
                          "refresh" kind that re-delivers a fixed 5-atom block
                          every time it is chosen.

PRE-REGISTERED CRITERION for churn_pump (read BEFORE running — this is a run
artifact, not a CI assertion):

  REFUTES "the noisy-TV guard is built" if the refresh kind's yield
  stabilizes POSITIVE and its SHARE OF CHOICES GROWS once decay onset begins
  (round > ttl): a channel that generates no learning is not merely tolerated
  but increasingly preferred — the realized noisy TV.

  SUSTAINS "the guard holds" if attempt-decay (``attempt_decay ** attempts``)
  and/or yield-decay (``yield_decay``) sink the refresh kind's score below the
  productive kinds despite the repeated re-delivery churn — i.e. the economy
  does not chase it.

  This is genuinely open per the panel brief ("possible: attempt_decay^attempts
  may rescue — this is worth running") — no result is assumed here.

All arms are deterministic (no RNG, no wall clock) and offline (no network,
no LLM). Every arm builds a fresh ``ArithmeticWorld`` + ``AttentionEconomy``
so arms never share state.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agon_evolution import run, DISPOSITION_CHALLENGE_M              # noqa: E402
from attention_economy import AttentionEconomy, Want                  # noqa: E402
from arithmetic_world import (                                        # noqa: E402
    ArithmeticWorld, ProbeDirectedFeed, FERMAT_LAW, SQUARE_LAW, scatter_chooser,
)

M0 = '(even "0")'


def refutation_round(res):
    for o in res.outcomes:
        if o.disposition == DISPOSITION_CHALLENGE_M:
            return o.round_idx
    return None


# --------------------------------------------------------------------------- #
# A0-A5 — promoted from the panel's scratchpad pilot, unchanged in substance.  #
# --------------------------------------------------------------------------- #

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
    return r, feed, res


def run_baseline_arms(rounds: int):
    arm("A0_economy_shipped", rounds=rounds)
    arm("A2_severity_greedy", chooser=severity_greedy, rounds=rounds)
    arm("A3_round_robin_fifo", chooser=round_robin, rounds=rounds)
    arm("A4_scatter_lattice6", chooser=scatter_chooser, lattice=6, rounds=rounds)
    arm("A1_flat_severity", feed_cls=FlatSeverityFeed, rounds=rounds)
    arm("A5_scatter_lattice60", chooser=scatter_chooser, rounds=rounds)


# --------------------------------------------------------------------------- #
# The discriminating world (Suspect 3(d)) — no severity-8 hunt anywhere; the  #
# counterexample (n=9, the first odd perfect square) is reachable only        #
# through the severity-1.0 confirm/extend probes every world already runs.   #
# --------------------------------------------------------------------------- #

def discriminating_arm(name, *, chooser=None, rounds=90):
    t0 = time.time()
    world = ArithmeticWorld(deny_odd_squares=True)
    # laws=() -- ProbeDirectedFeed only ever seeds hunt wants for FERMATS
    # instances of the laws it is given; passing none means NO hunt want is
    # ever registered on this world, for any law. The severity-8 label
    # channel does not exist here.
    feed = ProbeDirectedFeed(world, AttentionEconomy(), chooser=chooser, laws=())
    res = run(M0 + " " + SQUARE_LAW, feed, rounds=rounds,
              uod_id=f"exam4_disc_{name}", name=name, seed_laws=[SQUARE_LAW])
    r = refutation_round(res)
    print(f"{name:34s} refutation_round={r}   ({time.time()-t0:.1f}s, rounds={rounds})")
    return r, feed, res


def run_discriminating(rounds: int):
    print("-- discriminating world: SQUARE_LAW, no severity-8 hunts --")
    discriminating_arm("disc_economy", rounds=rounds)
    discriminating_arm("disc_severity_greedy", chooser=severity_greedy, rounds=rounds)
    discriminating_arm("disc_scatter", chooser=scatter_chooser, rounds=rounds)


# --------------------------------------------------------------------------- #
# The cost purse (Suspect 3(b)/x3) — "under budget" as a charged resource.    #
# --------------------------------------------------------------------------- #

PURSE = 30.0


def purse_arm(name, *, chooser=None, rounds=300, purse=PURSE):
    t0 = time.time()
    feed = ProbeDirectedFeed(ArithmeticWorld(), AttentionEconomy(),
                              chooser=chooser, purse=purse)
    res = run(M0 + " " + FERMAT_LAW, feed, rounds=rounds,
              uod_id=f"exam4_purse_{name}", name=name, seed_laws=[FERMAT_LAW])
    r = refutation_round(res)
    exhausted = feed.spent >= purse
    outcome = f"refuted@{r}" if r is not None else "not refuted"
    print(f"{name:34s} {outcome:16s} spent={feed.spent:6.2f}/{purse:.0f}  "
          f"rounds_run={len(res.outcomes)}/{rounds}  exhausted={exhausted}  "
          f"({time.time()-t0:.1f}s)")
    return r, feed, res


def run_cost_purse(rounds: int):
    print(f"-- cost purse: {PURSE:.0f} units, refutation-or-exhaustion --")
    purse_arm("purse_economy", rounds=rounds)                       # (1)
    purse_arm("purse_severity_greedy", chooser=severity_greedy, rounds=rounds)  # (2)
    purse_arm("purse_round_robin", chooser=round_robin, rounds=rounds)          # (4)
    purse_arm("purse_scatter", chooser=scatter_chooser, rounds=rounds)         # (5)


# --------------------------------------------------------------------------- #
# The churn pump (Suspect 11(d).2 / x1) — the realized noisy-TV test.        #
# --------------------------------------------------------------------------- #

REFRESH_BLOCK = ('(refresh_a "r1") (refresh_b "r2") (refresh_c "r3") '
                  '(refresh_d "r4") (refresh_e "r5")')


class ChurnPumpFeed(ProbeDirectedFeed):
    """The shipped feed plus one persistent ``refresh`` kind that re-delivers
    an identical fixed 5-atom block every time it is chosen — a channel that
    generates model churn (and, per the pinned Suspect-11 defect, "yield")
    with zero learning content, once disuse-decay (``ttl``) is on.

    ``severity=8.0`` deliberately matches the ``hunt`` kind's severity — the
    same authored boost that let Suspect 3's severity label win the S1
    headline. At severity 1.0 the channel never gets picked at all (a
    from-round-1-starved arm is untestable, the same IV-x1 unfalsifiability
    trap the S2 registration fell into); at 8.0 it gets a fair, adversarial
    shot at dominating the economy's choices — the worst case the "noisy-TV
    guard" claim needs to survive."""

    persistent_kinds = frozenset({"confirm", "refresh"})

    def _seed(self, round_idx):
        super()._seed(round_idx)
        self._economy.register(Want(
            kind="refresh", key=("refresh", "block"), cost=1.0, severity=8.0,
            created_round=round_idx))

    def _execute(self, w: Want):
        if w.kind == "refresh":
            return REFRESH_BLOCK
        return super()._execute(w)


def run_churn_pump(rounds: int = 120, ttl: int = 8):
    t0 = time.time()
    feed = ChurnPumpFeed(ArithmeticWorld(), AttentionEconomy())
    res = run(M0 + " " + FERMAT_LAW, feed, rounds=rounds, ttl=ttl,
              uod_id="exam4_churn_pump", name="churn pump", seed_laws=[FERMAT_LAW])

    trajectory = [(j["round"], j["snapshot"]["kinds"].get("refresh", 0.0))
                  for j in feed.journal]
    chosen_kinds = [j["chosen"][0][0] if j["chosen"] else None for j in feed.journal]

    def share(kinds):
        return (sum(1 for k in kinds if k == "refresh") / len(kinds)) if kinds else 0.0

    half = max(1, len(chosen_kinds) // 2)
    early_share = share(chosen_kinds[:half])
    late_share = share(chosen_kinds[half:])

    print(f"churn_pump: ttl={ttl} rounds={rounds} ({time.time()-t0:.1f}s)")
    print(f"  refresh choice share: first half={early_share:.3f}  "
          f"second half={late_share:.3f}")
    print("  refresh kind_yield trajectory (round, y):")
    for rnd, y in trajectory:
        print(f"    r{rnd:>4d}  y={y:.4f}")

    grows = late_share > early_share
    stabilizes_positive = trajectory and trajectory[-1][1] > 0
    if stabilizes_positive and grows:
        print("  >>> READS AS REFUTING the noisy-TV guard claim: refresh's "
              "yield is positive and its choice share grew after decay onset.")
    else:
        print("  >>> READS AS SUSTAINING the noisy-TV guard: refresh did not "
              "come to dominate choices despite the repeated churn.")
    return feed, res


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #

ARMS = {
    "a0": lambda rounds: arm("A0_economy_shipped", rounds=rounds),
    "a1": lambda rounds: arm("A1_flat_severity", feed_cls=FlatSeverityFeed, rounds=rounds),
    "a2": lambda rounds: arm("A2_severity_greedy", chooser=severity_greedy, rounds=rounds),
    "a3": lambda rounds: arm("A3_round_robin_fifo", chooser=round_robin, rounds=rounds),
    "a4": lambda rounds: arm("A4_scatter_lattice6", chooser=scatter_chooser, lattice=6, rounds=rounds),
    "a5": lambda rounds: arm("A5_scatter_lattice60", chooser=scatter_chooser, rounds=rounds),
    "baseline": run_baseline_arms,
    "discriminating": run_discriminating,
    "cost_purse": run_cost_purse,
    "churn_pump": lambda rounds: run_churn_pump(rounds=rounds if rounds else 120),
}


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--arm", choices=sorted(ARMS) + ["all"], default="all")
    p.add_argument("--rounds", type=int, default=None,
                    help="round budget (default: 90 for baseline/discriminating, "
                         "300 for cost_purse, 120 for churn_pump)")
    args = p.parse_args()

    which = args.arm
    default_rounds = {"cost_purse": 300, "churn_pump": 120}

    if which == "all":
        for name in ("baseline", "discriminating", "cost_purse", "churn_pump"):
            rounds = args.rounds if args.rounds is not None else default_rounds.get(name, 90)
            ARMS[name](rounds)
    else:
        rounds = args.rounds if args.rounds is not None else default_rounds.get(which, 90)
        ARMS[which](rounds)


if __name__ == "__main__":
    main()
