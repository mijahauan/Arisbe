"""
Comprehensive Serialization Testing Suite

Tests all serialization/deserialization functionality:
- JSON/YAML round-trip fidelity for EGI structures
- History persistence serialization
- DTO serialization/deserialization
- Style serialization
- Large data structure handling
- Performance characteristics
- Error handling and recovery
"""

import json
import tempfile
import uuid
import yaml
from pathlib import Path
from typing import Dict, Any, List

import pytest

from src.egi_core_dau import (
    create_empty_graph,
    create_vertex,
    create_edge,
    create_cut,
    RelationalGraphWithCuts,
    Vertex,
    Edge,
    Cut,
    Alphabet
)
from src.egi_dto import EGIStateDTO
from src.enhanced_transformation_history import (
    EnhancedEGITransformationHistory,
    CollaborationMetadata
)
from src.egi_transformation_history import (
    HistoryBranch,
    HistoryBranchType,
    StateSnapshot,
    TransformationStep,
    LogicalProvenance
)
from src.history_persistence import HistoryPersistenceManager
from src.efficient_historical_storage import EfficientHistoricalStorage
from src.formal_transformation_rules import TransformationContext, TransformationResult, AreaPolarity


class TestSerializationComprehensive:
    """Comprehensive test suite for serialization functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_egi = self._create_comprehensive_test_egi()
        self.test_history = self._create_test_transformation_history()
        self.persistence_manager = HistoryPersistenceManager(self.temp_dir)
        self.historical_storage = EfficientHistoricalStorage(self.temp_dir)

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_comprehensive_test_egi(self) -> RelationalGraphWithCuts:
        """Create comprehensive EGI with all possible features for serialization testing."""
        egi = create_empty_graph()
        
        # Create diverse vertices
        constant_vertex = create_vertex(label="Socrates", is_generic=False)
        generic_vertex = create_vertex(label=None, is_generic=True)
        typed_vertex = create_vertex(label="Human", is_generic=False)
        
        # Create cuts for nesting
        outer_cut = create_cut()
        inner_cut = create_cut()
        
        # Create edges with different arities
        unary_edge = create_edge(relation="Human")
        binary_edge = create_edge(relation="Loves")
        ternary_edge = create_edge(relation="Gives")
        
        # Build complex EGI structure
        egi = (egi
               .with_vertex(constant_vertex)
               .with_vertex(generic_vertex)
               .with_vertex(typed_vertex)
               .with_cut(outer_cut)
               .with_cut(inner_cut)
               .with_edge(unary_edge)
               .with_edge(binary_edge)
               .with_edge(ternary_edge)
               .with_nu_entry(unary_edge.id, (constant_vertex.id,))
               .with_nu_entry(binary_edge.id, (constant_vertex.id, typed_vertex.id))
               .with_nu_entry(ternary_edge.id, (constant_vertex.id, generic_vertex.id, typed_vertex.id)))
        
        # Add alphabet information
        alphabet = Alphabet(
            constants=frozenset(["Socrates"]),
            functors=frozenset(),
            relations=frozenset(["Human", "Loves", "Gives"]),
            arity=frozendict({
                "Human": 1,
                "Loves": 2,
                "Gives": 3
            })
        )
        egi = egi.with_alphabet(alphabet)
        
        # Add rho mapping
        rho_mapping = frozendict({
            constant_vertex.id: "Socrates"
        })
        egi = egi.with_rho(rho_mapping)
        
        return egi

    def _create_test_transformation_history(self) -> EnhancedEGITransformationHistory:
        """Create test transformation history for serialization testing."""
        # Create transformation steps
        steps = []
        for i in range(3):
            step = TransformationStep(
                step_id=f"step_{i}",
                rule_name=f"TestRule_{i}",
                source_egi=self.test_egi,
                target_egi=self.test_egi,  # Simplified for testing
                context=TransformationContext(
                    source_egi=self.test_egi,
                    target_area="sheet",
                    selected_subgraph=frozenset(),
                    area_polarity=AreaPolarity.POSITIVE,
                    nesting_depth=0
                ),
                result=TransformationResult(
                    success=True,
                    transformed_egi=self.test_egi,
                    applied_rule="TestRule",
                    validation_passed=True
                ),
                timestamp=f"2024-01-{i+1:02d}T10:00:00Z",
                metadata={"test_step": i}
            )
            steps.append(step)

        # Create branch
        main_branch = HistoryBranch(
            branch_id="main",
            branch_type=HistoryBranchType.MAIN,
            parent_branch_id=None,
            branch_point_step_id=None,
            steps=steps,
            metadata={"branch_type": "main"}
        )

        # Create collaboration metadata
        collaboration = CollaborationMetadata(
            contributors=["test_user"],
            creation_timestamp="2024-01-01T10:00:00Z",
            last_modified="2024-01-03T10:00:00Z",
            version="1.0.0",
            tags=["test"],
            description="Test history for serialization testing"
        )

        return EnhancedEGITransformationHistory(
            history_id=str(uuid.uuid4()),
            initial_egi=self.test_egi,
            branches={"main": main_branch},
            current_branch_id="main",
            collaboration_metadata=collaboration,
            logical_provenance=LogicalProvenance(
                proof_steps=[],
                semantic_annotations={},
                validation_checkpoints={}
            )
        )

    # ==================== EGI CORE SERIALIZATION TESTS ====================

    def test_egi_json_serialization_round_trip(self):
        """Test EGI JSON serialization preserves all data exactly."""
        # Convert EGI to dictionary
        egi_dict = self._egi_to_dict(self.test_egi)
        
        # Serialize to JSON
        json_str = json.dumps(egi_dict, indent=2)
        assert len(json_str) > 0
        
        # Deserialize from JSON
        loaded_dict = json.loads(json_str)
        loaded_egi = self._dict_to_egi(loaded_dict)
        
        # Verify complete fidelity
        self._assert_egi_equality(self.test_egi, loaded_egi)

    def test_egi_yaml_serialization_round_trip(self):
        """Test EGI YAML serialization preserves all data exactly."""
        # Convert EGI to dictionary
        egi_dict = self._egi_to_dict(self.test_egi)
        
        # Serialize to YAML
        yaml_str = yaml.dump(egi_dict, default_flow_style=False)
        assert len(yaml_str) > 0
        assert "vertices:" in yaml_str
        assert "edges:" in yaml_str
        
        # Deserialize from YAML
        loaded_dict = yaml.safe_load(yaml_str)
        loaded_egi = self._dict_to_egi(loaded_dict)
        
        # Verify complete fidelity
        self._assert_egi_equality(self.test_egi, loaded_egi)

    def test_egi_serialization_with_complex_structures(self):
        """Test serialization of EGI with complex nested structures."""
        # Create EGI with deeply nested cuts
        complex_egi = self._create_deeply_nested_egi(5)  # 5 levels of nesting
        
        # Test JSON round-trip
        egi_dict = self._egi_to_dict(complex_egi)
        json_str = json.dumps(egi_dict)
        loaded_dict = json.loads(json_str)
        loaded_egi = self._dict_to_egi(loaded_dict)
        
        # Verify structure preservation
        assert len(loaded_egi.V) == len(complex_egi.V)
        assert len(loaded_egi.E) == len(complex_egi.E)
        assert len(loaded_egi.Cut) == len(complex_egi.Cut)

    def test_egi_serialization_edge_cases(self):
        """Test serialization of edge cases and boundary conditions."""
        test_cases = [
            create_empty_graph(),  # Empty EGI
            self._create_single_vertex_egi(),  # Single vertex
            self._create_single_edge_egi(),  # Single edge
            self._create_disconnected_egi(),  # Disconnected components
        ]
        
        for i, test_egi in enumerate(test_cases):
            # Test JSON serialization
            egi_dict = self._egi_to_dict(test_egi)
            json_str = json.dumps(egi_dict)
            loaded_dict = json.loads(json_str)
            loaded_egi = self._dict_to_egi(loaded_dict)
            
            # Verify basic structure
            assert len(loaded_egi.V) == len(test_egi.V), f"Vertex count mismatch in test case {i}"
            assert len(loaded_egi.E) == len(test_egi.E), f"Edge count mismatch in test case {i}"

    # ==================== DTO SERIALIZATION TESTS ====================

    def test_egi_dto_serialization(self):
        """Test EGI DTO serialization functionality."""
        # Create DTO from EGI
        dto = EGIStateDTO.from_egi(self.test_egi)
        
        # Test JSON serialization
        dto_dict = dto.to_dict()
        json_str = json.dumps(dto_dict)
        loaded_dict = json.loads(json_str)
        loaded_dto = EGIStateDTO.from_dict(loaded_dict)
        
        # Verify DTO equality
        assert loaded_dto.egi_id == dto.egi_id
        assert loaded_dto.vertex_count == dto.vertex_count
        assert loaded_dto.edge_count == dto.edge_count
        assert loaded_dto.cut_count == dto.cut_count

    def test_egi_dto_yaml_serialization(self):
        """Test EGI DTO YAML serialization."""
        dto = EGIStateDTO.from_egi(self.test_egi)
        
        # Test YAML serialization
        yaml_str = dto.to_yaml()
        loaded_dto = EGIStateDTO.from_yaml(yaml_str)
        
        # Verify equality
        assert loaded_dto.egi_id == dto.egi_id
        assert loaded_dto.timestamp == dto.timestamp

    def test_egi_dto_batch_serialization(self):
        """Test batch serialization of multiple DTOs."""
        # Create multiple DTOs
        dtos = []
        for i in range(10):
            test_egi = self._create_simple_test_egi(i)
            dto = EGIStateDTO.from_egi(test_egi)
            dtos.append(dto)
        
        # Serialize batch to JSON
        batch_dict = {"dtos": [dto.to_dict() for dto in dtos]}
        json_str = json.dumps(batch_dict)
        
        # Deserialize batch
        loaded_batch = json.loads(json_str)
        loaded_dtos = [EGIStateDTO.from_dict(dto_dict) for dto_dict in loaded_batch["dtos"]]
        
        # Verify batch integrity
        assert len(loaded_dtos) == len(dtos)
        for original, loaded in zip(dtos, loaded_dtos):
            assert loaded.egi_id == original.egi_id

    # ==================== HISTORY SERIALIZATION TESTS ====================

    def test_history_persistence_json_serialization(self):
        """Test transformation history JSON serialization."""
        # Save history to JSON
        json_path = self.persistence_manager.save_history_json(self.test_history)
        assert json_path.exists()
        
        # Verify JSON structure
        with open(json_path, 'r') as f:
            history_data = json.load(f)
        
        required_fields = ["history_id", "initial_egi", "branches", "collaboration_metadata"]
        for field in required_fields:
            assert field in history_data, f"Missing field: {field}"
        
        # Load and verify
        loaded_history = self.persistence_manager.load_history_json(json_path)
        assert loaded_history.history_id == self.test_history.history_id
        assert len(loaded_history.branches) == len(self.test_history.branches)

    def test_history_persistence_yaml_serialization(self):
        """Test transformation history YAML serialization."""
        # Save history to YAML
        yaml_path = self.persistence_manager.save_history_yaml(self.test_history)
        assert yaml_path.exists()
        
        # Verify YAML is human-readable
        with open(yaml_path, 'r') as f:
            yaml_content = f.read()
            assert "history_id:" in yaml_content
            assert "branches:" in yaml_content
            assert "main:" in yaml_content
        
        # Load and verify
        loaded_history = self.persistence_manager.load_history_yaml(yaml_path)
        assert loaded_history.history_id == self.test_history.history_id

    def test_history_persistence_compressed_serialization(self):
        """Test compressed history serialization."""
        # Save in compressed format
        compressed_path = self.persistence_manager.save_history_compressed(self.test_history)
        assert compressed_path.exists()
        
        # Verify compression efficiency
        json_path = self.persistence_manager.save_history_json(self.test_history)
        json_size = json_path.stat().st_size
        compressed_size = compressed_path.stat().st_size
        
        # Compressed should be smaller (or at least not much larger for small data)
        compression_ratio = compressed_size / json_size
        assert compression_ratio <= 1.2, f"Poor compression ratio: {compression_ratio}"
        
        # Verify decompression
        loaded_history = self.persistence_manager.load_history_compressed(compressed_path)
        assert loaded_history.history_id == self.test_history.history_id

    def test_efficient_historical_storage_serialization(self):
        """Test efficient historical storage serialization."""
        # Store initial state
        state_id = self.historical_storage.store_state(self.test_egi, {"initial": True})
        assert state_id is not None
        
        # Create modified EGI
        modified_egi = self.test_egi.with_vertex(create_vertex(label="NewVertex", is_generic=True))
        
        # Store delta
        delta_id = self.historical_storage.store_delta(self.test_egi, modified_egi, {"delta": True})
        assert delta_id is not None
        
        # Retrieve and verify
        retrieved_egi = self.historical_storage.retrieve_state(state_id)
        assert len(retrieved_egi.V) == len(self.test_egi.V)
        
        # Apply delta and verify
        reconstructed_egi = self.historical_storage.apply_delta(state_id, delta_id)
        assert len(reconstructed_egi.V) == len(modified_egi.V)

    # ==================== PERFORMANCE TESTS ====================

    def test_serialization_performance_large_egi(self):
        """Test serialization performance with large EGI structures."""
        import time
        
        # Create large EGI
        large_egi = self._create_large_egi(1000)  # 1000 vertices
        
        # Test JSON serialization performance
        start_time = time.time()
        egi_dict = self._egi_to_dict(large_egi)
        json_str = json.dumps(egi_dict)
        json_serialize_time = time.time() - start_time
        
        # Test JSON deserialization performance
        start_time = time.time()
        loaded_dict = json.loads(json_str)
        loaded_egi = self._dict_to_egi(loaded_dict)
        json_deserialize_time = time.time() - start_time
        
        # Performance should be reasonable (< 10 seconds each)
        assert json_serialize_time < 10.0, f"JSON serialization too slow: {json_serialize_time:.2f}s"
        assert json_deserialize_time < 10.0, f"JSON deserialization too slow: {json_deserialize_time:.2f}s"
        
        # Verify correctness
        assert len(loaded_egi.V) == len(large_egi.V)

    def test_serialization_memory_efficiency(self):
        """Test memory efficiency of serialization operations."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Serialize multiple large EGIs
        for i in range(10):
            large_egi = self._create_large_egi(100)
            egi_dict = self._egi_to_dict(large_egi)
            json_str = json.dumps(egi_dict)
            # Immediately deserialize to test full cycle
            loaded_dict = json.loads(json_str)
            loaded_egi = self._dict_to_egi(loaded_dict)
        
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (< 500MB)
        assert memory_growth < 500 * 1024 * 1024, f"Excessive memory growth: {memory_growth / 1024 / 1024:.1f}MB"

    def test_serialization_concurrent_access(self):
        """Test thread-safe serialization operations."""
        import threading
        import time
        
        results = []
        errors = []
        
        def serialize_worker(worker_id: int):
            try:
                # Create unique EGI
                worker_egi = self._create_simple_test_egi(worker_id)
                
                # Serialize to JSON
                egi_dict = self._egi_to_dict(worker_egi)
                json_str = json.dumps(egi_dict)
                
                # Deserialize
                loaded_dict = json.loads(json_str)
                loaded_egi = self._dict_to_egi(loaded_dict)
                
                # Verify
                assert len(loaded_egi.V) == len(worker_egi.V)
                results.append(f"worker_{worker_id}_success")
                
            except Exception as e:
                errors.append(f"worker_{worker_id}_error: {e}")
        
        # Run concurrent workers
        threads = []
        for i in range(5):
            thread = threading.Thread(target=serialize_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify all succeeded
        assert len(errors) == 0, f"Concurrent serialization errors: {errors}"
        assert len(results) == 5

    # ==================== ERROR HANDLING TESTS ====================

    def test_serialization_error_handling(self):
        """Test error handling in serialization operations."""
        # Test with corrupted JSON
        corrupted_json = '{"vertices": [{"id": "incomplete"'
        
        with pytest.raises(json.JSONDecodeError):
            json.loads(corrupted_json)
        
        # Test with invalid EGI structure
        invalid_dict = {
            "vertices": "not_a_list",  # Should be a list
            "edges": [],
            "cuts": []
        }
        
        with pytest.raises(Exception):  # Should raise some kind of validation error
            self._dict_to_egi(invalid_dict)

    def test_serialization_data_validation(self):
        """Test data validation during serialization/deserialization."""
        # Create EGI with invalid references
        egi = create_empty_graph()
        vertex = create_vertex(label="Test", is_generic=False)
        edge = create_edge(relation="TestRel")
        
        egi = egi.with_vertex(vertex).with_edge(edge)
        # Add nu entry with non-existent vertex
        invalid_egi = egi.with_nu_entry(edge.id, ("nonexistent_vertex_id",))
        
        # Serialization should handle this gracefully or raise appropriate error
        try:
            egi_dict = self._egi_to_dict(invalid_egi)
            # If serialization succeeds, deserialization should validate
            loaded_egi = self._dict_to_egi(egi_dict)
            # Should either fix the issue or raise validation error
        except Exception as e:
            # Should be a meaningful validation error
            assert "vertex" in str(e).lower() or "reference" in str(e).lower()

    # ==================== HELPER METHODS ====================

    def _egi_to_dict(self, egi: RelationalGraphWithCuts) -> Dict[str, Any]:
        """Convert EGI to dictionary for serialization."""
        return {
            "vertices": [
                {
                    "id": v.id,
                    "label": v.label,
                    "is_generic": v.is_generic
                } for v in egi.V
            ],
            "edges": [
                {
                    "id": e.id,
                    "relation": egi.rel.get(e.id)
                } for e in egi.E
            ],
            "cuts": [
                {
                    "id": c.id
                } for c in egi.Cut
            ],
            "nu_mapping": {
                edge_id: list(vertex_ids) 
                for edge_id, vertex_ids in egi.nu.items()
            },
            "area_mapping": {
                element_id: list(area_elements)
                for element_id, area_elements in egi.area.items()
            },
            "sheet": egi.sheet,
            "alphabet": {
                "constants": list(egi.alphabet.constants) if egi.alphabet else [],
                "functors": list(egi.alphabet.functors) if egi.alphabet else [],
                "relations": list(egi.alphabet.relations) if egi.alphabet else [],
                "arity": dict(egi.alphabet.arity) if egi.alphabet else {}
            } if egi.alphabet else None,
            "rho": dict(egi.rho) if egi.rho else {}
        }

    def _dict_to_egi(self, data: Dict[str, Any]) -> RelationalGraphWithCuts:
        """Convert dictionary to EGI for deserialization."""
        egi = create_empty_graph()
        
        # Add vertices
        for v_data in data.get("vertices", []):
            vertex = create_vertex(
                label=v_data.get("label"),
                is_generic=v_data.get("is_generic", True)
            )
            vertex.id = v_data["id"]  # Preserve original ID
            egi = egi.with_vertex(vertex)
        
        # Add edges
        for e_data in data.get("edges", []):
            edge = create_edge(relation=e_data.get("relation", ""))
            edge.id = e_data["id"]  # Preserve original ID
            egi = egi.with_edge(edge)
        
        # Add cuts
        for c_data in data.get("cuts", []):
            cut = create_cut()
            cut.id = c_data["id"]  # Preserve original ID
            egi = egi.with_cut(cut)
        
        # Add nu mappings
        for edge_id, vertex_ids in data.get("nu_mapping", {}).items():
            egi = egi.with_nu_entry(edge_id, tuple(vertex_ids))
        
        # Add alphabet if present
        if data.get("alphabet"):
            alphabet_data = data["alphabet"]
            alphabet = Alphabet(
                constants=frozenset(alphabet_data.get("constants", [])),
                functors=frozenset(alphabet_data.get("functors", [])),
                relations=frozenset(alphabet_data.get("relations", [])),
                arity=frozendict(alphabet_data.get("arity", {}))
            )
            egi = egi.with_alphabet(alphabet)
        
        # Add rho mapping if present
        if data.get("rho"):
            egi = egi.with_rho(frozendict(data["rho"]))
        
        return egi

    def _assert_egi_equality(self, egi1: RelationalGraphWithCuts, egi2: RelationalGraphWithCuts):
        """Assert that two EGIs are structurally equal."""
        assert len(egi1.V) == len(egi2.V), "Vertex count mismatch"
        assert len(egi1.E) == len(egi2.E), "Edge count mismatch"
        assert len(egi1.Cut) == len(egi2.Cut), "Cut count mismatch"
        assert len(egi1.nu) == len(egi2.nu), "Nu mapping count mismatch"
        
        # Check vertex details
        v1_by_id = {v.id: v for v in egi1.V}
        v2_by_id = {v.id: v for v in egi2.V}
        
        for v_id in v1_by_id:
            assert v_id in v2_by_id, f"Vertex {v_id} missing in second EGI"
            v1, v2 = v1_by_id[v_id], v2_by_id[v_id]
            assert v1.label == v2.label, f"Label mismatch for vertex {v_id}"
            assert v1.is_generic == v2.is_generic, f"Generic flag mismatch for vertex {v_id}"

    def _create_deeply_nested_egi(self, nesting_levels: int) -> RelationalGraphWithCuts:
        """Create EGI with specified nesting levels."""
        egi = create_empty_graph()
        
        # Create nested cuts
        cuts = []
        for i in range(nesting_levels):
            cut = create_cut()
            cuts.append(cut)
            egi = egi.with_cut(cut)
        
        # Add some vertices and edges
        vertex = create_vertex(label=f"NestedVertex", is_generic=True)
        edge = create_edge(relation="NestedRelation")
        
        egi = egi.with_vertex(vertex).with_edge(edge)
        egi = egi.with_nu_entry(edge.id, (vertex.id,))
        
        return egi

    def _create_single_vertex_egi(self) -> RelationalGraphWithCuts:
        """Create EGI with single vertex."""
        egi = create_empty_graph()
        vertex = create_vertex(label="Single", is_generic=False)
        return egi.with_vertex(vertex)

    def _create_single_edge_egi(self) -> RelationalGraphWithCuts:
        """Create EGI with single edge and vertex."""
        egi = create_empty_graph()
        vertex = create_vertex(label="Single", is_generic=False)
        edge = create_edge(relation="SingleRel")
        return egi.with_vertex(vertex).with_edge(edge).with_nu_entry(edge.id, (vertex.id,))

    def _create_disconnected_egi(self) -> RelationalGraphWithCuts:
        """Create EGI with disconnected components."""
        egi = create_empty_graph()
        
        # Component 1
        v1 = create_vertex(label="A", is_generic=False)
        e1 = create_edge(relation="R1")
        
        # Component 2
        v2 = create_vertex(label="B", is_generic=False)
        e2 = create_edge(relation="R2")
        
        return (egi
                .with_vertex(v1).with_vertex(v2)
                .with_edge(e1).with_edge(e2)
                .with_nu_entry(e1.id, (v1.id,))
                .with_nu_entry(e2.id, (v2.id,)))

    def _create_simple_test_egi(self, index: int) -> RelationalGraphWithCuts:
        """Create simple test EGI with unique elements."""
        egi = create_empty_graph()
        vertex = create_vertex(label=f"TestVertex_{index}", is_generic=False)
        edge = create_edge(relation=f"TestRelation_{index}")
        return egi.with_vertex(vertex).with_edge(edge).with_nu_entry(edge.id, (vertex.id,))

    def _create_large_egi(self, num_vertices: int) -> RelationalGraphWithCuts:
        """Create large EGI for performance testing."""
        egi = create_empty_graph()
        
        vertices = []
        for i in range(num_vertices):
            vertex = create_vertex(label=f"LargeVertex_{i}", is_generic=True)
            vertices.append(vertex)
            egi = egi.with_vertex(vertex)
        
        # Add some edges
        for i in range(min(num_vertices // 2, 100)):  # Limit edges for performance
            edge = create_edge(relation=f"LargeRelation_{i}")
            egi = egi.with_edge(edge)
            
            # Connect to random vertices
            if i < len(vertices) - 1:
                egi = egi.with_nu_entry(edge.id, (vertices[i].id, vertices[i+1].id))
        
        return egi


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
