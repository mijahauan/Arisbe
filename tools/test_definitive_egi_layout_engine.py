#!/usr/bin/env python3
"""
Test script for Definitive EGI Layout Engine - Three-Step Approach

Tests the definitive three-step process:
1. Unified Force-Directed Layout (neato): Position all content optimally in 2D space
2. Bottom-Up Bounding Box Calculation: Calculate container boundaries around content
3. Area-Aware Ligature Routing (A*): Intelligent pathfinding respecting cut hierarchy
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from definitive_egi_layout_engine import DefinitiveEGILayoutEngine
from graphviz_svg_renderer import GraphvizSVGRenderer
from egif_parser_dau import parse_egif


def test_definitive_egi_layout_engine():
    """Test the definitive EGI layout engine"""
    
    print("🚀 TESTING DEFINITIVE EGI LAYOUT ENGINE - THREE-STEP APPROACH")
    print("=" * 75)
    
    # Initialize engines
    layout_engine = DefinitiveEGILayoutEngine()
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
        },
        {
            'name': 'ComplexConnections',
            'description': 'Multiple vertices with complex connections',
            'egif': '*x *y *z (Human x) (Human y) (Loves x y) (Friend y z) ~[ (Enemy x z) ]',
        },
        {
            'name': 'DeepNesting',
            'description': 'Deep nesting test',
            'egif': '*x (Human x) ~[ (Mortal x) ~[ (Greek x) ~[ (Philosopher x) ] ] ]',
        }
    ]
    
    results = []
    
    print(f"\n📚 Testing definitive pipeline: neato → bottom-up → area-aware A*")
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
            
            # Generate DTO using definitive approach
            dto = layout_engine.generate_layout(egi)
            print(f"   ✅ Definitive layout completed")
            
            # Validate DTO structure
            validation_result = validate_dto(dto, egi, test_case)
            
            # Print DTO details
            print_dto_details(dto)
            
            # Generate SVG
            svg_path = svg_renderer.save_svg(
                dto, 
                f"Definitive EGI Layout - {test_case['name']}", 
                test_case['egif'],
                f"definitive_{test_case['name'].lower()}",
                "test_outputs/definitive_layouts"
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
    
    # Advanced analysis
    if successful > 0:
        print("\n📊 DEFINITIVE LAYOUT QUALITY ANALYSIS:")
        analyze_definitive_layout_quality(results)
    
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
    
    # Check for 2D positioning (not all on same line)
    if dto.vertices:
        y_positions = [v.pos[1] for v in dto.vertices]
        unique_y_positions = len(set(y_positions))
        if unique_y_positions == 1 and len(dto.vertices) > 1:
            issues.append("All vertices positioned on same horizontal line (1D layout)")
        
        # Check for good 2D distribution
        x_positions = [v.pos[0] for v in dto.vertices]
        unique_x_positions = len(set(x_positions))
        
        total_positions = len(dto.vertices)
        if total_positions > 2:
            x_diversity = unique_x_positions / total_positions
            y_diversity = unique_y_positions / total_positions
            
            if x_diversity < 0.5 and y_diversity < 0.5:
                issues.append("Poor 2D space utilization - elements clustered")
    
    # Check vertex positioning optimization
    if len(dto.vertices) >= 2:
        vertex_spacing_quality = analyze_vertex_spacing(dto, egi)
        if vertex_spacing_quality < 0.3:
            issues.append("Vertex positioning appears suboptimal for ligature length")
    
    # Check for proper containment
    containment_issues = check_containment_correctness(dto, egi)
    issues.extend(containment_issues)
    
    success = len(issues) == 0
    
    if success:
        print("   ✅ DTO validation: PASSED")
    else:
        print("   ❌ DTO validation: FAILED")
        for issue in issues:
            print(f"      • {issue}")
    
    return {'success': success, 'issues': issues}


def check_containment_correctness(dto, egi):
    """Check that elements are properly contained within their designated areas"""
    issues = []
    
    # Build area rectangles lookup
    area_rects = {area.id: area.rect for area in dto.areas}
    
    # Check vertex containment
    for vertex in dto.vertices:
        if vertex.parent_area_id in area_rects:
            area_rect = area_rects[vertex.parent_area_id]
            if not (area_rect.x <= vertex.pos[0] <= area_rect.x + area_rect.width and
                   area_rect.y <= vertex.pos[1] <= area_rect.y + area_rect.height):
                issues.append(f"Vertex {vertex.id} outside its designated area {vertex.parent_area_id}")
    
    # Check edge label containment
    for edge_label in dto.edge_labels:
        if edge_label.parent_area_id in area_rects:
            area_rect = area_rects[edge_label.parent_area_id]
            label_center_x = edge_label.rect.x + edge_label.rect.width / 2
            label_center_y = edge_label.rect.y + edge_label.rect.height / 2
            
            if not (area_rect.x <= label_center_x <= area_rect.x + area_rect.width and
                   area_rect.y <= label_center_y <= area_rect.y + area_rect.height):
                issues.append(f"Edge label {edge_label.id} outside its designated area {edge_label.parent_area_id}")
    
    return issues


def analyze_vertex_spacing(dto, egi):
    """Analyze quality of vertex positioning relative to connected edges"""
    
    if len(dto.vertices) < 2:
        return 1.0  # Single vertex is always optimal
    
    total_quality = 0.0
    vertex_count = 0
    
    for vertex in dto.vertices:
        # Find connected edges for this vertex
        connected_edges = []
        for edge_id, vertex_seq in egi.nu.items():
            if vertex.id in [v for v in vertex_seq]:
                # Find the edge label
                for edge_label in dto.edge_labels:
                    if edge_label.id == edge_id:
                        connected_edges.append(edge_label)
                        break
        
        if len(connected_edges) >= 2:
            # Calculate if vertex is reasonably positioned relative to connected edges
            edge_positions = [(e.rect.x + e.rect.width/2, e.rect.y + e.rect.height/2) 
                            for e in connected_edges]
            
            # Calculate centroid of connected edges
            centroid_x = sum(pos[0] for pos in edge_positions) / len(edge_positions)
            centroid_y = sum(pos[1] for pos in edge_positions) / len(edge_positions)
            
            # Calculate distance from vertex to centroid
            vertex_to_centroid = ((vertex.pos[0] - centroid_x)**2 + 
                                (vertex.pos[1] - centroid_y)**2)**0.5
            
            # Calculate average distance from centroid to edges
            avg_edge_distance = sum(((pos[0] - centroid_x)**2 + 
                                   (pos[1] - centroid_y)**2)**0.5 
                                  for pos in edge_positions) / len(edge_positions)
            
            # Quality is better when vertex is closer to centroid
            if avg_edge_distance > 0:
                quality = max(0, 1 - (vertex_to_centroid / avg_edge_distance))
            else:
                quality = 1.0
            
            total_quality += quality
            vertex_count += 1
    
    return total_quality / vertex_count if vertex_count > 0 else 1.0


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
    
    # Print element positions with 2D analysis
    print(f"   📍 Element Positions:")
    
    if dto.vertices:
        y_positions = [v.pos[1] for v in dto.vertices]
        x_positions = [v.pos[0] for v in dto.vertices]
        y_spread = max(y_positions) - min(y_positions) if len(y_positions) > 1 else 0
        x_spread = max(x_positions) - min(x_positions) if len(x_positions) > 1 else 0
        
        print(f"      📏 Vertex spread: X={x_spread:.1f}, Y={y_spread:.1f}")
    
    for vertex in dto.vertices:
        print(f"      🔵 Vertex {vertex.id}: ({vertex.pos[0]:.1f}, {vertex.pos[1]:.1f}) in area {vertex.parent_area_id}")
    
    for edge in dto.edge_labels:
        center_x = edge.rect.x + edge.rect.width/2
        center_y = edge.rect.y + edge.rect.height/2
        print(f"      🏷️  Edge {edge.id} '{edge.label}': ({center_x:.1f}, {center_y:.1f}) in area {edge.parent_area_id}")
    
    # Print ligatures with path analysis
    print(f"   🔗 Ligatures:")
    for ligature in dto.ligatures:
        if len(ligature.path_points) >= 2:
            start = ligature.path_points[0]
            end = ligature.path_points[-1]
            length = ((end[0] - start[0])**2 + (end[1] - start[1])**2)**0.5
            path_complexity = len(ligature.path_points)
            print(f"      ➡️  {ligature.start_vertex_id} -> {ligature.end_edge_id}: {length:.1f} units ({path_complexity} points)")


def analyze_definitive_layout_quality(results):
    """Analyze overall layout quality across all test cases"""
    
    successful_results = [r for r in results if r['success'] and r['dto']]
    
    if not successful_results:
        print("      No successful layouts to analyze")
        return
    
    # Analyze 2D space utilization
    total_2d_score = 0
    total_positioning_score = 0
    
    for result in successful_results:
        dto = result['dto']
        if len(dto.vertices) > 1:
            # Calculate 2D distribution
            y_positions = [v.pos[1] for v in dto.vertices]
            x_positions = [v.pos[0] for v in dto.vertices]
            
            unique_y_count = len(set(y_positions))
            unique_x_count = len(set(x_positions))
            total_vertices = len(dto.vertices)
            
            # Score based on how well 2D space is utilized
            x_diversity = unique_x_count / total_vertices
            y_diversity = unique_y_count / total_vertices
            combined_2d_score = (x_diversity + y_diversity) / 2
            
            total_2d_score += combined_2d_score
            
            # Calculate positioning optimality
            y_spread = max(y_positions) - min(y_positions) if len(y_positions) > 1 else 0
            x_spread = max(x_positions) - min(x_positions) if len(x_positions) > 1 else 0
            
            # Good layouts should have reasonable spread in both dimensions
            positioning_score = min(1.0, (x_spread + y_spread) / 200)  # Normalize to reasonable range
            total_positioning_score += positioning_score
    
    avg_2d_score = total_2d_score / len(successful_results)
    avg_positioning_score = total_positioning_score / len(successful_results)
    
    print(f"      2D Space Utilization: {avg_2d_score*100:.1f}%")
    print(f"      Positioning Optimality: {avg_positioning_score*100:.1f}%")
    
    # Analyze ligature path complexity
    total_path_complexity = 0
    total_ligatures = 0
    for result in successful_results:
        dto = result['dto']
        for ligature in dto.ligatures:
            total_path_complexity += len(ligature.path_points)
            total_ligatures += 1
    
    if total_ligatures > 0:
        avg_path_complexity = total_path_complexity / total_ligatures
        print(f"      Average Ligature Complexity: {avg_path_complexity:.1f} points per path")
    
    # Overall quality assessment
    overall_score = (avg_2d_score + avg_positioning_score) / 2
    
    if overall_score > 0.8:
        print(f"      🎉 EXCELLENT layout quality! ({overall_score*100:.1f}%)")
    elif overall_score > 0.6:
        print(f"      ✅ GOOD layout quality ({overall_score*100:.1f}%)")
    elif overall_score > 0.4:
        print(f"      ⚠️  FAIR layout quality ({overall_score*100:.1f}%)")
    else:
        print(f"      ❌ POOR layout quality ({overall_score*100:.1f}%)")


if __name__ == "__main__":
    success = test_definitive_egi_layout_engine()
    sys.exit(0 if success else 1)
