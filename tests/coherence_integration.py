"""
Coherence Framework Integration for EGI Testing
Integrates the comprehensive EGI test suite with the coherence framework
for continuous validation during development.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

from .test_egi_integrity_suite import EGIIntegrityTestSuite, EGIIntegrityReporter
from .test_specifications_dau import ALL_TEST_SPECIFICATIONS, get_tests_by_priority


class CoherenceEGIValidator:
    """EGI validation component for the coherence framework."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.coherence_dir = self.project_root / ".coherence"
        self.test_results_file = self.coherence_dir / "egi_test_results.json"
        self.integrity_report_file = self.coherence_dir / "egi_integrity_report.txt"
    
    def run_egi_validation(self, priority_filter: str = None) -> Dict[str, Any]:
        """Run EGI validation tests with optional priority filtering."""
        print("🧪 Running EGI Integrity Validation...")
        
        # Filter tests by priority if specified
        if priority_filter:
            test_specs = get_tests_by_priority(priority_filter)
            print(f"Running {len(test_specs)} {priority_filter} priority tests")
        else:
            test_specs = ALL_TEST_SPECIFICATIONS
            print(f"Running all {len(test_specs)} EGI integrity tests")
        
        # Run the test suite
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "tests/test_egi_integrity_suite.py", 
                "-v", "--tb=short"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            test_success = result.returncode == 0
            
            # Parse test results
            validation_results = {
                "success": test_success,
                "total_tests": len(test_specs),
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timestamp": __import__('datetime').datetime.now().isoformat()
            }
            
            # Save results
            self._save_test_results(validation_results)
            
            # Generate integrity report
            if test_success:
                print("✅ EGI integrity validation passed")
            else:
                print("❌ EGI integrity validation failed")
                print(f"Error output: {result.stderr}")
            
            return validation_results
            
        except Exception as e:
            error_results = {
                "success": False,
                "error": str(e),
                "timestamp": __import__('datetime').datetime.now().isoformat()
            }
            self._save_test_results(error_results)
            return error_results
    
    def run_transformation_soundness_check(self, transformation_name: str = None) -> bool:
        """Run specific transformation soundness validation."""
        print(f"🔄 Checking transformation soundness: {transformation_name or 'all'}")
        
        # Run transformation-specific tests
        test_pattern = f"*transformation*{transformation_name}*" if transformation_name else "*transformation*"
        
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_egi_integrity_suite.py", 
            "-k", "transformation_soundness",
            "-v"
        ], capture_output=True, text=True, cwd=self.project_root)
        
        return result.returncode == 0
    
    def run_translation_fidelity_check(self, format_pair: Tuple[str, str] = None) -> bool:
        """Run translation fidelity validation for specific format pair."""
        format_desc = f"{format_pair[0]}↔{format_pair[1]}" if format_pair else "all formats"
        print(f"🔄 Checking translation fidelity: {format_desc}")
        
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_egi_integrity_suite.py", 
            "-k", "translation_fidelity",
            "-v"
        ], capture_output=True, text=True, cwd=self.project_root)
        
        return result.returncode == 0
    
    def validate_new_function(self, function_name: str, module_path: str) -> Dict[str, Any]:
        """Validate that a new function doesn't break EGI integrity."""
        print(f"🔍 Validating new function: {function_name} in {module_path}")
        
        # Run relevant subset of tests based on function type
        test_categories = self._determine_test_categories(function_name, module_path)
        
        validation_results = {}
        overall_success = True
        
        for category in test_categories:
            print(f"  Testing {category} compliance...")
            
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "tests/test_egi_integrity_suite.py", 
                "-k", category,
                "-v", "--tb=short"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            category_success = result.returncode == 0
            overall_success = overall_success and category_success
            
            validation_results[category] = {
                "success": category_success,
                "output": result.stdout if category_success else result.stderr
            }
        
        validation_results["overall_success"] = overall_success
        validation_results["function_name"] = function_name
        validation_results["module_path"] = module_path
        validation_results["timestamp"] = __import__('datetime').datetime.now().isoformat()
        
        return validation_results
    
    def _determine_test_categories(self, function_name: str, module_path: str) -> List[str]:
        """Determine which test categories are relevant for a function."""
        categories = []
        
        # Parser/Generator functions
        if "parser" in module_path or "generator" in module_path:
            categories.append("translation_fidelity")
        
        # Transformation functions
        if "transformation" in module_path or "rule" in function_name.lower():
            categories.extend(["transformation_soundness", "logical_equivalence"])
        
        # Core EGI functions
        if "egi_core" in module_path or "egi" in function_name.lower():
            categories.append("dau_compliance")
        
        # Default to all categories if uncertain
        if not categories:
            categories = ["logical_equivalence", "transformation_soundness", 
                         "translation_fidelity", "dau_compliance"]
        
        return categories
    
    def _save_test_results(self, results: Dict[str, Any]) -> None:
        """Save test results to coherence directory."""
        self.coherence_dir.mkdir(exist_ok=True)
        
        with open(self.test_results_file, 'w') as f:
            json.dump(results, f, indent=2)
    
    def generate_integrity_dashboard(self) -> str:
        """Generate EGI integrity dashboard for coherence framework."""
        if not self.test_results_file.exists():
            return "No EGI test results available. Run validation first."
        
        with open(self.test_results_file, 'r') as f:
            results = json.load(f)
        
        dashboard = [
            "EGI INTEGRITY DASHBOARD",
            "=" * 40,
            f"Last Updated: {results.get('timestamp', 'Unknown')}",
            f"Overall Status: {'✅ PASS' if results.get('success', False) else '❌ FAIL'}",
            f"Total Tests: {results.get('total_tests', 'Unknown')}",
            ""
        ]
        
        if not results.get('success', False):
            dashboard.extend([
                "ISSUES DETECTED:",
                "-" * 20,
                "• EGI integrity validation failed",
                "• Review test output for specific failures",
                "• Check transformation rule implementations",
                "• Verify linear form translation consistency",
                ""
            ])
        
        dashboard.extend([
            "RECOMMENDATIONS:",
            "-" * 20,
            "• Run 'python -m tests.coherence_integration validate' for full check",
            "• Use 'validate_function <name> <module>' for new functions",
            "• Monitor transformation soundness during development",
            "• Ensure round-trip translation fidelity",
            ""
        ])
        
        return "\n".join(dashboard)


