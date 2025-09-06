#!/usr/bin/env python3
"""
Fix sowa_cat_on_mat EGDF by regenerating it with correct IDs from current EGI.
"""

import json
from pathlib import Path

def fix_sowa_egdf():
    # Paths
    egi_path = Path("corpus/graphs/sowa_cat_on_mat/sowa_cat_on_mat.egi.json")
    egdf_path = Path("corpus/graphs/sowa_cat_on_mat/EGDF/diagram_20250902_101539.egdf.json")
    
    # Load current EGI
    egi_data = json.loads(egi_path.read_text())
    
    # Load existing EGDF
    egdf_data = json.loads(egdf_path.read_text())
    
    # Extract current IDs from EGI
    current_vertices = [v["id"] for v in egi_data["V"]]
    current_edges = [e["id"] for e in egi_data["E"]]
    
    print(f"Current EGI vertices: {current_vertices}")
    print(f"Current EGI edges: {current_edges}")
    
    # Map old EGDF IDs to new EGI IDs based on relation types
    egi_rel = egi_data["rel"]
    egdf_rel = egdf_data["egi_ref"]["inline"]["rel"]
    
    # Create mapping based on relation names
    edge_mapping = {}
    for new_eid, rel_name in egi_rel.items():
        # Find old edge with same relation
        for old_eid, old_rel in egdf_rel.items():
            if old_rel == rel_name and old_eid not in edge_mapping.values():
                edge_mapping[old_eid] = new_eid
                break
    
    # Create vertex mapping based on edge connections
    egi_nu = egi_data["nu"]
    egdf_nu = egdf_data["egi_ref"]["inline"]["nu"]
    
    vertex_mapping = {}
    for old_eid, new_eid in edge_mapping.items():
        old_vertices = egdf_nu.get(old_eid, [])
        new_vertices = egi_nu.get(new_eid, [])
        
        for i, old_vid in enumerate(old_vertices):
            if i < len(new_vertices) and old_vid not in vertex_mapping:
                vertex_mapping[old_vid] = new_vertices[i]
    
    print(f"Edge mapping: {edge_mapping}")
    print(f"Vertex mapping: {vertex_mapping}")
    
    # Update EGDF with new IDs
    # Update egi_ref inline data
    egdf_data["egi_ref"]["inline"] = egi_data
    
    # Update layout section
    if "layout" in egdf_data:
        layout = egdf_data["layout"]
        
        # Update vertices in layout
        if "vertices" in layout:
            new_vertices = {}
            for old_vid, pos_data in layout["vertices"].items():
                new_vid = vertex_mapping.get(old_vid, old_vid)
                new_vertices[new_vid] = pos_data
            layout["vertices"] = new_vertices
        
        # Update predicates in layout
        if "predicates" in layout:
            new_predicates = {}
            for old_eid, pred_data in layout["predicates"].items():
                new_eid = edge_mapping.get(old_eid, old_eid)
                new_predicates[new_eid] = pred_data
            layout["predicates"] = new_predicates
    
    # Update deltas section
    if "deltas" in egdf_data:
        new_deltas = []
        for delta in egdf_data["deltas"]:
            delta_id = delta.get("id")
            if delta_id in vertex_mapping:
                delta["id"] = vertex_mapping[delta_id]
            elif delta_id in edge_mapping:
                delta["id"] = edge_mapping[delta_id]
            new_deltas.append(delta)
        egdf_data["deltas"] = new_deltas
    
    # Save updated EGDF
    egdf_path.write_text(json.dumps(egdf_data, indent=2))
    print(f"Updated EGDF saved to {egdf_path}")

if __name__ == "__main__":
    fix_sowa_egdf()
