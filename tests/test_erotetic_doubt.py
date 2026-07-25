"""
Test suite for the Doubt class (erotetic logic).

Covers the full lifecycle of doubts: emergence, narrowing, deepening,
resolution, and re-emergence. Includes JSON serialization round-trips
and immutability guarantees.
"""

import pytest
from egif_parser_dau import parse_egif
from eg_navigation import same_graph
from erotetic_doubt import Doubt


@pytest.fixture
def blank_egi():
    """A blank sheet (empty EGI)."""
    return parse_egif("")


@pytest.fixture
def simple_egi():
    """A simple proposition: (P *x)."""
    return parse_egif("(P *x)")


@pytest.fixture
def complex_egi():
    """A more complex graph: ~[ (P *x) (Q x *y) ]."""
    return parse_egif("~[ (P *x) (Q x *y) ]")


@pytest.fixture
def sample_doubt(blank_egi):
    """A sample doubt with 3 possible answers."""
    answers = frozenset({"answer_1", "answer_2", "answer_3"})
    return Doubt(
        id="d0",
        presupposition=blank_egi,
        erotetic_core=answers,
        emerged_at_state_id="s0",
        kind="unknown_verdict",
        warrant=0.9,
        source="test",
    )


class TestDoubtConstruction:
    """Test Doubt instantiation and field defaults."""

    def test_minimal_construction(self, blank_egi):
        """Create a Doubt with minimal required fields."""
        doubt = Doubt(
            id="d0",
            presupposition=blank_egi,
            erotetic_core=frozenset({"a1", "a2"}),
            emerged_at_state_id="s0",
        )
        assert doubt.id == "d0"
        assert doubt.status == "unresolved"
        assert doubt.current_answers == frozenset()
        assert doubt.warrant == 1.0
        assert doubt.source == "unspecified"

    def test_full_construction(self, blank_egi):
        """Create a Doubt with all fields explicitly set."""
        answers = frozenset({"a1", "a2"})
        current = frozenset({"a1"})
        path = ["s0", "s1", "s2"]

        doubt = Doubt(
            id="d1",
            presupposition=blank_egi,
            erotetic_core=answers,
            current_answers=current,
            status="partial",
            emerged_at_state_id="s0",
            resolved_at_state_id="s2",
            resolution_path=path,
            kind="thin_spot",
            warrant=0.75,
            source="oracle",
        )

        assert doubt.id == "d1"
        assert doubt.current_answers == current
        assert doubt.status == "partial"
        assert doubt.resolved_at_state_id == "s2"
        assert len(doubt.resolution_path) == 3
        assert doubt.kind == "thin_spot"

    def test_immutability(self, blank_egi):
        """Doubts are immutable (frozen dataclass)."""
        doubt = Doubt(
            id="d0",
            presupposition=blank_egi,
            erotetic_core=frozenset({"a1"}),
            emerged_at_state_id="s0",
        )

        with pytest.raises(AttributeError):
            doubt.id = "d1"

        with pytest.raises(AttributeError):
            doubt.status = "resolved"


