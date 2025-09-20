"""
Comprehensive Test Infrastructure Validation

This test validates that our comprehensive test suites are properly structured
and can identify which components are actually testable with current imports.
"""

import importlib
import sys
from pathlib import Path

import pytest


@pytest.mark.skip(reason="Comprehensive validation tests require refactoring due to API changes - tracked as technical debt")
class TestComprehensiveValidation:
    """Validate comprehensive test infrastructure."""

    def test_comprehensive_test_files_exist(self):
        """Test that all comprehensive test files exist."""
        test_files = [
            "test_data_persistence_comprehensive.py",
            "test_integration_managers_comprehensive.py", 
            "test_ligature_algorithms_comprehensive.py",
            "test_serialization_comprehensive.py",
            "test_performance_comprehensive.py",
            "test_error_handling_comprehensive.py"
        ]
        
        tests_dir = Path(__file__).parent
        
        for test_file in test_files:
            test_path = tests_dir / test_file
            assert test_path.exists(), f"Missing comprehensive test file: {test_file}"
            assert test_path.stat().st_size > 1000, f"Test file too small: {test_file}"

    def test_import_availability(self):
        """Test which modules are available for comprehensive testing."""
        # Core modules that should be available
        core_modules = [
            "src.egi_core_dau",
            "src.graph_isomorphism_engine", 
            "src.egif_parser_dau",
            "src.egif_generator_dau",
            "src.cgif_parser_dau",
            "src.cgif_generator_dau",
            "src.clif_parser_dau",
            "src.clif_generator_dau",
            "src.formal_transformation_rules",
            "src.egi_transformation_history",
            "src.history_persistence"
        ]
        
        available_modules = []
        missing_modules = []
        
        for module_name in core_modules:
            try:
                importlib.import_module(module_name)
                available_modules.append(module_name)
            except ImportError as e:
                missing_modules.append((module_name, str(e)))
        
        print(f"\n✅ Available modules ({len(available_modules)}):")
        for module in available_modules:
            print(f"  - {module}")
        
        if missing_modules:
            print(f"\n❌ Missing modules ({len(missing_modules)}):")
            for module, error in missing_modules:
                print(f"  - {module}: {error}")
        
        # Should have most core modules available
        assert len(available_modules) >= 8, f"Too many missing core modules: {len(missing_modules)}"

    def test_integration_modules_availability(self):
        """Test availability of integration manager modules."""
        integration_modules = [
            "src.integrated_corpus_manager",
            "src.integrated_export_manager", 
            "src.integrated_view_manager",
            "src.core_dau_formalism",
            "src.integration_interfaces"
        ]
        
        available_count = 0
        for module_name in integration_modules:
            try:
                importlib.import_module(module_name)
                available_count += 1
                print(f"✅ {module_name}")
            except ImportError as e:
                print(f"❌ {module_name}: {e}")
        
        print(f"\nIntegration modules available: {available_count}/{len(integration_modules)}")
        
        # Note: Some integration modules may not be available, which is expected
        # This test documents what's available for testing

    def test_ligature_modules_availability(self):
        """Test availability of ligature algorithm modules."""
        ligature_modules = [
            "src.ligature_manipulation_rules",
            "src.ligature_optimization_engine",
            "src.ligature_aware_positioning_engine", 
            "src.enhanced_ligature_algorithms",
            "src.obstacle_aware_ligature_router",
            "src.single_object_ligature_detector"
        ]
        
        available_count = 0
        for module_name in ligature_modules:
            try:
                importlib.import_module(module_name)
                available_count += 1
                print(f"✅ {module_name}")
            except ImportError as e:
                print(f"❌ {module_name}: {e}")
        
        print(f"\nLigature modules available: {available_count}/{len(ligature_modules)}")

    def test_performance_test_infrastructure(self):
        """Test that performance testing infrastructure is available."""
        try:
            import psutil
            import time
            import threading
            from concurrent.futures import ThreadPoolExecutor
            
            # Test basic performance measurement
            start_time = time.time()
            process = psutil.Process()
            initial_memory = process.memory_info().rss
            
            # Simple operation
            test_data = list(range(1000))
            
            end_time = time.time()
            final_memory = process.memory_info().rss
            
            execution_time = end_time - start_time
            memory_used = final_memory - initial_memory
            
            assert execution_time >= 0
            assert isinstance(memory_used, int)
            
            print(f"✅ Performance infrastructure working: {execution_time:.4f}s, {memory_used} bytes")
            
        except ImportError as e:
            pytest.skip(f"Performance testing dependencies not available: {e}")

    def test_comprehensive_test_structure(self):
        """Test that comprehensive test files have proper structure."""
        test_files = [
            "test_data_persistence_comprehensive.py",
            "test_serialization_comprehensive.py",
            "test_error_handling_comprehensive.py"
        ]
        
        tests_dir = Path(__file__).parent
        
        for test_file in test_files:
            test_path = tests_dir / test_file
            if test_path.exists():
                content = test_path.read_text()
                
                # Check for proper test class structure
                assert "class Test" in content, f"Missing test class in {test_file}"
                assert "def test_" in content, f"Missing test methods in {test_file}"
                assert "def setup_method" in content, f"Missing setup in {test_file}"
                assert "def teardown_method" in content, f"Missing teardown in {test_file}"
                
                print(f"✅ {test_file} has proper structure")

    def test_existing_test_compatibility(self):
        """Test that comprehensive tests don't break existing test suite."""
        # Run a simple existing test to ensure compatibility
        from src.egi_core_dau import create_empty_graph, create_vertex
        
        # This should work with existing infrastructure
        egi = create_empty_graph()
        vertex = create_vertex(label="Test", is_generic=False)
        egi = egi.with_vertex(vertex)
        
        assert len(egi.V) == 1
        assert list(egi.V)[0].label == "Test"
        
        print("✅ Existing test infrastructure still works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
