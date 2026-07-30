# tests/test_c_channels.py
"""The ask channel and the challenge channel.

The ask channel: a question published, and answered from a peer's holdings. Its
unit tests come first; the two measurement gates in the middle are the real
question — does a pair that asks and answers end up better off than the same
pair mute, at equal run length?

The challenge channel: a published law disputed by a counterexample, and
disposed of by its author against its own record. Its measurement gates are at
the bottom, and they report a NEGATIVE result, deliberately unsmoothed.
"""

import pytest

from c_field import Field, apertures_for, default_spec
from c_marks import Mark, MarkBoard
from c_unit import Unit

A1 = (("c", "a1"),)
A2 = (("c", "a2"),)


def _two_units():
    spec = default_spec(seed=20260728)
    aps = apertures_for(spec, n_units=4)
    return spec, Field(spec), Unit("u0", aps[0]), Unit("u1", aps[1])


def _units(n=4, seed=20260728):
    spec = default_spec(seed=seed)
    aps = apertures_for(spec, n_units=4)
    return [Unit(f"u{i}", aps[i]) for i in range(n)]


# --- asking -------------------------------------------------------------------


def test_a_unit_asks_about_a_relation_it_has_no_instance_of():
    _spec, _field, u0, _u1 = _two_units()
    board = MarkBoard()
    u0.facts.add(("p1", (("c", "a1"),)))
    u0.laws.add(("p1", "q1"))       # q1 licensed but never observed
    q = u0.ask(board, 0)
    assert q is not None and q.kind == "question"


def test_a_question_names_the_atom_that_would_answer_it():
    """A question inscribes the very content a fact would, so an answer meets it
    without any matching apparatus — which is what lets `answer` work off content
    alone, and what makes an unprompted fact able to close a question."""
    _spec, _field, u0, _u1 = _two_units()
    board = MarkBoard()
    u0.facts.add(("p1", A1))
    u0.laws.add(("p1", "q1"))
    q = u0.ask(board, 0)
    assert q.content == ("q1", A1)
    assert q.author == "u0" and q.round_idx == 0
    assert board.open_questions() == [q]


def test_a_unit_with_no_licence_and_nothing_wanting_asks_nothing():
    """Two ways to want nothing: hold no law at all, or hold a law every one of
    whose licences is already instantiated."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0.facts.add(("p1", A1))                        # no law: no licence
    assert u0.ask(board, 0) is None

    u1.facts.update({("p1", A1), ("q1", A1)})       # licence already met
    u1.laws.add(("p1", "q1"))
    assert u1.ask(board, 0) is None
    assert board.all_marks() == []


def test_at_most_one_question_goes_out_per_round():
    """Attention is bounded: a channel that emptied the whole want-list every
    round would be a broadcast, not an act."""
    _spec, _field, u0, _u1 = _two_units()
    board = MarkBoard()
    u0._record({("p1", A1), ("p1", A2), ("p1", (("c", "a3"),))}, 0)
    u0.laws.add(("p1", "q1"))
    assert u0.ask(board, 0) is not None
    assert len(board.all_marks()) == 1
    assert u0.ask(board, 1) is not None
    assert len(board.all_marks()) == 2


def test_a_question_is_asked_once_ever_even_while_it_stands_unanswered():
    """The same discipline `publish` keeps: a re-mention that refreshes nothing
    would still be counted by the instruments, and whether re-asking refreshes a
    question's standing is unruled."""
    _spec, _field, u0, _u1 = _two_units()
    board = MarkBoard()
    u0._record({("p1", A1)}, 0)
    u0.laws.add(("p1", "q1"))
    first = u0.ask(board, 0)
    assert first is not None
    for r in range(1, 5):
        assert u0.ask(board, r) is None
    assert board.all_marks() == [first]
    assert board.republished == 0        # not even offered again


def test_the_freshest_live_want_is_the_one_asked_about():
    """MOST-WANTED IS URGENCY, NOT AGE. A want born from the latest arrival is
    staked at the very next attended round, so an answer is only in time if it
    comes now."""
    _spec, _field, u0, _u1 = _two_units()
    board = MarkBoard()
    u0._record({("p1", A1)}, 0)
    u0._record({("p1", A2)}, 5)
    u0.laws.add(("p1", "q1"))
    assert u0.ask(board, 6).content == ("q1", A2)
    assert u0.ask(board, 7).content == ("q1", A1)


def test_a_want_the_record_has_already_resolved_is_asked_about_last():
    """A forecast resolves exactly once, at the round it is due, so an answer
    arriving afterwards cannot change the verdict. Such an atom is still worth
    knowing — it is not dropped — but it loses to every live want."""
    _spec, _field, u0, _u1 = _two_units()
    board = MarkBoard()
    u0._record({("p1", A1)}, 0)
    u0._record({("p1", A2)}, 5)
    u0.laws.add(("p1", "q1"))
    u0.ledger.resolved.add(("q1", A2))          # the fresher want, already settled
    assert u0.ask(board, 6).content == ("q1", A1)
    assert u0.ask(board, 7).content == ("q1", A2)


