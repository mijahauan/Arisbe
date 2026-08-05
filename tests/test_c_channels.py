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

import dataclasses
import sys
from collections import Counter
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from c_channel_probe import audited, declares  # noqa: E402
from c_field import CYCLIC, PAIRS, Field, apertures_for, default_spec  # noqa: E402
from c_marks import FACT, Mark, MarkBoard  # noqa: E402
from c_unit import Unit  # noqa: E402

A1 = (("c", "a1"),)
A2 = (("c", "a2"),)


def _two_units():
    spec = default_spec(seed=20260728)
    aps = apertures_for(spec, n_units=4)
    return spec, Field(spec), Unit("u0", aps[0]), Unit("u1", aps[1])


def _units(n=4, seed=20260728):
    """`n` units on distinct apertures. Up to four they are the cyclic ones,
    unchanged; past four the community needs the `PAIRS` scheme, which is what
    the corroboration ruling asks for and what the cyclic scheme cannot
    build."""
    spec = default_spec(seed=seed)
    scheme = CYCLIC if n <= len(spec.domains) else PAIRS
    aps = apertures_for(spec, n_units=n, scheme=scheme)
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


def test_an_adopted_body_takes_its_turn_by_the_round_it_was_adopted():
    """URGENCY IS READ OFF THIS UNIT'S OWN ENCOUNTER, whatever route the body
    took. An adopted fact now carries the round the adopter took it up, and the
    want it creates is born at that round: the stake on its head goes down at the
    adopter's very next attended round, so it is urgent in exactly the sense the
    ordering means.

    Before this task an adopted body carried no date at all and sorted last, on
    the ground that a peer's publication schedule should not set this unit's
    priorities. That reason was about the AUTHOR's clock and it is untouched —
    the author published at round 0 and the adoption is at 3, and it is 3 that
    orders the want."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u1.facts.add(("p1", A2))
    hearsay, = u1.publish(board, 0)
    u0._record({("p1", A1)}, 0)
    u0.laws.add(("p1", "q1"))
    u0.adopt(hearsay, board, 3)                 # met here at 3, published at 0
    assert u0.ask(board, 3).content == ("q1", A2)
    assert u0.ask(board, 4).content == ("q1", A1)


def test_a_body_with_no_arrival_at_all_is_asked_about_last():
    """The abstention that survives: a body this unit holds with no arrival of
    any kind behind it — placed directly, as a test does — says nothing about how
    long the want has been waiting, and loses to every dated one."""
    _spec, _field, u0, _u1 = _two_units()
    board = MarkBoard()
    u0._record({("p1", A1)}, 0)
    u0.facts.add(("p1", A2))                    # no date, no route
    u0.laws.add(("p1", "q1"))
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
        u1.adopt(q, board, 0)
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
    assert u0.adopt(answer, board, 2) is True
    assert board.uptake_of(answer) == {"u0"}
    assert ("q1", A1) in u0.facts
    assert u0.first_seen == {("p1", A1): 0}         # the answer is NOT dated


# --- typifying: whom has it been worth asking? --------------------------------


def test_a_unit_learns_whom_to_ask_from_answers_that_proved_out():
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    good = Mark(author="u1", content=("q1", (("c", "a1"),)), kind="fact", round_idx=0)
    bad = Mark(author="u2", content=("q1", (("c", "a2"),)), kind="fact", round_idx=0)
    u0.credit(good, proved=True)
    u0.credit(good, proved=True)
    u0.credit(bad, proved=False)
    assert u0.whom_to_ask("q1") == "u1"


def test_whom_to_ask_is_none_before_any_evidence():
    _spec, _field, u0, _u1 = _two_units()
    assert u0.whom_to_ask("q1") is None


def test_a_preference_is_earned_per_relation_not_per_peer():
    """A peer's aperture is partial, so competence is too: `u1` bearing out
    everything it says about `q1` says nothing about `q2`, which it may never
    have met."""
    _spec, _field, u0, _u1 = _two_units()
    u0.credit(Mark(author="u1", content=("q1", A1), kind="fact", round_idx=0),
              proved=True)
    assert u0.whom_to_ask("q1") == "u1"
    assert u0.whom_to_ask("q2") is None


def test_a_peer_whose_testimony_never_bore_out_earns_no_preference():
    """A negative score is not a preference. `whom_to_ask` names a peer only on
    positive evidence, so a unit that has been let down by the only voice it
    ever heard is back where it started rather than pointed at somebody."""
    _spec, _field, u0, _u1 = _two_units()
    u0.credit(Mark(author="u1", content=("q1", A1), kind="fact", round_idx=0),
              proved=False)
    assert u0.peers["u1"]["q1"] == (0, 1)
    assert u0.whom_to_ask("q1") is None


def test_the_preference_ties_break_on_the_peer_id():
    _spec, _field, u0, _u1 = _two_units()
    for who in ("u3", "u1", "u2"):
        u0.credit(Mark(author=who, content=("q1", A1), kind="fact", round_idx=0),
                  proved=True)
    assert u0.whom_to_ask("q1") == "u1"


def test_a_unit_neither_credits_itself_nor_a_mark_that_asserts_nothing():
    _spec, _field, u0, _u1 = _two_units()
    with pytest.raises(ValueError, match="cannot credit its own mark"):
        u0.credit(Mark(author="u0", content=("q1", A1), kind="fact", round_idx=0),
                  proved=True)
    with pytest.raises(ValueError, match="cannot credit the question"):
        u0.credit(Mark(author="u1", content=("q1", A1), kind="question",
                       round_idx=0), proved=True)
    assert u0.peers == {}


def test_a_second_route_to_the_same_fact_proves_the_testimony_out():
    """The verdict is REPLICATION and nothing else: the unit adopted `q1(a1)`
    from a peer at round 1 and met it at its own membrane at round 3, so a
    second independent route delivered the same thing."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0._record({("p1", A1)}, 0)
    u0.laws.add(("p1", "q1"))
    u0.ask(board, 0)
    u1._record({("q1", A1)}, 0)
    answer, = u1.answer(board, 1)
    u0.adopt(answer, board, 1)
    assert u0.settle_credit(2) == []                 # window has not elapsed
    u0._record({("q1", A1)}, 3)                      # met first-hand
    assert u0.settle_credit(3) == [("u1", ("q1", A1), True)]
    assert u0.whom_to_ask("q1") == "u1"
    assert u0.settle_credit(9) == []                 # a verdict is entered once


def test_silence_at_this_unit_s_own_membrane_fails_the_testimony():
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0._record({("p1", A1), ("q1", A2)}, 0)          # q1 IS a relation it meets
    u0.laws.add(("p1", "q1"))
    u0.ask(board, 0)
    u1._record({("q1", A1)}, 0)
    answer, = u1.answer(board, 1)
    u0.adopt(answer, board, 1)
    assert u0.settle_credit(10) == []                # 9 rounds: not yet
    assert u0.settle_credit(11) == [("u1", ("q1", A1), False)]
    assert u0.peers["u1"]["q1"] == (0, 1)


def test_a_relation_this_unit_never_meets_yields_no_verdict_ever():
    """THE OPEN-WORLD DISCIPLINE, APPLIED TO TESTIMONY. A unit that never meets
    `q1` at its own membrane does not FAIL to see `q1(a1)` — it is not looking,
    and reading its own blindness as the peer's fault would credit the aperture
    rather than the testimony."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u0._record({("p1", A1)}, 0)
    u0.laws.add(("p1", "q1"))
    u0.ask(board, 0)
    u1._record({("q1", A1)}, 0)
    answer, = u1.answer(board, 1)
    u0.adopt(answer, board, 1)
    assert u0.settle_credit(50) == []
    assert u0.peers == {}


def test_a_fact_already_held_first_hand_credits_nobody():
    """The peer said something this unit already had, so nothing was taken up
    and there is nothing to bear out. Reading the unit's own earlier arrival
    back as a later replication would credit the peer for its own
    observation."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    u1._record({("q1", A1)}, 0)
    mark, = u1.publish(board, 0)
    u0._record({("q1", A1)}, 0)
    u0.adopt(mark, board, 5)
    assert u0.settle_credit(50) == []
    assert u0.peers == {}


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


# THE STANDING DISCIPLINE, ADDED BY THE CHANNEL AUDIT (`runs/RUN_C_AUDIT_LOG.md`).
# `@audited()` runs the arm inside `channel_calls()` and refuses to return if a
# channel this arm CALLED minted nothing. A finding of "no effect" from a
# mechanism that never ran is worth nothing at all, and the audit found two of
# them by hand; from here an arm whose channel goes quiet fails instead of
# printing a null. A zero that is PREDICTED is declared with `expect_silent=`
# and says why, at the decorator when the harness makes it structural and at
# the call site when the arm's own parameters do. A channel that is never
# called does not trip the guard, so the mute controls (`channel=False`,
# `ask=False`, `mute=True`) need no declaration.
@audited()
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
    declares(*(("adopt", "ask", "answer") if channel else ()))
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
                    uptakes += u.adopt(reply, board, r)
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

    WHY A NET COMPARISON WAS SAFE HERE AND IS STILL RETIRED. This arm seeds the
    law and runs no challenge channel, so no law can be lost in either arm and
    the inversion mechanism — buying a better score by destroying knowledge — is
    structurally absent. The comparison was therefore trustworthy here in a way
    it was not in GATE 1. It is retired anyway, because a gate that reads
    correctly only because of a property of its arm is a gate whose next reader
    has to rediscover that property. What the arm measures is stated instead:
    the channel sheds more losing stakes than winning ones.
    """
    live_pairs, mute_pairs = [], []
    live_hits = mute_hits = live_misses = mute_misses = 0
    for seed in SEEDS:
        live, board, answers, uptakes = _play(seed, ROUNDS, channel=True,
                                              stagger=2)
        mute, *_ = _play(seed, ROUNDS, channel=False, stagger=2)
        assert answers > 0 and uptakes > 0, (
            f"seed {seed}: the channel carried nothing, so nothing was tested")
        # Per-arm, so a single losing seed fails the gate and names itself.
        # RE-EXPRESSED 2026-07-31: the old form compared two net scores across
        # arms, which is the comparison the retirement forbids. In THIS arm no
        # law can be lost — `_play` seeds the law and runs no challenge channel —
        # so the score cannot be bought by destroying knowledge, and what the
        # channel actually does is shed losing stakes. That is stated directly,
        # and the shedding is made visible rather than folded into a scalar.
        for asking, silent in zip(live, mute):
            assert asking.ledger.misses < silent.ledger.misses, (
                f"seed {seed} {asking.unit_id}: asking shed no losing stake "
                f"({asking.ledger.misses} misses vs mute's "
                f"{silent.ledger.misses})")
            shed_misses = silent.ledger.misses - asking.ledger.misses
            shed_hits = silent.ledger.hits - asking.ledger.hits
            # KEPT CLAUSE FIVE, and named as one. Rearranged, this IS
            # `asking.net_score > silent.net_score` — the comparison the
            # retirement forbids as a verdict. It stands here because on THIS
            # arm no law can be lost (`_play` seeds the law and runs no
            # challenge channel), so the score cannot be bought by destroying
            # knowledge, which is the argument the docstring above makes. The
            # rule is spelling-independent: unfolding a forbidden comparison
            # into its components does not remove it, so it is annotated rather
            # than claimed gone.
            assert shed_misses > shed_hits, (
                f"seed {seed} {asking.unit_id}: the channel shed {shed_hits} "
                f"hits against {shed_misses} misses — it cost more than it saved")
        # NO PARTICIPATION CLAUSE HERE, and the absence is the point. Ceasing to
        # forecast is exactly the behaviour GATE 1 flags, so this gate must not
        # assert that the live arm kept betting — it did not, and that IS the
        # finding. The shedding is made visible by the two clauses above instead.
        # (Per the author's ruling of 2026-07-31: a participation clause is
        # asserted only where it can fail; a tautology here would read as
        # protection that is not there.)
        live_pairs.append(sum(u.ledger.net_score for u in live))
        mute_pairs.append(sum(u.ledger.net_score for u in mute))
        live_hits += sum(u.ledger.hits for u in live)
        mute_hits += sum(u.ledger.hits for u in mute)
        live_misses += sum(u.ledger.misses for u in live)
        mute_misses += sum(u.ledger.misses for u in mute)
    # THE AGGREGATE, RE-EXPRESSED 2026-07-31 for the same reason as the per-arm
    # clauses above. `sum(live_pairs) > sum(mute_pairs)` is not asserted here —
    # but KEPT CLAUSE SIX below (`(mute_misses - live_misses) > (mute_hits -
    # live_hits)`) is algebraically that same cross-arm net-score comparison,
    # unfolded into its hit/miss components rather than removed: the
    # retirement forbids a cross-arm net-score VERDICT, and unfolding a
    # forbidden comparison into its components does not make it a different
    # comparison, so it is annotated and kept, not claimed gone — for the same
    # reason KEPT CLAUSE FIVE gives above (this arm seeds the law and runs no
    # challenge channel, so no law can be lost and the score cannot be bought
    # by destroying knowledge). The genuinely NEW clause, not entailed by any
    # net comparison, is `asking.ledger.misses < silent.ledger.misses` above
    # (the per-seed miss-shedding clause) — that is what makes this gate
    # strictly stronger than the one it replaced. Net is REPORTED in the
    # message, never asserted as the verdict on its own.
    assert live_misses < mute_misses, (
        f"the channel shed no losing stake in aggregate — live {live_misses} "
        f"misses against mute's {mute_misses} (net {sum(live_pairs)} vs "
        f"{sum(mute_pairs)}, reported not asserted)")
    # KEPT CLAUSE SIX, and named as one. Rearranged, this IS
    # `sum(live_pairs) > sum(mute_pairs)` — the aggregate comparison the
    # retirement forbids as a verdict. It stands here for the reason given
    # above: no law can be lost on this arm, so the score cannot be bought by
    # destroying knowledge. Spelling-independent, same as clause five.
    assert (mute_misses - live_misses) > (mute_hits - live_hits), (
        f"the channel shed {mute_hits - live_hits} hits against "
        f"{mute_misses - live_misses} misses in aggregate — it cost more than "
        f"it saved")
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
        # `adopt` IS CALLED AND MINTS NOTHING, AND THAT IS THIS GATE'S RESULT.
        # Under full attention a shared domain delivers identically to both
        # units, so every reply arrives after the asker met the atom itself and
        # there is nothing left to take up — the same reason the `uptakes == 0`
        # assertion below states in its own words. The zero is the finding, not
        # a dead channel, so it is declared rather than repaired.
        live, board, answers, uptakes = _play(seed, 40, channel=True, stagger=1,
                                              expect_silent=("adopt",))
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
            # Full attention makes money. Within one arm, and safe: the line
            # above has just pinned the two arms' hits and misses EQUAL, so no
            # cross-arm reading is being taken from a scalar here.
            assert asking.ledger.hits > asking.ledger.misses


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


def test_a_self_raised_doubt_asks_before_it_eliminates():
    """THE INTERNAL ARM, AFTER THE RULING WAS APPLIED TO IT. The author's own
    record no longer meets the criterion it would use to induce this law today —
    six of twenty-six individuals carry the body without the head, far past the
    5% it admits under. Until this task that settled the law on the spot, at
    round 2: the doubter both raised the doubt and closed it, in one act, with
    nothing published and nobody asked.

    Now the same failure takes the same route the external arm takes. The law is
    SUSPENDED, a call for corroboration goes out, and a question goes out about
    one of the individuals that caused the failure — the ask channel's own mark,
    named so a peer can answer it from its own record. The law is given up only
    when the window has run out with nothing arriving to repair the record."""
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
    assert out.suspended == [("p1", "q1")]
    assert out.retracted_internally == []
    assert ("p1", "q1") in u0.laws and ("p1", "q1") in u0.suspended
    assert not u0._meets_criterion(("p1", "q1"), 2)  # condemned, not eliminated
    call, = board.corroboration_calls()
    assert call.author == "u0"
    asked = [m for m in board.all_marks() if m.kind == "question"]
    assert [m.author for m in asked] == ["u0"]
    assert asked[0].content[0] == "q1"               # about a pending head
    w = u0.corroboration_window
    for r in range(3, 2 + w):                        # the inquiry runs
        assert not u0.dispose_challenges(board, r)
        assert ("p1", "q1") in u0.suspended
    out = u0.dispose_challenges(board, 2 + w)         # round - 2 == the window
    assert out.retracted_internally == [("p1", "q1")]
    assert ("p1", "q1") not in u0.laws and u0.suspended == set()


def test_the_inquiry_that_repairs_the_record_saves_the_law():
    """THE CASE THE ORDERING EXISTS FOR, and it could not arise before: the
    author's own record condemned the law, the author asked, a peer answered, and
    the record that comes back through the window sustains the law after all.

    Three pending individuals against twenty confirmed put the pending rate at
    13%, past the 5% the criterion admits under. The author asks about them one
    per round; the peer holds two of the three heads and answers; and the
    criterion is re-read AT expiry rather than remembered from the round the
    doubt opened, so what it reads is the repaired record — one refuting of
    twenty-three, 4.3%, inside the tolerance. The law is restored by silence
    rather than given up.

    THE ONE THE PEER CANNOT ANSWER IS THE ONE IT CITED, so the challenge itself
    stands unrebutted the whole way: what the window closes on is a live doubt
    about a law the author's own record has come back to sustaining."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    _sustain(u0)
    for who in ("z1", "z2", "z3"):
        _dispute(u0, who=who)
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z1"),)))
    u1.challenge(board, 1)
    assert u0.dispose_challenges(board, 2).suspended == [("p1", "q1")]
    assert not u0._meets_criterion(("p1", "q1"), 2)  # condemned when it opened
    u1.facts.update({("q1", (("c", "z2"),)), ("q1", (("c", "z3"),))})
    w = u0.corroboration_window
    for r in range(3, 2 + w):
        for mark in u1.answer(board, r):            # answers what was asked
            u0.adopt(mark, board, r)
        u0.dispose_challenges(board, r)             # asks the next one
    assert ("q1", (("c", "z2"),)) in u0.facts
    assert ("q1", (("c", "z3"),)) in u0.facts
    assert u0._meets_criterion(("p1", "q1"), 2 + w)  # the record was repaired
    out = u0.dispose_challenges(board, 2 + w)
    assert out.restored_by_silence == [("p1", "q1")]
    assert ("p1", "q1") in u0.laws and u0.suspended == set()


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
        u1.adopt(call, board, 3)
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


