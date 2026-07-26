"""
Tests for AlternativeSet persistence in TomosService.

Tests the save_alternatives, load_alternatives, and related methods,
verifying:
- JSONL round-trip persistence
- Backward compatibility (no file created for empty alternatives)
- All AlternativeSet kinds serialize/deserialize correctly
- Atomic writes (no partial files on error)
- Proper error handling (corrupt JSON, missing UoD, etc.)
"""

import json
import sys
from pathlib import Path
from typing import Dict, FrozenSet

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from alternative_set import AlternativeSet
from egi_core_dau import RelationalGraphWithCuts
from egif_parser_dau import parse_egif
from tomos_service import TomosService
from universe_of_discourse import UniverseOfDiscourse, UoDMetadata, UoDType, UoDCategory
from datetime import datetime


TOMOS_ROOT = Path(__file__).parent.parent / "tomos"


@pytest.fixture(scope="module")
def tomos():
    """Fixture providing a TomosService instance."""
    return TomosService(TOMOS_ROOT)


# UoDs created by tests — clean them up after all tests run
TEST_UOD_IDS = set()


def register_test_uod(uod_id: str):
    """Register a test UoD for cleanup."""
    TEST_UOD_IDS.add(uod_id)


def cleanup_test_uods(tomos_service: TomosService):
    """Delete all registered test UoDs from the corpus."""
    import shutil

    for uod_id in TEST_UOD_IDS:
        entry = tomos_service.get_uod_metadata(uod_id)
        if entry:
            uod_path = tomos_service._entry_path(entry)
            if uod_path.exists():
                shutil.rmtree(uod_path)

        # Remove from index
        tomos_service._index.universes = [
            u for u in tomos_service._index.universes
            if u.get("uod_id") != uod_id
        ]

    # Save updated index
    tomos_service._save_index()


@pytest.fixture(scope="module", autouse=True)
def cleanup_after_all_tests(tomos):
    """Cleanup test UoDs after all tests run."""
    yield
    cleanup_test_uods(tomos)


@pytest.fixture
def sample_egi() -> RelationalGraphWithCuts:
    """Create a minimal EGI for testing."""
    return parse_egif("")


@pytest.fixture
def sample_alternatives(sample_egi) -> Dict[str, AlternativeSet]:
    """Create a set of sample alternatives for testing."""
    # Interrogative
    alt1 = AlternativeSet(
        id="a0",
        context=sample_egi,
        alternatives=frozenset({"h1", "h2", "h3"}),
        current_selection=frozenset(),
        kind="interrogative",
        emerged_at_state="s1",
        warrant=1.0,
        source="test",
    )

    # Hypothetical (narrowed)
    alt2 = AlternativeSet(
        id="a1",
        context=sample_egi,
        alternatives=frozenset({"t1", "t2"}),
        current_selection=frozenset({"t1"}),
        kind="hypothetical",
        emerged_at_state="s2",
        resolved_at_state="s4",
        selection_path=["s2", "s3", "s4"],
        warrant=0.8,
        source="test",
    )

    # Modal
    alt3 = AlternativeSet(
        id="a2",
        context=sample_egi,
        alternatives=frozenset({"f1", "f2", "f3"}),
        current_selection=frozenset({"f1", "f2"}),
        kind="modal",
        emerged_at_state="s1",
        warrant=0.6,
        source="test",
    )

    return {"a0": alt1, "a1": alt2, "a2": alt3}


@pytest.fixture
def sample_uod(sample_egi) -> UniverseOfDiscourse:
    """Create a sample UoD for testing."""
    metadata = UoDMetadata(
        uod_id="test_alternatives_uod",
        uod_type=UoDType.HISTORICAL,
        name="Test AlternativeSet Persistence",
        description="Testing save/load of alternatives",
        category=UoDCategory.ACTIVE_INQUIRY,
        created=datetime.now(),
        last_modified=datetime.now(),
        authors=["test"],
    )

    # Register this UoD for cleanup
    register_test_uod("test_alternatives_uod")

    return UniverseOfDiscourse(
        metadata=metadata,
        current_egi=sample_egi,
        current_layout_deltas=None,
    )


# =========================================================================
# Basic save/load tests
# =========================================================================


