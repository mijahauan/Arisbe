#!/usr/bin/env python3
"""
Simple command-line demo for cut-area correspondence system.
Tests various EGI cut structures and shows the spatial mapping results.
"""

import os
import sys

sys.path.append(os.path.dirname(__file__))

from frozendict import frozendict

from cut_area_correspondence import CutAreaCorrespondence, SpatialBounds
from egi_core_dau import Cut, RelationalGraphWithCuts


def create_test_egi(case_name: str) -> RelationalGraphWithCuts:
    """Create test EGI structures."""

    if case_name == "empty":
        return RelationalGraphWithCuts(
            V=frozenset(),
            E=frozenset(),
            nu=frozendict(),
            sheet="sheet",
            Cut=frozenset(),
            area=frozendict({"sheet": frozenset()}),
            rel=frozendict(),
        )

    elif case_name == "single":
        cuts = frozenset([Cut("cut1")])
        area_mapping = frozendict({"sheet": frozenset(["cut1"]), "cut1": frozenset()})

    elif case_name == "siblings":
        cuts = frozenset([Cut("cut1"), Cut("cut2"), Cut("cut3")])
        area_mapping = frozendict(
            {
                "sheet": frozenset(["cut1", "cut2", "cut3"]),
                "cut1": frozenset(),
                "cut2": frozenset(),
                "cut3": frozenset(),
            }
        )

    elif case_name == "nested":
        cuts = frozenset([Cut("cut1"), Cut("cut2")])
        area_mapping = frozendict(
            {
                "sheet": frozenset(["cut1"]),
                "cut1": frozenset(["cut2"]),
                "cut2": frozenset(),
            }
        )

    elif case_name == "deep":
        cuts = frozenset([Cut(f"cut{i}") for i in range(1, 5)])
        area_mapping = frozendict(
            {
                "sheet": frozenset(["cut1"]),
                "cut1": frozenset(["cut2"]),
                "cut2": frozenset(["cut3"]),
                "cut3": frozenset(["cut4"]),
                "cut4": frozenset(),
            }
        )

    elif case_name == "mixed":
        cuts = frozenset([Cut(f"cut{i}") for i in range(1, 7)])
        area_mapping = frozendict(
            {
                "sheet": frozenset(["cut1", "cut2"]),
                "cut1": frozenset(["cut3", "cut4"]),
                "cut2": frozenset(["cut5"]),
                "cut3": frozenset(["cut6"]),
                "cut4": frozenset(),
                "cut5": frozenset(),
                "cut6": frozenset(),
            }
        )

    else:
        raise ValueError(f"Unknown test case: {case_name}")

    return RelationalGraphWithCuts(
        V=frozenset(),
        E=frozenset(),
        nu=frozendict(),
        sheet="sheet",
        Cut=cuts,
        area=area_mapping,
        rel=frozendict(),
    )


def print_correspondence_info(correspondence: CutAreaCorrespondence):
    """Print detailed correspondence information."""
    summary = correspondence.get_correspondence_summary()

    print(
        f"Canvas: {summary['canvas_bounds']['width']}×{summary['canvas_bounds']['height']}"
    )
    print(f"Total Cuts: {summary['total_cuts']}")
    print(f"Root Cuts: {summary['root_cuts']}")
    print(f"Max Nesting Depth: {summary['max_nesting_depth']}")
    print()

    if summary["total_cuts"] > 0:
        print("Cut Details:")
        for cut_id, cut_info in summary["cut_bounds"].items():
            print(f"  {cut_id}:")
            print(f"    Parent: {cut_info['parent']}")
            print(f"    Depth: {cut_info['depth']}")
            print(
                f"    Bounds: ({cut_info['x']:.1f}, {cut_info['y']:.1f}) {cut_info['width']:.1f}×{cut_info['height']:.1f}"
            )
        print()

    print("Area Hierarchy:")
    for parent, children in summary["area_hierarchy"].items():
        if children:
            print(f"  {parent} → {children}")
    print()


def test_point_mapping(correspondence: CutAreaCorrespondence):
    """Test point-to-area mapping with various points."""
    canvas = correspondence.canvas.bounds

    test_points = [
        (canvas.x + 50, canvas.y + 50, "top-left"),
        (canvas.x + canvas.width / 2, canvas.y + canvas.height / 2, "center"),
        (canvas.x + canvas.width - 50, canvas.y + canvas.height - 50, "bottom-right"),
    ]

    print("Point Mapping Tests:")
    for x, y, description in test_points:
        try:
            area = correspondence.get_area_for_point(x, y)
            print(f"  Point ({x:.1f}, {y:.1f}) [{description}] → Area: {area}")
        except ValueError as e:
            print(f"  Point ({x:.1f}, {y:.1f}) [{description}] → Error: {e}")
    print()


def run_demo_case(case_name: str):
    """Run a single demo case."""
    print(f"=== Test Case: {case_name.upper()} ===")

    try:
        # Create EGI
        egi = create_test_egi(case_name)

        # Create correspondence
        canvas_bounds = SpatialBounds(0, 0, 800, 600)
        correspondence = CutAreaCorrespondence(canvas_bounds)
        correspondence.build_correspondence(egi)

        # Print information
        print_correspondence_info(correspondence)

        # Test point mapping
        test_point_mapping(correspondence)

        print("✓ Correspondence validation passed")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()

    print("-" * 50)


def main():
    """Run the cut correspondence demo."""
    print("Cut-Area Correspondence Demo")
    print("============================")
    print("Testing fundamental logic ↔ spatial cut mapping")
    print()

    test_cases = ["empty", "single", "siblings", "nested", "deep", "mixed"]

    for case in test_cases:
        run_demo_case(case)

    print("Demo completed!")
    print()
    print("Key Principles Demonstrated:")
    print("1. Logical Negation ↔ Spatial Cut: Bijective mapping")
    print("2. Area Containment: EGI area mapping ↔ spatial containment")
    print("3. Canvas Totality: Complete EGI ↔ total canvas area")
    print("4. Arbitrary Nesting: Support unlimited cut nesting levels")
    print("5. Sibling Management: Handle multiple cuts at same nesting level")


if __name__ == "__main__":
    main()
