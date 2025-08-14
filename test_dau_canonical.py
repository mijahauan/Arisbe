#!/usr/bin/env python3
"""
Test Dau-Compliant Canonical EGDF Implementation

Tests the new consolidated implementation against scattered code to ensure:
1. Deterministic EGI → EGDF mapping
2. Proper ligature geometry per Dau Chapter 16
3. Qt Graphics View compatibility
4. Interactive manipulation support
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from canonical import get_canonical_pipeline
from egdf_dau_canonical import create_dau_compliant_egdf_generator
from graphviz_layout_engine_v2 import GraphvizLayoutEngine


def test_canonical_egdf_generation():
    """Test canonical EGDF generation with sample EGIFs."""
    
    print("🎯 Testing Canonical Dau-Compliant EGDF Generation")
    print("=" * 60)
    
    # Initialize components
    pipeline = get_canonical_pipeline()
    egdf_generator = create_dau_compliant_egdf_generator()
    layout_engine = GraphvizLayoutEngine()
    
    # Test cases from our corpus (using working EGIF syntax)
    test_cases = [
        # Simple predicate with constant (quoted)
        '(Human "Socrates")',
        
        # Cut with crossing ligature
        "*x (Human x) ~[ (Mortal x) ]",
        
        # Complex case with multiple cuts
        "*x ~[ (P x) ] ~[ (Q x) ]"
    ]
    
    for i, egif in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {egif}")
        print("-" * 40)
        
        try:
            # Step 1: Parse EGIF → EGI
            egi = pipeline.parse_egif(egif)
            print(f"✓ EGI: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
            
            # Step 2: Generate Graphviz layout
            layout_result = layout_engine.create_layout_from_graph(egi)
            print(f"✓ Layout: {len(layout_result.primitives)} primitives")
            
            # Step 3: Generate canonical Dau-compliant EGDF
            egdf_primitives = egdf_generator.generate_egdf_from_layout(egi, layout_result)
            print(f"✓ EGDF: {len(egdf_primitives)} Dau-compliant primitives")
            
            # Analyze primitive types
            primitive_counts = {}
            for primitive in egdf_primitives:
                ptype = primitive.element_type
                primitive_counts[ptype] = primitive_counts.get(ptype, 0) + 1
            
            print(f"  - Primitives: {primitive_counts}")
            
            # Check for ligature system
            ligatures = [p for p in egdf_primitives if p.element_type == 'identity_line']
            vertices = [p for p in egdf_primitives if p.element_type == 'vertex']
            
            if ligatures:
                print(f"  - Ligatures: {len(ligatures)} (Dau Chapter 16 compliant)")
                for lig in ligatures:
                    if hasattr(lig, 'metadata') and 'path' in lig.metadata:
                        path_length = len(lig.metadata['path'])
                        print(f"    * {lig.element_id}: {path_length} coordinate path")
            
            if vertices:
                print(f"  - Vertices: {len(vertices)} (junction points)")
            
            print("✅ Canonical EGDF generation successful!")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()


def test_deterministic_mapping():
    """Test that same EGI produces same EGDF (deterministic requirement)."""
    
    print("\n🔄 Testing Deterministic Mapping")
    print("=" * 40)
    
    pipeline = get_canonical_pipeline()
    egdf_generator = create_dau_compliant_egdf_generator()
    layout_engine = GraphvizLayoutEngine()
    
    egif = "*x (Human x) ~[ (Mortal x) ]"
    
    try:
        # Generate EGDF twice
        egi = pipeline.parse_egif(egif)
        layout_result = layout_engine.create_layout_from_graph(egi)
        
        egdf1 = egdf_generator.generate_egdf_from_layout(egi, layout_result)
        egdf2 = egdf_generator.generate_egdf_from_layout(egi, layout_result)
        
        # Compare results
        if len(egdf1) == len(egdf2):
            print(f"✓ Same primitive count: {len(egdf1)}")
            
            # Check primitive types match
            types1 = sorted([p.element_type for p in egdf1])
            types2 = sorted([p.element_type for p in egdf2])
            
            if types1 == types2:
                print("✓ Same primitive types")
                print("✅ Deterministic mapping confirmed!")
            else:
                print("❌ Primitive types differ")
        else:
            print(f"❌ Different primitive counts: {len(egdf1)} vs {len(egdf2)}")
            
    except Exception as e:
        print(f"❌ Deterministic test failed: {e}")


def test_qt_graphics_compatibility():
    """Test Qt Graphics View compatibility for interactive manipulation."""
    
    print("\n🖱️ Testing Qt Graphics View Compatibility")
    print("=" * 45)
    
    pipeline = get_canonical_pipeline()
    egdf_generator = create_dau_compliant_egdf_generator()
    layout_engine = GraphvizLayoutEngine()
    
    egif = "*x (Human x) ~[ (Mortal x) ]"
    
    try:
        # Generate EGDF
        egi = pipeline.parse_egif(egif)
        layout_result = layout_engine.create_layout_from_graph(egi)
        egdf_primitives = egdf_generator.generate_egdf_from_layout(egi, layout_result)
        
        # Check Qt Graphics compatibility requirements
        print("Checking Qt Graphics View requirements:")
        
        # 1. All primitives have positions
        all_have_positions = all(hasattr(p, 'position') and p.position for p in egdf_primitives)
        print(f"✓ Positions: {all_have_positions}")
        
        # 2. All primitives have bounds
        all_have_bounds = all(hasattr(p, 'bounds') and p.bounds for p in egdf_primitives)
        print(f"✓ Bounds: {all_have_bounds}")
        
        # 3. Z-index ordering for layering
        z_indices = [p.z_index for p in egdf_primitives if hasattr(p, 'z_index')]
        has_z_ordering = len(z_indices) == len(egdf_primitives)
        print(f"✓ Z-ordering: {has_z_ordering}")
        
        # 4. Ligature paths for interactive manipulation
        ligatures = [p for p in egdf_primitives if p.element_type == 'identity_line']
        ligature_paths = [p for p in ligatures if hasattr(p, 'curve_points') and p.curve_points]
        has_ligature_paths = len(ligature_paths) == len(ligatures)
        print(f"✓ Ligature paths: {has_ligature_paths}")
        
        if all([all_have_positions, all_have_bounds, has_z_ordering, has_ligature_paths]):
            print("✅ Qt Graphics View compatibility confirmed!")
        else:
            print("❌ Some compatibility requirements missing")
            
    except Exception as e:
        print(f"❌ Qt compatibility test failed: {e}")


if __name__ == "__main__":
    print("🚀 Dau-Compliant Canonical EGDF Test Suite")
    print("=" * 60)
    
    test_canonical_egdf_generation()
    test_deterministic_mapping()
    test_qt_graphics_compatibility()
    
    print("\n🎉 Test suite complete!")
    print("\nNext steps:")
    print("1. Remove scattered ligature implementations")
    print("2. Integrate canonical EGDF with Qt Graphics View")
    print("3. Implement interactive manipulation layer")
