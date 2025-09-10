"""
Immutable EGI transformation architecture implementing diachronic vs synchronic views.
Core principle: We do not change graphs - we create new graphs from existing graphs.
"""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
from abc import ABC, abstractmethod

from egi_core_dau import RelationalGraphWithCuts, ElementID
from frozendict import frozendict


class TransformationRuleType(Enum):
    """EG transformation rule types following Peirce-Dau formalism."""
    INSERTION = "insertion"
    ERASURE = "erasure"
    ITERATION = "iteration"
    DEITERATION = "deiteration"
    DOUBLE_CUT_INSERTION = "double_cut_insertion"
    DOUBLE_CUT_ERASURE = "double_cut_erasure"


class ContextType(Enum):
    """Context types for EGI processing."""
    ERGASTERION = "ergasterion"  # Isolated origination context
    AGON = "agon"               # Integration testing context
    SHEET_OF_ASSERTION = "sheet_of_assertion"  # Final integrated state


@dataclass(frozen=True)
class TransformationStep:
    """Immutable record of a single transformation step."""
    step_id: str
    rule_type: TransformationRuleType
    source_egi_id: str
    target_egi_id: str
    transformation_data: frozendict
    timestamp: datetime
    context_type: ContextType
    logical_justification: str
    spatial_changes: frozendict  # Record of spatial modifications


@dataclass(frozen=True)
class EGISnapshot:
    """Immutable snapshot of an EGI at a specific moment (synchronic view)."""
    egi_id: str
    egi_state: RelationalGraphWithCuts
    timestamp: datetime
    context_type: ContextType
    provenance_step_id: Optional[str]  # The transformation step that created this EGI
    logical_description: str
    spatial_layout: frozendict  # Spatial positioning information


@dataclass
class TransformationSequence:
    """Diachronic view: sequence of transformations showing EGI evolution."""
    sequence_id: str
    initial_egi_id: str
    steps: List[TransformationStep] = field(default_factory=list)
    current_egi_id: Optional[str] = None
    context_type: ContextType = ContextType.ERGASTERION
    created_at: datetime = field(default_factory=datetime.now)
    description: str = ""
    
    def add_step(self, step: TransformationStep) -> None:
        """Add a transformation step to the sequence."""
        self.steps.append(step)
        self.current_egi_id = step.target_egi_id
    
    def get_current_state(self) -> str:
        """Get the current EGI ID after all transformations."""
        return self.current_egi_id or self.initial_egi_id


class ImmutableEGIRepository:
    """Repository for immutable EGI snapshots and transformation history."""
    
    def __init__(self):
        self.egi_snapshots: Dict[str, EGISnapshot] = {}
        self.transformation_steps: Dict[str, TransformationStep] = {}
        self.transformation_sequences: Dict[str, TransformationSequence] = {}
    
    def store_egi_snapshot(self, snapshot: EGISnapshot) -> None:
        """Store an immutable EGI snapshot."""
        self.egi_snapshots[snapshot.egi_id] = snapshot
    
    def store_transformation_step(self, step: TransformationStep) -> None:
        """Store a transformation step."""
        self.transformation_steps[step.step_id] = step
    
    def store_transformation_sequence(self, sequence: TransformationSequence) -> None:
        """Store a transformation sequence."""
        self.transformation_sequences[sequence.sequence_id] = sequence
    
    def get_egi_snapshot(self, egi_id: str) -> Optional[EGISnapshot]:
        """Retrieve an EGI snapshot (synchronic view)."""
        return self.egi_snapshots.get(egi_id)
    
    def get_transformation_sequence(self, sequence_id: str) -> Optional[TransformationSequence]:
        """Retrieve a transformation sequence (diachronic view)."""
        return self.transformation_sequences.get(sequence_id)
    
    def get_egi_history(self, egi_id: str) -> List[TransformationStep]:
        """Get the transformation history leading to an EGI."""
        history = []
        for step in self.transformation_steps.values():
            if step.target_egi_id == egi_id:
                history.append(step)
        return sorted(history, key=lambda s: s.timestamp)


