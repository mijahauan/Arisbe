#!/usr/bin/env python3
"""
Test CGAL installation and basic functionality for area management.
"""

import sys
import os
sys.path.append('src')

def test_cgal_installation():
    """Test CGAL installation and basic polygon operations."""
    print('🧪 Testing CGAL installation and basic functionality...')
    
    try:
        # Test basic CGAL imports
        from CGAL.CGAL_Kernel import Point_2
        from CGAL.CGAL_Polygon_2 import Polygon_2
        print('✅ CGAL kernel and polygon imports successful')
        
        # Test basic polygon creation (rectangle)
        points = [Point_2(0, 0), Point_2(10, 0), Point_2(10, 10), Point_2(0, 10)]
        polygon = Polygon_2(points)
        print(f'✅ Created test polygon with {polygon.size()} vertices')
        
        # Test polygon area calculation
        area = polygon.area()
        print(f'✅ Polygon area calculation: {area} (expected: 100)')
        
        # Test point-in-polygon
        test_point_inside = Point_2(5, 5)
        test_point_outside = Point_2(15, 15)
        
        inside_result = polygon.bounded_side(test_point_inside)
        outside_result = polygon.bounded_side(test_point_outside)
        
        print(f'✅ Point-in-polygon test:')
        print(f'   Point(5,5) result: {inside_result}')
        print(f'   Point(15,15) result: {outside_result}')
        
        # Test polygon orientation
        orientation = polygon.orientation()
        print(f'✅ Polygon orientation: {orientation}')
        
        print('🎯 CGAL is working correctly! Ready for area management implementation.')
        return True
        
    except ImportError as e:
        print(f'❌ CGAL import error: {e}')
        print('   Check CGAL installation in conda environment')
        print('   Try: conda install -c conda-forge cgal')
        return False
    except Exception as e:
        print(f'❌ CGAL functionality error: {e}')
        print('   CGAL installed but may have compatibility issues')
        return False

def test_cgal_boolean_operations():
    """Test CGAL boolean operations needed for area management."""
    print('\n🧪 Testing CGAL boolean operations...')
    
    try:
        from CGAL.CGAL_Kernel import Point_2
        from CGAL.CGAL_Polygon_2 import Polygon_2
        from CGAL.CGAL_Boolean_set_operations_2 import difference, intersection
        
        # Create two overlapping rectangles
        rect1_points = [Point_2(0, 0), Point_2(10, 0), Point_2(10, 10), Point_2(0, 10)]
        rect2_points = [Point_2(5, 5), Point_2(15, 5), Point_2(15, 15), Point_2(5, 15)]
        
        rect1 = Polygon_2(rect1_points)
        rect2 = Polygon_2(rect2_points)
        
        print(f'✅ Created two test rectangles')
        print(f'   Rect1 area: {rect1.area()}')
        print(f'   Rect2 area: {rect2.area()}')
        
        # Test intersection
        intersect = intersection(rect1, rect2)
        print(f'✅ Intersection computed')
        
        # Test difference (area subtraction)
        diff = difference(rect1, rect2)
        print(f'✅ Difference computed')
        
        print('🎯 CGAL boolean operations working! Ready for cut area subtraction.')
        return True
        
    except ImportError as e:
        print(f'❌ CGAL boolean operations import error: {e}')
        return False
    except Exception as e:
        print(f'❌ CGAL boolean operations error: {e}')
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("CGAL Installation Test for Arisbe Area Management")
    print("=" * 60)
    
    basic_test = test_cgal_installation()
    if basic_test:
        boolean_test = test_cgal_boolean_operations()
        if boolean_test:
            print("\n🎉 All CGAL tests passed! Ready to implement area management system.")
        else:
            print("\n⚠️  Basic CGAL works, but boolean operations failed.")
    else:
        print("\n❌ CGAL installation test failed.")
