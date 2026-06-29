"""The reference node — increment 1 (intra-UoD definition references).

The additive logic layer (``src/reference_node.py``) over the de-risked harness:
a Form-2 reference edge + an overlay mark, resolved by the definition splice
machinery, attested by ``RESOLVE ≡ INLINED-AND-ATTESTED``.  No protected module
is touched.

Covered: the overlay mark round-trips; authoring refuses an unresolvable edge
(R4 honest horizon); resolution reuses ``expand_at`` and is exact against an
independent raw fixture (R1); refold recovers the host (R3); the boundary hook
attests / refuses (R2 via real ELK, skipped if absent); the resolver seam
dispatches via a chain so schema/UoD resolvers drop in additively.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from definitions import DefinitionRegistry
from egif_parser_dau import parse_egif
from eg_navigation import same_graph
from reference_resolution_check import ReferenceViolation
from reference_node import (
    ChainReferenceResolver,
    DefinitionReferenceResolver,
    ReferenceMark,
    attest_reference,
    mark_reference,
    reference_candidate,
    refold_reference,
    resolve_reference,
    run_reference_mark,
)
from run_reference_resolution_check import SUBSET, POWER_SET_DEFINED, POWER_SET_RAW, _subset_edge


@pytest.fixture
def host():
    return parse_egif(POWER_SET_DEFINED)


@pytest.fixture
def resolver():
    return DefinitionReferenceResolver(DefinitionRegistry([SUBSET]))


# --- the overlay record ----------------------------------------------------- #

def test_mark_round_trips():
    m = ReferenceMark(edge_id="e1", target="subset", origin="math-defs", warrant="low")
    assert ReferenceMark.from_dict(m.to_dict()) == m


def test_mark_reference_refuses_unresolvable_edge(host, resolver):
    """R4 honest horizon: you cannot mark an edge no resolver can resolve."""
    # A vertex id / a non-defined edge is not a resolvable reference.
    bogus = next(iter(host.V)).id
    with pytest.raises(ValueError):
        mark_reference(host, bogus, resolver)


def test_mark_reference_captures_target_and_kind(host, resolver):
    edge = _subset_edge(host)
    mark = mark_reference(host, edge, resolver, origin="math-defs")
    assert mark.target == "subset"
    assert mark.kind == "definition"
    assert mark.origin == "math-defs"
    assert mark.warrant == "low"  # a reference is an abbreviation, not a truth-claim


# --- resolution + the law --------------------------------------------------- #

def test_resolve_matches_independent_raw_fixture(host, resolver):
    """R1: resolving the reference equals the independently-authored raw axiom."""
    edge = _subset_edge(host)
    mark = mark_reference(host, edge, resolver)
    resolved, fp = resolve_reference(host, mark, resolver)
    assert "subset" not in set(resolved.rel.values())
    assert same_graph(resolved, parse_egif(POWER_SET_RAW))
    assert fp is not None  # a definition reference has an exact inverse


def test_refold_recovers_host(host, resolver):
    """R3: reference → inlined → reference recovers the host (lossless)."""
    edge = _subset_edge(host)
    mark = mark_reference(host, edge, resolver)
    resolved, fp = resolve_reference(host, mark, resolver)
    assert same_graph(refold_reference(resolved, fp), host)


def test_run_reference_mark_passes_structurally(host, resolver):
    edge = _subset_edge(host)
    mark = mark_reference(host, edge, resolver)
    report = run_reference_mark(host, mark, resolver, inlined=parse_egif(POWER_SET_RAW))
    assert report.resolve_equals_inline  # R1 vs independent ground truth
    assert report.recoverable            # R3
    assert report.ok


# --- the boundary hook ------------------------------------------------------ #

def test_attest_reference_raises_on_wrong_independent_inline(host, resolver):
    """The hook bites: a doctored ground-truth inlining fails R1."""
    edge = _subset_edge(host)
    mark = mark_reference(host, edge, resolver)
    with pytest.raises(ReferenceViolation):
        attest_reference(
            host, mark, resolver, inlined=parse_egif("~[ (totally *different) ]")
        )


def test_attest_reference_passes_at_boundary_without_ground_truth(host, resolver):
    """At a production boundary there is no independent inlining: R1 is trivial,
    R3 carries the round-trip weight, and the hook must pass."""
    edge = _subset_edge(host)
    mark = mark_reference(host, edge, resolver)
    attest_reference(host, mark, resolver)  # must not raise


# --- the resolver seam (extension-readiness) -------------------------------- #

def test_chain_resolver_dispatches_to_definition(host):
    """The chain seam picks the definition resolver — the shape schema/UoD
    resolvers drop into without touching callers (increment 2)."""
    chain = ChainReferenceResolver(DefinitionReferenceResolver(DefinitionRegistry([SUBSET])))
    edge = _subset_edge(host)
    assert chain.can_resolve(host, edge)
    mark = mark_reference(host, edge, chain)
    resolved, fp = resolve_reference(host, mark, chain)
    assert same_graph(resolved, parse_egif(POWER_SET_RAW))


def test_chain_resolver_refuses_when_no_member_resolves(host):
    chain = ChainReferenceResolver()  # empty chain resolves nothing
    edge = _subset_edge(host)
    assert not chain.can_resolve(host, edge)


# --- the real §3.3 path (skipped if the layout engine isn't installed) ------ #

def test_boundary_attests_under_real_elk(host, resolver):
    try:
        from elk_layout_engine import ELKLayoutEngine
        from style_loader import load_default_style
    except Exception:  # noqa: BLE001
        pytest.skip("layout engine / web extras not installed")

    engine = ELKLayoutEngine()
    style = load_default_style()
    layout_fn = lambda egi: engine.generate_layout(egi, style)

    edge = _subset_edge(host)
    mark = mark_reference(host, edge, resolver)
    # R2: the resolved graph really attests §3.3 with the production engine.
    attest_reference(host, mark, resolver, layout_fn=layout_fn)
