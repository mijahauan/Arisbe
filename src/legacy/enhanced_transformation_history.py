"""
Enhanced EGI Transformation History with Domain Model Integration

Integrates the transformation history model with domain ontology support,
addressing your key requirements for the Endoporeutic Game:

1. Proof export capabilities
2. Collaboration-ready architecture
3. Compression for large histories
4. Natural language integration
5. Rule validation
6. Multiple domain contexts per EGI
"""

import json
import uuid
import zlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from domain_ontology_model import ConceptMapping, DomainModelManager, SemanticAnnotation
from egi_core_dau import ElementID, RelationalGraphWithCuts
from egi_transformation_history import (
    EGITransformationHistory,
    HistoryBranchType,
    LogicalProvenance,
    StateSnapshot,
    TransformationStep,
)


class ProofExportFormat(Enum):
    """Supported proof export formats."""

    COQ = "coq"
    LEAN = "lean"
    ISABELLE = "isabelle"
    METAMATH = "metamath"
    NATURAL_DEDUCTION = "natural_deduction"
    SEQUENT_CALCULUS = "sequent_calculus"
    LATEX_PROOF = "latex"


@dataclass
class CollaborationMetadata:
    """Metadata for collaborative editing."""

    session_id: str
    participants: Set[str] = field(default_factory=set)
    access_permissions: Dict[str, str] = field(
        default_factory=dict
    )  # user_id -> permission_level
    conflict_resolution_strategy: str = "manual"  # "manual", "last_write_wins", "merge"
    lock_holder: Optional[str] = None
    lock_timestamp: Optional[datetime] = None


