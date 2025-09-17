{{...}}
from historical_graph_model import HistoricalGraph, HistoryEvent, HistoryEventType

{{...}}


class UniversalComposer:
    """
    Universal interface for all graph composition workflows.

    Now creates HistoricalGraph objects that track the complete
    transformation sequence for any composition source.
    """

    def __init__(self, repository: "HistoricalGraphRepository"):
        self.repository = repository
        self.adapters = {
            CompositionSource.EGIF_IMPORT: EGIFImportAdapter(),
            CompositionSource.CGIF_IMPORT: CGIFImportAdapter(),
            CompositionSource.CLIF_IMPORT: CLIFImportAdapter(),
            CompositionSource.NATURAL_LANGUAGE: NaturalLanguageAdapter(),
            CompositionSource.SUBGRAPH_ADDITION: SubgraphAdditionAdapter(),
            CompositionSource.DE_NOVO: DeNovoCompositionAdapter(),
        }

    def create_historical_sheet(
        self,
        metadata: SheetMetadata,
        source: CompositionSource = CompositionSource.DE_NOVO,
    ) -> HistoricalGraph:
        """Create a new historical graph (sheet) with specified source."""
        historical_graph = HistoricalGraph(metadata=metadata, creation_source=source)

        # Store in repository
        self.repository.store_graph(historical_graph)

        return historical_graph

    def compose_from_source(
        self,
        sheet_id: str,
        source: CompositionSource,
        input_data: Any,
        author: str = "",
    ) -> CompositionResult:
        """
        Universal composition method that works with any source type.
        Creates or updates a HistoricalGraph with complete transformation history.
        """
        # Get or create historical graph
        historical_graph = self.repository.load_graph(sheet_id)
        if not historical_graph:
            # Create new historical graph
            metadata = SheetMetadata(
                sheet_id=sheet_id,
                title=f"Graph from {source.value}",
                purpose=SheetPurpose.RESEARCH,
            )
            historical_graph = self.create_historical_sheet(metadata, source)

        # Get appropriate adapter
        adapter = self.adapters.get(source)
        if not adapter:
            return CompositionResult(
                success=False,
                error_message=f"No adapter available for source: {source}",
                sheet_id=sheet_id,
            )

        try:
            # Convert input to composition sequence
            sequence = adapter.convert_to_sequence(input_data)

            # Create import event in history
            import_event = HistoryEvent(
                event_id=str(uuid.uuid4()),
                event_type=HistoryEventType.IMPORT,
                timestamp=datetime.now(),
                description=f"Imported from {source.value}",
                author=author,
                metadata={
                    "source": source.value,
                    "input_type": type(input_data).__name__,
                },
            )

            historical_graph.history.add_event(import_event)

            # Execute composition sequence with history tracking
            result = self._execute_sequence_with_history(
                historical_graph, sequence, author
            )

            # Update repository
            self.repository.store_graph(historical_graph)

            return result

        except Exception as e:
            return CompositionResult(
                success=False,
                error_message=f"Composition failed: {str(e)}",
                sheet_id=sheet_id,
            )

    def _execute_sequence_with_history(
        self,
        historical_graph: HistoricalGraph,
        sequence: CompositionSequence,
        author: str,
    ) -> CompositionResult:
        """Execute a composition sequence with full history tracking."""
        # Create sheet of assertion for execution
        sheet = SheetOfAssertion(historical_graph.metadata)
        sheet.historical_graph = historical_graph

        successful_steps = 0
        failed_steps = []

        for i, step in enumerate(sequence.steps):
            try:
                # Apply operation through sheet (which records in history)
                result = sheet.apply_operation(step.operation)

                if result.success:
                    successful_steps += 1
                    # Update historical graph with successful result
                    if result.modified_graph:
                        historical_graph.current_egi = result.modified_graph
                else:
                    failed_steps.append(
                        {
                            "step": i,
                            "description": step.step_description,
                            "error": result.error_message,
                        }
                    )

            except Exception as e:
                failed_steps.append(
                    {"step": i, "description": step.step_description, "error": str(e)}
                )

        # Create completion checkpoint
        if successful_steps > 0:
            historical_graph.create_checkpoint(
                f"Completed composition: {successful_steps} steps successful", author
            )

        success = len(failed_steps) == 0
        return CompositionResult(
            success=success,
            sheet_id=historical_graph.metadata.sheet_id,
            steps_completed=successful_steps,
            total_steps=len(sequence.steps),
            error_message=f"Failed steps: {failed_steps}" if failed_steps else None,
            composition_sequence=sequence,
        )

    def import_from_egif(
        self, sheet_id: str, egif_text: str, author: str = ""
    ) -> CompositionResult:
        """Import EGIF with full history tracking."""
        return self.compose_from_source(
            sheet_id, CompositionSource.EGIF_IMPORT, egif_text, author
        )

    def import_from_cgif(
        self, sheet_id: str, cgif_text: str, author: str = ""
    ) -> CompositionResult:
        """Import CGIF with full history tracking."""
        return self.compose_from_source(
            sheet_id, CompositionSource.CGIF_IMPORT, cgif_text, author
        )

    def import_from_clif(
        self, sheet_id: str, clif_text: str, author: str = ""
    ) -> CompositionResult:
        """Import CLIF with full history tracking."""
        return self.compose_from_source(
            sheet_id, CompositionSource.CLIF_IMPORT, clif_text, author
        )

    def compose_from_text(
        self, sheet_id: str, natural_language: str, author: str = ""
    ) -> CompositionResult:
        """Compose from natural language with full history tracking."""
        return self.compose_from_source(
            sheet_id, CompositionSource.NATURAL_LANGUAGE, natural_language, author
        )

    def add_subgraph(
        self,
        target_sheet_id: str,
        source_graph: RelationalGraphWithCuts,
        author: str = "",
    ) -> CompositionResult:
        """Add subgraph with full history tracking."""
        return self.compose_from_source(
            target_sheet_id, CompositionSource.SUBGRAPH_ADDITION, source_graph, author
        )

    def compose_interactively(
        self, sheet_id: str, sequence: CompositionSequence, author: str = ""
    ) -> CompositionResult:
        """Interactive composition with full history tracking."""
        return self.compose_from_source(
            sheet_id, CompositionSource.DE_NOVO, sequence, author
        )

    def replay_to_checkpoint(self, sheet_id: str, checkpoint_id: str) -> bool:
        """Replay a historical graph to a specific checkpoint."""
        historical_graph = self.repository.load_graph(sheet_id)
        if not historical_graph:
            return False

        success = historical_graph.replay_to_event(checkpoint_id)

        if success:
            # Update repository with replayed state
            self.repository.store_graph(historical_graph)

        return success

    def create_branch(
        self, sheet_id: str, branch_name: str, from_checkpoint: str = None
    ) -> bool:
        """Create a branch from a checkpoint in the transformation history."""
        historical_graph = self.repository.load_graph(sheet_id)
        if not historical_graph:
            return False

        return historical_graph.branch_from_event(branch_name, from_checkpoint)

    def merge_graphs(
        self, target_sheet_id: str, source_sheet_id: str, author: str = ""
    ) -> CompositionResult:
        """Merge one historical graph into another with full provenance."""
        target_graph = self.repository.load_graph(target_sheet_id)
        source_graph = self.repository.load_graph(source_sheet_id)

        if not target_graph or not source_graph:
            return CompositionResult(
                success=False,
                error_message="One or both graphs not found",
                sheet_id=target_sheet_id,
            )

        # Record merge in target graph history
        merge_event_id = target_graph.merge_from_graph(source_graph, author)

        # Convert source graph to composition sequence and apply to target
        source_sequence = source_graph.get_transformation_sequence()

        # Execute merge as composition sequence
        result = self._execute_sequence_with_history(
            target_graph, source_sequence, author
        )

        # Update repository
        self.repository.store_graph(target_graph)

        return result

    def get_composition_history(self, sheet_id: str) -> Optional[Dict[str, Any]]:
        """Get the complete composition history for a sheet."""
        historical_graph = self.repository.load_graph(sheet_id)
        if not historical_graph:
            return None

        return {
            "statistics": historical_graph.get_history_statistics(),
            "transformation_sequence": historical_graph.get_transformation_sequence(),
            "export_data": historical_graph.export_with_history(),
        }


{{...}}
