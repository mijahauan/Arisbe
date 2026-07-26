"""
Comprehensive tests for AlternativeSet integration into UniverseOfDiscourse.

Tests cover:
- Recording alternatives at states
- Selecting alternatives with answers
- Narrowing alternatives to subsets
- Querying alternatives at specific states
- Tracing alternative lifecycles through the DAG
- Edge cases and error handling
- Backward compatibility
"""

import pytest
from datetime import datetime

from egi_core_dau import RelationalGraphWithCuts, create_empty_graph
from egi_transformation_history import EGITransformationHistory
from alternative_set import AlternativeSet
from universe_of_discourse import UniverseOfDiscourse, UoDMetadata, UoDType, UoDCategory


# ===== Fixtures =====


@pytest.fixture
def simple_egi() -> RelationalGraphWithCuts:
    """Create a simple EGI (empty sheet)."""
    return create_empty_graph()


@pytest.fixture
def uod_metadata() -> UoDMetadata:
    """Create standard UoD metadata."""
    now = datetime.now()
    return UoDMetadata(
        uod_id="test-uod-001",
        uod_type=UoDType.HISTORICAL,
        name="Test UoD with Alternatives",
        description="Test Universe of Discourse for alternative-set tracking",
        category=UoDCategory.ACTIVE_INQUIRY,
        created=now,
        last_modified=now,
    )


@pytest.fixture
def simple_uod(simple_egi, uod_metadata) -> UniverseOfDiscourse:
    """Create a simple UoD with history."""
    uod = UniverseOfDiscourse(
        metadata=uod_metadata,
        current_egi=simple_egi,
        history=EGITransformationHistory(
            initial_egi=simple_egi,
            description="Initial state",
        ),
    )
    return uod


@pytest.fixture
def sample_alt_set(simple_egi) -> AlternativeSet:
    """Create a sample alternative-set for testing."""
    return AlternativeSet(
        id="a0",
        context=simple_egi,
        alternatives=frozenset({"answer_a_hash", "answer_b_hash", "answer_c_hash"}),
        current_selection=frozenset(),
        kind="interrogative",
        emerged_at_state="s0",
        warrant=0.8,
        source="test_fixture",
    )


@pytest.fixture
def multi_choice_alt_set(simple_egi) -> AlternativeSet:
    """Create an alternative-set with multiple possible choices."""
    return AlternativeSet(
        id="a1",
        context=simple_egi,
        alternatives=frozenset({
            "answer_x_hash",
            "answer_y_hash",
            "answer_z_hash",
            "answer_w_hash",
        }),
        current_selection=frozenset(),
        kind="hypothetical",
        emerged_at_state="s1",
        warrant=0.9,
        source="test_fixture",
    )


# ===== Tests: Recording Alternatives =====


class TestRecordAlternativeAtState:
    """Test recording alternatives at specific states."""

    def test_record_single_alternative(self, simple_uod, sample_alt_set):
        """Test recording a single alternative-set at a state."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_alternative_at_state(state_id, sample_alt_set)

        # Alternative-set should be in both registries
        assert sample_alt_set.id in simple_uod.all_alternatives
        assert state_id in simple_uod.alternatives_by_state
        assert sample_alt_set in simple_uod.alternatives_by_state[state_id]

    def test_record_multiple_alternatives_same_state(self, simple_uod, sample_alt_set, multi_choice_alt_set):
        """Test recording multiple alternatives at the same state."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_alternative_at_state(state_id, sample_alt_set)
        simple_uod.record_alternative_at_state(state_id, multi_choice_alt_set)

        # Both should be recorded
        assert len(simple_uod.alternatives_by_state[state_id]) == 2
        assert sample_alt_set.id in simple_uod.all_alternatives
        assert multi_choice_alt_set.id in simple_uod.all_alternatives

    def test_record_updates_metadata(self, simple_uod, sample_alt_set):
        """Test that recording an alternative-set updates last_modified."""
        original_time = simple_uod.metadata.last_modified
        state_id = simple_uod.history.current_state_id

        # Small delay to ensure time difference
        import time
        time.sleep(0.01)

        simple_uod.record_alternative_at_state(state_id, sample_alt_set)
        assert simple_uod.metadata.last_modified > original_time

    def test_record_empty_state_list_creation(self, simple_uod, sample_alt_set):
        """Test that recording creates state entry if it doesn't exist."""
        state_id = simple_uod.history.current_state_id
        assert state_id not in simple_uod.alternatives_by_state

        simple_uod.record_alternative_at_state(state_id, sample_alt_set)

        assert state_id in simple_uod.alternatives_by_state
        assert len(simple_uod.alternatives_by_state[state_id]) == 1


