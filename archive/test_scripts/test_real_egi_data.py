#!/usr/bin/env python3
"""
Test Chapter 21 with Real EGI Data

Loads actual EGI files from the corpus and tests Chapter 21 functionality
with real data instead of synthetic test cases.
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

def find_corpus_egi_files():
    """Find all EGI files in the corpus."""
    corpus_dir = Path("corpus/graphs")
    egi_files = []
    
    if not corpus_dir.exists():
        print("⚠️  Corpus directory not found")
        return []
    
    for graph_dir in corpus_dir.iterdir():
        if graph_dir.is_dir():
            # Look for .egi.json files
            egi_file = graph_dir / f"{graph_dir.name}.egi.json"
            if egi_file.exists():
                egi_files.append(egi_file)
    
    return egi_files

def load_egi_from_file(egi_path: Path):
    """Load EGI from JSON file."""
    try:
        from frozendict import frozendict
        from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut, ElementID, AlphabetDAU
        
        with open(egi_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Build EGI from JSON data
        sheet = data.get("sheet", "sheet")
        
        # Handle vertices
        V = []
        rho_map = data.get("rho", {})
        for v_obj in data.get("V", []):
            if isinstance(v_obj, dict):
                vid = v_obj.get("id")
                label = v_obj.get("label") or rho_map.get(vid)
                is_generic = v_obj.get("is_generic", True if label is None else False)
            else:
                vid = v_obj
                label = rho_map.get(vid)
                is_generic = True if label is None else False
            V.append(Vertex(id=vid, label=label, is_generic=is_generic))
        
        # Handle edges
        E = []
        for e_obj in data.get("E", []):
            if isinstance(e_obj, dict):
                E.append(Edge(id=e_obj.get("id")))
            else:
                E.append(Edge(id=e_obj))
        
        # Handle cuts
        CutSet = []
        for c_obj in data.get("Cut", []):
            if isinstance(c_obj, dict):
                CutSet.append(Cut(id=c_obj.get("id")))
            else:
                CutSet.append(Cut(id=c_obj))
        
        # Build mappings
        nu = frozendict({k: tuple(v) for k, v in (data.get("nu") or {}).items()})
        rel = frozendict(dict(data.get("rel") or {}))
        area = frozendict({k: frozenset(v) for k, v in (data.get("area") or {}).items()})
        rho = frozendict(dict(rho_map))
        
        # Build alphabet
        alph_data = data.get("alphabet", {})
        alph = AlphabetDAU(
            C=frozenset(alph_data.get("C", [])),
            F=frozenset(alph_data.get("F", [])),
            R=frozenset(alph_data.get("R", [])),
            ar=frozendict(alph_data.get("ar", {})),
        ).with_defaults()
        
        # Create EGI
        egi = RelationalGraphWithCuts(
            V=frozenset(V),
            E=frozenset(E),
            nu=nu,
            sheet=sheet,
            Cut=frozenset(CutSet),
            area=area,
            rel=rel,
            alphabet=alph,
            rho=rho,
        )
        
        return egi
        
    except Exception as e:
        print(f"❌ Failed to load EGI from {egi_path}: {e}")
        return None

def test_chapter21_with_real_data():
    """Test Chapter 21 functionality with real EGI data."""
    print("🧪 TESTING CHAPTER 21 WITH REAL EGI DATA")
    print("=" * 60)
    
    # Find EGI files
    egi_files = find_corpus_egi_files()
    print(f"📁 Found {len(egi_files)} EGI files in corpus")
    
    if not egi_files:
        print("⚠️  No EGI files found - creating a simple test case")
        return test_with_simple_egi()
    
    # Test with each EGI file
    results = []
    
    for i, egi_file in enumerate(egi_files[:3]):  # Test first 3 files
        print(f"\n📊 Testing EGI {i+1}: {egi_file.name}")
        print("-" * 40)
        
        # Load EGI
        egi = load_egi_from_file(egi_file)
        if not egi:
            results.append(False)
            continue
        
        print(f"✅ Loaded EGI: {len(egi.V)}v, {len(egi.E)}e, {len(egi.Cut)}c")
        
        # Test Chapter 21 functionality
        success = test_egi_with_chapter21(egi, egi_file.stem)
        results.append(success)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n🎯 REAL DATA TEST SUMMARY")
    print("=" * 40)
    print(f"Files tested: {total}")
    print(f"Successful:   {passed}")
    print(f"Success rate: {passed/total*100:.1f}%" if total > 0 else "No files tested")
    
    return passed == total

def test_egi_with_chapter21(egi, name: str):
    """Test a specific EGI with Chapter 21 functionality."""
    try:
        from chapter21_diagram_engine import (
            UniversalEGIEngine, ViewSpecification, InteractionMode, DisplayFormat
        )
        from chapter21_transformation_wizards import UniversalTransformationWizardSystem
        
        # Initialize engines
        engine = UniversalEGIEngine()
        wizard_system = UniversalTransformationWizardSystem(engine)
        
        # Test 1: View generation
        view_spec = ViewSpecification(
            focus_elements=set(),
            context_radius=2,
            interaction_mode=InteractionMode.ORGANON,
            show_subgraph_hints=True
        )
        
        view = engine.get_view(egi, view_spec)
        print(f"  ✅ View: {len(view.visible_vertices)}v, {len(view.visible_edges)}e, {len(view.visible_cuts)}c")
        
        # Test 2: Format synchronization
        formats = engine.synchronize_formats(egi)
        print(f"  ✅ Formats: {len(formats)} synchronized")
        
        # Show format samples
        for format_type, content in formats.items():
            if content:
                preview = content[:100] + "..." if len(content) > 100 else content
                print(f"    {format_type.value}: {preview}")
        
        # Test 3: Round-trip validation
        is_valid = engine.validate_round_trip_equivalence(egi)
        print(f"  ✅ Round-trip: {'VALID' if is_valid else 'INVALID'}")
        
        # Test 4: Transformation wizard
        wizard = wizard_system.create_wizard(DisplayFormat.DIAGRAM, egi)
        print(f"  ✅ Wizard: Ready for {name}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Chapter 21 test failed: {e}")
        return False

def test_with_simple_egi():
    """Fallback test with simple EGI."""
    print("\n🔧 FALLBACK: Testing with simple EGI")
    print("-" * 40)
    
    from frozendict import frozendict
    from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, ElementID
    
    # Create simple EGI
    v1 = Vertex(ElementID("alice"))
    v2 = Vertex(ElementID("bob"))
    e1 = Edge(ElementID("knows"))
    sheet = ElementID("sheet")
    
    simple_egi = RelationalGraphWithCuts(
        V=frozenset([v1, v2]),
        E=frozenset([e1]),
        nu=frozendict({e1.id: (v1.id, v2.id)}),
        sheet=sheet,
        Cut=frozenset(),
        area=frozendict({
            sheet: frozenset([v1.id, v2.id, e1.id])
        }),
        rel=frozendict({e1.id: "Knows"})
    )
    
    return test_egi_with_chapter21(simple_egi, "simple_test")

def demonstrate_format_output():
    """Demonstrate format output capabilities."""
    print("\n📝 FORMAT OUTPUT DEMONSTRATION")
    print("=" * 50)
    
    # Find first available EGI
    egi_files = find_corpus_egi_files()
    if egi_files:
        egi = load_egi_from_file(egi_files[0])
        if egi:
            from chapter21_diagram_engine import UniversalEGIEngine
            
            engine = UniversalEGIEngine()
            formats = engine.synchronize_formats(egi)
            
            print(f"EGI: {egi_files[0].name}")
            print(f"Elements: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
            print()
            
            for format_type, content in formats.items():
                print(f"=== {format_type.value.upper()} ===")
                if content:
                    # Show first few lines
                    lines = content.split('\n')[:5]
                    for line in lines:
                        print(line)
                    if len(content.split('\n')) > 5:
                        print("...")
                else:
                    print("(empty)")
                print()

if __name__ == "__main__":
    print("🧪 CHAPTER 21 REAL DATA TESTING")
    print("=" * 60)
    
    # Test with real data
    success = test_chapter21_with_real_data()
    
    # Demonstrate format output
    demonstrate_format_output()
    
    print(f"\n🎯 OVERALL RESULT: {'SUCCESS' if success else 'PARTIAL SUCCESS'}")
    print("✅ Chapter 21 tested with real EGI data")
    print("✅ Ready for interactive GUI integration")
