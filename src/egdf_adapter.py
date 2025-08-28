from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple
from frozendict import frozendict

from src.egdf_parser import EGDFDocument, EGIInlineSchema


def drawing_to_egdf_document(
    drawing: Dict[str, Any],
    layout: Optional[Dict[str, Any]] = None,
    styles: Optional[Dict[str, Any]] = None,
    deltas: Optional[List[Dict[str, Any]]] = None,
    *,
    version: str = "0.1",
    generator: str = "arisbe",
    created: str = "",
) -> EGDFDocument:
    """
    Build an EGDFDocument from a platform-independent drawing schema.
    This duplicates the logical extraction used by drawing_to_egi_adapter, but avoids
    importing GUI specifics and returns a self-contained EGDF (EGI inline + layout/styles/deltas).

    Expected drawing schema keys (superset tolerated):
      sheet_id: str
      cuts: [ {id, parent_id?} ]
      vertices: [ {id, area_id, label_kind?, label?} ]
      predicates: [ {id, name, area_id} ]
      ligatures: [ {edge_id, vertex_ids[]} ]
    """
    sheet_id: str = drawing.get("sheet_id") or "sheet"

    # Identify ids
    cut_ids: Set[str] = {c.get("id") for c in drawing.get("cuts", []) if c.get("id")}
    vertex_ids: Set[str] = {v.get("id") for v in drawing.get("vertices", []) if v.get("id")}
    edge_ids: Set[str] = {p.get("id") for p in drawing.get("predicates", []) if p.get("id")}

    # Relations and ν
    rel: Dict[str, str] = {p["id"]: p.get("name", p["id"]) for p in drawing.get("predicates", []) if p.get("id")}
    nu: Dict[str, List[str]] = {}
    for lig in drawing.get("ligatures", []):
        eid = lig.get("edge_id")
        if not eid:
            continue
        nu[eid] = list(lig.get("vertex_ids", []))
    for eid in edge_ids:
        nu.setdefault(eid, [])

    # Parent map (validate existence and cycles lightly)
    parent: Dict[str, Optional[str]] = {}
    for c in drawing.get("cuts", []):
        cid = c.get("id")
        if not cid:
            continue
        pid = c.get("parent_id") or sheet_id
        parent[cid] = pid
        if pid is not None and pid != sheet_id and pid not in cut_ids:
            raise ValueError(f"Invalid parent_id '{pid}' for cut '{cid}'")

    for cid, pid in parent.items():
        seen = {cid}
        cur = pid
        steps = 0
        while cur is not None and cur != sheet_id:
            if cur in seen:
                raise ValueError(f"Cycle detected in cut parentage: {cid} -> ... -> {cur}")
            seen.add(cur)
            cur = parent.get(cur)
            steps += 1
            if steps > len(cut_ids) + 1:
                raise ValueError("Unreasonable nesting depth; possible cycle")

    # Area containment
    area: Dict[str, List[str]] = {sheet_id: []}
    for cid in cut_ids:
        area[cid] = []
    for c in drawing.get("cuts", []):
        cid = c.get("id")
        if not cid:
            continue
        pid = c.get("parent_id") or sheet_id
        area.setdefault(pid, []).append(cid)
    for v in drawing.get("vertices", []):
        vid = v.get("id")
        if not vid:
            continue
        a = v.get("area_id") or sheet_id
        area.setdefault(a, []).append(vid)
    for p in drawing.get("predicates", []):
        pid = p.get("id")
        if not pid:
            continue
        a = p.get("area_id") or sheet_id
        area.setdefault(a, []).append(pid)

    # rho and alphabet
    rho: Dict[str, Optional[str]] = {}
    constants: Set[str] = set()
    for v in drawing.get("vertices", []):
        vid = v["id"]
        lk = v.get("label_kind")
        lbl = v.get("label")
        if lk == "constant" and lbl:
            rho[vid] = lbl
            constants.add(lbl)
        else:
            rho[vid] = None

    relation_names: Set[str] = set(rel.values())
    function_names: Set[str] = set()
    ar: Dict[str, int] = {}
    for eid, name in rel.items():
        ar[name] = max(ar.get(name, 0), len(nu.get(eid, [])))

    inline: EGIInlineSchema = {
        "sheet": sheet_id,
        "V": sorted(list(vertex_ids)),
        "E": sorted(list(edge_ids)),
        "Cut": sorted(list(cut_ids)),
        "nu": {k: list(v) for k, v in nu.items()},
        "rel": rel,
        "area": {k: list(v) for k, v in area.items()},
        "rho": rho,
        "alphabet": {
            "C": sorted(list(constants)),
            "F": sorted(list(function_names)),
            "R": sorted(list(relation_names)),
            "ar": ar,
        },
    }

    header = {"version": version, "generator": generator, "created": created}
    doc = EGDFDocument(header=header, egi_ref={"inline": inline})

    if layout:
        doc.layout = layout  # type: ignore[assignment]
    if styles:
        doc.styles = styles  # type: ignore[assignment]
    if deltas:
        doc.deltas = deltas  # type: ignore[assignment]

    # Trigger validation and hash computation
    _ = doc.to_dict()
    return doc
