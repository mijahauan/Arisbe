"""
Ergasterion: Isolated context for EGI origination and experimentation.
Provides safe environment for graph construction without affecting universe of discourse.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from frozendict import frozendict
from immutable_transformation_architecture import (
    ContextType,
    ImmutableEGIRepository,
    TransformationRuleType,
    TransformationSequence,
)

from egi_core_dau import Cut, Edge, ElementID, RelationalGraphWithCuts, Vertex
from egi_transformation_pipeline import EGITransformationPipeline


class ExperimentStatus(Enum):
    """Status of experiments in Ergasterion."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class HypothesisType(Enum):
    """Types of hypotheses being explored."""

    LOGICAL_STRUCTURE = "logical_structure"
    SEMANTIC_RELATION = "semantic_relation"
    TRANSFORMATION_SEQUENCE = "transformation_sequence"
    PROOF_ATTEMPT = "proof_attempt"


@dataclass
class Experiment:
    """Represents an isolated experiment in Ergasterion."""

    experiment_id: str
    title: str
    description: str
    hypothesis_type: HypothesisType
    initial_egi_id: str
    current_egi_id: str
    transformation_sequence_id: str
    status: ExperimentStatus
    created_at: datetime
    last_modified: datetime
    observations: List[str] = field(default_factory=list)
    conclusions: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)

    def add_observation(self, observation: str) -> None:
        """Add an observation to the experiment."""
        self.observations.append(observation)
        self.last_modified = datetime.now()

    def add_conclusion(self, conclusion: str) -> None:
        """Add a conclusion to the experiment."""
        self.conclusions.append(conclusion)
        self.last_modified = datetime.now()

    def update_status(self, new_status: ExperimentStatus) -> None:
        """Update experiment status."""
        self.status = new_status
        self.last_modified = datetime.now()


@dataclass
class WorkspaceSnapshot:
    """Snapshot of Ergasterion workspace state."""

    snapshot_id: str
    timestamp: datetime
    active_experiments: List[str]
    workspace_description: str
    total_egis_created: int
    total_transformations: int


