"""D-1: run the priced world across its four arms.

Design spec: docs/superpowers/specs/2026-08-02-d-series-building-the-stake-design.md

Usage:
    uv run python tools/run_d1.py                  # calibrate, then all arms
    uv run python tools/run_d1.py --rounds 60
"""

from __future__ import annotations

import argparse
import statistics
import sys
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from c_field import (PAIRS, Aperture, Field, apertures_for,  # noqa: E402
                     units_for_witnesses, wide_spec)
from c_marks import MarkBoard                                # noqa: E402
from c_unit import Unit                                      # noqa: E402
from d_world import PricedWorld, Source, seats_from          # noqa: E402

ARMS = ("A0", "A1", "A2a", "A2b")
SEEDS = (1, 2, 3, 4, 5, 7, 42, 99)
ROUNDS = 60
MIN_WITNESSES = 3


@dataclass
class ArmResult:
    arm: str
    seed: int
    rounds: int
    survivors: int
    born: int
    died: int
    acts_minted: int
    final_units: List[Unit] = dc_field(default_factory=list)
    charges_by_unit: Dict[str, float] = dc_field(default_factory=dict)
    first_law_round: Dict[str, int] = dc_field(default_factory=dict)
    world: Optional[PricedWorld] = None


def _planted(spec) -> set:
    return {d.law for d in spec.domains}


def play(arm: str, seed: int, rounds: int, source: Source) -> ArmResult:
    """One community, one seed, one arm.

    THE ROUND ORDER matters and is the C-series' own: adopt, attend, then the
    channel acts, then the world settles. Settling LAST means the round's acts
    are already on the board before anything is charged, so no charge can reach
    the acts it prices.

    THERE IS NO STAGGER. The C-series' bounded attention was a schedule imposed
    from outside; under a priced world every living unit attends every round and
    pays for it -- fix the price, let the quantum fall out."""
    if arm not in ARMS:
        raise ValueError(f"arm must be one of {ARMS}, got {arm!r}")
    spec = wide_spec(seed=seed)
    field = Field(spec)
    n0 = units_for_witnesses(spec, MIN_WITNESSES, PAIRS)

    mint_board = MarkBoard()
    void_board = MarkBoard()
    # A2a: no channel at all. A2b: mint (and pay) but nothing reaches anyone.
    speak_board = None if arm == "A2a" else mint_board
    hear_board = {"A0": mint_board, "A1": mint_board,
                  "A2a": None, "A2b": void_board}[arm]

    world = PricedWorld(source, seats_from(spec), mint_board,
                        subtract=(arm != "A0"))

    def make_unit(unit_id: str, aperture: Aperture) -> Unit:
        """A newborn inherits NOTHING but the board -- no facts, no laws, no
        standing -- and is socialized by marks it never made."""
        return Unit(unit_id, aperture)

    units: List[Unit] = []
    for i in range(n0):
        uid = f"u{i}"
        aperture = world.seats.take(uid)
        unit = Unit(uid, aperture)
        world._next_id = max(world._next_id, i + 1)
        # A FOUNDER IS ENDOWED AT THE WORLD'S ENTRY PRICE, exactly. It must
        # then DOUBLE before it may breed (threshold 2*E0), which is the rule
        # reading "pay a newcomer's entry and remain viable yourself".
        #
        # `max(..., 1.0)` would break that: with a measured E0 below 1.0 every
        # founder would start above the breeding threshold and split in round
        # 0, an artefact of the endowment rather than a finding. The fallback
        # applies ONLY to the calibration arm, where the entry price is not yet
        # known -- a zero endowment there would read as dead at round 0, since
        # `alive` is `balance > 0`.
        world.reserves.seed(uid, source.entry_price
                            if source.entry_price > 0.0 else 1.0)
        units.append(unit)

    planted = _planted(spec)
    first_law: Dict[str, int] = {}
    charges: Dict[str, float] = {}
    born = died = 0
    asked: Dict[str, list] = {}

    for r in range(rounds):
        if hear_board is not None:                       # (a) adopt replies
            for u in units:
                for q in list(asked.get(u.unit_id, [])):
                    reply = hear_board.answer_to(q)
                    if reply is not None and reply.author != u.unit_id:
                        u.adopt(reply, hear_board, r)
                        asked[u.unit_id].remove(q)
        for u in units:                                   # (b) attend
            u.step(field, r, induce=True)
            if u.unit_id not in first_law and (u.laws & planted):
                first_law[u.unit_id] = r
        if speak_board is not None:                       # (c) speak
            for u in units:
                u.publish(speak_board, r)
                mark = u.ask(speak_board, r)
                if mark is not None:
                    asked.setdefault(u.unit_id, []).append(mark)
                u.challenge(speak_board, r)
        if hear_board is not None:                        # (d) hear
            for u in units:
                u.answer(hear_board, r)

        # (e) the world. A0 NEVER BREEDS: it does not subtract, so a reserve
        # never falls and every unit would split every round until the seats ran
        # out -- an artefact of the control, not a finding. The control's job is
        # to leave the community exactly as it would have been.
        report = world.settle(units, r,
                              make_unit=None if arm == "A0" else make_unit)
        for uid, amount in report.charges.items():
            charges[uid] = charges.get(uid, 0.0) + amount
        born += len(report.born)
        died += len(report.died)
        units = list(report.units)
        if not units:
            break

    return ArmResult(
        arm=arm, seed=seed, rounds=rounds, survivors=len(units),
        born=born, died=died,
        acts_minted=len(mint_board.all_marks()),
        final_units=units, charges_by_unit=charges,
        first_law_round=first_law, world=world)


