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
