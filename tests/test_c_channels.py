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
# THE LIFECYCLE, ONCE. A unit challenges a published LAW mark when its own facts
# hold a counterexample — an individual carrying the law's body without its head
# — and the challenge carries that individual. The law's author, reading a
# challenge against a law it still holds, VERIFIES the counterexample against its
# own facts; holding that same individual WITH the head rebuts the challenge and
# the law stands. What has changed under the author's ruling is everything after
# that. A challenge the author cannot rebut no longer retracts anything: the
# author RE-ASSESSES the law against its own current record by its own induction
# criterion (the internal arm — if the record no longer sustains it, the doubt is
# settled inside the membrane), and if the record does sustain it the law is
# SUSPENDED and a call for corroboration is published (the external arm). An
# independent peer bearing the doubt out eliminates the law; a peer holding the
# disputed individual with the head restores it; silence restores it. The
# calculus still decides, and now the same standard governs holding a law and
# losing it.


# --- challenging ---------------------------------------------------------------


def test_a_counterexample_holder_challenges_a_published_law():
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z9"),)))       # body without head — a counterexample
    challenges = u1.challenge(board, 1)
    assert challenges and challenges[0].kind == "challenge"


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


# --- disposing: doubt, inquiry, and the two arms ------------------------------
#
# THE AUTHOR'S RULING, replacing Task 5's disposition rule: *corroborate and
# suspend, but do not eliminate until corroboration.* A challenge raises a doubt;
# a doubt provokes inquiry; inquiry has an INTERNAL arm (the author re-assesses
# the law against its own current record, by the very criterion it would use to
# induce it today) and an EXTERNAL one (it publishes a call for corroboration and
# the community answers from its own records).


def _sustain(unit, law=("p1", "q1"), n=20):
    """Give `unit` a record that genuinely sustains `law`, so that its own
    induction criterion would admit it today: n individuals carrying the body and
    then the head, dated a round apart so precedence fixes the direction.

    WITHOUT THIS A UNIT TESTS THE WRONG ARM. A unit holding a law and no facts
    fails its own criterion instantly (no support), so every challenge against it
    is settled internally and the suspension machinery is never reached. That is
    correct behaviour — an author with no record cannot sustain a law — but it is
    not what these tests are about."""
    body, head = law
    for i in range(n):
        args = (("c", f"s{i}"),)
        unit._record({(body, args)}, i)
        unit._record({(head, args)}, i + 1)


def _dispute(unit, law=("p1", "q1"), who="z9", when=0):
    """Give `unit` one individual carrying the law's body and not its head — the
    pending case a peer will cite. One refuting against twenty confirmed is 4.8%,
    inside the 5% tolerance `induce` admits under, so the law still meets the
    criterion.

    THE ROUND MATTERS NOW, and it is 0 rather than the 21 it used to be. Since
    the open-world reading went into `_pending_split` an individual only counts
    against a law once its body has been held longer than the field's consequent
    lag, so a body dated AFTER the round the law is disposed at would be set
    aside as unknown and every one of these tests would exercise the wrong
    branch. Dating it at 0 puts the disputed individual squarely in the past of
    every disposal below, which is the situation they are about: an author that
    HAS observed the gap and cannot close it."""
    unit._record({(law[0], (("c", who),))}, when)


def test_an_unrebutted_challenge_suspends_the_law_rather_than_retracting_it():
    """THE RULING, in one test. The author cannot rebut the cited individual, so
    under the old rule it retracted; now the law is SUSPENDED — still held, still
    on the record — and the author asks for help."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    _sustain(u0)
    _dispute(u0)
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z9"),)))
    u1.challenge(board, 1)
    out = u0.dispose_challenges(board, 2)
    assert out.suspended == [("p1", "q1")]
    assert out.retracted_by_corroboration == [] and out.retracted_internally == []
    assert ("p1", "q1") in u0.laws                  # NOT retracted
    assert ("p1", "q1") in u0.suspended


def test_a_suspended_law_licenses_no_anticipation():
    """The operational content of suspension: the unit stops betting on the law
    without giving it up, so it can neither win nor lose while the doubt
    stands."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    _sustain(u0)
    _dispute(u0)
    u0.laws.add(("p1", "q1"))
    assert u0.anticipate() == {("q1", (("c", "z9"),))}
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z9"),)))
    u1.challenge(board, 1)
    u0.dispose_challenges(board, 2)
    assert u0.anticipate() == set()
    u0.suspended.clear()
    assert u0.anticipate() == {("q1", (("c", "z9"),))}


def test_a_suspended_law_is_still_held_and_still_rendered():
    """Suspension withdraws a licence, not a law. `as_egi` renders what the unit
    holds — the record does not quietly lose the claim its author is still
    inquiring into."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    _sustain(u0)
    _dispute(u0)
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z9"),)))
    u1.challenge(board, 1)
    u0.dispose_challenges(board, 2)
    drawn = u0.as_egi()
    assert len(drawn.Cut) == 2                      # the law's Horn double cut
    assert len(u0.as_egi(laws=u0.laws - u0.suspended).Cut) == 0


def test_a_rebuttable_challenge_leaves_the_law_standing_and_unsuspended():
    """Unchanged from Task 5: the author holds the cited individual WITH the
    head, so the citation is false of the world it has met. No doubt is opened at
    all — there is nothing to inquire into."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0.laws.add(("p1", "q1"))
    u0.facts.update({("p1", (("c", "z9"),)), ("q1", (("c", "z9"),))})
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z9"),)))
    u1.challenge(board, 1)
    out = u0.dispose_challenges(board, 2)
    assert not out
    assert ("p1", "q1") in u0.laws and u0.suspended == set()
    assert board.corroboration_calls() == []


# --- the internal arm: doubt provokes a re-assessment -------------------------


