"""One kytos: it observes through its aperture, anticipates from the laws it
holds, and is scored at its own membrane.

It never reads the field's regime. As of stage 3 it can also publish what it
holds as an objectivated mark, read what its community has published, and adopt
another unit's mark — but it still never inspects another unit; what it meets is
an inscription on a board (see `c_marks`).
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from c_field import Aperture, Field
from c_marks import (CHALLENGE, CORROBORATION, FACT, LAW, QUESTION, Content,
                     Mark, MarkBoard)
from c_membrane import MembraneLedger
from egi_core_dau import RelationalGraphWithCuts
from egif_parser_dau import parse_egif
from model_materialization import Fact, Key, materialize_egi

MIN_SUPPORT = 3
MAX_PENDING_RATE = 0.05
"""THE ONE STANDARD, named once and read twice: by `induce`, which decides
whether to take a law up, and by `_meets_criterion`, which decides — when a
challenge puts a held law in doubt — whether the unit's own record still
sustains it.

THE SAME STANDARD MUST GOVERN HOLDING A LAW AND LOSING IT. Task 5 measured what
happens when it does not: admission tolerated a 5% pending RATE while the
disposition rule fired on any ONE pending individual, so every law admitted with
a nonzero pending rate was defeasible the moment it was published, and 98
distinct defeats became 426 retraction events as induction re-admitted what the
challenge rule had just destroyed. Two criteria at different strengths do not
disagree occasionally; they fight continuously. These constants are the fix, and
they are module-level rather than per-call defaults so that the two readers
cannot drift apart."""


@dataclass
class Doubt:
    """One live doubt about one law: what opened it, about whom, and when.

    HELD BESIDE `Unit.suspended` RATHER THAN INSIDE IT, because the ruling asks
    for a suspended SET — the thing `anticipate` consults — and a set cannot
    carry a clock. `Unit._suspend` and `Unit._unsuspend` are the only writers of
    either, so the invariant `set(self._doubts) == self.suspended` holds by
    construction.

    `challenger` is who raised the doubt, and it is kept for one reason: THE
    ORIGINAL CHALLENGER'S EVIDENCE MUST NOT COUNT TWICE. Corroboration means
    another record independently bearing on the same law, so the unit that
    opened the doubt cannot also close it.
    """

    challenger: str
    individual: Tuple[Key, ...]
    opened_at: int


@dataclass
class Disposition:
    """What one pass of `Unit.dispose_challenges` did, split by WHY.

    The splits are the measurement. A law given up because the unit's own record
    no longer sustains it is a different event from one given up because peers
    corroborated a doubt, and reporting them as one number would hide exactly
    the thing the ruling changed.
    """

    retracted_internally: List[Tuple[str, str]] = dc_field(default_factory=list)
    """Given up by the unit's own re-assessment: the law no longer meets the
    criterion the unit would use to induce it today. No corroboration was
    needed — the doubt was settled inside the membrane."""
    suspended: List[Tuple[str, str]] = dc_field(default_factory=list)
    """Put in doubt: still held, still on the record, licensing nothing, with a
    call for corroboration published."""
    retracted_by_corroboration: List[Tuple[str, str]] = dc_field(
        default_factory=list)
    """Given up because an independent peer's record bore out the doubt."""
    restored_by_rebuttal: List[Tuple[str, str]] = dc_field(default_factory=list)
    """Returned to active: the disputed individual turned out to carry the head
    after all, in this unit's own record or in a peer's published testimony."""
    restored_by_silence: List[Tuple[str, str]] = dc_field(default_factory=list)
    """Returned to active: the call went unanswered for the whole window, so
    the challenge failed to gather support."""

    def __bool__(self) -> bool:
        return bool(self.retracted_internally or self.suspended
                    or self.retracted_by_corroboration
                    or self.restored_by_rebuttal or self.restored_by_silence)


