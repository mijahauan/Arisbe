"""
Tests for style-selectable rendering — the keystone of the export /
view-in-style / draw-in-style work.

A style is the visual realization of the projection over the one
coordinate-free NaturalLayout (docs/MANIFEST_AND_MEANING.md): three
manifests (Dau / Peirce / Sowa), one meaning, each §3.3-attested.  Style
varies the manifest, never the meaning.
"""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egif_parser_dau import parse_egif
from web_api import main as web_main
from web_api.services.layout_service import generate_layout


@pytest.fixture
def client():
    return TestClient(web_main.app)


def test_styles_endpoint_lists_the_three_with_default(client):
    body = client.get("/styles").json()
    assert body["success"] is True
    names = {s["name"] for s in body["data"]}
    assert {"dau-compliant@1.0", "peirce-authentic@1.0", "sowa-compliant@1.0"} <= names
    # Exactly the dau-compliant style is flagged default.
    defaults = [s["name"] for s in body["data"] if s.get("is_default")]
    assert defaults == ["dau-compliant@1.0"]


def test_each_style_renders_and_attests():
    """The same EGI renders in all three styles; each passes §3.3 (no
    CorrespondenceViolation) and the manifests genuinely differ."""
    egi = parse_egif("(Human *x) ~[ (Mortal x) ]")
    svgs = {}
    for sn in ("dau-compliant@1.0", "peirce-authentic@1.0", "sowa-compliant@1.0"):
        _dto, svg = generate_layout(egi, style_name=sn)  # raises on §3.3 failure
        assert svg.startswith("<")
        svgs[sn] = svg
    # Three distinct manifests of one meaning.
    assert len(set(svgs.values())) == 3


def test_default_style_matches_none():
    egi = parse_egif("(Human *x) ~[ (Mortal x) ]")
    _d1, svg_none = generate_layout(egi)
    _d2, svg_dau = generate_layout(egi, style_name="dau-compliant@1.0")
    assert svg_none == svg_dau


def test_unknown_style_raises():
    egi = parse_egif("(Human *x)")
    with pytest.raises(Exception):
        generate_layout(egi, style_name="no-such-style@9.9")


def test_renderer_honors_peirce_script_and_ink():
    """Peirce's declared style is actually drawn: italic script labels, a
    cursive font, and softer ink — while Dau stays upright black."""
    egi = parse_egif("(Human *x) ~[ (Mortal x) ]")
    _d, dau = generate_layout(egi, style_name="dau-compliant@1.0")
    _p, peirce = generate_layout(egi, style_name="peirce-authentic@1.0")
    # Peirce: italic + cursive family + non-black ink.
    assert 'font-style="italic"' in peirce
    assert "Chancery" in peirce or "cursive" in peirce
    assert "#1a1a1a" in peirce
    # Dau: no italic, upright black.
    assert "font-style" not in dau
    assert "#1a1a1a" not in dau


def _ellipse_contains_cut_contents(egi, dto, slack=1e-6):
    """Every direct child element of an oval cut lies inside that cut's
    inscribed ellipse — the Tier-2 containment convention.  Returns the count
    of (point, cut) pairs that fall outside."""
    violations = 0
    for cid, b in dto.cut_bounds.items():
        cx, cy = (b.min_x + b.max_x) / 2, (b.min_y + b.max_y) / 2
        rx, ry = b.width / 2, b.height / 2
        pts = []
        for child in egi.area.get(cid, ()):
            if child in dto.cut_bounds:
                cb = dto.cut_bounds[child]
                pts += [
                    (cb.min_x, cb.min_y), (cb.max_x, cb.min_y),
                    (cb.min_x, cb.max_y), (cb.max_x, cb.max_y),
                ]
            elif child in dto.vertex_positions:
                p = dto.vertex_positions[child]
                pts.append((p.x, p.y))
            elif child in dto.predicate_positions:
                p = dto.predicate_positions[child]
                pts.append((p.x, p.y))
        for px, py in pts:
            if ((px - cx) / rx) ** 2 + ((py - cy) / ry) ** 2 > 1.0 + slack:
                violations += 1
    return violations