def test_a_challenge_provokes_a_re_assessment_that_settles_the_doubt_internally():
    """THE INTERNAL ARM. The author's own record no longer meets the criterion it
    would use to induce this law today — six of twenty-six individuals carry the
    body without the head, far past the 5% it admits under — so the doubt is
    settled inside the membrane. No corroboration is needed and none is asked
    for: the author was defeated by its own evidence."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    _sustain(u0)
    for who in ("z1", "z2", "z3", "z4", "z5", "z6"):
        _dispute(u0, who=who)
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z1"),)))
    u1.challenge(board, 1)
    out = u0.dispose_challenges(board, 2)
    assert out.retracted_internally == [("p1", "q1")]
    assert out.suspended == []
    assert ("p1", "q1") not in u0.laws and u0.suspended == set()
    assert board.corroboration_calls() == []        # nobody was asked anything


def test_the_re_assessment_runs_only_when_a_doubt_provokes_it():
    """INQUIRY IS OCCASIONED, not continuous. A law whose support has rotted away
    is still held while nobody disputes it — `induce` only ever added, and this
    ruling does not turn disposal into a background audit. What it does is make a
    challenge the occasion for the re-test that was never happening."""
    _spec, _field, u0, _u1 = _two_units()
    board = MarkBoard()
    _sustain(u0)
    for who in ("z1", "z2", "z3", "z4", "z5", "z6"):
        _dispute(u0, who=who)
    u0.laws.add(("p1", "q1"))
    assert not u0._meets_criterion(("p1", "q1"), 2)  # it would not induce it now
    assert not u0.dispose_challenges(board, 2)       # and nothing disturbs it
    assert ("p1", "q1") in u0.laws


def test_the_same_standard_governs_holding_a_law_and_losing_it():
    """THE INCOHERENCE, FIXED. Task 5 pinned the defect in miniature: `induce`
    admits at a 5% pending RATE and the old disposition rule fired on any ONE
    pending individual, so a law was refutable the moment its author proposed it
    (`test_induction_admits_a_law_the_challenge_rule_immediately_refutes`, which
    this test replaces). Now the challenger cites the very individual the
    author's induction tolerated, and the law is not destroyed by it — it is put
    in doubt, on the same terms it was taken up on.

    THE CLOCK RUNS FORWARD THROUGHOUT, which matters now that the criterion reads
    it: the pending body arrives at 21, the law is induced at 22, published at
    22, challenged at 23 and disposed at 24, so the disputed individual has been
    held past the consequent lag at every point the criterion is asked. It counts
    as a refutation and is tolerated as one — which is the claim."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    for i in range(20):
        args = (("c", f"a{i}"),)
        u0._record({("p1", args)}, i)
        u0._record({("q1", args)}, i + 1)
    pending = (("c", "a99"),)
    u0._record({("p1", pending)}, 21)               # 1 refuting of 21 = 4.8%
    assert u0.induce(22) == {("p1", "q1")}
    u0.publish(board, 22)
    u1.facts.add(("p1", pending))                   # the same individual
    u1.challenge(board, 23)
    out = u0.dispose_challenges(board, 24)
    assert out.suspended == [("p1", "q1")]
    assert ("p1", "q1") in u0.laws
    assert u0._meets_criterion(("p1", "q1"), 24)    # by its own standard, still


# --- the call for corroboration ------------------------------------------------


def test_the_author_publishes_a_call_naming_the_law_and_the_disputed_individual():
    """The ask channel's shape, pointed at a law: a public, attributable question
    that asserts nothing and names exactly what would bear on it."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    _sustain(u0)
    _dispute(u0)
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z9"),)))
    u1.challenge(board, 1)
    u0.dispose_challenges(board, 2)
    call, = board.corroboration_calls()
    assert (call.author, call.kind, call.round_idx) == ("u0", "corroboration", 2)
    assert call.content == ("p1", "q1")
    assert call.counterexample == ("p1", (("c", "z9"),))


def test_a_call_is_published_once_per_law_ever():
    """The discipline every other act here keeps. A second call about one law
    would be the same request again, counted twice by the instruments."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    _sustain(u0)
    _dispute(u0)
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z9"),)))
    u1.challenge(board, 1)
    for r in range(2, 6):
        u0.dispose_challenges(board, r)
    assert len(board.corroboration_calls()) == 1
    assert board.republished == 0


