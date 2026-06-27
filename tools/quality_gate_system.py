#!/usr/bin/env python3
"""
Standalone quality gate system for AI coherence framework.
"""
import subprocess
import sys
import os

def run_quality_checks():
    """Run basic quality checks with core protection enforcement."""
    print("Running enhanced quality checks with core protection...")
    
    # Step 1: Core Protection Check
    print("🔒 Enforcing core protection...")
    try:
        protection_result = subprocess.run([sys.executable, "tools/core_protection_system.py"], 
                                         capture_output=True, text=True)
        if protection_result.returncode != 0:
            print("❌ Core protection check failed")
            print(protection_result.stdout)
            return False
        else:
            print("✅ Core protection check passed")
    except Exception as e:
        print(f"⚠️  Core protection system unavailable: {e}")
    
    # Step 2: Run the core mathematical test suite (the protected-logic subset;
    # see CLAUDE.md "Core Protection System"). The full ~1350-test suite takes
    # ~12 minutes and belongs to CI / manual runs, not the commit gate. This
    # subset is headless pure-Python (~150 tests, <30s) and MUST pass.
    print("🧪 Running core tests...")
    core_test_files = [
        "tests/test_egi_core_comprehensive.py",
        "tests/test_chapter15_formal_calculus.py",
        "tests/test_rule_interaction.py",
        "tests/test_subgraph_closure_validation.py",
        "tests/test_graph_isomorphism_engine.py",
        "tests/test_it_minus_with_isomorphism.py",
        "tests/test_beta_proof_exercises.py",
        "tests/test_beta_modus_ponens_proof.py",
        "tests/test_beta_converse_proof.py",
        "tests/test_logical_proof_exercises.py",
        "tests/test_induction_proofs.py",
        # NOTE (2026-06-27): the correspondence invariant's runtime enforcers
        # (correspondence_attestation / presentation_ops / natural_layout) are now
        # protected modules, but the corpus-wide `test_correspondence_*` suites are
        # NOT added here — they generate layouts (ELK) and take minutes, busting
        # this gate's <30s budget / 180s timeout. They run in full CI instead.
    ]

    # Prefer the uv-managed environment (the project standard); fall back to
    # the current interpreter if uv is unavailable.
    import shutil
    if shutil.which("uv"):
        pytest_cmd = ["uv", "run", "pytest"]
    else:
        pytest_cmd = [sys.executable, "-m", "pytest"]

    try:
        result = subprocess.run(pytest_cmd + core_test_files + ["-q", "--tb=short"],
                              capture_output=True, text=True, timeout=180)
        if result.returncode != 0:
            print("❌ Core tests failed")
            print("STDOUT:", result.stdout[-1500:] if result.stdout else "No stdout")
            print("STDERR:", result.stderr[-500:] if result.stderr else "No stderr")
            return False
        else:
            print("✅ Core tests passed")
            # Show test count for transparency
            if "passed" in result.stdout:
                import re
                match = re.search(r'(\d+) passed', result.stdout)
                if match:
                    print(f"   {match.group(1)} core tests passed")
    except subprocess.TimeoutExpired:
        # The core subset is headless and fast; a timeout means something is
        # genuinely wrong, so fail loudly rather than waving it through.
        print("❌ Core tests timed out (>180s) — the core subset runs in <30s, so this is a real problem")
        return False
    
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
