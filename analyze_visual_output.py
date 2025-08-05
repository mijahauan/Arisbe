#!/usr/bin/env python3
"""
Analyze Visual Output

This script systematically analyzes the generated PNG files to identify
remaining visual problems in the EG diagram rendering.
"""

import sys
import os
from pathlib import Path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def analyze_visual_output():
    """Analyze the generated PNG files for remaining visual issues."""
    
    print("🔍 Analyzing Generated Visual Output")
    print("=" * 45)
    print("Examining PNG files for remaining layout and visual issues...")
    print()
    
    # Find all sample PNG files
    png_files = list(Path('.').glob('sample_*.png'))
    png_files.sort()
    
    if not png_files:
        print("❌ No sample PNG files found. Run generate_sample_egif_visuals.py first.")
        return
    
    print(f"Found {len(png_files)} PNG files to analyze:")
    for png_file in png_files:
        print(f"  • {png_file}")
    print()
    
    # Analyze each PNG file by recreating its layout data
    try:
        from egif_parser_dau import parse_egif
        from graphviz_layout_engine_v2 import GraphvizLayoutEngine
        
        layout_engine = GraphvizLayoutEngine()
        
        # Test cases corresponding to the PNG files
        test_cases = [
            ('sample_01_simple_constant.png', '(Human "Socrates")'),
            ('sample_02_variable_predicate.png', '*x (Human x)'),
            ('sample_03_simple_cut.png', '*x ~[ (Mortal x) ]'),
            ('sample_04_sibling_cuts.png', '*x ~[ (Human x) ] ~[ (Mortal x) ]'),
            ('sample_05_nested_cuts.png', '*x ~[ ~[ (Mortal x) ] ]'),
            ('sample_06_binary_relation.png', '*x *y (Loves x y)'),
            ('sample_07_mixed_constants_variables.png', '*x (Loves "Socrates" x)'),
            ('sample_08_complex_expression.png', '*x (Human x) ~[ (Mortal x) (Wise x) ]'),
        ]
        
        issues_found = []
        
        for png_file, egif in test_cases:
            if not Path(png_file).exists():
                continue
                
            print(f"📊 Analyzing: {png_file}")
            print(f"   EGIF: {egif}")
            
            try:
                # Parse and layout
                graph = parse_egif(egif)
                layout_result = layout_engine.create_layout_from_graph(graph)
                
                # Analyze layout for potential issues
                layout_issues = analyze_layout_issues(layout_result, egif)
                
                if layout_issues:
                    print(f"   ❌ Issues found:")
                    for issue in layout_issues:
                        print(f"      • {issue}")
                        issues_found.append(f"{png_file}: {issue}")
                else:
                    print(f"   ✅ No obvious layout issues detected")
                
            except Exception as e:
                print(f"   ❌ Error analyzing: {e}")
                issues_found.append(f"{png_file}: Analysis error - {e}")
            
            print()
        
        # Summary
        print("🎯 Visual Analysis Summary")
        print("-" * 30)
        if issues_found:
            print(f"❌ Found {len(issues_found)} potential issues:")
            for issue in issues_found:
                print(f"  • {issue}")
        else:
            print("✅ No obvious layout issues detected in analysis")
        
        print("\n📋 Manual Visual Inspection Checklist:")
        print("For each PNG file, manually verify:")
        print("  □ Predicate text is fully within cut boundaries")
        print("  □ Cuts do not overlap other cuts")
        print("  □ Adequate spacing between all elements")
        print("  □ Lines of identity are visually distinct from cut lines")
        print("  □ No text overlapping or crossing boundaries inappropriately")
        print("  □ Professional visual appearance")
        
        return len(issues_found) == 0
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False

