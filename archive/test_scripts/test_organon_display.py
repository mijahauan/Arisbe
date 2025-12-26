#!/usr/bin/env python3
"""
Test Organon GUI integration with UnifiedD3Engine.
Simulates loading and displaying a graph through DiagramController.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from diagram_controller import DiagramController
from entity_storage import EntityStorageManager
from egif_parser_dau import parse_egif

print("Testing Organon Integration with UnifiedD3Engine")
print("=" * 70)

# Test 1: Load from corpus
print("\n1. Testing with corpus entity...")
try:
    corpus_path = Path(__file__).parent / "corpus" / "graphs"
    storage = EntityStorageManager(corpus_path)
    entities = storage.list_entities()
    
    if entities:
        entity = storage.load_entity(entities[0])
        print(f"   ✅ Loaded entity: {entities[0]}")
        print(f"   - Vertices: {len(entity.current_egi.V)}")
        print(f"   - Edges: {len(entity.current_egi.E)}")
        print(f"   - Cuts: {len(entity.current_egi.Cut)}")
        
        controller = DiagramController()
        success = controller.load_egi(entity.current_egi)
        
        if success:
            dto = controller.get_renderable_dto()
            if dto:
                print(f"   ✅ Layout generated!")
                print(f"   - Vertex positions: {len(dto.vertex_positions)}")
                print(f"   - Predicate positions: {len(dto.predicate_positions)}")
                print(f"   - Cut bounds: {len(dto.cut_bounds)}")
                print(f"   - Viewport: ({dto.viewport_bounds.min_x:.1f}, {dto.viewport_bounds.min_y:.1f}) -> ({dto.viewport_bounds.max_x:.1f}, {dto.viewport_bounds.max_y:.1f})")
            else:
                print(f"   ❌ No DTO returned")
        else:
            print(f"   ❌ Failed to load EGI into controller")
    else:
        print(f"   ⚠️  No entities in corpus, skipping")
except Exception as e:
    import traceback
    print(f"   ❌ Corpus test failed: {e}")
    traceback.print_exc()

# Test 2: Load from EGIF
print("\n2. Testing with parsed EGIF...")
try:
    test_egif = "[*s] (Human s) ~[ (Mortal s) ]"
    egi = parse_egif(test_egif)
    print(f"   ✅ Parsed EGIF: {test_egif}")
    
    controller = DiagramController()
    success = controller.load_egi(egi)
    
    if success:
        dto = controller.get_renderable_dto()
        if dto:
            print(f"   ✅ Layout generated!")
            print(f"   - Vertex positions: {len(dto.vertex_positions)}")
            print(f"   - Predicate positions: {len(dto.predicate_positions)}")
            print(f"   - Cut bounds: {len(dto.cut_bounds)}")
            
            # Show positions
            print(f"\n   Position details:")
            for vid, pos in dto.vertex_positions.items():
                print(f"   - Vertex {vid[:8]}: ({pos.x:.1f}, {pos.y:.1f})")
            for pid, pos in dto.predicate_positions.items():
                depth = dto.containment_depth.get(pid, 0)
                print(f"   - Predicate {pid[:8]}: ({pos.x:.1f}, {pos.y:.1f}) [depth={depth}]")
            for cid, bounds in dto.cut_bounds.items():
                w = bounds.max_x - bounds.min_x
                h = bounds.max_y - bounds.min_y
                print(f"   - Cut {cid[:8]}: {w:.1f}x{h:.1f}")
        else:
            print(f"   ❌ No DTO returned")
    else:
        print(f"   ❌ Failed to load EGI into controller")
        
except Exception as e:
    import traceback
    print(f"   ❌ EGIF test failed: {e}")
    traceback.print_exc()

print("\n" + "=" * 70)
print("✅ Organon integration test complete!")
print("\nThe Organon GUI should now be able to display graphs using the")
print("new Unified Single-Simulation D3 layout engine.")
