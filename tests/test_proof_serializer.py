"""
Tests for ProofSerializer
=========================

Covers:
- to_json: schema structure, required fields, EGIF inclusion
- to_text: format, step labels, EGIF per step
- from_json: round-trip fidelity (state count, rule names, EGIFs, step numbers)
- Multi-step histories and annotated steps
- Single-state (trivial) history
- Branch-point histories (DAG with two outgoing paths from one state)
- Error cases: malformed JSON, missing EGIF field
"""

import json
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from egi_transformation_history import EGITransformationHistory
from egif_generator_dau import generate_egif
from egif_parser_dau import parse_egif
from formal_transformation_rules import (
    AreaPolarity,
    DoubleCutErasureRule,
    DoubleCutInsertionRule,
    TransformationContext,
)
from proof_serializer import ProofSerializer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _dc_plus_ctx(egi):
    """Return a TransformationContext suitable for DC+ on the sheet."""
    return TransformationContext(
        source_egi=egi,
        target_area=egi.sheet,
        selected_subgraph=frozenset(),
        area_polarity=AreaPolarity.POSITIVE,
        nesting_depth=0,
    )


def _apply_dc_plus(history):
    """Apply one DC+ step to the current state in *history* and return the step ID."""
    egi = history.get_current_state().egi
    ctx = _dc_plus_ctx(egi)
    result = DoubleCutInsertionRule().apply_transformation(ctx)
    assert result.success, "DC+ must succeed in test fixture"
    return history.add_transformation("DC+", ctx, result)


def _make_linear_history(n_steps=2, initial_egif="*x (Human x)"):
    """Create a history with *n_steps* consecutive DC+ applications."""
    egi = parse_egif(initial_egif)
    h = EGITransformationHistory(egi, "Initial state")
    for _ in range(n_steps):
        _apply_dc_plus(h)
    return h


def _make_annotated_history():
    """Create a 3-step history with user annotations on each step."""
    egi = parse_egif("*x (Human x)")
    h = EGITransformationHistory(egi, "Premise")
    for i, label in enumerate(["First double cut", "Second double cut", "Third double cut"]):
        current_egi = h.get_current_state().egi
        ctx = _dc_plus_ctx(current_egi)
        result = DoubleCutInsertionRule().apply_transformation(ctx)
        h.add_transformation("DC+", ctx, result, user_annotation=label)
    return h


def _make_branching_history():
    """
    Create a history with a branch point:
      S0 -DC+-> S1 -DC+-> S2   (main path)
                 +--DC+-> S3   (alternative)
    """
    egi = parse_egif("*x (Human x)")
    h = EGITransformationHistory(egi, "Root")

    # S0 → S1
    _apply_dc_plus(h)
    branch_point_id = h.current_state_id

    # S1 → S2 (main)
    _apply_dc_plus(h)

    # Branch back to S1, add S3
    h.create_branch_from_state(branch_point_id, description="Alt branch")
    _apply_dc_plus(h)

    return h, branch_point_id


# ---------------------------------------------------------------------------
# to_json — schema and content
# ---------------------------------------------------------------------------


