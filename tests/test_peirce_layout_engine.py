#!/usr/bin/env python3
"""
Test script for the Peirce Convention-Aware Layout Engine.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from clif_parser import CLIFParser
from egrf_from_graph import convert_graph_to_egrf
from gui.peirce_layout_engine import PeirceLayoutEngine

def test_peirce_layout_engine():
    """Test the Peirce Layout Engine with corpus examples."""
    
    # Test examples
    examples = [
        ("Simple implication", "(if (Man Socrates) (Mortal Socrates))"),
        ("Existential", "(exists (x) (and (P x) (Q x)))"),
        ("Existential with negation", "(exists (x) (and (P x) (not (Q x))))"),
    ]
    
    parser = CLIFParser()
    layout_engine = PeirceLayoutEngine(viewport_width=800, viewport_height=600)
    
    for name, clif_text in examples:
        print(f"\n{'='*60}")
        print(f"TESTING: {name}")
        print(f"CLIF: {clif_text}")
        print(f"{'='*60}")
        
        try:
            # Parse CLIF to EG-HG
            parse_result = parser.parse(clif_text)
            print(f"✓ CLIF parsed successfully")
            
            # Convert to EGRF
            egrf_doc = convert_graph_to_egrf(parse_result.graph, {})
            print(f"✓ EGRF created with {len(egrf_doc.logical_elements)} elements")
            
            # Print EGRF structure for debugging
            print(f"\n--- EGRF STRUCTURE ---")
            for element_data in egrf_doc.logical_elements:
                element_id = element_data.id
                logical_type = element_data.logical_type
                nesting_level = getattr(element_data, 'containment_level', 0)
                parent = getattr(element_data, 'parent_container', None)
                name = element_data.properties.get('name', 'unnamed')
                print(f"  {element_id}: {logical_type}, level={nesting_level}, parent={parent}, name='{name}'")
            
            # Test Peirce layout engine
            print(f"\n--- PEIRCE LAYOUT ENGINE ---")
            layout_result = layout_engine.calculate_layout(egrf_doc)
            print(f"✓ Peirce layout calculated for {len(layout_result)} elements")
            
            # Examine layout results
            for element_id, data in layout_result.items():
                pos = data.get('position', (0, 0))
                size = data.get('size', (0, 0))
                element_type = data.get('type', 'unknown')
                nesting_level = data.get('nesting_level', 0)
                visual_style = data.get('visual_style', {})
                
                print(f"  {element_id}: {element_type} at {pos}, size {size}, level {nesting_level}")
                
                # Check visual style
                if visual_style:
                    fill_color = visual_style.get('fill_color', 'none')
                    line_width = visual_style.get('line_width', 1.0)
                    print(f"    Style: fill={fill_color}, line_width={line_width}")
                
                # Check for line segments
                if 'line_segments' in data and data['line_segments']:
                    print(f"    Line segments: {len(data['line_segments'])}")
                    for i, segment in enumerate(data['line_segments']):
                        start = segment.get('start', (0, 0))
                        end = segment.get('end', (0, 0))
                        style = segment.get('style', {})
                        print(f"      Segment {i}: {start} → {end}, style={style}")
                
                # Validate coordinates
                x, y = pos
                w, h = size
                if x < 0 or y < 0:
                    print(f"    ⚠️  NEGATIVE COORDINATES: {pos}")
                if x > 1000 or y > 1000:
                    print(f"    ⚠️  LARGE COORDINATES: {pos}")
                if w > 500 or h > 500:
                    print(f"    ⚠️  LARGE SIZE: {size}")
                if w <= 0 or h <= 0:
                    print(f"    ⚠️  INVALID SIZE: {size}")
            
            # Check containment relationships
            print(f"\n--- CONTAINMENT VALIDATION ---")
            for element_id, data in layout_result.items():
                parent_id = data.get('parent_id')
                if parent_id and parent_id in layout_result:
                    parent_data = layout_result[parent_id]
                    
                    # Check if element is within parent bounds
                    elem_x, elem_y = data['position']
                    elem_w, elem_h = data['size']
                    parent_x, parent_y = parent_data['position']
                    parent_w, parent_h = parent_data['size']
                    
                    if (elem_x < parent_x or elem_y < parent_y or
                        elem_x + elem_w > parent_x + parent_w or
                        elem_y + elem_h > parent_y + parent_h):
                        print(f"    ⚠️  {element_id} NOT CONTAINED in {parent_id}")
                        print(f"      Element: ({elem_x}, {elem_y}) + ({elem_w}, {elem_h})")
                        print(f"      Parent:  ({parent_x}, {parent_y}) + ({parent_w}, {parent_h})")
                    else:
                        print(f"    ✓ {element_id} properly contained in {parent_id}")
            
            # Check for overlapping elements at same level
            print(f"\n--- OVERLAP VALIDATION ---")
            elements_by_level = {}
            for element_id, data in layout_result.items():
                level = data.get('nesting_level', 0)
                if level not in elements_by_level:
                    elements_by_level[level] = []
                elements_by_level[level].append((element_id, data))
            
            for level, elements in elements_by_level.items():
                if len(elements) > 1:
                    print(f"    Checking level {level} with {len(elements)} elements:")
                    for i, (id1, data1) in enumerate(elements):
                        for j, (id2, data2) in enumerate(elements[i+1:], i+1):
                            # Check for overlap
                            x1, y1 = data1['position']
                            w1, h1 = data1['size']
                            x2, y2 = data2['position']
                            w2, h2 = data2['size']
                            
                            if (x1 < x2 + w2 and x1 + w1 > x2 and
                                y1 < y2 + h2 and y1 + h1 > y2):
                                print(f"      ⚠️  OVERLAP: {id1} and {id2}")
                            else:
                                print(f"      ✓ No overlap: {id1} and {id2}")
                                
        except Exception as e:
            print(f"✗ Failed to process {name}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_peirce_layout_engine()

