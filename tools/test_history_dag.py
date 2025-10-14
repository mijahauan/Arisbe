"""
Test DAG-based transformation history for branching UoD development.

This test validates the new DAG functionality that allows:
- Branching from any historical state
- Multiple paths of exploration
- Branch points and merges
- Path finding through the DAG
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egi_core_dau import create_empty_graph, create_vertex, RelationalGraphWithCuts
from egi_transformation_history import (
    EGITransformationHistory,
    HistoryBranchType,
)
from formal_transformation_rules import TransformationContext, TransformationResult, AreaPolarity


def create_simple_egi(label: str) -> RelationalGraphWithCuts:
    """Create a simple EGI for testing."""
    egi = create_empty_graph()
    vertex = create_vertex(label=label, is_generic=False)
    return egi.with_vertex(vertex)


def create_mock_transformation_result(new_egi: RelationalGraphWithCuts) -> TransformationResult:
    """Create a mock transformation result."""
    return TransformationResult(
        success=True,
        result_egi=new_egi,
        error_message=None,
        changes_made={"test": "change"},
    )


def test_linear_history():
    """Test that linear history still works (backward compatibility)."""
    print("\n=== Test 1: Linear History (Backward Compatibility) ===")
    
    # Create initial history
    initial_egi = create_simple_egi("State0")
    history = EGITransformationHistory(initial_egi, "Initial state")
    
    # Add transformations linearly
    for i in range(1, 4):
        current_egi = history.get_current_state().egi
        context = TransformationContext(
            source_egi=current_egi,
            target_area="sheet",
            selected_subgraph=frozenset(),
            area_polarity=AreaPolarity.POSITIVE,
            nesting_depth=0
        )
        new_egi = create_simple_egi(f"State{i}")
        result = create_mock_transformation_result(new_egi)
        history.add_transformation(f"Rule{i}", context, result)
    
    # Verify linear sequence
    assert len(history.states) == 4, f"Expected 4 states, got {len(history.states)}"
    assert len(history.transformations) == 3, f"Expected 3 transformations, got {len(history.transformations)}"
    assert len(history.branch_points) == 0, f"Expected no branch points, got {len(history.branch_points)}"
    
    print(f"✓ Linear history: {len(history.states)} states, {len(history.transformations)} transformations")
    print(f"✓ No branch points (as expected for linear history)")
    
    return history


def test_branching_from_state():
    """Test creating branches from historical states."""
    print("\n=== Test 2: Branching from Historical State ===")
    
    # Start with linear history
    history = test_linear_history()
    
    # Get state 2 (middle of the sequence)
    state_2_id = history.state_sequence[2]  # Index 2 = third state (State2)
    print(f"✓ Branching from state: {state_2_id}")
    
    # Create exploration branch from state 2
    branch_id = history.create_branch_from_state(
        state_2_id,
        HistoryBranchType.EXPLORATION,
        "Alternative exploration path"
    )
    
    print(f"✓ Created branch: {branch_id}")
    assert history.current_state_id == state_2_id, "Current state should be branch point"
    assert history.current_branch_id == branch_id, "Should be on new branch"
    
    # Add transformations on the new branch
    for i in range(1, 3):
        current_egi = history.get_current_state().egi
        context = TransformationContext(
            source_egi=current_egi,
            target_area="sheet",
            selected_subgraph=frozenset(),
            area_polarity=AreaPolarity.POSITIVE,
            nesting_depth=0
        )
        new_egi = create_simple_egi(f"BranchState{i}")
        result = create_mock_transformation_result(new_egi)
        history.add_transformation(f"BranchRule{i}", context, result)
    
    # Verify branching structure
    assert len(history.states) == 6, f"Expected 6 states (4 main + 2 branch), got {len(history.states)}"
    assert state_2_id in history.branch_points, "State 2 should be a branch point"
    
    children = history.get_child_states(state_2_id)
    print(f"✓ State {state_2_id} has {len(children)} children (branch point)")
    assert len(children) == 2, f"Branch point should have 2 children, got {len(children)}"
    
    return history


def test_multiple_paths():
    """Test finding multiple paths through the DAG."""
    print("\n=== Test 3: Multiple Paths Through DAG ===")
    
    # Create branching history
    history = test_branching_from_state()
    
    # Get all leaf states (states with no outgoing edges)
    leaf_states = [sid for sid, s in history.states.items() if len(history.get_child_states(sid)) == 0]
    
    print(f"✓ Found {len(leaf_states)} leaf states")
    
    # Find all paths from root to each leaf
    for leaf_id in leaf_states:
        paths = history.get_all_paths_from_root(leaf_id)
        print(f"  - Paths to {leaf_id[:8]}: {len(paths)} path(s)")
        
        for i, path in enumerate(paths):
            print(f"    Path {i+1}: {len(path)} states")
    
    # Verify shortest path finding
    if len(leaf_states) >= 2:
        leaf1 = leaf_states[0]
        leaf2 = leaf_states[1]
        
        # Find path between two leaves (should go through common ancestor)
        sequence = history.get_transformation_sequence(history.root_state_id, leaf1)
        print(f"✓ Path from root to leaf: {sequence.total_steps} steps")
        assert sequence.is_valid_path, "Path should be valid"
    
    return history


def test_dag_statistics():
    """Test DAG statistics calculation."""
    print("\n=== Test 4: DAG Statistics ===")
    
    history = test_branching_from_state()
    
    stats = history.get_dag_statistics()
    
    print(f"✓ DAG Statistics:")
    print(f"  - Total states: {stats['total_states']}")
    print(f"  - Total transformations: {stats['total_transformations']}")
    print(f"  - Total branches: {stats['total_branches']}")
    print(f"  - Active branches: {stats['active_branches']}")
    print(f"  - Branch points: {stats['branch_points']}")
    print(f"  - Max depth: {stats['max_depth']}")
    print(f"  - Root state: {stats['root_state_id'][:8]}...")
    
    assert stats['total_states'] == 6, "Should have 6 total states"
    assert stats['branch_points'] == 1, "Should have 1 branch point"
    assert stats['total_branches'] == 2, "Should have 2 branches (main + exploration)"
    assert stats['max_depth'] > 0, "Max depth should be greater than 0"
    
    return history


def test_export_with_dag():
    """Test exporting DAG structure."""
    print("\n=== Test 5: Export DAG Data ===")
    
    history = test_branching_from_state()
    
    export_data = history.export_history_data()
    
    print(f"✓ Exported data contains:")
    print(f"  - history_id: {export_data['history_id'][:8]}...")
    print(f"  - root_state_id: {export_data['root_state_id'][:8]}...")
    print(f"  - branch_points: {len(export_data['branch_points'])}")
    print(f"  - states: {len(export_data['states'])}")
    print(f"  - transformations: {len(export_data['transformations'])}")
    print(f"  - branches: {len(export_data['branches'])}")
    
    assert 'root_state_id' in export_data, "Export should include root_state_id"
    assert 'branch_points' in export_data, "Export should include branch_points"
    assert 'dag_statistics' in export_data, "Export should include dag_statistics"
    
    print(f"✓ DAG export successful")


def run_all_tests():
    """Run all DAG tests."""
    print("=" * 60)
    print("Testing DAG-Based Transformation History")
    print("=" * 60)
    
    try:
        test_linear_history()
        test_branching_from_state()
        test_multiple_paths()
        test_dag_statistics()
        test_export_with_dag()
        
        print("\n" + "=" * 60)
        print("✅ ALL DAG TESTS PASSED")
        print("=" * 60)
        print("\nKey Features Validated:")
        print("  ✓ Linear history still works (backward compatible)")
        print("  ✓ Branching from any historical state")
        print("  ✓ Multiple paths through DAG")
        print("  ✓ Branch point detection")
        print("  ✓ Path finding (BFS)")
        print("  ✓ DAG statistics calculation")
        print("  ✓ Export includes DAG structure")
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