def analyze_layout_issues(layout_result, egif: str) -> list:
    """Analyze a layout result for potential visual issues."""
    
    issues = []
    
    # Get all elements by type
    cuts = [(k, v) for k, v in layout_result.primitives.items() if v.element_type == 'cut']
    predicates = [(k, v) for k, v in layout_result.primitives.items() if v.element_type == 'predicate']
    vertices = [(k, v) for k, v in layout_result.primitives.items() if v.element_type == 'vertex']
    
    # Check for overlapping cuts
    if len(cuts) >= 2:
        for i, (cut1_id, cut1) in enumerate(cuts):
            for j, (cut2_id, cut2) in enumerate(cuts[i+1:], i+1):
                if cuts_overlap(cut1.bounds, cut2.bounds):
                    issues.append(f"Cuts {cut1_id[:8]} and {cut2_id[:8]} overlap")
    
    # Check for predicates outside their designated areas
    for cut_id, cut in cuts:
        cut_bounds = cut.bounds
        for pred_id, pred in predicates:
            pred_bounds = pred.bounds
            if not is_fully_contained(pred_bounds, cut_bounds):
                # Check if this predicate should be in this cut
                # This is a simplified check - would need EGI area info for full accuracy
                if pred_bounds and cut_bounds:
                    if bounds_intersect(pred_bounds, cut_bounds):
                        issues.append(f"Predicate {pred_id[:8]} partially outside cut {cut_id[:8]}")
    
    # Check for very small spacing
    all_elements = list(layout_result.primitives.values())
    for i, elem1 in enumerate(all_elements):
        for elem2 in all_elements[i+1:]:
            if elem1.bounds and elem2.bounds:
                distance = calculate_distance(elem1.bounds, elem2.bounds)
                if distance < 10:  # Very close elements
                    issues.append(f"Elements too close (distance: {distance:.1f})")
                    break  # Don't spam with too many close element warnings
    
    return issues

def cuts_overlap(bounds1, bounds2) -> bool:
    """Check if two cut boundaries overlap."""
    if not bounds1 or not bounds2:
        return False
    
    x1_min, y1_min, x1_max, y1_max = bounds1
    x2_min, y2_min, x2_max, y2_max = bounds2
    
    # Check for overlap
    return not (x1_max < x2_min or x2_max < x1_min or y1_max < y2_min or y2_max < y1_min)

def is_fully_contained(inner_bounds, outer_bounds) -> bool:
    """Check if inner bounds are fully contained within outer bounds."""
    if not inner_bounds or not outer_bounds:
        return True  # Can't determine, assume OK
    
    ix_min, iy_min, ix_max, iy_max = inner_bounds
    ox_min, oy_min, ox_max, oy_max = outer_bounds
    
    return (ix_min >= ox_min and iy_min >= oy_min and 
            ix_max <= ox_max and iy_max <= oy_max)

def bounds_intersect(bounds1, bounds2) -> bool:
    """Check if two bounds intersect."""
    if not bounds1 or not bounds2:
        return False
    
    x1_min, y1_min, x1_max, y1_max = bounds1
    x2_min, y2_min, x2_max, y2_max = bounds2
    
    return not (x1_max < x2_min or x2_max < x1_min or y1_max < y2_min or y2_max < y1_min)

def calculate_distance(bounds1, bounds2) -> float:
    """Calculate minimum distance between two bounds."""
    if not bounds1 or not bounds2:
        return float('inf')
    
    x1_min, y1_min, x1_max, y1_max = bounds1
    x2_min, y2_min, x2_max, y2_max = bounds2
    
    # Calculate center points
    x1_center = (x1_min + x1_max) / 2
    y1_center = (y1_min + y1_max) / 2
    x2_center = (x2_min + x2_max) / 2
    y2_center = (y2_min + y2_max) / 2
    
    # Euclidean distance between centers
    return ((x1_center - x2_center) ** 2 + (y1_center - y2_center) ** 2) ** 0.5

if __name__ == "__main__":
    print("Arisbe Visual Output Analyzer")
    print("Examining generated PNG files for remaining issues...")
    print()
    
    success = analyze_visual_output()
    
    if success:
        print("\n✅ Analysis complete - no obvious issues detected")
        print("Manual visual inspection still recommended")
    else:
        print("\n❌ Analysis found potential issues")
        print("Manual visual inspection and fixes required")
