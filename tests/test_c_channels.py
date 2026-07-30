# tests/test_c_channels.py
"""The ask channel: a question published, and answered from a peer's holdings.

The unit tests come first; the two measurement gates at the bottom are the real
question — does a pair that asks and answers end up better off than the same
pair mute, at equal run length?
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
