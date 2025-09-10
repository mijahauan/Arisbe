"""
Diachronic and Synchronic view system for EGI transformations.
Separates historical transformation sequences from static EGI states.
"""

from typing import Dict, List, Optional, Set, Tuple, Any, Iterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

from egi_core_dau import RelationalGraphWithCuts, ElementID
from frozendict import frozendict
from immutable_transformation_architecture import (
    EGISnapshot, TransformationStep, TransformationSequence, 
    ImmutableEGIRepository, ContextType, TransformationRuleType
)


class ViewType(Enum):
    """Types of views for EGI analysis."""
    SYNCHRONIC = "synchronic"    # Static view of EGI at specific moment
    DIACHRONIC = "diachronic"    # Historical view of transformation sequence


@dataclass
class SynchronicView:
    """Static view of an EGI at a specific moment in time."""
    view_id: str
    egi_snapshot: EGISnapshot
    logical_analysis: Dict[str, Any]
    spatial_layout: Dict[str, Tuple[float, float]]
    semantic_description: str
    
    def get_vertex_count(self) -> int:
        """Get number of vertices in this EGI state."""
        return len(self.egi_snapshot.egi_state.V)
    
    def get_edge_count(self) -> int:
        """Get number of edges in this EGI state."""
        return len(self.egi_snapshot.egi_state.E)
    
    def get_cut_count(self) -> int:
        """Get number of cuts in this EGI state."""
        return len(self.egi_snapshot.egi_state.Cut)
    
    def get_nesting_depth(self) -> int:
        """Calculate maximum nesting depth of cuts."""
        # Simplified calculation - would need proper hierarchy analysis
        return len(self.egi_snapshot.egi_state.Cut)
    
    def analyze_logical_structure(self) -> Dict[str, Any]:
        """Analyze the logical structure of this EGI state."""
        return {
            "vertices": self.get_vertex_count(),
            "edges": self.get_edge_count(),
            "cuts": self.get_cut_count(),
            "max_nesting_depth": self.get_nesting_depth(),
            "areas": len(self.egi_snapshot.egi_state.area),
            "relations": len(self.egi_snapshot.egi_state.rel),
            "context_type": self.egi_snapshot.context_type.value,
            "timestamp": self.egi_snapshot.timestamp.isoformat()
        }


@dataclass
class DiachronicView:
    """Historical view of EGI evolution through transformation sequence."""
    view_id: str
    transformation_sequence: TransformationSequence
    snapshots: List[EGISnapshot]
    transformation_analysis: Dict[str, Any]
    logical_progression: List[str]
    
    def get_sequence_length(self) -> int:
        """Get number of transformation steps in sequence."""
        return len(self.transformation_sequence.steps)
    
    def get_rule_distribution(self) -> Dict[str, int]:
        """Get distribution of transformation rules used."""
        rule_counts = {}
        for step in self.transformation_sequence.steps:
            rule_type = step.rule_type.value
            rule_counts[rule_type] = rule_counts.get(rule_type, 0) + 1
        return rule_counts
    
    def get_temporal_span(self) -> Tuple[datetime, datetime]:
        """Get temporal span of the transformation sequence."""
        if not self.snapshots:
            return (self.transformation_sequence.created_at, self.transformation_sequence.created_at)
        
        start_time = min(snapshot.timestamp for snapshot in self.snapshots)
        end_time = max(snapshot.timestamp for snapshot in self.snapshots)
        return (start_time, end_time)
    
    def analyze_transformation_progression(self) -> Dict[str, Any]:
        """Analyze the progression of transformations."""
        if not self.transformation_sequence.steps:
            return {"empty_sequence": True}
        
        start_time, end_time = self.get_temporal_span()
        duration = (end_time - start_time).total_seconds()
        
        return {
            "total_steps": self.get_sequence_length(),
            "rule_distribution": self.get_rule_distribution(),
            "temporal_span_seconds": duration,
            "context_type": self.transformation_sequence.context_type.value,
            "logical_progression": self.logical_progression,
            "complexity_growth": self._calculate_complexity_growth()
        }
    
    def _calculate_complexity_growth(self) -> List[Dict[str, int]]:
        """Calculate how complexity grows through the sequence."""
        complexity_points = []
        for snapshot in self.snapshots:
            complexity_points.append({
                "vertices": len(snapshot.egi_state.V),
                "edges": len(snapshot.egi_state.E),
                "cuts": len(snapshot.egi_state.Cut),
                "total_elements": (len(snapshot.egi_state.V) + 
                                 len(snapshot.egi_state.E) + 
                                 len(snapshot.egi_state.Cut))
            })
        return complexity_points


