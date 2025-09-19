"""
Comprehensive Ligature Algorithms Testing Suite

Tests all ligature-related components (2,200+ lines):
- LigatureManipulationEngine (1,527 lines)
- LigatureOptimizationEngine (378 lines)
- LigatureAwarePositioningEngine (356 lines)
- Enhanced ligature algorithms
- Obstacle-aware routing
- Single object detection
- Chapter 16-17 compliance
"""

import math
import tempfile
import uuid
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass

import pytest

from src.egi_core_dau import (
    create_empty_graph, 
    create_vertex, 
    create_edge, 
    create_cut,
    RelationalGraphWithCuts,
    ElementID
)
from src.ligature_manipulation_rules import (
    LigatureManipulationEngine,
    MoveBranchesAlongLigatureRule,
    MergeLigaturesRule,
    SplitLigatureRule,
    LigatureValidationResult
)
from src.ligature_optimization_engine import (
    LigatureOptimizationEngine,
    OptimizationResult,
    LigatureConstraint,
    OptimizationMetrics
)
from src.ligature_aware_positioning_engine import (
    LigatureAwarePositioningEngine,
    PositioningResult,
    AreaConstraint,
    PositionConstraint
)
from src.enhanced_ligature_algorithms import (
    EnhancedLigatureAlgorithms,
    LigatureDetectionResult,
    LigatureOptimizationConfig
)
from src.obstacle_aware_ligature_router import (
    ObstacleAwareLigatureRouter,
    RoutingResult,
    ObstacleConstraint
)
from src.single_object_ligature_detector import (
    SingleObjectLigatureDetector,
    DetectionResult,
    LigatureCandidate
)
from src.formal_transformation_rules import TransformationContext, AreaPolarity


@dataclass
class TestPosition:
    """Test position for ligature testing."""
    x: float
    y: float
    element_id: ElementID