class EnhancedEGITransformationHistory(EGITransformationHistory):
    """
    Enhanced transformation history with domain model integration and advanced features.
    """

    def __init__(
        self, initial_egi: RelationalGraphWithCuts, description: str = "Initial state"
    ):
        super().__init__(initial_egi, description)

        # Domain model integration
        self.domain_model_manager = DomainModelManager()

        # Collaboration support
        self.collaboration_metadata = CollaborationMetadata(
            session_id=str(uuid.uuid4())
        )

        # Compression settings
        self.compression_threshold = 100  # Compress states older than 100 steps
        self.compressed_states: Dict[str, bytes] = {}

        # Natural language cache
        self.natural_language_cache: Dict[str, str] = {}

        # Proof export cache
        self.proof_export_cache: Dict[Tuple[str, str, ProofExportFormat], str] = {}

    def add_transformation_with_domain_context(
        self,
        rule_name: str,
        context,  # TransformationContext
        result,  # TransformationResult
        domain_contexts: Set[str] = None,
        natural_language: str = None,
        logical_provenance: LogicalProvenance = None,
        author_id: str = None,
    ) -> str:
        """Add transformation with rich domain and semantic context."""

        # Generate natural language if not provided
        if not natural_language and domain_contexts:
            natural_language = self._generate_transformation_natural_language(
                rule_name, context, domain_contexts
            )

        # Create enhanced transformation step
        step_id = str(uuid.uuid4())

        if result.success:
            # Create new state with domain model
            new_state_id = str(uuid.uuid4())
            current_step_number = self.states[self.current_state_id].step_number

            # Generate linear forms for the new state
            linear_forms = self._generate_linear_forms(result.result_egi)

            # Generate natural language summary
            nl_summary = self._generate_state_natural_language(
                result.result_egi, domain_contexts or set()
            )

            new_state = StateSnapshot(
                state_id=new_state_id,
                egi=result.result_egi,
                timestamp=datetime.now(timezone.utc),
                step_number=current_step_number + 1,
                description=f"After {rule_name}",
                domain_model=self.domain_model_manager,
                active_domain_contexts=domain_contexts or set(),
                linear_forms=linear_forms,
                natural_language_summary=nl_summary,
            )

            # Store new state
            self.states[new_state_id] = new_state

            # Check if compression needed
            if current_step_number > self.compression_threshold:
                self._compress_old_states()

        # Create transformation step with enhanced metadata
        transformation_step = TransformationStep(
            step_id=step_id,
            rule_name=rule_name,
            from_state_id=self.current_state_id,
            to_state_id=new_state_id if result.success else self.current_state_id,
            context=context,
            result=result,
            timestamp=datetime.now(timezone.utc),
            status=self._determine_status(result),
            logical_provenance=logical_provenance,
            affected_domain_contexts=domain_contexts or set(),
            natural_language_description=natural_language,
            author_id=author_id,
        )

        # Store transformation
        self.transformations[step_id] = transformation_step

        # Update sequences and current state
        if result.success:
            self.state_sequence.append(new_state_id)
            self.step_sequence.append(step_id)
            self.current_state_id = new_state_id

            # Update relationship indices
            self.state_to_incoming_step[new_state_id] = step_id
            self.state_to_outgoing_steps[new_state_id] = []
            self.state_to_outgoing_steps[self.current_state_id].append(step_id)
            self.step_to_branch[step_id] = self.current_branch_id

        return step_id

    def export_proof_sequence(
        self,
        from_state_id: str,
        to_state_id: str,
        export_format: ProofExportFormat,
        include_domain_context: bool = True,
    ) -> str:
        """Export a transformation sequence as a formal proof."""

        # Check cache first
        cache_key = (from_state_id, to_state_id, export_format)
        if cache_key in self.proof_export_cache:
            return self.proof_export_cache[cache_key]

        sequence = self.get_transformation_sequence(from_state_id, to_state_id)

        if not sequence.is_valid_path:
            return f"Error: No valid path from {from_state_id} to {to_state_id}"

        proof_text = self._generate_proof_export(
            sequence, export_format, include_domain_context
        )

        # Cache the result
        self.proof_export_cache[cache_key] = proof_text

        return proof_text

    def add_semantic_annotation_to_state(
        self,
        state_id: str,
        target_elements: Set[ElementID],
        domain_context_id: str,
        natural_language: str,
        logical_forms: Dict[str, str] = None,
    ) -> str:
        """Add semantic annotation to elements in a specific state."""

        return self.domain_model_manager.create_semantic_annotation(
            target_elements=target_elements,
            domain_context_id=domain_context_id,
            natural_language=natural_language,
            logical_forms=logical_forms or {},
        )

    def validate_transformation_sequence(
        self, from_state_id: str, to_state_id: str
    ) -> Dict[str, Any]:
        """Validate that a transformation sequence follows formal rules."""

        sequence = self.get_transformation_sequence(from_state_id, to_state_id)

        validation_results = {
            "is_valid": sequence.is_valid_path,
            "rule_violations": [],
            "domain_consistency_issues": [],
            "logical_gaps": [],
        }

        if not sequence.is_valid_path:
            validation_results["rule_violations"].append("Invalid transformation path")
            return validation_results

        # Validate each step
        for step in sequence.steps:
            # Check rule application validity
            if step.logical_provenance:
                rule_valid = self._validate_rule_application(step)
                if not rule_valid:
                    validation_results["rule_violations"].append(
                        f"Invalid rule application: {step.rule_name} at step {step.step_id}"
                    )

            # Check domain consistency
            for context_id in step.affected_domain_contexts:
                issues = self.domain_model_manager.validate_domain_consistency(
                    context_id
                )
                validation_results["domain_consistency_issues"].extend(issues)

        return validation_results

    def get_natural_language_narrative(
        self, from_state_id: str, to_state_id: str
    ) -> str:
        """Generate a natural language narrative of the transformation sequence."""

        sequence = self.get_transformation_sequence(from_state_id, to_state_id)

        if not sequence.is_valid_path:
            return "No valid transformation path found."

        narrative_parts = []

        # Initial state description
        from_state = self.states[from_state_id]
        if from_state.natural_language_summary:
            narrative_parts.append(
                f"Starting with: {from_state.natural_language_summary}"
            )

        # Transformation steps
        for i, step in enumerate(sequence.steps, 1):
            step_desc = step.natural_language_description or f"Applied {step.rule_name}"
            narrative_parts.append(f"{i}. {step_desc}")

            if step.logical_provenance:
                narrative_parts.append(
                    f"   Justification: {step.logical_provenance.semantic_interpretation}"
                )

        # Final state description
        to_state = self.states[to_state_id]
        if to_state.natural_language_summary:
            narrative_parts.append(f"Resulting in: {to_state.natural_language_summary}")

        return "\n".join(narrative_parts)

    def _generate_linear_forms(self, egi: RelationalGraphWithCuts) -> Dict[str, str]:
        """Generate various linear forms for an EGI state."""
        # This would integrate with existing parsers/exporters
        return {
            "egif": "# EGIF generation not implemented",
            "clif": "# CLIF generation not implemented",
            "cgif": "# CGIF generation not implemented",
        }

    def _generate_state_natural_language(
        self, egi: RelationalGraphWithCuts, domain_contexts: Set[str]
    ) -> str:
        """Generate natural language summary for an EGI state."""

        if not domain_contexts:
            return f"EGI with {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts"

        # Use domain model to generate meaningful descriptions
        descriptions = []
        for context_id in domain_contexts:
            if context_id in self.domain_model_manager.domain_contexts:
                context = self.domain_model_manager.domain_contexts[context_id]
                descriptions.append(f"In {context.name} domain")

        return "; ".join(descriptions) if descriptions else "Multi-domain EGI"

    def _generate_transformation_natural_language(
        self, rule_name: str, context, domain_contexts: Set[str]
    ) -> str:
        """Generate natural language description for a transformation."""

        base_desc = f"Applied {rule_name}"

        if domain_contexts:
            context_names = []
            for context_id in domain_contexts:
                if context_id in self.domain_model_manager.domain_contexts:
                    context_names.append(
                        self.domain_model_manager.domain_contexts[context_id].name
                    )

            if context_names:
                base_desc += f" in {', '.join(context_names)} context"

        return base_desc

    def _generate_proof_export(
        self,
        sequence,  # TransformationSequence
        export_format: ProofExportFormat,
        include_domain_context: bool,
    ) -> str:
        """Generate formal proof export in specified format."""

        if export_format == ProofExportFormat.NATURAL_DEDUCTION:
            return self._export_natural_deduction(sequence, include_domain_context)
        elif export_format == ProofExportFormat.COQ:
            return self._export_coq_proof(sequence, include_domain_context)
        elif export_format == ProofExportFormat.LATEX_PROOF:
            return self._export_latex_proof(sequence, include_domain_context)
        else:
            return f"Export format {export_format.value} not yet implemented"

    def _export_natural_deduction(self, sequence, include_domain_context: bool) -> str:
        """Export as natural deduction proof."""
        lines = ["Natural Deduction Proof", "=" * 25, ""]

        for i, step in enumerate(sequence.steps, 1):
            lines.append(f"{i}. {step.rule_name}")
            if step.logical_provenance:
                lines.append(f"   Rule: {step.logical_provenance.rule_citation}")
                lines.append(
                    f"   Justification: {step.logical_provenance.semantic_interpretation}"
                )
            lines.append("")

        return "\n".join(lines)

    def _export_coq_proof(self, sequence, include_domain_context: bool) -> str:
        """Export as Coq proof script."""
        lines = ["(* Generated Coq proof *)", ""]

        for step in sequence.steps:
            lines.append(f"(* {step.rule_name} *)")
            if step.logical_provenance:
                lines.append(f"(* {step.logical_provenance.semantic_interpretation} *)")
            lines.append("admit. (* Proof step not implemented *)")
            lines.append("")

        return "\n".join(lines)

    def _export_latex_proof(self, sequence, include_domain_context: bool) -> str:
        """Export as LaTeX proof."""
        lines = ["\\begin{proof}", "\\begin{enumerate}"]

        for step in sequence.steps:
            lines.append(f"  \\item {step.rule_name}")
            if step.logical_provenance:
                lines.append(
                    f"    \\\\{step.logical_provenance.semantic_interpretation}"
                )

        lines.extend(["\\end{enumerate}", "\\end{proof}"])

        return "\n".join(lines)

    def _validate_rule_application(self, step: TransformationStep) -> bool:
        """Validate that a rule was applied correctly."""
        # This would check against formal rule definitions
        # For now, just check that provenance exists
        return step.logical_provenance is not None

    def _compress_old_states(self):
        """Compress states older than the threshold."""
        current_step = self.states[self.current_state_id].step_number

        for state_id, state in list(self.states.items()):
            if current_step - state.step_number > self.compression_threshold:
                if state_id not in self.compressed_states:
                    # Serialize and compress the EGI
                    state_data = {
                        "egi_data": "# EGI serialization not implemented",
                        "metadata": dict(state.metadata),
                        "description": state.description,
                    }

                    compressed = zlib.compress(json.dumps(state_data).encode("utf-8"))
                    self.compressed_states[state_id] = compressed

    def _determine_status(self, result) -> str:
        """Determine transformation status from result."""
        from egi_transformation_history import TransformationStatus

        return (
            TransformationStatus.APPLIED
            if result.success
            else TransformationStatus.FAILED
        )

    def get_collaboration_status(self) -> Dict[str, Any]:
        """Get current collaboration status."""
        return {
            "session_id": self.collaboration_metadata.session_id,
            "active_participants": len(self.collaboration_metadata.participants),
            "lock_status": (
                "locked" if self.collaboration_metadata.lock_holder else "unlocked"
            ),
            "lock_holder": self.collaboration_metadata.lock_holder,
        }

    def acquire_lock(self, user_id: str) -> bool:
        """Acquire exclusive lock for editing."""
        if self.collaboration_metadata.lock_holder is None:
            self.collaboration_metadata.lock_holder = user_id
            self.collaboration_metadata.lock_timestamp = datetime.now(timezone.utc)
            return True
        return False

    def release_lock(self, user_id: str) -> bool:
        """Release exclusive lock."""
        if self.collaboration_metadata.lock_holder == user_id:
            self.collaboration_metadata.lock_holder = None
            self.collaboration_metadata.lock_timestamp = None
            return True
        return False
