"""
Tests for src/egi_transformation_history.py — the DAG-based proof history.

The history is the diachronic spine of a UoD: every successful rule application
adds a state node and a transformation edge to a DAG rooted at the initial
state. These tests pin down:

  - initial state structure (root, indices, single state, no transformations)
  - linear sequencing (state_to_incoming/outgoing edges consistent)
  - failed transformations recorded but do not advance current state
  - branching: two outgoing edges from the same source state mark that state
    as a branch_point; both children are reachable from root
  - get_transformation_sequence / get_state navigation across branches
  - rollback_to_state semantics (rejects forward rollback)
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from egi_core_dau import (
    RelationalGraphWithCuts,
    create_empty_graph,
    create_vertex,
)
from egi_transformation_history import (
    EGITransformationHistory,
    HistoryBranchType,
    StateSnapshot,
    TransformationStatus,
    TransformationStep,
)
from formal_transformation_rules import (
    AreaPolarity,
    TransformationContext,
    TransformationResult,
)


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #


def _egi(n: int = 1) -> RelationalGraphWithCuts:
    """An EGI with n generic vertices."""
    egi = create_empty_graph()
    for _ in range(n):
        egi = egi.with_vertex(create_vertex(is_generic=True))
    return egi


def _context(source: RelationalGraphWithCuts) -> TransformationContext:
    return TransformationContext(
        source_egi=source,
        target_area="sheet",
        selected_subgraph=frozenset(),
        area_polarity=AreaPolarity.POSITIVE,
        nesting_depth=0,
    )


def _result(new_egi: RelationalGraphWithCuts, *, success: bool = True) -> TransformationResult:
    return TransformationResult(
        success=success,
        result_egi=new_egi if success else None,
        error_message=None if success else "mock failure",
        changes_made={"mock": True},
    )


def _apply(history: EGITransformationHistory, rule_name: str) -> str:
    """Apply a single mock transformation that adds one vertex. Returns step_id."""
    new_egi = history.get_current_state().egi.with_vertex(
        create_vertex(is_generic=True)
    )
    return history.add_transformation(
        rule_name, _context(history.get_current_state().egi), _result(new_egi)
    )


# --------------------------------------------------------------------------- #
# Initial state                                                               #
# --------------------------------------------------------------------------- #


class TestInitialState:
    def test_history_starts_with_single_root_state(self):
        h = EGITransformationHistory(_egi(), "start")

        assert len(h.states) == 1
        assert len(h.transformations) == 0
        assert h.root_state_id == h.current_state_id
        assert h.root_state_id is not None

    def test_initial_indices_are_consistent(self):
        h = EGITransformationHistory(_egi(), "start")
        root = h.current_state_id

        assert h.state_to_incoming_step[root] is None
        assert h.state_to_outgoing_steps[root] == []
        assert h.state_sequence == [root]
        assert h.step_sequence == []
        assert h.branch_points == set()

    def test_initial_state_metadata_flags_initial(self):
        h = EGITransformationHistory(_egi(), "start")
        initial: StateSnapshot = h.get_current_state()

        assert initial.step_number == 0
        assert initial.description == "start"
        assert initial.metadata.get("is_initial") is True

    def test_main_branch_is_registered(self):
        h = EGITransformationHistory(_egi(), "start")

        assert len(h.branches) == 1
        main_branch = h.branches[h.current_branch_id]
        assert main_branch.branch_type == HistoryBranchType.LINEAR
        assert main_branch.parent_state_id == h.root_state_id
        assert main_branch.metadata.get("is_main") is True


# --------------------------------------------------------------------------- #
# Linear sequencing                                                           #
# --------------------------------------------------------------------------- #


class TestLinearSequencing:
    def test_single_transformation_advances_current_state(self):
        h = EGITransformationHistory(_egi(), "start")
        root = h.current_state_id

        step_id = _apply(h, "Rule1")

        assert len(h.states) == 2
        assert len(h.transformations) == 1
        assert h.current_state_id != root
        # incoming step on the new state is the step we just added
        assert h.state_to_incoming_step[h.current_state_id] == step_id
        # outgoing from root contains exactly the step
        assert h.state_to_outgoing_steps[root] == [step_id]
        # the step ended successfully
        assert h.transformations[step_id].status == TransformationStatus.APPLIED

    def test_three_linear_transformations_have_no_branch_points(self):
        h = EGITransformationHistory(_egi(), "start")
        for i in range(3):
            _apply(h, f"Rule{i}")

        assert len(h.states) == 4
        assert len(h.transformations) == 3
        assert h.branch_points == set()
        # state_sequence preserves linear order
        assert len(h.state_sequence) == 4
        # step_number advances strictly by 1 along the chain
        chain = [h.states[sid].step_number for sid in h.state_sequence]
        assert chain == [0, 1, 2, 3]


# --------------------------------------------------------------------------- #
# Failed transformations                                                      #
# --------------------------------------------------------------------------- #


class TestFailedTransformations:
    def test_failed_transformation_does_not_advance_state(self):
        h = EGITransformationHistory(_egi(), "start")
        before_state = h.current_state_id

        step_id = h.add_transformation(
            "FailingRule",
            _context(h.get_current_state().egi),
            _result(None, success=False),
        )

        assert h.current_state_id == before_state
        assert len(h.states) == 1  # no new state
        # but the failed step IS recorded
        assert step_id in h.transformations
        failed = h.transformations[step_id]
        assert failed.status == TransformationStatus.FAILED
        assert failed.from_state_id == failed.to_state_id == before_state


# --------------------------------------------------------------------------- #
# Branching: divergence from a shared source state                            #
# --------------------------------------------------------------------------- #


class TestBranching:
    def _diverge(self):
        """Build: root -> A; rewind; root -> B. Return (history, root, step_a, step_b)."""
        h = EGITransformationHistory(_egi(), "start")
        root = h.current_state_id
        step_a = _apply(h, "RuleA")

        # Rewind current_state_id to apply a second transformation from root.
        h.current_state_id = root
        step_b = _apply(h, "RuleB")
        return h, root, step_a, step_b

    def test_divergence_makes_root_a_branch_point(self):
        h, root, _, _ = self._diverge()
        assert root in h.branch_points

    def test_divergence_records_both_outgoing_steps(self):
        h, root, step_a, step_b = self._diverge()
        assert set(h.state_to_outgoing_steps[root]) == {step_a, step_b}

    def test_divergence_creates_three_distinct_states(self):
        h, root, step_a, step_b = self._diverge()
        # root + two children
        assert len(h.states) == 3
        a_dst = h.transformations[step_a].to_state_id
        b_dst = h.transformations[step_b].to_state_id
        assert a_dst != b_dst
        assert a_dst != root and b_dst != root

    def test_create_branch_from_state_rewinds_current_state(self):
        """create_branch_from_state must register a new branch AND set
        current_state_id to the source state so subsequent transformations
        attach as that source's outgoing edges."""
        h = EGITransformationHistory(_egi(), "start")
        for i in range(3):
            _apply(h, f"Rule{i}")
        middle_state = h.state_sequence[1]

        branch_id = h.create_branch_from_state(
            middle_state, HistoryBranchType.EXPLORATION, "alt path"
        )

        assert h.current_branch_id == branch_id
        assert h.current_state_id == middle_state
        assert branch_id in h.branches

    def test_create_branch_from_state_unknown_raises(self):
        h = EGITransformationHistory(_egi(), "start")
        with pytest.raises(ValueError, match="not found"):
            h.create_branch_from_state(
                "no-such-state",
                HistoryBranchType.EXPLORATION,
                "should fail",
            )


