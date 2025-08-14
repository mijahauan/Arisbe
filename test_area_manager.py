#!/usr/bin/env python3
"""
Test the ShapelyAreaManager for EG area boundary management.
"""

import sys
sys.path.append('src')

from shapely_area_manager import ShapelyAreaManager, Rectangle

def test_area_manager_basic():
    """Test basic area manager functionality."""
    print('🧪 Testing ShapelyAreaManager basic functionality...')
    
    try:
        # Create area manager with canvas bounds
        canvas_bounds = (0, 0, 200, 200)
        manager = ShapelyAreaManager(canvas_bounds)
        
        print(f'✅ Created area manager with canvas bounds: {canvas_bounds}')
        print(f'✅ Sheet area created with ID: {manager.sheet_id}')
        
        # Test area hierarchy
        hierarchy = manager.get_area_hierarchy()
        print(f'✅ Area hierarchy: {len(hierarchy)} areas')
        
        return True
        
    except Exception as e:
        print(f'❌ Area manager basic test error: {e}')
        return False

def test_cut_creation():
    """Test cut area creation and validation."""
    print('\n🧪 Testing cut area creation...')
    
    try:
        manager = ShapelyAreaManager((0, 0, 200, 200))
        
        # Create a valid cut within the sheet
        cut1_bounds = (20, 20, 80, 80)
        cut1_id = manager.create_cut_area(manager.sheet_id, cut1_bounds)
        print(f'✅ Created cut1: {cut1_id} with bounds {cut1_bounds}')
        
        # Create another cut
        cut2_bounds = (100, 100, 180, 180)
        cut2_id = manager.create_cut_area(manager.sheet_id, cut2_bounds)
        print(f'✅ Created cut2: {cut2_id} with bounds {cut2_bounds}')
        
        # Create nested cut within cut1
        nested_cut_bounds = (30, 30, 70, 70)
        nested_id = manager.create_cut_area(cut1_id, nested_cut_bounds)
        print(f'✅ Created nested cut: {nested_id} within {cut1_id}')
        
        # Test invalid cut (outside bounds)
        try:
            invalid_cut = manager.create_cut_area(manager.sheet_id, (190, 190, 250, 250))
            print(f'❌ Should have failed: created invalid cut {invalid_cut}')
        except ValueError as e:
            print(f'✅ Correctly rejected invalid cut: {e}')
        
        # Check hierarchy
        hierarchy = manager.get_area_hierarchy()
        print(f'✅ Total areas after cuts: {len(hierarchy)}')
        
        return True
        
    except Exception as e:
        print(f'❌ Cut creation test error: {e}')
        return False

def test_available_space():
    """Test available space calculation."""
    print('\n🧪 Testing available space calculation...')
    
    try:
        manager = ShapelyAreaManager((0, 0, 100, 100))
        
        # Sheet available space should be full area
        sheet_space = manager.get_available_space(manager.sheet_id)
        print(f'✅ Sheet available space area: {sheet_space.area}')
        
        # Add a cut
        cut_id = manager.create_cut_area(manager.sheet_id, (20, 20, 80, 80))
        
        # Sheet available space should be reduced
        sheet_space_after = manager.get_available_space(manager.sheet_id)
        print(f'✅ Sheet space after cut: {sheet_space_after.area}')
        print(f'✅ Space reduction: {sheet_space.area - sheet_space_after.area}')
        
        # Cut available space should be its full area
        cut_space = manager.get_available_space(cut_id)
        print(f'✅ Cut available space: {cut_space.area}')
        
        return True
        
    except Exception as e:
        print(f'❌ Available space test error: {e}')
        return False

def test_element_placement():
    """Test element placement and validation."""
    print('\n🧪 Testing element placement...')
    
    try:
        manager = ShapelyAreaManager((0, 0, 100, 100))
        cut_id = manager.create_cut_area(manager.sheet_id, (20, 20, 80, 80))
        
        # Test valid placements
        valid_sheet_pos = (10, 10)  # In sheet, outside cut
        valid_cut_pos = (50, 50)   # Inside cut
        
        can_place_sheet = manager.can_place_element('elem1', valid_sheet_pos, manager.sheet_id)
        can_place_cut = manager.can_place_element('elem2', valid_cut_pos, cut_id)
        
        print(f'✅ Can place in sheet at {valid_sheet_pos}: {can_place_sheet}')
        print(f'✅ Can place in cut at {valid_cut_pos}: {can_place_cut}')
        
        # Actually place elements
        placed_sheet = manager.place_element('elem1', valid_sheet_pos, manager.sheet_id)
        placed_cut = manager.place_element('elem2', valid_cut_pos, cut_id)
        
        print(f'✅ Placed elem1 in sheet: {placed_sheet}')
        print(f'✅ Placed elem2 in cut: {placed_cut}')
        
        # Test invalid placement (element in cut area but assigned to sheet)
        invalid_pos = (50, 50)  # Inside cut
        can_place_invalid = manager.can_place_element('elem3', invalid_pos, manager.sheet_id)
        print(f'✅ Can place in sheet at cut position {invalid_pos}: {can_place_invalid}')
        
        # Test position optimization
        desired_pos = (25, 25)  # On cut boundary
        optimized_pos = manager.optimize_position_in_area('elem4', desired_pos, manager.sheet_id)
        print(f'✅ Optimized position for {desired_pos} in sheet: {optimized_pos}')
        
        return True
        
    except Exception as e:
        print(f'❌ Element placement test error: {e}')
        return False

def test_validation():
    """Test area and placement validation."""
    print('\n🧪 Testing validation...')
    
    try:
        manager = ShapelyAreaManager((0, 0, 100, 100))
        cut_id = manager.create_cut_area(manager.sheet_id, (20, 20, 80, 80))
        
        # Place some elements
        manager.place_element('elem1', (10, 10), manager.sheet_id)
        manager.place_element('elem2', (50, 50), cut_id)
        
        # Validate all placements
        errors = manager.validate_all_placements()
        print(f'✅ Validation errors: {len(errors)}')
        if errors:
            for error in errors:
                print(f'   ⚠️  {error}')
        
        # Check final hierarchy
        hierarchy = manager.get_area_hierarchy()
        print(f'✅ Final hierarchy:')
        for area_id, info in hierarchy.items():
            print(f'   {area_id}: {info["type"]}, elements: {info["elements"]}')
        
        return True
        
    except Exception as e:
        print(f'❌ Validation test error: {e}')
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("ShapelyAreaManager Test Suite")
    print("=" * 60)
    
    tests = [
        test_area_manager_basic,
        test_cut_creation,
        test_available_space,
        test_element_placement,
        test_validation
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        else:
            break
    
    print(f"\n🎯 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All area manager tests passed! Ready for EGDF integration.")
    else:
        print("❌ Some tests failed. Check implementation before proceeding.")
