#!/usr/bin/env python3
"""
Test script for Abstract Layout Engine

Tests the new ALU-based engine that follows the 4-step process:
1. Build Spatial Hierarchy
2. Bottom-Up Layout Calculation  
3. Ligature Path Routing
4. Absolute Coordinate Finalization
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from abstract_layout_engine import AbstractLayoutEngine
from alu_svg_renderer import ALUSVGRenderer
from style_loader import StyleLoader
from egif_parser_dau import parse_egif


def test_abstract_layout_engine():
    """Test the Abstract Layout Engine with problematic cases"""
    
    print("🚀 TESTING ABSTRACT LAYOUT ENGINE (ALU)")
    print("=" * 60)
    
    # Load style
    try:
        style_loader = StyleLoader()
        style = style_loader.load_style('dau-compliant@1.0')
        print(f"✅ Style loaded: {style.style_name}")
    except Exception as e:
        print(f"❌ Failed to load style: {e}")
        return False
    
    # Initialize engines
    layout_engine = AbstractLayoutEngine(style)
    svg_renderer = ALUSVGRenderer()
    
    # Test cases
    test_cases = [
        {
            'name': 'SimpleBoundary',
            'description': 'Simple case: *x (Human x) ~[ (Mortal x) ]',
            'egif': '*x (Human x) ~[ (Mortal x) ]',
            'expected_areas': 2,  # sheet + 1 cut
            'expected_vertices': 1,  # x
            'expected_edges': 2,  # Human, Mortal
        },
        {
            'name': 'OverlappingText',
            'description': 'Original problematic case',
            'egif': '*x *y (Human x) (Human y) (Friend x y) ~[ (Enemy x y) ]',
            'expected_areas': 2,  # sheet + 1 cut
            'expected_vertices': 2,  # x, y
            'expected_edges': 4,  # Human, Human, Friend, Enemy
        }
    ]
    
    results = []
    
    print(f"\n📚 Testing with style: {style.style_name}")
    print()
    
    for test_case in test_cases:
        print(f"🧪 Testing: {test_case['name']} - {test_case['description']}")
        
        try:
            # Parse EGIF
            egi = parse_egif(test_case['egif'])
            vertex_count = len(egi.V)
            edge_count = len(egi.E) 
            cut_count = len(egi.Cut)
            print(f"   ✅ Parsed: {vertex_count} vertices, {edge_count} edges, {cut_count} cuts")
            
            # Generate ALU
            alu = layout_engine.generate_layout(egi)
            print(f"   ✅ ALU generated successfully")
            
            # Validate ALU structure
            validation_result = validate_alu(alu, egi, test_case)
            
            # Print ALU details
            print_alu_details(alu)
            
            # Generate SVG
            svg_path = svg_renderer.save_svg(
                alu, 
                f"ALU Layout - {test_case['name']}", 
                test_case['egif'],
                f"alu_{test_case['name'].lower()}",
                "test_outputs/alu_layouts"
            )
            print(f"   📄 SVG saved: {svg_path.name}")
            
            results.append({
                'name': test_case['name'],
                'success': validation_result['success'],
                'issues': validation_result['issues'],
                'alu': alu,
                'svg_path': svg_path
            })
            
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                'name': test_case['name'],
                'success': False,
                'issues': [f"Exception: {e}"],
                'alu': None
            })
        
        print()
    
    # Summary
    print("🎯 TEST SUMMARY:")
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    print(f"   Total tests: {total}")
    print(f"   Successful: {successful}")
    print(f"   Failed: {total - successful}")
    print(f"   Success rate: {successful/total*100:.1f}%")
    
    if successful < total:
        print("   ⚠️  Some tests failed - check output for details")
    else:
        print("   🎉 All tests passed!")
    
    return successful == total


def validate_alu(alu, egi, test_case):
    """Validate that ALU structure is correct"""
    issues = []
    
    # Check area count
    expected_areas = test_case['expected_areas']
    if len(alu.areas) != expected_areas:
        issues.append(f"Expected {expected_areas} areas, got {len(alu.areas)}")
    
    # Check vertex count
    expected_vertices = test_case['expected_vertices']
    if len(alu.vertices) != expected_vertices:
        issues.append(f"Expected {expected_vertices} vertices, got {len(alu.vertices)}")
    
    # Check edge count
    expected_edges = test_case['expected_edges']
    if len(alu.edge_labels) != expected_edges:
        issues.append(f"Expected {expected_edges} edges, got {len(alu.edge_labels)}")
    
    # Check for overlapping elements
    vertex_positions = [(v.x, v.y) for v in alu.vertices]
    edge_positions = [(e.x, e.y) for e in alu.edge_labels]
    all_positions = vertex_positions + edge_positions
    
    if len(all_positions) != len(set(all_positions)):
        issues.append("Some elements have identical positions (overlapping)")
    
    # Check that all elements have valid parent areas
    area_ids = {area.id for area in alu.areas}
    for vertex in alu.vertices:
        if vertex.parent_area_id not in area_ids:
            issues.append(f"Vertex {vertex.id} has invalid parent area {vertex.parent_area_id}")
    
    for edge in alu.edge_labels:
        if edge.parent_area_id not in area_ids:
            issues.append(f"Edge {edge.id} has invalid parent area {edge.parent_area_id}")
    
    # Check ligature count
    expected_ligatures = sum(len(vertex_seq) for vertex_seq in egi.nu.values() if vertex_seq)
    if len(alu.ligatures) != expected_ligatures:
        issues.append(f"Expected {expected_ligatures} ligatures, got {len(alu.ligatures)}")
    
    success = len(issues) == 0
    
    if success:
        print("   ✅ ALU validation: PASSED")
    else:
        print("   ❌ ALU validation: FAILED")
        for issue in issues:
            print(f"      • {issue}")
    
    return {'success': success, 'issues': issues}


def print_alu_details(alu):
    """Print detailed ALU structure"""
    
    print(f"   📊 ALU Structure:")
    print(f"      Areas: {len(alu.areas)}")
    print(f"      Vertices: {len(alu.vertices)}")
    print(f"      Edge Labels: {len(alu.edge_labels)}")
    print(f"      Ligatures: {len(alu.ligatures)}")
    print(f"      Total Size: {alu.total_width:.1f} x {alu.total_height:.1f}")
    
    # Print area hierarchy
    print(f"   🏗️  Area Hierarchy:")
    sheet_areas = [a for a in alu.areas if a.type == 'sheet']
    cut_areas = [a for a in alu.areas if a.type == 'cut']
    
    for area in sheet_areas:
        print(f"      📄 Sheet {area.id}: {area.width:.1f}x{area.height:.1f} at ({area.x:.1f}, {area.y:.1f})")
    
    for area in cut_areas:
        print(f"      ✂️  Cut {area.id}: {area.width:.1f}x{area.height:.1f} at ({area.x:.1f}, {area.y:.1f})")
    
    # Print element positions
    print(f"   📍 Element Positions:")
    for vertex in alu.vertices:
        print(f"      🔵 Vertex {vertex.id}: ({vertex.x:.1f}, {vertex.y:.1f}) in area {vertex.parent_area_id}")
    
    for edge in alu.edge_labels:
        print(f"      🏷️  Edge {edge.id} '{edge.text}': ({edge.x:.1f}, {edge.y:.1f}) in area {edge.parent_area_id}")
    
    # Print ligatures
    print(f"   🔗 Ligatures:")
    for ligature in alu.ligatures:
        start = ligature.path[0] if ligature.path else None
        end = ligature.path[-1] if ligature.path else None
        if start and end:
            length = start.distance_to(end)
            print(f"      ➡️  {ligature.start_vertex_id} -> {ligature.end_edge_id}: {length:.1f} units")


if __name__ == "__main__":
    success = test_abstract_layout_engine()
    sys.exit(0 if success else 1)