def test_a_unit_s_own_challenge_does_not_corroborate_its_own_doubt():
    """THE HONESTY CONSTRAINT, AND IT WAS LOAD-BEARING RATHER THAN THEORETICAL.

    `challenge` scans the board by content, so a unit holding a law that another
    unit also published may publish a challenge to it — its own inscription,
    against its own law. Here u0 does exactly that, and u2 disputes the same law
    independently. Two challenge marks stand; only ONE of them is a foreign
    record, and one foreign record is not corroboration. The law waits.

    WHY IT MATTERS: counting the author's own mark would mean a single foreign
    counterexample plus the author's own gap eliminates a law, which is the rule
    Task 5 measured destroying 58 of 58 laws the field actually carries. Measured
    with the mark counted, under bounded attention, it eliminated 64 of 64 true
    laws at an age of exactly one round — the self-raised doubt in different
    clothes. A second, genuinely independent record does corroborate, and the
    last two lines are that control."""
    u0, u1, u2, u3 = _units()
    board = MarkBoard()
    for u in (u0, u1):
        _sustain(u)
        _dispute(u)
        u.laws.add(("p1", "q1"))
        u.publish(board, 0)
    mine, = u0.challenge(board, 1)                  # its own law, disputed by it
    assert (mine.author, mine.content) == ("u0", ("p1", "q1"))
    u2.facts.add(("p1", (("c", "z9"),)))
    u2.challenge(board, 1)
    out = u0.dispose_challenges(board, 2)
    assert out.suspended == [("p1", "q1")]
    assert u0._doubts[("p1", "q1")].challenger == "u2"   # the foreign one
    for r in range(3, 6):
        assert u0.dispose_challenges(board, r).retracted_by_corroboration == []
        assert ("p1", "q1") in u0.suspended
    u3.facts.add(("p1", (("c", "z8"),)))            # a second foreign record
    u3.challenge(board, 6)
    out = u0.dispose_challenges(board, 6)
    assert out.retracted_by_corroboration == [("p1", "q1")]


def test_a_unit_publishing_twice_cannot_corroborate_alone():
    """THE AUTHOR'S RULING, IN ITS OWN WORDS: *"Repeating one's own observation
    does not"* build a socially available, objectified reality. So the tally
    counts DISTINCT RECORDS, never inscriptions — two marks from one unit are
    one witness.

    `challenge` mints once per law ever, so a unit cannot publish twice about one
    law through the ordinary route; the second mark here is hand-minted, which is
    the point. The rule must hold against whatever any future channel puts on the
    board, not merely against what today's channel happens to allow. The control
    is the last three lines: a genuinely second record does corroborate, so the
    law is not simply unkillable."""
    u0, u1, u2, _u3 = _units()
    board = MarkBoard()
    _sustain(u0)
    _dispute(u0)
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z9"),)))
    u1.challenge(board, 1)
    board.publish(Mark(author="u1", content=("p1", "q1"), kind="challenge",
                       round_idx=2, counterexample=("p1", (("c", "z8"),))))
    assert len(board.challenges_against(("p1", "q1"))) == 2
    assert u0.dispose_challenges(board, 2).suspended == [("p1", "q1")]
    for r in range(3, 7):                            # inside the window
        assert u0.dispose_challenges(board, r).retracted_by_corroboration == []
        assert ("p1", "q1") in u0.suspended
    u2.facts.add(("p1", (("c", "z7"),)))             # a second RECORD
    u2.challenge(board, 6)
    out = u0.dispose_challenges(board, 6)
    assert out.retracted_by_corroboration == [("p1", "q1")]


def test_the_corroborating_bar_is_the_author_s_to_set():
    """WHOSE READING IS WHOSE. The author ruled that a unit's own inscription
    never corroborates — that is unconditional and is not this knob. What IS the
    knob is the controller's reading that the CHALLENGER counts as one of the two
    witnesses: `corroborating_witnesses = 2` means challenger plus one further
    unit, and the stricter alternative — two further units beyond the challenger,
    three foreign records — is 3.

    Both are exercised here on one situation, so the difference is visible in a
    single test rather than across two arms. THE STRICTER BAR IS NOT MERELY
    STRICTER IN THIS FIELD, IT IS UNREACHABLE: with four domains at two-domain
    apertures a domain is met by at most three units, so holder + challenger +
    one corroborator exhausts the community and a third foreign record cannot
    exist. Measured over eight seeds at six units, `witnesses=3` reads **0
    corroborations of 144 doubts**, exactly what the cyclic four-unit arm read.
    Moving the line to 3 costs a fifth domain."""
    def arm(bar, dissenters):
        u0, *peers = _units(n=5)
        u0.corroborating_witnesses = bar
        board = MarkBoard()
        _sustain(u0)
        _dispute(u0)
        u0.laws.add(("p1", "q1"))
        u0.publish(board, 0)
        for i, peer in enumerate(peers[:dissenters]):
            peer.facts.add(("p1", (("c", f"z{9 - i}"),)))
            peer.challenge(board, 1)
        u0.dispose_challenges(board, 2)
        return u0.dispose_challenges(board, 3).retracted_by_corroboration

    assert arm(2, 1) == []                  # the challenger alone never closes
    assert arm(2, 2) == [("p1", "q1")]      # challenger + one further unit
    assert arm(3, 2) == []                  # the stricter bar refuses the same
    assert arm(3, 3) == [("p1", "q1")]      # and takes a third foreign record


def test_a_self_raised_doubt_names_no_challenger_until_a_peer_speaks():
    """A doubt opened by nothing but the author's own record names nobody, and
    the first peer to dispute the law FILLS that slot rather than corroborating
    it — there is as yet nothing but the author's own record for it to
    corroborate. Elimination from outside takes two distinct foreign records
    whoever raised the doubt, which is the same bar the external arm has always
    used."""
    u0, u1, u2, u3 = _units()
    board = MarkBoard()
    for u in (u0, u1):
        _sustain(u)
        _dispute(u)
        u.laws.add(("p1", "q1"))
        u.publish(board, 0)
    u0.challenge(board, 1)                          # the only dispute is its own
    out = u0.dispose_challenges(board, 2)
    assert out.suspended == [("p1", "q1")]
    assert u0._doubts[("p1", "q1")].challenger is None
    u2.facts.add(("p1", (("c", "z9"),)))
    u2.challenge(board, 3)
    assert not u0.dispose_challenges(board, 3)      # borne out, not corroborated
    assert u0._doubts[("p1", "q1")].challenger == "u2"
    u3.facts.add(("p1", (("c", "z8"),)))
    u3.challenge(board, 4)
    out = u0.dispose_challenges(board, 4)
    assert out.retracted_by_corroboration == [("p1", "q1")]


def test_a_suspended_law_is_not_returned_to_service_by_induction_or_uptake():
    """THE BACK DOOR, CHECKED AND CLOSED BY CONSTRUCTION. Suspension is a subset
    of `laws`, so a law under doubt is invisible to `induce`'s scan even when the
    record would admit it today, and `adopt` finds it already held and changes
    nothing. Only a disposal lifts a suspension, and it does so by name — a
    suspended law cannot be quietly returned to active service by a record that
    has grown or by a peer republishing it."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    _sustain(u0)
    _dispute(u0)
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z9"),)))
    u1.challenge(board, 1)
    assert u0.dispose_challenges(board, 2).suspended == [("p1", "q1")]
    assert u0._meets_criterion(("p1", "q1"), 3)     # induce WOULD admit it today
    assert u0.induce(3) == set()                    # and does not
    assert ("p1", "q1") in u0.suspended
    u1.laws.add(("p1", "q1"))
    law_mark, = [m for m in u1.publish(board, 3) if m.kind == "law"]
    assert u0.adopt(law_mark, board, 3) is False
    assert ("p1", "q1") in u0.suspended
    assert u0.anticipate() == set()                 # still licensing nothing


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
    must end in. The default is eight rounds and it is the author's to overrule."""
    _spec, _field, u0, u1 = _two_units()
    board = MarkBoard()
    _sustain(u0)
    _dispute(u0)
    u0.laws.add(("p1", "q1"))
    u0.publish(board, 0)
    u1.facts.add(("p1", (("c", "z9"),)))
    u1.challenge(board, 1)
    assert u0.dispose_challenges(board, 2).suspended == [("p1", "q1")]
    w = u0.corroboration_window
    assert w == 8, "the ruled default (2026-07-31); the arithmetic below derives from it"
    for r in range(3, 2 + w):
        assert not u0.dispose_challenges(board, r)
        assert ("p1", "q1") in u0.suspended
    out = u0.dispose_challenges(board, 2 + w)         # round - 2 == the window
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
    w = u0.corroboration_window
    expiry = 2 + w
    u0.dispose_challenges(board, expiry)             # restored by silence
    for r in range(expiry + 1, expiry + 7):
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
        u0.adopt(challenge, board, 2)
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


def _assert_uniform_rate(units):
    """Every unit in one community must carry the same rate parameters.

    RULING 2 (2026-07-31) made the disposition knobs part of the terminal unit's
    RATE. West's question asks whether capacity and rate stay invariant as a
    community grows; a community whose units already disagree about their own
    rate cannot answer it, and a sweep that changed the window for some units
    would measure the window rather than the scaling.
    """
    rates = {u.unit_id: (u.corroboration_window, u.corroborating_witnesses,
                         u.replication_window) for u in units}
    distinct = set(rates.values())
    if len(distinct) > 1:
        raise ValueError(
            "mixed rate parameters across a community: the terminal unit's "
            "(corroboration_window, corroborating_witnesses, replication_window) "
            f"must be uniform, got {dict(sorted(rates.items()))}")


# `corroborate` IS DECLARED SILENT BECAUSE IT IS THE DEFECT THE AUDIT FOUND, NOT
# BECAUSE THE ZERO IS INNOCENT. `runs/RUN_C_AUDIT_LOG.md` records it as **D-A1**:
# `_mint_challenge`'s once-per-law-ever key is shared between `challenge` and
# `corroborate`, and this harness runs `challenge` at phase (c) before
# `corroborate` at phase (d), so the key is always spent by the time a call for
# corroboration is read; the head branch is preempted the same way by `publish`
# through `(FACT, head)`. The method is STRUCTURALLY PREEMPTED — 1920 to 2880
# calls per arm, zero mints, in all twenty published arms that play it. Fixing
# it means changing `src/c_unit.py`, which alters what the C-series models and
# was deferred by the spec's §9 to its own sitting. THIS DECLARATION IS TO BE
# REMOVED WHEN D-A1 IS FIXED: once corroboration can mint, a silent
# `corroborate` is a defect again and the guard should say so. That instruction
# is enforced rather than merely written down:
# `test_the_corroborate_declarations_still_have_something_to_declare`, in
# `tests/test_c_channel_probe.py`, runs this harness with the declaration off
# and fails the day corroboration mints.
@audited(expect_silent=("corroborate",))
def _play_challenge(seed, rounds, *, channel, stagger=1, seed_laws=False,
                    wrong_laws=False, induce=True, n_units=4, scheme=CYCLIC,
                    window=None, witnesses=None):
    """A community of `n_units` on one board. Each round: attend the field
    (inducing), publish what is held, then — if the channel is live — challenge,
    answer standing calls, and dispose.

    `wrong_laws` seeds each unit with the CONVERSE of its first domain's law, a
    law the field does not carry. It is what gives the channel something correct
    to do: without it the arm contains no accidental law, because `induce`
    proposes only planted ones at every seed measured.

    `stagger=2` is bounded attention — even-indexed units attend even rounds,
    odd-indexed odd — so the units' records genuinely differ and a rebuttal is
    possible on the merits rather than by their holding identical facts.

    `n_units` / `scheme` are the community, and they move together: the cyclic
    scheme reaches four units and puts two witnesses on every domain, `PAIRS`
    reaches six and puts three on every domain. `window` and `witnesses`
    override `Unit.corroboration_window` and `Unit.corroborating_witnesses` when
    a measurement sweeps them; `None` leaves each unit's own default alone.
    """
    spec = default_spec(seed=seed)
    field = Field(spec)
    aps = apertures_for(spec, n_units=n_units, scheme=scheme)
    planted = {d.name: d.law for d in spec.domains}
    units = []
    for i in range(n_units):
        laws = {planted[n] for n in aps[i].domains} if seed_laws else set()
        if wrong_laws:
            body, head = planted[aps[i].domains[0]]
            laws = laws | {(head, body)}            # the converse: never carried
        u = Unit(f"u{i}", aps[i], laws=laws)
        if window is not None:
            u.corroboration_window = window
        if witnesses is not None:
            u.corroborating_witnesses = witnesses
        units.append(u)
    _assert_uniform_rate(units)
    declares("publish", *(("challenge", "corroborate", "dispose_challenges")
                          if channel else ()))
    board = MarkBoard()
    raised = 0
    events = []                    # (unit_id, law, why), with repeats: the thrash
    tally = {k: 0 for k in ("suspended", "internal", "corroborated",
                            "rebutted", "silence", "asked")}
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
                tally["asked"] += len(out.asked)
                for law in out.retracted_internally:
                    events.append((u.unit_id, law, "internal"))
                for law in out.retracted_by_corroboration:
                    events.append((u.unit_id, law, "corroborated"))
    return spec, units, board, raised, events, tally


def _cost_reading(units, board):
    """What each unit's acts cost, READ where the acts already reside.

    THE_KYTOS §1.3: an act's effect resides in its report inside the membrane
    (`MembraneLedger`), in resources outside it, and in the shared reports among
    kytē (`MarkBoard`, which carries author, kind and round on every mark). None
    of that needs a counter. Only attendance did, and that is `Unit.attended`.

    KINDS ARE KEPT APART AND NEVER SUMMED. Summing a board read and a challenge
    into one "cost" would price two different acts alike, which is the collision
    `Unit.peers` refuses for (borne out, not borne out).

    INTERNAL WORK THAT LEAVES NO REPORT IS NOT COUNTED, deliberately. An act
    whose effect reaches no report has no channel by which to influence
    anything, so counting it privately would invent one. This reading therefore
    sees channel work and attendance and does NOT see materialization or
    anticipation work — a named limit, not an oversight.

    This lives in the tests because it is an OBSERVER's reading. Putting it in
    `src/` would hand a unit a faculty it does not have.
    """
    authored = Counter((m.author, m.kind) for m in board.all_marks())
    out = {}
    for u in units:
        marks = {kind: n for (author, kind), n in sorted(authored.items())
                 if author == u.unit_id}
        out[u.unit_id] = {
            "attended": u.attended,
            "marks": marks,
            "bets": u.ledger.hits + u.ledger.misses,
            "per_round": ({k: n / u.attended for k, n in marks.items()}
                          if u.attended else {}),
        }
    return out


def test_the_cost_reading_reads_residences_that_already_exist():
    """COST IS READ, NOT INSTRUMENTED (THE_KYTOS §1.3). An act's effect resides
    in the report inside the membrane, in resources outside it, and in the shared
    reports among kytē — so a private counter beside the act would duplicate two
    of the three and invent the observer the doctrine refuses.

    The board already reports every channel act, attributed and dated; the ledger
    already holds the bets. `Unit.attended` is the only number that existed
    nowhere. This reader composes the three and adds nothing.

    THE TWIN IS THE POINT. Two units with the same aperture and the same rate
    parameters must read the same attendance — that is ruling 2's invariance
    condition made checkable, and it is what a size sweep would have to hold."""
    _spec, units, board, *_ = _play_challenge(20260728, 20, channel=True,
                                              stagger=1, seed_laws=True)
    cost = _cost_reading(units, board)

    # Attendance is uniform where attention is: stagger=1 means all four met
    # every round.
    assert {c["attended"] for c in cost.values()} == {20}
    # Every published mark is attributed to the unit that made it, and the
    # reading's per-unit totals account for the whole board.
    assert sum(sum(c["marks"].values()) for c in cost.values()) == \
        len(board.all_marks())
    # The reading is per KIND, never summed across kinds: a board read and a
    # challenge are not the same act and may not be priced alike.
    assert all(isinstance(c["marks"], dict) for c in cost.values())
    # And it is a RATE, with attendance as its denominator.
    for c in cost.values():
        for kind, n in c["marks"].items():
            assert c["per_round"][kind] == n / c["attended"]


def test_the_cost_reading_reads_zero_for_a_unit_that_never_attended():
    """A unit that never met the field has no rate, not a zero one — the same
    discipline `MembraneLedger.accuracy` keeps for an abstainer. Dividing by an
    attendance of zero would fabricate a denominator."""
    spec = default_spec(seed=20260728)
    ap = apertures_for(spec, n_units=4)[0]
    idle = Unit("u0", ap)
    cost = _cost_reading([idle], MarkBoard())
    assert cost["u0"]["attended"] == 0
    assert cost["u0"]["per_round"] == {}


