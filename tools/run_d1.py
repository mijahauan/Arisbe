"""D-1: run the priced world across its four arms.

Design spec: docs/superpowers/specs/2026-08-02-d-series-building-the-stake-design.md

Usage:
    uv run python tools/run_d1.py                  # calibrate, then all arms
    uv run python tools/run_d1.py --rounds 60
    uv run python tools/run_d1.py --domains 16     # a wider field, re-measured
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
from d_world import PricedWorld, Source, demand_of, seats_from  # noqa: E402

ARMS = ("A0", "A1", "A2a", "A2b")
SEEDS = (1, 2, 3, 4, 5, 7, 42, 99)
ROUNDS = 60
MIN_WITNESSES = 3
DOMAINS = 8
"""The field's width, and with it the SEAT CEILING: under PAIRS a field of k
domains offers exactly C(k, 2) apertures and no two units may share a slice, so
8 domains cap the population at 28, 12 at 66, 16 at 120.

IT IS AN OPTION AND NOT A CONSTANT because spec section 8 item 6 pre-registers an
ESCALATION RULE: if a measured equilibrium reaches 80% of the ceiling in any arm,
the field grows and every figure is re-measured, since a population taken at a
binding ceiling is not an equilibrium at all -- the cap decided it, not the
economy. Growing the field also raises `units_for_witnesses`' N0, so the whole
calibration (tariff, t*, E0) must be re-measured at each width; nothing carries
across."""


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
    first_hit_round: Dict[str, int] = dc_field(default_factory=dict)
    """The round each unit's ledger first records a `"hit"` -- the quantity
    `calibrate` actually needs. Holding a law earns nothing; a hit earns.
    Kept ALONGSIDE `first_law_round` rather than replacing it: the law-round
    figure stays informative (a later task reads it), it is simply not what
    the entry price should be calibrated on."""
    demand_by_unit: Dict[str, List[Tuple[int, float]]] = dc_field(
        default_factory=dict)
    """For each unit, its `(round, demand)` pairs for every round it was
    alive -- fix round 3, the raw material `calibrate` needs to measure a
    tariff AFTER the fact. The baseline arm-0 run `calibrate` plays is
    UNPRICED (`tariff=0.0`, since it is not yet known), so `charges_by_unit`
    reads all zero there and cannot supply either price; this carries the
    demand `world.settle()` actually charged against, so a tariff measured
    later can be applied against real history rather than replayed."""
    hit_rounds: int = 0
    """How many of this run's rounds had at least one unit hit (i.e.
    `report.incomes` was non-empty) -- fix round 3, the other half of the
    tariff measurement: `tariff = pool_per_round * hit_rounds / total_demand`
    is the price at which the baseline community's total charge would have
    exactly equalled its total income (see `calibrate`)."""
    world: Optional[PricedWorld] = None
    n_domains: int = DOMAINS
    n0: int = 0
    seat_ceiling: int = 0
    pop_trace: List[int] = dc_field(default_factory=list)
    """Population at the END of each round -- the series the ESCALATION CHECK
    is read off. `max(pop_trace)` against 0.8 * `seat_ceiling` decides whether
    a settled number may be reported as an equilibrium at all."""
    death_trace: List[int] = dc_field(default_factory=list)
    """Deaths in each round. Population alone cannot date the first death,
    because a birth in the same round hides it -- P-D3 reads survival TIME and
    needs the death dated, not inferred."""
    lifespan: Dict[str, Tuple[int, int]] = dc_field(default_factory=dict)
    """unit_id -> (first round alive, last round alive). A founder starts at 0;
    a newborn at the round after its birth, since `settle` seats it at the end
    of one round and it first attends in the next."""
    holders_by_law: Dict[Tuple[str, str], int] = dc_field(default_factory=dict)
    """law content -> HOLDER-ROUNDS, summed over every round and every living
    unit that held it. P-D2's lineage length: how long a law persisted in the
    community, weighted by how many carried it."""
    units_by_law: Dict[Tuple[str, str], set] = dc_field(default_factory=dict)
    """law content -> the set of unit ids that ever held it. P-D2's other half:
    how far it spread."""
    planted: set = dc_field(default_factory=set)
    choice_histogram: Dict[int, int] = dc_field(default_factory=dict)
    """How many positive-standing peers stood behind a unit's preference, at
    every (unit, relation) for which ANY peer had earned one -- P-D4's question
    of whether a CHOICE existed. The C-series measured this degenerate: all 939
    uptake decisions had exactly one candidate, so `whom_to_ask` never chose
    anything. Read as {candidates: occurrences}, sampled once per round."""
    standing_by_unit: Dict[str, int] = dc_field(default_factory=dict)
    """unit_id -> its LAST observed count of positive-standing peer records.
    Crossed with `lifespan` this is P-D4's survival reading."""

    @property
    def total_charge(self) -> float:
        return sum(self.charges_by_unit.values())

    @property
    def peak_population(self) -> int:
        return max(self.pop_trace) if self.pop_trace else 0