def test_a_call_cannot_be_adopted():
    """It asks about a law rather than claiming one; taking it up would enter a
    law its own author has put in doubt."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    _sustain(u0)
    _dispute(u0)
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z9"),)))
    u1.challenge(board, 1)
    u0.dispose_challenges(board, 2)
    call, = board.corroboration_calls()
    with pytest.raises(ValueError, match="corroboration call"):
        u1.adopt(call, board)
    assert ("p1", "q1") not in u1.laws


def test_a_corroboration_mark_must_name_a_law_and_an_individual():
    with pytest.raises(ValueError, match="corroboration"):        # fact-shaped
        Mark(author="u0", content=("p1", A1), kind="corroboration", round_idx=0,
             counterexample=("p1", A1))
    with pytest.raises(ValueError, match="no counterexample"):
        Mark(author="u0", content=("p1", "q1"), kind="corroboration", round_idx=0)
    with pytest.raises(ValueError, match="not the law's body"):
        Mark(author="u0", content=("p1", "q1"), kind="corroboration", round_idx=0,
             counterexample=("p2", A1))


# --- answering the call --------------------------------------------------------


def test_a_peer_answers_the_call_with_its_own_counterexample():
    """CORROBORATION IS A PEER'S OWN EVIDENCE, published as an ordinary challenge
    through the same once-per-law mint — because that is what it is. What makes
    it corroboration rather than a fresh dispute is only that another record
    already said the same thing: independence is a property of the two records,
    not of the mark."""
    u0, u1, u2, _u3 = _units()
    board = MarkBoard()
    _sustain(u0)
    _dispute(u0)
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z9"),)))
    u1.challenge(board, 1)
    u0.dispose_challenges(board, 2)                 # suspends; publishes the call
    u2.facts.add(("p1", (("c", "z8"),)))            # its own, different case
    answer, = u2.corroborate(board, 3)
    assert (answer.author, answer.kind) == ("u2", "challenge")
    assert answer.counterexample == ("p1", (("c", "z8"),))


def test_a_peer_answers_the_call_by_publishing_the_disputed_individual_with_the_head():
    """The other answer a call can get, and the ruling's own restoring move: the
    peer holds the very individual in dispute WITH the head. It is published as
    an ordinary fact mark, indistinguishable from the same content published
    unprompted, because that is what it is."""
    u0, u1, u2, _u3 = _units()
    board = MarkBoard()
    _sustain(u0)
    _dispute(u0)
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z9"),)))
    u1.challenge(board, 1)
    u0.dispose_challenges(board, 2)
    u2.facts.add(("q1", (("c", "z9"),)))            # the head, for that case
    answer, = u2.corroborate(board, 3)
    assert (answer.author, answer.kind, answer.content) == (
        "u2", "fact", ("q1", (("c", "z9"),)))


def test_a_unit_never_answers_its_own_call_and_says_nothing_it_has_not_met():
    """It cannot corroborate its own doubt, for the reason it cannot answer its
    own question — and a peer with neither the head nor a counterexample of its
    own simply has nothing to contribute. That silence is what the window
    measures."""
    u0, u1, u2, _u3 = _units()
    board = MarkBoard()
    _sustain(u0)
    _dispute(u0)
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z9"),)))
    u1.challenge(board, 1)
    u0.dispose_challenges(board, 2)
    assert u0.corroborate(board, 3) == []           # its own call
    assert u2.corroborate(board, 3) == []           # an empty record


# --- closing the doubt ---------------------------------------------------------


def test_independent_corroboration_eliminates_the_law():
    """The one thing that eliminates a law from outside: a second record,
    independently, bearing the doubt out."""
    u0, u1, u2, _u3 = _units()
    board = MarkBoard()
    _sustain(u0)
    _dispute(u0)
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z9"),)))
    u1.challenge(board, 1)
    assert u0.dispose_challenges(board, 2).suspended == [("p1", "q1")]
    u2.facts.add(("p1", (("c", "z8"),)))
    u2.corroborate(board, 3)
    out = u0.dispose_challenges(board, 4)
    assert out.retracted_by_corroboration == [("p1", "q1")]
    assert ("p1", "q1") not in u0.laws and u0.suspended == set()


def test_the_original_challenger_s_counterexample_does_not_count_twice():
    """INDEPENDENCE IS THE WHOLE POINT of requiring corroboration. The unit that
    opened the doubt cannot also close it: its counterexample is the one already
    being weighed, and counting it twice would turn one record's gap into two
    voices. Here the challenger is the only dissenting record, and the law is not
    eliminated however many rounds pass inside the window."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    _sustain(u0)
    _dispute(u0)
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z9"),)))
    u1.challenge(board, 1)
    u0.dispose_challenges(board, 2)
    for r in range(3, 7):                            # inside the window
        out = u0.dispose_challenges(board, r)
        assert out.retracted_by_corroboration == []
        assert ("p1", "q1") in u0.suspended


def test_a_peer_s_published_head_restores_the_suspended_law():
    """The ruling's restoring move. The author could not settle the case from its
    own record — under a fallible field a withheld consequent looks exactly like
    a refutation — and a peer that WAS looking supplies the missing observation.
    The law goes back to work; the peer's fact is not adopted, because what was
    restored is a licence, not a holding."""
    u0, u1, u2, _u3 = _units()
    board = MarkBoard()
    _sustain(u0)
    _dispute(u0)
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z9"),)))
    u1.challenge(board, 1)
    u0.dispose_challenges(board, 2)
    u2.facts.add(("q1", (("c", "z9"),)))
    u2.corroborate(board, 3)
    out = u0.dispose_challenges(board, 4)
    assert out.restored_by_rebuttal == [("p1", "q1")]
    assert ("p1", "q1") in u0.laws and u0.suspended == set()
    assert ("q1", (("c", "z9"),)) not in u0.facts    # restored, not adopted


def test_the_author_s_own_later_observation_restores_the_law():
    """A verification is a snapshot — Task 5's own concern, and suspension is
    what makes it repairable. The head arrives at the author's membrane two
    rounds after the doubt opened, and the author lifts its own suspension
    without needing anybody."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    _sustain(u0)
    _dispute(u0)
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z9"),)))
    u1.challenge(board, 1)
    u0.dispose_challenges(board, 2)
    u0._record({("q1", (("c", "z9"),))}, 3)          # the withheld head, late
    out = u0.dispose_challenges(board, 4)
    assert out.restored_by_rebuttal == [("p1", "q1")]
    assert ("p1", "q1") in u0.laws and u0.suspended == set()


def test_silence_restores_the_law_when_the_window_runs_out():
    """SILENCE CANNOT ELIMINATE. A challenge that gathers no support has failed,
    and "do not eliminate until corroboration" fixes the direction the window
    must end in. The default is five rounds and it is the author's to overrule."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    _sustain(u0)
    _dispute(u0)
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z9"),)))
    u1.challenge(board, 1)
    assert u0.dispose_challenges(board, 2).suspended == [("p1", "q1")]
    assert u0.corroboration_window == 5
    for r in range(3, 7):
        assert not u0.dispose_challenges(board, r)
        assert ("p1", "q1") in u0.suspended
    out = u0.dispose_challenges(board, 7)            # 7 - 2 == the window
    assert out.restored_by_silence == [("p1", "q1")]
    assert ("p1", "q1") in u0.laws and u0.suspended == set()


