"""Tests for the legible EGI diff (src/egi_diff.py).

The diff explains *how* two EGIs differ, in EG vocabulary — the discrepancy report
behind challenge mode. It must: report nothing for the same graph (incl. isomorphic
copies); name missing/extra relations and individuals; catch scope (wrong cut /
polarity — the gold Beta error); catch incidence (wrong connections); and catch
argument order. Aligned by content, not element id.

See docs/FREEFORM_COMPOSITION_AND_LEARNING.md (build step 3).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egi_diff import legible_diff
from egif_parser_dau import parse_egif
from elk_layout_engine import ELKLayoutEngine
from eg_reader import assign_order_labels
from drawing_to_egi import build_egi_from_drawing
from style_loader import load_default_style


def _kinds(report):
    return [f.kind for f in report.findings]


def _subjects(report, kind):
    return {f.subject for f in report.findings if f.kind == kind}


# --------------------------------------------------------------------------- #
# Same graph → no findings (incl. isomorphic copies from a different source).
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("egif", [
    "(man *x)",
    '(loves "Romeo" "Juliet")',
    "~[ (P *x) ~[ (Q x) ] ]",
])
def test_same_graph_no_findings(egif):
    egi = parse_egif(egif)
    rep = legible_diff(egi, egi)
    assert rep.matches and rep.findings == []


def test_isomorphic_via_drawing_no_findings(egif="~[ (P *x) ~[ (Q x) ] ]"):
    """An EGI vs the EGI recovered from its own drawing (different element ids) —
    content-aligned, so no spurious differences."""
    egi = parse_egif(egif)
    dto = assign_order_labels(egi, ELKLayoutEngine().generate_layout(egi, load_default_style()))
    pl = {e.id: egi.get_relation_name(e.id) for e in egi.E}
    vl = {v.id: v.label for v in egi.V}
    built = build_egi_from_drawing(dto, pl, vl)
    rep = legible_diff(egi, built)
    assert rep.matches, [f.message for f in rep.findings]


# --------------------------------------------------------------------------- #
# Missing / extra relations.
# --------------------------------------------------------------------------- #


def test_missing_relation():
    target = parse_egif("(P *x) (Q x)")
    attempt = parse_egif("(P *x)")
    rep = legible_diff(target, attempt)
    assert not rep.matches
    assert "Q" in _subjects(rep, "missing")


def test_extra_relation():
    target = parse_egif("(P *x)")
    attempt = parse_egif("(P *x) (Q x)")
    rep = legible_diff(target, attempt)
    assert "Q" in _subjects(rep, "extra")


# --------------------------------------------------------------------------- #
# Argument order vs incidence.
# --------------------------------------------------------------------------- #


def test_argument_order_difference():
    target = parse_egif('(loves "Romeo" "Juliet")')
    attempt = parse_egif('(loves "Juliet" "Romeo")')
    rep = legible_diff(target, attempt)
    assert "order" in _kinds(rep)
    # Same individuals, so it is NOT reported as missing/extra/incidence.
    assert "missing" not in _kinds(rep) and "incidence" not in _kinds(rep)


def test_incidence_difference():
    target = parse_egif('(loves "Romeo" "Juliet")')
    attempt = parse_egif('(loves "Romeo" "Caesar")')
    rep = legible_diff(target, attempt)
    assert "incidence" in _kinds(rep)
    assert "Juliet" in _subjects(rep, "missing")
    assert "Caesar" in _subjects(rep, "extra")


# --------------------------------------------------------------------------- #
# Scope — the gold Beta error (right relation, wrong cut).
# --------------------------------------------------------------------------- #


def test_scope_difference_in_scroll():
    """The scroll ∀x(P→Q): Q belongs inside the inner cut (depth 2, positive). An
    attempt that drops Q in the outer cut (depth 1, negative) is a scope error —
    the classic mistake challenge mode is built to catch."""
    target = parse_egif("~[ (P *x) ~[ (Q x) ] ]")
    attempt = parse_egif("~[ (P *x) (Q x) ]")
    rep = legible_diff(target, attempt)
    assert not rep.matches
    assert "Q" in _subjects(rep, "scope")
    assert "structure" in _kinds(rep)        # one fewer cut
    msg = " ".join(f.message for f in rep.by_kind("scope"))
    assert "cut" in msg and "should be" in msg


def test_constant_scope_difference():
    target = parse_egif('~[ (mortal "Socrates") ]')   # Socrates inside the cut
    attempt = parse_egif('(mortal "Socrates")')        # on the sheet
    rep = legible_diff(target, attempt)
    assert "scope" in _kinds(rep)
    assert "Socrates" in _subjects(rep, "scope")


# --------------------------------------------------------------------------- #
# Reflexivity of the summary.
# --------------------------------------------------------------------------- #


def test_summary_reads_match_and_mismatch():
    same = legible_diff(parse_egif("(P *x)"), parse_egif("(P *x)"))
    assert "same graph" in same.summary.lower()
    diff = legible_diff(parse_egif("(P *x)"), parse_egif("(Q *x)"))
    assert "difference" in diff.summary.lower()