class TransformationRule(ABC):
    """Abstract base class for EG transformation rules."""
    
    @abstractmethod
    def can_apply(self, egi: RelationalGraphWithCuts, context: ContextType) -> bool:
        """Check if this rule can be applied to the given EGI."""
        pass
    
    @abstractmethod
    def apply(self, egi: RelationalGraphWithCuts, 
             transformation_data: Dict[str, Any]) -> RelationalGraphWithCuts:
        """Apply the transformation rule to create a new EGI."""
        pass
    
    @abstractmethod
    def get_rule_type(self) -> TransformationRuleType:
        """Get the type of this transformation rule."""
        pass


class InsertionRule(TransformationRule):
    """Rule for inserting new elements (vertices, edges, cuts) in positive contexts."""
    
    def can_apply(self, egi: RelationalGraphWithCuts, context: ContextType) -> bool:
        """Insertion allowed in positive contexts."""
        return True  # Simplified - would check context polarity
    
    def apply(self, egi: RelationalGraphWithCuts, 
             transformation_data: Dict[str, Any]) -> RelationalGraphWithCuts:
        """Apply insertion transformation."""
        # Create new EGI with inserted element
        # This is a simplified implementation
        return egi  # Would create new EGI with modifications
    
    def get_rule_type(self) -> TransformationRuleType:
        return TransformationRuleType.INSERTION


class ErasureRule(TransformationRule):
    """Rule for erasing elements in negative contexts."""
    
    def can_apply(self, egi: RelationalGraphWithCuts, context: ContextType) -> bool:
        """Erasure allowed in negative contexts."""
        return True  # Simplified - would check context polarity
    
    def apply(self, egi: RelationalGraphWithCuts, 
             transformation_data: Dict[str, Any]) -> RelationalGraphWithCuts:
        """Apply erasure transformation."""
        # Create new EGI with element removed
        return egi  # Would create new EGI with modifications
    
    def get_rule_type(self) -> TransformationRuleType:
        return TransformationRuleType.ERASURE


class ImmutableTransformationEngine:
    """Engine for applying transformation rules to create new EGIs."""
    
    def __init__(self, repository: ImmutableEGIRepository):
        self.repository = repository
        self.rules: Dict[TransformationRuleType, TransformationRule] = {
            TransformationRuleType.INSERTION: InsertionRule(),
            TransformationRuleType.ERASURE: ErasureRule(),
            # Add other rules as needed
        }
    
    def apply_transformation(self, 
                           source_egi_id: str,
                           rule_type: TransformationRuleType,
                           transformation_data: Dict[str, Any],
                           context_type: ContextType,
                           logical_justification: str = "") -> str:
        """Apply a transformation rule to create a new EGI."""
        
        # Get source EGI
        source_snapshot = self.repository.get_egi_snapshot(source_egi_id)
        if not source_snapshot:
            raise ValueError(f"Source EGI {source_egi_id} not found")
        
        # Get transformation rule
        rule = self.rules.get(rule_type)
        if not rule:
            raise ValueError(f"Transformation rule {rule_type} not implemented")
        
        # Check if rule can be applied
        if not rule.can_apply(source_snapshot.egi_state, context_type):
            raise ValueError(f"Rule {rule_type} cannot be applied in context {context_type}")
        
        # Apply transformation to create new EGI
        new_egi_state = rule.apply(source_snapshot.egi_state, transformation_data)
        
        # Create new EGI snapshot
        new_egi_id = str(uuid.uuid4())
        step_id = str(uuid.uuid4())
        timestamp = datetime.now()
        
        new_snapshot = EGISnapshot(
            egi_id=new_egi_id,
            egi_state=new_egi_state,
            timestamp=timestamp,
            context_type=context_type,
            provenance_step_id=step_id,
            logical_description=logical_justification,
            spatial_layout=frozendict(transformation_data.get('spatial_layout', {}))
        )
        
        # Create transformation step
        transformation_step = TransformationStep(
            step_id=step_id,
            rule_type=rule_type,
            source_egi_id=source_egi_id,
            target_egi_id=new_egi_id,
            transformation_data=frozendict(transformation_data),
            timestamp=timestamp,
            context_type=context_type,
            logical_justification=logical_justification,
            spatial_changes=frozendict(transformation_data.get('spatial_changes', {}))
        )
        
        # Store in repository
        self.repository.store_egi_snapshot(new_snapshot)
        self.repository.store_transformation_step(transformation_step)
        
        return new_egi_id


