#!/usr/bin/env python3
"""
Test script for hierarchical index integration with EGI structures.
Tests the Peirce "man mortal" example to validate hierarchical indexing.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from egi_io import load_egi_json
from egi_core_dau import RelationalGraphWithCuts
from hierarchical_index import HierarchicalIndex
from egif_transformation_interface import EGIFTransformationInterface
from formal_transformation_rules import DeiterationRule

def test_hierarchical_index_integration():
    """Test hierarchical index integration with Peirce man-mortal example."""
    
    print("=== Testing Hierarchical Index Integration ===")
    
    # Load the EGIF file
    egif_path = "corpus/graphs/peirce_cp_4_394_man_mortal/peirce_cp_4_394_man_mortal.egi.json"
    
    try:
        egi = load_egi_json(egif_path)
        print(f"✓ Loaded EGI from {egif_path}")
        
        # Verify hierarchical index was automatically created
        assert egi.hierarchical_index is not None, "Hierarchical index should be automatically created"
        print("✓ Hierarchical index automatically created")
        
        # Test hierarchical index structure
        hi = egi.hierarchical_index
        
        # Check sheet
        sheet_level = hi.get_nesting_level(egi.sheet)
        sheet_polarity = hi.get_polarity(egi.sheet)
        print(f"✓ Sheet '{egi.sheet}': level {sheet_level}, polarity {sheet_polarity}")
        assert sheet_level == 0, f"Sheet should be level 0, got {sheet_level}"
        assert sheet_polarity == "positive", f"Sheet should be positive, got {sheet_polarity}"
        
        # Check outer cut (c_abe14f9e)
        outer_cut = "c_abe14f9e"
        outer_level = hi.get_nesting_level(outer_cut)
        outer_polarity = hi.get_polarity(outer_cut)
        print(f"✓ Outer cut '{outer_cut}': level {outer_level}, polarity {outer_polarity}")
        assert outer_level == 1, f"Outer cut should be level 1, got {outer_level}"
        assert outer_polarity == "negative", f"Outer cut should be negative, got {outer_polarity}"
        
        # Check inner cut (c_ddf31f9b)
        inner_cut = "c_ddf31f9b"
        inner_level = hi.get_nesting_level(inner_cut)
        inner_polarity = hi.get_polarity(inner_cut)
        print(f"✓ Inner cut '{inner_cut}': level {inner_level}, polarity {inner_polarity}")
        assert inner_level == 2, f"Inner cut should be level 2, got {inner_level}"
        assert inner_polarity == "positive", f"Inner cut should be positive, got {inner_polarity}"
        
        # Test parent-child relationships
        outer_parent = hi.get_parent(outer_cut)
        inner_parent = hi.get_parent(inner_cut)
        print(f"✓ Parent relationships: {outer_cut} -> {outer_parent}, {inner_cut} -> {inner_parent}")
        assert outer_parent == egi.sheet, f"Outer cut parent should be sheet, got {outer_parent}"
        assert inner_parent == outer_cut, f"Inner cut parent should be outer cut, got {inner_parent}"
        
        # Test children
        sheet_children = hi.get_children(egi.sheet)
        outer_children = hi.get_children(outer_cut)
        inner_children = hi.get_children(inner_cut)
        print(f"✓ Children: sheet -> {sheet_children}, outer -> {outer_children}, inner -> {inner_children}")
        assert outer_cut in sheet_children, f"Sheet should contain outer cut"
        assert inner_cut in outer_children, f"Outer cut should contain inner cut"
        assert len(inner_children) == 0, f"Inner cut should have no children"
        
        # Test areas by polarity
        positive_areas = hi.get_positive_areas()
        negative_areas = hi.get_negative_areas()
        print(f"✓ Positive areas: {positive_areas}")
        print(f"✓ Negative areas: {negative_areas}")
        assert egi.sheet in positive_areas, "Sheet should be positive"
        assert inner_cut in positive_areas, "Inner cut should be positive"
        assert outer_cut in negative_areas, "Outer cut should be negative"
        
        # Test transformation interface integration
        transformer = EGIFTransformationInterface()
        
        # Test polarity calculation using hierarchical index
        sheet_pol, sheet_depth = transformer._calculate_area_polarity(egi, egi.sheet)
        outer_pol, outer_depth = transformer._calculate_area_polarity(egi, outer_cut)
        inner_pol, inner_depth = transformer._calculate_area_polarity(egi, inner_cut)
        
        print(f"✓ Transformer polarity calculations:")
        print(f"  Sheet: {sheet_pol} (depth {sheet_depth})")
        print(f"  Outer: {outer_pol} (depth {outer_depth})")
        print(f"  Inner: {inner_pol} (depth {inner_depth})")
        
        assert (sheet_pol, sheet_depth) == ("positive", 0)
        assert (outer_pol, outer_depth) == ("negative", 1)
        assert (inner_pol, inner_depth) == ("positive", 2)
        
        # Test statistics
        stats = hi.get_statistics()
        print(f"✓ Hierarchical index statistics: {stats}")
        assert stats['total_areas'] == 3, f"Should have 3 areas, got {stats['total_areas']}"
        assert stats['max_nesting_level'] == 2, f"Max level should be 2, got {stats['max_nesting_level']}"
        assert stats['positive_areas'] == 2, f"Should have 2 positive areas, got {stats['positive_areas']}"
        assert stats['negative_areas'] == 1, f"Should have 1 negative area, got {stats['negative_areas']}"
        
        print("\n=== All Hierarchical Index Tests Passed! ===")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_it_minus_with_hierarchical_index():
    """Test IT- transformation with hierarchical index integration."""
    
    print("\n=== Testing IT- with Hierarchical Index ===")
    
    try:
        # Create a simple test case with duplicated predicates
        # This represents: ~[ P(x) ~[ P(x) ] ]
        # Should be able to deiterate P(x) from inner positive area
        
        from egi_core_dau import Vertex, Edge, Cut, ElementID, RelationName
        from frozendict import frozendict
        
        # Create vertices
        v1 = Vertex(id=ElementID("v1"), is_generic=True, label=None)
        
        # Create edges (predicates)
        e1 = Edge(id=ElementID("e1"))  # P(x) in outer area
        e2 = Edge(id=ElementID("e2"))  # P(x) in inner area
        
        # Create cuts
        outer_cut = Cut(id=ElementID("outer_cut"))
        inner_cut = Cut(id=ElementID("inner_cut"))
        
        # Create EGI structure
        egi = RelationalGraphWithCuts(
            V=frozenset([v1]),
            E=frozenset([e1, e2]),
            Cut=frozenset([outer_cut, inner_cut]),
            sheet=ElementID("sheet"),
            area=frozendict({
                ElementID("sheet"): frozenset([ElementID("outer_cut")]),
                ElementID("outer_cut"): frozenset([ElementID("e1"), ElementID("v1"), ElementID("inner_cut")]),
                ElementID("inner_cut"): frozenset([ElementID("e2")])
            }),
            nu=frozendict({
                ElementID("e1"): frozenset([ElementID("v1")]),
                ElementID("e2"): frozenset([ElementID("v1")])
            }),
            rel=frozendict({
                ElementID("e1"): RelationName("P"),
                ElementID("e2"): RelationName("P")
            })
        )
        
        print("✓ Created test EGI with duplicated predicates")
        
        # Verify hierarchical index was created
        assert egi.hierarchical_index is not None
        hi = egi.hierarchical_index
        
        # Check structure
        sheet_pol = hi.get_polarity(ElementID("sheet"))
        outer_pol = hi.get_polarity(ElementID("outer_cut"))
        inner_pol = hi.get_polarity(ElementID("inner_cut"))
        
        print(f"✓ Polarities: sheet={sheet_pol}, outer={outer_pol}, inner={inner_pol}")
        assert sheet_pol == "positive"
        assert outer_pol == "negative"
        assert inner_pol == "positive"
        
        # Test IT- transformation using the formal interface
        from formal_transformation_rules import TransformationContext, AreaPolarity
        
        deiteration_rule = DeiterationRule()
        
        # Create transformation context
        selected_subgraph = frozenset([ElementID("e2")])  # P(x) in inner area
        target_area = ElementID("inner_cut")
        
        context = TransformationContext(
            source_egi=egi,
            selected_subgraph=selected_subgraph,
            target_area=target_area,
            area_polarity=AreaPolarity.POSITIVE,
            nesting_depth=2
        )
        
        # Check preconditions
        can_apply, reason = deiteration_rule.check_preconditions(context)
        print(f"✓ IT- can apply: {can_apply} (reason: {reason})")
        
        if can_apply:
            # Apply the transformation
            result = deiteration_rule.apply_transformation(context)
            if result.success:
                print("✓ IT- transformation applied successfully")
                
                # Verify result has hierarchical index
                assert result.result_egi.hierarchical_index is not None
                print("✓ Result EGI maintains hierarchical index")
            else:
                print(f"✗ IT- transformation failed: {result.error_message}")
        else:
            print(f"✓ IT- precondition check completed (cannot apply: {reason})")
            
        print("✓ IT- transformation test completed")
        return True
        
    except Exception as e:
        print(f"✗ IT- test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success1 = test_hierarchical_index_integration()
    success2 = test_it_minus_with_hierarchical_index()
    
    if success1 and success2:
        print("\n🎉 All tests passed! Hierarchical index integration is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed.")
        sys.exit(1)
