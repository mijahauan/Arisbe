#!/usr/bin/env python3
"""
Debug script to check if graphics items have the correct flags for editability.
"""
import sys
from pathlib import Path

# Add paths
SRC = Path(__file__).resolve().parent / "src"
TOOLS = Path(__file__).resolve().parent / "tools"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from PySide6.QtWidgets import QApplication, QGraphicsItem
from PySide6.QtCore import QPointF
import corpus_index as cidx
import json

def check_graphics_flags():
    """Check if loaded graphics items have correct flags."""
    
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    from drawing_editor import DrawingEditor
    
    # Find an EGDF file to test with
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
        print("No EGDF files found")
        return
    
    print(f"Testing with: {test_egdf_path}")
    
    # Load EGDF
    egdf_content = json.loads(test_egdf_path.read_text(encoding="utf-8"))
    egi_inline = egdf_content.get("egi_ref", {}).get("inline", {})
    
    payload = {
        "egi": egi_inline,
        "egdf": egdf_content
    }
    
    editor = DrawingEditor()
    editor.load_payload(payload)
    
    print(f"\nEditor mode: {editor.erg_mode}")
    print(f"EGI locked: {editor.egi_locked}")
    print(f"Scene items: {len(editor.scene.items())}")
    
    # Check vertex flags
    print(f"\nVertices ({len(editor.model.vertices)}):")
    for vid, vertex in editor.model.vertices.items():
        gfx = vertex.gfx
        flags = gfx.flags()
        print(f"  {vid}:")
        print(f"    ItemIsMovable: {bool(flags & QGraphicsItem.ItemIsMovable)}")
        print(f"    ItemIsSelectable: {bool(flags & QGraphicsItem.ItemIsSelectable)}")
        print(f"    ItemSendsGeometryChanges: {bool(flags & QGraphicsItem.ItemSendsGeometryChanges)}")
        print(f"    Position: {gfx.pos()}")
    
    # Check predicate flags
    print(f"\nPredicates ({len(editor.model.predicates)}):")
    for pid, predicate in editor.model.predicates.items():
        gfx = predicate.gfx_rect
        flags = gfx.flags()
        print(f"  {pid}:")
        print(f"    ItemIsMovable: {bool(flags & QGraphicsItem.ItemIsMovable)}")
        print(f"    ItemIsSelectable: {bool(flags & QGraphicsItem.ItemIsSelectable)}")
        print(f"    ItemSendsGeometryChanges: {bool(flags & QGraphicsItem.ItemSendsGeometryChanges)}")
        print(f"    Position: {gfx.pos()}")

if __name__ == "__main__":
    check_graphics_flags()
