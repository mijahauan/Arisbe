"""
Agon: Integration process for testing how isolated graphs fit into universe of discourse.
Tests compatibility, identifies conflicts, and manages integration transformations.
"""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

from egi_core_dau import RelationalGraphWithCuts, ElementID, Vertex, Edge, Cut
from frozendict import frozendict
from immutable_transformation_architecture import (
    ImmutableEGIRepository, EGISnapshot, TransformationStep, ContextType, TransformationRuleType
)
from egi_transformation_pipeline import EGITransformationPipeline
from ergasterion_context import ErgasterionWorkspace, Experiment


class IntegrationStatus(Enum):
    """Status of integration attempts."""
    PENDING = "pending"
    COMPATIBLE = "compatible"
    CONFLICTED = "conflicted"
    ADAPTED = "adapted"
    REJECTED = "rejected"


class ConflictType(Enum):
    """Types of conflicts that can occur during integration."""
    SEMANTIC_CONTRADICTION = "semantic_contradiction"
    STRUCTURAL_INCOMPATIBILITY = "structural_incompatibility"
    NAMING_COLLISION = "naming_collision"
    LOGICAL_INCONSISTENCY = "logical_inconsistency"
    CONTEXTUAL_MISMATCH = "contextual_mismatch"


@dataclass
class IntegrationConflict:
    """Represents a conflict discovered during integration testing."""
    conflict_id: str
    conflict_type: ConflictType
    description: str
    affected_elements: Set[ElementID]
    severity: float  # 0.0 to 1.0
    suggested_resolution: str
    auto_resolvable: bool


@dataclass
class IntegrationAttempt:
    """Record of an attempt to integrate an EGI with universe of discourse."""
    attempt_id: str
    candidate_egi_id: str
    universe_egi_id: str
    status: IntegrationStatus
    conflicts: List[IntegrationConflict]
    adaptations_required: List[str]
    integration_cost: float  # Measure of complexity/effort required
    timestamp: datetime
    notes: str = ""
    
    def add_conflict(self, conflict: IntegrationConflict) -> None:
        """Add a conflict to this integration attempt."""
        self.conflicts.append(conflict)
        if conflict.severity >= 0.8:
            self.status = IntegrationStatus.CONFLICTED
    
    def resolve_conflict(self, conflict_id: str, resolution_note: str) -> None:
        """Mark a conflict as resolved."""
        for conflict in self.conflicts:
            if conflict.conflict_id == conflict_id:
                self.notes += f"\nResolved {conflict_id}: {resolution_note}"
                break


@dataclass
class UniverseOfDiscourse:
    """Represents the current universe of discourse."""
    universe_id: str
    current_egi_id: str
    description: str
    established_at: datetime
    integration_history: List[str] = field(default_factory=list)
    semantic_constraints: Dict[str, Any] = field(default_factory=dict)
    
    def add_integration(self, attempt_id: str) -> None:
        """Record an integration attempt."""
        self.integration_history.append(attempt_id)