class ViewManager:
    """Manages creation and retrieval of synchronic and diachronic views."""
    
    def __init__(self, repository: ImmutableEGIRepository):
        self.repository = repository
        self.synchronic_views: Dict[str, SynchronicView] = {}
        self.diachronic_views: Dict[str, DiachronicView] = {}
    
    def create_synchronic_view(self, egi_id: str, 
                             spatial_layout: Optional[Dict[str, Tuple[float, float]]] = None) -> str:
        """Create a synchronic view for a specific EGI state."""
        snapshot = self.repository.get_egi_snapshot(egi_id)
        if not snapshot:
            raise ValueError(f"EGI snapshot {egi_id} not found")
        
        view_id = str(uuid.uuid4())
        
        # Generate semantic description
        semantic_description = self._generate_semantic_description(snapshot)
        
        # Analyze logical structure
        logical_analysis = self._analyze_egi_logic(snapshot.egi_state)
        
        synchronic_view = SynchronicView(
            view_id=view_id,
            egi_snapshot=snapshot,
            logical_analysis=logical_analysis,
            spatial_layout=spatial_layout or {},
            semantic_description=semantic_description
        )
        
        self.synchronic_views[view_id] = synchronic_view
        return view_id
    
    def create_diachronic_view(self, sequence_id: str) -> str:
        """Create a diachronic view for a transformation sequence."""
        sequence = self.repository.get_transformation_sequence(sequence_id)
        if not sequence:
            raise ValueError(f"Transformation sequence {sequence_id} not found")
        
        view_id = str(uuid.uuid4())
        
        # Collect all snapshots in the sequence
        snapshots = []
        
        # Add initial snapshot
        initial_snapshot = self.repository.get_egi_snapshot(sequence.initial_egi_id)
        if initial_snapshot:
            snapshots.append(initial_snapshot)
        
        # Add snapshots for each transformation step
        for step in sequence.steps:
            target_snapshot = self.repository.get_egi_snapshot(step.target_egi_id)
            if target_snapshot:
                snapshots.append(target_snapshot)
        
        # Generate logical progression description
        logical_progression = self._generate_logical_progression(sequence, snapshots)
        
        # Analyze transformation patterns
        transformation_analysis = self._analyze_transformation_sequence(sequence, snapshots)
        
        diachronic_view = DiachronicView(
            view_id=view_id,
            transformation_sequence=sequence,
            snapshots=snapshots,
            transformation_analysis=transformation_analysis,
            logical_progression=logical_progression
        )
        
        self.diachronic_views[view_id] = diachronic_view
        return view_id
    
    def get_synchronic_view(self, view_id: str) -> Optional[SynchronicView]:
        """Retrieve a synchronic view."""
        return self.synchronic_views.get(view_id)
    
    def get_diachronic_view(self, view_id: str) -> Optional[DiachronicView]:
        """Retrieve a diachronic view."""
        return self.diachronic_views.get(view_id)
    
    def compare_synchronic_states(self, view_id_1: str, view_id_2: str) -> Dict[str, Any]:
        """Compare two synchronic states."""
        view_1 = self.synchronic_views.get(view_id_1)
        view_2 = self.synchronic_views.get(view_id_2)
        
        if not view_1 or not view_2:
            raise ValueError("One or both views not found")
        
        analysis_1 = view_1.analyze_logical_structure()
        analysis_2 = view_2.analyze_logical_structure()
        
        return {
            "vertex_change": analysis_2["vertices"] - analysis_1["vertices"],
            "edge_change": analysis_2["edges"] - analysis_1["edges"],
            "cut_change": analysis_2["cuts"] - analysis_1["cuts"],
            "complexity_change": (analysis_2["vertices"] + analysis_2["edges"] + analysis_2["cuts"]) - 
                                (analysis_1["vertices"] + analysis_1["edges"] + analysis_1["cuts"]),
            "context_transition": f"{analysis_1['context_type']} → {analysis_2['context_type']}",
            "temporal_gap": (view_2.egi_snapshot.timestamp - view_1.egi_snapshot.timestamp).total_seconds()
        }
    
    def _generate_semantic_description(self, snapshot: EGISnapshot) -> str:
        """Generate human-readable description of EGI state."""
        egi = snapshot.egi_state
        vertex_count = len(egi.V)
        edge_count = len(egi.E)
        cut_count = len(egi.Cut)
        
        description_parts = []
        
        if vertex_count > 0:
            description_parts.append(f"{vertex_count} vertex{'es' if vertex_count != 1 else ''}")
        
        if edge_count > 0:
            description_parts.append(f"{edge_count} edge{'s' if edge_count != 1 else ''}")
        
        if cut_count > 0:
            description_parts.append(f"{cut_count} cut{'s' if cut_count != 1 else ''}")
        
        if not description_parts:
            return "Empty EGI"
        
        base_description = "EGI with " + ", ".join(description_parts)
        
        if snapshot.logical_description:
            base_description += f" ({snapshot.logical_description})"
        
        return base_description
    
    def _analyze_egi_logic(self, egi: RelationalGraphWithCuts) -> Dict[str, Any]:
        """Analyze logical structure of an EGI."""
        return {
            "element_counts": {
                "vertices": len(egi.V),
                "edges": len(egi.E),
                "cuts": len(egi.Cut)
            },
            "structural_properties": {
                "areas": len(egi.area),
                "relations": len(egi.rel),
                "nu_mappings": len(egi.nu)
            },
            "connectivity": self._analyze_connectivity(egi),
            "nesting_structure": self._analyze_nesting(egi)
        }
    
    def _analyze_connectivity(self, egi: RelationalGraphWithCuts) -> Dict[str, Any]:
        """Analyze connectivity patterns in the EGI."""
        # Count vertices that participate in edges
        connected_vertices = set()
        for vertex_seq in egi.nu.values():
            connected_vertices.update(vertex_seq)
        
        isolated_vertices = len(egi.V) - len(connected_vertices)
        
        return {
            "connected_vertices": len(connected_vertices),
            "isolated_vertices": isolated_vertices,
            "connectivity_ratio": len(connected_vertices) / max(len(egi.V), 1)
        }
    
    def _analyze_nesting(self, egi: RelationalGraphWithCuts) -> Dict[str, Any]:
        """Analyze nesting structure of cuts."""
        # Simplified nesting analysis
        cut_areas = {cut_id: egi.area.get(cut_id, frozenset()) for cut_id in [c.id for c in egi.Cut]}
        
        return {
            "total_cuts": len(egi.Cut),
            "cut_areas": {cut_id: len(contents) for cut_id, contents in cut_areas.items()},
            "max_area_size": max([len(contents) for contents in cut_areas.values()], default=0)
        }
    
    def _generate_logical_progression(self, sequence: TransformationSequence, 
                                    snapshots: List[EGISnapshot]) -> List[str]:
        """Generate logical progression description for transformation sequence."""
        progression = []
        
        if snapshots:
            progression.append(f"Initial: {self._generate_semantic_description(snapshots[0])}")
        
        for i, step in enumerate(sequence.steps):
            if i + 1 < len(snapshots):
                next_snapshot = snapshots[i + 1]
                progression.append(f"Step {i+1}: {step.rule_type.value} → {self._generate_semantic_description(next_snapshot)}")
        
        return progression
    
    def _analyze_transformation_sequence(self, sequence: TransformationSequence, 
                                       snapshots: List[EGISnapshot]) -> Dict[str, Any]:
        """Analyze patterns in transformation sequence."""
        if not sequence.steps:
            return {"empty_sequence": True}
        
        rule_types = [step.rule_type.value for step in sequence.steps]
        
        return {
            "sequence_patterns": {
                "most_common_rule": max(set(rule_types), key=rule_types.count) if rule_types else None,
                "rule_diversity": len(set(rule_types)),
                "alternation_patterns": self._detect_alternation_patterns(rule_types)
            },
            "complexity_evolution": self._track_complexity_evolution(snapshots),
            "logical_coherence": self._assess_logical_coherence(sequence)
        }
    
    def _detect_alternation_patterns(self, rule_types: List[str]) -> List[str]:
        """Detect patterns in rule application sequence."""
        patterns = []
        
        # Look for simple alternations
        if len(rule_types) >= 2:
            for i in range(len(rule_types) - 1):
                if rule_types[i] != rule_types[i + 1]:
                    patterns.append(f"{rule_types[i]}→{rule_types[i + 1]}")
        
        return patterns
    
    def _track_complexity_evolution(self, snapshots: List[EGISnapshot]) -> Dict[str, List[int]]:
        """Track how complexity evolves through snapshots."""
        evolution = {
            "vertices": [],
            "edges": [],
            "cuts": [],
            "total": []
        }
        
        for snapshot in snapshots:
            egi = snapshot.egi_state
            v_count = len(egi.V)
            e_count = len(egi.E)
            c_count = len(egi.Cut)
            
            evolution["vertices"].append(v_count)
            evolution["edges"].append(e_count)
            evolution["cuts"].append(c_count)
            evolution["total"].append(v_count + e_count + c_count)
        
        return evolution
    
    def _assess_logical_coherence(self, sequence: TransformationSequence) -> Dict[str, Any]:
        """Assess logical coherence of transformation sequence."""
        return {
            "has_justifications": all(step.logical_justification for step in sequence.steps),
            "context_consistency": len(set(step.context_type for step in sequence.steps)) == 1,
            "temporal_ordering": all(
                sequence.steps[i].timestamp <= sequence.steps[i + 1].timestamp 
                for i in range(len(sequence.steps) - 1)
            ) if len(sequence.steps) > 1 else True
        }


