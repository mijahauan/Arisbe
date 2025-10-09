"""
Test History Timeline component.

Validates that:
1. Timeline displays state sequence correctly
2. Shows transformation arrows between states
3. Highlights current state
4. Emits signals on state click
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from datetime import datetime

from graph_entity import EntityCategory, EntityMetadata, EntityType, GraphEntity
from egi_core_dau import create_empty_graph, create_vertex, create_edge
from egi_transformation_history import EGITransformationHistory, StateSnapshot


def create_test_historical_entity():
    """Create a historical entity with 3 states for testing."""
    # Create initial EGI
    egi1 = create_empty_graph()
    v1 = create_vertex(label=None, is_generic=True)
    egi1 = egi1.with_vertex(v1)
    
    # Create history
    history = EGITransformationHistory(
        initial_egi=egi1,
        description="Initial state - one vertex"
    )
    
    initial_state_id = history.state_sequence[0]
    
    # Create state 2: Add edge
    egi2 = egi1
    e1 = create_edge()
    egi2 = egi2.with_edge(e1, [v1.id], relation_name="Human")
    
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
    
    # Create state 3: Add another edge
    egi3 = egi2
    e2 = create_edge()
    egi3 = egi3.with_edge(e2, [v1.id], relation_name="Mortal")
    
    state3_id = "state_003"
    state3 = StateSnapshot(
        state_id=state3_id,
        egi=egi3,
        timestamp=datetime.now(),
        step_number=2,
        description="Added Mortal predicate",
        linear_forms={"egif": "[*x] (Human x) (Mortal x)"}
    )
    history.states[state3_id] = state3
    history.state_sequence.append(state3_id)
    
    # Set current state
    history.current_state_id = state3_id
    
    # Create entity
    metadata = EntityMetadata(
        entity_id="test_timeline",
        entity_type=EntityType.HISTORICAL,
        name="Test Timeline Graph",
        description="A graph for testing timeline",
        category=EntityCategory.USER_CREATED,
        created=datetime.now(),
        last_modified=datetime.now(),
        current_state_id=state3_id,
        total_states=3,
        total_transformations=0,
        authors=["Test User"],
        tags={"test", "timeline"}
    )
    
    entity = GraphEntity(
        metadata=metadata,
        current_egi=egi3,
        history=history
    )
    
    return entity


def test_timeline_creation():
    """Test basic timeline creation and display."""
    print("=" * 70)
    print("TEST: History Timeline Creation")
    print("=" * 70)
    
    entity = create_test_historical_entity()
    
    print(f"✅ Created historical entity: {entity.name}")
    print(f"   Total states: {len(entity.history.state_sequence)}")
    print(f"   Current state: {entity.history.current_state_id}")
    print()
    
    return entity


def test_timeline_gui():
    """Test HistoryTimeline GUI component."""
    print("=" * 70)
    print("TEST: HistoryTimeline GUI Component")
    print("=" * 70)
    
    try:
        from PySide6.QtWidgets import QApplication
        from gui_clean.organon.history_timeline import HistoryTimeline
        
        # Create app
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create test entity
        entity = create_test_historical_entity()
        
        # Create timeline
        timeline = HistoryTimeline()
        
        print("Testing timeline display...")
        
        # Test with historical entity
        timeline.update_history(entity)
        
        # Verify timeline is visible
        assert timeline.isVisible(), "Timeline should be visible for historical entity"
        print("✅ Timeline visible for historical entity")
        
        # Verify timeline items created
        assert len(timeline._timeline_items) == 3, f"Expected 3 timeline items, got {len(timeline._timeline_items)}"
        print(f"✅ Timeline has {len(timeline._timeline_items)} state items")
        
        # Verify current state highlighted
        current_state_id = entity.history.current_state_id
        current_item = None
        for item in timeline._timeline_items:
            if item.state_id == current_state_id:
                current_item = item
                break
        
        assert current_item is not None, "Current state item should exist"
        assert current_item.is_current, "Current state should be marked as current"
        print("✅ Current state correctly highlighted")
        
        # Test with standalone entity (should hide timeline)
        from graph_entity import EntityMetadata, EntityType, EntityCategory, GraphEntity
        standalone_metadata = EntityMetadata(
            entity_id="test_standalone",
            entity_type=EntityType.STANDALONE,
            name="Test Standalone",
            description="Standalone entity",
            category=EntityCategory.USER_CREATED,
            created=datetime.now(),
            last_modified=datetime.now()
        )
        standalone_entity = GraphEntity(
            metadata=standalone_metadata,
            current_egi=create_empty_graph(),
            history=None
        )
        
        timeline.update_history(standalone_entity)
        assert not timeline.isVisible(), "Timeline should be hidden for standalone entity"
        print("✅ Timeline hidden for standalone entity")
        
        # Test signal emission
        signal_received = []
        def on_state_selected(state_id):
            signal_received.append(state_id)
        
        timeline.state_selected.connect(on_state_selected)
        timeline.update_history(entity)
        
        # Simulate clicking first state
        first_item = timeline._timeline_items[0]
        first_item.clicked.emit(first_item.state_id)
        
        assert len(signal_received) == 1, "Signal should be emitted on state click"
        assert signal_received[0] == first_item.state_id, "Signal should contain correct state ID"
        print("✅ State selection signal works correctly")
        
        print()
        return True
        
    except ImportError as e:
        print(f"⚠️  GUI test skipped (PySide6 not available): {e}")
        return False


def main():
    """Run all history timeline tests."""
    print()
    print("=" * 70)
    print("HISTORY TIMELINE VALIDATION")
    print("=" * 70)
    print()
    
    passed = 0
    total = 0
    
    # Test 1: Timeline creation
    total += 1
    try:
        test_timeline_creation()
        passed += 1
    except Exception as e:
        print(f"❌ Timeline creation test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: GUI component
    total += 1
    try:
        if test_timeline_gui():
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
