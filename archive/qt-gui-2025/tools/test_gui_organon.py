"""
Smoke test for Organon GUI functionality.

Tests that all components import and integrate correctly.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_imports():
    """Test that all GUI components import."""
    print("🔍 Testing imports...")
    
    # Core components
    from graph_entity import GraphEntity, EntityMetadata
    from entity_storage import EntityStorageManager
    print("  ✅ Core entity system")
    
    # GUI components
    from gui_clean.common.diagram_canvas import DiagramCanvas
    print("  ✅ DiagramCanvas")
    
    from gui_clean.organon.tomos_browser import TomosBrowserWidget
    print("  ✅ TomosBrowserWidget")
    
    from gui_clean.organon.organon_mode import OrganonMode
    print("  ✅ OrganonMode")
    
    from gui_clean.main_window import MainWindow
    print("  ✅ MainWindow")
    
    print()
    return True


def test_corpus_access():
    """Test tomos access."""
    print("🔍 Testing tomos access...")
    
    from entity_storage import EntityStorageManager
    from pathlib import Path
    
    corpus_path = Path(__file__).parent.parent / "corpus" / "graphs"
    storage = EntityStorageManager(corpus_path)
    
    # List entities
    entities = storage.list_entities()
    print(f"  ✅ Found {len(entities)} entities")
    
    if entities:
        # Load one
        entity = storage.load_entity(entities[0])
        print(f"  ✅ Loaded entity: {entity.name}")
        
        # Get EGIF
        egif = entity.get_current_egif()
        print(f"  ✅ Generated EGIF ({len(egif)} chars)")
    
    print()
    return True


def test_diagram_controller():
    """Test DiagramController integration."""
    print("🔍 Testing DiagramController...")
    
    from diagram_controller import DiagramController
    from entity_storage import EntityStorageManager
    from pathlib import Path
    
    corpus_path = Path(__file__).parent.parent / "corpus" / "graphs"
    storage = EntityStorageManager(corpus_path)
    
    entities = storage.list_entities()
    if not entities:
        print("  ⚠️  No entities to test with")
        return True
    
    # Load entity
    entity = storage.load_entity(entities[0])
    
    # Load into controller
    controller = DiagramController()
    controller.load_egi(entity.current_egi)
    print("  ✅ Loaded EGI into controller")
    
    # Get DTO
    dto = controller.get_renderable_dto()
    print(f"  ✅ Generated LayoutDTO ({len(dto.vertex_positions)} vertices, {len(dto.predicate_positions)} predicates)")
    
    print()
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("ORGANON GUI SMOKE TEST")
    print("=" * 60)
    print()
    
    tests = [
        ("Imports", test_imports),
        ("Tomos Access", test_corpus_access),
        ("DiagramController", test_diagram_controller),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"  ❌ {name} failed")
        except Exception as e:
            failed += 1
            print(f"  ❌ {name} failed with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("=" * 60)
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    
    if failed == 0:
        print("✅ All systems functional! Organon is ready to launch.")
        print()
        print("To run Organon:")
        print("  python src/gui_clean/main_application.py")
    else:
        print(f"❌ {failed} test(s) failed")
        return 1
    
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
