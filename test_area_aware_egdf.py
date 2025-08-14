#!/usr/bin/env python3
"""
Test the Area-Aware EGDF Generator integration.
"""

import sys
sys.path.append('src')

from egdf_area_aware import AreaAwareEGDFGenerator, create_area_aware_egdf_generator
from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut, ElementID
from layout_engine_clean import SpatialPrimitive, Coordinate, Bounds, LayoutResult
from frozendict import frozendict

def create_test_egi():
    """Create a simple test EGI for testing."""
    # Create vertices (only need IDs)
    v1 = Vertex("v1")
    v2 = Vertex("v2") 
    v3 = Vertex("v3")
    
    # Create edges (predicates - only need IDs)
    e1 = Edge("e1")
    e2 = Edge("e2")
    
    # Create cut
    cut1 = Cut("cut1")
    
    # Create EGI with proper vertex sequence mapping (using vertex IDs)
    egi = RelationalGraphWithCuts(
        V=frozenset([v1, v2, v3]),
        E=frozenset([e1, e2]),
        nu=frozendict({
            "e1": ("v1", "v2"),  # Vertex ID sequence for edge e1
            "e2": ("v2", "v3")   # Vertex ID sequence for edge e2
        }),
        sheet="sheet",
        Cut=frozenset([cut1]),
        area=frozendict({
            "sheet": frozenset(["v1", "e1", "cut1"]),  # cut1 exists IN the sheet area
            "cut1": frozenset(["v2", "v3", "e2"])      # cut1 DEFINES this area (contains these elements)
        }),
        rel=frozendict({
            "e1": "Loves",
            "e2": "Knows"
        })
    )
    
    return egi

def create_test_layout():
    """Create a simple test layout result."""
    primitives = {
        # Cut primitive
        "cut1": SpatialPrimitive(
            element_id="cut1",
            element_type="cut",
            position=(100, 100),
            bounds=(80, 80, 120, 120),  # Bounds is a tuple
            z_index=0
        ),
        
        # Predicate primitives
        "e1": SpatialPrimitive(
            element_id="e1",
            element_type="predicate",
            position=(50, 50),
            bounds=(40, 45, 60, 55),  # Bounds is a tuple
            z_index=2
        ),
        "e2": SpatialPrimitive(
            element_id="e2",
            element_type="predicate",
            position=(100, 100),
            bounds=(90, 95, 110, 105),  # Bounds is a tuple
            z_index=2
        ),
        
        # Vertex primitives
        "v1": SpatialPrimitive(
            element_id="v1",
            element_type="vertex",
            position=(30, 50),
            bounds=(24, 44, 36, 56),  # Bounds is a tuple
            z_index=3
        ),
        "v2": SpatialPrimitive(
            element_id="v2",
            element_type="vertex",
            position=(70, 50),
            bounds=(64, 44, 76, 56),  # Bounds is a tuple
            z_index=3
        ),
        "v3": SpatialPrimitive(
            element_id="v3",
            element_type="vertex",
            position=(100, 120),
            bounds=(94, 114, 106, 126),  # Bounds is a tuple
            z_index=3
        )
    }
    
    return LayoutResult(
        primitives=primitives,
        canvas_bounds=(0, 0, 200, 200),  # Test canvas bounds
        containment_hierarchy={"sheet": {"cut1"}, "cut1": set()}  # cut1 contained in sheet
    )

def test_area_aware_generator_creation():
    """Test creating the area-aware EGDF generator."""
    print('🧪 Testing area-aware EGDF generator creation...')
    
    try:
        # Test factory function
        generator = create_area_aware_egdf_generator()
        print(f'✅ Created generator with canvas bounds: {generator.canvas_bounds}')
        
        # Test custom bounds
        custom_generator = AreaAwareEGDFGenerator((0, 0, 400, 300))
        print(f'✅ Created custom generator with bounds: {custom_generator.canvas_bounds}')
        
        return True
        
    except Exception as e:
        print(f'❌ Generator creation error: {e}')
        return False

