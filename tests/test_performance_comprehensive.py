"""
Comprehensive Performance Validation Testing Suite

Tests performance characteristics of all major components:
- Large graph handling (1000+ vertices)
- Memory usage patterns and limits
- Algorithmic complexity validation
- Concurrent operation performance
- Stress testing under load
- Performance regression detection
"""

import gc
import math
import psutil
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Tuple
import os

import pytest

from src.egi_core_dau import (
    create_empty_graph,
    create_vertex,
    create_edge,
    create_cut,
    RelationalGraphWithCuts
)
from src.graph_isomorphism_engine import GraphIsomorphismEngine
from src.egif_generator_dau import generate_egif
from src.egif_parser_dau import parse_egif
from src.cgif_generator_dau import generate_cgif
from src.cgif_parser_dau import parse_cgif
from src.clif_generator_dau import generate_clif
from src.clif_parser_dau import parse_clif
from src.formal_transformation_rules import (
    IterationRule,
    DeiterationRule,
    DoubleCutIntroductionRule,
    DoubleCutErasureRule,
    InsertionRule,
    ErasureRule
)
from src.ligature_manipulation_rules import LigatureManipulationEngine
from src.history_persistence import HistoryPersistenceManager


class PerformanceMetrics:
    """Container for performance measurement results."""
    
    def __init__(self):
        self.execution_time: float = 0.0
        self.memory_usage_mb: float = 0.0
        self.peak_memory_mb: float = 0.0
        self.operations_per_second: float = 0.0
        self.success_rate: float = 0.0
        self.error_count: int = 0
        self.additional_metrics: Dict[str, Any] = {}