def calibrate(seed_list=SEEDS, rounds: int = ROUNDS) -> float:
    """E0 -- the world's entry price, MEASURED and not chosen.

    Arm 0 at the reference configuration supplies `t*`, the MEDIAN over units
    and seeds of the round at which a unit induces its first planted law; E0 is
    the charge a median unit has accrued by then.

    MEDIAN AT BOTH STEPS, so one lucky unit does not set the world's entry
    price. WHY t* AND NOT A HORIZON: an austere endowment kills every unit
    before induction can happen and the run is empty, while a horizon chosen by
    hand is a free parameter wearing a law's clothes. Read off t*, the claim is
    sharp -- a unit that learns slower than the recorded baseline dies before it
    learns."""
    rounds_to_law: List[int] = []
    per_round_charge: List[float] = []
    for seed in seed_list:
        result = play("A0", seed=seed, rounds=rounds, source=Source(1.0, 0.0))
        rounds_to_law.extend(result.first_law_round.values())
        for uid, total in result.charges_by_unit.items():
            per_round_charge.append(total / result.rounds)
    if not rounds_to_law:
        raise RuntimeError(
            f"no unit induced a planted law in {rounds} rounds over seeds "
            f"{list(seed_list)}: t* is undefined and E0 cannot be measured"
        )
    t_star = statistics.median(rounds_to_law)
    return statistics.median(per_round_charge) * (t_star + 1)


def main() -> None:
    parser = argparse.ArgumentParser(description="D-1: the priced world")
    parser.add_argument("--rounds", type=int, default=ROUNDS)
    parser.add_argument("--seeds", type=int, nargs="*", default=list(SEEDS))
    args = parser.parse_args()

    e0 = calibrate(args.seeds, args.rounds)
    print(f"calibration: E0 = {e0:.6f}  (measured, not chosen)")
    source = Source(pool_per_round=1.0, entry_price=e0)

    print(f"\n{'arm':>5} {'seed':>5} {'survivors':>10} {'born':>6} "
          f"{'died':>6} {'acts':>7}")
    for arm in ARMS:
        for seed in args.seeds:
            r = play(arm, seed=seed, rounds=args.rounds, source=source)
            print(f"{arm:>5} {seed:>5} {r.survivors:>10} {r.born:>6} "
                  f"{r.died:>6} {r.acts_minted:>7}")


if __name__ == "__main__":
    main()
