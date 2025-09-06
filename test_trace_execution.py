#!/usr/bin/env python3
"""
Test the tracing system to see what actually executes.
Run with: TRACE_EXECUTION=1 python test_trace_execution.py
"""
import os
import sys
from pathlib import Path

# Enable tracing
os.environ['TRACE_EXECUTION'] = '1'

# Add paths
SRC = Path(__file__).resolve().parent / "src"
TOOLS = Path(__file__).resolve().parent / "tools"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

def test_interactive_creation():
    """Test what functions execute during interactive drawing creation."""
    print("\n=== INTERACTIVE CREATION TRACE ===")
    
    from drawing_editor import DrawingEditor
    
    editor = DrawingEditor()
    
    # Add vertex interactively
    print("\n--- Adding vertex interactively ---")
    editor._add_vertex_at_position("test_v", QPointF(100, 100))
    
    # Export
    print("\n--- Exporting ---")
    result = editor.export_result()
    
    # Create proper payload structure for loading
    egdf = result.get("egdf", {})
    egi_inline = egdf.get("egi_ref", {}).get("inline", {})
    
    payload = {
        "egi": egi_inline,  # This is what load_payload expects
        "egdf": egdf
    }
    
    print(f"Created payload with EGI keys: {list(egi_inline.keys()) if egi_inline else 'Empty'}")
    
    return payload

def test_egdf_loading(payload):
    """Test what functions execute during EGDF loading."""
    print("\n=== EGDF LOADING TRACE ===")
    
    from drawing_editor import DrawingEditor
    
    editor = DrawingEditor()
    
    # Load payload with actual EGDF data
    print("\n--- Loading EGDF payload ---")
    print(f"Payload keys: {list(payload.keys()) if payload else 'None'}")
    if payload and 'egdf' in payload:
        print(f"EGDF keys: {list(payload['egdf'].keys())}")
    if payload and 'egi' in payload:
        print(f"EGI data present: {bool(payload['egi'])}")
        print(f"EGI keys: {list(payload['egi'].keys()) if payload['egi'] else 'Empty'}")
    editor.load_payload(payload)
    
    return editor

def main():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    try:
        # Test interactive creation
        payload = test_interactive_creation()
        
        # Test EGDF loading
        test_egdf_loading(payload)
        
        print("\n=== TRACE COMPLETE ===")
        print("Compare the function calls above to see what differs between")
        print("interactive creation and EGDF loading.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
