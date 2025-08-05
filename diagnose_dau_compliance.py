#!/usr/bin/env python3
"""
Dau Compliance Visual Diagnostic

Create side-by-side comparisons to identify exactly what's wrong 
with the QtDiagramCanvas Dau compliance.
"""

import sys
sys.path.insert(0, 'src')

from PySide6.QtWidgets import QApplication
from qt_diagram_canvas import QtDiagramCanvas

def create_dau_compliance_test():
    """Create visual test to identify Dau compliance issues."""
    print("🔍 Creating Dau Compliance Visual Diagnostic")
    print("=" * 50)
    
    app = QApplication([])
    
    # Test 1: Line Width Comparison (Critical for Dau compliance)
    print("1. Testing Heavy vs Fine Line Distinction...")
    canvas = QtDiagramCanvas(600, 400)
    
    # Heavy identity line (should be 4.0 width - very prominent)
    canvas.add_identity_line((50, 100), (200, 100), "heavy_4_0")
    canvas.add_predicate_text((125, 80), "Heavy Identity (4.0w)", "label_heavy")
    
    # Fine cut boundary (should be 1.0 width - delicate)
    canvas.add_cut((50, 150, 150, 50), "fine_1_0")
    canvas.add_predicate_text((125, 130), "Fine Cut (1.0w)", "label_fine")
    
    # Reference lines for visual comparison
    canvas.add_element({
        "element_type": "line",
        "element_id": "ref_1",
        "coordinates": [(250, 100), (400, 100)],
        "style_override": {"line_width": 1.0}
    })
    canvas.add_predicate_text((325, 80), "Reference 1.0w", "ref_1_label")
    
    canvas.add_element({
        "element_type": "line",
        "element_id": "ref_2",
        "coordinates": [(250, 130), (400, 130)],
        "style_override": {"line_width": 2.0}
    })
    canvas.add_predicate_text((325, 110), "Reference 2.0w", "ref_2_label")
    
    canvas.add_element({
        "element_type": "line",
        "element_id": "ref_4",
        "coordinates": [(250, 160), (400, 160)],
        "style_override": {"line_width": 4.0}
    })
    canvas.add_predicate_text((325, 140), "Reference 4.0w", "ref_4_label")
    
    # Title
    canvas.add_predicate_text((300, 30), "Dau Compliance Test: Heavy vs Fine Lines", "title")
    
    # Expected result description
    canvas.add_predicate_text((300, 200), "EXPECTED: Heavy identity should be 4x thicker than fine cut", "expected")
    canvas.add_predicate_text((300, 220), "PROBLEM: If they look similar, rendering is not Dau-compliant", "problem")
    
    canvas.render_complete()
    canvas.save_to_file("dau_compliance_line_widths.png")
    print("   Saved: dau_compliance_line_widths.png")
    
    # Test 2: Vertex Prominence Test
    print("2. Testing Vertex Spot Prominence...")
    canvas.clear_elements()
    
    # Test different vertex sizes to see if 3.5 is actually prominent
    sizes = [1.0, 2.0, 3.0, 3.5, 4.0, 5.0]
    for i, size in enumerate(sizes):
        x = 50 + i * 80
        canvas.add_element({
            "element_type": "vertex",
            "element_id": f"vertex_{i}",
            "coordinates": [(x, 150)],
            "style_override": {"vertex_radius": size}
        })
        canvas.add_predicate_text((x, 180), f"{size}r", f"size_label_{i}")
        
        # Add identity line for context
        canvas.add_identity_line((x, 150), (x, 120), f"identity_{i}")
    
    canvas.add_predicate_text((250, 50), "Vertex Spot Prominence Test", "title2")
    canvas.add_predicate_text((250, 80), "Dau Standard: 3.5 radius (should be clearly visible)", "dau_std")
    canvas.add_predicate_text((250, 220), "PROBLEM: If 3.5r spots are hard to see, not Dau-compliant", "problem2")
    
    canvas.render_complete()
    canvas.save_to_file("dau_compliance_vertex_prominence.png")
    print("   Saved: dau_compliance_vertex_prominence.png")
    
    # Test 3: Complete EG with Dau Elements
    print("3. Testing Complete EG Diagram...")
    canvas.clear_elements()
    
    # Simple predicate: (Human "Socrates")
    canvas.add_vertex((100, 200), "socrates_vertex")
    canvas.add_identity_line((100, 200), (180, 200), "socrates_identity")
    canvas.add_predicate_text((220, 200), "Human", "human_pred")
    canvas.add_hook_line((180, 200), (220, 200), "human_hook")
    
    # Negated predicate: ~[ (Mortal "Socrates") ]
    canvas.add_cut((300, 150, 200, 100), "mortal_cut")
    canvas.add_vertex((350, 200), "socrates_vertex2")
    canvas.add_identity_line((350, 200), (430, 200), "socrates_identity2")
    canvas.add_predicate_text((470, 200), "Mortal", "mortal_pred")
    canvas.add_hook_line((430, 200), (470, 200), "mortal_hook")
    
    # Connect the same individual across cut boundary
    canvas.add_identity_line((180, 200), (350, 200), "identity_bridge")
    
    # Labels
    canvas.add_predicate_text((300, 50), 'Complete EG: (Human "Socrates") ~[ (Mortal "Socrates") ]', "complete_title")
    canvas.add_predicate_text((300, 80), "EGIF: (Human \"Socrates\") ~[ (Mortal \"Socrates\") ]", "egif_display")
    
    # Dau compliance checklist
    canvas.add_predicate_text((50, 300), "Dau Compliance Checklist:", "checklist_title")
    canvas.add_predicate_text((50, 320), "□ Heavy identity lines (4.0w) clearly heavier than cut (1.0w)", "check1")
    canvas.add_predicate_text((50, 340), "□ Vertex spots (3.5r) prominently visible as identity markers", "check2")
    canvas.add_predicate_text((50, 360), "□ Hook lines (1.5w) clearly visible connecting predicates", "check3")
    canvas.add_predicate_text((50, 380), "□ Cut boundary fine-drawn (1.0w) and non-overlapping", "check4")
    
    canvas.render_complete()
    canvas.save_to_file("dau_compliance_complete_eg.png")
    print("   Saved: dau_compliance_complete_eg.png")
    
    app.quit()
    
    print("\n✅ Dau Compliance Diagnostic Complete!")
    print("📋 Generated Files:")
    print("   - dau_compliance_line_widths.png (Heavy vs Fine test)")
    print("   - dau_compliance_vertex_prominence.png (Vertex visibility test)")
    print("   - dau_compliance_complete_eg.png (Complete EG with checklist)")
    print("\n🎯 Next Steps:")
    print("1. Examine the PNG files to identify visual compliance issues")
    print("2. Compare with Dau's conventions for heavy lines vs fine cuts")
    print("3. Fix any rendering problems that prevent proper visual distinction")

if __name__ == "__main__":
    create_dau_compliance_test()