class TestToJson:
    def test_returns_valid_json_string(self):
        h = _make_linear_history(1)
        s = ProofSerializer.to_json(h)
        # Must be parseable JSON
        data = json.loads(s)
        assert isinstance(data, dict)

    def test_top_level_fields_present(self):
        h = _make_linear_history(1)
        data = json.loads(ProofSerializer.to_json(h))
        for field in (
            "schema_version",
            "history_id",
            "created_timestamp",
            "current_state_id",
            "root_state_id",
            "state_sequence",
            "states",
            "transformations",
        ):
            assert field in data, f"Missing top-level field: {field!r}"

    def test_schema_version_is_1_0(self):
        h = _make_linear_history(1)
        data = json.loads(ProofSerializer.to_json(h))
        assert data["schema_version"] == "1.0"

    def test_state_count_matches(self):
        h = _make_linear_history(3)
        data = json.loads(ProofSerializer.to_json(h))
        assert len(data["states"]) == 4  # root + 3 steps

    def test_transformation_count_matches(self):
        h = _make_linear_history(2)
        data = json.loads(ProofSerializer.to_json(h))
        assert len(data["transformations"]) == 2

    def test_every_state_has_egif_field(self):
        h = _make_linear_history(2)
        data = json.loads(ProofSerializer.to_json(h))
        for sid, sdata in data["states"].items():
            assert "egif" in sdata, f"State {sid} missing 'egif' field"
            assert isinstance(sdata["egif"], str)
            assert len(sdata["egif"]) > 0

    def test_egif_values_are_parseable(self):
        h = _make_linear_history(2)
        data = json.loads(ProofSerializer.to_json(h))
        for sid, sdata in data["states"].items():
            egi = parse_egif(sdata["egif"])  # Must not raise
            assert egi is not None

    def test_transformation_rule_name_preserved(self):
        h = _make_linear_history(2)
        data = json.loads(ProofSerializer.to_json(h))
        for tid, tdata in data["transformations"].items():
            assert tdata["rule_name"] == "DC+"

    def test_user_annotations_preserved(self):
        h = _make_annotated_history()
        data = json.loads(ProofSerializer.to_json(h))
        annotations = {
            tdata["user_annotation"]
            for tdata in data["transformations"].values()
            if tdata.get("user_annotation")
        }
        assert "First double cut" in annotations
        assert "Second double cut" in annotations

    def test_state_sequence_length(self):
        h = _make_linear_history(3)
        data = json.loads(ProofSerializer.to_json(h))
        assert len(data["state_sequence"]) == 4  # root + 3

    def test_root_state_in_state_sequence(self):
        h = _make_linear_history(2)
        data = json.loads(ProofSerializer.to_json(h))
        assert data["root_state_id"] in data["state_sequence"]

    def test_current_state_in_state_sequence(self):
        h = _make_linear_history(2)
        data = json.loads(ProofSerializer.to_json(h))
        assert data["current_state_id"] in data["state_sequence"]

    def test_indent_parameter_respected(self):
        h = _make_linear_history(1)
        s4 = ProofSerializer.to_json(h, indent=4)
        s2 = ProofSerializer.to_json(h, indent=2)
        # Both are valid JSON with same content
        assert json.loads(s4) == json.loads(s2)
        # 4-space indent produces a longer string
        assert len(s4) > len(s2)

    def test_single_state_history(self):
        egi = parse_egif("*x (Human x)")
        h = EGITransformationHistory(egi, "Only state")
        data = json.loads(ProofSerializer.to_json(h))
        assert len(data["states"]) == 1
        assert len(data["transformations"]) == 0


# ---------------------------------------------------------------------------
# to_text — human-readable format
# ---------------------------------------------------------------------------


class TestToText:
    def test_starts_with_proof_header(self):
        h = _make_linear_history(1)
        text = ProofSerializer.to_text(h)
        assert text.startswith("=== Proof ===")

    def test_step_count_in_output(self):
        h = _make_linear_history(3)
        text = ProofSerializer.to_text(h)
        # Steps 0..3
        for i in range(4):
            assert f"Step {i}" in text

    def test_initial_state_label(self):
        h = _make_linear_history(1)
        text = ProofSerializer.to_text(h)
        assert "Initial state" in text

    def test_rule_name_appears_in_output(self):
        h = _make_linear_history(2)
        text = ProofSerializer.to_text(h)
        assert "DC+" in text

    def test_egif_appears_in_each_step(self):
        h = _make_linear_history(2)
        text = ProofSerializer.to_text(h)
        # Every state's EGIF should appear somewhere in the text
        for sid, state in h.states.items():
            egif = generate_egif(state.egi)
            assert egif in text, f"EGIF {egif!r} missing from proof text"

    def test_single_state_text(self):
        egi = parse_egif("*x (Human x)")
        h = EGITransformationHistory(egi, "Only state")
        text = ProofSerializer.to_text(h)
        assert "Step 0" in text
        assert "Initial state" in text


# ---------------------------------------------------------------------------
# from_json — round-trip fidelity
# ---------------------------------------------------------------------------


