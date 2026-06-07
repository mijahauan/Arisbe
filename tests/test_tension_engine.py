"""
Tests for the tension layout engine (src/tension_engine.py) — the constrained
stress projection that places a relation *between* its argument vertices (the
Peircean single-line reading), as an opt-in alternative to ELK.

Covers:
- cat_on_mat: §3.3 attests AND the binary relation sits between its arguments
  (the readability win, not just "it runs");
- containment holds by construction on cut graphs;
- corpus-wide: every UoD's tension layout attests (or would fall back to ELK);
- determinism (same EGI → same layout);
- the service ?engine=tension path is attested; engine='elk' default unchanged.

See docs/TENSION_LAYOUT.md §9.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egif_parser_dau import parse_egif
from elk_layout_engine import ELKLayoutEngine
from style_loader import load_default_style
from correspondence_attestation import attest_correspondence, CorrespondenceViolation
from presentation_ops import element_area
from tension_engine import TensionLayoutEngine
from tomos_service import TomosService

TOMOS_ROOT = Path(__file__).parent.parent / "tomos"


def _engine():
    return TensionLayoutEngine()


def test_cat_on_mat_reads_relation_between_arguments():
    """The headline: tension places On between Cat and Mat (single-line reading)
    and the layout is §3.3-correct."""
    egi = parse_egif("(Cat *x) (On x *y) (Mat y)")
    dto = _engine().generate_layout(egi, load_default_style())
    attest_correspondence(egi, dto, context="test")  # must not raise

    name = {e.id: egi.get_relation_name(e.id) for e in egi.E}
    xs = {name[e.id]: dto.predicate_positions[e.id].x for e in egi.E}
    # On's x lies strictly between Cat's and Mat's — the relation is drawn
    # between its two arguments, not stacked in a separate column.
    lo, hi = sorted((xs["Cat"], xs["Mat"]))
    assert lo < xs["On"] < hi


def test_containment_holds_on_cut_graph():
    """Every element sits inside its area's cut bounds — containment by
    construction (the hierarchical/proxy decomposition)."""
    egi = parse_egif("(Q *x) ~[ (P x) ] ~[ (R x) ]")
    dto = _engine().generate_layout(egi, load_default_style())
    ea = element_area(egi)
    cut_ids = {c.id for c in egi.Cut}
    for eid, area in ea.items():
        if area in cut_ids:
            pos = dto.vertex_positions.get(eid) or dto.predicate_positions.get(eid)
            if pos is None:
                continue
            b = dto.cut_bounds[area]
            assert b.min_x <= pos.x <= b.max_x and b.min_y <= pos.y <= b.max_y
    attest_correspondence(egi, dto, context="test")


def test_corpus_engine_attests_most_and_is_deterministic():
    """The tension engine produces §3.3-correct layouts for the large majority of
    the corpus (the crossing-point-proxy routing realizes each line's
    crossing-sequence). The few it can't yet (a line clipping a sibling cut —
    routing refinement is future work) are the service's ELK-fallback cases, not
    failures here. Also pins determinism (same EGI → same layout)."""
    svc = TomosService(TOMOS_ROOT)
    style = load_default_style()
    total = attested = 0
    for meta in svc.list_uods():
        egi = svc.load_uod(meta["uod_id"]).current_egi
        a = _engine().generate_layout(egi, style)
        b = _engine().generate_layout(egi, style)
        assert a.vertex_positions == b.vertex_positions  # deterministic
        total += 1
        try:
            attest_correspondence(egi, a, context=f"tension:{meta['uod_id']}")
            attested += 1
        except CorrespondenceViolation:
            pass
    assert total > 0
    # The vast majority attest directly (today: 17/18); allow a small fallback
    # tail without pinning the exact number.
    assert attested >= total - 2


def test_service_attests_every_corpus_uod_via_fallback():
    """The service contract: ?engine=tension never fails — it returns the tension
    layout where it attests and the ELK layout otherwise. Every served (EGI, DTO)
    is §3.3-attested by construction (the service attests before returning)."""
    from web_api.services.layout_service import generate_layout
    svc = TomosService(TOMOS_ROOT)
    for meta in svc.list_uods():
        egi = svc.load_uod(meta["uod_id"]).current_egi
        dto, svg = generate_layout(egi, engine="tension")  # must not raise
        assert "<svg" in svg


def test_layout_is_deterministic():
    """Same EGI → identical layout (fixed SMACOF init; layout invariant L1)."""
    egi = parse_egif("(Q *x) ~[ (P x) ] ~[ (R x) ]")
    style = load_default_style()
    a = _engine().generate_layout(egi, style)
    b = _engine().generate_layout(egi, style)
    assert a.vertex_positions == b.vertex_positions
    assert a.predicate_positions == b.predicate_positions
    assert a.cut_bounds == b.cut_bounds


# --------------------------------------------------------------------------- #
# Service wiring                                                               #
# --------------------------------------------------------------------------- #


def test_service_engine_tension_is_attested():
    from web_api.services.layout_service import generate_layout
    egi = parse_egif("(Cat *x) (On x *y) (Mat y)")
    dto, svg = generate_layout(egi, engine="tension")
    assert "<svg" in svg
    # On between its arguments, end-to-end through the service.
    name = {e.id: egi.get_relation_name(e.id) for e in egi.E}
    xs = {name[e.id]: dto.predicate_positions[e.id].x for e in egi.E}
    lo, hi = sorted((xs["Cat"], xs["Mat"]))
    assert lo < xs["On"] < hi


def test_service_default_engine_is_elk_unchanged():
    """engine defaults to ELK; the default render is the ELK layout (the tension
    engine never touches the default path)."""
    from web_api.services.layout_service import generate_layout
    egi = parse_egif("(Cat *x) (On x *y) (Mat y)")
    dto_default, _ = generate_layout(egi)
    elk = ELKLayoutEngine().generate_layout(egi, load_default_style())
    assert dto_default.predicate_positions.keys() == elk.predicate_positions.keys()
    # ELK's two-column signature: predicates share a column, distinct from vertices.
    pred_x = {round(p.x, 1) for p in dto_default.predicate_positions.values()}
    vert_x = {round(p.x, 1) for p in dto_default.vertex_positions.values()}
    assert pred_x != vert_x


def test_service_falls_back_to_elk_when_tension_violates(monkeypatch):
    """If the tension engine ever yields a non-attesting layout, the service
    falls back to ELK rather than failing the request."""
    import web_api.services.layout_service as ls

    class _BadEngine:
        def generate_layout(self, egi, style, layout_deltas=None):
            # A deliberately broken DTO: drop all ligature paths so incidence fails.
            good = ELKLayoutEngine().generate_layout(egi, style)
            import dataclasses
            return dataclasses.replace(good, ligature_paths=[])

    import tension_engine
    monkeypatch.setattr(tension_engine, "TensionLayoutEngine", _BadEngine)
    egi = parse_egif("(Cat *x) (On x *y) (Mat y)")
    dto, svg = ls.generate_layout(egi, engine="tension")
    # Did not raise; fell back to a valid ELK layout (has ligature paths).
    assert dto.ligature_paths
    assert "<svg" in svg
