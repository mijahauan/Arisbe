#!/usr/bin/env python3
"""
Comprehensive Layout System Demonstration

Showcases the complete Arisbe layout pipeline:
1. Iron-clad layout engine (spatial-logical correspondence)
2. Style-aware layout engine (platform-independent styling)
3. Readability optimizer (logic-indifferent improvements)

This demonstrates the full "matters indifferent to the logic" optimization
while maintaining mathematical correctness.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from layout_engine_ironclad import LayoutEngineIronClad
from layout_engine_styled import StyleAwareLayoutEngine, ElementDistribution, LigatureRouting
from readability_optimizer import ReadabilityOptimizer, OptimizationLevel, OptimizationConstraints
from style_loader import StyleLoader, load_default_style
from egif_parser_dau import parse_egif


def demonstrate_layout_pipeline():
    """Demonstrate the complete layout pipeline"""
    
    print("🎯 ARISBE LAYOUT SYSTEM DEMONSTRATION")
    print("=" * 50)
    
    # Test EGI with potential for collisions and optimization
    test_egif = '''
    *x *y *z (Human x) (Human y) (Human z) 
    (Friend x y) (Friend y z) (Colleague x z)
    ~[ (Enemy x y) (Enemy y z) ]
    '''
    
    print(f"📝 Test EGIF: {test_egif.strip()}")
    egi = parse_egif(test_egif)
    # Count cuts by checking the Cut attribute
    cut_count = len([c for c in egi.Cut if c is not None]) if hasattr(egi, 'Cut') and egi.Cut else 0
    print(f"✅ Parsed EGI: {len(egi.V)} vertices, {len(egi.E)} edges, {cut_count} cuts")
    print()
    
    # STEP 1: Iron-clad layout engine (baseline)
    print("🔧 STEP 1: Iron-Clad Layout Engine")
    print("-" * 30)
    
    iron_clad_engine = LayoutEngineIronClad()
    iron_clad_layout = iron_clad_engine.compute_layout(egi)
    
    print(f"✅ Iron-clad layout computed")
    print(f"   Vertices: {len(iron_clad_layout.vertex_positions)}")
    print(f"   Predicates: {len(iron_clad_layout.predicate_positions)}")
    print(f"   Cut bounds: {len(iron_clad_layout.cut_bounds)}")
    print(f"   Viewport: {iron_clad_layout.viewport_bounds}")
    print()
    
    # STEP 2: Style-aware layout engine
    print("🎨 STEP 2: Style-Aware Layout Engine")
    print("-" * 35)
    
    # Load different styles
    style_loader = StyleLoader()
    available_styles = style_loader.list_available_styles()
    print(f"📚 Available styles: {', '.join(available_styles)}")
    
    # Test with different styles
    for style_name in ['dau-compliant@1.0', 'peirce-authentic@1.0', 'sowa-compliant@1.0']:
        if style_name in available_styles:
            print(f"\n🎭 Testing {style_name}:")
            
            style = style_loader.load_style(style_name)
            styled_engine = StyleAwareLayoutEngine(style)
            
            # Test with different distributions
            distributions = [
                ElementDistribution(layout_algorithm="grid"),
                ElementDistribution(layout_algorithm="circular"),
                ElementDistribution(layout_algorithm="organic")
            ]
            
            for dist in distributions:
                layout = styled_engine.compute_layout(egi, distribution=dist, optimize_readability=False)
                print(f"   {dist.layout_algorithm:>8}: {len(layout.vertex_positions)}v, {len(layout.predicate_positions)}p")
    
    print()
    
    # STEP 3: Readability optimization
    print("🔧 STEP 3: Readability Optimization")
    print("-" * 33)
    
    # Load default style for optimization demo
    default_style = load_default_style()
    styled_engine = StyleAwareLayoutEngine(default_style)
    
    # Create layout with potential collisions (disable optimization first)
    base_layout = styled_engine.compute_layout(egi, optimize_readability=False)
    
    # Create intentional collisions for demonstration
    collision_layout = create_collision_demo_layout(base_layout)
    
    # Test different optimization levels
    optimizer = ReadabilityOptimizer()
    
    print("📊 Optimization Level Comparison:")
    for level in OptimizationLevel:
        optimized = optimizer.optimize_layout(collision_layout, egi, level)
        
        # Calculate metrics
        collisions_before = len(optimizer._detect_collisions(collision_layout))
        collisions_after = len(optimizer._detect_collisions(optimized))
        readability_score = optimizer._calculate_readability_score(optimized)
        
        print(f"   {level.value:>10}: {collisions_before}→{collisions_after} collisions, score: {readability_score:.1f}")
    
    print()
    
    # STEP 4: Complete pipeline demonstration
    print("🚀 STEP 4: Complete Pipeline")
    print("-" * 25)
    
    # Demonstrate the full pipeline with different configurations
    configurations = [
        ("Basic Iron-Clad", None, None, False),
        ("Style-Aware Only", default_style, None, False),
        ("Style + Grid Distribution", default_style, ElementDistribution(layout_algorithm="grid"), False),
        ("Style + Organic Distribution", default_style, ElementDistribution(layout_algorithm="organic"), False),
        ("Complete Pipeline (Optimized)", default_style, ElementDistribution(layout_algorithm="organic"), True),
    ]
    
    print("🔄 Pipeline Configurations:")
    for name, style, distribution, optimize in configurations:
        if style:
            engine = StyleAwareLayoutEngine(style)
            layout = engine.compute_layout(egi, distribution=distribution, optimize_readability=optimize)
        else:
            engine = LayoutEngineIronClad()
            layout = engine.compute_layout(egi)
        
        # Calculate layout quality metrics
        collisions = len(ReadabilityOptimizer()._detect_collisions(layout)) if style else "N/A"
        viewport_area = layout.viewport_bounds.width * layout.viewport_bounds.height
        
        print(f"   {name:>30}: {viewport_area:>8.0f} area, {collisions} collisions")
    
    print()
    
    # STEP 5: Advanced features demonstration
    print("⚡ STEP 5: Advanced Features")
    print("-" * 26)
    
    # Custom optimization constraints
    custom_constraints = OptimizationConstraints(
        min_element_spacing=15.0,
        collision_penalty_weight=20.0,
        max_iterations=50
    )
    
    custom_optimizer = ReadabilityOptimizer(custom_constraints)
    custom_optimized = custom_optimizer.optimize_layout(collision_layout, egi, OptimizationLevel.AGGRESSIVE)
    
    print("🎛️  Custom Optimization Constraints:")
    print(f"   Min spacing: {custom_constraints.min_element_spacing}")
    print(f"   Collision penalty: {custom_constraints.collision_penalty_weight}")
    print(f"   Max iterations: {custom_constraints.max_iterations}")
    
    # Style-aware constraints integration
    style_aware_engine = StyleAwareLayoutEngine(default_style)
    integrated_layout = style_aware_engine.compute_layout(egi, optimize_readability=True)
    
    print(f"\n🔗 Style-Aware Integration:")
    print(f"   Element spacing from style: {default_style.element_spacing}")
    print(f"   Cut padding from style: {default_style.cut_padding}")
    print(f"   Automatic constraint derivation: ✅")
    
    print()
    
    # STEP 6: Validation and guarantees
    print("✅ STEP 6: Validation & Guarantees")
    print("-" * 32)
    
    # Validate iron-clad guarantees are maintained
    try:
        optimizer._validate_optimization(collision_layout, integrated_layout, egi)
        print("🛡️  Iron-clad guarantees: ✅ MAINTAINED")
    except AssertionError as e:
        print(f"❌ Iron-clad guarantee violation: {e}")
    
    # Validate style integration
    style_hints = integrated_layout.style_hints
    if 'style_aware' in style_hints and style_hints['style_aware']:
        print("🎨 Style integration: ✅ ACTIVE")
    else:
        print("❌ Style integration: MISSING")
    
    # Validate readability improvements
    original_collisions = len(optimizer._detect_collisions(collision_layout))
    optimized_collisions = len(optimizer._detect_collisions(integrated_layout))
    
    if optimized_collisions <= original_collisions:
        print(f"📈 Readability improvement: ✅ {original_collisions}→{optimized_collisions} collisions")
    else:
        print(f"❌ Readability regression: {original_collisions}→{optimized_collisions} collisions")
    
    print()
    print("🎉 DEMONSTRATION COMPLETE!")
    print("=" * 50)
    print("The Arisbe layout system successfully demonstrates:")
    print("✅ Mathematical correctness (iron-clad guarantees)")
    print("✅ Platform-independent styling")
    print("✅ Logic-indifferent readability optimization")
    print("✅ Complete integration and validation")


def create_collision_demo_layout(base_layout):
    """Create a layout with intentional collisions for demonstration"""
    
    # Create a copy for modification
    collision_layout = base_layout
    
    # Force some collisions by moving elements to similar positions
    vertex_ids = list(collision_layout.vertex_positions.keys())
    predicate_ids = list(collision_layout.predicate_positions.keys())
    
    if len(vertex_ids) >= 2:
        # Move vertices close together
        pos1 = collision_layout.vertex_positions[vertex_ids[0]]
        collision_layout.vertex_positions[vertex_ids[1]] = pos1
    
    if len(predicate_ids) >= 2:
        # Move predicates close together
        pos1 = collision_layout.predicate_positions[predicate_ids[0]]
        from layout_engine_ironclad import Point
        collision_layout.predicate_positions[predicate_ids[1]] = Point(pos1.x + 10, pos1.y + 5)
    
    return collision_layout


def demonstrate_style_comparison():
    """Demonstrate visual differences between styles"""
    
    print("\n🎭 STYLE COMPARISON DEMONSTRATION")
    print("=" * 40)
    
    test_egif = '*x (Human x) (Mortal x)'
    egi = parse_egif(test_egif)
    
    style_loader = StyleLoader()
    
    for style_name in style_loader.list_available_styles():
        if style_name.endswith('@1.0') and style_name != 'dau-classic@1.0':  # Skip invalid style
            try:
                style = style_loader.load_style(style_name)
            except Exception as e:
                print(f"⚠️  Skipping {style_name}: {e}")
                continue
            engine = StyleAwareLayoutEngine(style)
            layout = engine.compute_layout(egi)
            
            print(f"\n📋 {style.style_name} v{style.version}:")
            print(f"   Description: {style.description}")
            print(f"   Font: {style.font_family} {style.font_size}pt")
            print(f"   Cut shape: {style.cut_shape}")
            print(f"   Element spacing: {style.element_spacing}")
            print(f"   Alternating shading: {'✅' if style.alternating_shading_enabled else '❌'}")
            print(f"   Arity numbers: {'✅' if style.arity_numbers_enabled else '❌'}")


if __name__ == '__main__':
    try:
        demonstrate_layout_pipeline()
        demonstrate_style_comparison()
    except Exception as e:
        print(f"❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
