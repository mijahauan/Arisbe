"""
Comprehensive tests for Doubt integration into UniverseOfDiscourse.

Tests cover:
- Recording doubts at states
- Resolving doubts with answers
- Narrowing doubts to subsets
- Querying doubts at specific states
- Tracing doubt lifecycles through the DAG
- Edge cases and error handling
- Backward compatibility
"""

import pytest
from datetime import datetime

from egi_core_dau import RelationalGraphWithCuts, create_empty_graph
from egi_transformation_history import EGITransformationHistory
from alternative_set import Doubt  # Backward-compat alias; Doubt = AlternativeSet
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
        name="Test UoD with Doubts",
        description="Test Universe of Discourse for doubt tracking",
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
def sample_doubt(simple_egi) -> Doubt:
    """Create a sample doubt for testing (using new AlternativeSet field names)."""
    return Doubt(
        id="d0",
        context=simple_egi,
        alternatives=frozenset({"answer_a_hash", "answer_b_hash", "answer_c_hash"}),
        current_selection=frozenset(),
        kind="unknown_verdict",
        emerged_at_state="s0",
        resolved_at_state=None,
        selection_path=[],
        warrant=0.8,
        source="test_fixture",
    )


@pytest.fixture
def multi_answer_doubt(simple_egi) -> Doubt:
    """Create a doubt with multiple possible answers (using new AlternativeSet field names)."""
    return Doubt(
        id="d1",
        context=simple_egi,
        alternatives=frozenset({
            "answer_x_hash",
            "answer_y_hash",
            "answer_z_hash",
            "answer_w_hash",
        }),
        current_selection=frozenset(),
        kind="thin_spot",
        emerged_at_state="s1",
        resolved_at_state=None,
        selection_path=[],
        warrant=0.9,
        source="test_fixture",
    )


# ===== Tests: Recording Doubts =====


class TestRecordDoubtAtState:
    """Test recording doubts at specific states."""

    def test_record_single_doubt(self, simple_uod, sample_doubt):
        """Test recording a single doubt at a state."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_doubt_at_state(state_id, sample_doubt)

        # Doubt should be in both registries
        assert sample_doubt.id in simple_uod.all_doubts
        assert state_id in simple_uod.doubts_by_state
        assert sample_doubt in simple_uod.doubts_by_state[state_id]

    def test_record_multiple_doubts_same_state(self, simple_uod, sample_doubt, multi_answer_doubt):
        """Test recording multiple doubts at the same state."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_doubt_at_state(state_id, sample_doubt)
        simple_uod.record_doubt_at_state(state_id, multi_answer_doubt)

        # Both should be recorded
        assert len(simple_uod.doubts_by_state[state_id]) == 2
        assert sample_doubt.id in simple_uod.all_doubts
        assert multi_answer_doubt.id in simple_uod.all_doubts

    def test_record_same_doubt_multiple_states(self, simple_uod, sample_doubt, multi_answer_doubt):
        """Test recording doubts at the same state creates independent entries."""
        state_id = simple_uod.history.current_state_id

        # Record both doubts at same state
        simple_uod.record_doubt_at_state(state_id, sample_doubt)
        simple_uod.record_doubt_at_state(state_id, multi_answer_doubt)

        # Both should be in state list
        assert len(simple_uod.doubts_by_state[state_id]) == 2
        # And in global registry
        assert sample_doubt.id in simple_uod.all_doubts
        assert multi_answer_doubt.id in simple_uod.all_doubts

    def test_record_updates_metadata(self, simple_uod, sample_doubt):
        """Test that recording a doubt updates last_modified."""
        original_time = simple_uod.metadata.last_modified
        state_id = simple_uod.history.current_state_id

        # Small delay to ensure time difference
        import time
        time.sleep(0.01)

        simple_uod.record_doubt_at_state(state_id, sample_doubt)
        assert simple_uod.metadata.last_modified > original_time

    def test_record_doubt_empty_state_list_creation(self, simple_uod, sample_doubt):
        """Test that recording creates state entry if it doesn't exist."""
        state_id = simple_uod.history.current_state_id
        assert state_id not in simple_uod.doubts_by_state

        simple_uod.record_doubt_at_state(state_id, sample_doubt)

        assert state_id in simple_uod.doubts_by_state
        assert len(simple_uod.doubts_by_state[state_id]) == 1


