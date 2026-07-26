"""
Test suite for the AlternativeSet class (generalized deliberation structure).

Covers the full lifecycle of alternative-sets: emergence, narrowing, deepening,
resolution, and re-emergence. Includes JSON serialization round-trips,
immutability guarantees, and tests for all deliberative kinds.

Tests parametrized by kind to ensure semantics work uniformly across:
- interrogative (Q: "which answer?")
- hypothetical (Q: "which theory?")
- modal (Q: "which future?")
- counterfactual (Q: "if X, then?")
- agentive (Q: "which action?")
- epistemic (Q: "which world?")
- metacognitive (Q: "what could I think?")
"""

import pytest
from egif_parser_dau import parse_egif
from eg_navigation import same_graph
from alternative_set import AlternativeSet


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


@pytest.fixture(params=[
    "interrogative", "hypothetical", "modal",
    "counterfactual", "agentive", "epistemic", "metacognitive"
])
def alt_set_kind(request):
    """Parametrize over all deliberative kinds."""
    return request.param


@pytest.fixture
def sample_alt_set(blank_egi, alt_set_kind):
    """A sample alternative-set with 3 possible choices."""
    choices = frozenset({"choice_1", "choice_2", "choice_3"})
    return AlternativeSet(
        id="a0",
        context=blank_egi,
        alternatives=choices,
        kind=alt_set_kind,
        emerged_at_state="s0",
        warrant=0.9,
        source="test",
    )


@pytest.fixture
def multi_choice_alt_set(blank_egi, alt_set_kind):
    """An alternative-set with 4 possible choices."""
    choices = frozenset({"choice_x", "choice_y", "choice_z", "choice_w"})
    return AlternativeSet(
        id="a1",
        context=blank_egi,
        alternatives=choices,
        kind=alt_set_kind,
        emerged_at_state="s1",
        warrant=0.85,
        source="test",
    )


class TestAlternativeSetConstruction:
    """Test AlternativeSet instantiation and field defaults."""

    def test_minimal_construction(self, blank_egi):
        """Create an AlternativeSet with minimal required fields."""
        alt_set = AlternativeSet(
            id="a0",
            context=blank_egi,
            alternatives=frozenset({"c1", "c2"}),
            emerged_at_state="s0",
        )
        assert alt_set.id == "a0"
        assert alt_set.status == "unresolved"
        assert alt_set.current_selection == frozenset()
        assert alt_set.warrant == 1.0
        assert alt_set.source == "unspecified"
        assert alt_set.kind == "other"

    def test_full_construction(self, blank_egi):
        """Create an AlternativeSet with all fields explicitly set."""
        choices = frozenset({"c1", "c2"})
        current = frozenset({"c1"})
        path = ["s0", "s1", "s2"]

        alt_set = AlternativeSet(
            id="a1",
            context=blank_egi,
            alternatives=choices,
            current_selection=current,
            kind="interrogative",
            emerged_at_state="s0",
            resolved_at_state="s2",
            selection_path=path,
            warrant=0.75,
            source="oracle",
        )

        assert alt_set.id == "a1"
        assert alt_set.current_selection == current
        # Status is resolved when len(current_selection) == 1 (and thus len(current) == 1)
        assert alt_set.status == "resolved"
        assert alt_set.resolved_at_state == "s2"
        assert len(alt_set.selection_path) == 3
        assert alt_set.kind == "interrogative"

    def test_immutability(self, blank_egi):
        """AlternativeSets are immutable (frozen dataclass)."""
        alt_set = AlternativeSet(
            id="a0",
            context=blank_egi,
            alternatives=frozenset({"c1"}),
            emerged_at_state="s0",
        )

        with pytest.raises(AttributeError):
            alt_set.id = "a1"

        with pytest.raises(AttributeError):
            alt_set.current_selection = frozenset({"c1"})


