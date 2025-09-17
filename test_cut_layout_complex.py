"""
Test cut layout engine with complex nested examples from corpus.
"""

import json
from pathlib import Path
from src.cut_layout_engine import CutLayoutEngine
from egi_core_dau import RelationalGraphWithCuts, Cut, Vertex, Edge, ElementID
from frozendict import frozendict


def load_egi_from_json(json_path: str) -> RelationalGraphWithCuts:
    """Load EGI from JSON corpus file."""
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Convert JSON data to EGI objects
    vertices = frozenset(Vertex(ElementID(v["id"]), v.get("is_generic", False), v.get("label")) 
                        for v in data["V"])
    edges = frozenset(Edge(ElementID(e["id"])) for e in data["E"])
    cuts = frozenset(Cut(ElementID(c["id"])) for c in data["Cut"])
    
    # Convert area mappings
    area = frozendict({
        ElementID(area_id): frozenset(ElementID(elem_id) for elem_id in contents)
        for area_id, contents in data["area"].items()
    })
    
    # Convert nu mappings
    nu = frozendict({
        ElementID(edge_id): tuple(ElementID(v_id) for v_id in vertex_list)
        for edge_id, vertex_list in data["nu"].items()
    })
    
    # Convert rel mappings
    rel = frozendict({
        ElementID(edge_id): relation
        for edge_id, relation in data["rel"].items()
    })
    
    return RelationalGraphWithCuts(
        V=vertices,
        E=edges,
        nu=nu,
        sheet=ElementID(data["sheet"]),
        Cut=cuts,
        area=area,
        rel=rel
    )


def test_complex_example():
    """Test cut layout with mixed quantifier complex example."""
    print("Testing complex nested example...")
    
    # Load complex example
    complex_path = "/Users/mjh/Sync/GitHub/Arisbe/corpus/graphs/mixed_quantifier_complex/mixed_quantifier_complex.egi.json"
    egi = load_egi_from_json(complex_path)
    
    print(f"Loaded EGI with {len(egi.Cut)} cuts, {len(egi.V)} vertices, {len(egi.E)} edges")
    
    # Print area structure
    print("\nArea structure:")
    for area_id, contents in egi.area.items():
        print(f"  {area_id}: {list(contents)}")
    
    # Test cut layout
    engine = CutLayoutEngine()
    cut_bounds = engine.layout_cuts(egi)
    
    print("\nCut Layout Results:")
    for cut_id, bounds in cut_bounds.items():
        print(f"  {cut_id}: {bounds}")
    
    # Validate layout
    is_valid = engine.validate_layout(cut_bounds, egi)
    print(f"\nLayout valid: {is_valid}")
    
    return cut_bounds, is_valid


def test_peirce_example():
    """Test cut layout with Peirce modus ponens example."""
    print("\n" + "="*50)
    print("Testing Peirce modus ponens example...")
    
    # Load Peirce example
    peirce_path = "/Users/mjh/Sync/GitHub/Arisbe/corpus/graphs/peirce_modus_ponens/peirce_modus_ponens.egi.json"
    egi = load_egi_from_json(peirce_path)
    
    print(f"Loaded EGI with {len(egi.Cut)} cuts, {len(egi.V)} vertices, {len(egi.E)} edges")
    
    # Print area structure
    print("\nArea structure:")
    for area_id, contents in egi.area.items():
        print(f"  {area_id}: {list(contents)}")
    
    # Test cut layout
    engine = CutLayoutEngine()
    cut_bounds = engine.layout_cuts(egi)
    
    print("\nCut Layout Results:")
    for cut_id, bounds in cut_bounds.items():
        print(f"  {cut_id}: {bounds}")
    
    # Validate layout
    is_valid = engine.validate_layout(cut_bounds, egi)
    print(f"\nLayout valid: {is_valid}")
    
    return cut_bounds, is_valid


if __name__ == "__main__":
    print("Testing Cut Layout Engine with Corpus Examples")
    print("=" * 60)
    
    # Test both examples
    complex_bounds, complex_valid = test_complex_example()
    peirce_bounds, peirce_valid = test_peirce_example()
    
    print("\n" + "="*60)
    print("SUMMARY:")
    print(f"Complex example layout valid: {complex_valid}")
    print(f"Peirce example layout valid: {peirce_valid}")
    
    if complex_valid and peirce_valid:
        print("✓ All cut layouts are valid - no overlapping cuts!")
    else:
        print("✗ Some layouts have issues")
