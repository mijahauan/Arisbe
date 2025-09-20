#!/usr/bin/env python3
"""
Core Protection System - Protects validated core modules from unauthorized changes

This system implements strict protection for the 16 validated core modules
that have been tested with 87/87 passing tests. Any modifications to these
modules require explicit authorization and justification.
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
        
        # Protected core modules (from our analysis)
        self.protected_modules = {
            'area_spatial_constraint_system.py',
            'cgif_generator_dau.py',
            'cgif_parser_dau.py',
            'egi_core_dau.py',
            'egi_io.py',
            'egif_generator_dau.py',
            'egif_parser_dau.py',
            'enhanced_ligature_algorithms.py',
            'formal_transformation_rules.py',
            'hierarchical_index.py',
            'ligature_aware_positioning_engine.py',
            'ligature_manipulation_rules.py',
            'ligature_optimization_engine.py',
            'obstacle_aware_ligature_router.py',
            'single_object_ligature_detector.py',
            'syntactic_equivalence_checker.py'
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
        
        core_test_files = [
            "tests/test_egi_core_comprehensive.py",
            "tests/test_ligature_algorithms_working.py", 
            "tests/test_performance_working.py",
            "tests/test_chapter15_formal_calculus.py",
            "tests/test_chapter16_17_ligature_soundness_simplified.py",
            "tests/test_chapter20_syntactic_equivalence.py",
            "tests/test_advanced_performance_optimization.py",
            "tests/test_complete_serialization_simplified.py",
            "tests/test_production_scalability_validation.py",
            "tests/test_complete_system_integration.py",
            "tests/test_final_production_readiness.py",
            "tests/test_comprehensive_edge_case_validation.py"
        ]
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest"
            ] + core_test_files + [
                "-v", "--tb=short"
            ], capture_output=True, text=True, cwd=self.project_root)
            
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
            
            return {
                "test_result": "PASS" if result.returncode == 0 else "FAIL",
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "expected_passed": 87,
                "core_integrity": "MAINTAINED" if passed_tests >= 87 and failed_tests == 0 else "COMPROMISED"
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
        
        # Step 4: All checks passed - allow with logging
        print("\n✅ CORE MODIFICATION ALLOWED")
        print("   - Authorization confirmed")
        print("   - Core integrity maintained")
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
