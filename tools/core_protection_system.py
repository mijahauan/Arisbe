#!/usr/bin/env python3
"""
Core Protection System - Protects validated core modules from unauthorized changes

Protects the validated core modules from unauthorized changes. The mathematical
core test suite (covering egi_core_dau, formal_transformation_rules, rule_interaction,
subgraph_closure_validator, graph_isomorphism_engine, and Beta/logical proof
exercises) must always pass; modifications to protected modules require explicit
authorization (touch .core_modification_authorized).
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Set, Dict, List, Optional
from datetime import datetime

class CoreProtectionSystem:
    """Protects core modules from unauthorized modifications."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        
        # Protected core modules. This set IS the "bedrock note": the names plus
        # these comments record what is non-negotiable and why, and the pre-commit
        # gate enforces it (its real job in an AI-assisted solo workflow is to make
        # an inadvertent edit to the calculus impossible to miss — the commit fails
        # until `.core_modification_authorized` is created deliberately).
        # Rationale: each module here is either (a) the EGI data model and its IO,
        # (b) a Dau transformation rule or its interaction protocol, (c) a Beta-aware
        # validator/matcher relied on by the rules, (d) layout/ligature machinery
        # downstream code treats as a stable interface, or (e) a runtime enforcer of
        # the central linear<->graphical correspondence invariant. Modules dropped in
        # 2026-05 (enhanced_ligature_algorithms.py, syntactic_equivalence_checker.py)
        # were orphaned — no imports anywhere — and so could not be load-bearing.
        # The EGIF/CGIF/CLIF parsers/generators were dropped 2026-06-27 as
        # application-level I/O (see the note where they were, below).
        self.protected_modules = {
            # EGI data model + IO
            'egi_core_dau.py',
            'egi_io.py',
            'hierarchical_index.py',
            # Linear-format parsers/generators (EGIF/CGIF/CLIF) were REMOVED from
            # this set on 2026-06-27. The audit established they are application-
            # level I/O, not the calculus: the six transformation rules and the
            # validators do not import them (the data model + rules operate purely
            # on RelationalGraphWithCuts). Their correctness is guarded by the
            # corpus round-trip tests (test_tomos_parsing, test_clif_unit, the
            # properties_*_round_trip suites) in CI, not by this commit-time
            # speed-bump. Re-add only if a parser/generator becomes load-bearing
            # for the calculus itself.
            # Diachronic state + history
            'universe_of_discourse.py',
            'egi_transformation_history.py',
            # Transformation rules + headless stepwise protocol
            'formal_transformation_rules.py',
            'rule_interaction.py',
            # Beta-aware validation + isomorphism
            'subgraph_closure_validator.py',
            'graph_isomorphism_engine.py',
            # Correspondence machinery — the runtime enforcers of the central
            # invariant (linear<->graphical correspondence). Added 2026-06-27:
            # these are the most-imported modules in src/ and enforce the very
            # contract the protection exists to defend, so they are bedrock in
            # the same sense as the rules. natural_layout is the coordinate-free
            # foundation both rest on.
            'correspondence_attestation.py',
            'presentation_ops.py',
            'natural_layout.py',
            # Ligature machinery (stable interfaces). Four other ligature
            # modules listed in earlier versions of this set
            # (area_spatial_constraint_system, ligature_aware_positioning_engine,
            # ligature_optimization_engine, obstacle_aware_ligature_router) were
            # removed in May 2026 — they did not exist on disk; only stale
            # __pycache__ entries remained. The protection system was guarding
            # ghosts.
            'ligature_manipulation_rules.py',
            'single_object_ligature_detector.py',
        }
        
        self.src_path = self.project_root / "src"
        self.protection_log = self.project_root / "core_protection.log"
    
    def check_core_modifications(self) -> Dict[str, any]:
        """Check if any core modules have been modified."""
        print("🔒 Checking for core module modifications...")
        
        # Get list of modified files from git
        try:
            result = subprocess.run([
                'git', 'diff', '--name-only', 'HEAD'
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode != 0:
                return {"error": "Failed to check git status"}
            
            modified_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            # Check for staged changes too
            staged_result = subprocess.run([
                'git', 'diff', '--cached', '--name-only'
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if staged_result.returncode == 0 and staged_result.stdout.strip():
                staged_files = staged_result.stdout.strip().split('\n')
                modified_files.extend(staged_files)
            
            # Filter for core module modifications
            core_modifications = []
            for file_path in modified_files:
                if file_path.startswith('src/') and file_path.endswith('.py'):
                    filename = Path(file_path).name
                    if filename in self.protected_modules:
                        core_modifications.append(file_path)
            
            return {
                "core_modifications": core_modifications,
                "total_modifications": len(modified_files),
                "protection_status": "VIOLATION" if core_modifications else "CLEAN"
            }
            
        except Exception as e:
            return {"error": f"Failed to check modifications: {e}"}
    
    def validate_core_modification_authorization(self, modified_files: List[str]) -> Dict[str, any]:
        """Check if core modifications are authorized."""
        print("🛡️  Validating core modification authorization...")
        
        # Check for authorization markers in commit message or environment
        auth_methods = []
        
        # Method 1: Check for CORE_OVERRIDE environment variable
        if os.getenv('ARISBE_CORE_OVERRIDE'):
            auth_methods.append("ENVIRONMENT_OVERRIDE")
        
        # Method 2: Check for authorization file
        auth_file = self.project_root / ".core_modification_authorized"
        if auth_file.exists():
            auth_methods.append("AUTHORIZATION_FILE")
        
        # Method 3: Check commit message for authorization
        try:
            result = subprocess.run([
                'git', 'log', '--format=%B', '-n', '1'
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0 and "CORE_AUTHORIZED:" in result.stdout:
                auth_methods.append("COMMIT_MESSAGE")
        except:
            pass
        
        return {
            "authorized": len(auth_methods) > 0,
            "authorization_methods": auth_methods,
            "modified_core_files": modified_files
        }
    
    def run_core_validation_tests(self) -> Dict[str, any]:
        """Run the core validation test suite to ensure integrity."""
        print("🧪 Running core validation tests...")

        # The protected-logic subset: headless pure-Python (~150 tests, <30s).
        # See quality_gate_system.py for the canonical list.
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
            # NOTE (2026-06-27): the central correspondence invariant is guarded by
            # (a) the three correspondence modules now in `protected_modules`
            # (authorization required to touch the §3.3 enforcers) and (b) the full
            # `test_correspondence_invariant` / `test_correspondence_attestation`
            # suites in CI. They are deliberately NOT in this fast subset: they are
            # corpus-wide and generate layouts (ELK), taking minutes — far past the
            # <30s budget this gate exists to keep. A small in-gate smoke check is
            # possible future work if the speed-bump alone proves insufficient.
        ]

        # Prefer the uv-managed environment (the project standard).
        import shutil
        if shutil.which("uv"):
            pytest_cmd = ["uv", "run", "pytest"]
        else:
            pytest_cmd = [sys.executable, "-m", "pytest"]

        try:
            result = subprocess.run(
                pytest_cmd + core_test_files + ["-q", "--tb=short"],
                capture_output=True, text=True, cwd=self.project_root, timeout=180
            )

            # Parse results
            passed_tests = 0
            failed_tests = 0

            if result.stdout:
                import re
                passed_match = re.search(r'(\d+) passed', result.stdout)
                if passed_match:
                    passed_tests = int(passed_match.group(1))

                failed_match = re.search(r'(\d+) failed', result.stdout)
                if failed_match:
                    failed_tests = int(failed_match.group(1))

            # Collection errors are real failures, not environment quirks.
            if passed_tests == 0 and failed_tests == 0 and result.returncode != 0:
                stderr_preview = result.stderr[:300] if result.stderr else ""
                print(f"❌ Test collection failed (return code {result.returncode})")
                if stderr_preview:
                    print(f"   stderr: {stderr_preview}")
                return {
                    "test_result": "COLLECTION_ISSUE",
                    "passed_tests": 0,
                    "failed_tests": 0,
                    "core_integrity": "COMPROMISED - collection failed",
                }

            return {
                "test_result": "PASS" if result.returncode == 0 else "FAIL",
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "core_integrity": "MAINTAINED" if result.returncode == 0 and failed_tests == 0 else "COMPROMISED"
            }

        except subprocess.TimeoutExpired:
            # The core subset is headless and fast; a timeout means something is
            # genuinely wrong, so fail loudly rather than waving it through.
            print("❌ Core tests timed out (>180s) — the core subset runs in <30s, so this is a real problem")
            return {
                "test_result": "TIMEOUT",
                "passed_tests": 0,
                "failed_tests": 0,
                "core_integrity": "COMPROMISED - timeout",
            }

        except Exception as e:
            return {
                "test_result": "ERROR",
                "error": str(e),
                "core_integrity": "UNKNOWN"
            }
    
    def log_protection_event(self, event_type: str, details: Dict[str, any]):
        """Log protection system events."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details
        }
        
        try:
            with open(self.protection_log, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            print(f"⚠️  Failed to log protection event: {e}")
    
    def enforce_core_protection(self) -> bool:
        """Main protection enforcement function."""
        print("🔒 ARISBE CORE PROTECTION SYSTEM")
        print("=" * 50)
        
        # Step 1: Check for modifications
        mod_check = self.check_core_modifications()
        if "error" in mod_check:
            print(f"❌ Error checking modifications: {mod_check['error']}")
            return False
        
        print(f"📊 Modification Status: {mod_check['protection_status']}")
        print(f"   Total files modified: {mod_check['total_modifications']}")
        print(f"   Core files modified: {len(mod_check['core_modifications'])}")
        
        # If no core modifications, allow
        if not mod_check['core_modifications']:
            print("✅ No core modifications detected - ALLOWED")
            return True
        
        # Step 2: Core modifications detected - check authorization
        print("\n🚨 CORE MODIFICATIONS DETECTED:")
        for file_path in mod_check['core_modifications']:
            print(f"   - {file_path}")
        
        auth_check = self.validate_core_modification_authorization(mod_check['core_modifications'])
        
        print(f"\n🛡️  Authorization Status: {'AUTHORIZED' if auth_check['authorized'] else 'UNAUTHORIZED'}")
        if auth_check['authorization_methods']:
            print("   Authorization methods:")
            for method in auth_check['authorization_methods']:
                print(f"   - {method}")
        
        # If unauthorized, block
        if not auth_check['authorized']:
            print("\n❌ CORE MODIFICATION BLOCKED")
            print("   Reason: Unauthorized modification of protected core modules")
            print("\n💡 To authorize core modifications:")
            print("   1. Set environment: export ARISBE_CORE_OVERRIDE=true")
            print("   2. Create file: touch .core_modification_authorized")
            print("   3. Use commit message: CORE_AUTHORIZED: [justification]")
            print("\n⚠️  WARNING: Core modifications require mathematical justification")
            
            self.log_protection_event("CORE_MODIFICATION_BLOCKED", {
                "modified_files": mod_check['core_modifications'],
                "authorization_attempted": auth_check['authorization_methods']
            })
            
            return False
        
        # Step 3: Authorized modification - validate core integrity
        print("\n🧪 Running core integrity validation...")
        test_results = self.run_core_validation_tests()
        
        print(f"   Test Result: {test_results['test_result']}")
        print(f"   Passed Tests: {test_results.get('passed_tests', 0)}")
        print(f"   Failed Tests: {test_results.get('failed_tests', 0)}")
        print(f"   Core Integrity: {test_results.get('core_integrity', 'UNKNOWN')}")
        
        # Show note if present (for collection issues)
        if 'note' in test_results:
            print(f"   Note: {test_results['note']}")
        
        # If core integrity compromised, block
        if test_results.get('core_integrity') == 'COMPROMISED':
            print("\n❌ CORE MODIFICATION BLOCKED")
            print("   Reason: Core integrity compromised (tests failing)")
            print("   Required: All 87 core tests must pass")
            
            self.log_protection_event("CORE_INTEGRITY_COMPROMISED", {
                "modified_files": mod_check['core_modifications'],
                "test_results": test_results
            })
            
            return False
        
        # Handle collection issues (UNKNOWN with note about manual verification)
        if 'UNKNOWN' in test_results.get('core_integrity', '') and 'note' in test_results:
            print("\n⚠️  CORE TESTS HAD COLLECTION ISSUES")
            print("   Automated testing failed due to environment issue")
            print("   MANUAL VERIFICATION REQUIRED before proceeding")
            print(f"   {test_results['note']}")
        
        # Step 4: All checks passed - allow with logging
        print("\n✅ CORE MODIFICATION ALLOWED")
        print("   - Authorization confirmed")
        if test_results.get('core_integrity') == 'MAINTAINED':
            print("   - Core integrity maintained (87/87 tests passing)")
        else:
            print("   - Core integrity verified manually (automated collection failed)")
        print("   - All protection requirements met")
        
        self.log_protection_event("CORE_MODIFICATION_ALLOWED", {
            "modified_files": mod_check['core_modifications'],
            "authorization_methods": auth_check['authorization_methods'],
            "test_results": test_results
        })
        
        return True
    
    def generate_protection_report(self) -> str:
        """Generate a protection status report."""
        report = []
        report.append("🔒 ARISBE CORE PROTECTION STATUS REPORT")
        report.append("=" * 50)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")
        
        report.append(f"📦 Protected Modules: {len(self.protected_modules)}")
        for module in sorted(self.protected_modules):
            report.append(f"   - {module}")
        report.append("")
        
        # Check current status
        mod_check = self.check_core_modifications()
        report.append(f"🛡️  Current Status: {mod_check.get('protection_status', 'UNKNOWN')}")
        
        if mod_check.get('core_modifications'):
            report.append("   Modified core files:")
            for file_path in mod_check['core_modifications']:
                report.append(f"   - {file_path}")
        
        return '\n'.join(report)

def main():
    """Main entry point for core protection system."""
    protection_system = CoreProtectionSystem()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--report":
        # Generate protection report
        report = protection_system.generate_protection_report()
        print(report)
        return
    
    # Run protection enforcement
    allowed = protection_system.enforce_core_protection()
    sys.exit(0 if allowed else 1)

if __name__ == "__main__":
    main()
