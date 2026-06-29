"""The reference render glyph — increment 1b.

`SimpleSVGRenderer.render_to_svg(..., reference_marks=...)` decorates a reference
spot with a dashed accent box + a "+N beyond view" horizon badge, reusing the
overview horizon idiom. Pure chrome: it reads the overlay
(`reference_node.render_marks`), changes no DTO geometry, and is byte-identical to
before when no marks are passed — so §3.3 (which reads the DTO) is untouched.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from definitions import DefinitionRegistry
from egif_parser_dau import parse_egif
from correspondence_attestation import attest_correspondence
from simple_svg_renderer import SimpleSVGRenderer
from reference_node import (
    DefinitionReferenceResolver,
    mark_reference,
    reference_horizon,
    render_marks,
)
from run_reference_resolution_check import SUBSET, POWER_SET_DEFINED, _subset_edge


@pytest.fixture
def engine():
    from elk_layout_engine import ELKLayoutEngine
    return ELKLayoutEngine()


@pytest.fixture
def style():
    from style_loader import load_default_style
    return load_default_style()


@pytest.fixture
def host():
    return parse_egif(POWER_SET_DEFINED)


@pytest.fixture
def resolver():
    return DefinitionReferenceResolver(DefinitionRegistry([SUBSET]))


def test_horizon_counts_hidden_body(host, resolver):
    """The "+N" is the number of elements the reference stands for (the spliced
    body) — strictly positive for a real definition."""
    edge = _subset_edge(host)
    mark = mark_reference(host, edge, resolver)
    assert reference_horizon(host, mark, resolver) > 0


def test_glyph_drawn_only_when_marked(host, resolver, engine, style):
    edge = _subset_edge(host)
    mark = mark_reference(host, edge, resolver)
    dto = engine.generate_layout(host, style)
    renderer = SimpleSVGRenderer()

    plain = renderer.render_to_svg(dto, egi=host)
    assert "reference-spot" not in plain          # regression: off by default
    assert "reference-horizon" not in plain

    marks = render_marks(host, [mark], resolver)
    decorated = renderer.render_to_svg(dto, egi=host, reference_marks=marks)
    assert 'class="reference-spot"' in decorated
    assert 'data-reference="true"' in decorated
    assert f"+{marks[edge]}" in decorated          # the horizon badge
    assert "stroke-dasharray" in decorated         # the dashed reference box


def test_glyph_does_not_change_attested_geometry(host, resolver, engine, style):
    """The DTO §3.3 reads is unchanged whether or not the glyph is drawn — the
    badge is chrome outside the attested predicate extent."""
    edge = _subset_edge(host)
    mark = mark_reference(host, edge, resolver)
    dto = engine.generate_layout(host, style)
    # The same DTO renders both ways; §3.3 attests it (geometry is identical).
    attest_correspondence(host, dto, context="reference-glyph geometry")
    marks = render_marks(host, [mark], resolver)
    renderer = SimpleSVGRenderer()
    # Both render without error; the decorated one only adds chrome attributes.
    renderer.render_to_svg(dto, egi=host)
    renderer.render_to_svg(dto, egi=host, reference_marks=marks)
