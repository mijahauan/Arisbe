#!/usr/bin/env python3
"""
Fix Predicate Positioning and Line Connection Issues

This script addresses the critical visual issues identified:
1. Predicate text traversing cut boundaries (violates EG formalism)
2. Inconsistent connection between lines of identity and predicate periphery
3. Lines should connect to predicate text boundaries, not centers

The fix ensures:
- Predicate text never crosses cut boundaries
- Lines connect cleanly to predicate periphery
- Proper spatial relationships per Dau's conventions
"""

import sys
import os
sys.path.append('src')

def analyze_predicate_positioning_issues():
    """Analyze the current predicate positioning problems."""
    
    print("🔍 Analyzing Predicate Positioning Issues")
    print("=" * 50)
    
    issues = [
        {
            'issue': 'Predicate text traverses cut boundaries',
            'violation': 'EG formalism requires predicates to be entirely within their designated areas',
            'fix': 'Adjust predicate positioning to respect cut boundaries with proper margins'
        },
        {
            'issue': 'Lines connect to predicate centers, not periphery',
            'violation': "Dau's conventions show lines connecting to predicate text boundaries",
            'fix': 'Calculate predicate text bounds and connect lines to appropriate edges'
        },
        {
            'issue': 'Inconsistent line-to-predicate connections',
            'violation': 'Lines should have consistent, clean connections to predicate boundaries',
            'fix': 'Implement proper line endpoint calculation based on text dimensions'
        }
    ]
    
    for i, issue in enumerate(issues, 1):
        print(f"{i}. {issue['issue']}")
        print(f"   Violation: {issue['violation']}")
        print(f"   Fix: {issue['fix']}")
        print()

def create_predicate_positioning_fix():
    """Create the comprehensive fix for predicate positioning."""
    
    print("🔧 Creating Predicate Positioning Fix")
    print("-" * 40)
    
    # The fix involves modifying the renderer to:
    # 1. Calculate predicate text bounds
    # 2. Ensure predicates don't cross cut boundaries
    # 3. Connect lines to predicate periphery, not center
    # 4. Add proper margins and spacing
    
    fix_code = '''
    def _calculate_predicate_bounds(self, predicate_name: str, position: Tuple[float, float], 
                                   font_size: int = 12) -> Tuple[float, float, float, float]:
        """Calculate the bounding box of predicate text."""
        # Estimate text dimensions (this should use actual font metrics)
        char_width = font_size * 0.6  # Approximate character width
        char_height = font_size * 1.2  # Approximate character height
        
        text_width = len(predicate_name) * char_width
        text_height = char_height
        
        # Calculate bounds (x1, y1, x2, y2)
        x1 = position[0] - text_width / 2
        y1 = position[1] - text_height / 2
        x2 = position[0] + text_width / 2
        y2 = position[1] + text_height / 2
        
        return (x1, y1, x2, y2)
    
    def _ensure_predicate_within_cut(self, predicate_bounds: Tuple[float, float, float, float],
                                    cut_bounds: Tuple[float, float, float, float],
                                    margin: float = 5.0) -> Tuple[float, float]:
        """Adjust predicate position to ensure it stays within cut boundaries."""
        pred_x1, pred_y1, pred_x2, pred_y2 = predicate_bounds
        cut_x1, cut_y1, cut_x2, cut_y2 = cut_bounds
        
        # Calculate current center
        center_x = (pred_x1 + pred_x2) / 2
        center_y = (pred_y1 + pred_y2) / 2
        
        # Adjust if predicate extends beyond cut boundaries
        if pred_x1 < cut_x1 + margin:
            center_x = cut_x1 + margin + (pred_x2 - pred_x1) / 2
        elif pred_x2 > cut_x2 - margin:
            center_x = cut_x2 - margin - (pred_x2 - pred_x1) / 2
            
        if pred_y1 < cut_y1 + margin:
            center_y = cut_y1 + margin + (pred_y2 - pred_y1) / 2
        elif pred_y2 > cut_y2 - margin:
            center_y = cut_y2 - margin - (pred_y2 - pred_y1) / 2
        
        return (center_x, center_y)
    
    def _calculate_line_connection_point(self, predicate_bounds: Tuple[float, float, float, float],
                                        vertex_position: Tuple[float, float]) -> Tuple[float, float]:
        """Calculate where a line should connect to the predicate boundary."""
        pred_x1, pred_y1, pred_x2, pred_y2 = predicate_bounds
        vertex_x, vertex_y = vertex_position
        
        # Calculate predicate center
        pred_center_x = (pred_x1 + pred_x2) / 2
        pred_center_y = (pred_y1 + pred_y2) / 2
        
        # Calculate direction from vertex to predicate center
        dx = pred_center_x - vertex_x
        dy = pred_center_y - vertex_y
        
        # Find intersection with predicate boundary
        # This is a simplified version - should use proper line-rectangle intersection
        if abs(dx) > abs(dy):
            # Horizontal approach - connect to left or right edge
            if dx > 0:
                return (pred_x1, pred_center_y)  # Left edge
            else:
                return (pred_x2, pred_center_y)  # Right edge
        else:
            # Vertical approach - connect to top or bottom edge
            if dy > 0:
                return (pred_center_x, pred_y1)  # Top edge
            else:
                return (pred_center_x, pred_y2)  # Bottom edge
    '''
    
    print("✅ Predicate positioning fix code generated")
    print("This fix ensures:")
    print("  • Predicate text never crosses cut boundaries")
    print("  • Lines connect to predicate periphery, not center")
    print("  • Proper margins and spacing are maintained")
    print("  • Clean, consistent line-to-predicate connections")
    
    return fix_code

def test_current_vs_fixed_positioning():
    """Test current positioning vs the proposed fix."""
    
    print("\n🧪 Testing Current vs Fixed Positioning")
    print("-" * 45)
    
    # Import current components
    from egif_parser_dau import parse_egif
    from graphviz_layout_engine_v2 import GraphvizLayoutEngine
    from diagram_renderer_dau import DiagramRendererDau, VisualConvention
    from pyside6_canvas import PySide6Canvas
    
    # Test case that shows the positioning issues
    egif = '*x ~[ (Mortal x) ]'
    print(f"Testing: {egif}")
    print("Expected: Vertex outside cut, predicate inside cut, clean line connection")
    
    try:
        # Parse and layout
        graph = parse_egif(egif)
        layout_engine = GraphvizLayoutEngine()
        layout_result = layout_engine.create_layout_from_graph(graph)
        
        # Render current version
        canvas = PySide6Canvas(400, 300, title='Current Positioning')
        renderer = DiagramRendererDau(VisualConvention())
        renderer.render_diagram(canvas, graph, layout_result)
        canvas.save_to_file('current_positioning.png')
        
        print("✅ Current positioning rendered: current_positioning.png")
        print("   Check this file for:")
        print("   - Does predicate text cross cut boundary?")
        print("   - Does line connect to predicate center or edge?")
        print("   - Is there proper spacing and margins?")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Predicate Positioning and Line Connection Fix")
    print("=" * 50)
    
    # Analyze the issues
    analyze_predicate_positioning_issues()
    
    # Create the fix
    fix_code = create_predicate_positioning_fix()
    
    # Test current behavior
    test_current_vs_fixed_positioning()
    
    print("\n🎯 Next Steps:")
    print("1. Apply the positioning fix to diagram_renderer_dau.py")
    print("2. Test with various EGIF expressions")
    print("3. Validate that predicate text never crosses cut boundaries")
    print("4. Confirm lines connect cleanly to predicate periphery")
    print("5. Ensure proper visual discrimination per Dau's conventions")
