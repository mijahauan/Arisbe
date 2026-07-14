"""**The two acts by which M changes** (`src/model_acts.py`) — and their asymmetry.

The author's question: M contains "all swans are white"; how do we erase it, when ERA
works only in a positive context — and how do we *add* anything, when INS works only
in a negative one?

Working it out gives two completely different answers, and the difference is the
doctrine:

* **Erasing from M IS a rule.** M's laws sit on the sheet, which is *positive*, and
  ERA erases from a positive context. Relinquishing is a genuine Dau ERA and it is
  **sound** — erasure weakens (M ⊨ M−X). You may always come to believe *less*.
* **Adding to M is NOT a rule.** INS reaches only negative contexts, and no rule of
  any kind puts new content in a positive one. Admitting a fact is **juxtaposition**
  — the act of assertion itself — which is ampliative and enters from *outside* the
  calculus. It costs **warrant**.

    The calculus can license you to GIVE UP a belief.
    It can never license you to ACQUIRE one.

And: the same graph, in two places, is two different speech acts — the polarity of the
place decides.
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from contest_context import open_arena  # noqa: E402
from egif_generator_dau import generate_egif  # noqa: E402
from egif_parser_dau import parse_egif  # noqa: E402
from model_acts import (  # noqa: E402
    ASSERT, RELINQUISH, UnwarrantedAssertion, assert_into, relinquish, speech_act_of,
)
from proof_authoring import apply_rule  # noqa: E402

LAW = '~[ (swan *x) ~[ (white x) ] ]'
M = f'(swan "Ciel") (white "Ciel") {LAW}'


# --- erasing from M: a rule, and a sound one -------------------------------- #

def test_relinquishing_a_law_is_a_genuine_ERA():
    """M's laws sit on the SHEET, which is positive — and ERA erases from a positive
    context. So giving up "all swans are white" is a real Dau rule application."""
    m2, act = relinquish(parse_egif(M), LAW)
    assert act.kind == RELINQUISH
    assert act.is_rule, "erasing from the positive sheet IS ERA"
    assert act.sound, "erasure weakens — M ⊨ M−law; it can never make you assert a falsehood"
    out = generate_egif(m2)
    assert "swan" in out and "~[" not in out          # the facts remain; the law is gone


def test_giving_up_needs_no_warrant():
    """Logically, retraction is FREE. Coming to believe less can never make you
    wrong, so the calculus always permits it — no source required."""
    _m2, act = relinquish(parse_egif(M), LAW)
    assert act.warrant is None and act.sound


# --- adding to M: not a rule at all ----------------------------------------- #

def test_no_rule_can_put_new_content_on_the_sheet():
    """The crux. INS reaches only NEGATIVE contexts; the sheet is positive. Not one
    of the six rules can add content there — which is the calculus telling the truth:
    you cannot deduce your way to new information."""
    m = parse_egif('(swan "Ciel")')
    with pytest.raises(AssertionError, match="negative"):
        apply_rule("INS", m, egif='(black "Nox")', target=m.sheet)


def test_an_assertion_without_warrant_is_refused_and_says_why():
    """Adding to M is juxtaposition — the act of assertion — and no rule licenses it.
    So *something else* must, and the record must say what."""
    with pytest.raises(UnwarrantedAssertion, match="warrant"):
        assert_into(parse_egif(M), '(black "Nox")')


def test_an_assertion_with_warrant_lands_and_is_marked_ampliative():
    m2, act = assert_into(parse_egif(M), '(swan "Nox") (black "Nox")',
                          warrant="field report, Perth 1697")
    assert act.kind == ASSERT
    assert not act.is_rule, "no rule of inference reaches a positive context"
    assert not act.sound, "an addition is not truth-preserving — it is ampliative"
    assert act.warrant == "field report, Perth 1697"
    assert "black" in generate_egif(m2)


def test_the_refusal_points_at_the_alternative():
    """P5 (prevent, don't punish): if you only want to SUPPOSE it, the refusal tells
    you where — the negative arena, where it is free and fenced."""
    with pytest.raises(UnwarrantedAssertion, match="arena"):
        assert_into(parse_egif(M), '(black "Nox")')


# --- the same ink, two acts -------------------------------------------------- #

def test_the_polarity_of_the_place_decides_the_speech_act():
    """Insert a graph into a NEGATIVE arena and you have SUPPOSED it — free, sound,
    fenced. Scribe the identical graph on the POSITIVE sheet and you have ASSERTED
    it — no rule permits that, and you owe a warrant. Same ink; different act."""
    g, arena = open_arena(parse_egif(""))
    assert speech_act_of(g, g.sheet) == "assert"
    assert speech_act_of(g, arena.arena) == "suppose"


# --- the asymmetry, stated --------------------------------------------------- #

def test_the_asymmetry_is_total():
    """Give-up is licensed and sound. Acquire is unlicensed and ampliative. That is
    not a quirk of the implementation — it is what the six rules permit."""
    _m2, drop = relinquish(parse_egif(M), LAW)
    _m3, add = assert_into(parse_egif(M), '(black "Nox")', warrant="observed")
    assert drop.is_rule and drop.sound
    assert not add.is_rule and not add.sound
    assert drop.warrant is None and add.warrant


# --- the preparatory step is recorded on every Agon episode ------------------ #

def test_every_agon_episode_records_where_it_is_being_played():
    from web_api.services.agon_session_manager import _preparation

    blank = _preparation(parse_egif(""))
    assert blank["required"] == ["DC+"] and blank["arena_exists"] is False
    assert "no negative context" in blank["reason"]

    with_cut = _preparation(parse_egif("~[ (P) ]"))
    assert with_cut["required"] == [] and with_cut["arena_exists"] is True
