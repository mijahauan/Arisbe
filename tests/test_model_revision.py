"""Regression tests for model_revision.retract_subgraph — the challenge_to_M
law-relinquishment primitive.

RUN_8_LOG finding: over a long re-generalizing live run the reseeded law-cut,
after accumulated structural merges, took on a shape whose interior shares a line
of identity across an area boundary. The old implementation erased a sheet-level
law-cut by a Dau ERA, and because it ERAs *every* sheet cut while probing for the
target, one such cut made ERA raise ("Selected subgraph contains elements not in
target area"), crashing the whole retraction (4 crashes, all absorbed by the
crash/resume supervisor). The fix removes the cut *structurally*
(``_without_cut_subtree``, mirroring ``retract_atom``): it never raises while
probing, and it keeps a vertex still incident to a surviving edge rather than
severing a sheet atom's line of identity.
"""

import pytest

from egif_parser_dau import parse_egif
from eg_navigation import same_graph, child_cuts
from model_revision import (
    assert_fact,
    retract_subgraph,
    _without_cut_subtree,
    revise_with_disposition,
)

TEMP = "~[ (forecast_temp_band *s *t *b) ~[ (temp_band s t b) ] ]"
PRECIP = "~[ (forecast_precip *s *t) ~[ (precip s t) ] ]"
SWAN = "~[ (swan *x) ~[ (white x) ] ]"


def _build(*egifs):
    g = parse_egif(egifs[0])
    for e in egifs[1:]:
        g = assert_fact(g, e)
    return g


def test_retract_beta_law_isolated_reconstructs():
    """A lone Beta law relinquishes, and re-admitting it reconstructs M."""
    m = parse_egif(SWAN)
    erased = retract_subgraph(m, SWAN)
    assert same_graph(assert_fact(erased, SWAN), m)


def test_retract_law_amid_facts_and_sibling_law():
    """The run-8 shape: two Beta law-cuts + ground facts on one sheet. Retracting
    one law reconstructs M, leaves the *other* law and the facts standing, and
    never raises an ERA AssertionError while probing the sibling cut."""
    m = _build(TEMP, PRECIP, '(temp_band "KAUS" "12" "70")', '(precip "KBOS" "15")')

    erased = retract_subgraph(m, TEMP)                 # must not raise
    assert same_graph(assert_fact(erased, TEMP), m)    # exact M minus the temp law
    # the precip law and both ground facts survive untouched
    assert same_graph(
        erased,
        _build(PRECIP, '(temp_band "KAUS" "12" "70")', '(precip "KBOS" "15")'),
    )

    # symmetric: retracting the other law works too (order-independent)
    erased2 = retract_subgraph(m, PRECIP)
    assert same_graph(assert_fact(erased2, PRECIP), m)


def test_without_cut_subtree_preserves_a_shared_line():
    """The defensive property that fixes the crashing class: erasing a cut whose
    interior references a line of identity anchored on the sheet keeps that line —
    it removes the cut and its own edges as a unit, never severing the sheet atom.
    (This is exactly what the ERA path could not do.)"""
    m = parse_egif('(anchor *x) ~[ (P x) ] (other "z")')
    (cut_id,) = child_cuts(m, m.sheet)
    g = _without_cut_subtree(m, cut_id)
    # the cut and (P x) are gone; (anchor *x) and (other "z") — and the line x — remain
    assert same_graph(g, parse_egif('(anchor *x) (other "z")'))


def test_retract_subgraph_skips_noise_cut_without_erroring():
    """A sheet carrying an unrelated negated fact (a sibling cut) does not block
    retracting the target law: the probe skips the non-matching cut cleanly."""
    m = _build(TEMP, "~[ (foo \"a\") ]", '(temp_band "KAUS" "12" "70")')
    erased = retract_subgraph(m, TEMP)                 # must not raise on the noise cut
    assert same_graph(assert_fact(erased, TEMP), m)
    # the noise cut survives
    assert same_graph(erased, _build("~[ (foo \"a\") ]", '(temp_band "KAUS" "12" "70")'))


