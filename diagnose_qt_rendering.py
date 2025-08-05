#!/usr/bin/env python3
"""
QtDiagramCanvas Rendering Diagnostic

Analyze the actual rendering output to identify Dau compliance issues.
This will help us understand what's wrong with the current implementation.
"""

import sys
import os
sys.path.insert(0, 'src')

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PySide6.QtCore import Qt
from qt_diagram_canvas import QtDiagramCanvas, DauRenderingStyle

def analyze_rendering_style():
    """Analyze the current rendering style settings."""
    print("🔍 Current DauRenderingStyle Settings:")
    print("=" * 40)
    
    style = DauRenderingStyle()
    
    print(f"Heavy Identity Lines:")
    print(f"  Width: {style.IDENTITY_LINE_WIDTH} (should be 4.0)")
    print(f"  Color: {style.IDENTITY_LINE_COLOR}")
    
    print(f"\nFine Cut Boundaries:")
    print(f"  Width: {style.CUT_LINE_WIDTH} (should be 1.0)")
    print(f"  Color: {style.CUT_LINE_COLOR}")
    
    print(f"\nVertex Spots:")
    print(f"  Radius: {style.VERTEX_RADIUS} (should be 3.5)")
    print(f"  Color: {style.VERTEX_COLOR}")
    
    print(f"\nHook Lines:")
    print(f"  Width: {style.HOOK_LINE_WIDTH} (should be 1.5)")
    print(f"  Color: {style.HOOK_LINE_COLOR}")
    
    print(f"\nPredicate Text:")
    print(f"  Font: {style.PREDICATE_FONT_FAMILY}, {style.PREDICATE_FONT_SIZE}pt")
    print(f"  Color: {style.PREDICATE_TEXT_COLOR}")

def test_individual_elements():
    """Test rendering of individual elements to identify issues."""
    print("\n🎨 Testing Individual Element Rendering:")
    print("=" * 40)
    
    app = QApplication([])
    
    # Test 1: Heavy identity line vs fine cut comparison
    print("\n1. Heavy Identity Line vs Fine Cut Comparison:")
    canvas = QtDiagramCanvas(400, 200)
    
    # Heavy identity line (should be 4.0 width)
    canvas.add_identity_line((50, 50), (150, 50), "heavy_line")
    
    # Fine cut boundary (should be 1.0 width) 
    canvas.add_cut((50, 100, 100, 50), "fine_cut")
    
    # Reference lines for comparison
    canvas.add_element({
        "element_type": "line",
        "element_id": "ref_1",
        "coordinates": [(50, 150), (150, 150)],
        "style_override": {"line_width": 1.0}
    })
    
    canvas.add_element({
        "element_type": "line", 
        "element_id": "ref_4",
        "coordinates": [(200, 50), (300, 50)],
        "style_override": {"line_width": 4.0}
    })
    
    canvas.add_predicate_text((100, 25), "Heavy Identity (4.0)", "label1")
    canvas.add_predicate_text((100, 125), "Fine Cut (1.0)", "label2")
    canvas.add_predicate_text((100, 175), "Reference 1.0", "label3")
    canvas.add_predicate_text((250, 25), "Reference 4.0", "label4")
    
    canvas.render_complete()
    canvas.save_to_file("diagnostic_line_widths.png")
    print("  Saved: diagnostic_line_widths.png")
    
    # Test 2: Vertex spot sizes
    print("\n2. Vertex Spot Size Progression:")
    canvas.clear_elements()
    
    radii = [1.0, 2.0, 3.0, 3.5, 4.0]
    for i, radius in enumerate(radii):
        x = 50 + i * 60
        canvas.add_element({
            "element_type": "vertex",
            "element_id": f"vertex_{i}",
            "coordinates": [(x, 100)],
            "style_override": {"vertex_radius": radius}
        })
        canvas.add_predicate_text((x, 130), f"{radius}r", f"label_{i}")
    
    canvas.add_predicate_text((150, 50), "Vertex Radius Progression (Dau = 3.5)", "title")
    canvas.render_complete()
    canvas.save_to_file("diagnostic_vertex_sizes.png")
    print("  Saved: diagnostic_vertex_sizes.png")
    
    # Test 3: Complete EG element rendering
    print("\n3. Complete EG Element Test:")
    canvas.clear_elements()
    
    # Simple predicate with all elements
    canvas.add_vertex((100, 100), "vertex1")
    canvas.add_identity_line((100, 100), (180, 100), "identity1")
    canvas.add_predicate_text((220, 100), "Human", "pred1")
    canvas.add_hook_line((180, 100), (220, 100), "hook1")
    
    # Add labels showing expected vs actual
    canvas.add_predicate_text((160, 50), "Complete EG: (Human \"Socrates\")", "title")
    canvas.add_predicate_text((50, 130), "Vertex: 3.5r", "v_label")
    canvas.add_predicate_text((140, 130), "Identity: 4.0w", "i_label")
    canvas.add_predicate_text((200, 130), "Hook: 1.5w", "h_label")
    
    canvas.render_complete()
    canvas.save_to_file("diagnostic_complete_eg.png")
    print("  Saved: diagnostic_complete_eg.png")
    
    app.quit()
    print("\n✅ Diagnostic images saved. Check:")
    print("  - diagnostic_line_widths.png")
    print("  - diagnostic_vertex_sizes.png") 
    print("  - diagnostic_complete_eg.png")

def identify_common_issues():
    """Identify common Dau compliance issues."""
    print("\n🚨 Common Dau Compliance Issues to Check:")
    print("=" * 40)
    print("1. HEAVY LINES NOT HEAVY ENOUGH:")
    print("   - Identity lines should be 4x thicker than cuts")
    print("   - Should be visually prominent, not thin")
    
    print("\n2. CUTS NOT FINE ENOUGH:")
    print("   - Cut boundaries should be 1.0 width (fine-drawn)")
    print("   - Should appear delicate compared to identity lines")
    
    print("\n3. VERTEX SPOTS TOO SMALL:")
    print("   - Should be 3.5 radius (prominent identity markers)")
    print("   - Must be clearly visible as identity spots")
    
    print("\n4. HOOK LINES INVISIBLE:")
    print("   - Should be 1.5 width (enhanced for visibility)")
    print("   - Must connect predicates to identity lines clearly")
    
    print("\n5. RENDERING QUALITY ISSUES:")
    print("   - Anti-aliasing may be missing")
    print("   - Elements may not be rendering at all")
    print("   - Coordinate mapping may be incorrect")
    
    print("\n6. MISSING ELEMENTS:")
    print("   - Some element types may not be implemented")
    print("   - Style overrides may not be working")
    print("   - Element positioning may be wrong")

def main():
    """Run the diagnostic analysis."""
    print("🔍 QtDiagramCanvas Rendering Diagnostic")
    print("=" * 50)
    print("Analyzing Dau compliance issues in current rendering...")
    
    analyze_rendering_style()
    test_individual_elements()
    identify_common_issues()
    
    print("\n🎯 Next Steps:")
    print("1. Examine the diagnostic PNG files")
    print("2. Compare with Dau's visual conventions")
    print("3. Fix identified rendering issues")
    print("4. Re-test with validation suite")

if __name__ == "__main__":
    main()
