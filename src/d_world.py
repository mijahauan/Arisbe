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
from typing import Dict, List, Optional, Tuple

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
    it is not yet known, and a zero entry price breeds not at all."""

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
        """Total wealth. Conservative except on hitless rounds, where the pool
        is charged and nothing is paid back -- which is how a community comes to
        have a lifespan of its own doing."""
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


__all__ = ["Source", "Reserves", "Seats", "SeatsFull", "seats_from"]
