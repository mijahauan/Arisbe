"""
Comprehensive Error Handling Testing Suite

Tests error handling and recovery across all components:
- Invalid input handling
- Graceful degradation
- Error recovery mechanisms
- Boundary condition handling
- Resource exhaustion scenarios
- Exception propagation and logging
"""

import pytest
import tempfile
from pathlib import Path
from typing import Any, Dict

from src.egi_core_dau import create_empty_graph, create_vertex, create_edge
from src.egif_parser_dau import parse_egif
from src.cgif_parser_dau import parse_cgif
from src.clif_parser_dau import parse_clif
from src.graph_isomorphism_engine import GraphIsomorphismEngine
from src.formal_transformation_rules import IterationRule, TransformationContext, AreaPolarity
from src.history_persistence import HistoryPersistenceManager


class TestErrorHandlingComprehensive:
    """Comprehensive error handling test suite."""

    def setup_method(self):
        """Set up error handling test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.isomorphism_engine = GraphIsomorphismEngine()
        self.persistence_manager = HistoryPersistenceManager(self.temp_dir)

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # ==================== PARSING ERROR HANDLING ====================

    def test_egif_parser_invalid_input(self):
        """Test EGIF parser error handling with invalid inputs."""
        invalid_inputs = [
            "",  # Empty string
            "invalid egif content",  # Invalid format
            "[*x] (Human x) (Mortal",  # Incomplete expression
            "[*x *y] (Human x) (Loves x y) (Mortal z)",  # Undefined variable
            "[*x] (Human x) (Loves x)",  # Arity mismatch
            "[]",  # Empty quantification
            "[*] (Human x)",  # Invalid quantifier
        ]
        
        for invalid_input in invalid_inputs:
            with pytest.raises(Exception):  # Should raise appropriate parsing error
                parse_egif(invalid_input)

    def test_cgif_parser_invalid_input(self):
        """Test CGIF parser error handling with invalid inputs."""
        invalid_inputs = [
            "",
            "[Human",  # Incomplete concept
            "[Human: Socrates] -> [Mortal",  # Incomplete relation
            "[Human: ] -> [Mortal: Socrates]",  # Empty referent
            "[InvalidRelation: Socrates] -> []",  # Empty target
            "[Human: Socrates] -> [Human: Socrates] -> [Mortal]",  # Invalid chaining
        ]
        
        for invalid_input in invalid_inputs:
            with pytest.raises(Exception):
                parse_cgif(invalid_input)

    def test_clif_parser_invalid_input(self):
        """Test CLIF parser error handling with invalid inputs."""
        invalid_inputs = [
            "",
            "(Human",  # Incomplete expression
            "(forall (x) (Human x) (Mortal)",  # Incomplete quantification
            "(exists () (Human x))",  # Empty variable list
            "(Human x y z)",  # Too many arguments
            "(and (Human x) (or))",  # Empty disjunction
        ]
        
        for invalid_input in invalid_inputs:
            with pytest.raises(Exception):
                parse_clif(invalid_input)

    # ==================== TRANSFORMATION ERROR HANDLING ====================

    def test_transformation_invalid_context(self):
        """Test transformation error handling with invalid contexts."""
        rule = IterationRule()
        
        # Test with None EGI
        with pytest.raises(Exception):
            invalid_context = TransformationContext(
                source_egi=None,
                target_area="sheet",
                selected_subgraph=frozenset(),
                area_polarity=AreaPolarity.POSITIVE,
                nesting_depth=0
            )
            rule.check_preconditions(invalid_context)

    def test_transformation_empty_selection(self):
        """Test transformation with empty selections."""
        rule = IterationRule()
        egi = create_empty_graph()
        
        context = TransformationContext(
            source_egi=egi,
            target_area="sheet",
            selected_subgraph=frozenset(),  # Empty selection
            area_polarity=AreaPolarity.POSITIVE,
            nesting_depth=0
        )
        
        # Should handle gracefully
        preconditions = rule.check_preconditions(context)
        assert not preconditions.valid  # Should fail preconditions

    # ==================== ISOMORPHISM ERROR HANDLING ====================

    def test_isomorphism_invalid_inputs(self):
        """Test isomorphism engine error handling."""
        # Test with None inputs
        with pytest.raises(Exception):
            self.isomorphism_engine.test_cross_egi_isomorphism(
                None, frozenset(), None, frozenset()
            )
        
        # Test with mismatched element sets
        egi = create_empty_graph().with_vertex(create_vertex(label="Test", is_generic=False))
        
        result = self.isomorphism_engine.test_cross_egi_isomorphism(
            egi, frozenset(["nonexistent_id"]),  # Invalid element ID
            egi, frozenset(["nonexistent_id"])
        )
        
        # Should handle gracefully
        assert not result.is_isomorphic

    # ==================== PERSISTENCE ERROR HANDLING ====================

    def test_persistence_invalid_files(self):
        """Test persistence error handling with invalid files."""
        # Test loading non-existent file
        with pytest.raises(FileNotFoundError):
            self.persistence_manager.load_history_json("nonexistent.json")
        
        # Test loading corrupted JSON
        corrupted_file = Path(self.temp_dir) / "corrupted.json"
        with open(corrupted_file, 'w') as f:
            f.write('{"invalid": json content')
        
        with pytest.raises(Exception):
            self.persistence_manager.load_history_json(corrupted_file)

    def test_persistence_permission_errors(self):
        """Test persistence error handling with permission issues."""
        # Create read-only directory
        readonly_dir = Path(self.temp_dir) / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Read-only
        
        try:
            readonly_manager = HistoryPersistenceManager(readonly_dir)
            # Should handle permission errors gracefully
            with pytest.raises(PermissionError):
                test_history = self._create_minimal_history()
                readonly_manager.save_history_json(test_history)
        finally:
            readonly_dir.chmod(0o755)  # Restore permissions for cleanup

    # ==================== RESOURCE EXHAUSTION HANDLING ====================

    def test_memory_exhaustion_handling(self):
        """Test handling of memory exhaustion scenarios."""
        # This test is challenging to implement safely
        # We'll test with reasonable large structures instead
        
        try:
            # Create very large structure
            large_egi = create_empty_graph()
            for i in range(10000):  # Large but not memory-exhausting
                vertex = create_vertex(label=f"V_{i}", is_generic=True)
                large_egi = large_egi.with_vertex(vertex)
            
            # Should handle large structures gracefully
            assert len(large_egi.V) == 10000
            
        except MemoryError:
            # If memory error occurs, it should be handled gracefully
            pytest.skip("Memory exhaustion test skipped due to system limitations")

    # ==================== HELPER METHODS ====================

    def _create_minimal_history(self):
        """Create minimal history for testing."""
        from src.enhanced_transformation_history import (
            EnhancedEGITransformationHistory,
            CollaborationMetadata
        )
        from src.egi_transformation_history import (
            HistoryBranch,
            HistoryBranchType,
            LogicalProvenance
        )
        
        egi = create_empty_graph()
        branch = HistoryBranch(
            branch_id="main",
            branch_type=HistoryBranchType.MAIN,
            parent_branch_id=None,
            branch_point_step_id=None,
            steps=[],
            metadata={}
        )
        
        collaboration = CollaborationMetadata(
            contributors=["test"],
            creation_timestamp="2024-01-01T00:00:00Z",
            last_modified="2024-01-01T00:00:00Z",
            version="1.0.0",
            tags=[],
            description="Test history"
        )
        
        return EnhancedEGITransformationHistory(
            history_id="test_history",
            initial_egi=egi,
            branches={"main": branch},
            current_branch_id="main",
            collaboration_metadata=collaboration,
            logical_provenance=LogicalProvenance(
                proof_steps=[],
                semantic_annotations={},
                validation_checkpoints={}
            )
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
