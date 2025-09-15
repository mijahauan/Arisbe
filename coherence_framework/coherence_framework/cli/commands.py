#!/usr/bin/env python3
"""
CLI Commands for AI Coherence Framework

Provides command-line interface for all coherence framework operations.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from ..core.context_awareness import ContextAwarenessSystem
from ..core.quality_gates import QualityGateSystem
from ..core.smart_git import SmartCommitSystem
from .project_initializer import ProjectInitializer


def init_project():
    """Initialize coherence framework in current project."""
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
            return 1
        
        success = initializer.initialize_project(args.name, args.language)
    
    return 0 if success else 1


def check_coherence():
    """Check for existing solutions and coherence issues."""
    parser = argparse.ArgumentParser(description="Check codebase coherence")
    parser.add_argument("task_description", nargs="?", help="Description of task to check")
    parser.add_argument("--quality", action="store_true", help="Run quality checks")
    parser.add_argument("--fix", action="store_true", help="Auto-fix issues")
    parser.add_argument("--report", action="store_true", help="Generate detailed report")
    parser.add_argument("--dead-code", action="store_true", help="Check for dead code")
    parser.add_argument("--docs", action="store_true", help="Generate documentation")
    parser.add_argument("--threshold", type=int, default=80, help="Quality threshold")
    parser.add_argument("--ci", action="store_true", help="CI mode (exit codes)")
    
    args = parser.parse_args()
    
    if args.task_description:
        # Context awareness check
        context_system = ContextAwarenessSystem()
        results = context_system.check_context(args.task_description)
        
        if results.get("existing_solutions"):
            print("🚨 STOP: Existing solutions found!")
            for solution in results["existing_solutions"]:
                print(f"  • {solution}")
            print(f"\n💡 {results.get('message', 'Check existing implementations first')}")
            return 1 if args.ci else 0
        else:
            print("✅ No existing solutions found - proceed with implementation")
            return 0
    
    if args.quality:
        # Quality gate check
        quality_system = QualityGateSystem()
        metrics = quality_system.run_all_checks(fix_issues=args.fix)
        
        print(f"\n📊 Quality Report:")
        print(f"Overall Score: {metrics.overall_score}/100")
        print(f"Coverage: {metrics.coverage}%")
        print(f"Dead Code: {metrics.dead_code}%")
        print(f"Type Coverage: {metrics.type_coverage}%")
        print(f"Complexity: {metrics.complexity}")
        
        if args.report:
            quality_system.generate_report()
            print("📄 Detailed report generated: quality_report.html")
        
        if metrics.overall_score < args.threshold:
            print(f"❌ Quality below threshold ({args.threshold})")
            return 1 if args.ci else 0
        else:
            print("✅ Quality gates passed")
            return 0
    
    # Default: show help
    parser.print_help()
    return 0


def smart_commit():
    """Smart git commit with automated timing and messages."""
    parser = argparse.ArgumentParser(description="Smart git commit system")
    parser.add_argument("--auto", action="store_true", help="Enable auto-commit mode")
    parser.add_argument("--checkpoint", type=str, help="Create checkpoint with description")
    parser.add_argument("--recovery", action="store_true", help="Show recovery options")
    parser.add_argument("--message", "-m", type=str, help="Commit message")
    parser.add_argument("--wip", action="store_true", help="Work in progress commit")
    
    args = parser.parse_args()
    
    commit_system = SmartCommitSystem()
    
    if args.auto:
        print("🔄 Starting auto-commit mode (Ctrl+C to stop)")
        commit_system.start_auto_commit()
        return 0
    
    if args.checkpoint:
        success = commit_system.create_checkpoint(args.checkpoint)
        return 0 if success else 1
    
    if args.recovery:
        commit_system.show_recovery_options()
        return 0
    
    # Regular commit
    success = commit_system.smart_commit(
        message=args.message,
        is_wip=args.wip
    )
    return 0 if success else 1


def session_manager():
    """Manage development sessions."""
    parser = argparse.ArgumentParser(description="Development session manager")
    parser.add_argument("action", choices=["start", "end"], help="Session action")
    parser.add_argument("--feature", type=str, help="Feature name for branch")
    parser.add_argument("--auto-commit", action="store_true", help="Enable auto-commit")
    
    args = parser.parse_args()
    
    if args.action == "start":
        return _start_session(args.feature, args.auto_commit)
    elif args.action == "end":
        return _end_session()
    
    return 1


def _start_session(feature_name: Optional[str], auto_commit: bool) -> int:
    """Start development session."""
    print("🚀 Starting development session...")
    
    # Check git status
    import subprocess
    try:
        result = subprocess.run(["git", "status", "--porcelain"], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            print("⚠️  Uncommitted changes detected")
            response = input("Commit changes before starting session? (y/N): ")
            if response.lower() == 'y':
                commit_system = SmartCommitSystem()
                commit_system.smart_commit(is_wip=True)
    except:
        print("⚠️  Not in a git repository")
    
    # Create feature branch if specified
    if feature_name:
        try:
            subprocess.run(["git", "checkout", "-b", f"feature/{feature_name}"], 
                          check=True)
            print(f"🌿 Created feature branch: feature/{feature_name}")
        except subprocess.CalledProcessError:
            print(f"⚠️  Could not create branch feature/{feature_name}")
    
    # Run context check
    print("🔍 Running context awareness check...")
    context_system = ContextAwarenessSystem()
    context_system.show_pre_development_checklist()
    
    # Start auto-commit if requested
    if auto_commit:
        print("🔄 Auto-commit enabled")
        # Note: In practice, this would start a background process
    
    print("✅ Development session started!")
    return 0


def _end_session() -> int:
    """End development session."""
    print("🏁 Ending development session...")
    
    # Commit any remaining work
    commit_system = SmartCommitSystem()
    commit_system.smart_commit(message="Session end - WIP commit", is_wip=True)
    
    # Run final quality check
    quality_system = QualityGateSystem()
    metrics = quality_system.run_all_checks()
    print(f"📊 Final quality score: {metrics.overall_score}/100")
    
    # Show session summary
    import subprocess
    try:
        result = subprocess.run([
            "git", "log", "--oneline", "--since='1 hour ago'"
        ], capture_output=True, text=True)
        
        if result.stdout.strip():
            print("\n📝 Session commits:")
            print(result.stdout)
    except:
        pass
    
    print("✅ Development session ended!")
    return 0


# Entry points for console scripts
def main_init():
    """Entry point for coherence-init command."""
    sys.exit(init_project())


def main_check():
    """Entry point for coherence-check command."""
    sys.exit(check_coherence())


def main_commit():
    """Entry point for coherence-commit command."""
    sys.exit(smart_commit())


def main_session():
    """Entry point for coherence-session command."""
    sys.exit(session_manager())
