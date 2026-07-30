"""The exchange medium for the C-series: the OBJECTIVATED MARKS and the board
they are published on.

THREE THINGS STAY APART, and this module is only ever the middle one (spec
premise 2; THE_COMMENS_AND_THE_COMMUNITY §1).

- A unit's **UoD** is what it thinks with, inside its own membrane. That lives
  in `c_unit.Unit` — its facts, its laws, its own dated record of arrivals — and
  nothing here reaches into it.
- The **objectivated marks** are published, attributable inscriptions (Berger &
  Luckmann's objectivation). `Mark` is one such inscription and `MarkBoard` is
  where they stand. THIS IS WHAT THIS MODULE BUILDS, and what the instruments
  count: marks published and by whom, and their uptake.
- The **commens** is Peirce's Communicational Interpretant — the prior, enabling
  mutual understanding that makes a mark legible at all. IT IS NONE OF THESE
  OBJECTS. It belongs to no participant, so it cannot be a field of a unit, and
  it is not the pile of what has been said, so it cannot be the board.
  **NO DATA STRUCTURE IN THIS MODULE — OR ANYWHERE IN THIS SERIES — MAY CARRY
  ITS NAME.** An earlier draft of this program's own spec defined the commens as
  the marks; that is precisely the category mistake the doctrine warns against,
  and naming a class or a field for it would re-commit it in code, where it
  would then be measured. The commens is legible only at its contour, by
  failure: breakdown-and-repair episodes map what was not in fact held in
  common. Repair is instrumented later, off marks and provenance, and it too
  will not be named for what it measures the edge of.

WHAT CROSSES IS A SIGN, NEVER CONTENT. A mark is an inscription with an author
attached; a reader encounters it and forms its own interpretant out of its own
history. That is why attribution rides along in the mark itself rather than
being kept in a table beside it — the author is part of what is encountered, and
uptake is only countable because of it.

NOT EVERY MARK ASSERTS. As of the ask channel a mark may be a `"question"`: an
inscription that names an atom without claiming it. It is published, attributed
and encounterable like any other mark — asking is a public act, and that is what
lets a peer answer — but it puts nothing into a reader's record. The kinds are
therefore not decoration: `Mark.kind` is the only thing distinguishing a claim
from a request for one, and both readers and adopters dispatch on it.

A MARK MAY ALSO DISPUTE ONE. As of the challenge channel a mark may be a
`"challenge"`: it names the LAW it disputes and carries the COUNTEREXAMPLE its
author holds — an individual carrying the law's body without its head. It is
neither an assertion nor a request but a piece of evidence offered against a
standing claim, and it is what finally lets a held law be defeated by something
other than a decay clock.

A CHALLENGE IS A CLAIM THAT GETS CHECKED, NOT A COMMAND THAT GETS OBEYED. The
mark itself defeats nothing. It is the law's author that disposes of it, by
verifying the cited counterexample against its OWN record (`c_unit.Unit
.dispose_challenges`), and an author holding that same individual WITH the head
rebuts the challenge and keeps its law. Nothing about the challenger's standing,
volume or authority enters that decision. This is why the challenge names its
counterexample rather than merely asserting that one exists: an unverifiable
demand would make retraction a function of who spoke.

A CHALLENGE IS ADDRESSED TO A CLAIM, NOT TO A PERSON. Its content is the law
itself, so a challenge meets every author of that law — the same content-matching
that lets any published fact close a question. Two units that independently
published `p1 -> q1` published one claim twice, and evidence against it is
evidence against both.

AND A MARK MAY CALL FOR HELP. As of the author's corroboration ruling a mark may
be a `"corroboration"`: a QUESTION ABOUT A LAW, published by that law's own
author when a challenge it cannot rebut has put the law in doubt. It names the
law and the disputed individual, and what it asks of the community is whether
anyone else's record bears on the doubt. It is the ask channel's shape applied
to a law rather than to an atom — a public, attributable request that a peer
answers from its OWN record — and it exists because the author ruled that a law
is suspended by a challenge but eliminated only by corroboration. Nothing about
the call decides anything; it is the occasion for evidence, not evidence itself.
Its `counterexample` field carries the individual under dispute (the atom the
challenge cited), so a reader knows exactly which case is at issue.

THE BOARD IS PER-COMMUNITY AND SEALED in this stage. Sealing is structural, not
a flag: a board holds no reference to another board and there is no operation
here that reads one from another. Permeability is a later switch, and it will be
an added operation rather than a relaxed check.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple, Union

from model_materialization import Fact

FACT = "fact"
LAW = "law"
QUESTION = "question"
CHALLENGE = "challenge"
CORROBORATION = "corroboration"
KINDS = (FACT, LAW, QUESTION, CHALLENGE, CORROBORATION)

LAW_SHAPED = (LAW, CHALLENGE, CORROBORATION)
"""The kinds whose content is a `(body_rel, head_rel)` pair of names — the law
asserted, the law disputed, the law in doubt."""

CITES_AN_INDIVIDUAL = (CHALLENGE, CORROBORATION)
"""The kinds that carry an atom beside their content: the counterexample a
challenge OFFERS, and the disputed individual a corroboration call is ABOUT.
Both are atoms of the named law's BODY, and both are checked at minting."""

