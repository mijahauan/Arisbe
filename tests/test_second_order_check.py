"""The second-order de-risking harness (``src/second_order_check.py``, ROADMAP #13).

The frontier is "second-order logic as a picture" — the correspondence check (§3.3)
raised one order. This harness proves, on real candidates and *before* the core is
opened, the law a graph-of-a-graph device must satisfy (S1 stratified / S2
quote-equals-quoted-and-attested / S3 read-back / S4 honest horizon). These tests
pin both halves: the law **holds** on well-formed quotations, and the **falsifiers
bite** (a flat impredicative quote, a doctored quote, a lossy reader) — so a passing
report is earned, mirroring ``test_reference_resolution_check``.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egif_parser_dau import parse_egif
from second_order_check import (
    Quotation,
    QuotationReading,
    SORT_PROPOSITION,
    SecondOrderViolation,
    attest_quotation,
    check_quotation,
    run_quotation,
)

HOST = "(P *a)"                       # the graph the quotation is drawn in
QUOTED = "~[ (man *x) ~[ (mortal x) ] ]"   # a strictly-lower proposition it names


def _egi(s):
    return parse_egif(s)


def _predicative(**kw):
    """A predicative quotation: names a strictly-lower graph, drawn flat — the
    ordinary well-formed second-order device."""
    base = dict(
        name="q", sort=SORT_PROPOSITION, host=_egi(HOST),
        resolve=lambda: _egi(QUOTED), quoted_ground=_egi(QUOTED),
        enclosed=False,
    )
    base.update(kw)
    return Quotation(**base)


# --- the law holds on well-formed quotations -------------------------------- #

def test_predicative_flat_quote_passes():
    assert check_quotation(_predicative()) == []
    rep = run_quotation(_predicative())
    assert rep.ok and rep.well_sorted and rep.quote_equals_quoted


def test_impredicative_quote_is_well_formed_only_enclosed():
    # A self-quote (quoted_ground IS the host) drawn ENCLOSED is admitted (dragon 9:
    # a self-assessment is legitimate under a cut — ◇, not a flat □).
    host = _egi(HOST)
    ok = Quotation(name="self", sort=SORT_PROPOSITION, host=host,
                   resolve=lambda: _egi(HOST), quoted_ground=_egi(HOST),
                   enclosed=True)
    assert ok.is_impredicative() is True
    assert check_quotation(ok) == []


# --- falsifiers bite --------------------------------------------------------- #

def test_impredicative_quote_drawn_flat_fails_S1():
    # The comprehension floor: an impredicative (self-referential) quote drawn FLAT
    # on the sheet is forbidden — the paradox floor, drawn (dragon 9).
    bad = Quotation(name="self-flat", sort=SORT_PROPOSITION, host=_egi(HOST),
                    resolve=lambda: _egi(HOST), quoted_ground=_egi(HOST),
                    enclosed=False)
    failures = check_quotation(bad)
    assert any("S1 stratified" in f for f in failures)
    assert run_quotation(bad).well_sorted is False


def test_doctored_quote_fails_S2():
    # resolve() yields a different graph than the independent quoted_ground.
    bad = _predicative(resolve=lambda: _egi('(other *z)'))
    failures = check_quotation(bad)
    assert any("S2 quote-equals-quoted" in f for f in failures)
    assert run_quotation(bad).quote_equals_quoted is False


def test_non_second_order_sort_fails_S1():
    bad = _predicative(sort="individual")   # a plain first-order line is not a quote
    assert any("S1 well-sorted" in f for f in check_quotation(bad))


# --- S3 read-back (the reader is injected; the frontier itself) ------------- #

def test_read_back_faithful_passes_S3():
    q = _predicative(read_back=lambda: QuotationReading(SORT_PROPOSITION, _egi(QUOTED)))
    rep = run_quotation(q)
    assert rep.read_back_faithful is True and rep.ok


def test_read_back_that_drops_the_quote_fails_S3():
    q = _predicative(read_back=lambda: QuotationReading(SORT_PROPOSITION, _egi('(lost *z)')))
    assert any("S3 read-back" in f for f in check_quotation(q))
    assert run_quotation(q).read_back_faithful is False


def test_read_back_wrong_sort_fails_S3():
    q = _predicative(read_back=lambda: QuotationReading("abstraction", _egi(QUOTED)))
    assert any("S3 read-back" in f for f in check_quotation(q))


# --- honest horizon + the production hook ----------------------------------- #

def test_report_names_skipped_checks_as_honest_limits():
    rep = run_quotation(_predicative())   # no layout_fn, no read_back
    assert any("S2 §3.3 half" in l for l in rep.honest_limits)
    assert any("reader IS the frontier" in l for l in rep.honest_limits)
    assert rep.read_back_faithful is None   # skipped, not failed


def test_attest_quotation_raises_on_a_violation():
    bad = Quotation(name="self-flat", sort=SORT_PROPOSITION, host=_egi(HOST),
                    resolve=lambda: _egi(HOST), quoted_ground=_egi(HOST),
                    enclosed=False)
    with pytest.raises(SecondOrderViolation):
        attest_quotation(bad, context="test")
    # a well-formed one does not raise
    attest_quotation(_predicative())


# --- S2 §3.3 half against the real layout engine ---------------------------- #

def test_quoted_graph_is_attested_one_level_down_real_elk():
    from correspondence_attestation import attest_correspondence
    from web_api.services.layout_service import generate_layout

    def layout_fn(egi):
        dto, _svg = generate_layout(egi)
        return dto

    q = _predicative()
    failures = check_quotation(q, layout_fn=layout_fn, attest_fn=attest_correspondence)
    assert failures == [], failures            # the quoted graph draws in §3.3
    assert run_quotation(q, layout_fn=layout_fn, attest_fn=attest_correspondence).quoted_attested


# --- S5: trajectory-relative resolution (R_G functoriality) ------------------ #
# A name's resolution may vary by DAG state (Cohen's reference values R_G);
# the law holds at every resolving state, and non-resolving states are named.
# docs/FORCING_AND_THE_GAMMA_CROSSING.md §5.

from second_order_check import (  # noqa: E402
    attest_quotation_trajectory,
    check_quotation_at_states,
    run_quotation_trajectory,
)

QUOTED_B = "~[ (bird *x) ~[ (flies x) ] ]"     # a different lower graph, branch b


def _at_state(quoted, **kw):
    """The name as it stands at one state: predicative, resolving to ``quoted``."""
    return _predicative(resolve=lambda: _egi(quoted),
                        quoted_ground=_egi(quoted), **kw)


def test_S5_holds_when_each_state_resolves_to_its_own_ground():
    """The happy path: the same name resolves to *different* grounds on two
    branches, each state satisfying S1–S3 against its own ground."""
    per_state = {"s1": _at_state(QUOTED), "s2": _at_state(QUOTED_B)}
    assert check_quotation_at_states("mu", per_state) == []
    rep = run_quotation_trajectory("mu", per_state)
    assert rep.ok and rep.checked_states == ["s1", "s2"]
    assert rep.unresolved_states == []
    attest_quotation_trajectory("mu", per_state)   # does not raise


def test_S5_failure_names_the_breaking_state():
    """The falsifier: one state's resolution is doctored (resolve ≠ that state's
    ground) — S5 fails and the failure carries the state id."""
    doctored = _predicative(resolve=lambda: _egi(QUOTED_B),
                            quoted_ground=_egi(QUOTED))
    per_state = {"s1": _at_state(QUOTED), "s2": doctored}
    failures = check_quotation_at_states("mu", per_state)
    assert failures and all("S5[s2]" in f for f in failures)
    assert not any("S5[s1]" in f for f in failures)
    with pytest.raises(SecondOrderViolation):
        attest_quotation_trajectory("mu", per_state)


def test_S5_nonresolving_state_is_named_never_failed():
    """The horizon: a state where the name does not resolve (R_G undefined at
    that condition) is reported in unresolved_states — not a failure, never
    silent."""
    per_state = {"s1": _at_state(QUOTED), "s2": None}
    assert check_quotation_at_states("mu", per_state) == []
    rep = run_quotation_trajectory("mu", per_state)
    assert rep.ok
    assert rep.unresolved_states == ["s2"] and rep.checked_states == ["s1"]


def test_S5_wholly_unresolved_trajectory_is_vacuous_and_says_so():
    rep = run_quotation_trajectory("mu", {"s1": None, "s2": None})
    assert rep.ok and rep.checked_states == []
    assert any("vacuous" in lim for lim in rep.honest_limits)


def test_S5_per_state_law_is_the_full_law():
    """S5 quantifies the existing checks: a flat impredicative quote at one state
    fails S1 *through* S5 (the trajectory inherits the comprehension floor)."""
    host = _egi(HOST)
    flat_self = Quotation(name="q", sort=SORT_PROPOSITION, host=host,
                          resolve=lambda: _egi(HOST), quoted_ground=_egi(HOST),
                          enclosed=False)
    failures = check_quotation_at_states("mu", {"s1": flat_self})
    assert any("S5[s1]" in f and "S1 stratified" in f for f in failures)