def test_a_body_with_no_first_arrival_is_asked_about_last():
    """An adopted fact carries no date (the ruling of the assert channel), so the
    unit has no evidence of how long that want has been waiting. Treating it as
    urgent would let a peer's publication schedule set this unit's priorities."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u1.facts.add(("p1", A2))
    hearsay, = u1.publish(board, 0)
    u0._record({("p1", A1)}, 0)
    u0.laws.add(("p1", "q1"))
    u0.adopt(hearsay, board)                    # held, undated
    assert u0.ask(board, 1).content == ("q1", A1)
    assert u0.ask(board, 2).content == ("q1", A2)


def test_the_ask_order_is_deterministic():
    def sequence():
        _spec, _field, u0, _u1 = _two_units()
        board = MarkBoard()
        u0._record({("p1", A1), ("p1", A2), ("p2", A1)}, 3)
        u0.laws.update({("p1", "q1"), ("p2", "q2")})
        return [m.content for m in (u0.ask(board, r) for r in range(4))
                if m is not None]
    assert sequence() == sequence()


# --- answering ----------------------------------------------------------------


def test_another_unit_answers_from_its_own_holdings():
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0.facts.add(("p1", (("c", "a1"),)))
    u0.laws.add(("p1", "q1"))
    u0.ask(board, 0)
    u1.facts.add(("q1", (("c", "a1"),)))
    answers = u1.answer(board, 1)
    assert answers, "u1 holds the answer and should have offered it"
    assert all(m.author == "u1" for m in answers)


def test_an_answer_is_an_ordinary_fact_mark():
    """Nothing on the board records that a mark answered anything: what is
    published in reply is indistinguishable from the same content published
    unprompted, and the answering relation is recoverable from content."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0.facts.add(("p1", A1))
    u0.laws.add(("p1", "q1"))
    q = u0.ask(board, 0)
    u1.facts.add(("q1", A1))
    answer, = u1.answer(board, 1)
    assert (answer.kind, answer.content, answer.round_idx) == ("fact", q.content, 1)


def test_a_unit_answers_only_what_it_actually_holds():
    """An answer is drawn from `self.facts` and nowhere else — a unit can tell
    only what it has met. The field is not consulted."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0.facts.update({("p1", A1), ("p1", A2)})
    u0.laws.add(("p1", "q1"))
    u0.ask(board, 0)
    u0.ask(board, 1)                                # both wants now standing
    u1.facts.add(("q1", A1))                        # holds one of the two
    answered = u1.answer(board, 2)
    assert [m.content for m in answered] == [("q1", A1)]


def test_a_unit_never_answers_its_own_question():
    """Answering oneself would put the asker's own want on the board as a claim
    it never met — and since a question is closed by content, it would close the
    question against every peer who could really have answered it."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0.facts.add(("p1", A1))
    u0.laws.add(("p1", "q1"))
    u0.ask(board, 0)
    u0.facts.add(("q1", A1))                        # it now holds its own answer
    assert u0.answer(board, 1) == []
    assert board.open_questions()                   # still open for u1
    u1.facts.add(("q1", A1))
    assert [m.author for m in u1.answer(board, 2)] == ["u1"]


def test_an_old_question_is_answered_when_the_answer_is_finally_met():
    """A question stands until answered, so the scan is over ALL open questions
    rather than a round window — a peer that meets the answer forty rounds later
    can still supply it."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0.facts.add(("p1", A1))
    u0.laws.add(("p1", "q1"))
    u0.ask(board, 0)
    assert u1.answer(board, 1) == []                # nothing to say yet
    u1._record({("q1", A1)}, 40)
    assert [m.content for m in u1.answer(board, 41)] == [("q1", A1)]


def test_a_question_is_closed_by_any_fact_mark_with_its_content():
    """Openness is a property of the board, and a question is closed by a
    published answer — including a fact published for its own sake."""
    u0, u1, u2, _u3 = _units()
    board = MarkBoard()
    u0.facts.add(("p1", A1))
    u0.laws.add(("p1", "q1"))
    q = u0.ask(board, 0)
    assert board.open_questions() == [q]

    u1.facts.add(("q1", A1))
    u1.publish(board, 1)                            # said for its own sake
    assert board.open_questions() == []
    u2.facts.add(("q1", A1))
    assert u2.answer(board, 2) == []                # nothing left to answer
    assert board.answer_to(q).author == "u1"


def test_two_peers_do_not_both_answer_one_question():
    u0, u1, u2, _u3 = _units()
    board = MarkBoard()
    u0.facts.add(("p1", A1))
    u0.laws.add(("p1", "q1"))
    u0.ask(board, 0)
    u1.facts.add(("q1", A1))
    u2.facts.add(("q1", A1))
    assert len(u1.answer(board, 1)) == 1
    assert u2.answer(board, 1) == []


# --- a question is not a claim ------------------------------------------------


def test_a_question_mark_must_be_atom_shaped():
    """A question names the atom that would answer it, so a law-shaped pair is
    refused where it is minted rather than where it is read."""
    with pytest.raises(ValueError, match="question"):
        Mark(author="u0", content=("p1", "q1"), kind="question", round_idx=0)


def test_a_question_cannot_be_adopted():
    """It names an atom without claiming it. Taking one up would put an
    unasserted atom into a record, and the unit would then bet on someone else's
    doubt."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0.facts.add(("p1", A1))
    u0.laws.add(("p1", "q1"))
    q = u0.ask(board, 0)
    with pytest.raises(ValueError, match="question"):
        u1.adopt(q, board)
    assert u1.facts == set()


def test_a_question_alone_changes_nothing_a_peer_anticipates():
    """Publishing a doubt is not publishing a claim: a peer that reads the board
    and takes up everything a question offers takes up nothing."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0.facts.add(("p1", A1))
    u0.laws.add(("p1", "q1"))
    u0.ask(board, 0)
    read = u1.read(board, 0)
    assert [m.kind for m in read] == ["question"]
    assert u1.anticipate() == set()


def test_answering_creates_attributable_uptake_when_the_asker_takes_it_up():
    """The whole point of the channel, read off the attribution graph: a
    question produced a reliance edge that would not otherwise exist."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0._record({("p1", A1)}, 0)
    u0.laws.add(("p1", "q1"))
    q = u0.ask(board, 0)
    u1._record({("q1", A1)}, 1)
    answer, = u1.answer(board, 1)
    assert board.uptake_of(answer) == set()
    assert u0.adopt(answer, board) is True
    assert board.uptake_of(answer) == {"u0"}
    assert ("q1", A1) in u0.facts
    assert u0.first_seen == {("p1", A1): 0}         # the answer is NOT dated