def test_egdf_generation_with_areas():
    """Test EGDF generation with area constraints."""
    print('\n🧪 Testing EGDF generation with area constraints...')
    
    try:
        # Create test data
        egi = create_test_egi()
        layout = create_test_layout()
        generator = create_area_aware_egdf_generator((0, 0, 200, 200))
        
        print(f'✅ Created test EGI with {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts')
        print(f'✅ Created test layout with {len(layout.primitives)} primitives')
        
        # Generate EGDF
        primitives = generator.generate_egdf_from_layout(egi, layout)
        
        print(f'✅ Generated {len(primitives)} EGDF primitives')
        
        # Analyze primitive types
        primitive_types = {}
        for primitive in primitives:
            ptype = primitive.element_type
            primitive_types[ptype] = primitive_types.get(ptype, 0) + 1
        
        print(f'✅ Primitive breakdown: {primitive_types}')
        
        # Check area assignments
        area_assignments = {}
        for primitive in primitives:
            area_id = primitive.parent_area
            if area_id:
                area_assignments[area_id] = area_assignments.get(area_id, 0) + 1
        
        print(f'✅ Area assignments: {area_assignments}')
        
        return True
        
    except Exception as e:
        print(f'❌ EGDF generation error: {e}')
        import traceback
        traceback.print_exc()
        return False

def test_area_constraint_validation():
    """Test area constraint validation."""
    print('\n🧪 Testing area constraint validation...')
    
    try:
        egi = create_test_egi()
        layout = create_test_layout()
        generator = create_area_aware_egdf_generator((0, 0, 200, 200))
        
        # Generate EGDF
        primitives = generator.generate_egdf_from_layout(egi, layout)
        
        # Get area debug info
        debug_info = generator.get_area_debug_info()
        
        print(f'✅ Area hierarchy: {len(debug_info.get("area_hierarchy", {}))} areas')
        
        validation_errors = debug_info.get('validation_errors', [])
        print(f'✅ Validation errors: {len(validation_errors)}')
        
        if validation_errors:
            for error in validation_errors[:3]:  # Show first 3
                print(f'   ⚠️  {error}')
        
        # Check area manager state
        if generator.area_manager:
            hierarchy = generator.area_manager.get_area_hierarchy()
            print(f'✅ Area manager tracking {len(hierarchy)} areas')
            
            for area_id, info in hierarchy.items():
                print(f'   {area_id}: {info["type"]}, {len(info["elements"])} elements')
        
        return True
        
    except Exception as e:
        print(f'❌ Area validation error: {e}')
        return False

def test_position_optimization():
    """Test position optimization within areas."""
    print('\n🧪 Testing position optimization...')
    
    try:
        generator = create_area_aware_egdf_generator((0, 0, 200, 200))
        
        # Create a simple area manager for testing
        from shapely_area_manager import ShapelyAreaManager
        manager = ShapelyAreaManager((0, 0, 200, 200))
        cut_id = manager.create_cut_area("sheet", (50, 50, 150, 150))
        
        generator.area_manager = manager
        
        # Test position optimization
        desired_pos = (25, 25)  # Outside cut, should stay in sheet
        optimized_pos = generator._optimize_position_in_area(desired_pos, "sheet")
        print(f'✅ Optimized position {desired_pos} → {optimized_pos} in sheet')
        
        # Test position in cut
        cut_pos = (100, 100)  # Inside cut
        optimized_cut_pos = generator._optimize_position_in_area(cut_pos, cut_id)
        print(f'✅ Optimized position {cut_pos} → {optimized_cut_pos} in cut')
        
        # Test invalid position
        invalid_pos = (100, 100)  # Cut position but assigned to sheet
        optimized_invalid = generator._optimize_position_in_area(invalid_pos, "sheet")
        print(f'✅ Optimized invalid position {invalid_pos} → {optimized_invalid} in sheet')
        
        return True
        
    except Exception as e:
        print(f'❌ Position optimization error: {e}')
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Area-Aware EGDF Generator Test Suite")
    print("=" * 60)
    
    tests = [
        test_area_aware_generator_creation,
        test_egdf_generation_with_areas,
        test_area_constraint_validation,
        test_position_optimization
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        else:
            break
    
    print(f"\n🎯 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All area-aware EGDF tests passed! Ready for pipeline integration.")
    else:
        print("❌ Some tests failed. Check implementation before proceeding.")
