"""
Test Layout Engine Ligature and Predicate Rendering

Demonstrates the current gap: layout engine doesn't compute ligature paths
or predicate positions, which are essential for EG diagrams.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from layout_engine import LayoutEngine
from egif_parser_dau import parse_egif
from gui.styles.dau_compliant_style import DauCompliantStyle


def test_ligature_rendering_gap():
    """Demonstrate that ligatures are not currently rendered"""
    engine = LayoutEngine()
    style = DauCompliantStyle()
    
    # EGIF with explicit relation (should have ligatures)
    egif = '*x *y (Loves x y)'
    egi = parse_egif(egif)
    
    print(f"\nEGIF: {egif}")
    print(f"Vertices in EGI: {len(egi.V)}")
    print(f"Edges in EGI: {len(egi.E)}")
    
    # Generate layout
    layout = engine.compute_layout(egi, diagram_style=style)
    
    print(f"Vertex positions: {len(layout.vertex_positions)}")
    print(f"Edge paths: {len(layout.edge_paths)}")  # This will be 0!
    print(f"Cut bounds: {len(layout.cut_bounds)}")
    
    # The problem: we have edges in the EGI but no edge paths in the layout
    assert len(egi.E) > 0, "EGI should have edges for the relation"
    assert len(layout.edge_paths) == 0, "Current layout engine doesn't compute edge paths"
    
    print("❌ Gap identified: Layout engine ignores ligatures!")


def test_predicate_rendering_gap():
    """Demonstrate that predicates are not positioned"""
    engine = LayoutEngine()
    style = DauCompliantStyle()
    
    # EGIF with predicate
    egif = '*x (Human x)'
    egi = parse_egif(egif)
    
    print(f"\nEGIF: {egif}")
    print(f"Vertices: {len(egi.V)}")
    print(f"Edges: {len(egi.E)}")
    
    layout = engine.compute_layout(egi, diagram_style=style)
    
    # Check what we're missing
    for edge in egi.E:
        print(f"Edge {edge.id}: {edge.relation_name} - not positioned in layout")
    
    print("❌ Gap identified: Predicates have no spatial representation!")


if __name__ == "__main__":
    test_ligature_rendering_gap()
    test_predicate_rendering_gap()