class CompatibilityAnalyzer:
    """Analyzes compatibility between candidate EGI and universe of discourse."""
    
    def __init__(self, repository: ImmutableEGIRepository):
        self.repository = repository
    
    def analyze_compatibility(self, candidate_egi_id: str, 
                            universe_egi_id: str) -> List[IntegrationConflict]:
        """Analyze compatibility between candidate and universe EGIs."""
        conflicts = []
        
        candidate_snapshot = self.repository.get_egi_snapshot(candidate_egi_id)
        universe_snapshot = self.repository.get_egi_snapshot(universe_egi_id)
        
        if not candidate_snapshot or not universe_snapshot:
            conflicts.append(IntegrationConflict(
                conflict_id=str(uuid.uuid4()),
                conflict_type=ConflictType.STRUCTURAL_INCOMPATIBILITY,
                description="Missing EGI snapshots",
                affected_elements=set(),
                severity=1.0,
                suggested_resolution="Ensure both EGIs exist in repository",
                auto_resolvable=False
            ))
            return conflicts
        
        candidate_egi = candidate_snapshot.egi_state
        universe_egi = universe_snapshot.egi_state
        
        # Check for naming collisions
        conflicts.extend(self._check_naming_collisions(candidate_egi, universe_egi))
        
        # Check for semantic contradictions
        conflicts.extend(self._check_semantic_contradictions(candidate_egi, universe_egi))
        
        # Check for structural compatibility
        conflicts.extend(self._check_structural_compatibility(candidate_egi, universe_egi))
        
        # Check for logical consistency
        conflicts.extend(self._check_logical_consistency(candidate_egi, universe_egi))
        
        return conflicts
    
    def _check_naming_collisions(self, candidate: RelationalGraphWithCuts, 
                               universe: RelationalGraphWithCuts) -> List[IntegrationConflict]:
        """Check for element naming collisions."""
        conflicts = []
        
        # Check vertex name collisions
        candidate_vertex_ids = {v.id for v in candidate.V}
        universe_vertex_ids = {v.id for v in universe.V}
        vertex_collisions = candidate_vertex_ids & universe_vertex_ids
        
        if vertex_collisions:
            conflicts.append(IntegrationConflict(
                conflict_id=str(uuid.uuid4()),
                conflict_type=ConflictType.NAMING_COLLISION,
                description=f"Vertex naming collisions: {vertex_collisions}",
                affected_elements=vertex_collisions,
                severity=0.6,
                suggested_resolution="Rename colliding vertices with unique suffixes",
                auto_resolvable=True
            ))
        
        # Check edge name collisions
        candidate_edge_ids = {e.id for e in candidate.E}
        universe_edge_ids = {e.id for e in universe.E}
        edge_collisions = candidate_edge_ids & universe_edge_ids
        
        if edge_collisions:
            conflicts.append(IntegrationConflict(
                conflict_id=str(uuid.uuid4()),
                conflict_type=ConflictType.NAMING_COLLISION,
                description=f"Edge naming collisions: {edge_collisions}",
                affected_elements=edge_collisions,
                severity=0.7,
                suggested_resolution="Rename colliding edges with unique suffixes",
                auto_resolvable=True
            ))
        
        return conflicts
    
    def _check_semantic_contradictions(self, candidate: RelationalGraphWithCuts,
                                     universe: RelationalGraphWithCuts) -> List[IntegrationConflict]:
        """Check for semantic contradictions between relation meanings."""
        conflicts = []
        
        # Check for contradictory relation definitions
        for edge_id, relation_name in candidate.rel.items():
            if edge_id in universe.rel:
                universe_relation = universe.rel[edge_id]
                if relation_name != universe_relation:
                    conflicts.append(IntegrationConflict(
                        conflict_id=str(uuid.uuid4()),
                        conflict_type=ConflictType.SEMANTIC_CONTRADICTION,
                        description=f"Edge {edge_id} has different relations: '{relation_name}' vs '{universe_relation}'",
                        affected_elements={edge_id},
                        severity=0.9,
                        suggested_resolution="Resolve semantic meaning or rename edge",
                        auto_resolvable=False
                    ))
        
        return conflicts
    
    def _check_structural_compatibility(self, candidate: RelationalGraphWithCuts,
                                      universe: RelationalGraphWithCuts) -> List[IntegrationConflict]:
        """Check for structural compatibility issues."""
        conflicts = []
        
        # Check for incompatible nu mappings (same edge, different vertex sequences)
        for edge_id, vertex_seq in candidate.nu.items():
            if edge_id in universe.nu:
                universe_seq = universe.nu[edge_id]
                if vertex_seq != universe_seq:
                    conflicts.append(IntegrationConflict(
                        conflict_id=str(uuid.uuid4()),
                        conflict_type=ConflictType.STRUCTURAL_INCOMPATIBILITY,
                        description=f"Edge {edge_id} has different vertex sequences",
                        affected_elements={edge_id},
                        severity=0.8,
                        suggested_resolution="Reconcile vertex sequence definitions",
                        auto_resolvable=False
                    ))
        
        return conflicts
    
    def _check_logical_consistency(self, candidate: RelationalGraphWithCuts,
                                 universe: RelationalGraphWithCuts) -> List[IntegrationConflict]:
        """Check for logical consistency issues."""
        conflicts = []
        
        # Simplified logical consistency check
        # In practice, this would involve more sophisticated logical analysis
        
        # Check for potential contradictions in cut structures
        candidate_cut_count = len(candidate.Cut)
        universe_cut_count = len(universe.Cut)
        
        if candidate_cut_count > 0 and universe_cut_count > 0:
            # This is a simplified check - real implementation would analyze cut interactions
            conflicts.append(IntegrationConflict(
                conflict_id=str(uuid.uuid4()),
                conflict_type=ConflictType.LOGICAL_INCONSISTENCY,
                description="Complex cut interactions require detailed logical analysis",
                affected_elements=set(),
                severity=0.5,
                suggested_resolution="Perform detailed logical consistency analysis",
                auto_resolvable=False
            ))
        
        return conflicts