# ===== Tests: Selecting Alternatives =====


class TestSelectAlternativeAtState:
    """Test selecting alternatives at specific states."""

    def test_select_alternative_basic(self, simple_uod, sample_alt_set):
        """Test selecting an alternative-set to a single choice."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_alternative_at_state(state_id, sample_alt_set)

        # Select the alternative-set
        choice = "answer_a_hash"
        selected = simple_uod.select_alternative_at_state(sample_alt_set.id, state_id, choice)

        # Check selected state
        assert selected.status == "resolved"
        assert selected.current_selection == frozenset({choice})
        assert selected.resolved_at_state == state_id
        assert simple_uod.all_alternatives[sample_alt_set.id].status == "resolved"

    def test_select_nonexistent_alternative_raises(self, simple_uod):
        """Test that selecting a nonexistent alternative raises ValueError."""
        state_id = simple_uod.history.current_state_id
        with pytest.raises(ValueError, match="not found in registry"):
            simple_uod.select_alternative_at_state("nonexistent", state_id, "answer_hash")

    def test_select_with_invalid_choice_raises(self, simple_uod, sample_alt_set):
        """Test that selecting with an invalid choice raises ValueError."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_alternative_at_state(state_id, sample_alt_set)

        # Try to select with choice not in alternatives
        with pytest.raises(ValueError, match="not in alternatives"):
            simple_uod.select_alternative_at_state(sample_alt_set.id, state_id, "invalid_answer_hash")

    def test_select_records_at_state(self, simple_uod, sample_alt_set):
        """Test that selecting records the alternative-set at the selection state."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_alternative_at_state(state_id, sample_alt_set)

        # Select at same state
        selected = simple_uod.select_alternative_at_state(
            sample_alt_set.id, state_id, "answer_a_hash"
        )

        # Should be recorded at state
        assert state_id in simple_uod.alternatives_by_state
        # Will have 2 entries: initial and selected
        alts_at_state = simple_uod.alternatives_at_state(state_id)
        assert len(alts_at_state) >= 1
        # Last entry should be the selected version
        assert alts_at_state[-1].status == "resolved"


# ===== Tests: Narrowing Alternatives =====


class TestNarrowAlternativeAtState:
    """Test narrowing alternatives to subsets of choices."""

    def test_narrow_alternative_basic(self, simple_uod, multi_choice_alt_set):
        """Test narrowing an alternative-set to a subset of choices."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_alternative_at_state(state_id, multi_choice_alt_set)

        # Narrow to two choices
        narrowed_choices = {"answer_x_hash", "answer_y_hash"}
        narrowed = simple_uod.narrow_alternative_at_state(multi_choice_alt_set.id, state_id, narrowed_choices)

        # Check narrowed state
        assert narrowed.alternatives == frozenset(narrowed_choices)
        assert narrowed.status == "partial"
        assert state_id in narrowed.selection_path

    def test_narrow_nonexistent_alternative_raises(self, simple_uod):
        """Test that narrowing a nonexistent alternative raises ValueError."""
        state_id = simple_uod.history.current_state_id
        with pytest.raises(ValueError, match="not found in registry"):
            simple_uod.narrow_alternative_at_state("nonexistent", state_id, {"answer_hash"})

    def test_narrow_with_no_overlap_raises(self, simple_uod, multi_choice_alt_set):
        """Test that narrowing with no overlap raises ValueError."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_alternative_at_state(state_id, multi_choice_alt_set)

        # Try to narrow to choices outside alternatives
        with pytest.raises(ValueError, match="No overlap"):
            simple_uod.narrow_alternative_at_state(
                multi_choice_alt_set.id, state_id, {"invalid_answer_1", "invalid_answer_2"}
            )

    def test_narrow_partial_overlap(self, simple_uod, multi_choice_alt_set):
        """Test narrowing with partial overlap (valid)."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_alternative_at_state(state_id, multi_choice_alt_set)

        # Narrow with partial overlap (2 valid, 1 invalid)
        narrowed_choices = {"answer_x_hash", "answer_y_hash", "invalid_answer"}
        narrowed = simple_uod.narrow_alternative_at_state(
            multi_choice_alt_set.id, state_id, narrowed_choices
        )

        # Should only keep valid choices
        assert frozenset({"answer_x_hash", "answer_y_hash"}) == narrowed.alternatives

    def test_narrow_records_at_state(self, simple_uod, multi_choice_alt_set):
        """Test that narrowing records the alternative-set at the narrowing state."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_alternative_at_state(state_id, multi_choice_alt_set)

        narrowed = simple_uod.narrow_alternative_at_state(
            multi_choice_alt_set.id, state_id, {"answer_x_hash", "answer_y_hash"}
        )

        # Should be recorded at state
        assert state_id in simple_uod.alternatives_by_state
        # Will have 2 entries: initial and narrowed
        alts_at_state = simple_uod.alternatives_at_state(state_id)
        assert len(alts_at_state) >= 2
        # Last one should be the narrowed version
        assert alts_at_state[-1].status == "partial"


# ===== Tests: Querying Alternatives =====


class TestAlternativesAtState:
    """Test querying alternatives at specific states."""

    def test_alternatives_at_state_empty(self, simple_uod):
        """Test that querying a state with no alternatives returns empty list."""
        state_id = simple_uod.history.current_state_id
        alts = simple_uod.alternatives_at_state(state_id)
        assert alts == []

    def test_alternatives_at_state_single(self, simple_uod, sample_alt_set):
        """Test querying a state with one alternative-set."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_alternative_at_state(state_id, sample_alt_set)

        alts = simple_uod.alternatives_at_state(state_id)
        assert len(alts) == 1
        assert alts[0] == sample_alt_set

    def test_alternatives_at_state_multiple(self, simple_uod, sample_alt_set, multi_choice_alt_set):
        """Test querying a state with multiple alternatives."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_alternative_at_state(state_id, sample_alt_set)
        simple_uod.record_alternative_at_state(state_id, multi_choice_alt_set)

        alts = simple_uod.alternatives_at_state(state_id)
        assert len(alts) == 2
        assert sample_alt_set in alts
        assert multi_choice_alt_set in alts

    def test_alternatives_at_state_nonexistent_state(self, simple_uod):
        """Test querying a nonexistent state returns empty list."""
        alts = simple_uod.alternatives_at_state("nonexistent_state")
        assert alts == []


# ===== Tests: Alternative Lifecycle =====


class TestAlternativeLifecycle:
    """Test tracing alternative lifecycles through the DAG."""

    def test_lifecycle_single_state(self, simple_uod, simple_egi):
        """Test lifecycle of an alternative-set that emerges and stays at one state."""
        state_id = simple_uod.history.current_state_id

        # Create an alternative-set with the correct emerged_at_state
        alt_set = AlternativeSet(
            id="lifecycle_test_a0",
            context=simple_egi,
            alternatives=frozenset({"answer_a", "answer_b"}),
            kind="interrogative",
            emerged_at_state=state_id,
        )

        simple_uod.record_alternative_at_state(state_id, alt_set)

        lifecycle = simple_uod.alternative_lifecycle(alt_set.id)
        # Should have at least one entry
        assert len(lifecycle) >= 1
        # First entry should be at the emerged state
        assert lifecycle[0][0] == state_id

    def test_lifecycle_multiple_operations(self, simple_uod, sample_alt_set):
        """Test lifecycle through multiple operations at same state."""
        state_id = simple_uod.history.current_state_id

        # Record the alternative-set initially
        simple_uod.record_alternative_at_state(state_id, sample_alt_set)

        # Narrow the alternative-set
        narrowed = simple_uod.narrow_alternative_at_state(
            sample_alt_set.id, state_id, {"answer_a_hash"}
        )

        # Select the alternative-set
        selected = simple_uod.select_alternative_at_state(
            sample_alt_set.id, state_id, "answer_a_hash"
        )

        lifecycle = simple_uod.alternative_lifecycle(sample_alt_set.id)

        # Should have entries
        assert len(lifecycle) >= 1
        # Latest version in lifecycle should be selected
        assert lifecycle[-1][1].status == "resolved"

    def test_lifecycle_nonexistent_alternative_raises(self, simple_uod):
        """Test that querying lifecycle of nonexistent alternative raises ValueError."""
        with pytest.raises(ValueError, match="not found in registry"):
            simple_uod.alternative_lifecycle("nonexistent")

    def test_lifecycle_returns_tuples(self, simple_uod, sample_alt_set):
        """Test that lifecycle returns (state_id, AlternativeSet) tuples."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_alternative_at_state(state_id, sample_alt_set)

        lifecycle = simple_uod.alternative_lifecycle(sample_alt_set.id)

        for entry in lifecycle:
            assert isinstance(entry, tuple)
            assert len(entry) == 2
            state_id_entry, alt_entry = entry
            assert isinstance(state_id_entry, str)
            assert isinstance(alt_entry, AlternativeSet)

    def test_lifecycle_ordered(self, simple_uod, sample_alt_set):
        """Test that lifecycle maintains order through selection_path."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_alternative_at_state(state_id, sample_alt_set)

        # Narrow the alternative-set to add it to selection path
        simple_uod.narrow_alternative_at_state(sample_alt_set.id, state_id, {"answer_a_hash"})

        lifecycle = simple_uod.alternative_lifecycle(sample_alt_set.id)

        # Should include emerged state
        state_ids = [state_id_in_lifecycle for state_id_in_lifecycle, _ in lifecycle]
        assert state_id in state_ids


# ===== Tests: Backward Compatibility =====


class TestBackwardCompatibility:
    """Test that existing code using Doubt names still works."""

    def test_uod_without_alternatives_default_empty(self, simple_uod):
        """Test that UoD fields default to empty."""
        assert simple_uod.alternatives_by_state == {}
        assert simple_uod.all_alternatives == {}

    def test_uod_without_alternatives_query_returns_empty(self, simple_uod):
        """Test that querying alternatives on UoD without alternatives returns empty."""
        state_id = simple_uod.history.current_state_id
        assert simple_uod.alternatives_at_state(state_id) == []

    def test_existing_uod_can_add_alternatives_later(self, simple_uod, sample_alt_set):
        """Test that an existing UoD can add alternatives later."""
        # Initially no alternatives
        assert len(simple_uod.all_alternatives) == 0

        # Add alternative
        state_id = simple_uod.history.current_state_id
        simple_uod.record_alternative_at_state(state_id, sample_alt_set)

        # Now has alternatives
        assert len(simple_uod.all_alternatives) == 1
        assert sample_alt_set.id in simple_uod.all_alternatives

    def test_uod_properties_unchanged_by_alternatives(self, simple_uod, sample_alt_set):
        """Test that adding alternatives doesn't change other UoD properties."""
        state_id = simple_uod.history.current_state_id
        egi_before = simple_uod.current_egi

        simple_uod.record_alternative_at_state(state_id, sample_alt_set)

        # UoD properties should be unchanged
        assert simple_uod.current_egi == egi_before
        assert simple_uod.uod_id == "test-uod-001"
        assert simple_uod.name == "Test UoD with Alternatives"

    def test_doubt_backward_compat_alias_works(self, simple_uod, sample_alt_set):
        """Test that old Doubt name still works via backward-compatibility methods."""
        state_id = simple_uod.history.current_state_id

        # Record using old method name (should forward to new name)
        simple_uod.record_doubt_at_state(state_id, sample_alt_set)

        # Should be in new registry
        assert sample_alt_set.id in simple_uod.all_alternatives

        # Query using old method name (should forward to new name)
        doubts = simple_uod.doubts_at_state(state_id)
        assert len(doubts) == 1
        assert doubts[0] == sample_alt_set

    def test_old_doubt_methods_forward_to_new_names(self, simple_uod, sample_alt_set, multi_choice_alt_set):
        """Test that old method names forward to new implementations."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_doubt_at_state(state_id, multi_choice_alt_set)

        # Old method name should work
        narrowed = simple_uod.narrow_doubt_at_state(
            multi_choice_alt_set.id, state_id, {"answer_x_hash", "answer_y_hash"}
        )
        assert narrowed.status == "partial"

        # Old query method should work
        lifecycle = simple_uod.doubt_lifecycle(multi_choice_alt_set.id)
        assert len(lifecycle) >= 1


# ===== Tests: Edge Cases and Integration =====


class TestEdgeCases:
    """Test edge cases and integration scenarios."""

    def test_record_same_alternative_twice_same_state(self, simple_uod, sample_alt_set):
        """Test recording the same alternative-set twice at the same state."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_alternative_at_state(state_id, sample_alt_set)
        simple_uod.record_alternative_at_state(state_id, sample_alt_set)

        # Should have two entries at state (same alternative-set recorded twice)
        alts = simple_uod.alternatives_at_state(state_id)
        assert len(alts) == 2

    def test_select_then_query_state(self, simple_uod, sample_alt_set):
        """Test that selected alternatives appear at selection state."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_alternative_at_state(state_id, sample_alt_set)

        simple_uod.select_alternative_at_state(sample_alt_set.id, state_id, "answer_a_hash")

        # Selected alternative should appear at state
        alts_at_state = simple_uod.alternatives_at_state(state_id)
        # Will have recorded once, then selected once
        assert len(alts_at_state) >= 1
        # Last entry should be selected
        assert alts_at_state[-1].status == "resolved"

    def test_narrow_then_select(self, simple_uod, multi_choice_alt_set):
        """Test narrowing followed by selection."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_alternative_at_state(state_id, multi_choice_alt_set)

        # Narrow
        narrowed = simple_uod.narrow_alternative_at_state(
            multi_choice_alt_set.id, state_id, {"answer_x_hash", "answer_y_hash"}
        )
        assert narrowed.status == "partial"

        # Select
        selected = simple_uod.select_alternative_at_state(
            multi_choice_alt_set.id, state_id, "answer_x_hash"
        )
        assert selected.status == "resolved"

        # Check registry has latest
        assert simple_uod.all_alternatives[multi_choice_alt_set.id].status == "resolved"

    def test_all_alternatives_immutable_copy(self, simple_uod, sample_alt_set):
        """Test that all_alternatives contains immutable AlternativeSet objects."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_alternative_at_state(state_id, sample_alt_set)

        # Try to modify (should fail for frozen dataclass)
        retrieved = simple_uod.all_alternatives[sample_alt_set.id]
        with pytest.raises(Exception):  # FrozenInstanceError
            retrieved.id = "modified"

    def test_state_list_fresh_instance(self, simple_uod, sample_alt_set):
        """Test that alternatives_at_state returns a fresh list."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_alternative_at_state(state_id, sample_alt_set)

        list1 = simple_uod.alternatives_at_state(state_id)
        list2 = simple_uod.alternatives_at_state(state_id)

        # Should be different list objects
        assert list1 is not list2
        # But same contents
        assert list1 == list2