def test_a_community_of_mixed_rates_is_refused():
    """RULING 2 (2026-07-31): the disposition knobs ARE the terminal unit's rate
    parameter, so a community whose units disagree on them is not a community of
    terminal units and any West-shaped reading off it is void. Nothing enforced
    this before — `corroboration_window` is a per-unit dataclass field any caller
    could set individually.

    The refusal names what disagreed, in the style `apertures_for`'s
    `min_witnesses` already uses: a silent mixed-rate run is the failure mode,
    not a loud one."""
    spec = default_spec(seed=20260728)
    aps = apertures_for(spec, n_units=4)
    units = [Unit(f"u{i}", aps[i]) for i in range(4)]
    _assert_uniform_rate(units)                     # uniform by construction

    units[2].corroboration_window = 3
    with pytest.raises(ValueError) as exc:
        _assert_uniform_rate(units)
    assert "rate" in str(exc.value)
    assert "u2" in str(exc.value)


def test_a_sweep_still_varies_the_window_for_the_whole_community():
    """The guard forbids a MIXED community, never a swept one. A sweep sets the
    window for every unit at once, which is what a sweep should always have been
    doing — and `test_the_silence_window_at_three_five_and_eight` is exactly such
    a sweep, so it must keep passing untouched."""
    spec, units, *_ = _play_challenge(20260728, 10, channel=True, window=3)
    assert {u.corroboration_window for u in units} == {3}


def test_suspension_saves_the_true_laws_the_existential_rule_destroyed():
    """THE HEADLINE, AND IT IS POSITIVE — which is not what three of the
    measurements in this file report, so read the counts rather than the
    direction.

    RE-MEASURED AT WINDOW 8 (the ruled default, 2026-07-31). Eight seeds, 60
    rounds, four units inducing from what they meet. Four rules have now been
    measured on this arm, and the columns are the argument:

                                    existential  suspension  +open world  +inquiry
        raised                               58          58           60        60
        suspended                             —          28           60        60
        eliminated by corroboration           —          18           12         0
        retracted by internal re-assessment   —          38            6         6
        restored by rebuttal                  —           2           44        46
        restored by silence                   —           0            0         4
        ----------------------------------------------------------------------------
        distinct (unit, law) defeats         58          56           16         6
        **true laws still gone at the end**  34           2            0         2
        retraction events (thrash)          426          56           16         6
        net live / net mute             384/596     454/596     932/1038   924/1038

    THE LAST COLUMN IS THIS TASK: the internal arm no longer eliminates on the
    spot, and the corroboration tally no longer counts the author's own record
    (`Unit.Doubt`). Defeats fall from 16 to 6 and corroborated eliminations from
    12 to 0 — every one of those 12 had the author's own published challenge in
    the live set, so what read as a peer bearing out a doubt was a unit's record
    voting twice. Four doubts now end in silence where none did, which is the
    window doing the job it was built for and had never once been given.

    TWO TRUE LAWS ARE NOW PERMANENTLY LOST WHERE NONE WERE AT WINDOW 5 — the
    longer window is not free even on the metric this test exists to protect.
    A law given up by `retracted_internally` is one whose own author's record
    stayed against it for the whole window; the window's only job on that path
    is to give an inquiry more rounds to repair the record before the law goes,
    and at eight rounds two of the doubts opened simply outlast the repair
    without a peer ever supplying the missing head. This is the price named but
    left open in `corroboration_window`'s own docstring ("a longer window makes
    every unit do more work per doubt") showing up on a different meter: not
    more work, but two laws the five-round window would have kept.

    THE PRICE IN SCORE, at equal run length (60 rounds both arms): **+924 live
    against +1038 mute** — an 11% cost, materially unchanged from window 5's
    11%, against 24% for the ruling alone and 36% for the existential rule. The
    cost is what suspension is: a true law mute for the window forgoes the hits
    it would have won, and holding a doubt open longer rather than closing it
    early costs that many more rounds of licence. It loses at 8 of 8 seeds,
    asserted per-seed.

    AT WINDOW 5, the previous default, for comparison — this is the reading the
    ruling was made on and it is kept for that reason:

                                    existential  suspension  +open world  +inquiry
        raised                               58          58           60        60
        suspended                             —          28           60        60
        eliminated by corroboration           —          18           12         0
        retracted by internal re-assessment   —          38            4         4
        restored by rebuttal                  —           2           44        44
        restored by silence                   —           0            0        10
        ----------------------------------------------------------------------------
        distinct (unit, law) defeats         58          56           16         4
        **true laws still gone at the end**  34           2            0         0
        retraction events (thrash)          426          56           16         4
        net live / net mute             384/596     454/596     932/1038   922/1038

    At window 5 the last column read: defeats fall from 16 to 4 and corroborated
    eliminations from 12 to 0; ten doubts end in silence; no true law is
    permanently lost; the score cost is +922 live against +1038 mute, an 11%
    cost against 10% before that task.
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
        # KEPT UNDER THE RETIREMENT, like GATE 1's decomposition clause. This
        # compares two arms' net scores, which as a VERDICT the 2026-07-31 ruling
        # forbids — but its content is that the channel COSTS score while saving
        # the true laws the existential rule destroyed. It asserts the inversion,
        # it does not decide by it, and deleting it would remove the evidence.
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
    assert (raised_total, defeats, false_defeats) == (60, 6, 6)
    assert agg == {"suspended": 60, "internal": 6, "corroborated": 0,
                   "rebutted": 46, "silence": 4}
    # THE COMPARISON THIS TASK EXISTS FOR: 34 of 58 true laws permanently lost
    # under the existential rule, 2 under the ruling, 0 at window 5 once
    # `pending` is read open-world, and 2 again at window 8 (see the
    # docstring's "TWO TRUE LAWS ARE NOW PERMANENTLY LOST" finding).
    assert (lost_true, lost_false) == (2, 0)
    # One retraction event per defeat: induction and disposal have stopped
    # fighting (426 events for 98 defeats before).
    assert events_total == defeats == 6
    assert (live_total, mute_total) == (924, 1038)


def test_the_channel_still_kills_every_false_law_and_now_by_the_author_s_own_record():
    """IT DID NOT BECOME TOOTHLESS, and the teeth stayed inward.

    RE-MEASURED AT WINDOW 8 (the ruled default, 2026-07-31). Same eight seeds
    and rounds, each unit additionally seeded with the CONVERSE of its first
    domain's law — a law the field does not carry, so defeating it is a correct
    retraction. Measured after inquiry was put before elimination: **31 of 32
    converses defeated and permanently gone, the thirty-second still SUSPENDED
    when the run ended, 6 true laws defeated, 4 recovered and 2 permanently
    lost.** It was 32 of 32 with 16 recovered before the ruling, and 31 of 32
    with all 4 true laws recovered at window 5. The converse that survives is
    the same one as at window 5 and is still not an escape: at seed 42 the
    converse `g_head -> g_local` is first disputed at round 55 and suspended
    there, and the run stops at 59 with its eight-round window still open. It
    licenses nothing throughout — the arm asserts that rather than counting it
    as held.

    THE TWO LOST TRUE LAWS ARE SEED 1's, the same seed and the same finding as
    `test_suspension_saves_the_true_laws_the_existential_rule_destroyed`'s: a
    longer window gives an internal doubt more rounds to run, and at seed 1 two
    of those doubts outlast the eight rounds without a peer supplying the
    missing head. This is not a new mechanism — it is the same trade read from
    the false-law test's side of the board.

    EVERY ONE OF THE 31 DIES BY INTERNAL RE-ASSESSMENT — not one needed a peer,
    exactly as before, and now every one of them waits out the window first. A
    converse's individuals are refuting and stay refuting: `a_head -> a_local`
    leaves individuals pending whose bodies the unit has held for many rounds,
    so eight rounds of inquiry change nothing about it, and nothing arrives to
    save it. That is what a delay before elimination is supposed to do to a
    false law — cost time, not bite.

    THE ARITHMETIC OF THE TRADE. The mute arm pays **77** for holding those
    converses (+1038 to +961); the live arm is **+924**, so the benefit is 77
    and the cost is 961 − 924 = **37**, against 39 at window 5, 29 two tasks
    before, 142 for the ruling alone and 212 for the existential rule. The two
    lost true laws show up here too: the live arm no longer matches the mute
    arm seed by seed as it did at window 5, because seed 1 now loses a true law
    and forgoes the hits it would have earned, while the mute arm — which
    disposes of nothing, channel or no, since `dispose_challenges` only runs
    `if channel` — keeps holding it, so the identity that held at window 5
    does not hold at window 8.

    AT WINDOW 5, the previous default, for comparison — this is the reading the
    ruling was made on and it is kept for that reason: 31 of 32 converses
    defeated, the thirty-second still SUSPENDED at the run's end; 4 true laws
    defeated and all 4 recovered, none permanently lost; every one of the 31
    false-law defeats by internal re-assessment; live and mute arms identical
    at **+922 both**, so the whole 77-point benefit
    of holding the converses cost only 1038 − 922 = **39** — the delay costing
    ten of the seventy-seven and buying the true laws their inquiry, with no
    loss of a true law to weigh against it.
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
        survivors = [(u.unit_id, law) for u in live for law in u.laws
                     if law not in planted]
        assert correct_here + len(survivors) == 4, (
            f"seed {seed}: {correct_here} of 4 wrong laws defeated, "
            f"{len(survivors)} still held")
        # A converse that outlived the run is one still under inquiry, and it
        # licenses nothing while it is.
        assert all(law in unit.suspended for uid, law in survivors
                   for unit in live if unit.unit_id == uid), (
            f"seed {seed}: a converse stands ACTIVE at the end — {survivors}")
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
    assert correct == 31
    # THE AMENDMENT'S QUESTION: which arm does the discriminating work?
    assert (internal_false, corroborated_false) == (31, 0)
    assert (recovered_true, lost_true) == (4, 2)
    assert (live_total, mute_total) == (924, 961)


