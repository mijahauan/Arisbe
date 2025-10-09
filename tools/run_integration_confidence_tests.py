#!/usr/bin/env python3
"""
Master test runner for integration confidence testing.
Runs all validation tests before merging the new layout engine.
"""

import sys
import subprocess
from pathlib import Path


def run_test(test_script: str, description: str) -> bool:
    """Run a test script and return success status."""
    print(f"\n{'='*70}")
    print(f"🧪 {description}")
    print(f"{'='*70}")
    
    try:
        result = subprocess.run(
            [sys.executable, test_script],
            cwd=Path(__file__).parent.parent,
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False


def main():
    """Run complete integration confidence test suite."""
    print("="*70)
    print("INTEGRATION CONFIDENCE TEST SUITE")
    print("Validating DefinitiveThreePassEngine integration")
    print("="*70)
    
    tests = [
        # Core functionality
        ("tools/test_diagram_controller.py", "DiagramController Tests (11 tests)"),
        ("tests/end_to_end/test_user_workflows.py", "Workflow Simulation Tests (8 tests)"),
        ("tools/test_gui_organon.py", "GUI Organon Tests (3 tests)"),
        
        # New validation tests
        ("tools/test_engine_comparison.py", "Engine Regression Comparison"),
        ("tools/test_position_persistence.py", "Position Persistence Validation"),
        ("tools/test_deterministic_layouts.py", "Deterministic Seeding Validation"),
    ]
    
    results = {}
    for script, description in tests:
        script_path = Path(__file__).parent.parent / script
        if not script_path.exists():
            print(f"⚠️  Skipping {description} - script not found")
            continue
        
        results[description] = run_test(str(script_path), description)
    
    # Summary
    print("\n" + "="*70)
    print("📊 INTEGRATION CONFIDENCE SUMMARY")
    print("="*70)
    
    for desc, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {desc}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"\n📈 Overall: {passed}/{total} test suites passed ({percentage:.0f}%)")
    
    # Confidence assessment
    if percentage >= 90:
        print("\n🎉 HIGH CONFIDENCE - Ready to merge!")
        confidence = "HIGH"
    elif percentage >= 75:
        print("\n✅ GOOD CONFIDENCE - Safe to merge with monitoring")
        confidence = "GOOD"
    elif percentage >= 50:
        print("\n⚠️  MODERATE CONFIDENCE - Review failures before merge")
        confidence = "MODERATE"
    else:
        print("\n❌ LOW CONFIDENCE - Fix critical issues before merge")
        confidence = "LOW"
    
    print(f"\n🎯 RECOMMENDATION: {confidence} confidence level")
    
    return passed >= total * 0.75  # 75% threshold for success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
