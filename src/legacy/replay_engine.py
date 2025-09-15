"""
Replay Engine for Historical Graphs

Enables efficient reconstruction of graph states from transformation sequences.
Supports time travel, branching, and differential replay for performance.
"""

import copy
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from rtree_cut_tracker import RTreeCutTracker
from transformation_engine import (
    OperationRequest,
    OperationResult,
    TransformationEngine,
)
from universal_composition import CompositionSequence, CompositionStep

from egi_core_dau import Cut, Edge, ElementID, RelationalGraphWithCuts, Vertex
from historical_graph_model import (
    GraphHistory,
    HistoricalGraph,
    HistoryEvent,
    HistoryEventType,
)


class ReplayStrategy(Enum):
    """Strategies for replaying transformation sequences."""

    FULL_REPLAY = "full_replay"  # Replay from beginning
    SNAPSHOT_BASED = "snapshot_based"  # Use nearest snapshot
    DIFFERENTIAL = "differential"  # Apply only differences
    CACHED = "cached"  # Use cached intermediate states


@dataclass
class ReplayState:
    """State information during replay process."""

    current_egi: RelationalGraphWithCuts
    current_event_id: str
    spatial_tracker: RTreeCutTracker
    step_count: int
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class ReplayEngine:
    """
    Engine for replaying transformation sequences to reconstruct graph states.

    Provides efficient time travel through graph history with multiple
    replay strategies optimized for different use cases.
    """

    def __init__(self):
        self.transformation_engine = TransformationEngine(RTreeCutTracker())

        # Cache for intermediate states during replay
        self.replay_cache: Dict[str, ReplayState] = {}

        # Performance metrics
        self.replay_stats = {
            "full_replays": 0,
            "snapshot_replays": 0,
            "differential_replays": 0,
            "cache_hits": 0,
        }

    def replay_to_event(
        self,
        historical_graph: HistoricalGraph,
        target_event_id: str,
        strategy: ReplayStrategy = ReplayStrategy.SNAPSHOT_BASED,
    ) -> ReplayState:
        """
        Replay transformations to reach a specific historical event.
        """
        if target_event_id not in historical_graph.history.events:
            return ReplayState(
                current_egi=RelationalGraphWithCuts(),
                current_event_id="",
                spatial_tracker=RTreeCutTracker(),
                step_count=0,
                errors=["Target event not found in history"],
            )

        # Check cache first
        cache_key = f"{historical_graph.metadata.sheet_id}:{target_event_id}"
        if cache_key in self.replay_cache:
            self.replay_stats["cache_hits"] += 1
            return copy.deepcopy(self.replay_cache[cache_key])

        # Select replay strategy
        if strategy == ReplayStrategy.SNAPSHOT_BASED:
            return self._replay_from_snapshot(historical_graph, target_event_id)
        elif strategy == ReplayStrategy.FULL_REPLAY:
            return self._replay_from_beginning(historical_graph, target_event_id)
        elif strategy == ReplayStrategy.DIFFERENTIAL:
            return self._replay_differential(historical_graph, target_event_id)
        else:
            return self._replay_from_snapshot(historical_graph, target_event_id)

    def _replay_from_beginning(
        self, historical_graph: HistoricalGraph, target_event_id: str
    ) -> ReplayState:
        """Replay from the very beginning of graph history."""
        self.replay_stats["full_replays"] += 1

        # Start with empty graph
        current_egi = RelationalGraphWithCuts()
        spatial_tracker = RTreeCutTracker()

        # Get sequence of events to replay
        events = historical_graph.history.get_events_to_replay(target_event_id)

        step_count = 0
        errors = []

        for event in events:
            if event.event_type == HistoryEventType.TRANSFORMATION and event.operation:
                try:
                    # Apply transformation
                    result = self.transformation_engine.apply_operation(
                        current_egi, event.operation
                    )

                    if result.success and result.modified_graph:
                        current_egi = result.modified_graph
                        step_count += 1
                    else:
                        errors.append(
                            f"Failed to replay event {event.event_id}: {result.error_message}"
                        )

                except Exception as e:
                    errors.append(
                        f"Exception replaying event {event.event_id}: {str(e)}"
                    )

        replay_state = ReplayState(
            current_egi=current_egi,
            current_event_id=target_event_id,
            spatial_tracker=spatial_tracker,
            step_count=step_count,
            errors=errors,
        )

        # Cache the result
        cache_key = f"{historical_graph.metadata.sheet_id}:{target_event_id}"
        self.replay_cache[cache_key] = copy.deepcopy(replay_state)

        return replay_state

    def _replay_from_snapshot(
        self, historical_graph: HistoricalGraph, target_event_id: str
    ) -> ReplayState:
        """Replay from the nearest available snapshot."""
        self.replay_stats["snapshot_replays"] += 1

        # Find nearest snapshot
        events = historical_graph.history.get_events_to_replay(target_event_id)
        start_egi = RelationalGraphWithCuts()
        start_index = 0

        # Look for snapshots in reverse order (nearest to target)
        for i in range(len(events) - 1, -1, -1):
            event = events[i]
            if event.event_id in historical_graph.snapshots:
                start_egi = copy.deepcopy(historical_graph.snapshots[event.event_id])
                start_index = i + 1
                break

        # Replay from snapshot point
        current_egi = start_egi
        spatial_tracker = RTreeCutTracker()

        # Rebuild spatial tracker from starting EGI
        self._rebuild_spatial_tracker(spatial_tracker, current_egi)

        step_count = start_index
        errors = []

        # Replay remaining events
        for event in events[start_index:]:
            if event.event_type == HistoryEventType.TRANSFORMATION and event.operation:
                try:
                    result = self.transformation_engine.apply_operation(
                        current_egi, event.operation
                    )

                    if result.success and result.modified_graph:
                        current_egi = result.modified_graph
                        step_count += 1
                    else:
                        errors.append(
                            f"Failed to replay event {event.event_id}: {result.error_message}"
                        )

                except Exception as e:
                    errors.append(
                        f"Exception replaying event {event.event_id}: {str(e)}"
                    )

        replay_state = ReplayState(
            current_egi=current_egi,
            current_event_id=target_event_id,
            spatial_tracker=spatial_tracker,
            step_count=step_count,
            errors=errors,
        )

        # Cache the result
        cache_key = f"{historical_graph.metadata.sheet_id}:{target_event_id}"
        self.replay_cache[cache_key] = copy.deepcopy(replay_state)

        return replay_state

    def _replay_differential(
        self, historical_graph: HistoricalGraph, target_event_id: str
    ) -> ReplayState:
        """Replay using differential approach from current state."""
        self.replay_stats["differential_replays"] += 1

        current_event = historical_graph.history.current_event_id
        if not current_event:
            return self._replay_from_beginning(historical_graph, target_event_id)

        # If target is current state, return current state
        if target_event_id == current_event:
            return ReplayState(
                current_egi=copy.deepcopy(historical_graph.current_egi),
                current_event_id=target_event_id,
                spatial_tracker=RTreeCutTracker(),
                step_count=0,
            )

        # For now, fall back to snapshot-based replay
        # Full differential implementation would track forward/backward deltas
        return self._replay_from_snapshot(historical_graph, target_event_id)

    def _rebuild_spatial_tracker(
        self, spatial_tracker: RTreeCutTracker, egi: RelationalGraphWithCuts
    ):
        """Rebuild spatial tracker from EGI state."""
        for cut_id, cut in egi.Cut.items():
            if hasattr(cut, "spatial_bounds") and cut.spatial_bounds:
                spatial_tracker.add_cut(
                    cut_id=cut_id,
                    bounds=cut.spatial_bounds,
                    parent_area=getattr(cut, "parent_area", None),
                    placement_type=getattr(cut, "placement_type", None),
                )

    def replay_sequence(
        self, initial_egi: RelationalGraphWithCuts, sequence: CompositionSequence
    ) -> ReplayState:
        """
        Replay a composition sequence from a given initial state.
        """
        current_egi = copy.deepcopy(initial_egi)
        spatial_tracker = RTreeCutTracker()

        # Rebuild spatial tracker from initial state
        self._rebuild_spatial_tracker(spatial_tracker, current_egi)

        step_count = 0
        errors = []

        for step in sequence.steps:
            try:
                result = self.transformation_engine.apply_operation(
                    current_egi, step.operation
                )

                if result.success and result.modified_graph:
                    current_egi = result.modified_graph
                    step_count += 1
                else:
                    errors.append(
                        f"Failed to replay step {step_count}: {result.error_message}"
                    )

            except Exception as e:
                errors.append(f"Exception replaying step {step_count}: {str(e)}")

        return ReplayState(
            current_egi=current_egi,
            current_event_id="sequence_end",
            spatial_tracker=spatial_tracker,
            step_count=step_count,
            errors=errors,
        )

    def create_replay_branch(
        self,
        historical_graph: HistoricalGraph,
        branch_point_event_id: str,
        new_operations: List[OperationRequest],
    ) -> ReplayState:
        """
        Create a hypothetical branch by replaying to a point and applying new operations.
        """
        # Replay to branch point
        branch_state = self.replay_to_event(historical_graph, branch_point_event_id)

        if branch_state.errors:
            return branch_state

        # Apply new operations
        current_egi = branch_state.current_egi
        spatial_tracker = branch_state.spatial_tracker

        for operation in new_operations:
            try:
                result = self.transformation_engine.apply_operation(
                    current_egi, operation
                )

                if result.success and result.modified_graph:
                    current_egi = result.modified_graph
                    branch_state.step_count += 1
                else:
                    branch_state.errors.append(
                        f"Failed branch operation: {result.error_message}"
                    )

            except Exception as e:
                branch_state.errors.append(f"Exception in branch operation: {str(e)}")

        branch_state.current_egi = current_egi
        branch_state.spatial_tracker = spatial_tracker

        return branch_state

    def validate_replay_consistency(
        self, historical_graph: HistoricalGraph
    ) -> Dict[str, Any]:
        """
        Validate that replay produces consistent results with stored snapshots.
        """
        validation_results = {
            "consistent": True,
            "tested_snapshots": 0,
            "inconsistencies": [],
        }

        for event_id, snapshot_egi in historical_graph.snapshots.items():
            # Replay to this event
            replay_state = self.replay_to_event(historical_graph, event_id)

            validation_results["tested_snapshots"] += 1

            # Compare with stored snapshot
            if not self._compare_egi_states(replay_state.current_egi, snapshot_egi):
                validation_results["consistent"] = False
                validation_results["inconsistencies"].append(
                    {"event_id": event_id, "replay_errors": replay_state.errors}
                )

        return validation_results

    def _compare_egi_states(
        self, egi1: RelationalGraphWithCuts, egi2: RelationalGraphWithCuts
    ) -> bool:
        """Compare two EGI states for consistency (simplified comparison)."""
        return (
            len(egi1.V) == len(egi2.V)
            and len(egi1.E) == len(egi2.E)
            and len(egi1.Cut) == len(egi2.Cut)
            # Full comparison would check all elements and relationships
        )

    def get_replay_statistics(self) -> Dict[str, Any]:
        """Get performance statistics for replay operations."""
        return {
            **self.replay_stats,
            "cache_size": len(self.replay_cache),
            "cache_efficiency": (
                self.replay_stats["cache_hits"]
                / max(1, sum(self.replay_stats.values()))
            ),
        }

    def clear_cache(self):
        """Clear replay cache to free memory."""
        self.replay_cache.clear()

    def optimize_snapshots(
        self, historical_graph: HistoricalGraph, target_intervals: int = 10
    ) -> List[str]:
        """
        Suggest optimal snapshot points for efficient replay.
        """
        total_events = len(historical_graph.history.events)
        if total_events <= target_intervals:
            return list(historical_graph.history.events.keys())

        # Suggest evenly spaced snapshot points
        interval = total_events // target_intervals
        suggested_snapshots = []

        for i in range(0, total_events, interval):
            if i < len(historical_graph.history.event_sequence):
                event_id = historical_graph.history.event_sequence[i]
                suggested_snapshots.append(event_id)

        return suggested_snapshots
