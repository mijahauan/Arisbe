#!/usr/bin/env python3
"""
Project Initializer - Sets up coherence framework in any codebase

This module provides the core functionality to initialize the AI Coherence Framework
in any new or existing project, creating all necessary tools and configurations.
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import yaml
import json


class ProjectInitializer:
    """Initialize AI Coherence Framework in any project."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.coherence_dir = self.project_root / ".coherence"
        self.tools_dir = self.project_root / "tools"
        
    def initialize_project(self, project_name: Optional[str] = None, 
                         language: str = "python") -> bool:
        """Initialize coherence framework in the project."""
        print(f"🚀 Initializing AI Coherence Framework in {self.project_root}")
        
        try:
            # Create directory structure
            self._create_directory_structure()
            
            # Create configuration files
            self._create_configuration(project_name, language)
            
            # Install core tools
            self._install_core_tools()
            
            # Set up git hooks
            self._setup_git_hooks()
            
            # Create IDE integration
            self._setup_ide_integration()
            
            # Create documentation templates
            self._create_documentation_templates()
            
            # Initialize quality baselines
            self._initialize_quality_baselines()
            
            print("✅ AI Coherence Framework initialized successfully!")
            print("\nNext steps:")
            print("1. Review configuration in .coherence/config.yaml")
            print("2. Run: coherence-check --quality (establish baseline)")
            print("3. Start development: coherence-session start")
            
            return True
            
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return False
    
    def _create_directory_structure(self):
        """Create necessary directory structure."""
        directories = [
            self.coherence_dir,
            self.coherence_dir / "templates",
            self.coherence_dir / "rules",
            self.tools_dir,
            self.project_root / ".vscode",
            self.project_root / "docs",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created directory: {directory.relative_to(self.project_root)}")
    
    def _create_configuration(self, project_name: Optional[str], language: str):
        """Create configuration files."""
        if not project_name:
            project_name = self.project_root.name
        
        # Main configuration
        config = {
            "project": {
                "name": project_name,
                "language": language,
                "source_dirs": self._detect_source_dirs(language),
                "test_dirs": self._detect_test_dirs(language),
                "exclude_dirs": [".git", "__pycache__", "node_modules", ".venv", "venv"],
            },
            "quality": {
                "coverage_threshold": 80,
                "complexity_threshold": 10,
                "dead_code_threshold": 5,
                "style_threshold": 90,
            },
            "git": {
                "auto_commit_interval": 900,  # 15 minutes
                "branch_prefix": "feature/",
                "checkpoint_prefix": "checkpoint/",
            },
            "context": {
                "keywords": [],
                "custom_rules": [],
            }
        }
        
        config_file = self.coherence_dir / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        
        print(f"⚙️  Created configuration: {config_file.relative_to(self.project_root)}")
        
        # Integration rules template
        integration_rules = {
            "rules": [
                {
                    "name": "example_pattern",
                    "description": "Example integration rule",
                    "trigger_keywords": ["example", "pattern"],
                    "existing_solution": "src/examples/",
                    "severity": "warning"
                }
            ]
        }
        
        rules_file = self.coherence_dir / "integration_rules.yaml"
        with open(rules_file, 'w') as f:
            yaml.dump(integration_rules, f, default_flow_style=False, indent=2)
        
        print(f"📋 Created integration rules: {rules_file.relative_to(self.project_root)}")
    
    def _detect_source_dirs(self, language: str) -> List[str]:
        """Detect likely source directories based on language."""
        common_patterns = {
            "python": ["src", "lib", self.project_root.name],
            "javascript": ["src", "lib", "app"],
            "typescript": ["src", "lib", "app"],
            "java": ["src/main/java", "src"],
            "csharp": ["src", "lib"],
            "go": [".", "pkg", "cmd"],
            "rust": ["src", "lib"],
        }
        
        patterns = common_patterns.get(language, ["src", "lib"])
        
        # Check which directories actually exist
        existing_dirs = []
        for pattern in patterns:
            dir_path = self.project_root / pattern
            if dir_path.exists() and dir_path.is_dir():
                existing_dirs.append(pattern)
        
        return existing_dirs if existing_dirs else ["src"]
    
    def _detect_test_dirs(self, language: str) -> List[str]:
        """Detect likely test directories."""
        common_patterns = ["tests", "test", "spec", "__tests__"]
        
        existing_dirs = []
        for pattern in common_patterns:
            dir_path = self.project_root / pattern
            if dir_path.exists() and dir_path.is_dir():
                existing_dirs.append(pattern)
        
        return existing_dirs if existing_dirs else ["tests"]
    
    def _install_core_tools(self):
        """Install core coherence tools."""
        # Copy tools from framework package
        framework_tools = Path(__file__).parent.parent / "tools"
        
        tools_to_copy = [
            "quality_gate_system.py",
            "context_awareness_system.py", 
            "smart_commit.py",
            "function_indexer.py",
            "coherence_analyzer.py",
            "living_documentation_generator.py",
            "start_dev_session.sh",
            "end_dev_session.sh",
        ]
        
        for tool in tools_to_copy:
            source = framework_tools / tool
            dest = self.tools_dir / tool
            
            if source.exists():
                shutil.copy2(source, dest)
                if tool.endswith('.sh'):
                    os.chmod(dest, 0o755)
                print(f"🔧 Installed tool: {tool}")
            else:
                # Create template if source doesn't exist
                self._create_tool_template(dest, tool)
    
    def _create_tool_template(self, dest_path: Path, tool_name: str):
        """Create a template tool file."""
        templates = {
            "quality_gate_system.py": '''#!/usr/bin/env python3
"""Quality Gate System - Automated quality monitoring."""

from coherence_framework import QualityGateSystem

def main():
    system = QualityGateSystem()
    metrics = system.run_all_checks()
    print(f"Quality Score: {metrics.overall_score()}/100")

if __name__ == "__main__":
    main()
''',
            "context_awareness_system.py": '''#!/usr/bin/env python3
"""Context Awareness System - Prevent reinventing solutions."""

from coherence_framework import ContextAwarenessSystem

def main():
    system = ContextAwarenessSystem()
    # Implementation will be provided by framework
    pass

if __name__ == "__main__":
    main()
''',
        }
        
        template = templates.get(tool_name, f'# {tool_name} - Generated by AI Coherence Framework\n')
        
        with open(dest_path, 'w') as f:
            f.write(template)
        
        print(f"📝 Created template: {tool_name}")
    
    def _setup_git_hooks(self):
        """Set up git hooks for quality gates."""
        hooks_dir = self.project_root / ".git" / "hooks"
        
        if not hooks_dir.exists():
            print("⚠️  No .git directory found - skipping git hooks setup")
            return
        
        # Pre-commit hook
        pre_commit_hook = '''#!/bin/bash
# AI Coherence Framework Pre-commit Hook

echo "🔍 Running AI Coherence Quality Gates..."

# Check if this is a WIP commit
commit_msg_file=".git/COMMIT_EDITMSG"
if [ -f "$commit_msg_file" ]; then
    commit_msg=$(cat "$commit_msg_file" 2>/dev/null || echo "")
    if [[ "$commit_msg" == *"WIP"* ]] || [[ "$commit_msg" == *"🚧"* ]]; then
        echo "🚧 WIP commit detected - running minimal checks"
        python tools/quality_gate_system.py --check --threshold 50
        exit $?
    fi
fi

# Full quality check for regular commits
python tools/quality_gate_system.py --check --threshold 80
if [ $? -ne 0 ]; then
    echo "❌ Quality gate failed. Use 'WIP:' prefix for work-in-progress commits."
    exit 1
fi

echo "✅ Quality gates passed!"
exit 0
'''
        
        hook_path = hooks_dir / "pre-commit"
        with open(hook_path, 'w') as f:
            f.write(pre_commit_hook)
        
        os.chmod(hook_path, 0o755)
        print(f"🪝 Installed git pre-commit hook")
    
    def _setup_ide_integration(self):
        """Set up IDE integration files."""
        # VS Code tasks
        vscode_tasks = {
            "version": "2.0.0",
            "tasks": [
                {
                    "label": "Coherence: Context Check",
                    "type": "shell",
                    "command": "python",
                    "args": ["tools/context_awareness_system.py", "--check", "${input:taskDescription}"],
                    "group": "build",
                    "presentation": {"echo": True, "reveal": "always"}
                },
                {
                    "label": "Coherence: Quality Check", 
                    "type": "shell",
                    "command": "python",
                    "args": ["tools/quality_gate_system.py", "--check"],
                    "group": "test"
                },
                {
                    "label": "Coherence: Smart Commit",
                    "type": "shell", 
                    "command": "python",
                    "args": ["tools/smart_commit.py"],
                    "group": "build"
                }
            ],
            "inputs": [
                {
                    "id": "taskDescription",
                    "description": "Describe the task you're working on",
                    "default": "",
                    "type": "promptString"
                }
            ]
        }
        
        tasks_file = self.project_root / ".vscode" / "tasks.json"
        with open(tasks_file, 'w') as f:
            json.dump(vscode_tasks, f, indent=2)
        
        print(f"🔧 Created VS Code integration: {tasks_file.relative_to(self.project_root)}")
    
    def _create_documentation_templates(self):
        """Create documentation templates."""
        templates = {
            "CONTEXT_AWARENESS_REMINDER.md": '''# AI Coherence Framework - Context Awareness

## 🚨 BEFORE CODING ANYTHING - CHECK EXISTING SOLUTIONS

### Quick Commands:
- `coherence-check "task description"` - Check for existing solutions
- `python tools/quality_gate_system.py --check` - Quality status
- `python tools/function_indexer.py "keywords"` - Search functions

### Workflow:
1. Check context: `coherence-check "your task"`
2. Search existing: `python tools/function_indexer.py "keywords"`
3. Code with existing patterns
4. Commit: `coherence-commit --auto`

## 🎯 Goal: INTEGRATE and REUSE, not CREATE and DUPLICATE!
''',
            "ARCHITECTURE_MAP.md": '''# Project Architecture Map

*This file is auto-generated by the AI Coherence Framework*

## System Overview
- **Core Components**: [Auto-detected from code]
- **Integration Points**: [Auto-detected from analysis]
- **Data Flow**: [Auto-generated from dependencies]

## Quality Metrics
- **Overall Score**: [Auto-updated]
- **Test Coverage**: [Auto-updated]
- **Dead Code**: [Auto-updated]

*Last updated: [Auto-timestamp]*
''',
        }
        
        for filename, content in templates.items():
            file_path = self.project_root / filename
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"📚 Created documentation: {filename}")
    
    def _initialize_quality_baselines(self):
        """Initialize quality measurement baselines."""
        # Create initial quality check
        try:
            result = subprocess.run([
                "python", "tools/quality_gate_system.py", "--check"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            print("📊 Initial quality baseline established")
            
        except Exception as e:
            print(f"⚠️  Could not establish quality baseline: {e}")
    
    def detect_existing_framework(self) -> bool:
        """Check if framework is already installed."""
        return (self.coherence_dir / "config.yaml").exists()
    
    def upgrade_framework(self) -> bool:
        """Upgrade existing framework installation."""
        if not self.detect_existing_framework():
            return False
        
        print("🔄 Upgrading AI Coherence Framework...")
        
        # Backup existing configuration
        backup_dir = self.coherence_dir / "backup"
        backup_dir.mkdir(exist_ok=True)
        
        config_file = self.coherence_dir / "config.yaml"
        if config_file.exists():
            shutil.copy2(config_file, backup_dir / f"config.yaml.backup")
        
        # Update tools
        self._install_core_tools()
        
        print("✅ Framework upgraded successfully!")
        return True


def main():
    """CLI entry point for project initialization."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize AI Coherence Framework")
    parser.add_argument("--name", help="Project name")
    parser.add_argument("--language", default="python", help="Primary language")
    parser.add_argument("--upgrade", action="store_true", help="Upgrade existing installation")
    
    args = parser.parse_args()
    
    initializer = ProjectInitializer()
    
    if args.upgrade:
        success = initializer.upgrade_framework()
    else:
        if initializer.detect_existing_framework():
            print("⚠️  AI Coherence Framework already installed.")
            print("Use --upgrade to update existing installation.")
            return
        
        success = initializer.initialize_project(args.name, args.language)
    
    if success:
        print("\n🎉 Ready to maintain coherence in your codebase!")
    else:
        print("\n❌ Setup failed. Please check the errors above.")


if __name__ == "__main__":
    main()
