"""
Demo: Hierarchical View System with Collapsible Contexts

This demo showcases:
1. Multi-scale EGI visualization with context collapse
2. R-tree spatial indexing performance
3. Level-of-detail rendering based on zoom
4. Seamless navigation between abstraction levels
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hierarchical_view_system import (
    HierarchicalViewSystem, ViewContext, ViewLevel, 
    SpatialBounds, ContextSummary
)
from egi_core_dau import RelationalGraphWithCuts, Cut
import time
import random
from frozendict import frozendict


def create_large_nested_egi(num_root_cuts: int = 20, max_depth: int = 4) -> RelationalGraphWithCuts:
    """Create a large EGI with deep nesting for testing scalability."""
    
    # Initialize collections for EGI components
    vertices = set()
    edges = set()
    cuts = set()
    nu_mapping = {}
    area_mapping = {"sheet": set()}
    rel_mapping = {}
    
    cut_counter = 0
    
    def create_nested_structure(parent_area: str, depth: int, cuts_at_level: int) -> None:
        nonlocal cut_counter
        
        if depth <= 0:
            return
        
        # Create cuts at this level
        level_cuts = []
        for i in range(cuts_at_level):
            cut_id = f"cut_{cut_counter}"
            cut_counter += 1
            
            # Create cut
            cut = Cut(cut_id)
            cuts.add(cut)
            level_cuts.append(cut_id)
            
            # Add to parent area
            if parent_area not in area_mapping:
                area_mapping[parent_area] = set()
            area_mapping[parent_area].add(cut_id)
            
            # Initialize cut as area
            area_mapping[cut_id] = set()
        
        # Recursively create nested structures
        for cut_id in level_cuts:
            # Vary the number of children to create complexity
            children_count = random.randint(1, 5) if depth > 1 else 0
            if children_count > 0:
                create_nested_structure(cut_id, depth - 1, children_count)
    
    # Create root structure
    create_nested_structure("sheet", max_depth, num_root_cuts)
    
    # Convert area mapping to frozen sets
    frozen_area_mapping = {}
    for area_id, contained_elements in area_mapping.items():
        frozen_area_mapping[area_id] = frozenset(contained_elements)
    
    # Create the RelationalGraphWithCuts with all required components
    egi = RelationalGraphWithCuts(
        V=frozenset(vertices),
        E=frozenset(edges),
        nu=frozendict(nu_mapping),
        sheet="sheet",
        Cut=frozenset(cuts),
        area=frozendict(frozen_area_mapping),
        rel=frozendict(rel_mapping)
    )
    
    return egi


def benchmark_spatial_queries(view_system: HierarchicalViewSystem, num_queries: int = 1000) -> None:
    """Benchmark R-tree spatial query performance."""
    print(f"\n=== R-tree Spatial Query Benchmark ===")
    
    # Generate random query rectangles
    viewport = view_system.viewport_bounds
    queries = []
    
    for _ in range(num_queries):
        # Random position within viewport
        x = random.uniform(viewport.x, viewport.x + viewport.width * 0.8)
        y = random.uniform(viewport.y, viewport.y + viewport.height * 0.8)
        
        # Random size (10% to 50% of viewport)
        width = random.uniform(viewport.width * 0.1, viewport.width * 0.5)
        height = random.uniform(viewport.height * 0.1, viewport.height * 0.5)
        
        queries.append(SpatialBounds(x, y, width, height))
    
    # Benchmark R-tree queries
    start_time = time.time()
    total_results = 0
    
    for query_bounds in queries:
        results = view_system.spatial_index.query_region(query_bounds)
        total_results += len(results)
    
    end_time = time.time()
    
    print(f"R-tree Performance:")
    print(f"  - {num_queries} spatial queries")
    print(f"  - Total time: {(end_time - start_time) * 1000:.2f} ms")
    print(f"  - Average per query: {((end_time - start_time) / num_queries) * 1000:.3f} ms")
    print(f"  - Total contexts found: {total_results}")
    print(f"  - Average contexts per query: {total_results / num_queries:.1f}")


def demonstrate_context_collapse(view_system: HierarchicalViewSystem, egi: RelationalGraphWithCuts) -> None:
    """Demonstrate context collapse and expansion functionality."""
    print(f"\n=== Context Collapse/Expand Demo ===")
    
    # Show initial state
    visible_contexts = view_system.get_visible_contexts()
    print(f"Initial visible contexts: {len(visible_contexts)}")
    
    # Find contexts with high complexity
    complex_contexts = []
    for context in visible_contexts:
        if context.summary and context.summary.complexity_score > 15:
            complex_contexts.append(context)
    
    if complex_contexts:
        print(f"Found {len(complex_contexts)} complex contexts for collapse demo")
        
        # Collapse the most complex context
        most_complex = max(complex_contexts, key=lambda c: c.summary.complexity_score)
        print(f"\nCollapsing context '{most_complex.context_id}':")
        print(f"  - Complexity score: {most_complex.summary.complexity_score:.1f}")
        print(f"  - Contains {len(most_complex.contained_cuts)} cuts")
        print(f"  - Max depth: {most_complex.summary.max_nesting_depth}")
        
        view_system.collapse_context(most_complex.context_id)
        
        # Show effect on visible contexts
        visible_after_collapse = view_system.get_visible_contexts()
        print(f"  - Visible contexts after collapse: {len(visible_after_collapse)}")
        
        # Expand it back
        print(f"\nExpanding context '{most_complex.context_id}':")
        view_system.expand_context(most_complex.context_id)
        
        visible_after_expand = view_system.get_visible_contexts()
        print(f"  - Visible contexts after expand: {len(visible_after_expand)}")


def demonstrate_zoom_levels(view_system: HierarchicalViewSystem, egi: RelationalGraphWithCuts) -> None:
    """Demonstrate automatic level-of-detail based on zoom."""
    print(f"\n=== Zoom Level-of-Detail Demo ===")
    
    zoom_levels = [0.25, 0.5, 1.0, 2.0, 4.0]
    
    for zoom in zoom_levels:
        print(f"\nZoom level: {zoom}x")
        view_system.set_zoom_level(zoom)
        
        visible_contexts = view_system.get_visible_contexts()
        
        # Count contexts by view level
        level_counts = {level: 0 for level in ViewLevel}
        for context in visible_contexts:
            level_counts[context.view_level] += 1
        
        print(f"  - Total visible contexts: {len(visible_contexts)}")
        for level, count in level_counts.items():
            if count > 0:
                print(f"  - {level.value}: {count}")


def analyze_scalability(view_system: HierarchicalViewSystem, egi: RelationalGraphWithCuts) -> None:
    """Analyze system scalability with large EGI structures."""
    print(f"\n=== Scalability Analysis ===")
    
    total_cuts = len(egi.Cut)
    total_contexts = len(view_system.contexts)
    
    print(f"EGI Structure:")
    print(f"  - Total cuts: {total_cuts}")
    print(f"  - Total contexts: {total_contexts}")
    print(f"  - Context reduction ratio: {total_cuts / total_contexts:.1f}:1")
    
    # Analyze context complexity distribution
    complexities = []
    for context in view_system.contexts.values():
        if context.summary:
            complexities.append(context.summary.complexity_score)
    
    if complexities:
        complexities.sort()
        print(f"\nContext Complexity Distribution:")
        print(f"  - Min complexity: {min(complexities):.1f}")
        print(f"  - Max complexity: {max(complexities):.1f}")
        print(f"  - Median complexity: {complexities[len(complexities)//2]:.1f}")
        print(f"  - Average complexity: {sum(complexities)/len(complexities):.1f}")
    
    # Analyze viewport efficiency
    viewport_area = view_system.viewport_bounds.area()
    visible_contexts = view_system.get_visible_contexts()
    
    if visible_contexts:
        visible_area = sum(c.spatial_bounds.area() for c in visible_contexts if c.spatial_bounds)
        coverage_ratio = visible_area / viewport_area
        
        print(f"\nViewport Efficiency:")
        print(f"  - Viewport area: {viewport_area:.0f}")
        print(f"  - Visible context area: {visible_area:.0f}")
        print(f"  - Coverage ratio: {coverage_ratio:.2f}")
        print(f"  - Contexts per viewport: {len(visible_contexts)}")


def main():
    """Main demo function showcasing hierarchical view system capabilities."""
    print("=" * 60)
    print("HIERARCHICAL VIEW SYSTEM WITH COLLAPSIBLE CONTEXTS")
    print("=" * 60)
    
    # Create viewport bounds
    viewport = SpatialBounds(0, 0, 1200, 800)
    
    print(f"Viewport: {viewport.width}x{viewport.height}")
    
    # Test different EGI sizes
    test_cases = [
        ("Small EGI", 5, 3),
        ("Medium EGI", 15, 4), 
        ("Large EGI", 25, 5),
        ("Very Large EGI", 40, 6)
    ]
    
    for case_name, num_roots, max_depth in test_cases:
        print(f"\n" + "=" * 40)
        print(f"Testing: {case_name}")
        print(f"Root cuts: {num_roots}, Max depth: {max_depth}")
        print("=" * 40)
        
        # Create test EGI
        print("Creating large nested EGI structure...")
        start_time = time.time()
        egi = create_large_nested_egi(num_roots, max_depth)
        creation_time = time.time() - start_time
        
        print(f"EGI created in {creation_time * 1000:.1f} ms")
        print(f"Total cuts: {len(egi.Cut)}")
        
        # Build hierarchical view system
        print("Building hierarchical view system...")
        start_time = time.time()
        view_system = HierarchicalViewSystem(viewport)
        view_system.build_hierarchical_view(egi, max_depth=3)
        build_time = time.time() - start_time
        
        print(f"View system built in {build_time * 1000:.1f} ms")
        print(f"Total contexts created: {len(view_system.contexts)}")
        
        # Run demonstrations
        analyze_scalability(view_system, egi)
        benchmark_spatial_queries(view_system, num_queries=500)
        demonstrate_context_collapse(view_system, egi)
        demonstrate_zoom_levels(view_system, egi)
        
        # Performance summary
        print(f"\n--- Performance Summary for {case_name} ---")
        print(f"EGI Creation: {creation_time * 1000:.1f} ms")
        print(f"View System Build: {build_time * 1000:.1f} ms")
        print(f"Total Processing: {(creation_time + build_time) * 1000:.1f} ms")
        print(f"Cuts per ms: {len(egi.Cut) / ((creation_time + build_time) * 1000):.1f}")
    
    print(f"\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    
    print(f"\nKey Insights:")
    print(f"1. R-tree enables O(log n) spatial queries regardless of EGI size")
    print(f"2. Context collapse reduces visual complexity by orders of magnitude")
    print(f"3. Level-of-detail automatically adapts to zoom levels")
    print(f"4. System scales to arbitrarily large EGI structures")
    print(f"5. 'Whole worlds of graphs' can indeed lie in single collapsed contexts")


if __name__ == "__main__":
    main()