def test_oval_styles_draw_ellipses_dau_keeps_rectangles():
    """cut_shape "oval" is realized as an ellipse-class figure: Sowa draws a
    crisp inscribed <ellipse>; Peirce (hand-drawn) draws a closed wobbled
    <path>.  The Dau rounded-rectangle stays a <rect> and never an ellipse."""
    egi = parse_egif("(Human *x) ~[ (Mortal x) ]")
    _d, dau = generate_layout(egi, style_name="dau-compliant@1.0")
    assert "<ellipse" not in dau and "<rect" in dau
    _s, sowa = generate_layout(egi, style_name="sowa-compliant@1.0")
    assert "<ellipse" in sowa
    _p, peirce = generate_layout(egi, style_name="peirce-authentic@1.0")
    assert "<ellipse" not in peirce and " Z" in peirce  # wobbled closed loop


def test_oval_cuts_contain_their_contents_including_nested():
    """The layout engine grows each oval cut so its inscribed ellipse contains
    its contents — even through a nested double cut, where a single padding
    pass would under-pad the outer cut (the refit cascade)."""
    for egif in (
        "(Human *x) ~[ (Mortal x) ]",
        "~[ ~[ (P *x) (Q x) (R x) ] ]",      # double cut, multi-content
        "~[ (A *x) ] ~[ (B *y) ] (C *z)",    # sibling cuts
    ):
        egi = parse_egif(egif)
        dto, _svg = generate_layout(egi, style_name="peirce-authentic@1.0")
        assert _ellipse_contains_cut_contents(egi, dto) == 0, egif


def test_peirce_hand_drawn_wobble_is_deterministic_and_scoped():
    """Peirce's hand-drawn variation turns the oval cut into a closed wobbled
    path; it is deterministic (same render every time, invariant L1) and does
    not leak into the wobble-free styles (Sowa keeps a crisp <ellipse>, Dau a
    <rect>)."""
    egi = parse_egif("~[ (Human *x) ~[ (Mortal x) ] ]")
    _p1, peirce1 = generate_layout(egi, style_name="peirce-authentic@1.0")
    _p2, peirce2 = generate_layout(egi, style_name="peirce-authentic@1.0")
    assert peirce1 == peirce2                      # deterministic "hand"
    assert "<ellipse" not in peirce1               # oval wobbled into a path…
    assert " Z" in peirce1                          # …a closed loop
    # Wobble-free styles are untouched.
    _s1, sowa = generate_layout(egi, style_name="sowa-compliant@1.0")
    assert "<ellipse" in sowa
    _d1, dau = generate_layout(egi, style_name="dau-compliant@1.0")
    assert "<ellipse" not in dau and "<rect" in dau


def test_jitter_is_stable_and_bounded():
    """The wobble's pseudo-randomness is reproducible (hash-based, not salted)
    and stays in [-1, 1]."""
    from simple_svg_renderer import SimpleSVGRenderer as R
    vals = [R._jitter("cut-abc", i) for i in range(50)]
    assert all(-1.0 <= v <= 1.0 for v in vals)
    assert vals == [R._jitter("cut-abc", i) for i in range(50)]   # stable
    assert R._jitter("cut-abc", 0) != R._jitter("cut-xyz", 0)     # seed matters


def test_smooth_path_curves_multipoint_ligatures():
    """Organic routing curves a multi-point line of identity (Catmull-Rom →
    cubic Bézier), and is a straight segment for two points."""
    from collections import namedtuple
    from simple_svg_renderer import SimpleSVGRenderer
    P = namedtuple("P", "x y")
    three = SimpleSVGRenderer._smooth_path([P(0, 0), P(10, 20), P(30, 0)], 0, 0)
    assert " C " in three  # cubic curve segments
    two = SimpleSVGRenderer._smooth_path([P(0, 0), P(10, 10)], 0, 0)
    assert " C " not in two and " L " in two