class TestStatusEncoding:
    """Test that status is correctly encoded via current_selection cardinality."""

    def test_status_unresolved_empty_selection(self, sample_alt_set):
        """Status is unresolved when current_selection is empty."""
        assert sample_alt_set.current_selection == frozenset()
        assert sample_alt_set.status == "unresolved"

    def test_status_partial_multiple_selections(self, blank_egi):
        """Status is partial when 0 < len(current_selection) < len(alternatives)."""
        alt_set = AlternativeSet(
            id="a0",
            context=blank_egi,
            alternatives=frozenset({"c1", "c2", "c3"}),
            current_selection=frozenset({"c1", "c2"}),
            emerged_at_state="s0",
        )
        assert alt_set.status == "partial"

    def test_status_resolved_single_selection(self, blank_egi):
        """Status is resolved when len(current_selection) == 1."""
        alt_set = AlternativeSet(
            id="a0",
            context=blank_egi,
            alternatives=frozenset({"c1", "c2"}),
            current_selection=frozenset({"c1"}),
            emerged_at_state="s0",
        )
        assert alt_set.status == "resolved"


class TestAlternativeSetNarrow:
    """Test narrowing the alternatives."""

    def test_narrow_reduces_alternatives(self, sample_alt_set):
        """Narrowing reduces alternatives to intersection."""
        narrowed = sample_alt_set.narrow_to({"choice_1", "choice_2"})

        assert narrowed.alternatives == frozenset({"choice_1", "choice_2"})
        assert narrowed.current_selection == frozenset({"choice_1", "choice_2"})

    def test_narrow_updates_status_unresolved_to_partial(self, sample_alt_set):
        """Narrowing changes status from unresolved → partial."""
        assert sample_alt_set.status == "unresolved"

        narrowed = sample_alt_set.narrow_to({"choice_1", "choice_2"})

        assert narrowed.status == "partial"

    def test_narrow_preserves_status_if_partial(self, blank_egi):
        """Narrowing preserves status if already partial."""
        partial_alt = AlternativeSet(
            id="a0",
            context=blank_egi,
            alternatives=frozenset({"c1", "c2", "c3"}),
            current_selection=frozenset({"c1"}),
            kind="hypothetical",
            emerged_at_state="s0",
        )

        narrowed = partial_alt.narrow_to({"c1", "c2"})

        assert narrowed.status == "partial"

    def test_narrow_preserves_other_fields(self, sample_alt_set):
        """Narrowing preserves id, kind, warrant, source."""
        narrowed = sample_alt_set.narrow_to({"choice_1"})

        assert narrowed.id == sample_alt_set.id
        assert narrowed.kind == sample_alt_set.kind
        assert narrowed.warrant == sample_alt_set.warrant
        assert narrowed.source == sample_alt_set.source

    def test_narrow_empty_choices_raises(self, sample_alt_set):
        """Narrowing to empty set raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            sample_alt_set.narrow_to(set())

    def test_narrow_no_overlap_raises(self, sample_alt_set):
        """Narrowing to non-overlapping set raises ValueError."""
        with pytest.raises(ValueError, match="No overlap"):
            sample_alt_set.narrow_to({"nonexistent"})

    def test_narrow_subset_works(self, sample_alt_set):
        """Narrowing to a single choice works."""
        narrowed = sample_alt_set.narrow_to({"choice_1"})

        assert narrowed.alternatives == frozenset({"choice_1"})
        assert narrowed.current_selection == frozenset({"choice_1"})


class TestAlternativeSetSelect:
    """Test selecting (resolving) to a single alternative."""

    def test_select_locks_status(self, sample_alt_set):
        """Selecting locks status to 'resolved'."""
        selected = sample_alt_set.select("choice_1")

        assert selected.status == "resolved"

    def test_select_sets_single_choice(self, sample_alt_set):
        """Selecting sets current_selection to singleton."""
        selected = sample_alt_set.select("choice_2")

        assert selected.current_selection == frozenset({"choice_2"})

    def test_select_invalid_choice_raises(self, sample_alt_set):
        """Selecting non-existent choice raises ValueError."""
        with pytest.raises(ValueError, match="not in alternatives"):
            sample_alt_set.select("nonexistent")

    def test_select_preserves_alternatives(self, sample_alt_set):
        """Selecting preserves alternatives unchanged."""
        original_alts = sample_alt_set.alternatives
        selected = sample_alt_set.select("choice_1")

        assert selected.alternatives == original_alts

    def test_select_preserves_metadata(self, sample_alt_set):
        """Selecting preserves all metadata fields."""
        selected = sample_alt_set.select("choice_1")

        assert selected.id == sample_alt_set.id
        assert selected.kind == sample_alt_set.kind
        assert selected.warrant == sample_alt_set.warrant
        assert selected.source == sample_alt_set.source


class TestAlternativeSetDeepen:
    """Test deepening (adding new alternatives)."""

    def test_deepen_expands_alternatives(self, sample_alt_set):
        """Deepening expands alternatives."""
        deepened = sample_alt_set.deepen({"choice_4", "choice_5"})

        assert frozenset({"choice_4", "choice_5"}).issubset(deepened.alternatives)
        assert len(deepened.alternatives) == 5

    def test_deepen_preserves_existing(self, sample_alt_set):
        """Deepening preserves existing alternatives."""
        deepened = sample_alt_set.deepen({"choice_4"})

        for choice in sample_alt_set.alternatives:
            assert choice in deepened.alternatives

    def test_deepen_from_unresolved_stays_unresolved(self, sample_alt_set):
        """Deepening unresolved alternative-set keeps it unresolved."""
        assert sample_alt_set.status == "unresolved"

        deepened = sample_alt_set.deepen({"choice_4"})

        assert deepened.status == "unresolved"

    def test_deepen_from_partial_stays_partial(self, blank_egi):
        """Deepening a partial alternative-set keeps it partial."""
        partial = AlternativeSet(
            id="a0",
            context=blank_egi,
            alternatives=frozenset({"c1", "c2"}),
            current_selection=frozenset({"c1", "c2"}),  # Multiple items = partial
            kind="modal",
            emerged_at_state="s0",
        )

        deepened = partial.deepen({"c3"})

        assert deepened.status == "partial"
        assert deepened.current_selection == frozenset({"c1", "c2"})

    def test_deepen_empty_raises(self, sample_alt_set):
        """Deepening with empty set raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            sample_alt_set.deepen(set())

    def test_deepen_preserves_metadata(self, sample_alt_set):
        """Deepening preserves metadata."""
        deepened = sample_alt_set.deepen({"choice_4"})

        assert deepened.id == sample_alt_set.id
        assert deepened.kind == sample_alt_set.kind
        assert deepened.warrant == sample_alt_set.warrant


