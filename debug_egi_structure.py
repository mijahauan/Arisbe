#!/usr/bin/env python3
"""Debug script to examine EGI structure and area containment."""

from src.egif_parser_dau import parse_egif

def debug_egi_structure(egif: str, name: str):
    """Debug the EGI structure for a given EGIF."""
    print(f"\n🔍 Debugging: {name}")
    print(f"EGIF: {egif}")
    print("-" * 40)
    
    try:
        egi = parse_egif(egif)
        
        print(f"Sheet ID: {egi.sheet}")
        print(f"Cuts: {[str(cut.id) for cut in egi.Cut]}")
        print(f"Vertices: {[str(v.id) for v in egi.V]}")
        print(f"Edges: {[str(e.id) for e in egi.E]}")
        
        print(f"\nArea containment:")
        for area_id, contents in egi.area.items():
            contents_list = [str(elem_id) for elem_id in contents]
            print(f"  {area_id}: {contents_list}")
            
        print(f"\nCut ordering and expected depths:")
        for i, cut in enumerate(egi.Cut):
            # Find what contains this cut
            containing_area = None
            for area_id, contents in egi.area.items():
                if cut.id in contents:
                    containing_area = area_id
                    break
            
            # Calculate expected depth based on containment
            enclosing_cuts = 0
            current = containing_area
            
            # Count how many cuts enclose this cut
            while current != egi.sheet:
                parent = None
                for area_id, contents in egi.area.items():
                    if current in contents:
                        parent = area_id
                        break
                if parent and any(c.id == parent for c in egi.Cut):
                    enclosing_cuts += 1
                current = parent if parent else egi.sheet
            
            expected_depth = enclosing_cuts + 1
            expected_polarity = "positive" if expected_depth % 2 == 0 else "negative"
            
            print(f"  cut_{i} ({cut.id}): Expected depth {expected_depth}, polarity {expected_polarity}")
            print(f"    Contained in: {containing_area}, Enclosing cuts: {enclosing_cuts}")
        
        # Manual polarity calculation
        print(f"\nManual polarity calculation:")
        for cut in egi.Cut:
            print(f"  Cut {cut.id}:")
            
            # Find what contains this cut
            containing_area = None
            for area_id, contents in egi.area.items():
                if cut.id in contents:
                    containing_area = area_id
                    break
            
            print(f"    Contained in: {containing_area}")
            
            # Count nesting depth
            depth = 0
            current_area = containing_area
            
            while current_area != egi.sheet:
                # Find what contains the current area
                next_containing_area = None
                for area_id, contents in egi.area.items():
                    if current_area in contents:
                        next_containing_area = area_id
                        break
                
                if next_containing_area is None:
                    break
                    
                # If the containing area is a cut, increment depth
                if any(c.id == next_containing_area for c in egi.Cut):
                    depth += 1
                
                current_area = next_containing_area
            
            # The cut itself adds 1 to depth
            depth += 1
            polarity = "positive" if depth % 2 == 0 else "negative"
            print(f"    Depth: {depth}, Polarity: {polarity}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_cases = [
        ("stanford_nested_quantifiers", "~[ *x *y (Loves x y) ]"),
        ("peirce_man_mortal", "~[ (Human \"Socrates\") ~[ (Mortal \"Socrates\") ] ]"),
        ("roberts_disjunction", "~[ ~[ (P \"x\") ] ~[ (Q \"x\") ] ]")
    ]
    
    for name, egif in test_cases:
        debug_egi_structure(egif, name)