class TestDoubtNarrow:
    """Test narrowing the erotetic_core."""

    def test_narrow_reduces_core(self, sample_doubt):
        """Narrowing reduces erotetic_core to intersection."""
        narrowed = sample_doubt.narrow_to({"answer_1", "answer_2"})

        assert narrowed.erotetic_core == frozenset({"answer_1", "answer_2"})
        assert narrowed.current_answers == frozenset({"answer_1", "answer_2"})

    def test_narrow_updates_status_unresolved_to_partial(self, sample_doubt):
        """Narrowing changes status from unresolved → partial."""
        assert sample_doubt.status == "unresolved"

        narrowed = sample_doubt.narrow_to({"answer_1", "answer_2"})

        assert narrowed.status == "partial"

    def test_narrow_preserves_status_if_partial(self, blank_egi):
        """Narrowing preserves status if already partial."""
        partial_doubt = Doubt(
            id="d0",
            presupposition=blank_egi,
            erotetic_core=frozenset({"a1", "a2", "a3"}),
            status="partial",
            emerged_at_state_id="s0",
        )

        narrowed = partial_doubt.narrow_to({"a1", "a2"})

        assert narrowed.status == "partial"

    def test_narrow_preserves_other_fields(self, sample_doubt):
        """Narrowing preserves id, kind, warrant, source."""
        narrowed = sample_doubt.narrow_to({"answer_1"})

        assert narrowed.id == sample_doubt.id
        assert narrowed.kind == sample_doubt.kind
        assert narrowed.warrant == sample_doubt.warrant
        assert narrowed.source == sample_doubt.source

    def test_narrow_empty_answers_raises(self, sample_doubt):
        """Narrowing to empty set raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            sample_doubt.narrow_to(set())

    def test_narrow_no_overlap_raises(self, sample_doubt):
        """Narrowing to non-overlapping set raises ValueError."""
        with pytest.raises(ValueError, match="No overlap"):
            sample_doubt.narrow_to({"nonexistent"})

    def test_narrow_subset_works(self, sample_doubt):
        """Narrowing to a single answer works."""
        narrowed = sample_doubt.narrow_to({"answer_1"})

        assert narrowed.erotetic_core == frozenset({"answer_1"})
        assert narrowed.current_answers == frozenset({"answer_1"})


class TestDoubtResolve:
    """Test resolving to a single answer."""

    def test_resolve_locks_status(self, sample_doubt):
        """Resolving locks status to 'resolved'."""
        resolved = sample_doubt.resolve_to("answer_1")

        assert resolved.status == "resolved"

    def test_resolve_sets_single_answer(self, sample_doubt):
        """Resolving sets current_answers to singleton."""
        resolved = sample_doubt.resolve_to("answer_2")

        assert resolved.current_answers == frozenset({"answer_2"})

    def test_resolve_invalid_answer_raises(self, sample_doubt):
        """Resolving to non-existent answer raises ValueError."""
        with pytest.raises(ValueError, match="not in erotetic_core"):
            sample_doubt.resolve_to("nonexistent")

    def test_resolve_preserves_core(self, sample_doubt):
        """Resolving preserves erotetic_core unchanged."""
        original_core = sample_doubt.erotetic_core
        resolved = sample_doubt.resolve_to("answer_1")

        assert resolved.erotetic_core == original_core

    def test_resolve_preserves_metadata(self, sample_doubt):
        """Resolving preserves all metadata fields."""
        resolved = sample_doubt.resolve_to("answer_1")

        assert resolved.id == sample_doubt.id
        assert resolved.kind == sample_doubt.kind
        assert resolved.warrant == sample_doubt.warrant
        assert resolved.source == sample_doubt.source


class TestDoubtDeepen:
    """Test deepening (adding new answers)."""

    def test_deepen_expands_core(self, sample_doubt):
        """Deepening expands erotetic_core."""
        deepened = sample_doubt.deepen({"answer_4", "answer_5"})

        assert frozenset({"answer_4", "answer_5"}).issubset(deepened.erotetic_core)
        assert len(deepened.erotetic_core) == 5

    def test_deepen_preserves_existing(self, sample_doubt):
        """Deepening preserves existing answers."""
        deepened = sample_doubt.deepen({"answer_4"})

        for ans in sample_doubt.erotetic_core:
            assert ans in deepened.erotetic_core

    def test_deepen_from_unresolved_stays_unresolved(self, sample_doubt):
        """Deepening unresolved doubt keeps it unresolved."""
        assert sample_doubt.status == "unresolved"

        deepened = sample_doubt.deepen({"answer_4"})

        assert deepened.status == "unresolved"

    def test_deepen_from_partial_stays_partial(self, blank_egi):
        """Deepening a partial doubt keeps it partial."""
        partial = Doubt(
            id="d0",
            presupposition=blank_egi,
            erotetic_core=frozenset({"a1", "a2"}),
            current_answers=frozenset({"a1"}),
            status="partial",
            emerged_at_state_id="s0",
        )

        deepened = partial.deepen({"a3"})

        assert deepened.status == "partial"
        assert deepened.current_answers == frozenset({"a1"})

    def test_deepen_empty_raises(self, sample_doubt):
        """Deepening with empty set raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            sample_doubt.deepen(set())

    def test_deepen_preserves_metadata(self, sample_doubt):
        """Deepening preserves metadata."""
        deepened = sample_doubt.deepen({"answer_4"})

        assert deepened.id == sample_doubt.id
        assert deepened.kind == sample_doubt.kind
        assert deepened.warrant == sample_doubt.warrant


