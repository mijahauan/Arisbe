{{...}}
from historical_graph_model import (
    CompositionSource,
    HistoricalGraph,
    HistoricalGraphRepository,
)

{{...}}


class SheetOfAssertion:
    """
    Unified Universe of Discourse represented as a historical graph.

    The Sheet of Assertion is now a HistoricalGraph that tracks all
    transformations applied to it, enabling complete provenance and replay.
    """

    def __init__(
        self,
        metadata: SheetMetadata,
        creation_source: CompositionSource = CompositionSource.DE_NOVO,
    ):
        self.metadata = metadata

        # Core historical graph with transformation tracking
        self.historical_graph = HistoricalGraph(
            metadata=metadata, creation_source=creation_source
        )

        # Spatial tracking for cuts and areas
        self.spatial_tracker = RTreeCutTracker()

        # Transformation engine for all operations
        self.transformation_engine = TransformationEngine(
            spatial_tracker=self.spatial_tracker,
            history_callback=self._record_transformation,
        )

        # Context tracking within the sheet
        self.active_contexts: Dict[str, GraphContext] = {}
        self.context_hierarchy: Dict[str, List[str]] = {}  # parent -> children

    @property
    def current_egi(self) -> RelationalGraphWithCuts:
        """Get the current EGI state."""
        return self.historical_graph.current_egi

    def _record_transformation(
        self, operation: OperationRequest, result: OperationResult
    ):
        """Callback to record transformations in history."""
        self.historical_graph.apply_transformation(operation, result, author="system")

    def apply_operation(self, operation: OperationRequest) -> OperationResult:
        """Apply an operation through the transformation engine with history tracking."""
        # Apply through transformation engine (which calls history callback)
        result = self.transformation_engine.apply_operation(self.current_egi, operation)

        # Update metadata
        if result.success:
            self.metadata.update_modified()

        return result

    def create_checkpoint(self, description: str, author: str = "") -> str:
        """Create a checkpoint in the transformation history."""
        return self.historical_graph.create_checkpoint(description, author)

    def replay_to_event(self, event_id: str) -> bool:
        """Replay transformations to reach a specific historical state."""
        success = self.historical_graph.replay_to_event(event_id)

        if success:
            # Rebuild spatial tracker from replayed state
            self._rebuild_spatial_tracker()

        return success

    def _rebuild_spatial_tracker(self):
        """Rebuild spatial tracker from current EGI state."""
        self.spatial_tracker = RTreeCutTracker()

        # Add all cuts from current EGI to spatial tracker
        for cut_id, cut in self.current_egi.Cut.items():
            if hasattr(cut, "spatial_bounds") and cut.spatial_bounds:
                self.spatial_tracker.add_cut(
                    cut_id=cut_id,
                    bounds=cut.spatial_bounds,
                    parent_area=cut.parent_area,
                    placement_type=CutPlacementType.MANUAL,
                )

    def get_transformation_sequence(self) -> CompositionSequence:
        """Get the complete transformation sequence that created this sheet."""
        return self.historical_graph.get_transformation_sequence()

    def branch_from_event(self, branch_name: str, event_id: str) -> bool:
        """Create a new branch from a specific historical event."""
        return self.historical_graph.branch_from_event(branch_name, event_id)

    def get_history_statistics(self) -> Dict[str, Any]:
        """Get statistics about the sheet's transformation history."""
        return self.historical_graph.history.get_statistics()

    def export_with_history(self) -> Dict[str, Any]:
        """Export sheet with complete transformation history."""
        base_export = self.historical_graph.export_with_history()

        # Add sheet-specific data
        base_export.update(
            {
                "spatial_tracker": self.spatial_tracker.export_state(),
                "active_contexts": {
                    cid: ctx.to_dict() for cid, ctx in self.active_contexts.items()
                },
                "context_hierarchy": self.context_hierarchy,
            }
        )

        return base_export

    @classmethod
    def import_with_history(cls, data: Dict[str, Any]) -> "SheetOfAssertion":
        """Import sheet with complete transformation history."""
        # Import historical graph
        historical_graph = HistoricalGraph.import_with_history(data)

        # Create sheet
        sheet = cls(historical_graph.metadata)
        sheet.historical_graph = historical_graph

        # Restore spatial tracker
        if "spatial_tracker" in data:
            sheet.spatial_tracker.import_state(data["spatial_tracker"])

        # Restore contexts
        if "active_contexts" in data:
            for cid, ctx_data in data["active_contexts"].items():
                sheet.active_contexts[cid] = GraphContext.from_dict(ctx_data)

        if "context_hierarchy" in data:
            sheet.context_hierarchy = data["context_hierarchy"]

        return sheet


{{...}}