# ===== Tests: Resolving Doubts =====


class TestResolveDoubtAtState:
    """Test resolving doubts at specific states."""

    def test_resolve_doubt_basic(self, simple_uod, sample_doubt):
        """Test resolving a doubt to a single answer."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_doubt_at_state(state_id, sample_doubt)

        # Resolve the doubt (same state for simplicity)
        answer = "answer_a_hash"
        resolved = simple_uod.resolve_doubt_at_state(sample_doubt.id, state_id, answer)

        # Check resolved state
        assert resolved.status == "resolved"
        assert resolved.current_selection == frozenset({answer})
        assert resolved.resolved_at_state == state_id
        assert simple_uod.all_doubts[sample_doubt.id].status == "resolved"

    def test_resolve_nonexistent_doubt_raises(self, simple_uod):
        """Test that resolving a nonexistent doubt raises ValueError."""
        state_id = simple_uod.history.current_state_id
        with pytest.raises(ValueError, match="not found in registry"):
            simple_uod.resolve_doubt_at_state("nonexistent", state_id, "answer_hash")

    def test_resolve_with_invalid_answer_raises(self, simple_uod, sample_doubt):
        """Test that resolving with an invalid answer raises ValueError."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_doubt_at_state(state_id, sample_doubt)

        # Try to resolve with answer not in alternatives
        with pytest.raises(ValueError, match="not in alternatives"):
            simple_uod.resolve_doubt_at_state(sample_doubt.id, state_id, "invalid_answer_hash")

    def test_resolve_records_at_state(self, simple_uod, sample_doubt):
        """Test that resolving a doubt records it at the resolution state."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_doubt_at_state(state_id, sample_doubt)

        # Resolve at same state
        resolved = simple_uod.resolve_doubt_at_state(
            sample_doubt.id, state_id, "answer_a_hash"
        )

        # Should be recorded at state (as a second entry in the list)
        assert state_id in simple_uod.doubts_by_state
        # Since we recorded once, then resolved at same state, we have 2 entries
        doubts_at_state = simple_uod.doubts_at_state(state_id)
        # Last entry should be the resolved version
        assert doubts_at_state[-1].status == "resolved"

    def test_resolve_multiple_times_latest_wins(self, simple_uod, sample_doubt):
        """Test that resolving multiple times keeps the latest resolution."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_doubt_at_state(state_id, sample_doubt)

        # First resolution
        resolved_1 = simple_uod.resolve_doubt_at_state(
            sample_doubt.id, state_id, "answer_a_hash"
        )
        assert resolved_1.current_selection == frozenset({"answer_a_hash"})

        # Reopen and resolve to different answer
        reopened = Doubt(
            id=sample_doubt.id,
            context=resolved_1.context,
            alternatives=resolved_1.alternatives,
            current_selection=frozenset(),
            emerged_at_state=resolved_1.emerged_at_state,
            resolved_at_state=None,
            selection_path=list(resolved_1.selection_path) + [state_id],
            kind=resolved_1.kind,
            warrant=resolved_1.warrant,
            source=resolved_1.source,
        )
        simple_uod.all_alternatives[sample_doubt.id] = reopened

        # Second resolution
        resolved_2 = simple_uod.resolve_doubt_at_state(
            sample_doubt.id, state_id, "answer_b_hash"
        )

        # Latest resolution should be in registry
        assert simple_uod.all_doubts[sample_doubt.id].current_selection == frozenset({"answer_b_hash"})
        assert simple_uod.all_doubts[sample_doubt.id].resolved_at_state == state_id


# ===== Tests: Narrowing Doubts =====