def test_under_bounded_attention_the_discrimination_still_inverts_and_now_internally():
    """THE NEGATIVE RESULT THAT SURVIVED THE RULING, AND SURVIVES ITS UNIFORM
    APPLICATION TOO. Reported, not tuned away.

    Bounded attention (each unit attends half the rounds), both the planted laws
    and the converses seeded, no induction — so the same twelve laws per seed are
    held in both arms and the only variable is the challenge channel. NO ASK
    CHANNEL RUNS HERE, which is the point of the arm and, as it turns out, the
    whole explanation. Measured over eight seeds: **64 of 64 true laws defeated
    and permanently gone, 2 of 32 false ones (6%)** — thirty converses survive
    while every true law dies. Those are the same counts the existential rule
    produced, and the same the open-world reading produced.

    WHAT THIS TASK CHANGED HERE IS THE ROUTE, NOT THE OUTCOME. Before it, the
    internal arm eliminated on the spot and the external apparatus ran zero
    times: **0 suspended, 0 calls published**, 66 internal retractions at a
    median of round 0. Now **all 66 doubts are suspended, all 66 calls are
    published, 248 questions go out** (re-measured 2026-08-04 by the channel
    audit, `RUN_C_AUDIT_LOG.md` §6 — "159" was the window-5 count, narrated
    past the window-8 ruling of 2026-07-31 and never carried forward), every
    doubt runs its full five-round window — and all 66 end in retraction
    anyway, because nothing arrives to repair the record. The apparatus is no
    longer dead code. It is a channel with nothing coming down it.

    THAT IS THE FINDING, AND IT IS EXACT: an inquiry with no answering channel is
    a delay, not an inquiry. Every one of the 66 refusals fails on `min_support`
    — a law SEEDED into a unit with no record has no supporting individual, and
    under half attention its consequents keep arriving on the rounds it sleeps
    through, so five rounds of waiting add no support. The corroboration arm now
    contributes **nothing at all** (0 eliminations, against 32 when the author's
    own published challenge was still allowed to count as a second voice, and 64
    when it could also take the challenger's slot): under the CYCLIC aperture
    scheme a law has at most two holders and at most two disputants, so a genuine
    second foreign record never exists.

    THAT LAST CLAUSE WAS TESTED RATHER THAN LEFT STANDING, and it held — the
    field was what failed the rule, not the rule. Given six units at distinct
    2-domain apertures, every domain reaches three witnesses and corroboration
    fires 45 times in 144 doubts on this very arm
    (`test_corroboration_fires_once_a_domain_has_three_witnesses`). It buys
    nothing: 96 of 96 true laws still go, and 48 of 48 converses with them.

    WHAT ANSWERS IT IS THE ASK CHANNEL, measured in the gate below: with peers
    able to tell each other what they saw, 28 of these 64 true laws survive.

    AND THE NET SCORE IMPROVES ANYWAY: −433 live against −1421 mute, identical to
    every previous rule's figures. That is still the trap. Under bounded attention
    a true law cannot pay — its consequents arrive on rounds nobody is watching —
    so destroying it removes losing bets and the arm moves toward abstention. **A
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
    # EVERY defeat is internal, and every one of them now waits out a full
    # inquiry first: 66 suspensions and 66 published calls where there were
    # none, and not one of them changes a law's fate, because no channel is
    # carrying anything back.
    assert (internal, external, suspended, calls) == (66, 0, 66, 66)
    # KEPT UNDER THE RETIREMENT, and this is the sharpest instance of why the
    # statistic was retired: the score improves while `true_held` above reads 0
    # of 64. The clause asserts that inversion; it decides nothing by it. The
    # exact figures are pinned on the next line.
    assert live_total > mute_total
    assert (live_total, mute_total) == (-433, -1421)


def _witness_arm(n_units, scheme, witnesses=None):
    """The bounded-attention arm Task 5e measured corroboration at 0 of 66 in,
    run over a named community. Returns the aggregate over the eight seeds.

    WHAT `agg["corroborated"]` COUNTS, since the gates below read it as the
    corroboration lifecycle firing: `dispose_challenges` counting DISTINCT
    FOREIGN AUTHORS of challenge marks (`src/c_unit.py:1764`). It does not come
    from `Unit.corroborate`, which is declared silent on `_play_challenge`
    above and mints nothing in any arm — the audit's **D-A1**. The numbers are
    right; nothing here was solicited and answered."""
    agg = {k: 0 for k in ("suspended", "internal", "corroborated", "rebutted",
                          "silence", "asked")}
    agg.update(raised=0, calls=0, true_defeats=0, true_held=0,
               false_defeats=0, false_held=0, net_live=0, net_mute=0)
    for seed in C_SEEDS:
        spec, live, board, raised, events, tally = _play_challenge(
            seed, C_ROUNDS, channel=True, stagger=2, seed_laws=True,
            wrong_laws=True, induce=False, n_units=n_units, scheme=scheme,
            witnesses=witnesses)
        _s, mute, _b, _r, _e, _t = _play_challenge(
            seed, C_ROUNDS, channel=False, stagger=2, seed_laws=True,
            wrong_laws=True, induce=False, n_units=n_units, scheme=scheme,
            witnesses=witnesses)
        planted = {d.law for d in spec.domains}
        distinct = {(uid, law) for uid, law, _why in events}
        for k in ("suspended", "internal", "corroborated", "rebutted",
                  "silence", "asked"):
            agg[k] += tally[k]
        agg["raised"] += raised
        agg["calls"] += len(board.corroboration_calls())
        agg["true_defeats"] += sum(1 for _u, law in distinct if law in planted)
        agg["false_defeats"] += sum(1 for _u, law in distinct
                                    if law not in planted)
        agg["true_held"] += sum(1 for u in live for law in u.laws
                                if law in planted)
        agg["false_held"] += sum(1 for u in live for law in u.laws
                                 if law not in planted)
        agg["net_live"] += sum(u.ledger.net_score for u in live)
        agg["net_mute"] += sum(u.ledger.net_score for u in mute)
    return agg


def test_corroboration_fires_once_a_domain_has_three_witnesses():
    """**P-F1 HELD IN ITS MECHANISM AND REFUTED IN ITS ATTRIBUTION**, and the
    refutation is the more useful half. The prediction, recorded before the run:

    > Elimination-by-corroboration fires at a six-unit / four-domain community
    > and fires ZERO times at four units, because three witnesses per domain is
    > the threshold and four units cannot reach it. The transition is a
    > structural property of the community's SIZE, not of the disposition rule.

    Eight seeds, 60 rounds, bounded attention, planted laws AND converses seeded,
    no induction, no ask channel — the arm Task 5e measured corroboration at 0 of
    66 in:

        arm                witnesses  raised  susp  CORROB  window  true lost
        4 units cyclic     2 2 2 2        96    66       0      66      64/64
        4 units PAIRS      3 2 2 1        88    80       4      76      56/64
        6 units pairs      3 3 3 3       160   144      45      99      96/96
        6 units pairs w=3  3 3 3 3       160   144       0     144      96/96

    THE FIRST CLAUSE HOLDS: 45 corroborations at six units against 0 at four
    under the cyclic scheme, which is what the whole task was built to produce.

    THE SECOND CLAUSE IS WRONG. Corroboration fires **four times at FOUR units**
    once those four units take distinct 2-domain apertures, because the truncated
    pairs community is lopsided — alpha 3, beta 2, gamma 2, delta 1 — and alpha's
    three witnesses are enough. So the controlling variable is WITNESSES PER
    DOMAIN, not community size; six units is merely the smallest community in
    which EVERY domain reaches three. That is why `apertures_for` refuses on
    `min_witnesses` rather than on a unit count.

    THE STRICTER READING IS UNREACHABLE IN THIS FIELD, not merely stricter. At
    `corroborating_witnesses = 3` the six-unit community reads 0 of 144 — the
    same as the cyclic four-unit arm — because three witnesses per domain means
    holder + challenger + one corroborator and a third foreign record cannot
    exist. Moving the author's line to three costs a fifth domain.

    **P-F2 HELD.** Corroboration goes 0 → 4 → 45 while true laws still held goes
    0 → 8 → **0**: at six units the channel destroys 96 of 96 true laws and 48 of
    48 converses, and the live net is exactly **0** because no unit ever gets to
    place a bet. Forty-five corroborations bought nothing; they finished the job
    the window was already doing. A channel that repairs whatever it is asked
    about cannot tell a true law from a false one, and neither can one that
    eliminates whatever two records dispute.

    WHAT "CORROBORATION FIRES" MEANS HERE, AND IT IS NOT WHAT IT SOUNDS LIKE
    (the channel audit, `runs/RUN_C_AUDIT_LOG.md` §1). Every figure above is
    reproduced and every one is right, but not one of them came from
    `Unit.corroborate`, which mints nothing in any arm this series ever ran —
    the audit's **D-A1**, and the reason `_play_challenge` declares it silent.
    `CORROB` is `dispose_challenges` counting DISTINCT FOREIGN AUTHORS of
    challenge marks. So the finding survives read as *a law is eliminated once
    two distinct foreign records have independently published a counterexample
    to it*, and does NOT survive read as a call SOLICITED and ANSWERED: the
    units counted as corroborators had published their counterexamples a phase
    earlier and would have published them identically had no call ever existed.
    The guard cannot carry this one — an allowlisted channel is exactly the
    channel it cannot speak for — so it is said here, in place.
    """
    cyclic4 = _witness_arm(4, CYCLIC)
    pairs4 = _witness_arm(4, PAIRS)
    pairs6 = _witness_arm(6, PAIRS)
    strict6 = _witness_arm(6, PAIRS, witnesses=3)

    # P-F1, first clause: it fires at six units, and not at all under cyclic.
    assert cyclic4["corroborated"] == 0
    assert pairs6["corroborated"] == 45
    # P-F1, second clause: REFUTED. Four units corroborate when one domain
    # reaches three witnesses.
    assert pairs4["corroborated"] == 4
    # The stricter bar is unreachable at three witnesses per domain.
    assert strict6["corroborated"] == 0
    assert strict6["internal"] == strict6["suspended"] == 144

    assert (cyclic4["raised"], cyclic4["suspended"], cyclic4["calls"]) == (96, 66, 66)
    assert (pairs4["raised"], pairs4["suspended"], pairs4["calls"]) == (88, 80, 80)
    assert (pairs6["raised"], pairs6["suspended"], pairs6["calls"]) == (160, 144, 144)
    # The three exits, and the window carries what corroboration does not.
    assert (cyclic4["internal"], cyclic4["rebutted"], cyclic4["silence"]) == (66, 0, 0)
    assert (pairs4["internal"], pairs4["rebutted"], pairs4["silence"]) == (76, 0, 0)
    assert (pairs6["internal"], pairs6["rebutted"], pairs6["silence"]) == (99, 0, 0)

    # P-F2: corroboration starts firing and true-law survival does not improve.
    assert (cyclic4["true_defeats"], cyclic4["true_held"]) == (64, 0)
    assert (pairs4["true_defeats"], pairs4["true_held"]) == (56, 8)
    assert (pairs6["true_defeats"], pairs6["true_held"]) == (96, 0)
    assert (cyclic4["false_defeats"], cyclic4["false_held"]) == (2, 30)
    assert (pairs4["false_defeats"], pairs4["false_held"]) == (24, 8)
    assert (pairs6["false_defeats"], pairs6["false_held"]) == (48, 0)
    # At six units nothing survives to bet, so the live arm's net is exactly 0.
    assert (cyclic4["net_live"], cyclic4["net_mute"]) == (-433, -1421)
    assert (pairs4["net_live"], pairs4["net_mute"]) == (-247, -1409)
    assert (pairs6["net_live"], pairs6["net_mute"]) == (0, -2122)


def test_on_the_induce_arm_corroboration_buys_churn():
    """THE THIRD ARM, AND THE ONE WHERE CORROBORATION'S ONLY MEASURABLE EFFECT IS
    THRASH. Eight seeds, 60 rounds, units inducing from what they meet, the
    challenge channel live — the arm where the previous four rules were compared.

    RE-MEASURED AT WINDOW 8 (the ruled default, 2026-07-31):

        arm                raised  susp  CORROB  internal  rebutted  silence  defeats  true lost   net live/mute
        4 units cyclic         60    60       0         6        46        4        6          2     924 / 1038
        4 units PAIRS          51    51       6         2        41        0        8          0     923 / 1033
        6 units pairs          90    90      24         0        66        0       24          0    1398 / 1557
        6 units pairs w=3      90    90       0         9        69        6        9          3    1386 / 1557

    (The four-unit cyclic row is Task 5e's, reproduced digit for digit; it is
    asserted in `test_suspension_saves_the_true_laws_the_existential_rule_destroyed`
    and is repeated here only as the column to read the others against — its
    window-8 reading is 924/1038 with 6 internal and 2 true laws permanently
    lost, exactly as that test now reports.)

    TWENTY-FOUR DEFEATS AND NOT ONE PERMANENT LOSS still holds at six units with
    the looser bar (`witnesses` left at the field's own default): every law
    corroboration eliminates there is induced again from the record that still
    supports it, so the retraction event happens and the law comes back. The
    internal arm still goes fully silent at that bar (0 internal retractions, 0
    restorations by silence) because corroboration closes every doubt before the
    window can act.

    THE STRICTER BAR NO LONGER READS LIKE THE SMALL COMMUNITY: at witnesses=3,
    corroboration still never fires (0), but the longer window turns 6 internal
    retractions into 9 and 15 silences into 6 — the same trade the window's own
    docstring names, more rounds for an internal doubt to run before it is
    forced to a verdict. THREE TRUE LAWS ARE NOW PERMANENTLY LOST AT THIS BAR
    WHERE NONE WERE AT WINDOW 5 — the same mechanism as the four-unit cyclic
    arm's two, showing up again wherever a doubt is settled by this unit's own
    record rather than a peer's: eight rounds is long enough for some of those
    doubts to outlast the repair.

    SO THE CLAIM NARROWS: it is not that nothing is bought at any bar — it is
    that corroboration itself still buys nothing (0 permanent loss from a
    corroborated elimination in every arm measured, at either bar) while the
    window it now shares the arm with has its own separately-measured price.
    The channel's cost is unchanged in direction and materially unchanged in
    size: 10.98% at both four units (cyclic) and six units (the stricter bar) —
    the same figure at both community sizes, which was also true at window 5
    (11.18% at both). Corroboration produced churn, exactly as before; the
    window is what now also occasionally costs a law.

    AT WINDOW 5, the previous default, for comparison — this is the reading the
    ruling was made on and it is kept for that reason:

        arm                raised  susp  CORROB  internal  rebutted  silence  defeats  true lost   net live/mute
        4 units cyclic         60    60       0         4        44       10        4          0     922 / 1038
        4 units PAIRS          51    51       6         2        39        4        8          0     919 / 1033
        6 units pairs          90    90      24         0        66        0       24          0    1398 / 1557
        6 units pairs w=3      90    90       0         6        66       15        6          0    1383 / 1557

    At window 5, TWENTY-FOUR DEFEATS AND NOT ONE PERMANENT LOSS read for the
    loose bar exactly as at window 8. The stricter bar read like the small
    community again: 0 corroborations, the window doing the work, six defeats,
    and NOTHING BOUGHT AND LITTLE SPENT — permanent true-law loss 0 in all four
    arms, cost 10.2% at six units against 11.2% at four (this file's original
    rounding; the precise figure, recomputed here, is 11.18% at both)."""
    six = _witness_induce_arm(6, PAIRS)
    strict = _witness_induce_arm(6, PAIRS, witnesses=3)
    assert (six["raised"], six["suspended"], six["corroborated"]) == (90, 90, 24)
    assert (six["internal"], six["rebutted"], six["silence"]) == (0, 66, 0)
    assert (six["defeats"], six["lost_true"]) == (24, 0)
    assert (six["net_live"], six["net_mute"]) == (1398, 1557)
    assert (strict["corroborated"], strict["internal"],
            strict["silence"]) == (0, 9, 6)
    assert (strict["defeats"], strict["lost_true"]) == (9, 3)
    assert (strict["net_live"], strict["net_mute"]) == (1386, 1557)


def _witness_induce_arm(n_units, scheme, witnesses=None):
    agg = {k: 0 for k in ("suspended", "internal", "corroborated", "rebutted",
                          "silence")}
    agg.update(raised=0, defeats=0, lost_true=0, net_live=0, net_mute=0)
    for seed in C_SEEDS:
        spec, live, _board, raised, events, tally = _play_challenge(
            seed, C_ROUNDS, channel=True, n_units=n_units, scheme=scheme,
            witnesses=witnesses)
        _s, mute, _b, _r, _e, _t = _play_challenge(
            seed, C_ROUNDS, channel=False, n_units=n_units, scheme=scheme,
            witnesses=witnesses)
        planted = {d.law for d in spec.domains}
        distinct = {(uid, law) for uid, law, _why in events}
        held = {(u.unit_id, law) for u in live for law in u.laws}
        for k in ("suspended", "internal", "corroborated", "rebutted", "silence"):
            agg[k] += tally[k]
        agg["raised"] += raised
        agg["defeats"] += len(distinct)
        agg["lost_true"] += sum(1 for _u, law in distinct - held
                                if law in planted)
        agg["net_live"] += sum(u.ledger.net_score for u in live)
        agg["net_mute"] += sum(u.ledger.net_score for u in mute)
    return agg


# --- can the community repair what the field withheld? ------------------------
#
# THE ONE THING NEITHER THE RULING NOR THE OPEN-WORLD READING CAN FIX is a
# consequent that never reached this membrane at all: after the lag it is
# indistinguishable from a refutation, and no amount of care with this unit's own
# record recovers it. But a peer whose aperture overlaps may have been looking
# when it arrived, and the ask channel already exists. The driver below runs the
# ask channel and the challenge channel together so the question can be put.


# `corroborate` IS DECLARED SILENT FOR THE SAME REASON AND ON THE SAME TERMS as
# on `_play_challenge` above — **D-A1** in `runs/RUN_C_AUDIT_LOG.md`, the shared
# `_mint_challenge` key, with this harness running `challenge` at phase (f)
# before `corroborate` at phase (g). Zero mints on 1920–2880 calls in TWELVE of
# the thirteen full-community arms, `tests/test_c_speaker_variance.py`'s three
# included; the thirteenth is K3 (`ask=False, mute=True`), which makes zero
# calls on every channel and so shows nothing either way. Deferred to `src/` by
# the spec's §9. THIS DECLARATION IS TO BE REMOVED WHEN D-A1 IS FIXED, and
# `test_the_corroborate_declarations_still_have_something_to_declare`, in
# `tests/test_c_channel_probe.py`, is what will say when.
@audited(expect_silent=("corroborate",))
def _play_ask_and_challenge(seed, rounds, *, ask, stagger=2, n_units=4,
                            scheme=CYCLIC, window=None, witnesses=None,
                            typify=None, rep_window=None, mute=False,
                            liars=()):
    """A community of `n_units`, planted laws AND converses seeded, no
    induction, bounded attention. `ask` switches the ask/answer/adopt channel on
    and off; the challenge channel runs in both arms, so the only variable is
    whether peers can tell each other what they saw.

    `mute` IS THE STAGE-3 GATE'S TWIN AND IT IS A DIFFERENT ARM FROM `ask=False`.
    Every table written before Task 7 calls `ask=False` "mute", and it means the
    ASK channel is mute: those units still publish, still challenge, still
    corroborate and still dispose. `mute=True` silences all four channels — no
    mark of any kind is minted, read or disposed of, so each unit runs the field
    alone with the laws it was seeded with. It requires `ask=False`, because a
    community that cannot publish cannot answer either.

    UPTAKE IS TARGETED, exactly as in the ask channel's own measurement above: a
    unit adopts a fact mark ONLY when it answers a question that unit itself
    asked. Task 3 measured indiscriminate uptake and found it worse than silence.

    `typify` IS THIS TASK'S VARIABLE, and it has three settings.

    - `None` — untargeted, the control: whatever comes back is taken up. Every
      figure this arm produces reproduces Tasks 5e and 5f digit for digit.
    - `"prefer"` — the typified arm, and the literal reading of `whom_to_ask`: a
      unit that has earned a preference about the relation takes up only that
      peer's reply, and a unit with no preference does what it always did.
    - `"distrust"` — the stronger reading, present as a CONTROL rather than as a
      proposal: a unit with no preference additionally refuses a reply from a
      peer whose testimony about that relation has already failed. It exists
      because `"prefer"` alone cannot show whether the preference machinery is
      inert or merely never exercised, and Task 5f's lesson is that a comparison
      which obviously holds needs the arm that could show it does not.

    THE PREFERENCE BITES AT UPTAKE, NOT AT PUBLICATION, and that is a limitation
    of the board rather than a design choice: a question is published to
    everyone, so there is no addressee to narrow. What a unit can do is decide
    whose answer to take, which is the same choice one step later.

    `n_units` / `scheme` / `window` / `witnesses` are the community and the two
    disposition knobs, exactly as in `_play_challenge`; `rep_window` is the
    replication window each unit waits before reading silence as a failure.
    """
    if mute and ask:
        raise ValueError(
            "mute=True silences publication, so there is nothing for the ask "
            "channel to answer from: pass ask=False with it")
    # `liars` IS EXAMINATION VII's RULING MADE AVAILABLE HERE: (unit_id,
    # ObserverNoise) pairs, so one unit's OBSERVATION of its domains can
    # differ from its neighbours'. Empty by default, and an unnamed unit
    # reads the domain stream unchanged, so every figure this driver
    # produced before the argument existed reproduces exactly.
    spec = default_spec(seed=seed)
    if liars:
        spec = dataclasses.replace(spec, observers=tuple(liars))
    field = Field(spec)
    aps = apertures_for(spec, n_units=n_units, scheme=scheme)
    planted = {d.name: d.law for d in spec.domains}
    units, mine = [], {}
    for i in range(n_units):
        laws = {planted[n] for n in aps[i].domains}
        body, head = planted[aps[i].domains[0]]
        mine[f"u{i}"] = (frozenset(laws), (head, body))
        u = Unit(f"u{i}", aps[i], laws=laws | {(head, body)})
        if window is not None:
            u.corroboration_window = window
        if witnesses is not None:
            u.corroborating_witnesses = witnesses
        if rep_window is not None:
            u.replication_window = rep_window
        units.append(u)
    _assert_uniform_rate(units)
    # `mute` short-circuits the round at (e), so it skips publish, challenge,
    # corroborate, dispose AND settle_credit; it also forbids `ask`, so a mute
    # arm plays nothing at all and says so.
    declares(*(("adopt", "ask", "answer", "settle_credit") if ask else ()),
             *(() if mute else ("publish", "challenge", "corroborate",
                                "dispose_challenges")))
    board = MarkBoard()
    asked = {u.unit_id: [] for u in units}
    settled = {u.unit_id: set() for u in units}
    questions = uptakes = 0
    # WAS THERE EVER A CHOICE? `occ_pref` counts the uptake decisions at which a
    # unit actually held a preference about the relation, `occ_bite` the ones at
    # which that preference named somebody OTHER than the unit answering, and
    # `suppliers` how many distinct peers ever answered a given unit about a
    # given relation. A preference that never disagrees with the only voice
    # available is a preference that decides nothing.
    suppliers = {u.unit_id: {} for u in units}
    occ_pref = occ_bite = 0
    refused = set()
    adopted = []
    # GATE 2'S TWO MATRICES. `put` is every question actually published, asker
    # and content, including the ones a disposal's inquiry publishes; `consult`
    # is who ended up taking whose word, counted on uptake because a question
    # has no addressee — the board carries it to everyone, so the only place a
    # unit expresses whom it consults is which reply it takes.
    put = []
    consult = Counter()
    # HOW MANY VOICES STOOD BEHIND THE CONTENT AT THE MOMENT OF CHOICE. `said`
    # is every fact content on the board and who has said it, accumulated from
    # what each act actually minted rather than re-scanned per decision (a board
    # scan per reply is quadratic in the run). It is read at phase (a), so it
    # holds exactly what was published through round r−1 — which is what an
    # asker deciding at round r could have chosen between.
    said = {}
    voices, voices_by_rel = Counter(), Counter()
    independent = relayed = twin = choice_lowest = 0
    pref_choice = pref_choice_bite = 0
    by_id = {u.unit_id: u for u in units}
    exits = {k: 0 for k in ("suspended", "internal", "corroborated",
                            "rebutted", "silence")}

    for r in range(rounds):
        if ask:                                             # (a) adopt replies
            for u in units:
                for q in asked[u.unit_id]:
                    if q.content in settled[u.unit_id]:
                        continue
                    reply = board.answer_to(q)
                    if reply is None or reply.author == u.unit_id:
                        continue
                    relation = reply.content[0]
                    speakers = said.get(reply.content, set()) - {u.unit_id}
                    if typify is not None:
                        preferred = u.whom_to_ask(relation)
                        if preferred is not None:
                            occ_pref += 1
                            occ_bite += reply.author != preferred
                            # THE DECISIVE INTERSECTION for gate 2: not "was a
                            # preference held" but "was one held WHERE a choice
                            # existed", which is the only place it could decide
                            # anything.
                            if len(speakers) > 1:
                                pref_choice += 1
                                pref_choice_bite += reply.author != preferred
                            take = reply.author == preferred
                        elif typify == "distrust":
                            take = u.standing_with(reply.author, relation) >= 0
                        else:
                            take = True
                        if not take:
                            refused.add((u.unit_id, q.content))
                            continue
                    settled[u.unit_id].add(q.content)
                    took = u.adopt(reply, board, r)
                    uptakes += took
                    if took:
                        adopted.append(reply.content)
                        consult[(u.unit_id, reply.author)] += 1
                        # COUNTED ONLY WHEN SOMETHING WAS ACTUALLY TOLD. A reply
                        # whose content the asker already held is not a second
                        # voice about that relation — it is the same fact
                        # arriving twice — and counting it would report choices
                        # nobody had.
                        suppliers[u.unit_id].setdefault(relation, set()).add(
                            reply.author)
                        # THE SAME DISCIPLINE APPLIED TO THE CHOICE ITSELF. A
                        # first cut counted the voices at every decision and read
                        # 13 gamma-relation choices at six units; every one was a
                        # reply whose content the asker's own membrane had
                        # delivered in the meantime, so nothing was chosen and
                        # nothing was told. Counted on fresh uptake, gamma drops
                        # out entirely — which is what the aperture layout says
                        # should happen, since all three gamma witnesses attend
                        # the same rounds and hold the same gamma facts.
                        voices[len(speakers)] += 1
                        voices_by_rel[(relation, len(speakers))] += 1
                        # WHERE A SECOND VOICE COMES FROM. A unit publishes
                        # everything it holds, adopted testimony included, so a
                        # peer can stand behind an atom it never met. Split the
                        # decisions that offered a choice into the ones where
                        # every voice had met the atom first-hand by that round
                        # and the ones where at least one was relaying what it
                        # had itself been told.
                        if len(speakers) > 1:
                            # WHICH OF THE AVAILABLE VOICES ANSWERED. `answer_to`
                            # returns the first mark published and every phase
                            # walks the units in order, so the claim to check is
                            # that the lowest-numbered voice answers every time —
                            # measured rather than argued, because a peer that
                            # met the atom earlier could in principle have got
                            # there first.
                            choice_lowest += reply.author == min(speakers)
                            met = [by_id[a].first_seen.get(reply.content)
                                   for a in speakers]
                            if all(w is not None and w <= r for w in met):
                                independent += 1
                                # AND WHETHER THE TWO VOICES ARE TWINS. Peers
                                # that met the atom on the SAME round witness
                                # its domain on the same attendance phase, so
                                # they hold the same facts about it and differ
                                # only in name.
                                if len(set(met)) == 1:
                                    twin += 1
                            else:
                                relayed += 1
        for i, u in enumerate(units):                       # (b) attend
            if stagger == 1 or r % stagger == i % stagger:
                u.step(field, r, induce=False)
        if ask:
            for u in units:                                 # (c) ask
                mark = u.ask(board, r)
                if mark is not None:
                    asked[u.unit_id].append(mark)
                    put.append((u.unit_id, mark.content))
                    questions += 1
            for u in units:                                 # (d) answer
                for m in u.answer(board, r):
                    said.setdefault(m.content, set()).add(m.author)
        if mute:
            continue
        for u in units:                                     # (e) publish
            for m in u.publish(board, r):
                if m.kind == FACT:
                    said.setdefault(m.content, set()).add(m.author)
        for u in units:                                     # (f) challenge
            u.challenge(board, r)
        for u in units:                                     # (g) corroborate
            for m in u.corroborate(board, r):
                if m.kind == FACT:
                    said.setdefault(m.content, set()).add(m.author)
        for u in units:                                     # (h) dispose
            out = u.dispose_challenges(board, r)
            exits["suspended"] += len(out.suspended)
            exits["internal"] += len(out.retracted_internally)
            exits["corroborated"] += len(out.retracted_by_corroboration)
            exits["rebutted"] += len(out.restored_by_rebuttal)
            exits["silence"] += len(out.restored_by_silence)
            # THE INQUIRY'S OWN QUESTIONS. A disposal may publish one, and the
            # asker has to be able to take up its own answer — uptake here is
            # targeted, so a question no driver watches is a question wasted.
            # Registered only in the ask arm, so the variable stays the channel.
            if ask:
                for mark in out.asked:
                    asked[u.unit_id].append(mark)
                    put.append((u.unit_id, mark.content))
                    questions += 1
        if ask:                                             # (i) settle credit
            # RUN IN EVERY ASK ARM, INCLUDING THE UNTARGETED CONTROL. Nothing
            # reads `peers` unless `typify` is set, so the control's figures are
            # unmoved; what it buys is the credit distribution measured in the
            # arm that does not act on it.
            for u in units:
                u.settle_credit(r)

    # WHAT WAS TAKEN UP, SPLIT BY WHETHER THE FIELD EVER LICENSED IT. A head
    # atom outside `licensed_heads` had no antecedent at any round, so only
    # `spurious_rate` could have produced it — that is P-G1's category, read
    # modeler-side because no unit could read it.
    heads = {d.law[1]: field.licensed_heads(d.name, rounds) for d in spec.domains}
    licensed = sum(1 for c in adopted if c[0] in heads and c in heads[c[0]])
    fabricated = sum(1 for c in adopted
                     if c[0] in heads and c not in heads[c[0]])
    proved = sum(1 for u in units for f in u._credited if f in u.first_seen)
    failed = sum(1 for u in units for f in u._credited if f not in u.first_seen)
    preferences = sum(
        1 for u in units
        for rel in {r for s in u.peers.values() for r in s}
        if u.whom_to_ask(rel) is not None)
    scores = [p - f for u in units for by_rel in u.peers.values()
              for (p, f) in by_rel.values()]

    # THE LOOSE READING, KEPT ONLY SO THE TIGHT ONE CAN BE READ AGAINST IT.
    # `could` asks how many peers ever held the asked atom first-hand, counted
    # at the END of the run; since a record only grows, that credits a peer who
    # met the atom forty rounds after the question closed. It over-reads, and
    # `voices` — counted from the board at the round the asker actually decided
    # — is the number reported.
    firsthand = {u.unit_id: set(u.first_seen) for u in units}
    could = Counter()
    for asker, content in put:
        could[sum(1 for u in units
                  if u.unit_id != asker and content in firsthand[u.unit_id])] += 1
    prefs = Counter()
    for u in units:
        for rel in sorted({r for by_rel in u.peers.values() for r in by_rel}):
            who = u.whom_to_ask(rel)
            if who is not None:
                prefs[(u.unit_id, who)] += 1

    tally = dict(true_ref=0, conv_ref=0, true_lost=0, conv_lost=0,
                 repairable=0, unrepairable=0, questions=questions,
                 uptakes=uptakes, net=sum(u.ledger.net_score for u in units),
                 adopted_licensed=licensed, adopted_fabricated=fabricated,
                 adopted_body=len(adopted) - licensed - fabricated,
                 proved=proved, failed=failed,
                 pending=sum(len(u._supplied_by) - len(u._credited)
                             for u in units),
                 preferences=preferences, occ_pref=occ_pref, occ_bite=occ_bite,
                 refused=len(refused),
                 score_pos=sum(1 for s in scores if s > 0),
                 score_neg=sum(1 for s in scores if s < 0),
                 score_zero=sum(1 for s in scores if s == 0),
                 one_supplier=sum(1 for s in suppliers.values()
                                  for v in s.values() if len(v) == 1),
                 many_suppliers=sum(1 for s in suppliers.values()
                                    for v in s.values() if len(v) > 1),
                 # GATE 1'S COMPANIONS: what the score is made of, so a zero
                 # from silence and a zero from balanced betting cannot look
                 # alike. `bets` excludes abstentions, which the membrane never
                 # punishes.
                 hits=sum(u.ledger.hits for u in units),
                 misses=sum(u.ledger.misses for u in units),
                 abstain=sum(u.ledger.abstentions for u in units),
                 true_total=0, conv_total=0, true_susp=0, conv_susp=0,
                 independent=independent, relayed=relayed, twin=twin,
                 choice_lowest=choice_lowest,
                 pref_choice=pref_choice, pref_choice_bite=pref_choice_bite,
                 consult=consult, prefs=prefs, could=could,
                 voices=voices, voices_by_rel=voices_by_rel,
                 **exits)
    tally["bets"] = tally["hits"] + tally["misses"]
    tally["units"] = units          # for per-peer inspection; not aggregated
    for u in units:
        laws, conv = mine[u.unit_id]
        for body, head in sorted(laws):
            _c, refuting, _unk = u._pending_split(body, head, rounds - 1)
            tally["true_ref"] += len(refuting)
            tally["true_total"] += 1
            tally["true_lost"] += (body, head) not in u.laws
            # A SUSPENDED LAW IS STILL HELD AND LICENSES NOTHING, so "held at
            # the end" is reported beside it rather than instead of it.
            tally["true_susp"] += (body, head) in u.suspended
            for args in refuting:
                held = any((head, args) in p.facts for p in units if p is not u)
                tally["repairable" if held else "unrepairable"] += 1
        _c, refuting, _unk = u._pending_split(conv[0], conv[1], rounds - 1)
        tally["conv_ref"] += len(refuting)
        tally["conv_total"] += 1
        tally["conv_lost"] += conv not in u.laws
        tally["conv_susp"] += conv in u.suspended
    return tally


def test_peer_testimony_repairs_the_true_law_once_the_law_survives_to_ask():
    """P-C1 RE-TESTED AND NOW HELD; P-C2 RE-TESTED AND REFUTED AGAIN, backwards
    for the second time. The predictions are the ones recorded before the
    previous run, re-run unchanged.

    **P-C1:** with the ask channel live, a unit's refuting count on a TRUE law is
    lower than with the channel muted, because peer-supplied facts fill heads the
    field withheld from this unit. **P-C2:** the same channel does NOT materially
    lower the refuting count on a FALSE law, because no peer holds the missing
    head either.

    THE MEASUREMENT — eight seeds, 60 rounds, four units under bounded attention,
    planted laws and converses seeded, the challenge channel live in both arms.

    RE-MEASURED AT WINDOW 8 (the ruled default, 2026-07-31). The "live (was)" and
    "live (window 5)" columns are the previous readings, kept for the chain:

                              muted   live (was)  live (window 5)  live (window 8)
        refuting, true laws     640          636              349               220
        refuting, converses     321           42               20                21
        true laws lost        64/64        64/64            36/64             20/64
        converses lost         2/32         2/32             0/32              0/32
        net score              −433          −39             −106              −185
        questions / uptakes     0/0      480/448          1024/939          1258/1151

    **P-C1 IS STILL HELD, AND MORE STRONGLY.** The refuting count on true laws
    now falls 65.6% (640 → 220, against 45.5% at window 5), and 44 of the 64 true
    laws permanently lost in the muted arm now survive the run (against 28 at
    window 5). The mechanism is the same one window 5 showed: nothing about the
    ask channel changed, a law simply lives longer, so it has more rounds in
    which testimony can reach it. THE INSTRUMENTED QUESTION-TARGET SPLIT (463
    true-law / 488 converse, reported at window 5) was NOT re-run this pass — the
    split-by-target instrumentation was ad hoc and is not carried by
    `_play_ask_and_challenge`'s returned tally, so it is not reproduced here
    rather than guessed at. The re-measured totals it would have split
    (1258 questions, 1151 uptakes, both up from window 5) stand as the evidence
    in its place.

    **P-C2 IS STILL REFUTED, IN THE SAME DIRECTION, FOR THE THIRD TIME.** The
    channel now removes 93.5% of the converse's refuting individuals (321 → 21,
    against 94% at window 5) and still saves both converses the muted arm loses.
    The premise is refuted exactly as before: a converse `X_head -> X_local`
    wants an `X_local`, and every peer sharing the domain has plenty.

    THE COMMUNITY'S EVIDENCE MOVES FURTHER. Of the true laws' 640 refuting
    individuals in the muted arm, 590 are repairable in principle (92.2%,
    unmoved by the window). In the live arm the repairable residue now falls to
    170 — **71.2% of what was available has been delivered**, against 49.3% at
    window 5. The longer window gives testimony more rounds to arrive, and more
    of it does.

    THE DISPOSAL EXITS MOVE TOWARD REBUTTAL. Live: 66 suspensions, 44 restored by
    rebuttal, 2 restored by silence, 20 retracted internally — so **22 of the 66
    doubts end at the window** (internal + silence), down from 41 of 66 at window
    5. A longer window gives a peer more chances to answer before a doubt is
    forced to a verdict, so more doubts end by rebuttal (44, up from 25) and
    fewer by the window closing on them unanswered.

    WHAT IT COSTS: the live arm's net falls again, from −106 (window 5) to −185
    (window 8) — the same figure GATE 1 and `test_the_silence_window_at_three_
    five_and_eight`'s four-unit/window-8 row report independently. A repaired
    law goes on betting for longer under bounded attention, and under bounded
    attention a true law still cannot pay. Read the counts, not the direction.

    AND WHAT A BIGGER COMMUNITY DOES TO IT, measured in
    `test_the_silence_window_at_three_five_and_eight` on this same driver at
    window 8: six units at distinct apertures save 49 of 96 true laws here (51%)
    against these four units' 44 of 64 (69%), while corroboration fires 45 times
    rather than never. **The larger community still keeps a SMALLER proportion
    of its true laws** — at window 5 the same comparison read 27 of 96 (28%)
    against 28 of 64 (44%); the ratio narrows a little (a longer window helps the
    smaller community's true laws more, per this task's own P-C1 finding) but
    the direction is unchanged.

    AT WINDOW 5, the previous default, for comparison — this is the reading the
    ruling was made on and it is kept for that reason:

    **P-C1 IS HELD.** The refuting count on true laws falls by 45.5%, and 28 of
    the 64 true laws that were permanently lost in the muted arm survive the run.
    Nothing about the ask channel changed; what changed is that a law now lives
    long enough to use it. The question budget bears that out directly:
    instrumented over the same eight seeds, **463 questions ask about a true
    law's head and 488 about a converse's**, where before the split was 16
    against 464. The channel had been spending itself on the only laws still
    standing, and those were the false ones.

    **P-C2 IS REFUTED, AND IN THE OPPOSITE DIRECTION TO ITS OWN CLAIM, FOR THE
    SECOND TIME.** The channel removes 94% of the converse's refuting individuals
    and saves both converses the muted arm loses. Its premise — that no peer
    holds the missing head — is simply false in this field: a converse
    `X_head -> X_local` wants an `X_local`, and every peer sharing the domain has
    plenty. Testimony repairs whatever it is asked about, and it cannot tell a
    true law from a false one, because that is not what a question asks.

    THE COMMUNITY'S EVIDENCE MOVES NOW. Of the true laws' 640 refuting
    individuals in the muted arm, some peer holds the missing head for **590 —
    92.2% repairable in principle**, which was true before and did not move. In
    the live arm the repairable residue falls to 299, so roughly half of what was
    available has actually been delivered.

    THE DISPOSAL EXITS, and the window at last does something. Muted: 66
    suspensions, 66 retracted internally at the window, nothing else. Live: 66
    suspensions, 25 restored by rebuttal, 5 restored by silence, 36 retracted
    internally — so **41 of the 66 doubts end at the window** where the window
    had fired exactly zero times in every measurement before this task.

    WHAT IT COSTS: the live arm's net falls from −39 to −106. A repaired law goes
    on betting under bounded attention, and under bounded attention a true law
    still cannot pay. Read the counts, not the direction.

    AND WHAT A BIGGER COMMUNITY DOES TO IT, measured in
    `test_corroboration_fires_once_a_domain_has_three_witnesses` and
    `test_the_silence_window_at_three_five_and_eight` on this same driver: six
    units at distinct apertures save 27 of 96 true laws here (28%) against these
    four units' 28 of 64 (44%), while corroboration fires 45 times rather than
    never. **The larger community keeps a SMALLER proportion of its true laws.**
    """
    keys = ("true_ref", "conv_ref", "true_lost", "conv_lost", "repairable",
            "unrepairable", "questions", "uptakes", "net", "suspended",
            "internal", "corroborated", "rebutted", "silence")
    agg = {k: 0 for k in keys}
    muted_agg = dict(agg)
    for seed in C_SEEDS:
        live = _play_ask_and_challenge(seed, C_ROUNDS, ask=True)
        mute = _play_ask_and_challenge(seed, C_ROUNDS, ask=False)
        for k in agg:
            agg[k] += live[k]
            muted_agg[k] += mute[k]
    assert agg["questions"] > 0 and agg["uptakes"] > 0, (
        "the channel carried nothing, so nothing was tested")
    # P-C1: HELD, more strongly at window 8. The true laws' refuting count
    # falls 65.6% (was 45.5% at window 5).
    assert (muted_agg["true_ref"], agg["true_ref"]) == (640, 220)
    # P-C2: refuted the other way, still. The converse's count collapses further.
    assert (muted_agg["conv_ref"], agg["conv_ref"]) == (321, 21)
    # AND A LAW'S FATE CHANGES FURTHER: 44 of the 64 true laws survive (was 28).
    assert (muted_agg["true_lost"], agg["true_lost"]) == (64, 20)
    assert (muted_agg["conv_lost"], agg["conv_lost"]) == (2, 0)
    # 92.2% of what the true laws needed was held by some peer in the muted arm;
    # 71.2% of it now reaches the unit that needs it (was 49.3% at window 5).
    assert (muted_agg["repairable"], muted_agg["unrepairable"]) == (590, 50)
    assert agg["repairable"] == 170
    # THE WINDOW FIRES: 22 of 66 doubts end there (internal + silence), against
    # 41 of 66 at window 5 and 0 before that task — the longer window shifts
    # more doubts to rebuttal instead.
    assert muted_agg["suspended"] == agg["suspended"] == 66
    assert (muted_agg["internal"], muted_agg["rebutted"],
            muted_agg["silence"]) == (66, 0, 0)
    assert (agg["internal"], agg["rebutted"], agg["silence"]) == (20, 44, 2)
    assert muted_agg["corroborated"] == agg["corroborated"] == 0
    # The net score falls further, because a repaired law goes on betting for
    # longer and under bounded attention a true law still cannot pay.
    assert (muted_agg["net"], agg["net"]) == (-433, -185)


def test_the_silence_window_at_three_five_and_eight():
    """THE WINDOW'S DEFAULT WAS LOAD-BEARING AND UNMEASURED; it is measured now,
    and it was NOT changed — it is the author's.

    Eight seeds, 60 rounds, bounded attention, planted laws and converses seeded.

    WITHOUT AN ANSWERING CHANNEL THE VALUE CHANGES NOTHING. Windows of 3, 5 and 8
    read identical suspensions, corroborations, internal retractions and
    survivors at both community sizes — every column, not merely the totals. That
    is the previous task's finding at full strength: an inquiry with no answering
    channel is a delay, and the LENGTH of a delay is irrelevant when nothing
    comes back. It is asserted here rather than narrated, because it is the
    control that makes the next table mean something.

    WITH THE ASK CHANNEL LIVE it is the most consequential knob in the arm, and
    it trades score for laws monotonically:

        units  window  internal  rebutted  true lost  conv lost   net
        4           3        64         0      64/64       0/32   −41
        4           5        36        25      36/64       0/32  −106
        4           8        20        44      20/64       0/32  −185
        6           3        71        28      96/96      20/48   −29
        6           5        41        58      69/96      17/48   −77
        6           8        19        80      47/96      17/48  −134

    AND IT DISCRIMINATES, WHICH NOTHING ELSE IN THIS SERIES HAS DONE. At six
    units, moving from 3 to 8 saves **49 true laws** (96 lost down to 47) while
    sparing only **3 converses** (20 down to 17). A true law's missing head is
    exactly the thing a peer can supply; a converse's is not. Corroboration is
    flat at 45 across all three windows, so this knob and
    `corroborating_witnesses` are independent.
    """
    # THE LIVENESS CLAUSE THIS GATE LACKED, now mechanical rather than narrated.
    # `mute[0] == mute[1] == mute[2]` below is a three-way equality three dead
    # arms would satisfy, and the fourteen concrete non-zero figures further
    # down were its only real protection (`RUN_C_AUDIT_LOG.md`, "Unchecked
    # liveness claims"). Every arm here goes through `_play_ask_and_challenge`,
    # which is `@audited(expect_silent=("corroborate",))`: a channel it calls
    # that mints nothing fails the arm before any figure is compared — WITH THE
    # ONE EXCEPTION THE DECLARATION NAMES. `corroborate` is allowlisted there as
    # the audit's D-A1, so the `corroborated == 45` line below is still carried
    # by prose and by `dispose_challenges`, not by the guard. Every other
    # channel this gate reads is covered.
    for n_units, scheme in ((4, CYCLIC), (6, PAIRS)):
        mute = [_aggregate_ask(n_units, scheme, ask=False, window=w)
                for w in (3, 5, 8)]
        assert mute[0] == mute[1] == mute[2], (
            f"{n_units} units: the window changed an arm with no channel "
            f"answering — {mute}")

    four = [_aggregate_ask(4, CYCLIC, ask=True, window=w) for w in (3, 5, 8)]
    six = [_aggregate_ask(6, PAIRS, ask=True, window=w) for w in (3, 5, 8)]
    assert [d["internal"] for d in four] == [64, 36, 20]
    assert [d["rebutted"] for d in four] == [0, 25, 44]
    assert [d["silence"] for d in four] == [2, 5, 2]
    assert [d["true_lost"] for d in four] == [64, 36, 20]
    assert [d["conv_lost"] for d in four] == [0, 0, 0]
    assert [d["net"] for d in four] == [-41, -106, -185]
    assert [d["internal"] for d in six] == [71, 41, 19]
    assert [d["rebutted"] for d in six] == [28, 58, 80]
    assert [d["true_lost"] for d in six] == [96, 69, 47]
    assert [d["conv_lost"] for d in six] == [20, 17, 17]
    assert [d["net"] for d in six] == [-29, -77, -134]
    # Flat corroboration: the two knobs do not interact.
    assert [d["corroborated"] for d in six] == [45, 45, 45]
    # THE DISCRIMINATION, STATED AS THE RATIO IT IS: 49 true laws saved against
    # 3 converses spared.
    assert (six[0]["true_lost"] - six[2]["true_lost"],
            six[0]["conv_lost"] - six[2]["conv_lost"]) == (49, 3)


_ASK_KEYS = ("true_ref", "conv_ref", "true_lost", "conv_lost", "repairable",
             "unrepairable", "questions", "uptakes", "net", "suspended",
             "internal", "corroborated", "rebutted", "silence")

_TYPIFY_KEYS = _ASK_KEYS + (
    "adopted_licensed", "adopted_fabricated", "adopted_body", "proved",
    "failed", "pending", "preferences", "occ_pref", "occ_bite", "refused",
    "one_supplier", "many_suppliers", "score_pos", "score_neg", "score_zero")

_GATE_KEYS = _TYPIFY_KEYS + (
    "hits", "misses", "abstain", "bets", "true_total", "conv_total",
    "true_susp", "conv_susp", "independent", "relayed", "twin",
    "choice_lowest", "pref_choice", "pref_choice_bite")
"""Everything `_TYPIFY_KEYS` carries, plus gate 1's companion statistics: the
score split into the bets it is made of, and the law counts read as held rather
than as lost."""

_MATRIX_KEYS = ("consult", "prefs", "could", "voices", "voices_by_rel")
"""The gate-2 readings that are distributions rather than totals. They are
summed as `Counter`s across seeds and handed back as copies, so a reader cannot
mutate the memoised arm underneath the next reader."""

_ARMS = {}
"""Aggregates already computed, keyed by their arguments.

