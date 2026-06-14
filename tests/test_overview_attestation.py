"""
Overview attestation — the navigation-projection contract.

Mirrors ``test_correspondence_attestation.py``: a corpus-ish happy path plus
adversarial units confirming each property's failure is caught.  The overview
(``docs/ADAPTIVE_SCOPE_VIEWER.md``) is a *deliberately incomplete* drawing that
collapses deep cuts into placeholders; ``attest_overview`` is the honest weaker
contract — P1 visible-part §3.3 on the quotient (which subsumes boundary-line
crossing/endpoint via synthetic boundary predicates), P2 faithful summary, and
the expansion law tying it back to full §3.3.
"""

import copy
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "web_api", "services"))

import presentation_ops as po
from correspondence_attestation import (
    OverviewViolation,
    attest_overview,
    check_correspondence,
    check_overview,
)
from egif_parser_dau import parse_egif
from layout_dto import Point
from layout_service import generate_layout
from overview_projection import (
    boundary_degree,
    boundary_incidences,
    collapse_quotient,
    frontier_placeholders,
    overview_summary,
    synthetic_boundary_id,
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _cuts_by_parent(egi):
    """Map cut_id -> parent context, via presentation_ops."""
    return po.cut_parents(egi)


def _inner_cuts(egi):
    """Cut ids that are not direct children of the sheet (nested)."""
    pm = _cuts_by_parent(egi)
    return [c for c in pm if pm[c] != egi.sheet]


def _top_cuts(egi):
    """Cut ids directly on the sheet."""
    pm = _cuts_by_parent(egi)
    return [c for c in pm if pm[c] == egi.sheet]


def _overview(egi, collapsed):
    """Build a faithful overview the way the server will: quotient -> layout.

    Returns ``(dto, summary)`` ready to feed ``check_overview`` — happy by
    construction, so adversarial tests can perturb a copy.
    """
    quotient = collapse_quotient(egi, collapsed)
    dto, _svg = generate_layout(quotient)
    summary = overview_summary(egi, collapsed)
    return dto, summary


# Graphs exercising the boundary / nesting shapes.
G_BOUNDARY = "~[ (P *x) ~[ (Q x) ] ]"     # line crosses into the inner cut
G_CLOSED = "(Man *x) ~[ (Mortal *y) ]"    # cut self-contained: no boundary line
G_NESTED = "~[ ~[ (P *x) ] ]"             # two levels for frontier-vs-hidden
G_WIDE = "(A *x) (B *y) ~[ (C *z) ] ~[ (D *w) ]"  # two sibling top cuts


# --------------------------------------------------------------------------- #
# Happy path + the expansion law
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("egif", [G_BOUNDARY, G_CLOSED, G_NESTED, G_WIDE])
def test_empty_collapse_equals_full_correspondence(egif):
    """The expansion law's base case: with nothing collapsed, an overview is a
    full drawing and ``check_overview`` agrees with ``check_correspondence``."""
    egi = parse_egif(egif)
    dto, _ = generate_layout(egi)
    assert check_overview(egi, dto, {}) == check_correspondence(egi, dto) == []


def test_boundary_collapse_attests():
    """Collapsing a cut that a line of identity enters: the synthetic boundary
    predicate carries the line into the placeholder and P1 attests it."""
    egi = parse_egif(G_BOUNDARY)
    inner = _inner_cuts(egi)[0]
    assert boundary_degree(egi, inner) == 1
    dto, summary = _overview(egi, {inner})
    assert summary[inner]["boundary_degree"] == 1
    attest_overview(egi, dto, summary)  # does not raise


def test_closed_collapse_has_no_boundary():
    """A self-contained cut collapses with zero boundary lines."""
    egi = parse_egif(G_CLOSED)
    cut = _top_cuts(egi)[0]
    assert boundary_degree(egi, cut) == 0
    dto, summary = _overview(egi, {cut})
    assert summary[cut]["boundary_degree"] == 0
    attest_overview(egi, dto, summary)


def test_wide_partial_collapse_attests():
    """Collapse one of two sibling cuts; the other stays fully drawn."""
    egi = parse_egif(G_WIDE)
    top = _top_cuts(egi)
    assert len(top) == 2
    dto, summary = _overview(egi, {top[0]})
    assert set(summary) == {top[0]}
    attest_overview(egi, dto, summary)


# --------------------------------------------------------------------------- #
# Frontier vs. hidden placeholders
# --------------------------------------------------------------------------- #

def test_nested_collapse_only_outer_is_frontier():
    """Collapsing both an outer cut and a cut nested inside it: only the outer is
    a drawn placeholder; the inner is hidden within it."""
    egi = parse_egif(G_NESTED)
    pm = _cuts_by_parent(egi)
    outer = [c for c in pm if pm[c] == egi.sheet][0]
    inner = [c for c in pm if pm[c] == outer][0]
    frontier = frontier_placeholders(egi, {outer, inner})
    assert frontier == {outer}
    # overview_summary only reports the frontier placeholder.
    summary = overview_summary(egi, {outer, inner})
    assert set(summary) == {outer}


def test_claiming_a_hidden_placeholder_fails():
    """Claiming a placeholder that is itself hidden inside another collapsed cut
    is a violation (it is not drawn)."""
    egi = parse_egif(G_NESTED)
    pm = _cuts_by_parent(egi)
    outer = [c for c in pm if pm[c] == egi.sheet][0]
    inner = [c for c in pm if pm[c] == outer][0]
    dto, _ = _overview(egi, {outer, inner})
    # Claim BOTH as placeholders — inner is not a frontier cut.
    summary = overview_summary(egi, {outer, inner})
    summary[inner] = {"cuts": 0, "vertices": 1, "predicates": 1,
                      "polarity": "negative", "boundary_degree": 0}
    failures = check_overview(egi, dto, summary)
    assert any("hidden inside another placeholder" in f for f in failures)


# --------------------------------------------------------------------------- #
# P1 adversarial — corrupt a VISIBLE element
# --------------------------------------------------------------------------- #

def test_p1_moved_visible_vertex_fails():
    """Move a visible vertex far outside its area: P1's §3.3 containment fails."""
    egi = parse_egif(G_BOUNDARY)
    inner = _inner_cuts(egi)[0]
    dto, summary = _overview(egi, {inner})
    bad = copy.deepcopy(dto)
    vid = next(iter(bad.vertex_positions))
    bad.vertex_positions[vid] = Point(99999.0, 99999.0)
    with pytest.raises(OverviewViolation):
        attest_overview(egi, bad, summary)


def test_p1_dropped_visible_ligature_fails():
    """Drop a visible ligature path: P1's §3.3 incidence fails."""
    egi = parse_egif(G_BOUNDARY)
    inner = _inner_cuts(egi)[0]
    dto, summary = _overview(egi, {inner})
    bad = copy.deepcopy(dto)
    # Drop the path for the visible predicate P (not the synthetic boundary one).
    bad.ligature_paths = [
        lp for lp in bad.ligature_paths
        if "__bnd__" in lp.predicate_id  # keep only boundary path -> drops P's
    ]
    with pytest.raises(OverviewViolation):
        attest_overview(egi, bad, summary)


# --------------------------------------------------------------------------- #
# Boundary integrity (P3 realised through P1's quotient §3.3)
# --------------------------------------------------------------------------- #

def test_boundary_line_not_crossing_placeholder_fails():
    """Reroute the boundary line so it no longer enters the placeholder: P1's
    identity-crossing check (on the synthetic predicate) fails."""
    egi = parse_egif(G_BOUNDARY)
    inner = _inner_cuts(egi)[0]
    dto, summary = _overview(egi, {inner})
    bad = copy.deepcopy(dto)
    # The synthetic boundary predicate's path lives inside the placeholder and
    # exits to the visible vertex.  Flatten it to a zero-length stub at the
    # vertex — now it never crosses the placeholder boundary.
    for lp in bad.ligature_paths:
        if "__bnd__" in lp.predicate_id:
            vpos = bad.vertex_positions[lp.vertex_id]
            lp.points = (Point(vpos.x, vpos.y), Point(vpos.x, vpos.y))
    with pytest.raises(OverviewViolation):
        attest_overview(egi, bad, summary)


def test_boundary_degree_independent_of_collapse_set():
    """``boundary_degree`` / ``boundary_incidences`` are a property of the cut
    alone (the documented invariant)."""
    egi = parse_egif(G_BOUNDARY)
    inner = _inner_cuts(egi)[0]
    inc = boundary_incidences(egi, inner)
    assert len(inc) == boundary_degree(egi, inner) == 1
    edge_id, port, vid = inc[0]
    # The hidden edge is Q; the visible vertex is x.
    assert egi.get_relation_name(edge_id) == "Q"
    assert port == 0
    assert vid in {v.id for v in egi.V}


# --------------------------------------------------------------------------- #
# P2 adversarial — corrupt the BADGE
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("key,bad_value", [
    ("predicates", 99),
    ("vertices", 99),
    ("cuts", 99),
    ("polarity", "negative"),
    ("boundary_degree", 99),
])
def test_p2_lying_badge_fails(key, bad_value):
    """A placeholder badge that misreports its hidden subtree is caught."""
    egi = parse_egif(G_BOUNDARY)
    inner = _inner_cuts(egi)[0]
    dto, summary = _overview(egi, {inner})
    summary[inner] = dict(summary[inner])
    summary[inner][key] = bad_value
    failures = check_overview(egi, dto, summary)
    assert any("overview-summary" in f and key in f for f in failures)


def test_p2_missing_badge_key_fails():
    egi = parse_egif(G_BOUNDARY)
    inner = _inner_cuts(egi)[0]
    dto, summary = _overview(egi, {inner})
    summary[inner] = {k: v for k, v in summary[inner].items() if k != "predicates"}
    failures = check_overview(egi, dto, summary)
    assert any("missing 'predicates'" in f for f in failures)


def test_claiming_a_non_cut_fails():
    egi = parse_egif(G_BOUNDARY)
    dto, _ = generate_layout(egi)
    failures = check_overview(egi, dto, {"not_a_real_cut": {}})
    assert any("not cuts" in f for f in failures)


# --------------------------------------------------------------------------- #
# Monotonicity (the expansion step)
# --------------------------------------------------------------------------- #

def test_expanding_a_placeholder_stays_faithful_and_reveals_more():
    """Expanding (un-collapsing) a placeholder yields a still-faithful overview
    with strictly more visible elements and one fewer placeholder."""
    egi = parse_egif(G_WIDE)
    top = _top_cuts(egi)
    # Collapsed: both top cuts.
    dto_a, sum_a = _overview(egi, set(top))
    attest_overview(egi, dto_a, sum_a)
    # Expand one of them.
    dto_b, sum_b = _overview(egi, {top[1]})
    attest_overview(egi, dto_b, sum_b)
    assert len(sum_b) == len(sum_a) - 1
    # Strictly more drawn elements after expanding.
    drawn_a = len(dto_a.vertex_positions) + len(dto_a.predicate_positions)
    drawn_b = len(dto_b.vertex_positions) + len(dto_b.predicate_positions)
    assert drawn_b > drawn_a


def test_quotient_is_a_valid_egi():
    """The quotient is a well-formed RelationalGraphWithCuts (it passes Dau
    constraints at construction — else this raises)."""
    egi = parse_egif(G_BOUNDARY)
    inner = _inner_cuts(egi)[0]
    q = collapse_quotient(egi, {inner})
    # Placeholder kept as a leaf cut; hidden edge Q gone; synthetic boundary
    # predicate present.
    assert inner in {c.id for c in q.Cut}
    names = sorted(q.get_relation_name(e.id) for e in q.E)
    assert "Q" not in names
    assert "P" in names
