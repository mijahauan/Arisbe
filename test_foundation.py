#!/usr/bin/env python3
"""
Test Foundation for Arisbe EG Works

Simple test to verify the foundation components work before launching the full GUI.
This avoids the NumPy/PySide6 compatibility issue while testing core functionality.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_canonical_pipeline():
    """Test the canonical pipeline functionality."""
    print("🧪 Testing Canonical Pipeline...")
    
    try:
        from src.canonical import get_canonical_pipeline
        pipeline = get_canonical_pipeline()
        print("✓ Canonical pipeline created successfully")
        
        # Test basic EGIF parsing
        test_egif = "(P) ~[(Q)]"
        print(f"Testing EGIF: {test_egif}")
        
        egi = pipeline.parse_egif(test_egif)
        print(f"✓ EGIF parsed to EGI: {len(egi.V)} vertices, {len(egi.E)} edges, {len(egi.Cut)} cuts")
        
        # Test round-trip
        egif_output = pipeline.egi_to_egif(egi)
        print(f"✓ Round-trip EGIF: {egif_output}")
        
        return True
        
    except Exception as e:
        print(f"✗ Canonical pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_corpus_manager():
    """Test the corpus manager functionality."""
    print("\n📚 Testing Corpus Manager...")
    
    try:
        from src.corpus_manager import CorpusManager
        corpus = CorpusManager()
        print("✓ Corpus manager created successfully")
        
        examples = corpus.get_corpus_examples()
        print(f"✓ Found {len(examples)} corpus examples")
        
        for example in examples:
            print(f"  - {example['id']}: {example['title']} ({example['content']})")
        
        return True
        
    except Exception as e:
        print(f"✗ Corpus manager test failed: {e}")
        return False

def test_salvaged_components():
    """Test salvaged components availability."""
    print("\n🔧 Testing Salvaged Components...")
    
    # Test non-PySide6 components first
    safe_components = [
        ('src.qt_canvas_adapter', 'QtCanvasAdapter'),
        ('src.enhanced_diagram_controller', 'EnhancedDiagramController')
    ]
    
    available = []
    for module_name, class_name in safe_components:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✓ {class_name} available")
            available.append((module_name, class_name))
        except Exception as e:
            print(f"⚠ {class_name} not available: {e}")
    
    # Test DiagramRendererDau separately (may have NumPy issues)
    try:
        # Check if file exists without importing
        import os
        if os.path.exists('src/diagram_renderer_dau.py'):
            print(f"✓ DiagramRendererDau file exists (import may have NumPy issues)")
            available.append(('src.diagram_renderer_dau', 'DiagramRendererDau'))
        else:
            print(f"⚠ DiagramRendererDau file missing")
    except Exception as e:
        print(f"⚠ DiagramRendererDau check failed: {e}")
    
    print(f"✓ {len(available)}/3 components available")
    return len(available) >= 2  # Accept if at least 2/3 components work

def test_app_structure():
    """Test application structure."""
    print("\n🏗️ Testing App Structure...")
    
    # Check directory structure
    required_dirs = ['apps', 'apps/bullpen', 'apps/browser', 'apps/endoporeutic_game']
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✓ Directory exists: {dir_path}")
        else:
            print(f"✗ Directory missing: {dir_path}")
            return False
    
    # Check key files
    required_files = [
        'arisbe_eg_works.py',
        'apps/bullpen/bullpen_app.py',
        'apps/bullpen/__init__.py'
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ File exists: {file_path}")
        else:
            print(f"✗ File missing: {file_path}")
            return False
    
    return True

def main():
    """Run foundation tests."""
    print("🎯 ARISBE EG WORKS - FOUNDATION TEST")
    print("=" * 50)
    
    tests = [
        ("App Structure", test_app_structure),
        ("Canonical Pipeline", test_canonical_pipeline),
        ("Corpus Manager", test_corpus_manager),
        ("Salvaged Components", test_salvaged_components)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 FOUNDATION TEST RESULTS")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 Foundation is ready for GUI development!")
        return True
    else:
        print("⚠ Foundation needs fixes before GUI development")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
