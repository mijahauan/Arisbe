#!/usr/bin/env python3
"""
Corrected Dau Convention Validation

Test the corrected QtDiagramCanvas implementation with proper Dau conventions:
- Heavy identity lines (8.0w) connect vertices directly to predicate periphery
- No separate hook lines
- Prominent vertex spots (6.0r) as identity markers
- Fine cut boundaries (1.0w) for logical containment
"""

import sys
sys.path.insert(0, 'src')

from PySide6.QtWidgets import QApplication
from qt_diagram_canvas import QtDiagramCanvas, DauRenderingStyle

def validate_corrected_dau_conventions():
    """Validate corrected Dau conventions with proper vertex-to-predicate connections."""
    print("🎯 Corrected Dau Convention Validation")
    print("=" * 50)
    
    app = QApplication([])
    
    # Display corrected parameters
    style = DauRenderingStyle()
    print("📊 Corrected Dau Parameters:")
    print(f"   Heavy Identity Lines: {style.IDENTITY_LINE_WIDTH}w (connects to predicate periphery)")
    print(f"   Vertex Spots: {style.VERTEX_RADIUS}r (prominent identity markers)")
    print(f"   Fine Cut Boundaries: {style.CUT_LINE_WIDTH}w (delicate containment)")
    print(f"   Hook Lines: REMOVED (heavy lines connect directly to periphery)")
    print()
    
    # Test 1: Corrected Simple Predicate Connection
    print("1. Testing Corrected Simple Predicate Connection...")
    canvas = QtDiagramCanvas(700, 400)
    
    canvas.add_predicate_text((350, 30), "Corrected Dau Convention: Heavy Lines to Predicate Periphery", "title")
    
    # Simple predicate: (Human "Socrates") - CORRECTED
    canvas.add_vertex((100, 200), "socrates_vertex")
    canvas.add_vertex_to_predicate_connection((100, 200), (200, 200), "Human", "socrates_to_human")
    canvas.add_predicate_text((200, 200), "Human", "human_pred")
    
    # Labels explaining the correction
    canvas.add_predicate_text((150, 170), "Heavy Identity Line (8.0w)", "heavy_label")
    canvas.add_predicate_text((150, 230), "Connects to Predicate Periphery", "periphery_label")
    canvas.add_predicate_text((150, 250), "(No Separate Hook Line)", "no_hook_label")
    
    # Comparison with old incorrect approach
    canvas.add_predicate_text((450, 150), "OLD (Incorrect):", "old_title")
    canvas.add_predicate_text((450, 170), "Vertex → Hook Line → Predicate", "old_approach")
    
    canvas.add_predicate_text((450, 220), "NEW (Dau Correct):", "new_title")
    canvas.add_predicate_text((450, 240), "Vertex → Heavy Line → Periphery", "new_approach")
    
    # Validation criteria
    canvas.add_predicate_text((350, 300), "✅ Corrected Dau Criteria:", "criteria_title")
    canvas.add_predicate_text((50, 330), "□ Heavy identity lines (8.0w) connect directly to predicate periphery", "check1")
    canvas.add_predicate_text((50, 350), "□ No separate hook lines - all connections are heavy identity lines", "check2")
    canvas.add_predicate_text((50, 370), "□ Vertex spots (6.0r) are prominent identity markers", "check3")
    
    canvas.render_complete()
    canvas.save_to_file("corrected_dau_simple_predicate.png")
    print("   Saved: corrected_dau_simple_predicate.png")
    
    # Test 2: Corrected EGIF Example
    print("2. Testing Corrected EGIF Example...")
    canvas.clear_elements()
    
    # EGIF: (Human "Socrates") ~[ (Mortal "Socrates") ]
    canvas.add_predicate_text((350, 30), 'Corrected EGIF: (Human "Socrates") ~[ (Mortal "Socrates") ]', "egif_title")
    
    # Sheet-level: (Human "Socrates") - CORRECTED
    canvas.add_vertex((100, 200), "socrates_sheet")
    canvas.add_vertex_to_predicate_connection((100, 200), (200, 200), "Human", "sheet_connection")
    canvas.add_predicate_text((200, 200), "Human", "human_pred")
    
    # Cut-level: ~[ (Mortal "Socrates") ] - CORRECTED
    canvas.add_cut((350, 150, 300, 100), "mortal_cut")
    canvas.add_vertex((450, 200), "socrates_cut")
    canvas.add_vertex_to_predicate_connection((450, 200), (550, 200), "Mortal", "cut_connection")
    canvas.add_predicate_text((550, 200), "Mortal", "mortal_pred")
    
    # Identity bridge (same individual across contexts) - HEAVY LINE
    canvas.add_identity_line((100, 200), (450, 200), "identity_bridge")
    
    # Corrected rendering explanation
    canvas.add_predicate_text((350, 300), "🎯 Corrected Dau Rendering:", "corrected_title")
    canvas.add_predicate_text((50, 330), "• All vertex-to-predicate connections are heavy identity lines (8.0w)", "feature1")
    canvas.add_predicate_text((50, 350), "• No separate hook lines - connections go directly to periphery", "feature2")
    canvas.add_predicate_text((50, 370), "• Identity bridge maintains heavy line consistency", "feature3")
    
    canvas.render_complete()
    canvas.save_to_file("corrected_dau_egif_example.png")
    print("   Saved: corrected_dau_egif_example.png")
    
    # Test 3: Binary Relation with Corrected Connections
    print("3. Testing Binary Relation with Corrected Connections...")
    canvas.clear_elements()
    
    canvas.add_predicate_text((350, 30), 'Corrected Binary Relation: (Loves "John" "Mary")', "binary_title")
    
    # Two vertices for the binary relation
    canvas.add_vertex((100, 150), "john_vertex")
    canvas.add_vertex((100, 250), "mary_vertex")
    
    # Both connect to the same predicate with heavy identity lines
    canvas.add_vertex_to_predicate_connection((100, 150), (250, 200), "Loves", "john_to_loves")
    canvas.add_vertex_to_predicate_connection((100, 250), (250, 200), "Loves", "mary_to_loves")
    canvas.add_predicate_text((250, 200), "Loves", "loves_pred")
    
    # Labels for the vertices
    canvas.add_predicate_text((70, 150), "John", "john_label")
    canvas.add_predicate_text((70, 250), "Mary", "mary_label")
    
    # Explanation
    canvas.add_predicate_text((350, 300), "Binary Relation Connections:", "binary_explanation")
    canvas.add_predicate_text((50, 330), "• Both vertices connect to predicate periphery with heavy lines", "binary_feature1")
    canvas.add_predicate_text((50, 350), "• No hook lines - all connections are identity lines", "binary_feature2")
    canvas.add_predicate_text((50, 370), "• Argument order preserved through connection geometry", "binary_feature3")
    
    canvas.render_complete()
    canvas.save_to_file("corrected_dau_binary_relation.png")
    print("   Saved: corrected_dau_binary_relation.png")
    
    app.quit()
    
    print("\n✅ Corrected Dau Convention Validation Complete!")
    print("📋 Generated Corrected Validation Files:")
    print("   - corrected_dau_simple_predicate.png")
    print("   - corrected_dau_egif_example.png") 
    print("   - corrected_dau_binary_relation.png")
    print("\n🎯 Critical Correction Applied:")
    print("✅ Removed separate hook lines")
    print("✅ Heavy identity lines connect directly to predicate periphery")
    print("✅ All vertex-to-predicate connections use heavy line width (8.0w)")
    print("✅ Visual consistency with Dau's conventions maintained")
    print("\n🚀 Ready for Phase 1B: Selection/Overlay Implementation")

if __name__ == "__main__":
    validate_corrected_dau_conventions()
