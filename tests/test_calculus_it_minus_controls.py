"""IT- deiterating what is not a copy, held by collected tests (Dau Def 15.2,
p.164-166; ledger entry it-minus-erases-a-copy-of-another-line and its
soundness half it-minus-erases-a-copy-of-another-line-changes-meaning).

Deiteration erases only what iteration could have inserted, and iteration
hooks a copy to an outside vertex only along the same line. The engine ignores
the identity of every vertex outside the copy, names included, so it erases
candidates that are not copies, and on these hand-built controls the result is
UNSOUND. The corpus instances of the entry happen to be inert, so a partial
fix to IT- could shrink the ledger and go green while these survive: the
controls are the instrument that tells a real repair from a partial one.

Each unsound application is a strict xfail. A fix to IT- flips it to XPASS,
which strict mode fails until the xfail is removed — the ledger's SHRINK
discipline, applied to the controls. The controls are calculus_adjudication's,
so the script's printed figures and these tests cover one list.
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

XFAIL_REASON = (
    "ledger it-minus-erases-a-copy-of-another-line (refusal, SEVERE) and "
    "it-minus-erases-a-copy-of-another-line-changes-meaning (soundness): Dau Def 15.2 "
    "deiteration (p.164-166) erases only what iteration could have inserted; the engine "
    "deiterates this non-copy and the result is UNSOUND. XPASS means IT- was fixed: "
    "remove this xfail and shrink those entries.")


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
    """The refusal the entry records: the vertex of "b" sits in the cut with
    the candidate edge, where the engine compares it."""
    rec, (label, detail) = _case(NAME_INSIDE_THE_COPY)
    out = rec.outcome
    assert not out.applied and not out.crashed
    assert "No isomorphic original found" in out.message
    assert (label, detail) == ("not:IT-:refused", None)


@pytest.mark.xfail(strict=True, raises=AssertionError, reason=XFAIL_REASON)
@pytest.mark.parametrize("text", list(APPLIED.values()), ids=list(APPLIED))
def test_a_non_copy_is_not_deiterated(text):
    rec, (label, detail) = _case(text)
    out = rec.outcome
    # The recorded fact: the engine applies the move and the result is UNSOUND.
    # Anything else — a crash, or an application that is no longer UNSOUND —
    # is a change to read, not a fix, and fails outright (not an xfail).
    if out.crashed or (out.applied and not (detail or "").startswith("UNSOUND")):
        pytest.fail(f"the recorded fact moved: applied={out.applied} crashed={out.crashed} "
                    f"soundness={label} {detail} {out.message[:120]}")
    assert not out.applied, f"the engine deiterates a non-copy: {detail}"
