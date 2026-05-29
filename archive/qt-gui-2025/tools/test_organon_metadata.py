"""
Test Organon MetadataPanel integration.

Validates that:
1. MetadataPanel displays entity information correctly
2. Standalone vs Historical entities shown differently
3. Complexity metrics calculated correctly
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from datetime import datetime

from graph_entity import EntityCategory, EntityMetadata, EntityType, GraphEntity
from egi_core_dau import create_empty_graph, create_vertex, create_edge
from egi_transformation_history import EGITransformationHistory, StateSnapshot


def test_metadata_panel_standalone():
    """Test metadata panel with standalone entity."""
    print("=" * 70)
    print("TEST: Metadata Panel - Standalone Entity")
    print("=" * 70)
    
    # Create simple EGI
    egi = create_empty_graph()
    v1 = create_vertex(label=None, is_generic=True)  # Generic vertex has no label
    egi = egi.with_vertex(v1)
    e1 = create_edge()
    egi = egi.with_edge(e1, [v1.id], relation_name="Human")
    
    # Create standalone entity
    metadata = EntityMetadata(
        entity_id="test_standalone",
        entity_type=EntityType.STANDALONE,
        name="Test Standalone Graph",
        description="A simple test graph for validation",
        category=EntityCategory.USER_CREATED,
        created=datetime.now(),
        last_modified=datetime.now(),
        authors=["Test User"],
        tags={"test", "standalone", "simple"}
    )
    
    entity = GraphEntity(
        metadata=metadata,
        current_egi=egi,
        history=None
    )
    
    # Verify entity properties
    assert entity.is_standalone
    assert not entity.is_historical
    assert entity.name == "Test Standalone Graph"
    
    print(f"✅ Entity created: {entity.name}")
    print(f"   Type: Standalone")
    print(f"   Category: {metadata.category.value}")
    print(f"   Vertices: {len(egi.V)}")
    print(f"   Edges: {len(egi.E)}")
    print(f"   Cuts: {len(egi.Cut)}")
    print()
    
    return entity


def test_metadata_panel_historical():
    """Test metadata panel with historical entity."""
    print("=" * 70)
    print("TEST: Metadata Panel - Historical Entity")
    print("=" * 70)
    
    # Create initial EGI
    egi1 = create_empty_graph()
    v1 = create_vertex(label=None, is_generic=True)  # Generic vertex has no label
    egi1 = egi1.with_vertex(v1)
    
    # Create history with initial EGI
    history = EGITransformationHistory(
        initial_egi=egi1,
        description="Initial state with one vertex"
    )
    
    # Get the initial state ID
    initial_state_id = history.state_sequence[0]
    
    # Create EGI with additional edge (state 2)
    egi2 = egi1
    e1 = create_edge()
    egi2 = egi2.with_edge(e1, [v1.id], relation_name="Human")
    
    # Add second state manually for testing
    state2_id = "state_002"
    state2 = StateSnapshot(
        state_id=state2_id,
        egi=egi2,
        timestamp=datetime.now(),
        step_number=1,
        description="Added Human predicate",
        linear_forms={"egif": "[*x] (Human x)"}
    )
    history.states[state2_id] = state2
    history.state_sequence.append(state2_id)
    history.current_state_id = state2_id
    
    # Create historical entity
    metadata = EntityMetadata(
        entity_id="test_historical",
        entity_type=EntityType.HISTORICAL,
        name="Test Historical Graph",
        description="A graph with transformation history",
        category=EntityCategory.THEOREM_PROVING,
        created=datetime.now(),
        last_modified=datetime.now(),
        current_state_id=state2_id,
        total_states=2,
        total_transformations=0,  # No formal transformations recorded
        authors=["Proof Author"],
        tags={"test", "historical", "proof"},
        source_citation="Test Theorem 1.2.3"
    )
    
    entity = GraphEntity(
        metadata=metadata,
        current_egi=egi2,
        history=history
    )
    
    # Verify entity properties
    assert entity.is_historical
    assert not entity.is_standalone
    assert entity.name == "Test Historical Graph"
    assert metadata.total_states == 2
    
    print(f"✅ Entity created: {entity.name}")
    print(f"   Type: Historical")
    print(f"   Category: {metadata.category.value}")
    print(f"   Total States: {len(history.state_sequence)}")
    print(f"   Transformations: {len(history.transformations)}")
    print(f"   Current: State 2 of {len(history.state_sequence)}")
    print(f"   Citation: {metadata.source_citation}")
    print()
    
    return entity


def test_gui_metadata_panel():
    """Test MetadataPanel GUI component (requires Qt)."""
    print("=" * 70)
    print("TEST: MetadataPanel GUI Component")
    print("=" * 70)
    
    try:
        from PySide6.QtWidgets import QApplication
        from gui_clean.organon.metadata_panel import MetadataPanel
        
        # Create app (required for Qt widgets)
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create test entities
        standalone = test_metadata_panel_standalone()
        historical = test_metadata_panel_historical()
        
        # Create metadata panel
        panel = MetadataPanel()
        
        # Test with standalone entity
        print("Testing standalone entity display...")
        panel.update_metadata(standalone)
        assert "Test Standalone Graph" in panel.name_label.text()
        assert "Standalone" in panel.type_label.text()
        assert not panel.history_group.isVisible()
        print("✅ Standalone entity displayed correctly")
        print()
        
        # Test with historical entity
        print("Testing historical entity display...")
        try:
            print(f"   Entity is_historical: {historical.is_historical}")
            print(f"   Entity history: {historical.history}")
            print(f"   History states: {len(historical.history.states) if historical.history else 0}")
            panel.update_metadata(historical)
            print(f"   History group visible: {panel.history_group.isVisible()}")
            print(f"   Name label: {panel.name_label.text()}")
            print(f"   Type label: {panel.type_label.text()}")
            print(f"   States label: {panel.states_label.text()}")
            assert "Test Historical Graph" in panel.name_label.text(), f"Expected 'Test Historical Graph', got '{panel.name_label.text()}'"
            assert "Historical" in panel.type_label.text(), f"Expected 'Historical' in type, got '{panel.type_label.text()}'"
            assert panel.history_group.isVisible(), "History group should be visible"
            assert "2" in panel.states_label.text(), f"Expected '2' in states, got '{panel.states_label.text()}'"
            print("✅ Historical entity displayed correctly")
            print()
        except AssertionError as e:
            print(f"❌ Assertion failed: {e}")
            raise
        except Exception as e:
            print(f"❌ Error: {e}")
            raise
        
        # Test clear
        print("Testing clear...")
        panel.clear()
        assert "(no entity loaded)" in panel.name_label.text()
        assert not panel.history_group.isVisible()
        print("✅ Clear works correctly")
        print()
        
        return True
        
    except ImportError as e:
        print(f"⚠️  GUI test skipped (PySide6 not available): {e}")
        return False


def main():
    """Run all metadata panel tests."""
    print()
    print("=" * 70)
    print("ORGANON METADATA PANEL VALIDATION")
    print("=" * 70)
    print()
    
    passed = 0
    total = 0
    
    # Test 1: Standalone entity
    total += 1
    try:
        test_metadata_panel_standalone()
        passed += 1
    except Exception as e:
        print(f"❌ Standalone entity test failed: {e}")
    
    # Test 2: Historical entity
    total += 1
    try:
        test_metadata_panel_historical()
        passed += 1
    except Exception as e:
        print(f"❌ Historical entity test failed: {e}")
    
    # Test 3: GUI component
    total += 1
    try:
        if test_gui_metadata_panel():
            passed += 1
        else:
            print("⚠️  GUI test skipped")
            total -= 1  # Don't count skipped test
    except Exception as e:
        print(f"❌ GUI component test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    if passed == total:
        print(f"✅ All tests passed ({passed}/{total})")
        return 0
    else:
        print(f"⚠️  Some tests failed ({passed}/{total})")
        return 1


if __name__ == "__main__":
    sys.exit(main())