class TestNarrowDoubtAtState:
    """Test narrowing doubts to subsets of answers."""

    def test_narrow_doubt_basic(self, simple_uod, multi_answer_doubt):
        """Test narrowing a doubt to a subset of answers."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_doubt_at_state(state_id, multi_answer_doubt)

        # Narrow to two answers
        narrowed_answers = {"answer_x_hash", "answer_y_hash"}
        narrowed = simple_uod.narrow_doubt_at_state(multi_answer_doubt.id, state_id, narrowed_answers)

        # Check narrowed state
        assert narrowed.alternatives == frozenset(narrowed_answers)
        assert narrowed.status == "partial"
        assert state_id in narrowed.selection_path

    def test_narrow_nonexistent_doubt_raises(self, simple_uod):
        """Test that narrowing a nonexistent doubt raises ValueError."""
        state_id = simple_uod.history.current_state_id
        with pytest.raises(ValueError, match="not found in registry"):
            simple_uod.narrow_doubt_at_state("nonexistent", state_id, {"answer_hash"})

    def test_narrow_with_no_overlap_raises(self, simple_uod, multi_answer_doubt):
        """Test that narrowing with no overlap raises ValueError."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_doubt_at_state(state_id, multi_answer_doubt)

        # Try to narrow to answers outside alternatives
        with pytest.raises(ValueError, match="No overlap"):
            simple_uod.narrow_doubt_at_state(
                multi_answer_doubt.id, state_id, {"invalid_answer_1", "invalid_answer_2"}
            )

    def test_narrow_partial_overlap(self, simple_uod, multi_answer_doubt):
        """Test narrowing with partial overlap (valid)."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_doubt_at_state(state_id, multi_answer_doubt)

        # Narrow with partial overlap (2 valid, 1 invalid)
        narrowed_answers = {"answer_x_hash", "answer_y_hash", "invalid_answer"}
        narrowed = simple_uod.narrow_doubt_at_state(
            multi_answer_doubt.id, state_id, narrowed_answers
        )

        # Should only keep valid answers
        assert frozenset({"answer_x_hash", "answer_y_hash"}) == narrowed.alternatives

    def test_narrow_records_at_state(self, simple_uod, multi_answer_doubt):
        """Test that narrowing records the doubt at the narrowing state."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_doubt_at_state(state_id, multi_answer_doubt)

        narrowed = simple_uod.narrow_doubt_at_state(
            multi_answer_doubt.id, state_id, {"answer_x_hash", "answer_y_hash"}
        )

        # Should be recorded at state
        assert state_id in simple_uod.doubts_by_state
        # Will have 2 entries: initial and narrowed
        doubts_at_state = simple_uod.doubts_at_state(state_id)
        assert len(doubts_at_state) >= 2
        # Last one should be the narrowed version
        assert doubts_at_state[-1].status == "partial"

    def test_narrow_multiple_times_progressive_narrowing(self, simple_uod, multi_answer_doubt):
        """Test narrowing multiple times progressively at same state."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_doubt_at_state(state_id, multi_answer_doubt)

        # First narrowing
        narrowed_1 = simple_uod.narrow_doubt_at_state(
            multi_answer_doubt.id, state_id, {"answer_x_hash", "answer_y_hash", "answer_z_hash"}
        )
        assert len(narrowed_1.alternatives) == 3

        # Second narrowing (even narrower)
        narrowed_2 = simple_uod.narrow_doubt_at_state(
            multi_answer_doubt.id, state_id, {"answer_x_hash", "answer_y_hash"}
        )
        assert len(narrowed_2.alternatives) == 2
        # Resolution path should include the state
        assert state_id in narrowed_2.selection_path


# ===== Tests: Querying Doubts =====


class TestDoubtsAtState:
    """Test querying doubts at specific states."""

    def test_doubts_at_state_empty(self, simple_uod):
        """Test that querying a state with no doubts returns empty list."""
        state_id = simple_uod.history.current_state_id
        doubts = simple_uod.doubts_at_state(state_id)
        assert doubts == []

    def test_doubts_at_state_single(self, simple_uod, sample_doubt):
        """Test querying a state with one doubt."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_doubt_at_state(state_id, sample_doubt)

        doubts = simple_uod.doubts_at_state(state_id)
        assert len(doubts) == 1
        assert doubts[0] == sample_doubt

    def test_doubts_at_state_multiple(self, simple_uod, sample_doubt, multi_answer_doubt):
        """Test querying a state with multiple doubts."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_doubt_at_state(state_id, sample_doubt)
        simple_uod.record_doubt_at_state(state_id, multi_answer_doubt)

        doubts = simple_uod.doubts_at_state(state_id)
        assert len(doubts) == 2
        assert sample_doubt in doubts
        assert multi_answer_doubt in doubts

    def test_doubts_at_state_nonexistent_state(self, simple_uod):
        """Test querying a nonexistent state returns empty list."""
        doubts = simple_uod.doubts_at_state("nonexistent_state")
        assert doubts == []

    def test_doubts_at_state_multiple_distinct_doubts(self, simple_uod, sample_doubt, multi_answer_doubt):
        """Test doubts at state with multiple distinct doubts."""
        state_id = simple_uod.history.current_state_id

        # Record multiple doubts
        simple_uod.record_doubt_at_state(state_id, sample_doubt)
        simple_uod.record_doubt_at_state(state_id, multi_answer_doubt)

        doubts = simple_uod.doubts_at_state(state_id)
        assert len(doubts) == 2
        doubt_ids = {d.id for d in doubts}
        assert sample_doubt.id in doubt_ids
        assert multi_answer_doubt.id in doubt_ids


# ===== Tests: Doubt Lifecycle =====


class TestDoubtLifecycle:
    """Test tracing doubt lifecycles through the DAG."""

    def test_lifecycle_single_state(self, simple_uod, simple_egi):
        """Test lifecycle of a doubt that emerges and stays at one state."""
        state_id = simple_uod.history.current_state_id

        # Create a doubt with the correct emerged_at_state
        doubt = Doubt(
            id="lifecycle_test_d0",
            context=simple_egi,
            alternatives=frozenset({"answer_a", "answer_b"}),
            emerged_at_state=state_id,
        )

        simple_uod.record_doubt_at_state(state_id, doubt)

        lifecycle = simple_uod.doubt_lifecycle(doubt.id)
        # Should have at least one entry
        assert len(lifecycle) >= 1
        # First entry should be at the emerged state
        assert lifecycle[0][0] == state_id

    def test_lifecycle_multiple_operations(self, simple_uod, sample_doubt):
        """Test lifecycle through multiple operations at same state."""
        state_id = simple_uod.history.current_state_id

        # Record the doubt initially
        simple_uod.record_doubt_at_state(state_id, sample_doubt)

        # Narrow the doubt
        narrowed = simple_uod.narrow_doubt_at_state(
            sample_doubt.id, state_id, {"answer_a_hash"}
        )

        # Resolve the doubt
        resolved = simple_uod.resolve_doubt_at_state(
            sample_doubt.id, state_id, "answer_a_hash"
        )

        lifecycle = simple_uod.doubt_lifecycle(sample_doubt.id)

        # Should have entries
        assert len(lifecycle) >= 1
        # Latest version in lifecycle should be resolved
        assert lifecycle[-1][1].status == "resolved"

    def test_lifecycle_nonexistent_doubt_raises(self, simple_uod):
        """Test that querying lifecycle of nonexistent doubt raises ValueError."""
        with pytest.raises(ValueError, match="not found in registry"):
            simple_uod.doubt_lifecycle("nonexistent")

    def test_lifecycle_returns_tuples(self, simple_uod, sample_doubt):
        """Test that lifecycle returns (state_id, Doubt) tuples."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_doubt_at_state(state_id, sample_doubt)

        lifecycle = simple_uod.doubt_lifecycle(sample_doubt.id)

        for entry in lifecycle:
            assert isinstance(entry, tuple)
            assert len(entry) == 2
            state_id_entry, doubt_entry = entry
            assert isinstance(state_id_entry, str)
            assert isinstance(doubt_entry, Doubt)

    def test_lifecycle_ordered(self, simple_uod, sample_doubt):
        """Test that lifecycle maintains order through selection_path."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_doubt_at_state(state_id, sample_doubt)

        # Narrow the doubt to add it to resolution path
        simple_uod.narrow_doubt_at_state(sample_doubt.id, state_id, {"answer_a_hash"})

        lifecycle = simple_uod.doubt_lifecycle(sample_doubt.id)

        # Should include emerged state
        state_ids = [state_id_in_lifecycle for state_id_in_lifecycle, _ in lifecycle]
        assert state_id in state_ids


# ===== Tests: Backward Compatibility =====


class TestBackwardCompatibility:
    """Test that existing UoDs without doubts work correctly."""

    def test_uod_without_doubts_default_empty(self, simple_uod):
        """Test that UoD fields default to empty."""
        assert simple_uod.doubts_by_state == {}
        assert simple_uod.all_doubts == {}

    def test_uod_without_doubts_query_returns_empty(self, simple_uod):
        """Test that querying doubts on UoD without doubts returns empty."""
        state_id = simple_uod.history.current_state_id
        assert simple_uod.doubts_at_state(state_id) == []

    def test_existing_uod_can_add_doubts_later(self, simple_uod, sample_doubt):
        """Test that an existing UoD can add doubts later."""
        # Initially no doubts
        assert len(simple_uod.all_doubts) == 0

        # Add doubt
        state_id = simple_uod.history.current_state_id
        simple_uod.record_doubt_at_state(state_id, sample_doubt)

        # Now has doubts
        assert len(simple_uod.all_doubts) == 1
        assert sample_doubt.id in simple_uod.all_doubts

    def test_uod_properties_unchanged_by_doubts(self, simple_uod, sample_doubt):
        """Test that adding doubts doesn't change other UoD properties."""
        state_id = simple_uod.history.current_state_id
        egi_before = simple_uod.current_egi

        simple_uod.record_doubt_at_state(state_id, sample_doubt)

        # UoD properties should be unchanged
        assert simple_uod.current_egi == egi_before
        assert simple_uod.uod_id == "test-uod-001"
        assert simple_uod.name == "Test UoD with Doubts"