def test_retract_subgraph_no_match_raises_clean_valueerror():
    """Nothing to retract → a clean ValueError, never a rule AssertionError."""
    m = _build('(temp_band "KAUS" "12" "70")')          # no cut at all
    with pytest.raises(ValueError):
        retract_subgraph(m, TEMP)


def test_challenge_to_m_end_to_end_relinquishes_law():
    """The full disposition path (the one that crashed in run 8): challenge_to_M
    relinquishes the impugned law and admits the refuting anomaly, on a sheet that
    also carries a sibling law + facts."""
    m = _build(SWAN, PRECIP, '(swan "odile")')
    revised = revise_with_disposition(
        m, "challenge_to_M", subgraph_egif=SWAN, fact_egif='(swan "odile") (black "odile")'
    )
    # the over-general swan law is gone; the precip law still stands
    assert not same_graph(revised, m)
    assert same_graph(assert_fact(retract_subgraph(revised, PRECIP), PRECIP), revised)


# --------------------------------------------------------------------------- #
# Sweep #2: the residence-aware dispatch — when M is resident in the standing #
# world-scroll, every disposition is enacted by licensed rules (INS-of-cell / #
# ERA-in-cell) and the recorded variant returns the executed derivation.      #
# --------------------------------------------------------------------------- #

from eg_navigation import same_graph as _same
from model_revision import revise_with_disposition_recorded
from world_scroll import find_world_scroll, m_view, wrap_m


def _resident(*egifs):
    g, _ = wrap_m(_build(*egifs))
    return g


def test_resident_enlargement_is_a_licensed_ins_of_cell():
    m = _resident('(swan "Ciel")')
    revised, derivation = revise_with_disposition_recorded(
        m, "new_fact", fact_egif='(swan "Dover")')
    assert derivation == ["INS"]
    scroll = find_world_scroll(revised)
    assert scroll is not None and len(scroll.cell_ids) == 2
    assert _same(m_view(revised), parse_egif('(swan "Ciel") (swan "Dover")'))


def test_resident_generalization_admits_a_law_cell():
    m = _resident('(swan "Ciel") (white "Ciel")')
    revised, derivation = revise_with_disposition_recorded(
        m, "generalization", rule_egif=SWAN)
    assert derivation == ["INS"]
    assert _same(m_view(revised),
                 parse_egif(f'(swan "Ciel") (white "Ciel") {SWAN}'))


def test_resident_retract_fact_is_a_licensed_era():
    m = _resident('(swan "Ciel") (white "Ciel")')
    revised, derivation = revise_with_disposition_recorded(
        m, "retract_fact", relation="white", labels=["Ciel"])
    assert derivation == ["ERA"]
    assert _same(m_view(revised), parse_egif('(swan "Ciel")'))


def test_resident_challenge_is_era_then_ins():
    m = _resident(SWAN, '(swan "Ciel") (white "Ciel")')
    revised, derivation = revise_with_disposition_recorded(
        m, "challenge_to_M", subgraph_egif=SWAN,
        fact_egif='(swan "Nox") (black "Nox")')
    assert derivation == ["ERA", "INS"]
    assert _same(m_view(revised),
                 parse_egif('(swan "Ciel") (white "Ciel") (swan "Nox") '
                            '(black "Nox")'))
    # the residence stands; the emptied husk is a scar
    assert find_world_scroll(revised) is not None


def test_plain_dispatcher_returns_the_same_graph_resident():
    m = _resident('(swan "Ciel")')
    a = revise_with_disposition(m, "new_fact", fact_egif='(swan "Dover")')
    b, _ = revise_with_disposition_recorded(m, "new_fact",
                                            fact_egif='(swan "Dover")')
    assert _same(a, b)


def test_sheet_fallback_reports_empty_derivation():
    m = _build('(swan "Ciel")')          # bare sheet-level M, no scroll
    revised, derivation = revise_with_disposition_recorded(
        m, "new_fact", fact_egif='(swan "Dover")')
    assert derivation == []              # no rule licensed the move — honest
    assert _same(revised, parse_egif('(swan "Ciel") (swan "Dover")'))
