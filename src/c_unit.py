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

from c_field import CONSEQUENT_LAG, Aperture, Field
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
cannot drift apart.

THE VALUE 0.05 SITS BELOW THE FIELD'S DEFAULT WITHHOLD RATE OF 0.10, AND THAT
WAS MEASURED RATHER THAN ARGUED. Reading `pending` open-world (see
`_pending_split`) removes the individuals whose consequents could not have
arrived, which is what the tolerance used to be silently absorbing. What it does
NOT remove is a consequent the field withheld outright: once the lag has elapsed
that individual is indistinguishable from a genuine refutation, so the tolerance
still has to cover the withhold rate. Measured over the fourteen seeds this suite
uses, 60 rounds, one unit absorbing the field, asking the criterion about its
aperture's two planted laws at every round from 10 to 59 — the proportion of
rounds at which a TRUE law meets its own criterion:

    tolerance      withhold 0.00   withhold 0.10   withhold 0.20
    0.05                  100.0%           52.8%           18.2%
    0.10                  100.0%           76.3%           43.0%
    0.15                  100.0%           93.6%           65.0%
    0.20                  100.0%           99.0%           80.5%
    0.30                  100.0%          100.0%           94.9%

SO THE ANSWER TO "DOES THE CRITERION STILL DEPEND ON A TOLERANCE ABOVE THE
FIELD'S WITHHOLD RATE" IS YES, and the dependence is steep: with no withholding
the tolerance is irrelevant, and at each withhold rate a true law reads sustained
at most rounds only once the tolerance is one and a half to two times the
withhold. A unit cannot observe its field's withhold rate. Whatever value stands
here therefore encodes an assumption about the world that the unit holding the
law has no way to check — the same shape of assumption as `CONSEQUENT_LAG`, and
worth naming as such.

THE VALUE WAS NOT RAISED, and the reason is that raising it buys nothing where
the defect actually bit and costs a great deal everywhere else. Measured end to
end on the induce arm — eight seeds, 60 rounds, four units inducing from what
they meet, the challenge channel live, the tolerance the only variable:

    tolerance   defeats   suspensions   true laws lost   UNPLANTED LAWS HELD
    0.05              4            60                0                     0
    0.10              8            62                0                     0
    0.15             10            76                0                    10
    0.20             14           103                0                    26
    0.30             19           133                0                    49

(Re-measured after inquiry was ordered before elimination; the sweep read 16 /
14 / 25 / 43 / 60 defeats and 0 / 0 / 10 / 25 / 54 unplanted laws under the
previous disposal, so the argument's shape is unchanged and the defeat counts
fell across the board.)