class TestAlternativeSetRemerge:
    """Test re-emergence (abductive cycle)."""

    def test_remerge_updates_context(self, blank_egi, simple_egi, sample_alt_set):
        """Re-emergence updates context."""
        remerged = sample_alt_set.remerge_with(simple_egi)

        assert remerged.context == simple_egi
        assert remerged.context != sample_alt_set.context

    def test_remerge_resets_status(self, simple_egi, sample_alt_set):
        """Re-emergence resets status to unresolved."""
        selected = sample_alt_set.select("choice_1")
        assert selected.status == "resolved"

        remerged = selected.remerge_with(simple_egi)

        assert remerged.status == "unresolved"

    def test_remerge_clears_current_selection(self, simple_egi, sample_alt_set):
        """Re-emergence clears current_selection."""
        narrowed = sample_alt_set.narrow_to({"choice_1"})
        assert narrowed.current_selection == frozenset({"choice_1"})

        remerged = narrowed.remerge_with(simple_egi)

        assert remerged.current_selection == frozenset()

    def test_remerge_clears_resolved_at_state(self, simple_egi):
        """Re-emergence clears resolved_at_state."""
        alt_set = AlternativeSet(
            id="a0",
            context=parse_egif(""),
            alternatives=frozenset({"c1"}),
            resolved_at_state="s3",
            emerged_at_state="s0",
        )

        remerged = alt_set.remerge_with(simple_egi)

        assert remerged.resolved_at_state is None

    def test_remerge_preserves_identity(self, simple_egi, sample_alt_set):
        """Re-emergence preserves id and kind."""
        remerged = sample_alt_set.remerge_with(simple_egi)

        assert remerged.id == sample_alt_set.id
        assert remerged.kind == sample_alt_set.kind

    def test_remerge_preserves_alternatives(self, simple_egi, sample_alt_set):
        """Re-emergence preserves alternatives."""
        remerged = sample_alt_set.remerge_with(simple_egi)

        assert remerged.alternatives == sample_alt_set.alternatives


