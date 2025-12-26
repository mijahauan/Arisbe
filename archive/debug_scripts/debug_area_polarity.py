#!/usr/bin/env python3
"""
Debug script to understand area polarity in double cut structure.
"""

from src.egif_parser_dau import parse_egif
from src.formal_transformation_rules import AreaPolarity

def analyze_double_cut_structure():
    """Analyze the polarity of areas in double cut structure."""
    print("=== Analyzing Double Cut Structure ===")
    
    # Parse double cut structure
    egif = "~[ ~[ ] ]"
    egi = parse_egif(egif)
    
    print(f"EGIF: {egif}")
    print(f"Areas: {len(egi.area)}")
    
    # Calculate nesting depth for each area
    def calculate_nesting_depth(area_id, egi):
        """Calculate nesting depth by counting containing cuts."""
        depth = 0
        for cut in egi.Cut:
            cut_contents = egi.area.get(cut.id, frozenset())
            if area_id in cut_contents:
                depth += 1
        return depth
    
    for area_id, contents in egi.area.items():
        depth = calculate_nesting_depth(area_id, egi)
        polarity = AreaPolarity.POSITIVE if depth % 2 == 0 else AreaPolarity.NEGATIVE
        
        print(f"Area {area_id}:")
        print(f"  Contents: {contents}")
        print(f"  Nesting depth: {depth}")
        print(f"  Polarity: {polarity.value}")
        
        # Check if this area contains cuts
        contains_cuts = any(cut.id in contents for cut in egi.Cut)
        print(f"  Contains cuts: {contains_cuts}")
        print()

def find_negative_area():
    """Find a negative area for insertion."""
    print("=== Finding Negative Area for Insertion ===")
    
    egif = "~[ ~[ ] ]"
    egi = parse_egif(egif)
    
    def calculate_nesting_depth(area_id, egi):
        depth = 0
        for cut in egi.Cut:
            cut_contents = egi.area.get(cut.id, frozenset())
            if area_id in cut_contents:
                depth += 1
        return depth
    
    negative_areas = []
    for area_id, contents in egi.area.items():
        depth = calculate_nesting_depth(area_id, egi)
        if depth % 2 == 1:  # Odd depth = negative
            negative_areas.append((area_id, depth, contents))
    
    print(f"Found {len(negative_areas)} negative areas:")
    for area_id, depth, contents in negative_areas:
        print(f"  {area_id}: depth={depth}, contents={contents}")
    
    return negative_areas

if __name__ == "__main__":
    analyze_double_cut_structure()
    find_negative_area()
