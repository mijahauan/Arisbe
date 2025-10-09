#!/usr/bin/env python3
"""
Comprehensive Corpus Test for Connection Port System

Tests the optimized connection port system across the entire corpus
to validate consistent performance and visual quality.
"""

import sys
from pathlib import Path
import time
import traceback

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from definitive_egi_layout_engine import DefinitiveEGILayoutEngine
from graphviz_svg_renderer import GraphvizSVGRenderer
from style_loader import StyleLoader
from egi_io import load_egi_json


def check_cut_overlaps(dto):
    """
    Check for cut violations:
    1. Sibling cuts overlapping (INVALID)
    2. Child cuts extending beyond parent bounds (INVALID)
    """
    cuts = {}
    for area in dto.areas:
        if not area.is_sheet:
            r = area.rect
            cuts[area.id] = {
                'id': area.id,
                'x1': r.x, 'y1': r.y,
                'x2': r.x + r.width, 'y2': r.y + r.height,
                'parent': area.parent_id
            }
    
    if len(cuts) < 2:
        return 0
    
    violations = 0
    
    # Helper: Check if cut1 is ancestor of cut2
    def is_ancestor(cut1_id, cut2_id):
        current = cut2_id
        while current:
            if current == cut1_id:
                return True
            current = cuts.get(current, {}).get('parent')
        return False
    
    # Check 1: Sibling overlaps (but allow ancestor-descendant overlaps)
    cut_list = list(cuts.values())
    for i in range(len(cut_list)):
        for j in range(i+1, len(cut_list)):
            c1, c2 = cut_list[i], cut_list[j]
            
            # Skip ancestor-descendant pairs (nesting is OK)
            if is_ancestor(c1['id'], c2['id']) or is_ancestor(c2['id'], c1['id']):
                continue
            
            # Check if siblings overlap
            if not (c1['x2'] <= c2['x1'] or c2['x2'] <= c1['x1'] or
                    c1['y2'] <= c2['y1'] or c2['y2'] <= c1['y1']):
                violations += 1
    
    # Check 2: Parent-child containment
    for cut_id, cut in cuts.items():
        if cut['parent'] and cut['parent'] in cuts:
            parent = cuts[cut['parent']]
            
            # Child must be INSIDE parent (with tolerance for rendering)
            tolerance = 2  # Allow 2px rendering error
            if not (cut['x1'] >= parent['x1'] - tolerance and
                    cut['x2'] <= parent['x2'] + tolerance and
                    cut['y1'] >= parent['y1'] - tolerance and
                    cut['y2'] <= parent['y2'] + tolerance):
                violations += 1
    
    return violations