class TestAlternativeSetSerialization:
    """Test JSON serialization (to_dict/from_dict)."""

    def test_to_dict_includes_all_fields(self, sample_alt_set):
        """to_dict includes all fields."""
        data = sample_alt_set.to_dict()

        assert "id" in data
        assert "context" in data
        assert "alternatives" in data
        assert "current_selection" in data
        assert "kind" in data
        assert "emerged_at_state" in data
        assert "resolved_at_state" in data
        assert "selection_path" in data
        assert "warrant" in data
        assert "source" in data

    def test_to_dict_context_is_string(self, sample_alt_set):
        """to_dict converts context to EGIF string."""
        data = sample_alt_set.to_dict()

        assert isinstance(data["context"], str)

    def test_to_dict_alternatives_is_list(self, sample_alt_set):
        """to_dict converts alternatives to sorted list."""
        data = sample_alt_set.to_dict()

        assert isinstance(data["alternatives"], list)
        assert data["alternatives"] == sorted(sample_alt_set.alternatives)

    def test_round_trip_blank_context(self, blank_egi):
        """Round-trip: blank context."""
        original = AlternativeSet(
            id="a0",
            context=blank_egi,
            alternatives=frozenset({"c1", "c2"}),
            kind="interrogative",
            emerged_at_state="s0",
        )

        data = original.to_dict()
        restored = AlternativeSet.from_dict(data)

        assert restored.id == original.id
        assert restored.alternatives == original.alternatives
        assert restored.status == original.status
        assert restored.kind == original.kind

    def test_round_trip_with_current_selection(self, blank_egi):
        """Round-trip with current_selection set."""
        original = AlternativeSet(
            id="a1",
            context=blank_egi,
            alternatives=frozenset({"c1", "c2", "c3"}),
            current_selection=frozenset({"c1", "c2"}),
            kind="hypothetical",
            emerged_at_state="s0",
        )

        data = original.to_dict()
        restored = AlternativeSet.from_dict(data)

        assert restored.current_selection == original.current_selection
        assert restored.status == original.status

    def test_round_trip_with_resolved_at_state(self, blank_egi):
        """Round-trip with resolved_at_state set."""
        original = AlternativeSet(
            id="a2",
            context=blank_egi,
            alternatives=frozenset({"c1"}),
            current_selection=frozenset({"c1"}),
            kind="modal",
            emerged_at_state="s0",
            resolved_at_state="s3",
        )

        data = original.to_dict()
        restored = AlternativeSet.from_dict(data)

        assert restored.resolved_at_state == original.resolved_at_state

    def test_round_trip_with_selection_path(self, blank_egi):
        """Round-trip with selection_path."""
        original = AlternativeSet(
            id="a3",
            context=blank_egi,
            alternatives=frozenset({"c1"}),
            kind="counterfactual",
            emerged_at_state="s0",
            selection_path=["s0", "s1", "s2", "s3"],
        )

        data = original.to_dict()
        restored = AlternativeSet.from_dict(data)

        assert restored.selection_path == original.selection_path

    def test_round_trip_with_metadata(self, blank_egi):
        """Round-trip with full metadata."""
        original = AlternativeSet(
            id="a4",
            context=blank_egi,
            alternatives=frozenset({"c1", "c2"}),
            kind="agentive",
            warrant=0.75,
            source="attention_brief",
            emerged_at_state="s0",
        )

        data = original.to_dict()
        restored = AlternativeSet.from_dict(data)

        assert restored.kind == original.kind
        assert restored.warrant == original.warrant
        assert restored.source == original.source

    def test_round_trip_complex_context(self, complex_egi):
        """Round-trip with a complex presupposition."""
        original = AlternativeSet(
            id="a5",
            context=complex_egi,
            alternatives=frozenset({"c1", "c2"}),
            kind="epistemic",
            emerged_at_state="s0",
        )

        data = original.to_dict()
        restored = AlternativeSet.from_dict(data)

        # Check that the context was preserved
        # Use same_graph for structural equality (IDs may differ after parse/generate)
        assert same_graph(restored.context, original.context)


