#!/usr/bin/env python3
"""
Test Shapely installation and functionality for area management.
"""

import sys
import os
sys.path.append('src')

def test_shapely_basic():
    """Test basic Shapely functionality."""
    print('🧪 Testing Shapely basic functionality...')
    
    try:
        from shapely.geometry import Polygon, Point
        from shapely.ops import unary_union
        
        print('✅ Shapely imports successful')
        
        # Test basic polygon creation
        coords = [(0, 0), (10, 0), (10, 10), (0, 10)]
        polygon = Polygon(coords)
        
        print(f'✅ Created polygon with area: {polygon.area}')
        print(f'✅ Polygon is valid: {polygon.is_valid}')
        
        # Test point-in-polygon
        point_inside = Point(5, 5)
        point_outside = Point(15, 15)
        
        print(f'✅ Point (5,5) inside polygon: {polygon.contains(point_inside)}')
        print(f'✅ Point (15,15) inside polygon: {polygon.contains(point_outside)}')
        
        return True
        
    except ImportError as e:
        print(f'❌ Shapely import error: {e}')
        return False
    except Exception as e:
        print(f'❌ Shapely functionality error: {e}')
        return False

def test_shapely_boolean_operations():
    """Test Shapely boolean operations for area management."""
    print('\n🧪 Testing Shapely boolean operations...')
    
    try:
        from shapely.geometry import Polygon
        from shapely.ops import unary_union
        
        # Create two overlapping rectangles (simulating cuts)
        rect1 = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        rect2 = Polygon([(5, 5), (15, 5), (15, 15), (5, 15)])
        
        print(f'✅ Rectangle 1 area: {rect1.area}')
        print(f'✅ Rectangle 2 area: {rect2.area}')
        
        # Test intersection
        intersection = rect1.intersection(rect2)
        print(f'✅ Intersection area: {intersection.area}')
        
        # Test difference (area subtraction - key for cut management)
        difference = rect1.difference(rect2)
        print(f'✅ Difference area: {difference.area}')
        
        # Test union
        union = rect1.union(rect2)
        print(f'✅ Union area: {union.area}')
        
        # Test boundary relationships
        print(f'✅ Rectangles touch: {rect1.touches(rect2)}')
        print(f'✅ Rectangles intersect: {rect1.intersects(rect2)}')
        print(f'✅ Rectangles overlap: {rect1.overlaps(rect2)}')
        
        return True
        
    except Exception as e:
        print(f'❌ Boolean operations error: {e}')
        return False

def test_edge_cases():
    """Test edge cases relevant to EG area management."""
    print('\n🧪 Testing edge cases...')
    
    try:
        from shapely.geometry import Polygon, Point
        
        # Test touching boundaries (cuts sharing edges)
        cut1 = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
        cut2 = Polygon([(10, 0), (20, 0), (20, 10), (10, 10)])  # Shares edge
        
        print(f'✅ Adjacent cuts touch: {cut1.touches(cut2)}')
        print(f'✅ Adjacent cuts don\'t overlap: {not cut1.overlaps(cut2)}')
        
        # Test point on boundary
        boundary_point = Point(10, 5)  # On shared edge
        print(f'✅ Point on boundary - Cut1 contains: {cut1.contains(boundary_point)}')
        print(f'✅ Point on boundary - Cut2 contains: {cut2.contains(boundary_point)}')
        print(f'✅ Point on boundary - Distance to Cut1: {cut1.distance(boundary_point)}')
        
        # Test nested cuts
        outer_cut = Polygon([(0, 0), (20, 0), (20, 20), (0, 20)])
        inner_cut = Polygon([(5, 5), (15, 5), (15, 15), (5, 15)])
        
        available_area = outer_cut.difference(inner_cut)
        print(f'✅ Nested cuts - Available area: {available_area.area}')
        print(f'✅ Available area is valid: {available_area.is_valid}')
        
        return True
        
    except Exception as e:
        print(f'❌ Edge case testing error: {e}')
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Shapely Installation Test for Arisbe Area Management")
    print("=" * 60)
    
    basic_test = test_shapely_basic()
    if basic_test:
        boolean_test = test_shapely_boolean_operations()
        if boolean_test:
            edge_test = test_edge_cases()
            if edge_test:
                print("\n🎉 All Shapely tests passed! Ready to implement area management system.")
                print("🎯 Shapely provides robust geometric operations for EG area boundaries.")
            else:
                print("\n⚠️  Basic operations work, but edge cases need attention.")
        else:
            print("\n⚠️  Basic Shapely works, but boolean operations failed.")
    else:
        print("\n❌ Shapely installation test failed.")
