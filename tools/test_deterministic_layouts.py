#!/usr/bin/env python3
"""
Test that deterministic seeding produces identical layouts.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from entity_storage import EntityStorageManager
from style_loader import StyleLoader
from definitive_three_pass_engine import DefinitiveThreePassEngine, LayoutDeltas


def test_deterministic_seeding():
    """Test that same seed produces identical layouts."""
    print("="*70)
    print("DETERMINISTIC SEEDING TEST")
    print("="*70)
    
    storage = EntityStorageManager(Path("tomos/graphs"))
    entity = storage.load_entity("peirce_modus_ponens")
    egi = entity.current_egi
    style = StyleLoader().load_default_style()
    
    # Generate with seed=42 (first time)
    print("\n1️⃣ First generation (seed=42)...")
    deltas1 = LayoutDeltas()
    deltas1.deterministic_seed = 42
    
    engine1 = DefinitiveThreePassEngine()
    dto1 = engine1.generate_layout(egi, style, layout_deltas=deltas1)
    
    # Generate with seed=42 (second time)
    print("\n2️⃣ Second generation (seed=42)...")
    deltas2 = LayoutDeltas()
    deltas2.deterministic_seed = 42
    
    engine2 = DefinitiveThreePassEngine()
    dto2 = engine2.generate_layout(egi, style, layout_deltas=deltas2)
    
    # Compare positions
    print("\n3️⃣ Comparing positions...")
    
    if len(dto1.vertices) != len(dto2.vertices):
        print(f"❌ Different vertex counts: {len(dto1.vertices)} vs {len(dto2.vertices)}")
        return False
    
    max_diff = 0.0
    for v1, v2 in zip(dto1.vertices, dto2.vertices):
        if v1.id != v2.id:
            print(f"❌ Vertex order differs")
            return False
        
        diff = ((v1.pos[0] - v2.pos[0])**2 + (v1.pos[1] - v2.pos[1])**2)**0.5
        max_diff = max(max_diff, diff)
    
    if max_diff < 0.01:
        print(f"   ✅ PERFECT! Identical positions (max diff: {max_diff:.6f}px)")
        return True
    else:
        print(f"   ❌ Positions differ (max diff: {max_diff:.2f}px)")
        return False


def test_different_seeds():
    """Test that different seeds produce different layouts."""
    print("\n" + "="*70)
    print("DIFFERENT SEEDS TEST")
    print("="*70)
    
    storage = EntityStorageManager(Path("tomos/graphs"))
    entity = storage.load_entity("peirce_modus_ponens")
    egi = entity.current_egi
    style = StyleLoader().load_default_style()
    
    # Generate with seed=42
    deltas1 = LayoutDeltas()
    deltas1.deterministic_seed = 42
    
    engine1 = DefinitiveThreePassEngine()
    dto1 = engine1.generate_layout(egi, style, layout_deltas=deltas1)
    
    # Generate with seed=99
    deltas2 = LayoutDeltas()
    deltas2.deterministic_seed = 99
    
    engine2 = DefinitiveThreePassEngine()
    dto2 = engine2.generate_layout(egi, style, layout_deltas=deltas2)
    
    # Positions should differ
    max_diff = 0.0
    for v1, v2 in zip(dto1.vertices, dto2.vertices):
        diff = ((v1.pos[0] - v2.pos[0])**2 + (v1.pos[1] - v2.pos[1])**2)**0.5
        max_diff = max(max_diff, diff)
    
    if max_diff > 1.0:
        print(f"   ✅ Different seeds produce different layouts (diff: {max_diff:.1f}px)")
        return True
    else:
        print(f"   ⚠️  Seeds should produce different results (diff: {max_diff:.2f}px)")
        return False


if __name__ == "__main__":
    test1 = test_deterministic_seeding()
    test2 = test_different_seeds()
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"{'✅' if test1 else '❌'} Deterministic seeding")
    print(f"{'✅' if test2 else '❌'} Different seeds")
    
    sys.exit(0 if (test1 and test2) else 1)
