#!/usr/bin/env python3
"""
Visual Validation of Position Correction System

This script generates visual outputs to validate that the Position Correction System
is properly addressing spatial primitive positioning issues and improving diagram quality.
"""

import sys
import os

# Add src directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, '..', 'src')
sys.path.insert(0, src_dir)

from egif_parser_dau import EGIFParser
from graphviz_layout_engine_v2 import GraphvizLayoutEngine
from dau_position_corrector import apply_dau_position_corrections
from diagram_renderer_dau import DiagramRendererDau
from pipeline_contracts import validate_layout_result
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def create_visual_comparison(egif_text: str, title: str, output_prefix: str):
    """Create before/after visual comparison of position corrections."""
    
    print(f"\n🎨 Creating visual comparison: {title}")
    print(f"   EGIF: {egif_text}")
    
    try:
        # Parse EGIF
        parser = EGIFParser(egif_text)
        egi = parser.parse()
        
        # Generate initial layout
        layout_engine = GraphvizLayoutEngine(mode="default-nopp")
        original_layout = layout_engine.create_layout_from_graph(egi)
        validate_layout_result(original_layout)
        
        # Apply position corrections
        corrected_layout = apply_dau_position_corrections(original_layout, egi)
        validate_layout_result(corrected_layout)
        
        # Create side-by-side comparison
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Plot original layout
        plot_layout(ax1, original_layout, "Original Layout (Graphviz)")
        
        # Plot corrected layout
        plot_layout(ax2, corrected_layout, "Corrected Layout (Dau Position Corrector)")
        
        plt.suptitle(f"{title}\nEGIF: {egif_text}", fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        # Save comparison
        output_file = f"output/{output_prefix}_comparison.png"
        os.makedirs("output", exist_ok=True)
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"   ✅ Visual comparison saved: {output_file}")
        
        # Generate position analysis
        analyze_position_changes(original_layout, corrected_layout, title)
        
        plt.close()
        
    except Exception as e:
        print(f"   ❌ Visual comparison failed: {e}")

def plot_layout(ax, layout_result, title):
    """Plot a layout result with proper element visualization."""
    
    ax.set_title(title, fontweight='bold')
    ax.set_aspect('equal')
    
    # Get canvas bounds
    x1, y1, x2, y2 = layout_result.canvas_bounds
    ax.set_xlim(x1 - 20, x2 + 20)
    ax.set_ylim(y1 - 20, y2 + 20)
    
    # Plot elements by type
    for element_id, primitive in layout_result.primitives.items():
        x, y = primitive.position
        
        if primitive.element_type == 'vertex':
            # Vertex as filled circle (identity spot)
            ax.plot(x, y, 'ko', markersize=8, markerfacecolor='black')
            ax.text(x + 5, y + 5, f"v", fontsize=8, color='blue')
            
        elif primitive.element_type == 'predicate':
            # Predicate as text with bounding box
            bbox_x1, bbox_y1, bbox_x2, bbox_y2 = primitive.bounds
            width = bbox_x2 - bbox_x1
            height = bbox_y2 - bbox_y1
            
            # Draw bounding rectangle
            rect = patches.Rectangle((bbox_x1, bbox_y1), width, height, 
                                   linewidth=1, edgecolor='red', facecolor='lightcoral', alpha=0.3)
            ax.add_patch(rect)
            
            # Add predicate label
            ax.text(x, y, f"P", fontsize=10, ha='center', va='center', fontweight='bold')
            
        elif primitive.element_type == 'cut':
            # Cut as oval
            bbox_x1, bbox_y1, bbox_x2, bbox_y2 = primitive.bounds
            width = bbox_x2 - bbox_x1
            height = bbox_y2 - bbox_y1
            
            # Draw oval
            ellipse = patches.Ellipse((x, y), width, height, 
                                    linewidth=2, edgecolor='green', facecolor='none')
            ax.add_patch(ellipse)
            
        elif primitive.element_type == 'edge':
            # Edge as line with hooks
            if primitive.curve_points and len(primitive.curve_points) >= 2:
                xs = [pt[0] for pt in primitive.curve_points]
                ys = [pt[1] for pt in primitive.curve_points]
                ax.plot(xs, ys, 'b-', linewidth=3, alpha=0.7)
                
                # Mark endpoints
                ax.plot(xs[0], ys[0], 'bo', markersize=4)
                ax.plot(xs[-1], ys[-1], 'bo', markersize=4)
    
    ax.grid(True, alpha=0.3)
    ax.set_xlabel('X coordinate')
    ax.set_ylabel('Y coordinate')

def analyze_position_changes(original_layout, corrected_layout, title):
    """Analyze and report position changes between layouts."""
    
    print(f"\n📊 Position Analysis for {title}:")
    
    changes_detected = False
    
    for element_id in original_layout.primitives:
        if element_id in corrected_layout.primitives:
            orig_pos = original_layout.primitives[element_id].position
            corr_pos = corrected_layout.primitives[element_id].position
            
            # Calculate position change
            dx = corr_pos[0] - orig_pos[0]
            dy = corr_pos[1] - orig_pos[1]
            distance = (dx**2 + dy**2)**0.5
            
            if distance > 0.1:  # Threshold for significant change
                element_type = original_layout.primitives[element_id].element_type
                print(f"   📍 {element_id} ({element_type}): moved {distance:.1f} units")
                print(f"      From: ({orig_pos[0]:.1f}, {orig_pos[1]:.1f})")
                print(f"      To:   ({corr_pos[0]:.1f}, {corr_pos[1]:.1f})")
                changes_detected = True
    
    if not changes_detected:
        print("   ✅ No significant position changes detected (positions already optimal)")

def main():
    """Generate visual validations for key test cases."""
    
    print("🎨 Visual Validation of Position Correction System")
    print("=" * 60)
    
    # Test cases that should show positioning improvements
    test_cases = [
        {
            'egif': '(Human "Socrates")',
            'title': 'Simple Predicate',
            'prefix': 'simple_predicate'
        },
        {
            'egif': '~[ (Mortal "Socrates") ]',
            'title': 'Cut with Predicate',
            'prefix': 'cut_predicate'
        },
        {
            'egif': '(Human "Socrates") ~[ (Mortal "Socrates") ]',
            'title': 'Shared Constant (Problematic Case)',
            'prefix': 'shared_constant'
        },
        {
            'egif': '*x (Human x) ~[ (Mortal x) ]',
            'title': 'Quantified Variable',
            'prefix': 'quantified_variable'
        },
        {
            'egif': '*x ~[ (P x) ~[ (Q x) ] ]',
            'title': 'Complex Nesting',
            'prefix': 'complex_nesting'
        }
    ]
    
    for test_case in test_cases:
        create_visual_comparison(
            test_case['egif'], 
            test_case['title'], 
            test_case['prefix']
        )
    
    print(f"\n✅ Visual validation complete!")
    print("📁 Check the 'output/' directory for generated comparison images")
    print("=" * 60)

if __name__ == '__main__':
    main()
