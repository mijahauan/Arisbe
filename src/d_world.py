"""The D-series priced world: where the C-series' cost meter becomes a
subtraction.

THE WHOLE OMISSION THIS CLOSES. The E-series meter charging `sum |M|`, the
`MembraneLedger` scoring hits and misses, `Field.deliver` delivering and
`Unit.anticipate` anticipating -- all of it exists, and all of it is an
observer's scorecard, computed beside the system and affecting nothing.
Nothing was ever subtracted from anything.

WHAT IS DELIBERATELY ABSENT, each refused for a reason recorded in the design
spec's section 9: a chooser, a sense organ for the reserve, a `die()`, a TTL, a
lifespan, a genome, a mutation operator, an attempt-ordering rule, and any price
set by hand.

THE RESERVE IS NOT ON `Unit`. The world holds it, keyed by unit id. That is not
a discipline anyone has to remember -- the architecture enforces it, because a
unit cannot read what it does not have -- and it puts the reserve where
THE_KYTOS section 1.3 says an act's effect resides: in the RESOURCES, outside
the membrane, never in a private field beside the act.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from c_field import PAIRS, Aperture, FieldSpec, apertures_for


@dataclass(frozen=True)
class Source:
    """The world's bounded sustenance, and the price of entering it.

    `pool_per_round` is E1 and is THE NUMERAIRE: it fixes the unit of account
    and nothing else, so it is never varied. Every other quantity in this module
    is a pool-share.

    `entry_price` is E0, MEASURED rather than chosen -- the charge a median unit
    accrues over the rounds it takes the measured baseline learner to induce its
    first law (design spec section 4). It is zero in the calibration arm, where
    it is not yet known, and a zero entry price breeds not at all.

    BOTH FIELDS ARE ASSUMED NON-NEGATIVE. Nothing constructs a `Source` with a
    negative `pool_per_round` or `entry_price`, and this is a precondition,
    not a validated one -- a guard here would be speculative. `PricedWorld`'s
    "a balance never goes below zero" guarantee (see `PricedWorld.settle`)
    relies on it: a negative `pool_per_round` would pay negative income, and
    a negative `entry_price` would invert the reproduction threshold."""

    pool_per_round: float = 1.0
    entry_price: float = 0.0


class Reserves:
    """Every unit's holdings, held OUTSIDE every membrane.

    Death is `balance <= 0` and nothing else. Exactly zero is dead rather than
    a last breath, so that the boundary is one comparison and not two."""

    def __init__(self) -> None:
        self._amounts: Dict[str, float] = {}

    def seed(self, unit_id: str, amount: float) -> None:
        """Endow a unit at entry. ONCE, EVER -- re-seeding would create wealth
        from nothing, and the conservation property (see `PricedWorld.settle`)
        is what makes the whole measurement readable."""
        if unit_id in self._amounts:
            raise ValueError(
                f"{unit_id} is already endowed at {self._amounts[unit_id]}: "
                f"a unit is endowed once, at entry, and re-seeding would create "
                f"wealth from nothing"
            )
        self._amounts[unit_id] = amount

    def credit(self, unit_id: str, amount: float) -> None:
        self._amounts[unit_id] = self._amounts.get(unit_id, 0.0) + amount

    def charge(self, unit_id: str, amount: float) -> None:
        self._amounts[unit_id] = self._amounts.get(unit_id, 0.0) - amount

    def balance(self, unit_id: str) -> float:
        return self._amounts.get(unit_id, 0.0)

    def alive(self, unit_id: str) -> bool:
        return self._amounts.get(unit_id, 0.0) > 0.0

    def drop(self, unit_id: str) -> None:
        self._amounts.pop(unit_id, None)

    def total(self) -> float:
        """Total wealth. NOT A FIXED STOCK -- the world is open: an external
        source pays income to predictors, and the tariff dissipates what each
        unit can actually pay, so this figure moves both ways.

        THE EXACT INVARIANT, true every round by construction (see
        `PricedWorld.settle`, which computes both terms):

            total_after == total_before - collected + incomes

        where `collected` is what the tariff actually took (bounded by each
        unit's own balance) and `incomes` is what the external source paid in
        (the pool, split pro rata by hits). A hitless round still burns:
        nothing enters and `collected` still leaves, which is how a community
        comes to have a lifespan of its own doing. When a unit cannot pay in
        full, LESS leaves than the price demanded while the full pool still
        enters, so this figure can RISE in a round where a peer starves --
        the survivors are not charged for a dead unit's shortfall."""
        return sum(self._amounts.values())

    def living(self) -> List[str]:
        """Sorted, so anything downstream of it is deterministic."""
        return sorted(u for u, a in self._amounts.items() if a > 0.0)


class SeatsFull(Exception):
    """No slice of the field is free. RAISED, NEVER DEGRADED: handing a newcomer
    an occupied aperture would seat a twin, and premise 3 requires units to meet
    the field differently. Whether a unit BORN onto an occupied slice is the same
    case as one SEEDED onto it is the design spec's section 11.1 candidate, and
    it is unruled -- so this refuses until it is."""


class Seats:
    """The slices of the field a community may occupy, and who holds them.

    THE CEILING IS THE WORLD'S, not a parameter. `apertures_for` yields C(k, 2)
    distinct two-domain slices over k domains and refuses to seat two units on
    one, so the field's width is the population ceiling and nobody chose a
    maximum."""

    def __init__(self, domain_sets: List[Tuple[str, ...]]):
        self._domain_sets = list(domain_sets)
        self._occupant: List[Optional[str]] = [None] * len(self._domain_sets)

    def take(self, unit_id: str) -> Aperture:
        """Seat `unit_id` on the lowest free slice and hand back ITS OWN
        aperture.

        Lowest-free rather than next-in-sequence so that a run is a
        deterministic function of who died and when, and not of an allocation
        counter that remembers history nobody can read.

        The aperture is MINTED HERE with the occupant's id, because `Field.at`
        reads `aperture.unit_id` as the observer and a newcomer inheriting the
        previous occupant's object would meet the field through a dead unit's
        membrane."""
        for i, held in enumerate(self._occupant):
            if held is None:
                self._occupant[i] = unit_id
                return Aperture(unit_id=unit_id, domains=self._domain_sets[i])
        raise SeatsFull(
            f"no free seat for {unit_id}: all {len(self._domain_sets)} slices of "
            f"this field are occupied, and seating a twin would defeat premise 3"
        )

    def release(self, unit_id: str) -> None:
        for i, held in enumerate(self._occupant):
            if held == unit_id:
                self._occupant[i] = None
                return
        raise ValueError(f"{unit_id} is not seated in this world")

    def free(self) -> int:
        return sum(1 for held in self._occupant if held is None)

    def occupied(self) -> int:
        return sum(1 for held in self._occupant if held is not None)


def seats_from(spec: FieldSpec, scheme: str = PAIRS) -> Seats:
    """Every distinct slice `scheme` allows over `spec` -- the world's ceiling,
    read off the field rather than declared."""
    k = len(spec.domains)
    ceiling = k if scheme != PAIRS else k * (k - 1) // 2
    return Seats([ap.domains
                  for ap in apertures_for(spec, ceiling, scheme=scheme)])


def demand_of(unit, board, round_idx: int) -> float:
    """What this unit asks of the world this round: everything it holds, plus
    every mark it minted.

    A HELD FACT-ROUND AND A MINTED ACT EACH COUNT 1. That is a choice of units
    and it is the NULL one -- it asserts no difference between holding and
    speaking. It replaces the design's earlier 50/50 split, which asserted the
    same thing more contrivedly, by equalising totals that depend on how many
    facts and acts happen to occur.

    AN ACT IS A MARK MINTED -- by `publish`, `ask`, `answer`, `challenge` or
    `corroborate`, without distinction between them. Charging the kinds at
    different rates would be a designer's claim about which speech is dear, and
    the design refuses to make one.

    ENCOUNTERING A MARK IS FREE. `Unit.read` returns the whole board with no
    filter and no chooser, so a price per mark READ would make each unit's cost
    proportional to community size by construction -- total cost as N squared,
    an exponent written rather than found. Pricing minted acts leaves per-unit
    cost independent of N, so any superlinearity has to be earned."""
    acts = sum(1 for m in board.since(round_idx)
               if m.round_idx == round_idx and m.author == unit.unit_id)
    return float(len(unit.facts) + len(unit.laws) + acts)


def hits_of(unit, round_idx: int) -> int:
    """This round's matches: anticipated AND arrived.

    Read straight off `MembraneLedger.entries`, so the world introduces no new
    statistic and scores matches and nothing else. No credit for communicating,
    corroborating or typifying -- if those pay, they pay only by producing
    better anticipations."""
    return sum(1 for e in unit.ledger.entries
               if e.round_idx == round_idx and e.result == "hit")


@dataclass(frozen=True)
class RoundReport:
    """What the world did this round. Observability -- no unit reads it."""
    round_idx: int
    demand: float
    tau: Optional[float]
    collected: float
    charges: Dict[str, float]
    incomes: Dict[str, float]
    born: Tuple[Tuple[str, str], ...]
    died: Tuple[str, ...]
    units: Tuple[Any, ...]


class PricedWorld:
    """A bounded source, a price that clears it, and reserves held outside every
    membrane.

    NOTHING IS EVER DECLINED. A unit acts exactly as it would with no world at
    all; the tariff subtracts regardless; running out is death. The alternative
    -- refusing acts a unit cannot afford -- was rejected because whoever fixes
    the ATTEMPT ORDER fixes the priority, and which act gets dropped first is a
    substantive claim a designer would be making on the world's behalf. This
    still governs every ACT: nothing a unit does is ever refused.

    THE PRICE IS DETERMINED, NOT SET. `tau = pool / demand` is whatever clears
    the world's bounded supply against what the community actually did. It is
    not a negotiation: nobody bargains and nobody may refuse, which would need
    the chooser this design excludes.

    EXTRACTION IS BOUNDED, WHICH IS NOT DECLINING. The nominal charge
    `tau * demand` is a meter reading and is reported in full, unchanged, in
    `RoundReport.charges`. What the world actually TAKES is bounded by what a
    unit actually HOLDS -- you cannot take 0.99 out of something holding
    0.5 -- so `collected = min(charge, balance)`. That is exhaustion, not
    refusal: the unit still held its model, still minted its marks, still
    acted, and none of that was ever declined. Only extraction is bounded, and
    a bound is not a choice among candidates. NO UNIT CAN EVER END IN DEBT:
    extraction never exceeds what exists, so a dying unit lands at exactly
    0.0, never below it, and there is no debt to forgive.

    THE WORLD IS OPEN, NOT CLOSED. `pool_per_round` is a genuine inflow from
    a source OUTSIDE the community -- the design spec calls it "how much
    sustenance exists per round" -- and it enters in full whenever anyone
    hits, independent of what the tariff could collect. Conservation of
    energy does not require a closed system; it requires that nothing be
    created or destroyed WITHIN the system while accounting honestly for
    what crosses its boundary. The exact invariant, true every round by
    construction:

        total_after == total_before - collected + sum(incomes)

    where `collected` is the outflow (bounded by what existed to take) and
    `sum(incomes)` is the inflow (the pool, split pro rata by hits, paid in
    full whenever `total_hits > 0`). A round with no hits pays nothing in and
    still takes `collected` out -- so a community has a lifespan, and it is
    its own doing. A round where someone is too exhausted to pay in full
    takes LESS than the nominal charge out while the SAME pool comes in, so
    total wealth can RISE on a round where a peer starves -- the survivors
    are not charged for a dead unit's shortfall, and the inflow came from
    outside them. That is accepted, not compensated for."""

    def __init__(self, source: Source, seats: Seats, board,
                 subtract: bool = True):
        self.source = source
        self.seats = seats
        self.board = board
        self.subtract = subtract
        """False is ARM 0: the charge computed and reported but never applied,
        which is exactly today's system. It is the control and the calibration
        source, and it is the only coherent control now that price is
        determined, since `tau = pool / demand` has no zero."""
        self.reserves = Reserves()
        self._next_id = 0

    def admit(self, unit) -> None:
        """Seat a unit and record its id for newborn naming. It is NOT endowed
        here -- endowment is the caller's, because the calibration arm has no
        entry price yet."""
        self.seats.take(unit.unit_id)
        if unit.unit_id.startswith("u") and unit.unit_id[1:].isdigit():
            self._next_id = max(self._next_id, int(unit.unit_id[1:]) + 1)

    def _mint_id(self) -> str:
        uid = f"u{self._next_id}"
        self._next_id += 1
        return uid

    def settle(self, units: Sequence, round_idx: int,
               make_unit=None) -> RoundReport:
        """Charge, pay, then let the population settle.

        THE ORDER IS THE MEASUREMENT: the round's acts are already done and on
        the board before anything is charged, so no charge can reach the acts it
        prices. Births and deaths come last, so a unit is judged on the round it
        actually played.

        `charges` IS THE NOMINAL METER READING (`tau * demand`), reported in
        full regardless of what a unit can actually pay. `collected` (the dict)
        is what the world actually takes -- bounded by each unit's own
        balance, so extraction can never drive a balance below zero;
        `RoundReport.collected` (the total) is its sum, the round's OUTFLOW.
        Income is the round's INFLOW, drawn from the full external
        `pool_per_round` and split pro rata by hits -- not from what was
        collected -- so the community is fed from outside it, not merely
        redistributed among its own dwindling stock."""
        living = [u for u in units]
        demand = sum(demand_of(u, self.board, round_idx) for u in living)
        tau = (self.source.pool_per_round / demand) if demand > 0 else None

        charges: Dict[str, float] = {}
        if tau is not None:
            for u in living:
                charges[u.unit_id] = tau * demand_of(u, self.board, round_idx)

        collected: Dict[str, float] = {}
        for uid, amount in charges.items():
            collected[uid] = (min(amount, self.reserves.balance(uid))
                               if self.subtract else amount)
        total_collected = sum(collected.values())

        total_hits = sum(hits_of(u, round_idx) for u in living)
        incomes: Dict[str, float] = {}
        if total_hits > 0:
            for u in living:
                h = hits_of(u, round_idx)
                if h:
                    incomes[u.unit_id] = (
                        self.source.pool_per_round * h / total_hits)

        if self.subtract:
            for uid, amount in sorted(collected.items()):
                self.reserves.charge(uid, amount)
            for uid, amount in sorted(incomes.items()):
                self.reserves.credit(uid, amount)

        born, died, living = self._settle_population(living, make_unit)
        return RoundReport(round_idx=round_idx, demand=demand, tau=tau,
                           collected=total_collected, charges=charges,
                           incomes=incomes, born=born, died=died,
                           units=tuple(living))

    def _settle_population(self, living, make_unit):
        """Who left, then who arrived.

        DEATH FIRST, so a seat freed this round is available this round and a
        community at the ceiling can still turn over.

        BIRTH SPLITS THE RESERVE IN HALF rather than issuing each unit the entry
        price, which keeps it CONSERVATIVE: a parent at three times the entry
        price yields two units at one and a half times it, not two at the entry
        price with the remainder burned. Wealth is redistributed and never
        created or destroyed, which is what makes the conservation reading
        meaningful.

        THE THRESHOLD IS NOT A CHOSEN MULTIPLE. The entry price IS what it costs
        to enter this world, so `2 * entry_price` reads: you may reproduce when
        you can pay a newcomer's entry and remain viable yourself. A world with
        no entry price -- the calibration arm, where it is not yet measured --
        does not breed at all, since a zero threshold would split every unit
        every round.

        A FULL WORLD SIMPLY DOES NOT BREED. `SeatsFull` is the right refusal
        when someone asks for a seat, but a world with no room is a fact about
        the world and not an error the run should die on."""
        died = []
        for u in list(living):
            if not self.reserves.alive(u.unit_id):
                self.seats.release(u.unit_id)
                self.reserves.drop(u.unit_id)
                died.append(u.unit_id)
        survivors = [u for u in living if u.unit_id not in set(died)]

        born = []
        if make_unit is not None and self.source.entry_price > 0.0:
            threshold = 2.0 * self.source.entry_price
            for u in list(survivors):
                if self.reserves.balance(u.unit_id) < threshold:
                    continue
                if self.seats.free() == 0:
                    break
                child_id = self._mint_id()
                aperture = self.seats.take(child_id)
                half = self.reserves.balance(u.unit_id) / 2.0
                self.reserves.charge(u.unit_id, half)
                self.reserves.seed(child_id, half)
                survivors.append(make_unit(child_id, aperture))
                born.append((u.unit_id, child_id))

        return tuple(born), tuple(died), survivors


__all__ = ["Source", "Reserves", "Seats", "SeatsFull", "seats_from",
           "demand_of", "hits_of", "RoundReport", "PricedWorld"]