class ErgasterionWorkspace:
    """Isolated workspace for EGI experimentation."""

    def __init__(self, workspace_id: str, description: str = ""):
        self.workspace_id = workspace_id
        self.description = description
        self.created_at = datetime.now()

        # Isolated repository for this workspace
        self.repository = ImmutableEGIRepository()
        self.transformation_pipeline = EGITransformationPipeline()
        self.transformation_pipeline.repository = self.repository

        # Experiment management
        self.experiments: Dict[str, Experiment] = {}
        self.active_experiment_id: Optional[str] = None

        # Workspace state
        self.snapshots: List[WorkspaceSnapshot] = []
        self.total_egis_created = 0
        self.total_transformations = 0

    def create_experiment(
        self,
        title: str,
        description: str,
        hypothesis_type: HypothesisType,
        initial_egi: Optional[RelationalGraphWithCuts] = None,
    ) -> str:
        """Create a new experiment in the workspace."""
        experiment_id = str(uuid.uuid4())

        # Create initial EGI if not provided
        if initial_egi is None:
            initial_egi = self._create_empty_egi()

        initial_egi_id = f"exp_{experiment_id}_initial"

        # Store initial EGI
        from immutable_transformation_architecture import EGISnapshot

        initial_snapshot = EGISnapshot(
            egi_id=initial_egi_id,
            egi_state=initial_egi,
            timestamp=datetime.now(),
            context_type=ContextType.ERGASTERION,
            provenance_step_id=None,
            logical_description=f"Initial EGI for experiment: {title}",
            spatial_layout=frozendict(),
        )

        self.repository.store_egi_snapshot(initial_snapshot)
        self.total_egis_created += 1

        # Create transformation sequence
        sequence = TransformationSequence(
            sequence_id=f"seq_{experiment_id}",
            initial_egi_id=initial_egi_id,
            context_type=ContextType.ERGASTERION,
            description=f"Transformation sequence for: {title}",
        )

        self.repository.store_transformation_sequence(sequence)

        # Create experiment
        experiment = Experiment(
            experiment_id=experiment_id,
            title=title,
            description=description,
            hypothesis_type=hypothesis_type,
            initial_egi_id=initial_egi_id,
            current_egi_id=initial_egi_id,
            transformation_sequence_id=sequence.sequence_id,
            status=ExperimentStatus.ACTIVE,
            created_at=datetime.now(),
            last_modified=datetime.now(),
        )

        self.experiments[experiment_id] = experiment
        self.active_experiment_id = experiment_id

        return experiment_id

    def apply_transformation_to_experiment(
        self,
        experiment_id: str,
        rule_type: TransformationRuleType,
        transformation_data: Dict[str, Any],
        logical_justification: str = "",
    ) -> str:
        """Apply a transformation within an experiment."""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        if experiment.status != ExperimentStatus.ACTIVE:
            raise ValueError(f"Experiment {experiment_id} is not active")

        # Apply transformation
        new_egi_id = self.transformation_pipeline.apply_transformation(
            source_egi_id=experiment.current_egi_id,
            rule_type=rule_type,
            transformation_data=transformation_data,
            context_type=ContextType.ERGASTERION,
            logical_justification=logical_justification,
        )

        # Update experiment
        experiment.current_egi_id = new_egi_id
        experiment.last_modified = datetime.now()

        # Update sequence
        sequence = self.repository.get_transformation_sequence(
            experiment.transformation_sequence_id
        )
        if sequence:
            # Find the transformation step that was just created
            for step in self.repository.transformation_steps.values():
                if step.target_egi_id == new_egi_id:
                    sequence.add_step(step)
                    break

        self.total_transformations += 1

        # Auto-generate observation
        observation = f"Applied {rule_type.value}: {logical_justification}"
        experiment.add_observation(observation)

        return new_egi_id

    def set_active_experiment(self, experiment_id: str) -> None:
        """Set the active experiment."""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")
        self.active_experiment_id = experiment_id

    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Get an experiment by ID."""
        return self.experiments.get(experiment_id)

    def get_active_experiment(self) -> Optional[Experiment]:
        """Get the currently active experiment."""
        if self.active_experiment_id:
            return self.experiments.get(self.active_experiment_id)
        return None

    def list_experiments(
        self, status_filter: Optional[ExperimentStatus] = None
    ) -> List[Experiment]:
        """List experiments, optionally filtered by status."""
        experiments = list(self.experiments.values())
        if status_filter:
            experiments = [exp for exp in experiments if exp.status == status_filter]
        return sorted(experiments, key=lambda e: e.last_modified, reverse=True)

    def create_workspace_snapshot(self, description: str = "") -> str:
        """Create a snapshot of current workspace state."""
        snapshot_id = str(uuid.uuid4())

        snapshot = WorkspaceSnapshot(
            snapshot_id=snapshot_id,
            timestamp=datetime.now(),
            active_experiments=[
                exp_id
                for exp_id, exp in self.experiments.items()
                if exp.status == ExperimentStatus.ACTIVE
            ],
            workspace_description=description,
            total_egis_created=self.total_egis_created,
            total_transformations=self.total_transformations,
        )

        self.snapshots.append(snapshot)
        return snapshot_id

    def analyze_experiment_patterns(self) -> Dict[str, Any]:
        """Analyze patterns across experiments in this workspace."""
        if not self.experiments:
            return {"no_experiments": True}

        # Analyze hypothesis types
        hypothesis_counts = {}
        for exp in self.experiments.values():
            h_type = exp.hypothesis_type.value
            hypothesis_counts[h_type] = hypothesis_counts.get(h_type, 0) + 1

        # Analyze status distribution
        status_counts = {}
        for exp in self.experiments.values():
            status = exp.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        # Analyze transformation patterns
        transformation_counts = {}
        for sequence in self.repository.transformation_sequences.values():
            for step in sequence.steps:
                rule_type = step.rule_type.value
                transformation_counts[rule_type] = (
                    transformation_counts.get(rule_type, 0) + 1
                )

        return {
            "total_experiments": len(self.experiments),
            "hypothesis_distribution": hypothesis_counts,
            "status_distribution": status_counts,
            "transformation_distribution": transformation_counts,
            "average_observations_per_experiment": sum(
                len(exp.observations) for exp in self.experiments.values()
            )
            / len(self.experiments),
            "total_egis_created": self.total_egis_created,
            "total_transformations": self.total_transformations,
        }

    def _create_empty_egi(self) -> RelationalGraphWithCuts:
        """Create an empty EGI for new experiments."""
        return RelationalGraphWithCuts(
            V=frozenset(),
            E=frozenset(),
            nu=frozendict(),
            sheet="sheet",
            Cut=frozenset(),
            area=frozendict({"sheet": frozenset()}),
            rel=frozendict(),
        )


class ErgasterionManager:
    """Manages multiple Ergasterion workspaces."""

    def __init__(self):
        self.workspaces: Dict[str, ErgasterionWorkspace] = {}
        self.active_workspace_id: Optional[str] = None

    def create_workspace(self, description: str = "") -> str:
        """Create a new Ergasterion workspace."""
        workspace_id = str(uuid.uuid4())
        workspace = ErgasterionWorkspace(workspace_id, description)

        self.workspaces[workspace_id] = workspace
        self.active_workspace_id = workspace_id

        return workspace_id

    def get_workspace(self, workspace_id: str) -> Optional[ErgasterionWorkspace]:
        """Get a workspace by ID."""
        return self.workspaces.get(workspace_id)

    def get_active_workspace(self) -> Optional[ErgasterionWorkspace]:
        """Get the currently active workspace."""
        if self.active_workspace_id:
            return self.workspaces.get(self.active_workspace_id)
        return None

    def set_active_workspace(self, workspace_id: str) -> None:
        """Set the active workspace."""
        if workspace_id not in self.workspaces:
            raise ValueError(f"Workspace {workspace_id} not found")
        self.active_workspace_id = workspace_id

    def list_workspaces(self) -> List[ErgasterionWorkspace]:
        """List all workspaces."""
        return list(self.workspaces.values())

    def analyze_cross_workspace_patterns(self) -> Dict[str, Any]:
        """Analyze patterns across all workspaces."""
        if not self.workspaces:
            return {"no_workspaces": True}

        total_experiments = sum(len(ws.experiments) for ws in self.workspaces.values())
        total_egis = sum(ws.total_egis_created for ws in self.workspaces.values())
        total_transformations = sum(
            ws.total_transformations for ws in self.workspaces.values()
        )

        return {
            "total_workspaces": len(self.workspaces),
            "total_experiments": total_experiments,
            "total_egis_created": total_egis,
            "total_transformations": total_transformations,
            "average_experiments_per_workspace": total_experiments
            / len(self.workspaces),
            "most_active_workspace": max(
                self.workspaces.values(), key=lambda ws: ws.total_transformations
            ).workspace_id,
        }


def demonstrate_ergasterion():
    """Demonstrate Ergasterion isolated context functionality."""

    print("🔬 Ergasterion Isolated Context Demonstration")
    print("=" * 50)

    # Create Ergasterion manager
    manager = ErgasterionManager()

    # Create workspace
    workspace_id = manager.create_workspace("Logic exploration workspace")
    workspace = manager.get_active_workspace()

    print(f"📁 Created workspace: {workspace_id[:8]}...")
    print(f"📝 Description: {workspace.description}")

    # Create first experiment
    exp1_id = workspace.create_experiment(
        title="Basic conjunction exploration",
        description="Explore conjunction through vertex insertion",
        hypothesis_type=HypothesisType.LOGICAL_STRUCTURE,
    )

    print(f"\n🧪 Experiment 1: {workspace.get_experiment(exp1_id).title}")

    # Apply transformations
    workspace.apply_transformation_to_experiment(
        experiment_id=exp1_id,
        rule_type=TransformationRuleType.INSERTION,
        transformation_data={
            "element_type": "vertex",
            "element_id": "v1",
            "target_area": "sheet",
        },
        logical_justification="Insert first vertex for conjunction",
    )

    workspace.apply_transformation_to_experiment(
        experiment_id=exp1_id,
        rule_type=TransformationRuleType.INSERTION,
        transformation_data={
            "element_type": "vertex",
            "element_id": "v2",
            "target_area": "sheet",
        },
        logical_justification="Insert second vertex for conjunction",
    )

    # Add observations and conclusions
    exp1 = workspace.get_experiment(exp1_id)
    exp1.add_observation("Two vertices create spatial conjunction")
    exp1.add_conclusion("Conjunction can be expressed through vertex juxtaposition")

    print(f"   Observations: {len(exp1.observations)}")
    print(f"   Transformations applied: 2")

    # Create second experiment
    exp2_id = workspace.create_experiment(
        title="Negation through cuts",
        description="Explore negation using cut insertion",
        hypothesis_type=HypothesisType.LOGICAL_STRUCTURE,
    )

    print(f"\n🧪 Experiment 2: {workspace.get_experiment(exp2_id).title}")

    # Apply transformations to second experiment
    workspace.apply_transformation_to_experiment(
        experiment_id=exp2_id,
        rule_type=TransformationRuleType.INSERTION,
        transformation_data={
            "element_type": "vertex",
            "element_id": "v3",
            "target_area": "sheet",
        },
        logical_justification="Insert vertex to be negated",
    )

    workspace.apply_transformation_to_experiment(
        experiment_id=exp2_id,
        rule_type=TransformationRuleType.INSERTION,
        transformation_data={
            "element_type": "cut",
            "element_id": "c1",
            "target_area": "sheet",
            "enclosed_elements": frozenset(["v3"]),
        },
        logical_justification="Insert cut around vertex for negation",
    )

    exp2 = workspace.get_experiment(exp2_id)
    exp2.add_observation("Cut around vertex creates negation context")
    exp2.update_status(ExperimentStatus.COMPLETED)

    print(f"   Status: {exp2.status.value}")
    print(f"   Transformations applied: 2")

    # Create workspace snapshot
    snapshot_id = workspace.create_workspace_snapshot("After initial experiments")
    print(f"\n📸 Created workspace snapshot: {snapshot_id[:8]}...")

    # Analyze patterns
    analysis = workspace.analyze_experiment_patterns()
    print(f"\n📊 Workspace Analysis:")
    print(f"   Total experiments: {analysis['total_experiments']}")
    print(f"   Hypothesis types: {analysis['hypothesis_distribution']}")
    print(f"   Status distribution: {analysis['status_distribution']}")
    print(f"   Transformation types: {analysis['transformation_distribution']}")
    print(f"   Total EGIs created: {analysis['total_egis_created']}")

    # Cross-workspace analysis
    cross_analysis = manager.analyze_cross_workspace_patterns()
    print(f"\n🌐 Cross-Workspace Analysis:")
    print(f"   Total workspaces: {cross_analysis['total_workspaces']}")
    print(f"   Total experiments: {cross_analysis['total_experiments']}")
    print(f"   Total transformations: {cross_analysis['total_transformations']}")

    return manager, workspace


if __name__ == "__main__":
    demonstrate_ergasterion()
