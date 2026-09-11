"""Soundness, strict (spec 2026-09-10 §5.3). The instrument is shown to bite
on hand-built wrong results before its silence on the engine means anything."""
import pytest

from calculus_apply import Outcome
from calculus_layers import soundness
from calculus_ledger import assert_extent, check_ledger
from calculus_rules import Move
from calculus_run import MODES, Record, run
from egif_parser_dau import parse_egif


def _check(rule, g_text, h_text):
    g, h = parse_egif(g_text), parse_egif(h_text)
    rec = Record("A", "hand", g, Move(rule, ()), "hand|key", Outcome(True, h, ""), True, "")
    return soundness(rec, {"_sem": MODES["default"].sem})


def test_the_instrument_catches_an_unsound_erasure():
    # erasing inside a negative context: ~[ (P x) ] -> ~[ ], always false
    label, detail = _check("ERA", "~[ (P *x) ]", "~[ ]")
    assert detail and detail.startswith("UNSOUND")


def test_the_instrument_catches_a_lost_equivalence():
    # sound as an erasure, but DC+ claims an equivalence
    label, detail = _check("DC+", "(P *x) (Q *y)", "(P *x)")
    assert detail and detail.startswith("NOT AN EQUIVALENCE")


def test_the_instrument_passes_a_true_equivalence():
    assert _check("DC+", "(P *x)", "~[ ~[ (P *x) ] ]")[1] is None


def _layer(mode):
    lr = run(mode).layers["soundness"]
    problems = check_ledger("soundness", lr.evaluated_ledgered, lr.failures)
    assert not problems, "\n\n".join(problems)


def test_soundness():
    _layer("default")


def test_soundness_extent():
    assert_extent("default:soundness", dict(sorted(run("default").layers["soundness"].counts.items())))


@pytest.mark.exhaustive
def test_soundness_exhaustive():
    _layer("exhaustive")


@pytest.mark.exhaustive
def test_soundness_extent_exhaustive():
    assert_extent("exhaustive:soundness",
                  dict(sorted(run("exhaustive").layers["soundness"].counts.items())))