def test_save_and_load_alternatives(tomos, sample_uod, sample_alternatives):
    """Test basic save/load cycle for alternatives."""
    # Create the UoD first
    tomos.save_uod(sample_uod)

    # Save alternatives
    tomos.save_alternatives(sample_uod.uod_id, sample_alternatives)

    # Load alternatives back
    loaded = tomos.load_alternatives(sample_uod.uod_id)

    # Verify all alternatives were loaded
    assert len(loaded) == 3
    assert set(loaded.keys()) == {"a0", "a1", "a2"}

    # Verify each alternative matches
    for alt_id in sample_alternatives:
        loaded_alt = loaded[alt_id]
        original_alt = sample_alternatives[alt_id]

        assert loaded_alt.id == original_alt.id
        assert loaded_alt.kind == original_alt.kind
        assert loaded_alt.alternatives == original_alt.alternatives
        assert loaded_alt.current_selection == original_alt.current_selection
        assert loaded_alt.emerged_at_state == original_alt.emerged_at_state
        assert loaded_alt.resolved_at_state == original_alt.resolved_at_state
        assert loaded_alt.selection_path == original_alt.selection_path
        assert loaded_alt.warrant == original_alt.warrant
        assert loaded_alt.source == original_alt.source


def test_save_empty_alternatives_does_not_create_file(tomos, sample_uod):
    """Test that saving empty alternatives doesn't create a file."""
    tomos.save_uod(sample_uod)

    # Save empty alternatives
    tomos.save_alternatives(sample_uod.uod_id, {})

    # Verify file does not exist
    from tomos_service import TomosService
    inner_tomos = TomosService(TOMOS_ROOT)
    entry = inner_tomos.get_uod_metadata(sample_uod.uod_id)
    uod_path = inner_tomos._entry_path(entry)
    files = inner_tomos._get_uod_files(uod_path)

    assert not files["alternatives"].exists()


def test_load_alternatives_returns_empty_dict_when_file_missing(tomos, sample_uod):
    """Test backward compat: missing file returns empty dict."""
    tomos.save_uod(sample_uod)

    # Don't save alternatives (file won't exist)
    # Load alternatives should return empty dict, not raise
    loaded = tomos.load_alternatives(sample_uod.uod_id)

    assert isinstance(loaded, dict)
    assert len(loaded) == 0


# =========================================================================
# Round-trip tests
# =========================================================================


def test_round_trip_save_load_preserves_all_data(tomos, sample_uod, sample_alternatives):
    """Test that data survives multiple save/load cycles."""
    # Use unique UoD for this test
    unique_uod = UniverseOfDiscourse(
        metadata=UoDMetadata(
            uod_id="test_round_trip_unique",
            uod_type=UoDType.HISTORICAL,
            name="Test Round Trip",
            description="Testing multiple save/load cycles",
            category=UoDCategory.ACTIVE_INQUIRY,
            created=datetime.now(),
            last_modified=datetime.now(),
        ),
        current_egi=sample_uod.current_egi,
    )

    register_test_uod(unique_uod.uod_id)
    tomos.save_uod(unique_uod)
    tomos.save_alternatives(unique_uod.uod_id, sample_alternatives)

    # First load
    loaded1 = tomos.load_alternatives(unique_uod.uod_id)

    # Save again (what we just loaded)
    tomos.save_alternatives(unique_uod.uod_id, loaded1)

    # Load again
    loaded2 = tomos.load_alternatives(unique_uod.uod_id)

    # Compare by dicts (to avoid frozen EGI comparison issues)
    for alt_id in loaded1:
        d1 = loaded1[alt_id].to_dict()
        d2 = loaded2[alt_id].to_dict()
        assert d1 == d2


def test_round_trip_idempotence_via_dict_comparison(tomos, sample_uod, sample_alternatives):
    """Test that to_dict/from_dict round-trip is idempotent."""
    tomos.save_uod(sample_uod)

    # Save and load
    tomos.save_alternatives(sample_uod.uod_id, sample_alternatives)
    loaded = tomos.load_alternatives(sample_uod.uod_id)

    # Compare dicts
    for alt_id in sample_alternatives:
        orig_dict = sample_alternatives[alt_id].to_dict()
        loaded_dict = loaded[alt_id].to_dict()

        # Context EGIF is already round-tripped via the parser
        assert orig_dict["id"] == loaded_dict["id"]
        assert orig_dict["alternatives"] == loaded_dict["alternatives"]
        assert orig_dict["current_selection"] == loaded_dict["current_selection"]
        assert orig_dict["kind"] == loaded_dict["kind"]
        assert orig_dict["emerged_at_state"] == loaded_dict["emerged_at_state"]
        assert orig_dict["resolved_at_state"] == loaded_dict["resolved_at_state"]
        assert orig_dict["selection_path"] == loaded_dict["selection_path"]
        assert orig_dict["warrant"] == loaded_dict["warrant"]
        assert orig_dict["source"] == loaded_dict["source"]


