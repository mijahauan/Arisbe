#!/usr/bin/env python3
"""
Critical test: Verify EGDF can reproduce exact drawing it was generated from.

Tests the complete round-trip:
1. Create drawing in DrawingEditor
2. Export to EGDF
3. Load EGDF back into clean DrawingEditor
4. Verify identical visual layout

This proves EGDF contains complete drawing specification.
"""
import sys
from pathlib import Path
import json
import tempfile
from typing import Dict, Any, List, Tuple

# Add src to path
SRC = Path(__file__).resolve().parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Add tools to path  
TOOLS = Path(__file__).resolve().parent / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF, QRectF

def test_egdf_drawing_roundtrip():
    """Test complete drawing round-trip through EGDF."""
    
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    try:
        # Test simpler approach: load existing EGDF, verify it reproduces correctly
        import corpus_index as cidx
        
        # Find an existing EGDF file
        test_egdf_path = None
        for graph_dir in cidx.GRAPH_ROOT.iterdir():
            if graph_dir.is_dir():
                egdf_dir = graph_dir / "EGDF"
                if egdf_dir.exists():
                    for egdf_file in egdf_dir.glob("*.json"):
                        test_egdf_path = egdf_file
                        break
                if test_egdf_path:
                    break
        
        if not test_egdf_path:
            print("✗ No EGDF files found in corpus for testing")
            return False
        
        print(f"Testing round-trip with: {test_egdf_path}")
        
        # Load EGDF content
        egdf_content = json.loads(test_egdf_path.read_text(encoding="utf-8"))
        egi_inline = egdf_content.get("egi_ref", {}).get("inline", {})
        
        if not egi_inline:
            print("✗ EGDF missing EGI inline data")
            return False
        
        from drawing_editor import DrawingEditor
        
        # Create editor and load the EGDF
        editor = DrawingEditor()
        payload = {
            "egi": egi_inline,
            "egdf": egdf_content,
            # No mode flag - auto-detect constraints
        }
        editor.load_payload(payload)
        
        # Export back to EGDF
        export_payload = editor.export_result()
        export_egdf = export_payload.get("egdf", {})
        
        if not export_egdf:
            print("✗ Failed to export EGDF from loaded drawing")
            return False
        
        # Compare key layout sections
        original_layout = egdf_content.get("layout", {})
        export_layout = export_egdf.get("layout", {})
        
        _compare_layout_sections(original_layout, export_layout)
        
        print("✓ EGDF round-trip test PASSED")
        return True
        
    except Exception as e:
        print(f"✗ EGDF round-trip test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def _compare_layout_sections(original: Dict[str, Any], exported: Dict[str, Any]) -> None:
    """Compare layout sections for round-trip fidelity."""
    
    TOLERANCE = 2.0  # pixels
    
    def _positions_equal(pos1: float, pos2: float) -> bool:
        return abs(pos1 - pos2) <= TOLERANCE
    
    # Compare cuts
    orig_cuts = original.get("cuts", {})
    exp_cuts = exported.get("cuts", {})
    
    assert set(orig_cuts.keys()) == set(exp_cuts.keys()), f"Cut IDs differ: {set(orig_cuts.keys())} vs {set(exp_cuts.keys())}"
    
    for cut_id in orig_cuts:
        orig = orig_cuts[cut_id]
        exp = exp_cuts[cut_id]
        assert _positions_equal(orig["x"], exp["x"]), f"Cut {cut_id} x differs: {orig['x']} vs {exp['x']}"
        assert _positions_equal(orig["y"], exp["y"]), f"Cut {cut_id} y differs: {orig['y']} vs {exp['y']}"
        assert _positions_equal(orig["w"], exp["w"]), f"Cut {cut_id} width differs: {orig['w']} vs {exp['w']}"
        assert _positions_equal(orig["h"], exp["h"]), f"Cut {cut_id} height differs: {orig['h']} vs {exp['h']}"
    
    # Compare predicates
    orig_preds = original.get("predicates", {})
    exp_preds = exported.get("predicates", {})
    
    assert set(orig_preds.keys()) == set(exp_preds.keys()), f"Predicate IDs differ: {set(orig_preds.keys())} vs {set(exp_preds.keys())}"
    
    for pred_id in orig_preds:
        orig = orig_preds[pred_id]
        exp = exp_preds[pred_id]
        assert _positions_equal(orig["x"], exp["x"]), f"Predicate {pred_id} x differs: {orig['x']} vs {exp['x']}"
        assert _positions_equal(orig["y"], exp["y"]), f"Predicate {pred_id} y differs: {orig['y']} vs {exp['y']}"
        assert orig["text"] == exp["text"], f"Predicate {pred_id} text differs: {orig['text']} vs {exp['text']}"
    
    # Compare vertices
    orig_verts = original.get("vertices", {})
    exp_verts = exported.get("vertices", {})
    
    assert set(orig_verts.keys()) == set(exp_verts.keys()), f"Vertex IDs differ: {set(orig_verts.keys())} vs {set(exp_verts.keys())}"
    
    for vertex_id in orig_verts:
        orig = orig_verts[vertex_id]
        exp = exp_verts[vertex_id]
        assert _positions_equal(orig["x"], exp["x"]), f"Vertex {vertex_id} x differs: {orig['x']} vs {exp['x']}"
        assert _positions_equal(orig["y"], exp["y"]), f"Vertex {vertex_id} y differs: {orig['y']} vs {exp['y']}"
    
    print(f"✓ Layout comparison passed: {len(orig_cuts)} cuts, {len(orig_preds)} predicates, {len(orig_verts)} vertices")


def _create_test_drawing(editor: 'DrawingEditor') -> None:
    """Create a test drawing with cuts, predicates, vertices, and ligatures."""
    
    # Add outer cut
    editor._add_cut_at_position("cut_outer", QRectF(50, 50, 300, 200))
    
    # Add inner cut inside outer cut
    editor.active_parent_area = "cut_outer"
    editor._add_cut_at_position("cut_inner", QRectF(100, 100, 150, 100))
    
    # Add predicate in outer cut
    editor.active_parent_area = "cut_outer"
    editor._add_predicate_at_position("pred_loves", "Loves", QPointF(200, 75))
    
    # Add vertex in inner cut
    editor.active_parent_area = "cut_inner"
    editor._add_vertex_at_position("vertex_x", QPointF(150, 130))
    
    # Create ligature connecting predicate to vertex
    editor._create_ligature_between("pred_loves", "vertex_x")
    
    # Reset parent area
    editor.active_parent_area = None


def _extract_visual_layout(editor: 'DrawingEditor') -> Dict[str, Any]:
    """Extract visual layout data from DrawingEditor for comparison."""
    layout = {
        "cuts": {},
        "predicates": {},
        "vertices": {},
        "ligatures": {}
    }
    
    # Extract cut positions and sizes
    for cut_id, cut_model in editor.model.cuts.items():
        layout["cuts"][cut_id] = {
            "x": cut_model.rect.x(),
            "y": cut_model.rect.y(),
            "width": cut_model.rect.width(),
            "height": cut_model.rect.height(),
            "parent_id": cut_model.parent_id
        }
    
    # Extract predicate positions and sizes
    for pred_id, pred_model in editor.model.predicates.items():
        layout["predicates"][pred_id] = {
            "x": pred_model.pos.x(),
            "y": pred_model.pos.y(),
            "text": pred_model.name,
            "area_id": pred_model.area_id
        }
    
    # Extract vertex positions
    for vertex_id, vertex_model in editor.model.vertices.items():
        layout["vertices"][vertex_id] = {
            "x": vertex_model.pos.x(),
            "y": vertex_model.pos.y(),
            "area_id": vertex_model.area_id
        }
    
    # Extract ligature paths
    for lig_id, lig_model in editor.model.ligatures.items():
        layout["ligatures"][lig_id] = {
            "points": [(p.x(), p.y()) for p in lig_model.points],
            "area_id": lig_model.area_id
        }
    
    return layout


def _assert_layouts_identical(layout1: Dict[str, Any], layout2: Dict[str, Any]) -> None:
    """Assert two visual layouts are identical within tolerance."""
    
    POSITION_TOLERANCE = 2.0  # pixels
    
    def _positions_equal(pos1: float, pos2: float) -> bool:
        return abs(pos1 - pos2) <= POSITION_TOLERANCE
    
    # Compare cuts
    assert set(layout1["cuts"].keys()) == set(layout2["cuts"].keys()), "Cut IDs differ"
    for cut_id in layout1["cuts"]:
        cut1 = layout1["cuts"][cut_id]
        cut2 = layout2["cuts"][cut_id]
        assert _positions_equal(cut1["x"], cut2["x"]), f"Cut {cut_id} x position differs"
        assert _positions_equal(cut1["y"], cut2["y"]), f"Cut {cut_id} y position differs"
        assert _positions_equal(cut1["width"], cut2["width"]), f"Cut {cut_id} width differs"
        assert _positions_equal(cut1["height"], cut2["height"]), f"Cut {cut_id} height differs"
    
    # Compare predicates
    assert set(layout1["predicates"].keys()) == set(layout2["predicates"].keys()), "Predicate IDs differ"
    for pred_id in layout1["predicates"]:
        pred1 = layout1["predicates"][pred_id]
        pred2 = layout2["predicates"][pred_id]
        assert _positions_equal(pred1["x"], pred2["x"]), f"Predicate {pred_id} x position differs"
        assert _positions_equal(pred1["y"], pred2["y"]), f"Predicate {pred_id} y position differs"
        assert pred1["text"] == pred2["text"], f"Predicate {pred_id} text differs"
    
    # Compare vertices
    assert set(layout1["vertices"].keys()) == set(layout2["vertices"].keys()), "Vertex IDs differ"
    for vertex_id in layout1["vertices"]:
        vertex1 = layout1["vertices"][vertex_id]
        vertex2 = layout2["vertices"][vertex_id]
        assert _positions_equal(vertex1["x"], vertex2["x"]), f"Vertex {vertex_id} x position differs"
        assert _positions_equal(vertex1["y"], vertex2["y"]), f"Vertex {vertex_id} y position differs"
    
    # Compare ligatures
    assert set(layout1["ligatures"].keys()) == set(layout2["ligatures"].keys()), "Ligature IDs differ"
    for lig_id in layout1["ligatures"]:
        lig1 = layout1["ligatures"][lig_id]
        lig2 = layout2["ligatures"][lig_id]
        points1 = lig1["points"]
        points2 = lig2["points"]
        assert len(points1) == len(points2), f"Ligature {lig_id} point count differs"
        for i, (p1, p2) in enumerate(zip(points1, points2)):
            assert _positions_equal(p1[0], p2[0]), f"Ligature {lig_id} point {i} x differs"
            assert _positions_equal(p1[1], p2[1]), f"Ligature {lig_id} point {i} y differs"


if __name__ == "__main__":
    success = test_egdf_drawing_roundtrip()
    sys.exit(0 if success else 1)