Permanent loss of true laws is already zero at 0.05, so a larger tolerance has
nothing to repair; what it does instead is admit accidental laws — 49 of them
standing at the end of the run at 0.30, none at 0.05 — and put more laws in doubt
(133 suspensions against 60) rather than fewer. The per-round reading agrees:
across the twenty ordered relation pairs one unit's aperture can carry, the
proportion of rounds at which an UNPLANTED pair meets the criterion rises
0.0% / 0.1% / 0.6% / 1.0% / 2.4% over those five tolerances at withhold 0.10. The
converses stay at 0.0% at every tolerance, refused by precedence rather than by
the rate, so a converse-only measurement would have reported the cost as zero. It
is not zero."""


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

    WHAT THAT RULE MEANS WHEN THE CHALLENGER IS THE HOLDER, since a doubt can
    now be raised by the author's own record as well as by a peer's citation.
    THE AUTHOR'S OWN RECORD IS NEVER ONE OF THE TWO VOICES. It is not a vote: it
    is the very record every cited counterexample is checked against, and it
    already has an exit of its own at the window. Counting it as corroboration
    would let ONE foreign counterexample plus the author's own gap eliminate a
    law — which is exactly the rule Task 5 measured, where a single foreign
    counterexample destroyed 58 of 58 laws the field actually carries, since
    under a fallible field the author's own gap is what a withheld consequent
    looks like. So `challenger` names a PEER or nothing, and the corroboration
    tally reads foreign challenge marks only: **elimination from outside takes
    two distinct foreign records, whoever raised the doubt.**

    THE HOLE THIS CLOSED WAS LOAD-BEARING. `challenge` scans the board by
    content, so a unit that holds a law two units published may publish a
    challenge to it — its own inscription, against its own law. Before this
    task the author's own mark could take the challenger's slot or be counted as
    the corroborating voice, and measured under bounded attention it was in the
    live set of all 8 of 8 corroborations at seed 1, eliminating 64 of 64 true
    laws at an age of exactly one round across the eight seeds. The self-raised
    doubt had merely changed clothes: what used to be an immediate internal
    retraction became a one-round self-corroboration.

    WHAT THE AUTHOR'S OWN RECORD MAY DO is decide which way the window ends, and
    only once the window has run out. It cannot shorten the inquiry. That is the
    whole of the change this task makes: before it, a re-assessment that failed
    settled the law on the spot, so the doubter's own record both raised and
    closed the doubt in one act, and under bounded attention it did so at round 0
    in 66 of 66 measured cases — before the community it could have asked had
    said anything. The criterion is re-read AT expiry rather than remembered from
    the round the doubt opened, so a record that has grown in the meantime is
    read as it stands (`Unit._dispose_doubt`).
    """

    challenger: Optional[str]
    """Whose citation the doubt currently rests on, or `None` while no peer has
    disputed the law at all — a SELF-RAISED doubt, opened because the author's
    own published counterexample contradicts its own law. The first peer to
    speak fills the slot (`Unit._dispose_doubt`), and only a second, distinct
    peer corroborates."""
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
    criterion the unit would use to induce it today, AND the inquiry that
    re-assessment provoked ran its whole window without anything arriving to
    repair the record. No peer corroborated; the author settled it on its own
    evidence, after asking."""
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
    the challenge failed to gather support — AND the author's own record still
    sustains the law. THE WINDOW FIRES ONCE AND EXITS TWO WAYS: this list and
    `retracted_internally` are both window expiries, split by what the record
    says at the moment it expires."""
    asked: List[Mark] = dc_field(default_factory=list)
    """The questions published in the course of the inquiry — one per pass, about
    an individual the doubted law licenses and the record lacks.

    RETURNED RATHER THAN LEFT ON THE BOARD ALONE because an asker has to be able
    to take up its own answer: uptake in this series is targeted (a unit adopts a
    reply only to a question it asked itself), and a question minted inside a
    disposal would otherwise be one no driver knows to watch for."""

    def __bool__(self) -> bool:
        """Whether any LAW'S STANDING moved. A pass that only published a
        question is falsy: the inquiry is under way and nothing has been
        decided, which is exactly what the callers testing for quiescence
        mean."""
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
    material part of a sixty-round run.

    3, 5 AND 8 ARE NOW MEASURED, AND THE DEFAULT WAS LEFT ALONE — it is the
    author's. Eight seeds, 60 rounds, bounded attention, planted laws and
    converses seeded.

    WITHOUT AN ANSWERING CHANNEL THE VALUE CHANGES NOTHING. At four units and at
    six, windows of 3, 5 and 8 read identical suspensions, corroborations,
    internal retractions and survivors — every column. That is the previous
    task's finding at full strength: an inquiry with no answering channel is a
    delay, and the LENGTH of a delay is irrelevant when nothing comes back.

    WITH THE ASK CHANNEL LIVE IT IS THE MOST CONSEQUENTIAL KNOB IN THE ARM, and
    it trades score for laws monotonically:

        units   window   internal   rebutted   true laws lost   net
        4            3         64          0            64/64   −41
        4            5         36         25            36/64  −106
        4            8         20         44            20/64  −185
        6            3         71         28            96/96   −29
        6            5         41         58            69/96   −77
        6            8         19         80            47/96  −134

    AND IT DISCRIMINATES, WHICH NOTHING ELSE IN THIS SERIES HAS. At six units,
    3 → 8 saves 49 true laws (96 lost to 47) while sparing only 3 converses (20
    to 17). A true law's missing head is the thing a peer can actually supply and
    a converse's is not, so waiting longer helps the true law disproportionately.
    Corroboration is flat at 45 across all three windows, so this knob and
    `corroborating_witnesses` are independent.

    IT NOW FIRES, WHICH IT NEVER DID BEFORE. Under the ruling's original shape
    the window expired zero times in every measured arm: a doubt was settled by
    the author's own record long before five rounds passed, or by a peer, or not
    at all. With the internal arm routed through the same lifecycle it carries
    most of the traffic — over eight seeds, 60 rounds, four units under bounded
    attention with the ask channel live, **41 of 66 doubts end at the window**
    (36 given up, 5 restored) against 25 closed early by rebuttal; with the ask
    channel muted, all 66. So the value of this number now matters to the
    outcome in a way it did not, and it is worth the author's attention rather
    than a default's."""
    corroborating_witnesses: int = 2
    """How many DISTINCT FOREIGN RECORDS must stand against a law before the
    doubt is corroborated and the law eliminated.

    THE AUTHOR'S RULING, in the author's own words: *"Corroboration exists
    largely to generate and build confidence in the independent views that build
    a socially available, objectified reality. Repeating one's own observation
    does not do this. So, 2 needs at least 2 independent witnesses."* The ground
    is Berger & Luckmann's rather than arithmetical, and it is the better reason:
    a record repeating itself contributes nothing to a shared, objectivated
    reality, so a unit's own inscription is never a corroborating voice however
    many times it is published.

    WHO THE TWO ARE. The HOLDER never counts — its record is what every citation
    is checked against, and it has an exit of its own at the window. The
    CHALLENGER counts as ONE: it observed the counterexample and said so, which
    is an independent view. So the default 2 means the challenger plus at least
    one further unit, distinct from both the challenger and the holder. The
    original challenger's evidence still cannot count TWICE — the tally is over
    distinct authors, so it counts once, as one of the two, and cannot close the
    doubt it opened alone.

    WHY IT IS A KNOB. Whether the challenger should count as one of the two is
    the controller's reading of the ruling, not the ruling itself, and the
    stricter alternative — two further units beyond the challenger, i.e. THREE
    foreign records — is reachable by setting this to 3. Both bars are exercised
    on one situation in
    `tests/test_c_channels.py::test_the_corroborating_bar_is_the_author_s_to_set`
    and measured end to end over eight seeds in
    `::test_corroboration_fires_once_a_domain_has_three_witnesses`, so the line
    can be moved on evidence rather than on another build.

    THE STRICTER BAR IS UNREACHABLE IN THIS FIELD, which is a finding rather
    than an argument against it. Four domains at two-domain apertures give a
    domain at most three witnesses, so holder + challenger + one corroborator
    exhausts the community: measured at six units over eight seeds, a bar of 3
    reads **0 corroborations of 144 doubts** — exactly what the cyclic four-unit
    arm reads. Moving the author's line to 3 costs a fifth domain, not a bigger
    community.

    IT COUNTS RECORDS, NEVER INSCRIPTIONS. Two marks from one unit are one
    witness. `challenge` mints once per law ever per unit, so a unit cannot
    publish twice against one law in the first place, but the tally is a set of
    authors so that the rule holds whatever any future channel mints — pinned in
    `test_a_unit_publishing_twice_cannot_corroborate_alone`.

    WHAT THE FIELD MUST SUPPLY FOR IT TO FIRE AT ALL. Two foreign records means
    a domain must be witnessed by at least THREE units (holder, challenger,
    corroborator). Under the cyclic aperture scheme every domain sits in exactly
    two apertures at any community size, so this rule was measured firing 0 times
    in 66 doubts — the rule was correct and the field could not satisfy it. See
    `c_field.apertures_for`'s `PAIRS` scheme and its `min_witnesses` refusal."""
    replication_window: int = 10
    """How many rounds an adopted fact waits for the unit's own aperture to
    deliver it before the unit reads the silence as a failure (`settle_credit`).

    NO HONEST VALUE EXISTS IN THIS FIELD, and the number is here so that the
    absence is visible rather than buried in a comparison. "Enough rounds for it
    to have arrived" is a claim about the field's redelivery cadence, and this
    field draws one individual per relation per round from a list of forty: an
    individual waits about forty rounds for its next turn, and a unit under
    bounded attention meets half of those, so the expected wait is longer than
    the sixty-round run. Whatever stands here therefore decides mostly how many
    adopted facts get read as failures, not whether they really failed — the
    same shape of assumption `MAX_PENDING_RATE` and `CONSEQUENT_LAG` carry, and
    worth naming as such.

    MEASURED AT 5, 10 AND 20, four units under bounded attention, eight seeds,
    60 rounds, the typified arm, over the same 939 adoptions:

        window   proved   failed   still pending   preferences held at the end
        5           347      552              40                             0
        10          347      508              84                             1
        20          347      434             158                             5

    THE PROVED COUNT DOES NOT MOVE. Whether a second route delivers the fact is
    the field's business and not this deadline's; all the window decides is how
    many unreplicated facts are read as failures and how many are still waiting
    when the run ends. A longer window holds more preferences only by declining
    to conclude. Measured in
    `tests/test_c_channels.py::test_the_replication_verdict_reads_the_field_s_cadence_not_the_peer`."""
    peers: Dict[str, Dict[str, int]] = dc_field(default_factory=dict)
    """What this unit has learned about WHOM IT IS TALKING TO: per peer, per
    relation, a running count of the answers that proved out minus the answers
    that did not.

    THIS IS THE FIRST THING IN THE SERIES A UNIT HOLDS ABOUT ANOTHER UNIT, and
    it is deliberately not a model of that unit. It records how one unit's
    testimony about one relation has fared in this unit's own record — Berger &
    Luckmann's reciprocal typification of habitualized action by TYPES of actor
    ("someone who tells me things about a_head that hold up"), not an inspection
    of the peer's holdings, its aperture or its reasoning. Nothing here reads
    another unit; every entry is written by `credit`, from a mark this unit
    encountered and a verdict this unit reached against its own arrivals.

    KEYED BY RELATION RATHER THAN BY PEER ALONE, because a peer's aperture is
    partial: a unit that meets alpha and delta can speak well about `a_head` and
    know nothing whatever about `g_head`, and one number per peer would average
    competence over domains the peer never sees."""
    ledger: MembraneLedger = dc_field(default_factory=MembraneLedger)
    last_provenance: Dict[Fact, FrozenSet[Fact]] = dc_field(default_factory=dict)
    first_seen: Dict[Fact, int] = dc_field(default_factory=dict)
    """The round each fact was FIRST held. Only ever written, never revised: a
    fact re-delivered later does not move its first arrival. This is the unit's
    own record of its own history — it reads no round order off the field, only
    off when things reached its own membrane — and it is what lets `induce`
    tell a law from its converse (see `induce`).

    FIRST-HAND ONLY. An adopted mark does not write here; the argument is in
    `adopt`, and `adopted_at` is where testimony's own clock is kept."""
    adopted_at: Dict[Fact, int] = dc_field(default_factory=dict)
    """The round this unit ADOPTED each fact it took from a peer's mark. Written
    once, never revised, exactly as `first_seen` is.

    TWO CLOCKS, BECAUSE TWO DIFFERENT QUESTIONS ARE ASKED OF A DATE and only one
    of them needs the date to be a deliverance.

    - *Which way does this law run?* — answered by `_body_precedes_head`, which
      infers direction from the field's one-round lag and therefore reads
      `first_seen` and nothing else. A peer's mark is not a deliverance and says
      nothing about when anything happened, so it is kept out; the arm that shows
      what happens if it is let in is
      `tests/test_c_marks.py::test_testimony_cannot_mislead_precedence_and_defeat_a_true_law`.
    - *Has the head had time to arrive?* — answered by `_pending_split`, which
      needs to know only WHEN THIS UNIT CAME TO HOLD THE BODY. That the unit met
      it in a peer's inscription rather than at its own membrane does not make
      the question unanswerable: the unit knows perfectly well which round it
      read the board. Both clocks feed `_held_since`, which is what that reader
      uses.

    THE DATE IS THE ADOPTING UNIT'S ENCOUNTER, NOT THE PEER'S OBSERVATION, and
    the difference is the whole reason this is a second dict rather than a
    reunion. It records when *I* met the fact. It makes no claim about when the
    author met it, and nothing reads it as one."""
    _published: Set[Tuple[str, Content]] = dc_field(default_factory=set)
    """What this unit has already published, as `(kind, content)` pairs — not as
    marks, since a mark carries the round it was published in and would compare
    unequal every round, so the unit would republish everything forever."""
    _supplied_by: Dict[Fact, Mark] = dc_field(default_factory=dict)
    """Which mark each adopted fact came in on, kept so that a verdict reached
    later can be credited to the unit that actually supplied it. Written by
    `adopt` and read by `settle_credit`; the mark is frozen, so keeping it is
    keeping the inscription rather than a surrogate for it."""
    _credited: Set[Fact] = dc_field(default_factory=set)
    """The adopted facts already settled either way. A verdict is entered ONCE,
    for the reason `anticipate` stakes once: the unit of account is the fact, and
    a fact re-read every round would charge one piece of testimony to its author
    fifty times."""
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

    def _held_since(self, fact: Fact) -> Optional[int]:
        """The round this unit came to hold `fact`, by whichever route reached
        it first — its own membrane or a peer's mark — or `None` if it holds it
        with no date at all (placed directly, as tests do).

        THE EARLIER OF THE TWO WINS, because the question this answers is "how
        long have I had this", and the answer is the first time it arrived by any
        route. A fact adopted at round 5 and delivered first-hand at round 9 has
        been in this record since 5."""
        dates = [d for d in (self.first_seen.get(fact), self.adopted_at.get(fact))
                 if d is not None]
        return min(dates) if dates else None

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
        assumed. Measured on the induce arm, eight seeds, 60 rounds: **+922 with
        the channel live against +1038 mute**, an 11% cost, of which about one
        point in ten is the extra rounds a doubt now spends being inquired into
        rather than settled on the spot (it was +932 before that change).
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
        0.00 to 0.11, so the 0.5 cut is not near any observed value. (The
        mid-range pairs that do sit near 0.5 — `shared -> a_head` and the like,
        0.38 to 0.75 — are refused by the pending rate instead, which after the
        open-world reading of `pending` reads 0.41 to 0.65 for them, still an
        order clear of the 0.05 tolerance.)

        RE-MEASURED at the end of a 60-round run rather than at every round, the
        planted spread reads 0.87 to 1.00 and the converse spread 0.00 to 0.13,
        with the nearest other pair at 0.17. The gap is narrower than the
        every-round reading above reports and is still wide; the two figures are
        left side by side rather than one overwriting the other, because the
        difference is in when the question is asked and neither is wrong.

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

    def _pending_split(self, body_rel: str, head_rel: str, round_idx: int
                       ) -> Tuple[Set[Tuple[Key, ...]], Set[Tuple[Key, ...]],
                                  Set[Tuple[Key, ...]]]:
        """Split the individuals this unit holds under `body_rel` into three:
        those it also holds under `head_rel` (CONFIRMED), those that could have
        carried the head by now and do not (REFUTING), and those about which the
        unit has observed nothing either way (UNKNOWN).

        THE THIRD SET IS THE POINT. An individual holding the body without the
        head reaches that state by three routes, and only one of them is
        evidence against the law:

        1. The lag has not elapsed. The field delivers a consequent
           `CONSEQUENT_LAG` rounds after its antecedent, so an individual whose
           body arrived this round HAS no head yet and cannot have one. Nothing
           has been observed against the law.
        2. The head was never delivered here. `FieldSpec.withhold_rate` is 0.10
           by default and bounded attention drops more, so a consequent can
           simply fail to reach this membrane, leaving its individual pending
           forever. The unit did not observe an absence; it failed to observe.
        3. The head genuinely does not hold. Only this refutes.

        An undated body — a fact placed directly, with no arrival of any kind
        behind it — is UNKNOWN for the same reason: ABSENT TIMING EVIDENCE IS NOT
        COUNTER-EVIDENCE, which is the principle `_body_precedes_head` already
        keeps for direction. A unit that cannot say when it came to hold the body
        cannot say whether the head has had time to arrive.

        AN ADOPTED BODY IS DATED AND DOES COUNT, which it did not before this
        task. The clock read here is `_held_since`, so a fact taken from a peer's
        mark is timed by THE ROUND THIS UNIT ADOPTED IT — its own encounter, not
        the author's observation. The reason is that testimony which can only
        ever help is not testimony: under the previous ruling an adopted fact
        enlarged a law's support (an individual carrying body and head is
        confirmed on content alone) and could never weigh against one, so the
        assert channel was a one-way instrument for induction. Reading the
        adoption round closes that: after the lag has elapsed an adopted body
        with no head refutes exactly as a delivered one does. Measured in
        `tests/test_c_marks.py::test_adopted_facts_count_as_support_and_now_as_refutation`.

        ROUTE 1 IS THE ONE THIS SPLIT REPAIRS, and it repairs itself by waiting.
        ROUTE 2 IS NOT REPAIRED HERE: once the lag has elapsed, an individual
        whose head simply never reached this membrane is indistinguishable from
        one whose head does not hold, so it lands in REFUTING beside route 3.
        Only the community could tell them apart — a peer that was looking when
        the head arrived can publish it, and adopting it moves the individual
        from refuting to confirmed. Whether the community does is measured in
        `tests/test_c_channels.py::test_peer_testimony_repairs_the_true_law_once_the_law_survives_to_ask`,
        and over eight seeds under bounded attention IT NOW DOES: some peer holds
        the missing head for 590 of the 640 refuting individuals a muted arm
        carries, and with the ask channel live the refuting count falls to 349
        while 28 of 64 true laws that were otherwise lost survive the run. It did
        NOT before inquiry was ordered ahead of elimination — the same
        measurement then read 636 and four repaired individuals, because the
        internal re-assessment retracted the law at round 0 and a law nobody
        holds asks no questions.
        """
        holders = self._holders()
        body_args = holders.get(body_rel, set())
        head_args = holders.get(head_rel, set())
        confirmed = body_args & head_args
        refuting: Set[Tuple[Key, ...]] = set()
        unknown: Set[Tuple[Key, ...]] = set()
        for args in body_args - head_args:
            arrived = self._held_since((body_rel, args))
            if arrived is None or round_idx - arrived < CONSEQUENT_LAG:
                unknown.add(args)
            else:
                refuting.add(args)
        return confirmed, refuting, unknown

    def _meets_criterion(self, law: Tuple[str, str], round_idx: int,
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

        THE RATE IS READ OVER WHAT WAS OBSERVED, NOT OVER EVERY INDIVIDUAL HELD.
        `_pending_split` sets aside the individuals whose heads could not have
        arrived yet or never reached this membrane, and the tolerance is measured
        against the rest: `refuting / (refuting + confirmed)`. AN UNKNOWN
        INDIVIDUAL LEAVES BOTH THE NUMERATOR AND THE DENOMINATOR. Counting it in
        the denominator would silently convert an abstention into a pass —
        twenty unseen individuals would dilute two real refutations to 9% —
        and counting it in the numerator is the defect this replaces.

        WHEN NOTHING WAS OBSERVED EITHER WAY THE TEST ABSTAINS AND PASSES, and
        `min_support` is what still stops a law with no evidence: a zero
        denominator means the confirmed set is empty too, so support is zero and
        the law was already refused above.

        `round_idx` is the round the question is asked AT, threaded from the
        caller — `step` for `induce`, the disposal round for a challenged law.
        The unit reads no clock of its own; what "now" means is supplied by
        whoever is asking, and both readers supply the same kind of thing.

        Read only against `self.facts`. Nothing about the challenger, the board
        or the field's regime enters."""
        body_rel, head_rel = law
        if body_rel == head_rel:
            return False
        confirmed, refuting, _unknown = self._pending_split(
            body_rel, head_rel, round_idx)
        if len(confirmed) < min_support:
            return False
        observed = len(refuting) + len(confirmed)
        if observed and len(refuting) > max_pending_rate * observed:
            return False
        return self._body_precedes_head(body_rel, head_rel, confirmed)

    def induce(self, round_idx: int, min_support: int = MIN_SUPPORT,
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

        THE PENDING SET IS READ OPEN-WORLD. An individual whose head has not had
        time to arrive, or never arrived at this membrane at all, is set aside
        rather than counted against the law; see `_pending_split`. That is why
        `round_idx` is required — "few enough carry body without head" is a claim
        about a moment, and the unit is told which one rather than guessing.

        THE TEST ITSELF LIVES IN `_meets_criterion`, which is also what a
        challenged law is re-assessed against. One criterion, two readers: what
        it takes to take a law up is exactly what it takes to keep it.

        A SUSPENDED LAW IS NOT RE-ADMITTED HERE, and the guard is the same `law
        in self.laws` skip that stops any held law being proposed twice:
        suspension is a subset of `laws`, so a law under doubt is invisible to
        this scan and cannot be quietly returned to active service by a record
        that has grown. Only `_dispose_doubt` lifts a suspension, and it does so
        by name. (The other route into `laws` is `adopt`, which likewise finds a
        suspended law already held and changes nothing.)"""
        holders = self._holders()
        found: Set[Tuple[str, str]] = set()
        for body_rel in sorted(holders):
            for head_rel in sorted(holders):
                law = (body_rel, head_rel)
                if law in self.laws:
                    continue
                if self._meets_criterion(law, round_idx, min_support,
                                         max_pending_rate):
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
            self.induce(round_idx)

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
        and adopting is a separate act. Choosing WHOSE marks to read seriously is
        typification's business (`credit`, `whom_to_ask`) — built now, and
        measured inert in this field: a reply about a relation can come only
        from a peer that witnesses the domain on the rounds this unit does not,
        and there is at most one of those, so a preference has nothing to prefer
        against.
        """
        return [m for m in board.since(round_idx) if m.author != self.unit_id]

    def adopt(self, mark: Mark, board: MarkBoard, round_idx: int) -> bool:
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

        AN ADOPTED FACT IS HELD, AND IT IS DATED BY THIS UNIT'S OWN ENCOUNTER —
        `round_idx`, the round this unit read the board and took the content up.
        IT IS NOT A CLAIM ABOUT WHEN THE PEER OBSERVED ANYTHING. The peer's own
        history is not on the mark and there would be no reason to trust it if it
        were; what this unit can say without hearsay is which round the fact
        entered its own record, and that is what `adopted_at` holds.

        THE DATE GOES IN A SECOND DICT, NOT IN `first_seen`, and the split is the
        whole ruling. `first_seen` is the unit's record of when something reached
        its OWN membrane from the field, and `_body_precedes_head` reads it to
        tell a law from its converse: direction is inferred from the field's
        one-round lag, so those dates must be dates of deliverances. An adopted
        mark is not a deliverance. It reached the unit as a peer's inscription,
        at whatever round that peer got round to publishing, which stands in no
        fixed relation to when anything happened.

        Stamping it anyway would make a unit's sense of temporal order partly
        hearsay, and precedence-based induction could then be defeated by
        testimony: a peer's marks arriving late about individuals whose heads
        this unit observed early read as twenty supporters with the body second,
        outvoting the few genuine observations, and a TRUE law is refused
        because of when someone else spoke. That is measured, not feared —
        `tests/test_c_marks.py::test_testimony_cannot_mislead_precedence_and_defeat_a_true_law`
        builds both arms and the stamped one refuses the law.

        The alternative candidates were considered and rejected. Stamping the
        author's `round_idx` into `first_seen` imports another unit's clock while
        LOOKING first-hand, which is the same defect wearing a better disguise.
        Carrying the author's own `first_seen` alongside the mark would make the
        content of a mark include the author's private history, and there is no
        reason a reader should be able to read that off an inscription — nor any
        reason to trust it if it could.

        WHAT THE ADOPTION DATE BUYS IS A TESTIMONY THAT CAN WEIGH BOTH WAYS.
        Adopted content has always enlarged a law's SUPPORT — an individual
        carrying body and head is confirmed on content alone, no date needed —
        and until this task an adopted BODY could not refute one, because
        `_pending_split` set an undated body aside as unknown. Testimony that can
        only ever help is not testimony: the assert channel was a one-way
        instrument for induction, and a peer could bear a law out but never
        weigh against it. Dating the encounter closes that, and only that: after
        the field's lag has elapsed an adopted body with no head refutes exactly
        as a delivered one does, while direction still reads deliverances only.
        Measured both ways in
        `tests/test_c_marks.py::test_adopted_facts_count_as_support_and_now_as_refutation`.

        And the first-hand date is not spent: if the field later delivers an
        adopted fact, `_record` dates it in `first_seen` then, at the unit's first
        genuinely first-hand encounter with it.
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
            self.facts.add(mark.content)        # NOT self._record: not first-hand
            self.adopted_at.setdefault(mark.content, round_idx)
            if fresh:
                # WHO SUPPLIED IT IS PART OF WHAT WAS ENCOUNTERED. The author
                # rides on the mark already; remembering it is what lets a
                # verdict reached ten rounds from now be credited to the unit
                # that actually spoke (`settle_credit`).
                self._supplied_by.setdefault(mark.content, mark)
        elif mark.kind == LAW:
            fresh = mark.content not in self.laws
            self.laws.add(mark.content)
        else:                                   # pragma: no cover - Mark refuses
            raise ValueError(f"unknown mark kind {mark.kind!r}")
        if fresh:
            board.record_uptake(mark, self.unit_id)
        return fresh

    # --- the typify channel: credit, whom_to_ask, settle_credit --------------
    #
    # A QUESTION CANNOT CHOOSE WHOM TO ASK. It is published to the whole board,
    # and until now that was the end of it: a unit took whatever came back,
    # because it had nothing on which to prefer one voice to another. What it
    # can do instead is keep a record of how each voice has fared, and act on it
    # — which is typification, and it is the one thing in this series that
    # cannot exist in a solitary unit at all.
    #
    # THE RECORD IS THE UNIT'S OWN AND READS NOTHING ELSE. A verdict on a piece
    # of testimony comes from the unit's own subsequent arrivals, never from the
    # field's regime, never from whether a law survived, and never from anything
    # only the experiment knows. That constraint is what stops the channel being
    # a tautology, and it is what makes the verdict weak — see `settle_credit`.

    def credit(self, mark: Mark, proved: bool) -> None:
        """Enter one verdict about one peer's testimony on one relation.

        A verdict is a small integer, not a probability and not a reputation:
        `+1` when the testimony proved out, `−1` when it did not. What it
        accumulates over is `(author, relation)`, so a peer earns its standing
        where it actually has an aperture and nowhere else.

        THE VERDICT IS SUPPLIED, NOT COMPUTED HERE, because who is entitled to
        reach it matters more than how it is tallied. `settle_credit` is the
        reader that reaches one from this unit's own record; a caller may reach
        one another way, and this method will enter it — which is why it says in
        `settle_credit`, and not here, what a sound verdict may rest on.

        A unit does not credit itself. Its own inscription is not testimony, and
        an entry under its own name would let it prefer itself to the community
        it is asking."""
        if mark.author == self.unit_id:
            raise ValueError(
                f"{self.unit_id} cannot credit its own mark {mark.content!r}: "
                f"a unit's own inscription is not testimony, and typifying "
                f"itself would let it prefer its own voice to the community's"
            )
        if mark.kind != FACT:
            raise ValueError(
                f"{self.unit_id} cannot credit the {mark.kind} {mark.content!r}: "
                f"only a fact mark asserts something this unit's own arrivals "
                f"can bear out or fail to"
            )
        relation, _args = mark.content
        self.peers.setdefault(mark.author, {})
        self.peers[mark.author][relation] = (
            self.peers[mark.author].get(relation, 0) + (1 if proved else -1))

    def whom_to_ask(self, relation: str) -> Optional[str]:
        """The peer whose testimony about `relation` has fared best, or `None`
        when no peer has earned a positive score.

        `None` MEANS "NO PREFERENCE", NOT "NOBODY". A unit with no evidence
        about a relation is in exactly the position every unit was in before
        this channel existed, and the honest thing for it to do is what it did
        then — publish the question to the whole board and take what comes. A
        preference has to be earned before it may narrow anything.

        Ties break on the peer's own id, so which of two equally-borne-out
        voices is preferred is a deterministic function of this unit's record
        rather than of dictionary order."""
        best: Optional[Tuple[str, int]] = None
        for author in sorted(self.peers):
            score = self.peers[author].get(relation, 0)
            if score > 0 and (best is None or score > best[1]):
                best = (author, score)
        return None if best is None else best[0]

    def settle_credit(self, round_idx: int) -> List[Tuple[str, Fact, bool]]:
        """Reach a verdict on every piece of adopted testimony this unit's own
        record can now decide, enter it, and report what was decided.

        REPLICATION IS THE VERDICT, and it is the only one available to a unit
        that cannot check the world. An adopted fact PROVES OUT when this unit's
        own aperture later delivers the same fact — a second, independent route
        brought the same thing. It FAILS when the unit has met that relation
        first-hand before (so the fact's domain is one it actually witnesses),
        `replication_window` rounds have passed, and nothing arrived.

        THE THIRD OUTCOME IS THE ONE THAT KEEPS IT HONEST. A fact whose window
        has not elapsed is undecided and credits nothing either way; so is a
        fact of a relation this unit has never met at its own membrane, because
        a unit whose aperture does not cover a domain never fails to see
        anything there — it simply is not looking, and reading its own blindness
        as a peer's fault would credit the aperture rather than the testimony.
        That is `_pending_split`'s open-world discipline applied to a second
        question, and for the same reason.

        WHAT THE VERDICT DOES NOT CARRY, measured rather than argued: any
        information about the peer. Replication depends on whether the field
        redraws that individual, which is independent of who reported it, so the
        verdict is an unbiased and nearly powerless signal — every peer
        accumulates at the same base rate. Eight seeds, 60 rounds, four units
        under bounded attention: 855 verdicts entered on 939 adoptions, 347 of
        them positive, and of the 96 (peer, relation) pairs the community
        accumulates any record about, **1 ends the run with a positive score**.
        At six units it is 5 of 107. Measured in
        `tests/test_c_channels.py::test_typified_asking_changes_nothing_and_the_reason_is_that_nobody_had_a_choice`.

        A FACT ALREADY HELD WHEN THE MARK ARRIVED NEVER REACHES HERE, and it is
        `adopt` that keeps it out: `_supplied_by` is written only when something
        NEW was taken up, exactly as uptake is recorded only then. The peer told
        this unit something it already had, and reading its own earlier arrival
        back as a later replication would credit the peer for its own
        observation. Pinned in
        `tests/test_c_channels.py::test_a_fact_already_held_first_hand_credits_nobody`.
        """
        decided: List[Tuple[str, Fact, bool]] = []
        seen_relations = {rel for rel, _args in self.first_seen}
        for fact in sorted(self._supplied_by):
            if fact in self._credited:
                continue
            mark = self._supplied_by[fact]
            adopted = self.adopted_at.get(fact)
            if adopted is None:                 # placed directly, never dated
                continue
            if fact in self.first_seen:         # a second route delivered it
                self._credited.add(fact)
                self.credit(mark, True)
                decided.append((mark.author, fact, True))
                continue
            relation, _args = fact
            if relation not in seen_relations:
                continue                        # not looking there: no verdict
            if round_idx - adopted < self.replication_window:
                continue                        # the window has not elapsed
            self._credited.add(fact)
            self.credit(mark, False)
            decided.append((mark.author, fact, False))
        return decided

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

        AN UNDATED BODY SORTS LAST among live wants — a body this unit holds with
        no arrival of any kind behind it, which in practice means one placed
        directly by a test. It has no evidence of how long that want has been
        waiting, and treating a body of unknown age as urgent would let something
        other than its own history set its priorities.

        AN ADOPTED BODY IS NOT UNDATED. It sorts by the round this unit adopted
        it (`_held_since`), because that is when the want was born HERE: the
        stake on its head will be placed at this unit's next attended round
        whatever route the body took to reach it. Before this task an adopted
        body carried no date at all and sorted last on the ground that a peer's
        publication schedule should not set this unit's priorities — true of the
        AUTHOR's clock, and now beside the point, since the clock read is this
        unit's own encounter.

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
                # -held_since: newest body first. A body this unit holds with no
                # arrival behind it at all sorts after every dated one.
                dated = self._held_since((body_rel, args))
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
        answer is relevant to it by the very definition of what it asked.

        THAT TARGETING HAS A SECOND CONSEQUENCE, FOUND BY MEASURING IT: a unit
        can only ever ask about an atom its own record already licenses, so a
        head the field FABRICATED — one that no antecedent ever licensed — is
        never asked about and never adopted. Over eight seeds and 60 rounds the
        field fabricated 37 head atoms, every one inside some unit's aperture,
        and **0 of the 939 adoptions took one up**
        (`tests/test_c_channels.py::test_no_fabricated_fact_is_ever_adopted_so_p_g1_has_no_category_to_measure`).

        WHAT A QUESTION CANNOT DO is choose whom to ask — it is published to the
        whole board. Typification (`credit`, `whom_to_ask`) is what would choose,
        and it is built and measured inert: a unit has at most one peer that can
        answer it about a given relation, so over the same eight seeds and 60
        rounds, on the 41 occasions (four units) and 54 (six units) at which a
        preference existed, it disagreed with the answering peer exactly 0 times.
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

        THE CITATION IS NOT READ OPEN-WORLD, and the asymmetry is deliberate but
        worth naming. `_pending_split` sets aside individuals whose heads could
        not have arrived yet; this reader does not, so a peer may cite an
        individual whose body it absorbed this very round. Nothing unsound
        follows — the cited law's author checks the citation against its own
        record and its own criterion, and an unelapsed case is one the author
        will find no fault with — but the challenge is noisier than it needs to
        be, and every noisy challenge spends the once-per-law-ever mint that a
        real counterexample would otherwise have used.
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
    #               today (`_meets_criterion`). This is where the gap Task 5 left
    #               open closes — `induce` only ever ADDED, and an admitted law
    #               was never re-tested against a grown record.
    #
    #   (external)  The author cannot rebut the cited individual from its own
    #               record, so it publishes a call for corroboration and the
    #               community answers from its own records.
    #
    # BOTH ARMS NOW TAKE THE SAME ROUTE: SUSPEND, SOLICIT, THEN DISPOSE. Until
    # this task only the external one did. An internal re-assessment that failed
    # retracted the law on the spot — the doubter both raising and closing the
    # doubt in one act — and the measurement said what that costs: under bounded
    # attention 66 of 66 internal refusals fired on `min_support` at a median of
    # ROUND 0, before any consequent could have arrived, so 64 of 64 true laws
    # were gone before the community they could have asked had spoken, and the
    # whole external apparatus ran zero times (0 suspended, 0 calls). *Do not
    # eliminate until corroboration* reads the same whoever raised the doubt.
    # A law in doubt is therefore held, published, licensing nothing, with a call
    # for corroboration out and a question going out each round; an independent
    # peer bearing the doubt out eliminates it; a peer holding the disputed
    # individual WITH the head restores it; and the window ends it either way —
    # restoring the law if the record sustains it by then, giving it up if not.
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
        reader cannot tell that its author gave it up or put it in doubt. What
        does reach the board is the INQUIRY — the call for corroboration, and the
        questions `_inquire` sends about the pending individuals — so a reader
        can see that a law is being asked about, never that it was given up.
        Closing the rest is the maintenance channel's work (spec §9b), left
        visible rather than pre-empted.
        """
        out = Disposition()
        for law in sorted(self.laws):
            standing = self._standing_challenges(law, board, round_idx)
            if law in self.suspended:
                self._dispose_doubt(law, standing, board, round_idx, out)
            elif standing:
                self._open_doubt(law, standing, board, round_idx, out)
        return out

    def _inquire(self, law: Tuple[str, str], board: MarkBoard, round_idx: int,
                 out: Disposition) -> None:
        """Ask the community about ONE individual the doubted law licenses and
        this record lacks — the internal arm's outward face.

        THIS IS THE ASK CHANNEL, UNMODIFIED AND POINTED AT THE DOUBT. The atom
        published is a `QUESTION` mark drawn from `_wants`, minted through the
        same once-per-content-ever key every other act uses, and answered by
        `answer` from a peer's own record. No new channel, no new mark kind, and
        no new priority rule: `_wants` already orders by what an answer could
        still change, and this reader simply takes the first of them that the
        law under doubt licenses.

        ONE PER PASS, for the reason `ask` sends one per round: attention is
        bounded, and a disposal that emptied the whole want-list would be a
        broadcast rather than an act. A doubt that stands for the whole window
        therefore asks up to `corroboration_window` questions, one per round,
        working down the pending individuals in want order.

        WHY THE INTERNAL ARM NEEDS ITS OWN QUESTION AT ALL, when the call for
        corroboration is already published. The two ask different things. A call
        names the law and the individual A PEER DISPUTED, and what it invites is
        evidence about that one case. An internal failure is about SUPPORT — the
        record does not carry enough confirmed individuals, or carries too many
        refuting ones — and the individuals that caused it are typically not the
        one cited. A question names one of those directly, which is the only
        shape of request a peer can answer from its own holdings.
        """
        body_rel, head_rel = law
        licensed = {(head_rel, args) for rel, args in self.facts
                    if rel == body_rel and (head_rel, args) not in self.facts}
        if not licensed:
            return
        for want in self._wants():
            if want not in licensed:
                continue
            key = (QUESTION, want)
            if key in self._published:
                continue
            mark = Mark(author=self.unit_id, content=want, kind=QUESTION,
                        round_idx=round_idx)
            board.publish(mark)
            self._published.add(key)
            out.asked.append(mark)
            return

    def _open_doubt(self, law: Tuple[str, str], standing: List[Mark],
                    board: MarkBoard, round_idx: int,
                    out: Disposition) -> None:
        """Dispose of a fresh challenge against an active law: rebut it, or
        suspend, solicit, and ask.

        NOTHING IS ELIMINATED HERE, whoever raised the doubt. Until this task an
        internal re-assessment that failed retracted the law on the spot, and
        under bounded attention it did so at round 0 in 66 of 66 measured cases:
        a seeded law has no supporting record when the first challenge lands, so
        the criterion refused it for want of evidence before the community had
        said anything at all. The external apparatus the author's ruling built —
        suspension, the call for corroboration, the window — never opened once in
        that arm: 0 suspended, 0 calls published. THE RULING IS APPLIED
        UNIFORMLY: *do not eliminate until corroboration* reads the same whoever
        raised the doubt, so the internal arm now takes the same route the
        external one does, and is disposed of in `_dispose_doubt`.

        WHAT THE RE-ASSESSMENT STILL DOES AT THIS POINT is decide whether to ask.
        A law whose own record no longer sustains it is a law with pending
        individuals to ask about, so the inquiry opens with a question as well as
        a call.
        """
        live = [m for m in standing
                if not self._rebutted(m, board, round_idx, testimony=False)]
        self._spent.update(m for m in standing if m not in live)
        if not live:
            return                              # rebutted: the law stands
        # A FOREIGN CITATION NAMES THE DOUBT WHEN THERE IS ONE, and when there is
        # none the doubt is SELF-RAISED and names nobody. A unit may have
        # published a challenge to a law it also holds; letting that inscription
        # take the challenger's slot would make the author's own record one of
        # the two voices corroboration needs, so a single peer could eliminate —
        # a weaker bar than the external arm has ever used, and the one Task 5
        # measured destroying 58 of 58 true laws. The author's record decides at
        # the window and nowhere else.
        foreign = [m for m in live if m.author != self.unit_id]
        trigger = foreign[0] if foreign else live[0]
        self._suspend(law, Doubt(challenger=trigger.author if foreign else None,
                                 individual=trigger.counterexample[1],
                                 opened_at=round_idx))
        self._solicit(law, trigger, board, round_idx)
        if not self._meets_criterion(law, round_idx):
            self._inquire(law, board, round_idx, out)
        out.suspended.append(law)

    def _dispose_doubt(self, law: Tuple[str, str], standing: List[Mark],
                       board: MarkBoard, round_idx: int,
                       out: Disposition) -> None:
        """Carry a suspended law's doubt forward one round.

        THE ORDER IS THE RULING'S ORDER, and each step is the answer to a
        different question.

        1. Has an INDEPENDENT peer borne the doubt out? That is corroboration,
           and it is the only thing that eliminates a law BEFORE the inquiry has
           run. TWO RECORDS ARE EXCLUDED FROM THE COUNT, AND FOR ONE REASON —
           a record already being weighed does not get a second voice. The unit
           that opened the doubt is excluded because its counterexample IS the
           doubt. THE AUTHOR ITSELF IS EXCLUDED because its own record is what
           every citation is checked against, and a unit may perfectly well have
           published a challenge to a law it also holds (`challenge` scans the
           board by content, so a claim two units published is disputable by
           either); reading that inscription back as a second voice would let a
           unit corroborate its own doubt with its own evidence.

           THAT WAS NOT A HYPOTHETICAL. Measured under bounded attention before
           the exclusion was added, the author's own challenge mark was in the
           live set of all 8 of 8 corroborations at seed 1 — as the trigger in
           four and as the corroborator in six — and across the eight seeds it
           eliminated 64 of 64 true laws at an age of exactly one round. The
           self-raised doubt had simply changed clothes: what used to be an
           immediate internal retraction became a one-round self-corroboration.

           WHAT IS COUNTED IS DISTINCT FOREIGN AUTHORS, and the bar is
           `corroborating_witnesses` (default 2 — the challenger plus one
           further unit). Counting authors rather than live inscriptions is the
           author's ruling in code: repeating one's own observation adds no
           voice. The count also tightened one edge the previous formulation
           left loose — it asked whether any foreign speaker OTHER THAN the
           named challenger stood, so a doubt whose challenger had since been
           rebutted could be eliminated by a single remaining peer. Measured
           over the eight seeds and every arm in this suite, the tightening
           moved nothing: that case never arose.
        2. Is the doubt dead, and does the record still sustain the law? A
           rebuttal — the author's own record, or a peer's published testimony
           about the disputed individual — retires the citation, and if the
           author's own criterion is met the law goes back to work.
        3. Has the window run out? THE WINDOW FIRES ONCE AND EXITS TWO WAYS,
           by what the record says at the moment it expires. Sustained: the
           challenge failed to gather support and SILENCE CANNOT ELIMINATE, so
           the law is restored — a doubt nobody shares is a doubt that has run
           out, not a verdict. Not sustained: the author's own record is against
           its own law and the community had the whole window to repair it, so
           the law is given up.
        4. Otherwise the inquiry continues, and if the record does not sustain
           the law a further question goes out (`_inquire`).

        THE CRITERION IS RE-READ EVERY PASS AND REMEMBERED FROM NONE. A record
        grows: facts arrive at the membrane, answers are adopted, and a law that
        failed its own criterion when the doubt opened may meet it four rounds
        later. Reading the criterion at the moment the window expires rather than
        recording a verdict when the doubt opened is what makes the inquiry
        capable of changing the outcome — which is the whole point of ordering
        inquiry before elimination.

        A challenge disposed of here is spent (`_spent`): it has had its answer,
        and the same inscription does not get to raise the same doubt again.
        """
        doubt = self._doubts[law]
        live = [m for m in standing
                if not self._rebutted(m, board, round_idx, testimony=True)]
        self._spent.update(m for m in standing if m not in live)
        # THE WITNESSES ARE DISTINCT FOREIGN AUTHORS, NOT LIVE INSCRIPTIONS. A
        # set of authors is what makes "repeating one's own observation does not
        # do this" true of the code as well as of the ruling: two marks from one
        # unit collapse to one voice here, whatever minted them.
        witnesses = {m.author for m in live} - {self.unit_id}
        if doubt.challenger is None and witnesses:
            # A self-raised doubt acquires its challenger from the first peer to
            # dispute the law. That peer bears the doubt out; it does not
            # corroborate it, because there is as yet nothing but the author's
            # own record for it to corroborate.
            doubt.challenger = sorted(witnesses)[0]
        if len(witnesses) >= self.corroborating_witnesses:
            self._spent.update(live)
            if self.retract_law(law):
                out.retracted_by_corroboration.append(law)
            return
        sustains = self._meets_criterion(law, round_idx)
        if sustains and not live:
            self._unsuspend(law)
            out.restored_by_rebuttal.append(law)
            return
        if round_idx - doubt.opened_at >= self.corroboration_window:
            self._spent.update(live)
            if sustains:
                self._unsuspend(law)
                out.restored_by_silence.append(law)
            elif self.retract_law(law):
                out.retracted_internally.append(law)
            return
        if not sustains:
            self._inquire(law, board, round_idx, out)

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
