# tests/test_c_marks.py
import dataclasses

import pytest

from c_field import Field, apertures_for, default_spec
from c_marks import Mark, MarkBoard
from c_unit import Unit

M1 = Mark(author="u0", content=("p1", (("c", "a1"),)), kind="fact", round_idx=0)


def _setup(seed=7):
    spec = default_spec(seed=seed)
    return spec, Field(spec), apertures_for(spec, n_units=4)


def _unary(rel, names):
    return {(rel, (("c", n),)) for n in names}


# --- the mark: an attributed inscription -------------------------------------


def test_a_mark_carries_its_author_so_uptake_is_attributable():
    board = MarkBoard()
    board.publish(M1)
    assert board.all_marks() == [M1]
    assert M1.author == "u0"


def test_a_mark_is_frozen_and_hashable_so_it_can_key_uptake():
    assert {M1: {"u1"}}[M1] == {"u1"}
    with pytest.raises(dataclasses.FrozenInstanceError):
        M1.author = "u9"            # type: ignore[misc]


def test_a_mark_refuses_a_kind_it_cannot_dispose_of():
    """`adopt` dispatches on `kind`; an unknown kind would reach it as content
    of no known sort, so it is refused where it is minted rather than where it
    is read."""
    with pytest.raises(ValueError, match="kind"):
        Mark(author="u0", content=("p1", "q1"), kind="opinion", round_idx=0)


def test_a_mark_refuses_content_that_does_not_match_its_kind():
    """A fact and a law are both 2-tuples, so only `kind` tells them apart. A
    law-shaped tuple filed as a fact would land in `Unit.facts` and only fail
    much later, in `as_egi`, as an unrelated-looking error."""
    with pytest.raises(ValueError, match="fact"):
        Mark(author="u0", content=("p1", "q1"), kind="fact", round_idx=0)
    with pytest.raises(ValueError, match="law"):
        Mark(author="u0", content=("p1", (("c", "a1"),)), kind="law", round_idx=0)


# --- the board: per-community, append-only, sealed ---------------------------


def test_uptake_is_recorded_per_adopter():
    board = MarkBoard()
    board.publish(M1)
    assert board.uptake_of(M1) == set()
    board.record_uptake(M1, "u1")
    board.record_uptake(M1, "u2")
    board.record_uptake(M1, "u1")           # idempotent
    assert board.uptake_of(M1) == {"u1", "u2"}


def test_since_returns_only_marks_from_that_round_onward():
    board = MarkBoard()
    board.publish(M1)
    later = Mark(author="u1", content=("p1", (("c", "a2"),)), kind="fact", round_idx=5)
    board.publish(later)
    assert board.since(5) == [later]


def test_the_board_keeps_publication_order():
    board = MarkBoard()
    a = Mark(author="u1", content=("p1", (("c", "a1"),)), kind="fact", round_idx=3)
    b = Mark(author="u0", content=("p1", (("c", "a2"),)), kind="fact", round_idx=1)
    board.publish(a)
    board.publish(b)
    assert board.all_marks() == [a, b]      # not re-sorted by round
    assert board.since(0) == [a, b]


def test_the_board_is_append_only_from_outside():
    """A caller that mutated the returned list could unpublish a mark; the
    reader hands back a copy."""
    board = MarkBoard()
    board.publish(M1)
    board.all_marks().clear()
    board.uptake_of(M1).add("nobody")
    assert board.all_marks() == [M1]
    assert board.uptake_of(M1) == set()


def test_republishing_one_mark_does_not_double_count_it():
    """An identical mark is the same author saying the same thing in the same
    round: appending it twice would inflate the published-mark count that the
    structural observable reads. A re-mention in a LATER round is a different
    mark and is kept — the board simply does not treat it as refreshing
    anything (the maintenance channel is unruled)."""
    board = MarkBoard()
    board.publish(M1)
    board.publish(M1)
    assert board.all_marks() == [M1]
    assert board.republished == 1
    again = Mark(author="u0", content=M1.content, kind="fact", round_idx=4)
    board.publish(again)
    assert board.all_marks() == [M1, again]


def test_uptake_of_an_unpublished_mark_is_refused():
    """Nothing can be taken up that was never put where it could be
    encountered, and attributing uptake to an unpublished mark would enter a
    reliance edge no reader could have formed."""
    board = MarkBoard()
    with pytest.raises(ValueError, match="not published"):
        board.record_uptake(M1, "u1")
    with pytest.raises(ValueError, match="not published"):
        board.uptake_of(M1)


def test_boards_are_sealed_between_communities():
    """Sealing is structural, not a flag: two boards share no state and there
    is no operation on a board that reads another one."""
    here, there = MarkBoard(), MarkBoard()
    here.publish(M1)
    assert there.all_marks() == []
    assert not [n for n in dir(here)
                if not n.startswith("_") and n in {"merge", "import_from", "sync"}]


# --- the assert channel on the unit -----------------------------------------


