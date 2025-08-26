from typing import Dict, List, Set, Tuple
from frozendict import frozendict

from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut


def drawing_to_relational_graph(drawing: Dict) -> RelationalGraphWithCuts:
    """
    Build a Dau-compliant RelationalGraphWithCuts from a simple drawing schema.

    Expected schema:
      {
        "sheet_id": str,
        "cuts": [ {"id": str, "parent_id": str|None} ],
        "vertices": [ {"id": str, "area_id": str} ],
        "predicates": [ {"id": str, "name": str, "area_id": str} ],
        "ligatures": [ {"edge_id": str, "vertex_ids": List[str]} ]
      }
    Rules:
      - area_id must be either sheet_id or a cut id.
      - parent_id must be either sheet_id or another cut id.
    """
    sheet_id: str = drawing["sheet_id"]

    # Collect basic sets
    cut_ids: Set[str] = {c["id"] for c in drawing.get("cuts", [])}
    vertex_ids: Set[str] = {v["id"] for v in drawing.get("vertices", [])}
    edge_ids: Set[str] = {p["id"] for p in drawing.get("predicates", [])}

    V = tuple(Vertex(vid) for vid in sorted(vertex_ids))
    E = tuple(Edge(eid) for eid in sorted(edge_ids))
    CutSet = tuple(Cut(cid) for cid in sorted(cut_ids))

    # Build rel mapping (edge -> name)
    rel_dict: Dict[str, str] = {p["id"]: p.get("name", p["id"]) for p in drawing.get("predicates", [])}

    # Build nu mapping (edge -> tuple(vertices))
    nu_map: Dict[str, Tuple[str, ...]] = {}
    for lig in drawing.get("ligatures", []):
        eid = lig["edge_id"]
        nu_map[eid] = tuple(lig.get("vertex_ids", []))
    # Ensure all predicates exist in ν, even if empty (nullary relation)
    for eid in edge_ids:
        nu_map.setdefault(eid, tuple())

    # Build area containment mapping: area_id -> frozenset(child_ids)
    area: Dict[str, Set[str]] = {sheet_id: set()}
    for c in drawing.get("cuts", []):
        area.setdefault(c["id"], set())
    # Add child cuts under their parents; default to sheet
    for c in drawing.get("cuts", []):
        parent = c.get("parent_id") or sheet_id
        area.setdefault(parent, set()).add(c["id"])
    # Place vertices and edges into their declared areas
    for v in drawing.get("vertices", []):
        area.setdefault(v["area_id"], set()).add(v["id"]) 
    for p in drawing.get("predicates", []):
        area.setdefault(p["area_id"], set()).add(p["id"]) 

    # Freeze mappings
    nu = frozendict({k: tuple(v) for k, v in nu_map.items()})
    rel = frozendict(rel_dict)
    area_frozen = frozendict({k: frozenset(v) for k, v in area.items()})

    return RelationalGraphWithCuts(
        V=V,
        E=E,
        nu=nu,
        sheet=sheet_id,
        Cut=CutSet,
        area=area_frozen,
        rel=rel,
    )
