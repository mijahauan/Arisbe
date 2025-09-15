#!/usr/bin/env python3
"""
Context Memory System - Layer 4 Integration

Integrates all layers and creates a memory system to remember to use these tools.
This is the meta-layer that ensures the layered strategy is actually utilized.
"""

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass
class ContextPrompt:
    """A prompt to check existing solutions before implementing new ones."""

    trigger_keywords: List[str]
    check_commands: List[str]
    message: str
    priority: str  # 'high', 'medium', 'low'


class ContextMemorySystem:
    """System that reminds to use the layered strategy tools."""

    def __init__(self):
        self.prompts: List[ContextPrompt] = []
        self._initialize_prompts()

    def _initialize_prompts(self):
        """Initialize context prompts for common scenarios."""

        self.prompts = [
            ContextPrompt(
                trigger_keywords=["polarity", "positive", "negative", "area polarity"],
                check_commands=[
                    'python tools/function_lookup.py "polarity"',
                    'grep -n "get_polarity\\|calculate.*polarity" src/*.py',
                ],
                message="🔍 BEFORE implementing polarity calculation: Check existing HierarchicalIndex.get_polarity() O(1) solution",
                priority="high",
            ),
            ContextPrompt(
                trigger_keywords=[
                    "hierarchy",
                    "nesting",
                    "containment",
                    "depth",
                    "level",
                ],
                check_commands=[
                    'python tools/function_lookup.py "hierarchy"',
                    "python tools/architectural_mapper.py | grep -i hierarchy",
                ],
                message="🔍 BEFORE implementing hierarchy/nesting: Check existing HierarchicalIndex and spatial indexing solutions",
                priority="high",
            ),
            ContextPrompt(
                trigger_keywords=["transformation", "rule", "apply", "transform"],
                check_commands=[
                    'python tools/pattern_catalog.py | grep -A5 "Transformation"',
                    'python tools/function_lookup.py "transformation"',
                ],
                message="🔍 BEFORE implementing transformation: Check formal_transformation_rules.py and transformation wizard patterns",
                priority="high",
            ),
            ContextPrompt(
                trigger_keywords=["spatial", "bounds", "containment", "region", "area"],
                check_commands=[
                    'python tools/function_lookup.py "spatial"',
                    "ls src/legacy/*spatial* src/legacy/*rtree*",
                ],
                message="🔍 BEFORE implementing spatial operations: Check R-tree indexing in legacy/ directory",
                priority="medium",
            ),
            ContextPrompt(
                trigger_keywords=["gui", "dialog", "wizard", "interface", "user"],
                check_commands=[
                    'python tools/pattern_catalog.py | grep -A5 "User Interface"',
                    'find src/gui -name "*.py" | head -5',
                ],
                message="🔍 BEFORE implementing GUI: Check existing PySide6 patterns and transformation wizard system",
                priority="medium",
            ),
            ContextPrompt(
                trigger_keywords=["performance", "efficient", "fast", "o(1)", "lookup"],
                check_commands=[
                    "python tools/function_lookup.py --o1",
                    'python tools/pattern_catalog.py | grep -A3 "Performance"',
                ],
                message="🔍 BEFORE optimizing: Check existing O(1) solutions and performance patterns",
                priority="high",
            ),
            ContextPrompt(
                trigger_keywords=["index", "search", "find", "lookup", "query"],
                check_commands=[
                    'python tools/semantic_code_analyzer.py | grep -A5 "cluster"',
                    'python tools/function_lookup.py "index"',
                ],
                message="🔍 BEFORE implementing indexing: Check existing indexing systems (HierarchicalIndex, R-tree, corpus index)",
                priority="medium",
            ),
        ]

    def check_context_for_problem(
        self, problem_description: str
    ) -> List[ContextPrompt]:
        """Check if problem matches any context prompts."""
        problem_lower = problem_description.lower()
        matching_prompts = []

        for prompt in self.prompts:
            if any(keyword in problem_lower for keyword in prompt.trigger_keywords):
                matching_prompts.append(prompt)

        return matching_prompts

    def generate_context_check_script(self, output_path: str):
        """Generate a script that can be run before implementing new features."""
        script_lines = [
            "#!/bin/bash",
            "# Context Check Script - Run before implementing new features",
            "# This script helps avoid reinventing existing solutions",
            "",
            'PROBLEM="$1"',
            "",
            'if [ -z "$PROBLEM" ]; then',
            "    echo \"Usage: $0 '<problem description>'\"",
            "    echo \"Example: $0 'polarity calculation'\"",
            "    exit 1",
            "fi",
            "",
            'echo "🔍 Checking existing solutions for: $PROBLEM"',
            'echo "="*50',
            "",
        ]

        # Add checks for each prompt
        for i, prompt in enumerate(self.prompts):
            keywords_pattern = "|".join(prompt.trigger_keywords)
            script_lines.extend(
                [
                    f"# Check {i+1}: {prompt.message.replace('🔍 BEFORE implementing ', '')}",
                    f'if echo "$PROBLEM" | grep -iE "({keywords_pattern})" > /dev/null; then',
                    f'    echo "⚠️  {prompt.message}"',
                    '    echo "Run these commands:"',
                ]
            )

            for cmd in prompt.check_commands:
                script_lines.append(f'    echo "  {cmd}"')

            script_lines.extend(['    echo ""', "fi", ""])

        script_lines.extend(
            [
                'echo "💡 Always check:"',
                "echo \"  1. python tools/function_lookup.py '<your problem>'\"",
                'echo "  2. python tools/architectural_mapper.py (for subsystem guidance)"',
                'echo "  3. python tools/pattern_catalog.py (for established patterns)"',
                'echo "  4. python tools/semantic_code_analyzer.py (for relationships)"',
                "",
            ]
        )

        with open(output_path, "w") as f:
            f.write("\n".join(script_lines))

        # Make executable
        os.chmod(output_path, 0o755)

    def create_memory_integration_guide(self) -> str:
        """Create a guide for integrating this system into development workflow."""
        guide = [
            "# How to Remember to Use the Layered Strategy",
            "",
            "## 1. Pre-Implementation Checklist",
            "",
            "Before implementing ANY new functionality, run:",
            "```bash",
            "./tools/context_check.sh '<problem description>'",
            "```",
            "",
            "## 2. IDE Integration",
            "",
            "Add these as IDE snippets or shortcuts:",
            "",
            "### Quick Function Lookup",
            "```bash",
            'python tools/function_lookup.py "$SELECTION"',
            "```",
            "",
            "### Architecture Check",
            "```bash",
            'python tools/architectural_mapper.py | grep -i "$CONCEPT"',
            "```",
            "",
            "### Pattern Check",
            "```bash",
            'python tools/pattern_catalog.py | grep -A5 "$PROBLEM"',
            "```",
            "",
            "## 3. Memory Triggers",
            "",
            "Set up these memory triggers:",
            "",
        ]

        for prompt in self.prompts:
            guide.extend(
                [
                    f"### {prompt.message}",
                    f"**Triggers**: {', '.join(prompt.trigger_keywords)}",
                    f"**Priority**: {prompt.priority}",
                    "**Commands**:",
                ]
            )
            for cmd in prompt.check_commands:
                guide.append(f"- `{cmd}`")
            guide.append("")

        guide.extend(
            [
                "## 4. Automated Integration",
                "",
                "### Git Pre-commit Hook",
                "Add to `.git/hooks/pre-commit`:",
                "```bash",
                "# Check for potential reinvention",
                "git diff --cached --name-only | grep '\\.py$' | while read file; do",
                "    if git diff --cached \"$file\" | grep -E '(def|class).*polarity|hierarchy|transformation'; then",
                '        echo "⚠️  Check existing solutions before implementing polarity/hierarchy/transformation"',
                "        echo \"Run: python tools/function_lookup.py '<your concept>'\"",
                "    fi",
                "done",
                "```",
                "",
                "### VS Code Integration",
                "Add to `.vscode/tasks.json`:",
                "```json",
                "{",
                '    "label": "Check Existing Solutions",',
                '    "type": "shell",',
                '    "command": "python",',
                '    "args": ["tools/function_lookup.py", "${selectedText}"],',
                '    "group": "build"',
                "}",
                "```",
                "",
                "## 5. Memory System Integration",
                "",
                "The key is to make checking existing solutions **easier than implementing from scratch**.",
                "",
                "### Quick Commands (add to .bashrc/.zshrc)",
                "```bash",
                "alias arisbe-check='python tools/function_lookup.py'",
                "alias arisbe-arch='python tools/architectural_mapper.py'",
                "alias arisbe-patterns='python tools/pattern_catalog.py'",
                "```",
                "",
                "### Development Workflow",
                "1. **Problem identified** → Run context check",
                "2. **Existing solution found** → Use it",
                "3. **No solution found** → Implement + document pattern",
                "4. **Update tools** → Add new pattern to catalog",
                "",
            ]
        )

        return "\n".join(guide)

    def export_memory_system(self, output_dir: str):
        """Export the complete memory system."""
        output_path = Path(output_dir)

        # Export prompts
        prompts_data = {
            "prompts": [asdict(prompt) for prompt in self.prompts],
            "metadata": {
                "total_prompts": len(self.prompts),
                "high_priority": len([p for p in self.prompts if p.priority == "high"]),
            },
        }

        with open(output_path / "context_prompts.json", "w") as f:
            json.dump(prompts_data, f, indent=2)

        # Generate context check script
        self.generate_context_check_script(str(output_path / "context_check.sh"))

        # Generate memory integration guide
        guide = self.create_memory_integration_guide()
        with open(output_path / "MEMORY_INTEGRATION_GUIDE.md", "w") as f:
            f.write(guide)


def main():
    """Set up the context memory system."""
    memory_system = ContextMemorySystem()

    print("Setting up context memory system...")

    # Export to tools directory
    memory_system.export_memory_system("/Users/mjh/Sync/GitHub/Arisbe/tools")

    print("Context memory system created:")
    print("- tools/context_check.sh (executable script)")
    print("- tools/context_prompts.json (prompt definitions)")
    print("- tools/MEMORY_INTEGRATION_GUIDE.md (integration guide)")

    # Test with polarity problem
    polarity_prompts = memory_system.check_context_for_problem("polarity calculation")
    print(
        f"\nExample: 'polarity calculation' triggers {len(polarity_prompts)} prompts:"
    )
    for prompt in polarity_prompts:
        print(f"  {prompt.message}")


if __name__ == "__main__":
    main()
