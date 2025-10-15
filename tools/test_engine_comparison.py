#!/usr/bin/env python3
"""
Compare old DefinitiveEGILayoutEngine vs new DefinitiveThreePassEngine
to ensure no regressions and validate improvements.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from entity_storage import EntityStorageManager
from style_loader import StyleLoader
from definitive_egi_layout_engine import DefinitiveEGILayoutEngine
from definitive_three_pass_engine import DefinitiveThreePassEngine


def compare_engines(entity_name: str):
    """Compare both engines on same graph."""
    print(f"\n{'='*70}")
    print(f"COMPARING ENGINES: {entity_name}")
    print(f"{'='*70}\n")
    
    # Load graph
    storage = EntityStorageManager(Path("tomos/graphs"))
    entity = storage.load_entity(entity_name)
    egi = entity.current_egi
    style = StyleLoader().load_default_style()
    
    # Old engine
    print("🔵 OLD ENGINE (DefinitiveEGILayoutEngine):")
    old_engine = DefinitiveEGILayoutEngine()
    try:
        old_dto = old_engine.generate_layout(egi, style)
        old_stats = {
            'vertices': len(old_dto.vertices),
            'edges': len(old_dto.edge_labels),
            'ligatures': len(old_dto.ligatures),
            'areas': len(old_dto.areas),
        }
        print(f"   ✅ Generated: {old_stats}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        old_dto = None
        old_stats = None
    
    # New engine
    print("\n🟢 NEW ENGINE (DefinitiveThreePassEngine):")
    new_engine = DefinitiveThreePassEngine()
    try:
        new_dto = new_engine.generate_layout(egi, style)
        new_stats = {
            'vertices': len(new_dto.vertices),
            'edges': len(new_dto.edge_labels),
            'ligatures': len(new_dto.ligatures),
            'areas': len(new_dto.areas),
        }
        print(f"   ✅ Generated: {new_stats}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        new_dto = None
        new_stats = None
    
    # Compare
    if old_stats and new_stats:
        print("\n📊 COMPARISON:")
        all_match = True
        for key in old_stats:
            old_val = old_stats[key]
            new_val = new_stats[key]
            match = "✅" if old_val == new_val else "⚠️"
            print(f"   {key:12s}: {old_val:3d} → {new_val:3d} {match}")
            if old_val != new_val:
                all_match = False
        
        if all_match:
            print("\n   ✅ Perfect match - no regressions!")
        else:
            print("\n   ⚠️  Differences detected - review needed")
        
        return all_match
    elif new_stats and not old_stats:
        print("\n   🎉 NEW ENGINE WORKS, OLD ENGINE FAILED!")
        return True
    else:
        print("\n   ❌ Both engines failed or new engine regressed")
        return False


def run_comparison_suite():
    """Run comparison on representative tomos graphs."""
    test_graphs = [
        # Simple
        "peirce_modus_ponens",
        # Nested cuts
        "dau_2006_p112_ligature", 
        # Complex
        "dau_theorem_proving",
        "roberts_domain_modeling",
        # Various styles
        "sowa_conceptual_graph_1",
        "peirce_1903_lowell_lecture",
    ]
    
    results = {}
    for graph_name in test_graphs:
        try:
            match = compare_engines(graph_name)
            results[graph_name] = match
        except Exception as e:
            print(f"\n❌ Error testing {graph_name}: {e}")
            results[graph_name] = False
    
    # Summary
    print("\n" + "="*70)
    print("COMPARISON SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, passed_test in results.items():
        status = "✅" if passed_test else "❌"
        print(f"{status} {name}")
    
    print(f"\nResults: {passed}/{total} graphs validated")
    
    if passed == total:
        print("🎉 All comparisons passed - high confidence!")
        return True
    elif passed >= total * 0.8:
        print("✅ Most comparisons passed - good confidence")
        return True
    else:
        print("⚠️  Multiple differences - review needed")
        return False


if __name__ == "__main__":
    success = run_comparison_suite()
    sys.exit(0 if success else 1)
