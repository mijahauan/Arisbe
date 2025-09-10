"""
Comprehensive transformation provenance tracking system.
Maintains complete history and lineage of EGI transformations.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
from collections import defaultdict

from egi_core_dau import RelationalGraphWithCuts, ElementID
from frozendict import frozendict
from immutable_transformation_architecture import (
    TransformationStep, EGISnapshot, TransformationSequence, 
    ImmutableEGIRepository, ContextType, TransformationRuleType
)


class ProvenanceEventType(Enum):
    """Types of provenance events."""
    EGI_CREATION = "egi_creation"
    TRANSFORMATION_APPLICATION = "transformation_application"
    SEQUENCE_INITIATION = "sequence_initiation"
    CONTEXT_TRANSITION = "context_transition"
    INTEGRATION_ATTEMPT = "integration_attempt"
    VALIDATION_CHECK = "validation_check"


@dataclass
class ProvenanceEvent:
    """Individual event in the provenance chain."""
    event_id: str
    event_type: ProvenanceEventType
    timestamp: datetime
    actor: str  # Who/what initiated this event
    source_egi_id: Optional[str]
    target_egi_id: Optional[str]
    transformation_step_id: Optional[str]
    context_type: ContextType
    metadata: Dict[str, Any]
    description: str


@dataclass
class EGILineage:
    """Complete lineage information for an EGI."""
    egi_id: str
    creation_event_id: str
    ancestor_egis: List[str]
    descendant_egis: List[str]
    transformation_path: List[str]  # Sequence of transformation step IDs
    provenance_events: List[str]
    lineage_depth: int
    
    def add_descendant(self, descendant_egi_id: str, transformation_step_id: str) -> None:
        """Add a descendant EGI to this lineage."""
        if descendant_egi_id not in self.descendant_egis:
            self.descendant_egis.append(descendant_egi_id)
            self.transformation_path.append(transformation_step_id)


@dataclass
class TransformationChain:
    """Chain of transformations showing EGI evolution."""
    chain_id: str
    root_egi_id: str
    current_egi_id: str
    transformation_steps: List[str]
    branch_points: List[Tuple[str, List[str]]]  # EGI ID and its branches
    chain_length: int
    
    def add_transformation(self, step_id: str, target_egi_id: str) -> None:
        """Add a transformation to the chain."""
        self.transformation_steps.append(step_id)
        self.current_egi_id = target_egi_id
        self.chain_length += 1


class ProvenanceTracker:
    """Tracks and manages transformation provenance."""
    
    def __init__(self, repository: ImmutableEGIRepository):
        self.repository = repository
        self.provenance_events: Dict[str, ProvenanceEvent] = {}
        self.egi_lineages: Dict[str, EGILineage] = {}
        self.transformation_chains: Dict[str, TransformationChain] = {}
        self.event_index: Dict[ProvenanceEventType, List[str]] = defaultdict(list)
    
    def record_egi_creation(self, egi_id: str, actor: str, context_type: ContextType,
                          description: str = "", metadata: Optional[Dict[str, Any]] = None) -> str:
        """Record the creation of a new EGI."""
        event_id = str(uuid.uuid4())
        
        event = ProvenanceEvent(
            event_id=event_id,
            event_type=ProvenanceEventType.EGI_CREATION,
            timestamp=datetime.now(),
            actor=actor,
            source_egi_id=None,
            target_egi_id=egi_id,
            transformation_step_id=None,
            context_type=context_type,
            metadata=metadata or {},
            description=description or f"Created EGI {egi_id}"
        )
        
        self._store_event(event)
        
        # Create lineage for new EGI
        lineage = EGILineage(
            egi_id=egi_id,
            creation_event_id=event_id,
            ancestor_egis=[],
            descendant_egis=[],
            transformation_path=[],
            provenance_events=[event_id],
            lineage_depth=0
        )
        
        self.egi_lineages[egi_id] = lineage
        
        # Create transformation chain
        chain_id = f"chain_{egi_id}"
        chain = TransformationChain(
            chain_id=chain_id,
            root_egi_id=egi_id,
            current_egi_id=egi_id,
            transformation_steps=[],
            branch_points=[],
            chain_length=0
        )
        
        self.transformation_chains[chain_id] = chain
        
        return event_id
    
    def record_transformation(self, transformation_step: TransformationStep, 
                            actor: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Record a transformation application."""
        event_id = str(uuid.uuid4())
        
        event = ProvenanceEvent(
            event_id=event_id,
            event_type=ProvenanceEventType.TRANSFORMATION_APPLICATION,
            timestamp=transformation_step.timestamp,
            actor=actor,
            source_egi_id=transformation_step.source_egi_id,
            target_egi_id=transformation_step.target_egi_id,
            transformation_step_id=transformation_step.step_id,
            context_type=transformation_step.context_type,
            metadata=metadata or {},
            description=f"Applied {transformation_step.rule_type.value}: {transformation_step.logical_justification}"
        )
        
        self._store_event(event)
        
        # Update lineages
        self._update_lineages_for_transformation(transformation_step, event_id)
        
        # Update transformation chains
        self._update_chains_for_transformation(transformation_step)
        
        return event_id
    
    def record_context_transition(self, egi_id: str, from_context: ContextType, 
                                to_context: ContextType, actor: str, reason: str) -> str:
        """Record a context transition (e.g., Ergasterion to Agon)."""
        event_id = str(uuid.uuid4())
        
        event = ProvenanceEvent(
            event_id=event_id,
            event_type=ProvenanceEventType.CONTEXT_TRANSITION,
            timestamp=datetime.now(),
            actor=actor,
            source_egi_id=egi_id,
            target_egi_id=egi_id,
            transformation_step_id=None,
            context_type=to_context,
            metadata={"from_context": from_context.value, "to_context": to_context.value, "reason": reason},
            description=f"Context transition: {from_context.value} → {to_context.value}"
        )
        
        self._store_event(event)
        
        # Update lineage
        if egi_id in self.egi_lineages:
            self.egi_lineages[egi_id].provenance_events.append(event_id)
        
        return event_id
    
    def get_egi_lineage(self, egi_id: str) -> Optional[EGILineage]:
        """Get complete lineage for an EGI."""
        return self.egi_lineages.get(egi_id)
    
    def get_transformation_chain(self, egi_id: str) -> Optional[TransformationChain]:
        """Get transformation chain containing the EGI."""
        for chain in self.transformation_chains.values():
            if egi_id == chain.root_egi_id or egi_id == chain.current_egi_id:
                return chain
            # Check if EGI is in the transformation path
            for step_id in chain.transformation_steps:
                step = self.repository.transformation_steps.get(step_id)
                if step and (step.source_egi_id == egi_id or step.target_egi_id == egi_id):
                    return chain
        return None
    
    def trace_egi_ancestry(self, egi_id: str) -> List[str]:
        """Trace the complete ancestry of an EGI back to its root."""
        lineage = self.egi_lineages.get(egi_id)
        if not lineage:
            return []
        
        ancestry = []
        current_egi = egi_id
        
        while current_egi:
            ancestry.append(current_egi)
            # Find parent EGI
            parent_egi = None
            for step_id in lineage.transformation_path:
                step = self.repository.transformation_steps.get(step_id)
                if step and step.target_egi_id == current_egi:
                    parent_egi = step.source_egi_id
                    break
            current_egi = parent_egi
            if current_egi and current_egi in self.egi_lineages:
                lineage = self.egi_lineages[current_egi]
            else:
                break
        
        return list(reversed(ancestry))  # Root to current
    
    def find_common_ancestor(self, egi_id_1: str, egi_id_2: str) -> Optional[str]:
        """Find the most recent common ancestor of two EGIs."""
        ancestry_1 = set(self.trace_egi_ancestry(egi_id_1))
        ancestry_2 = set(self.trace_egi_ancestry(egi_id_2))
        
        common_ancestors = ancestry_1 & ancestry_2
        if not common_ancestors:
            return None
        
        # Find the most recent (deepest) common ancestor
        max_depth = -1
        most_recent_ancestor = None
        
        for ancestor_id in common_ancestors:
            lineage = self.egi_lineages.get(ancestor_id)
            if lineage and lineage.lineage_depth > max_depth:
                max_depth = lineage.lineage_depth
                most_recent_ancestor = ancestor_id
        
        return most_recent_ancestor
    
    def get_transformation_history(self, egi_id: str) -> List[TransformationStep]:
        """Get complete transformation history leading to an EGI."""
        lineage = self.egi_lineages.get(egi_id)
        if not lineage:
            return []
        
        history = []
        for step_id in lineage.transformation_path:
            step = self.repository.transformation_steps.get(step_id)
            if step:
                history.append(step)
        
        return sorted(history, key=lambda s: s.timestamp)
    
    def analyze_transformation_patterns(self, egi_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Analyze transformation patterns across EGIs."""
        target_egis = egi_ids or list(self.egi_lineages.keys())
        
        rule_usage = defaultdict(int)
        context_usage = defaultdict(int)
        actor_activity = defaultdict(int)
        transformation_frequency = defaultdict(list)
        
        for egi_id in target_egis:
            history = self.get_transformation_history(egi_id)
            for step in history:
                rule_usage[step.rule_type.value] += 1
                context_usage[step.context_type.value] += 1
                
                # Find actor from provenance events
                for event in self.provenance_events.values():
                    if event.transformation_step_id == step.step_id:
                        actor_activity[event.actor] += 1
                        break
                
                transformation_frequency[egi_id].append(step.timestamp)
        
        return {
            "rule_usage_distribution": dict(rule_usage),
            "context_usage_distribution": dict(context_usage),
            "actor_activity_distribution": dict(actor_activity),
            "total_transformations": sum(rule_usage.values()),
            "unique_transformation_chains": len(self.transformation_chains),
            "average_chain_length": sum(chain.chain_length for chain in self.transformation_chains.values()) / max(len(self.transformation_chains), 1)
        }
    
    def generate_provenance_report(self, egi_id: str) -> Dict[str, Any]:
        """Generate comprehensive provenance report for an EGI."""
        lineage = self.egi_lineages.get(egi_id)
        if not lineage:
            return {"error": f"No lineage found for EGI {egi_id}"}
        
        # Get EGI snapshot
        snapshot = self.repository.get_egi_snapshot(egi_id)
        
        # Get transformation history
        history = self.get_transformation_history(egi_id)
        
        # Get ancestry
        ancestry = self.trace_egi_ancestry(egi_id)
        
        # Get transformation chain
        chain = self.get_transformation_chain(egi_id)
        
        # Get related events
        related_events = []
        for event_id in lineage.provenance_events:
            event = self.provenance_events.get(event_id)
            if event:
                related_events.append({
                    "event_type": event.event_type.value,
                    "timestamp": event.timestamp.isoformat(),
                    "actor": event.actor,
                    "description": event.description
                })
        
        return {
            "egi_id": egi_id,
            "current_state": {
                "vertices": len(snapshot.egi_state.V) if snapshot else 0,
                "edges": len(snapshot.egi_state.E) if snapshot else 0,
                "cuts": len(snapshot.egi_state.Cut) if snapshot else 0,
                "context": snapshot.context_type.value if snapshot else "unknown",
                "description": snapshot.logical_description if snapshot else ""
            },
            "lineage_info": {
                "creation_event": lineage.creation_event_id,
                "lineage_depth": lineage.lineage_depth,
                "ancestor_count": len(lineage.ancestor_egis),
                "descendant_count": len(lineage.descendant_egis)
            },
            "transformation_history": [
                {
                    "rule_type": step.rule_type.value,
                    "timestamp": step.timestamp.isoformat(),
                    "justification": step.logical_justification,
                    "context": step.context_type.value
                }
                for step in history
            ],
            "ancestry_chain": ancestry,
            "transformation_chain_info": {
                "chain_id": chain.chain_id if chain else None,
                "chain_length": chain.chain_length if chain else 0,
                "root_egi": chain.root_egi_id if chain else None
            },
            "provenance_events": related_events
        }
    
    def _store_event(self, event: ProvenanceEvent) -> None:
        """Store a provenance event and update indices."""
        self.provenance_events[event.event_id] = event
        self.event_index[event.event_type].append(event.event_id)
    
    def _update_lineages_for_transformation(self, step: TransformationStep, event_id: str) -> None:
        """Update lineages when a transformation occurs."""
        source_lineage = self.egi_lineages.get(step.source_egi_id)
        if not source_lineage:
            return
        
        # Create lineage for target EGI
        target_lineage = EGILineage(
            egi_id=step.target_egi_id,
            creation_event_id=event_id,
            ancestor_egis=source_lineage.ancestor_egis + [step.source_egi_id],
            descendant_egis=[],
            transformation_path=source_lineage.transformation_path + [step.step_id],
            provenance_events=[event_id],
            lineage_depth=source_lineage.lineage_depth + 1
        )
        
        self.egi_lineages[step.target_egi_id] = target_lineage
        
        # Update source lineage
        source_lineage.add_descendant(step.target_egi_id, step.step_id)
        source_lineage.provenance_events.append(event_id)
    
    def _update_chains_for_transformation(self, step: TransformationStep) -> None:
        """Update transformation chains when a transformation occurs."""
        # Find chain containing source EGI
        source_chain = None
        for chain in self.transformation_chains.values():
            if chain.current_egi_id == step.source_egi_id:
                source_chain = chain
                break
        
        if source_chain:
            source_chain.add_transformation(step.step_id, step.target_egi_id)


def demonstrate_provenance_tracking():
    """Demonstrate comprehensive provenance tracking."""
    
    from egi_transformation_pipeline import EGITransformationPipeline
    
    print("📋 Transformation Provenance Tracking Demonstration")
    print("=" * 55)
    
    # Create pipeline and provenance tracker
    pipeline = EGITransformationPipeline()
    tracker = ProvenanceTracker(pipeline.repository)
    
    # Create initial EGI
    from egi_core_dau import RelationalGraphWithCuts, Vertex
    initial_egi = RelationalGraphWithCuts(
        V=frozenset([Vertex("v1")]),
        E=frozenset(),
        nu=frozendict(),
        sheet="sheet",
        Cut=frozenset(),
        area=frozendict({"sheet": frozenset(["v1"])}),
        rel=frozendict()
    )
    
    initial_egi_id = "provenance_demo_initial"
    from immutable_transformation_architecture import EGISnapshot
    initial_snapshot = EGISnapshot(
        egi_id=initial_egi_id,
        egi_state=initial_egi,
        timestamp=datetime.now(),
        context_type=ContextType.ERGASTERION,
        provenance_step_id=None,
        logical_description="Initial EGI for provenance demo",
        spatial_layout=frozendict()
    )
    
    pipeline.repository.store_egi_snapshot(initial_snapshot)
    
    # Record EGI creation
    creation_event_id = tracker.record_egi_creation(
        egi_id=initial_egi_id,
        actor="demo_user",
        context_type=ContextType.ERGASTERION,
        description="Created initial EGI for provenance demonstration"
    )
    
    print(f"📍 Recorded EGI creation: {creation_event_id[:8]}...")
    
    # Apply transformations and track provenance
    transformations = [
        {
            "rule_type": TransformationRuleType.INSERTION,
            "data": {"element_type": "vertex", "element_id": "v2", "target_area": "sheet"},
            "justification": "Insert second vertex"
        },
        {
            "rule_type": TransformationRuleType.INSERTION,
            "data": {"element_type": "edge", "element_id": "e1", "target_area": "sheet", 
                    "vertex_sequence": ("v1", "v2"), "relation_name": "Connected"},
            "justification": "Connect vertices with edge"
        },
        {
            "rule_type": TransformationRuleType.INSERTION,
            "data": {"element_type": "cut", "element_id": "c1", "target_area": "sheet",
                    "enclosed_elements": frozenset(["v2"])},
            "justification": "Add cut around v2 for negation"
        }
    ]
    
    current_egi_id = initial_egi_id
    
    for i, transform in enumerate(transformations, 1):
        # Apply transformation
        new_egi_id = pipeline.apply_transformation(
            source_egi_id=current_egi_id,
            rule_type=transform["rule_type"],
            transformation_data=transform["data"],
            context_type=ContextType.ERGASTERION,
            logical_justification=transform["justification"]
        )
        
        # Find the transformation step that was created
        step = None
        for s in pipeline.repository.transformation_steps.values():
            if s.target_egi_id == new_egi_id:
                step = s
                break
        
        if step:
            # Record transformation in provenance
            transform_event_id = tracker.record_transformation(
                transformation_step=step,
                actor="demo_user",
                metadata={"transformation_number": i}
            )
            
            print(f"🔄 Transformation {i}: {transform['rule_type'].value} → {new_egi_id[:8]}...")
            print(f"   Event ID: {transform_event_id[:8]}...")
        
        current_egi_id = new_egi_id
    
    # Record context transition
    context_event_id = tracker.record_context_transition(
        egi_id=current_egi_id,
        from_context=ContextType.ERGASTERION,
        to_context=ContextType.AGON,
        actor="demo_user",
        reason="Moving to integration testing"
    )
    
    print(f"🔄 Context transition: Ergasterion → Agon")
    print(f"   Event ID: {context_event_id[:8]}...")
    
    # Generate provenance report
    report = tracker.generate_provenance_report(current_egi_id)
    
    print(f"\n📊 Provenance Report for {current_egi_id[:8]}...")
    print(f"Current State: {report['current_state']['vertices']}V, {report['current_state']['edges']}E, {report['current_state']['cuts']}C")
    print(f"Lineage Depth: {report['lineage_info']['lineage_depth']}")
    print(f"Ancestor Count: {report['lineage_info']['ancestor_count']}")
    
    print(f"\n📈 Transformation History:")
    for i, transform in enumerate(report['transformation_history'], 1):
        print(f"   {i}. {transform['rule_type']}: {transform['justification']}")
        print(f"      Context: {transform['context']}")
    
    print(f"\n🌳 Ancestry Chain:")
    for i, ancestor_id in enumerate(report['ancestry_chain']):
        print(f"   {i+1}. {ancestor_id[:8]}...")
    
    print(f"\n📋 Provenance Events:")
    for event in report['provenance_events']:
        print(f"   • {event['event_type']}: {event['description']}")
        print(f"     Actor: {event['actor']}, Time: {event['timestamp']}")
    
    # Analyze transformation patterns
    patterns = tracker.analyze_transformation_patterns()
    print(f"\n🔍 Transformation Pattern Analysis:")
    print(f"   Total transformations: {patterns['total_transformations']}")
    print(f"   Rule usage: {patterns['rule_usage_distribution']}")
    print(f"   Context usage: {patterns['context_usage_distribution']}")
    print(f"   Actor activity: {patterns['actor_activity_distribution']}")
    print(f"   Unique chains: {patterns['unique_transformation_chains']}")
    print(f"   Average chain length: {patterns['average_chain_length']:.1f}")
    
    return tracker, pipeline


if __name__ == "__main__":
    demonstrate_provenance_tracking()