# --- the measurement: does asking and answering beat being mute? -------------
#
# THE DRIVER IS EXPLICIT ON PURPOSE. Task 3 measured the assert channel with
# INDISCRIMINATE uptake and found it strictly harmful at every seed — a unit that
# adopts facts about regions outside its own aperture starts betting on them and
# loses. So the filter by which anything is taken up here is written out in full
# rather than hidden in a helper: a unit adopts a fact mark ONLY when it answers
# a question that unit itself asked. That is targeting by construction — the atom
# asked about is licensed by the asker's own law over an individual its own record
# already carries.
#
# PHASE ORDER, AND WHY. Each round runs (a) adopt, (b) attend the field, (c) ask,
# (d) answer, with ALL units doing each phase together so none gets a
# within-round lookahead over another. Adopting BEFORE attending is what gives an
# answer a chance to matter at all: a stake is placed inside `step`, before the
# round's arrivals are seen, so testimony that arrives afterwards is too late to
# do anything but be counted as a late arrival. `step` itself is untouched.

ROUNDS = 60
SEEDS = [1, 2, 3, 4, 5, 7, 42, 99, 555, 808, 2026, 12345, 20260728, 31337]


def _play(seed, rounds, *, channel, stagger):
    """Two units sharing one domain, each holding that domain's planted law.

    `stagger=2` means u0 attends the field on even rounds and u1 on odd ones —
    BOUNDED ATTENTION, and the first division of labour: each unit is the only
    one of the pair that met what arrived on its rounds. `stagger=1` is the
    control in which both attend every round.

    The law is SEEDED rather than induced, deliberately. A staggered unit cannot
    induce it: it sees bodies whose heads are delivered on the rounds it sleeps
    through, which leaves those individuals permanently pending and the pending
    rate refuses the law. Seeding it is the same device
    `tests/test_c_stage_gates.py` uses to test a law's worth in isolation.
    """
    spec = default_spec(seed=seed)
    field = Field(spec)
    aps = apertures_for(spec, n_units=4)
    shared = spec.domains[1]                    # beta: in u0's aperture and u1's
    units = [Unit("u0", aps[0], laws={shared.law}),
             Unit("u1", aps[1], laws={shared.law})]
    board = MarkBoard()
    asked = {u.unit_id: [] for u in units}
    settled = {u.unit_id: set() for u in units}
    answers = 0
    uptakes = 0

    for r in range(rounds):
        if channel:                                             # (a) adopt
            for u in units:
                for q in asked[u.unit_id]:
                    if q.content in settled[u.unit_id]:
                        continue
                    reply = board.answer_to(q)
                    if reply is None or reply.author == u.unit_id:
                        continue
                    settled[u.unit_id].add(q.content)
                    uptakes += u.adopt(reply, board)
        for i, u in enumerate(units):                           # (b) attend
            if stagger == 1 or r % stagger == i:
                u.step(field, r)
        if channel:
            for u in units:                                     # (c) ask
                mark = u.ask(board, r)
                if mark is not None:
                    asked[u.unit_id].append(mark)
            for u in units:                                     # (d) answer
                answers += len(u.answer(board, r))
    return units, board, answers, uptakes


def test_asking_and_answering_beats_being_mute_at_equal_run_length():
    """THE GATE THIS TASK EXISTS FOR, and the answer is yes — where the asker's
    own attention does not reach.

    Two units share domain beta and each holds beta's planted law, but each
    attends the field on only half the rounds. That is a real predicament, not a
    contrivance: a body absorbed on an even round has its consequent delivered on
    the odd round that follows, so the unit that saw the body is not looking when
    the head arrives, and its stake on that head is a certain loss. Mute, the
    pair bleeds. The peer, however, WAS looking — and a question names exactly
    the atom it saw.

    MEASURED at 60 rounds, over the fourteen seeds this suite uses, live pair net
    against mute pair net:

        seed        live    mute        seed        live    mute
        1            −1     −27        555          −3     −31
        2            −2     −32        808          −2     −32
        3            −4     −28        2026         −4     −31
        4            −1     −28        12345        −5     −31
        5            +0     −29        20260728     −2     −26
        7            −2     −33        31337        +0     −25
        42           −5     −28
        99           −2     −31

    Live wins at 14 of 14 seeds and at all 28 individual arms; pair totals −33
    against −412, so the channel recovers 92% of what bounded attention costs.
    About 31 questions go out per run and about 29 are answered and taken up.

    WHAT IT DOES NOT DO IS TURN A PROFIT, and the reason is worth stating
    plainly. An answer NEVER WINS A BET; it only prevents one. Adopting the atom
    before the stake is placed means no stake is placed, so the arithmetic can
    only improve by removing losing bets — and it does: hits fall from 11 to 2
    across the fourteen seeds while misses fall from 423 to 35. The live arm is
    therefore still slightly negative (a pair net of about −2), where total
    abstention would be 0 and where the same pair with FULL attention makes +48.
    Communication here repairs a deficit of attention; it does not substitute for
    attention.
    """
    live_pairs, mute_pairs = [], []
    live_hits = mute_hits = 0
    for seed in SEEDS:
        live, board, answers, uptakes = _play(seed, ROUNDS, channel=True,
                                              stagger=2)
        mute, *_ = _play(seed, ROUNDS, channel=False, stagger=2)
        assert answers > 0 and uptakes > 0, (
            f"seed {seed}: the channel carried nothing, so nothing was tested")
        # Per-arm, so a single losing seed fails the gate and names itself.
        for asking, silent in zip(live, mute):
            assert asking.ledger.net_score > silent.ledger.net_score, (
                f"seed {seed} {asking.unit_id}: asking "
                f"({asking.ledger.net_score:+d}) did not beat mute "
                f"({silent.ledger.net_score:+d})")
        live_pairs.append(sum(u.ledger.net_score for u in live))
        mute_pairs.append(sum(u.ledger.net_score for u in mute))
        live_hits += sum(u.ledger.hits for u in live)
        mute_hits += sum(u.ledger.hits for u in mute)
    assert sum(live_pairs) > sum(mute_pairs)
    # AN ANSWER PREVENTS A BET, IT DOES NOT WIN ONE: the live arm takes FEWER
    # hits than the mute arm and improves anyway, by shedding losing stakes.
    assert live_hits <= mute_hits


