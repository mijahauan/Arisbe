#!/usr/bin/env python3
"""
Test Definitive EGI Layout Engine with Actual Corpus Graphs

Tests the definitive three-step layout engine using real graphs from the Arisbe corpus.
This provides validation on actual EGI examples rather than synthetic test cases.
"""

import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from definitive_egi_layout_engine import DefinitiveEGILayoutEngine
from graphviz_svg_renderer import GraphvizSVGRenderer
from egi_io import load_egi_json


def test_definitive_corpus_graphs():
    """Test the definitive layout engine with actual corpus graphs"""
    
    print("🚀 TESTING DEFINITIVE EGI LAYOUT ENGINE - CORPUS GRAPHS")
    print("=" * 70)
    
    # Initialize engines
    layout_engine = DefinitiveEGILayoutEngine()
    svg_renderer = GraphvizSVGRenderer()
    
    # Find all corpus graphs
    corpus_dir = Path(__file__).parent.parent / 'corpus' / 'graphs'
    
    if not corpus_dir.exists():
        print(f"❌ Corpus directory not found: {corpus_dir}")
        return False
    
    # Collect all .egi.json files
    corpus_graphs = []
    for graph_dir in corpus_dir.iterdir():
        if graph_dir.is_dir():
            egi_files = list(graph_dir.glob("*.egi.json"))
            if egi_files:
                corpus_graphs.append({
                    'name': graph_dir.name,
                    'path': egi_files[0],
                    'description': f"Corpus graph: {graph_dir.name}"
                })
    
    if not corpus_graphs:
        print(f"❌ No .egi.json files found in {corpus_dir}")
        return False
    
    print(f"\n📚 Found {len(corpus_graphs)} corpus graphs")
    print(f"📚 Testing definitive pipeline: neato → bottom-up → area-aware A*")
    print()
    
    results = []
    
    for graph_info in corpus_graphs:
        print(f"🧪 Testing: {graph_info['name']}")
        print(f"   📁 {graph_info['description']}")
        
        try:
            # Load EGI from JSON
            egi = load_egi_json(str(graph_info['path']))
            
            vertex_count = len(egi.V)
            edge_count = len(egi.E) 
            cut_count = len(egi.Cut)
            print(f"   ✅ Loaded: {vertex_count} vertices, {edge_count} edges, {cut_count} cuts")
            
            # Generate description from EGI structure
            description = generate_egi_description(egi)
            print(f"   📝 Structure: {description}")
            
            # Generate DTO using definitive approach
            dto = layout_engine.generate_layout(egi)
            print(f"   ✅ Definitive layout completed")
            
            # Validate DTO structure
            validation_result = validate_corpus_dto(dto, egi, graph_info)
            
            # Print DTO details
            print_corpus_dto_details(dto)
            
            # Generate SVG
            svg_path = svg_renderer.save_svg(
                dto, 
                f"Corpus Graph - {graph_info['name']}", 
                description,
                f"corpus_{graph_info['name'].lower()}",
                "test_outputs/corpus_layouts"
            )
            print(f"   📄 SVG saved: {svg_path.name}")
            
            results.append({
                'name': graph_info['name'],
                'success': validation_result['success'],
                'issues': validation_result['issues'],
                'dto': dto,
                'svg_path': svg_path,
                'vertex_count': vertex_count,
                'edge_count': edge_count,
                'cut_count': cut_count
            })
            
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                'name': graph_info['name'],
                'success': False,
                'issues': [f"Exception: {e}"],
                'dto': None
            })
        
        print()
    
    # Summary
    print("🎯 CORPUS TEST SUMMARY:")
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    print(f"   Total corpus graphs: {total}")
    print(f"   Successful layouts: {successful}")
    print(f"   Failed layouts: {total - successful}")
    print(f"   Success rate: {successful/total*100:.1f}%")
    
    if successful < total:
        print("   ⚠️  Some corpus graphs failed - check output for details")
        print("   📋 Failed graphs:")
        for result in results:
            if not result['success']:
                print(f"      • {result['name']}: {result['issues'][0] if result['issues'] else 'Unknown error'}")
    else:
        print("   🎉 All corpus graphs processed successfully!")
    
    # Advanced analysis
    if successful > 0:
        print("\n📊 CORPUS LAYOUT QUALITY ANALYSIS:")
        analyze_corpus_layout_quality(results)
    
    # Graph complexity analysis
    print("\n📈 CORPUS COMPLEXITY ANALYSIS:")
    analyze_corpus_complexity(results)
    
    return successful == total


def generate_egi_description(egi):
    """Generate a human-readable description of the EGI structure"""
    
    # Get relation names
    relations = list(egi.rel.values())
    
    # Get vertex labels (constants)
    constants = [egi.rho.get(v.id) for v in egi.V if egi.rho.get(v.id)]
    constants = [c for c in constants if c]  # Remove None values
    
    # Build description
    parts = []
    
    if constants:
        parts.append(f"Constants: {', '.join(constants)}")
    
    if relations:
        parts.append(f"Relations: {', '.join(relations)}")
    
    if egi.Cut:
        parts.append(f"{len(egi.Cut)} cuts")
    
    return " | ".join(parts) if parts else "Simple graph"