class TestPerformanceComprehensive:
    """Comprehensive performance testing suite."""

    def setup_method(self):
        """Set up performance testing environment."""
        self.process = psutil.Process(os.getpid())
        self.baseline_memory = self.process.memory_info().rss
        
        # Initialize engines for testing
        self.isomorphism_engine = GraphIsomorphismEngine()
        self.ligature_engine = LigatureManipulationEngine()
        
        # Performance thresholds (adjust based on requirements)
        self.thresholds = {
            "small_graph_parse_time": 0.1,      # 100ms for small graphs
            "medium_graph_parse_time": 1.0,     # 1s for medium graphs  
            "large_graph_parse_time": 10.0,     # 10s for large graphs
            "memory_growth_limit_mb": 500,      # 500MB memory growth limit
            "isomorphism_time_limit": 5.0,      # 5s for isomorphism check
            "transformation_time_limit": 2.0,   # 2s for transformations
            "concurrent_operations": 10,        # Support 10 concurrent operations
        }

    def teardown_method(self):
        """Clean up after performance tests."""
        # Force garbage collection
        gc.collect()

    # ==================== GRAPH CREATION PERFORMANCE ====================

    def test_graph_creation_performance(self):
        """Test performance of creating graphs of various sizes."""
        sizes = [10, 100, 500, 1000, 2000]
        metrics = {}
        
        for size in sizes:
            start_memory = self.process.memory_info().rss
            start_time = time.time()
            
            # Create graph
            egi = self._create_performance_test_graph(size)
            
            end_time = time.time()
            end_memory = self.process.memory_info().rss
            
            creation_time = end_time - start_time
            memory_used = (end_memory - start_memory) / 1024 / 1024  # MB
            
            metrics[size] = {
                "creation_time": creation_time,
                "memory_used_mb": memory_used,
                "vertices_per_second": size / creation_time if creation_time > 0 else float('inf')
            }
            
            # Verify graph was created correctly
            assert len(egi.V) == size
            assert len(egi.E) >= size // 2  # Should have reasonable number of edges
            
            print(f"Graph size {size}: {creation_time:.3f}s, {memory_used:.1f}MB, {metrics[size]['vertices_per_second']:.0f} vertices/s")
        
        # Verify performance scales reasonably (should be roughly linear)
        for i in range(1, len(sizes)):
            prev_size, curr_size = sizes[i-1], sizes[i]
            prev_time, curr_time = metrics[prev_size]["creation_time"], metrics[curr_size]["creation_time"]
            
            # Time should scale roughly linearly (allow 3x factor for overhead)
            expected_time = prev_time * (curr_size / prev_size)
            assert curr_time <= expected_time * 3, f"Performance degradation at size {curr_size}"

    def test_graph_modification_performance(self):
        """Test performance of modifying existing graphs."""
        base_egi = self._create_performance_test_graph(1000)
        
        # Test vertex addition performance
        start_time = time.time()
        modified_egi = base_egi
        for i in range(100):
            new_vertex = create_vertex(label=f"Added_{i}", is_generic=True)
            modified_egi = modified_egi.with_vertex(new_vertex)
        
        vertex_addition_time = time.time() - start_time
        assert vertex_addition_time < 1.0, f"Vertex addition too slow: {vertex_addition_time:.3f}s"
        
        # Test edge addition performance
        start_time = time.time()
        for i in range(50):
            new_edge = create_edge(relation=f"AddedRel_{i}")
            modified_egi = modified_egi.with_edge(new_edge)
        
        edge_addition_time = time.time() - start_time
        assert edge_addition_time < 1.0, f"Edge addition too slow: {edge_addition_time:.3f}s"
        
        # Verify final graph
        assert len(modified_egi.V) == len(base_egi.V) + 100
        assert len(modified_egi.E) == len(base_egi.E) + 50

    # ==================== PARSING PERFORMANCE ====================

    def test_linear_format_parsing_performance(self):
        """Test performance of parsing different linear formats."""
        test_sizes = [10, 50, 100, 200]
        
        for size in test_sizes:
            # Create test EGI
            test_egi = self._create_performance_test_graph(size)
            
            # Test EGIF parsing performance
            egif_text = generate_egif(test_egi)
            start_time = time.time()
            parsed_egi = parse_egif(egif_text)
            egif_parse_time = time.time() - start_time
            
            # Test CGIF parsing performance
            cgif_text = generate_cgif(test_egi)
            start_time = time.time()
            parsed_egi = parse_cgif(cgif_text)
            cgif_parse_time = time.time() - start_time
            
            # Test CLIF parsing performance
            clif_text = generate_clif(test_egi)
            start_time = time.time()
            parsed_egi = parse_clif(clif_text)
            clif_parse_time = time.time() - start_time
            
            # Verify performance thresholds
            threshold = self.thresholds["small_graph_parse_time"] if size <= 50 else self.thresholds["medium_graph_parse_time"]
            
            assert egif_parse_time < threshold, f"EGIF parsing too slow for size {size}: {egif_parse_time:.3f}s"
            assert cgif_parse_time < threshold, f"CGIF parsing too slow for size {size}: {cgif_parse_time:.3f}s"
            assert clif_parse_time < threshold, f"CLIF parsing too slow for size {size}: {clif_parse_time:.3f}s"
            
            print(f"Size {size} - EGIF: {egif_parse_time:.3f}s, CGIF: {cgif_parse_time:.3f}s, CLIF: {clif_parse_time:.3f}s")

    def test_large_graph_parsing_stress(self):
        """Stress test parsing with very large graphs."""
        # Create large graph
        large_egi = self._create_performance_test_graph(1000)
        
        # Test EGIF with large graph
        egif_text = generate_egif(large_egi)
        start_time = time.time()
        start_memory = self.process.memory_info().rss
        
        parsed_egi = parse_egif(egif_text)
        
        parse_time = time.time() - start_time
        memory_used = (self.process.memory_info().rss - start_memory) / 1024 / 1024
        
        # Verify performance
        assert parse_time < self.thresholds["large_graph_parse_time"], f"Large graph parsing too slow: {parse_time:.3f}s"
        assert memory_used < self.thresholds["memory_growth_limit_mb"], f"Excessive memory usage: {memory_used:.1f}MB"
        
        # Verify correctness
        assert len(parsed_egi.V) == len(large_egi.V)
        assert len(parsed_egi.E) == len(large_egi.E)

    # ==================== ISOMORPHISM PERFORMANCE ====================

    def test_isomorphism_performance_scaling(self):
        """Test isomorphism engine performance with different graph sizes."""
        sizes = [10, 25, 50, 75, 100]
        
        for size in sizes:
            # Create two similar graphs
            egi1 = self._create_performance_test_graph(size, seed=42)
            egi2 = self._create_performance_test_graph(size, seed=42)  # Same seed = isomorphic
            
            # Test isomorphism check performance
            start_time = time.time()
            result = self.isomorphism_engine.test_cross_egi_isomorphism(
                egi1, frozenset(egi1.get_all_elements()),
                egi2, frozenset(egi2.get_all_elements())
            )
            isomorphism_time = time.time() - start_time
            
            # Verify result and performance
            assert result.is_isomorphic, f"Isomorphic graphs not detected as such (size {size})"
            assert isomorphism_time < self.thresholds["isomorphism_time_limit"], f"Isomorphism check too slow for size {size}: {isomorphism_time:.3f}s"
            
            print(f"Isomorphism size {size}: {isomorphism_time:.3f}s")

    def test_isomorphism_worst_case_performance(self):
        """Test isomorphism performance in worst-case scenarios."""
        # Create graphs that are almost isomorphic (should take longer to verify)
        base_egi = self._create_performance_test_graph(50)
        
        # Create slightly different graph
        different_vertex = create_vertex(label="Different", is_generic=False)
        modified_egi = base_egi.with_vertex(different_vertex)
        
        start_time = time.time()
        result = self.isomorphism_engine.test_cross_egi_isomorphism(
            base_egi, frozenset(base_egi.get_all_elements()),
            modified_egi, frozenset(modified_egi.get_all_elements())
        )
        worst_case_time = time.time() - start_time
        
        # Should correctly identify as non-isomorphic
        assert not result.is_isomorphic
        assert worst_case_time < self.thresholds["isomorphism_time_limit"] * 2  # Allow more time for worst case

    # ==================== TRANSFORMATION PERFORMANCE ====================

    def test_transformation_rules_performance(self):
        """Test performance of formal transformation rules."""
        test_egi = self._create_performance_test_graph(100)
        
        # Test each transformation rule
        rules = [
            IterationRule(),
            DeiterationRule(),
            DoubleCutIntroductionRule(),
            DoubleCutErasureRule(),
            InsertionRule(),
            ErasureRule()
        ]
        
        for rule in rules:
            rule_name = rule.get_rule_name()
            
            # Create appropriate context for the rule
            context = self._create_transformation_context(test_egi, rule_name)
            
            # Test precondition checking performance
            start_time = time.time()
            preconditions = rule.check_preconditions(context)
            precondition_time = time.time() - start_time
            
            if preconditions.valid:
                # Test transformation application performance
                start_time = time.time()
                result = rule.apply_transformation(context)
                transformation_time = time.time() - start_time
                
                assert transformation_time < self.thresholds["transformation_time_limit"], f"{rule_name} too slow: {transformation_time:.3f}s"
                
                if result.success:
                    print(f"{rule_name}: precondition {precondition_time:.3f}s, transformation {transformation_time:.3f}s")

    def test_ligature_manipulation_performance(self):
        """Test performance of ligature manipulation algorithms."""
        # Create graph with ligature opportunities
        ligature_egi = self._create_ligature_test_graph(200)
        
        # Test ligature detection performance
        start_time = time.time()
        validation_result = self.ligature_engine.validate_ligatures(ligature_egi)
        detection_time = time.time() - start_time
        
        assert detection_time < 5.0, f"Ligature detection too slow: {detection_time:.3f}s"
        assert validation_result.is_valid
        
        print(f"Ligature detection (200 vertices): {detection_time:.3f}s")

    # ==================== CONCURRENT PERFORMANCE ====================

    def test_concurrent_parsing_performance(self):
        """Test performance of concurrent parsing operations."""
        # Create test data
        test_egis = [self._create_performance_test_graph(50, seed=i) for i in range(10)]
        egif_texts = [generate_egif(egi) for egi in test_egis]
        
        def parse_worker(egif_text: str) -> Tuple[bool, float]:
            start_time = time.time()
            try:
                parsed_egi = parse_egif(egif_text)
                parse_time = time.time() - start_time
                return True, parse_time
            except Exception:
                return False, time.time() - start_time
        
        # Test concurrent parsing
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=self.thresholds["concurrent_operations"]) as executor:
            futures = [executor.submit(parse_worker, text) for text in egif_texts]
            results = [future.result() for future in as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Verify all succeeded
        success_count = sum(1 for success, _ in results if success)
        assert success_count == len(test_egis), f"Only {success_count}/{len(test_egis)} concurrent parses succeeded"
        
        # Verify performance
        avg_parse_time = sum(parse_time for _, parse_time in results) / len(results)
        assert total_time < 5.0, f"Concurrent parsing took too long: {total_time:.3f}s"
        
        print(f"Concurrent parsing: {total_time:.3f}s total, {avg_parse_time:.3f}s average")

    def test_concurrent_isomorphism_performance(self):
        """Test performance of concurrent isomorphism checks."""
        # Create test graph pairs
        base_egi = self._create_performance_test_graph(30)
        test_pairs = [(base_egi, self._create_performance_test_graph(30, seed=i)) for i in range(8)]
        
        def isomorphism_worker(egi_pair: Tuple[RelationalGraphWithCuts, RelationalGraphWithCuts]) -> Tuple[bool, float]:
            egi1, egi2 = egi_pair
            start_time = time.time()
            try:
                result = self.isomorphism_engine.test_cross_egi_isomorphism(
                    egi1, frozenset(egi1.get_all_elements()),
                    egi2, frozenset(egi2.get_all_elements())
                )
                check_time = time.time() - start_time
                return True, check_time
            except Exception:
                return False, time.time() - start_time
        
        # Test concurrent isomorphism checks
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(isomorphism_worker, pair) for pair in test_pairs]
            results = [future.result() for future in as_completed(futures)]
        
        total_time = time.time() - start_time
        
        # Verify results
        success_count = sum(1 for success, _ in results if success)
        assert success_count == len(test_pairs), f"Only {success_count}/{len(test_pairs)} concurrent checks succeeded"
        
        print(f"Concurrent isomorphism: {total_time:.3f}s total")

    # ==================== MEMORY PERFORMANCE ====================

    def test_memory_usage_scaling(self):
        """Test memory usage scaling with graph size."""
        sizes = [100, 200, 500, 1000]
        memory_measurements = {}
        
        for size in sizes:
            # Measure memory before
            gc.collect()
            memory_before = self.process.memory_info().rss
            
            # Create graph
            egi = self._create_performance_test_graph(size)
            
            # Measure memory after
            memory_after = self.process.memory_info().rss
            memory_used = (memory_after - memory_before) / 1024 / 1024  # MB
            
            memory_measurements[size] = memory_used
            
            print(f"Graph size {size}: {memory_used:.1f}MB")
            
            # Clean up
            del egi
            gc.collect()
        
        # Verify memory usage scales reasonably (should be roughly linear)
        for i in range(1, len(sizes)):
            prev_size, curr_size = sizes[i-1], sizes[i]
            prev_memory, curr_memory = memory_measurements[prev_size], memory_measurements[curr_size]
            
            # Memory should scale roughly linearly (allow 2x factor for overhead)
            expected_memory = prev_memory * (curr_size / prev_size)
            assert curr_memory <= expected_memory * 2, f"Memory usage scaling issue at size {curr_size}"

    def test_memory_leak_detection(self):
        """Test for memory leaks in repeated operations."""
        initial_memory = self.process.memory_info().rss
        
        # Perform many operations that should not leak memory
        for i in range(100):
            # Create and destroy graphs
            egi = self._create_performance_test_graph(50)
            egif_text = generate_egif(egi)
            parsed_egi = parse_egif(egif_text)
            
            # Force cleanup
            del egi, parsed_egi
            
            # Periodic garbage collection
            if i % 20 == 0:
                gc.collect()
        
        # Final cleanup and measurement
        gc.collect()
        final_memory = self.process.memory_info().rss
        memory_growth = (final_memory - initial_memory) / 1024 / 1024  # MB
        
        # Should not have significant memory growth
        assert memory_growth < 50, f"Potential memory leak detected: {memory_growth:.1f}MB growth"
        
        print(f"Memory growth after 100 operations: {memory_growth:.1f}MB")

    # ==================== STRESS TESTING ====================

    def test_extreme_load_stress(self):
        """Stress test with extreme loads."""
        # Test with very large graph
        large_egi = self._create_performance_test_graph(2000)
        
        start_time = time.time()
        start_memory = self.process.memory_info().rss
        
        # Perform multiple operations
        egif_text = generate_egif(large_egi)
        parsed_egi = parse_egif(egif_text)
        
        # Test isomorphism with subset
        subset_elements = frozenset(list(large_egi.get_all_elements())[:100])
        isomorphism_result = self.isomorphism_engine.test_cross_egi_isomorphism(
            large_egi, subset_elements,
            parsed_egi, subset_elements
        )
        
        end_time = time.time()
        end_memory = self.process.memory_info().rss
        
        total_time = end_time - start_time
        memory_used = (end_memory - start_memory) / 1024 / 1024
        
        # Verify operations completed successfully
        assert len(parsed_egi.V) == len(large_egi.V)
        assert isomorphism_result.is_isomorphic
        
        # Verify performance within acceptable bounds
        assert total_time < 60.0, f"Stress test took too long: {total_time:.1f}s"
        assert memory_used < 1000, f"Excessive memory usage: {memory_used:.1f}MB"
        
        print(f"Stress test (2000 vertices): {total_time:.1f}s, {memory_used:.1f}MB")

    def test_persistence_performance_stress(self):
        """Stress test persistence operations."""
        import tempfile
        
        temp_dir = tempfile.mkdtemp()
        persistence_manager = HistoryPersistenceManager(temp_dir)
        
        try:
            # Create large history
            large_history = self._create_large_transformation_history(100)  # 100 steps
            
            # Test save performance
            start_time = time.time()
            json_path = persistence_manager.save_history_json(large_history)
            save_time = time.time() - start_time
            
            # Test load performance
            start_time = time.time()
            loaded_history = persistence_manager.load_history_json(json_path)
            load_time = time.time() - start_time
            
            # Verify performance
            assert save_time < 30.0, f"History save too slow: {save_time:.1f}s"
            assert load_time < 30.0, f"History load too slow: {load_time:.1f}s"
            
            # Verify correctness
            assert len(loaded_history.branches["main"].steps) == 100
            
            print(f"Persistence (100 steps): save {save_time:.1f}s, load {load_time:.1f}s")
            
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    # ==================== HELPER METHODS ====================

    def _create_performance_test_graph(self, num_vertices: int, seed: int = None) -> RelationalGraphWithCuts:
        """Create graph for performance testing with specified characteristics."""
        if seed is not None:
            import random
            random.seed(seed)
        
        egi = create_empty_graph()
        
        # Create vertices
        vertices = []
        for i in range(num_vertices):
            vertex = create_vertex(
                label=f"PerfVertex_{i}" if i % 3 == 0 else None,
                is_generic=i % 3 != 0
            )
            vertices.append(vertex)
            egi = egi.with_vertex(vertex)
        
        # Create edges (roughly half as many as vertices)
        num_edges = max(1, num_vertices // 2)
        for i in range(num_edges):
            edge = create_edge(relation=f"PerfRel_{i % 10}")  # Reuse relation names
            egi = egi.with_edge(edge)
            
            # Connect to vertices
            if i < len(vertices) - 1:
                egi = egi.with_nu_entry(edge.id, (vertices[i].id, vertices[i + 1].id))
            elif len(vertices) > 0:
                egi = egi.with_nu_entry(edge.id, (vertices[0].id,))
        
        # Add some cuts for complexity
        num_cuts = max(1, num_vertices // 20)
        for i in range(num_cuts):
            cut = create_cut()
            egi = egi.with_cut(cut)
        
        return egi

    def _create_ligature_test_graph(self, num_vertices: int) -> RelationalGraphWithCuts:
        """Create graph with ligature opportunities for performance testing."""
        egi = create_empty_graph()
        
        # Create central hub vertex (ligature opportunity)
        hub_vertex = create_vertex(label="Hub", is_generic=True)
        egi = egi.with_vertex(hub_vertex)
        
        # Create spoke vertices
        spoke_vertices = []
        for i in range(num_vertices - 1):
            vertex = create_vertex(label=f"Spoke_{i}", is_generic=True)
            spoke_vertices.append(vertex)
            egi = egi.with_vertex(vertex)
            
            # Connect to hub (creates ligature at hub)
            edge = create_edge(relation=f"Connection_{i % 5}")  # Reuse relations
            egi = egi.with_edge(edge)
            egi = egi.with_nu_entry(edge.id, (hub_vertex.id, vertex.id))
        
        return egi

    def _create_transformation_context(self, egi: RelationalGraphWithCuts, rule_name: str):
        """Create appropriate transformation context for testing."""
        from src.formal_transformation_rules import TransformationContext, AreaPolarity
        
        # Select appropriate subgraph based on rule
        if "ITERATION" in rule_name or "DEITERATION" in rule_name:
            # Select a small subgraph for iteration rules
            selected_elements = frozenset(list(egi.get_all_elements())[:3])
        else:
            # Select single element for other rules
            selected_elements = frozenset([list(egi.V)[0].id]) if egi.V else frozenset()
        
        return TransformationContext(
            source_egi=egi,
            target_area=egi.sheet,
            selected_subgraph=selected_elements,
            area_polarity=AreaPolarity.POSITIVE,
            nesting_depth=0
        )

    def _create_large_transformation_history(self, num_steps: int):
        """Create large transformation history for persistence testing."""
        from src.enhanced_transformation_history import (
            EnhancedEGITransformationHistory,
            CollaborationMetadata
        )
        from src.egi_transformation_history import (
            HistoryBranch,
            HistoryBranchType,
            TransformationStep,
            LogicalProvenance
        )
        from src.formal_transformation_rules import TransformationResult
        
        base_egi = self._create_performance_test_graph(50)
        
        # Create many transformation steps
        steps = []
        for i in range(num_steps):
            step = TransformationStep(
                step_id=f"perf_step_{i}",
                rule_name=f"PerfRule_{i % 6}",
                source_egi=base_egi,
                target_egi=base_egi,
                context=self._create_transformation_context(base_egi, "TEST"),
                result=TransformationResult(
                    success=True,
                    transformed_egi=base_egi,
                    applied_rule="PerfRule",
                    validation_passed=True
                ),
                timestamp=f"2024-01-{(i % 30) + 1:02d}T{(i % 24):02d}:00:00Z",
                metadata={"performance_test": True, "step_index": i}
            )
            steps.append(step)
        
        # Create branch
        main_branch = HistoryBranch(
            branch_id="main",
            branch_type=HistoryBranchType.MAIN,
            parent_branch_id=None,
            branch_point_step_id=None,
            steps=steps,
            metadata={"performance_test": True}
        )
        
        # Create collaboration metadata
        collaboration = CollaborationMetadata(
            contributors=["perf_tester"],
            creation_timestamp="2024-01-01T00:00:00Z",
            last_modified="2024-01-31T23:59:59Z",
            version="1.0.0",
            tags=["performance", "test"],
            description="Large history for performance testing"
        )
        
        return EnhancedEGITransformationHistory(
            history_id=str(uuid.uuid4()),
            initial_egi=base_egi,
            branches={"main": main_branch},
            current_branch_id="main",
            collaboration_metadata=collaboration,
            logical_provenance=LogicalProvenance(
                proof_steps=[],
                semantic_annotations={},
                validation_checkpoints={}
            )
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s to see print output
