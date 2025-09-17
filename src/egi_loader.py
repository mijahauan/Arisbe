"""
EGI Loader for Dau-compliant JSON format.
Converts corpus JSON files to RelationalGraphWithCuts instances.
"""

import json
from typing import Dict, Any, Optional
from frozendict import frozendict

from egi_core_dau import (
    RelationalGraphWithCuts, Vertex, Edge, Cut, ElementID,
    AlphabetDAU
)


def load_egi_from_json(file_path: str) -> RelationalGraphWithCuts:
    """Load EGI from JSON file in corpus format."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    return deserialize_egi_from_dict(data)


def deserialize_egi_from_dict(data: Dict[str, Any]) -> RelationalGraphWithCuts:
    """Convert JSON dict to RelationalGraphWithCuts instance."""
    
    # Parse vertices
    vertices = frozenset([
        Vertex(
            id=v_data["id"],
            label=v_data.get("label"),
            is_generic=v_data.get("is_generic", True)
        )
        for v_data in data.get("V", [])
    ])
    
    # Parse edges
    edges = frozenset([
        Edge(id=e_data["id"])
        for e_data in data.get("E", [])
    ])
    
    # Parse cuts
    cuts = frozenset([
        Cut(id=c_data["id"])
        for c_data in data.get("Cut", [])
    ])
    
    # Parse nu mapping (edge -> vertex sequence)
    nu_data = data.get("nu", {})
    nu_mapping = frozendict({
        edge_id: tuple(vertex_ids) if isinstance(vertex_ids, list) else vertex_ids
        for edge_id, vertex_ids in nu_data.items()
    })
    
    # Parse area mapping
    area_data = data.get("area", {})
    area_mapping = frozendict({
        context_id: frozenset(element_ids)
        for context_id, element_ids in area_data.items()
    })
    
    # Parse relation mapping
    rel_data = data.get("rel", {})
    rel_mapping = frozendict(rel_data)
    
    # Parse sheet
    sheet = data.get("sheet", "default_sheet")
    
    # Parse optional alphabet
    alphabet = None
    if "alphabet" in data:
        alphabet_data = data["alphabet"]
        alphabet = AlphabetDAU(
            C=frozenset(alphabet_data.get("C", [])),
            F=frozenset(alphabet_data.get("F", [])),
            R=frozenset(alphabet_data.get("R", [])),
            ar=frozendict(alphabet_data.get("ar", {}))
        )
    
    # Parse optional rho mapping
    rho_data = data.get("rho", {})
    rho_mapping = frozendict(rho_data)
    
    # Create EGI instance
    egi = RelationalGraphWithCuts(
        V=vertices,
        E=edges,
        nu=nu_mapping,
        sheet=sheet,
        Cut=cuts,
        area=area_mapping,
        rel=rel_mapping,
        alphabet=alphabet,
        rho=rho_mapping
    )
    
    return egi


def serialize_egi_to_dict(egi: RelationalGraphWithCuts) -> Dict[str, Any]:
    """Convert RelationalGraphWithCuts instance to JSON dict."""
    
    # Convert vertices
    vertices_data = [
        {
            "id": v.id,
            "label": v.label,
            "is_generic": v.is_generic
        }
        for v in egi.V
    ]
    
    # Convert edges
    edges_data = [
        {"id": e.id}
        for e in egi.E
    ]
    
    # Convert cuts
    cuts_data = [
        {"id": c.id}
        for c in egi.Cut
    ]
    
    # Convert nu mapping
    nu_data = {
        edge_id: list(vertex_seq) if isinstance(vertex_seq, tuple) else vertex_seq
        for edge_id, vertex_seq in egi.nu.items()
    }
    
    # Convert area mapping
    area_data = {
        context_id: list(element_set)
        for context_id, element_set in egi.area.items()
    }
    
    # Convert relation mapping
    rel_data = dict(egi.rel)
    
    # Build result
    result = {
        "V": vertices_data,
        "E": edges_data,
        "Cut": cuts_data,
        "nu": nu_data,
        "area": area_data,
        "rel": rel_data,
        "sheet": egi.sheet
    }
    
    # Add optional components
    if egi.alphabet:
        result["alphabet"] = {
            "C": list(egi.alphabet.C),
            "F": list(egi.alphabet.F),
            "R": list(egi.alphabet.R),
            "ar": dict(egi.alphabet.ar)
        }
    
    if egi.rho:
        result["rho"] = dict(egi.rho)
    
    return result


def save_egi_to_json(egi: RelationalGraphWithCuts, file_path: str):
    """Save EGI to JSON file."""
    data = serialize_egi_to_dict(egi)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)


# Convenience functions for common corpus files
def load_dau_ligature_example() -> RelationalGraphWithCuts:
    """Load the Dau 2006 p112 ligature example."""
    return load_egi_from_json(
        "/Users/mjh/Sync/GitHub/Arisbe/corpus/graphs/dau_2006_p112_ligature/dau_2006_p112_ligature.egi.json"
    )


def load_peirce_modus_ponens() -> RelationalGraphWithCuts:
    """Load the Peirce modus ponens example."""
    return load_egi_from_json(
        "/Users/mjh/Sync/GitHub/Arisbe/corpus/graphs/peirce_modus_ponens/peirce_modus_ponens.egi.json"
    )


def load_mixed_quantifier_complex() -> RelationalGraphWithCuts:
    """Load the mixed quantifier complex example."""
    return load_egi_from_json(
        "/Users/mjh/Sync/GitHub/Arisbe/corpus/graphs/mixed_quantifier_complex/mixed_quantifier_complex.egi.json"
    )
