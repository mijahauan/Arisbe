#!/usr/bin/env python3
"""
Trace the exact sequence of drawing creation to understand what state we need to reproduce.
This will help identify the minimal working process and obsolete code remnants.
"""
import sys
from pathlib import Path
import json

# Add src and tools to path
SRC = Path(__file__).resolve().parent / "src"
TOOLS = Path(__file__).resolve().parent / "tools"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from PySide6.QtWidgets import QApplication, QGraphicsItem
from PySide6.QtCore import QPointF, QRectF

def trace_interactive_drawing():
    """Trace what happens when creating a drawing interactively."""
    
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    from drawing_editor import DrawingEditor
    
    print("=== TRACING INTERACTIVE DRAWING CREATION ===")
    
    # Create editor
    editor = DrawingEditor()
    print(f"1. Editor created - scene items: {len(editor.scene.items())}")
    
    # Add a vertex manually (simulate user click)
    print("2. Adding vertex manually...")
    vertex_pos = QPointF(100, 100)
    
    # Trace what _add_vertex_at_position actually does
    print("   - Before add_vertex: scene items =", len(editor.scene.items()))
    print("   - Model vertices =", len(editor.model.vertices))
    
    vertex_id = editor._add_vertex_at_position("test_vertex", vertex_pos)
    
    print("   - After add_vertex: scene items =", len(editor.scene.items()))
    print("   - Model vertices =", len(editor.model.vertices))
    print("   - Vertex graphics item flags:")
    
    if "test_vertex" in editor.model.vertices:
        vertex = editor.model.vertices["test_vertex"]
        gfx = vertex.gfx
        print(f"     - ItemIsMovable: {bool(gfx.flags() & QGraphicsItem.ItemIsMovable)}")
        print(f"     - ItemIsSelectable: {bool(gfx.flags() & QGraphicsItem.ItemIsSelectable)}")
        print(f"     - Position: {gfx.pos()}")
        print(f"     - Scene position: {gfx.scenePos()}")
    
    # Add a predicate
    print("3. Adding predicate manually...")
    pred_pos = QPointF(150, 100)
    
    print("   - Before add_predicate: scene items =", len(editor.scene.items()))
    print("   - Model predicates =", len(editor.model.predicates))
    
    pred_id = editor._add_predicate_at_position("test_pred", "TestPred", pred_pos)
    
    print("   - After add_predicate: scene items =", len(editor.scene.items()))
    print("   - Model predicates =", len(editor.model.predicates))
    
    if "test_pred" in editor.model.predicates:
        predicate = editor.model.predicates["test_pred"]
        gfx = predicate.gfx_rect
        print(f"     - ItemIsMovable: {bool(gfx.flags() & QGraphicsItem.ItemIsMovable)}")
        print(f"     - ItemIsSelectable: {bool(gfx.flags() & QGraphicsItem.ItemIsSelectable)}")
        print(f"     - Position: {gfx.pos()}")
        print(f"     - Scene position: {gfx.scenePos()}")
    
    # Export to see what gets saved
    print("4. Exporting to EGDF...")
    export_result = editor.export_result()
    egdf = export_result.get("egdf", {})
    layout = egdf.get("layout", {})
    
    print("   - Exported vertices:", list(layout.get("vertices", {}).keys()))
    print("   - Exported predicates:", list(layout.get("predicates", {}).keys()))
    
    return export_result

def trace_egdf_loading(egdf_payload):
    """Trace what happens when loading the same data from EGDF."""
    
    print("\n=== TRACING EGDF LOADING ===")
    
    from drawing_editor import DrawingEditor
    
    # Create fresh editor
    editor = DrawingEditor()
    print(f"1. Fresh editor created - scene items: {len(editor.scene.items())}")
    
    # Load the payload
    print("2. Loading EGDF payload...")
    print("   - Before load_payload: scene items =", len(editor.scene.items()))
    print("   - Model vertices =", len(editor.model.vertices))
    print("   - Model predicates =", len(editor.model.predicates))
    
    editor.load_payload(egdf_payload)
    
    print("   - After load_payload: scene items =", len(editor.scene.items()))
    print("   - Model vertices =", len(editor.model.vertices))
    print("   - Model predicates =", len(editor.model.predicates))
    
    # Check the loaded graphics items
    print("3. Checking loaded graphics items...")
    
    for vid, vertex in editor.model.vertices.items():
        gfx = vertex.gfx
        print(f"   - Vertex {vid}:")
        print(f"     - ItemIsMovable: {bool(gfx.flags() & QGraphicsItem.ItemIsMovable)}")
        print(f"     - ItemIsSelectable: {bool(gfx.flags() & QGraphicsItem.ItemIsSelectable)}")
        print(f"     - Position: {gfx.pos()}")
        print(f"     - Scene position: {gfx.scenePos()}")
    
    for pid, predicate in editor.model.predicates.items():
        gfx = predicate.gfx_rect
        print(f"   - Predicate {pid}:")
        print(f"     - ItemIsMovable: {bool(gfx.flags() & QGraphicsItem.ItemIsMovable)}")
        print(f"     - ItemIsSelectable: {bool(gfx.flags() & QGraphicsItem.ItemIsSelectable)}")
        print(f"     - Position: {gfx.pos()}")
        print(f"     - Scene position: {gfx.scenePos()}")

def main():
    """Run the tracing to understand the difference between working and broken states."""
    
    try:
        # Trace interactive creation (working)
        export_result = trace_interactive_drawing()
        
        # Trace EGDF loading (broken)
        trace_egdf_loading(export_result)
        
        print("\n=== ANALYSIS ===")
        print("Compare the flags and states above to see what differs between")
        print("interactive creation (working) and EGDF loading (broken).")
        
    except Exception as e:
        print(f"Error during tracing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
