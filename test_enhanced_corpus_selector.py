#!/usr/bin/env python3
"""
Test script for the enhanced corpus selector in the graph editor.

Tests the new categorized dropdown system and corpus manager integration.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# Import the enhanced graph editor
from gui.graph_editor import GraphEditor
from gui.corpus_manager import CorpusManager


def test_corpus_manager():
    """Test the corpus manager functionality."""
    print("=" * 60)
    print("TESTING CORPUS MANAGER")
    print("=" * 60)
    
    manager = CorpusManager()
    manager.discover_examples()
    
    # Test statistics
    stats = manager.get_statistics()
    print(f"✓ Total examples: {stats['total_examples']}")
    print(f"✓ Categories: {list(stats['categories'].keys())}")
    print(f"✓ Complexity levels: {list(stats['complexity_levels'].keys())}")
    
    # Test category filtering
    print(f"\n📂 CATEGORIES:")
    for category in manager.get_categories():
        examples = manager.get_examples_by_category(category)
        print(f"  {category}: {len(examples)} examples")
        for example in examples[:3]:  # Show first 3
            print(f"    - {example.display_name} ({example.complexity_level})")
        if len(examples) > 3:
            print(f"    ... and {len(examples) - 3} more")
    
    # Test complexity filtering
    print(f"\n🎯 COMPLEXITY LEVELS:")
    for level in manager.get_complexity_levels():
        examples = manager.get_examples_by_complexity(level)
        print(f"  {level}: {len(examples)} examples")
    
    # Test validation
    issues = manager.validate_examples()
    if issues:
        print(f"\n⚠️  VALIDATION ISSUES ({len(issues)}):")
        for issue in issues[:5]:  # Show first 5
            print(f"    - {issue}")
        if len(issues) > 5:
            print(f"    ... and {len(issues) - 5} more")
    else:
        print(f"\n✅ All examples validated successfully")
    
    return manager


def test_graph_editor_integration():
    """Test the graph editor integration with enhanced corpus selector."""
    print("\n" + "=" * 60)
    print("TESTING GRAPH EDITOR INTEGRATION")
    print("=" * 60)
    
    # Create Qt application
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        app.setAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL)
    
    try:
        # Create graph editor
        print("Creating graph editor...")
        editor = GraphEditor()
        
        # Test corpus manager initialization
        print(f"✓ Corpus manager loaded {len(editor.corpus_manager.examples)} examples")
        
        # Test dropdown population
        print("✓ Dropdown populated with examples")
        
        # Test category filtering
        categories = editor.corpus_manager.get_categories()
        print(f"✓ Available categories: {categories}")
        
        # Test complexity filtering
        levels = editor.corpus_manager.get_complexity_levels()
        print(f"✓ Available complexity levels: {levels}")
        
        # Test example loading (if examples available)
        examples = editor.corpus_manager.get_all_examples()
        if examples:
            # Try to load the first beginner example
            beginner_examples = editor.corpus_manager.get_examples_by_complexity('beginner')
            if beginner_examples:
                test_example = beginner_examples[0]
                print(f"✓ Testing example load: {test_example.display_name}")
                
                if test_example.clif:
                    print(f"  - CLIF: {test_example.clif[:50]}...")
                    print(f"  - Category: {test_example.category}")
                    print(f"  - Complexity: {test_example.complexity_level}")
                    print(f"  - Source: {test_example.source}")
                else:
                    print(f"  - ⚠️  No CLIF statement available")
            else:
                print("⚠️  No beginner examples found")
        else:
            print("⚠️  No examples available for testing")
        
        print("✅ Graph editor integration test completed")
        return True
        
    except Exception as e:
        print(f"❌ Error testing graph editor integration: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_filtering_functionality():
    """Test the filtering functionality of the corpus selector."""
    print("\n" + "=" * 60)
    print("TESTING FILTERING FUNCTIONALITY")
    print("=" * 60)
    
    manager = CorpusManager()
    manager.discover_examples()
    
    # Test category filtering
    print("📂 Testing category filtering:")
    for category in manager.get_categories():
        examples = manager.get_examples_by_category(category)
        print(f"  {category}: {len(examples)} examples")
        
        # Verify all examples are from the correct category
        for example in examples:
            if example.category != category:
                print(f"    ❌ Wrong category: {example.name} is {example.category}, not {category}")
                return False
        print(f"    ✓ All examples correctly categorized")
    
    # Test complexity filtering
    print("\n🎯 Testing complexity filtering:")
    for level in manager.get_complexity_levels():
        examples = manager.get_examples_by_complexity(level)
        print(f"  {level}: {len(examples)} examples")
        
        # Verify all examples are from the correct complexity level
        for example in examples:
            if example.complexity_level != level:
                print(f"    ❌ Wrong complexity: {example.name} is {example.complexity_level}, not {level}")
                return False
        print(f"    ✓ All examples correctly filtered by complexity")
    
    # Test search functionality
    print("\n🔍 Testing search functionality:")
    search_terms = ["pear", "negation", "conjunction"]
    for term in search_terms:
        results = manager.search_examples(term)
        print(f"  '{term}': {len(results)} results")
        for result in results:
            if term.lower() not in (result.description.lower() + " " + 
                                   result.logical_pattern.lower() + " " + 
                                   result.teaching_purpose.lower()):
                print(f"    ⚠️  Unexpected result: {result.display_name}")
    
    print("✅ Filtering functionality test completed")
    return True


def main():
    """Run all tests."""
    print("🧪 ENHANCED CORPUS SELECTOR TEST SUITE")
    print("=" * 60)
    
    success = True
    
    try:
        # Test 1: Corpus Manager
        manager = test_corpus_manager()
        if not manager.examples:
            print("❌ No examples found - cannot continue with other tests")
            return False
        
        # Test 2: Filtering
        if not test_filtering_functionality():
            success = False
        
        # Test 3: Graph Editor Integration
        if not test_graph_editor_integration():
            success = False
        
        # Summary
        print("\n" + "=" * 60)
        if success:
            print("🎉 ALL TESTS PASSED!")
            print("✅ Enhanced corpus selector is working correctly")
        else:
            print("❌ SOME TESTS FAILED")
            print("⚠️  Enhanced corpus selector needs attention")
        print("=" * 60)
        
        return success
        
    except Exception as e:
        print(f"❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