class ErgasterionContext:
    """Isolated context for graph origination and experimentation."""
    
    def __init__(self, repository: ImmutableEGIRepository, 
                 transformation_engine: ImmutableTransformationEngine):
        self.repository = repository
        self.transformation_engine = transformation_engine
        self.active_sequences: Dict[str, TransformationSequence] = {}
    
    def create_origination_sequence(self, initial_egi_id: str, 
                                  description: str = "") -> str:
        """Create a new transformation sequence for graph origination."""
        sequence_id = str(uuid.uuid4())
        sequence = TransformationSequence(
            sequence_id=sequence_id,
            initial_egi_id=initial_egi_id,
            context_type=ContextType.ERGASTERION,
            description=description
        )
        
        self.active_sequences[sequence_id] = sequence
        self.repository.store_transformation_sequence(sequence)
        return sequence_id
    
    def apply_transformation_to_sequence(self, 
                                       sequence_id: str,
                                       rule_type: TransformationRuleType,
                                       transformation_data: Dict[str, Any],
                                       logical_justification: str = "") -> str:
        """Apply a transformation within an origination sequence."""
        sequence = self.active_sequences.get(sequence_id)
        if not sequence:
            raise ValueError(f"Sequence {sequence_id} not found")
        
        current_egi_id = sequence.get_current_state()
        new_egi_id = self.transformation_engine.apply_transformation(
            source_egi_id=current_egi_id,
            rule_type=rule_type,
            transformation_data=transformation_data,
            context_type=ContextType.ERGASTERION,
            logical_justification=logical_justification
        )
        
        # Add step to sequence
        step = self.repository.transformation_steps[
            [s for s in self.repository.transformation_steps.values() 
             if s.target_egi_id == new_egi_id][0].step_id
        ]
        sequence.add_step(step)
        
        return new_egi_id


class AgonContext:
    """Context for testing integration of isolated graphs with universe of discourse."""
    
    def __init__(self, repository: ImmutableEGIRepository,
                 transformation_engine: ImmutableTransformationEngine):
        self.repository = repository
        self.transformation_engine = transformation_engine
        self.universe_of_discourse_egi_id: Optional[str] = None
    
    def set_universe_of_discourse(self, egi_id: str) -> None:
        """Set the current universe of discourse EGI."""
        self.universe_of_discourse_egi_id = egi_id
    
    def test_integration(self, candidate_egi_id: str) -> Dict[str, Any]:
        """Test if a candidate EGI can integrate with the universe of discourse."""
        if not self.universe_of_discourse_egi_id:
            raise ValueError("Universe of discourse not set")
        
        candidate = self.repository.get_egi_snapshot(candidate_egi_id)
        universe = self.repository.get_egi_snapshot(self.universe_of_discourse_egi_id)
        
        if not candidate or not universe:
            raise ValueError("EGI snapshots not found")
        
        # Simplified integration testing
        return {
            "compatible": True,  # Would perform actual compatibility testing
            "conflicts": [],
            "required_adaptations": []
        }


class EndoporeuticGameReplay:
    """System for replaying and analyzing transformation sequences."""
    
    def __init__(self, repository: ImmutableEGIRepository):
        self.repository = repository
    
    def replay_sequence(self, sequence_id: str) -> List[EGISnapshot]:
        """Replay a transformation sequence to show EGI evolution."""
        sequence = self.repository.get_transformation_sequence(sequence_id)
        if not sequence:
            raise ValueError(f"Sequence {sequence_id} not found")
        
        snapshots = []
        
        # Add initial EGI
        initial_snapshot = self.repository.get_egi_snapshot(sequence.initial_egi_id)
        if initial_snapshot:
            snapshots.append(initial_snapshot)
        
        # Add snapshots for each transformation step
        for step in sequence.steps:
            target_snapshot = self.repository.get_egi_snapshot(step.target_egi_id)
            if target_snapshot:
                snapshots.append(target_snapshot)
        
        return snapshots
    
    def analyze_sequence_logic(self, sequence_id: str) -> Dict[str, Any]:
        """Analyze the logical progression of a transformation sequence."""
        sequence = self.repository.get_transformation_sequence(sequence_id)
        if not sequence:
            raise ValueError(f"Sequence {sequence_id} not found")
        
        return {
            "total_steps": len(sequence.steps),
            "rule_types_used": [step.rule_type.value for step in sequence.steps],
            "logical_progression": [step.logical_justification for step in sequence.steps],
            "context_transitions": [step.context_type.value for step in sequence.steps]
        }


