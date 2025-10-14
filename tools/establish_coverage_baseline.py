#!/usr/bin/env python3
"""
Establish Coverage Baseline

Creates baseline coverage measurement and optional quality gate integration.
Tracks coverage over time and can enforce minimum thresholds.

USAGE:
    python tools/establish_coverage_baseline.py
    python tools/establish_coverage_baseline.py --set-threshold 15
    python tools/establish_coverage_baseline.py --add-to-gates
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import argparse


class CoverageBaseline:
    """Establishes and tracks coverage baseline."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.baseline_file = self.project_root / ".coverage_baseline.json"
        self.coverage_report = self.project_root / "coverage_report.txt"
        
    def measure_current_coverage(self) -> Optional[float]:
        """Measure current test coverage."""
        print("🧪 Running coverage measurement...")
        
        try:
            result = subprocess.run(
                ['python', 'tools/integrate_coverage_measurement.py'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode != 0:
                print("⚠️  Coverage measurement failed")
                return None
            
            # Extract coverage percentage from output
            output = result.stdout
            for line in output.split('\n'):
                if 'TOTAL' in line and '%' in line:
                    parts = line.split()
                    for part in parts:
                        if '%' in part:
                            return float(part.rstrip('%'))
            
            return None
            
        except Exception as e:
            print(f"❌ Error measuring coverage: {e}")
            return None
    
    def get_module_coverage(self) -> Dict[str, float]:
        """Extract per-module coverage from report."""
        if not self.coverage_report.exists():
            return {}
        
        module_coverage = {}
        
        with open(self.coverage_report, 'r') as f:
            lines = f.readlines()
        
        # Parse coverage report
        for line in lines:
            if line.startswith('src/') and '%' in line:
                parts = line.split()
                if len(parts) >= 4:
                    module = parts[0]
                    coverage_str = parts[-1].rstrip('%')
                    try:
                        coverage = float(coverage_str)
                        module_coverage[module] = coverage
                    except ValueError:
                        continue
        
        return module_coverage
    
    def save_baseline(self, total_coverage: float, module_coverage: Dict[str, float]) -> None:
        """Save baseline to file."""
        baseline_data = {
            "baseline_date": datetime.now().isoformat(),
            "total_coverage": total_coverage,
            "module_coverage": module_coverage,
            "measurements": [
                {
                    "date": datetime.now().isoformat(),
                    "total_coverage": total_coverage
                }
            ]
        }
        
        # If baseline exists, append measurement
        if self.baseline_file.exists():
            with open(self.baseline_file, 'r') as f:
                existing = json.load(f)
            
            existing["measurements"].append({
                "date": datetime.now().isoformat(),
                "total_coverage": total_coverage
            })
            
            # Update baseline if coverage improved
            if total_coverage > existing.get("total_coverage", 0):
                existing["total_coverage"] = total_coverage
                existing["baseline_date"] = datetime.now().isoformat()
                existing["module_coverage"] = module_coverage
            
            baseline_data = existing
        
        with open(self.baseline_file, 'w') as f:
            json.dump(baseline_data, f, indent=2)
        
        print(f"\n✅ Baseline saved: {self.baseline_file}")
    
    def generate_coverage_report(self, total_coverage: float, module_coverage: Dict[str, float]) -> str:
        """Generate coverage analysis report."""
        lines = [
            "# Coverage Baseline Report",
            "",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Overall Coverage",
            "",
            f"**Total Coverage**: {total_coverage:.1f}%",
            "",
        ]
        
        # Categorize modules by coverage
        excellent = {k: v for k, v in module_coverage.items() if v >= 80}
        good = {k: v for k, v in module_coverage.items() if 50 <= v < 80}
        fair = {k: v for k, v in module_coverage.items() if 20 <= v < 50}
        poor = {k: v for k, v in module_coverage.items() if 0 < v < 20}
        none = {k: v for k, v in module_coverage.items() if v == 0}
        
        lines.extend([
            "### Coverage Distribution",
            "",
            f"- **Excellent (≥80%)**: {len(excellent)} modules",
            f"- **Good (50-79%)**: {len(good)} modules",
            f"- **Fair (20-49%)**: {len(fair)} modules",
            f"- **Poor (1-19%)**: {len(poor)} modules",
            f"- **None (0%)**: {len(none)} modules",
            "",
        ])
        
        # Highlight well-tested modules
        if excellent:
            lines.extend([
                "## Well-Tested Modules (≥80%)",
                "",
            ])
            for module, cov in sorted(excellent.items(), key=lambda x: x[1], reverse=True)[:10]:
                lines.append(f"- {module}: {cov:.0f}%")
            lines.append("")
        
        # Highlight modules needing tests
        if none:
            lines.extend([
                "## Modules Without Tests (0%)",
                "",
                f"**Count**: {len(none)} modules",
                "",
                "**Examples** (first 10):",
                "",
            ])
            for module in sorted(none.keys())[:10]:
                lines.append(f"- {module}")
            
            if len(none) > 10:
                lines.append(f"- *... and {len(none) - 10} more*")
            
            lines.append("")
        
        # Recommendations
        lines.extend([
            "## Recommendations",
            "",
            "### Short Term (Next Sprint)",
            "1. Focus on core modules with 0% coverage",
            "2. Target: Bring total coverage from 11% to 20%",
            "3. Prioritize modules in protected core",
            "",
            "### Medium Term (Next Month)",
            "1. Achieve 40% total coverage",
            "2. All protected modules > 50% coverage",
            "3. Integration tests for GUI components",
            "",
            "### Long Term (Next Quarter)",
            "1. Target 70% total coverage",
            "2. All production modules > 80% coverage",
            "3. Full regression test suite",
            "",
            "## Next Steps",
            "",
            "1. Review modules with 0% coverage",
            "2. Write tests for high-priority modules first",
            "3. Re-run baseline measurement monthly",
            "4. Track progress in session state",
            "",
        ])
        
        return '\n'.join(lines)
    
    def add_to_quality_gates(self, threshold: float = 10.0) -> bool:
        """Add coverage check to quality gates (optional)."""
        quality_gate = self.project_root / "tools" / "quality_gate_system.py"
        
        if not quality_gate.exists():
            print("⚠️  Quality gate system not found")
            return False
        
        print(f"\n💡 Coverage gate can be added with threshold {threshold}%")
        print("   This would fail commits if coverage drops below threshold")
        print("   Not recommended yet - coverage too low (11%)")
        print("\n   Recommended: Wait until coverage reaches 25% before enforcing")
        
        return True
    
    def run(self, set_threshold: Optional[float] = None, add_to_gates: bool = False) -> bool:
        """Run baseline establishment."""
        print("=" * 60)
        print("COVERAGE BASELINE ESTABLISHMENT")
        print("=" * 60)
        
        # Measure coverage
        total_coverage = self.measure_current_coverage()
        
        if total_coverage is None:
            print("❌ Could not measure coverage")
            return False
        
        print(f"\n📊 Current Coverage: {total_coverage:.1f}%")
        
        # Get per-module coverage
        module_coverage = self.get_module_coverage()
        print(f"   Analyzed {len(module_coverage)} modules")
        
        # Save baseline
        self.save_baseline(total_coverage, module_coverage)
        
        # Generate report
        report = self.generate_coverage_report(total_coverage, module_coverage)
        report_file = self.project_root / "COVERAGE_BASELINE_REPORT.md"
        
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"✅ Report generated: {report_file}")
        
        # Optional: Add to quality gates
        if add_to_gates:
            self.add_to_quality_gates(threshold=set_threshold or total_coverage)
        
        print("\n" + "=" * 60)
        print("✅ Baseline established")
        print("=" * 60)
        
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Establish coverage baseline"
    )
    parser.add_argument(
        '--set-threshold',
        type=float,
        default=None,
        help='Set minimum coverage threshold'
    )
    parser.add_argument(
        '--add-to-gates',
        action='store_true',
        help='Add coverage check to quality gates'
    )
    
    args = parser.parse_args()
    
    baseline = CoverageBaseline()
    success = baseline.run(
        set_threshold=args.set_threshold,
        add_to_gates=args.add_to_gates
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