MEMOISED BECAUSE AN ARM COSTS SIXTY ROUNDS TIMES EIGHT SEEDS AND FOUR GATES
BELOW READ THE SAME ONES. Every arm is a deterministic function of its
arguments — asserted on this driver, typify path included, at the head of
`test_the_replication_verdict_reads_the_field_s_cadence_not_the_peer` — so
reading a cached one is reading the same run, not a shortcut past it. Nothing
here trims a seed or an arm.

NO ARM REACHED THROUGH HERE DECLARES A SILENCE, so `expect_silent` is not a
parameter of this driver: the only zero these arms carry is `corroborate`,
declared once on `_play_ask_and_challenge` itself. If one ever needs its own
declaration, IT MUST GO INTO `arm` BELOW — two arms differing only in what they
allowlist are two different arms, and a cache key that cannot tell them apart
would serve one the other's figures."""


def _aggregate_ask(n_units, scheme, *, ask, window=None, witnesses=None,
                   typify=None, rep_window=None, mute=False, keys=_ASK_KEYS):
    arm = (n_units, scheme, ask, window, witnesses, typify, rep_window, mute)
    cached = _ARMS.get(arm)
    if cached is None:
        cached = {k: 0 for k in _GATE_KEYS}
        cached.update({k: Counter() for k in _MATRIX_KEYS})
        for seed in C_SEEDS:
            t = _play_ask_and_challenge(seed, C_ROUNDS, ask=ask,
                                        n_units=n_units, scheme=scheme,
                                        window=window, witnesses=witnesses,
                                        typify=typify, rep_window=rep_window,
                                        mute=mute)
            for k in _GATE_KEYS:
                cached[k] += t[k]
            for k in _MATRIX_KEYS:
                cached[k].update(t[k])
        _ARMS[arm] = cached
    return {k: (Counter(cached[k]) if k in _MATRIX_KEYS else cached[k])
            for k in keys}


