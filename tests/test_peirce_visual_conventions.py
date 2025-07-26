#!/usr/bin/env python3
"""
Test script for the Peirce Layout Engine with Visual Conventions.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from clif_parser import CLIFParser
from egrf_from_graph import convert_graph_to_egrf
from gui.peirce_layout_engine import PeirceLayoutEngine

def test_peirce_visual_conventions():
    """Test the Peirce Layout Engine with visual conventions applied."""
    
    # Test with simple implication
    clif_text = "(if (Man Socrates) (Mortal Socrates))"
    
    parser = CLIFParser()
    layout_engine = PeirceLayoutEngine(viewport_width=800, viewport_height=600)
    
    print(f"Testing Peirce Visual Conventions")
    print(f"CLIF: {clif_text}")
    print(f"{'='*60}")
    
    try:
        # Parse CLIF to EG-HG
        parse_result = parser.parse(clif_text)
        print(f"✓ CLIF parsed successfully")
        
        # Convert to EGRF
        egrf_doc = convert_graph_to_egrf(parse_result.graph, {})
        print(f"✓ EGRF created with {len(egrf_doc.logical_elements)} elements")
        
        # Test Peirce layout engine with visual conventions
        print(f"\n--- PEIRCE LAYOUT WITH VISUAL CONVENTIONS ---")
        rendering_instructions = layout_engine.calculate_layout(egrf_doc)
        
        print(f"✓ Rendering instructions generated")
        print(f"  Elements: {len(rendering_instructions.get('elements', []))}")
        print(f"  Ligatures: {len(rendering_instructions.get('ligatures', []))}")
        
        # Examine rendering instructions
        print(f"\n--- RENDERING INSTRUCTIONS ---")
        
        # Elements
        for element in rendering_instructions.get('elements', []):
            element_id = element.get('id', 'unknown')
            element_type = element.get('type', 'unknown')
            z_index = element.get('z_index', 0)
            
            if element_type == 'context':
                shape = element.get('shape', {})
                style = element.get('style', {})
                print(f"  {element_id}: {element_type} (z={z_index})")
                print(f"    Shape: {shape.get('type', 'unknown')} at ({shape.get('x', 0)}, {shape.get('y', 0)})")
                print(f"    Size: {shape.get('width', 0)} x {shape.get('height', 0)}")
                print(f"    Style: fill={style.get('fill_color', 'none')}, stroke={style.get('stroke_color', 'none')}")
                print(f"    Line width: {style.get('line_width', 0)}")
                
            elif element_type == 'predicate':
                position = element.get('position', (0, 0))
                size = element.get('size', (0, 0))
                text = element.get('text', 'unknown')
                style = element.get('style', {})
                text_style = element.get('text_style', {})
                print(f"  {element_id}: {element_type} '{text}' (z={z_index})")
                print(f"    Position: {position}, Size: {size}")
                print(f"    Text style: {text_style.get('font_family', 'default')} {text_style.get('font_size', 12)}pt")
                print(f"    Color: {style.get('text_color', 'black')}")
        
        # Ligatures
        for ligature in rendering_instructions.get('ligatures', []):
            ligature_id = ligature.get('id', 'unknown')
            start = ligature.get('start', (0, 0))
            end = ligature.get('end', (0, 0))
            style = ligature.get('style', {})
            z_index = ligature.get('z_index', 0)
            print(f"  {ligature_id}: ligature (z={z_index})")
            print(f"    Line: {start} → {end}")
            print(f"    Style: color={style.get('stroke_color', 'black')}, width={style.get('line_width', 1)}")
        
        # Check Peirce's conventions
        print(f"\n--- PEIRCE'S CONVENTIONS VALIDATION ---")
        
        # Check alternating shading
        context_elements = [e for e in rendering_instructions.get('elements', []) if e.get('type') == 'context']
        for element in context_elements:
            nesting_level = element.get('z_index', 0) // 10  # Approximate nesting level from z_index
            fill_color = element.get('style', {}).get('fill_color', 'unknown')
            expected_even = nesting_level % 2 == 0
            is_white = fill_color == '#FFFFFF'
            is_gray = fill_color == '#E8E8E8'
            
            if (expected_even and is_white) or (not expected_even and is_gray):
                print(f"    ✓ {element.get('id')}: Correct alternating shading (level {nesting_level}, {fill_color})")
            else:
                print(f"    ⚠️  {element.get('id')}: Incorrect shading (level {nesting_level}, {fill_color})")
        
        # Check line weights
        ligatures = rendering_instructions.get('ligatures', [])
        for ligature in ligatures:
            line_width = ligature.get('style', {}).get('line_width', 0)
            if line_width >= 3.0:  # Heavy lines for ligatures
                print(f"    ✓ {ligature.get('id')}: Heavy line for ligature ({line_width})")
            else:
                print(f"    ⚠️  {ligature.get('id')}: Line too thin for ligature ({line_width})")
        
        context_elements = [e for e in rendering_instructions.get('elements', []) if e.get('type') == 'context']
        for element in context_elements:
            line_width = element.get('style', {}).get('line_width', 0)
            if line_width <= 2.0:  # Thin lines for cuts
                print(f"    ✓ {element.get('id')}: Thin line for cut ({line_width})")
            else:
                print(f"    ⚠️  {element.get('id')}: Line too thick for cut ({line_width})")
        
        # Check oval shapes for cuts
        for element in context_elements:
            shape = element.get('shape', {})
            shape_type = shape.get('type', 'unknown')
            corner_radius = shape.get('corner_radius', 0)
            
            if shape_type == 'oval' and corner_radius > 0:
                print(f"    ✓ {element.get('id')}: Proper oval shape for cut")
            elif shape_type == 'rectangle' and corner_radius == 0:
                print(f"    ✓ {element.get('id')}: Proper rectangle for sheet")
            else:
                print(f"    ⚠️  {element.get('id')}: Unexpected shape ({shape_type}, radius={corner_radius})")
                
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_peirce_visual_conventions()

