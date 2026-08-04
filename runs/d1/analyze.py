"""D-1 analysis pass: the priors read off one instrumented sweep.

Not a library and not a permanent tool -- the hand pass task 8 owes for P-D2
and P-D4, which have no dedicated instrument in the D-1 build (see the task-8
brief's known-gaps note 1). Dumps JSON so RUN_D1_LOG.md quotes figures rather
than adjectives.

    uv run python runs/d1/analyze.py --domains 12 --rounds 60
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from c_field import PAIRS, units_for_witnesses, wide_spec   # noqa: E402
from d_world import seats_from                              # noqa: E402
from run_d1 import ARMS, MIN_WITNESSES, SEEDS, calibrate, play  # noqa: E402


def classify(law, planted):
    if law in planted:
        return "planted"
    if (law[1], law[0]) in planted:
        return "converse"
    return "other"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--domains", type=int, default=12)
    ap.add_argument("--rounds", type=int, default=60)
    ap.add_argument("--seeds", type=int, nargs="*", default=list(SEEDS))
    ap.add_argument("--out", default=str(Path(__file__).parent / "analysis.json"))
    args = ap.parse_args()

    spec = wide_spec(seed=args.seeds[0], n_domains=args.domains)
    ceiling = seats_from(spec).free()
    n0 = units_for_witnesses(spec, MIN_WITNESSES, PAIRS)

    source = calibrate(args.seeds, args.rounds, n_domains=args.domains)
    out = {
        "domains": args.domains, "rounds": args.rounds,
        "seeds": args.seeds, "seat_ceiling": ceiling, "n0": n0,
        "tariff": source.tariff, "entry_price": source.entry_price,
        "arms": {},
    }
    print(f"field {args.domains}  seats {ceiling}  N0 {n0}  "
          f"tariff {source.tariff:.6f}  E0 {source.entry_price:.6f}",
          flush=True)

    for arm in ARMS:
        rows = []
        for seed in args.seeds:
            r = play(arm, seed=seed, rounds=args.rounds, source=source,
                     n_domains=args.domains)
            planted = r.planted
            lineage = {"planted": [], "converse": [], "other": []}
            spread = {"planted": [], "converse": [], "other": []}
            for law, holder_rounds in r.holders_by_law.items():
                k = classify(law, planted)
                lineage[k].append(holder_rounds)
                spread[k].append(len(r.units_by_law[law]))
            lifespans = {u: b - a + 1 for u, (a, b) in r.lifespan.items()}
            survivors = {u.unit_id for u in r.final_units}
            lived = [lifespans[u] for u in lifespans]
            stand_surv = [r.standing_by_unit.get(u, 0) for u in survivors]
            stand_dead = [r.standing_by_unit.get(u, 0)
                          for u in lifespans if u not in survivors]
            rows.append({
                "seed": seed,
                "survivors": r.survivors, "born": r.born, "died": r.died,
                "acts": r.acts_minted, "charge": r.total_charge,
                "peak": r.peak_population, "pop_trace": r.pop_trace,
                "n0": r.n0,
                "extinct_at": (len(r.pop_trace)
                               if r.pop_trace and r.pop_trace[-1] == 0
                               else None),
                "death_trace": r.death_trace,
                "first_death_round": next(
                    (i for i, d in enumerate(r.death_trace) if d > 0), None),
                "mean_lifespan": statistics.mean(lived) if lived else 0.0,
                "ever_lived": len(lifespans),
                "lineage_mean": {k: (statistics.mean(v) if v else 0.0)
                                 for k, v in lineage.items()},
                "lineage_n": {k: len(v) for k, v in lineage.items()},
                "spread_mean": {k: (statistics.mean(v) if v else 0.0)
                                for k, v in spread.items()},
                "choice_histogram": {str(k): v
                                     for k, v in sorted(r.choice_histogram.items())},
                "standing_survivors_mean": (statistics.mean(stand_surv)
                                            if stand_surv else 0.0),
                "standing_dead_mean": (statistics.mean(stand_dead)
                                       if stand_dead else 0.0),
                "hit_rounds": r.hit_rounds,
                # The SETTLED level, not the peak: the escalation rule is about
                # an equilibrium, and a transient overshoot is not one. Both are
                # reported, and the stricter of the two decides.
                "tail_mean": (statistics.mean(r.pop_trace[-10:])
                              if r.pop_trace else 0.0),
            })
            print(f"  {arm} seed {seed}: surv {r.survivors} born {r.born} "
                  f"died {r.died} peak {r.peak_population} "
                  f"charge {r.total_charge:.3f}", flush=True)
        out["arms"][arm] = rows

    Path(args.out).write_text(json.dumps(out, indent=1))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
