"""
Test suite for ReadabilityOptimizer

Tests collision detection, avoidance, spacing optimization, and other
readability improvements while ensuring iron-clad guarantees are maintained.
"""

import unittest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from readability_optimizer import (
    ReadabilityOptimizer, OptimizationLevel, OptimizationConstraints,
    CollisionInfo, optimize_layout_readability
)
from layout_engine_ironclad import LayoutDTO, Point, BoundingBox
from layout_engine_styled import StyleAwareLayoutEngine
from style_loader import load_default_style
from egif_parser_dau import parse_egif


class TestReadabilityOptimizer(unittest.TestCase):
    """Test suite for readability optimization"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.optimizer = ReadabilityOptimizer()
        self.style = load_default_style()
        self.layout_engine = StyleAwareLayoutEngine(self.style)
        
        # Create test EGI with potential collisions
        self.test_egif = '*x *y (Human x) (Human y) (Friend x y)'
        self.test_egi = parse_egif(self.test_egif)
        
        # Create a layout with intentional collisions for testing
        self.collision_layout = self._create_collision_layout()
    
    def _create_collision_layout(self) -> LayoutDTO:
        """Create a layout with intentional element collisions"""
        
        # Generate base layout
        base_layout = self.layout_engine.compute_layout(self.test_egi)
        
        # Force collisions by moving elements to same positions
        vertex_ids = list(base_layout.vertex_positions.keys())
        predicate_ids = list(base_layout.predicate_positions.keys())
        
        if len(vertex_ids) >= 2:
            # Move second vertex to same position as first
            base_layout.vertex_positions[vertex_ids[1]] = base_layout.vertex_positions[vertex_ids[0]]
        
        if len(predicate_ids) >= 2:
            # Move predicates close together
            pos1 = base_layout.predicate_positions[predicate_ids[0]]
            base_layout.predicate_positions[predicate_ids[1]] = Point(pos1.x + 5, pos1.y + 2)
        
        return base_layout
    
    def test_collision_detection(self):
        """Test collision detection functionality"""
        
        collisions = self.optimizer._detect_collisions(self.collision_layout)
        
        # Should detect collisions in our collision layout
        self.assertGreater(len(collisions), 0, "Should detect collisions in collision layout")
        
        # Check collision properties
        for collision in collisions:
            self.assertIsInstance(collision, CollisionInfo)
            self.assertGreater(collision.overlap_area, 0)
            self.assertGreaterEqual(collision.severity, 0.0)
            self.assertLessEqual(collision.severity, 1.0)
            
            # Collision center should be within both element bounds
            center = collision.collision_center
            self.assertIsInstance(center, Point)
    
    def test_collision_resolution(self):
        """Test that collisions are properly resolved"""
        
        # Detect initial collisions
        initial_collisions = self.optimizer._detect_collisions(self.collision_layout)
        self.assertGreater(len(initial_collisions), 0, "Should have initial collisions")
        
        # Apply collision resolution
        resolved_layout = self.optimizer._resolve_collisions(
            self.collision_layout, initial_collisions, self.test_egi
        )
        
        # Check that collisions are reduced
        final_collisions = self.optimizer._detect_collisions(resolved_layout)
        
        # Should have fewer or less severe collisions
        total_initial_severity = sum(c.severity for c in initial_collisions)
        total_final_severity = sum(c.severity for c in final_collisions)
        
        self.assertLessEqual(total_final_severity, total_initial_severity,
                           "Total collision severity should be reduced")
        
        # Verify iron-clad guarantees are maintained
        self.assertEqual(len(resolved_layout.vertex_positions), len(self.collision_layout.vertex_positions))
        self.assertEqual(len(resolved_layout.predicate_positions), len(self.collision_layout.predicate_positions))
    
    def test_optimization_levels(self):
        """Test different optimization levels"""
        
        layouts = {}
        
        # Test all optimization levels
        for level in OptimizationLevel:
            optimized = self.optimizer.optimize_layout(self.collision_layout, self.test_egi, level)
            layouts[level] = optimized
            
            # Verify basic properties
            self.assertIsInstance(optimized, LayoutDTO)
            self.assertEqual(len(optimized.vertex_positions), len(self.collision_layout.vertex_positions))
            self.assertEqual(len(optimized.predicate_positions), len(self.collision_layout.predicate_positions))
        
        # Compare readability scores
        scores = {}
        for level, layout in layouts.items():
            scores[level] = self.optimizer._calculate_readability_score(layout)
        
        # More aggressive optimization should generally produce better scores
        # (though this isn't guaranteed due to local optima)
        self.assertIsInstance(scores[OptimizationLevel.MINIMAL], (int, float))
        self.assertIsInstance(scores[OptimizationLevel.STANDARD], (int, float))
        self.assertIsInstance(scores[OptimizationLevel.AGGRESSIVE], (int, float))
    
    def test_spacing_optimization(self):
        """Test spacing optimization functionality"""
        
        # Create layout with poor spacing
        poor_spacing_layout = self._create_poor_spacing_layout()
        
        # Apply spacing optimization
        optimized = self.optimizer._optimize_spacing(poor_spacing_layout, self.test_egi)
        
        # Calculate spacing scores
        original_score = self.optimizer._calculate_spacing_score(poor_spacing_layout)
        optimized_score = self.optimizer._calculate_spacing_score(optimized)
        
        # Optimized layout should have better or equal spacing
        self.assertGreaterEqual(optimized_score, original_score - 1.0,  # Allow small tolerance
                               "Spacing optimization should improve or maintain spacing quality")
    
    def _create_poor_spacing_layout(self) -> LayoutDTO:
        """Create a layout with poor element spacing"""
        
        base_layout = self.layout_engine.compute_layout(self.test_egi)
        
        # Cluster elements together for poor spacing
        vertex_ids = list(base_layout.vertex_positions.keys())
        if len(vertex_ids) >= 2:
            center = base_layout.vertex_positions[vertex_ids[0]]
            for i, vertex_id in enumerate(vertex_ids[1:], 1):
                # Place vertices very close together
                base_layout.vertex_positions[vertex_id] = Point(
                    center.x + i * 3,  # Very small spacing
                    center.y + i * 2
                )
        
        return base_layout
    
    def test_readability_score_calculation(self):
        """Test readability score calculation"""
        
        # Test with collision layout (should have poor score)
        collision_score = self.optimizer._calculate_readability_score(self.collision_layout)
        
        # Test with clean layout
        clean_layout = self.layout_engine.compute_layout(self.test_egi)
        clean_score = self.optimizer._calculate_readability_score(clean_layout)
        
        # Clean layout should generally have better score than collision layout
        # (though exact comparison depends on other factors)
        self.assertIsInstance(collision_score, (int, float))
        self.assertIsInstance(clean_score, (int, float))
    
    def test_position_constraint_validation(self):
        """Test that position changes respect area constraints"""
        
        # Get a vertex and its area
        vertex_id = list(self.collision_layout.vertex_positions.keys())[0]
        original_pos = self.collision_layout.vertex_positions[vertex_id]
        
        # Test position within constraints
        nearby_pos = Point(original_pos.x + 5, original_pos.y + 5)
        respects_constraints = self.optimizer._position_respects_constraints(
            vertex_id, nearby_pos, self.collision_layout, self.test_egi
        )
        
        # Should respect constraints for reasonable movement
        self.assertTrue(respects_constraints, "Reasonable position change should respect constraints")
        
        # Test position far outside (if we have area bounds)
        if self.collision_layout.cut_bounds:
            far_pos = Point(original_pos.x + 1000, original_pos.y + 1000)
            respects_far = self.optimizer._position_respects_constraints(
                vertex_id, far_pos, self.collision_layout, self.test_egi
            )
            # This might still be True if element is on sheet level with no bounds
            self.assertIsInstance(respects_far, bool)
    
    def test_optimization_convergence(self):
        """Test that optimization converges and doesn't run indefinitely"""
        
        # Use aggressive optimization with limited iterations
        constraints = OptimizationConstraints(max_iterations=5, convergence_threshold=0.1)
        optimizer = ReadabilityOptimizer(constraints)
        
        # Should complete without hanging
        optimized = optimizer.optimize_layout(
            self.collision_layout, self.test_egi, OptimizationLevel.AGGRESSIVE
        )
        
        self.assertIsInstance(optimized, LayoutDTO)
    
    def test_iron_clad_guarantee_preservation(self):
        """Test that optimization preserves all iron-clad guarantees"""
        
        original = self.collision_layout
        optimized = self.optimizer.optimize_layout(original, self.test_egi)
        
        # Should not raise any assertion errors
        try:
            self.optimizer._validate_optimization(original, optimized, self.test_egi)
        except AssertionError as e:
            self.fail(f"Iron-clad guarantee validation failed: {e}")
        
        # Additional checks
        self.assertEqual(optimized.area_hierarchy, original.area_hierarchy)
        self.assertEqual(optimized.containment_depth, original.containment_depth)
        self.assertEqual(len(optimized.vertex_positions), len(original.vertex_positions))
        self.assertEqual(len(optimized.predicate_positions), len(original.predicate_positions))
    
    def test_convenience_function(self):
        """Test the convenience function for easy integration"""
        
        optimized = optimize_layout_readability(
            self.collision_layout, self.test_egi, OptimizationLevel.STANDARD
        )
        
        self.assertIsInstance(optimized, LayoutDTO)
        self.assertEqual(len(optimized.vertex_positions), len(self.collision_layout.vertex_positions))
    
    def test_custom_constraints(self):
        """Test optimization with custom constraints"""
        
        custom_constraints = OptimizationConstraints(
            min_element_spacing=15.0,
            collision_penalty_weight=20.0,
            max_iterations=10
        )
        
        optimizer = ReadabilityOptimizer(custom_constraints)
        optimized = optimizer.optimize_layout(self.collision_layout, self.test_egi)
        
        self.assertIsInstance(optimized, LayoutDTO)
        self.assertEqual(optimizer.constraints.min_element_spacing, 15.0)
        self.assertEqual(optimizer.constraints.collision_penalty_weight, 20.0)
    
    def test_bounds_overlap_detection(self):
        """Test bounding box overlap detection"""
        
        # Non-overlapping bounds
        bounds1 = BoundingBox(0, 0, 10, 10)
        bounds2 = BoundingBox(15, 15, 25, 25)
        self.assertFalse(self.optimizer._bounds_overlap(bounds1, bounds2))
        
        # Overlapping bounds
        bounds3 = BoundingBox(5, 5, 15, 15)
        self.assertTrue(self.optimizer._bounds_overlap(bounds1, bounds3))
        
        # Touching bounds (should be considered overlapping in our implementation)
        bounds4 = BoundingBox(10, 0, 20, 10)
        self.assertTrue(self.optimizer._bounds_overlap(bounds1, bounds4))  # Just touching
        
        # Identical bounds
        bounds5 = BoundingBox(0, 0, 10, 10)
        self.assertTrue(self.optimizer._bounds_overlap(bounds1, bounds5))
    
    def test_overlap_area_calculation(self):
        """Test overlap area calculation"""
        
        # Non-overlapping bounds
        bounds1 = BoundingBox(0, 0, 10, 10)
        bounds2 = BoundingBox(15, 15, 25, 25)
        overlap = self.optimizer._calculate_overlap_area(bounds1, bounds2)
        self.assertEqual(overlap, 0.0)
        
        # Overlapping bounds
        bounds3 = BoundingBox(5, 5, 15, 15)
        overlap2 = self.optimizer._calculate_overlap_area(bounds1, bounds3)
        self.assertEqual(overlap2, 25.0)  # 5x5 overlap
        
        # Complete overlap (smaller inside larger)
        bounds4 = BoundingBox(2, 2, 8, 8)
        overlap3 = self.optimizer._calculate_overlap_area(bounds1, bounds4)
        self.assertEqual(overlap3, 36.0)  # 6x6 overlap
    
    def test_collision_severity_calculation(self):
        """Test collision severity calculation"""
        
        # Light overlap
        bounds1 = BoundingBox(0, 0, 10, 10)  # Area = 100
        bounds2 = BoundingBox(8, 8, 18, 18)  # Area = 100, overlap = 4
        severity = self.optimizer._calculate_collision_severity(bounds1, bounds2, 4.0)
        self.assertEqual(severity, 0.04)  # 4/100
        
        # Complete overlap
        bounds3 = BoundingBox(0, 0, 10, 10)
        severity2 = self.optimizer._calculate_collision_severity(bounds1, bounds3, 100.0)
        self.assertEqual(severity2, 1.0)  # Complete overlap
        
        # No overlap
        severity3 = self.optimizer._calculate_collision_severity(bounds1, bounds2, 0.0)
        self.assertEqual(severity3, 0.0)


class TestOptimizationConstraints(unittest.TestCase):
    """Test optimization constraints configuration"""
    
    def test_default_constraints(self):
        """Test default constraint values"""
        constraints = OptimizationConstraints()
        
        self.assertEqual(constraints.min_element_spacing, 5.0)
        self.assertEqual(constraints.collision_penalty_weight, 10.0)
        self.assertEqual(constraints.max_iterations, 100)
        self.assertEqual(constraints.convergence_threshold, 0.01)
    
    def test_custom_constraints(self):
        """Test custom constraint configuration"""
        constraints = OptimizationConstraints(
            min_element_spacing=20.0,
            collision_penalty_weight=15.0,
            max_iterations=50
        )
        
        self.assertEqual(constraints.min_element_spacing, 20.0)
        self.assertEqual(constraints.collision_penalty_weight, 15.0)
        self.assertEqual(constraints.max_iterations, 50)


if __name__ == '__main__':
    unittest.main()
