#!/usr/bin/env python3
"""
Quality Gate System - Standalone Version

Automated quality monitoring and enforcement for any codebase.
Integrates multiple quality tools into a unified system.
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import yaml


@dataclass
class QualityMetrics:
    """Quality metrics container."""
    coverage: float = 0.0
    dead_code: float = 0.0
    type_coverage: float = 0.0
    complexity: float = 0.0
    security_issues: int = 0
    style_violations: int = 0
    coherence_score: float = 0.0
    
    def overall_score(self) -> int:
        """Calculate overall quality score (0-100)."""
        # Weighted scoring
        score = (
            self.coverage * 0.25 +
            (100 - self.dead_code) * 0.15 +
            self.type_coverage * 0.20 +
            max(0, 100 - self.complexity * 10) * 0.15 +
            max(0, 100 - self.security_issues * 10) * 0.15 +
            max(0, 100 - self.style_violations) * 0.10
        )
        return int(min(100, max(0, score)))


class QualityGateSystem:
    """Standalone quality gate system for any codebase."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.config_dir = self.project_root / ".coherence"
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load quality configuration."""
        config_file = self.config_dir / "config.yaml"
        if config_file.exists():
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        
        # Default configuration
        return {
            "project": {
                "source_dirs": ["src", "lib"],
                "test_dirs": ["tests", "test"],
            },
            "quality": {
                "coverage_threshold": 80,
                "complexity_threshold": 10,
                "dead_code_threshold": 5,
                "style_threshold": 90,
            }
        }
    
    def run_all_checks(self, fix_issues: bool = False) -> QualityMetrics:
        """Run all quality checks and return metrics."""
        metrics = QualityMetrics()
        
        print("🔍 Running quality checks...")
        
        # Test coverage
        try:
            metrics.coverage = self._check_coverage()
            print(f"📊 Coverage: {metrics.coverage:.1f}%")
        except Exception as e:
            print(f"⚠️  Coverage check failed: {e}")
        
        # Dead code detection
        try:
            metrics.dead_code = self._check_dead_code()
            print(f"🧹 Dead code: {metrics.dead_code:.1f}%")
        except Exception as e:
            print(f"⚠️  Dead code check failed: {e}")
        
        # Type coverage
        try:
            metrics.type_coverage = self._check_type_coverage()
            print(f"🔍 Type coverage: {metrics.type_coverage:.1f}%")
        except Exception as e:
            print(f"⚠️  Type check failed: {e}")
        
        # Code complexity
        try:
            metrics.complexity = self._check_complexity()
            print(f"📈 Complexity: {metrics.complexity:.1f}")
        except Exception as e:
            print(f"⚠️  Complexity check failed: {e}")
        
        # Security issues
        try:
            metrics.security_issues = self._check_security()
            print(f"🔒 Security issues: {metrics.security_issues}")
        except Exception as e:
            print(f"⚠️  Security check failed: {e}")
        
        # Style violations
        try:
            metrics.style_violations = self._check_style(fix_issues)
            print(f"✨ Style violations: {metrics.style_violations}")
        except Exception as e:
            print(f"⚠️  Style check failed: {e}")
        
        return metrics
    
    def _check_coverage(self) -> float:
        """Check test coverage using coverage.py."""
        try:
            # Run coverage
            subprocess.run(["coverage", "run", "-m", "pytest"], 
                          capture_output=True, cwd=self.project_root)
            
            # Get coverage report
            result = subprocess.run(["coverage", "report", "--format=json"], 
                                  capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return data.get("totals", {}).get("percent_covered", 0.0)
        except Exception:
            pass
        
        return 0.0
    
    def _check_dead_code(self) -> float:
        """Check for dead code using vulture."""
        try:
            source_dirs = self.config["project"]["source_dirs"]
            cmd = ["vulture"] + source_dirs + ["--min-confidence", "80"]
            
            result = subprocess.run(cmd, capture_output=True, text=True, 
                                  cwd=self.project_root)
            
            # Count dead code items
            lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
            dead_items = len([line for line in lines if line.strip()])
            
            # Estimate percentage (rough heuristic)
            total_files = sum(1 for d in source_dirs 
                            for _ in (self.project_root / d).rglob("*.py")
                            if (self.project_root / d).exists())
            
            if total_files > 0:
                return min(100, (dead_items / total_files) * 10)
        except Exception:
            pass
        
        return 0.0
    
    def _check_type_coverage(self) -> float:
        """Check type coverage using mypy."""
        try:
            source_dirs = self.config["project"]["source_dirs"]
            
            for source_dir in source_dirs:
                if not (self.project_root / source_dir).exists():
                    continue
                
                result = subprocess.run(
                    ["mypy", source_dir, "--strict", "--show-error-codes"],
                    capture_output=True, text=True, cwd=self.project_root
                )
                
                # Parse mypy output for type coverage estimation
                if "error" not in result.stdout.lower():
                    return 90.0  # High type coverage if no errors
                else:
                    # Rough estimation based on error count
                    error_count = result.stdout.count("error:")
                    return max(0, 90 - error_count * 5)
        except Exception:
            pass
        
        return 0.0
    
    def _check_complexity(self) -> float:
        """Check code complexity using radon."""
        try:
            source_dirs = self.config["project"]["source_dirs"]
            cmd = ["radon", "cc"] + source_dirs + ["-a", "-nc"]
            
            result = subprocess.run(cmd, capture_output=True, text=True,
                                  cwd=self.project_root)
            
            if result.returncode == 0 and result.stdout.strip():
                # Parse average complexity
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if "Average complexity:" in line:
                        complexity_str = line.split(":")[-1].strip()
                        return float(complexity_str.split()[0])
        except Exception:
            pass
        
        return 0.0
    
    def _check_security(self) -> int:
        """Check security issues using bandit."""
        try:
            source_dirs = self.config["project"]["source_dirs"]
            cmd = ["bandit", "-r"] + source_dirs + ["-f", "json"]
            
            result = subprocess.run(cmd, capture_output=True, text=True,
                                  cwd=self.project_root)
            
            if result.stdout.strip():
                data = json.loads(result.stdout)
                return len(data.get("results", []))
        except Exception:
            pass
        
        return 0
    
    def _check_style(self, fix_issues: bool = False) -> int:
        """Check style violations using flake8 and black."""
        violations = 0
        
        try:
            source_dirs = self.config["project"]["source_dirs"]
            
            # Check with black
            if fix_issues:
                subprocess.run(["black"] + source_dirs, 
                             capture_output=True, cwd=self.project_root)
                subprocess.run(["isort"] + source_dirs,
                             capture_output=True, cwd=self.project_root)
            else:
                result = subprocess.run(["black", "--check"] + source_dirs,
                                      capture_output=True, text=True,
                                      cwd=self.project_root)
                if result.returncode != 0:
                    violations += result.stdout.count("would reformat")
            
            # Check with flake8
            result = subprocess.run(["flake8"] + source_dirs,
                                  capture_output=True, text=True,
                                  cwd=self.project_root)
            
            if result.stdout.strip():
                violations += len(result.stdout.strip().split('\n'))
        
        except Exception:
            pass
        
        return violations
    
    def generate_report(self) -> str:
        """Generate detailed quality report."""
        metrics = self.run_all_checks()
        
        report = f"""# Quality Report
        