# Example usage demonstration
def demonstrate_immutable_architecture():
    """Demonstrate the immutable EGI transformation architecture."""
    
    # Initialize components
    repository = ImmutableEGIRepository()
    engine = ImmutableTransformationEngine(repository)
    ergasterion = ErgasterionContext(repository, engine)
    agon = AgonContext(repository, engine)
    replay_system = EndoporeuticGameReplay(repository)
    
    print("🏗️  Immutable EGI Transformation Architecture Demo")
    print("=" * 60)
    
    # Create initial EGI (simplified)
    from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut
    
    initial_egi = RelationalGraphWithCuts(
        V=frozenset([Vertex("v1")]),
        E=frozenset(),
        nu=frozendict(),
        sheet="sheet",
        Cut=frozenset(),
        area=frozendict({"sheet": frozenset(["v1"])}),
        rel=frozendict()
    )
    
    initial_egi_id = "initial_001"
    initial_snapshot = EGISnapshot(
        egi_id=initial_egi_id,
        egi_state=initial_egi,
        timestamp=datetime.now(),
        context_type=ContextType.ERGASTERION,
        provenance_step_id=None,
        logical_description="Initial EGI with single vertex",
        spatial_layout=frozendict({"v1": (100, 100)})
    )
    
    repository.store_egi_snapshot(initial_snapshot)
    
    # Create origination sequence in Ergasterion
    sequence_id = ergasterion.create_origination_sequence(
        initial_egi_id, "Demonstration of vertex insertion"
    )
    
    print(f"📍 Created origination sequence: {sequence_id}")
    print(f"🔬 Context: Ergasterion (isolated)")
    
    # Apply transformations
    new_egi_id = ergasterion.apply_transformation_to_sequence(
        sequence_id=sequence_id,
        rule_type=TransformationRuleType.INSERTION,
        transformation_data={"element_type": "vertex", "element_id": "v2"},
        logical_justification="Insert second vertex for conjunction"
    )
    
    print(f"✅ Applied insertion transformation: {initial_egi_id} → {new_egi_id}")
    
    # Demonstrate diachronic view
    sequence = repository.get_transformation_sequence(sequence_id)
    print(f"\n📈 Diachronic View (Transformation History):")
    print(f"   Initial EGI: {sequence.initial_egi_id}")
    print(f"   Steps: {len(sequence.steps)}")
    for i, step in enumerate(sequence.steps, 1):
        print(f"   {i}. {step.rule_type.value}: {step.source_egi_id} → {step.target_egi_id}")
        print(f"      Justification: {step.logical_justification}")
    
    # Demonstrate synchronic view
    current_snapshot = repository.get_egi_snapshot(new_egi_id)
    print(f"\n📊 Synchronic View (Current State):")
    print(f"   EGI ID: {current_snapshot.egi_id}")
    print(f"   Context: {current_snapshot.context_type.value}")
    print(f"   Description: {current_snapshot.logical_description}")
    print(f"   Vertices: {len(current_snapshot.egi_state.V)}")
    
    # Demonstrate replay system
    snapshots = replay_system.replay_sequence(sequence_id)
    print(f"\n🎬 Endoporeutic Game Replay:")
    print(f"   Total snapshots: {len(snapshots)}")
    for i, snapshot in enumerate(snapshots):
        print(f"   {i+1}. {snapshot.egi_id}: {snapshot.logical_description}")
    
    analysis = replay_system.analyze_sequence_logic(sequence_id)
    print(f"\n🔍 Sequence Analysis:")
    print(f"   Total steps: {analysis['total_steps']}")
    print(f"   Rules used: {analysis['rule_types_used']}")
    
    return repository, engine, ergasterion, agon, replay_system


if __name__ == "__main__":
    demonstrate_immutable_architecture()