def validate_corpus_dto(dto, egi, graph_info):
    """Validate DTO structure for corpus graphs"""
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
    
    # Check for 2D positioning (if multiple vertices)
    if len(dto.vertices) > 1:
        y_positions = [v.pos[1] for v in dto.vertices]
        unique_y_positions = len(set(y_positions))
        if unique_y_positions == 1:
            issues.append("All vertices positioned on same horizontal line (1D layout)")
    
    # Check containment correctness
    containment_issues = check_corpus_containment(dto, egi)
    issues.extend(containment_issues)
    
    success = len(issues) == 0
    
    if success:
        print("   ✅ DTO validation: PASSED")
    else:
        print("   ❌ DTO validation: FAILED")
        for issue in issues[:3]:  # Show first 3 issues
            print(f"      • {issue}")
        if len(issues) > 3:
            print(f"      • ... and {len(issues) - 3} more issues")
    
    return {'success': success, 'issues': issues}


def check_corpus_containment(dto, egi):
    """Check containment correctness for corpus graphs"""
    issues = []
    
    # Build area rectangles lookup
    area_rects = {area.id: area.rect for area in dto.areas}
    
    # Check vertex containment
    for vertex in dto.vertices:
        if vertex.parent_area_id in area_rects:
            area_rect = area_rects[vertex.parent_area_id]
            if not (area_rect.x <= vertex.pos[0] <= area_rect.x + area_rect.width and
                   area_rect.y <= vertex.pos[1] <= area_rect.y + area_rect.height):
                issues.append(f"Vertex {vertex.id} outside its area {vertex.parent_area_id}")
    
    # Check edge label containment
    for edge_label in dto.edge_labels:
        if edge_label.parent_area_id in area_rects:
            area_rect = area_rects[edge_label.parent_area_id]
            label_center_x = edge_label.rect.x + edge_label.rect.width / 2
            label_center_y = edge_label.rect.y + edge_label.rect.height / 2
            
            if not (area_rect.x <= label_center_x <= area_rect.x + area_rect.width and
                   area_rect.y <= label_center_y <= area_rect.y + area_rect.height):
                issues.append(f"Edge label {edge_label.id} outside its area {edge_label.parent_area_id}")
    
    return issues


def print_corpus_dto_details(dto):
    """Print DTO details for corpus graphs"""
    
    print(f"   📊 Layout Results:")
    print(f"      Areas: {len(dto.areas)} | Vertices: {len(dto.vertices)} | Edge Labels: {len(dto.edge_labels)} | Ligatures: {len(dto.ligatures)}")
    
    # Analyze 2D positioning
    if len(dto.vertices) > 1:
        y_positions = [v.pos[1] for v in dto.vertices]
        x_positions = [v.pos[0] for v in dto.vertices]
        y_spread = max(y_positions) - min(y_positions)
        x_spread = max(x_positions) - min(x_positions)
        
        print(f"   📏 2D Distribution: X-spread={x_spread:.1f}, Y-spread={y_spread:.1f}")
        
        # Calculate 2D utilization score
        unique_y = len(set(y_positions))
        unique_x = len(set(x_positions))
        total_vertices = len(dto.vertices)
        
        x_diversity = unique_x / total_vertices
        y_diversity = unique_y / total_vertices
        utilization_2d = (x_diversity + y_diversity) / 2 * 100
        
        print(f"   🎯 2D Utilization: {utilization_2d:.1f}% (X: {x_diversity*100:.1f}%, Y: {y_diversity*100:.1f}%)")
    
    # Analyze ligature complexity
    if dto.ligatures:
        path_lengths = [len(lig.path_points) for lig in dto.ligatures]
        avg_complexity = sum(path_lengths) / len(path_lengths)
        print(f"   🔗 Ligature Complexity: {avg_complexity:.1f} points/path (range: {min(path_lengths)}-{max(path_lengths)})")


