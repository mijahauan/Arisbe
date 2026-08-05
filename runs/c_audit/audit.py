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
    # SEEDS[:8], not the full 14-seed SEEDS: the published call site for this
    # arm (tests/test_c_channels.py:698,
    # test_asking_and_answering_beats_being_mute_at_equal_run_length) uses
    # SEEDS[:8]. The committed script had drifted to the full SEEDS list;
    # fixed here so P2's ablation replays the arm that was actually published.
    Arm("P2", _play, SEEDS[:8], 40, dict(channel=True, stagger=1)),
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
    """Calls against mints, aggregated over the arm's own seeds.

    WHY THIS PASS STANDS THE STANDING GUARD DOWN. Task 6 put `@audited()` on all
    three harnesses, so an arm whose channel mints nothing now raises instead of
    returning — which is right in the test suite and exactly wrong here. THIS
    SCRIPT IS THE INSTRUMENT THAT REPORTS A SILENCE. Its whole job a dozen lines
    below is to print `SILENT` beside a zero; a silence must reach that line,
    not stop the pass. `ablating()` is the suspension the probe already provides
    for the case where a zero is the observation rather than the defect.

    A DECLARATION WOULD NOT DO INSTEAD. Passing `expect_silent` through
    `Arm.kwargs` would put the allowlist into the kwargs line printed into
    `CALLS.txt`, so the record of what an arm WAS would carry what the audit
    EXPECTED of it — and it would have to be maintained here as well as in the
    test file, where a divergence between the two would be invisible.

    Without this, `--pass count` died on arm P2 — whose `adopt` zero is declared
    at the published call site, which this script does not go through — after
    `main()` had already truncated `CALLS.txt`, taking the audit's own record
    with it. 218 lines to 6.
    """
    tallies = {}
    for arm in arms:
        with channel_calls() as tally, ablating():
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


def figures(arm, result) -> Dict[str, int]:
    """The arm's OWN numbers, reduced to a comparable dict of ints.

    Nothing here is computed by the audit: every value is one the harness
    already returns, or a count of something it returns.
    """
    if arm.harness is _play:
        units, _board, answers, uptakes = result
        return dict(answers=answers, uptakes=uptakes,
                    hits=sum(u.ledger.hits for u in units),
                    misses=sum(u.ledger.misses for u in units),
                    abstentions=sum(u.ledger.abstentions for u in units),
                    laws=sum(len(u.laws) for u in units))
    if arm.harness is _play_challenge:
        _spec, units, board, raised, events, tally = result
        out = {f"disp_{k}": v for k, v in tally.items()}
        out.update(raised=raised, events=len(events),
                   marks=len(board.all_marks()),
                   laws=sum(len(u.laws) for u in units),
                   suspended=sum(len(u.suspended) for u in units))
        return out
    # _play_ask_and_challenge: the tally dict, minus the non-scalar entries.
    skip = {"consult", "prefs", "could", "voices", "voices_by_rel", "units"}
    return {k: v for k, v in result.items() if k not in skip}


def ablate_pass(arms, tallies, out=sys.stdout):
    """For each channel that FIRED in an arm, replay the arm without it."""
    for arm in arms:
        tally = tallies[arm.name]
        base = {}
        # The BASE run stands the guard down for the same reason `count_pass`
        # does: this is the observer, and an arm's silence is its subject
        # matter. The ablated runs below already carry `ablating()` — an
        # ablation silences downstream channels on purpose.
        with ablating():
            for seed in arm.seeds:
                for k, v in figures(arm, arm.play(seed)).items():
                    base[k] = base.get(k, 0) + v
        firing = [c for c in CHANNELS if tally.effects[c]]
        print(f"\n{arm.name}  fired: {firing}", file=out)
        for channel in firing:
            got = {}
            with ablating(), muted(channel):
                for seed in arm.seeds:
                    for k, v in figures(arm, arm.play(seed)).items():
                        got[k] = got.get(k, 0) + v
            moved = {k: (base[k], got[k]) for k in base if base[k] != got.get(k)}
            if not moved:
                print(f"   -{channel:<18} INERT: not one figure moved",
                      file=out)
            else:
                shown = sorted(moved.items(),
                               key=lambda kv: -abs(kv[1][0] - kv[1][1]))[:8]
                print(f"   -{channel:<18} moved {len(moved)}/{len(base)}: "
                      + ", ".join(f"{k} {a}->{b}" for k, (a, b) in shown),
                      file=out)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--pass", dest="which", choices=["count", "ablate"],
                   default="count")
    p.add_argument("--arms", nargs="*", default=None)
    p.add_argument("--append", action="store_true",
                   help="append to ABLATION.txt instead of overwriting it "
                        "(the full pass exceeds one run; groups append "
                        "after the first). Never touches CALLS.txt, the "
                        "committed Task 2 record: the tallies this pass "
                        "needs are recomputed to a scratch file instead.")
    args = p.parse_args()
    arms = [BY_NAME[n] for n in args.arms] if args.arms else ARMS
    if args.which == "count":
        path = OUT / "CALLS.txt"
        # WRITTEN ONCE, THEN ECHOED. An earlier version called `count_pass`
        # a second time to put the same report on stdout, which replayed all
        # 23 arms and doubled a ~15-minute pass for a copy of a file that was
        # already on disk.
        with path.open("w") as fh:
            count_pass(arms, out=fh)
        print(path.read_text())
        print(f"\nwritten: {path}")
    else:
        scratch = OUT / "ABLATION_CALLS_scratch.txt"
        with scratch.open("w") as fh:
            tallies = count_pass(arms, out=fh)
        path = OUT / "ABLATION.txt"
        with path.open("a" if args.append else "w") as fh:
            ablate_pass(arms, tallies, out=fh)
        print(path.read_text())
        print(f"\nwritten: {path}")


if __name__ == "__main__":
    main()
