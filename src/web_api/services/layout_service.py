"""
Layout and SVG generation service for the Arisbe Web API.

Wraps ELKLayoutEngine and SimpleSVGRenderer with anchoring support.
"""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

# Ensure src/ is on path (when imported from web_api/services/)
_src_dir = Path(__file__).parent.parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from correspondence_attestation import attest_correspondence
from elk_layout_engine import ELKLayoutEngine
from layout_dto import LayoutDTO, BoundingBox, LigaturePath, Point
from simple_svg_renderer import SimpleSVGRenderer
from style_loader import load_default_style
from egif_generator_dau import EGIFGenerator


@dataclass
class LayoutDelta:
    """Position anchor for an element during re-layout."""
    new_position: Optional[Tuple[float, float]] = None


def generate_layout(
    egi,
    previous_layout: Optional[LayoutDTO] = None,
) -> Tuple[LayoutDTO, str]:
    """Generate layout and SVG for an EGI.

    If *previous_layout* is provided, unchanged elements are anchored at
    their previous positions to reduce visual jump.

    Returns:
        (layout_dto, svg_string)
    """
    style = load_default_style()
    engine = ELKLayoutEngine()

    # Build layout_deltas from previous layout when available
    layout_deltas: Optional[Dict[str, LayoutDelta]] = None
    if previous_layout is not None:
        layout_deltas = {}
        for v_id, pos in previous_layout.vertex_positions.items():
            layout_deltas[v_id] = LayoutDelta(new_position=(pos.x, pos.y))
        for p_id, pos in previous_layout.predicate_positions.items():
            layout_deltas[p_id] = LayoutDelta(new_position=(pos.x, pos.y))

    dto = engine.generate_layout(egi, style, layout_deltas=layout_deltas)

    # Boundary-event attestation (docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md
    # §6, §8 bullet 1).  Every (EGI, DTO) pair we hand to the renderer
    # — initial diagram serve, post-transformation re-render, anywhere
    # else this wrapper is called from — is verified to be in §3.3
    # correspondence before it leaves the service.  A drift between
    # picture and proposition raises CorrespondenceViolation; the
    # system refuses to serve a drawing it can't attest.
    attest_correspondence(egi, dto, context="layout_service.generate_layout")

    # Generate EGIF linear form for the renderer title
    try:
        egif = EGIFGenerator().generate(egi)
    except Exception:
        egif = ""

    renderer = SimpleSVGRenderer()
    svg = renderer.render_to_svg(dto, title="Existential Graph", egif=egif, egi=egi)

    return dto, svg


def layout_dto_to_dict(dto: LayoutDTO) -> dict:
    """Serialize a LayoutDTO to a JSON-compatible dict."""
    vertex_positions = {
        k: {"x": v.x, "y": v.y} for k, v in dto.vertex_positions.items()
    }
    predicate_positions = {
        k: {"x": v.x, "y": v.y} for k, v in dto.predicate_positions.items()
    }
    cut_bounds = {
        k: {
            "min_x": b.min_x,
            "min_y": b.min_y,
            "max_x": b.max_x,
            "max_y": b.max_y,
        }
        for k, b in dto.cut_bounds.items()
    }
    ligature_paths = [
        {
            "predicate_id": lig.predicate_id,
            "vertex_id": lig.vertex_id,
            "points": [{"x": p.x, "y": p.y} for p in lig.points],
            "port_index": lig.port_index,
        }
        for lig in dto.ligature_paths
    ]
    viewport_bounds = {
        "min_x": dto.viewport_bounds.min_x,
        "min_y": dto.viewport_bounds.min_y,
        "max_x": dto.viewport_bounds.max_x,
        "max_y": dto.viewport_bounds.max_y,
    }
    return {
        "vertex_positions": vertex_positions,
        "predicate_positions": predicate_positions,
        "cut_bounds": cut_bounds,
        "ligature_paths": ligature_paths,
        "viewport_bounds": viewport_bounds,
        "sheet_id": dto.sheet_id,
    }
