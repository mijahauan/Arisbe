#!/usr/bin/env python3
"""
Daily Quality Dashboard for Arisbe Coherence Framework
Generates comprehensive daily quality reports with persistent awareness.
"""

import subprocess
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any
import re

class DailyQualityDashboard:
    """Generate comprehensive daily quality reports."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.report_dir = self.project_root / "quality_reports"
        self.report_dir.mkdir(exist_ok=True)
        
    def run_tests_with_metrics(self) -> Dict[str, Any]:
        """Run tests and collect detailed metrics."""
        print("🧪 Running comprehensive test analysis...")
        
        # Run tests with detailed output
        result = subprocess.run([
            sys.executable, "-m", "pytest", "tests/", 
            "-v", "--tb=short", "--durations=10"
        ], capture_output=True, text=True, cwd=self.project_root)
        
        # Parse test results
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "error_tests": 0,
            "test_duration": 0,
            "failing_test_details": [],
            "performance_data": {},
            "coverage_data": {}
        }
        
        if result.stdout:
            # Extract test counts
            if "passed" in result.stdout:
                passed_match = re.search(r'(\d+) passed', result.stdout)
                if passed_match:
                    metrics["passed_tests"] = int(passed_match.group(1))
                    
            if "failed" in result.stdout:
                failed_match = re.search(r'(\d+) failed', result.stdout)
                if failed_match:
                    metrics["failed_tests"] = int(failed_match.group(1))
                    
            if "skipped" in result.stdout:
                skipped_match = re.search(r'(\d+) skipped', result.stdout)
                if skipped_match:
                    metrics["skipped_tests"] = int(skipped_match.group(1))
                    
            if "error" in result.stdout:
                error_match = re.search(r'(\d+) error', result.stdout)
                if error_match:
                    metrics["error_tests"] = int(error_match.group(1))
                    
            # Extract duration
            duration_match = re.search(r'in ([\d.]+)s', result.stdout)
            if duration_match:
                metrics["test_duration"] = float(duration_match.group(1))
                
            metrics["total_tests"] = (
                metrics["passed_tests"] + metrics["failed_tests"] + 
                metrics["skipped_tests"] + metrics["error_tests"]
            )
            
        # Store full output for analysis
        metrics["test_output"] = result.stdout
        metrics["test_errors"] = result.stderr
        metrics["return_code"] = result.returncode
        
        return metrics
    
    def analyze_code_quality(self) -> Dict[str, Any]:
        """Analyze code quality metrics."""
        print("🔍 Analyzing code quality...")
        
        quality_metrics = {
            "timestamp": datetime.now().isoformat(),
            "syntax_errors": [],
            "complexity_issues": [],
            "style_violations": [],
            "security_issues": []
        }
        
        # Check syntax errors
        for py_file in self.project_root.glob("src/**/*.py"):
            result = subprocess.run([
                sys.executable, "-m", "py_compile", str(py_file)
            ], capture_output=True)
            
            if result.returncode != 0:
                quality_metrics["syntax_errors"].append(str(py_file))
        
        # Note: Additional quality checks would go here
        # (flake8, mypy, bandit, etc. - if installed)
        
        return quality_metrics
    
    def track_performance_trends(self) -> Dict[str, Any]:
        """Track performance trends over time."""
        print("📈 Tracking performance trends...")
        
        # Run performance-specific tests
        perf_result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_performance_working.py",
            "tests/test_advanced_performance_optimization.py",
            "tests/test_production_scalability_validation.py",
            "-v", "--tb=no"
        ], capture_output=True, text=True, cwd=self.project_root)
        
        performance_data = {
            "timestamp": datetime.now().isoformat(),
            "performance_tests_passed": 0,
            "performance_tests_failed": 0,
            "performance_duration": 0,
            "performance_status": "UNKNOWN"
        }
        
        if perf_result.stdout:
            passed_match = re.search(r'(\d+) passed', perf_result.stdout)
            if passed_match:
                performance_data["performance_tests_passed"] = int(passed_match.group(1))
                
            failed_match = re.search(r'(\d+) failed', perf_result.stdout)
            if failed_match:
                performance_data["performance_tests_failed"] = int(failed_match.group(1))
                
            duration_match = re.search(r'in ([\d.]+)s', perf_result.stdout)
            if duration_match:
                performance_data["performance_duration"] = float(duration_match.group(1))
        
        # Determine performance status
        if performance_data["performance_tests_failed"] == 0:
            performance_data["performance_status"] = "EXCELLENT"
        elif performance_data["performance_tests_failed"] < 3:
            performance_data["performance_status"] = "GOOD"
        else:
            performance_data["performance_status"] = "NEEDS_ATTENTION"
            
        return performance_data
    
    def generate_daily_report(self) -> Dict[str, Any]:
        """Generate comprehensive daily quality report."""
        print("📊 Generating Daily Quality Dashboard...")
        print("=" * 60)
        
        # Collect all metrics
        test_metrics = self.run_tests_with_metrics()
        quality_metrics = self.analyze_code_quality()
        performance_metrics = self.track_performance_trends()
        
        # Compile comprehensive report
        report = {
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "report_timestamp": datetime.now().isoformat(),
            "overall_status": self._determine_overall_status(test_metrics, quality_metrics),
            "test_metrics": test_metrics,
            "quality_metrics": quality_metrics,
            "performance_metrics": performance_metrics,
            "recommendations": self._generate_recommendations(test_metrics, quality_metrics)
        }
        
        # Save report
        report_file = self.report_dir / f"daily_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        # Generate human-readable summary
        self._print_dashboard_summary(report)
        
        return report
    
    def _determine_overall_status(self, test_metrics: Dict, quality_metrics: Dict) -> str:
        """Determine overall project health status."""
        if test_metrics["failed_tests"] == 0 and len(quality_metrics["syntax_errors"]) == 0:
            return "EXCELLENT"
        elif test_metrics["failed_tests"] < 10 and len(quality_metrics["syntax_errors"]) == 0:
            return "GOOD"
        elif test_metrics["failed_tests"] < 50:
            return "NEEDS_ATTENTION"
        else:
            return "CRITICAL"
    
    def _generate_recommendations(self, test_metrics: Dict, quality_metrics: Dict) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        if test_metrics["failed_tests"] > 0:
            recommendations.append(f"Fix {test_metrics['failed_tests']} failing tests")
            
        if len(quality_metrics["syntax_errors"]) > 0:
            recommendations.append(f"Fix {len(quality_metrics['syntax_errors'])} syntax errors")
            
        if test_metrics["passed_tests"] > 200:
            recommendations.append("Consider test suite optimization for faster CI")
            
        if not recommendations:
            recommendations.append("Maintain current quality standards")
            
        return recommendations
    
    def _print_dashboard_summary(self, report: Dict[str, Any]):
        """Print human-readable dashboard summary."""
        print("\n🎯 ARISBE DAILY QUALITY DASHBOARD")
        print("=" * 60)
        print(f"📅 Date: {report['report_date']}")
        print(f"🎯 Overall Status: {report['overall_status']}")
        print()
        
        # Test Summary
        tm = report['test_metrics']
        print("🧪 TEST SUMMARY:")
        print(f"   Total Tests: {tm['total_tests']}")
        print(f"   ✅ Passed: {tm['passed_tests']}")
        print(f"   ❌ Failed: {tm['failed_tests']}")
        print(f"   ⏭️  Skipped: {tm['skipped_tests']}")
        print(f"   ⚠️  Errors: {tm['error_tests']}")
        print(f"   ⏱️  Duration: {tm['test_duration']:.2f}s")
        
        if tm['failed_tests'] > 0:
            pass_rate = (tm['passed_tests'] / tm['total_tests']) * 100
            print(f"   📊 Pass Rate: {pass_rate:.1f}%")
        print()
        
        # Quality Summary
        qm = report['quality_metrics']
        print("🔍 QUALITY SUMMARY:")
        print(f"   Syntax Errors: {len(qm['syntax_errors'])}")
        if qm['syntax_errors']:
            print("   Files with errors:", qm['syntax_errors'][:3])
        print()
        
        # Performance Summary
        pm = report['performance_metrics']
        print("📈 PERFORMANCE SUMMARY:")
        print(f"   Status: {pm['performance_status']}")
        print(f"   Performance Tests Passed: {pm['performance_tests_passed']}")
        print(f"   Performance Tests Failed: {pm['performance_tests_failed']}")
        print()
        
        # Recommendations
        print("💡 RECOMMENDATIONS:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"   {i}. {rec}")
        print()
        
        # Quality Gate Status
        if tm['failed_tests'] == 0 and len(qm['syntax_errors']) == 0:
            print("✅ QUALITY GATE: PASS - Ready for commit")
        else:
            print("❌ QUALITY GATE: FAIL - Fix issues before commit")
        
        print("=" * 60)

def main():
    """Main entry point for daily quality dashboard."""
    dashboard = DailyQualityDashboard()
    
    try:
        report = dashboard.generate_daily_report()
        
        # Exit with appropriate code for CI/CD
        if report['test_metrics']['failed_tests'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        print(f"❌ Dashboard generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