Content = Union[Fact, Tuple[str, str]]
"""What a mark inscribes: a ground atom, or a law as its `(body, head)` pair —
the same two shapes `c_unit.Unit` holds, so an adopted mark needs no
translation to enter a reader's own record.

A QUESTION inscribes an atom too — the very shape a fact takes — and that is
deliberate. A question names precisely what would answer it, so an answer is
the same content published under a different kind, and a reader needs no
matching apparatus to see that the two meet. What a question does NOT carry is
assertoric force: `kind` is the difference, and `c_unit.Unit.adopt` refuses to
take a question's content into a record for exactly that reason.

A CHALLENGE inscribes the LAW it disputes — the same `(body, head)` pair the law
mark carried — so a challenge meets the claim rather than its author, and every
holder of that law can dispose of it. Its evidence rides in `Mark.counterexample`
rather than in the content, because the content is what the mark is ABOUT and the
counterexample is what it OFFERS."""


@dataclass(frozen=True)
class Mark:
    """One published, attributed inscription.

    Frozen, so a mark cannot be edited after publication — a board that is
    append-only in its list but whose entries were mutable would be append-only
    in name — and hashable, so the mark itself keys its uptake rather than some
    surrogate id that could drift from it.

    `round_idx` is the round the AUTHOR published in. It is a fact about the
    inscription, not about the world: it is emphatically not when the author
    observed the content, and a reader must not treat it as an observation date
    (see `c_unit.Unit.adopt`, which is where that temptation actually arises).
    """

    author: str
    content: Content
    kind: str
    round_idx: int
    counterexample: Optional[Fact] = None
    """The evidence a `"challenge"` offers: an individual the challenger's own
    record carries under the law's BODY and not under its HEAD. On a
    `"corroboration"` call it is the same atom read the other way round — the
    disputed individual the call is ABOUT, republished by the law's author so
    that a peer can answer about the very case at issue rather than about the
    law in general.

    IT IS CARRIED, NOT MERELY CLAIMED, and that is the whole difference between
    a challenge and a demand. The law's author checks this atom against its own
    facts and keeps the law if it can rebut it, so what is published has to be
    the thing itself. A challenge that said only "your law is refuted somewhere"
    could not be checked, and retraction would then follow from having spoken.

    Defaulted, so it is absent on every other kind — an assertion or a question
    that carried one would be offering evidence against a law it never named."""

    def __post_init__(self) -> None:
        """Refuse a mark that cannot be disposed of, at the point of minting.

        `Unit.adopt` dispatches on `kind`, and a fact and a law are BOTH
        2-tuples — `("p1", "q1")` is a law, `("p1", (("c", "a1"),))` a fact — so
        `kind` is the only thing that tells them apart. A law-shaped tuple filed
        as a fact would enter `Unit.facts` and surface much later as an
        unrelated-looking failure in `as_egi`. Checking the shape against the
        declared kind here means a misfiled mark never reaches a reader.
        """
        if self.kind not in KINDS:
            raise ValueError(
                f"mark kind {self.kind!r} is not one of {KINDS}: a reader "
                f"dispatches on kind and could not dispose of this one"
            )
        if not (isinstance(self.content, tuple) and len(self.content) == 2):
            raise ValueError(
                f"mark content {self.content!r} is neither a fact "
                f"(relation, args) nor a law (body, head)"
            )
        rel, rest = self.content
        if not isinstance(rel, str):
            raise ValueError(f"mark content {self.content!r} has no relation name")
        if self.kind in LAW_SHAPED and not isinstance(rest, str):
            raise ValueError(
                f"mark of kind {self.kind!r} carries {self.content!r}, which is "
                f"shaped like a fact: a law — and a challenge, which names the "
                f"law it disputes, and a corroboration call, which names the law "
                f"in doubt — is a (body_rel, head_rel) pair of names"
            )
        if self.kind in (FACT, QUESTION) and not isinstance(rest, tuple):
            raise ValueError(
                f"mark of kind {self.kind!r} carries {self.content!r}, which is "
                f"shaped like a law: a fact — and a question, which names the "
                f"atom that would answer it — is (relation, ((kind, label), ...))"
            )
        self._check_counterexample(rel)

    def _check_counterexample(self, body_rel: str) -> None:
        """A challenge must carry checkable evidence, and nothing else may carry
        any.

        THE EVIDENCE IS VALIDATED WHERE IT IS MINTED, for the reason the kinds
        are: a disposer reads `counterexample` and decides a law's fate by it, so
        a challenge citing an atom of some unrelated relation would defeat a law
        it says nothing about. The atom's relation must be the law's BODY — that
        is what "carries the body without the head" means — and whether the
        author also holds the head is precisely what is left for the author to
        check, so it cannot be checked here.

        A CORROBORATION CALL IS HELD TO THE SAME STANDARD, because it is the
        same atom: a call that named no individual would be asking the community
        about a law in general, which no peer could answer from its own record.
        """
        if self.kind not in CITES_AN_INDIVIDUAL:
            if self.counterexample is not None:
                raise ValueError(
                    f"mark of kind {self.kind!r} carries a counterexample "
                    f"{self.counterexample!r}: only a challenge offers evidence, "
                    f"and only a corroboration call names the individual in "
                    f"dispute — both against a law they name"
                )
            return
        c = self.counterexample
        if c is None:
            raise ValueError(
                f"{self.kind} to {self.content!r} carries no counterexample: a "
                f"challenge is evidence offered against a law, and a "
                f"corroboration call is a question about one disputed "
                f"individual; neither could be checked without the atom itself"
            )
        if not (isinstance(c, tuple) and len(c) == 2 and isinstance(c[0], str)
                and isinstance(c[1], tuple)):
            raise ValueError(
                f"challenge counterexample {c!r} is not an atom "
                f"(relation, ((kind, label), ...))"
            )
        if c[0] != body_rel:
            raise ValueError(
                f"{self.kind} to {self.content!r} cites {c[0]!r}, which is not the "
                f"law's body {body_rel!r}: a counterexample to body -> head is "
                f"an individual holding the BODY without the head"
            )