@dataclass
class Unit:
    unit_id: str
    aperture: Aperture
    facts: Set[Fact] = dc_field(default_factory=set)
    laws: Set[Tuple[str, str]] = dc_field(default_factory=set)
    suspended: Set[Tuple[str, str]] = dc_field(default_factory=set)
    """The laws this unit holds but does not act on: challenged, not rebutted,
    not yet corroborated. A SUBSET OF `laws` — a suspended law is still on the
    record and is still published; what it has lost is its licence. `anticipate`
    skips it, so it stakes nothing and can neither win nor lose while the doubt
    stands.

    THIS IS THE AUTHOR'S RULING: *corroborate and suspend, but do not eliminate
    until corroboration.* Task 5 measured the alternative — a foreign
    counterexample retracting a law outright — and found that under a fallible
    field it destroyed 58 of 58 laws the field actually carries, and that under
    bounded attention it destroyed 64 of 64 true laws while sparing 30 of 32
    false ones, because rebuttability tracks how common the head relation is in
    the author's record rather than whether the law is true. Suspension is what
    lets a doubt be entertained without being obeyed."""
    corroboration_window: int = 5
    """How many rounds a call for corroboration stands before silence restores
    the law. DEFAULT 5, and it is a choice rather than a measurement.

    THE RATIONALE IS THE RULING'S OWN. A challenge that gathers no support has
    failed, and "do not eliminate until corroboration" means silence cannot
    eliminate — so the window must end in restoration, not in retraction. Five
    rounds is long enough for the community to have spoken several times (the
    field's lag is one round, and under bounded attention a peer attends every
    other round, so five rounds is two or three chances for every peer to publish
    what bears on the case) and short enough that a law is not mute for a
    material part of a sixty-round run. Nothing measured here picks 5 over 3 or
    8; it is flagged as the author's to overrule."""
    ledger: MembraneLedger = dc_field(default_factory=MembraneLedger)
    last_provenance: Dict[Fact, FrozenSet[Fact]] = dc_field(default_factory=dict)
    first_seen: Dict[Fact, int] = dc_field(default_factory=dict)
    """The round each fact was FIRST held. Only ever written, never revised: a
    fact re-delivered later does not move its first arrival. This is the unit's
    own record of its own history — it reads no round order off the field, only
    off when things reached its own membrane — and it is what lets `induce`
    tell a law from its converse (see `induce`).

    FIRST-HAND ONLY. An adopted mark does not write here; the argument is in
    `adopt`."""
    _published: Set[Tuple[str, Content]] = dc_field(default_factory=set)
    """What this unit has already published, as `(kind, content)` pairs — not as
    marks, since a mark carries the round it was published in and would compare
    unequal every round, so the unit would republish everything forever."""
    _doubts: Dict[Tuple[str, str], Doubt] = dc_field(default_factory=dict)
    """The live doubt behind each suspended law. Keyed identically to
    `suspended`; see `Doubt`."""
    _spent: Set[Mark] = dc_field(default_factory=set)
    """Every challenge mark this unit has already disposed of — retracted under,
    restored against, or rebutted.

    A CHALLENGE IS DISPOSED OF ONCE, EVER, which is the discipline every other
    act in this module already keeps (`publish`, `ask` and `challenge` are all
    once per content, ever). Without it the channel oscillates on its own: a law
    restored by silence meets the same unanswered challenge at the next round and
    is suspended again forever, and a law retracted under corroboration and later
    re-induced from a grown record is killed again by evidence that has already
    been weighed. What can raise a fresh doubt is FRESH EVIDENCE — a challenge
    from a peer that has not yet spoken — and that is precisely what corroboration
    means here.

    Marks, not laws: the unit is keeping track of which INSCRIPTIONS it has
    answered for, and a mark is frozen and hashable so it can key itself."""

    def _record(self, arrived: Set[Fact], round_idx: int) -> None:
        """Hold what arrived, and note the round for anything new."""
        for f in arrived:
            if f not in self.first_seen:
                self.first_seen[f] = round_idx
        self.facts.update(arrived)

    def _suspend(self, law: Tuple[str, str], doubt: Doubt) -> None:
        """Put a law in doubt: held, published, licensing nothing."""
        self.suspended.add(law)
        self._doubts[law] = doubt

    def _unsuspend(self, law: Tuple[str, str]) -> None:
        """Lift a doubt, whether because the law was restored or because it was
        given up. Both writers go through here so the set and the clock cannot
        drift apart."""
        self.suspended.discard(law)
        self._doubts.pop(law, None)

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
        self._unsuspend(law)        # a law given up is not a law in doubt
        return held

    def as_egi(self, laws: Optional[Set[Tuple[str, str]]] = None
               ) -> RelationalGraphWithCuts:
        """Render this unit's held content as a real EGI: each fact an atom on
        the sheet, each law a Horn cut ``~[ (body *x) ~[ (head x) ] ]``.

        This is the same EGIF idiom `model_revision.add_rule` uses, so a unit's
        model is the same kind of object the rest of Arisbe reasons over. Facts
        and laws are emitted in sorted order, so the rendering is a
        deterministic function of the unit's state.

        `laws` narrows which of the unit's laws are drawn, and it exists for one
        caller: `anticipate`, which reasons from the ACTIVE laws only. The
        default renders everything held, suspended laws included, because that
        is what the unit's record contains — suspension withdraws a law's
        licence, not the law.
        """
        laws = self.laws if laws is None else laws
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
        for body_rel, head_rel in sorted(laws):
            parts.append(f"~[ ({body_rel} *x) ~[ ({head_rel} x) ] ]")
        return parse_egif(" ".join(parts) if parts else "")

    def anticipate(self) -> Set[Fact]:
        """Forward-chain the unit's own model and STAKE what it does not
        already hold and has not already been scored on. A prediction concerns
        what this unit has not yet seen and has not yet answered for.

        A FORECAST IS AN ACT, NOT A STANDING STATE. What the unit takes to be
        derivable is `last_provenance`, which is written every call and holds
        the whole closure. What it *stakes* is the return value, and a stake is
        placed once: a fact this unit's record has already resolved (hit or
        miss, `MembraneLedger.resolved`) is not offered again.

        SHOULD A STILL-LICENSED FACT BE RE-BET? NO — and this is the choice,
        argued rather than assumed. If the law still licenses `head(a17)` after
        `head(a17)` was missed once, betting again stakes the same proposition a
        second time. The record's unit of account is the proposition, not the
        round and not the delivery, so a second stake would enter a second
        verdict on one claim and the same withheld consequent would be charged
        for the rest of the run — which is exactly the defect this replaces
        (misses quadratic in run length, a true law losing money). The
        alternative position — re-bet, but only when fresh evidence intervenes,
        e.g. the body is re-delivered — is coherent and bounded, but it needs
        the bet keyed by its support rather than by its content, and it buys
        information the aggregate does not need: one resolved claim per
        proposition is already a track record.

        THE PRICE IS PAID, NOT HIDDEN. Refusing to re-bet forgoes credit when a
        missed fact later arrives after all; `MembraneLedger.late_arrivals`
        counts exactly those. Measured over the suite's fourteen seeds, 60
        rounds, one planted law held alone: 21 to 31 hits, 0 to 7 misses, and 23
        to 32 late arrivals — so the discipline forgoes roughly as many credits
        as it takes, and the arm still finishes between +17 and +29. It was
        NEGATIVE (−16 at one measured arm) when the same forecasts were charged
        every round.

        The chaining is the project's real materializer over the unit's own EGI
        — not a hand-rolled tuple match — so anticipation is a genuine least
        Herbrand closure (chained derivations included) and the support of every
        anticipation is recorded in ``last_provenance``.

        A SUSPENDED LAW LICENSES NOTHING. It is still held and still published,
        but a law under a doubt its author could not settle is not a law the
        author is willing to bet on, and that is the whole operational content
        of suspension: the unit stops staking on it without giving it up. The
        price is visible in the arithmetic — a suspended TRUE law forgoes the
        hits it would have won — which is why the window is measured rather than
        assumed.
        """
        active = self.laws - self.suspended
        if not active or not self.facts:
            self.last_provenance = {}
            return set()
        provenance: Dict[Fact, FrozenSet[Fact]] = {}
        materialize_egi(self.as_egi(laws=active), provenance=provenance)
        self.last_provenance = provenance
        return {f for f in provenance
                if f not in self.facts and f not in self.ledger.resolved}

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

    def _holders(self) -> Dict[str, Set[Tuple[Key, ...]]]:
        """Which individuals this unit holds under each relation."""
        holders: Dict[str, Set[Tuple[Key, ...]]] = {}
        for rel, args in self.facts:
            holders.setdefault(rel, set()).add(args)
        return holders

    def _meets_criterion(self, law: Tuple[str, str],
                         min_support: int = MIN_SUPPORT,
                         max_pending_rate: float = MAX_PENDING_RATE) -> bool:
        """Would this unit induce `law` from its record AS IT STANDS NOW?

        THE INTERNAL ARM OF INQUIRY, and the reason it exists is Peircean rather
        than arithmetical: doubt provokes inquiry, and inquiry has an inward
        face as well as an outward one. A challenge that merely prompted the
        author to look up one individual would not be an inquiry at all — it
        would be a lookup. What a doubt should provoke is a genuine
        re-assessment: does my own record still sustain this law?

        IT IS THE INDUCTION CRITERION, UNCHANGED AND UNDUPLICATED — support,
        pending rate, precedence — which is why `induce` reads it too. That
        identity is the point. A law is held on exactly the terms it was taken
        up on, so a foreign counterexample can put a law in doubt but cannot
        impose a standard the author never used; and the gap Task 5 left open —
        `induce` only ever ADDS, and an admitted law is never re-tested against a
        grown record — is closed by making a challenge the occasion for the
        re-test.

        Read only against `self.facts`. Nothing about the challenger, the board
        or the field's regime enters."""
        body_rel, head_rel = law
        if body_rel == head_rel:
            return False
        holders = self._holders()
        body_args = holders.get(body_rel, set())
        head_args = holders.get(head_rel, set())
        support = body_args & head_args
        if len(support) < min_support:
            return False
        if len(body_args - head_args) > max_pending_rate * len(body_args):
            return False
        return self._body_precedes_head(body_rel, head_rel, support)

    def induce(self, min_support: int = MIN_SUPPORT,
               max_pending_rate: float = MAX_PENDING_RATE
               ) -> Set[Tuple[str, str]]:
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
        individuals.

        THE TEST ITSELF LIVES IN `_meets_criterion`, which is also what a
        challenged law is re-assessed against. One criterion, two readers: what
        it takes to take a law up is exactly what it takes to keep it."""
        holders = self._holders()
        found: Set[Tuple[str, str]] = set()
        for body_rel in sorted(holders):
            for head_rel in sorted(holders):
                law = (body_rel, head_rel)
                if law in self.laws:
                    continue
                if self._meets_criterion(law, min_support, max_pending_rate):
                    found.add(law)
        self.laws.update(found)
        return found

    def step(self, field: Field, round_idx: int, induce: bool = False) -> None:
        """One round: anticipate from what is held, observe what arrives, be
        scored on the forecast, then optionally induce from the enlarged
        record. Inducing last means a law never scores the round that taught
        it. The bet is placed before the outcome is seen.

        THE ORDER IS THE MEASUREMENT. `anticipate` runs before `field.at`, so
        nothing about this round's arrivals can reach the choice of what to
        stake; and the forecast is DUE NOW, because the field delivers a
        consequent one round after its antecedent and `_record` runs after
        scoring, so every fact the stake was derived from was held at r−1 or
        earlier. Resolve-once (see `anticipate`) is what makes "due now" mean
        "decided now" instead of "decided now and every round after"."""
        anticipated = self.anticipate()
        arrived = set(field.at(self.aperture, round_idx))
        self.ledger.score(anticipated, arrived, round_idx)
        self._record(arrived, round_idx)
        if induce:
            self.induce()

    # --- the assert channel: publish, read, adopt ---------------------------
    #
    # These are separate acts from `step`, deliberately. Folding publication
    # into the round would fix a communication schedule here, before stage 4's
    # budget can price it, and it would put a peer's mark inside the window
    # `step` keeps clear between anticipating and observing.

    def publish(self, board: MarkBoard, round_idx: int) -> List[Mark]:
        """Objectivate what this unit holds and has not already said, returning
        the marks minted.

        Facts before laws, each in sorted order, so the sequence of marks is a
        deterministic function of the unit's state — the same requirement
        `as_egi` meets, for the same reason.

        WHAT IS PUBLISHED IS WHAT IS HELD, not what was newly *delivered*: a
        unit does not distinguish, in what it says, between a fact the field
        brought it this round and one it has carried for fifty. What it does not
        do is say the same thing twice (`_published`), because a re-mention that
        refreshes nothing would still be counted by the instruments, and whether
        a re-mention refreshes standing is unruled (spec §9b's maintenance
        channel).
        """
        minted: List[Mark] = []
        for kind, contents in ((FACT, sorted(self.facts)), (LAW, sorted(self.laws))):
            for content in contents:
                key = (kind, content)
                if key in self._published:
                    continue
                mark = Mark(author=self.unit_id, content=content, kind=kind,
                            round_idx=round_idx)
                board.publish(mark)
                self._published.add(key)
                minted.append(mark)
        return minted

    def read(self, board: MarkBoard, round_idx: int) -> List[Mark]:
        """The community's marks from `round_idx` onward, EXCLUDING this unit's
        own — a unit encounters others' inscriptions, and its own model is
        already what it is.

        The unit is not obliged to adopt any of them; reading is encountering,
        adopting is a separate act, and stage 4's typification is what will make
        the choice of whose marks to read seriously.
        """
        return [m for m in board.since(round_idx) if m.author != self.unit_id]

    def adopt(self, mark: Mark, board: MarkBoard) -> bool:
        """Take a mark's content into this unit's own record, reporting whether
        anything NEW was taken up.

        UPTAKE IS RECORDED ONLY WHEN SOMETHING WAS ACTUALLY TAKEN UP. Uptake is
        the structural observable — who relies on whom — and a reader that had
        already reached the content itself owes the author nothing for it.
        Recording concurrence as reliance would credit an author for every unit
        whose aperture happened to deliver the same atom, which on overlapping
        apertures is most of them, and the attribution graph would then measure
        overlap rather than influence.

        A QUESTION IS NOT ADOPTABLE. It names an atom without claiming it, so
        there is no content to take up; taking one up would put an unasserted
        atom into a record and the unit would then bet on someone else's doubt.

        A unit may not adopt its own mark. A self-edge in the attribution graph
        would assert that a unit relies on itself, which is not reliance; `read`
        already excludes own marks, so arriving here is a caller's error and is
        named rather than silently absorbed.

        AN ADOPTED FACT IS HELD, BUT IT IS NOT DATED — the ruling of this task,
        and the one place where the sign/content distinction has teeth in the
        arithmetic.

        `first_seen` is the unit's record of when something reached its OWN
        membrane from the field, and `_body_precedes_head` reads it to tell a
        law from its converse: direction is inferred from the field's one-round
        lag, so the dates must be dates of deliverances. An adopted mark is not
        a deliverance. It reached the unit as a peer's inscription, at whatever
        round that peer got round to publishing, which stands in no fixed
        relation to when anything happened.

        Stamping it anyway would make a unit's sense of temporal order partly
        hearsay, and precedence-based induction could then be defeated by
        testimony: a peer's marks arriving late about individuals whose heads
        this unit observed early read as twenty supporters with the body second,
        outvoting the few genuine observations, and a TRUE law is refused
        because of when someone else spoke. That is measured, not feared —
        `tests/test_c_marks.py::test_testimony_cannot_mislead_precedence_and_defeat_a_true_law`
        builds both arms and the stamped one refuses the law.

        The alternative candidates were considered and rejected. Stamping the
        author's `round_idx` imports another unit's clock while LOOKING
        first-hand, which is the same defect wearing a better disguise. Carrying
        the author's own `first_seen` alongside the mark would make the content
        of a mark include the author's private history, and there is no reason a
        reader should be able to read that off an inscription — nor any reason to
        trust it if it could.

        WHAT THE RULING COSTS IS NOTHING, AND WHAT IT KEEPS IS TIMING. An
        undated fact is still evidence: it enlarges a law's support and it can
        still leave an antecedent pending and so refute one. It abstains only
        from the direction test, which `_body_precedes_head` already handles —
        absent timing evidence is not counter-evidence. And the date is not
        spent: if the field later delivers an adopted fact, `_record` dates it
        then, at the unit's first genuinely first-hand encounter with it.
        """
        if mark.author == self.unit_id:
            raise ValueError(
                f"{self.unit_id} cannot adopt its own mark {mark.content!r}: "
                f"a unit does not rely on itself, and the uptake would enter "
                f"a self-edge in the attribution graph"
            )
        if mark.kind == QUESTION:
            raise ValueError(
                f"{self.unit_id} cannot adopt the question {mark.content!r}: a "
                f"question names an atom without claiming it, so there is "
                f"nothing to take up — answer it instead (`answer`), or take up "
                f"the answering fact mark"
            )
        if mark.kind == CHALLENGE:
            raise ValueError(
                f"{self.unit_id} cannot adopt the challenge to {mark.content!r}: "
                f"a challenge disputes a law rather than claiming one, and "
                f"taking it up would enter the very law it argues against — "
                f"dispose of it instead (`dispose_challenges`)"
            )
        if mark.kind == CORROBORATION:
            raise ValueError(
                f"{self.unit_id} cannot adopt the corroboration call about "
                f"{mark.content!r}: a call for help asks about a law rather "
                f"than claiming one, and taking it up would enter a law its own "
                f"author has put in doubt — answer it instead (`corroborate`)"
            )
        if mark.kind == FACT:
            fresh = mark.content not in self.facts
            self.facts.add(mark.content)        # NOT self._record: no date
        elif mark.kind == LAW:
            fresh = mark.content not in self.laws
            self.laws.add(mark.content)
        else:                                   # pragma: no cover - Mark refuses
            raise ValueError(f"unknown mark kind {mark.kind!r}")
        if fresh:
            board.record_uptake(mark, self.unit_id)
        return fresh

    # --- the ask channel: ask, answer ---------------------------------------
    #
    # THIS IS WHERE ATTENTION BECOMES SOCIAL. Until now a unit's only source was
    # the field at its own membrane; with a question published it can also be
    # told, and — the other half, and the one that makes it a division of labour
    # — it can spend a turn telling rather than probing.

    def _wants(self) -> List[Fact]:
        """The atoms this unit has a licence to expect and no instance of, most
        wanted first.

        A want is an atom `head(a)` such that the unit holds a law
        `body -> head` and holds `body(a)` but not `head(a)`. That is exactly the
        shape of a question this unit could USE: it is licensed by something the
        unit already holds, it concerns an individual the unit is already
        tracking, and it is unsettled.

        MOST-WANTED IS ORDERED BY WHAT AN ANSWER COULD STILL CHANGE, in two
        stages, because attention is bounded and only one question goes out per
        round.

        1. A want the record has ALREADY RESOLVED goes last. A forecast resolves
           exactly once, at the round it is due (`MembraneLedger.score`), so an
           answer arriving afterwards cannot alter the verdict — it is a `late
           arrival`, counted and left. Such an atom is still worth knowing, so it
           is not dropped; it simply loses every contest with a live want.
        2. Among live wants, the one whose BODY ARRIVED MOST RECENTLY goes first.
           A want born this round is staked at the very next round the unit
           attends the field, so an answer is only in time if it comes now; an
           older live want has already survived a staking round and is less
           urgent. Urgency, not age, is what a bounded channel should spend
           itself on.

        AN UNDATED BODY SORTS LAST among live wants, and this follows the ruling
        already made in `adopt`: an adopted fact carries no first-arrival, so the
        unit has no evidence of how long it has been waiting. Treating a body of
        unknown age as urgent would let a peer's publication schedule set this
        unit's priorities, which is the same defect the dating ruling refused.

        Ties break on the atom itself, so the order is a deterministic function
        of the unit's state.
        """
        wants: List[Tuple[Tuple[int, int, Fact], Fact]] = []
        for body_rel, head_rel in sorted(self.laws):
            for rel, args in sorted(self.facts):
                if rel != body_rel:
                    continue
                head = (head_rel, args)
                if head in self.facts:
                    continue
                settled = 1 if head in self.ledger.resolved else 0
                # -first_seen: newest body first. A body with no first-arrival
                # (adopted, never delivered here) sorts after every dated one.
                dated = self.first_seen.get((body_rel, args))
                freshness = -dated if dated is not None else 1
                wants.append(((settled, freshness, head), head))
        wants.sort(key=lambda w: w[0])
        seen: Set[Fact] = set()
        out: List[Fact] = []
        for _key, head in wants:
            if head not in seen:        # two laws may want one atom
                seen.add(head)
                out.append(head)
        return out

    def ask(self, board: MarkBoard, round_idx: int) -> Optional[Mark]:
        """Publish this unit's most-wanted unknown as a standing question, or
        `None` if it wants nothing it has not already asked.

        AT MOST ONE QUESTION PER ROUND, because attention is bounded and a
        channel that emptied a unit's whole want-list every round would be a
        broadcast rather than an act. Which one goes out is the interesting
        choice and it is made in `_wants`.

        A QUESTION IS ASKED ONCE, EVER. `_published` is keyed by `(kind,
        content)`, so a want that has been asked is never re-asked even while it
        stands unanswered. The reason is the reason the assert channel does not
        re-publish: a re-mention that refreshes nothing would still be counted by
        the instruments, and whether re-asking refreshes a question's standing is
        unruled (spec §9b's maintenance channel). What this costs is that a
        question nobody could answer at the time is never re-offered to a
        community that has since grown — the maintenance channel's business, and
        it is left visible rather than pre-empted here.

        WHAT A QUESTION IS FOR, and why this channel and not the assert channel
        is where communication starts paying. Task 3 measured the assert channel
        with indiscriminate uptake and found it STRICTLY HARMFUL: at every seed,
        four units adopting every peer mark all went from positive to negative
        net scores. The cause was aperture. A fact adopted about an individual of
        a domain the adopter cannot observe licenses an anticipation whose
        consequent can never arrive at the adopter's membrane — a guaranteed
        miss. Communication without targeting is worse than silence.

        A question is the first piece of targeting, and it targets by
        CONSTRUCTION rather than by luck: the atom asked about is one this unit's
        own laws license over an individual its own record already carries, so an
        answer is relevant to it by the very definition of what it asked. What a
        question CANNOT do is choose whom to ask — it is published to the whole
        board — and that is typification's work, next.
        """
        for want in self._wants():
            key = (QUESTION, want)
            if key in self._published:
                continue
            mark = Mark(author=self.unit_id, content=want, kind=QUESTION,
                        round_idx=round_idx)
            board.publish(mark)
            self._published.add(key)
            return mark
        return None

    def answer(self, board: MarkBoard, round_idx: int) -> List[Mark]:
        """Publish a `"fact"` mark for every open question this unit can settle
        from its own holdings, returning the marks minted.

        THIS IS THE OTHER HALF OF THE DIVISION OF LABOUR, and it is a genuine
        alternative use of a turn: a unit that answers spends its publication on
        what a peer lacks rather than on what it happens to hold. Nothing here
        consults the field — an answer is drawn from `self.facts` and from
        nowhere else, so a unit can only tell what it has actually met.

        NEVER ITS OWN QUESTION. Answering oneself would put the asker's want on
        the board as a claim it never met, and — since `open_questions` closes a
        question by content — it would close the question against every peer who
        could really have answered it. `read` excludes own marks for the
        analogous reason; here the exclusion is by author on the question rather
        than on the answer.

        THE QUESTIONS SCANNED ARE ALL OPEN ONES, not only this round's. A
        question stands until answered, and a unit that meets the answer forty
        rounds later can still supply it. This is why the scan goes through
        `MarkBoard.open_questions` rather than `read(board, round_idx)`, which is
        windowed by round and would silently drop everything older.

        A FACT MARK IS A FACT MARK, whatever prompted it. What is published in
        reply is indistinguishable from the same content published unprompted —
        the same `(kind, content)` key in `_published`, so a unit never says one
        thing twice whether asked or not, and a reader encounters an inscription
        rather than a reply. Nothing in the board records that a mark answered a
        question; the answering relation is recoverable from content, which is
        the point of a question naming the atom that would answer it.
        """
        minted: List[Mark] = []
        for question in board.open_questions():
            if question.author == self.unit_id:
                continue
            content = question.content
            if content not in self.facts:
                continue
            key = (FACT, content)
            if key in self._published:
                continue
            mark = Mark(author=self.unit_id, content=content, kind=FACT,
                        round_idx=round_idx)
            board.publish(mark)
            self._published.add(key)
            minted.append(mark)
        return minted

    # --- the challenge channel: challenge, dispose_challenges ----------------
    #
    # THIS IS WHERE A LAW BECOMES DEFEASIBLE BY EVIDENCE. Until now `induce`
    # only ever ADDED: an admitted law was never re-tested against a grown
    # record, so the only thing that could ever remove one was a decay clock,
    # and durability could not read false for a reason. A challenge is the other
    # way — and it is the reason retraction (`retract_law`) was built first.

    def _counterexample_to(self, law: Tuple[str, str]) -> Optional[Fact]:
        """An individual this unit holds under the law's body and not under its
        head, as the body atom itself — or `None` if its record has none.

        Sorted, so which counterexample is cited is a deterministic function of
        the unit's state rather than of set iteration order.

        THIS READS ONLY `self.facts`, which is the point. A unit may cite what it
        has met and nothing else; it has no access to the field's regime, to
        another unit's record, or to what was withheld. That is what makes a
        counterexample a piece of testimony rather than an oracle's verdict —
        and it is why a challenge has to be checked rather than obeyed.
        """
        body_rel, head_rel = law
        for rel, args in sorted(self.facts):
            if rel == body_rel and (head_rel, args) not in self.facts:
                return (body_rel, args)
        return None

    def challenge(self, board: MarkBoard, round_idx: int) -> List[Mark]:
        """Publish a challenge against every published law this unit's own
        record contradicts, returning the marks minted.

        WHAT IS CHALLENGED IS A CLAIM, NOT A PEER. The mark's content is the law
        itself, so one challenge meets every unit that published it — the same
        content-matching that lets any published fact close a question. The
        scan is over the whole board rather than a round window, because a law
        published forty rounds ago still stands: nothing has withdrawn it, and a
        unit that only now holds the counterexample is only now able to say so.

        A UNIT DOES NOT CHALLENGE ITS OWN INSCRIPTION. `read` excludes own marks
        for the same reason: what a unit encounters is somebody else's. (It may
        still end up disposing of a challenge it authored — see
        `dispose_challenges` — because a law it holds is disputed by evidence it
        itself published, and it would be a strange record that made an
        exception for its own.)

        ONCE PER LAW, EVER, keyed in `_published` like every other act. A second
        challenge to one law carrying a second counterexample would be a second
        inscription making the same point, and it would be counted by the
        instruments as if two things had been disputed. It would also convert
        the channel into a volume contest — which is the thing the disposition
        rule most needs not to be, since the author's verification does not
        count challenges.

        NOT CAPPED PER ROUND, unlike `ask`. Asking spends a unit's own bounded
        attention on one want among many, so which one goes out is a real
        choice; challenging spends nothing but the evidence already in hand, and
        withholding a counterexample this round would not sharpen the next one.
        Stage 4's budget is where this asymmetry should be priced, not here.
        """
        minted: List[Mark] = []
        disputable: Set[Tuple[str, str]] = set()
        for mark in board.all_marks():
            if mark.kind == LAW and mark.author != self.unit_id:
                disputable.add(mark.content)
        for law in sorted(disputable):
            mark = self._mint_challenge(law, board, round_idx)
            if mark is not None:
                minted.append(mark)
        return minted

    def _mint_challenge(self, law: Tuple[str, str], board: MarkBoard,
                        round_idx: int) -> Optional[Mark]:
        """Publish one challenge against `law` if this unit's own record holds a
        counterexample and it has not already said so. Shared by `challenge`
        (which scans the board for laws to dispute) and `corroborate` (which is
        asked about one), so that the once-per-law-ever key is kept in ONE place:
        a unit answering a call for help must not be able to enter a second
        inscription of evidence it has already published."""
        key = (CHALLENGE, law)
        if key in self._published:
            return None
        counter = self._counterexample_to(law)
        if counter is None:
            return None
        mark = Mark(author=self.unit_id, content=law, kind=CHALLENGE,
                    round_idx=round_idx, counterexample=counter)
        board.publish(mark)
        self._published.add(key)
        return mark

    # --- the corroboration lifecycle: doubt, inquiry, disposal ---------------
    #
    # THE AUTHOR'S RULING: *corroborate and suspend, but do not eliminate until
    # corroboration.* A challenge no longer retracts anything by itself. What it
    # does is raise a doubt, and a doubt provokes INQUIRY — which in Peirce has
    # two arms, and had only one here before this task.
    #
    #   (internal)  The author re-assesses the law against its OWN current
    #               record, by the very criterion it would use to induce the law
    #               today (`_meets_criterion`). If the record no longer sustains
    #               it, the doubt is settled inside the membrane: retract, and no
    #               corroboration is needed. This is also where the gap Task 5
    #               left open closes — `induce` only ever ADDED, and an admitted
    #               law was never re-tested against a grown record.
    #
    #   (external)  If the record still sustains the law but the author cannot
    #               rebut the cited individual, the law is SUSPENDED — held,
    #               published, licensing nothing — and the author publishes a
    #               call for corroboration. An independent peer bearing out the
    #               doubt eliminates the law; a peer holding the disputed
    #               individual WITH the head restores it; silence for the whole
    #               window restores it.
    #
    # THE INCOHERENCE THIS FIXES. Admission tolerated a 5% pending RATE while
    # disposition fired on any ONE pending individual, so the two criteria fought
    # continuously (98 distinct defeats, 426 retraction events) and, worse, could
    # not tell a withheld consequent from a false law: 58 of 58 successful
    # challenges destroyed a law the field actually carries. Now the same
    # standard governs holding a law and losing it, and a foreign counterexample
    # can suspend but never unilaterally kill.

    def _rebutted(self, mark: Mark, board: MarkBoard, round_idx: int,
                  *, testimony: bool) -> bool:
        """Does the cited individual carry the law's head after all?

        THE AUTHOR'S OWN RECORD DECIDES FIRST, always: this is the check Task 5
        built, unchanged, and it is why a challenge is a claim that gets checked
        rather than a command that gets obeyed.

        `testimony` additionally admits a PEER'S PUBLISHED head atom, and it is
        set only while a law is suspended. That is the ruling's own step — "on a
        peer rebutting, the law is restored" — and it is the reason the call for
        corroboration is worth publishing: a call can be answered either way, and
        an answer that the disputed individual does carry the head defeats the
        doubt as squarely as a corroboration confirms it. A published mark is
        attributable and checkable, which is the most a unit can ask of anything
        that did not arrive at its own membrane; and it is not adopted here — the
        law is restored, not the peer's fact taken up.
        """
        _body_rel, head_rel = mark.content
        _rel, args = mark.counterexample
        head = (head_rel, args)
        if head in self.facts:
            return True
        if not testimony:
            return False
        return any(m.author != self.unit_id
                   for m in board.fact_marks(head, upto=round_idx))

    def _standing_challenges(self, law: Tuple[str, str], board: MarkBoard,
                             round_idx: int) -> List[Mark]:
        """The challenges against `law` this unit has not already answered for,
        in publication order — bounded by `round_idx`, since a disposal at r
        answers for challenges published at r or earlier and never for one made
        afterwards."""
        return [m for m in board.challenges_against(law, upto=round_idx)
                if m not in self._spent]

    def _solicit(self, law: Tuple[str, str], about: Mark, board: MarkBoard,
                 round_idx: int) -> Optional[Mark]:
        """Publish the call for corroboration: a question about a law, naming the
        individual in dispute.

        THIS IS THE ASK CHANNEL'S MACHINERY, pointed at a law. The author cannot
        settle the doubt alone — its own record simply lacks the head, and under
        a fallible field that is exactly what a withheld consequent looks like —
        so it does the one thing a unit in a community can do: it asks. The call
        asserts nothing (it cannot be adopted), it names precisely what would
        bear on it (the law and the individual), and it is answered from a peer's
        own record, which is the shape every other question here has.

        ONCE PER LAW, EVER, like every other act (`_published`). A second call
        about one law would be the same request again, and the instruments would
        count two inquiries where one was made. The cost is that a later doubt
        about the same law under a DIFFERENT individual re-uses the standing
        call, so the call's named individual can go stale; nothing turns on it —
        a peer's answer is checked against the live doubt's own challenge mark,
        never against the call — but it is a legibility cost and it is named
        rather than hidden.
        """
        key = (CORROBORATION, law)
        if key in self._published:
            return None
        mark = Mark(author=self.unit_id, content=law, kind=CORROBORATION,
                    round_idx=round_idx, counterexample=about.counterexample)
        board.publish(mark)
        self._published.add(key)
        return mark

    def dispose_challenges(self, board: MarkBoard,
                           round_idx: int) -> Disposition:
        """Answer for every challenge standing against a law this unit holds, and
        move each law's standing accordingly. Returns what changed and WHY.

        A law is visited once per pass, and a doubt opened in this pass is not
        also disposed of in it: the grace of at least one round is structural,
        not a special case, and it is what gives the community a chance to speak
        before anything is eliminated.

        NOTHING IS PUBLISHED BY A RETRACTION OR A RESTORATION, and that is still
        a real gap. The board is append-only: a defeated law's mark stands, and a
        reader cannot tell that its author gave it up or put it in doubt. The
        call for corroboration is the one piece of a law's changed standing that
        does reach the board. Closing the rest is the maintenance channel's work
        (spec §9b), left visible rather than pre-empted.
        """
        out = Disposition()
        for law in sorted(self.laws):
            standing = self._standing_challenges(law, board, round_idx)
            if law in self.suspended:
                self._dispose_doubt(law, standing, board, round_idx, out)
            elif standing:
                self._open_doubt(law, standing, board, round_idx, out)
        return out

    def _open_doubt(self, law: Tuple[str, str], standing: List[Mark],
                    board: MarkBoard, round_idx: int,
                    out: Disposition) -> None:
        """Dispose of a fresh challenge against an active law: rebut it, settle
        it internally, or suspend and ask for help."""
        live = [m for m in standing
                if not self._rebutted(m, board, round_idx, testimony=False)]
        self._spent.update(m for m in standing if m not in live)
        if not live:
            return                              # rebutted: the law stands
        if not self._meets_criterion(law):
            # THE INTERNAL ARM. The doubt sent the author back to its own record
            # and the record no longer sustains the law. Nobody else was needed.
            self._spent.update(live)
            if self.retract_law(law):
                out.retracted_internally.append(law)
            return
        trigger = live[0]
        self._suspend(law, Doubt(challenger=trigger.author,
                                 individual=trigger.counterexample[1],
                                 opened_at=round_idx))
        self._solicit(law, trigger, board, round_idx)
        out.suspended.append(law)

    def _dispose_doubt(self, law: Tuple[str, str], standing: List[Mark],
                       board: MarkBoard, round_idx: int,
                       out: Disposition) -> None:
        """Carry a suspended law's doubt forward one round.

        THE ORDER IS THE RULING'S ORDER, and each step is the answer to a
        different question.

        1. Is the doubt still live? A rebuttal — the author's own record, or a
           peer's published testimony about the disputed individual — retires it,
           and the law goes back to work.
        2. Does the author's own record still sustain the law? The internal arm
           runs every round the doubt stands, not only when it opened: the record
           grows, and a law that stops meeting its own criterion is defeated by
           the author's own evidence whatever the community says.
        3. Has an INDEPENDENT peer borne the doubt out? That is corroboration,
           and it is the only thing that eliminates a law from outside. The unit
           that opened the doubt cannot corroborate itself — its counterexample
           is the one already being weighed, and counting it twice would make one
           record's gap into two votes.
        4. Has the call gone unanswered for the whole window? Then the challenge
           has failed to gather support, and SILENCE CANNOT ELIMINATE: the law is
           restored. That is the direction the ruling fixes — a doubt nobody
           shares is a doubt that has run out, not a verdict.

        A challenge disposed of here is spent (`_spent`): it has had its answer,
        and the same inscription does not get to raise the same doubt again.
        """
        doubt = self._doubts[law]
        live = [m for m in standing
                if not self._rebutted(m, board, round_idx, testimony=True)]
        self._spent.update(m for m in standing if m not in live)
        if not live:
            self._unsuspend(law)
            out.restored_by_rebuttal.append(law)
            return
        if not self._meets_criterion(law):
            self._spent.update(live)
            if self.retract_law(law):
                out.retracted_internally.append(law)
            return
        if {m.author for m in live} - {doubt.challenger}:
            self._spent.update(live)
            if self.retract_law(law):
                out.retracted_by_corroboration.append(law)
            return
        if round_idx - doubt.opened_at >= self.corroboration_window:
            self._spent.update(live)
            self._unsuspend(law)
            out.restored_by_silence.append(law)

    def corroborate(self, board: MarkBoard, round_idx: int) -> List[Mark]:
        """Answer other units' calls for corroboration from this unit's own
        record, returning the marks minted.

        THE OTHER HALF OF THE CALL, exactly as `answer` is the other half of
        `ask`. A unit reads what it is being asked about and replies with what it
        has actually met — and there are only two things it can have met that
        bear on a doubt:

        - THE DISPUTED INDIVIDUAL WITH THE HEAD, which rebuts the doubt. It is
          published as an ordinary fact mark, indistinguishable from the same
          content published unprompted, because that is what it is: a fact this
          unit holds. The asking author reads it in `_rebutted` and restores.
        - ITS OWN COUNTEREXAMPLE to the law, which corroborates. It is published
          as an ordinary challenge, through the same once-per-law-ever mint
          `challenge` uses, because that is what it is: this unit's own evidence
          against a standing claim. What makes it CORROBORATION rather than a
          fresh dispute is only that another record already said the same thing —
          independence is a property of the two records, not of the mark.

        NEVER ITS OWN CALL: a unit cannot corroborate its own doubt, for the
        reason it cannot answer its own question. And it says nothing it has not
        met — nothing here consults the field, and a unit with neither the head
        nor a counterexample simply has nothing to contribute, which is the
        silence the window measures.
        """
        minted: List[Mark] = []
        for call in board.corroboration_calls(upto=round_idx):
            if call.author == self.unit_id:
                continue
            law = call.content
            _body_rel, head_rel = law
            _rel, args = call.counterexample
            head = (head_rel, args)
            if head in self.facts:
                key = (FACT, head)
                if key in self._published:
                    continue
                mark = Mark(author=self.unit_id, content=head, kind=FACT,
                            round_idx=round_idx)
                board.publish(mark)
                self._published.add(key)
                minted.append(mark)
                continue
            mark = self._mint_challenge(law, board, round_idx)
            if mark is not None:
                minted.append(mark)
        return minted
