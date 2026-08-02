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
from typing import Dict, List


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


__all__ = ["Source", "Reserves"]
