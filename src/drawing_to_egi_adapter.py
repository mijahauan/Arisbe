from typing import Dict, List, Set, Tuple, Optional
from frozendict import frozendict

from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut, AlphabetDAU


def drawing_to_relational_graph(drawing: Dict) -> RelationalGraphWithCuts:
    """
    Build a Dau-compliant RelationalGraphWithCuts from a simple drawing schema.

    Expected schema (fields beyond these are ignored if unknown):
      {
        "sheet_id": str,
        "cuts": [ {"id": str, "parent_id": str|None} ],
        "vertices": [ {"id": str, "area_id": str, "label_kind": str|None, "label": str|None} ],
        "predicates": [ {"id": str, "name": str, "area_id": str} ],
        "ligatures": [ {"edge_id": str, "vertex_ids": List[str]} ]
      }
    Rules:
      - area_id must be either sheet_id or a cut id.
      - parent_id must be either sheet_id or another cut id.
    """
    # Default sheet id if absent
    sheet_id: str = drawing.get("sheet_id") or "sheet"

    # Collect basic sets
    cut_ids: Set[str] = {c.get("id") for c in drawing.get("cuts", []) if c.get("id")}
    vertex_ids: Set[str] = {v.get("id") for v in drawing.get("vertices", []) if v.get("id")}
    edge_ids: Set[str] = {p.get("id") for p in drawing.get("predicates", []) if p.get("id")}

    V = tuple(Vertex(vid) for vid in sorted(vertex_ids))
    E = tuple(Edge(eid) for eid in sorted(edge_ids))
    CutSet = tuple(Cut(cid) for cid in sorted(cut_ids))

    # Build rel mapping (edge -> name)
    rel_dict: Dict[str, str] = {p.get("id"): p.get("name", p.get("id")) for p in drawing.get("predicates", []) if p.get("id")}

    # Build nu mapping (edge -> tuple(vertices))
    nu_map: Dict[str, Tuple[str, ...]] = {}
    for lig in drawing.get("ligatures", []):
        eid = lig.get("edge_id")
        if not eid:
            continue
        nu_map[eid] = tuple(lig.get("vertex_ids", []))
    # Ensure all predicates exist in ν, even if empty (nullary relation)
    for eid in edge_ids:
        nu_map.setdefault(eid, tuple())

    # Build area containment mapping: area_id -> frozenset(child_ids)
    area: Dict[str, Set[str]] = {sheet_id: set()}
    for c in drawing.get("cuts", []):
        cid = c.get("id")
        if not cid:
            continue
        area.setdefault(cid, set())
    # Add child cuts under their parents; default to sheet
    for c in drawing.get("cuts", []):
        cid = c.get("id")
        if not cid:
            continue
        parent = c.get("parent_id") or sheet_id
        area.setdefault(parent, set()).add(cid)
    # Place vertices and edges into their declared areas
    for v in drawing.get("vertices", []):
        vid = v.get("id")
        if not vid:
            continue
        area_id = v.get("area_id") or sheet_id
        area.setdefault(area_id, set()).add(vid)
    for p in drawing.get("predicates", []):
        pid = p.get("id")
        if not pid:
            continue
        area_id = p.get("area_id") or sheet_id
        area.setdefault(area_id, set()).add(pid)

    # Compute AlphabetDAU and rho (constants on vertices) if available in drawing
    # Constants set C from vertices with label_kind == 'constant'
    constants: Set[str] = set()
    rho_map: Dict[str, Optional[str]] = {}
    for v in drawing.get("vertices", []):
        vid = v["id"]
        lk = v.get("label_kind")
        lbl = v.get("label")
        if lk == "constant" and lbl:
            constants.add(lbl)
            rho_map[vid] = lbl
        else:
            # explicit None for generic
            rho_map[vid] = None

    # Relation names (R) from predicates; functions (F) not represented in drawing yet
    relation_names: Set[str] = set(rel_dict.values())
    function_names: Set[str] = set()

    # Arity map from nu lengths where known
    ar_map: Dict[str, int] = {}
    for eid, name in rel_dict.items():
        ar_map[name] = max(ar_map.get(name, 0), len(nu_map.get(eid, ())))

    alphabet = AlphabetDAU(C=frozenset(constants), F=frozenset(function_names), R=frozenset(relation_names), ar=frozendict(ar_map)).with_defaults()

    # Freeze mappings
    nu = frozendict({k: tuple(v) for k, v in nu_map.items()})
    rel = frozendict(rel_dict)
    area_frozen = frozendict({k: frozenset(v) for k, v in area.items()})
    rho_frozen = frozendict(rho_map)

    return RelationalGraphWithCuts(
        V=V,
        E=E,
        nu=nu,
        sheet=sheet_id,
        Cut=CutSet,
        area=area_frozen,
        rel=rel,
        alphabet=alphabet,
        rho=rho_frozen,
    )
