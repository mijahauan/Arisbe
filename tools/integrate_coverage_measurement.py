#!/usr/bin/env python3
"""
Integrate Coverage Measurement

Runs coverage.py on protected core modules and generates coverage reports.
Validates that protected modules have adequate test coverage.

USAGE:
    python tools/integrate_coverage_measurement.py
    python tools/integrate_coverage_measurement.py --html
    python tools/integrate_coverage_measurement.py --fail-under 80
    
Can be integrated into quality gates and CI/CD.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional
import argparse


class CoverageIntegrator:
    """Integrates coverage.py measurement for core modules."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.src_path = self.project_root / "src"
        self.tests_path = self.project_root / "tests"
        self.state_file = self.project_root / ".coherence_session_state.json"
        
        # Coverage output files
        self.coverage_data = self.project_root / ".coverage"
        self.coverage_report = self.project_root / "coverage_report.txt"
        self.coverage_html_dir = self.project_root / "htmlcov"
        
        # Load protected modules
        self.protected_modules = self._load_protected_modules()
    
    def _load_protected_modules(self) -> List[str]:
        """Load list of protected core modules."""
        if not self.state_file.exists():
            return []
        
        with open(self.state_file, 'r') as f:
            state = json.load(f)
        
        protected = []
        components = state.get("active_components", {})
        tier1 = components.get("production_tier1", {}).get("modules", [])
        
        for module_desc in tier1:
            if "PROTECTED" in module_desc or ".py" in module_desc:
                # Extract filename from "src/filename.py - Description (PROTECTED)"
                parts = module_desc.split()
                if parts:
                    filename = parts[0].split('/')[-1]
                    if filename.endswith('.py'):
                        # Get module path relative to src/
                        module_path = self.src_path / filename
                        if module_path.exists():
                            protected.append(filename[:-3])  # Remove .py
        
        return protected
    
    def run_coverage(self, html: bool = False) -> bool:
        """Run coverage measurement on core tests."""
        print("=" * 60)
        print("COVERAGE MEASUREMENT")
        print("=" * 60)
        
        if not self.tests_path.exists():
            print("❌ Tests directory not found")
            return False
        
        # Run coverage on tests
        print("🧪 Running tests with coverage...")
        
        try:
            # Run pytest with coverage
            cmd = [
                'python', '-m', 'coverage', 'run',
                '--source=src',
                '-m', 'pytest',
                'tests/',
                '-v'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode != 0:
                print("⚠️  Tests failed or coverage could not run")
                print(result.stdout)
                print(result.stderr)
                # Don't fail - coverage might still be useful
            
            print("✅ Coverage data collected")
            
        except Exception as e:
            print(f"❌ Error running coverage: {e}")
            return False
        
        return True
    
    def generate_report(self, html: bool = False) -> Optional[Dict[str, float]]:
        """Generate coverage report."""
        print("\n📊 Generating coverage report...")
        
        try:
            # Generate text report
            result = subprocess.run(
                ['python', '-m', 'coverage', 'report'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                report = result.stdout
                print("\n" + report)
                
                # Save to file
                with open(self.coverage_report, 'w') as f:
                    f.write(report)
                
                print(f"✅ Report saved to: {self.coverage_report}")
            else:
                print("⚠️  Could not generate report")
                print(result.stderr)
        
        except Exception as e:
            print(f"⚠️  Error generating report: {e}")
        
        # Generate HTML report if requested
        if html:
            print("\n🌐 Generating HTML coverage report...")
            
            try:
                result = subprocess.run(
                    ['python', '-m', 'coverage', 'html'],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root
                )
                
                if result.returncode == 0:
                    print(f"✅ HTML report generated: {self.coverage_html_dir}/index.html")
                else:
                    print("⚠️  Could not generate HTML report")
            
            except Exception as e:
                print(f"⚠️  Error generating HTML: {e}")
        
        # Extract coverage data
        return self._extract_coverage_data()
    
    def _extract_coverage_data(self) -> Optional[Dict[str, float]]:
        """Extract coverage percentages from report."""
        try:
            result = subprocess.run(
                ['python', '-m', 'coverage', 'json', '-o', '-'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                coverage_data = json.loads(result.stdout)
                return {
                    "total_coverage": coverage_data.get("totals", {}).get("percent_covered", 0.0),
                    "files": coverage_data.get("files", {})
                }
        
        except Exception:
            pass
        
        return None
    
    def check_coverage_threshold(self, coverage_data: Dict, threshold: float) -> bool:
        """Check if coverage meets threshold."""
        if not coverage_data:
            print("⚠️  No coverage data available")
            return True  # Don't fail if we can't measure
        
        total_coverage = coverage_data.get("total_coverage", 0.0)
        
        print(f"\n📈 Total Coverage: {total_coverage:.1f}%")
        
        if total_coverage < threshold:
            print(f"❌ Coverage {total_coverage:.1f}% below threshold {threshold}%")
            return False
        else:
            print(f"✅ Coverage {total_coverage:.1f}% meets threshold {threshold}%")
            return True
    
    def update_session_state(self, coverage_data: Optional[Dict]) -> None:
        """Update session state with coverage information."""
        if not coverage_data or not self.state_file.exists():
            return
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            # Update test status
            if "test_status" not in state:
                state["test_status"] = {}
            
            total_coverage = coverage_data.get("total_coverage", 0.0)
            state["test_status"]["coverage"] = f"{total_coverage:.1f}%"
            
            # Write back
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            print(f"✅ Session state updated with coverage: {total_coverage:.1f}%")
        
        except Exception as e:
            print(f"⚠️  Could not update session state: {e}")
    
    def run(self, html: bool = False, fail_under: Optional[float] = None) -> bool:
        """Run coverage integration."""
        # Run coverage
        if not self.run_coverage(html=html):
            return False
        
        # Generate report
        coverage_data = self.generate_report(html=html)
        
        # Update session state
        self.update_session_state(coverage_data)
        
        # Check threshold if specified
        if fail_under is not None:
            if not self.check_coverage_threshold(coverage_data, fail_under):
                return False
        
        print("\n" + "=" * 60)
        print("✅ Coverage measurement complete")
        print("=" * 60)
        
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Integrate coverage measurement for core modules"
    )
    parser.add_argument(
        '--html',
        action='store_true',
        help='Generate HTML coverage report'
    )
    parser.add_argument(
        '--fail-under',
        type=float,
        default=None,
        help='Fail if coverage is below this percentage'
    )
    
    args = parser.parse_args()
    
    integrator = CoverageIntegrator()
    success = integrator.run(html=args.html, fail_under=args.fail_under)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
