"""
Overview layout service + the ``?lod=overview`` Organon route (build step 2 of
docs/ADAPTIVE_SCOPE_VIEWER.md).

The contract: ``generate_overview_layout`` collapses deep cuts into placeholders
(``collapse_quotient`` → ``generate_layout`` of the quotient) and is attested by
``attest_overview``; the route surfaces it read-only with a ``collapsed`` badge
map.  A small graph opens fully (overview ≡ full drawing); a budget/expand choice
folds the deep mass into faithful placeholders.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "web_api" / "services"))

import presentation_ops as po
from correspondence_attestation import attest_overview, OverviewViolation
from egif_parser_dau import parse_egif
from layout_service import (
    DEFAULT_OVERVIEW_BUDGET,
    _resolve_collapsed,
    generate_overview_layout,
)
from tomos_service import TomosService
from web_api import main as web_main


TOMOS_ROOT = Path(__file__).parent.parent / "tomos"

# A graph with a nested cut a line of identity enters — the boundary case.
G_BOUNDARY = "~[ (P *x) ~[ (Q x) ] ]"
# A flat graph with several sibling cuts — exercises the budget policy.
G_WIDE = "(A *x) ~[ (C *z) ] ~[ (D *w) ] ~[ (E *u) ]"


# --------------------------------------------------------------------------- #
# Service — generate_overview_layout
# --------------------------------------------------------------------------- #

def test_small_graph_opens_fully():
    """A graph within budget collapses nothing — an overview of it is just the
    ordinary drawing."""
    egi = parse_egif(G_BOUNDARY)
    dto, svg, summary, collapsed = generate_overview_layout(egi)
    assert collapsed == set()
    assert summary == {}
    assert svg


def test_budget_forces_collapse_and_attests():
    """A zero budget collapses every top cut; the result is overview-faithful."""
    egi = parse_egif(G_WIDE)
    dto, svg, summary, collapsed = generate_overview_layout(egi, budget=0)
    top = {c for c, p in po.cut_parents(egi).items() if p == egi.sheet}
    assert collapsed == top
    assert set(summary) == top
    # Re-attest explicitly (the service already did) — no raise.
    attest_overview(egi, dto, summary)


def test_expand_opens_named_cut():
    """Expanding a cut opens it; its unexpanded siblings stay placeholders."""
    egi = parse_egif(G_WIDE)
    top = sorted(c for c, p in po.cut_parents(egi).items() if p == egi.sheet)
    dto, svg, summary, collapsed = generate_overview_layout(egi, expand=[top[0]])
    assert top[0] not in collapsed       # expanded → open
    assert set(collapsed) == set(top[1:])  # siblings collapsed
    attest_overview(egi, dto, summary)


def test_overview_badge_is_faithful():
    """The placeholder badge reports the true hidden subtree (counts/polarity/
    boundary degree)."""
    egi = parse_egif(G_BOUNDARY)
    top = [c for c, p in po.cut_parents(egi).items() if p == egi.sheet][0]
    _, _, summary, _ = generate_overview_layout(egi, expand=[])
    badge = summary[top]
    assert badge["cuts"] == 1          # the inner cut
    assert badge["vertices"] == 1      # x
    assert badge["predicates"] == 2    # P, Q
    assert badge["polarity"] == "negative"  # depth 1
    assert badge["boundary_degree"] == 0    # nothing enters the OUTER cut


def test_resolve_collapsed_auto_policy_respects_budget():
    """The auto-expand policy opens at most ``budget`` cuts; the rest collapse."""
    egi = parse_egif(G_WIDE)
    collapsed = _resolve_collapsed(egi, expand=None, budget=1)
    top = {c for c, p in po.cut_parents(egi).items() if p == egi.sheet}
    # One opened, the remaining two are placeholders.
    assert len(collapsed) == len(top) - 1


def test_nested_expand_includes_ancestors():
    """Expanding an inner cut auto-opens its ancestor, so the inner is drawn open
    (not hidden)."""
    egi = parse_egif(G_BOUNDARY)
    pm = po.cut_parents(egi)
    inner = [c for c in pm if pm[c] != egi.sheet][0]
    collapsed = _resolve_collapsed(egi, expand=[inner])
    # Expanding inner opens both inner and its ancestor → nothing collapsed.
    assert collapsed == set()


# --------------------------------------------------------------------------- #
# Route — GET /organon/uods/{id}?lod=overview
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def client():
    return TestClient(web_main.app)


@pytest.fixture(scope="module")
def corpus_ids():
    return [u["uod_id"] for u in TomosService(TOMOS_ROOT).list_uods()]


@pytest.fixture(scope="module")
def cut_bearing_uod(corpus_ids):
    """A corpus UoD that actually has cuts, so overview has something to collapse."""
    tomos = TomosService(TOMOS_ROOT)
    preferred = "peirce_modus_ponens"
    candidates = ([preferred] if preferred in corpus_ids else []) + list(corpus_ids)
    for uid in candidates:
        try:
            uod = tomos.load_uod(uid, attest=False)
        except TypeError:
            uod = tomos.load_uod(uid)
        egi = getattr(uod, "current_egi", None)
        if egi is not None and len(egi.Cut) >= 1:
            return uid
    pytest.skip("no cut-bearing UoD in tomos")


def test_route_overview_returns_collapsed_map(client, cut_bearing_uod):
    """``?lod=overview`` returns an SVG + layout DTO + a ``collapsed`` badge map,
    read-only, no error."""
    resp = client.get(f"/organon/uods/{cut_bearing_uod}",
                      params={"lod": "overview"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"], body
    data = body["data"]
    assert data["lod"] == "overview"
    assert data["svg"]
    assert "collapsed" in data
    assert isinstance(data["collapsed"], dict)
    # Every badge carries the full form-only summary.
    for badge in data["collapsed"].values():
        assert set(badge) == {"cuts", "vertices", "predicates",
                              "polarity", "boundary_degree"}


def test_route_full_is_default_and_has_no_collapsed(client, cut_bearing_uod):
    """The default ``lod=full`` is the canonical drawing — no ``collapsed`` map."""
    resp = client.get(f"/organon/uods/{cut_bearing_uod}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data.get("lod") != "overview"
    assert "collapsed" not in data
