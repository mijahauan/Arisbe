#!/usr/bin/env python3
"""
Test script to verify EGI DTO handoff between Organon and Ergasterion.
"""

import sys
import os
from pathlib import Path

# Add src to path
repo_root = Path(__file__).parent
src_dir = repo_root / "src"
sys.path.insert(0, str(src_dir))

from egi_dto import EGIStateDTO, VertexDTO, EdgeDTO, CutDTO, SpatialInfo, egi_to_dto
from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut, AlphabetDAU
import corpus_index as cidx

def test_dto_conversion():
    """Test converting EGI to DTO and back."""
    print("Testing EGI DTO conversion...")
    
    # Load a sample graph from corpus
    corpus_dir = repo_root / "corpus" / "graphs" / "peirce_cp_4_394_man_mortal"
    if not corpus_dir.exists():
        print(f"Corpus directory not found: {corpus_dir}")
        return False
    
    try:
        # Load EGI from corpus
        from egi_system import create_egi_system
        egi_system = create_egi_system()
        
        egi_path = corpus_dir / "peirce_cp_4_394_man_mortal.egi.json"
        if not egi_path.exists():
            print(f"EGI file not found: {egi_path}")
            return False
        
        import json
        with open(egi_path, 'r') as f:
            egi_data = json.load(f)
        
        # Convert to RelationalGraphWithCuts using the same method as Organon
        from egi_core_dau import Vertex, Edge, Cut, AlphabetDAU
        from frozendict import frozendict
        
        # Build vertices
        V = []
        rho_map = egi_data.get("rho", {})
        for v_obj in egi_data.get("V", []):
            if isinstance(v_obj, dict):
                vid = v_obj.get("id")
                label = v_obj.get("label", rho_map.get(vid, ""))
                is_generic = v_obj.get("is_generic", True)
                V.append(Vertex(id=vid, label=label, is_generic=is_generic))
            else:
                V.append(Vertex(id=v_obj, label=rho_map.get(v_obj, ""), is_generic=True))
        
        # Build edges
        E = []
        for e_obj in egi_data.get("E", []):
            if isinstance(e_obj, dict):
                E.append(Edge(id=e_obj.get("id")))
            else:
                E.append(Edge(id=e_obj))
        
        # Build cuts
        CutSet = []
        for c_obj in egi_data.get("Cut", []):
            if isinstance(c_obj, dict):
                CutSet.append(Cut(id=c_obj.get("id")))
            else:
                CutSet.append(Cut(id=c_obj))
        
        # Build mappings
        nu = frozendict({k: tuple(v) for k, v in (egi_data.get("nu") or {}).items()})
        rel = frozendict(dict(egi_data.get("rel") or {}))
        area = frozendict({k: frozenset(v) for k, v in (egi_data.get("area") or {}).items()})
        rho = frozendict(dict(rho_map))
        
        alph_data = egi_data.get("alphabet") or {}
        alph = AlphabetDAU(
            C=frozenset(alph_data.get("C") or []),
            F=frozenset(alph_data.get("F") or []),
            R=frozenset(alph_data.get("R") or []),
            ar=frozendict(alph_data.get("ar") or {}),
        ).with_defaults()
        
        graph = RelationalGraphWithCuts(
            V=frozenset(V),
            E=frozenset(E),
            nu=nu,
            sheet=egi_data.get("sheet", "sheet"),
            Cut=frozenset(CutSet),
            area=area,
            rel=rel,
            rho=rho,
            alphabet=alph
        )
        
        print(f"Loaded graph with {len(graph.V)} vertices, {len(graph.E)} edges, {len(graph.Cut)} cuts")
        
        # Convert to DTO
        dto = egi_to_dto(graph)
        print(f"Converted to DTO with {len(dto.vertices)} vertices, {len(dto.edges)} edges, {len(dto.cuts)} cuts")
        
        # Verify DTO structure
        assert len(dto.vertices) == len(graph.V)
        assert len(dto.edges) == len(graph.E) 
        assert len(dto.cuts) == len(graph.Cut)
        
        print("✅ DTO conversion successful!")
        return True
        
    except Exception as e:
        print(f"❌ DTO conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_handoff_payload():
    """Test creating handoff payload like Organon does."""
    print("\nTesting handoff payload creation...")
    
    try:
        # Simulate Organon's _build_handoff_payload
        corpus_dir = repo_root / "corpus" / "graphs" / "peirce_cp_4_394_man_mortal"
        
        egi_path = corpus_dir / "peirce_cp_4_394_man_mortal.egi.json"
        import json
        with open(egi_path, 'r') as f:
            egi_data = json.load(f)
        
        # Convert to RelationalGraphWithCuts using the same method as Organon
        from egi_core_dau import Vertex, Edge, Cut, AlphabetDAU
        from frozendict import frozendict
        
        # Build vertices
        V = []
        rho_map = egi_data.get("rho", {})
        for v_obj in egi_data.get("V", []):
            if isinstance(v_obj, dict):
                vid = v_obj.get("id")
                label = v_obj.get("label", rho_map.get(vid, ""))
                is_generic = v_obj.get("is_generic", True)
                V.append(Vertex(id=vid, label=label, is_generic=is_generic))
            else:
                V.append(Vertex(id=v_obj, label=rho_map.get(v_obj, ""), is_generic=True))
        
        # Build edges
        E = []
        for e_obj in egi_data.get("E", []):
            if isinstance(e_obj, dict):
                E.append(Edge(id=e_obj.get("id")))
            else:
                E.append(Edge(id=e_obj))
        
        # Build cuts
        CutSet = []
        for c_obj in egi_data.get("Cut", []):
            if isinstance(c_obj, dict):
                CutSet.append(Cut(id=c_obj.get("id")))
            else:
                CutSet.append(Cut(id=c_obj))
        
        # Build mappings
        nu = frozendict({k: tuple(v) for k, v in (egi_data.get("nu") or {}).items()})
        rel = frozendict(dict(egi_data.get("rel") or {}))
        area = frozendict({k: frozenset(v) for k, v in (egi_data.get("area") or {}).items()})
        rho = frozendict(dict(rho_map))
        
        alph_data = egi_data.get("alphabet") or {}
        alph = AlphabetDAU(
            C=frozenset(alph_data.get("C") or []),
            F=frozenset(alph_data.get("F") or []),
            R=frozenset(alph_data.get("R") or []),
            ar=frozendict(alph_data.get("ar") or {}),
        ).with_defaults()
        
        graph = RelationalGraphWithCuts(
            V=frozenset(V),
            E=frozenset(E),
            nu=nu,
            sheet=egi_data.get("sheet", "sheet"),
            Cut=frozenset(CutSet),
            area=area,
            rel=rel,
            rho=rho,
            alphabet=alph
        )
        egi_dto = egi_to_dto(graph)
        
        # Create payload like Organon
        payload = {
            "source_path": str(corpus_dir),
            "graph_dir": str(corpus_dir),
            "egi_dto": egi_dto,
            "style_id": "default",
        }
        
        print(f"Created payload with DTO containing {len(egi_dto.vertices)} elements")
        print("✅ Handoff payload creation successful!")
        return True
        
    except Exception as e:
        print(f"❌ Handoff payload creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing EGI DTO Handoff System")
    print("=" * 40)
    
    success = True
    success &= test_dto_conversion()
    success &= test_handoff_payload()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 All tests passed! DTO handoff system is working.")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    sys.exit(0 if success else 1)