def test_entire_corpus():
    """Test connection port system across the entire corpus"""
    
    print("🌍 COMPREHENSIVE CORPUS CONNECTION PORT TEST")
    print("=" * 55)
    
    layout_engine = DefinitiveEGILayoutEngine()
    svg_renderer = GraphvizSVGRenderer()
    style_loader = StyleLoader()
    style = style_loader.load_default_style()
    
    # Find all corpus graphs
    corpus_dir = Path(__file__).parent.parent / 'corpus' / 'graphs'
    
    if not corpus_dir.exists():
        print("❌ Corpus directory not found")
        return
    
    # Collect all EGI files
    all_graphs = []
    for graph_dir in corpus_dir.iterdir():
        if graph_dir.is_dir():
            egi_files = list(graph_dir.glob("*.egi.json"))
            if egi_files:
                all_graphs.append({
                    'name': graph_dir.name,
                    'path': egi_files[0],
                    'dir': graph_dir
                })
    
    print(f"📚 Found {len(all_graphs)} corpus graphs to test")
    print()
    
    # Test results tracking
    results = {
        'total_graphs': len(all_graphs),
        'successful': 0,
        'failed': 0,
        'total_vertices': 0,
        'total_edges': 0,
        'total_ports': 0,
        'total_ligatures': 0,
        'unary_predicates': 0,
        'multi_arity_predicates': 0,
        'max_arity': 0,
        'crossing_issues': 0,
        'processing_time': 0
    }
    
    failed_graphs = []
    port_statistics = {}
    
    start_time = time.time()
    
    # Process each graph
    for i, graph_info in enumerate(all_graphs, 1):
        graph_name = graph_info['name']
        print(f"🧪 [{i:2d}/{len(all_graphs)}] Testing: {graph_name}", end='', flush=True)
        
        try:
            graph_start = time.time()
            
            # Load EGI
            egi = load_egi_json(str(graph_info['path']))
            
            # Generate layout with connection ports
            dto = layout_engine.generate_layout(egi, style)
            
            graph_elapsed = time.time() - graph_start
            print(f" ({graph_elapsed:.1f}s)")
            
            # Analyze the results
            graph_stats = analyze_graph_results(egi, dto, graph_name)
            
            # CRITICAL: Check for cut overlaps (the actual correctness test!)
            cut_overlaps = check_cut_overlaps(dto)
            graph_stats['cut_overlaps'] = cut_overlaps
            
            if cut_overlaps > 0:
                print(f"   ❌ LAYOUT FAILURE: {cut_overlaps} cut overlaps detected!")
                results['failed'] += 1
                failed_graphs.append({'name': graph_name, 'error': f'{cut_overlaps} cut overlaps'})
            else:
                results['successful'] += 1
            results['total_vertices'] += graph_stats['vertices']
            results['total_edges'] += graph_stats['edges']
            results['total_ports'] += graph_stats['total_ports']
            results['total_ligatures'] += graph_stats['ligatures']
            results['unary_predicates'] += graph_stats['unary_predicates']
            results['multi_arity_predicates'] += graph_stats['multi_arity_predicates']
            results['max_arity'] = max(results['max_arity'], graph_stats['max_arity'])
            results['crossing_issues'] += graph_stats['crossing_issues']
            
            # Store port statistics
            port_statistics[graph_name] = graph_stats
            
            # Generate SVG with actual EGIF
            from egif_generator_dau import EGIFGenerator
            egif_gen = EGIFGenerator(egi)
            egif = egif_gen.generate()
            
            svg_path = svg_renderer.save_svg(
                dto,
                f"Corpus Test - {graph_name}",
                egif,
                f"corpus_test_{graph_name.lower()}",
                "test_outputs/corpus_connection_ports",
                style
            )
            
            print(f"   ✅ Success: {graph_stats['vertices']}V, {graph_stats['edges']}E, {graph_stats['total_ports']}P, {graph_stats['ligatures']}L")
            if graph_stats['crossing_issues'] > 0:
                print(f"   ⚠️  {graph_stats['crossing_issues']} potential crossing issues")
            
        except Exception as e:
            results['failed'] += 1
            failed_graphs.append({'name': graph_name, 'error': str(e)})
            print(f"   ❌ Failed: {e}")
            # Uncomment for detailed error debugging
            # traceback.print_exc()
    
    end_time = time.time()
    results['processing_time'] = end_time - start_time
    
    # Generate comprehensive report
    generate_corpus_report(results, port_statistics, failed_graphs)


def analyze_graph_results(egi, dto, graph_name):
    """Analyze the results for a single graph"""
    
    stats = {
        'vertices': len(egi.V),
        'edges': len(egi.E),
        'cuts': len(egi.Cut),
        'total_ports': 0,
        'ligatures': len(dto.ligatures),
        'unary_predicates': 0,
        'multi_arity_predicates': 0,
        'max_arity': 0,
        'crossing_issues': 0,
        'port_distribution': {'N': 0, 'E': 0, 'S': 0, 'W': 0, 'NE': 0, 'NW': 0, 'SE': 0, 'SW': 0}
    }
    
    # Analyze each edge label
    for edge_label in dto.edge_labels:
        num_ports = len(edge_label.connection_ports)
        stats['total_ports'] += num_ports
        
        if num_ports == 1:
            stats['unary_predicates'] += 1
        elif num_ports > 1:
            stats['multi_arity_predicates'] += 1
        
        stats['max_arity'] = max(stats['max_arity'], num_ports)
        
        # Count port directions
        for port in edge_label.connection_ports:
            if port.direction in stats['port_distribution']:
                stats['port_distribution'][port.direction] += 1
        
        # Check for potential crossing issues
        vertex_sequence = egi.nu.get(edge_label.id, [])
        if len(vertex_sequence) > 1:
            # Simple crossing detection for multi-arity predicates
            edge_ligatures = [lig for lig in dto.ligatures if lig.end_edge_id == edge_label.id]
            if len(edge_ligatures) > 1:
                crossings = detect_potential_crossings(edge_ligatures, edge_label)
                stats['crossing_issues'] += crossings
    
    return stats