def test_with_full_attention_the_ask_channel_is_inert_rather_than_harmful():
    """THE CONTROL, and the structural reason the gate above reads as it does.

    When both units attend every round they hold identical beta facts — the field
    is a pure function of (seed, domain, round), so a shared domain delivers the
    same atoms to both — and neither can ever tell the other anything about beta.
    Questions still go out (46–56 per 40-round run) and peers do answer them
    (21–27 answers), but EVERY ANSWER IS REDUNDANT: it arrives a round after the
    asker met the atom itself. So the uptake count is zero at every seed — the
    attribution graph records reliance only where something was actually taken
    up — and the two arms finish IDENTICAL, hit for hit and miss for miss.

    That is the contrast with the assert channel. Indiscriminate uptake was
    strictly harmful — every seed's positive arm went negative, because adopting
    a fact about a domain you cannot observe licenses an anticipation that can
    never arrive. A question cannot do that: it is licensed by the asker's own
    law over an individual its own record carries, so an irrelevant answer is not
    something it is possible to receive. Where the channel has nothing to add it
    adds nothing.

    IT ALSO LOCATES EXACTLY WHERE COMMUNICATION PAYS. A stake on `head(a)` is
    placed at the asker's next attended round; a peer can only publish `head(a)`
    after observing it, which under full attention is the very round the asker
    observes it too — too late to pre-empt a bet the asker was going to win. So
    an answer can only ever remove a stake the asker could NOT have won, which is
    why targeting works here and why it works only across a difference in
    attention, never across a difference in aperture.
    """
    for seed in SEEDS[:8]:
        live, board, answers, uptakes = _play(seed, 40, channel=True, stagger=1)
        mute, *_ = _play(seed, 40, channel=False, stagger=1)
        assert [m for m in board.all_marks() if m.kind == "question"]
        assert answers > 0, f"seed {seed}: the peers never even spoke"
        assert uptakes == 0, (
            f"seed {seed}: a shared domain delivers identically to both units, "
            f"so every answer arrives after the asker met the atom itself and "
            f"nothing can be taken up — got {uptakes} uptake edges")
        for asking, silent in zip(live, mute):
            assert (asking.ledger.hits, asking.ledger.misses) == (
                silent.ledger.hits, silent.ledger.misses), (
                f"seed {seed} {asking.unit_id}: the channel moved the record "
                f"without carrying anything")
            assert asking.ledger.net_score > 0     # full attention makes money


def test_the_channel_leaves_anticipate_before_observe_alone():
    """Asking and answering are separate acts from `step`, which is untouched:
    the bet is still placed before the round's arrivals are seen, and every dated
    fact is still first-hand."""
    live, _board, answers, uptakes = _play(20260728, 20, channel=True, stagger=2)
    assert answers > 0 and uptakes > 0
    for u in live:
        assert u.ledger.entries
        assert u.ledger.restaked == 0
        assert set(u.first_seen) <= u.facts
        adopted = u.facts - set(u.first_seen)
        assert adopted, "nothing was taken up, so the ruling is not exercised"
        for fact in adopted:
            assert fact not in u.first_seen        # an answer carries no date


def test_the_channel_is_deterministic():
    def run():
        units, board, answers, uptakes = _play(3, 30, channel=True, stagger=2)
        return ([(u.ledger.hits, u.ledger.misses) for u in units],
                [(m.author, m.kind, m.content) for m in board.all_marks()],
                answers, uptakes)
    assert run() == run()


# =============================================================================
# THE CHALLENGE CHANNEL
# =============================================================================
#
# A law can now be DEFEATED, not merely outlived. Everything the project
# measures about durability rested on that being possible: until now `induce`
# only ever added, so a law's only exit was a decay clock and K2 could never
# read false for a reason.
#
# THE DISPOSITION RULE, ONCE. A unit challenges a published LAW mark when its
# own facts hold a counterexample — an individual carrying the law's body
# without its head — and the challenge carries that individual. The law's
# author, reading a challenge against a law it still holds, VERIFIES the
# counterexample against its own facts and retracts only if it cannot rebut it.
# Holding that same individual WITH the head rebuts the challenge and the law
# stands. The calculus decides, not the challenger's authority.


# --- challenging ---------------------------------------------------------------


def test_a_counterexample_holder_challenges_a_published_law():
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z9"),)))       # body without head — a counterexample
    challenges = u1.challenge(board, 1)
    assert challenges and challenges[0].kind == "challenge"


def test_an_unrebutted_challenge_retracts_the_law_from_its_author():
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z9"),)))
    u1.challenge(board, 1)
    retracted = u0.dispose_challenges(board, 2)
    assert ("p1", "q1") in retracted
    assert ("p1", "q1") not in u0.laws


def test_a_rebuttable_challenge_leaves_the_law_standing():
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0.laws.add(("p1", "q1"))
    u0.facts.update({("p1", (("c", "z9"),)), ("q1", (("c", "z9"),))})   # author holds the head
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z9"),)))
    u1.challenge(board, 1)
    retracted = u0.dispose_challenges(board, 2)
    assert ("p1", "q1") not in retracted
    assert ("p1", "q1") in u0.laws


