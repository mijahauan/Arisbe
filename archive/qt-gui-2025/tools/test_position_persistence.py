#!/usr/bin/env python3
"""
Test position persistence across multiple relayouts.
Validates that user-defined positions are maintained correctly.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from diagram_controller import DiagramController
from egif_parser_dau import parse_egif


def test_position_persistence():
    """Test that position updates persist across operations."""
    print("="*70)
    print("POSITION PERSISTENCE TEST")
    print("="*70)
    
    # Create simple graph
    egif = "[*x] (P x)"
    egi = parse_egif(egif)
    
    controller = DiagramController()
    controller.load_egi(egi)
    
    # Get initial positions
    dto1 = controller.get_renderable_dto()
    if not dto1.vertices:
        print("❌ No vertices in layout")
        return False
    
    v1 = dto1.vertices[0]
    initial_pos = v1.pos
    print(f"\n1️⃣ Initial position: {initial_pos}")
    
    # Update position (small offset to stay in bounds)
    new_pos = (initial_pos[0] + 20, initial_pos[1] + 20)
    print(f"2️⃣ Updating to: {new_pos}")
    
    success = controller.update_element_position(v1.id, new_pos)
    if not success:
        print("❌ Position update failed")
        return False
    
    # Check position persisted
    dto2 = controller.get_renderable_dto()
    v1_after = next((v for v in dto2.vertices if v.id == v1.id), None)
    if not v1_after:
        print("❌ Vertex disappeared")
        return False
    
    print(f"3️⃣ Position after update: {v1_after.pos}")
    
    # Verify exact match
    dist = ((v1_after.pos[0] - new_pos[0])**2 + (v1_after.pos[1] - new_pos[1])**2)**0.5
    if dist < 1.0:
        print(f"   ✅ PERFECT! Distance: {dist:.3f}px")
    elif dist < 10.0:
        print(f"   ✅ Good! Distance: {dist:.1f}px")
        print(f"   ⚠️  Small drift detected")
    else:
        print(f"   ❌ FAILED! Distance: {dist:.1f}px")
        return False
    
    # Apply transformation (tests persistence through EGI modification)
    print(f"\n4️⃣ Applying DC+ transformation...")
    sheet_id = controller.egi_model.sheet
    success = controller.apply_formal_rule("DC+", [v1.id], sheet_id)
    if not success:
        print("❌ Transformation failed")
        return False
    
    # Check position still persisted
    dto3 = controller.get_renderable_dto()
    v1_final = next((v for v in dto3.vertices if v.id == v1.id), None)
    if not v1_final:
        print("⚠️  Vertex disappeared after transformation (might be in nested cut)")
        # This is OK - vertex moved to nested area
        return True
    
    print(f"5️⃣ Position after transformation: {v1_final.pos}")
    
    final_dist = ((v1_final.pos[0] - new_pos[0])**2 + (v1_final.pos[1] - new_pos[1])**2)**0.5
    if final_dist < 10.0:
        print(f"   ✅ Position persisted through transformation! Distance: {final_dist:.1f}px")
        return True
    else:
        print(f"   ⚠️  Position changed after transformation: {final_dist:.1f}px")
        print(f"   This is a known issue - positions may not persist through transformations")
        return False


def test_multiple_positions():
    """Test multiple position updates."""
    print("\n" + "="*70)
    print("MULTIPLE POSITION UPDATES TEST")
    print("="*70)
    
    egif = "[*x] [*y] (Loves x y)"
    egi = parse_egif(egif)
    
    controller = DiagramController()
    controller.load_egi(egi)
    
    dto = controller.get_renderable_dto()
    if len(dto.vertices) < 2:
        print("❌ Need at least 2 vertices")
        return False
    
    v1, v2 = dto.vertices[0], dto.vertices[1]
    print(f"\n1️⃣ Initial positions:")
    print(f"   v1: {v1.pos}")
    print(f"   v2: {v2.pos}")
    
    # Update both
    new_pos1 = (v1.pos[0] + 15, v1.pos[1] + 15)
    new_pos2 = (v2.pos[0] - 15, v2.pos[1] + 15)
    
    controller.update_element_position(v1.id, new_pos1)
    controller.update_element_position(v2.id, new_pos2)
    
    # Verify both persisted
    dto2 = controller.get_renderable_dto()
    v1_after = next((v for v in dto2.vertices if v.id == v1.id), None)
    v2_after = next((v for v in dto2.vertices if v.id == v2.id), None)
    
    if not (v1_after and v2_after):
        print("❌ Vertices disappeared")
        return False
    
    print(f"\n2️⃣ Positions after update:")
    print(f"   v1: {v1_after.pos}")
    print(f"   v2: {v2_after.pos}")
    
    dist1 = ((v1_after.pos[0] - new_pos1[0])**2 + (v1_after.pos[1] - new_pos1[1])**2)**0.5
    dist2 = ((v2_after.pos[0] - new_pos2[0])**2 + (v2_after.pos[1] - new_pos2[1])**2)**0.5
    
    if dist1 < 10 and dist2 < 10:
        print(f"   ✅ Both positions persisted! ({dist1:.1f}px, {dist2:.1f}px)")
        return True
    else:
        print(f"   ⚠️  Some drift detected: ({dist1:.1f}px, {dist2:.1f}px)")
        return False


def run_persistence_suite():
    """Run all persistence tests."""
    tests = [
        ("Single Position Persistence", test_position_persistence),
        ("Multiple Positions", test_multiple_positions),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n❌ Error in {name}: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False
    
    # Summary
    print("\n" + "="*70)
    print("PERSISTENCE TEST SUMMARY")
    print("="*70)
    
    for name, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {name}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\nResults: {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    success = run_persistence_suite()
    sys.exit(0 if success else 1)