def main():
    """Command-line interface for EGI validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="EGI Integrity Validation for Coherence Framework")
    parser.add_argument("command", choices=["validate", "transform", "translate", "function", "dashboard"])
    parser.add_argument("--priority", choices=["high", "medium", "low"], help="Filter tests by priority")
    parser.add_argument("--transformation", help="Specific transformation to test")
    parser.add_argument("--formats", nargs=2, help="Format pair for translation testing")
    parser.add_argument("--function", help="Function name to validate")
    parser.add_argument("--module", help="Module path for function validation")
    
    args = parser.parse_args()
    
    validator = CoherenceEGIValidator()
    
    if args.command == "validate":
        results = validator.run_egi_validation(args.priority)
        if not results["success"]:
            sys.exit(1)
    
    elif args.command == "transform":
        success = validator.run_transformation_soundness_check(args.transformation)
        if not success:
            sys.exit(1)
    
    elif args.command == "translate":
        format_pair = tuple(args.formats) if args.formats else None
        success = validator.run_translation_fidelity_check(format_pair)
        if not success:
            sys.exit(1)
    
    elif args.command == "function":
        if not args.function or not args.module:
            print("Error: --function and --module required for function validation")
            sys.exit(1)
        
        results = validator.validate_new_function(args.function, args.module)
        if not results["overall_success"]:
            print("Function validation failed:")
            for category, result in results.items():
                if category not in ["overall_success", "function_name", "module_path", "timestamp"]:
                    if not result["success"]:
                        print(f"  {category}: FAILED")
            sys.exit(1)
    
    elif args.command == "dashboard":
        dashboard = validator.generate_integrity_dashboard()
        print(dashboard)


if __name__ == "__main__":
    main()