def test_the_challenge_names_the_law_and_carries_the_counterexample():
    """Content is the LAW — so the mark meets the claim rather than its author —
    and the evidence rides in `counterexample`, because the content is what the
    mark is about and the counterexample is what it offers."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", A2))
    mark, = u1.challenge(board, 1)
    assert (mark.author, mark.kind, mark.round_idx) == ("u1", "challenge", 1)
    assert mark.content == ("p1", "q1")
    assert mark.counterexample == ("p1", A2)


def test_nothing_is_challenged_when_the_challenger_holds_no_counterexample():
    """A unit that holds the body WITH the head has nothing to say against the
    law, and a unit that holds no instance of the body has nothing to say at
    all."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    assert u1.challenge(board, 1) == []              # holds nothing
    u1.facts.update({("p1", A1), ("q1", A1)})
    assert u1.challenge(board, 1) == []              # holds the law's instance
    assert [m.kind for m in board.all_marks()] == ["law"]


def test_a_law_is_challenged_once_ever():
    """A second challenge carrying a second counterexample would be a second
    inscription making one point — counted twice by the instruments, and turning
    disposition into a volume contest, which is the thing the rule most needs not
    to be."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.update({("p1", A1), ("p1", A2)})        # two counterexamples
    assert len(u1.challenge(board, 1)) == 1
    assert u1.challenge(board, 2) == []
    assert len([m for m in board.all_marks() if m.kind == "challenge"]) == 1
    assert board.republished == 0                    # not even offered again


def test_a_unit_does_not_challenge_its_own_inscription():
    """`read` excludes own marks for the same reason: what a unit encounters is
    somebody else's."""
    _spec, _field, u0, _u1 = _two_units()
    board = MarkBoard()
    u0.laws.add(("p1", "q1"))
    u0.facts.add(("p1", A1))                         # its own counterexample
    u0.publish(board, 0)
    assert u0.challenge(board, 1) == []


def test_a_challenge_meets_every_author_of_the_law():
    """Addressed to a claim, not to a person. Two units that independently
    published `p1 -> q1` published ONE claim twice, and evidence against it is
    evidence against both — the same content-matching that lets any published
    fact close a question."""
    u0, u1, u2, _u3 = _units()
    board = MarkBoard()
    u0.laws.add(("p1", "q1"))
    u1.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.publish(board, 0)                             # the identical claim
    u2.facts.add(("p1", A1))
    assert len(u2.challenge(board, 1)) == 1          # one challenge, not two
    assert u0.dispose_challenges(board, 2) == [("p1", "q1")]
    assert u1.dispose_challenges(board, 2) == [("p1", "q1")]


def test_the_challenge_order_is_deterministic():
    def sequence():
        _spec, _field, u0, u1 = _two_units()
        board = MarkBoard()
        u0.laws.update({("p1", "q1"), ("p2", "q2"), ("p3", "q3")})
        u0.publish(board, 0)
        u1.facts.update({("p1", A1), ("p2", A2), ("p3", A1)})
        return [(m.content, m.counterexample) for m in u1.challenge(board, 1)]
    assert sequence() == sequence()


# --- disposing: the calculus decides ------------------------------------------


def test_a_challenge_to_a_law_the_unit_does_not_hold_disposes_of_nothing():
    """Nothing is retracted that was never held — `retract_law`'s honest return
    value, carried up."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", A1))
    u1.challenge(board, 1)
    assert u1.dispose_challenges(board, 2) == []      # u1 never held it
    other = Unit("u2", u1.aperture)
    assert other.dispose_challenges(board, 2) == []


def test_disposal_is_idempotent():
    """A law given up is not given up twice, and the second pass reports
    nothing — a caller reading the return value learns what actually changed."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", A1))
    u1.challenge(board, 1)
    assert u0.dispose_challenges(board, 2) == [("p1", "q1")]
    assert u0.dispose_challenges(board, 3) == []


def test_a_disposal_does_not_answer_for_a_challenge_made_later():
    """A disposal at round r answers for challenges published at r or earlier.
    The board is a place and keeps no clock, so the bound comes from the
    caller."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", A1))
    u1.challenge(board, 5)
    assert u0.dispose_challenges(board, 4) == []
    assert ("p1", "q1") in u0.laws
    assert u0.dispose_challenges(board, 5) == [("p1", "q1")]


def test_volume_of_challenges_does_not_decide_a_law():
    """THE POINT OF THE CHANNEL. Three peers challenge one law and every one of
    their counterexamples is rebutted by the author's own record: the law
    stands. A rule that counted challenges would have retracted it three times
    over — and the challengers are not wrong about their own records, they are
    simply not the ones who decide."""
    u0, u1, u2, u3 = _units()
    board = MarkBoard()
    u0.laws.add(("p1", "q1"))
    for args in (A1, A2, (("c", "a3"),)):
        u0.facts.update({("p1", args), ("q1", args)})   # the author holds each head
    u0.publish(board, 0)
    for peer, args in ((u1, A1), (u2, A2), (u3, (("c", "a3"),))):
        peer.facts.add(("p1", args))
        assert peer.challenge(board, 1)
    assert len(board.challenges_against(("p1", "q1"))) == 3
    assert u0.dispose_challenges(board, 2) == []
    assert ("p1", "q1") in u0.laws


def test_one_unrebutted_challenge_among_many_rebutted_ones_still_defeats_the_law():
    """Verification is per-counterexample, not a vote: the law falls to the one
    citation the author cannot answer, whatever the others say."""
    u0, u1, u2, _u3 = _units()
    board = MarkBoard()
    u0.laws.add(("p1", "q1"))
    u0.facts.update({("p1", A1), ("q1", A1)})           # rebuts a citation of a1
    u0.facts.add(("p1", A2))                            # but not one of a2
    u0.publish(board, 0)
    u1.facts.add(("p1", A1))
    u1.challenge(board, 1)
    u2.facts.add(("p1", A2))
    u2.challenge(board, 1)
    assert u0.dispose_challenges(board, 2) == [("p1", "q1")]


def test_the_author_verifies_against_its_own_record_not_the_challengers():
    """The two records disagree, and the author's is the one that decides its own
    law. The challenger is not lying — it really does lack the head — and it
    still does not get to retract someone else's law."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0.laws.add(("p1", "q1"))
    u0.facts.update({("p1", A1), ("q1", A1)})
    u0.publish(board, 0)
    u1.facts.add(("p1", A1))                            # no q1(a1) in ITS record
    challenge, = u1.challenge(board, 1)
    assert challenge.counterexample == ("p1", A1)
    assert u0.dispose_challenges(board, 2) == []
    assert ("p1", "q1") in u0.laws


