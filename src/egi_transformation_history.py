"""
EGI Transformation History Data Model

Captures complete transformation sequences with state versioning, enabling:
- Recovery of any historical state
- Viewing transformation sequences between states
- Rollback and branching capabilities
- Provenance tracking for logical reasoning
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Union, Tuple
from datetime import datetime, timezone
from enum import Enum
import uuid
from abc import ABC, abstractmethod

from egi_core_dau import RelationalGraphWithCuts, ElementID
from formal_transformation_rules import TransformationResult, TransformationContext
from domain_ontology_model import DomainModelManager, SemanticAnnotation
from frozendict import frozendict


class TransformationStatus(Enum):
    """Status of a transformation step."""
    PENDING = "pending"
    APPLIED = "applied"
    FAILED = "failed"
    REVERTED = "reverted"


class HistoryBranchType(Enum):
    """Type of branching in transformation history."""
    LINEAR = "linear"           # Single sequential path
    EXPLORATION = "exploration" # Temporary exploration branch
    ALTERNATIVE = "alternative" # Alternative proof path
    ROLLBACK = "rollback"      # Rollback to earlier state


@dataclass(frozen=True)
class StateSnapshot:
    """Immutable snapshot of an EGI state with domain model integration."""
    state_id: str
    egi: RelationalGraphWithCuts
    timestamp: datetime
    step_number: int
    description: str
    
    # Domain model and semantic context
    domain_model: Optional[DomainModelManager] = None
    active_domain_contexts: Set[str] = field(default_factory=set)
    
    # Linear and diagrammatic forms for reference
    linear_forms: Dict[str, str] = field(default_factory=dict)  # "egif", "clif", "cgif", etc.
    diagram_metadata: Dict[str, Any] = field(default_factory=dict)  # Layout, styling info
    
    # Natural language annotations
    natural_language_summary: Optional[str] = None
    
    metadata: frozendict[str, Any] = field(default_factory=lambda: frozendict())
    
    def __post_init__(self):
        # Ensure hierarchical index is present for efficient operations
        if self.egi.hierarchical_index is None:
            raise ValueError("EGI must have hierarchical index for state snapshots")


@dataclass(frozen=True)
class LogicalProvenance:
    """Captures the logical reasoning and rule citations for a transformation."""
    rule_citation: str  # Reference to formal rule (e.g., "Dau 12.3.1", "Peirce Alpha.2")
    logical_equivalence: str  # What the transformation preserves
    semantic_interpretation: str  # Natural language meaning
    proof_obligations: List[str] = field(default_factory=list)  # What must be verified
    domain_assumptions: List[str] = field(default_factory=list)  # Domain-specific assumptions
    ontological_commitments: List[str] = field(default_factory=list)  # Ontological commitments made


@dataclass(frozen=True)
class TransformationStep:
    """Record of a single transformation step with rich semantic context."""
    step_id: str
    rule_name: str
    from_state_id: str
    to_state_id: str
    context: TransformationContext
    result: TransformationResult
    timestamp: datetime
    status: TransformationStatus
    
    # Semantic and logical context
    logical_provenance: Optional[LogicalProvenance] = None
    affected_domain_contexts: Set[str] = field(default_factory=set)
    natural_language_description: Optional[str] = None
    
    # User annotations
    user_annotation: Optional[str] = None
    
    # Collaboration support
    author_id: Optional[str] = None
    reviewer_ids: Set[str] = field(default_factory=set)
    approval_status: Optional[str] = None  # "pending", "approved", "rejected"
    
    metadata: frozendict[str, Any] = field(default_factory=lambda: frozendict())


@dataclass(frozen=True)
class HistoryBranch:
    """A branch in the transformation history tree."""
    branch_id: str
    branch_type: HistoryBranchType
    parent_state_id: str
    created_timestamp: datetime
    description: str
    is_active: bool = True
    metadata: frozendict[str, Any] = field(default_factory=lambda: frozendict())


@dataclass
class TransformationSequence:
    """A sequence of transformation steps between two states."""
    from_state_id: str
    to_state_id: str
    steps: List[TransformationStep]
    total_steps: int
    is_valid_path: bool
    logical_summary: Optional[str] = None


class EGITransformationHistory:
    """
    Complete transformation history for an EGI with versioning and branching.
    
    Key capabilities:
    - State snapshots at each transformation step
    - Bidirectional transformation tracking
    - Branch management for exploration and alternatives
    - Efficient state recovery and sequence viewing
    - Provenance tracking for logical reasoning
    """
    
    def __init__(self, initial_egi: RelationalGraphWithCuts, description: str = "Initial state"):
        self.history_id = str(uuid.uuid4())
        self.created_timestamp = datetime.now(timezone.utc)
        
        # Core state storage
        self.states: Dict[str, StateSnapshot] = {}
        self.transformations: Dict[str, TransformationStep] = {}
        self.branches: Dict[str, HistoryBranch] = {}
        
        # Navigation indices
        self.state_sequence: List[str] = []  # Linear sequence of state IDs
        self.step_sequence: List[str] = []   # Linear sequence of step IDs
        self.current_state_id: str = ""
        self.current_branch_id: str = ""
        
        # Relationship indices for efficient queries
        self.state_to_incoming_step: Dict[str, Optional[str]] = {}
        self.state_to_outgoing_steps: Dict[str, List[str]] = {}
        self.step_to_branch: Dict[str, str] = {}
        
        # Initialize with initial state
        self._add_initial_state(initial_egi, description)
    
    def _add_initial_state(self, egi: RelationalGraphWithCuts, description: str):
        """Add the initial state and create main branch."""
        # Create initial state
        initial_state_id = str(uuid.uuid4())
        initial_state = StateSnapshot(
            state_id=initial_state_id,
            egi=egi,
            timestamp=self.created_timestamp,
            step_number=0,
            description=description,
            metadata=frozendict({"is_initial": True})
        )
        
        # Create main branch
        main_branch_id = str(uuid.uuid4())
        main_branch = HistoryBranch(
            branch_id=main_branch_id,
            branch_type=HistoryBranchType.LINEAR,
            parent_state_id=initial_state_id,
            created_timestamp=self.created_timestamp,
            description="Main transformation sequence",
            metadata=frozendict({"is_main": True})
        )
        
        # Store initial state and branch
        self.states[initial_state_id] = initial_state
        self.branches[main_branch_id] = main_branch
        self.state_sequence.append(initial_state_id)
        self.current_state_id = initial_state_id
        self.current_branch_id = main_branch_id
        
        # Initialize indices
        self.state_to_incoming_step[initial_state_id] = None
        self.state_to_outgoing_steps[initial_state_id] = []
    
    def add_transformation(self, 
                         rule_name: str,
                         context: TransformationContext,
                         result: TransformationResult,
                         user_annotation: Optional[str] = None,
                         logical_justification: Optional[str] = None) -> str:
        """Add a transformation step and create new state."""
        
        if not result.success:
            # Record failed transformation but don't change state
            step_id = str(uuid.uuid4())
            failed_step = TransformationStep(
                step_id=step_id,
                rule_name=rule_name,
                from_state_id=self.current_state_id,
                to_state_id=self.current_state_id,  # Same state
                context=context,
                result=result,
                timestamp=datetime.now(timezone.utc),
                status=TransformationStatus.FAILED,
                user_annotation=user_annotation,
                logical_justification=logical_justification
            )
            self.transformations[step_id] = failed_step
            return step_id
        
        # Create new state from successful transformation
        new_state_id = str(uuid.uuid4())
        current_step_number = self.states[self.current_state_id].step_number
        
        new_state = StateSnapshot(
            state_id=new_state_id,
            egi=result.result_egi,
            timestamp=datetime.now(timezone.utc),
            step_number=current_step_number + 1,
            description=f"After {rule_name}",
            metadata=frozendict(result.changes_made)
        )
        
        # Create transformation step
        step_id = str(uuid.uuid4())
        transformation_step = TransformationStep(
            step_id=step_id,
            rule_name=rule_name,
            from_state_id=self.current_state_id,
            to_state_id=new_state_id,
            context=context,
            result=result,
            timestamp=datetime.now(timezone.utc),
            status=TransformationStatus.APPLIED,
            user_annotation=user_annotation,
            logical_justification=logical_justification
        )
        
        # Store new state and transformation
        self.states[new_state_id] = new_state
        self.transformations[step_id] = transformation_step
        
        # Update sequences and indices
        self.state_sequence.append(new_state_id)
        self.step_sequence.append(step_id)
        
        # Update relationship indices
        self.state_to_incoming_step[new_state_id] = step_id
        self.state_to_outgoing_steps[new_state_id] = []
        self.state_to_outgoing_steps[self.current_state_id].append(step_id)
        self.step_to_branch[step_id] = self.current_branch_id
        
        # Update current state
        self.current_state_id = new_state_id
        
        return step_id
    
    def get_state(self, state_id: str) -> Optional[StateSnapshot]:
        """Get a specific state snapshot."""
        return self.states.get(state_id)
    
    def get_current_state(self) -> StateSnapshot:
        """Get the current state."""
        return self.states[self.current_state_id]
    
    def get_transformation_sequence(self, from_state_id: str, to_state_id: str) -> TransformationSequence:
        """Get the sequence of transformations between two states."""
        # Find path between states (simplified - assumes linear path for now)
        from_step_num = self.states[from_state_id].step_number
        to_step_num = self.states[to_state_id].step_number
        
        if from_step_num > to_step_num:
            # Reverse direction not yet implemented
            return TransformationSequence(
                from_state_id=from_state_id,
                to_state_id=to_state_id,
                steps=[],
                total_steps=0,
                is_valid_path=False,
                logical_summary="Reverse path not implemented"
            )
        
        # Get steps in sequence
        steps = []
        current_state = from_state_id
        
        while current_state != to_state_id:
            outgoing_steps = self.state_to_outgoing_steps.get(current_state, [])
            if not outgoing_steps:
                break
            
            # Take first outgoing step (linear assumption)
            step_id = outgoing_steps[0]
            step = self.transformations[step_id]
            steps.append(step)
            current_state = step.to_state_id
        
        is_valid = (current_state == to_state_id)
        
        return TransformationSequence(
            from_state_id=from_state_id,
            to_state_id=to_state_id,
            steps=steps,
            total_steps=len(steps),
            is_valid_path=is_valid,
            logical_summary=self._generate_sequence_summary(steps) if is_valid else None
        )
    
    def rollback_to_state(self, target_state_id: str, create_branch: bool = True) -> bool:
        """Rollback to a previous state, optionally creating a branch."""
        if target_state_id not in self.states:
            return False
        
        target_state = self.states[target_state_id]
        current_state = self.states[self.current_state_id]
        
        if target_state.step_number >= current_state.step_number:
            return False  # Can't rollback to future state
        
        if create_branch:
            # Create rollback branch
            branch_id = str(uuid.uuid4())
            rollback_branch = HistoryBranch(
                branch_id=branch_id,
                branch_type=HistoryBranchType.ROLLBACK,
                parent_state_id=target_state_id,
                created_timestamp=datetime.now(timezone.utc),
                description=f"Rollback from step {current_state.step_number} to {target_state.step_number}"
            )
            self.branches[branch_id] = rollback_branch
            self.current_branch_id = branch_id
        
        # Update current state
        self.current_state_id = target_state_id
        return True
    
    def create_exploration_branch(self, description: str) -> str:
        """Create a new exploration branch from current state."""
        branch_id = str(uuid.uuid4())
        exploration_branch = HistoryBranch(
            branch_id=branch_id,
            branch_type=HistoryBranchType.EXPLORATION,
            parent_state_id=self.current_state_id,
            created_timestamp=datetime.now(timezone.utc),
            description=description
        )
        self.branches[branch_id] = exploration_branch
        self.current_branch_id = branch_id
        return branch_id
    
    def get_history_statistics(self) -> Dict[str, Any]:
        """Get statistics about the transformation history."""
        total_states = len(self.states)
        total_transformations = len(self.transformations)
        successful_transformations = sum(1 for t in self.transformations.values() 
                                       if t.status == TransformationStatus.APPLIED)
        failed_transformations = sum(1 for t in self.transformations.values() 
                                   if t.status == TransformationStatus.FAILED)
        
        return {
            "history_id": self.history_id,
            "total_states": total_states,
            "total_transformations": total_transformations,
            "successful_transformations": successful_transformations,
            "failed_transformations": failed_transformations,
            "current_step": self.states[self.current_state_id].step_number,
            "total_branches": len(self.branches),
            "created": self.created_timestamp.isoformat()
        }
    
    def _generate_sequence_summary(self, steps: List[TransformationStep]) -> str:
        """Generate a logical summary of a transformation sequence."""
        if not steps:
            return "No transformations"
        
        rule_counts = {}
        for step in steps:
            rule_counts[step.rule_name] = rule_counts.get(step.rule_name, 0) + 1
        
        summary_parts = []
        for rule, count in rule_counts.items():
            if count == 1:
                summary_parts.append(rule)
            else:
                summary_parts.append(f"{rule} (×{count})")
        
        return " → ".join(summary_parts)
    
    def export_history_data(self) -> Dict[str, Any]:
        """Export complete history data for persistence."""
        return {
            "history_id": self.history_id,
            "created_timestamp": self.created_timestamp.isoformat(),
            "current_state_id": self.current_state_id,
            "current_branch_id": self.current_branch_id,
            "states": {sid: {
                "state_id": s.state_id,
                "step_number": s.step_number,
                "description": s.description,
                "timestamp": s.timestamp.isoformat(),
                "metadata": dict(s.metadata),
                # EGI would need separate serialization
            } for sid, s in self.states.items()},
            "transformations": {tid: {
                "step_id": t.step_id,
                "rule_name": t.rule_name,
                "from_state_id": t.from_state_id,
                "to_state_id": t.to_state_id,
                "timestamp": t.timestamp.isoformat(),
                "status": t.status.value,
                "user_annotation": t.user_annotation,
                "logical_justification": t.logical_justification,
                "metadata": dict(t.metadata)
            } for tid, t in self.transformations.items()},
            "branches": {bid: {
                "branch_id": b.branch_id,
                "branch_type": b.branch_type.value,
                "parent_state_id": b.parent_state_id,
                "created_timestamp": b.created_timestamp.isoformat(),
                "description": b.description,
                "is_active": b.is_active,
                "metadata": dict(b.metadata)
            } for bid, b in self.branches.items()}
        }


class HistoryViewer:
    """Utility class for viewing and analyzing transformation histories."""
    
    def __init__(self, history: EGITransformationHistory):
        self.history = history
    
    def get_state_diff(self, state_id_1: str, state_id_2: str) -> Dict[str, Any]:
        """Get structural differences between two states."""
        state1 = self.history.get_state(state_id_1)
        state2 = self.history.get_state(state_id_2)
        
        if not state1 or not state2:
            return {"error": "Invalid state IDs"}
        
        # Compare EGI structures
        egi1, egi2 = state1.egi, state2.egi
        
        return {
            "vertices_added": len(egi2.V) - len(egi1.V),
            "edges_added": len(egi2.E) - len(egi1.E),
            "cuts_added": len(egi2.Cut) - len(egi1.Cut),
            "step_difference": state2.step_number - state1.step_number,
            "time_difference": (state2.timestamp - state1.timestamp).total_seconds()
        }
    
    def get_transformation_tree(self) -> Dict[str, Any]:
        """Get a tree representation of the transformation history."""
        # Simplified tree structure for now
        return {
            "root_state": self.history.state_sequence[0] if self.history.state_sequence else None,
            "linear_sequence": self.history.state_sequence,
            "branches": list(self.history.branches.keys()),
            "total_states": len(self.history.states)
        }
