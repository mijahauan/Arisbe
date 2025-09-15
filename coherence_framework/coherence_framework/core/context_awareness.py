#!/usr/bin/env python3
"""
Context Awareness System - Standalone Version

Prevents reinventing existing solutions by maintaining persistent context
about what has already been implemented in the codebase.
"""

import os
import re
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class ContextResult:
    """Result of context awareness check."""
    existing_solutions: List[str]
    message: str
    severity: str  # 'info', 'warning', 'error'
    recommendations: List[str]


class ContextAwarenessSystem:
    """Standalone context awareness system for any codebase."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.config_dir = self.project_root / ".coherence"
        self.config = self._load_config()
        self.integration_rules = self._load_integration_rules()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load project configuration."""
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
            "context": {
                "keywords": [],
                "custom_rules": [],
            }
        }
    
    def _load_integration_rules(self) -> Dict[str, Any]:
        """Load integration rules."""
        rules_file = self.config_dir / "integration_rules.yaml"
        if rules_file.exists():
            with open(rules_file, 'r') as f:
                return yaml.safe_load(f)
        
        return {"rules": []}
    
    def check_context(self, task_description: str) -> ContextResult:
        """Check if task matches existing solutions."""
        task_lower = task_description.lower()
        
        # Check integration rules
        for rule in self.integration_rules.get("rules", []):
            keywords = rule.get("trigger_keywords", [])
            
            if any(keyword.lower() in task_lower for keyword in keywords):
                return ContextResult(
                    existing_solutions=[rule.get("existing_solution", "")],
                    message=f"🚨 {rule.get('description', 'Existing solution found')}",
                    severity=rule.get("severity", "warning"),
                    recommendations=[f"Check {rule.get('existing_solution', '')}"]
                )
        
        # Check for common patterns
        patterns = self._get_common_patterns()
        for pattern, solution in patterns.items():
            if pattern.lower() in task_lower:
                return ContextResult(
                    existing_solutions=[solution],
                    message=f"🚨 Common pattern detected: {pattern}",
                    severity="warning",
                    recommendations=[f"Review existing implementation: {solution}"]
                )
        
        # No existing solutions found
        return ContextResult(
            existing_solutions=[],
            message="✅ No existing solutions found - proceed with implementation",
            severity="info",
            recommendations=["Document your solution for future reference"]
        )
    
    def _get_common_patterns(self) -> Dict[str, str]:
        """Get common programming patterns to check for."""
        return {
            "database": "Check for existing Repository pattern or ORM usage",
            "authentication": "Look for existing auth middleware or user management",
            "validation": "Check for existing validation decorators or schemas",
            "logging": "Review existing logging configuration and patterns",
            "configuration": "Check for existing config management system",
            "caching": "Look for existing cache implementations",
            "api": "Review existing API patterns and base classes",
            "testing": "Check existing test utilities and fixtures",
            "serialization": "Look for existing serializer patterns",
            "error handling": "Review existing exception classes and handlers",
        }
    
    def show_pre_development_checklist(self):
        """Display pre-development checklist."""
        checklist_file = self.project_root / ".arisbe_context_check"
        
        if checklist_file.exists():
            print("📋 Pre-Development Checklist:")
            with open(checklist_file, 'r') as f:
                print(f.read())
        else:
            self._create_default_checklist()
            print("📋 Created default pre-development checklist")
    
    def _create_default_checklist(self):
        """Create default context checklist."""
        checklist_content = """# Pre-Development Context Checklist

## Before starting ANY new implementation:

### 1. Search Existing Solutions
- [ ] Run: `coherence-check "your task description"`
- [ ] Search codebase for similar functionality
- [ ] Check existing interfaces and base classes

### 2. Review Architecture
- [ ] Read ARCHITECTURE_MAP.md for system overview
- [ ] Check integration patterns in existing code
- [ ] Identify reusable components

### 3. Quality Baseline
- [ ] Run: `coherence-check --quality`
- [ ] Ensure current code quality is acceptable
- [ ] Fix any critical issues before adding new code

### 4. Git Safety
- [ ] Create feature branch: `git checkout -b feature/task-name`
- [ ] Set up auto-commit: `coherence-commit --auto`
- [ ] Create checkpoint before major changes

## Goal: INTEGRATE and REUSE, not CREATE and DUPLICATE!
"""
        
        checklist_file = self.project_root / ".arisbe_context_check"
        with open(checklist_file, 'w') as f:
            f.write(checklist_content)
    
    def add_custom_rule(self, name: str, description: str, 
                       keywords: List[str], solution_path: str):
        """Add custom integration rule."""
        new_rule = {
            "name": name,
            "description": description,
            "trigger_keywords": keywords,
            "existing_solution": solution_path,
            "severity": "warning"
        }
        
        self.integration_rules["rules"].append(new_rule)
        
        # Save updated rules
        rules_file = self.config_dir / "integration_rules.yaml"
        with open(rules_file, 'w') as f:
            yaml.dump(self.integration_rules, f, default_flow_style=False, indent=2)
        
        print(f"✅ Added custom rule: {name}")
    
    def scan_codebase_for_patterns(self) -> Dict[str, List[str]]:
        """Scan codebase to automatically detect patterns."""
        patterns = {}
        
        source_dirs = self.config["project"]["source_dirs"]
        
        for source_dir in source_dirs:
            dir_path = self.project_root / source_dir
            if not dir_path.exists():
                continue
                
            for file_path in dir_path.rglob("*.py"):
                self._analyze_file_patterns(file_path, patterns)
        
        return patterns
    
    def _analyze_file_patterns(self, file_path: Path, patterns: Dict[str, List[str]]):
        """Analyze a single file for patterns."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Look for common patterns
            pattern_checks = {
                "database": [r"class.*Repository", r"def.*query", r"\.execute\("],
                "validation": [r"def.*validate", r"@validator", r"ValidationError"],
                "authentication": [r"def.*login", r"@login_required", r"authenticate"],
                "api": [r"@app\.route", r"@router\.", r"class.*API"],
                "testing": [r"def test_", r"@pytest\.", r"unittest\.TestCase"],
            }
            
            for pattern_name, regexes in pattern_checks.items():
                for regex in regexes:
                    if re.search(regex, content, re.IGNORECASE):
                        if pattern_name not in patterns:
                            patterns[pattern_name] = []
                        patterns[pattern_name].append(str(file_path.relative_to(self.project_root)))
                        break
        
        except Exception:
            # Skip files that can't be read
            pass
    
    def generate_context_report(self) -> str:
        """Generate comprehensive context awareness report."""
        patterns = self.scan_codebase_for_patterns()
        
        report = "# Context Awareness Report\n\n"
        report += "## Detected Patterns\n\n"
        
        for pattern_name, files in patterns.items():
            report += f"### {pattern_name.title()}\n"
            for file_path in files[:5]:  # Limit to 5 examples
                report += f"- `{file_path}`\n"
            if len(files) > 5:
                report += f"- ... and {len(files) - 5} more files\n"
            report += "\n"
        
        report += "## Integration Rules\n\n"
        for rule in self.integration_rules.get("rules", []):
            report += f"### {rule['name']}\n"
            report += f"**Description:** {rule['description']}\n"
            report += f"**Keywords:** {', '.join(rule['trigger_keywords'])}\n"
            report += f"**Solution:** `{rule['existing_solution']}`\n\n"
        
        return report


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Context Awareness System")
    parser.add_argument("--check", type=str, help="Check task description")
    parser.add_argument("--checklist", action="store_true", help="Show checklist")
    parser.add_argument("--scan", action="store_true", help="Scan for patterns")
    parser.add_argument("--report", action="store_true", help="Generate report")
    
    args = parser.parse_args()
    
    system = ContextAwarenessSystem()
    
    if args.check:
        result = system.check_context(args.check)
        print(result.message)
        if result.existing_solutions:
            for solution in result.existing_solutions:
                print(f"  • {solution}")
    
    elif args.checklist:
        system.show_pre_development_checklist()
    
    elif args.scan:
        patterns = system.scan_codebase_for_patterns()
        print("🔍 Detected Patterns:")
        for pattern, files in patterns.items():
            print(f"  {pattern}: {len(files)} files")
    
    elif args.report:
        report = system.generate_context_report()
        report_file = Path("context_awareness_report.md")
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"📄 Report generated: {report_file}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