def analyze_corpus_layout_quality(results):
    """Analyze layout quality across corpus graphs"""
    
    successful_results = [r for r in results if r['success'] and r['dto']]
    
    if not successful_results:
        print("      No successful layouts to analyze")
        return
    
    # Analyze 2D space utilization across all graphs
    total_2d_scores = []
    total_positioning_scores = []
    
    for result in successful_results:
        dto = result['dto']
        if len(dto.vertices) > 1:
            # Calculate 2D distribution
            y_positions = [v.pos[1] for v in dto.vertices]
            x_positions = [v.pos[0] for v in dto.vertices]
            
            unique_y_count = len(set(y_positions))
            unique_x_count = len(set(x_positions))
            total_vertices = len(dto.vertices)
            
            # Score based on 2D space utilization
            x_diversity = unique_x_count / total_vertices
            y_diversity = unique_y_count / total_vertices
            combined_2d_score = (x_diversity + y_diversity) / 2
            
            total_2d_scores.append(combined_2d_score)
            
            # Calculate positioning spread
            y_spread = max(y_positions) - min(y_positions) if len(y_positions) > 1 else 0
            x_spread = max(x_positions) - min(x_positions) if len(x_positions) > 1 else 0
            
            positioning_score = min(1.0, (x_spread + y_spread) / 300)  # Normalize
            total_positioning_scores.append(positioning_score)
    
    if total_2d_scores:
        avg_2d_score = sum(total_2d_scores) / len(total_2d_scores)
        avg_positioning_score = sum(total_positioning_scores) / len(total_positioning_scores)
        
        print(f"      Average 2D Space Utilization: {avg_2d_score*100:.1f}%")
        print(f"      Average Positioning Spread: {avg_positioning_score*100:.1f}%")
        
        # Overall quality assessment
        overall_score = (avg_2d_score + avg_positioning_score) / 2
        
        if overall_score > 0.7:
            print(f"      🎉 EXCELLENT corpus layout quality! ({overall_score*100:.1f}%)")
        elif overall_score > 0.5:
            print(f"      ✅ GOOD corpus layout quality ({overall_score*100:.1f}%)")
        elif overall_score > 0.3:
            print(f"      ⚠️  FAIR corpus layout quality ({overall_score*100:.1f}%)")
        else:
            print(f"      ❌ POOR corpus layout quality ({overall_score*100:.1f}%)")
    
    # Analyze ligature routing efficiency
    total_ligatures = 0
    total_path_complexity = 0
    
    for result in successful_results:
        dto = result['dto']
        for ligature in dto.ligatures:
            total_path_complexity += len(ligature.path_points)
            total_ligatures += 1
    
    if total_ligatures > 0:
        avg_path_complexity = total_path_complexity / total_ligatures
        print(f"      Average Ligature Complexity: {avg_path_complexity:.1f} points per path")
        
        if avg_path_complexity <= 2.5:
            print(f"      ✅ Excellent ligature efficiency (≤2.5 points/path)")
        elif avg_path_complexity <= 4.0:
            print(f"      ⚠️  Fair ligature efficiency (≤4.0 points/path)")
        else:
            print(f"      ❌ Poor ligature efficiency (>4.0 points/path)")


def analyze_corpus_complexity(results):
    """Analyze the complexity distribution of corpus graphs"""
    
    successful_results = [r for r in results if r['success']]
    
    if not successful_results:
        print("      No successful results to analyze")
        return
    
    # Categorize by complexity
    simple_graphs = []      # 1-2 vertices, 0-1 cuts
    medium_graphs = []      # 3-5 vertices, 1-2 cuts
    complex_graphs = []     # 6+ vertices or 3+ cuts
    
    for result in successful_results:
        v_count = result.get('vertex_count', 0)
        c_count = result.get('cut_count', 0)
        
        if v_count <= 2 and c_count <= 1:
            simple_graphs.append(result)
        elif v_count <= 5 and c_count <= 2:
            medium_graphs.append(result)
        else:
            complex_graphs.append(result)
    
    print(f"      Graph Complexity Distribution:")
    print(f"        Simple (≤2V, ≤1C): {len(simple_graphs)} graphs")
    print(f"        Medium (≤5V, ≤2C): {len(medium_graphs)} graphs")
    print(f"        Complex (>5V or >2C): {len(complex_graphs)} graphs")
    
    # Success rates by complexity
    total_simple = len([r for r in results if (r.get('vertex_count', 0) <= 2 and r.get('cut_count', 0) <= 1)])
    total_medium = len([r for r in results if (r.get('vertex_count', 0) <= 5 and r.get('cut_count', 0) <= 2 and not (r.get('vertex_count', 0) <= 2 and r.get('cut_count', 0) <= 1))])
    total_complex = len([r for r in results if (r.get('vertex_count', 0) > 5 or r.get('cut_count', 0) > 2)])
    
    if total_simple > 0:
        simple_success_rate = len(simple_graphs) / total_simple * 100
        print(f"        Simple Success Rate: {simple_success_rate:.1f}%")
    
    if total_medium > 0:
        medium_success_rate = len(medium_graphs) / total_medium * 100
        print(f"        Medium Success Rate: {medium_success_rate:.1f}%")
    
    if total_complex > 0:
        complex_success_rate = len(complex_graphs) / total_complex * 100
        print(f"        Complex Success Rate: {complex_success_rate:.1f}%")
    
    # Highlight most complex successfully processed graph
    if successful_results:
        most_complex = max(successful_results, key=lambda r: r.get('vertex_count', 0) + r.get('cut_count', 0) * 2)
        print(f"      Most Complex Success: {most_complex['name']} ({most_complex.get('vertex_count', 0)}V, {most_complex.get('cut_count', 0)}C)")


if __name__ == "__main__":
    success = test_definitive_corpus_graphs()
    sys.exit(0 if success else 1)
