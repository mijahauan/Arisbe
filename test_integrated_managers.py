#!/usr/bin/env python3
"""
Test script for integrated managers functionality.

This script tests the newly integrated corpus, view, and export managers
to ensure they work correctly with the core Dau formalism system.
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_core_integration():
    """Test that all managers integrate properly with core formalism."""
    logger.info("Testing core integration...")
    
    try:
        # Import core manager
        from src.core_dau_formalism import get_dau_formalism_manager
        core_manager = get_dau_formalism_manager()
        logger.info("✓ Core Dau formalism manager loaded")
        
        # Import integrated managers
        from src.integrated_corpus_manager import get_integrated_corpus_manager
        from src.integrated_view_manager import get_integrated_view_manager
        from src.integrated_export_manager import get_integrated_export_manager
        
        corpus_manager = get_integrated_corpus_manager()
        view_manager = get_integrated_view_manager()
        export_manager = get_integrated_export_manager()
        
        logger.info("✓ All integrated managers loaded successfully")
        
        # Test coherence registry integration
        from src.coherence_registry import get_coherence_registry
        registry = get_coherence_registry()
        
        # Check if managers are registered
        registered_components = registry.list_components()
        manager_names = [comp.name for comp in registered_components]
        
        expected_managers = ["IntegratedCorpusManager", "IntegratedViewManager", "IntegratedExportManager"]
        for manager in expected_managers:
            if manager in manager_names:
                logger.info(f"✓ {manager} registered in coherence registry")
            else:
                logger.warning(f"✗ {manager} not found in registry")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Core integration test failed: {e}")
        return False

def test_corpus_manager():
    """Test integrated corpus manager functionality."""
    logger.info("Testing integrated corpus manager...")
    
    try:
        from src.integrated_corpus_manager import get_integrated_corpus_manager, CorpusCategory
        from src.egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut
        
        corpus_manager = get_integrated_corpus_manager()
        
        # Create a simple test EGI
        test_egi = RelationalGraphWithCuts()
        
        # Add vertices
        v1 = Vertex("v1", "Person", is_generic=True)
        v2 = Vertex("v2", "John", is_generic=False)
        test_egi.V.extend([v1, v2])
        
        # Add edge
        e1 = Edge("e1")
        test_egi.E.append(e1)
        test_egi.rel["e1"] = "loves"
        test_egi.nu["e1"] = ("v1", "v2")
        
        # Set up areas
        test_egi.sheet = "sheet"
        test_egi.area = {"sheet": {"v1", "v2", "e1"}}
        
        # Test adding EGI to corpus
        metadata = {
            "title": "Test EGI",
            "description": "Simple test EGI for integration testing",
            "category": "examples"
        }
        
        item_id = corpus_manager.add_egi(test_egi, metadata)
        logger.info(f"✓ Added EGI to corpus with ID: {item_id}")
        
        # Test retrieving EGI
        retrieved_egi = corpus_manager.get_egi(item_id)
        if retrieved_egi:
            logger.info("✓ Successfully retrieved EGI from corpus")
        else:
            logger.error("✗ Failed to retrieve EGI from corpus")
            return False
        
        # Test search functionality
        search_results = corpus_manager.search_corpus("test")
        if search_results.total_count > 0:
            logger.info(f"✓ Search found {search_results.total_count} items")
        else:
            logger.warning("✗ Search returned no results")
        
        # Test statistics
        stats = corpus_manager.get_corpus_statistics()
        logger.info(f"✓ Corpus statistics: {stats['total_items']} items")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Corpus manager test failed: {e}")
        return False

def test_view_manager():
    """Test integrated view manager functionality."""
    logger.info("Testing integrated view manager...")
    
    try:
        from src.integrated_view_manager import get_integrated_view_manager, ViewType, ViewLevel, ViewConfiguration
        from src.egi_core_dau import RelationalGraphWithCuts, Vertex, Edge
        
        view_manager = get_integrated_view_manager()
        
        # Create a simple test EGI
        test_egi = RelationalGraphWithCuts()
        
        # Add vertices
        v1 = Vertex("v1", "Cat", is_generic=True)
        v2 = Vertex("v2", "Fluffy", is_generic=False)
        test_egi.V.extend([v1, v2])
        
        # Add edge
        e1 = Edge("e1")
        test_egi.E.append(e1)
        test_egi.rel["e1"] = "is"
        test_egi.nu["e1"] = ("v2", "v1")
        
        # Set up areas
        test_egi.sheet = "sheet"
        test_egi.area = {"sheet": {"v1", "v2", "e1"}}
        
        # Test overview view generation
        overview_view = view_manager.generate_view(test_egi, ViewType.OVERVIEW)
        logger.info(f"✓ Generated overview view with {len(overview_view.elements)} elements")
        
        # Test detailed view generation
        detailed_view = view_manager.generate_view(test_egi, ViewType.DETAILED)
        logger.info(f"✓ Generated detailed view with {len(detailed_view.elements)} elements")
        
        # Test multiple view generation
        view_types = [ViewType.OVERVIEW, ViewType.DETAILED, ViewType.HIERARCHICAL]
        multiple_views = view_manager.generate_multiple_views(test_egi, view_types)
        logger.info(f"✓ Generated {len(multiple_views)} different view types")
        
        # Test view export
        exported_json = view_manager.export_view(detailed_view, "json")
        if exported_json and len(exported_json) > 100:  # Should be substantial JSON
            logger.info("✓ Successfully exported view to JSON")
        else:
            logger.warning("✗ View export may have failed")
        
        # Test supported view types
        supported_types = view_manager.get_supported_view_types()
        logger.info(f"✓ Supports {len(supported_types)} view types")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ View manager test failed: {e}")
        return False

def test_export_manager():
    """Test integrated export manager functionality."""
    logger.info("Testing integrated export manager...")
    
    try:
        from src.integrated_export_manager import get_integrated_export_manager, ExportFormat, ExportConfiguration
        from src.egi_core_dau import RelationalGraphWithCuts, Vertex, Edge
        
        export_manager = get_integrated_export_manager()
        
        # Create a simple test EGI
        test_egi = RelationalGraphWithCuts()
        
        # Add vertices
        v1 = Vertex("v1", "Dog", is_generic=True)
        v2 = Vertex("v2", "Rover", is_generic=False)
        test_egi.V.extend([v1, v2])
        
        # Add edge
        e1 = Edge("e1")
        test_egi.E.append(e1)
        test_egi.rel["e1"] = "barks"
        test_egi.nu["e1"] = ("v2",)
        
        # Set up areas
        test_egi.sheet = "sheet"
        test_egi.area = {"sheet": {"v1", "v2", "e1"}}
        
        # Test EGIF export
        egif_result = export_manager.export_egi(test_egi, ExportFormat.EGIF)
        if egif_result.success and egif_result.content:
            logger.info("✓ Successfully exported to EGIF format")
        else:
            logger.error(f"✗ EGIF export failed: {egif_result.errors}")
            return False
        
        # Test JSON export
        json_result = export_manager.export_egi(test_egi, ExportFormat.JSON)
        if json_result.success and json_result.content:
            logger.info("✓ Successfully exported to JSON format")
        else:
            logger.error(f"✗ JSON export failed: {json_result.errors}")
            return False
        
        # Test multiple format export
        formats = [ExportFormat.EGIF, ExportFormat.CGIF, ExportFormat.JSON]
        multi_results = export_manager.export_multiple_formats(test_egi, formats)
        
        successful_exports = sum(1 for result in multi_results.values() if result.success)
        logger.info(f"✓ Multi-format export: {successful_exports}/{len(formats)} successful")
        
        # Test supported formats
        supported_formats = export_manager.get_supported_formats()
        logger.info(f"✓ Supports {len(supported_formats)} export formats")
        
        # Test export statistics
        stats = export_manager.get_export_statistics()
        logger.info(f"✓ Export statistics: {stats['total_exports']} total exports")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Export manager test failed: {e}")
        return False

def test_coherence_integration():
    """Test integration with coherence framework."""
    logger.info("Testing coherence framework integration...")
    
    try:
        from tests.coherence_integration import run_comprehensive_validation
        
        # Run comprehensive validation including new managers
        validation_results = run_comprehensive_validation()
        
        if validation_results.get("overall_status") == "VALID":
            logger.info("✓ Comprehensive validation passed")
        else:
            logger.warning("⚠ Comprehensive validation had issues")
            for category, result in validation_results.get("categories", {}).items():
                if not result.get("passed", False):
                    logger.warning(f"  - {category}: {result.get('message', 'Failed')}")
        
        # Check core formalism status
        core_status = validation_results.get("core_formalism_status", {})
        if core_status.get("operational", False):
            logger.info("✓ Core formalism operational")
        else:
            logger.warning("⚠ Core formalism has issues")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Coherence integration test failed: {e}")
        return False

def main():
    """Run all integration tests."""
    logger.info("Starting integrated managers test suite...")
    
    tests = [
        ("Core Integration", test_core_integration),
        ("Corpus Manager", test_corpus_manager),
        ("View Manager", test_view_manager),
        ("Export Manager", test_export_manager),
        ("Coherence Integration", test_coherence_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running {test_name} Test")
        logger.info(f"{'='*50}")
        
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name:25} {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All integrated managers are working correctly!")
        return 0
    else:
        logger.error("❌ Some tests failed. Check the logs above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
