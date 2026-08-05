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


def test_the_corroborate_declarations_still_have_something_to_declare():
    """THE TRIPWIRE ON THE ALLOWLIST, AND ITS FAILURE IS THE INSTRUCTION.

    `_play_challenge` and `_play_ask_and_challenge` both declare `corroborate`
    silent, and both comments say to remove the declaration when D-A1 is fixed.
    That was prose with no mechanism behind it — the same unenforced-claim shape
    this audit spent five tasks finding, and an allowlist that outlives its
    defect re-hides the next regression with the suite green either way.

    WHEN THIS TEST FAILS, `Unit.corroborate` has minted. That means D-A1 is
    fixed, the two `expect_silent=("corroborate",)` declarations are now hiding
    a channel that can speak for itself, and BOTH MUST BE DELETED — along with
    this test, which has then done its whole job. Nothing else about a green
    suite would have said so.

    It checks the harness with its declaration REMOVED, which is the only way to
    observe a channel an allowlist is covering. Twenty rounds and four units are
    enough: the zero is structural, not a long-run or large-community effect, so
    it costs about three seconds."""
    from test_c_channels import _play_challenge

    bare = audited()(_play_challenge.__wrapped__)
    with pytest.raises(AssertionError, match="corroborate"):
        bare(20260728, 20, channel=True, stagger=1, seed_laws=True)


def test_every_measurement_harness_carries_the_guard():
    """WHAT PROTECTS THE GUARD'S OWN COVERAGE, which is otherwise three
    hand-placed decorators and nothing else.

    `@audited()` sits on `_play`, `_play_challenge` and
    `_play_ask_and_challenge` because somebody put it there. A fourth harness
    written next month, or one of these three refactored under a new name,
    silently gets no guard — and a discipline is worth exactly its coverage.
    So the rule is stated AS A RULE rather than as three decorators: every
    module-level `_play*` function in `test_c_channels.py` is audited.

    `functools.wraps` leaves `__wrapped__` on a decorated function and on
    nothing else, which is what makes the rule checkable from outside. A
    harness that genuinely must be exempt should say so where it is defined,
    not by being quietly missed here."""
    import test_c_channels

    harnesses = sorted(name for name in vars(test_c_channels)
                       if name.startswith("_play")
                       and callable(getattr(test_c_channels, name)))
    assert harnesses, "no _play* harness found — has the file been renamed?"
    unguarded = [n for n in harnesses
                 if not hasattr(getattr(test_c_channels, n), "__wrapped__")]
    assert not unguarded, (
        f"measurement harness(es) {unguarded} carry no @audited() guard, so an "
        f"arm they play could mint nothing and still report a full set of "
        f"figures. Decorate them — or, if a silence is predicted there, "
        f"decorate with expect_silent=(...) so the prediction is written down.")


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
