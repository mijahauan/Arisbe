"""
Interactive EGI Transformer with Transformation History Integration

Integrates the transformation history system with the interactive transformer,
providing real-time history tracking, rollback capabilities, and semantic annotations.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml
from enhanced_transformation_history import (
    EnhancedEGITransformationHistory,
    ProofExportFormat,
)

from domain_ontology_model import DomainModelManager, OntologyReference, OntologyType
from egi_core_dau import ElementID, RelationalGraphWithCuts
from egi_transformation_history import LogicalProvenance
from egif_transformation_interface import TransformationRequest
from formal_transformation_rules import AreaPolarity, TransformationContext
from history_persistence import HistoryPersistenceManager
from interactive_egif_transformer import GraphAnalysis, InteractiveEGIFTransformer


@dataclass
class HistoryState:
    """Current state of the transformation history."""

    current_step: int
    total_steps: int
    can_undo: bool
    can_redo: bool
    current_branch: str
    available_branches: List[str]
    unsaved_changes: bool


@dataclass
class TransformationSession:
    """A complete transformation session with history."""

    session_id: str
    name: str
    description: str
    created_timestamp: datetime
    last_modified: datetime
    history: EnhancedEGITransformationHistory
    persistence_manager: HistoryPersistenceManager
    auto_save_enabled: bool = True
    save_interval_steps: int = 5


class InteractiveTransformerWithHistory:
    """Enhanced interactive transformer with full history integration."""

    def __init__(self, base_history_path: str = "transformation_histories"):
        self.base_transformer = InteractiveEGIFTransformer()
        self.persistence_manager = HistoryPersistenceManager(base_history_path)

        # Current session
        self.current_session: Optional[TransformationSession] = None
        self.history_state = HistoryState(0, 0, False, False, "", [], False)

        # Session management
        self.sessions: Dict[str, TransformationSession] = {}
        self.recent_sessions: List[str] = []

        # Auto-save tracking
        self.steps_since_save = 0

    def create_new_session(
        self, name: str, description: str = "", initial_egif_path: Optional[str] = None
    ) -> str:
        """Create a new transformation session with history tracking."""

        # Load initial EGIF if provided
        if initial_egif_path:
            # Read the EGIF file directly
            egif_path = Path(initial_egif_path)
            if not egif_path.exists():
                raise ValueError(f"EGIF file not found: {initial_egif_path}")

            with open(egif_path, "r") as f:
                egif_data = json.load(f)
                egif_string = egif_data.get("egif", "")

            # Parse and analyze the EGIF
            analysis = self.base_transformer.analyze_graph(egif_string)
            self.base_transformer.current_egif = egif_string
            self.base_transformer.current_egi = (
                self.base_transformer.interface.parse_egif_to_egi(egif_string)
            )
            self.base_transformer.analysis = analysis

            self.current_egi = self.base_transformer.current_egi
        else:
            # Create empty EGI or use current one
            initial_egi = self.base_transformer.current_egi
            if initial_egi is None:
                raise ValueError("No initial EGI available. Load an EGIF file first.")

        # Create enhanced history
        initial_egi = (
            self.current_egi if initial_egif_path else self.base_transformer.current_egi
        )
        if initial_egi is None:
            raise ValueError("No initial EGI available. Load an EGIF file first.")

        history = EnhancedEGITransformationHistory(
            initial_egi=initial_egi, description=f"Session: {name}"
        )

        # Create session
        session = TransformationSession(
            session_id=history.history_id,
            name=name,
            description=description,
            created_timestamp=datetime.now(),
            last_modified=datetime.now(),
            history=history,
            persistence_manager=self.persistence_manager,
        )

        # Set as current session
        self.current_session = session
        self.sessions[session.session_id] = session
        self.recent_sessions.insert(0, session.session_id)

        # Update history state
        self._update_history_state()

        # Auto-save initial state
        if session.auto_save_enabled:
            self._auto_save_session()

        return session.session_id

    def load_session(self, session_path: str) -> str:
        """Load an existing transformation session."""

        # Load history from file
        history = self.persistence_manager.load_history_json(session_path)

        # Get current EGI state
        current_state = history.get_current_state()

        # Update base transformer
        self.base_transformer.current_egi = current_state.egi
        self.base_transformer.current_egif = current_state.linear_forms.get("egif", "")
        self.base_transformer.analysis = self._create_analysis_from_egi(
            current_state.egi
        )

        # Create session object
        session = TransformationSession(
            session_id=history.history_id,
            name=f"Loaded Session",
            description="Loaded from file",
            created_timestamp=history.created_timestamp,
            last_modified=datetime.now(),
            history=history,
            persistence_manager=self.persistence_manager,
        )

        # Set as current session
        self.current_session = session
        self.sessions[session.session_id] = session

        # Update history state
        self._update_history_state()

        return session.session_id

    def apply_transformation_with_history(
        self,
        rule_name: str,
        target_area: str,
        user_annotation: str = "",
        domain_contexts: Set[str] = None,
    ) -> Dict[str, Any]:
        """Apply transformation and record in history."""

        if not self.current_session:
            return {"success": False, "error": "No active session"}

        # Create transformation request
        request = TransformationRequest(
            source_egif=self.base_transformer.current_egif,
            rule_name=rule_name,
            target_area_description=target_area,
            operation_details={},
            description=f"Apply {rule_name} transformation",
        )

        result = self.base_transformer.interface.apply_transformation(
            request, existing_egi=self.base_transformer.current_egi
        )

        if not result.success:
            return {"success": False, "error": result.error_message}

        # Create logical provenance
        provenance = LogicalProvenance(
            rule_citation=f"Rule: {rule_name}",
            logical_equivalence="Transformation preserves logical equivalence",
            semantic_interpretation=user_annotation or f"Applied {rule_name}",
            proof_obligations=[],
            domain_assumptions=[],
            ontological_commitments=[],
        )

        # Create transformation context
        from egi_core_dau import ElementID

        context = TransformationContext(
            source_egi=self.base_transformer.current_egi,
            target_area=ElementID(target_area),
            selected_subgraph=frozenset(
                ElementID(e) for e in (selected_elements or [])
            ),
            area_polarity=AreaPolarity.POSITIVE,  # Would be calculated properly
            nesting_depth=0,  # Would be calculated properly
        )

        # Add to history
        step_id = self.current_session.history.add_transformation_with_domain_context(
            rule_name=rule_name,
            context=context,
            result=result,
            domain_contexts=domain_contexts or set(),
            natural_language=user_annotation or f"Applied {rule_name}",
            logical_provenance=provenance,
            author_id="interactive_user",
        )

        # Update current EGI
        self.base_transformer.current_egi = result.result_egi
        self.base_transformer.analysis = self._create_analysis_from_egi(
            result.result_egi
        )

        # Update session
        self.current_session.last_modified = datetime.now()
        self.history_state.unsaved_changes = True
        self.steps_since_save += 1

        # Update history state
        self._update_history_state()

        # Auto-save if needed
        if (
            self.current_session.auto_save_enabled
            and self.steps_since_save >= self.current_session.save_interval_steps
        ):
            self._auto_save_session()

        return {
            "success": True,
            "step_id": step_id,
            "new_state_id": self.current_session.history.current_state_id,
            "history_state": self.history_state,
        }

    def undo_transformation(self) -> Dict[str, Any]:
        """Undo the last transformation."""

        if not self.current_session or not self.history_state.can_undo:
            return {"success": False, "error": "Cannot undo"}

        # Get previous state
        current_step = self.current_session.history.states[
            self.current_session.history.current_state_id
        ].step_number

        if current_step == 0:
            return {"success": False, "error": "Already at initial state"}

        # Find previous state
        previous_state_id = None
        for state_id, state in self.current_session.history.states.items():
            if state.step_number == current_step - 1:
                previous_state_id = state_id
                break

        if not previous_state_id:
            return {"success": False, "error": "Previous state not found"}

        # Rollback to previous state
        success = self.current_session.history.rollback_to_state(
            previous_state_id, create_branch=False
        )

        if success:
            # Update current EGI
            previous_state = self.current_session.history.states[previous_state_id]
            self.base_transformer.current_egi = previous_state.egi
            self.base_transformer.analysis = self._create_analysis_from_egi(
                previous_state.egi
            )

            # Update history state
            self._update_history_state()
            self.history_state.unsaved_changes = True

            return {
                "success": True,
                "current_state_id": previous_state_id,
                "history_state": self.history_state,
            }

        return {"success": False, "error": "Rollback failed"}

    def create_exploration_branch(self, description: str) -> str:
        """Create a new exploration branch from current state."""

        if not self.current_session:
            raise ValueError("No active session")

        branch_id = self.current_session.history.create_exploration_branch(description)
        self._update_history_state()

        return branch_id

    def get_transformation_narrative(
        self, from_step: Optional[int] = None, to_step: Optional[int] = None
    ) -> str:
        """Get natural language narrative of transformations."""

        if not self.current_session:
            return "No active session"

        # Get state IDs for the range
        states_by_step = {
            state.step_number: state_id
            for state_id, state in self.current_session.history.states.items()
        }

        from_step = from_step or 0
        to_step = to_step or max(states_by_step.keys())

        from_state_id = states_by_step.get(from_step)
        to_state_id = states_by_step.get(to_step)

        if not from_state_id or not to_state_id:
            return "Invalid step range"

        return self.current_session.history.get_natural_language_narrative(
            from_state_id, to_state_id
        )

    def export_proof(
        self,
        export_format: ProofExportFormat,
        from_step: Optional[int] = None,
        to_step: Optional[int] = None,
    ) -> str:
        """Export transformation sequence as formal proof."""

        if not self.current_session:
            return "No active session"

        # Get state IDs for the range
        states_by_step = {
            state.step_number: state_id
            for state_id, state in self.current_session.history.states.items()
        }

        from_step = from_step or 0
        to_step = to_step or max(states_by_step.keys())

        from_state_id = states_by_step.get(from_step)
        to_state_id = states_by_step.get(to_step)

        if not from_state_id or not to_state_id:
            return "Invalid step range"

        return self.current_session.history.export_proof_sequence(
            from_state_id, to_state_id, export_format, include_domain_context=True
        )

    def save_session(self, format_type: str = "json") -> str:
        """Save current session to file."""

        if not self.current_session:
            raise ValueError("No active session")

        if format_type == "json":
            filepath = self.persistence_manager.save_history_json(
                self.current_session.history
            )
        elif format_type == "yaml":
            filepath = self.persistence_manager.save_history_yaml(
                self.current_session.history
            )
        elif format_type == "compressed":
            filepath = self.persistence_manager.save_history_compressed(
                self.current_session.history
            )
        else:
            raise ValueError(f"Unsupported format: {format_type}")

        self.history_state.unsaved_changes = False
        self.steps_since_save = 0

        return str(filepath)

    def get_session_statistics(self) -> Dict[str, Any]:
        """Get statistics about current session."""

        if not self.current_session:
            return {"error": "No active session"}

        history_stats = self.current_session.history.get_history_statistics()

        return {
            "session_info": {
                "session_id": self.current_session.session_id,
                "name": self.current_session.name,
                "description": self.current_session.description,
                "created": self.current_session.created_timestamp.isoformat(),
                "last_modified": self.current_session.last_modified.isoformat(),
            },
            "history_stats": history_stats,
            "history_state": self.history_state,
            "domain_contexts": len(
                self.current_session.history.domain_model_manager.domain_contexts
            ),
            "semantic_annotations": len(
                self.current_session.history.domain_model_manager.semantic_annotations
            ),
        }

    def _update_history_state(self):
        """Update the history state information."""

        if not self.current_session:
            self.history_state = HistoryState(0, 0, False, False, "", [], False)
            return

        current_state = self.current_session.history.get_current_state()
        total_states = len(self.current_session.history.states)

        self.history_state = HistoryState(
            current_step=current_state.step_number,
            total_steps=total_states - 1,  # Subtract 1 for initial state
            can_undo=current_state.step_number > 0,
            can_redo=False,  # Redo not implemented yet
            current_branch=self.current_session.history.current_branch_id,
            available_branches=list(self.current_session.history.branches.keys()),
            unsaved_changes=self.history_state.unsaved_changes,
        )

    def _auto_save_session(self):
        """Auto-save the current session."""

        if not self.current_session or not self.current_session.auto_save_enabled:
            return

        try:
            # Save as checkpoint
            self.persistence_manager.save_incremental_checkpoint(
                self.current_session.history
            )
            self.steps_since_save = 0
            self.history_state.unsaved_changes = False
        except Exception as e:
            print(f"Auto-save failed: {e}")

    def _create_analysis_from_egi(self, egi: RelationalGraphWithCuts) -> GraphAnalysis:
        """Create graph analysis from EGI (simplified version)."""

        return GraphAnalysis(
            egif="# EGIF generation not implemented",
            vertex_count=len(egi.V),
            edge_count=len(egi.E),
            cut_count=len(egi.Cut),
            areas={},  # Would be populated with area analysis
            elements={},  # Would be populated with element analysis
            suggested_operations=[],  # Would be populated with suggestions
        )

    def get_available_sessions(self) -> List[Dict[str, Any]]:
        """Get list of available saved sessions."""

        sessions = []

        # Check JSON files
        for json_file in self.persistence_manager.json_path.glob("history_*.json"):
            try:
                with open(json_file, "r") as f:
                    data = json.load(f)

                sessions.append(
                    {
                        "file_path": str(json_file),
                        "format": "json",
                        "history_id": data.get("history_metadata", {}).get(
                            "history_id", "unknown"
                        ),
                        "created": data.get("history_metadata", {}).get(
                            "created_timestamp", "unknown"
                        ),
                        "total_states": len(data.get("states", {})),
                        "total_transformations": len(data.get("transformations", {})),
                    }
                )
            except Exception:
                continue

        return sessions
