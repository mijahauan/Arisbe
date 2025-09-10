#!/usr/bin/env python3
"""
Debug script to understand deep context structure.
"""

from src.egif_parser_dau import parse_egif

def analyze_deep_context(depth=4):
    """Analyze the structure of a deep context."""
    print(f"=== Analyzing Deep Context (depth {depth}) ===")
    
    # Build nested cut structure
    cuts = []
    for i in range(depth // 2):
        cuts.append("~[")
    
    # Add empty composition area
    cuts.append(" ")
    
    # Close cuts
    for i in range(depth // 2):
        cuts.append("]")
    
    egif = " ".join(cuts)
    print(f"EGIF: {egif}")
    
    egi = parse_egif(egif)
    print(f"Areas: {len(egi.area)}")
    
    def calculate_nesting_depth(area_id, egi):
        """Calculate nesting depth by counting containing cuts."""
        depth = 0
        for cut in egi.Cut:
            cut_contents = egi.area.get(cut.id, frozenset())
            if area_id in cut_contents:
                depth += 1
        return depth
    
    for area_id, contents in egi.area.items():
        area_depth = calculate_nesting_depth(area_id, egi)
        polarity = "positive" if area_depth % 2 == 0 else "negative"
        
        print(f"Area {area_id}:")
        print(f"  Contents: {contents}")
        print(f"  Nesting depth: {area_depth}")
        print(f"  Polarity: {polarity}")
        print()
    
    # Find negative areas
    negative_areas = []
    for area_id in egi.area.keys():
        area_depth = calculate_nesting_depth(area_id, egi)
        if area_depth % 2 == 1:  # Negative area
            negative_areas.append((area_id, area_depth))
    
    print(f"Negative areas: {negative_areas}")
    return negative_areas

if __name__ == "__main__":
    analyze_deep_context(4)
    print()
    analyze_deep_context(6)