def _planted(spec) -> set:
    return {d.law for d in spec.domains}


def play(arm: str, seed: int, rounds: int, source: Source,
         n_domains: int = DOMAINS) -> ArmResult:
    """One community, one seed, one arm.

    THE ROUND ORDER matters and is the C-series' own: adopt, attend, then the
    channel acts (publish/ask/challenge, answer, corroborate, dispose
    challenges, SETTLE CREDIT), then the world settles. Settling LAST means the round's acts
    are already on the board before anything is charged, so no charge can reach
    the acts it prices. CORROBORATE AND DISPOSE ARE NOT OPTIONAL (fix round 2):
    without them a challenge is minted, charged, and never resolves anything --
    `dispose_challenges` is the only route by which an induced law is ever
    suspended or retracted, so leaving it out made every law permanent once
    induced, true or false.

    THERE IS NO STAGGER. The C-series' bounded attention was a schedule imposed
    from outside; under a priced world every living unit attends every round and
    pays for it -- fix the price, let the quantum fall out."""
    if arm not in ARMS:
        raise ValueError(f"arm must be one of {ARMS}, got {arm!r}")
    # THE FIELD'S WIDTH IS AN ARGUMENT, NOT A CONSTANT (spec section 8 item 6).
    # It sets the seat ceiling AND, through `units_for_witnesses`, the founding
    # population: a wider field needs more units before every domain has three
    # witnesses, so N0 moves with it and no figure measured at one width may be
    # read at another.
    spec = wide_spec(seed=seed, n_domains=n_domains)
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
    first_hit: Dict[str, int] = {}
    charges: Dict[str, float] = {}
    demand_by_unit: Dict[str, List[Tuple[int, float]]] = {}
    hit_rounds = 0
    born = died = 0
    asked: Dict[str, list] = {}
    pop_trace: List[int] = []
    death_trace: List[int] = []
    lifespan: Dict[str, Tuple[int, int]] = {}
    holders_by_law: Dict[Tuple[str, str], int] = {}
    units_by_law: Dict[Tuple[str, str], set] = {}
    choice_histogram: Dict[int, int] = {}
    standing_by_unit: Dict[str, int] = {}

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
            # E0 must cover the time to first EARNING, not first belief: a
            # held law that has not yet paid off is not income. Read the
            # ledger `step` just populated for THIS round's own hits -- a
            # unit born mid-run reaches this line only once it is part of
            # `units` (the round after its birth), with its own fresh,
            # empty ledger, so it is recorded on its OWN first hit, never
            # skipped and never credited with a parent's.
            if u.unit_id not in first_hit and any(
                    e.round_idx == r and e.result == "hit"
                    for e in u.ledger.entries):
                first_hit[u.unit_id] = r
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
        if speak_board is not None:                       # (e) corroborate
            for u in units:
                u.corroborate(speak_board, r)
        if hear_board is not None:                        # (f) dispose
            # THE MISSING HALF OF THE DOUBT LIFECYCLE (fix round 2). Without
            # this call `challenge` mints marks that are counted and charged
            # like any other act but never resolve anything: `dispose_
            # challenges` is the SOLE caller of `_suspend` and one of only two
            # callers of `retract_law` in c_unit.py -- the only route by
            # which an induced law is ever suspended or retracted. Left out,
            # a unit bets on every law it induces, true or false, for the
            # rest of the run. Reads `hear_board`, mirroring (a)/(d): under
            # A2b it reads the permanently empty `void_board`, so a standing
            # challenge is minted and charged but can never be corroborated
            # or answered -- the same "cost held, sign removed" ablation the
            # rest of the round already applies.
            for u in units:
                u.dispose_challenges(hear_board, r)
        if hear_board is not None:                        # (g) settle credit
            # THE TYPIFY CHANNEL'S OTHER HALF, AND IT WAS MISSING (fix round 4,
            # found by RUNNING the measurement and reading zero). The C-series'
            # own driver closes the round with `settle_credit`
            # (`tests/test_c_channels.py`, step (i)); this one did not, and the
            # docstring above still claimed the order was "the C-series' own".
            # `credit` is called from nowhere else, so `Unit.peers` stayed
            # EMPTY at every unit, every seed and every arm -- 0 peer records,
            # not 0 positive ones -- and P-D4 had no instrument at all rather
            # than an inert one.
            #
            # IT CHANGES NO DYNAMICS, and that is itself the finding. Nothing
            # in the round reads `peers`: `ask` publishes its question to the
            # WHOLE board (c_unit.py: "what a question cannot do is choose whom
            # to ask") and (a) adopts `answer_to`, the first matching fact,
            # whoever wrote it. `whom_to_ask` has no consumer here, so the
            # preference cannot reach an act and the price cannot reach the
            # preference. Pinned by
            # `test_settling_credit_populates_peers_and_moves_no_dynamics`.
            for u in units:
                u.settle_credit(r)

        # RECORD EACH LIVING UNIT'S RAW DEMAND THIS ROUND (fix round 3) --
        # the same board state `world.settle()` is about to charge against --
        # so `calibrate` can measure a tariff and an entry price after the
        # fact even when this arm is played UNPRICED (`tariff=0.0`), where
        # `report.charges` would read all zero.
        for u in units:
            demand_by_unit.setdefault(u.unit_id, []).append(
                (r, demand_of(u, mint_board, r)))

        # THE READING PASS -- P-D2 and P-D4, which have no dedicated instrument
        # in this build and are read by hand off `Unit.laws` and `Unit.peers`
        # against the reserves. It observes and changes nothing.
        for u in units:
            start, _ = lifespan.get(u.unit_id, (r, r))
            lifespan[u.unit_id] = (start, r)
            for law in u.laws:                        # P-D2: lineage
                holders_by_law[law] = holders_by_law.get(law, 0) + 1
                units_by_law.setdefault(law, set()).add(u.unit_id)
            positive = 0                              # P-D4: was there a choice?
            by_relation: Dict[str, int] = {}
            for author, relations in u.peers.items():
                for relation in relations:
                    if u.standing_with(author, relation) > 0:
                        positive += 1
                        by_relation[relation] = by_relation.get(relation, 0) + 1
            for candidates in by_relation.values():
                choice_histogram[candidates] = (
                    choice_histogram.get(candidates, 0) + 1)
            standing_by_unit[u.unit_id] = positive

        # (g) the world. A0 NEVER BREEDS: it does not subtract, so a reserve
        # never falls and every unit would split every round until the seats ran
        # out -- an artefact of the control, not a finding. The control's job is
        # to leave the community exactly as it would have been.
        report = world.settle(units, r,
                              make_unit=None if arm == "A0" else make_unit)
        for uid, amount in report.charges.items():
            charges[uid] = charges.get(uid, 0.0) + amount
        if report.incomes:
            hit_rounds += 1
        born += len(report.born)
        died += len(report.died)
        units = list(report.units)
        pop_trace.append(len(units))
        death_trace.append(len(report.died))
        if not units:
            break

    return ArmResult(
        arm=arm, seed=seed, rounds=rounds, survivors=len(units),
        born=born, died=died,
        acts_minted=len(mint_board.all_marks()),
        final_units=units, charges_by_unit=charges,
        first_law_round=first_law, first_hit_round=first_hit,
        demand_by_unit=demand_by_unit, hit_rounds=hit_rounds, world=world,
        n_domains=n_domains, n0=n0,
        seat_ceiling=world.seats.free() + world.seats.occupied(),
        pop_trace=pop_trace, death_trace=death_trace, lifespan=lifespan,
        holders_by_law=holders_by_law, units_by_law=units_by_law,
        planted=planted, choice_histogram=choice_histogram,
        standing_by_unit=standing_by_unit)


