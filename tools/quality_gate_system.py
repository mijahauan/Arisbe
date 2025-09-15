#!/usr/bin/env python3
"""
Standalone quality gate system for AI coherence framework.
"""
import subprocess
import sys
import os

def run_quality_checks():
    """Run basic quality checks without the full coherence framework."""
    print("Running basic quality checks...")
    
    # Run tests
    print("🧪 Running tests...")
    result = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ Tests failed")
        return False
    else:
        print("✅ Tests passed")
    
    # Check for basic syntax errors
    print("🔍 Checking syntax...")
    for root, dirs, files in os.walk("src"):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                result = subprocess.run([sys.executable, "-m", "py_compile", filepath],
                                      capture_output=True)
                if result.returncode != 0:
                    print(f"❌ Syntax error in {filepath}")
                    return False
    
    print("✅ All quality checks passed")
    return True

def main():
    success = run_quality_checks()
    if not success:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
