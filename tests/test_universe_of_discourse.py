"""
Tests for src/universe_of_discourse.py — the diachronic-process abstraction.

UoD is the central abstraction (per docs/UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md): a
single EGI is a synchronic snapshot, UoD is the evolving sequence of snapshots
with transformation history and layout deltas. These tests pin down:

  - construction (standalone vs historical, category semantics, backward-compat aliases)
  - state updates (cache invalidation, layout-delta passthrough)
  - promotion from standalone to historical (layout deltas survive)
  - history access surface (raises on standalone)
  - branching: applying two transformations from the same source state makes that
    state a branch point in the underlying history DAG
"""

from datetime import datetime
from pathlib import Path

import pytest

# Match the import pattern documented in CLAUDE.md
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egi_core_dau import create_empty_graph, create_vertex
from egi_transformation_history import EGITransformationHistory
from formal_transformation_rules import (
    AreaPolarity,
    TransformationContext,
    TransformationResult,
)
from universe_of_discourse import (
    EntityCategory,
    EntityMetadata,
    EntityType,
    GraphEntity,
    UniverseOfDiscourse,
    UoDCategory,
    UoDMetadata,
    UoDType,
)


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #


def _egi_with_one_vertex(label: str | None = None, is_generic: bool = True):
    egi = create_empty_graph()
    v = create_vertex(label=label, is_generic=is_generic)
    return egi.with_vertex(v), v


def _standalone_metadata(
    name: str = "Test UoD",
    category: UoDCategory = UoDCategory.LITERATURE_EXAMPLE,
) -> UoDMetadata:
    now = datetime.now()
    return UoDMetadata(
        uod_id=f"uod_{name.lower().replace(' ', '_')}",
        uod_type=UoDType.STANDALONE,
        name=name,
        description=f"Test UoD: {name}",
        category=category,
        created=now,
        last_modified=now,
    )


def _mock_result(new_egi) -> TransformationResult:
    return TransformationResult(
        success=True,
        result_egi=new_egi,
        error_message=None,
        changes_made={"test_marker": True},
    )


def _mock_context(source_egi) -> TransformationContext:
    return TransformationContext(
        source_egi=source_egi,
        target_area="sheet",
        selected_subgraph=frozenset(),
        area_polarity=AreaPolarity.POSITIVE,
        nesting_depth=0,
    )


# --------------------------------------------------------------------------- #
# Construction                                                                #
# --------------------------------------------------------------------------- #


class TestConstruction:
    def test_standalone_uod_has_no_history(self):
        egi, _ = _egi_with_one_vertex(label="Human", is_generic=False)
        uod = UniverseOfDiscourse(
            metadata=_standalone_metadata("Peirce Example"),
            current_egi=egi,
            history=None,
        )

        assert uod.is_standalone
        assert not uod.is_historical
        assert uod.is_static  # LITERATURE_EXAMPLE
        assert not uod.is_dynamic
        assert uod.history is None

    def test_active_inquiry_is_dynamic_not_static(self):
        egi, _ = _egi_with_one_vertex()
        uod = UniverseOfDiscourse(
            metadata=_standalone_metadata(
                "Active Inquiry", category=UoDCategory.ACTIVE_INQUIRY
            ),
            current_egi=egi,
            history=None,
        )

        assert uod.is_dynamic
        assert not uod.is_static
        # is_standalone refers to *history attachment*, not provenance
        assert uod.is_standalone

    def test_historical_type_with_history_object(self):
        egi, _ = _egi_with_one_vertex()
        history = EGITransformationHistory(egi, "start")
        metadata = _standalone_metadata("With History")
        metadata.uod_type = UoDType.HISTORICAL
        uod = UniverseOfDiscourse(
            metadata=metadata, current_egi=egi, history=history
        )

        assert uod.is_historical
        assert not uod.is_standalone

    def test_backward_compat_aliases(self):
        """Old names (EntityType, EntityCategory, EntityMetadata, GraphEntity)
        must remain importable and identical to the new names so that pre-rename
        callers (still present per CLAUDE.md migration note) keep working."""
        assert EntityType is UoDType
        assert EntityCategory is UoDCategory
        assert EntityMetadata is UoDMetadata
        assert GraphEntity is UniverseOfDiscourse

    def test_metadata_entity_aliases(self):
        """entity_id and entity_type aliases on UoDMetadata pass through."""
        m = _standalone_metadata("Alias Test")
        assert m.entity_id == m.uod_id
        assert m.entity_type == m.uod_type