class IntegrationAdapter:
    """Handles adaptation of EGIs to resolve integration conflicts."""
    
    def __init__(self, transformation_pipeline: EGITransformationPipeline):
        self.transformation_pipeline = transformation_pipeline
    
    def adapt_for_integration(self, candidate_egi_id: str, 
                            conflicts: List[IntegrationConflict]) -> Optional[str]:
        """Adapt candidate EGI to resolve integration conflicts."""
        current_egi_id = candidate_egi_id
        
        for conflict in conflicts:
            if conflict.auto_resolvable:
                current_egi_id = self._resolve_conflict(current_egi_id, conflict)
        
        return current_egi_id if current_egi_id != candidate_egi_id else None
    
    def _resolve_conflict(self, egi_id: str, conflict: IntegrationConflict) -> str:
        """Resolve a specific conflict through transformation."""
        if conflict.conflict_type == ConflictType.NAMING_COLLISION:
            return self._resolve_naming_collision(egi_id, conflict)
        
        # Add other conflict resolution strategies as needed
        return egi_id
    
    def _resolve_naming_collision(self, egi_id: str, conflict: IntegrationConflict) -> str:
        """Resolve naming collision by renaming elements."""
        # This would implement actual renaming transformations
        # For now, return original EGI (simplified)
        return egi_id