class TestFromJson:
    def test_round_trip_state_count(self):
        h = _make_linear_history(3)
        restored = ProofSerializer.from_json(ProofSerializer.to_json(h))
        assert len(restored.states) == len(h.states)

    def test_round_trip_transformation_count(self):
        h = _make_linear_history(3)
        restored = ProofSerializer.from_json(ProofSerializer.to_json(h))
        applied_orig = sum(
            1 for t in h.transformations.values() if t.status.value == "applied"
        )
        applied_rest = sum(
            1 for t in restored.transformations.values() if t.status.value == "applied"
        )
        assert applied_rest == applied_orig

    def test_round_trip_rule_names(self):
        h = _make_linear_history(2)
        restored = ProofSerializer.from_json(ProofSerializer.to_json(h))
        orig_rules = sorted(t.rule_name for t in h.transformations.values())
        rest_rules = sorted(t.rule_name for t in restored.transformations.values())
        assert rest_rules == orig_rules

    def test_round_trip_egif_content(self):
        """Each restored state's EGIF must match the original's EGIF."""
        h = _make_linear_history(2)
        data = json.loads(ProofSerializer.to_json(h))
        restored = ProofSerializer.from_json(ProofSerializer.to_json(h))

        # Compare EGIFs from original JSON (canonical reference)
        original_egifs = sorted(s["egif"] for s in data["states"].values())
        restored_egifs = sorted(
            generate_egif(s.egi) for s in restored.states.values()
        )
        assert restored_egifs == original_egifs

    def test_round_trip_step_numbers(self):
        h = _make_linear_history(3)
        restored = ProofSerializer.from_json(ProofSerializer.to_json(h))
        orig_steps = sorted(s.step_number for s in h.states.values())
        rest_steps = sorted(s.step_number for s in restored.states.values())
        assert rest_steps == orig_steps

    def test_round_trip_history_id_is_new(self):
        """Restored history gets a fresh UUID (it is a new history object)."""
        h = _make_linear_history(2)
        restored = ProofSerializer.from_json(ProofSerializer.to_json(h))
        # History IDs should differ since we're constructing a new history
        assert restored.history_id != h.history_id

    def test_round_trip_via_text_then_json(self):
        """to_text + to_json on same history must both succeed without error."""
        h = _make_linear_history(2)
        text = ProofSerializer.to_text(h)
        json_str = ProofSerializer.to_json(h)
        assert "DC+" in text
        assert "DC+" in json_str

    def test_single_state_round_trip(self):
        egi = parse_egif("*x (Human x)")
        h = EGITransformationHistory(egi, "Trivial proof")
        restored = ProofSerializer.from_json(ProofSerializer.to_json(h))
        assert len(restored.states) == 1
        assert len(restored.transformations) == 0

    def test_invalid_json_raises(self):
        with pytest.raises(Exception):
            ProofSerializer.from_json("not json at all {{{")

    def test_missing_egif_field_raises(self):
        h = _make_linear_history(1)
        data = json.loads(ProofSerializer.to_json(h))
        # Remove EGIF from one state
        first_sid = list(data["states"].keys())[0]
        del data["states"][first_sid]["egif"]
        with pytest.raises(ValueError, match="missing 'egif' field"):
            ProofSerializer.from_json(json.dumps(data))

    def test_unparseable_egif_raises(self):
        h = _make_linear_history(1)
        data = json.loads(ProofSerializer.to_json(h))
        first_sid = list(data["states"].keys())[0]
        data["states"][first_sid]["egif"] = "NOT VALID EGIF !!!"
        with pytest.raises((ValueError, Exception)):
            ProofSerializer.from_json(json.dumps(data))


# ---------------------------------------------------------------------------
# Branching history
# ---------------------------------------------------------------------------


class TestBranchingHistory:
    def test_branch_point_serialized(self):
        h, bp_id = _make_branching_history()
        data = json.loads(ProofSerializer.to_json(h))
        assert len(data["branch_points"]) >= 1

    def test_all_states_serialized_in_dag(self):
        h, _ = _make_branching_history()
        data = json.loads(ProofSerializer.to_json(h))
        # At minimum: root + S1 + S2 + S3
        assert len(data["states"]) >= 4

    def test_text_output_covers_main_path(self):
        h, _ = _make_branching_history()
        text = ProofSerializer.to_text(h)
        # to_text follows the main path to current_state_id
        assert "Step 0" in text
        assert "DC+" in text