# --- a challenge is not a claim ------------------------------------------------


def test_a_challenge_mark_must_be_law_shaped_and_carry_checkable_evidence():
    with pytest.raises(ValueError, match="challenge"):        # fact-shaped content
        Mark(author="u0", content=("p1", A1), kind="challenge", round_idx=0,
             counterexample=("p1", A1))
    with pytest.raises(ValueError, match="no counterexample"):
        Mark(author="u0", content=("p1", "q1"), kind="challenge", round_idx=0)
    with pytest.raises(ValueError, match="not the law's body"):
        Mark(author="u0", content=("p1", "q1"), kind="challenge", round_idx=0,
             counterexample=("p2", A1))
    with pytest.raises(ValueError, match="not an atom"):
        Mark(author="u0", content=("p1", "q1"), kind="challenge", round_idx=0,
             counterexample=("p1", "q1"))


def test_only_a_challenge_carries_a_counterexample():
    """An assertion or a question that carried one would be offering evidence
    against a law it never named."""
    for kind, content in (("fact", ("p1", A1)), ("law", ("p1", "q1")),
                          ("question", ("p1", A1))):
        with pytest.raises(ValueError, match="only a challenge"):
            Mark(author="u0", content=content, kind=kind, round_idx=0,
                 counterexample=("p1", A1))


def test_a_challenge_cannot_be_adopted():
    """Taking it up would enter the very law it argues against."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", A1))
    challenge, = u1.challenge(board, 1)
    with pytest.raises(ValueError, match="challenge"):
        u0.adopt(challenge, board)
    assert ("p1", "q1") in u0.laws                  # and nothing was taken up
    assert u0.facts == set()


def test_a_defeated_law_still_stands_on_the_board():
    """The board is append-only: what a mark CLAIMS and what its author still
    HOLDS have come apart, and nothing here closes that gap. Left visible rather
    than pre-empted — the maintenance channel's work (spec §9b)."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0.laws.add(("p1", "q1"))
    law_mark, = u0.publish(board, 0)
    u1.facts.add(("p1", A1))
    u1.challenge(board, 1)
    u0.dispose_challenges(board, 2)
    assert ("p1", "q1") not in u0.laws
    assert law_mark in board.all_marks()


def test_induction_admits_a_law_the_challenge_rule_immediately_refutes():
    """THE STRUCTURAL FINDING, in miniature: the two criteria disagree BY
    CONSTRUCTION.

    `induce` tolerates a RATE of pending individuals (up to 5%, which is what
    lets a true law survive the field's withheld consequents). `challenge` fires
    on ANY ONE pending individual — an existential, not a rate. So the
    disposition rule is strictly stronger than the admission rule, and every law
    admitted with a nonzero pending rate is challengeable the moment it is
    published. Here the challenger's counterexample is an individual the AUTHOR'S
    OWN RECORD already had, and the author duly retracts a law its own induction
    proposed one line earlier.
    """
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    for i in range(20):                             # body first, head after —
        args = (("c", f"a{i}"),)                    # so precedence fixes the
        u0._record({("p1", args)}, i)               # direction and the converse
        u0._record({("q1", args)}, i + 1)           # is refused outright
    pending = (("c", "a99"),)
    u0._record({("p1", pending)}, 21)               # 1 of 21 = 4.8%, admitted
    assert u0.induce() == {("p1", "q1")}
    u0.publish(board, 0)
    u1.facts.add(("p1", pending))                   # the same individual
    u1.challenge(board, 1)
    assert u0.dispose_challenges(board, 2) == [("p1", "q1")]


# --- the measurement: what does defeasibility cost under noise? ---------------
#
# THE DRIVER IS EXPLICIT, as in the ask channel's measurement above. Four units
# with distinct overlapping apertures induce laws from what they meet, publish
# what they hold, challenge what their records contradict, and dispose of the
# challenges standing against them. Nothing adopts anything: Task 3 measured
# indiscriminate uptake and found it strictly harmful, and mixing it in here
# would confound the challenge channel's effect with that one.
#
# THE MODELER'S LABEL IS READ ONLY IN THIS FILE. `spec.domains[i].law` says which
# laws the field actually carries, so a retraction can be labelled a FALSE
# retraction (a true law defeated) or a CORRECT one (an accidental law defeated).
# No `Unit` reads it — a unit that knew which laws were planted would not be
# testing anything.

C_ROUNDS = 60
C_SEEDS = [1, 2, 3, 4, 5, 7, 42, 99]


