"""
Coherence Analyzer - Automated Codebase Coherence Analysis

This module provides automated analysis of codebase coherence, tracking:
- Function registration completeness
- Component integration status  
- Test coverage alignment
- Foundation stability metrics
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

class CoherenceAnalyzer:
    """Analyze and report on codebase coherence metrics."""
    
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.analysis_results = {}
        
    def run_full_analysis(self) -> Dict[str, Any]:
        """Run comprehensive coherence analysis."""
        print("🔍 Running Arisbe Coherence Analysis...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "foundation_status": self._analyze_foundation_status(),
            "test_coverage": self._analyze_test_coverage(),
            "registry_completeness": self._analyze_registry_completeness(),
            "integration_health": self._analyze_integration_health(),
            "coherence_score": 0  # Will be calculated
        }
        
        # Calculate overall coherence score
        results["coherence_score"] = self._calculate_coherence_score(results)
        
        return results
    
    def _analyze_foundation_status(self) -> Dict[str, Any]:
        """Analyze foundation component status."""
        print("  📊 Analyzing foundation status...")
        
        # Run the EGI integrity test suite
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "tests/test_egi_integrity_suite.py::EGIIntegrityTestSuite::test_comprehensive_egi_integrity",
                "--tb=no", "-q"
            ], capture_output=True, text=True, cwd=self.root_path)
            
            integrity_passing = result.returncode == 0
            
        except Exception as e:
            print(f"    ⚠️  Could not run integrity tests: {e}")
            integrity_passing = False
        
        # Check for critical files
        critical_files = [
            "src/egi_core_dau.py",
            "src/clif_parser_dau.py", 
            "src/clif_generator_dau.py",
            "src/cgif_parser_dau.py",
            "src/cgif_generator_dau.py",
            "src/egif_parser_dau.py",
            "src/egif_generator_dau.py",
            "src/graph_isomorphism_engine.py",
            "src/formal_transformation_rules.py"
        ]
        
        files_present = sum(1 for f in critical_files if (self.root_path / f).exists())
        
        return {
            "integrity_tests_passing": integrity_passing,
            "critical_files_present": files_present,
            "total_critical_files": len(critical_files),
            "foundation_completeness": files_present / len(critical_files)
        }
    
    def _analyze_test_coverage(self) -> Dict[str, Any]:
        """Analyze test coverage metrics."""
        print("  🧪 Analyzing test coverage...")
        
        try:
            # Run pytest to get test results
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "tests/", "--tb=no", "-q"
            ], capture_output=True, text=True, cwd=self.root_path)
            
            output_lines = result.stdout.split('\n')
            summary_line = [line for line in output_lines if 'failed' in line or 'passed' in line][-1]
            
            # Parse test results
            if 'passed' in summary_line:
                parts = summary_line.split()
                passed = failed = 0
                for i, part in enumerate(parts):
                    if 'passed' in part:
                        passed = int(parts[i-1]) if i > 0 else 0
                    elif 'failed' in part:
                        failed = int(parts[i-1]) if i > 0 else 0
                
                total = passed + failed
                pass_rate = passed / total if total > 0 else 0
            else:
                pass_rate = 0
                passed = failed = 0
                
        except Exception as e:
            print(f"    ⚠️  Could not analyze test coverage: {e}")
            pass_rate = 0
            passed = failed = 0
        
        return {
            "test_pass_rate": pass_rate,
            "tests_passed": passed,
            "tests_failed": failed,
            "coverage_acceptable": pass_rate >= 0.90
        }
    
    def _analyze_registry_completeness(self) -> Dict[str, Any]:
        """Analyze coherence registry completeness."""
        print("  📋 Analyzing registry completeness...")
        
        try:
            # Try to import and check registry
            sys.path.insert(0, str(self.root_path / "src"))
            from coherence_registry import get_coherence_registry
            
            registry = get_coherence_registry()
            quick_ref = registry.get_quick_reference()
            
            return {
                "registry_accessible": True,
                "total_functions": quick_ref["total_functions"],
                "total_components": quick_ref["total_components"],
                "categories_populated": sum(1 for cat_data in quick_ref["categories"].values() 
                                          if cat_data["functions"] > 0 or cat_data["components"] > 0)
            }
            
        except Exception as e:
            print(f"    ⚠️  Could not access coherence registry: {e}")
            return {
                "registry_accessible": False,
                "total_functions": 0,
                "total_components": 0,
                "categories_populated": 0
            }
    
    def _analyze_integration_health(self) -> Dict[str, Any]:
        """Analyze integration component health."""
        print("  🔗 Analyzing integration health...")
        
        # Check for integration files
        integration_files = [
            "src/core_dau_formalism.py",
            "src/integration_interfaces.py",
            "src/hierarchical_index.py"
        ]
        
        files_present = sum(1 for f in integration_files if (self.root_path / f).exists())
        
        return {
            "integration_files_present": files_present,
            "total_integration_files": len(integration_files),
            "integration_completeness": files_present / len(integration_files)
        }
    
    def _calculate_coherence_score(self, results: Dict[str, Any]) -> float:
        """Calculate overall coherence score (0-100)."""
        
        foundation_score = results["foundation_status"]["foundation_completeness"] * 30
        test_score = results["test_coverage"]["test_pass_rate"] * 40
        registry_score = (1 if results["registry_completeness"]["registry_accessible"] else 0) * 20
        integration_score = results["integration_health"]["integration_completeness"] * 10
        
        return foundation_score + test_score + registry_score + integration_score
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate human-readable coherence report."""
        
        score = results["coherence_score"]
        status = "🟢 EXCELLENT" if score >= 90 else "🟡 GOOD" if score >= 70 else "🔴 NEEDS ATTENTION"
        
        report = f"""
Arisbe Codebase Coherence Report
================================
Generated: {results["timestamp"]}
Overall Score: {score:.1f}/100 {status}

Foundation Status:
  • Integrity Tests: {"✅ PASSING" if results["foundation_status"]["integrity_tests_passing"] else "❌ FAILING"}
  • Critical Files: {results["foundation_status"]["critical_files_present"]}/{results["foundation_status"]["total_critical_files"]} present
  • Completeness: {results["foundation_status"]["foundation_completeness"]:.1%}

Test Coverage:
  • Pass Rate: {results["test_coverage"]["test_pass_rate"]:.1%}
  • Tests Passed: {results["test_coverage"]["tests_passed"]}
  • Tests Failed: {results["test_coverage"]["tests_failed"]}
  • Status: {"✅ ACCEPTABLE" if results["test_coverage"]["coverage_acceptable"] else "❌ NEEDS IMPROVEMENT"}

Registry Completeness:
  • Registry Access: {"✅ WORKING" if results["registry_completeness"]["registry_accessible"] else "❌ BROKEN"}
  • Functions Registered: {results["registry_completeness"]["total_functions"]}
  • Components Registered: {results["registry_completeness"]["total_components"]}

Integration Health:
  • Integration Files: {results["integration_health"]["integration_files_present"]}/{results["integration_health"]["total_integration_files"]} present
  • Completeness: {results["integration_health"]["integration_completeness"]:.1%}

Recommendations:
"""
        
        if score < 70:
            report += "  🚨 CRITICAL: Foundation needs immediate attention before GUI development\n"
        elif score < 90:
            report += "  ⚠️  Foundation is functional but could be strengthened\n"
        else:
            report += "  ✅ Foundation is solid and ready for GUI development\n"
            
        return report
