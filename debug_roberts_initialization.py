#!/usr/bin/env python3
"""
Debug script to trace exactly what elements get created from Roberts disjunction EGI
"""
import json
import sys
from pathlib import Path

# Add src to path
REPO_ROOT = Path(__file__).parent
SRC_DIR = REPO_ROOT / "src"
TOOLS_DIR = REPO_ROOT / "tools"
sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(TOOLS_DIR))

def analyze_roberts_initialization():
    """Trace what elements get created from the Roberts disjunction example."""
    
    # Load the EGI file
    egi_path = REPO_ROOT / "corpus/graphs/roberts_1973_p57_disjunction/roberts_1973_p57_disjunction.egi.json"
    with open(egi_path) as f:
        egi_data = json.load(f)
    
    print("=== ORIGINAL EGI DATA ===")
    print(f"Cuts: {len(egi_data.get('Cut', []))}")
    for i, cut in enumerate(egi_data.get('Cut', [])):
        print(f"  Cut {i+1}: {cut}")
    
    print(f"Vertices: {len(egi_data.get('V', []))}")
    for i, vertex in enumerate(egi_data.get('V', [])):
        print(f"  Vertex {i+1}: {vertex}")
        
    print(f"Edges: {len(egi_data.get('E', []))}")
    for i, edge in enumerate(egi_data.get('E', [])):
        print(f"  Edge {i+1}: {edge}")
    
    print(f"Area mapping:")
    for area_id, elements in egi_data.get('area', {}).items():
        print(f"  {area_id}: {elements}")
    
    # Now trace the schema conversion without Qt
    print("\n=== SCHEMA CONVERSION (NO QT) ===")
    
    # Replicate the _schema_from_egi_inline logic without Qt dependencies
    def _norm_id(x):
        if isinstance(x, dict) and isinstance(x.get("id"), str):
            return x["id"]
        if isinstance(x, str):
            return x
        return json.dumps(x, sort_keys=True)

    def _norm_id_list(xs):
        if not isinstance(xs, list):
            return []
        return [_norm_id(x) for x in xs]

    def _norm_area(a):
        out = {}
        if isinstance(a, dict):
            for k, v in a.items():
                out[_norm_id(k)] = _norm_id_list(v)
        return out

    def _norm_map_str(m):
        out = {}
        if isinstance(m, dict):
            for k, v in m.items():
                out[_norm_id(k)] = _norm_id(v)
        return out

    def _norm_map_list(m):
        out = {}
        if isinstance(m, dict):
            for k, v in m.items():
                out[_norm_id(k)] = _norm_id_list(v)
        return out

    sheet_id = _norm_id(egi_data.get("sheet", "S"))
    area = _norm_area(egi_data.get("area", {}))
    rel = _norm_map_str(egi_data.get("rel", {}))
    nu = _norm_map_list(egi_data.get("nu", {}))
    cuts_ids = _norm_id_list(egi_data.get("Cut", []))
    cuts_set = set(cuts_ids)

    # Build parent map for cuts
    parent_map = {}
    for cut in cuts_set:
        parent = sheet_id
        for a, elems in area.items():
            if cut in elems:
                parent = a
                break
        parent_map[cut] = parent

    cuts = [{"id": c, "parent_id": parent_map.get(c, sheet_id)} for c in cuts_set]

    vertices = []
    for v in egi_data.get("V", []):
        vid = _norm_id(v)
        v_area = sheet_id
        for a, elems in area.items():
            if vid in elems:
                v_area = a
                break
        vertices.append({"id": vid, "area_id": v_area})

    predicates = []
    for e in egi_data.get("E", []):
        eid = _norm_id(e)
        e_area = sheet_id
        for a, elems in area.items():
            if eid in elems:
                e_area = a
                break
        predicates.append({"id": eid, "name": rel.get(eid, eid), "area_id": e_area})

    ligatures = [{"edge_id": _norm_id(e), "vertex_ids": _norm_id_list(vs)} for e, vs in nu.items()]

    schema = {"sheet_id": sheet_id, "cuts": cuts, "vertices": vertices, "predicates": predicates, "ligatures": ligatures}
    
    print(f"Schema cuts: {len(schema.get('cuts', []))}")
    for i, cut in enumerate(schema.get('cuts', [])):
        print(f"  Schema Cut {i+1}: {cut}")
    
    print(f"Schema vertices: {len(schema.get('vertices', []))}")
    for i, vertex in enumerate(schema.get('vertices', [])):
        print(f"  Schema Vertex {i+1}: {vertex}")
        
    print(f"Schema predicates: {len(schema.get('predicates', []))}")
    for i, predicate in enumerate(schema.get('predicates', [])):
        print(f"  Schema Predicate {i+1}: {predicate}")
    
    print(f"Schema ligatures: {len(schema.get('ligatures', []))}")
    for i, ligature in enumerate(schema.get('ligatures', [])):
        print(f"  Schema Ligature {i+1}: {ligature}")
    
    # Check if there are any discrepancies
    print("\n=== DISCREPANCY CHECK ===")
    original_cuts = len(egi_data.get('Cut', []))
    schema_cuts = len(schema.get('cuts', []))
    if original_cuts != schema_cuts:
        print(f"❌ CUT MISMATCH: Original has {original_cuts} cuts, schema has {schema_cuts} cuts")
    else:
        print(f"✅ Cuts match: {original_cuts}")
    
    original_vertices = len(egi_data.get('V', []))
    schema_vertices = len(schema.get('vertices', []))
    if original_vertices != schema_vertices:
        print(f"❌ VERTEX MISMATCH: Original has {original_vertices} vertices, schema has {schema_vertices} vertices")
    else:
        print(f"✅ Vertices match: {original_vertices}")
        
    original_edges = len(egi_data.get('E', []))
    schema_predicates = len(schema.get('predicates', []))
    if original_edges != schema_predicates:
        print(f"❌ EDGE/PREDICATE MISMATCH: Original has {original_edges} edges, schema has {schema_predicates} predicates")
    else:
        print(f"✅ Edges/Predicates match: {original_edges}")
    
    return schema

if __name__ == "__main__":
    analyze_roberts_initialization()
