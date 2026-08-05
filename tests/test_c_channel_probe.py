# tests/test_c_channel_probe.py
"""The instrument's own tests. It found a dead channel in D-1 and is about to be
pointed at the C-series' published figures, so it is tested before it is trusted."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest  # noqa: E402

from c_channel_probe import (_effect, ablating, audited, channel_calls,  # noqa: E402
                             muted)
from c_field import apertures_for, default_spec  # noqa: E402
from c_marks import MarkBoard  # noqa: E402
from c_unit import Disposition, Unit  # noqa: E402

A1 = (("c", "a1"),)


def _two_units():
    spec = default_spec(seed=20260728)
    aps = apertures_for(spec, n_units=4)
    return Unit("u0", aps[0]), Unit("u1", aps[1])


def test_a_channel_that_mints_is_counted_as_a_call_and_an_effect():
    u0, _u1 = _two_units()
    u0._record({("p1", A1)}, 0)
    board = MarkBoard()
    with channel_calls() as tally:
        marks = u0.publish(board, 0)
    assert len(marks) == 1
    assert tally.calls["publish"] == 1
    assert tally.effects["publish"] == 1
    assert tally.silent() == ()


def test_a_channel_with_nothing_to_say_is_a_call_with_no_effect():
    """THE WHOLE POINT OF THE INSTRUMENT. A call that mints nothing is invisible
    to every figure a sweep prints, and this is where it becomes visible."""
    u0, _u1 = _two_units()
    board = MarkBoard()
    with channel_calls() as tally:
        assert u0.publish(board, 0) == []
    assert tally.calls["publish"] == 1
    assert tally.effects["publish"] == 0
    assert tally.silent() == ("publish",)


def test_muting_a_channel_puts_no_mark_on_the_board():
    """Replacement, not wrapping: `publish` mints onto the board as a side
    effect, so a counting wrapper would leave the channel running."""
    u0, _u1 = _two_units()
    u0._record({("p1", A1)}, 0)
    board = MarkBoard()
    with muted("publish"):
        assert u0.publish(board, 0) == []
    assert board.all_marks() == []
    assert len(u0.publish(board, 0)) == 1        # restored on exit


def test_a_muted_channel_is_not_reported_silent():
    """A channel the ablation removed on purpose is not a defect, and the two
    must not read alike."""
    u0, _u1 = _two_units()
    board = MarkBoard()
    with muted("publish"), channel_calls() as tally:
        u0.publish(board, 0)
    assert tally.calls["publish"] == 1
    assert tally.silent() == ()


def test_the_originals_are_restored_after_an_exception():
    original = Unit.publish
    with pytest.raises(RuntimeError):
        with channel_calls():
            raise RuntimeError("boom")
    assert Unit.publish is original
    with pytest.raises(RuntimeError):
        with muted("publish"):
            raise RuntimeError("boom")
    assert Unit.publish is original


def test_ask_reports_one_effect_for_a_mark_and_none_for_silence():
    assert _effect("ask", None) == 0
    assert _effect("ask", object()) == 1


def test_adopt_reports_its_boolean():
    assert _effect("adopt", True) == 1
    assert _effect("adopt", False) == 0


def test_dispose_sums_the_five_outcome_lists_and_counts_questions_apart():
    """D-1's definition, kept so the two audits are comparable: the five outcome
    lists are the effect, and the questions an inquiry publishes are reported
    beside it rather than folded in."""
    d = Disposition(suspended=[("p1", "q1")], restored_by_silence=[("p2", "q2")])
    assert _effect("dispose_challenges", d) == 2


def test_the_audited_decorator_refuses_a_silent_channel():
    board = MarkBoard()

    @audited()
    def arm():
        u0, _u1 = _two_units()
        return u0.publish(board, 0)

    with pytest.raises(AssertionError, match="publish"):
        arm()


def test_the_audited_decorator_accepts_a_declared_silence():
    board = MarkBoard()

    @audited()
    def arm():
        u0, _u1 = _two_units()
        return u0.publish(board, 0)

    assert arm(expect_silent=("publish",)) == []


def test_the_guard_bites_on_a_real_harness(monkeypatch):
    """THE GUARD MADE TO FAIL ONCE, ON PURPOSE, ON A PUBLISHED HARNESS. A guard
    nobody has watched fail is a guard nobody knows the shape of — D-1's
    mortality guard passed a fully installed TTL because it was never made to
    bite, and the C-series' corroboration gate passed a channel that had never
    minted a mark.

    A DEAD CHANNEL DOES NOT LOOK LIKE A MUTED ONE, which is why the bite is
    staged this way. `muted()` is the ablation device, and `ChannelTally.silent`
    excludes what it silences on purpose — that is
    `test_a_muted_channel_is_not_reported_silent`, above — so muting `answer`
    here would prove nothing about a defect: the guard is built not to fire on
    a deliberate ablation. What a defect actually looks like is instead the
    method itself returning an empty list every time it is called
    while the arm goes on reporting figures — `Unit.corroborate`'s condition in
    twenty published arms, reproduced here on `Unit.answer`, whose 410 mints
    `_play` genuinely depends on."""
    from test_c_channels import _play

    monkeypatch.setattr(Unit, "answer", lambda self, board, r: [])
    with pytest.raises(AssertionError, match="answer"):
        _play(1, 10, channel=True, stagger=2)


def test_the_audited_decorator_stands_down_while_ablating():
    """An ablation legitimately silences downstream channels, so the standing
    assertion is suspended for the duration rather than worked around."""
    board = MarkBoard()

    @audited()
    def arm():
        u0, _u1 = _two_units()
        return u0.publish(board, 0)

    with ablating():
        assert arm() == []
