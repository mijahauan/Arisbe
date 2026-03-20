from typing import Dict, List, Optional, Set, Tuple

from frozendict import frozendict

from egi_core_dau import AlphabetDAU, Cut, Edge, RelationalGraphWithCuts, Vertex


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

    # Collect basic sets - handle both dict and list formats
    cuts_data = drawing.get("cuts", [])
    if isinstance(cuts_data, dict):
        cut_ids: Set[str] = set(cuts_data.keys())
    else:
        cut_ids: Set[str] = {
            c.get("id") for c in cuts_data if isinstance(c, dict) and c.get("id")
        }

    vertices_data = drawing.get("vertices", [])
    if isinstance(vertices_data, dict):
        vertex_ids: Set[str] = set(vertices_data.keys())
    else:
        vertex_ids: Set[str] = {
            v.get("id") for v in vertices_data if isinstance(v, dict) and v.get("id")
        }

    predicates_data = drawing.get("predicates", [])
    if isinstance(predicates_data, dict):
        edge_ids: Set[str] = set(predicates_data.keys())
    else:
        edge_ids: Set[str] = {
            p.get("id") for p in predicates_data if isinstance(p, dict) and p.get("id")
        }

    # Build vertices with proper label and is_generic properties
    vertex_objects = []
    for vid in sorted(vertex_ids):
        # Find the vertex data in the drawing schema
        vertex_data = None
        vertices_data = drawing.get("vertices", [])
        if isinstance(vertices_data, dict):
            vertex_data = vertices_data.get(vid, {})
        else:
            for v in vertices_data:
                if isinstance(v, dict) and v.get("id") == vid:
                    vertex_data = v
                    break

        if vertex_data:
            lk = vertex_data.get("label_kind")
            lbl = vertex_data.get("label")
            if lk == "constant" and lbl:
                # Named constant vertex
                vertex_objects.append(Vertex(id=vid, label=lbl, is_generic=False))
            else:
                # Generic vertex
                vertex_objects.append(Vertex(id=vid, label=None, is_generic=True))
        else:
            # Fallback: treat as generic vertex
            vertex_objects.append(Vertex(id=vid, label=None, is_generic=True))

    V = tuple(vertex_objects)
    E = tuple(Edge(eid) for eid in sorted(edge_ids))
    CutSet = tuple(Cut(cid) for cid in sorted(cut_ids))

    # Build rel mapping (edge -> name)
    predicates_data = drawing.get("predicates", [])
    rel_dict: Dict[str, str] = {}
    if isinstance(predicates_data, dict):
        for pid, pdata in predicates_data.items():
            if isinstance(pdata, dict):
                rel_dict[pid] = pdata.get("name", pdata.get("text", pid))
            else:
                rel_dict[pid] = pid
    else:
        rel_dict = {
            p.get("id"): p.get("name", p.get("id"))
            for p in predicates_data
            if isinstance(p, dict) and p.get("id")
        }

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

    # --- Early validation: cut parent references and cycles ---
    # Build explicit parent map from the drawing; default parent is sheet
    parent_map: Dict[str, Optional[str]] = {}
    cuts_data = drawing.get("cuts", [])
    if isinstance(cuts_data, dict):
        for cid, cdata in cuts_data.items():
            if isinstance(cdata, dict):
                pid = cdata.get("parent_id") or sheet_id
            else:
                pid = sheet_id
            parent_map[cid] = pid
    else:
        for c in cuts_data:
            if not isinstance(c, dict):
                continue
            cid = c.get("id")
            if not cid:
                continue
            pid = c.get("parent_id") or sheet_id
            parent_map[cid] = pid

    # Validate parent references exist and detect cycles
    for cid, pid in parent_map.items():
        # Parent must be sheet or another known cut
        if pid is not None and pid != sheet_id and pid not in cut_ids:
            raise ValueError(
                f"Invalid parent_id '{pid}' for cut '{cid}': not in cuts and not sheet"
            )
        # Cycle detection by walking up to sheet
        seen: Set[str] = set([cid])
        cur = pid
        steps = 0
        while cur is not None and cur != sheet_id:
            if cur in seen:
                raise ValueError(
                    f"Cycle detected in cut parentage: '{cid}' -> ... -> '{cur}'"
                )
            seen.add(cur)
            cur = parent_map.get(cur)
            steps += 1
            if steps > len(cut_ids) + 1:
                raise ValueError(
                    "Unreasonable cut nesting depth; possible cycle or corrupted parent map"
                )

    # Build area containment mapping: area_id -> frozenset(child_ids)
    area: Dict[str, Set[str]] = {sheet_id: set()}
    cuts_data = drawing.get("cuts", [])
    if isinstance(cuts_data, dict):
        for cid in cuts_data.keys():
            area.setdefault(cid, set())
    else:
        for c in cuts_data:
            if isinstance(c, dict):
                cid = c.get("id")
                if cid:
                    area.setdefault(cid, set())

    # Add child cuts under their parents; default to sheet
    if isinstance(cuts_data, dict):
        for cid, cdata in cuts_data.items():
            if isinstance(cdata, dict):
                parent = cdata.get("parent_id") or sheet_id
            else:
                parent = sheet_id
            area.setdefault(parent, set()).add(cid)
    else:
        for c in cuts_data:
            if isinstance(c, dict):
                cid = c.get("id")
                if cid:
                    parent = c.get("parent_id") or sheet_id
                    area.setdefault(parent, set()).add(cid)

    # Place vertices and edges into their declared areas
    vertices_data = drawing.get("vertices", [])
    if isinstance(vertices_data, dict):
        for vid, vdata in vertices_data.items():
            if isinstance(vdata, dict):
                area_id = vdata.get("area_id") or sheet_id
            else:
                area_id = sheet_id
            area.setdefault(area_id, set()).add(vid)
    else:
        for v in vertices_data:
            if isinstance(v, dict):
                vid = v.get("id")
                if vid:
                    area_id = v.get("area_id") or sheet_id
                    area.setdefault(area_id, set()).add(vid)

    predicates_data = drawing.get("predicates", [])
    if isinstance(predicates_data, dict):
        for pid, pdata in predicates_data.items():
            if isinstance(pdata, dict):
                area_id = pdata.get("area_id") or sheet_id
            else:
                area_id = sheet_id
            area.setdefault(area_id, set()).add(pid)
    else:
        for p in predicates_data:
            if isinstance(p, dict):
                pid = p.get("id")
                if pid:
                    area_id = p.get("area_id") or sheet_id
                    area.setdefault(area_id, set()).add(pid)

    # Compute AlphabetDAU and rho (constants on vertices) if available in drawing
    # Constants set C from vertices with label_kind == 'constant'
    constants: Set[str] = set()
    rho_map: Dict[str, Optional[str]] = {}
    vertices_data = drawing.get("vertices", [])
    if isinstance(vertices_data, dict):
        for vid, vdata in vertices_data.items():
            if isinstance(vdata, dict):
                lk = vdata.get("label_kind")
                lbl = vdata.get("label")
                if lk == "constant" and lbl:
                    constants.add(lbl)
                    rho_map[vid] = lbl
                else:
                    rho_map[vid] = None
            else:
                rho_map[vid] = None
    else:
        for v in vertices_data:
            if isinstance(v, dict):
                vid = v.get("id")
                if vid:
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

    alphabet = AlphabetDAU(
        C=frozenset(constants),
        F=frozenset(function_names),
        R=frozenset(relation_names),
        ar=frozendict(ar_map),
    ).with_defaults()

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
