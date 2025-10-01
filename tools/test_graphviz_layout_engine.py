#!/usr/bin/env python3
"""
Test script for Graphviz Layout Engine

Tests the three-stage pipeline:
1. Hierarchical Layout (Graphviz)
2. Ligature Routing (A* pathfinding)  
3. DTO Assembly
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from graphviz_layout_engine import GraphvizLayoutEngine
from graphviz_svg_renderer import GraphvizSVGRenderer
from egif_parser_dau import parse_egif


def test_graphviz_layout_engine():
    """Test the Graphviz-based layout engine"""
    
    print("🚀 TESTING GRAPHVIZ LAYOUT ENGINE")
    print("=" * 60)
    
    # Initialize engines
    layout_engine = GraphvizLayoutEngine()
    svg_renderer = GraphvizSVGRenderer()
    
    # Test cases
    test_cases = [
        {
            'name': 'SimpleBoundary',
            'description': 'Simple case: *x (Human x) ~[ (Mortal x) ]',
            'egif': '*x (Human x) ~[ (Mortal x) ]',
        },
        {
            'name': 'OverlappingText',
            'description': 'Original problematic case',
            'egif': '*x *y (Human x) (Human y) (Friend x y) ~[ (Enemy x y) ]',
        },
        {
            'name': 'NestedCuts',
            'description': 'Nested cuts test',
            'egif': '*x (Human x) ~[ (Mortal x) ~[ (Greek x) ] ]',
        }
    ]
    
    results = []
    
    print(f"\n📚 Testing Graphviz three-stage pipeline")
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
            
            # Generate DOT (Stage 1)
            dot_string = layout_engine._generate_dot(egi)
            print(f"   ✅ DOT generated ({len(dot_string)} chars)")
            
            # Show DOT for debugging
            print(f"   📝 DOT preview:")
            dot_lines = dot_string.split('\n')
            for i, line in enumerate(dot_lines[:10]):
                print(f"      {line}")
            if len(dot_lines) > 10:
                remaining_lines = len(dot_lines) - 10
                print(f"      ... ({remaining_lines} more lines)")
            
            # Generate DTO (Stages 2 & 3)
            dto = layout_engine.generate_layout(egi)
            print(f"   ✅ DTO generated successfully")
            
            # Validate DTO structure
            validation_result = validate_dto(dto, egi, test_case)
            
            # Print DTO details
            print_dto_details(dto)
            
            # Generate SVG
            svg_path = svg_renderer.save_svg(
                dto, 
                f"Graphviz Layout - {test_case['name']}", 
                test_case['egif'],
                f"graphviz_{test_case['name'].lower()}",
                "test_outputs/graphviz_layouts"
            )
            print(f"   📄 SVG saved: {svg_path.name}")
            
            results.append({
                'name': test_case['name'],
                'success': validation_result['success'],
                'issues': validation_result['issues'],
                'dto': dto,
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
                'dto': None
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


def validate_dto(dto, egi, test_case):
    """Validate that DTO structure is correct"""
    issues = []
    
    # Check basic structure
    if not dto.areas:
        issues.append("No areas generated")
    
    if not dto.vertices:
        issues.append("No vertices generated")
    
    if not dto.edge_labels:
        issues.append("No edge labels generated")
    
    # Check vertex count
    expected_vertices = len(egi.V)
    if len(dto.vertices) != expected_vertices:
        issues.append(f"Expected {expected_vertices} vertices, got {len(dto.vertices)}")
    
    # Check edge count
    expected_edges = len(egi.E)
    if len(dto.edge_labels) != expected_edges:
        issues.append(f"Expected {expected_edges} edges, got {len(dto.edge_labels)}")
    
    # Check area count (sheet + cuts)
    expected_areas = 1 + len(egi.Cut)  # sheet + cuts
    if len(dto.areas) != expected_areas:
        issues.append(f"Expected {expected_areas} areas, got {len(dto.areas)}")
    
    # Check for sheet area
    sheet_areas = [area for area in dto.areas if area.is_sheet]
    if len(sheet_areas) != 1:
        issues.append(f"Expected 1 sheet area, got {len(sheet_areas)}")
    
    # Check ligature count
    expected_ligatures = sum(len(vertex_seq) for vertex_seq in egi.nu.values() if vertex_seq)
    if len(dto.ligatures) != expected_ligatures:
        issues.append(f"Expected {expected_ligatures} ligatures, got {len(dto.ligatures)}")
    
    success = len(issues) == 0
    
    if success:
        print("   ✅ DTO validation: PASSED")
    else:
        print("   ❌ DTO validation: FAILED")
        for issue in issues:
            print(f"      • {issue}")
    
    return {'success': success, 'issues': issues}


def print_dto_details(dto):
    """Print detailed DTO structure"""
    
    print(f"   📊 DTO Structure:")
    print(f"      Areas: {len(dto.areas)}")
    print(f"      Vertices: {len(dto.vertices)}")
    print(f"      Edge Labels: {len(dto.edge_labels)}")
    print(f"      Ligatures: {len(dto.ligatures)}")
    
    # Print area hierarchy
    print(f"   🏗️  Area Hierarchy:")
    sheet_areas = [a for a in dto.areas if a.is_sheet]
    cut_areas = [a for a in dto.areas if not a.is_sheet]
    
    for area in sheet_areas:
        print(f"      📄 Sheet {area.id}: {area.rect.width:.1f}x{area.rect.height:.1f} at ({area.rect.x:.1f}, {area.rect.y:.1f})")
    
    for area in cut_areas:
        print(f"      ✂️  Cut {area.id}: {area.rect.width:.1f}x{area.rect.height:.1f} at ({area.rect.x:.1f}, {area.rect.y:.1f})")
    
    # Print element positions
    print(f"   📍 Element Positions:")
    for vertex in dto.vertices:
        print(f"      🔵 Vertex {vertex.id}: ({vertex.pos[0]:.1f}, {vertex.pos[1]:.1f}) in area {vertex.parent_area_id}")
    
    for edge in dto.edge_labels:
        print(f"      🏷️  Edge {edge.id} '{edge.label}': ({edge.rect.x:.1f}, {edge.rect.y:.1f}) in area {edge.parent_area_id}")
    
    # Print ligatures
    print(f"   🔗 Ligatures:")
    for ligature in dto.ligatures:
        if len(ligature.path_points) >= 2:
            start = ligature.path_points[0]
            end = ligature.path_points[-1]
            length = ((end[0] - start[0])**2 + (end[1] - start[1])**2)**0.5
            print(f"      ➡️  {ligature.start_vertex_id} -> {ligature.end_edge_id}: {length:.1f} units ({len(ligature.path_points)} points)")


if __name__ == "__main__":
    success = test_graphviz_layout_engine()
    sys.exit(0 if success else 1)
