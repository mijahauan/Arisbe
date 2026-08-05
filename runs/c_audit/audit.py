"""Did the C-series' channels mint anything when its figures were taken?

Two passes. COUNT: replay every published arm and report calls against mints per
channel. ABLATE: replay it again with each firing channel absent and diff the
figures the arm itself returns. See
docs/superpowers/specs/2026-08-04-c-series-channel-audit-design.md.

    uv run python runs/c_audit/audit.py --pass count
    uv run python runs/c_audit/audit.py --pass ablate
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Sequence

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from c_channel_probe import CHANNELS, ablating, channel_calls, muted  # noqa: E402
from c_field import CYCLIC, PAIRS                                     # noqa: E402
from test_c_channels import (C_ROUNDS, C_SEEDS, ROUNDS, SEEDS, _play,  # noqa: E402
                             _play_ask_and_challenge, _play_challenge)
from test_c_speaker_variance import ALL_LIARS, ONE_LIAR               # noqa: E402

OUT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Arm:
    name: str
    harness: Callable
    seeds: Sequence[int]
    rounds: int
    kwargs: Dict[str, Any]

    def play(self, seed):
        return self.harness(seed, self.rounds, **self.kwargs)


_C3 = dict(channel=True, stagger=2, seed_laws=True, wrong_laws=True,
           induce=False)

ARMS = [
    Arm("P1", _play, SEEDS, ROUNDS, dict(channel=True, stagger=2)),
    Arm("P2", _play, SEEDS, 40, dict(channel=True, stagger=1)),
    Arm("C1", _play_challenge, C_SEEDS, C_ROUNDS, dict(channel=True)),
    Arm("C2", _play_challenge, C_SEEDS, C_ROUNDS,
        dict(channel=True, wrong_laws=True)),
    Arm("C3", _play_challenge, C_SEEDS, C_ROUNDS, dict(_C3)),
    Arm("C4", _play_challenge, C_SEEDS, C_ROUNDS,
        dict(_C3, n_units=4, scheme=PAIRS)),
    Arm("C5", _play_challenge, C_SEEDS, C_ROUNDS,
        dict(_C3, n_units=6, scheme=PAIRS)),
    Arm("C6", _play_challenge, C_SEEDS, C_ROUNDS,
        dict(_C3, n_units=6, scheme=PAIRS, witnesses=3)),
    Arm("C7", _play_challenge, C_SEEDS, C_ROUNDS,
        dict(channel=True, n_units=6, scheme=PAIRS)),
    Arm("C8", _play_challenge, C_SEEDS, C_ROUNDS,
        dict(channel=True, n_units=6, scheme=PAIRS, witnesses=3)),
    Arm("K1", _play_ask_and_challenge, C_SEEDS, C_ROUNDS, dict(ask=True)),
    Arm("K2", _play_ask_and_challenge, C_SEEDS, C_ROUNDS, dict(ask=False)),
    Arm("K3", _play_ask_and_challenge, C_SEEDS, C_ROUNDS,
        dict(ask=False, mute=True)),
    Arm("K4", _play_ask_and_challenge, C_SEEDS, C_ROUNDS,
        dict(ask=True, typify="prefer")),
    Arm("K5", _play_ask_and_challenge, C_SEEDS, C_ROUNDS,
        dict(ask=True, typify="distrust")),
    Arm("K6", _play_ask_and_challenge, C_SEEDS, C_ROUNDS,
        dict(ask=True, n_units=6, scheme=PAIRS)),
    Arm("K7", _play_ask_and_challenge, C_SEEDS, C_ROUNDS,
        dict(ask=True, typify="prefer", n_units=6, scheme=PAIRS)),
    Arm("K8", _play_ask_and_challenge, C_SEEDS, C_ROUNDS,
        dict(ask=True, window=3)),
    Arm("K9", _play_ask_and_challenge, C_SEEDS, C_ROUNDS,
        dict(ask=True, window=8)),
    Arm("K10", _play_ask_and_challenge, C_SEEDS, C_ROUNDS,
        dict(ask=True, window=8, n_units=6, scheme=PAIRS)),
    Arm("L1", _play_ask_and_challenge, C_SEEDS, C_ROUNDS,
        dict(ask=True, liars=ONE_LIAR)),
    Arm("L2", _play_ask_and_challenge, C_SEEDS, C_ROUNDS,
        dict(ask=True, typify="prefer", liars=ONE_LIAR)),
    Arm("L3", _play_ask_and_challenge, C_SEEDS, C_ROUNDS,
        dict(ask=True, typify="prefer", liars=ALL_LIARS)),
]

BY_NAME = {a.name: a for a in ARMS}


def count_pass(arms, out=sys.stdout):
    """Calls against mints, aggregated over the arm's own seeds."""
    tallies = {}
    for arm in arms:
        with channel_calls() as tally:
            for seed in arm.seeds:
                arm.play(seed)
        tallies[arm.name] = tally
        print(f"\n{arm.name}  {arm.harness.__name__}  "
              f"{len(arm.seeds)} seeds x {arm.rounds} rounds  {arm.kwargs}",
              file=out)
        for name in CHANNELS:
            if not tally.calls[name]:
                continue
            verdict = "SILENT" if not tally.effects[name] else ""
            print(f"   {name:<20} calls={tally.calls[name]:>7}  "
                  f"mints={tally.effects[name]:>7}  {verdict}", file=out)
        if tally.extra["dispose_asked"]:
            print(f"   {'(dispose asked)':<20} "
                  f"{tally.extra['dispose_asked']:>26}", file=out)
        silent = tally.silent()
        print(f"   -> silent: {silent if silent else 'none'}", file=out)
    return tallies


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pass", dest="which", choices=["count", "ablate"],
                   default="count")
    p.add_argument("--arms", nargs="*", default=None)
    args = p.parse_args()
    arms = [BY_NAME[n] for n in args.arms] if args.arms else ARMS
    if args.which == "count":
        path = OUT / "CALLS.txt"
        with path.open("w") as fh:
            count_pass(arms, out=fh)
        count_pass(arms)
        print(f"\nwritten: {path}")


if __name__ == "__main__":
    main()
