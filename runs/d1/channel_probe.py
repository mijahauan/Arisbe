"""Count what each channel call actually MINTS, per run, per arm.

Found the dead answer channel (fix round 5) and is kept as the instrument that
would find it again: a call that is made hundreds of times and returns an empty
list every time is invisible to every figure the sweep prints.

    uv run python runs/d1/channel_probe.py --domains 8 --rounds 60 --seeds 1
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from c_unit import Unit                       # noqa: E402
from run_d1 import ARMS, calibrate, play      # noqa: E402

TALLY: Counter = Counter()
CALLS: Counter = Counter()


def _wrap(name):
    original = getattr(Unit, name)

    def wrapped(self, *a, **k):
        out = original(self, *a, **k)
        CALLS[name] += 1
        if name == "ask":
            TALLY[name] += 1 if out is not None else 0
        elif name == "adopt":
            TALLY[name] += 1 if out else 0
        elif name == "dispose_challenges":
            TALLY[name] += (len(out.suspended) + len(out.retracted_internally)
                            + len(out.retracted_by_corroboration)
                            + len(out.restored_by_rebuttal)
                            + len(out.restored_by_silence))
        else:
            TALLY[name] += len(out) if out is not None else 0
        return out

    setattr(Unit, name, wrapped)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--rounds", type=int, default=60)
    p.add_argument("--domains", type=int, default=8)
    p.add_argument("--seeds", type=int, nargs="*", default=[1])
    p.add_argument("--arms", nargs="*", default=list(ARMS))
    args = p.parse_args()

    for name in ("publish", "ask", "answer", "challenge", "corroborate",
                 "dispose_challenges", "adopt", "settle_credit"):
        _wrap(name)

    source = calibrate(args.seeds, args.rounds, n_domains=args.domains)
    print(f"field {args.domains} domains  tariff={source.tariff:.6f}  "
          f"E0={source.entry_price:.6f}")
    for arm in args.arms:
        for seed in args.seeds:
            TALLY.clear()
            CALLS.clear()
            r = play(arm, seed=seed, rounds=args.rounds, source=source,
                     n_domains=args.domains)
            print(f"\n{arm} seed={seed}  survivors={r.survivors} "
                  f"born={r.born} died={r.died} acts={r.acts_minted}")
            for name in ("adopt", "ask", "answer", "publish", "challenge",
                         "corroborate", "dispose_challenges", "settle_credit"):
                print(f"   {name:<20} calls={CALLS[name]:>7}  "
                      f"effects={TALLY[name]:>7}")


if __name__ == "__main__":
    main()