# --------------------------------------------------------------------------- #
# Linear-form caching and invalidation                                        #
# --------------------------------------------------------------------------- #


class TestLinearFormCaching:
    def test_egif_is_cached_per_state(self):
        egi, _ = _egi_with_one_vertex()
        uod = UniverseOfDiscourse(
            metadata=_standalone_metadata(), current_egi=egi, history=None
        )

        first = uod.get_current_egif()
        # Same call returns the same cached object.
        assert uod.get_current_egif() is first

    def test_update_current_state_invalidates_caches(self):
        egi1, _ = _egi_with_one_vertex()
        uod = UniverseOfDiscourse(
            metadata=_standalone_metadata(), current_egi=egi1, history=None
        )
        before = uod.get_current_egif()

        # New EGI with one more vertex.
        egi2, _ = _egi_with_one_vertex()
        egi2 = uod.current_egi.with_vertex(create_vertex(is_generic=True))
        uod.update_current_state(egi2)

        after = uod.get_current_egif()
        # The string itself may or may not differ, but the cache must have been
        # cleared — so the returned object identity should not be the prior one.
        assert after is not before

    def test_update_current_state_preserves_layout_deltas_when_omitted(self):
        egi, v = _egi_with_one_vertex()
        deltas = {"vertex_positions": {v.id: [10, 20]}}
        uod = UniverseOfDiscourse(
            metadata=_standalone_metadata(),
            current_egi=egi,
            current_layout_deltas=deltas,
            history=None,
        )

        # Update EGI but not deltas.
        new_egi = egi.with_vertex(create_vertex(is_generic=True))
        uod.update_current_state(new_egi)

        assert uod.current_layout_deltas == deltas

    def test_update_current_state_overrides_layout_deltas_when_given(self):
        egi, _ = _egi_with_one_vertex()
        uod = UniverseOfDiscourse(
            metadata=_standalone_metadata(),
            current_egi=egi,
            current_layout_deltas={"a": 1},
            history=None,
        )
        new_egi = egi.with_vertex(create_vertex(is_generic=True))
        uod.update_current_state(new_egi, new_layout_deltas={"b": 2})

        assert uod.current_layout_deltas == {"b": 2}


# --------------------------------------------------------------------------- #
# Promotion to historical                                                     #
# --------------------------------------------------------------------------- #


class TestPromoteToHistorical:
    def test_promote_creates_history_with_initial_state(self):
        egi, _ = _egi_with_one_vertex()
        uod = UniverseOfDiscourse(
            metadata=_standalone_metadata(category=UoDCategory.THEOREM_PROOF),
            current_egi=egi,
            history=None,
        )

        uod.promote_to_historical(initial_description="initial")

        assert uod.is_historical
        assert not uod.is_standalone
        assert uod.history is not None
        assert len(uod.history.states) == 1
        assert uod.metadata.uod_type == UoDType.HISTORICAL
        assert uod.metadata.current_state_id == uod.history.current_state_id

    def test_promote_is_idempotent(self):
        egi, _ = _egi_with_one_vertex()
        uod = UniverseOfDiscourse(
            metadata=_standalone_metadata(category=UoDCategory.THEOREM_PROOF),
            current_egi=egi,
            history=None,
        )
        uod.promote_to_historical("first")
        history_obj = uod.history
        uod.promote_to_historical("second")
        # Second call is a no-op — same history object, no new state.
        assert uod.history is history_obj
        assert len(uod.history.states) == 1

    def test_promote_preserves_layout_deltas_in_initial_state(self):
        egi, v = _egi_with_one_vertex()
        deltas = {"vertex_positions": {v.id: [42, 99]}}
        uod = UniverseOfDiscourse(
            metadata=_standalone_metadata(category=UoDCategory.ACTIVE_INQUIRY),
            current_egi=egi,
            current_layout_deltas=deltas,
            history=None,
        )

        uod.promote_to_historical("with deltas")

        initial = uod.get_current_state()
        assert initial.diagram_metadata.get("layout_deltas") == deltas


# --------------------------------------------------------------------------- #
# Standalone UoDs reject history operations                                   #
# --------------------------------------------------------------------------- #


