#!/usr/bin/env python3
"""
Simple test to verify QtDiagramCanvas fixes work
"""

import sys
sys.path.insert(0, 'src')

from PySide6.QtWidgets import QApplication
from qt_diagram_canvas import QtDiagramCanvas

def test_basic_rendering():
    """Test basic rendering with fixed implementation."""
    print("🔧 Testing QtDiagramCanvas fixes...")
    
    app = QApplication([])
    
    try:
        # Create canvas
        canvas = QtDiagramCanvas(400, 300)
        
        # Test vertex rendering (was broken)
        canvas.add_vertex((100, 150), "test_vertex")
        print("✅ Vertex rendering: No crash")
        
        # Test identity line rendering  
        canvas.add_identity_line((100, 150), (200, 150), "test_identity")
        print("✅ Identity line rendering: No crash")
        
        # Test predicate text rendering (was broken)
        canvas.add_predicate_text((250, 150), "Test", "test_text")
        print("✅ Predicate text rendering: No crash")
        
        # Test generic line rendering (was missing)
        canvas.add_element({
            "element_type": "line",
            "element_id": "test_line",
            "coordinates": [(50, 200), (150, 200)],
            "style_override": {"line_width": 2.0}
        })
        print("✅ Generic line rendering: No crash")
        
        # Test rendering
        canvas.render_complete()
        print("✅ Canvas rendering: No crash")
        
        # Test save (was broken)
        success = canvas.save_to_file("test_qt_fixes.png")
        if success:
            print("✅ File save: Success")
        else:
            print("❌ File save: Failed")
        
        app.quit()
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        app.quit()
        return False

if __name__ == "__main__":
    success = test_basic_rendering()
    if success:
        print("\n🎯 Basic rendering fixes verified!")
        print("Next: Check visual compliance with Dau conventions")
    else:
        print("\n🚨 Still has critical bugs!")