# --- does typification discriminate? ------------------------------------------
#
# THE LAST CANDIDATE. Task 5e found that testimony repairs whatever it is asked
# about and cannot tell a true law from a false one; Task 5f found that
# corroboration, once a community was large enough to supply it, eliminated
# every law it was given. Typification is what Berger & Luckmann actually name
# as the mechanism by which a shared reality gets built — reciprocal
# typification of habitualized action by types of actor — and it is the one
# thing in this series that cannot exist in a solitary unit, so it is the
# sharpest test available of whether a community exists here at all.


def test_typified_asking_changes_nothing_and_the_reason_is_that_nobody_had_a_choice():
    """**P-G3 HELD, IN THE STRONGEST FORM AVAILABLE: typified asking is not
    merely weak here, it is EXACTLY INERT** — every one of the fourteen figures
    the untargeted arm reports is reproduced digit for digit by the typified
    one, at both community sizes.

    P-G3 predicted that typification changes nothing where every peer sees the
    same distribution of noise, and that the gain requires peers to actually
    differ. The measurement says something sharper than the prediction did: the
    peers did not merely fail to differ usefully, **NO UNIT EVER HAD TWO VOICES
    TO CHOOSE BETWEEN.** Eight seeds, 60 rounds.

    RE-MEASURED AT WINDOW 8 (the ruled default, 2026-07-31):

        arm            (unit, relation)   with 2+     uptake decisions   ... at which
                       pairs told by      suppliers   at which a unit    the preference
                       exactly 1 peer                 held a preference  disagreed
        4 units, cyclic              96          0                  53              0
        6 units, pairs              107          0                  72              0

    THE FIELD IS WHY, AND IT IS ARITHMETIC RATHER THAN LUCK. A unit answers only
    from what it has met, so a reply about `a_head` can come only from a peer
    that witnesses alpha. Under bounded attention with `stagger=2` a peer that
    witnesses alpha ON THE SAME ROUNDS meets exactly what the asker meets and
    has nothing to add, so the only peer that can ever tell it something new is
    one witnessing the same domain on the OPPOSITE rounds — and at four units
    there is exactly one of those per asker. A preference cannot express itself
    when the alternative to the preferred voice is silence.

    THAT SENTENCE ORIGINALLY READ "at both community sizes" AND TASK 7 FALSIFIED
    IT. Six units put three witnesses on a domain, and at alpha they are u0
    (even), u1 (odd) and u2 (even), so the ODD asker has TWO opposite-phase peers
    rather than one
    (`test_gate_two_consultation_is_non_uniform_and_no_unit_at_four_ever_had_a_choice`,
    where the uptake and choice-count figures also moved at window 8). The
    measurement below is unaffected and the reason it is unaffected is worth
    keeping: the two candidate voices attend the same rounds as each other, so
    they hold the same facts, and `MarkBoard.answer_to` returns the first mark
    published — which the lower-numbered unit always mints first. One peer is the
    perpetual answerer, so `many_suppliers` is 0 for a reason about publication
    order rather than about what anybody could have said.

    A SUPPLIER IS COUNTED ONLY WHEN IT TOLD THE UNIT SOMETHING IT DID NOT HOLD.
    Counted the looser way — every reply encountered, including ones whose
    content had arrived at the asker's own membrane in the meantime — six units
    read 115 pairs with one supplier and 7 with two, and all seven turn out to
    be the same fact reaching the unit twice rather than two peers informing it.
    The looser count would have reported choices nobody had.

    WHAT THE UNITS DID LEARN, and at four units it is now LITERALLY NOTHING.
    Of the 96 (peer, relation) pairs a four-unit community accumulates any
    record about, **0 end the run with a positive score** (was 1 at window 5);
    94 end negative and 2 at zero. NO (PEER, RELATION) RECORD AT FOUR UNITS
    EVER ENDS THE RUN POSITIVE — that is the precise claim, not that a
    preference was never consulted: the mechanism still decided 53 uptakes at
    four units (`occ_pref`, up from 41 at window 5), it simply never once
    favoured a record that ended positive. The same fact
    `test_gate_two_consultation_is_non_uniform_and_no_unit_at_four_ever_had_a_choice`
    now reports directly (its own `prefs` tally sums to 0 at four units, where
    it summed to 1 at window 5): a longer window gives the field more rounds to
    redraw against a testimony pair before the run ends, and the one relation
    that used to end up barely positive no longer does. Six units: **2 positive
    of 107** (was 5), 105 negative, 0 at zero. Replication is a coin flip on
    whether the field redraws that individual, and the field draws one
    individual per relation per round from a list of forty, so most testimony is
    never borne out within a sixty-round run whoever gave it — and a longer
    window means more rounds in which it can still be overturned. See
    `test_the_replication_verdict_reads_the_field_s_cadence_not_the_peer`.

    AT WINDOW 5, the previous default, for comparison — this is the reading the
    ruling was made on and it is kept for that reason:

        arm            (unit, relation)   with 2+     uptake decisions   ... at which
                       pairs told by      suppliers   at which a unit    the preference
                       exactly 1 peer                 held a preference  disagreed
        4 units, cyclic              96          0                  41              0
        6 units, pairs              107          0                  54              0

    Counted at the decision, 394 of the 928 uptakes at six units had two peers
    standing behind the content (the window-5 reading of
    `test_gate_two_consultation_is_non_uniform_and_no_unit_at_four_ever_had_a_choice`).
    A preference WAS held at 41 and 54 uptake decisions, and disagreed at none.
    Of the 96 (peer, relation) pairs a four-unit community accumulates any
    record about, 1 ended the run with a positive score, 90 negative and 5 at
    zero. Six units: 5 positive of 107, 99 negative, 3 at zero.
    """
    for n_units, scheme in ((4, CYCLIC), (6, PAIRS)):
        control = _aggregate_ask(n_units, scheme, ask=True)
        typified = _aggregate_ask(n_units, scheme, ask=True, typify="prefer")
        assert control == typified, (
            f"{n_units} units: typified asking moved a figure — "
            f"{ {k: (control[k], typified[k]) for k in control if control[k] != typified[k]} }")
    four = _aggregate_ask(4, CYCLIC, ask=True, typify="prefer",
                          keys=_TYPIFY_KEYS)
    six = _aggregate_ask(6, PAIRS, ask=True, typify="prefer", keys=_TYPIFY_KEYS)
    # The channel carried something, so inertness is a result rather than a
    # measurement that never ran.
    assert (four["questions"], four["uptakes"]) == (1258, 1151)
    assert (six["questions"], six["uptakes"]) == (1358, 1213)
    # A preference WAS held at 53 and 72 uptake decisions, and disagreed at none.
    assert (four["occ_pref"], four["occ_bite"]) == (53, 0)
    assert (six["occ_pref"], six["occ_bite"]) == (72, 0)
    # AND NO UNIT, AT EITHER SIZE, WAS EVER TOLD SOMETHING NEW ABOUT ONE
    # RELATION BY TWO DIFFERENT PEERS. Every (unit, relation) pair that acquired
    # anything at all acquired it from exactly one voice.
    assert (four["one_supplier"], four["many_suppliers"]) == (96, 0)
    assert (six["one_supplier"], six["many_suppliers"]) == (107, 0)
    # And almost nothing was learned — and at four units, NOTHING: no
    # (peer, relation) pair ever earns a positive score, where one did at
    # window 5 (see `test_gate_two_...`'s own `prefs` tally, 0 vs 1).
    assert (four["preferences"], six["preferences"]) == (0, 2)
    assert (four["score_pos"], four["score_neg"], four["score_zero"]) == (
        0, 94, 2)
    assert (six["score_pos"], six["score_neg"], six["score_zero"]) == (2, 105, 0)