def demonstrate_view_separation():
    """Demonstrate separation of diachronic and synchronic views."""
    
    from egi_transformation_pipeline import EGITransformationPipeline
    
    # Create pipeline and generate some transformations
    pipeline = EGITransformationPipeline()
    
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
    
    initial_egi_id = "demo_initial"
    from immutable_transformation_architecture import EGISnapshot
    initial_snapshot = EGISnapshot(
        egi_id=initial_egi_id,
        egi_state=initial_egi,
        timestamp=datetime.now(),
        context_type=ContextType.ERGASTERION,
        provenance_step_id=None,
        logical_description="Demo initial EGI",
        spatial_layout=frozendict()
    )
    
    pipeline.repository.store_egi_snapshot(initial_snapshot)
    
    # Apply some transformations
    egi_2_id = pipeline.apply_transformation(
        source_egi_id=initial_egi_id,
        rule_type=TransformationRuleType.INSERTION,
        transformation_data={"element_type": "vertex", "element_id": "v2", "target_area": "sheet"},
        context_type=ContextType.ERGASTERION,
        logical_justification="Add second vertex"
    )
    
    egi_3_id = pipeline.apply_transformation(
        source_egi_id=egi_2_id,
        rule_type=TransformationRuleType.INSERTION,
        transformation_data={
            "element_type": "edge", "element_id": "e1", "target_area": "sheet",
            "vertex_sequence": ("v1", "v2"), "relation_name": "Connected"
        },
        context_type=ContextType.ERGASTERION,
        logical_justification="Connect vertices with edge"
    )
    
    # Create view manager
    view_manager = ViewManager(pipeline.repository)
    
    print("🔍 Diachronic vs Synchronic View Demonstration")
    print("=" * 55)
    
    # Create synchronic views
    sync_view_1_id = view_manager.create_synchronic_view(initial_egi_id)
    sync_view_2_id = view_manager.create_synchronic_view(egi_2_id)
    sync_view_3_id = view_manager.create_synchronic_view(egi_3_id)
    
    print("📊 SYNCHRONIC VIEWS (Static States)")
    print("-" * 35)
    
    for i, view_id in enumerate([sync_view_1_id, sync_view_2_id, sync_view_3_id], 1):
        view = view_manager.get_synchronic_view(view_id)
        analysis = view.analyze_logical_structure()
        print(f"State {i}: {view.semantic_description}")
        print(f"   Elements: {analysis['vertices']}V, {analysis['edges']}E, {analysis['cuts']}C")
        print(f"   Context: {analysis['context_type']}")
    
    # Create transformation sequence for diachronic view
    from immutable_transformation_architecture import TransformationSequence
    sequence = TransformationSequence(
        sequence_id="demo_sequence",
        initial_egi_id=initial_egi_id,
        context_type=ContextType.ERGASTERION,
        description="Demo transformation sequence"
    )
    
    # Add steps to sequence
    for step in pipeline.repository.transformation_steps.values():
        sequence.add_step(step)
    
    pipeline.repository.store_transformation_sequence(sequence)
    
    # Create diachronic view
    dia_view_id = view_manager.create_diachronic_view("demo_sequence")
    dia_view = view_manager.get_diachronic_view(dia_view_id)
    
    print(f"\n📈 DIACHRONIC VIEW (Historical Sequence)")
    print("-" * 40)
    print(f"Sequence: {dia_view.transformation_sequence.description}")
    print(f"Total steps: {dia_view.get_sequence_length()}")
    print(f"Rule distribution: {dia_view.get_rule_distribution()}")
    
    analysis = dia_view.analyze_transformation_progression()
    print(f"Complexity growth: {analysis['complexity_growth']}")
    
    print(f"\nLogical progression:")
    for i, step_desc in enumerate(dia_view.logical_progression, 1):
        print(f"   {i}. {step_desc}")
    
    # Compare synchronic states
    comparison = view_manager.compare_synchronic_states(sync_view_1_id, sync_view_3_id)
    print(f"\n🔄 COMPARISON (Initial vs Final)")
    print("-" * 30)
    print(f"Vertex change: +{comparison['vertex_change']}")
    print(f"Edge change: +{comparison['edge_change']}")
    print(f"Total complexity change: +{comparison['complexity_change']}")
    print(f"Context: {comparison['context_transition']}")
    
    return view_manager, pipeline


if __name__ == "__main__":
    demonstrate_view_separation()