def calibrate(seed_list=SEEDS, rounds: int = ROUNDS,
              n_domains: int = DOMAINS) -> Source:
    """Both prices, MEASURED off ONE arm-0 run per seed -- `tariff` before
    `entry_price` (E0), IN THAT ORDER, because E0 is a SUM OF CHARGES and a
    charge cannot be computed until a tariff exists to compute it with.

    `tariff` (fix round 3, author's ruling). Running the demand-normalised
    `tau = pool_per_round / demand` (fix rounds 1-2's form) exposed a deeper
    defect: total collected is EXACTLY `pool_per_round` every round no
    matter what the community does, so the tariff had no AGGREGATE bite --
    measured directly, `A2a` (the channel off entirely) and `A2b` (mints and
    is charged, reaches nobody) collected identically every round and
    finished every seed with IDENTICAL survivor/birth/death counts, though
    `A2b` minted thousands of acts `A2a` never touched. `tariff` REPLACES it
    as a CALIBRATED CONSTANT: the flat price per unit of demand at which the
    baseline community BREAKS EVEN over its own run -- total charge equals
    total income. Total income is `pool_per_round` times the number of
    ROUNDS with at least one hit (income is paid in full, once, whenever
    anyone hits that round); total charge is `tariff` times the summed
    demand over every unit and every round it was alive. Solving
    `tariff * total_demand == pool_per_round * hit_rounds`:

        tariff = pool_per_round * hit_rounds / total_demand

    summed across every seed in the list first, so one seed cannot set the
    price. Calibration is still MEASUREMENT, not choice -- that principle is
    unchanged; only the demand-normalised FORM was retired, because it gave
    the tariff no aggregate bite.

    THE BASELINE RUN ITSELF IS PLAYED UNPRICED (`Source(pool, 0.0, 0.0)`):
    neither price is known yet, so `ArmResult.charges_by_unit` reads all
    zero and cannot supply either measurement. `ArmResult.demand_by_unit`
    carries the raw per-round demand `world.settle()` actually charged
    against instead, so the just-measured `tariff` can be applied against
    real recorded history after the fact, with no need to replay anything.

    `t*` and `entry_price` (E0) are as fix round 1 left them: `t*` is the
    MEDIAN over units and seeds of the round of a unit's first hit (holding
    a law earns nothing; only a hit earns). `entry_price` is the MEDIAN over
    units of that unit's own cumulative charge through round `t*`
    (`tariff * demand_in_that_round`, summed over rounds `0..t*` from its
    own `demand_by_unit`). MEDIAN AT BOTH STEPS, so one lucky unit sets
    neither price.

    Returns a `Source(pool_per_round, entry_price, tariff)` rather than a
    bare float, since there are now two measured numbers and a caller needs
    both."""
    pool_per_round = 1.0
    baseline = Source(pool_per_round, 0.0, 0.0)

    total_demand = 0.0
    hit_rounds_total = 0
    rounds_to_hit: List[int] = []
    demand_by_unit: Dict[Tuple[int, str], List[Tuple[int, float]]] = {}

    for seed in seed_list:
        result = play("A0", seed=seed, rounds=rounds, source=baseline,
                      n_domains=n_domains)
        rounds_to_hit.extend(result.first_hit_round.values())
        hit_rounds_total += result.hit_rounds
        for uid, pairs in result.demand_by_unit.items():
            total_demand += sum(d for _, d in pairs)
            # Unit ids are only unique WITHIN one seed's run (u0, u1, ... are
            # re-minted fresh per seed), so key by (seed, uid) -- otherwise a
            # same-named unit from a different seed's run would silently
            # overwrite this one's demand history.
            demand_by_unit[(seed, uid)] = pairs

    if total_demand <= 0.0:
        raise RuntimeError(
            f"no unit ever held or spoke in {rounds} rounds over seeds "
            f"{list(seed_list)}: total demand is zero and tariff cannot be "
            f"measured"
        )
    tariff = pool_per_round * hit_rounds_total / total_demand

    if not rounds_to_hit:
        raise RuntimeError(
            f"no unit ever hit in {rounds} rounds over seeds "
            f"{list(seed_list)}: t* is undefined because nothing ever earned, "
            f"and entry_price cannot be measured"
        )
    t_star = statistics.median(rounds_to_hit)

    per_unit_charge_through_tstar = [
        sum(tariff * d for r, d in pairs if r <= t_star)
        for pairs in demand_by_unit.values()
    ]
    entry_price = statistics.median(per_unit_charge_through_tstar)

    return Source(pool_per_round, entry_price, tariff)