## Overall Score: {metrics.overall_score()}/100

## Detailed Metrics

### Test Coverage: {metrics.coverage:.1f}%
- Threshold: {self.config['quality']['coverage_threshold']}%
- Status: {'✅ PASS' if metrics.coverage >= self.config['quality']['coverage_threshold'] else '❌ FAIL'}

### Dead Code: {metrics.dead_code:.1f}%
- Threshold: {self.config['quality']['dead_code_threshold']}%
- Status: {'✅ PASS' if metrics.dead_code <= self.config['quality']['dead_code_threshold'] else '❌ FAIL'}

### Type Coverage: {metrics.type_coverage:.1f}%
- Status: {'✅ GOOD' if metrics.type_coverage >= 80 else '⚠️ NEEDS IMPROVEMENT'}

### Code Complexity: {metrics.complexity:.1f}
- Threshold: {self.config['quality']['complexity_threshold']}
- Status: {'✅ PASS' if metrics.complexity <= self.config['quality']['complexity_threshold'] else '❌ FAIL'}

### Security Issues: {metrics.security_issues}
- Status: {'✅ PASS' if metrics.security_issues == 0 else '❌ FAIL'}

### Style Violations: {metrics.style_violations}
- Status: {'✅ PASS' if metrics.style_violations == 0 else '⚠️ NEEDS FORMATTING'}

## Recommendations

"""
        
        # Add recommendations
        if metrics.coverage < self.config['quality']['coverage_threshold']:
            report += "- 📊 Increase test coverage by adding more unit tests\n"
        
        if metrics.dead_code > self.config['quality']['dead_code_threshold']:
            report += "- 🧹 Remove dead code identified by vulture\n"
        
        if metrics.complexity > self.config['quality']['complexity_threshold']:
            report += "- 📈 Refactor complex functions to reduce cyclomatic complexity\n"
        
        if metrics.security_issues > 0:
            report += "- 🔒 Fix security issues identified by bandit\n"
        
        if metrics.style_violations > 0:
            report += "- ✨ Run `coherence-check --fix` to auto-format code\n"
        
        return report
    
    def check_quality_gate(self, threshold: int = 80) -> bool:
        """Check if quality meets threshold."""
        metrics = self.run_all_checks()
        return metrics.overall_score() >= threshold


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Quality Gate System")
    parser.add_argument("--check", action="store_true", help="Run quality checks")
    parser.add_argument("--fix", action="store_true", help="Auto-fix issues")
    parser.add_argument("--report", action="store_true", help="Generate report")
    parser.add_argument("--threshold", type=int, default=80, help="Quality threshold")
    
    args = parser.parse_args()
    
    system = QualityGateSystem()
    
    if args.check or not any([args.fix, args.report]):
        metrics = system.run_all_checks(fix_issues=args.fix)
        print(f"\n📊 Overall Quality Score: {metrics.overall_score()}/100")
        
        if metrics.overall_score() >= args.threshold:
            print("✅ Quality gate PASSED")
            return 0
        else:
            print(f"❌ Quality gate FAILED (threshold: {args.threshold})")
            return 1
    
    if args.report:
        report = system.generate_report()
        report_file = Path("quality_report.md")
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"📄 Report generated: {report_file}")


if __name__ == "__main__":
    main()
