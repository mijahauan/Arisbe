"""
Contract tests for challenge mode (``src/challenge_mode.py``).

Design-of-record: ``docs/FREEFORM_COMPOSITION_AND_LEARNING.md`` (build step 4).

The grading core is EGI-vs-EGI (``same_graph`` + the legible diff); the drawing→EGI
path is tested in ``test_drawing_to_egi.py``.  These pin: the bank parses and is a
gradient; an attempt that denotes the same graph passes regardless of surface form;
and a wrong attempt fails with the *right* EG-vocabulary finding.
"""

from egif_parser_dau import parse_egif

from challenge_mode import (
    CHALLENGE_BANK,
    Challenge,
    get_challenge,
    grade,
    list_challenges,
    list_dragons,
)


# ---------------------------------------------------------------------------
# The bank
# ---------------------------------------------------------------------------

def test_bank_is_non_empty_with_unique_ids():
    assert CHALLENGE_BANK
    ids = [c.id for c in CHALLENGE_BANK]
    assert len(ids) == len(set(ids))


def test_every_prompt_parses():
    for c in CHALLENGE_BANK:
        egi = parse_egif(c.prompt_egif)  # raises on a malformed prompt
        assert egi is not None


def test_list_is_sorted_by_difficulty():
    diffs = [c.difficulty for c in list_challenges()]
    assert diffs == sorted(diffs)


def test_get_challenge_found_and_missing():
    assert isinstance(get_challenge("universal"), Challenge)
    assert get_challenge("no-such-challenge") is None


def test_gradient_spans_easy_to_hard():
    diffs = {c.difficulty for c in CHALLENGE_BANK}
    assert min(diffs) == 1
    assert max(diffs) >= 5  # the universal: a line crossing a cut boundary


# ---------------------------------------------------------------------------
# The drawable-dragon walk (docs/FIELD_GUIDE_AND_DRAGONS.md)
# ---------------------------------------------------------------------------

def test_list_dragons_covers_the_five_drawable_pitfalls():
    dragons = list_dragons()
    # Dragons 1–5 are the drawable ones; 6–8 are conceptual (not in the bank).
    assert [c.dragon for c in dragons] == [1, 2, 3, 4, 5]


def test_every_dragon_challenge_carries_an_antidote():
    for c in list_dragons():
        assert c.antidote, f"{c.id} (dragon {c.dragon}) must carry a field-guide antidote"
        assert c.temptation, f"{c.id} (dragon {c.dragon}) must name the common temptation"


def test_empty_cut_is_false_and_grades_itself():
    # 🐉2: a cut around nothing — its own faithful render must grade as a match.
    c = get_challenge("empty-cut")
    assert c is not None and c.dragon == 2
    assert grade(c.prompt_egif, parse_egif(c.prompt_egif)).matches


def test_removable_double_cut_is_not_the_scroll():
    # 🐉3: the removable double cut and the scroll look alike but are different
    # graphs — the scroll has content in the ring between the two cuts.
    double = parse_egif(get_challenge("double-cut").prompt_egif)
    scroll = parse_egif(get_challenge("scroll").prompt_egif)
    assert not grade(scroll, double).matches


# ---------------------------------------------------------------------------
# Grading — a correct attempt passes regardless of surface form
# ---------------------------------------------------------------------------

def test_identical_attempt_passes():
    for c in CHALLENGE_BANK:
        report = grade(c.prompt_egif, parse_egif(c.prompt_egif))
        assert report.matches, f"{c.id} should grade its own prompt as a match"
        assert report.findings == []


def test_target_may_be_prebuilt_egi():
    target = parse_egif('(man "Socrates")')
    assert grade(target, parse_egif('(man "Socrates")')).matches


def test_same_graph_different_variable_name_passes():
    # The universal, drawn with a different (still generic) line — same graph.
    target = '~[ (man *x) ~[ (mortal x) ] ]'
    attempt = parse_egif('~[ (man *y) ~[ (mortal y) ] ]')
    assert grade(target, attempt).matches


# ---------------------------------------------------------------------------
# Grading — wrong attempts fail with the right finding
# ---------------------------------------------------------------------------

def test_argument_order_error_is_reported():
    report = grade('(loves "Romeo" "Juliet")', parse_egif('(loves "Juliet" "Romeo")'))
    assert not report.matches
    assert report.by_kind("order")


def test_extra_relation_is_reported():
    report = grade('(man "Socrates")', parse_egif('(man "Socrates") (mortal "Socrates")'))
    assert not report.matches
    assert report.by_kind("extra")


def test_missing_relation_is_reported():
    report = grade('(man "Socrates") (mortal "Socrates")', parse_egif('(man "Socrates")'))
    assert not report.matches
    assert report.by_kind("missing")


def test_scope_error_on_the_scroll_is_reported():
    # Target: man and mortal in *nested* cuts (the scroll).  Attempt: both in one
    # cut — the inner negation is gone, so the cut count (structure) differs.
    target = '~[ (man "Socrates") ~[ (mortal "Socrates") ] ]'
    attempt = parse_egif('~[ (man "Socrates") (mortal "Socrates") ]')
    report = grade(target, attempt)
    assert not report.matches
    assert report.by_kind("structure") or report.by_kind("scope")
