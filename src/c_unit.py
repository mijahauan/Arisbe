"""One kytos, for C-series stage 1: it observes through its aperture,
anticipates from the laws it holds, and is scored at its own membrane.

It never reads the field's regime and never sees another unit. Communication
arrives in stage 3.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Dict, FrozenSet, List, Set, Tuple

from c_field import Aperture, Field
from c_membrane import MembraneLedger
from egi_core_dau import RelationalGraphWithCuts
from egif_parser_dau import parse_egif
from model_materialization import Fact, Key, materialize_egi


@dataclass
class Unit:
    unit_id: str
    aperture: Aperture
    facts: Set[Fact] = dc_field(default_factory=set)
    laws: Set[Tuple[str, str]] = dc_field(default_factory=set)
    ledger: MembraneLedger = dc_field(default_factory=MembraneLedger)
    last_provenance: Dict[Fact, FrozenSet[Fact]] = dc_field(default_factory=dict)

    def absorb(self, field: Field, round_idx: int) -> None:
        """Take in everything that arrived this round."""
        self.facts.update(field.at(self.aperture, round_idx))

    def as_egi(self) -> RelationalGraphWithCuts:
        """Render this unit's held content as a real EGI: each fact an atom on
        the sheet, each law a Horn cut ``~[ (body *x) ~[ (head x) ] ]``.

        This is the same EGIF idiom `model_revision.add_rule` uses, so a unit's
        model is the same kind of object the rest of Arisbe reasons over. Facts
        and laws are emitted in sorted order, so the rendering is a
        deterministic function of the unit's state.
        """
        parts: List[str] = []
        for rel, args in sorted(self.facts):
            for kind, label in args:
                if kind != "c":
                    raise ValueError(
                        f"{self.unit_id} holds a non-constant individual "
                        f"{(kind, label)!r} in ({rel} …); the C-series field "
                        f"delivers only named individuals, and emitting a "
                        f"generic line as a constant label would misrepresent it"
                    )
            labels = " ".join(f'"{a[1]}"' for a in args)
            parts.append(f"({rel} {labels})")
        for body_rel, head_rel in sorted(self.laws):
            parts.append(f"~[ ({body_rel} *x) ~[ ({head_rel} x) ] ]")
        return parse_egif(" ".join(parts) if parts else "")

    def anticipate(self) -> Set[Fact]:
        """Forward-chain the unit's own model and keep what it does not already
        hold. A prediction concerns what this unit has not yet seen.

        The chaining is the project's real materializer over the unit's own EGI
        — not a hand-rolled tuple match — so anticipation is a genuine least
        Herbrand closure (chained derivations included) and the support of every
        anticipation is recorded in ``last_provenance``.
        """
        if not self.laws or not self.facts:
            self.last_provenance = {}
            return set()
        provenance: Dict[Fact, FrozenSet[Fact]] = {}
        materialize_egi(self.as_egi(), provenance=provenance)
        self.last_provenance = provenance
        return {f for f in provenance if f not in self.facts}

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