def _play_challenge(seed, rounds, *, channel, stagger=1, seed_laws=False,
                    wrong_laws=False, induce=True):
    """Four units, one board. Each round: attend the field (inducing), publish
    what is held, then — if the channel is live — challenge and dispose.

    `wrong_laws` seeds each unit with the CONVERSE of its first domain's law, a
    law the field does not carry. It is what gives the channel something correct
    to do: without it the arm contains no accidental law, because `induce`
    proposes only planted ones at every seed measured.

    `stagger=2` is bounded attention — u0/u2 attend even rounds, u1/u3 odd — so
    the units' records genuinely differ and a rebuttal is possible on the merits
    rather than by their holding identical facts.
    """
    spec = default_spec(seed=seed)
    field = Field(spec)
    aps = apertures_for(spec, n_units=4)
    planted = {d.name: d.law for d in spec.domains}
    units = []
    for i in range(4):
        laws = {planted[n] for n in aps[i].domains} if seed_laws else set()
        if wrong_laws:
            body, head = planted[aps[i].domains[0]]
            laws = laws | {(head, body)}            # the converse: never carried
        units.append(Unit(f"u{i}", aps[i], laws=laws))
    board = MarkBoard()
    raised = 0
    retractions = []                                # (unit_id, law), with repeats
    for r in range(rounds):
        for i, u in enumerate(units):               # (a) attend + induce
            if stagger == 1 or r % stagger == i % stagger:
                u.step(field, r, induce=induce)
        for u in units:                             # (b) publish what is held
            u.publish(board, r)
        if channel:
            for u in units:                         # (c) challenge
                raised += len(u.challenge(board, r))
            for u in units:                         # (d) dispose
                for law in u.dispose_challenges(board, r):
                    retractions.append((u.unit_id, law))
    return spec, units, board, raised, retractions


def test_every_successful_challenge_defeats_a_law_the_field_actually_carries():
    """THE HEADLINE, AND IT IS NEGATIVE. Reported, not tuned away.

    Eight seeds, 60 rounds, four units inducing from what they meet. Across the
    eight seeds: **58 challenges raised, 58 succeeded (100%), and all 58 defeated
    a law the field actually carries.** ZERO correct retractions — not because
    the rule missed them, but because there were none to make: `induce` proposes
    only planted laws at every seed measured (pinned in `test_c_unit.py`), so
    every law on the board is true and every success is a false retraction. Over
    the full fourteen seeds the suite uses, the same reading: 98 raised, 98
    succeeded, 98 false, 0 correct.

    WHY A TRUE LAW IS REFUTABLE AT ALL is the field's noise, working exactly as
    Task 1 intended: about a tenth of licensed consequents are withheld, so an
    individual can carry a body whose head never arrives, and a peer holding that
    individual has a perfectly honest counterexample. The author cannot
    distinguish it from a genuine refutation — its own record simply lacks the
    head — so it retracts. **That is what fallibility costs, and it is the whole
    finding: under noise, an existential counterexample rule cannot tell a
    withheld consequent from a false law.**

    THE PRICE IN SCORE, at equal run length (60 rounds both arms):

        seed    live    mute    |   seed    live    mute
        1        +24     +26    |   5        +98    +112
        2        +40     +54    |   7        +32     +80
        3        +38     +82    |   42       +56     +66
        4        +22     +60    |   99       +74    +116
        totals  +384    +596    (14 seeds: +750 against +1096)

    The channel costs **36% of the pair's net score** at eight seeds (32% at
    fourteen), and it loses at 8 of 8 seeds. Nothing here is a threshold to be
    raised: a confirmation count would buy discrimination the rule does not have,
    by making retraction a function of how many peers spoke — which is the one
    thing the disposition rule exists to refuse.

    WHAT SURVIVES IS THE OSCILLATION. Only 34 of the 58 defeated laws are still
    absent at the end of the run: the rest are re-induced from the very record
    that holds the counterexample (`induce` tolerates a 5% pending rate,
    `challenge` tolerates none — see
    `test_induction_admits_a_law_the_challenge_rule_immediately_refutes`) and
    then retracted again. Across fourteen seeds the 98 distinct defeats are 426
    retraction EVENTS. Induction and challenge are fighting.
    """
    raised_total = succeeded = false_retractions = correct_retractions = 0
    live_total = mute_total = 0
    for seed in C_SEEDS:
        spec, live, _board, raised, retractions = _play_challenge(
            seed, C_ROUNDS, channel=True)
        _s, mute, _b, _r, _rr = _play_challenge(seed, C_ROUNDS, channel=False)
        planted = {d.law for d in spec.domains}
        defeats = set(retractions)                  # distinct (unit, law)
        assert raised > 0 and defeats, f"seed {seed}: nothing was challenged"
        false_here = sum(1 for _u, law in defeats if law in planted)
        # EVERY successful challenge defeated a law the field carries.
        assert false_here == len(defeats), (
            f"seed {seed}: {len(defeats) - false_here} correct retractions — "
            f"an accidental law reached the board, so the reading has changed")
        live_net = sum(u.ledger.net_score for u in live)
        mute_net = sum(u.ledger.net_score for u in mute)
        # Per-seed, so a single seed where challenge PAYS names itself.
        assert live_net < mute_net, (
            f"seed {seed}: the challenge channel did not cost anything "
            f"({live_net:+d} against {mute_net:+d})")
        raised_total += raised
        succeeded += len(defeats)
        false_retractions += false_here
        correct_retractions += len(defeats) - false_here
        live_total += live_net
        mute_total += mute_net
    assert (raised_total, succeeded) == (58, 58)
    assert (false_retractions, correct_retractions) == (58, 0)
    assert (live_total, mute_total) == (384, 596)


