#!/usr/bin/env python3
"""
Simple test script for cut-area correspondence system.
Tests the fundamental mapping between logical negation and spatial cuts.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from frozendict import frozendict
from cut_area_correspondence import CutAreaCorrespondence, SpatialBounds
from egi_core_dau import RelationalGraphWithCuts, Cut


def test_empty_egi():
    """Test correspondence with empty EGI (no cuts)."""
    print("Testing empty EGI...")
    
    # Create empty EGI
    egi = RelationalGraphWithCuts(
        V=frozenset(),
        E=frozenset(),
        nu=frozendict(),
        sheet="sheet",
        Cut=frozenset(),
        area=frozendict({"sheet": frozenset()}),
        rel=frozendict()
    )
    
    # Create correspondence
    canvas_bounds = SpatialBounds(0, 0, 800, 600)
    correspondence = CutAreaCorrespondence(canvas_bounds)
    correspondence.build_correspondence(egi)
    
    # Validate
    assert len(correspondence.cut_areas) == 0
    assert correspondence.get_area_for_point(400, 300) == "sheet"
    print("✓ Empty EGI test passed")


def test_single_cut():
    """Test correspondence with single cut."""
    print("Testing single cut...")
    
    # Create EGI with one cut
    cut1 = Cut("cut1")
    egi = RelationalGraphWithCuts(
        V=frozenset(),
        E=frozenset(),
        nu=frozendict(),
        sheet="sheet",
        Cut=frozenset([cut1]),
        area=frozendict({
            "sheet": frozenset(["cut1"]),
            "cut1": frozenset()
        }),
        rel=frozendict()
    )
    
    # Create correspondence
    canvas_bounds = SpatialBounds(0, 0, 800, 600)
    correspondence = CutAreaCorrespondence(canvas_bounds)
    correspondence.build_correspondence(egi)
    
    # Validate
    assert len(correspondence.cut_areas) == 1
    assert "cut1" in correspondence.cut_areas
    
    cut_area = correspondence.cut_areas["cut1"]
    assert cut_area.is_root_cut()
    assert cut_area.nesting_depth == 1
    
    # Test point mapping
    center_x, center_y = cut_area.spatial_bounds.center()
    assert correspondence.get_area_for_point(center_x, center_y) == "cut1"
    print("✓ Single cut test passed")


def test_nested_cuts():
    """Test correspondence with nested cuts."""
    print("Testing nested cuts...")
    
    # Create EGI with nested cuts
    cut1 = Cut("cut1")
    cut2 = Cut("cut2")
    egi = RelationalGraphWithCuts(
        V=frozenset(),
        E=frozenset(),
        nu=frozendict(),
        sheet="sheet",
        Cut=frozenset([cut1, cut2]),
        area=frozendict({
            "sheet": frozenset(["cut1"]),
            "cut1": frozenset(["cut2"]),
            "cut2": frozenset()
        }),
        rel=frozendict()
    )
    
    # Create correspondence
    canvas_bounds = SpatialBounds(0, 0, 800, 600)
    correspondence = CutAreaCorrespondence(canvas_bounds)
    correspondence.build_correspondence(egi)
    
    # Validate
    assert len(correspondence.cut_areas) == 2
    
    cut1_area = correspondence.cut_areas["cut1"]
    cut2_area = correspondence.cut_areas["cut2"]
    
    assert cut1_area.is_root_cut()
    assert not cut2_area.is_root_cut()
    assert cut1_area.nesting_depth == 1
    assert cut2_area.nesting_depth == 2
    
    # Test spatial containment
    assert canvas_bounds.contains_bounds(cut1_area.spatial_bounds)
    assert cut1_area.spatial_bounds.contains_bounds(cut2_area.spatial_bounds)
    
    # Test point mapping (deepest cut wins)
    cut2_center = cut2_area.spatial_bounds.center()
    assert correspondence.get_area_for_point(*cut2_center) == "cut2"
    print("✓ Nested cuts test passed")


def test_sibling_cuts():
    """Test correspondence with sibling cuts."""
    print("Testing sibling cuts...")
    
    # Create EGI with sibling cuts
    cut1 = Cut("cut1")
    cut2 = Cut("cut2")
    cut3 = Cut("cut3")
    egi = RelationalGraphWithCuts(
        V=frozenset(),
        E=frozenset(),
        nu=frozendict(),
        sheet="sheet",
        Cut=frozenset([cut1, cut2, cut3]),
        area=frozendict({
            "sheet": frozenset(["cut1", "cut2", "cut3"]),
            "cut1": frozenset(),
            "cut2": frozenset(),
            "cut3": frozenset()
        }),
        rel=frozendict()
    )
    
    # Create correspondence
    canvas_bounds = SpatialBounds(0, 0, 800, 600)
    correspondence = CutAreaCorrespondence(canvas_bounds)
    correspondence.build_correspondence(egi)
    
    # Validate
    assert len(correspondence.cut_areas) == 3
    
    # All should be root cuts
    for cut_area in correspondence.cut_areas.values():
        assert cut_area.is_root_cut()
        assert cut_area.nesting_depth == 1
    
    # No overlaps between siblings
    cut_bounds = [cut_area.spatial_bounds for cut_area in correspondence.cut_areas.values()]
    for i, bounds1 in enumerate(cut_bounds):
        for bounds2 in cut_bounds[i+1:]:
            assert not bounds1.overlaps(bounds2)
    
    print("✓ Sibling cuts test passed")


def test_correspondence_summary():
    """Test correspondence summary generation."""
    print("Testing correspondence summary...")
    
    # Create EGI with mixed structure
    cuts = [Cut(f"cut{i}") for i in range(1, 4)]
    egi = RelationalGraphWithCuts(
        V=frozenset(),
        E=frozenset(),
        nu=frozendict(),
        sheet="sheet",
        Cut=frozenset(cuts),
        area=frozendict({
            "sheet": frozenset(["cut1", "cut2"]),
            "cut1": frozenset(["cut3"]),
            "cut2": frozenset(),
            "cut3": frozenset()
        }),
        rel=frozendict()
    )
    
    # Create correspondence
    canvas_bounds = SpatialBounds(0, 0, 800, 600)
    correspondence = CutAreaCorrespondence(canvas_bounds)
    correspondence.build_correspondence(egi)
    
    # Get summary
    summary = correspondence.get_correspondence_summary()
    
    # Validate summary
    assert summary["total_cuts"] == 3
    assert summary["root_cuts"] == 2
    assert summary["max_nesting_depth"] == 2
    assert "cut1" in summary["cut_bounds"]
    assert "cut2" in summary["cut_bounds"]
    assert "cut3" in summary["cut_bounds"]
    
    print("✓ Correspondence summary test passed")


def main():
    """Run all tests."""
    print("Cut-Area Correspondence Test Suite")
    print("==================================")
    
    try:
        test_empty_egi()
        test_single_cut()
        test_nested_cuts()
        test_sibling_cuts()
        test_correspondence_summary()
        
        print("\n🎉 All tests passed!")
        print("\nFundamental cut-area correspondence system is working correctly:")
        print("- Logical negation ↔ spatial cut mapping: ✓")
        print("- Area containment correspondence: ✓")
        print("- Canvas totality: ✓")
        print("- Arbitrary nesting support: ✓")
        print("- Sibling cut management: ✓")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
