#!/usr/bin/env python3
"""
Test script to verify ligatures are properly loaded and displayed from EGDF files.
"""
import sys
import json
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

def test_ligature_loading():
    """Test that ligatures are loaded from EGDF and displayed correctly."""
    
    # Load the test EGDF file
    egdf_path = Path("corpus/graphs/sowa_cat_on_mat/EGDF/diagram_20250902_202811.egdf.json")
    if not egdf_path.exists():
        print(f"EGDF file not found: {egdf_path}")
        return False
    
    with open(egdf_path) as f:
        egdf_data = json.load(f)
    
    print("=== EGDF Data Analysis ===")
    print(f"EGI inline data: {egdf_data.get('egi_ref', {}).get('inline', {}).keys()}")
    
    # Check nu mapping (ligatures)
    nu_mapping = egdf_data.get('egi_ref', {}).get('inline', {}).get('nu', {})
    print(f"Nu mapping (ligatures): {nu_mapping}")
    
    # Expected ligatures from the data:
    # "e_0720f7": ["v_b25600", "v_e909bc"] - On(cat, mat)
    # "e_8a2b9a": ["v_e909bc"] - Mat(mat)  
    # "e_f4ccfd": ["v_b25600"] - Cat(cat)
    
    expected_ligatures = {
        "e_0720f7": ["v_b25600", "v_e909bc"],
        "e_8a2b9a": ["v_e909bc"], 
        "e_f4ccfd": ["v_b25600"]
    }
    
    print("\n=== Expected Ligatures ===")
    for edge_id, vertex_ids in expected_ligatures.items():
        predicate_name = egdf_data.get('egi_ref', {}).get('inline', {}).get('rel', {}).get(edge_id, edge_id)
        print(f"  {predicate_name} ({edge_id}) -> {vertex_ids}")
    
    # Test schema conversion
    sys.path.append("tools")
    from drawing_editor import DrawingEditor
    
    editor = DrawingEditor()
    inline_egi = egdf_data.get('egi_ref', {}).get('inline', {})
    schema = editor._schema_from_egi_inline(inline_egi)
    
    print("\n=== Schema Conversion ===")
    print(f"Schema ligatures: {schema.get('ligatures', [])}")
    
    # Verify ligatures are correctly converted
    schema_ligatures = {lig['edge_id']: lig['vertex_ids'] for lig in schema.get('ligatures', [])}
    
    success = True
    for edge_id, expected_vertices in expected_ligatures.items():
        if edge_id not in schema_ligatures:
            print(f"ERROR: Missing ligature for {edge_id}")
            success = False
        elif set(schema_ligatures[edge_id]) != set(expected_vertices):
            print(f"ERROR: Wrong vertices for {edge_id}. Expected {expected_vertices}, got {schema_ligatures[edge_id]}")
            success = False
        else:
            print(f"✓ Ligature {edge_id} correctly loaded")
    
    return success

if __name__ == "__main__":
    success = test_ligature_loading()
    print(f"\n=== Test Result ===")
    print("PASS" if success else "FAIL")
    sys.exit(0 if success else 1)
