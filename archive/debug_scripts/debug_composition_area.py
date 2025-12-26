#!/usr/bin/env python3
"""
Debug script to check composition area selection and polarity.
"""

from src.composition_context import StandardCompositionContexts
from src.formal_transformation_rules import AreaPolarity

def debug_composition_area():
    """Debug the composition area selection."""
    print("=== Debugging Composition Area Selection ===")
    
    # Create standard context
    context = StandardCompositionContexts.create_double_cut_context()
    
    print(f"Context ID: {context.context_id}")
    print(f"Composition area: {context.composition_area}")
    print(f"Base EGIF: {context.base_egi}")
    
    # Calculate nesting depth for the selected area
    def calculate_nesting_depth(area_id, egi):
        depth = 0
        for cut in egi.Cut:
            cut_contents = egi.area.get(cut.id, frozenset())
            if area_id in cut_contents:
                depth += 1
        return depth
    
    selected_depth = calculate_nesting_depth(context.composition_area, context.base_egi)
    polarity = AreaPolarity.POSITIVE if selected_depth % 2 == 0 else AreaPolarity.NEGATIVE
    
    print(f"Selected area depth: {selected_depth}")
    print(f"Selected area polarity: {polarity.value}")
    
    # Check all areas
    print("\nAll areas:")
    for area_id, contents in context.base_egi.area.items():
        depth = calculate_nesting_depth(area_id, context.base_egi)
        area_polarity = AreaPolarity.POSITIVE if depth % 2 == 0 else AreaPolarity.NEGATIVE
        print(f"  {area_id}: depth={depth}, polarity={area_polarity.value}, contents={contents}")

if __name__ == "__main__":
    debug_composition_area()