class TestAlternativeSetLifecycle:
    """Test a complete alternative-set lifecycle."""

    def test_lifecycle_unresolved_to_partial_to_resolved(self, blank_egi):
        """Full lifecycle: unresolved → partial → resolved."""
        # Emergence
        alt_set = AlternativeSet(
            id="a0",
            context=blank_egi,
            alternatives=frozenset({"c1", "c2", "c3"}),
            kind="interrogative",
            emerged_at_state="s0",
        )
        assert alt_set.status == "unresolved"

        # Narrowing → partial
        narrowed = alt_set.narrow_to({"c1", "c2"})
        assert narrowed.status == "partial"

        # Resolution
        selected = narrowed.select("c1")
        assert selected.status == "resolved"
        assert selected.current_selection == frozenset({"c1"})

    def test_lifecycle_with_deepening(self, blank_egi):
        """Lifecycle with deepening: narrow → deepen → select."""
        alt_set = AlternativeSet(
            id="a0",
            context=blank_egi,
            alternatives=frozenset({"c1", "c2"}),
            kind="hypothetical",
            emerged_at_state="s0",
        )

        # Narrow to multiple items (partial)
        narrowed = alt_set.narrow_to({"c1", "c2"})
        assert narrowed.current_selection == frozenset({"c1", "c2"})
        assert narrowed.status == "partial"

        # Deepen
        deepened = narrowed.deepen({"c3"})
        assert frozenset({"c3"}).issubset(deepened.alternatives)
        assert deepened.status == "partial"

        # Select
        selected = deepened.select("c3")
        assert selected.status == "resolved"

    def test_lifecycle_with_reemergence(self, blank_egi, simple_egi):
        """Lifecycle with re-emergence: select → remerge → select."""
        # Initial
        alt_set = AlternativeSet(
            id="a0",
            context=blank_egi,
            alternatives=frozenset({"c1", "c2"}),
            kind="modal",
            emerged_at_state="s0",
        )

        # Select
        selected = alt_set.select("c1")
        assert selected.status == "resolved"

        # Re-emerge
        remerged = selected.remerge_with(simple_egi)
        assert remerged.status == "unresolved"
        assert remerged.current_selection == frozenset()

        # Select again
        selected_again = remerged.select("c1")
        assert selected_again.status == "resolved"


class TestAlternativeSetEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_single_alternative(self, blank_egi):
        """Alternative-set with single-element alternatives."""
        alt_set = AlternativeSet(
            id="a0",
            context=blank_egi,
            alternatives=frozenset({"c1"}),
            kind="counterfactual",
            emerged_at_state="s0",
        )

        selected = alt_set.select("c1")
        assert selected.status == "resolved"
        assert selected.alternatives == frozenset({"c1"})

    def test_large_alternatives(self, blank_egi):
        """Alternative-set with many possible choices."""
        many_choices = frozenset({f"c{i}" for i in range(100)})

        alt_set = AlternativeSet(
            id="a0",
            context=blank_egi,
            alternatives=many_choices,
            kind="agentive",
            emerged_at_state="s0",
        )

        assert len(alt_set.alternatives) == 100

        narrowed = alt_set.narrow_to({f"c{i}" for i in range(50)})
        assert len(narrowed.alternatives) == 50

    def test_warrant_at_boundaries(self, blank_egi):
        """Test warrant at 0.0 and 1.0."""
        low_warrant = AlternativeSet(
            id="a0",
            context=blank_egi,
            alternatives=frozenset({"c1"}),
            kind="epistemic",
            emerged_at_state="s0",
            warrant=0.0,
        )
        assert low_warrant.warrant == 0.0

        high_warrant = AlternativeSet(
            id="a1",
            context=blank_egi,
            alternatives=frozenset({"c1"}),
            kind="metacognitive",
            emerged_at_state="s0",
            warrant=1.0,
        )
        assert high_warrant.warrant == 1.0

    def test_empty_selection_path(self, blank_egi):
        """Alternative-set with empty selection_path (default)."""
        alt_set = AlternativeSet(
            id="a0",
            context=blank_egi,
            alternatives=frozenset({"c1"}),
            kind="interrogative",
            emerged_at_state="s0",
        )

        assert alt_set.selection_path == []

    def test_long_selection_path(self, blank_egi):
        """Alternative-set with long selection_path."""
        path = [f"s{i}" for i in range(100)]

        alt_set = AlternativeSet(
            id="a0",
            context=blank_egi,
            alternatives=frozenset({"c1"}),
            kind="hypothetical",
            emerged_at_state="s0",
            selection_path=path,
        )

        data = alt_set.to_dict()
        restored = AlternativeSet.from_dict(data)

        assert restored.selection_path == path


class TestAlternativeSetComparison:
    """Test comparison and equality semantics."""

    def test_identical_alt_sets_equal(self, blank_egi):
        """Two identically constructed alt-sets are equal."""
        a1 = AlternativeSet(
            id="a0",
            context=blank_egi,
            alternatives=frozenset({"c1"}),
            kind="interrogative",
            emerged_at_state="s0",
        )

        a2 = AlternativeSet(
            id="a0",
            context=blank_egi,
            alternatives=frozenset({"c1"}),
            kind="interrogative",
            emerged_at_state="s0",
        )

        assert a1 == a2

    def test_different_ids_not_equal(self, blank_egi):
        """Alt-sets with different ids are not equal."""
        a1 = AlternativeSet(
            id="a0",
            context=blank_egi,
            alternatives=frozenset({"c1"}),
            kind="interrogative",
            emerged_at_state="s0",
        )

        a2 = AlternativeSet(
            id="a1",
            context=blank_egi,
            alternatives=frozenset({"c1"}),
            kind="interrogative",
            emerged_at_state="s0",
        )

        assert a1 != a2

    def test_different_kinds_not_equal(self, blank_egi):
        """Alt-sets with different kinds are not equal."""
        a1 = AlternativeSet(
            id="a0",
            context=blank_egi,
            alternatives=frozenset({"c1"}),
            kind="interrogative",
            emerged_at_state="s0",
        )

        a2 = AlternativeSet(
            id="a0",
            context=blank_egi,
            alternatives=frozenset({"c1"}),
            kind="hypothetical",
            emerged_at_state="s0",
        )

        assert a1 != a2