class TestDoubtReemergent:
    """Test re-emergence (abductive cycle)."""

    def test_reemergent_updates_presupposition(self, blank_egi, simple_egi, sample_doubt):
        """Re-emergence updates presupposition."""
        reemergent = sample_doubt.reemergent_from(simple_egi)

        assert reemergent.presupposition == simple_egi
        assert reemergent.presupposition != sample_doubt.presupposition

    def test_reemergent_resets_status(self, simple_egi, sample_doubt):
        """Re-emergence resets status to unresolved."""
        resolved = sample_doubt.resolve_to("answer_1")
        assert resolved.status == "resolved"

        reemergent = resolved.reemergent_from(simple_egi)

        assert reemergent.status == "unresolved"

    def test_reemergent_clears_current_answers(self, simple_egi, sample_doubt):
        """Re-emergence clears current_answers."""
        narrowed = sample_doubt.narrow_to({"answer_1"})
        assert narrowed.current_answers == frozenset({"answer_1"})

        reemergent = narrowed.reemergent_from(simple_egi)

        assert reemergent.current_answers == frozenset()

    def test_reemergent_clears_resolution_id(self, simple_egi):
        """Re-emergence clears resolved_at_state_id."""
        doubt = Doubt(
            id="d0",
            presupposition=parse_egif(""),
            erotetic_core=frozenset({"a1"}),
            resolved_at_state_id="s3",
            emerged_at_state_id="s0",
        )

        reemergent = doubt.reemergent_from(simple_egi)

        assert reemergent.resolved_at_state_id is None

    def test_reemergent_preserves_identity(self, simple_egi, sample_doubt):
        """Re-emergence preserves id and kind."""
        reemergent = sample_doubt.reemergent_from(simple_egi)

        assert reemergent.id == sample_doubt.id
        assert reemergent.kind == sample_doubt.kind

    def test_reemergent_preserves_erotetic_core(self, simple_egi, sample_doubt):
        """Re-emergence preserves erotetic_core."""
        reemergent = sample_doubt.reemergent_from(simple_egi)

        assert reemergent.erotetic_core == sample_doubt.erotetic_core


