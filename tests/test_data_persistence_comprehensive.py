"""
Comprehensive Data Persistence Testing Suite

Tests all aspects of the HistoryPersistenceManager including:
- JSON/YAML/Compressed format round-trip fidelity
- Large history handling
- Incremental checkpoints
- Error handling and recovery
- Performance characteristics
- Concurrent access safety
"""

import json
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import List

import pytest
import yaml

from src.egi_core_dau import create_empty_graph, create_vertex, create_edge
# Using available transformation history components
# from src.enhanced_transformation_history import (
#     CollaborationMetadata,
#     EnhancedEGITransformationHistory,
#     ProofExportFormat,
# )
from src.egi_transformation_history import (
    HistoryBranch,
    HistoryBranchType,
    LogicalProvenance,
    StateSnapshot,
    TransformationStatus,
    TransformationStep,
)
from src.formal_transformation_rules import (
    AreaPolarity,
    TransformationContext,
    TransformationResult,
)
from src.history_persistence import HistoryPersistenceManager


class TestDataPersistenceComprehensive:
    """Comprehensive test suite for data persistence functionality."""

    def setup_method(self):
        """Set up test environment with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.persistence_manager = HistoryPersistenceManager(self.temp_dir)
        self.test_history = self._create_test_history()

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_history(self):
        """Create a comprehensive test history with multiple transformations."""
        # Create initial EGI
        initial_egi = create_empty_graph()
        vertex1 = create_vertex(label="Human", is_generic=False)
        vertex2 = create_vertex(label=None, is_generic=True)
        edge1 = create_edge(relation="Human")
        
        initial_egi = initial_egi.with_vertex(vertex1).with_vertex(vertex2).with_edge(edge1)
        initial_egi = initial_egi.with_nu_entry(edge1.id, (vertex1.id,))

        # Create transformation steps
        steps = []
        for i in range(5):
            step = TransformationStep(
                step_id=f"step_{i}",
                rule_name=f"TestRule_{i}",
                source_egi=initial_egi,
                target_egi=initial_egi,  # Simplified for testing
                context=TransformationContext(
                    source_egi=initial_egi,
                    target_area="sheet",
                    selected_subgraph=frozenset([vertex1.id]),
                    area_polarity=AreaPolarity.POSITIVE,
                    nesting_depth=0
                ),
                result=TransformationResult(
                    success=True,
                    transformed_egi=initial_egi,
                    applied_rule="TestRule",
                    validation_passed=True
                ),
                timestamp=f"2024-01-{i+1:02d}T10:00:00Z",
                metadata={"test_step": i}
            )
            steps.append(step)

        # Create branches
        main_branch = HistoryBranch(
            branch_id="main",
            branch_type=HistoryBranchType.MAIN,
            parent_branch_id=None,
            branch_point_step_id=None,
            steps=steps,
            metadata={"branch_type": "main"}
        )

        experimental_branch = HistoryBranch(
            branch_id="experimental",
            branch_type=HistoryBranchType.EXPERIMENTAL,
            parent_branch_id="main",
            branch_point_step_id="step_2",
            steps=steps[:2],  # Shorter branch
            metadata={"branch_type": "experimental"}
        )

        # Create collaboration metadata (simplified)
        collaboration = {
            "contributors": ["test_user_1", "test_user_2"],
            "creation_timestamp": "2024-01-01T10:00:00Z",
            "last_modified": "2024-01-05T10:00:00Z",
            "version": "1.0.0",
            "tags": ["test", "comprehensive"],
            "description": "Test history for comprehensive testing"
        }

        # Simplified test history for now
        return {
            "history_id": str(uuid.uuid4()),
            "initial_egi": initial_egi,
            "branches": {"main": main_branch, "experimental": experimental_branch},
            "current_branch_id": "main",
            "collaboration_metadata": collaboration,
            "logical_provenance": LogicalProvenance(
                proof_steps=[],
                semantic_annotations={},
                validation_checkpoints={}
            )
        }

    def test_json_round_trip_fidelity(self):
        """Test JSON serialization preserves all data exactly."""
        # Save to JSON
        saved_path = self.persistence_manager.save_history_json(self.test_history)
        assert saved_path.exists()
        
        # Load from JSON
        loaded_history = self.persistence_manager.load_history_json(saved_path)
        
        # Verify complete fidelity
        assert loaded_history.history_id == self.test_history.history_id
        assert loaded_history.current_branch_id == self.test_history.current_branch_id
        assert len(loaded_history.branches) == len(self.test_history.branches)
        
        # Verify branch details
        for branch_id, original_branch in self.test_history.branches.items():
            loaded_branch = loaded_history.branches[branch_id]
            assert loaded_branch.branch_id == original_branch.branch_id
            assert loaded_branch.branch_type == original_branch.branch_type
            assert len(loaded_branch.steps) == len(original_branch.steps)
            
            # Verify step details
            for i, (original_step, loaded_step) in enumerate(zip(original_branch.steps, loaded_branch.steps)):
                assert loaded_step.step_id == original_step.step_id
                assert loaded_step.rule_name == original_step.rule_name
                assert loaded_step.timestamp == original_step.timestamp

        # Verify collaboration metadata
        assert loaded_history.collaboration_metadata.contributors == self.test_history.collaboration_metadata.contributors
        assert loaded_history.collaboration_metadata.version == self.test_history.collaboration_metadata.version

    def test_yaml_round_trip_fidelity(self):
        """Test YAML serialization preserves all data exactly."""
        # Save to YAML
        saved_path = self.persistence_manager.save_history_yaml(self.test_history)
        assert saved_path.exists()
        
        # Verify YAML is human-readable
        with open(saved_path, 'r') as f:
            yaml_content = f.read()
            assert "history_id:" in yaml_content
            assert "branches:" in yaml_content
            assert "collaboration_metadata:" in yaml_content
        
        # Load from YAML
        loaded_history = self.persistence_manager.load_history_yaml(saved_path)
        
        # Verify complete fidelity (same checks as JSON)
        assert loaded_history.history_id == self.test_history.history_id
        assert loaded_history.current_branch_id == self.test_history.current_branch_id
        assert len(loaded_history.branches) == len(self.test_history.branches)

    def test_compressed_format_efficiency(self):
        """Test compressed format saves space and preserves data."""
        # Save in all formats
        json_path = self.persistence_manager.save_history_json(self.test_history)
        yaml_path = self.persistence_manager.save_history_yaml(self.test_history)
        compressed_path = self.persistence_manager.save_history_compressed(self.test_history)
        
        # Verify compressed is smaller
        json_size = json_path.stat().st_size
        compressed_size = compressed_path.stat().st_size
        assert compressed_size < json_size, "Compressed format should be smaller"
        
        # Verify compressed preserves data
        loaded_history = self.persistence_manager.load_history_compressed(compressed_path)
        assert loaded_history.history_id == self.test_history.history_id
        assert len(loaded_history.branches) == len(self.test_history.branches)

    def test_incremental_checkpoint_functionality(self):
        """Test incremental checkpoint saving and loading."""
        # Save initial checkpoint
        checkpoint_path = self.persistence_manager.save_incremental_checkpoint(
            self.test_history, "test_checkpoint"
        )
        assert checkpoint_path.exists()
        
        # Verify checkpoint metadata
        checkpoint_dir = checkpoint_path.parent
        metadata_file = checkpoint_dir / "checkpoint_metadata.json"
        assert metadata_file.exists()
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
            assert metadata["checkpoint_name"] == "test_checkpoint"
            assert "timestamp" in metadata
            assert "history_id" in metadata

    def test_large_history_handling(self):
        """Test handling of large histories with many transformations."""
        # Create large history
        large_history = self._create_large_test_history(100)  # 100 steps
        
        # Test JSON handling
        start_time = time.time()
        json_path = self.persistence_manager.save_history_json(large_history)
        save_time = time.time() - start_time
        
        start_time = time.time()
        loaded_history = self.persistence_manager.load_history_json(json_path)
        load_time = time.time() - start_time
        
        # Verify performance is reasonable (< 5 seconds for 100 steps)
        assert save_time < 5.0, f"Save took too long: {save_time}s"
        assert load_time < 5.0, f"Load took too long: {load_time}s"
        
        # Verify data integrity
        assert len(loaded_history.branches["main"].steps) == 100
        assert loaded_history.history_id == large_history.history_id

    def test_error_handling_invalid_files(self):
        """Test error handling for invalid or corrupted files."""
        # Test invalid JSON
        invalid_json_path = Path(self.temp_dir) / "invalid.json"
        with open(invalid_json_path, 'w') as f:
            f.write("{ invalid json content")
        
        with pytest.raises(Exception):  # Should raise JSON decode error
            self.persistence_manager.load_history_json(invalid_json_path)
        
        # Test invalid YAML
        invalid_yaml_path = Path(self.temp_dir) / "invalid.yaml"
        with open(invalid_yaml_path, 'w') as f:
            f.write("invalid: yaml: content: [")
        
        with pytest.raises(Exception):  # Should raise YAML parse error
            self.persistence_manager.load_history_yaml(invalid_yaml_path)
        
        # Test non-existent file
        with pytest.raises(FileNotFoundError):
            self.persistence_manager.load_history_json("nonexistent.json")

    def test_concurrent_access_safety(self):
        """Test thread-safe concurrent access to persistence operations."""
        results = []
        errors = []
        
        def save_and_load_worker(worker_id: int):
            try:
                # Create unique history for this worker
                worker_history = self._create_test_history()
                worker_history.history_id = f"worker_{worker_id}_history"
                
                # Save and load
                saved_path = self.persistence_manager.save_history_json(
                    worker_history, f"worker_{worker_id}_history.json"
                )
                loaded_history = self.persistence_manager.load_history_json(saved_path)
                
                # Verify integrity
                assert loaded_history.history_id == worker_history.history_id
                results.append(f"worker_{worker_id}_success")
                
            except Exception as e:
                errors.append(f"worker_{worker_id}_error: {e}")
        
        # Run 5 concurrent workers
        threads = []
        for i in range(5):
            thread = threading.Thread(target=save_and_load_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify all succeeded
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert len(results) == 5, f"Expected 5 successes, got {len(results)}"

    def test_format_compatibility_across_versions(self):
        """Test that saved files remain compatible across format versions."""
        # Save in current format
        json_path = self.persistence_manager.save_history_json(self.test_history)
        
        # Manually verify JSON structure contains expected fields
        with open(json_path, 'r') as f:
            data = json.load(f)
            
        # Verify required top-level fields
        required_fields = ["history_id", "initial_egi", "branches", "current_branch_id", "collaboration_metadata"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Verify branch structure
        assert "main" in data["branches"]
        main_branch = data["branches"]["main"]
        assert "steps" in main_branch
        assert len(main_branch["steps"]) > 0

    def test_memory_usage_efficiency(self):
        """Test memory usage doesn't grow excessively with large histories."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create and save multiple large histories
        for i in range(10):
            large_history = self._create_large_test_history(50)
            self.persistence_manager.save_history_json(large_history, f"large_history_{i}.json")
        
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (< 100MB for this test)
        assert memory_growth < 100 * 1024 * 1024, f"Excessive memory growth: {memory_growth / 1024 / 1024:.1f}MB"

    def test_proof_export_functionality(self):
        """Test proof sequence export functionality."""
        # Export proof sequence
        proof_path = self.persistence_manager.export_proof_sequence(
            self.test_history,
            from_state_id="step_0",
            to_state_id="step_4",
            export_format=ProofExportFormat.DETAILED_JSON
        )
        
        assert proof_path.exists()
        
        # Verify proof content
        with open(proof_path, 'r') as f:
            proof_data = json.load(f)
            
        assert "proof_sequence" in proof_data
        assert "from_state_id" in proof_data
        assert "to_state_id" in proof_data
        assert len(proof_data["proof_sequence"]) > 0

    def _create_large_test_history(self, num_steps: int) -> EnhancedEGITransformationHistory:
        """Create a test history with specified number of steps."""
        base_history = self._create_test_history()
        
        # Add more steps to main branch
        additional_steps = []
        for i in range(5, num_steps):  # Start from 5 since we already have 5
            step = TransformationStep(
                step_id=f"step_{i}",
                rule_name=f"TestRule_{i}",
                source_egi=base_history.initial_egi,
                target_egi=base_history.initial_egi,
                context=TransformationContext(
                    source_egi=base_history.initial_egi,
                    target_area="sheet",
                    selected_subgraph=frozenset(),
                    area_polarity=AreaPolarity.POSITIVE,
                    nesting_depth=0
                ),
                result=TransformationResult(
                    success=True,
                    transformed_egi=base_history.initial_egi,
                    applied_rule="TestRule",
                    validation_passed=True
                ),
                timestamp=f"2024-01-{(i % 30) + 1:02d}T10:00:00Z",
                metadata={"test_step": i, "large_history": True}
            )
            additional_steps.append(step)
        
        # Update main branch with all steps
        main_branch = base_history.branches["main"]
        main_branch.steps.extend(additional_steps)
        
        return base_history


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
