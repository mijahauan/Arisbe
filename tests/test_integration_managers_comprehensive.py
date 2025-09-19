"""
Comprehensive Integration Managers Testing Suite

Tests all integration manager components:
- IntegratedCorpusManager (734 lines)
- IntegratedViewManager (1,247 lines)  
- IntegratedExportManager (717 lines)
- CoreDauFormalismManager (679 lines)
- Integration interfaces and protocols
"""

import json
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any, List

import pytest

from src.egi_core_dau import create_empty_graph, create_vertex, create_edge, RelationalGraphWithCuts
from src.integrated_corpus_manager import (
    IntegratedCorpusManager,
    CorpusCategory,
    CorpusItem,
    CorpusSearchResult,
    CorpusValidationResult,
)
from src.integrated_export_manager import (
    IntegratedExportManager,
    ExportFormat,
    ExportResult,
    ExportValidationResult,
)
from src.integrated_view_manager import (
    IntegratedViewManager,
    ViewType,
    ViewConfiguration,
    ViewResult,
    ViewGenerationResult,
)
from src.core_dau_formalism import CoreDauFormalismManager, LinearFormat
from src.integration_interfaces import IntegrationManager, IntegrationContext


class TestIntegrationManagersComprehensive:
    """Comprehensive test suite for all integration managers."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_egi = self._create_test_egi()
        
        # Initialize managers
        self.corpus_manager = IntegratedCorpusManager(base_path=self.temp_dir)
        self.export_manager = IntegratedExportManager()
        self.view_manager = IntegratedViewManager()
        self.formalism_manager = CoreDauFormalismManager()
        
        # Create integration context
        self.integration_context = IntegrationContext(
            corpus_manager=self.corpus_manager,
            export_manager=self.export_manager,
            view_manager=self.view_manager,
            formalism_manager=self.formalism_manager
        )
        self.integration_manager = IntegrationManager(self.integration_context)

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_egi(self) -> RelationalGraphWithCuts:
        """Create a test EGI for testing."""
        egi = create_empty_graph()
        
        # Add vertices
        human_vertex = create_vertex(label="Human", is_generic=False)
        socrates_vertex = create_vertex(label="Socrates", is_generic=False)
        mortal_vertex = create_vertex(label="Mortal", is_generic=False)
        
        # Add edges
        human_edge = create_edge(relation="Human")
        mortal_edge = create_edge(relation="Mortal")
        
        # Build EGI
        egi = (egi
               .with_vertex(human_vertex)
               .with_vertex(socrates_vertex)
               .with_vertex(mortal_vertex)
               .with_edge(human_edge)
               .with_edge(mortal_edge)
               .with_nu_entry(human_edge.id, (socrates_vertex.id,))
               .with_nu_entry(mortal_edge.id, (socrates_vertex.id,)))
        
        return egi

    # ==================== CORPUS MANAGER TESTS ====================

    def test_corpus_manager_add_and_retrieve_egi(self):
        """Test adding and retrieving EGIs from corpus."""
        metadata = {
            "title": "Test EGI",
            "category": CorpusCategory.TESTS.value,
            "description": "Test EGI for comprehensive testing",
            "tags": ["test", "comprehensive"]
        }
        
        # Add EGI to corpus
        egi_id = self.corpus_manager.add_egi(self.test_egi, metadata)
        assert egi_id is not None
        assert isinstance(egi_id, str)
        
        # Retrieve EGI
        retrieved_egi = self.corpus_manager.get_egi(egi_id)
        assert retrieved_egi is not None
        assert len(retrieved_egi.V) == len(self.test_egi.V)
        assert len(retrieved_egi.E) == len(self.test_egi.E)
        
        # Retrieve metadata
        retrieved_metadata = self.corpus_manager.get_metadata(egi_id)
        assert retrieved_metadata["title"] == metadata["title"]
        assert retrieved_metadata["category"] == metadata["category"]

    def test_corpus_manager_search_functionality(self):
        """Test corpus search capabilities."""
        # Add multiple EGIs with different metadata
        test_egis = []
        for i in range(5):
            metadata = {
                "title": f"Test EGI {i}",
                "category": CorpusCategory.TESTS.value,
                "description": f"Test EGI number {i}",
                "tags": ["test", f"item_{i}"]
            }
            egi_id = self.corpus_manager.add_egi(self.test_egi, metadata)
            test_egis.append(egi_id)
        
        # Search by category
        search_results = self.corpus_manager.search_corpus({
            "category": CorpusCategory.TESTS.value
        })
        assert len(search_results) >= 5
        
        # Search by tag
        tag_results = self.corpus_manager.search_corpus({
            "tags": ["test"]
        })
        assert len(tag_results) >= 5
        
        # Search by title pattern
        title_results = self.corpus_manager.search_corpus({
            "title_pattern": "Test EGI"
        })
        assert len(title_results) >= 5

    def test_corpus_manager_validation(self):
        """Test corpus validation functionality."""
        # Add valid EGI
        valid_metadata = {
            "title": "Valid EGI",
            "category": CorpusCategory.TESTS.value,
            "description": "Valid test EGI"
        }
        egi_id = self.corpus_manager.add_egi(self.test_egi, valid_metadata)
        
        # Validate corpus
        validation_result = self.corpus_manager.validate_corpus()
        assert validation_result.is_valid
        assert egi_id in [item.egi_id for item in validation_result.validated_items]

    def test_corpus_manager_categories(self):
        """Test corpus category management."""
        # Get available categories
        categories = self.corpus_manager.get_categories()
        assert CorpusCategory.TESTS in categories
        assert CorpusCategory.EXAMPLES in categories
        
        # Add EGIs to different categories
        for category in [CorpusCategory.TESTS, CorpusCategory.EXAMPLES]:
            metadata = {
                "title": f"EGI for {category.value}",
                "category": category.value,
                "description": f"Test EGI for {category.value} category"
            }
            egi_id = self.corpus_manager.add_egi(self.test_egi, metadata)
            
            # Verify category assignment
            retrieved_metadata = self.corpus_manager.get_metadata(egi_id)
            assert retrieved_metadata["category"] == category.value

    # ==================== EXPORT MANAGER TESTS ====================

    def test_export_manager_all_formats(self):
        """Test exporting to all supported formats."""
        export_formats = [
            ExportFormat.EGIF,
            ExportFormat.CGIF,
            ExportFormat.CLIF,
            ExportFormat.JSON,
            ExportFormat.YAML
        ]
        
        for export_format in export_formats:
            result = self.export_manager.export_egi(
                self.test_egi,
                export_format,
                output_path=Path(self.temp_dir) / f"test_export.{export_format.value.lower()}"
            )
            
            assert result.success, f"Export to {export_format.value} failed: {result.error_message}"
            assert result.output_path.exists()
            assert result.output_path.stat().st_size > 0

    def test_export_manager_validation(self):
        """Test export validation functionality."""
        # Export to EGIF
        egif_path = Path(self.temp_dir) / "test.egif"
        result = self.export_manager.export_egi(self.test_egi, ExportFormat.EGIF, egif_path)
        assert result.success
        
        # Validate export
        validation_result = self.export_manager.validate_export(egif_path, ExportFormat.EGIF)
        assert validation_result.is_valid
        assert validation_result.format_compliance
        
        # Test round-trip validation
        roundtrip_result = self.export_manager.validate_roundtrip(self.test_egi, ExportFormat.EGIF)
        assert roundtrip_result.is_valid
        assert roundtrip_result.structural_equivalence

    def test_export_manager_batch_export(self):
        """Test batch export functionality."""
        # Create multiple EGIs
        egis = [self.test_egi for _ in range(3)]
        export_configs = [
            {"format": ExportFormat.EGIF, "filename": f"batch_{i}.egif"}
            for i in range(3)
        ]
        
        # Batch export
        results = self.export_manager.batch_export(
            egis,
            export_configs,
            output_directory=Path(self.temp_dir)
        )
        
        assert len(results) == 3
        for result in results:
            assert result.success
            assert result.output_path.exists()

    def test_export_manager_format_conversion(self):
        """Test format conversion capabilities."""
        # Export to EGIF first
        egif_path = Path(self.temp_dir) / "source.egif"
        egif_result = self.export_manager.export_egi(self.test_egi, ExportFormat.EGIF, egif_path)
        assert egif_result.success
        
        # Convert to other formats
        target_formats = [ExportFormat.CGIF, ExportFormat.CLIF, ExportFormat.JSON]
        
        for target_format in target_formats:
            target_path = Path(self.temp_dir) / f"converted.{target_format.value.lower()}"
            conversion_result = self.export_manager.convert_format(
                egif_path,
                ExportFormat.EGIF,
                target_format,
                target_path
            )
            
            assert conversion_result.success, f"Conversion to {target_format.value} failed"
            assert target_path.exists()

    # ==================== VIEW MANAGER TESTS ====================

    def test_view_manager_generate_all_view_types(self):
        """Test generating all supported view types."""
        view_types = [
            ViewType.OVERVIEW,
            ViewType.DETAILED,
            ViewType.TRANSFORMATION,
            ViewType.PROOF_SEQUENCE
        ]
        
        for view_type in view_types:
            config = ViewConfiguration(
                view_type=view_type,
                egi=self.test_egi,
                output_format="SVG",
                width=800,
                height=600
            )
            
            result = self.view_manager.generate_view(config)
            assert result.success, f"View generation failed for {view_type.value}: {result.error_message}"
            assert result.view_data is not None
            assert len(result.view_data) > 0

    def test_view_manager_configuration_validation(self):
        """Test view configuration validation."""
        # Valid configuration
        valid_config = ViewConfiguration(
            view_type=ViewType.DETAILED,
            egi=self.test_egi,
            output_format="SVG",
            width=800,
            height=600
        )
        
        validation_result = self.view_manager.validate_configuration(valid_config)
        assert validation_result.is_valid
        
        # Invalid configuration (missing EGI)
        invalid_config = ViewConfiguration(
            view_type=ViewType.DETAILED,
            egi=None,
            output_format="SVG",
            width=800,
            height=600
        )
        
        invalid_validation = self.view_manager.validate_configuration(invalid_config)
        assert not invalid_validation.is_valid
        assert "EGI is required" in invalid_validation.error_messages

    def test_view_manager_custom_styling(self):
        """Test custom styling capabilities."""
        style_config = {
            "vertex_color": "#FF0000",
            "edge_color": "#0000FF",
            "background_color": "#FFFFFF",
            "font_family": "Arial",
            "font_size": 12
        }
        
        config = ViewConfiguration(
            view_type=ViewType.DETAILED,
            egi=self.test_egi,
            output_format="SVG",
            width=800,
            height=600,
            style_config=style_config
        )
        
        result = self.view_manager.generate_view(config)
        assert result.success
        
        # Verify style was applied (check SVG contains style elements)
        svg_content = result.view_data
        assert "#FF0000" in svg_content or "red" in svg_content.lower()

    def test_view_manager_batch_generation(self):
        """Test batch view generation."""
        configs = []
        for i, view_type in enumerate([ViewType.OVERVIEW, ViewType.DETAILED]):
            config = ViewConfiguration(
                view_type=view_type,
                egi=self.test_egi,
                output_format="SVG",
                width=800,
                height=600,
                output_path=Path(self.temp_dir) / f"batch_view_{i}.svg"
            )
            configs.append(config)
        
        results = self.view_manager.batch_generate_views(configs)
        assert len(results) == 2
        
        for result in results:
            assert result.success
            if result.output_path:
                assert result.output_path.exists()

    # ==================== FORMALISM MANAGER TESTS ====================

    def test_formalism_manager_validation(self):
        """Test core formalism validation."""
        # Validate EGI structure
        validation_result = self.formalism_manager.validate_egi(self.test_egi)
        assert validation_result.is_valid
        assert validation_result.dau_compliant
        
        # Check specific validation aspects
        assert validation_result.vertex_constraints_valid
        assert validation_result.edge_constraints_valid
        assert validation_result.area_containment_valid

    def test_formalism_manager_linear_format_support(self):
        """Test linear format support in formalism manager."""
        supported_formats = self.formalism_manager.get_supported_formats()
        
        expected_formats = [LinearFormat.EGIF, LinearFormat.CGIF, LinearFormat.CLIF]
        for format in expected_formats:
            assert format in supported_formats
        
        # Test format conversion
        for format in expected_formats:
            converted = self.formalism_manager.convert_to_format(self.test_egi, format)
            assert converted is not None
            assert len(converted) > 0

    def test_formalism_manager_transformation_validation(self):
        """Test transformation validation in formalism manager."""
        # Create a simple transformation (add a vertex)
        new_vertex = create_vertex(label="TestVertex", is_generic=True)
        transformed_egi = self.test_egi.with_vertex(new_vertex)
        
        # Validate transformation
        validation_result = self.formalism_manager.validate_transformation(
            source_egi=self.test_egi,
            target_egi=transformed_egi,
            transformation_rule="TEST_ADD_VERTEX"
        )
        
        assert validation_result.is_valid
        assert validation_result.preserves_semantics

    # ==================== INTEGRATION MANAGER TESTS ====================

    def test_integration_manager_workflow(self):
        """Test complete integration workflow."""
        # 1. Add EGI to corpus
        metadata = {
            "title": "Integration Test EGI",
            "category": CorpusCategory.TESTS.value,
            "description": "EGI for testing integration workflow"
        }
        
        egi_id = self.integration_manager.add_egi_to_corpus(self.test_egi, metadata)
        assert egi_id is not None
        
        # 2. Generate view
        view_config = ViewConfiguration(
            view_type=ViewType.DETAILED,
            egi=self.test_egi,
            output_format="SVG",
            width=800,
            height=600
        )
        
        view_result = self.integration_manager.generate_view(view_config)
        assert view_result.success
        
        # 3. Export to multiple formats
        export_results = self.integration_manager.export_egi_multiple_formats(
            self.test_egi,
            [ExportFormat.EGIF, ExportFormat.CGIF, ExportFormat.JSON],
            output_directory=Path(self.temp_dir)
        )
        
        assert len(export_results) == 3
        for result in export_results:
            assert result.success

    def test_integration_manager_error_handling(self):
        """Test integration manager error handling."""
        # Test with invalid EGI
        invalid_egi = None
        
        # Should handle gracefully
        try:
            self.integration_manager.add_egi_to_corpus(invalid_egi, {})
            assert False, "Should have raised an error"
        except Exception as e:
            assert "invalid" in str(e).lower() or "none" in str(e).lower()

    def test_integration_manager_performance(self):
        """Test integration manager performance with multiple operations."""
        import time
        
        start_time = time.time()
        
        # Perform multiple operations
        for i in range(10):
            metadata = {
                "title": f"Performance Test EGI {i}",
                "category": CorpusCategory.TESTS.value,
                "description": f"Performance test EGI number {i}"
            }
            
            # Add to corpus
            egi_id = self.integration_manager.add_egi_to_corpus(self.test_egi, metadata)
            
            # Generate view
            view_config = ViewConfiguration(
                view_type=ViewType.OVERVIEW,
                egi=self.test_egi,
                output_format="SVG",
                width=400,
                height=300
            )
            self.integration_manager.generate_view(view_config)
            
            # Export
            export_result = self.integration_manager.export_egi(
                self.test_egi,
                ExportFormat.EGIF,
                Path(self.temp_dir) / f"perf_test_{i}.egif"
            )
            assert export_result.success
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete 10 full workflows in reasonable time (< 30 seconds)
        assert total_time < 30.0, f"Performance test took too long: {total_time:.2f}s"

    def test_cross_manager_communication(self):
        """Test communication between different managers."""
        # Add EGI to corpus via corpus manager
        metadata = {"title": "Cross-manager test", "category": CorpusCategory.TESTS.value}
        egi_id = self.corpus_manager.add_egi(self.test_egi, metadata)
        
        # Retrieve via integration manager
        retrieved_egi = self.integration_manager.get_egi_from_corpus(egi_id)
        assert retrieved_egi is not None
        assert len(retrieved_egi.V) == len(self.test_egi.V)
        
        # Export via export manager
        export_result = self.export_manager.export_egi(
            retrieved_egi,
            ExportFormat.EGIF,
            Path(self.temp_dir) / "cross_manager_test.egif"
        )
        assert export_result.success
        
        # Generate view via view manager
        view_config = ViewConfiguration(
            view_type=ViewType.DETAILED,
            egi=retrieved_egi,
            output_format="SVG",
            width=800,
            height=600
        )
        view_result = self.view_manager.generate_view(view_config)
        assert view_result.success


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