def test_no_fabricated_fact_is_ever_adopted_so_p_g1_has_no_category_to_measure():
    """**P-G1 IS NOT REFUTED — IT IS UNMEASURABLE IN THIS FIELD, AND THE COUNT
    THAT SAYS SO IS ZERO.** Its premise fails twice over.

    P-G1 held that typification lowers the adoption rate of SPURIOUS facts more
    than of real ones, "because the field's `spurious_rate` fabricates a head
    with no antecedent to license it, and a fabrication is by construction
    unreplicated — no second observer meets it."

    THE FIRST FAILURE IS ABOUT WHO MEETS A FABRICATION. A spurious atom is not
    one peer's invention: `c_field.Field.deliver` puts it in the DOMAIN's
    delivery, so every unit witnessing that domain on that round meets it. A
    fabrication has as many observers as any other arrival.

    THE SECOND FAILURE IS THE DECISIVE ONE: **a fabricated fact can never be
    asked about, so it can never be adopted.** A question names an atom the
    asker's own law licenses over an individual its own record already carries
    — that is the ask channel's targeting-by-construction — so a unit asks for
    `a_head(x)` only while holding `a_local(x)`, and an individual carrying
    `a_local` is one the field licensed a head for. The other questions in this
    arm come from the seeded converse and ask for `a_local(x)`, an ANTECEDENT
    relation, which `spurious_rate` never fabricates.

    MEASURED, over eight seeds and 60 rounds: the field licensed **1004** head
    atoms and fabricated **37** that no antecedent ever licensed, all 37 inside
    some unit's aperture — both figures are the field's own and do not depend on
    `corroboration_window`. Adoptions of a fabricated atom, in every arm and at
    both community sizes: **0 of 1151 and 0 of 1213** (RE-MEASURED AT WINDOW 8,
    the ruled default, 2026-07-31 — the totals were 0 of 939 and 0 of 928 at
    window 5, kept below for comparison; the zero itself does not move at either
    window, only the total adoptions it is a fraction of). Whatever typification
    could do to a fabrication, it has nothing here to do it to.

    WHAT WOULD HAVE TO CHANGE for the category to exist: units would have to be
    able to ask about atoms their own record does not already license — which
    means either induction running in this arm, so a unit can hold a law over
    relations the field does not connect, or a membrane that lets a unit relay
    what a third party said rather than only what it met. Both are changes to
    the experiment, not to this channel, so the number is reported rather than
    manufactured.
    """
    for n_units, scheme in ((4, CYCLIC), (6, PAIRS)):
        for typify in (None, "prefer", "distrust"):
            arm = _aggregate_ask(n_units, scheme, ask=True, typify=typify,
                                 keys=_TYPIFY_KEYS)
            assert arm["adopted_fabricated"] == 0, (
                f"{n_units} units, typify={typify!r}: a fabricated head atom "
                f"was adopted, so P-G1 has a category after all")
            assert arm["adopted_licensed"] > 0, (
                "no head atom was adopted at all, so the zero above is vacuous")
    # THE SPLIT, so the zero above is read against what WAS taken up.
    # RE-MEASURED AT WINDOW 8: of the 1151 adoptions at four units, 697 are head
    # atoms (every one of them licensed) and 454 are atoms of an ANTECEDENT
    # relation, which `spurious_rate` never fabricates at all. Six units: 754
    # and 459 of 1213. AT WINDOW 5, the previous default: of 939 adoptions at
    # four units, 479 head / 460 antecedent; six units 478 / 450 of 928 — kept
    # for comparison, this is the reading the ruling was made on.
    four = _aggregate_ask(4, CYCLIC, ask=True, keys=_TYPIFY_KEYS)
    six = _aggregate_ask(6, PAIRS, ask=True, keys=_TYPIFY_KEYS)
    assert (four["adopted_licensed"], four["adopted_body"]) == (697, 454)
    assert (six["adopted_licensed"], six["adopted_body"]) == (754, 459)
    # The field really does fabricate: 37 head atoms over eight seeds that no
    # antecedent ever licensed, every one of them inside some unit's aperture.
    fabricated = 0
    for seed in C_SEEDS:
        spec = default_spec(seed=seed)
        field = Field(spec)
        for d in spec.domains:
            licensed = field.licensed_heads(d.name, C_ROUNDS)
            delivered = {f for r in range(C_ROUNDS)
                         for f in field.deliver(d.name, r) if f[0] == d.law[1]}
            fabricated += len(delivered - licensed)
    assert fabricated == 37


def test_refusing_a_peer_that_let_you_down_halves_uptake_and_saves_no_law():
    """THE CONTROL THE LITERAL READING COULD NOT SUPPLY, and the reason it is
    here is Task 5f's: a comparison that obviously holds needs the arm that
    could show it does not. `whom_to_ask` names a peer only on POSITIVE
    evidence, so a unit let down by the only voice it ever hears is back where
    it started rather than warned — and the inert result above cannot tell
    whether the machinery does nothing or is simply never exercised. This arm
    exercises it: a unit with no preference refuses a reply from a peer whose
    testimony about that relation has already failed.

    IT BITES HARD AND BUYS NOTHING.

    RE-MEASURED AT WINDOW 8 (the ruled default, 2026-07-31). Eight seeds, 60
    rounds:

        arm                     uptakes   refuting (true)   refuting (conv)   true lost   conv lost     net
        4u untargeted              1151               220                21       20/64        0/32    −185
        4u distrust                 466               488               223       20/64        0/32    −745
        6u untargeted              1213               517               152       47/96       17/48    −134
        6u distrust                 496               815               328       47/96       17/48    −760

    **NOT ONE LAW'S FATE MOVES, STILL.** The same 20 of 64 true laws are lost at
    four units and the same 47 of 96 at six, the same converses stand, and every
    disposal exit is identical to the untargeted control's — because a doubt is
    settled from the credit a unit has accumulated by the time its window
    closes, and refusing a peer changes what testimony arrives, not when the
    window itself acts. What the refusals do reach is the evidence: **687 and
    717 questions go unanswered** (up from 525/505 at window 5 — a longer window
    means more questions are asked in total, so more of them go unanswered under
    distrust too), and the refuting counts rise on true laws and converses
    alike.

    THE ONE ASYMMETRY STILL RUNS THE WRONG WAY FOR THE SERIES' PURPOSES. The
    converse's refuting count rises by a factor of **10.6** (223/21, essentially
    unchanged from window 5's 10.6) against the true law's **2.2** (488/220, up
    from 1.5) — distrust still weighs harder against the false law than the true
    one, though less lopsidedly than at window 5, and it still changes no
    outcome whatever, because nothing reads those counts after the window has
    closed.

    AND IT COSTS THE SCORE, MORE STEEPLY STILL, for the same reason: an adopted
    head atom mostly PREVENTS A LOSING BET rather than winning one. A unit that
    holds `a_head(x)` no longer stakes on it, so refusing the answer buys back a
    forecast the field was never going to deliver. Net falls −185 → −745 (4.0×,
    against 5.2× at window 5) and −134 → −760 (5.7×, against 6.9× at window 5).
    Read the counts, not the direction.

    AT WINDOW 5, the previous default, for comparison — this is the reading the
    ruling was made on and it is kept for that reason:

        arm                     uptakes   refuting (true)   refuting (conv)   true lost   conv lost     net
        4u untargeted               939               349                20       36/64        0/32    −106
        4u distrust                 417               518               211       36/64        0/32    −551
        6u untargeted               928               695               158       69/96       17/48     −77
        6u distrust                 423               849               333       69/96       17/48    −534

    525 and 505 questions went unanswered; the converse's refuting count rose by
    a factor of 10.6 against the true law's 1.5; net fell −106 → −551 (5.2×) and
    −77 → −534 (6.9×).
    """
    four = _aggregate_ask(4, CYCLIC, ask=True, typify="distrust",
                          keys=_TYPIFY_KEYS)
    six = _aggregate_ask(6, PAIRS, ask=True, typify="distrust",
                         keys=_TYPIFY_KEYS)
    four_control = _aggregate_ask(4, CYCLIC, ask=True, keys=_TYPIFY_KEYS)
    six_control = _aggregate_ask(6, PAIRS, ask=True, keys=_TYPIFY_KEYS)
    # The refusals happened, so the arm is not the control under another name.
    assert (four["refused"], six["refused"]) == (687, 717)
    assert (four_control["uptakes"], four["uptakes"]) == (1151, 466)
    assert (six_control["uptakes"], six["uptakes"]) == (1213, 496)
    # The evidence moves, and it moves harder against the converse.
    assert (four_control["true_ref"], four["true_ref"]) == (220, 488)
    assert (four_control["conv_ref"], four["conv_ref"]) == (21, 223)
    assert (six_control["true_ref"], six["true_ref"]) == (517, 815)
    assert (six_control["conv_ref"], six["conv_ref"]) == (152, 328)
    # AND NOT ONE LAW'S FATE MOVES, at either size, on either kind of law.
    for control, arm in ((four_control, four), (six_control, six)):
        assert (control["true_lost"], control["conv_lost"]) == (
            arm["true_lost"], arm["conv_lost"])
        assert [control[k] for k in ("suspended", "internal", "corroborated",
                                     "rebutted", "silence")] == [
            arm[k] for k in ("suspended", "internal", "corroborated",
                             "rebutted", "silence")]
    assert (four["true_lost"], four["conv_lost"]) == (20, 0)
    assert (six["true_lost"], six["conv_lost"]) == (47, 17)
    # The score falls steeply, because an adopted head mostly prevents a bet.
    assert (four_control["net"], four["net"]) == (-185, -745)
    assert (six_control["net"], six["net"]) == (-134, -760)


def test_the_replication_verdict_reads_the_field_s_cadence_not_the_peer():
    """WHY ALMOST NOTHING IS EVER LEARNED, measured rather than argued.

    `settle_credit`'s verdict is replication: an adopted fact proves out when
    the unit's own aperture later delivers it too. Whether that happens depends
    on whether the field redraws that individual, and the field draws ONE
    individual per relation per round from a list of forty — so an individual
    waits about forty rounds for its next turn and a unit under bounded
    attention meets half of those. Four units, cyclic, eight seeds, 60 rounds,
    the replication window (`rep_window`, distinct from `corroboration_window`)
    the only variable.

    RE-MEASURED AT WINDOW 8 (`corroboration_window`, the ruled default,
    2026-07-31 — `rep_window` itself still swept at 5/10/20 as before):

        rep_window   proved   failed   still pending   preferences held at the end
        5               431      673              47                             0
        10              431      618             102                             0
        20              431      522             198                             4

    **THE PROVED COUNT STILL DOES NOT MOVE AT ALL.** 431 of the 1151 adoptions
    (up from 347 of 939, a nearly identical ~37% share either way) are borne out
    by a second route and the rest are not, whatever deadline the unit keeps;
    all the window decides is how many of the unreplicated ones get read as
    failures and how many are still waiting when the run ends. A knob that
    changes only the denominator is reading the field's cadence, not the peer's
    reliability — which is the whole reason the preference machinery above has
    nothing to bite on. This still holds unchanged by the `corroboration_window`
    default; the invariant is about `rep_window`, a different knob.

    A LONGER `rep_window` STILL LEARNS MORE PREFERENCES ONLY BY DECLINING TO
    CONCLUDE, though the exact count moved: it now goes 0 → 0 → 4 of 96 (peer,
    relation) pairs across the three windows (was 0 → 1 → 5), consistent with
    this file's other finding that four units hold zero preferences by default
    at `corroboration_window` 8 — the middle `rep_window` no longer resolves
    even the one pair it used to. It still does so by leaving failures pending
    rather than by finding successes; that is honest and is not a route to a
    channel that discriminates.

    AT WINDOW 5 (`corroboration_window`), the previous default, for comparison —
    this is the reading the ruling was made on and it is kept for that reason:

        rep_window   proved   failed   still pending   preferences held at the end
        5               347      552              40                             0
        10              347      508              84                             1
        20              347      434             158                             5
    """
    # THE ARMS ARE MEMOISED AND READ BY FOUR GATES, so determinism is not a
    # nicety here: it is what makes a cached arm the same run rather than a
    # shortcut past one. Asserted on the typify path itself, which the older
    # determinism gate does not reach.
    def once():
        t = _play_ask_and_challenge(3, 30, ask=True, typify="distrust")
        return tuple(sorted(t.items()))
    assert once() == once()

    arms = [_aggregate_ask(4, CYCLIC, ask=True, typify="prefer", rep_window=w,
                           keys=_TYPIFY_KEYS) for w in (5, 10, 20)]
    assert [a["proved"] for a in arms] == [431, 431, 431]
    assert [a["failed"] for a in arms] == [673, 618, 522]
    assert [a["pending"] for a in arms] == [47, 102, 198]
    assert [a["preferences"] for a in arms] == [0, 0, 4]
    # Every verdict is accounted for: nothing is entered twice and nothing is
    # dropped, at every window.
    for arm in arms:
        assert arm["proved"] + arm["failed"] + arm["pending"] == arm["uptakes"]


# --- the two stage-3 gates -----------------------------------------------------
#
# THE PLAN PRE-REGISTERED THESE and instructed that a null be reported rather
# than tuned away. Both are run below at the community the plan named — four
# units — with the six-unit community reported beside them, because six units is
# the only size at which any unit was ever offered a second voice.


def test_gate_one_the_score_improves_while_the_community_learns_less():
    """**GATE 1 PASSED ON `net_score`, THE PASS MEANT THE OPPOSITE OF WHAT IT LOOKED
    LIKE, AND ON 2026-07-31 THE STATISTIC WAS RETIRED FROM THE GATE ROLE FOR IT.**
    The figures below are pinned and reported; the verdict is carried by the laws
    held and the bets placed.

    Four units, eight seeds, 60 rounds, planted laws and converses
    seeded, bounded attention. The live world runs all four stage-3 channels; the
    mute twin runs none, so each unit meets the same field alone.

    RE-MEASURED AT WINDOW 8 (the ruled default, 2026-07-31):

        four units                mute twin      live world
        net score                     −1421            −185
        bets placed                    1497             193
        hits                             38               4
        misses                         1459             189
        hit rate among bets           0.0254          0.0207
        abstentions                    5009            5619
        true laws held at the end     64/64           44/64
        converses held at the end     32/32           32/32

    **THIS IS EXACTLY THE FOUR-UNIT WINDOW-8 ROW `corroboration_window`'s OWN
    SWEEP TABLE ALREADY PREDICTED** (`4 / 8 / internal 20 / rebutted 44 /
    true-lost 20-of-64 / net −185`) — the ruling's evidence and this gate's
    re-measurement are the same run read twice, and they agree digit for digit.

    THE FOLD ITSELF MOVED, WHICH IS FURTHER EVIDENCE AGAINST LEANING ON IT: the
    live world's score now exceeds the mute twin's by a factor of **7.7**, not
    thirteen (−1421 / −185 vs the window-5 −1421 / −106). A statistic whose own
    headline number is this sensitive to an unrelated knob — the window governs
    how long a doubt stays open, not how communication trades score for
    forecasting — is exactly the kind of instability the retirement argument
    rests on; the test's own name is left as it stands, on purpose, as a visible
    record of what net_score does under a knob that has nothing to do with its
    claim. It still places 87.1% fewer bets (down from 92.7%), lands 4 hits
    against 38, holds 20 fewer of the 64 true laws it was given (down from 36
    fewer), and holds every one of the 32 false ones in both arms.
    **Communication still buys a better score by very nearly ceasing to
    forecast — the direction is unchanged, only the size of the effect.**

    **`net_score` ALONE STILL CANNOT CARRY THIS GATE, and the four earlier
    inversions now read (window 8, with window 5 beside them):**

    - Task 5, bounded attention with the challenge channel: net rose −1421 →
      −433 while 64 of 64 true laws were destroyed — unchanged at either window,
      because this arm has no ask channel for the window length to act through.
    - Task 5e, the ask channel with inquiry ordered before elimination: net fell
      −39 → **−185** (was −39 → −106) while **44** of the 64 true laws were
      saved (was 28) — see
      `test_peer_testimony_repairs_the_true_law_once_the_law_survives_to_ask`.
    - Task 5f, six units mute: net read exactly 0 against four units' −2122,
      unchanged — no unit survived to place a bet at all, at either window.
    - Task 6, the distrust arm: net fell **−185 → −745** (was −106 → −551) with
      every law's fate and every disposal exit identical, because an adopted
      head atom mostly prevents a losing bet rather than winning one — see
      `test_refusing_a_peer_that_let_you_down_halves_uptake_and_saves_no_law`.

    Spec §9a retired `accuracy` at these bet volumes for a related reason, and
    the hit rates above show why it stays retired: 4 hits of 193 and 3 of 140
    decide a ratio, so the six-unit live arm's 0.0214 against its mute twin's
    0.0199 rests on three events and carries nothing. **Read bets placed and laws
    held; the ratio is reported for completeness and should not be leaned on.**

    THE DECOMPOSITION IS WHAT SETTLES IT. Inserting the challenge-channel-only
    arm between the two shows both steps moving the score the same way for
    opposite epistemic reasons:

        four units              net    bets   true held   converses held
        mute twin             −1421    1497       64/64            32/32
        challenge only         −433     455        0/64            30/32
        all four channels      −185     193       44/64            32/32

    The first step improves the score by 988 by destroying every true law
    (unchanged); the second improves it by a further **248** by restoring
    **44** of them (was +327 restoring 28). **A statistic that rises both when
    true laws are destroyed and when they are restored is still not measuring
    what the gate asks about.**

    SIX UNITS READS THE SAME WAY AND HARDER: net −2122 → **−134** (was −77),
    bets 2210 → **140** (was 83), hits 44 → 3 (unchanged), true laws held
    96/96 → **49/96** (was 27/96), converses held 48/48 → 31/48 (unchanged).
    Converses die there where the live arm at four units loses none, and the
    channels stay anti-discriminating all the same: **49.0% of the true laws
    lost against 35.4% of the converses** (was 71.9% against 35.4%).

    The mute twin reproduces Task 5's −1421 and the challenge-only arm its −433,
    which is the check that this new arm is the same world under a new switch
    rather than a differently-configured one — both figures window-invariant,
    confirming again that a doubt with no ask channel behind it does not read
    `corroboration_window` at all.

    AT WINDOW 5, the previous default, for comparison — this is the reading the
    ruling was made on and it is kept for that reason:

        four units                mute twin      live world
        net score                     −1421            −106
        bets placed                    1497             110
        hits                             38               2
        misses                         1459             108
        hit rate among bets           0.0254          0.0182
        abstentions                    5009            5654
        true laws held at the end     64/64           28/64
        converses held at the end     32/32           32/32

    The live world's score exceeded the mute twin's by a factor of thirteen. It
    also placed 92.7% fewer bets, landed 2 hits against 38, held 36 fewer of the
    64 true laws it was given, and held every one of the 32 false ones in both
    arms.

        four units              net    bets   true held   converses held
        mute twin             −1421    1497       64/64            32/32
        challenge only         −433     455        0/64            30/32
        all four channels      −106     110       28/64            32/32

    The first step improved the score by 988 by destroying every true law; the
    second improved it by a further 327 by restoring 28 of them. Six units read
    net −2122 → −77, bets 2210 → 83, hits 44 → 3, true laws held 96/96 → 27/96,
    converses held 48/48 → 31/48 — 71.9% of the true laws lost against 35.4% of
    the converses.
    """
    four_mute = _aggregate_ask(4, CYCLIC, ask=False, mute=True, keys=_GATE_KEYS)
    four_live = _aggregate_ask(4, CYCLIC, ask=True, keys=_GATE_KEYS)
    four_chal = _aggregate_ask(4, CYCLIC, ask=False, keys=_GATE_KEYS)
    six_mute = _aggregate_ask(6, PAIRS, ask=False, mute=True, keys=_GATE_KEYS)
    six_live = _aggregate_ask(6, PAIRS, ask=True, keys=_GATE_KEYS)

    # The mute twin really is mute: no question, no uptake, and no doubt ever
    # entertained, so nothing but the field reached any unit.
    assert (four_mute["questions"], four_mute["uptakes"]) == (0, 0)
    assert [four_mute[k] for k in ("suspended", "internal", "corroborated",
                                   "rebutted", "silence")] == [0] * 5
    # THE GATE'S OWN CLAUSE, DEMOTED 2026-07-31. It passed, and passing meant the
    # opposite of what it looked like, which is why `net_score` was retired from
    # the gate role. The figures are PINNED — pinning is reporting, with teeth —
    # and the verdict is carried by the law and participation clauses below.
    assert (four_mute["net"], four_live["net"]) == (-1421, -185)
    # AND THE COMPANIONS SAY IT PASSED BY BETTING ALMOST NOT AT ALL.
    assert (four_mute["bets"], four_live["bets"]) == (1497, 193)
    assert (four_mute["hits"], four_live["hits"]) == (38, 4)
    assert (four_mute["misses"], four_live["misses"]) == (1459, 189)
    assert (four_mute["abstain"], four_live["abstain"]) == (5009, 5619)
    # 87.1% fewer bets at window 8, against 92.7% at window 5 — the ratio moved
    # (0.0735 -> 0.1289), so the threshold moved with it.
    assert four_live["bets"] / four_mute["bets"] < 0.13
    # THE OUTCOME THE SERIES CARES ABOUT MOVES THE OTHER WAY: 20 of the 64 true
    # laws are gone (was 36) and every one of the 32 converses still stands.
    assert (four_mute["true_total"], four_live["true_total"]) == (64, 64)
    assert (four_mute["true_lost"], four_live["true_lost"]) == (0, 20)
    assert (four_mute["conv_total"], four_live["conv_total"]) == (32, 32)
    assert (four_mute["conv_lost"], four_live["conv_lost"]) == (0, 0)
    # No law standing at the end is standing suspended, so "held" means "held
    # and licensing anticipations" in both arms.
    assert (four_mute["true_susp"], four_live["true_susp"]) == (0, 0)
    assert (four_mute["conv_susp"], four_live["conv_susp"]) == (0, 0)
    assert (four_chal["net"], four_chal["bets"]) == (-433, 455)
    assert (four_chal["true_lost"], four_chal["conv_lost"]) == (64, 2)
    # THE DECOMPOSITION, AND THIS COMPARISON IS KEPT ON PURPOSE. Its content is
    # that the score rose in BOTH directions — the first step by destroying every
    # true law, the second by restoring 28 — so it asserts the inversion itself
    # rather than deciding anything by it. Retiring it would delete the evidence
    # the retirement rests on.
    assert four_mute["net"] < four_chal["net"] < four_live["net"]
    # The hit rate is reported and not leaned on: it falls in the live arm at
    # four units and rises at six, on 2 and 3 hits respectively.
    assert four_live["hits"] / four_live["bets"] < four_mute["hits"] / four_mute["bets"]
    assert six_live["hits"] / six_live["bets"] > six_mute["hits"] / six_mute["bets"]
    assert (six_live["hits"], six_mute["hits"]) == (3, 44)
    # SIX UNITS, THE SAME SHAPE AND HARDER.
    assert (six_mute["net"], six_live["net"]) == (-2122, -134)
    assert (six_mute["bets"], six_live["bets"]) == (2210, 140)
    assert (six_mute["true_lost"], six_live["true_lost"]) == (0, 47)
    assert (six_mute["conv_lost"], six_live["conv_lost"]) == (0, 17)
    assert six_live["true_lost"] / 96 > six_live["conv_lost"] / 48


