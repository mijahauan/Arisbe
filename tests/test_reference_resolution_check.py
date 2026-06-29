"""The reference / transclusion validation harness (``reference_resolution_check``).

Proves the law a first-class reference node would carry — RESOLVE ≡
INLINED-AND-ATTESTED — on real graphs, before the protected core is opened to add
the element (ROADMAP #3 / THE_MINIMAL_IN_VIEW_SET §12 option (b)).

The suite has two halves:

  * **the law holds** on every real candidate the runner builds (definition
    references + a transclusion reference);
  * **the metrics bite** — doctored candidates fail R1 (resolve ≢ inline), R3
    (lossy refold), and R2 (resolved not attested) — so the PASS above is earned,
    not vacuous (the same falsifier discipline as the diagram↔narration harness).
"""

import pytest

from definitions import DefinitionRegistry, expand_at, fold
from egif_parser_dau import parse_egif
from reference_resolution_check import (
    Reference,
    ReferenceViolation,
    attest_reference,
    check_reference,
    run_reference,
)

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from run_reference_resolution_check import (  # noqa: E402
    SUBSET,
    POWER_SET_DEFINED,
    POWER_SET_RAW,
    definition_candidates,
    transclusion_candidates,
    _subset_edge,
)


# --------------------------------------------------------------------------- #
# the law holds on every real candidate
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "ref",
    definition_candidates() + transclusion_candidates(),
    ids=lambda r: r.name,
)
def test_law_holds_structurally(ref):
    """R1 (+ R3 where applicable) without a layout engine — the structural law."""
    report = run_reference(ref)  # no layout_fn → R2 skipped + declared
    assert report.resolve_equals_inline, report.failures
    if ref.refold is not None:
        assert report.recoverable, report.failures
    assert report.ok


def test_transclusion_names_its_unresolved_horizon():
    """R4: an import no resolver located is *reported*, never silently dropped —
    and an incomplete reference is still licit (not a failure)."""
    (ref,) = transclusion_candidates()
    report = run_reference(ref)
    assert "no_such_module" in report.unresolved
    assert report.ok  # the gap is named, so the reference still passes


# --------------------------------------------------------------------------- #
# the metrics bite — falsifiers
# --------------------------------------------------------------------------- #

def test_R1_bites_when_resolve_disagrees_with_inline():
    """Doctor the inlined ground truth to a *different* graph → R1 must fail."""
    reg = DefinitionRegistry([SUBSET])
    host = parse_egif(POWER_SET_DEFINED)
    resolved = expand_at(host, reg, _subset_edge(host))
    bad = Reference(
        name="doctored-inline",
        origin="falsifier",
        resolve=lambda r=resolved: r,
        inlined=parse_egif("~[ (totally *different) ]"),  # not the raw fixture
    )
    failures = check_reference(bad)
    assert any("R1" in f for f in failures)
    assert not run_reference(bad).resolve_equals_inline


def test_R3_bites_when_refold_is_lossy():
    """Doctor the inverse to return a different graph → R3 must fail."""
    reg = DefinitionRegistry([SUBSET])
    host = parse_egif(POWER_SET_DEFINED)
    resolved = expand_at(host, reg, _subset_edge(host))
    bad = Reference(
        name="lossy-refold",
        origin="falsifier",
        resolve=lambda r=resolved: r,
        inlined=parse_egif(POWER_SET_RAW),
        host=host,
        refold=lambda r: parse_egif("~[ ]"),  # does not recover the host
    )
    failures = check_reference(bad)
    assert any("R3" in f for f in failures)
    assert run_reference(bad).recoverable is False


def test_R2_bites_when_resolved_is_not_attested():
    """An attest_fn that rejects the resolved graph → R2 must fail (proves R2 is
    wired through, not skipped, when a layout_fn is present)."""
    reg = DefinitionRegistry([SUBSET])
    host = parse_egif(POWER_SET_DEFINED)
    resolved = expand_at(host, reg, _subset_edge(host))

    def rejecting_attest(egi, dto):
        raise AssertionError("simulated §3.3 violation")

    ref = Reference(
        name="unattested",
        origin="falsifier",
        resolve=lambda r=resolved: r,
        inlined=parse_egif(POWER_SET_RAW),
    )
    failures = check_reference(
        ref, layout_fn=lambda egi: None, attest_fn=rejecting_attest
    )
    assert any("R2" in f for f in failures)


def test_R1_resolve_failure_is_reported_not_crashed():
    """A reference whose resolve() raises is a law failure (reported), not a crash."""
    def boom():
        raise RuntimeError("cannot fetch the referenced module")

    ref = Reference(
        name="unresolvable",
        origin="falsifier",
        resolve=boom,
        inlined=parse_egif("~[ ]"),
    )
    failures = check_reference(ref)
    assert any("R1 resolve" in f for f in failures)
    assert not run_reference(ref).ok


# --------------------------------------------------------------------------- #
# the production-shaped hook
# --------------------------------------------------------------------------- #

def test_attest_reference_raises_on_violation_passes_on_good():
    good, _ = definition_candidates()
    attest_reference(good)  # must not raise

    bad = Reference(
        name="bad",
        origin="falsifier",
        resolve=lambda: parse_egif("~[ ]"),
        inlined=parse_egif("(P)"),
    )
    with pytest.raises(ReferenceViolation) as exc:
        attest_reference(bad, context="unit-test")
    assert exc.value.failures
    assert "unit-test" in str(exc.value)


def test_structural_run_declares_R2_skip():
    """When no layout_fn is given the harness *declares* R2 untested (honest
    limits), rather than silently passing it."""
    good, _ = definition_candidates()
    report = run_reference(good)
    assert any("R2" in lim for lim in report.honest_limits)
    assert report.resolved_attested  # not failed — skipped-and-declared


# --------------------------------------------------------------------------- #
# the real §3.3 path (skipped if the layout engine isn't installed)
# --------------------------------------------------------------------------- #

def test_R2_against_real_elk_layout():
    """The resolved graph really attests under §3.3 with the production engine."""
    try:
        from elk_layout_engine import ELKLayoutEngine
        from style_loader import load_default_style
    except Exception:  # noqa: BLE001
        pytest.skip("layout engine / web extras not installed")

    engine = ELKLayoutEngine()
    style = load_default_style()
    layout_fn = lambda egi: engine.generate_layout(egi, style)

    for ref in definition_candidates() + transclusion_candidates():
        report = run_reference(ref, layout_fn=layout_fn)
        assert report.resolved_attested, report.failures
        assert report.ok
