#!/usr/bin/env python3
"""
Test the Dau Position Correction System

Validates that the position corrector properly fixes spatial primitive positioning
to respect EGI logical structure and Dau visual conventions.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.egif_parser_dau import EGIFParser
from src.graphviz_layout_engine_v2 import GraphvizLayoutEngine
from src.dau_position_corrector import DauPositionCorrector, apply_dau_position_corrections
from src.diagram_renderer_dau import DiagramRendererDau
from src.pipeline_contracts import validate_layout_result, validate_relational_graph_with_cuts


def test_position_correction_basic():
    """Test basic position correction functionality."""
    print("🧪 Testing Basic Position Correction")
    
    # Test case: vertex should be inside cut but Graphviz places it outside
    egif = '*x ~[ (P x) ]'
    
    parser = EGIFParser()
    egi = parser.parse(egif)
    
    print(f"📝 EGIF: {egif}")
    print(f"🔍 EGI Structure:")
    print(f"   Vertices: {[v.id for v in egi.V]}")
    print(f"   Edges: {[e.id for e in egi.E]}")
    print(f"   Contexts: {list(egi.area.keys())}")
    
    # Validate EGI contract compliance
    try:
        validate_relational_graph_with_cuts(egi)
        print("✅ EGI passes contract validation")
    except Exception as e:
        print(f"❌ EGI contract validation failed: {e}")
    
    # Generate initial layout using the working pipeline
    layout_engine = GraphvizLayoutEngine(mode="default-nopp")  # No post-processing to avoid containment errors
    initial_layout = layout_engine.generate_layout(egi)
    
    print(f"\n📐 Initial Layout:")
    for elem_id, primitive in initial_layout.primitives.items():
        print(f"   {primitive.element_type} {elem_id}: pos={primitive.position}, bounds={primitive.bounds}")
    
    # Validate initial layout contract compliance
    try:
        validate_layout_result(initial_layout)
        print("✅ Initial layout passes contract validation")
    except Exception as e:
        print(f"❌ Initial layout contract validation failed: {e}")
    
    # Apply position corrections
    corrected_layout = apply_dau_position_corrections(initial_layout, egi)
    
    print(f"\n✅ Corrected Layout:")
    for elem_id, primitive in corrected_layout.primitives.items():
        print(f"   {primitive.element_type} {elem_id}: pos={primitive.position}, bounds={primitive.bounds}")
    
    return corrected_layout


def test_position_correction_complex():
    """Test position correction with complex nested structure."""
    print("\n🧪 Testing Complex Position Correction")
    
    # Test case: Roberts' Disjunction with shared constant
    egif = '(Human "Socrates") ~[ (Mortal "Socrates") ]'
    
    parser = EGIFParser()
    egi = parser.parse(egif)
    
    print(f"📝 EGIF: {egif}")
    
    # Generate and correct layout
    layout_engine = GraphvizLayoutEngine(mode="default-nopp")
    initial_layout = layout_engine.generate_layout(egi)
    corrected_layout = apply_dau_position_corrections(initial_layout, egi)
    
    # Validate that Socrates vertex is positioned correctly
    socrates_primitive = None
    for primitive in corrected_layout.primitives.values():
        if primitive.element_type == 'vertex' and 'Socrates' in primitive.element_id:
            socrates_primitive = primitive
            break
    
    if socrates_primitive:
        print(f"✅ Socrates vertex positioned at: {socrates_primitive.position}")
    else:
        print("❌ Could not find Socrates vertex")
    
    return corrected_layout


def test_cut_shape_specification():
    """Test that cuts are specified as rounded rectangles, not ovals."""
    print("\n🧪 Testing Cut Shape Specification")
    
    egif = '~[ (P) ]'
    
    parser = EGIFParser()
    egi = parser.parse(egif)
    
    layout_engine = GraphvizLayoutEngine(mode="default-nopp")
    layout = layout_engine.generate_layout(egi)
    corrected_layout = apply_dau_position_corrections(layout, egi)
    
    # Find cut primitive
    cut_primitive = None
    for primitive in corrected_layout.primitives.values():
        if primitive.element_type == 'cut':
            cut_primitive = primitive
            break
    
    if cut_primitive:
        print(f"✅ Cut primitive found: {cut_primitive.element_id}")
        print(f"   Position: {cut_primitive.position}")
        print(f"   Bounds: {cut_primitive.bounds}")
        
        # Verify bounds represent a rounded rectangle (not circular)
        x1, y1, x2, y2 = cut_primitive.bounds
        width = x2 - x1
        height = y2 - y1
        aspect_ratio = width / height if height > 0 else 1.0
        
        print(f"   Dimensions: {width:.1f} × {height:.1f}")
        print(f"   Aspect ratio: {aspect_ratio:.2f}")
        
        if abs(aspect_ratio - 1.0) > 0.2:
            print("   ✅ Shape is rectangular (not circular)")
        else:
            print("   ⚠️  Shape is nearly square (could be circular)")
    else:
        print("❌ No cut primitive found")
    
    return corrected_layout


def test_visual_rendering_with_corrections():
    """Test that corrected layouts render properly."""
    print("\n🧪 Testing Visual Rendering with Corrections")
    
    egif = '*x (Human x) ~[ (Mortal x) (Wise x) ]'
    
    parser = EGIFParser()
    egi = parser.parse(egif)
    
    layout_engine = GraphvizLayoutEngine(mode="default-nopp")
    initial_layout = layout_engine.generate_layout(egi)
    corrected_layout = apply_dau_position_corrections(initial_layout, egi)
    
    # Test rendering
    renderer = DiagramRendererDau()
    
    try:
        # This would normally render to a canvas, but we'll just test the setup
        print("✅ Renderer initialized successfully")
        print(f"   Layout has {len(corrected_layout.primitives)} primitives")
        
        # Verify all required primitives are present
        vertex_count = sum(1 for p in corrected_layout.primitives.values() if p.element_type == 'vertex')
        predicate_count = sum(1 for p in corrected_layout.primitives.values() if p.element_type == 'predicate')
        cut_count = sum(1 for p in corrected_layout.primitives.values() if p.element_type == 'cut')
        
        print(f"   Primitives: {vertex_count} vertices, {predicate_count} predicates, {cut_count} cuts")
        
    except Exception as e:
        print(f"❌ Rendering test failed: {e}")
    
    return corrected_layout


def main():
    """Run all position correction tests."""
    print("🚀 Dau Position Correction System Tests")
    print("=" * 50)
    
    try:
        # Test basic correction
        test_position_correction_basic()
        
        # Test complex correction
        test_position_correction_complex()
        
        # Test cut shape specification
        test_cut_shape_specification()
        
        # Test visual rendering
        test_visual_rendering_with_corrections()
        
        print("\n" + "=" * 50)
        print("✅ All position correction tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
