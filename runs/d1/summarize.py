"""Turn the analysis JSONs into the figures RUN_D1_LOG.md quotes.

Reads only what `analyze.py` already wrote -- no re-running, so every number
here is the same run the raw sweep printed.

    uv run python runs/d1/summarize.py runs/d1/analysis_d16.json
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path


def mean(xs):
    return statistics.mean(xs) if xs else 0.0


def report(path: Path) -> None:
    d = json.loads(path.read_text())
    k, ceiling, n0 = d["domains"], d["seat_ceiling"], d["n0"]
    tariff, e0 = d["tariff"], d["entry_price"]
    print(f"\n{'='*78}\nFIELD {k} domains  seats={ceiling}  N0={n0}  "
          f"tariff={tariff:.6f}  E0={e0:.6f}  2*E0={2*e0:.6f}")

    print("\n-- per seed --")
    print(f"{'arm':>5} {'seed':>5} {'surv':>6} {'born':>6} {'died':>6} "
          f"{'acts':>8} {'charge':>9} {'peak':>6} {'1stdeath':>9}")
    for arm, rows in d["arms"].items():
        for r in rows:
            fd = r["first_death_round"]
            print(f"{arm:>5} {r['seed']:>5} {r['survivors']:>6} {r['born']:>6} "
                  f"{r['died']:>6} {r['acts']:>8} {r['charge']:>9.3f} "
                  f"{r['peak']:>6} {('-' if fd is None else fd):>9}")

    print("\n-- arm summary --")
    print(f"{'arm':>5} {'surv':>7} {'%ceil':>7} {'Neq/N0':>7} {'born':>7} "
          f"{'died':>7} {'acts':>9} {'charge':>8} {'life':>7} {'trough':>7} "
          f"{'tail10':>7} {'swing':>7} {'dem/ur':>7}")
    for arm, rows in d["arms"].items():
        surv = mean([r["survivors"] for r in rows])
        troughs, peaks, swings, demur = [], [], [], []
        for r in rows:
            window = r["pop_trace"][20:60]
            if window:
                troughs.append(min(window))
                peaks.append(max(window))
                swings.append(max(window) - min(window))
            unit_rounds = r["mean_lifespan"] * r["ever_lived"]
            if unit_rounds and tariff:
                demur.append((r["charge"] / tariff) / unit_rounds)
        print(f"{arm:>5} {surv:>7.2f} {100*surv/ceiling:>7.1f} "
              f"{surv/n0:>7.3f} {mean([r['born'] for r in rows]):>7.1f} "
              f"{mean([r['died'] for r in rows]):>7.1f} "
              f"{mean([r['acts'] for r in rows]):>9.0f} "
              f"{mean([r['charge'] for r in rows]):>8.2f} "
              f"{mean([r['mean_lifespan'] for r in rows]):>7.2f} "
              f"{mean(troughs):>7.1f} "
              f"{mean([r['tail_mean'] for r in rows]):>7.2f} "
              f"{mean(swings):>7.1f} {mean(demur):>7.1f}")

    print("\n-- P-D1: first death, deaths, extinctions --")
    for arm, rows in d["arms"].items():
        fds = [r["first_death_round"] for r in rows]
        named = [f for f in fds if f is not None]
        ext = [r["extinct_at"] for r in rows if r["extinct_at"] is not None]
        print(f"{arm:>5} first death {sorted(set(named)) if named else 'NONE'} "
              f" seeds with a death {len(named)}/{len(rows)} "
              f" deaths/run {min(r['died'] for r in rows)}-"
              f"{max(r['died'] for r in rows)} "
              f" extinctions {len(ext)}")

    print("\n-- P-D2: lineage (holder-rounds / spread / laws per run) --")
    for arm, rows in d["arms"].items():
        cells = []
        for cls in ("planted", "converse", "other"):
            cells.append(
                f"{cls}: {mean([r['lineage_mean'][cls] for r in rows]):8.1f} / "
                f"{mean([r['spread_mean'][cls] for r in rows]):6.2f} / "
                f"{mean([r['lineage_n'][cls] for r in rows]):5.2f}")
        print(f"{arm:>5}  " + "   ".join(cells))

    print("\n-- P-D4: choice histogram + standing survivors vs dead --")
    for arm, rows in d["arms"].items():
        hist = {}
        for r in rows:
            for cand, n in r["choice_histogram"].items():
                hist[int(cand)] = hist.get(int(cand), 0) + n
        total = sum(hist.values())
        multi = sum(n for c, n in hist.items() if c >= 2)
        share = (100 * multi / total) if total else 0.0
        print(f"{arm:>5} occasions {total:>7}  >=2 candidates {multi:>6} "
              f"({share:5.1f}%)  hist {dict(sorted(hist.items()))}")
        print(f"{'':>5}   standing: survivors "
              f"{mean([r['standing_survivors_mean'] for r in rows]):.2f}  "
              f"dead {mean([r['standing_dead_mean'] for r in rows]):.2f}")

    print("\n-- escalation check --")
    highest = max(r["peak"] for rows in d["arms"].values() for r in rows)
    a1 = mean([r["survivors"] for r in d["arms"]["A1"]])
    capped = sum(1 for r in d["arms"]["A1"] if r["survivors"] >= ceiling)
    print(f"  highest population {highest} vs 80% of {ceiling} = "
          f"{0.8*ceiling:.1f} -> "
          f"{'FIRES' if highest >= 0.8*ceiling else 'clear'}")
    print(f"  A1 settled {a1:.2f} = {100*a1/ceiling:.1f}% of ceiling; "
          f"A1 seeds ending AT the cap: {capped}/{len(d['arms']['A1'])}")


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        report(Path(arg))
