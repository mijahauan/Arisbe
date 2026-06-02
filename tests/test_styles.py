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