class TestStandaloneRejectsHistoryOps:
    @pytest.fixture
    def standalone(self) -> UniverseOfDiscourse:
        egi, _ = _egi_with_one_vertex()
        return UniverseOfDiscourse(
            metadata=_standalone_metadata(), current_egi=egi, history=None
        )

    def test_get_state_raises(self, standalone):
        with pytest.raises(ValueError, match="standalone"):
            standalone.get_state("any-id")

    def test_get_transformation_raises(self, standalone):
        with pytest.raises(ValueError, match="standalone"):
            standalone.get_transformation("any-id")

    def test_get_current_state_raises(self, standalone):
        with pytest.raises(ValueError, match="standalone"):
            standalone.get_current_state()

    def test_get_state_range_raises(self, standalone):
        with pytest.raises(ValueError, match="standalone"):
            standalone.get_state_range("a", "b")


# --------------------------------------------------------------------------- #
# Diachronic evolution and branching at the UoD level                         #
# --------------------------------------------------------------------------- #


class TestDiachronicEvolution:
    def _promoted_uod(self) -> UniverseOfDiscourse:
        egi, _ = _egi_with_one_vertex()
        uod = UniverseOfDiscourse(
            metadata=_standalone_metadata(category=UoDCategory.THEOREM_PROOF),
            current_egi=egi,
            history=None,
        )
        uod.promote_to_historical("initial")
        return uod

    def test_transformation_extends_history_linearly(self):
        uod = self._promoted_uod()
        initial_state_id = uod.history.current_state_id

        new_egi = uod.current_egi.with_vertex(create_vertex(is_generic=True))
        uod.history.add_transformation(
            "TestRule", _mock_context(uod.current_egi), _mock_result(new_egi)
        )

        assert len(uod.history.states) == 2
        assert len(uod.history.transformations) == 1
        assert uod.history.current_state_id != initial_state_id

    def test_two_transformations_from_same_state_create_branch_point(self):
        """Apply two distinct transformations from the same source state by
        rewinding `current_state_id` between calls. The shared source state
        must end up in `branch_points` and have two outgoing steps."""
        uod = self._promoted_uod()
        source_state_id = uod.history.current_state_id

        # First transformation
        egi_a = uod.current_egi.with_vertex(create_vertex(is_generic=True))
        uod.history.add_transformation(
            "RuleA", _mock_context(uod.current_egi), _mock_result(egi_a)
        )

        # Rewind to the source and apply a second, distinct transformation
        uod.history.current_state_id = source_state_id
        egi_b = uod.current_egi.with_vertex(create_vertex(is_generic=True))
        uod.history.add_transformation(
            "RuleB", _mock_context(uod.current_egi), _mock_result(egi_b)
        )

        assert source_state_id in uod.history.branch_points
        assert len(uod.history.state_to_outgoing_steps[source_state_id]) == 2
        assert len(uod.history.states) == 3  # initial + 2 children


# --------------------------------------------------------------------------- #
# Metadata serialization round-trip                                           #
# --------------------------------------------------------------------------- #


class TestMetadataRoundTrip:
    def test_to_dict_from_dict_is_identity_on_core_fields(self):
        m = _standalone_metadata("Round Trip", category=UoDCategory.EPG_SESSION)
        m.authors = ["alice", "bob"]
        m.tags = {"x", "y"}
        m.domain_contexts = {"logic"}
        m.source_citation = "Test 2026"

        restored = UoDMetadata.from_dict(m.to_dict())

        assert restored.uod_id == m.uod_id
        assert restored.uod_type == m.uod_type
        assert restored.name == m.name
        assert restored.category == m.category
        assert restored.authors == m.authors
        assert restored.tags == m.tags
        assert restored.domain_contexts == m.domain_contexts
        assert restored.source_citation == m.source_citation

    def test_from_dict_accepts_legacy_entity_field_names(self):
        m = _standalone_metadata("Legacy")
        legacy = m.to_dict()
        # Simulate older serializer that used entity_id/entity_type
        legacy["entity_id"] = legacy.pop("uod_id")
        legacy["entity_type"] = legacy.pop("uod_type")

        restored = UoDMetadata.from_dict(legacy)
        assert restored.uod_id == m.uod_id
        assert restored.uod_type == m.uod_type

    def test_from_dict_aliases_legacy_category_strings(self):
        """The category map in from_dict must coerce the documented legacy
        strings ('peirce', 'scholars', 'user_created') into their modern
        UoDCategory enum members."""
        m = _standalone_metadata("Legacy Cat")
        d = m.to_dict()
        d["category"] = "peirce"
        assert UoDMetadata.from_dict(d).category == UoDCategory.LITERATURE_EXAMPLE
        d["category"] = "user_created"
        assert UoDMetadata.from_dict(d).category == UoDCategory.ACTIVE_INQUIRY
