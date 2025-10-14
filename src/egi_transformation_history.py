"""
EGI Transformation History Data Model

Captures complete transformation sequences with state versioning, enabling:
- Recovery of any historical state
- Viewing transformation sequences between states
- Rollback and branching capabilities
- Provenance tracking for logical reasoning
"""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from frozendict import frozendict

# from domain_ontology_model import DomainModelManager, SemanticAnnotation  # Removed orphaned dependency
from egi_core_dau import ElementID, RelationalGraphWithCuts
from formal_transformation_rules import TransformationContext, TransformationResult


class TransformationStatus(Enum):
    """Status of a transformation step."""

    PENDING = "pending"
    APPLIED = "applied"
    FAILED = "failed"
    REVERTED = "reverted"


class HistoryBranchType(Enum):
    """Type of branching in transformation history."""

    LINEAR = "linear"  # Single sequential path
    EXPLORATION = "exploration"  # Temporary exploration branch
    ALTERNATIVE = "alternative"  # Alternative proof path
    ROLLBACK = "rollback"  # Rollback to earlier state


@dataclass(frozen=True)
class StateSnapshot:
    """Immutable snapshot of an EGI state with domain model integration."""

    state_id: str
    egi: RelationalGraphWithCuts
    timestamp: datetime
    step_number: int
    description: str

    # Domain model and semantic context
    domain_model: Optional[Any] = None  # Placeholder for future domain model integration
    active_domain_contexts: Set[str] = field(default_factory=set)

    # Linear and diagrammatic forms for reference
    linear_forms: Dict[str, str] = field(
        default_factory=dict
    )  # "egif", "clif", "cgif", etc.
    diagram_metadata: Dict[str, Any] = field(
        default_factory=dict
    )  # Layout, styling info

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

    rule_citation: (
        str  # Reference to formal rule (e.g., "Dau 12.3.1", "Peirce Alpha.2")
    )
    logical_equivalence: str  # What the transformation preserves
    semantic_interpretation: str  # Natural language meaning
    proof_obligations: List[str] = field(default_factory=list)  # What must be verified
    domain_assumptions: List[str] = field(
        default_factory=list
    )  # Domain-specific assumptions
    ontological_commitments: List[str] = field(
        default_factory=list
    )  # Ontological commitments made


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

    def __init__(
        self, initial_egi: RelationalGraphWithCuts, description: str = "Initial state"
    ):
        self.history_id = str(uuid.uuid4())
        self.created_timestamp = datetime.now(timezone.utc)

        # Core state storage
        self.states: Dict[str, StateSnapshot] = {}
        self.transformations: Dict[str, TransformationStep] = {}
        self.branches: Dict[str, HistoryBranch] = {}

        # Navigation indices (linear - deprecated but kept for compatibility)
        self.state_sequence: List[str] = []  # DEPRECATED: Use DAG traversal
        self.step_sequence: List[str] = []  # DEPRECATED: Use DAG traversal
        self.current_state_id: str = ""
        self.current_branch_id: str = ""

        # DAG structure
        self.root_state_id: Optional[str] = None  # Root of the DAG
        self.branch_points: Set[str] = set()  # States with multiple outgoing edges

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
            metadata=frozendict({"is_initial": True}),
        )

        # Create main branch
        main_branch_id = str(uuid.uuid4())
        main_branch = HistoryBranch(
            branch_id=main_branch_id,
            branch_type=HistoryBranchType.LINEAR,
            parent_state_id=initial_state_id,
            created_timestamp=self.created_timestamp,
            description="Main transformation sequence",
            metadata=frozendict({"is_main": True}),
        )

        # Store initial state and branch
        self.states[initial_state_id] = initial_state
        self.branches[main_branch_id] = main_branch
        self.state_sequence.append(initial_state_id)
        self.current_state_id = initial_state_id
        self.current_branch_id = main_branch_id
        
        # Set as root of DAG
        self.root_state_id = initial_state_id

        # Initialize indices
        self.state_to_incoming_step[initial_state_id] = None
        self.state_to_outgoing_steps[initial_state_id] = []

    def add_transformation(
        self,
        rule_name: str,
        context: TransformationContext,
        result: TransformationResult,
        user_annotation: Optional[str] = None,
    ) -> str:
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
            metadata=frozendict(result.changes_made),
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
        )

        # Store new state and transformation
        self.states[new_state_id] = new_state
        self.transformations[step_id] = transformation_step

        # Update sequences (deprecated but kept for backward compatibility)
        self.state_sequence.append(new_state_id)
        self.step_sequence.append(step_id)

        # Update DAG structure
        self.state_to_incoming_step[new_state_id] = step_id
        self.state_to_outgoing_steps[new_state_id] = []
        self.state_to_outgoing_steps[self.current_state_id].append(step_id)
        self.step_to_branch[step_id] = self.current_branch_id
        
        # Track branch points (states with multiple outgoing edges)
        if len(self.state_to_outgoing_steps[self.current_state_id]) > 1:
            self.branch_points.add(self.current_state_id)

        # Update current state
        self.current_state_id = new_state_id

        return step_id

    def get_state(self, state_id: str) -> Optional[StateSnapshot]:
        """Get a specific state snapshot."""
        return self.states.get(state_id)

    def get_current_state(self) -> StateSnapshot:
        """Get the current state."""
        return self.states[self.current_state_id]

    def get_transformation_sequence(
        self, from_state_id: str, to_state_id: str
    ) -> TransformationSequence:
        """Get the sequence of transformations between two states using BFS."""
        # Use breadth-first search to find path in DAG
        path = self._find_path_bfs(from_state_id, to_state_id)
        
        if path is None:
            return TransformationSequence(
                from_state_id=from_state_id,
                to_state_id=to_state_id,
                steps=[],
                total_steps=0,
                is_valid_path=False,
                logical_summary="No path found between states",
            )
        
        # Convert state path to transformation steps
        steps = []
        for i in range(len(path) - 1):
            current_state = path[i]
            next_state = path[i + 1]
            
            # Find the step that connects these states
            step_id = self._find_step_between_states(current_state, next_state)
            if step_id:
                steps.append(self.transformations[step_id])
        
        return TransformationSequence(
            from_state_id=from_state_id,
            to_state_id=to_state_id,
            steps=steps,
            total_steps=len(steps),
            is_valid_path=True,
            logical_summary=self._generate_sequence_summary(steps),
        )
    
    def _find_path_bfs(self, from_state_id: str, to_state_id: str) -> Optional[List[str]]:
        """Find shortest path between states using breadth-first search."""
        if from_state_id == to_state_id:
            return [from_state_id]
        
        from collections import deque
        
        queue = deque([(from_state_id, [from_state_id])])
        visited = {from_state_id}
        
        while queue:
            current_state, path = queue.popleft()
            
            # Explore all outgoing edges
            for step_id in self.state_to_outgoing_steps.get(current_state, []):
                step = self.transformations.get(step_id)
                if not step:
                    continue
                
                next_state = step.to_state_id
                
                if next_state == to_state_id:
                    return path + [next_state]
                
                if next_state not in visited:
                    visited.add(next_state)
                    queue.append((next_state, path + [next_state]))
        
        return None  # No path found
    
    def _find_step_between_states(self, from_state: str, to_state: str) -> Optional[str]:
        """Find the step ID that connects two adjacent states."""
        for step_id in self.state_to_outgoing_steps.get(from_state, []):
            step = self.transformations.get(step_id)
            if step and step.to_state_id == to_state:
                return step_id
        return None

    def rollback_to_state(
        self, target_state_id: str, create_branch: bool = True
    ) -> bool:
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
                description=f"Rollback from step {current_state.step_number} to {target_state.step_number}",
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
            description=description,
        )
        self.branches[branch_id] = exploration_branch
        self.current_branch_id = branch_id
        return branch_id

    def get_history_statistics(self) -> Dict[str, Any]:
        """Get statistics about the transformation history."""
        total_states = len(self.states)
        total_transformations = len(self.transformations)
        successful_transformations = sum(
            1
            for t in self.transformations.values()
            if t.status == TransformationStatus.APPLIED
        )
        failed_transformations = sum(
            1
            for t in self.transformations.values()
            if t.status == TransformationStatus.FAILED
        )

        return {
            "history_id": self.history_id,
            "total_states": total_states,
            "total_transformations": total_transformations,
            "successful_transformations": successful_transformations,
            "failed_transformations": failed_transformations,
            "current_step": self.states[self.current_state_id].step_number,
            "total_branches": len(self.branches),
            "created": self.created_timestamp.isoformat(),
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
    
    # ===== DAG-Specific Methods =====
    
    def create_branch_from_state(
        self, 
        source_state_id: str, 
        branch_type: HistoryBranchType = HistoryBranchType.EXPLORATION,
        description: str = "New exploration branch"
    ) -> str:
        """
        Create a new branch from an existing state.
        This allows exploring alternative transformation paths.
        
        Args:
            source_state_id: The state to branch from
            branch_type: Type of branch being created
            description: Description of this branch
            
        Returns:
            The branch_id of the newly created branch
        """
        if source_state_id not in self.states:
            raise ValueError(f"State {source_state_id} not found")
        
        # Create new branch
        branch_id = str(uuid.uuid4())
        branch = HistoryBranch(
            branch_id=branch_id,
            branch_type=branch_type,
            parent_state_id=source_state_id,
            created_timestamp=datetime.now(timezone.utc),
            description=description,
            metadata=frozendict({"source_state": source_state_id}),
        )
        
        self.branches[branch_id] = branch
        
        # Switch to this branch
        self.current_state_id = source_state_id
        self.current_branch_id = branch_id
        
        return branch_id
    
    def get_all_paths_from_root(self, target_state_id: str) -> List[List[str]]:
        """
        Get all paths from root to target state (supports multiple paths in DAG).
        
        Returns:
            List of paths, where each path is a list of state IDs
        """
        if not self.root_state_id:
            return []
        
        if target_state_id == self.root_state_id:
            return [[self.root_state_id]]
        
        all_paths = []
        self._find_all_paths_dfs(self.root_state_id, target_state_id, [], all_paths, set())
        return all_paths
    
    def _find_all_paths_dfs(
        self, 
        current: str, 
        target: str, 
        path: List[str], 
        all_paths: List[List[str]],
        visited: Set[str]
    ):
        """DFS to find all paths from current to target."""
        if current in visited:
            return  # Cycle detection
        
        path = path + [current]
        visited = visited | {current}
        
        if current == target:
            all_paths.append(path)
            return
        
        for step_id in self.state_to_outgoing_steps.get(current, []):
            step = self.transformations.get(step_id)
            if step:
                self._find_all_paths_dfs(step.to_state_id, target, path, all_paths, visited)
    
    def get_child_states(self, state_id: str) -> List[str]:
        """Get all immediate child states (direct descendants in DAG)."""
        child_states = []
        for step_id in self.state_to_outgoing_steps.get(state_id, []):
            step = self.transformations.get(step_id)
            if step:
                child_states.append(step.to_state_id)
        return child_states
    
    def get_all_branches(self) -> List[HistoryBranch]:
        """Get all branches in the history."""
        return list(self.branches.values())
    
    def get_active_branches(self) -> List[HistoryBranch]:
        """Get all active (non-merged) branches."""
        return [b for b in self.branches.values() if b.is_active]
    
    def is_branch_point(self, state_id: str) -> bool:
        """Check if a state is a branch point (has multiple outgoing edges)."""
        return state_id in self.branch_points
    
    def get_branch_points(self) -> List[str]:
        """Get all branch point state IDs."""
        return list(self.branch_points)
    
    def get_dag_statistics(self) -> Dict[str, Any]:
        """Get statistics about the DAG structure."""
        return {
            "total_states": len(self.states),
            "total_transformations": len(self.transformations),
            "total_branches": len(self.branches),
            "active_branches": len(self.get_active_branches()),
            "branch_points": len(self.branch_points),
            "root_state_id": self.root_state_id,
            "current_state_id": self.current_state_id,
            "max_depth": self._calculate_max_depth(),
        }
    
    def _calculate_max_depth(self) -> int:
        """Calculate maximum depth of the DAG from root."""
        if not self.root_state_id:
            return 0
        
        max_depth = 0
        visited = set()
        
        def dfs_depth(state_id: str, depth: int):
            nonlocal max_depth
            if state_id in visited:
                return
            visited.add(state_id)
            max_depth = max(max_depth, depth)
            
            for child in self.get_child_states(state_id):
                dfs_depth(child, depth + 1)
        
        dfs_depth(self.root_state_id, 0)
        return max_depth

    def export_history_data(self) -> Dict[str, Any]:
        """Export complete history data for persistence."""
        return {
            "history_id": self.history_id,
            "created_timestamp": self.created_timestamp.isoformat(),
            "current_state_id": self.current_state_id,
            "current_branch_id": self.current_branch_id,
            "root_state_id": self.root_state_id,
            "branch_points": list(self.branch_points),
            "dag_statistics": self.get_dag_statistics(),
            "states": {
                sid: {
                    "state_id": s.state_id,
                    "step_number": s.step_number,
                    "description": s.description,
                    "timestamp": s.timestamp.isoformat(),
                    "metadata": dict(s.metadata),
                    # EGI would need separate serialization
                }
                for sid, s in self.states.items()
            },
            "transformations": {
                tid: {
                    "step_id": t.step_id,
                    "rule_name": t.rule_name,
                    "from_state_id": t.from_state_id,
                    "to_state_id": t.to_state_id,
                    "timestamp": t.timestamp.isoformat(),
                    "status": t.status.value,
                    "user_annotation": t.user_annotation,
                    "logical_provenance": str(t.logical_provenance) if t.logical_provenance else None,
                    "metadata": dict(t.metadata),
                }
                for tid, t in self.transformations.items()
            },
            "branches": {
                bid: {
                    "branch_id": b.branch_id,
                    "branch_type": b.branch_type.value,
                    "parent_state_id": b.parent_state_id,
                    "created_timestamp": b.created_timestamp.isoformat(),
                    "description": b.description,
                    "is_active": b.is_active,
                    "metadata": dict(b.metadata),
                }
                for bid, b in self.branches.items()
            },
        }