def test_a_challenge_that_failed_to_gather_support_does_not_raise_the_doubt_again():
    """A CHALLENGE IS DISPOSED OF ONCE, EVER — the discipline `publish`, `ask` and
    `challenge` already keep. Without it the channel oscillates on its own: the
    restored law meets the same unanswered inscription next round and is
    suspended again forever. What can raise a fresh doubt is fresh evidence, and
    that is exactly what corroboration means here."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    _sustain(u0)
    _dispute(u0)
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z9"),)))
    u1.challenge(board, 1)
    u0.dispose_challenges(board, 2)
    u0.dispose_challenges(board, 7)                  # restored by silence
    for r in range(8, 14):
        assert not u0.dispose_challenges(board, r)
    assert ("p1", "q1") in u0.laws and u0.suspended == set()


def test_a_shorter_window_is_the_author_s_to_set():
    """The window is a named parameter with a stated default, not a constant
    buried in the disposal."""
    _spec, _field, _u0, u1 = _two_units()
    board = MarkBoard()
    u0 = Unit("u0", _u0.aperture, corroboration_window=1)
    _sustain(u0)
    _dispute(u0)
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z9"),)))
    u1.challenge(board, 1)
    u0.dispose_challenges(board, 2)
    assert u0.dispose_challenges(board, 3).restored_by_silence == [("p1", "q1")]


# --- what did not change -------------------------------------------------------


def test_a_challenge_to_a_law_the_unit_does_not_hold_disposes_of_nothing():
    """Nothing is disposed of that was never held."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", A1))
    u1.challenge(board, 1)
    assert not u1.dispose_challenges(board, 2)        # u1 never held it
    other = Unit("u2", u1.aperture)
    assert not other.dispose_challenges(board, 2)


def test_a_disposal_does_not_answer_for_a_challenge_made_later():
    """A disposal at round r answers for challenges published at r or earlier.
    The board is a place and keeps no clock, so the bound comes from the
    caller."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    _sustain(u0)
    _dispute(u0)
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z9"),)))
    u1.challenge(board, 5)
    assert not u0.dispose_challenges(board, 4)
    assert u0.dispose_challenges(board, 5).suspended == [("p1", "q1")]


def test_volume_of_challenges_does_not_decide_a_law():
    """THE POINT OF THE CHANNEL, unchanged. Three peers challenge one law and
    every one of their counterexamples is rebutted by the author's own record: no
    doubt is opened at all. A rule that counted challenges would have taken three
    voices for corroboration — and the challengers are not wrong about their own
    records, they are simply not the ones who decide."""
    u0, u1, u2, u3 = _units()
    board = MarkBoard()
    u0.laws.add(("p1", "q1"))
    for args in (A1, A2, (("c", "a3"),)):
        u0.facts.update({("p1", args), ("q1", args)})
    u0.publish(board, 0)
    for peer, args in ((u1, A1), (u2, A2), (u3, (("c", "a3"),))):
        peer.facts.add(("p1", args))
        assert peer.challenge(board, 1)
    assert len(board.challenges_against(("p1", "q1"))) == 3
    assert not u0.dispose_challenges(board, 2)
    assert ("p1", "q1") in u0.laws and u0.suspended == set()


def test_the_author_verifies_against_its_own_record_not_the_challengers():
    """The two records disagree, and the author's is the one that decides its own
    law. The challenger is not lying — it really does lack the head — and it
    still does not get to suspend someone else's law."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0.laws.add(("p1", "q1"))
    u0.facts.update({("p1", A1), ("q1", A1)})
    u0.publish(board, 0)
    u1.facts.add(("p1", A1))
    challenge, = u1.challenge(board, 1)
    assert challenge.counterexample == ("p1", A1)
    assert not u0.dispose_challenges(board, 2)
    assert ("p1", "q1") in u0.laws


def test_a_challenge_meets_every_author_of_the_law():
    """Addressed to a claim, not to a person: two units that independently
    published `p1 -> q1` published ONE claim twice, and one challenge puts it in
    doubt for both — each inquiring into its own record."""
    u0, u1, u2, _u3 = _units()
    board = MarkBoard()
    for u in (u0, u1):
        _sustain(u)
        _dispute(u)
        u.laws.add(("p1", "q1"))
        u.publish(board, 0)
    u2.facts.add(("p1", (("c", "z9"),)))
    assert len(u2.challenge(board, 1)) == 1           # one challenge, not two
    assert u0.dispose_challenges(board, 2).suspended == [("p1", "q1")]
    assert u1.dispose_challenges(board, 2).suspended == [("p1", "q1")]


def test_a_suspended_or_defeated_law_still_stands_on_the_board():
    """The board is append-only: what a mark CLAIMS and what its author now HOLDS
    have come apart. The call for corroboration is the one piece of a law's
    changed standing that reaches the board at all; the rest is the maintenance
    channel's work (spec §9b)."""
    u0, u1, u2, _u3 = _units()
    board = MarkBoard()
    _sustain(u0)
    _dispute(u0)
    u0.laws.add(("p1", "q1"))
    law_mark = [m for m in u0.publish(board, 0) if m.kind == "law"][0]
    u1.facts.add(("p1", (("c", "z9"),)))
    u1.challenge(board, 1)
    u0.dispose_challenges(board, 2)
    u2.facts.add(("p1", (("c", "z8"),)))
    u2.corroborate(board, 3)
    u0.dispose_challenges(board, 4)
    assert ("p1", "q1") not in u0.laws
    assert law_mark in board.all_marks()


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
    assert ("p1", "q1") in u0.laws
    assert u0.facts == set()


# --- the measurement: does suspension save the true laws? ---------------------
#
# THE DRIVER IS EXPLICIT, as in the ask channel's measurement above. Four units
# with distinct overlapping apertures induce laws from what they meet, publish
# what they hold, challenge what their records contradict, answer each other's
# calls for corroboration, and dispose of the doubts standing against them.
# Nothing adopts anything: Task 3 measured indiscriminate uptake and found it
# strictly harmful, and mixing it in here would confound two effects.
#
# THE MODELER'S LABEL IS READ ONLY IN THIS FILE. `spec.domains[i].law` says which
# laws the field actually carries, so a retraction can be labelled FALSE (a true
# law defeated) or CORRECT (an accidental law defeated). No `Unit` reads it — a
# unit that knew which laws were planted would not be testing anything.