class TestDoubtSerialization:
    """Test JSON serialization (to_dict/from_dict)."""

    def test_to_dict_includes_all_fields(self, sample_doubt):
        """to_dict includes all fields."""
        data = sample_doubt.to_dict()

        assert "id" in data
        assert "presupposition" in data
        assert "erotetic_core" in data
        assert "current_answers" in data
        assert "status" in data
        assert "emerged_at_state_id" in data
        assert "resolved_at_state_id" in data
        assert "resolution_path" in data
        assert "kind" in data
        assert "warrant" in data
        assert "source" in data

    def test_to_dict_presupposition_is_string(self, sample_doubt):
        """to_dict converts presupposition to EGIF string."""
        data = sample_doubt.to_dict()

        assert isinstance(data["presupposition"], str)

    def test_to_dict_erotetic_core_is_list(self, sample_doubt):
        """to_dict converts erotetic_core to sorted list."""
        data = sample_doubt.to_dict()

        assert isinstance(data["erotetic_core"], list)
        assert data["erotetic_core"] == sorted(sample_doubt.erotetic_core)

    def test_round_trip_blank_sheet(self, blank_egi):
        """Round-trip: blank sheet."""
        original = Doubt(
            id="d0",
            presupposition=blank_egi,
            erotetic_core=frozenset({"a1", "a2"}),
            emerged_at_state_id="s0",
        )

        data = original.to_dict()
        restored = Doubt.from_dict(data)

        assert restored.id == original.id
        assert restored.erotetic_core == original.erotetic_core
        assert restored.status == original.status

    def test_round_trip_with_current_answers(self, blank_egi):
        """Round-trip with current_answers set."""
        original = Doubt(
            id="d1",
            presupposition=blank_egi,
            erotetic_core=frozenset({"a1", "a2", "a3"}),
            current_answers=frozenset({"a1", "a2"}),
            status="partial",
            emerged_at_state_id="s0",
        )

        data = original.to_dict()
        restored = Doubt.from_dict(data)

        assert restored.current_answers == original.current_answers
        assert restored.status == original.status

    def test_round_trip_with_resolution_id(self, blank_egi):
        """Round-trip with resolved_at_state_id set."""
        original = Doubt(
            id="d2",
            presupposition=blank_egi,
            erotetic_core=frozenset({"a1"}),
            current_answers=frozenset({"a1"}),
            status="resolved",
            emerged_at_state_id="s0",
            resolved_at_state_id="s3",
        )

        data = original.to_dict()
        restored = Doubt.from_dict(data)

        assert restored.resolved_at_state_id == original.resolved_at_state_id

    def test_round_trip_with_resolution_path(self, blank_egi):
        """Round-trip with resolution_path."""
        original = Doubt(
            id="d3",
            presupposition=blank_egi,
            erotetic_core=frozenset({"a1"}),
            emerged_at_state_id="s0",
            resolution_path=["s0", "s1", "s2", "s3"],
        )

        data = original.to_dict()
        restored = Doubt.from_dict(data)

        assert restored.resolution_path == original.resolution_path

    def test_round_trip_with_metadata(self, blank_egi):
        """Round-trip with full metadata."""
        original = Doubt(
            id="d4",
            presupposition=blank_egi,
            erotetic_core=frozenset({"a1", "a2"}),
            kind="thin_spot",
            warrant=0.75,
            source="attention_brief",
            emerged_at_state_id="s0",
        )

        data = original.to_dict()
        restored = Doubt.from_dict(data)

        assert restored.kind == original.kind
        assert restored.warrant == original.warrant
        assert restored.source == original.source

    def test_round_trip_complex_graph(self, complex_egi):
        """Round-trip with a complex presupposition."""
        original = Doubt(
            id="d5",
            presupposition=complex_egi,
            erotetic_core=frozenset({"a1", "a2"}),
            emerged_at_state_id="s0",
        )

        data = original.to_dict()
        restored = Doubt.from_dict(data)

        # Check that the presupposition was preserved
        # Use same_graph for structural equality (IDs may differ after parse/generate)
        assert same_graph(restored.presupposition, original.presupposition)


class TestDoubtLifecycle:
    """Test a complete doubt lifecycle."""

    def test_lifecycle_unresolved_to_partial_to_resolved(self, blank_egi):
        """Full lifecycle: unresolved → partial → resolved."""
        # Emergence
        doubt = Doubt(
            id="d0",
            presupposition=blank_egi,
            erotetic_core=frozenset({"a1", "a2", "a3"}),
            emerged_at_state_id="s0",
        )
        assert doubt.status == "unresolved"

        # Narrowing → partial
        narrowed = doubt.narrow_to({"a1", "a2"})
        assert narrowed.status == "partial"

        # Resolution
        resolved = narrowed.resolve_to("a1")
        assert resolved.status == "resolved"
        assert resolved.current_answers == frozenset({"a1"})

    def test_lifecycle_with_deepening(self, blank_egi):
        """Lifecycle with deepening: narrow → deepen → resolve."""
        doubt = Doubt(
            id="d0",
            presupposition=blank_egi,
            erotetic_core=frozenset({"a1", "a2"}),
            emerged_at_state_id="s0",
        )

        # Narrow
        narrowed = doubt.narrow_to({"a1"})
        assert narrowed.current_answers == frozenset({"a1"})

        # Deepen
        deepened = narrowed.deepen({"a3"})
        assert frozenset({"a3"}).issubset(deepened.erotetic_core)
        assert deepened.status == "partial"

        # Resolve
        resolved = deepened.resolve_to("a3")
        assert resolved.status == "resolved"

    def test_lifecycle_with_reemergence(self, blank_egi, simple_egi):
        """Lifecycle with re-emergence: resolve → reemergent → resolve."""
        # Initial
        doubt = Doubt(
            id="d0",
            presupposition=blank_egi,
            erotetic_core=frozenset({"a1", "a2"}),
            emerged_at_state_id="s0",
        )

        # Resolve
        resolved = doubt.resolve_to("a1")
        assert resolved.status == "resolved"

        # Re-emerge
        reemergent = resolved.reemergent_from(simple_egi)
        assert reemergent.status == "unresolved"
        assert reemergent.current_answers == frozenset()

        # Resolve again
        resolved_again = reemergent.resolve_to("a1")
        assert resolved_again.status == "resolved"


class TestDoubtEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_single_answer_erotetic_core(self, blank_egi):
        """Doubt with single-element erotetic_core."""
        doubt = Doubt(
            id="d0",
            presupposition=blank_egi,
            erotetic_core=frozenset({"a1"}),
            emerged_at_state_id="s0",
        )

        resolved = doubt.resolve_to("a1")
        assert resolved.status == "resolved"
        assert resolved.erotetic_core == frozenset({"a1"})

    def test_large_erotetic_core(self, blank_egi):
        """Doubt with many possible answers."""
        many_answers = frozenset({f"a{i}" for i in range(100)})

        doubt = Doubt(
            id="d0",
            presupposition=blank_egi,
            erotetic_core=many_answers,
            emerged_at_state_id="s0",
        )

        assert len(doubt.erotetic_core) == 100

        narrowed = doubt.narrow_to({f"a{i}" for i in range(50)})
        assert len(narrowed.erotetic_core) == 50

    def test_warrant_at_boundaries(self, blank_egi):
        """Test warrant at 0.0 and 1.0."""
        low_warrant = Doubt(
            id="d0",
            presupposition=blank_egi,
            erotetic_core=frozenset({"a1"}),
            emerged_at_state_id="s0",
            warrant=0.0,
        )
        assert low_warrant.warrant == 0.0

        high_warrant = Doubt(
            id="d1",
            presupposition=blank_egi,
            erotetic_core=frozenset({"a1"}),
            emerged_at_state_id="s0",
            warrant=1.0,
        )
        assert high_warrant.warrant == 1.0

    def test_empty_resolution_path(self, blank_egi):
        """Doubt with empty resolution_path (default)."""
        doubt = Doubt(
            id="d0",
            presupposition=blank_egi,
            erotetic_core=frozenset({"a1"}),
            emerged_at_state_id="s0",
        )

        assert doubt.resolution_path == []

    def test_long_resolution_path(self, blank_egi):
        """Doubt with long resolution_path."""
        path = [f"s{i}" for i in range(100)]

        doubt = Doubt(
            id="d0",
            presupposition=blank_egi,
            erotetic_core=frozenset({"a1"}),
            emerged_at_state_id="s0",
            resolution_path=path,
        )

        data = doubt.to_dict()
        restored = Doubt.from_dict(data)

        assert restored.resolution_path == path


class TestDoubtComparison:
    """Test comparison and equality semantics."""

    def test_identical_doubts_equal(self, blank_egi):
        """Two identically constructed doubts are equal."""
        d1 = Doubt(
            id="d0",
            presupposition=blank_egi,
            erotetic_core=frozenset({"a1"}),
            emerged_at_state_id="s0",
        )

        d2 = Doubt(
            id="d0",
            presupposition=blank_egi,
            erotetic_core=frozenset({"a1"}),
            emerged_at_state_id="s0",
        )

        assert d1 == d2

    def test_different_ids_not_equal(self, blank_egi):
        """Doubts with different ids are not equal."""
        d1 = Doubt(
            id="d0",
            presupposition=blank_egi,
            erotetic_core=frozenset({"a1"}),
            emerged_at_state_id="s0",
        )

        d2 = Doubt(
            id="d1",
            presupposition=blank_egi,
            erotetic_core=frozenset({"a1"}),
            emerged_at_state_id="s0",
        )

        assert d1 != d2
