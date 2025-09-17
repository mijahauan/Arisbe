"""
EGI Transformation History Persistence System

Supports multiple serialization formats with hybrid approach:
- JSON for performance and compatibility
- YAML for human-readable exports
- Binary compression for large histories
"""

import gzip
import json
import pickle
import uuid
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from egi_io import from_dict, to_dict
from enhanced_transformation_history import (
    CollaborationMetadata,
    EnhancedEGITransformationHistory,
    ProofExportFormat,
)

# from domain_ontology_model import DomainModelManager  # Removed orphaned dependency
from egi_core_dau import ElementID
from egi_transformation_history import (
    HistoryBranch,
    HistoryBranchType,
    LogicalProvenance,
    StateSnapshot,
    TransformationStatus,
    TransformationStep,
)
from formal_transformation_rules import (
    AreaPolarity,
    TransformationContext,
    TransformationResult,
)


class HistoryPersistenceManager:
    """Manages persistence of EGI transformation histories in multiple formats."""

    def __init__(self, base_path: Union[str, Path] = "histories"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)

        # Format-specific subdirectories
        self.json_path = self.base_path / "json"
        self.yaml_path = self.base_path / "yaml"
        self.compressed_path = self.base_path / "compressed"

        for path in [self.json_path, self.yaml_path, self.compressed_path]:
            path.mkdir(exist_ok=True)

    def save_history_json(
        self,
        history: EnhancedEGITransformationHistory,
        filename: Optional[str] = None,
        include_compressed_states: bool = False,
    ) -> Path:
        """Save history in JSON format (primary storage)."""

        if filename is None:
            filename = f"history_{history.history_id}.json"

        filepath = self.json_path / filename

        # Serialize the complete history
        history_data = self._serialize_history_to_dict(
            history, include_compressed_states
        )

        # Write JSON with pretty formatting
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(
                history_data,
                f,
                indent=2,
                ensure_ascii=False,
                default=self._json_serializer,
            )

        return filepath

    def load_history_json(
        self, filepath: Union[str, Path]
    ) -> EnhancedEGITransformationHistory:
        """Load history from JSON format."""

        filepath = Path(filepath)

        with open(filepath, "r", encoding="utf-8") as f:
            history_data = json.load(f)

        return self._deserialize_history_from_dict(history_data)

    def save_history_yaml(
        self,
        history: EnhancedEGITransformationHistory,
        filename: Optional[str] = None,
        include_annotations: bool = True,
    ) -> Path:
        """Save history in YAML format (human-readable export)."""

        if filename is None:
            filename = f"history_{history.history_id}.yaml"

        filepath = self.yaml_path / filename

        # Create human-readable version with annotations
        history_data = self._serialize_history_to_dict(
            history, include_compressed_states=False
        )

        if include_annotations:
            history_data = self._add_yaml_annotations(history_data)

        # Write YAML with comments and formatting
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(
                history_data,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
                indent=2,
            )

        return filepath

    def load_history_yaml(
        self, filepath: Union[str, Path]
    ) -> EnhancedEGITransformationHistory:
        """Load history from YAML format."""

        filepath = Path(filepath)

        with open(filepath, "r", encoding="utf-8") as f:
            history_data = yaml.safe_load(f)

        # Remove annotation fields if present
        history_data = self._remove_yaml_annotations(history_data)

        return self._deserialize_history_from_dict(history_data)

    def save_history_compressed(
        self, history: EnhancedEGITransformationHistory, filename: Optional[str] = None
    ) -> Path:
        """Save history in compressed binary format (for large histories)."""

        if filename is None:
            filename = f"history_{history.history_id}.gz"

        filepath = self.compressed_path / filename

        # Serialize to JSON then compress
        history_data = self._serialize_history_to_dict(
            history, include_compressed_states=True
        )
        json_bytes = json.dumps(history_data, default=self._json_serializer).encode(
            "utf-8"
        )

        with gzip.open(filepath, "wb") as f:
            f.write(json_bytes)

        return filepath

    def load_history_compressed(
        self, filepath: Union[str, Path]
    ) -> EnhancedEGITransformationHistory:
        """Load history from compressed format."""

        filepath = Path(filepath)

        with gzip.open(filepath, "rb") as f:
            json_bytes = f.read()

        history_data = json.loads(json_bytes.decode("utf-8"))
        return self._deserialize_history_from_dict(history_data)

    def save_incremental_checkpoint(
        self,
        history: EnhancedEGITransformationHistory,
        checkpoint_name: Optional[str] = None,
    ) -> Path:
        """Save incremental checkpoint (only recent changes)."""

        if checkpoint_name is None:
            checkpoint_name = f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        filepath = self.json_path / f"{checkpoint_name}.json"

        # Only save recent states (last 10 steps)
        current_step = history.states[history.current_state_id].step_number
        recent_threshold = max(0, current_step - 10)

        checkpoint_data = {
            "history_id": history.history_id,
            "checkpoint_name": checkpoint_name,
            "created_timestamp": datetime.now().isoformat(),
            "base_step": recent_threshold,
            "current_step": current_step,
            "recent_states": {},
            "recent_transformations": {},
        }

        # Include only recent states and transformations
        for state_id, state in history.states.items():
            if state.step_number >= recent_threshold:
                checkpoint_data["recent_states"][state_id] = self._serialize_state(
                    state
                )

        for step_id, step in history.transformations.items():
            from_step = history.states[step.from_state_id].step_number
            if from_step >= recent_threshold:
                checkpoint_data["recent_transformations"][step_id] = (
                    self._serialize_transformation(step)
                )

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, indent=2, default=self._json_serializer)

        return filepath

    def export_proof_sequence(
        self,
        history: EnhancedEGITransformationHistory,
        from_state_id: str,
        to_state_id: str,
        export_format: str = "yaml",
    ) -> Path:
        """Export a specific transformation sequence as a standalone proof."""

        sequence = history.get_transformation_sequence(from_state_id, to_state_id)

        proof_data = {
            "proof_metadata": {
                "from_state": from_state_id,
                "to_state": to_state_id,
                "total_steps": sequence.total_steps,
                "is_valid": sequence.is_valid_path,
                "exported_timestamp": datetime.now().isoformat(),
            },
            "initial_state": self._serialize_state(history.states[from_state_id]),
            "final_state": self._serialize_state(history.states[to_state_id]),
            "transformation_steps": [
                self._serialize_transformation(step) for step in sequence.steps
            ],
            "natural_language_narrative": history.get_natural_language_narrative(
                from_state_id, to_state_id
            ),
            "logical_summary": sequence.logical_summary,
        }

        filename = f"proof_{from_state_id[:8]}_{to_state_id[:8]}.{export_format}"

        if export_format == "yaml":
            filepath = self.yaml_path / filename
            with open(filepath, "w", encoding="utf-8") as f:
                yaml.dump(proof_data, f, default_flow_style=False, allow_unicode=True)
        else:
            filepath = self.json_path / filename
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(proof_data, f, indent=2, default=self._json_serializer)

        return filepath

    def _serialize_history_to_dict(
        self,
        history: EnhancedEGITransformationHistory,
        include_compressed_states: bool = False,
    ) -> Dict[str, Any]:
        """Serialize complete history to dictionary."""

        return {
            "format_version": "1.0",
            "history_metadata": {
                "history_id": history.history_id,
                "created_timestamp": history.created_timestamp.isoformat(),
                "current_state_id": history.current_state_id,
                "current_branch_id": history.current_branch_id,
                "compression_threshold": history.compression_threshold,
            },
            "states": {
                state_id: self._serialize_state(state)
                for state_id, state in history.states.items()
            },
            "transformations": {
                step_id: self._serialize_transformation(step)
                for step_id, step in history.transformations.items()
            },
            "branches": {
                branch_id: {
                    "branch_id": branch.branch_id,
                    "branch_type": branch.branch_type.value,
                    "parent_state_id": branch.parent_state_id,
                    "created_timestamp": branch.created_timestamp.isoformat(),
                    "description": branch.description,
                    "is_active": branch.is_active,
                    "metadata": dict(branch.metadata),
                }
                for branch_id, branch in history.branches.items()
            },
            "domain_model": self._serialize_domain_model(history.domain_model_manager),
            "collaboration_metadata": {
                "session_id": history.collaboration_metadata.session_id,
                "participants": list(history.collaboration_metadata.participants),
                "access_permissions": history.collaboration_metadata.access_permissions,
                "conflict_resolution_strategy": history.collaboration_metadata.conflict_resolution_strategy,
            },
            "navigation_indices": {
                "state_sequence": history.state_sequence,
                "step_sequence": history.step_sequence,
                "state_to_incoming_step": history.state_to_incoming_step,
                "state_to_outgoing_steps": history.state_to_outgoing_steps,
                "step_to_branch": history.step_to_branch,
            },
            "compressed_states": (
                {
                    state_id: compressed_data.hex()
                    for state_id, compressed_data in history.compressed_states.items()
                }
                if include_compressed_states
                else {}
            ),
        }

    def _serialize_state(self, state: StateSnapshot) -> Dict[str, Any]:
        """Serialize a state snapshot."""
        return {
            "state_id": state.state_id,
            "timestamp": state.timestamp.isoformat(),
            "step_number": state.step_number,
            "description": state.description,
            "egi_data": to_dict(state.egi),  # Use existing EGI serialization
            "active_domain_contexts": list(state.active_domain_contexts),
            "linear_forms": state.linear_forms,
            "diagram_metadata": state.diagram_metadata,
            "natural_language_summary": state.natural_language_summary,
            "metadata": dict(state.metadata),
        }

    def _serialize_transformation(self, step: TransformationStep) -> Dict[str, Any]:
        """Serialize a transformation step."""
        return {
            "step_id": step.step_id,
            "rule_name": step.rule_name,
            "from_state_id": step.from_state_id,
            "to_state_id": step.to_state_id,
            "timestamp": step.timestamp.isoformat(),
            "status": step.status.value,
            "logical_provenance": (
                self._serialize_provenance(step.logical_provenance)
                if step.logical_provenance
                else None
            ),
            "affected_domain_contexts": list(step.affected_domain_contexts),
            "natural_language_description": step.natural_language_description,
            "user_annotation": step.user_annotation,
            "author_id": step.author_id,
            "reviewer_ids": list(step.reviewer_ids),
            "approval_status": step.approval_status,
            "context_data": self._serialize_context(step.context),
            "result_data": self._serialize_result(step.result),
            "metadata": dict(step.metadata),
        }

    def _serialize_provenance(self, provenance: LogicalProvenance) -> Dict[str, Any]:
        """Serialize logical provenance."""
        return {
            "rule_citation": provenance.rule_citation,
            "logical_equivalence": provenance.logical_equivalence,
            "semantic_interpretation": provenance.semantic_interpretation,
            "proof_obligations": provenance.proof_obligations,
            "domain_assumptions": provenance.domain_assumptions,
            "ontological_commitments": provenance.ontological_commitments,
        }

    def _serialize_domain_model(
        self, domain_manager: Any
    ) -> Dict[str, Any]:
        """Serialize domain model manager."""
        # Placeholder for future domain model integration
        return {}

    def _serialize_context(self, context) -> Dict[str, Any]:
        """Serialize transformation context."""
        return {
            "target_area": str(context.target_area),
            "selected_subgraph": [str(elem) for elem in context.selected_subgraph],
            "area_polarity": context.area_polarity.value,
            "nesting_depth": context.nesting_depth,
        }

    def _serialize_result(self, result) -> Dict[str, Any]:
        """Serialize transformation result."""
        return {
            "success": result.success,
            "error_message": result.error_message,
            "changes_made": result.changes_made,
            "result_egi_data": (
                to_dict(result.result_egi) if result.result_egi else None
            ),
        }

    def _deserialize_history_from_dict(
        self, data: Dict[str, Any]
    ) -> EnhancedEGITransformationHistory:
        """Deserialize history from dictionary."""
        from egi_io import from_dict
        from enhanced_transformation_history import (
            CollaborationMetadata,
            EnhancedEGITransformationHistory,
        )

        from egi_transformation_history import (
            HistoryBranch,
            HistoryBranchType,
            LogicalProvenance,
            StateSnapshot,
            TransformationStatus,
            TransformationStep,
        )
        from formal_transformation_rules import (
            AreaPolarity,
            TransformationContext,
            TransformationResult,
        )

        # Extract metadata
        metadata = data["history_metadata"]

        # Reconstruct initial EGI from first state
        states_data = data["states"]
        initial_state_id = min(
            states_data.keys(), key=lambda sid: states_data[sid]["step_number"]
        )
        initial_state_data = states_data[initial_state_id]
        initial_egi = from_dict(initial_state_data["egi_data"])

        # Create history instance
        history = EnhancedEGITransformationHistory(
            initial_egi=initial_egi,
            description=f"Loaded session {metadata['history_id']}",
        )

        # Override with loaded metadata
        history.history_id = metadata["history_id"]
        history.created_timestamp = datetime.fromisoformat(
            metadata["created_timestamp"]
        )
        history.current_state_id = metadata["current_state_id"]
        history.current_branch_id = metadata["current_branch_id"]
        history.compression_threshold = metadata.get("compression_threshold", 50)

        # Deserialize states
        history.states = {}
        for state_id, state_data in states_data.items():
            state = self._deserialize_state(state_data)
            history.states[state_id] = state

        # Deserialize transformations
        history.transformations = {}
        for step_id, step_data in data["transformations"].items():
            step = self._deserialize_transformation(step_data)
            history.transformations[step_id] = step

        # Deserialize branches
        history.branches = {}
        for branch_id, branch_data in data["branches"].items():
            branch = self._deserialize_branch(branch_data)
            history.branches[branch_id] = branch

        # Deserialize domain model
        if "domain_model" in data:
            history.domain_model_manager.import_domain_model_data(data["domain_model"])

        # Deserialize collaboration metadata
        if "collaboration_metadata" in data:
            collab_data = data["collaboration_metadata"]
            history.collaboration_metadata = CollaborationMetadata(
                session_id=collab_data["session_id"],
                participants=set(collab_data["participants"]),
                access_permissions=collab_data["access_permissions"],
                conflict_resolution_strategy=collab_data[
                    "conflict_resolution_strategy"
                ],
            )

        # Deserialize navigation indices
        if "navigation_indices" in data:
            indices = data["navigation_indices"]
            history.state_sequence = indices["state_sequence"]
            history.step_sequence = indices["step_sequence"]
            history.state_to_incoming_step = indices["state_to_incoming_step"]
            history.state_to_outgoing_steps = indices["state_to_outgoing_steps"]
            history.step_to_branch = indices["step_to_branch"]

        # Deserialize compressed states
        if "compressed_states" in data:
            history.compressed_states = {
                state_id: bytes.fromhex(hex_data)
                for state_id, hex_data in data["compressed_states"].items()
            }

        return history

    def _add_yaml_annotations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add human-readable annotations for YAML export."""
        annotated = data.copy()

        # Add descriptive comments as special fields
        annotated["_description"] = "EGI Transformation History - Human Readable Export"
        annotated["_format_info"] = {
            "version": data.get("format_version", "1.0"),
            "exported_timestamp": datetime.now().isoformat(),
            "note": "This is a human-readable export. Use JSON format for programmatic loading.",
        }

        return annotated

    def _remove_yaml_annotations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove annotation fields from YAML data."""
        cleaned = data.copy()

        # Remove annotation fields
        for key in list(cleaned.keys()):
            if key.startswith("_"):
                del cleaned[key]

        return cleaned

    def _json_serializer(self, obj):
        """Custom JSON serializer for complex objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, "__dict__"):
            return obj.__dict__
        else:
            return str(obj)

    def get_storage_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored histories."""
        stats = {
            "json_files": len(list(self.json_path.glob("*.json"))),
            "yaml_files": len(list(self.yaml_path.glob("*.yaml"))),
            "compressed_files": len(list(self.compressed_path.glob("*.gz"))),
            "total_size_mb": 0,
        }

        # Calculate total size
        for path in [self.json_path, self.yaml_path, self.compressed_path]:
            for file_path in path.iterdir():
                if file_path.is_file():
                    stats["total_size_mb"] += file_path.stat().st_size / (1024 * 1024)

        stats["total_size_mb"] = round(stats["total_size_mb"], 2)

        return stats

    def _deserialize_state(self, state_data: Dict[str, Any]) -> StateSnapshot:
        """Deserialize a state snapshot."""
        from egi_io import from_dict

        from egi_transformation_history import StateSnapshot

        egi = from_dict(state_data["egi_data"])

        return StateSnapshot(
            state_id=state_data["state_id"],
            egi=egi,
            timestamp=datetime.fromisoformat(state_data["timestamp"]),
            step_number=state_data["step_number"],
            description=state_data["description"],
            active_domain_contexts=set(state_data["active_domain_contexts"]),
            linear_forms=state_data["linear_forms"],
            diagram_metadata=state_data["diagram_metadata"],
            natural_language_summary=state_data["natural_language_summary"],
            metadata=state_data["metadata"],
        )

    def _deserialize_transformation(
        self, step_data: Dict[str, Any]
    ) -> TransformationStep:
        """Deserialize a transformation step."""
        from egi_transformation_history import TransformationStatus, TransformationStep
        from formal_transformation_rules import (
            AreaPolarity,
            TransformationContext,
            TransformationResult,
        )

        # Deserialize logical provenance
        provenance = None
        if step_data["logical_provenance"]:
            provenance = self._deserialize_provenance(step_data["logical_provenance"])

        # Deserialize context and result
        context = self._deserialize_context(step_data["context_data"])
        result = self._deserialize_result(step_data["result_data"])

        return TransformationStep(
            step_id=step_data["step_id"],
            rule_name=step_data["rule_name"],
            from_state_id=step_data["from_state_id"],
            to_state_id=step_data["to_state_id"],
            timestamp=datetime.fromisoformat(step_data["timestamp"]),
            status=TransformationStatus(step_data["status"]),
            logical_provenance=provenance,
            affected_domain_contexts=set(step_data["affected_domain_contexts"]),
            natural_language_description=step_data["natural_language_description"],
            user_annotation=step_data["user_annotation"],
            author_id=step_data["author_id"],
            reviewer_ids=set(step_data["reviewer_ids"]),
            approval_status=step_data["approval_status"],
            context=context,
            result=result,
            metadata=step_data["metadata"],
        )

    def _deserialize_provenance(self, prov_data: Dict[str, Any]) -> LogicalProvenance:
        """Deserialize logical provenance."""
        from egi_transformation_history import LogicalProvenance

        return LogicalProvenance(
            rule_citation=prov_data["rule_citation"],
            logical_equivalence=prov_data["logical_equivalence"],
            semantic_interpretation=prov_data["semantic_interpretation"],
            proof_obligations=prov_data["proof_obligations"],
            domain_assumptions=prov_data["domain_assumptions"],
            ontological_commitments=prov_data["ontological_commitments"],
        )

    def _deserialize_context(
        self, context_data: Dict[str, Any]
    ) -> TransformationContext:
        """Deserialize transformation context."""
        from egi_core_dau import ElementID
        from formal_transformation_rules import AreaPolarity, TransformationContext

        return TransformationContext(
            target_area=ElementID(context_data["target_area"]),
            selected_subgraph=frozenset(
                ElementID(elem) for elem in context_data["selected_subgraph"]
            ),
            area_polarity=AreaPolarity(context_data["area_polarity"]),
            nesting_depth=context_data["nesting_depth"],
        )

    def _deserialize_result(self, result_data: Dict[str, Any]) -> TransformationResult:
        """Deserialize transformation result."""
        from egi_io import from_dict

        from formal_transformation_rules import TransformationResult

        result_egi = None
        if result_data["result_egi_data"]:
            result_egi = from_dict(result_data["result_egi_data"])

        return TransformationResult(
            success=result_data["success"],
            error_message=result_data["error_message"],
            changes_made=result_data["changes_made"],
            result_egi=result_egi,
        )

    def _deserialize_branch(self, branch_data: Dict[str, Any]) -> HistoryBranch:
        """Deserialize transformation branch."""
        return HistoryBranch(
            branch_id=branch_data["branch_id"],
            branch_type=HistoryBranchType(branch_data["branch_type"]),
            parent_state_id=branch_data["parent_state_id"],
            created_timestamp=datetime.fromisoformat(branch_data["created_timestamp"]),
            description=branch_data["description"],
            is_active=branch_data["is_active"],
            metadata=branch_data["metadata"],
        )
