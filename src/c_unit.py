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
    first_seen: Dict[Fact, int] = dc_field(default_factory=dict)
    """The round each fact was FIRST held. Only ever written, never revised: a
    fact re-delivered later does not move its first arrival. This is the unit's
    own record of its own history — it reads no round order off the field, only
    off when things reached its own membrane — and it is what lets `induce`
    tell a law from its converse (see `induce`)."""

    def _record(self, arrived: Set[Fact], round_idx: int) -> None:
        """Hold what arrived, and note the round for anything new."""
        for f in arrived:
            if f not in self.first_seen:
                self.first_seen[f] = round_idx
        self.facts.update(arrived)

    def absorb(self, field: Field, round_idx: int) -> None:
        """Take in everything that arrived this round."""
        self._record(set(field.at(self.aperture, round_idx)), round_idx)

    def retract_law(self, law: Tuple[str, str]) -> bool:
        """Give up a law, reporting whether it had been held.

        Retraction is the counterpart of induction: without it a law once
        proposed could only ever be outlived, never defeated, and the challenge
        channel would have nothing to dispose into. The return value is the
        honest part — a caller that retracts what was never held learns so,
        rather than being told a defeat happened."""
        held = law in self.laws
        self.laws.discard(law)
        return held

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

    def _body_precedes_head(self, body_rel: str, head_rel: str,
                            support: Set[Tuple[Key, ...]]) -> bool:
        """Did the body arrive no later than the head, for most of the
        individuals that carry both?

        THIS IS WHAT TELLS A LAW FROM ITS CONVERSE. Co-occurrence is symmetric
        and implication is not, so support and counterexample tolerance alone
        cannot distinguish `body -> head` from `head -> body`: both hold of
        exactly the same individuals. What breaks the symmetry is time. The
        field delivers a consequent one round AFTER its antecedent, so for a law
        the field really carries the body is seen first, and for its converse the
        body (the real head) is seen second.

        THE CRITERION IS A STRICT MAJORITY of the supporting individuals for
        which the unit has a first-arrival on both facts — not all of them.
        Requiring precedence everywhere would be too strict under a fallible
        field: a spurious head arrives with no antecedent to license it, so it
        can reach an individual BEFORE that individual's body ever arrives, and
        one such case would veto a true law forever. A majority tolerates those
        while still refusing a converse outright.

        THE MARGIN IS WIDE, which is why a majority is enough rather than a
        tuned fraction. Measured over the fourteen seeds this suite uses, 60
        rounds, all twenty body->head pairs on unit u0's aperture: the PLANTED
        laws score 0.89 to 1.00 on this proportion and their CONVERSES score
        0.00 to 0.11. Nothing measured lands between 0.11 and 0.38, so the 0.5
        cut is not near any observed value. (The mid-range pairs that do sit
        near 0.5 — `shared -> a_head` and the like, 0.50 to 0.65 — are refused
        by the pending rate instead, at 0.52 to 0.63 pending.)

        A tie counts as precedence, so the test is `<=` rather than `<`: two
        facts first held in the same round say nothing against either
        direction. ABSENT TIMING EVIDENCE IS NOT COUNTER-EVIDENCE — if the unit
        has no first-arrival for any supporting individual (facts placed
        directly rather than absorbed from a field), the test abstains and
        passes rather than silently refusing every law."""
        timed = [(self.first_seen[(body_rel, a)], self.first_seen[(head_rel, a)])
                 for a in support
                 if (body_rel, a) in self.first_seen
                 and (head_rel, a) in self.first_seen]
        if not timed:
            return True
        precedent = sum(1 for body_at, head_at in timed if body_at <= head_at)
        return precedent * 2 > len(timed)

    def induce(self, min_support: int = 3,
               max_pending_rate: float = 0.05) -> Set[Tuple[str, str]]:
        """Propose body -> head where enough individuals carry both, few enough
        carry body without head, and the body was seen first.

        THE TOLERANCE IS A RATE, NOT A COUNT. A count is measured against a
        monotonically growing fact set, so it silently tightens over a run: one
        pending individual out of five is a very different claim from one out of
        forty, and an absolute `max_pending` reads them alike. A proportion
        keeps the tolerance's meaning fixed as the record grows, and it is what
        lets a true law survive the field's withheld consequents — a withheld
        consequent leaves its individual permanently pending — while a false law
        with fifteen-plus outstanding individuals still falls.

        DIRECTION COMES FROM PRECEDENCE, not from support. See
        `_body_precedes_head`: without it this criterion admits every law's
        converse alongside it, because the two are supported by exactly the same
        individuals."""
        holders: Dict[str, Set[Tuple[Key, ...]]] = {}
        for rel, args in self.facts:
            holders.setdefault(rel, set()).add(args)
        found: Set[Tuple[str, str]] = set()
        for body_rel, body_args in sorted(holders.items()):
            for head_rel, head_args in sorted(holders.items()):
                if body_rel == head_rel:
                    continue
                support = body_args & head_args
                if len(support) < min_support:
                    continue
                if len(body_args - head_args) > max_pending_rate * len(body_args):
                    continue
                if not self._body_precedes_head(body_rel, head_rel, support):
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
        self._record(arrived, round_idx)
        if induce:
            self.induce()