C_ROUNDS = 60
C_SEEDS = [1, 2, 3, 4, 5, 7, 42, 99]


def _play_challenge(seed, rounds, *, channel, stagger=1, seed_laws=False,
                    wrong_laws=False, induce=True):
    """Four units, one board. Each round: attend the field (inducing), publish
    what is held, then — if the channel is live — challenge, answer standing
    calls, and dispose.

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
    events = []                    # (unit_id, law, why), with repeats: the thrash
    tally = {k: 0 for k in ("suspended", "internal", "corroborated",
                            "rebutted", "silence")}
    for r in range(rounds):
        for i, u in enumerate(units):               # (a) attend + induce
            if stagger == 1 or r % stagger == i % stagger:
                u.step(field, r, induce=induce)
        for u in units:                             # (b) publish what is held
            u.publish(board, r)
        if channel:
            for u in units:                         # (c) challenge
                raised += len(u.challenge(board, r))
            for u in units:                         # (d) answer standing calls
                u.corroborate(board, r)
            for u in units:                         # (e) dispose
                out = u.dispose_challenges(board, r)
                tally["suspended"] += len(out.suspended)
                tally["internal"] += len(out.retracted_internally)
                tally["corroborated"] += len(out.retracted_by_corroboration)
                tally["rebutted"] += len(out.restored_by_rebuttal)
                tally["silence"] += len(out.restored_by_silence)
                for law in out.retracted_internally:
                    events.append((u.unit_id, law, "internal"))
                for law in out.retracted_by_corroboration:
                    events.append((u.unit_id, law, "corroborated"))
    return spec, units, board, raised, events, tally


def test_suspension_saves_the_true_laws_the_existential_rule_destroyed():
    """THE HEADLINE, AND IT IS POSITIVE — which is not what the last two
    measurements here reported, so read the counts rather than the direction.

    Eight seeds, 60 rounds, four units inducing from what they meet. Three rules
    have now been measured on this arm, and the columns are the argument:

                                        existential   suspension   + open world
        raised                                   58           58             60
        suspended                                 —           28             60
        eliminated by corroboration               —           18             12
        retracted by internal re-assessment       —           38              4
        restored by rebuttal                      —            2             44
        restored by silence                       —            0              0
        -----------------------------------------------------------------------
        distinct (unit, law) defeats             58           56             16
        **true laws still gone at the end**      34            2          **0**
        retraction events (thrash)              426           56             16
        net live / net mute                 384/596      454/596        932/1038

    THE OPEN-WORLD READING OF `pending` IS WHAT CLOSED THE LAST TWO. Under the
    ruling alone the internal arm did most of the killing and every one of its
    38 victims was a true law, because an individual whose consequent had not yet
    had time to arrive was read as counter-evidence. Setting those aside
    (`Unit._pending_split`) takes the internal arm from 38 victims to 4 and the
    permanent loss of true laws from 2 to 0.

    AND IT IS WHAT LET THE EXTERNAL ARM RUN AT ALL. Suspensions rise from 28 to
    60 and restorations by rebuttal from 2 to 44: the doubts that used to be
    settled inside the membrane by a miscounted record are now put to the
    community, and the community answers — 44 of the 60 with the disputed
    individual's head. That is the machinery the author's ruling built, doing the
    work it was built for. At seed 5 it runs to completion with nothing defeated
    at all: six challenges raised, six laws suspended, six rebutted, none lost.

    THE PRICE IN SCORE, at equal run length (60 rounds both arms): **+932 live
    against +1038 mute** — a 10% cost, where the ruling alone paid 24% and the
    existential rule 36%. The channel still costs, and the cost is what
    suspension is: a true law mute for a few rounds forgoes the hits it would
    have won. It loses at 8 of 8 seeds, asserted per-seed.
    """
    raised_total = 0
    agg = {k: 0 for k in ("suspended", "internal", "corroborated",
                          "rebutted", "silence")}
    events_total = defeats = false_defeats = 0
    lost_true = lost_false = 0
    live_total = mute_total = 0
    for seed in C_SEEDS:
        spec, live, _board, raised, events, tally = _play_challenge(
            seed, C_ROUNDS, channel=True)
        _s, mute, _b, _r, _e, _t = _play_challenge(seed, C_ROUNDS, channel=False)
        planted = {d.law for d in spec.domains}
        distinct = {(uid, law) for uid, law, _why in events}
        # THE GUARD IS THAT THE CHANNEL RAN, not that a law died. Under the old
        # rule every seed produced defeats, so requiring one was a free way to
        # say "something happened"; now seed 5 raises six challenges, suspends
        # six laws and rebuts all six, defeating nothing — which is the outcome
        # this task exists to produce, not an inert run. What must be nonzero is
        # the evidence and the inquiry it provoked.
        assert raised > 0 and tally["suspended"] > 0, (
            f"seed {seed}: nothing was disputed")
        # Every law on the board is one the field carries, as in Task 5.
        false_here = sum(1 for _u, law in distinct if law in planted)
        assert false_here == len(distinct), (
            f"seed {seed}: an accidental law reached the board")
        held = {(u.unit_id, law) for u in live for law in u.laws}
        gone = distinct - held
        lost_true += sum(1 for _u, law in gone if law in planted)
        lost_false += sum(1 for _u, law in gone if law not in planted)
        live_net = sum(u.ledger.net_score for u in live)
        mute_net = sum(u.ledger.net_score for u in mute)
        assert live_net < mute_net, (
            f"seed {seed}: the channel did not cost anything "
            f"({live_net:+d} against {mute_net:+d})")
        raised_total += raised
        for k in agg:
            agg[k] += tally[k]
        events_total += len(events)
        defeats += len(distinct)
        false_defeats += false_here
        live_total += live_net
        mute_total += mute_net
    assert (raised_total, defeats, false_defeats) == (60, 16, 16)
    assert agg == {"suspended": 60, "internal": 4, "corroborated": 12,
                   "rebutted": 44, "silence": 0}
    # THE COMPARISON THIS TASK EXISTS FOR: 34 of 58 true laws permanently lost
    # under the existential rule, 2 under the ruling, NONE once `pending` is
    # read open-world.
    assert (lost_true, lost_false) == (0, 0)
    # One retraction event per defeat: induction and disposal have stopped
    # fighting (426 events for 98 defeats before).
    assert events_total == defeats == 16
    assert (live_total, mute_total) == (932, 1038)


def test_the_channel_still_kills_every_false_law_and_now_by_the_author_s_own_record():
    """IT DID NOT BECOME TOOTHLESS, and the teeth stayed inward.

    Same eight seeds and rounds, each unit additionally seeded with the CONVERSE
    of its first domain's law — a law the field does not carry, so defeating it
    is a correct retraction. Measured after the open-world reading: **32 of 32
    converses defeated and permanently gone, 16 true laws defeated and all 16
    recovered, none permanently lost** (it was 32 of 32 with 54 recovered and 2
    lost under the ruling alone; the drop from 56 defeats to 16 is the first
    gate's finding, not a loss of bite).

    EVERY ONE OF THE 32 DIES BY INTERNAL RE-ASSESSMENT — not one needed a peer,
    exactly as before. Setting aside what could not have been observed does not
    save a converse: `a_head -> a_local` leaves individuals pending whose bodies
    the unit has held for many rounds, so they are refuting and stay refuting.
    That is the discrimination the open-world reading had to preserve and does.

    THE ARITHMETIC OF THE TRADE, and it improved again. The mute arm pays **77**
    for holding those converses (+1038 to +961); the live arm is **+932 in both
    arms**, identical seed by seed, because the wrong law dies before it can bet.
    So the benefit is 77 and the cost is 961 − 932 = **29**, where the ruling
    alone paid 142 and the existential rule 212. The trade has turned: a real
    good now bought at a third of its price rather than at twice it.
    """
    internal_false = corroborated_false = 0
    correct = recovered_true = lost_true = 0
    live_total = mute_total = 0
    for seed in C_SEEDS:
        spec, live, _board, _raised, events, _tally = _play_challenge(
            seed, C_ROUNDS, channel=True, wrong_laws=True)
        _s, mute, _b, _r, _e, _t = _play_challenge(
            seed, C_ROUNDS, channel=False, wrong_laws=True)
        planted = {d.law for d in spec.domains}
        distinct = {(uid, law) for uid, law, _why in events}
        held = {(u.unit_id, law) for u in live for law in u.laws}
        correct_here = sum(1 for _u, law in distinct if law not in planted)
        assert correct_here == 4, (
            f"seed {seed}: {correct_here} of 4 wrong laws defeated")
        assert not any(law not in planted for u in live for law in u.laws), (
            f"seed {seed}: a converse law survived the channel")
        internal_false += sum(1 for _u, law, why in events
                              if law not in planted and why == "internal")
        corroborated_false += sum(1 for _u, law, why in events
                                  if law not in planted and why == "corroborated")
        correct += correct_here
        recovered_true += sum(1 for u, law in distinct
                              if law in planted and (u, law) in held)
        lost_true += sum(1 for u, law in distinct
                         if law in planted and (u, law) not in held)
        live_total += sum(u.ledger.net_score for u in live)
        mute_total += sum(u.ledger.net_score for u in mute)
    assert correct == 32
    # THE AMENDMENT'S QUESTION: which arm does the discriminating work?
    assert (internal_false, corroborated_false) == (32, 0)
    assert (recovered_true, lost_true) == (16, 0)
    assert (live_total, mute_total) == (932, 961)


def test_under_bounded_attention_the_discrimination_still_inverts_and_now_internally():
    """THE NEGATIVE RESULT THAT SURVIVED THE RULING. Reported, not tuned away.

    Bounded attention (each unit attends half the rounds), both the planted laws
    and the converses seeded, no induction — so the same twelve laws per seed are
    held in both arms and the only variable is the channel. Measured over eight
    seeds: **64 of 64 true laws defeated and permanently gone, 2 of 32 false ones
    (6%)** — thirty converses survive while every true law dies. Those are the
    same counts the existential rule produced.

    THE OPEN-WORLD READING OF `pending` CHANGED NOT ONE OF THESE NUMBERS, and
    instrumenting the refusals says why. Every one of the 66 internal
    retractions fails on **`min_support`, none on the pending rate**, and they
    fall at rounds 0 to 2 with a median of **round 0**. A law SEEDED into a unit
    with no record has no supporting individual when the first challenge lands —
    a consequent cannot have arrived yet — so the re-assessment refuses it for
    want of evidence and the law is gone before the run begins. Setting aside
    what could not have been observed does not help: at round 0 there is nothing
    observed to set aside.

    THIS CORRECTS THE EXPLANATION THIS TEST CARRIED BEFORE, which said a true
    law's pending RATE sits near 50% under half attention and the criterion
    refuses it on that. The rate clause fires zero times here. What is true is
    the asymmetry in WHO GETS CHALLENGED: a true law's body arrives at round 0
    and its head cannot, so a peer holds a counterexample immediately; a
    converse's body IS a consequent, which arrives a round later, so at round 0
    almost nobody can dispute one — and since a law is challenged once per peer
    ever, the converses are never disputed again. Two of thirty-two die; the
    other thirty are simply never asked about.

    **THE ANTI-DISCRIMINATION IS NOT THE DISPOSITION RULE'S. IT IS THE FIELD'S
    TIMING, read through a criterion that requires support a seeded law has not
    had time to accumulate.** Suspension cannot help where the author's own
    record is the accuser, and it did not pretend to: the external arm never
    even opened. What the ruling and the open-world reading fixed is the case
    where a law the author's own record still sustains was destroyed anyway (the
    first gate above, 34 permanent losses down to 0). This case was never that.

    AND THE NET SCORE IMPROVES ANYWAY: −433 live against −1421 mute, identical to
    the old rule's figures. That is still the trap. Under bounded attention a true
    law cannot pay — its consequents arrive on rounds nobody is watching — so
    destroying it removes losing bets and the arm moves toward abstention. **A
    net-score improvement is not evidence that a channel discriminates.** Read it
    beside the counts, never instead of them.
    """
    true_defeats = false_defeats = 0
    internal = external = suspended = calls = 0
    true_held = false_held = 0
    live_total = mute_total = 0
    for seed in C_SEEDS:
        spec, live, board, raised, events, tally = _play_challenge(
            seed, C_ROUNDS, channel=True, stagger=2, seed_laws=True,
            wrong_laws=True, induce=False)
        _s, mute, _b, _r, _e, _t = _play_challenge(
            seed, C_ROUNDS, channel=False, stagger=2, seed_laws=True,
            wrong_laws=True, induce=False)
        planted = {d.law for d in spec.domains}
        distinct = {(uid, law) for uid, law, _why in events}
        assert raised > 0
        true_defeats += sum(1 for _u, law in distinct if law in planted)
        false_defeats += sum(1 for _u, law in distinct if law not in planted)
        internal += tally["internal"]
        external += tally["corroborated"]
        suspended += tally["suspended"]
        calls += len(board.corroboration_calls())
        true_held += sum(1 for u in live for law in u.laws if law in planted)
        false_held += sum(1 for u in live for law in u.laws
                          if law not in planted)
        assert not any(law in planted for u in live for law in u.laws), (
            f"seed {seed}: a true law survived bounded attention")
        live_total += sum(u.ledger.net_score for u in live)
        mute_total += sum(u.ledger.net_score for u in mute)
    assert (true_defeats, true_held) == (64, 0)      # 64 of 64 true laws gone
    assert (false_defeats, false_held) == (2, 30)    # 30 of 32 wrong laws stand
    # EVERY defeat is internal: the external arm never opened, so suspension had
    # nothing to save and nothing to blame.
    assert (internal, external, suspended, calls) == (66, 0, 0, 0)
    assert live_total > mute_total
    assert (live_total, mute_total) == (-433, -1421)


# --- can the community repair what the field withheld? ------------------------
#
# THE ONE THING NEITHER THE RULING NOR THE OPEN-WORLD READING CAN FIX is a
# consequent that never reached this membrane at all: after the lag it is
# indistinguishable from a refutation, and no amount of care with this unit's own
# record recovers it. But a peer whose aperture overlaps may have been looking
# when it arrived, and the ask channel already exists. The driver below runs the
# ask channel and the challenge channel together so the question can be put.


def _play_ask_and_challenge(seed, rounds, *, ask, stagger=2):
    """Four units, planted laws AND converses seeded, no induction, bounded
    attention. `ask` switches the ask/answer/adopt channel on and off; the
    challenge channel runs in both arms, so the only variable is whether peers
    can tell each other what they saw.

    UPTAKE IS TARGETED, exactly as in the ask channel's own measurement above: a
    unit adopts a fact mark ONLY when it answers a question that unit itself
    asked. Task 3 measured indiscriminate uptake and found it worse than silence.
    """
    spec = default_spec(seed=seed)
    field = Field(spec)
    aps = apertures_for(spec, n_units=4)
    planted = {d.name: d.law for d in spec.domains}
    units, mine = [], {}
    for i in range(4):
        laws = {planted[n] for n in aps[i].domains}
        body, head = planted[aps[i].domains[0]]
        mine[f"u{i}"] = (frozenset(laws), (head, body))
        units.append(Unit(f"u{i}", aps[i], laws=laws | {(head, body)}))
    board = MarkBoard()
    asked = {u.unit_id: [] for u in units}
    settled = {u.unit_id: set() for u in units}
    questions = uptakes = 0

    for r in range(rounds):
        if ask:                                             # (a) adopt replies
            for u in units:
                for q in asked[u.unit_id]:
                    if q.content in settled[u.unit_id]:
                        continue
                    reply = board.answer_to(q)
                    if reply is None or reply.author == u.unit_id:
                        continue
                    settled[u.unit_id].add(q.content)
                    uptakes += u.adopt(reply, board)
        for i, u in enumerate(units):                       # (b) attend
            if stagger == 1 or r % stagger == i % stagger:
                u.step(field, r, induce=False)
        if ask:
            for u in units:                                 # (c) ask
                mark = u.ask(board, r)
                if mark is not None:
                    asked[u.unit_id].append(mark)
                    questions += 1
            for u in units:                                 # (d) answer
                u.answer(board, r)
        for u in units:                                     # (e) publish
            u.publish(board, r)
        for u in units:                                     # (f) challenge
            u.challenge(board, r)
        for u in units:                                     # (g) corroborate
            u.corroborate(board, r)
        for u in units:                                     # (h) dispose
            u.dispose_challenges(board, r)

    tally = dict(true_ref=0, conv_ref=0, true_lost=0, conv_lost=0,
                 repairable=0, unrepairable=0, questions=questions,
                 uptakes=uptakes, net=sum(u.ledger.net_score for u in units))
    for u in units:
        laws, conv = mine[u.unit_id]
        for body, head in sorted(laws):
            _c, refuting, _unk = u._pending_split(body, head, rounds - 1)
            tally["true_ref"] += len(refuting)
            tally["true_lost"] += (body, head) not in u.laws
            for args in refuting:
                held = any((head, args) in p.facts for p in units if p is not u)
                tally["repairable" if held else "unrepairable"] += 1
        _c, refuting, _unk = u._pending_split(conv[0], conv[1], rounds - 1)
        tally["conv_ref"] += len(refuting)
        tally["conv_lost"] += conv not in u.laws
    return tally


def test_peer_testimony_repairs_the_false_law_and_not_the_true_one():
    """PRE-REGISTERED AND REFUTED, both halves, and the second one backwards.

    THE PREDICTIONS, recorded before the run. **P-C1:** with the ask channel
    live, a unit's refuting count on a TRUE law is lower than with the channel
    muted, because peer-supplied facts fill heads the field withheld from this
    unit. **P-C2:** the same channel does NOT materially lower the refuting count
    on a FALSE law, because no peer holds the missing head either.

    THE MEASUREMENT — eight seeds, 60 rounds, four units under bounded attention,
    planted laws and converses seeded, the challenge channel live in both arms:

                              muted     live      change
        refuting, true laws     640      636       −0.6%
        refuting, converses     321       42        −87%
        true laws lost        64/64    64/64    unchanged
        converses lost         2/32     2/32    unchanged
        net score              −433      −39
        questions / uptakes     0/0    480/448

    **P-C1 IS REFUTED.** 480 questions went out, 448 answers were taken up, and
    four of them landed on a true law's refuting individual. **P-C2 IS REFUTED IN
    THE OPPOSITE DIRECTION TO ITS OWN CLAIM:** the channel repaired 87% of the
    converse's refuting individuals. The instrument works; it points the wrong
    way.

    IT IS NOT THAT THE COMMUNITY LACKS THE EVIDENCE. Of the true laws' 640
    refuting individuals in the muted arm, some peer holds the missing head for
    **590 — 92.2% are repairable in principle.** The information is in the
    community and does not move.

    WHY: THE AUTHOR GIVES THE LAW UP BEFORE IT CAN ASK. A seeded law has no
    supporting record when the first challenge lands, so the internal
    re-assessment refuses it on `min_support` at round 0 (measured in the gate
    above: 66 of 66 refusals on support, median round 0). A law the unit no
    longer holds licenses no want, so `_wants` stops generating questions about
    its head — while the converse, which is challenged rarely and therefore
    survives, goes on generating them for the whole run. Instrumented over the
    same eight seeds: **16 of the 480 questions ask about a true law's head and
    464 ask about the converse's**, and all 64 true-law retractions fall at round
    0. The channel spends itself on the only laws still standing, and those are
    the false ones.

    THE QUESTION-GENERATION ITSELF IS NOT AT FAULT, which the brief asked to be
    checked. `Unit._wants` is defined over exactly the pending set — an atom the
    unit's law licenses over an individual its record already carries — so it
    targets what `_pending_split` sets aside, by construction. It simply has
    nothing to target once the law is gone.

    WHAT THIS SAYS ABOUT THE COMMUNITY HYPOTHESIS: it was not tested here. To
    test it a law would have to survive long enough to ask, which is a question
    about the order of retraction and inquiry, not about the channel.
    """
    agg = {k: 0 for k in ("true_ref", "conv_ref", "true_lost", "conv_lost",
                          "repairable", "unrepairable", "questions", "uptakes",
                          "net")}
    muted_agg = dict(agg)
    for seed in C_SEEDS:
        live = _play_ask_and_challenge(seed, C_ROUNDS, ask=True)
        mute = _play_ask_and_challenge(seed, C_ROUNDS, ask=False)
        for k in agg:
            agg[k] += live[k]
            muted_agg[k] += mute[k]
    assert agg["questions"] > 0 and agg["uptakes"] > 0, (
        "the channel carried nothing, so nothing was tested")
    # P-C1: refuted. The true laws' refuting count barely moves.
    assert (muted_agg["true_ref"], agg["true_ref"]) == (640, 636)
    # P-C2: refuted the other way. The converse's refuting count collapses.
    assert (muted_agg["conv_ref"], agg["conv_ref"]) == (321, 42)
    # And no law's fate changes: the same true laws are lost in both arms.
    assert muted_agg["true_lost"] == agg["true_lost"] == 64
    assert muted_agg["conv_lost"] == agg["conv_lost"] == 2
    # NOT FOR WANT OF EVIDENCE: 92.2% of what the true laws needed was held by
    # some peer in the muted arm and never reached the unit that needed it.
    assert (muted_agg["repairable"], muted_agg["unrepairable"]) == (590, 50)
    # The net score improves anyway — which, as the gate above says, is not
    # evidence that a channel discriminates.
    assert (muted_agg["net"], agg["net"]) == (-433, -39)


def test_the_channel_leaves_anticipate_before_observe_alone():
    """Challenging, corroborating and disposing are separate acts from `step`,
    which is untouched: the bet is still placed before the round's arrivals are
    seen, no forecast is charged twice, and every dated fact is still
    first-hand."""
    _spec, units, board, raised, events, tally = _play_challenge(
        3, 30, channel=True)
    assert raised > 0 and events
    assert [m for m in board.all_marks() if m.kind == "challenge"]
    assert tally["suspended"] > 0, "no doubt was ever entertained"
    for u in units:
        assert u.ledger.entries
        assert u.ledger.restaked == 0
        assert set(u.first_seen) == u.facts          # nothing adopted, all dated
        assert u.suspended <= u.laws                 # suspension is not removal


def test_the_channel_is_deterministic():
    def run():
        _spec, units, board, raised, events, tally = _play_challenge(
            3, 30, channel=True)
        return ([(u.ledger.hits, u.ledger.misses, sorted(u.laws),
                  sorted(u.suspended)) for u in units],
                [(m.author, m.kind, m.content, m.counterexample)
                 for m in board.all_marks()
                 if m.kind in ("challenge", "corroboration")],
                raised, events, tally)
    assert run() == run()