class AgonIntegrationProcess:
    """Main process for testing and managing EGI integration with universe of discourse."""
    
    def __init__(self):
        self.repository = ImmutableEGIRepository()
        self.transformation_pipeline = EGITransformationPipeline()
        self.transformation_pipeline.repository = self.repository
        
        self.compatibility_analyzer = CompatibilityAnalyzer(self.repository)
        self.integration_adapter = IntegrationAdapter(self.transformation_pipeline)
        
        self.integration_attempts: Dict[str, IntegrationAttempt] = {}
        self.universe_of_discourse: Optional[UniverseOfDiscourse] = None
    
    def establish_universe_of_discourse(self, egi_id: str, description: str) -> str:
        """Establish an EGI as the universe of discourse."""
        universe_id = str(uuid.uuid4())
        
        self.universe_of_discourse = UniverseOfDiscourse(
            universe_id=universe_id,
            current_egi_id=egi_id,
            description=description,
            established_at=datetime.now()
        )
        
        return universe_id
    
    def test_integration(self, candidate_egi_id: str, notes: str = "") -> str:
        """Test integration of candidate EGI with universe of discourse."""
        if not self.universe_of_discourse:
            raise ValueError("Universe of discourse not established")
        
        attempt_id = str(uuid.uuid4())
        
        # Analyze compatibility
        conflicts = self.compatibility_analyzer.analyze_compatibility(
            candidate_egi_id, self.universe_of_discourse.current_egi_id
        )
        
        # Calculate integration cost
        integration_cost = sum(conflict.severity for conflict in conflicts)
        
        # Determine initial status
        if not conflicts:
            status = IntegrationStatus.COMPATIBLE
        elif all(conflict.auto_resolvable for conflict in conflicts):
            status = IntegrationStatus.PENDING
        else:
            status = IntegrationStatus.CONFLICTED
        
        # Create integration attempt
        attempt = IntegrationAttempt(
            attempt_id=attempt_id,
            candidate_egi_id=candidate_egi_id,
            universe_egi_id=self.universe_of_discourse.current_egi_id,
            status=status,
            conflicts=conflicts,
            adaptations_required=[],
            integration_cost=integration_cost,
            timestamp=datetime.now(),
            notes=notes
        )
        
        self.integration_attempts[attempt_id] = attempt
        self.universe_of_discourse.add_integration(attempt_id)
        
        return attempt_id
    
    def attempt_integration(self, attempt_id: str) -> bool:
        """Attempt to integrate EGI, applying adaptations if necessary."""
        attempt = self.integration_attempts.get(attempt_id)
        if not attempt:
            raise ValueError(f"Integration attempt {attempt_id} not found")
        
        if attempt.status == IntegrationStatus.COMPATIBLE:
            # Direct integration
            return self._perform_integration(attempt)
        
        elif attempt.status == IntegrationStatus.PENDING:
            # Try adaptation first
            adapted_egi_id = self.integration_adapter.adapt_for_integration(
                attempt.candidate_egi_id, attempt.conflicts
            )
            
            if adapted_egi_id:
                attempt.candidate_egi_id = adapted_egi_id
                attempt.status = IntegrationStatus.ADAPTED
                return self._perform_integration(attempt)
        
        # Integration failed
        attempt.status = IntegrationStatus.REJECTED
        return False
    
    def _perform_integration(self, attempt: IntegrationAttempt) -> bool:
        """Perform the actual integration of EGI into universe of discourse."""
        # This would implement the actual integration transformation
        # For now, simulate successful integration
        
        candidate_snapshot = self.repository.get_egi_snapshot(attempt.candidate_egi_id)
        universe_snapshot = self.repository.get_egi_snapshot(attempt.universe_egi_id)
        
        if not candidate_snapshot or not universe_snapshot:
            return False
        
        # Create integrated EGI (simplified - would merge the EGIs properly)
        integrated_egi_id = str(uuid.uuid4())
        
        # For demonstration, use the universe EGI as the integrated result
        integrated_snapshot = EGISnapshot(
            egi_id=integrated_egi_id,
            egi_state=universe_snapshot.egi_state,
            timestamp=datetime.now(),
            context_type=ContextType.SHEET_OF_ASSERTION,
            provenance_step_id=None,
            logical_description=f"Integrated with {attempt.candidate_egi_id}",
            spatial_layout=frozendict()
        )
        
        self.repository.store_egi_snapshot(integrated_snapshot)
        
        # Update universe of discourse
        self.universe_of_discourse.current_egi_id = integrated_egi_id
        
        attempt.status = IntegrationStatus.COMPATIBLE
        return True
    
    def get_integration_attempt(self, attempt_id: str) -> Optional[IntegrationAttempt]:
        """Get an integration attempt by ID."""
        return self.integration_attempts.get(attempt_id)
    
    def list_integration_attempts(self, status_filter: Optional[IntegrationStatus] = None) -> List[IntegrationAttempt]:
        """List integration attempts, optionally filtered by status."""
        attempts = list(self.integration_attempts.values())
        if status_filter:
            attempts = [att for att in attempts if att.status == status_filter]
        return sorted(attempts, key=lambda a: a.timestamp, reverse=True)
    
    def analyze_integration_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in integration attempts."""
        if not self.integration_attempts:
            return {"no_attempts": True}
        
        status_counts = {}
        conflict_type_counts = {}
        total_conflicts = 0
        
        for attempt in self.integration_attempts.values():
            status = attempt.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            for conflict in attempt.conflicts:
                conflict_type = conflict.conflict_type.value
                conflict_type_counts[conflict_type] = conflict_type_counts.get(conflict_type, 0) + 1
                total_conflicts += 1
        
        return {
            "total_attempts": len(self.integration_attempts),
            "status_distribution": status_counts,
            "conflict_type_distribution": conflict_type_counts,
            "average_conflicts_per_attempt": total_conflicts / len(self.integration_attempts),
            "success_rate": status_counts.get("compatible", 0) / len(self.integration_attempts)
        }


def demonstrate_agon_integration():
    """Demonstrate Agon integration process."""
    
    print("⚔️  Agon Integration Process Demonstration")
    print("=" * 45)
    
    # Create Agon process
    agon = AgonIntegrationProcess()
    
    # Create universe of discourse EGI
    from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge
    universe_egi = RelationalGraphWithCuts(
        V=frozenset([Vertex("alice"), Vertex("bob")]),
        E=frozenset([Edge("knows")]),
        nu=frozendict({"knows": ("alice", "bob")}),
        sheet="sheet",
        Cut=frozenset(),
        area=frozendict({"sheet": frozenset(["alice", "bob", "knows"])}),
        rel=frozendict({"knows": "Knows"})
    )
    
    universe_egi_id = "universe_001"
    from immutable_transformation_architecture import EGISnapshot
    universe_snapshot = EGISnapshot(
        egi_id=universe_egi_id,
        egi_state=universe_egi,
        timestamp=datetime.now(),
        context_type=ContextType.SHEET_OF_ASSERTION,
        provenance_step_id=None,
        logical_description="Universe of discourse with Alice knows Bob",
        spatial_layout=frozendict()
    )
    
    agon.repository.store_egi_snapshot(universe_snapshot)
    
    # Establish universe of discourse
    universe_id = agon.establish_universe_of_discourse(
        universe_egi_id, "Social knowledge universe"
    )
    
    print(f"🌍 Established universe of discourse: {universe_id[:8]}...")
    print(f"📝 Description: {agon.universe_of_discourse.description}")
    
    # Create candidate EGI from Ergasterion (with naming collision)
    candidate_egi = RelationalGraphWithCuts(
        V=frozenset([Vertex("alice"), Vertex("charlie")]),  # "alice" collision
        E=frozenset([Edge("likes")]),
        nu=frozendict({"likes": ("alice", "charlie")}),
        sheet="sheet",
        Cut=frozenset(),
        area=frozendict({"sheet": frozenset(["alice", "charlie", "likes"])}),
        rel=frozendict({"likes": "Likes"})
    )
    
    candidate_egi_id = "candidate_001"
    candidate_snapshot = EGISnapshot(
        egi_id=candidate_egi_id,
        egi_state=candidate_egi,
        timestamp=datetime.now(),
        context_type=ContextType.ERGASTERION,
        provenance_step_id=None,
        logical_description="Candidate EGI: Alice likes Charlie",
        spatial_layout=frozendict()
    )
    
    agon.repository.store_egi_snapshot(candidate_snapshot)
    
    # Test integration
    attempt_id = agon.test_integration(
        candidate_egi_id, "Testing social relationship integration"
    )
    
    attempt = agon.get_integration_attempt(attempt_id)
    print(f"\n🧪 Integration Test: {attempt_id[:8]}...")
    print(f"📊 Status: {attempt.status.value}")
    print(f"⚠️  Conflicts found: {len(attempt.conflicts)}")
    
    for i, conflict in enumerate(attempt.conflicts, 1):
        print(f"   {i}. {conflict.conflict_type.value}: {conflict.description}")
        print(f"      Severity: {conflict.severity:.1f}, Auto-resolvable: {conflict.auto_resolvable}")
    
    print(f"💰 Integration cost: {attempt.integration_cost:.2f}")
    
    # Attempt integration
    success = agon.attempt_integration(attempt_id)
    updated_attempt = agon.get_integration_attempt(attempt_id)
    
    print(f"\n🎯 Integration Attempt Result:")
    print(f"   Success: {success}")
    print(f"   Final status: {updated_attempt.status.value}")
    
    if success:
        print(f"   New universe EGI: {agon.universe_of_discourse.current_egi_id}")
    
    # Create another candidate (compatible)
    compatible_egi = RelationalGraphWithCuts(
        V=frozenset([Vertex("david")]),
        E=frozenset(),
        nu=frozendict(),
        sheet="sheet",
        Cut=frozenset(),
        area=frozendict({"sheet": frozenset(["david"])}),
        rel=frozendict()
    )
    
    compatible_egi_id = "compatible_001"
    compatible_snapshot = EGISnapshot(
        egi_id=compatible_egi_id,
        egi_state=compatible_egi,
        timestamp=datetime.now(),
        context_type=ContextType.ERGASTERION,
        provenance_step_id=None,
        logical_description="Compatible EGI: David exists",
        spatial_layout=frozendict()
    )
    
    agon.repository.store_egi_snapshot(compatible_snapshot)
    
    # Test compatible integration
    compatible_attempt_id = agon.test_integration(
        compatible_egi_id, "Testing compatible integration"
    )
    
    compatible_attempt = agon.get_integration_attempt(compatible_attempt_id)
    print(f"\n✅ Compatible Integration Test:")
    print(f"   Status: {compatible_attempt.status.value}")
    print(f"   Conflicts: {len(compatible_attempt.conflicts)}")
    print(f"   Integration cost: {compatible_attempt.integration_cost:.2f}")
    
    # Analyze integration patterns
    analysis = agon.analyze_integration_patterns()
    print(f"\n📈 Integration Analysis:")
    print(f"   Total attempts: {analysis['total_attempts']}")
    print(f"   Status distribution: {analysis['status_distribution']}")
    print(f"   Success rate: {analysis['success_rate']:.1%}")
    if 'conflict_type_distribution' in analysis:
        print(f"   Conflict types: {analysis['conflict_type_distribution']}")
    
    return agon


if __name__ == "__main__":
    demonstrate_agon_integration()