# --------------------------------------------------------------------------- #
# Path navigation                                                             #
# --------------------------------------------------------------------------- #


class TestPathNavigation:
    def test_transformation_sequence_along_linear_path(self):
        h = EGITransformationHistory(_egi(), "start")
        root = h.current_state_id
        for i in range(3):
            _apply(h, f"Rule{i}")
        leaf = h.current_state_id

        seq = h.get_transformation_sequence(root, leaf)

        assert seq.is_valid_path
        assert seq.total_steps == 3
        # steps must come back in the order they were applied
        rule_names = [s.rule_name for s in seq.steps]
        assert rule_names == ["Rule0", "Rule1", "Rule2"]

    def test_transformation_sequence_unreachable_returns_invalid_path(self):
        """In a divergent DAG, going from one branch's leaf to the other
        leaf is not reachable via forward edges. The history reports
        is_valid_path=False rather than raising."""
        h = EGITransformationHistory(_egi(), "start")
        root = h.current_state_id
        step_a = _apply(h, "RuleA")
        h.current_state_id = root
        step_b = _apply(h, "RuleB")
        a_leaf = h.transformations[step_a].to_state_id
        b_leaf = h.transformations[step_b].to_state_id

        seq = h.get_transformation_sequence(a_leaf, b_leaf)
        assert not seq.is_valid_path
        assert seq.total_steps == 0


# --------------------------------------------------------------------------- #
# Rollback                                                                    #
# --------------------------------------------------------------------------- #


class TestRollback:
    def test_rollback_to_earlier_state_succeeds_and_creates_rollback_branch(self):
        h = EGITransformationHistory(_egi(), "start")
        for i in range(3):
            _apply(h, f"Rule{i}")
        target = h.state_sequence[1]
        before_branch = h.current_branch_id

        ok = h.rollback_to_state(target, create_branch=True)

        assert ok
        assert h.current_state_id == target
        assert h.current_branch_id != before_branch
        assert h.branches[h.current_branch_id].branch_type == HistoryBranchType.ROLLBACK

    def test_rollback_to_unknown_state_returns_false(self):
        h = EGITransformationHistory(_egi(), "start")
        assert h.rollback_to_state("no-such-state") is False

    def test_rollback_to_future_state_rejected(self):
        """The current state's step_number must strictly exceed the target's
        for rollback to make sense; rolling back to current or beyond returns
        False without changing state."""
        h = EGITransformationHistory(_egi(), "start")
        _apply(h, "Rule0")
        current = h.current_state_id

        # Try to "rollback" to the current state (same step_number).
        ok = h.rollback_to_state(current)
        assert ok is False
        assert h.current_state_id == current  # unchanged


# --------------------------------------------------------------------------- #
# Statistics                                                                  #
# --------------------------------------------------------------------------- #


class TestStatistics:
    def test_statistics_counts_successes_and_failures_separately(self):
        h = EGITransformationHistory(_egi(), "start")
        _apply(h, "Rule0")  # success
        h.add_transformation(
            "Boom",
            _context(h.get_current_state().egi),
            _result(None, success=False),
        )
        stats = h.get_history_statistics()

        assert stats["total_states"] == 2
        assert stats["total_transformations"] == 2
        assert stats["successful_transformations"] == 1
        assert stats["failed_transformations"] == 1