def test_the_rule_defeats_a_false_law_too_and_at_exactly_the_same_rate():
    """IT IS NOT BROKEN — IT IS INDISCRIMINATE, which is worse and more
    interesting.

    Same eight seeds and rounds, but each unit is additionally seeded with the
    CONVERSE of its first domain's law — a law the field does not carry, so
    defeating it is a correct retraction. Measured: **90 challenges raised, 90
    succeeded, 58 false and 32 correct.** Every one of the 32 wrong laws dies
    (32 of 32) and every one of the 58 true laws is defeated at least once (58 of
    58). Under full attention the rule retracts *whatever anyone has a
    counterexample to*, and truth makes no difference to its rate.

    THE ARITHMETIC OF THE TRADE, and it is not close. The mute arm's net falls
    from +596 to +519 when the converse laws are seeded, so holding those four
    wrong laws costs **77**; the live arm's net is **+384 in both arms**,
    identical seed by seed, because the channel kills the converse before it can
    place a losing bet. So the channel's BENEFIT here is 77 and its COST — the
    58 true laws it defeats — is 596 − 384 = 212. **It buys a real good at
    roughly three times its price.**
    """
    raised_total = false_retractions = correct_retractions = 0
    live_total = mute_total = 0
    for seed in C_SEEDS:
        spec, live, _board, raised, retractions = _play_challenge(
            seed, C_ROUNDS, channel=True, wrong_laws=True)
        _s, mute, _b, _r, _rr = _play_challenge(
            seed, C_ROUNDS, channel=False, wrong_laws=True)
        planted = {d.law for d in spec.domains}
        defeats = set(retractions)
        false_here = sum(1 for _u, law in defeats if law in planted)
        correct_here = len(defeats) - false_here
        # All four seeded converses die at every seed — the rule works.
        assert correct_here == 4, (
            f"seed {seed}: {correct_here} of 4 wrong laws defeated")
        # And so do the true ones.
        assert false_here > 0, f"seed {seed}: no true law was defeated"
        assert not any(law not in planted for u in live for law in u.laws), (
            f"seed {seed}: a converse law survived the channel")
        raised_total += raised
        false_retractions += false_here
        correct_retractions += correct_here
        live_total += sum(u.ledger.net_score for u in live)
        mute_total += sum(u.ledger.net_score for u in mute)
    assert raised_total == 90
    assert (false_retractions, correct_retractions) == (58, 32)
    # The benefit is real (the mute arm pays 596 - 519 = 77 for its wrong laws)
    # and the cost is about three times it (596 - 384 = 212).
    assert (live_total, mute_total) == (384, 519)


def test_under_bounded_attention_the_rule_defeats_the_true_law_and_spares_the_false_one():
    """THE INVERSION, and the sharpest thing measured here.

    Bounded attention (each unit attends half the rounds), both the planted laws
    and the converses seeded, no induction — so the same twelve laws per seed are
    held in both arms and the only variable is the channel. Measured over eight
    seeds: **64 of 64 true laws defeated (100%), 2 of 32 false laws defeated
    (6%)** — thirty of the thirty-two converse laws SURVIVE while every true law
    dies. Over fourteen seeds: 112 of 112 true, 7 of 56 false.

    WHY, AND IT IS NOT LUCK. Rebuttal asks whether the author holds the cited
    individual WITH the law's head. A converse's head is an ANTECEDENT relation
    (`a_head -> a_local`), delivered fresh every round, so the author almost
    always holds it and rebuts. A true law's head is a CONSEQUENT, withheld a
    tenth of the time and missed on every round the unit sleeps through, so the
    author often does not. **Rebuttability tracks how common the head relation is
    in the author's record — not whether the law is true.** The rule is not
    merely undiscriminating here; it is ANTI-discriminating.

    AND THE NET SCORE IMPROVES ANYWAY: −433 live against −1421 mute over the
    eight seeds (−696 against −2476 over fourteen). That is the trap this test
    exists to spring. Under bounded attention a true law cannot pay — its
    consequents arrive on rounds nobody is watching — so destroying it removes
    losing bets and the arm moves toward abstention. **A net-score improvement is
    not evidence that a channel discriminates.** Read it beside the counts above,
    never instead of them.
    """
    true_defeats = false_defeats = 0
    true_held = false_held = 0
    live_total = mute_total = 0
    for seed in C_SEEDS:
        spec, live, _board, raised, retractions = _play_challenge(
            seed, C_ROUNDS, channel=True, stagger=2, seed_laws=True,
            wrong_laws=True, induce=False)
        _s, mute, _b, _r, _rr = _play_challenge(
            seed, C_ROUNDS, channel=False, stagger=2, seed_laws=True,
            wrong_laws=True, induce=False)
        planted = {d.law for d in spec.domains}
        defeats = set(retractions)
        assert raised > 0
        true_defeats += sum(1 for _u, law in defeats if law in planted)
        false_defeats += sum(1 for _u, law in defeats if law not in planted)
        true_held += sum(1 for u in live for law in u.laws if law in planted)
        false_held += sum(1 for u in live for law in u.laws
                          if law not in planted)
        # Every unit loses every true law it was given, at every seed.
        assert not any(law in planted for u in live for law in u.laws), (
            f"seed {seed}: a true law survived bounded attention")
        live_total += sum(u.ledger.net_score for u in live)
        mute_total += sum(u.ledger.net_score for u in mute)
    assert (true_defeats, true_held) == (64, 0)      # 64 of 64 true laws gone
    assert (false_defeats, false_held) == (2, 30)    # 30 of 32 wrong laws stand
    # The score IMPROVES while the discrimination inverts — the whole warning.
    assert live_total > mute_total
    assert (live_total, mute_total) == (-433, -1421)


def test_the_challenge_channel_leaves_anticipate_before_observe_alone():
    """Challenging and disposing are separate acts from `step`, which is
    untouched: the bet is still placed before the round's arrivals are seen, no
    forecast is charged twice, and every dated fact is still first-hand."""
    _spec, units, board, raised, retractions = _play_challenge(
        3, 30, channel=True)
    assert raised > 0 and retractions
    assert [m for m in board.all_marks() if m.kind == "challenge"]
    for u in units:
        assert u.ledger.entries
        assert u.ledger.restaked == 0
        assert set(u.first_seen) == u.facts          # nothing adopted, all dated


def test_the_challenge_channel_is_deterministic():
    def run():
        _spec, units, board, raised, retractions = _play_challenge(
            3, 30, channel=True)
        return ([(u.ledger.hits, u.ledger.misses, sorted(u.laws)) for u in units],
                [(m.author, m.kind, m.content, m.counterexample)
                 for m in board.all_marks() if m.kind == "challenge"],
                raised, retractions)
    assert run() == run()