class TestLigatureAlgorithmsComprehensive:
    """Comprehensive test suite for ligature algorithms."""

    def setup_method(self):
        """Set up test environment."""
        self.manipulation_engine = LigatureManipulationEngine()
        self.optimization_engine = LigatureOptimizationEngine()
        self.positioning_engine = LigatureAwarePositioningEngine()
        self.enhanced_algorithms = EnhancedLigatureAlgorithms()
        self.router = ObstacleAwareLigatureRouter()
        self.detector = SingleObjectLigatureDetector()
        
        # Create test EGIs
        self.simple_egi = self._create_simple_ligature_egi()
        self.complex_egi = self._create_complex_ligature_egi()
        self.nested_egi = self._create_nested_cuts_egi()

    def _create_simple_ligature_egi(self) -> RelationalGraphWithCuts:
        """Create simple EGI with ligature opportunities."""
        egi = create_empty_graph()
        
        # Create vertices that can share ligatures
        human_vertex = create_vertex(label="Human", is_generic=False)
        mortal_vertex = create_vertex(label="Mortal", is_generic=False)
        socrates_vertex = create_vertex(label="Socrates", is_generic=False)
        
        # Create edges
        human_edge = create_edge(relation="Human")
        mortal_edge = create_edge(relation="Mortal")
        
        # Build EGI with shared vertex (ligature opportunity)
        egi = (egi
               .with_vertex(human_vertex)
               .with_vertex(mortal_vertex)
               .with_vertex(socrates_vertex)
               .with_edge(human_edge)
               .with_edge(mortal_edge)
               .with_nu_entry(human_edge.id, (socrates_vertex.id,))
               .with_nu_entry(mortal_edge.id, (socrates_vertex.id,)))
        
        return egi

    def _create_complex_ligature_egi(self) -> RelationalGraphWithCuts:
        """Create complex EGI with multiple ligature opportunities."""
        egi = create_empty_graph()
        
        # Create multiple vertices
        vertices = []
        for i in range(6):
            vertex = create_vertex(label=f"Entity_{i}", is_generic=True)
            vertices.append(vertex)
            egi = egi.with_vertex(vertex)
        
        # Create edges with overlapping vertex usage (ligature opportunities)
        edges = []
        for i in range(4):
            edge = create_edge(relation=f"Relation_{i}")
            edges.append(edge)
            egi = egi.with_edge(edge)
        
        # Create nu mappings with shared vertices
        egi = (egi
               .with_nu_entry(edges[0].id, (vertices[0].id, vertices[1].id))
               .with_nu_entry(edges[1].id, (vertices[1].id, vertices[2].id))
               .with_nu_entry(edges[2].id, (vertices[2].id, vertices[3].id))
               .with_nu_entry(edges[3].id, (vertices[0].id, vertices[3].id)))
        
        return egi

    def _create_nested_cuts_egi(self) -> RelationalGraphWithCuts:
        """Create EGI with nested cuts for testing area-aware ligatures."""
        egi = create_empty_graph()
        
        # Create vertices
        vertex1 = create_vertex(label="A", is_generic=False)
        vertex2 = create_vertex(label="B", is_generic=False)
        vertex3 = create_vertex(label="C", is_generic=False)
        
        # Create cuts
        outer_cut = create_cut()
        inner_cut = create_cut()
        
        # Create edges
        edge1 = create_edge(relation="R1")
        edge2 = create_edge(relation="R2")
        
        # Build nested structure
        egi = (egi
               .with_vertex(vertex1)
               .with_vertex(vertex2)
               .with_vertex(vertex3)
               .with_cut(outer_cut)
               .with_cut(inner_cut)
               .with_edge(edge1)
               .with_edge(edge2)
               .with_nu_entry(edge1.id, (vertex1.id, vertex2.id))
               .with_nu_entry(edge2.id, (vertex2.id, vertex3.id)))
        
        # Set up area containment (simplified for testing)
        # In real implementation, this would use proper area management
        
        return egi

    # ==================== LIGATURE MANIPULATION ENGINE TESTS ====================

    def test_move_branches_along_ligature_rule(self):
        """Test Chapter 16 move branches along ligature rule."""
        rule = MoveBranchesAlongLigatureRule()
        
        # Create transformation context
        context = TransformationContext(
            source_egi=self.simple_egi,
            target_area=self.simple_egi.sheet,
            selected_subgraph=frozenset([v.id for v in self.simple_egi.V[:2]]),
            area_polarity=AreaPolarity.POSITIVE,
            nesting_depth=0
        )
        
        # Check preconditions
        preconditions_met = rule.check_preconditions(context)
        assert preconditions_met.valid, f"Preconditions failed: {preconditions_met.reason}"
        
        # Apply transformation
        result = rule.apply_transformation(context)
        assert result.success, f"Transformation failed: {result.error_message}"
        assert result.transformed_egi is not None
        assert result.validation_passed

    def test_merge_ligatures_rule(self):
        """Test ligature merging rule."""
        rule = MergeLigaturesRule()
        
        # Create context with mergeable ligatures
        context = TransformationContext(
            source_egi=self.complex_egi,
            target_area=self.complex_egi.sheet,
            selected_subgraph=frozenset([v.id for v in self.complex_egi.V[:3]]),
            area_polarity=AreaPolarity.POSITIVE,
            nesting_depth=0
        )
        
        # Test merge operation
        result = rule.apply_transformation(context)
        assert result.success, f"Merge failed: {result.error_message}"
        
        # Verify ligature was merged (fewer separate vertex instances)
        original_vertex_count = len(self.complex_egi.V)
        merged_vertex_count = len(result.transformed_egi.V)
        assert merged_vertex_count <= original_vertex_count

    def test_split_ligature_rule(self):
        """Test ligature splitting rule."""
        rule = SplitLigatureRule()
        
        # First create a merged ligature, then split it
        context = TransformationContext(
            source_egi=self.simple_egi,
            target_area=self.simple_egi.sheet,
            selected_subgraph=frozenset([v.id for v in self.simple_egi.V[:1]]),
            area_polarity=AreaPolarity.POSITIVE,
            nesting_depth=0
        )
        
        result = rule.apply_transformation(context)
        assert result.success, f"Split failed: {result.error_message}"
        
        # Verify ligature was split (more separate vertex instances)
        original_vertex_count = len(self.simple_egi.V)
        split_vertex_count = len(result.transformed_egi.V)
        assert split_vertex_count >= original_vertex_count

    def test_ligature_validation_comprehensive(self):
        """Test comprehensive ligature validation."""
        # Validate simple EGI
        validation_result = self.manipulation_engine.validate_ligatures(self.simple_egi)
        assert validation_result.is_valid
        assert len(validation_result.detected_ligatures) > 0
        
        # Validate complex EGI
        complex_validation = self.manipulation_engine.validate_ligatures(self.complex_egi)
        assert complex_validation.is_valid
        assert len(complex_validation.detected_ligatures) >= len(validation_result.detected_ligatures)

    def test_ligature_manipulation_engine_performance(self):
        """Test performance of ligature manipulation with large graphs."""
        import time
        
        # Create large EGI
        large_egi = self._create_large_ligature_egi(50)  # 50 vertices
        
        start_time = time.time()
        validation_result = self.manipulation_engine.validate_ligatures(large_egi)
        validation_time = time.time() - start_time
        
        # Should complete validation in reasonable time (< 5 seconds)
        assert validation_time < 5.0, f"Validation took too long: {validation_time:.2f}s"
        assert validation_result.is_valid

    # ==================== LIGATURE OPTIMIZATION ENGINE TESTS ====================

    def test_optimization_engine_basic_optimization(self):
        """Test basic ligature optimization."""
        # Create optimization constraints
        constraints = [
            LigatureConstraint(
                constraint_type="MIN_PATH_LENGTH",
                target_elements=frozenset([v.id for v in self.simple_egi.V[:2]]),
                weight=1.0
            ),
            LigatureConstraint(
                constraint_type="AVOID_CROSSINGS",
                target_elements=frozenset([e.id for e in self.simple_egi.E]),
                weight=0.8
            )
        ]
        
        # Run optimization
        result = self.optimization_engine.optimize_ligatures(
            self.simple_egi,
            constraints,
            max_iterations=100
        )
        
        assert result.success, f"Optimization failed: {result.error_message}"
        assert result.optimized_egi is not None
        assert result.metrics.total_path_length >= 0
        assert result.metrics.crossing_count >= 0

    def test_optimization_engine_multi_objective(self):
        """Test multi-objective optimization."""
        constraints = [
            LigatureConstraint(
                constraint_type="MIN_PATH_LENGTH",
                target_elements=frozenset([v.id for v in self.complex_egi.V]),
                weight=0.6
            ),
            LigatureConstraint(
                constraint_type="AVOID_CROSSINGS",
                target_elements=frozenset([e.id for e in self.complex_egi.E]),
                weight=0.4
            ),
            LigatureConstraint(
                constraint_type="MAINTAIN_READABILITY",
                target_elements=frozenset([v.id for v in self.complex_egi.V]),
                weight=0.3
            )
        ]
        
        result = self.optimization_engine.optimize_ligatures(
            self.complex_egi,
            constraints,
            max_iterations=50
        )
        
        assert result.success
        assert result.metrics.convergence_achieved
        assert result.metrics.final_score > 0

    def test_optimization_engine_convergence(self):
        """Test optimization convergence behavior."""
        constraints = [
            LigatureConstraint(
                constraint_type="MIN_PATH_LENGTH",
                target_elements=frozenset([v.id for v in self.simple_egi.V]),
                weight=1.0
            )
        ]
        
        # Test with different iteration limits
        for max_iter in [10, 50, 100]:
            result = self.optimization_engine.optimize_ligatures(
                self.simple_egi,
                constraints,
                max_iterations=max_iter
            )
            
            assert result.success
            assert result.metrics.iterations_completed <= max_iter

    # ==================== LIGATURE-AWARE POSITIONING ENGINE TESTS ====================

    def test_positioning_engine_basic_positioning(self):
        """Test basic ligature-aware positioning."""
        # Create area constraints
        area_constraints = [
            AreaConstraint(
                area_id=self.simple_egi.sheet,
                min_x=0, min_y=0, max_x=800, max_y=600,
                padding=20
            )
        ]
        
        # Create position constraints
        position_constraints = [
            PositionConstraint(
                element_id=v.id,
                constraint_type="FIXED_POSITION",
                x=100 + i * 150,
                y=300,
                tolerance=10
            ) for i, v in enumerate(self.simple_egi.V[:2])
        ]
        
        result = self.positioning_engine.position_elements(
            self.simple_egi,
            area_constraints,
            position_constraints
        )
        
        assert result.success, f"Positioning failed: {result.error_message}"
        assert len(result.element_positions) > 0
        assert result.constraint_violations == 0

    def test_positioning_engine_area_respect(self):
        """Test that positioning respects area boundaries."""
        # Create tight area constraint
        tight_constraint = AreaConstraint(
            area_id=self.nested_egi.sheet,
            min_x=0, min_y=0, max_x=200, max_y=200,
            padding=10
        )
        
        result = self.positioning_engine.position_elements(
            self.nested_egi,
            [tight_constraint],
            []
        )
        
        assert result.success
        
        # Verify all positions are within bounds
        for element_id, position in result.element_positions.items():
            assert 10 <= position.x <= 190  # Accounting for padding
            assert 10 <= position.y <= 190

    def test_positioning_engine_ligature_optimization(self):
        """Test positioning optimization for ligature paths."""
        # Position elements to minimize ligature path lengths
        result = self.positioning_engine.optimize_for_ligatures(
            self.complex_egi,
            optimization_weight=0.8,
            max_iterations=50
        )
        
        assert result.success
        assert result.ligature_metrics.average_path_length > 0
        assert result.ligature_metrics.total_crossings >= 0

    # ==================== ENHANCED LIGATURE ALGORITHMS TESTS ====================

    def test_enhanced_algorithms_detection(self):
        """Test enhanced ligature detection algorithms."""
        detection_result = self.enhanced_algorithms.detect_ligature_opportunities(
            self.complex_egi
        )
        
        assert detection_result.success
        assert len(detection_result.ligature_candidates) > 0
        
        # Verify candidate quality
        for candidate in detection_result.ligature_candidates:
            assert candidate.confidence_score > 0
            assert len(candidate.involved_elements) >= 2

    def test_enhanced_algorithms_optimization_config(self):
        """Test enhanced algorithms with custom optimization configuration."""
        config = LigatureOptimizationConfig(
            enable_path_optimization=True,
            enable_crossing_reduction=True,
            enable_readability_enhancement=True,
            optimization_weight_path=0.4,
            optimization_weight_crossing=0.3,
            optimization_weight_readability=0.3,
            max_optimization_iterations=75
        )
        
        result = self.enhanced_algorithms.optimize_with_config(
            self.complex_egi,
            config
        )
        
        assert result.success
        assert result.applied_optimizations > 0
        assert result.final_quality_score > 0

    def test_enhanced_algorithms_adaptive_optimization(self):
        """Test adaptive optimization based on graph characteristics."""
        # Test with different graph types
        test_egis = [self.simple_egi, self.complex_egi, self.nested_egi]
        
        for egi in test_egis:
            result = self.enhanced_algorithms.adaptive_optimize(egi)
            assert result.success, f"Adaptive optimization failed for EGI with {len(egi.V)} vertices"
            assert result.optimization_strategy is not None

    # ==================== OBSTACLE-AWARE LIGATURE ROUTER TESTS ====================

    def test_obstacle_aware_routing_basic(self):
        """Test basic obstacle-aware ligature routing."""
        # Create obstacles
        obstacles = [
            ObstacleConstraint(
                obstacle_id="obstacle_1",
                x=200, y=200, width=100, height=100,
                avoidance_padding=20
            ),
            ObstacleConstraint(
                obstacle_id="obstacle_2",
                x=400, y=300, width=80, height=80,
                avoidance_padding=15
            )
        ]
        
        # Define start and end points
        start_point = (50, 50)
        end_point = (600, 500)
        
        routing_result = self.router.route_ligature_path(
            start_point,
            end_point,
            obstacles
        )
        
        assert routing_result.success, f"Routing failed: {routing_result.error_message}"
        assert len(routing_result.path_points) >= 2  # At least start and end
        assert routing_result.total_path_length > 0
        assert routing_result.obstacle_collisions == 0

    def test_obstacle_aware_routing_complex_obstacles(self):
        """Test routing with complex obstacle configurations."""
        # Create maze-like obstacle configuration
        obstacles = []
        for i in range(5):
            for j in range(3):
                obstacles.append(ObstacleConstraint(
                    obstacle_id=f"maze_{i}_{j}",
                    x=i * 120 + 50,
                    y=j * 150 + 50,
                    width=80,
                    height=100,
                    avoidance_padding=10
                ))
        
        start_point = (25, 25)
        end_point = (675, 475)
        
        routing_result = self.router.route_ligature_path(
            start_point,
            end_point,
            obstacles,
            algorithm="A_STAR"  # Use A* for complex routing
        )
        
        assert routing_result.success
        assert routing_result.obstacle_collisions == 0
        assert len(routing_result.path_points) > 2  # Should have intermediate points

    def test_obstacle_aware_routing_performance(self):
        """Test routing performance with many obstacles."""
        import time
        
        # Create many obstacles
        obstacles = []
        for i in range(50):
            obstacles.append(ObstacleConstraint(
                obstacle_id=f"perf_obstacle_{i}",
                x=i * 15 + 10,
                y=(i % 10) * 60 + 10,
                width=10,
                height=50,
                avoidance_padding=5
            ))
        
        start_time = time.time()
        routing_result = self.router.route_ligature_path(
            (5, 5),
            (800, 600),
            obstacles
        )
        routing_time = time.time() - start_time
        
        assert routing_result.success
        assert routing_time < 2.0, f"Routing took too long: {routing_time:.2f}s"

    # ==================== SINGLE OBJECT LIGATURE DETECTOR TESTS ====================

    def test_single_object_detection_basic(self):
        """Test basic single object ligature detection."""
        detection_result = self.detector.detect_single_object_ligatures(
            self.simple_egi
        )
        
        assert detection_result.success
        assert len(detection_result.detected_ligatures) >= 0
        
        # Verify detection quality
        for ligature in detection_result.detected_ligatures:
            assert ligature.confidence > 0
            assert len(ligature.connected_elements) >= 2

    def test_single_object_detection_precision(self):
        """Test detection precision and recall."""
        # Create EGI with known ligature patterns
        known_ligature_egi = self._create_known_ligature_pattern()
        
        detection_result = self.detector.detect_single_object_ligatures(
            known_ligature_egi,
            precision_threshold=0.8
        )
        
        assert detection_result.success
        assert detection_result.precision_score >= 0.8
        assert detection_result.recall_score >= 0.7

    def test_single_object_detection_filtering(self):
        """Test detection with various filtering criteria."""
        # Test with different confidence thresholds
        for threshold in [0.3, 0.5, 0.7, 0.9]:
            detection_result = self.detector.detect_single_object_ligatures(
                self.complex_egi,
                confidence_threshold=threshold
            )
            
            assert detection_result.success
            
            # Higher thresholds should yield fewer but higher-quality results
            for ligature in detection_result.detected_ligatures:
                assert ligature.confidence >= threshold

    # ==================== INTEGRATION AND STRESS TESTS ====================

    def test_ligature_algorithms_integration(self):
        """Test integration between all ligature algorithm components."""
        # 1. Detect ligature opportunities
        detection_result = self.enhanced_algorithms.detect_ligature_opportunities(
            self.complex_egi
        )
        assert detection_result.success
        
        # 2. Optimize ligature layout
        constraints = [
            LigatureConstraint(
                constraint_type="MIN_PATH_LENGTH",
                target_elements=frozenset([c.primary_element for c in detection_result.ligature_candidates]),
                weight=1.0
            )
        ]
        
        optimization_result = self.optimization_engine.optimize_ligatures(
            self.complex_egi,
            constraints,
            max_iterations=50
        )
        assert optimization_result.success
        
        # 3. Position elements with ligature awareness
        positioning_result = self.positioning_engine.optimize_for_ligatures(
            optimization_result.optimized_egi,
            optimization_weight=0.7,
            max_iterations=30
        )
        assert positioning_result.success
        
        # 4. Validate final result
        final_validation = self.manipulation_engine.validate_ligatures(
            positioning_result.positioned_egi
        )
        assert final_validation.is_valid

    def test_ligature_algorithms_stress_test(self):
        """Stress test ligature algorithms with large, complex graphs."""
        # Create very large EGI
        large_egi = self._create_large_ligature_egi(100)  # 100 vertices, many edges
        
        import time
        start_time = time.time()
        
        # Run full ligature processing pipeline
        detection_result = self.enhanced_algorithms.detect_ligature_opportunities(large_egi)
        optimization_result = self.optimization_engine.optimize_ligatures(
            large_egi,
            [LigatureConstraint("MIN_PATH_LENGTH", frozenset([v.id for v in large_egi.V[:10]]), 1.0)],
            max_iterations=25  # Reduced for stress test
        )
        positioning_result = self.positioning_engine.optimize_for_ligatures(
            large_egi,
            optimization_weight=0.5,
            max_iterations=15  # Reduced for stress test
        )
        
        total_time = time.time() - start_time
        
        # All operations should succeed
        assert detection_result.success
        assert optimization_result.success
        assert positioning_result.success
        
        # Should complete in reasonable time (< 30 seconds)
        assert total_time < 30.0, f"Stress test took too long: {total_time:.2f}s"

    def test_ligature_algorithms_error_handling(self):
        """Test error handling in ligature algorithms."""
        # Test with invalid EGI
        empty_egi = create_empty_graph()
        
        # Should handle gracefully
        detection_result = self.enhanced_algorithms.detect_ligature_opportunities(empty_egi)
        assert detection_result.success  # Should succeed with empty results
        assert len(detection_result.ligature_candidates) == 0
        
        # Test with malformed constraints
        invalid_constraints = [
            LigatureConstraint(
                constraint_type="INVALID_TYPE",
                target_elements=frozenset(["nonexistent_id"]),
                weight=-1.0  # Invalid weight
            )
        ]
        
        optimization_result = self.optimization_engine.optimize_ligatures(
            self.simple_egi,
            invalid_constraints,
            max_iterations=10
        )
        # Should either succeed with warnings or fail gracefully
        assert optimization_result.success or optimization_result.error_message is not None

    # ==================== HELPER METHODS ====================

    def _create_large_ligature_egi(self, num_vertices: int) -> RelationalGraphWithCuts:
        """Create large EGI with many ligature opportunities for stress testing."""
        egi = create_empty_graph()
        
        # Create vertices
        vertices = []
        for i in range(num_vertices):
            vertex = create_vertex(label=f"V_{i}", is_generic=True)
            vertices.append(vertex)
            egi = egi.with_vertex(vertex)
        
        # Create edges with overlapping vertex usage (many ligature opportunities)
        edges = []
        for i in range(num_vertices // 2):
            edge = create_edge(relation=f"R_{i}")
            edges.append(edge)
            egi = egi.with_edge(edge)
            
            # Connect to multiple vertices to create ligature opportunities
            connected_vertices = vertices[i:i+3] if i+3 <= num_vertices else vertices[i:]
            if len(connected_vertices) >= 2:
                egi = egi.with_nu_entry(edge.id, tuple(v.id for v in connected_vertices[:2]))
        
        return egi

    def _create_known_ligature_pattern(self) -> RelationalGraphWithCuts:
        """Create EGI with known ligature pattern for precision testing."""
        egi = create_empty_graph()
        
        # Create a star pattern (one central vertex connected to many others)
        central_vertex = create_vertex(label="Central", is_generic=True)
        egi = egi.with_vertex(central_vertex)
        
        outer_vertices = []
        for i in range(5):
            vertex = create_vertex(label=f"Outer_{i}", is_generic=True)
            outer_vertices.append(vertex)
            egi = egi.with_vertex(vertex)
            
            # Create edge connecting central to outer
            edge = create_edge(relation=f"Connection_{i}")
            egi = egi.with_edge(edge)
            egi = egi.with_nu_entry(edge.id, (central_vertex.id, vertex.id))
        
        # This creates a clear ligature pattern at the central vertex
        return egi


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