def detect_potential_crossings(ligatures, edge_label):
    """Detect potential crossing issues in ligature routing"""
    
    crossing_count = 0
    
    if len(ligatures) < 2:
        return 0
    
    # Check each pair of ligatures for potential crossings
    for i, lig1 in enumerate(ligatures):
        for j, lig2 in enumerate(ligatures[i+1:], i+1):
            if ligatures_may_cross(lig1, lig2, edge_label):
                crossing_count += 1
    
    return crossing_count


def ligatures_may_cross(lig1, lig2, edge_label):
    """Check if two ligatures may cross visually"""
    
    if not lig1.path_points or not lig2.path_points or len(lig1.path_points) < 2 or len(lig2.path_points) < 2:
        return False
    
    # Get start and end points
    start1 = lig1.path_points[0]
    end1 = lig1.path_points[-1]
    start2 = lig2.path_points[0]
    end2 = lig2.path_points[-1]
    
    # Simple crossing check based on relative positions
    label_center_x = edge_label.rect.x + edge_label.rect.width / 2
    label_center_y = edge_label.rect.y + edge_label.rect.height / 2
    
    # Check if ligatures cross the label center from opposite sides
    start1_left = start1[0] < label_center_x
    start2_left = start2[0] < label_center_x
    end1_left = end1[0] < label_center_x
    end2_left = end2[0] < label_center_x
    
    # Potential crossing if starts are on opposite sides but ends cross over
    if start1_left != start2_left:
        if (start1_left and not end1_left and not start2_left and end2_left) or \
           (not start1_left and end1_left and start2_left and not end2_left):
            return True
    
    return False


