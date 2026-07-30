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
from c_marks import CHALLENGE, FACT, LAW, QUESTION, Content, Mark, MarkBoard
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
    tell a law from its converse (see `induce`).

    FIRST-HAND ONLY. An adopted mark does not write here; the argument is in
    `adopt`."""
    _published: Set[Tuple[str, Content]] = dc_field(default_factory=set)
    """What this unit has already published, as `(kind, content)` pairs — not as
    marks, since a mark carries the round it was published in and would compare
    unequal every round, so the unit would republish everything forever."""

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
        """
        if not self.laws or not self.facts:
            self.last_provenance = {}
            return set()
        provenance: Dict[Fact, FrozenSet[Fact]] = {}
        materialize_egi(self.as_egi(), provenance=provenance)
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
            key = (CHALLENGE, law)
            if key in self._published:
                continue
            counter = self._counterexample_to(law)
            if counter is None:
                continue
            mark = Mark(author=self.unit_id, content=law, kind=CHALLENGE,
                        round_idx=round_idx, counterexample=counter)
            board.publish(mark)
            self._published.add(key)
            minted.append(mark)
        return minted

    def dispose_challenges(self, board: MarkBoard,
                           round_idx: int) -> List[Tuple[str, str]]:
        """Verify every standing challenge against a law this unit holds, and
        retract the laws it cannot rebut. Returns the laws given up.

        THE CALCULUS DECIDES, NOT THE CHALLENGER'S AUTHORITY. A challenge cites
        an individual said to carry the law's body without its head; this unit
        checks that individual AGAINST ITS OWN FACTS. If its record holds that
        same individual WITH the head, the citation is false of the world this
        unit has met, the challenge is rebutted, and the law stands. Nothing
        about who challenged, how often, or how many peers agreed enters here —
        a challenge is a claim that gets checked, never a command that gets
        obeyed, and the difference is what keeps a law's fate a matter of
        evidence rather than of standing.

        WHAT CANNOT BE REBUTTED IS GIVEN UP, EVEN WHEN THE LAW IS TRUE. An
        author whose own record simply lacks the head — because the field
        withheld that consequent, or because the author was not attending when
        it arrived — cannot distinguish that case from a genuine refutation, and
        it retracts. This is not an oversight to be tuned away with a
        confirmation threshold. It is what defeasibility costs under a fallible
        field, and it is measured rather than hidden: see
        `tests/test_c_channels.py`, which counts how many successful challenges
        defeat a law the field actually carries.

        ITS OWN CHALLENGES ARE NOT EXEMPT. A unit that challenged `p1 -> q1` on
        a peer's board and also holds `p1 -> q1` has published evidence against
        something it believes; the honest disposal is the same one it would make
        of a stranger's evidence, and the verification is identical in either
        case. (`challenge` will not have produced this from a law it holds
        unless a peer published the law too.)

        NOTHING IS PUBLISHED BY A RETRACTION, and that is a real gap rather than
        an oversight. The board is append-only: a law mark that has been defeated
        still stands there, and a unit reading the board later cannot tell that
        its author gave it up. What a mark CLAIMS and what its author still HOLDS
        have come apart, and closing that gap is the maintenance channel's work
        (spec §9b), left visible here rather than pre-empted.

        `round_idx` bounds which challenges are answerable: a disposal at r
        answers for challenges published at r or earlier, never for one made
        afterwards. The board is a place and keeps no clock, so the bound comes
        from the caller.
        """
        retracted: List[Tuple[str, str]] = []
        for law in sorted(self.laws):
            _body_rel, head_rel = law
            for mark in board.challenges_against(law, upto=round_idx):
                _rel, args = mark.counterexample
                if (head_rel, args) in self.facts:
                    continue                    # rebutted: the law stands
                if self.retract_law(law):
                    retracted.append(law)
                break
        return retracted