def main() -> None:
    parser = argparse.ArgumentParser(description="D-1: the priced world")
    parser.add_argument("--rounds", type=int, default=ROUNDS)
    parser.add_argument("--seeds", type=int, nargs="*", default=list(SEEDS))
    parser.add_argument(
        "--domains", type=int, default=DOMAINS,
        help="field width; sets the seat ceiling C(k,2) and, through "
             "units_for_witnesses, N0. Every price is re-measured at it.")
    args = parser.parse_args()

    source = calibrate(args.seeds, args.rounds, n_domains=args.domains)
    probe = wide_spec(seed=args.seeds[0], n_domains=args.domains)
    n0 = units_for_witnesses(probe, MIN_WITNESSES, PAIRS)
    ceiling = seats_from(probe).free()
    print(f"field: {args.domains} domains  seats = {ceiling}  N0 = {n0}  "
          f"(80% of ceiling = {0.8 * ceiling:.1f})")
    print(f"calibration: tariff = {source.tariff:.6f}  "
          f"E0 = {source.entry_price:.6f}  (both measured, not chosen)")

    print(f"\n{'arm':>5} {'seed':>5} {'survivors':>10} {'born':>6} "
          f"{'died':>6} {'acts':>7} {'charge':>10} {'peak':>6}")
    peak_overall = 0
    for arm in ARMS:
        for seed in args.seeds:
            r = play(arm, seed=seed, rounds=args.rounds, source=source,
                     n_domains=args.domains)
            peak_overall = max(peak_overall, r.peak_population)
            print(f"{arm:>5} {seed:>5} {r.survivors:>10} {r.born:>6} "
                  f"{r.died:>6} {r.acts_minted:>7} {r.total_charge:>10.3f} "
                  f"{r.peak_population:>6}")
    # THE ESCALATION CHECK, printed by the driver rather than left to the
    # reader: a population at or above 80% of the ceiling is the CAP's number
    # and not the economy's, and may not be reported as an equilibrium.
    print(f"\nescalation check: highest population {peak_overall} vs 80% of "
          f"{ceiling} = {0.8 * ceiling:.1f} -> "
          f"{'FIRES: re-measure at a wider field' if peak_overall >= 0.8 * ceiling else 'clear'}")


if __name__ == "__main__":
    main()