def test_a_unit_publishes_what_it_holds_and_does_not_republish_it():
    _spec, _field, aps = _setup()
    board = MarkBoard()
    u = Unit("u0", aps[0])
    u.facts.update(_unary("p1", ["x0", "x1"]))
    u.laws.add(("p1", "q1"))

    minted = u.publish(board, round_idx=0)
    assert {m.kind for m in minted} == {"fact", "law"}
    assert all(m.author == "u0" and m.round_idx == 0 for m in minted)
    assert len(minted) == 3
    assert u.publish(board, round_idx=1) == []      # nothing new to say

    u.facts.update(_unary("p1", ["x2"]))
    fresh = u.publish(board, round_idx=2)
    assert [m.content for m in fresh] == [("p1", (("c", "x2"),))]
    assert len(board.all_marks()) == 4


def test_publication_order_is_deterministic():
    _spec, _field, aps = _setup()
    contents = []
    for _ in range(3):
        board = MarkBoard()
        u = Unit("u0", aps[0])
        u.facts.update(_unary("p1", ["x2", "x0", "x1"]))
        u.laws.update({("q1", "r1"), ("p1", "q1")})
        contents.append([(m.kind, m.content) for m in u.publish(board, 0)])
    assert contents[0] == contents[1] == contents[2]


def test_a_unit_reads_the_board_but_never_its_own_marks():
    _spec, _field, aps = _setup()
    board = MarkBoard()
    mine, theirs = Unit("u0", aps[0]), Unit("u1", aps[1])
    mine.facts.update(_unary("p1", ["x0"]))
    theirs.facts.update(_unary("p2", ["y0"]))
    mine.publish(board, 0)
    theirs.publish(board, 0)

    read = mine.read(board, 0)
    assert [m.author for m in read] == ["u1"]
    assert mine.read(board, 1) == []             # nothing published since round 1


def test_adopting_a_mark_takes_up_its_content_and_records_attributable_uptake():
    _spec, _field, aps = _setup()
    board = MarkBoard()
    author, reader = Unit("u0", aps[0]), Unit("u1", aps[1])
    author.facts.update(_unary("p1", ["x0"]))
    author.laws.add(("p1", "q1"))
    fact_mark, law_mark = author.publish(board, 0)

    assert reader.adopt(fact_mark, board) is True
    assert reader.adopt(law_mark, board) is True
    assert ("p1", (("c", "x0"),)) in reader.facts
    assert ("p1", "q1") in reader.laws
    assert board.uptake_of(fact_mark) == {"u1"}
    assert board.uptake_of(law_mark) == {"u1"}


def test_adopting_twice_takes_up_nothing_new():
    _spec, _field, aps = _setup()
    board = MarkBoard()
    author, reader = Unit("u0", aps[0]), Unit("u1", aps[1])
    author.facts.update(_unary("p1", ["x0"]))
    mark, = author.publish(board, 0)
    assert reader.adopt(mark, board) is True
    assert reader.adopt(mark, board) is False
    assert board.uptake_of(mark) == {"u1"}


def test_uptake_is_not_recorded_for_content_the_reader_already_held():
    """THE ATTRIBUTION IS HONEST OR IT MEASURES NOTHING. Uptake is the
    structural observable — who relies on whom — so it is recorded only when
    the mark actually changed the reader's model. A reader that had already
    found the content itself credits the author with nothing."""
    _spec, _field, aps = _setup()
    board = MarkBoard()
    author, reader = Unit("u0", aps[0]), Unit("u1", aps[1])
    author.facts.update(_unary("p1", ["x0"]))
    mark, = author.publish(board, 0)
    reader.facts.update(_unary("p1", ["x0"]))        # arrived at it independently
    assert reader.adopt(mark, board) is False
    assert board.uptake_of(mark) == set()


def test_a_unit_may_not_adopt_its_own_mark():
    """A self-edge in the attribution graph would say a unit relies on itself,
    which is not reliance; `read` already excludes own marks, so reaching here
    is a caller's error and is named."""
    _spec, _field, aps = _setup()
    board = MarkBoard()
    u = Unit("u0", aps[0])
    u.facts.update(_unary("p1", ["x0"]))
    mark, = u.publish(board, 0)
    with pytest.raises(ValueError, match="own mark"):
        u.adopt(mark, board)


def test_an_adopted_law_changes_what_the_reader_anticipates():
    """The channel has epistemic teeth: what crosses is a sign, and the reader's
    interpretant of it is whatever its OWN record makes of it — the law is
    chained over the reader's own facts, not the author's."""
    _spec, _field, aps = _setup()
    board = MarkBoard()
    author, reader = Unit("u0", aps[0]), Unit("u1", aps[1])
    author.laws.add(("p1", "q1"))
    law_mark, = author.publish(board, 0)
    reader.facts.update(_unary("p1", ["own0"]))      # the reader's own individual
    assert reader.anticipate() == set()
    reader.adopt(law_mark, board)
    assert reader.anticipate() == {("q1", (("c", "own0"),))}


# --- THE RULING: an adopted fact is held, but it is not dated ----------------


