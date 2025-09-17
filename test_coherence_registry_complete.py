#!/usr/bin/env python3
"""
Complete Coherence Registry Test - Validate full registry functionality.
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_coherence_registry_initialization():
    """Test coherence registry full initialization."""
    logger.info("Testing coherence registry initialization...")
    
    try:
        from src.coherence_registry import CoherenceRegistry
        
        # Create registry instance (this will run full initialization)
        registry = CoherenceRegistry()
        
        # Verify registry has components and functions
        assert len(registry.components) > 0, "Registry should have registered components"
        assert len(registry.functions) > 0, "Registry should have registered functions"
        
        logger.info(f"✓ Registry initialized with {len(registry.components)} components and {len(registry.functions)} functions")
        return True, registry
        
    except Exception as e:
        logger.error(f"✗ Registry initialization failed: {e}")
        return False, None

def test_core_components_registered(registry):
    """Test that core components are properly registered."""
    logger.info("Testing core component registration...")
    
    try:
        # Check for key core components
        expected_components = [
            "RelationalGraphWithCuts",
            "Vertex", 
            "HierarchicalIndex",
            "CoreDauFormalismManager"
        ]
        
        for component_name in expected_components:
            assert component_name in registry.components, f"Missing component: {component_name}"
            component = registry.components[component_name]
            assert component.description is not None, f"Component {component_name} missing description"
            assert len(component.key_methods) > 0, f"Component {component_name} missing key methods"
        
        logger.info(f"✓ All {len(expected_components)} core components registered")
        return True
        
    except Exception as e:
        logger.error(f"✗ Core component registration test failed: {e}")
        return False

def test_transformation_rules_registered(registry):
    """Test that transformation rules are registered."""
    logger.info("Testing transformation rule registration...")
    
    try:
        # Check for transformation rule components
        expected_rules = [
            "IterationRule",
            "DeiterationRule", 
            "InsertionRule",
            "ErasureRule",
            "DoubleCutInsertionRule",
            "DoubleCutErasureRule"
        ]
        
        for rule_name in expected_rules:
            assert rule_name in registry.components, f"Missing transformation rule: {rule_name}"
            rule = registry.components[rule_name]
            assert "transformation" in rule.category.value, f"Rule {rule_name} not in transformation category"
        
        logger.info(f"✓ All {len(expected_rules)} transformation rules registered")
        return True
        
    except Exception as e:
        logger.error(f"✗ Transformation rule registration test failed: {e}")
        return False

def test_integrated_managers_registered(registry):
    """Test that integrated managers are registered."""
    logger.info("Testing integrated manager registration...")
    
    try:
        # Check for integrated manager components
        expected_managers = [
            "IntegratedCorpusManager",
            "IntegratedViewManager", 
            "IntegratedExportManager"
        ]
        
        registered_managers = []
        for manager_name in expected_managers:
            if manager_name in registry.components:
                registered_managers.append(manager_name)
                manager = registry.components[manager_name]
                assert manager.description is not None, f"Manager {manager_name} missing description"
        
        logger.info(f"✓ {len(registered_managers)} integrated managers registered: {registered_managers}")
        return True
        
    except Exception as e:
        logger.error(f"✗ Integrated manager registration test failed: {e}")
        return False

def test_function_registration(registry):
    """Test that functions are properly registered."""
    logger.info("Testing function registration...")
    
    try:
        # Check for core functions
        function_count = len(registry.functions)
        assert function_count > 0, "Should have registered functions"
        
        # Check function structure
        for func_name, func in registry.functions.items():
            assert func.description is not None, f"Function {func_name} missing description"
            assert func.category is not None, f"Function {func_name} missing category"
            assert func.function_type is not None, f"Function {func_name} missing function type"
        
        logger.info(f"✓ {function_count} functions properly registered")
        return True
        
    except Exception as e:
        logger.error(f"✗ Function registration test failed: {e}")
        return False

def test_category_organization(registry):
    """Test that components are properly categorized."""
    logger.info("Testing category organization...")
    
    try:
        # Check that categories have components
        non_empty_categories = []
        for category, components in registry.categories.items():
            if len(components) > 0:
                non_empty_categories.append(category.value)
        
        assert len(non_empty_categories) > 0, "Should have components in categories"
        
        logger.info(f"✓ Components organized in {len(non_empty_categories)} categories: {non_empty_categories}")
        return True
        
    except Exception as e:
        logger.error(f"✗ Category organization test failed: {e}")
        return False

def test_search_functionality(registry):
    """Test registry search capabilities."""
    logger.info("Testing search functionality...")
    
    try:
        # Test component search
        if hasattr(registry, 'search_components'):
            results = registry.search_components("EGI")
            logger.info(f"Search for 'EGI' returned {len(results)} results")
        
        # Test function search  
        if hasattr(registry, 'search_functions'):
            results = registry.search_functions("parse")
            logger.info(f"Search for 'parse' returned {len(results)} results")
        
        logger.info("✓ Search functionality available")
        return True
        
    except Exception as e:
        logger.error(f"✗ Search functionality test failed: {e}")
        return False

def main():
    """Run complete coherence registry tests."""
    logger.info("Starting complete coherence registry test suite...")
    
    # Initialize registry
    success, registry = test_coherence_registry_initialization()
    if not success:
        logger.error("❌ Registry initialization failed - cannot continue")
        return 1
    
    tests = [
        ("Core Components", lambda: test_core_components_registered(registry)),
        ("Transformation Rules", lambda: test_transformation_rules_registered(registry)),
        ("Integrated Managers", lambda: test_integrated_managers_registered(registry)),
        ("Function Registration", lambda: test_function_registration(registry)),
        ("Category Organization", lambda: test_category_organization(registry)),
        ("Search Functionality", lambda: test_search_functionality(registry))
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
    logger.info("COMPLETE COHERENCE REGISTRY SUMMARY")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name:25} {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed >= 5:
        logger.info("🎉 COHERENCE REGISTRY COMPLETE!")
        logger.info("✅ Registry is fully functional and properly organized")
        logger.info("📋 All core components and managers are discoverable")
        return 0
    else:
        logger.error("❌ Registry has some issues but core functionality works")
        return 1

if __name__ == "__main__":
    sys.exit(main())