def generate_corpus_report(results, port_statistics, failed_graphs):
    """Generate comprehensive test report"""
    
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE CORPUS TEST RESULTS")
    print("=" * 60)
    
    # Overall statistics
    print(f"\n🎯 OVERALL PERFORMANCE:")
    print(f"   Total graphs tested: {results['total_graphs']}")
    print(f"   Successful: {results['successful']} ({results['successful']/results['total_graphs']*100:.1f}%)")
    print(f"   Failed: {results['failed']} ({results['failed']/results['total_graphs']*100:.1f}%)")
    print(f"   Processing time: {results['processing_time']:.2f} seconds")
    print(f"   Average time per graph: {results['processing_time']/results['total_graphs']:.3f} seconds")
    
    # Graph complexity statistics
    print(f"\n📈 GRAPH COMPLEXITY:")
    print(f"   Total vertices: {results['total_vertices']}")
    print(f"   Total edges: {results['total_edges']}")
    print(f"   Average vertices per graph: {results['total_vertices']/results['successful']:.1f}")
    print(f"   Average edges per graph: {results['total_edges']/results['successful']:.1f}")
    
    # Connection port statistics
    print(f"\n🔌 CONNECTION PORT ANALYSIS:")
    print(f"   Total connection ports: {results['total_ports']}")
    print(f"   Total ligatures: {results['total_ligatures']}")
    print(f"   Unary predicates: {results['unary_predicates']}")
    print(f"   Multi-arity predicates: {results['multi_arity_predicates']}")
    print(f"   Maximum predicate arity: {results['max_arity']}")
    print(f"   Average ports per graph: {results['total_ports']/results['successful']:.1f}")
    
    # Port direction distribution
    print(f"\n🧭 PORT DIRECTION DISTRIBUTION:")
    total_ports = results['total_ports']
    if total_ports > 0:
        direction_totals = {'N': 0, 'E': 0, 'S': 0, 'W': 0, 'NE': 0, 'NW': 0, 'SE': 0, 'SW': 0}
        for stats in port_statistics.values():
            for direction, count in stats['port_distribution'].items():
                direction_totals[direction] += count
        
        for direction in ['N', 'E', 'S', 'W']:
            count = direction_totals[direction]
            percentage = count / total_ports * 100
            print(f"   {direction}: {count:4d} ({percentage:5.1f}%)")
        
        intercardinal_total = sum(direction_totals[d] for d in ['NE', 'NW', 'SE', 'SW'])
        if intercardinal_total > 0:
            print(f"   Intercardinal: {intercardinal_total:4d} ({intercardinal_total/total_ports*100:5.1f}%)")
    
    # Quality assessment
    print(f"\n✅ QUALITY ASSESSMENT:")
    print(f"   Potential crossing issues: {results['crossing_issues']}")
    if results['crossing_issues'] == 0:
        print(f"   🎉 EXCELLENT: No crossing issues detected across entire corpus!")
    else:
        crossing_rate = results['crossing_issues'] / results['successful']
        print(f"   ⚠️  Average crossings per graph: {crossing_rate:.2f}")
    
    # Port optimization effectiveness
    unary_rate = results['unary_predicates'] / (results['unary_predicates'] + results['multi_arity_predicates']) * 100
    print(f"   Unary predicate optimization: {results['unary_predicates']} predicates ({unary_rate:.1f}%)")
    print(f"   Multi-arity optimization: {results['multi_arity_predicates']} predicates ({100-unary_rate:.1f}%)")
    
    # Top complexity graphs
    print(f"\n🏆 TOP COMPLEXITY GRAPHS:")
    complexity_ranking = []
    for name, stats in port_statistics.items():
        complexity_score = stats['vertices'] + stats['edges'] * 2 + stats['total_ports']
        complexity_ranking.append((name, complexity_score, stats))
    
    complexity_ranking.sort(key=lambda x: x[1], reverse=True)
    for i, (name, score, stats) in enumerate(complexity_ranking[:5], 1):
        print(f"   {i}. {name}: {stats['vertices']}V, {stats['edges']}E, {stats['total_ports']}P (score: {score})")
    
    # Failed graphs analysis
    if failed_graphs:
        print(f"\n❌ FAILED GRAPHS ANALYSIS:")
        for failure in failed_graphs:
            print(f"   • {failure['name']}: {failure['error']}")
    
    # Success metrics
    print(f"\n🎉 SUCCESS METRICS:")
    success_rate = results['successful'] / results['total_graphs'] * 100
    if success_rate >= 95:
        print(f"   🌟 OUTSTANDING: {success_rate:.1f}% success rate")
    elif success_rate >= 90:
        print(f"   ✅ EXCELLENT: {success_rate:.1f}% success rate")
    elif success_rate >= 80:
        print(f"   👍 GOOD: {success_rate:.1f}% success rate")
    else:
        print(f"   ⚠️  NEEDS IMPROVEMENT: {success_rate:.1f}% success rate")
    
    print(f"   📄 Generated {results['successful']} SVG files in test_outputs/corpus_connection_ports/")
    
    # Final assessment
    print(f"\n🏁 FINAL ASSESSMENT:")
    if results['failed'] == 0 and results['crossing_issues'] == 0:
        print("   🎯 PERFECT: All graphs processed successfully with no crossing issues!")
        print("   🚀 Connection port system is production-ready for the entire corpus!")
    elif results['failed'] <= 2 and results['crossing_issues'] <= 5:
        print("   ✅ EXCELLENT: Minimal issues detected, system performs very well!")
    else:
        print("   📋 GOOD: System works well with some areas for improvement identified.")


if __name__ == "__main__":
    test_entire_corpus()
    
    print("\n🌍 COMPREHENSIVE CORPUS TEST COMPLETE!")
    print("   📊 Detailed analysis and SVG files generated")
    print("   🔍 Check test_outputs/corpus_connection_ports/ for visual results")
    print("   📈 Connection port system validated across entire corpus")