def test_an_adopted_fact_is_held_but_carries_no_first_arrival():
    """`first_seen` records what reached THIS unit's membrane from the field.
    An adopted mark reached it from a peer, so it enters `facts` and is not
    dated — see `Unit.adopt`'s docstring for the argument."""
    _spec, _field, aps = _setup()
    board = MarkBoard()
    author, reader = Unit("u0", aps[0]), Unit("u1", aps[1])
    author.facts.update(_unary("p1", ["x0"]))
    mark, = author.publish(board, 9)
    reader.adopt(mark, board)
    assert ("p1", (("c", "x0"),)) in reader.facts
    assert reader.first_seen == {}


def test_a_later_first_hand_delivery_dates_a_fact_that_was_adopted_first():
    """Adoption does not consume the date. If the field later delivers the same
    fact, THAT is the unit's first first-hand encounter and it is recorded."""
    _spec, field, aps = _setup()
    board = MarkBoard()
    author, reader = Unit("u0", aps[0]), Unit("u1", aps[1])
    delivered = set(field.at(reader.aperture, 3))
    one = sorted(delivered)[0]
    author.facts.add(one)
    mark, = author.publish(board, 0)
    reader.adopt(mark, board)
    assert reader.first_seen == {}
    reader.absorb(field, 3)
    assert reader.first_seen[one] == 3


def test_testimony_cannot_mislead_precedence_and_defeat_a_true_law():
    """THE DECISIVE CASE, and why the ruling is what it is.

    A unit has three first-hand supporters of `p1 -> q1` with the body seen
    first — the field's own lag, correctly observed. It then adopts twenty `p1`
    facts from a peer, about individuals whose `q1` it happened to observe
    early. Those twenty say nothing about direction: the unit never saw their
    bodies arrive at all.

    Stamped with the ADOPTION round they would say the opposite of nothing:
    twenty supporters with the body apparently second, outvoting the three
    real observations, and the true law would be refused on the strength of
    when a peer got round to mentioning it. The second arm below builds exactly
    that state by hand and shows the refusal, so the ruling is demonstrated
    rather than asserted."""
    _spec, _field, aps = _setup()
    board = MarkBoard()
    peer = Unit("u0", aps[0])
    peer.facts.update(_unary("p1", [f"y{i}" for i in range(20)]))
    marks = peer.publish(board, 9)

    honest = Unit("u1", aps[1])
    honest._record(_unary("q1", [f"y{i}" for i in range(20)]), 0)
    honest._record(_unary("p1", ["z0", "z1", "z2"]), 1)
    honest._record(_unary("q1", ["z0", "z1", "z2"]), 2)
    for m in marks:
        honest.adopt(m, board)
    assert ("p1", "q1") in honest.induce(min_support=3, max_pending_rate=0.05)

    hearsay = Unit("u2", aps[2])
    hearsay._record(_unary("q1", [f"y{i}" for i in range(20)]), 0)
    hearsay._record(_unary("p1", ["z0", "z1", "z2"]), 1)
    hearsay._record(_unary("q1", ["z0", "z1", "z2"]), 2)
    hearsay._record(_unary("p1", [f"y{i}" for i in range(20)]), 9)   # dated by testimony
    assert ("p1", "q1") not in hearsay.induce(min_support=3,
                                              max_pending_rate=0.05)


def test_adopted_facts_still_count_as_support_and_as_refutation():
    """The ruling withholds only the DATE. Adopted content is still evidence:
    it enlarges support, and it can still leave a law's antecedent pending and
    so refute it."""
    _spec, _field, aps = _setup()
    board = MarkBoard()
    peer = Unit("u0", aps[0])
    peer.facts.update(_unary("p1", ["x0", "x1", "x2"]))
    peer.facts.update(_unary("q1", ["x0", "x1", "x2"]))
    published = peer.publish(board, 0)

    supported = Unit("u1", aps[1])
    for m in published:
        supported.adopt(m, board)
    assert ("p1", "q1") in supported.induce(min_support=3,
                                            max_pending_rate=0.05)

    refuted = Unit("u2", aps[2])
    refuted._record(_unary("p1", ["w0", "w1", "w2"]), 0)
    refuted._record(_unary("q1", ["w0", "w1", "w2"]), 1)
    stray = Mark(author="u0", content=("p1", (("c", "w9"),)), kind="fact",
                 round_idx=2)
    board.publish(stray)
    refuted.adopt(stray, board)                  # 1 pending of 4 = 0.25 > 0.05
    assert ("p1", "q1") not in refuted.induce(min_support=3,
                                              max_pending_rate=0.05)


def test_adoption_does_not_disturb_anticipate_before_observe():
    """Publishing and reading are separate acts from `step`, which is
    untouched: the bet is still placed before the round's arrivals are seen."""
    _spec, field, aps = _setup()
    board = MarkBoard()
    u = Unit("u0", aps[0])
    u.laws.add(field.domain("alpha").law)
    for r in range(5):
        u.step(field, r)
        u.publish(board, r)
    assert u.ledger.entries
    assert board.all_marks()
    assert set(u.first_seen) == u.facts       # every dated fact is first-hand
