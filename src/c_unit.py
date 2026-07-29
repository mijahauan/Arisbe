"""One kytos, for C-series stage 1: it observes through its aperture,
anticipates from the laws it holds, and is scored at its own membrane.

It never reads the field's regime and never sees another unit. Communication
arrives in stage 3.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Dict, Set, Tuple

from c_field import Aperture, Field
from c_membrane import MembraneLedger
from model_materialization import Fact, Key


@dataclass
class Unit:
    unit_id: str
    aperture: Aperture
    facts: Set[Fact] = dc_field(default_factory=set)
    laws: Set[Tuple[str, str]] = dc_field(default_factory=set)
    ledger: MembraneLedger = dc_field(default_factory=MembraneLedger)

    def absorb(self, field: Field, round_idx: int) -> None:
        """Take in everything that arrived this round."""
        self.facts.update(field.at(self.aperture, round_idx))

    def anticipate(self) -> Set[Fact]:
        """Apply every held law to held facts; keep only what is not already
        held. A prediction concerns what this unit has not yet seen."""
        out: Set[Fact] = set()
        for body_rel, head_rel in self.laws:
            for rel, args in self.facts:
                if rel == body_rel:
                    candidate: Fact = (head_rel, args)
                    if candidate not in self.facts:
                        out.add(candidate)
        return out

    def induce(self, min_support: int = 3,
               max_pending: int = 1) -> Set[Tuple[str, str]]:
        """Propose body -> head where enough individuals carry both and at
        most `max_pending` carry body without head.

        The tolerance is the field's one-round lag: the antecedent just
        delivered has not had its consequent delivered yet, so exactly one
        individual per body relation is legitimately pending. Zero tolerance
        would read that timing artifact as a refutation and block every true
        law permanently."""
        holders: Dict[str, Set[Tuple[Key, ...]]] = {}
        for rel, args in self.facts:
            holders.setdefault(rel, set()).add(args)
        found: Set[Tuple[str, str]] = set()
        for body_rel, body_args in sorted(holders.items()):
            for head_rel, head_args in sorted(holders.items()):
                if body_rel == head_rel:
                    continue
                if len(body_args & head_args) < min_support:
                    continue
                if len(body_args - head_args) > max_pending:
                    continue
                law = (body_rel, head_rel)
                if law not in self.laws:
                    found.add(law)
        self.laws.update(found)
        return found

    def step(self, field: Field, round_idx: int, induce: bool = False) -> None:
        """One round: anticipate from what is held, observe what arrives, be
        scored on the forecast, then optionally induce from the enlarged
        record. Inducing last means a law never scores the round that taught
        it. The bet is placed before the outcome is seen."""
        anticipated = self.anticipate()
        arrived = set(field.at(self.aperture, round_idx))
        self.ledger.score(anticipated, arrived, round_idx)
        self.facts.update(arrived)
        if induce:
            self.induce()