# ===== Tests: Edge Cases and Integration =====


class TestEdgeCases:
    """Test edge cases and integration scenarios."""

    def test_record_same_doubt_twice_same_state(self, simple_uod, sample_doubt):
        """Test recording the same doubt twice at the same state."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_doubt_at_state(state_id, sample_doubt)
        simple_uod.record_doubt_at_state(state_id, sample_doubt)

        # Should have two entries at state (same doubt recorded twice)
        doubts = simple_uod.doubts_at_state(state_id)
        assert len(doubts) == 2

    def test_resolve_then_query_state(self, simple_uod, sample_doubt):
        """Test that resolved doubts appear at resolution state."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_doubt_at_state(state_id, sample_doubt)

        simple_uod.resolve_doubt_at_state(sample_doubt.id, state_id, "answer_a_hash")

        # Resolved doubt should appear at state
        doubts_at_state = simple_uod.doubts_at_state(state_id)
        # Will have recorded once, then resolved once
        assert len(doubts_at_state) >= 1
        # Last entry should be resolved
        assert doubts_at_state[-1].status == "resolved"

    def test_narrow_then_resolve(self, simple_uod, multi_answer_doubt):
        """Test narrowing followed by resolution."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_doubt_at_state(state_id, multi_answer_doubt)

        # Narrow
        narrowed = simple_uod.narrow_doubt_at_state(
            multi_answer_doubt.id, state_id, {"answer_x_hash", "answer_y_hash"}
        )
        assert narrowed.status == "partial"

        # Resolve
        resolved = simple_uod.resolve_doubt_at_state(
            multi_answer_doubt.id, state_id, "answer_x_hash"
        )
        assert resolved.status == "resolved"

        # Check registry has latest
        assert simple_uod.all_doubts[multi_answer_doubt.id].status == "resolved"

    def test_all_doubts_immutable_copy(self, simple_uod, sample_doubt):
        """Test that all_doubts contains immutable Doubt objects."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_doubt_at_state(state_id, sample_doubt)

        # Try to modify (should fail for frozen dataclass)
        retrieved = simple_uod.all_doubts[sample_doubt.id]
        with pytest.raises(Exception):  # FrozenInstanceError
            retrieved.id = "modified"

    def test_state_list_fresh_instance(self, simple_uod, sample_doubt):
        """Test that doubts_at_state returns a fresh list."""
        state_id = simple_uod.history.current_state_id
        simple_uod.record_doubt_at_state(state_id, sample_doubt)

        list1 = simple_uod.doubts_at_state(state_id)
        list2 = simple_uod.doubts_at_state(state_id)

        # Should be different list objects
        assert list1 is not list2
        # But same contents
        assert list1 == list2
