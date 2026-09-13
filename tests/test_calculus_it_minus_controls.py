"""IT- deiterating what is not a copy, held by collected tests (Dau Def 15.2,
p.164-166).

Deiteration erases only what iteration could have inserted, and iteration
hooks a copy to an outside vertex only along the same line.

History. The engine ignored the identity of every vertex outside the copy,
names included, so it erased candidates that are not copies, and on these
hand-built controls the result was UNSOUND — ledger entries
it-minus-erases-a-copy-of-another-line (refusal, SEVERE) and its soundness
half it-minus-erases-a-copy-of-another-line-changes-meaning. The corpus
instances of those entries happened to be inert, so a partial fix to IT- could
shrink the ledger and go green while these survived: the controls were the
instrument that told a real repair from a partial one. Each unsound
application was a strict xfail, so a fix flipped it to XPASS, which strict
mode failed until the xfail was removed.

FIXED by this arc's Task 6, commit "IT- erases only a copy, not a look-alike
(Dau Def 15.2, p.166)": DeiterationRule._check_deiteration_with_isomorphism_engine
now filters the isomorphism engine's structural matches through
_match_is_a_copy, and both ledger entries were retired. The three xfails are
gone; what stands below is the positive fact — each of the three is refused,
with the copy condition's message, and legal() still finds no source. The
controls are calculus_adjudication's, so the script's printed figures and
these tests cover one list.
"""
import pytest

from calculus_adjudication import IT_MINUS_CONTROLS, control_selection
from calculus_apply import apply_move
from calculus_layers import soundness
from calculus_rules import Move, legal
from calculus_run import MODES, Record
from egif_parser_dau import parse_egif

ANOTHER_LINE = "*x *y (P x) ~[ (P y) ]"
NAME_AGAINST_LINE = '*y (P "a") ~[ (P y) ]'
NAME_INSIDE_THE_COPY = '(P "a") ~[ (P "b") ]'
NAME_AGAINST_NAME = '(Q "a") (Q "b") ~[ (P "b") ] ~[ ~[ (P "a") ] ]'
APPLIED = {"another-line": ANOTHER_LINE, "name-against-line": NAME_AGAINST_LINE,
           "name-against-name": NAME_AGAINST_NAME}

# The copy condition's refusal, from DeiterationRule (Dau Def 15.2, p.166).
COPY_REFUSAL = "No isomorphic original found whose edges reach the same lines"


def _case(text):
    g = parse_egif(text)
    m = Move("IT-", control_selection(g))
    verdict, why = legal(g, m)
    rec = Record("A", "control", g, m, f"control|{text}", apply_move(g, m), verdict, why)
    return rec, soundness(rec, {"_sem": MODES["default"].sem})


def test_the_controls_are_these():
    assert set(IT_MINUS_CONTROLS) == {*APPLIED.values(), NAME_INSIDE_THE_COPY}


@pytest.mark.parametrize("text", IT_MINUS_CONTROLS)
def test_legal_finds_no_source_for_any_control(text):
    rec, _ = _case(text)
    assert (rec.verdict, rec.why) == (False, "no source of which this is a copy")


def test_a_name_inside_the_copy_is_compared_and_refused():
    """The refusal the entry recorded: the vertex of "b" sits in the cut with
    the candidate edge, where the engine compares it — so this one was always
    refused, before the copy condition and after it."""
    rec, (label, detail) = _case(NAME_INSIDE_THE_COPY)
    out = rec.outcome
    assert not out.applied and not out.crashed
    assert "No isomorphic original found" in out.message
    assert (label, detail) == ("not:IT-:refused", None)


@pytest.mark.parametrize("text", list(APPLIED.values()), ids=list(APPLIED))
def test_a_non_copy_is_not_deiterated(text):
    """Each of the three the engine used to deiterate is now refused by the
    copy condition, and legal() still finds no source of which the candidate
    is a copy (Dau Def 15.2, p.166: iteration copies G0's vertices fresh and
    reaches an outside vertex only along that same line)."""
    rec, (label, detail) = _case(text)
    out = rec.outcome
    assert not out.applied and not out.crashed, out.message
    assert COPY_REFUSAL in out.message, out.message
    assert "Dau Def 15.2, p.166" in out.message, out.message
    # legal() judged these illegal all along; the engine now agrees.
    assert (rec.verdict, rec.why) == (False, "no source of which this is a copy")
    # A refused move is not evaluated for soundness: nothing left to be UNSOUND.
    assert (label, detail) == ("not:IT-:refused", None)