class MarkBoard:
    """Where one community's marks stand: append-only, attributable, sealed.

    Append-only in both directions — a published mark is never removed, and the
    readers hand back copies so no caller can unpublish by mutating what it was
    given. (A mark's *standing* is a separate question from its presence: the
    challenge channel disposes of what a mark claims without erasing the fact
    that it was said.)
    """

    def __init__(self) -> None:
        self._marks: List[Mark] = []
        self._uptake: Dict[Mark, Set[str]] = {}
        self.republished = 0
        """How many identical marks were offered again and NOT appended.
        Observability, never a score. An identical mark is the same author
        saying the same thing in the same round, so appending it would inflate
        the published-mark count the structural observable reads; a genuine
        re-mention in a later round has a different `round_idx`, is a distinct
        mark, and IS kept — the board simply does not treat it as refreshing
        anything, because whether a re-mention refreshes standing is unruled
        (spec §9b, the maintenance channel, deliberately not decided here)."""

    def publish(self, mark: Mark) -> None:
        """Put a mark where others may encounter it."""
        if mark in self._uptake:
            self.republished += 1
            return
        self._marks.append(mark)
        self._uptake[mark] = set()

    def all_marks(self) -> List[Mark]:
        """Every mark, in publication order — which is not round order, since a
        unit may publish something it has held for a while."""
        return list(self._marks)

    def since(self, round_idx: int) -> List[Mark]:
        """The marks published in `round_idx` or later, in publication order."""
        return [m for m in self._marks if m.round_idx >= round_idx]

    def open_questions(self) -> List[Mark]:
        """The questions standing unanswered, in publication order.

        OPENNESS IS A PROPERTY OF THE BOARD, not of any unit, which is why it is
        read here. A question is closed by a PUBLISHED answer — an inscription
        anyone could encounter — and not by some unit privately coming to know
        the atom. Were openness kept per-unit instead, two peers holding the same
        answer would each have to guess whether the other had spoken, and the
        board would stop being the shared place where what has been said stands.

        A question is answered by a `"fact"` mark carrying THE SAME CONTENT, by
        anyone, in any round — including a fact published for its own sake rather
        than in reply. That is the point of a question inscribing the atom that
        would answer it: no matching apparatus is needed for the two to meet, and
        an asker's want can be satisfied by a peer who was simply saying what it
        held.

        A closed question does not re-open. The board is append-only, so nothing
        can withdraw the answering mark; whether the answer STANDS is a separate
        question from whether it was said, and disposing of that is the challenge
        channel's work, not this reader's.
        """
        answered = {m.content for m in self._marks if m.kind == FACT}
        return [m for m in self._marks
                if m.kind == QUESTION and m.content not in answered]

    def answer_to(self, question: Mark) -> Optional[Mark]:
        """The first published `"fact"` mark that answers `question`, if any.

        Read by an asker, so that taking up an answer is a targeted act: the
        alternative is to sweep the board and adopt whatever is there, which is
        measurably worse than silence (see the finding recorded in
        `c_unit.Unit.ask`)."""
        for m in self._marks:
            if m.kind == FACT and m.content == question.content:
                return m
        return None

    def challenges_against(self, law: Tuple[str, str],
                           upto: Optional[int] = None) -> List[Mark]:
        """Every challenge standing against `law`, in publication order.

        BY CONTENT, NOT BY ADDRESSEE. A challenge names the law it disputes and
        no one else, so this reader answers "what evidence stands against this
        claim" rather than "who was told". Two units that both published
        `p1 -> q1` published one claim twice; the evidence meets both, and each
        disposes of it against its own record.

        `upto` bounds the marks by publication round, so a disposer at round r
        does not answer for a challenge made after it. The board itself keeps no
        notion of a current round — it is a place, not a clock — so the bound is
        the caller's to supply.
        """
        return [m for m in self._marks
                if m.kind == CHALLENGE and m.content == law
                and (upto is None or m.round_idx <= upto)]

    def corroboration_calls(self, law: Optional[Tuple[str, str]] = None,
                            upto: Optional[int] = None) -> List[Mark]:
        """The calls for corroboration standing on this board, in publication
        order — every one, or only those about `law`.

        READ BY BOTH SIDES, which is why it lives here rather than in either.
        A peer reads it to find out what it is being asked about; the calling
        author reads its own call back to recover the round the doubt opened in
        and the individual it named, because a call is a public inscription and
        there is no reason for the author to keep a private copy of what it
        already said in the open.

        `upto` bounds by publication round, as `challenges_against` does and for
        the same reason: the board is a place and keeps no clock.
        """
        return [m for m in self._marks
                if m.kind == CORROBORATION
                and (law is None or m.content == law)
                and (upto is None or m.round_idx <= upto)]

    def fact_marks(self, content: Fact,
                   upto: Optional[int] = None) -> List[Mark]:
        """Every published `"fact"` mark carrying exactly `content`, in
        publication order.

        `answer_to` reads the board this way for a question; a corroboration
        call needs the same reading for the head atom that would rebut its
        doubt, and it needs ALL of them rather than the first, because who said
        it matters (an author does not rebut its own doubt with its own
        testimony — it has its own record for that).
        """
        return [m for m in self._marks
                if m.kind == FACT and m.content == content
                and (upto is None or m.round_idx <= upto)]

    def record_uptake(self, mark: Mark, adopter: str) -> None:
        """Note that `adopter` took this mark up. Idempotent: uptake is a SET of
        adopters, because the observable is how many units rely on a mark, not
        how many times each mentioned it.

        Refuses a mark that was never published: nothing can be taken up that
        was never put where it could be encountered, and an uptake edge on an
        unpublished mark would be a reliance no reader could have formed.
        """
        self._require_published(mark)
        self._uptake[mark].add(adopter)

    def uptake_of(self, mark: Mark) -> Set[str]:
        """Who took this mark up — a copy, so the record cannot be edited
        through the reader."""
        self._require_published(mark)
        return set(self._uptake[mark])

    def _require_published(self, mark: Mark) -> None:
        if mark not in self._uptake:
            raise ValueError(
                f"mark {mark.content!r} by {mark.author} is not published on "
                f"this board: it could not have been encountered here"
            )