class TestKindSemantics:
    """Test semantics for each deliberative kind."""

    def test_interrogative_narrowing(self, blank_egi):
        """Interrogative narrowing: reducing possible answers."""
        alt_set = AlternativeSet(
            id="q1",
            context=blank_egi,
            alternatives=frozenset({"answer_a", "answer_b", "answer_c"}),
            kind="interrogative",
            emerged_at_state="s0",
            source="question",
        )

        narrowed = alt_set.narrow_to({"answer_a", "answer_b"})
        assert narrowed.status == "partial"
        assert len(narrowed.alternatives) == 2

    def test_hypothetical_testing(self, blank_egi):
        """Hypothetical testing: narrowing theories."""
        alt_set = AlternativeSet(
            id="h1",
            context=blank_egi,
            alternatives=frozenset({"theory_x", "theory_y", "theory_z"}),
            kind="hypothetical",
            emerged_at_state="s0",
            source="anomaly",
        )

        # Narrow to multiple theories (partial)
        narrowed = alt_set.narrow_to({"theory_x", "theory_y"})
        assert narrowed.status == "partial"

        # Select one
        selected = narrowed.select("theory_x")
        assert selected.status == "resolved"

    def test_modal_possibility_tracking(self, blank_egi):
        """Modal: tracking possible futures."""
        alt_set = AlternativeSet(
            id="m1",
            context=blank_egi,
            alternatives=frozenset({"future_1", "future_2", "future_3"}),
            kind="modal",
            emerged_at_state="s0",
        )

        narrowed = alt_set.narrow_to({"future_1", "future_2"})
        assert narrowed.status == "partial"

    def test_counterfactual_context_shift(self, blank_egi, simple_egi):
        """Counterfactual: shifting context for hypothetical."""
        alt_set = AlternativeSet(
            id="c1",
            context=blank_egi,
            alternatives=frozenset({"consequence_a", "consequence_b"}),
            kind="counterfactual",
            emerged_at_state="s0",
        )

        remerged = alt_set.remerge_with(simple_egi)
        assert remerged.status == "unresolved"
        assert remerged.context == simple_egi

    def test_agentive_commitment(self, blank_egi):
        """Agentive: committing to an action."""
        alt_set = AlternativeSet(
            id="ag1",
            context=blank_egi,
            alternatives=frozenset({"action_1", "action_2", "action_3"}),
            kind="agentive",
            emerged_at_state="s0",
        )

        selected = alt_set.select("action_1")
        assert selected.status == "resolved"

    def test_epistemic_world_elimination(self, blank_egi):
        """Epistemic: narrowing possible worlds."""
        alt_set = AlternativeSet(
            id="e1",
            context=blank_egi,
            alternatives=frozenset({"world_1", "world_2", "world_3", "world_4"}),
            kind="epistemic",
            emerged_at_state="s0",
        )

        narrowed = alt_set.narrow_to({"world_1", "world_2"})
        assert narrowed.status == "partial"

    def test_metacognitive_self_awareness(self, blank_egi):
        """Metacognitive: reflecting on possibilities."""
        alt_set = AlternativeSet(
            id="mc1",
            context=blank_egi,
            alternatives=frozenset({"think_a", "think_b", "think_c"}),
            kind="metacognitive",
            emerged_at_state="s0",
        )

        # Narrow to multiple possibilities (partial)
        narrowed = alt_set.narrow_to({"think_a", "think_b"})
        assert narrowed.status == "partial"


class TestBackwardCompatibilityAlias:
    """Test that Doubt alias works for backward compatibility."""

    def test_doubt_alias_exists(self):
        """Doubt alias should exist for backward compatibility."""
        from alternative_set import Doubt
        assert Doubt is AlternativeSet

    def test_doubt_construction_works(self, blank_egi):
        """Can construct using old Doubt name."""
        from alternative_set import Doubt
        doubt = Doubt(
            id="d0",
            context=blank_egi,
            alternatives=frozenset({"c1", "c2"}),
            emerged_at_state="s0",
        )
        assert doubt.id == "d0"
        assert isinstance(doubt, AlternativeSet)
