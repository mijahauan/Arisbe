#!/usr/bin/env python3
"""
Test Corpus Loading

Quick test to verify that corpus loading is working correctly
after fixing the source field type mismatch.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from corpus_browser import CorpusBrowser


def test_corpus_loading():
    """Test corpus loading functionality."""
    
    print("🧪 Testing Corpus Loading")
    print("=" * 30)
    
    try:
        # Create corpus browser (this triggers loading)
        corpus_browser = CorpusBrowser("corpus/corpus")
        
        # Check if examples were loaded
        if corpus_browser.examples:
            print(f"✅ Successfully loaded {len(corpus_browser.examples)} examples")
            
            # Show first few examples
            print("\n📚 Available Examples:")
            for i, (example_id, example) in enumerate(corpus_browser.examples.items()):
                if i >= 5:  # Show first 5
                    print(f"  ... and {len(corpus_browser.examples) - 5} more")
                    break
                print(f"  - {example.title} ({example.category})")
                print(f"    ID: {example_id}")
                print(f"    Pattern: {example.logical_pattern}")
                print(f"    EGIF: {example.egif_path.name if example.egif_path else 'None'}")
                print()
            
            # Test loading EGIF content from first example
            first_example = next(iter(corpus_browser.examples.values()))
            if first_example.egif_path and first_example.egif_path.exists():
                with open(first_example.egif_path, 'r') as f:
                    egif_content = f.read().strip()
                print(f"✅ Sample EGIF content from '{first_example.title}':")
                print(f"   {egif_content}")
                
                return True, egif_content
            else:
                print("⚠ First example has no EGIF file")
                return True, None
        else:
            print("❌ No examples loaded")
            return False, None
            
    except Exception as e:
        print(f"❌ Corpus loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None


if __name__ == "__main__":
    success, sample_egif = test_corpus_loading()
    
    if success:
        print("\n🎉 Corpus loading is working!")
        if sample_egif:
            print(f"📝 You can now test with: {sample_egif}")
    else:
        print("\n💥 Corpus loading still has issues")