def test_gate_two_consultation_is_non_uniform_and_no_unit_at_four_ever_had_a_choice():
    """**GATE 2 READS THE PRE-REGISTERED NULL.** Its first clause now holds only
    by the larger community's record, and its second still holds for a reason
    that has nothing to do with consultation.

    RE-MEASURED AT WINDOW 8 (the ruled default, 2026-07-31).

    CLAUSE 1 — at least one unit's `whom_to_ask` is non-`None`:
    **NO LONGER TRUE AT FOUR UNITS AT ALL.** Of the 96 (peer, relation) records a
    four-unit community accumulates, **0 end the run positive** (was 1 at window
    5): no (peer, relation) record at four units ever ends the run positive at
    the ruled default. Six units still do: **2 of 107** (was 5). The clause
    survives only through the six-unit reading now.

    WHAT ACTUALLY MOVED IS THIS CLAUSE, NOT THE TEST'S OWN NAME. The name's
    claim — no unit at four ever had a CHOICE between two voices — was already
    unconditionally true at window 5 too: the window-5 matrix below shows all
    939 decisions at four units with exactly one voice behind them, so a
    preference never had two voices to decide between, then or now (`four
    ["choice_lowest"] == 0` at window 8, same fact). **FINDING: a longer
    window removed typification's last foothold at four units** — the one
    (peer, relation) pair that used to end the run barely positive no longer
    does, because eight rounds give the field more chances to redraw against
    it before the run ends (the same mechanism
    `test_the_replication_verdict_reads_the_field_s_cadence_not_the_peer`
    shows directly by sweeping the OTHER window, `rep_window`).

    CLAUSE 2 — the who-asks-whom distribution is not uniform: **yes, and it is
    still the aperture layout that made it so.** Four units, eight seeds, 60
    rounds, 1151 uptakes over the twelve ordered (asker, answerer) pairs, where
    uniform would put 96 in each:

              takes from     u0     u1     u2     u3
              u0              —     78      0    204
              u1            218      —     69      0
              u2              0    207      —     80
              u3             87      0    208      —

    The four empty cells are still exactly the two pairs of units that share no
    domain, and every non-empty cell is still a pair that shares one. Each unit
    now takes roughly **70–76%** of its uptake from the single peer that
    witnesses the domain its own seeded converse names (was ~90%) — 204 of 282,
    218 of 287, 207 of 287, 208 of 295 — because that converse still wants an
    ANTECEDENT relation the field delivers every round, but the longer window
    gives more rounds for the OTHER peer's testimony to also be taken up before
    a doubt resolves, so the dominant peer's share of the total falls even
    though its raw count barely moves.

    THE DIAGNOSTIC THE PLAN DID NOT ASK FOR, AND IT IS STILL THE ONE THAT
    MATTERS, AT FOUR UNITS. Counting, at each uptake decision, how many distinct
    peers had already published that content: **all 1151 decisions at four
    units still had exactly one.** A community in which every question has
    exactly one possible answerer has not failed to typify; it never posed the
    question typification answers — unmoved by the window, because it is a fact
    about the apertures' phase structure, not about how long a doubt is allowed
    to stand.

    SIX UNITS STILL OFFERS A CHOICE, AND NOW THE CHOICE IS NOT ALWAYS BETWEEN
    TWINS. There, **498** of 1213 decisions had two peers standing behind the
    content (was 394 of 928) — **469 independent first-hand witnesses and, NEW
    AT WINDOW 8, 29 THAT RELAY ADOPTED TESTIMONY** (was 0 relayed at window 5).
    Of the 469 independent ones, all 469 still met the atom on the SAME ROUND
    (the twin count still equals the independent count exactly), because a
    domain at six units is witnessed by three units of which two attend the
    same rounds — that half of the finding is unmoved. The 29 relayed decisions
    are the new thing a longer window makes possible: enough rounds now pass
    for a peer to have adopted a third party's testimony and republish it before
    the asker's own decision, so a second "voice" can now be someone repeating
    what it was told rather than what it met. On the 498, a preference was held
    at 25 decisions (was 23) and named the answering peer at every one.

    AND THE "LOWER-NUMBERED ANSWERS" PATTERN IS NO LONGER ABSOLUTE. At window 5
    the lower-numbered of two voices answered literally every one of 394 two-
    voice decisions. At window 8 it answers **481 of 498 (96.6%)**, not all —
    the 17 exceptions arrive in the same window that introduced the 29 relayed
    decisions, which is consistent with (though not separately proven to be
    caused by) a relayed reply sometimes reaching the board after the
    lower-numbered peer's first-hand one would have, rather than always before.

    THE INSTRUMENT WAS TIGHTENED BEFORE THESE NUMBERS WERE PUBLISHED, the same
    way Task 6's supplier count was. A first cut counted voices at every decision
    rather than at every decision that told the unit something, and read 13
    gamma-relation choices at six units. Every one was a reply whose content the
    asker's own membrane had delivered in the meantime. Counted on fresh uptake,
    gamma still vanishes at window 8 — unmoved, since all three gamma witnesses
    still attend the same rounds and hold the same gamma facts regardless of the
    window.

    WHAT A LOOSER READING WOULD HAVE SAID, kept as `could` so the tight number
    can be read against it: counting, per question, how many peers ever met the
    atom first-hand at any round of the run, four units now read 85 questions no
    peer could ever have answered and 1173 answerable by exactly one (was 68 and
    956); six units read 87, 464 and 807 with two (was 72, 324 and 649). The
    looser count still credits a peer that met the atom forty rounds after the
    question closed, which is still why the decision-time count is the one
    reported.

    AT WINDOW 5, the previous default, for comparison — this is the reading the
    ruling was made on and it is kept for that reason:

    CLAUSE 1 — at least one unit's `whom_to_ask` is non-`None`: yes, exactly
    one. Of the 96 (peer, relation) records a four-unit community accumulates,
    1 ended the run positive; six units read 5 of 107.

    CLAUSE 2's matrix, 939 uptakes:

              takes from     u0     u1     u2     u3
              u0              —     22      0    189
              u1            229      —     26      0
              u2              0    197      —     21
              u3             21      0    234      —

    Each unit took about 90% of its uptake from the single peer that witnesses
    the domain its own seeded converse names — 189 of 211, 229 of 255, 197 of
    218, 234 of 255. All 939 decisions at four units had exactly one voice
    behind them. Six units: 394 of 928 decisions had two peers standing behind
    the content, all 394 independent first-hand witnesses met on the same
    round (twins), none relaying adopted testimony, and the lower-numbered
    voice answered all 394 of them. A preference was held at 23 of the 394 and
    named the answering peer every time. The looser `could` reading: four units
    68/956 at 0/1 peers; six units 72/324/649 at 0/1/2 peers.
    """
    four = _aggregate_ask(4, CYCLIC, ask=True, keys=_GATE_KEYS + _MATRIX_KEYS)
    six = _aggregate_ask(6, PAIRS, ask=True, keys=_GATE_KEYS + _MATRIX_KEYS)
    four_pref = _aggregate_ask(4, CYCLIC, ask=True, typify="prefer",
                               keys=_GATE_KEYS + _MATRIX_KEYS)
    six_pref = _aggregate_ask(6, PAIRS, ask=True, typify="prefer",
                              keys=_GATE_KEYS + _MATRIX_KEYS)

    # CLAUSE 1: no preference at all at four units any more; six still has two.
    assert sum(four["prefs"].values()) == 0
    assert sum(six["prefs"].values()) == 2
    assert four["preferences"] == 0 and six["preferences"] == 2

    # CLAUSE 2: the matrix, exactly as tabulated.
    assert dict(four["consult"]) == {
        ("u0", "u1"): 78, ("u0", "u3"): 204,
        ("u1", "u0"): 218, ("u1", "u2"): 69,
        ("u2", "u1"): 207, ("u2", "u3"): 80,
        ("u3", "u0"): 87, ("u3", "u2"): 208}
    assert sum(four["consult"].values()) == four["uptakes"] == 1151
    # NON-UNIFORM, AND EXPLAINED BY THE APERTURES: a cell is non-empty exactly
    # when the two units share a domain.
    aps = {a.unit_id: set(a.domains)
           for a in apertures_for(default_spec(), n_units=4, scheme=CYCLIC)}
    for a in sorted(aps):
        for b in sorted(aps):
            if a == b:
                continue
            assert (four["consult"][(a, b)] > 0) == bool(aps[a] & aps[b]), (
                f"{a} took from {b} in a way the apertures do not explain")
    # Roughly 70-76% of each unit's uptake comes from one peer (was ~90%).
    for a in sorted(aps):
        row = {b: n for (x, b), n in four["consult"].items() if x == a}
        assert max(row.values()) / sum(row.values()) > 0.70

    # THE DIAGNOSTIC: not one decision at four units offered a second voice.
    assert dict(four["voices"]) == {1: 1151}
    assert {n for _rel, n in four["voices_by_rel"]} == {1}
    assert sorted(rel for rel, _n in four["voices_by_rel"]) == [
        "a_head", "a_local", "b_head", "b_local", "d_head", "d_local",
        "g_head", "g_local"]
    assert four["independent"] == four["relayed"] == four["twin"] == 0
    assert four_pref["pref_choice"] == 0, (
        "a preference decided something at four units, where no decision had "
        "two voices to decide between")
    assert (four_pref["occ_pref"], four_pref["occ_bite"]) == (53, 0)

    # SIX UNITS: a choice existed, and now not every voice is first-hand.
    assert dict(six["voices"]) == {1: 715, 2: 498}
    assert six["independent"] == 469 and six["relayed"] == 29, (
        "at window 8 a second voice can now be relayed testimony, not only a "
        "first-hand twin — see the docstring's window-5-vs-8 comparison")
    assert six["twin"] == 469, (
        "every independent second voice still met the atom on the same round "
        "as the first, so among the independent decisions none are non-twins")
    # THE "LOWER-NUMBERED ANSWERS" PATTERN IS NOW ALMOST BUT NOT QUITE ABSOLUTE:
    # 481 of the 498 two-voice decisions, not all 498 (was all 394 at window 5).
    assert six["choice_lowest"] == 481
    assert four["choice_lowest"] == 0
    assert (six_pref["pref_choice"], six_pref["pref_choice_bite"]) == (25, 0)
    assert (six_pref["occ_pref"], six_pref["occ_bite"]) == (72, 0)
    # Gamma still offers nothing at six units: all three of its witnesses
    # attend the same rounds, so no peer can supply what another lacks.
    assert not [rel for rel, _n in six["voices_by_rel"] if rel.startswith("g_")]

    # THE LOOSER READING, KEPT FOR CONTRAST.
    assert dict(four["could"]) == {0: 85, 1: 1173}
    assert dict(six["could"]) == {0: 87, 1: 464, 2: 807}


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
    """Both communities, because the six-unit one is the first in this series
    whose apertures come out of `itertools.combinations` rather than a modular
    index — and because it is the only arm in which corroboration actually fires,
    so the order challenges are weighed in could matter and must not."""
    def run(n_units, scheme):
        _spec, units, board, raised, events, tally = _play_challenge(
            3, 30, channel=True, n_units=n_units, scheme=scheme)
        return ([(u.ledger.hits, u.ledger.misses, sorted(u.laws),
                  sorted(u.suspended)) for u in units],
                [(m.author, m.kind, m.content, m.counterexample)
                 for m in board.all_marks()
                 if m.kind in ("challenge", "corroboration")],
                raised, events, tally)
    assert run(4, CYCLIC) == run(4, CYCLIC)
    assert run(6, PAIRS) == run(6, PAIRS)


# --- Examination VII, amendable finding (a): peers keeps both components ----


def test_a_peer_half_wrong_is_not_a_peer_never_heard_from():
    """EXAMINATION V's V.2 COLLISION, REPRODUCED HERE AND CLOSED.

    `credit` used to write `proved - failed` as one integer, which is
    irreversible: a peer borne out ten times and failed ten times landed on the
    same 0 as a peer nobody had ever heard from, indistinguishable to
    `whom_to_ask` and to any other reader. Examination VII censused five of 96
    records sitting on that point at four units, and three of 107 at six.

    The remedy V.2 received was two moves — rename out of the doctrinal
    namespace, AND keep the constituents structurally distinct. `peers` passed
    the first and failed the second."""
    _spec, _field, tested, _u1 = _two_units()
    _spec2, _field2, silent, _u1b = _two_units()
    for i in range(10):
        tested.credit(Mark("u1", ("q1", (("c", f"x{i}"),)), FACT, i), proved=True)
        tested.credit(Mark("u1", ("q1", (("c", f"y{i}"),)), FACT, i), proved=False)

    assert tested.peers["u1"]["q1"] == (10, 10)
    assert silent.peers == {}
    assert tested.peers["u1"]["q1"] != silent.peers.get("u1", {}).get("q1")
    # and the derived score still reads the same as it always did
    assert tested.whom_to_ask("q1") is None
    assert silent.whom_to_ask("q1") is None


def test_the_derived_score_is_what_whom_to_ask_still_reads():
    _spec, _field, u, _u1 = _two_units()
    for i in range(3):
        u.credit(Mark("u1", ("q1", (("c", f"x{i}"),)), FACT, i), proved=True)
    u.credit(Mark("u2", ("q1", (("c", "z"),)), FACT, 0), proved=True)
    u.credit(Mark("u2", ("q1", (("c", "w"),)), FACT, 1), proved=False)
    assert u.peers["u1"]["q1"] == (3, 0)
    assert u.peers["u2"]["q1"] == (1, 1)
    assert u.whom_to_ask("q1") == "u1"          # 3 beats 0, as before
