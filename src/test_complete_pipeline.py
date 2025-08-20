#!/usr/bin/env python3
"""
Complete Pipeline Integration Test

Tests the fully integrated spatially-aware layout pipeline with:
- Spatial awareness system
- Dependency-ordered 9-phase pipeline
- Inside-out space propagation
- Collision detection with spatial exclusion
- Element positioning with cut containment
"""

from typing import Dict, List, Any
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from egif_parser_dau import EGIFParser
from layout_phase_implementations import DependencyOrderedPipeline
from spatial_awareness_system import SpatialAwarenessSystem


def test_simple_egif():
    """Test pipeline with simple EGIF: *x (Human x)"""
    print("🧪 Testing Simple EGIF: *x (Human x)")
    
    egif = "*x (Human x)"
    parser = EGIFParser(egif)
    egi = parser.parse()
    
    print(f"   EGI parsed: V={len(egi.V)}, E={len(egi.E)}, area={len(egi.area)}")
    
    # Create pipeline engine
    pipeline = DependencyOrderedPipeline()
    
    # Generate layout
    try:
        result = pipeline.execute_pipeline(egi)
        print(f"   Pipeline completed, elements: {len(result.elements)}")
    except Exception as e:
        print(f"   Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        result = type('MockResult', (), {'elements': {}, 'layout_quality_score': 0.0})()
    
    success = len(result.elements) > 0 and result.layout_quality_score > 0
    print(f"   Success: {success}")
    if success:
        print(f"   Elements: {len(result.elements)}")
        for element_id, element in result.elements.items():
            print(f"      {element.element_type} {element_id}: {element.position} -> {element.bounds}")
        
        # Check spatial awareness
        try:
            spatial_report = engine.spatial_system.get_utilization_report()
            print(f"   Spatial System: Active with {len(spatial_report) if isinstance(spatial_report, dict) else 0} containers")
        except Exception as e:
            print(f"   Spatial System: {e}")
    else:
        print(f"   Layout failed - no elements generated")
    
    return result


def test_nested_cuts_egif():
    """Test pipeline with nested cuts: *x (Human x) ~[ (Mortal x) ]"""
    print("\n🧪 Testing Nested Cuts EGIF: *x (Human x) ~[ (Mortal x) ]")
    
    egif = "*x (Human x) ~[ (Mortal x) ]"
    parser = EGIFParser(egif)
    egi = parser.parse()
    
    # Create pipeline engine
    pipeline = DependencyOrderedPipeline()
    
    # Generate layout
    result = pipeline.execute_pipeline(egi)
    
    success = len(result.elements) > 0 and result.layout_quality_score > 0
    print(f"   Success: {success}")
    if success:
        print(f"   Elements: {len(result.elements)}")
        
        # Group elements by type
        cuts = [e for e in result.elements.values() if e.element_type == 'cut']
        predicates = [e for e in result.elements.values() if e.element_type == 'predicate']
        vertices = [e for e in result.elements.values() if e.element_type == 'vertex']
        
        print(f"      Cuts: {len(cuts)}")
        for cut in cuts:
            print(f"         {cut.element_id}: {cut.bounds}")
        
        print(f"      Predicates: {len(predicates)}")
        for pred in predicates:
            print(f"         {getattr(pred, 'display_name', pred.element_id)} in {pred.parent_area}: {pred.position}")
        
        print(f"      Vertices: {len(vertices)}")
        for vertex in vertices:
            print(f"         {getattr(vertex, 'display_name', vertex.element_id)} in {vertex.parent_area}: {vertex.position}")
        
        # Verify spatial exclusion - predicates should not overlap with cuts
        print(f"   Spatial Exclusion Check:")
        violations = check_spatial_exclusion_violations(result.elements)
        if violations:
            print(f"      ❌ {len(violations)} violations found:")
            for violation in violations:
                print(f"         {violation}")
        else:
            print(f"      ✅ No spatial exclusion violations")
        
        # Check spatial utilization
        spatial_report = engine.spatial_system.get_utilization_report()
        if spatial_report and isinstance(spatial_report, dict):
            print(f"   Spatial Utilization:")
            for container_id, utilization in spatial_report.items():
                if isinstance(utilization, (int, float)):
                    print(f"      {container_id}: {utilization:.1f}% utilized")
                else:
                    print(f"      {container_id}: {utilization}")
        else:
            print(f"   Layout failed - no elements generated")
    
    else:
        print(f"   Layout failed - no elements generated")
    
    return result


def test_complex_egif():
    """Test pipeline with complex graph: *x *y (Human x) (Loves x y) ~[ (Mortal x) (Happy y) ]"""
    print("\n🧪 Testing Complex EGIF: *x *y (Human x) (Loves x y) ~[ (Mortal x) (Happy y) ]")
    
    # Complex EGIF with multiple predicates and cuts
    egif_content = "*x *y (Human x) (Loves x y) ~[ (Mortal x) (Happy y) ]"
    parser = EGIFParser(egif_content)
    egi = parser.parse()
    
    # Create pipeline engine
    pipeline = DependencyOrderedPipeline()
    
    # Generate layout
    result = pipeline.execute_pipeline(egi)
    
    success = len(result.elements) > 0 and result.layout_quality_score > 0
    print(f"   Success: {success}")
    if success:
        print(f"   Elements: {len(result.elements)}")
        
        # Group elements by type and container
        elements_by_container = {}
        for element in result.elements.values():
            container = element.parent_area
            if container not in elements_by_container:
                elements_by_container[container] = []
            elements_by_container[container].append(element)
        
        print(f"   Elements by Container:")
        for container_id, elements in elements_by_container.items():
            print(f"      {container_id}:")
            for element in elements:
                display_name = getattr(element, 'display_name', element.element_id)
                print(f"         {element.element_type} {display_name}: {element.position}")
        
        # Check collision detection
        print(f"   Collision Check:")
        collisions = check_element_collisions(result.elements)
        if collisions:
            print(f"      ❌ {len(collisions)} collisions found:")
            for collision in collisions:
                print(f"         {collision}")
        else:
            print(f"      ✅ No element collisions")
        
        # Check pipeline status
        status = engine.get_pipeline_status()
        print(f"   Pipeline Status:")
        print(f"      Completed Phases: {len(status['completed_phases'])}")
        for phase in status['completed_phases']:
            print(f"         ✅ {phase}")
        
    else:
        print(f"   Layout failed - no elements generated")
    
    return result


def check_spatial_exclusion_violations(elements: Dict[str, Any]) -> List[str]:
    """Check for spatial exclusion violations (parent elements overlapping child cuts)."""
    violations = []
    
    cuts = [e for e in elements.values() if e.element_type == 'cut']
    non_cuts = [e for e in elements.values() if e.element_type != 'cut']
    
    for cut in cuts:
        for element in non_cuts:
            # Check if element is in parent of this cut and overlaps
            if element.parent_area != cut.element_id and bounds_overlap(element.bounds, cut.bounds):
                # This could be a spatial exclusion violation
                if is_parent_child_relationship(element.parent_area, cut.element_id):
                    violations.append(f"{element.element_type} {element.element_id} overlaps child cut {cut.element_id}")
    
    return violations


def check_element_collisions(elements: Dict[str, Any]) -> List[str]:
    """Check for element collisions within the same container."""
    collisions = []
    
    # Group elements by container
    elements_by_container = {}
    for element in elements.values():
        container = element.parent_area
        if container not in elements_by_container:
            elements_by_container[container] = []
        elements_by_container[container].append(element)
    
    # Check for collisions within each container
    for container_id, container_elements in elements_by_container.items():
        for i, elem1 in enumerate(container_elements):
            for j, elem2 in enumerate(container_elements[i+1:], i+1):
                if bounds_overlap(elem1.bounds, elem2.bounds):
                    collisions.append(f"{elem1.element_type} {elem1.element_id} overlaps {elem2.element_type} {elem2.element_id} in {container_id}")
    
    return collisions


def bounds_overlap(bounds1, bounds2) -> bool:
    """Check if two bounding rectangles overlap."""
    x1_min, y1_min, x1_max, y1_max = bounds1
    x2_min, y2_min, x2_max, y2_max = bounds2
    
    return not (x1_max <= x2_min or x2_max <= x1_min or 
               y1_max <= y2_min or y2_max <= y1_min)


def is_parent_child_relationship(parent_id: str, child_id: str) -> bool:
    """Check if there's a parent-child relationship between containers."""
    # Simplified check - in real implementation would traverse hierarchy
    return parent_id != child_id


def test_incremental_updates():
    """Test incremental updates and spatial change propagation."""
    print("\n🧪 Testing Incremental Updates")
    
    egif = "*x (Human x)"
    parser = EGIFParser(egif)
    egi = parser.parse()
    
    # Create pipeline engine
    pipeline = DependencyOrderedPipeline()
    
    # Generate initial layout
    initial_result = pipeline.execute_pipeline(egi)
    initial_success = len(initial_result.elements) > 0 and initial_result.layout_quality_score > 0
    print(f"   Initial Layout: {initial_success}")
    
    if initial_success:
        # Test spatial change propagation
        from spatial_constraint_integration import SpatialChangePropagatior
        
        propagator = SpatialChangePropagatior(pipeline.spatial_system)
        
        # Simulate element addition
        from layout_types import LayoutElement
        from layout_utilities import ElementDimensions
        
        new_element = LayoutElement(
            element_id="new_predicate",
            element_type='predicate',
            position=(200, 100),
            bounds=(180, 85, 220, 115),
            parent_area='sheet'
        )
        
        affected_containers = propagator.handle_element_addition(new_element)
        print(f"   Element Addition Affected: {len(affected_containers)} containers")
        for container in affected_containers:
            print(f"      {container}")
        
        # Test spatial utilization after change
        spatial_report = engine.spatial_system.get_utilization_report()
        print(f"   Updated Spatial Utilization:")
        for container_id, utilization in spatial_report.items():
            if isinstance(utilization, (int, float)):
                print(f"      {container_id}: {utilization:.1f}% utilized")
            elif isinstance(utilization, dict) and 'utilization_ratio' in utilization:
                print(f"      {container_id}: {utilization['utilization_ratio']*100:.1f}% utilized")
            else:
                print(f"      {container_id}: {utilization}")


if __name__ == "__main__":
    print("🚀 Complete Pipeline Integration Test")
    print("=" * 50)
    
    # Test simple case
    simple_result = test_simple_egif()
    
    # Test nested cuts
    nested_result = test_nested_cuts_egif()
    
    # Test complex case
    complex_result = test_complex_egif()
    
    # Test incremental updates
    test_incremental_updates()
    
    print("\n" + "=" * 50)
    print("✅ Complete Pipeline Integration Test Finished")
    
    # Summary
    results = [simple_result, nested_result, complex_result]
    successful = sum(1 for r in results if len(r.elements) > 0 and r.layout_quality_score > 0)
    print(f"📊 Results: {successful}/{len(results)} tests passed")
    
    if successful == len(results):
        print("🎉 All tests passed! Pipeline is functioning correctly.")
    else:
        print("⚠️  Some tests failed. Check error messages above.")