# =========================================================================
# JSONL format tests
# =========================================================================


def test_alternatives_are_stored_in_jsonl_format(tomos, sample_uod, sample_alternatives):
    """Test that alternatives.jsonl is valid JSONL (one JSON per line)."""
    tomos.save_uod(sample_uod)
    tomos.save_alternatives(sample_uod.uod_id, sample_alternatives)

    from tomos_service import TomosService
    inner_tomos = TomosService(TOMOS_ROOT)
    entry = inner_tomos.get_uod_metadata(sample_uod.uod_id)
    uod_path = inner_tomos._entry_path(entry)
    files = inner_tomos._get_uod_files(uod_path)
    alternatives_path = files["alternatives"]

    # Read and verify JSONL format
    assert alternatives_path.exists()

    with open(alternatives_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Should have one line per alternative
    assert len(lines) == 3

    # Each line should be valid JSON
    for line in lines:
        data = json.loads(line.strip())
        assert "id" in data
        assert "kind" in data


def test_jsonl_lines_are_ordered_by_id(tomos, sample_uod, sample_alternatives):
    """Test that JSONL lines are written in sorted order by ID."""
    tomos.save_uod(sample_uod)
    tomos.save_alternatives(sample_uod.uod_id, sample_alternatives)

    from tomos_service import TomosService
    inner_tomos = TomosService(TOMOS_ROOT)
    entry = inner_tomos.get_uod_metadata(sample_uod.uod_id)
    uod_path = inner_tomos._entry_path(entry)
    files = inner_tomos._get_uod_files(uod_path)
    alternatives_path = files["alternatives"]

    with open(alternatives_path, 'r', encoding='utf-8') as f:
        ids = [json.loads(line.strip())["id"] for line in f]

    # Should be in sorted order
    assert ids == sorted(ids)


# =========================================================================
# Error handling tests
# =========================================================================


def test_load_alternatives_raises_on_corrupt_json(tomos, sample_uod):
    """Test that corrupt JSON raises ValueError with helpful message."""
    # Use unique UoD for this test
    unique_uod = UniverseOfDiscourse(
        metadata=UoDMetadata(
            uod_id="test_corrupt_json_unique",
            uod_type=UoDType.HISTORICAL,
            name="Test Corrupt JSON",
            description="Testing corrupt JSON handling",
            category=UoDCategory.ACTIVE_INQUIRY,
            created=datetime.now(),
            last_modified=datetime.now(),
        ),
        current_egi=sample_uod.current_egi,
    )

    register_test_uod(unique_uod.uod_id)
    tomos.save_uod(unique_uod)

    from tomos_service import TomosService
    inner_tomos = TomosService(TOMOS_ROOT)
    entry = inner_tomos.get_uod_metadata(unique_uod.uod_id)
    uod_path = inner_tomos._entry_path(entry)
    files = inner_tomos._get_uod_files(uod_path)
    alternatives_path = files["alternatives"]

    # Write corrupt JSON (missing commas/unclosed braces)
    with open(alternatives_path, 'w', encoding='utf-8') as f:
        f.write('{"id": "a0", "kind": "interrogative"}\n')
        f.write('{invalid json on line 2}\n')  # Corrupt line

    # Loading should raise ValueError
    with pytest.raises(ValueError, match="Malformed JSON|Failed to deserialize"):
        tomos.load_alternatives(unique_uod.uod_id)


def test_save_alternatives_raises_on_missing_uod(tomos):
    """Test that save_alternatives raises KeyError for missing UoD."""
    with pytest.raises(KeyError, match="not found"):
        tomos.save_alternatives("nonexistent_uod", {})


def test_load_alternatives_raises_on_missing_uod(tomos):
    """Test that load_alternatives raises KeyError for missing UoD."""
    with pytest.raises(KeyError, match="not found"):
        tomos.load_alternatives("nonexistent_uod")


# =========================================================================
# AlternativeSet kind tests (all 7 kinds)
# =========================================================================


@pytest.mark.parametrize(
    "kind",
    [
        "interrogative",
        "hypothetical",
        "modal",
        "counterfactual",
        "agentive",
        "epistemic",
        "metacognitive",
    ],
)
def test_all_alternative_set_kinds_persist(tomos, sample_egi, sample_uod, kind):
    """Test that all AlternativeSet kinds serialize/deserialize correctly."""
    tomos.save_uod(sample_uod)

    # Create alternatives with this kind
    alternatives = {
        f"alt_{kind}": AlternativeSet(
            id=f"alt_{kind}",
            context=sample_egi,
            alternatives=frozenset({"opt1", "opt2", "opt3"}),
            current_selection=frozenset({"opt1"}),
            kind=kind,  # type: ignore
            emerged_at_state="s1",
            warrant=0.9,
            source="test",
        )
    }

    # Save and load
    tomos.save_alternatives(sample_uod.uod_id, alternatives)
    loaded = tomos.load_alternatives(sample_uod.uod_id)

    # Verify kind is preserved
    assert loaded[f"alt_{kind}"].kind == kind


# =========================================================================
# load_uod_with_alternatives tests
# =========================================================================


def test_load_uod_with_alternatives_combines_uod_and_alternatives(
    tomos, sample_uod, sample_alternatives
):
    """Test that load_uod_with_alternatives populates all_alternatives."""
    tomos.save_uod(sample_uod)
    tomos.save_alternatives(sample_uod.uod_id, sample_alternatives)

    # Load via convenience method
    loaded_uod = tomos.load_uod_with_alternatives(sample_uod.uod_id)

    assert loaded_uod is not None
    assert len(loaded_uod.all_alternatives) == 3
    assert set(loaded_uod.all_alternatives.keys()) == {"a0", "a1", "a2"}


def test_load_uod_with_alternatives_returns_none_for_missing_uod(tomos):
    """Test that load_uod_with_alternatives returns None for missing UoD."""
    loaded = tomos.load_uod_with_alternatives("nonexistent_uod")
    assert loaded is None


def test_load_uod_with_alternatives_returns_empty_alternatives_for_missing_file(tomos):
    """Test backward compat: missing alternatives.jsonl gives empty all_alternatives."""
    # Use unique UoD for this test
    unique_uod = UniverseOfDiscourse(
        metadata=UoDMetadata(
            uod_id="test_missing_alts_file_unique",
            uod_type=UoDType.HISTORICAL,
            name="Test Missing Alts File",
            description="Testing missing alternatives.jsonl",
            category=UoDCategory.ACTIVE_INQUIRY,
            created=datetime.now(),
            last_modified=datetime.now(),
        ),
        current_egi=parse_egif(""),
    )

    register_test_uod(unique_uod.uod_id)
    tomos.save_uod(unique_uod)
    # Don't save alternatives

    loaded_uod = tomos.load_uod_with_alternatives(unique_uod.uod_id)

    assert loaded_uod is not None
    assert loaded_uod.all_alternatives == {}


# =========================================================================
# save_uod_with_alternatives tests
# =========================================================================


def test_save_uod_with_alternatives_saves_both(tomos, sample_uod, sample_alternatives):
    """Test that save_uod_with_alternatives persists both UoD and alternatives."""
    # Populate UoD with alternatives
    populated_uod = UniverseOfDiscourse(
        metadata=sample_uod.metadata,
        current_egi=sample_uod.current_egi,
        current_layout_deltas=sample_uod.current_layout_deltas,
        alternatives_by_state=sample_uod.alternatives_by_state,
        all_alternatives=sample_alternatives,
    )

    # Save via convenience method
    tomos.save_uod_with_alternatives(populated_uod)

    # Verify both UoD and alternatives were persisted
    loaded_uod = tomos.load_uod(sample_uod.uod_id)
    assert loaded_uod is not None

    loaded_alts = tomos.load_alternatives(sample_uod.uod_id)
    assert len(loaded_alts) == 3


# =========================================================================
# Lifecycle tracking tests (emerged_at_state, resolved_at_state, etc.)
# =========================================================================


def test_alternative_lifecycle_fields_persist(tomos, sample_egi, sample_uod):
    """Test that lifecycle fields (emerged_at_state, etc.) survive round-trip."""
    tomos.save_uod(sample_uod)

    alt = AlternativeSet(
        id="lifecycle_test",
        context=sample_egi,
        alternatives=frozenset({"a", "b", "c"}),
        current_selection=frozenset({"a"}),
        kind="interrogative",
        emerged_at_state="s1",
        resolved_at_state="s5",
        selection_path=["s1", "s2", "s3", "s4", "s5"],
        warrant=0.85,
        source="lifecycle_test",
    )

    alternatives = {"lifecycle_test": alt}

    tomos.save_alternatives(sample_uod.uod_id, alternatives)
    loaded = tomos.load_alternatives(sample_uod.uod_id)

    loaded_alt = loaded["lifecycle_test"]

    assert loaded_alt.emerged_at_state == "s1"
    assert loaded_alt.resolved_at_state == "s5"
    assert loaded_alt.selection_path == ["s1", "s2", "s3", "s4", "s5"]


# =========================================================================
# Status encoding tests (unresolved, partial, resolved)
# =========================================================================


def test_status_unresolved_persists(tomos, sample_egi, sample_uod):
    """Test that unresolved status (empty current_selection) is preserved."""
    tomos.save_uod(sample_uod)

    alt = AlternativeSet(
        id="unresolved_test",
        context=sample_egi,
        alternatives=frozenset({"a", "b", "c"}),
        current_selection=frozenset(),  # Unresolved
        kind="interrogative",
        emerged_at_state="s1",
    )

    tomos.save_alternatives(sample_uod.uod_id, {"unresolved_test": alt})
    loaded = tomos.load_alternatives(sample_uod.uod_id)

    assert loaded["unresolved_test"].status == "unresolved"
    assert len(loaded["unresolved_test"].current_selection) == 0


def test_status_partial_persists(tomos, sample_egi, sample_uod):
    """Test that partial status is preserved."""
    tomos.save_uod(sample_uod)

    alt = AlternativeSet(
        id="partial_test",
        context=sample_egi,
        alternatives=frozenset({"a", "b", "c"}),
        current_selection=frozenset({"a", "b"}),  # Partial (narrowed but not single)
        kind="interrogative",
        emerged_at_state="s1",
    )

    tomos.save_alternatives(sample_uod.uod_id, {"partial_test": alt})
    loaded = tomos.load_alternatives(sample_uod.uod_id)

    assert loaded["partial_test"].status == "partial"
    assert len(loaded["partial_test"].current_selection) == 2


def test_status_resolved_persists(tomos, sample_egi, sample_uod):
    """Test that resolved status (single element) is preserved."""
    tomos.save_uod(sample_uod)

    alt = AlternativeSet(
        id="resolved_test",
        context=sample_egi,
        alternatives=frozenset({"a", "b", "c"}),
        current_selection=frozenset({"a"}),  # Resolved
        kind="interrogative",
        emerged_at_state="s1",
        resolved_at_state="s2",
    )

    tomos.save_alternatives(sample_uod.uod_id, {"resolved_test": alt})
    loaded = tomos.load_alternatives(sample_uod.uod_id)

    assert loaded["resolved_test"].status == "resolved"
    assert len(loaded["resolved_test"].current_selection) == 1


# =========================================================================
# Serialization edge cases
# =========================================================================


def test_frozenset_alternatives_round_trips(tomos, sample_egi, sample_uod):
    """Test that frozenset alternatives survive JSON round-trip."""
    tomos.save_uod(sample_uod)

    alt = AlternativeSet(
        id="frozenset_test",
        context=sample_egi,
        alternatives=frozenset({"opt_1", "opt_2", "opt_3"}),
        current_selection=frozenset({"opt_1", "opt_2"}),
        kind="interrogative",
        emerged_at_state="s1",
    )

    tomos.save_alternatives(sample_uod.uod_id, {"frozenset_test": alt})
    loaded = tomos.load_alternatives(sample_uod.uod_id)

    # Frozensets come back as frozensets
    assert isinstance(loaded["frozenset_test"].alternatives, frozenset)
    assert isinstance(loaded["frozenset_test"].current_selection, frozenset)
    assert loaded["frozenset_test"].alternatives == frozenset(
        {"opt_1", "opt_2", "opt_3"}
    )
    assert loaded["frozenset_test"].current_selection == frozenset(
        {"opt_1", "opt_2"}
    )


def test_empty_selection_round_trips(tomos, sample_egi, sample_uod):
    """Test that empty current_selection round-trips correctly."""
    tomos.save_uod(sample_uod)

    alt = AlternativeSet(
        id="empty_selection_test",
        context=sample_egi,
        alternatives=frozenset({"a", "b"}),
        current_selection=frozenset(),
        kind="interrogative",
        emerged_at_state="s1",
    )

    tomos.save_alternatives(sample_uod.uod_id, {"empty_selection_test": alt})
    loaded = tomos.load_alternatives(sample_uod.uod_id)

    assert loaded["empty_selection_test"].current_selection == frozenset()


def test_egif_context_round_trips(tomos, sample_egi, sample_uod):
    """Test that context EGI round-trips correctly via EGIF."""
    tomos.save_uod(sample_uod)

    # Context is the sample_egi
    alt = AlternativeSet(
        id="egif_test",
        context=sample_egi,
        alternatives=frozenset({"h1", "h2"}),
        current_selection=frozenset(),
        kind="interrogative",
        emerged_at_state="s1",
    )

    tomos.save_alternatives(sample_uod.uod_id, {"egif_test": alt})
    loaded = tomos.load_alternatives(sample_uod.uod_id)

    # The loaded context should be equivalent to the original
    loaded_alt = loaded["egif_test"]
    assert isinstance(loaded_alt.context, RelationalGraphWithCuts)


# =========================================================================
# Corpus-wide backward compatibility tests
# =========================================================================


def test_existing_uods_without_alternatives_files_load_cleanly(tomos):
    """Test that existing corpus UoDs (without alternatives.jsonl) load fine."""
    # Get a real UoD from the corpus that doesn't have alternatives
    uod_list = tomos.list_uods()
    if not uod_list:
        pytest.skip("No UoDs in test corpus")

    uod_id = uod_list[0]["uod_id"]

    # load_alternatives should return empty dict
    loaded_alts = tomos.load_alternatives(uod_id)
    assert isinstance(loaded_alts, dict)
    assert len(loaded_alts) == 0

    # load_uod_with_alternatives should work fine too
    loaded_uod = tomos.load_uod_with_alternatives(uod_id)
    assert loaded_uod is not None
    assert loaded_uod.all_alternatives == {}


# =========================================================================
# Metadata and warrant tests
# =========================================================================


def test_warrant_values_persist(tomos, sample_egi):
    """Test that warrant values (0.0-1.0) are preserved."""
    # Use unique UoD for this test
    unique_uod = UniverseOfDiscourse(
        metadata=UoDMetadata(
            uod_id="test_warrant_values_unique",
            uod_type=UoDType.HISTORICAL,
            name="Test Warrant Values",
            description="Testing warrant persistence",
            category=UoDCategory.ACTIVE_INQUIRY,
            created=datetime.now(),
            last_modified=datetime.now(),
        ),
        current_egi=sample_egi,
    )

    register_test_uod(unique_uod.uod_id)
    tomos.save_uod(unique_uod)

    warrant_values = [0.0, 0.25, 0.5, 0.75, 1.0]
    alternatives = {}

    for i, warrant in enumerate(warrant_values):
        alt = AlternativeSet(
            id=f"warrant_{i}",
            context=sample_egi,
            alternatives=frozenset({"a", "b"}),
            current_selection=frozenset(),
            kind="interrogative",
            emerged_at_state="s1",
            warrant=warrant,
        )
        alternatives[f"warrant_{i}"] = alt

    # Save all alternatives at once
    tomos.save_alternatives(unique_uod.uod_id, alternatives)

    # Load and verify
    all_alts = tomos.load_alternatives(unique_uod.uod_id)

    for i, warrant in enumerate(warrant_values):
        assert all_alts[f"warrant_{i}"].warrant == warrant


def test_source_field_persists(tomos, sample_egi):
    """Test that source field is preserved."""
    # Use unique UoD for this test
    unique_uod = UniverseOfDiscourse(
        metadata=UoDMetadata(
            uod_id="test_source_field_unique",
            uod_type=UoDType.HISTORICAL,
            name="Test Source Field",
            description="Testing source field persistence",
            category=UoDCategory.ACTIVE_INQUIRY,
            created=datetime.now(),
            last_modified=datetime.now(),
        ),
        current_egi=sample_egi,
    )

    register_test_uod(unique_uod.uod_id)
    tomos.save_uod(unique_uod)

    sources = ["unknown_verdict", "thin_spot", "oracle", "test_source"]
    alternatives = {}

    for source in sources:
        alt = AlternativeSet(
            id=f"source_{source}",
            context=sample_egi,
            alternatives=frozenset({"a", "b"}),
            current_selection=frozenset(),
            kind="interrogative",
            emerged_at_state="s1",
            source=source,
        )
        alternatives[f"source_{source}"] = alt

    # Save all alternatives at once
    tomos.save_alternatives(unique_uod.uod_id, alternatives)

    # Load and verify
    all_alts = tomos.load_alternatives(unique_uod.uod_id)

    for source in sources:
        assert all_alts[f"source_{source}"].source == source
