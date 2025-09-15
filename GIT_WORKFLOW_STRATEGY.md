# Arisbe Git Workflow Strategy - Graceful Recovery from Code Excursions

## **The Problem**
Code excursions and diversions can lead to:
- Lost work when experiments fail
- Difficulty reverting to known-good states
- Unclear development history
- Fear of experimentation due to recovery complexity

## **The Solution: Strategic Git Workflow**

### **1. Branch-Based Development Strategy**

#### **Main Branch Protection**
```bash
# Never work directly on main - always use feature branches
git checkout -b feature/your-task-name
```

#### **Branch Naming Convention**
```bash
# Feature development
git checkout -b feature/polarity-optimization
git checkout -b feature/transformation-validation

# Bug fixes
git checkout -b fix/coherence-analyzer-crash
git checkout -b fix/pre-commit-hook-issue

# Experiments (safe to abandon)
git checkout -b experiment/new-rendering-approach
git checkout -b spike/alternative-architecture

# Integration work
git checkout -b integrate/orphaned-dau-tests
git checkout -b integrate/corpus-management
```

### **2. Commit Timing Strategy**

#### **Micro-Commits for Safety**
Commit **every 15-30 minutes** or after **each logical unit**:

```bash
# After each small, working change
git add -A
git commit -m "WIP: Add polarity calculation interface"

# After tests pass
git add -A  
git commit -m "✅ Polarity calculation tests passing"

# After documentation
git add -A
git commit -m "📚 Document polarity calculation usage"

# After integration
git add -A
git commit -m "🔗 Integrate polarity calc with transformation system"
```

#### **Commit Message Convention**
```bash
# Status prefixes for easy scanning
git commit -m "🚧 WIP: Initial transformation validator structure"
git commit -m "✅ WORKING: Transformation validation complete"
git commit -m "🐛 FIX: Resolve circular import in validator"
git commit -m "📚 DOCS: Add transformation validator examples"
git commit -m "🔗 INTEGRATE: Connect validator to quality gates"
git commit -m "🧪 TEST: Add comprehensive validator test suite"
git commit -m "♻️ REFACTOR: Simplify validator interface"
git commit -m "🎯 MILESTONE: Transformation system complete"
```

### **3. Automated Commit System**

#### **Smart Auto-Commit Tool**
```python
#!/usr/bin/env python3
# tools/smart_commit.py

import subprocess
import os
import time
from datetime import datetime
from pathlib import Path

class SmartCommitSystem:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.last_commit_time = None
        
    def should_auto_commit(self):
        """Determine if an auto-commit should happen."""
        # Check if files have changed
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True)
        
        if not result.stdout.strip():
            return False, "No changes to commit"
        
        # Check if enough time has passed (15 minutes)
        if self.last_commit_time:
            time_diff = time.time() - self.last_commit_time
            if time_diff < 900:  # 15 minutes
                return False, f"Only {time_diff/60:.1f} minutes since last commit"
        
        # Check if tests are passing (optional safety check)
        test_result = subprocess.run(['python', '-m', 'pytest', 'tests/', '-x', '--tb=no'], 
                                   capture_output=True, text=True)
        
        if test_result.returncode == 0:
            return True, "Tests passing, safe to commit"
        else:
            return True, "Tests failing, but committing WIP for safety"
    
    def generate_smart_commit_message(self):
        """Generate intelligent commit message based on changes."""
        # Get changed files
        result = subprocess.run(['git', 'diff', '--name-only', '--cached'], 
                              capture_output=True, text=True)
        
        if not result.stdout.strip():
            # Stage all changes first
            subprocess.run(['git', 'add', '-A'])
            result = subprocess.run(['git', 'diff', '--name-only', '--cached'], 
                                  capture_output=True, text=True)
        
        changed_files = result.stdout.strip().split('\n')
        
        # Analyze changes to generate appropriate message
        if any('test' in f for f in changed_files):
            prefix = "🧪 TEST:"
        elif any('doc' in f.lower() or f.endswith('.md') for f in changed_files):
            prefix = "📚 DOCS:"
        elif any('tool' in f for f in changed_files):
            prefix = "🔧 TOOL:"
        elif len(changed_files) == 1:
            prefix = f"📝 UPDATE:"
        else:
            prefix = "🚧 WIP:"
        
        # Generate description based on file patterns
        if len(changed_files) == 1:
            file_name = Path(changed_files[0]).stem
            message = f"{prefix} Update {file_name}"
        elif len(changed_files) <= 3:
            file_names = [Path(f).stem for f in changed_files]
            message = f"{prefix} Update {', '.join(file_names)}"
        else:
            message = f"{prefix} Multiple file updates ({len(changed_files)} files)"
        
        # Add timestamp for WIP commits
        if prefix == "🚧 WIP:":
            timestamp = datetime.now().strftime("%H:%M")
            message += f" - {timestamp}"
        
        return message
    
    def auto_commit(self):
        """Perform automatic commit with smart message."""
        should_commit, reason = self.should_auto_commit()
        
        if not should_commit:
            print(f"⏸️  Skipping auto-commit: {reason}")
            return False
        
        # Stage all changes
        subprocess.run(['git', 'add', '-A'])
        
        # Generate commit message
        message = self.generate_smart_commit_message()
        
        # Commit
        result = subprocess.run(['git', 'commit', '-m', message], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Auto-committed: {message}")
            self.last_commit_time = time.time()
            return True
        else:
            print(f"❌ Auto-commit failed: {result.stderr}")
            return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Smart commit system")
    parser.add_argument("--auto", action="store_true", help="Auto-commit if appropriate")
    parser.add_argument("--message", help="Custom commit message")
    
    args = parser.parse_args()
    
    system = SmartCommitSystem()
    
    if args.auto:
        system.auto_commit()
    elif args.message:
        subprocess.run(['git', 'add', '-A'])
        subprocess.run(['git', 'commit', '-m', args.message])
    else:
        # Interactive mode
        message = system.generate_smart_commit_message()
        print(f"Suggested commit message: {message}")
        
        user_input = input("Use this message? (y/n/custom): ").strip().lower()
        if user_input == 'y':
            subprocess.run(['git', 'add', '-A'])
            subprocess.run(['git', 'commit', '-m', message])
        elif user_input == 'custom':
            custom_message = input("Enter custom message: ")
            subprocess.run(['git', 'add', '-A'])
            subprocess.run(['git', 'commit', '-m', custom_message])

if __name__ == "__main__":
    main()
```

### **4. Recovery Strategies**

#### **Quick Recovery Commands**
```bash
# See recent commits with visual graph
alias git-recent="git log --oneline --graph -10"

# Quick reset to last working state
alias git-reset-soft="git reset --soft HEAD~1"  # Keep changes, undo commit
alias git-reset-hard="git reset --hard HEAD~1"  # Lose changes, undo commit

# Stash current work quickly
alias git-stash-quick="git stash push -m 'Quick stash $(date)'"

# Create checkpoint branch before risky changes
alias git-checkpoint="git checkout -b checkpoint/$(date +%Y%m%d-%H%M%S)"
```

#### **Excursion Recovery Workflow**
```bash
# 1. Realize you're on an unproductive path
git status  # See what's changed

# 2. Decide recovery strategy:

# Option A: Keep work but reset to clean state
git stash push -m "Excursion attempt - may be useful later"
git reset --hard HEAD  # Back to last commit

# Option B: Commit the attempt for future reference
git add -A
git commit -m "🚫 EXCURSION: Attempted alternative approach - reverting"
git reset --hard HEAD~1  # Go back but keep commit in reflog

# Option C: Branch the excursion and return to main path
git checkout -b excursion/failed-attempt
git add -A
git commit -m "🚫 EXCURSION: Alternative approach - needs rethink"
git checkout feature/original-task  # Back to main work

# 3. Continue with original plan
python tools/context_awareness_system.py --check "original task"
```

### **5. Integration with Quality System**

#### **Enhanced Pre-commit Hook**
```bash
#!/bin/bash
# .git/hooks/pre-commit (enhanced version)

echo "🔍 Running Arisbe Quality Gates..."

# Check if this is a WIP commit (allow lower standards)
commit_msg=$(git log --format=%B -n 1 HEAD 2>/dev/null || echo "")
if [[ "$commit_msg" == *"WIP"* ]] || [[ "$commit_msg" == *"🚧"* ]]; then
    echo "🚧 WIP commit detected - running minimal checks"
    
    # Only check for critical issues in WIP commits
    if ! python tools/quality_gate_system.py --check --threshold 50; then
        echo "❌ Critical issues found even for WIP. Fix before committing."
        exit 1
    fi
    
    echo "✅ WIP commit quality check passed"
    exit 0
fi

# Full quality check for non-WIP commits
if ! python tools/quality_gate_system.py --check --threshold 80; then
    echo "❌ Quality gate failed. Use 'WIP:' prefix for work-in-progress commits."
    echo "Or fix issues and commit again."
    exit 1
fi

echo "✅ Full quality gates passed!"
exit 0
```

### **6. Development Session Management**

#### **Session Start Routine**
```bash
#!/bin/bash
# tools/start_dev_session.sh

echo "🚀 Starting Arisbe Development Session"

# 1. Check current status
echo "📊 Current repository status:"
git status --short
git log --oneline -5

# 2. Create session branch if needed
current_branch=$(git branch --show-current)
if [[ "$current_branch" == "main" ]]; then
    echo "⚠️  You're on main branch. Creating feature branch..."
    read -p "Enter feature name: " feature_name
    git checkout -b "feature/$feature_name"
fi

# 3. Run context awareness check
echo "🧠 Running context awareness check..."
read -p "Describe what you're working on: " task_description
python tools/context_awareness_system.py --check "$task_description"

# 4. Check quality baseline
echo "📈 Checking quality baseline..."
python tools/quality_gate_system.py --check

# 5. Set up auto-commit timer (optional)
read -p "Enable auto-commit every 15 minutes? (y/n): " auto_commit
if [[ "$auto_commit" == "y" ]]; then
    echo "⏰ Auto-commit enabled. Run 'python tools/smart_commit.py --auto' periodically"
fi

echo "✅ Development session ready!"
```

#### **Session End Routine**
```bash
#!/bin/bash
# tools/end_dev_session.sh

echo "🏁 Ending Arisbe Development Session"

# 1. Final commit of any remaining work
if [[ -n $(git status --porcelain) ]]; then
    echo "📝 Uncommitted changes found. Creating final commit..."
    python tools/smart_commit.py
fi

# 2. Quality check
echo "📊 Final quality check..."
python tools/quality_gate_system.py --check --report

# 3. Update documentation
echo "📚 Updating living documentation..."
python tools/living_documentation_generator.py

# 4. Session summary
echo "📋 Session Summary:"
git log --oneline --since="2 hours ago"

# 5. Merge to main if feature complete
current_branch=$(git branch --show-current)
if [[ "$current_branch" != "main" ]]; then
    read -p "Feature complete? Merge to main? (y/n): " merge_main
    if [[ "$merge_main" == "y" ]]; then
        git checkout main
        git merge "$current_branch"
        git branch -d "$current_branch"
        echo "✅ Feature merged and branch cleaned up"
    fi
fi

echo "✅ Development session ended cleanly!"
```

## **7. Practical Usage Examples**

### **Starting a New Feature**
```bash
# 1. Start session
./tools/start_dev_session.sh

# 2. Work with frequent commits
# ... make changes ...
python tools/smart_commit.py --auto

# 3. Create checkpoint before risky change
git checkpoint

# 4. If experiment fails
git reset --hard HEAD~1  # Back to checkpoint

# 5. End session
./tools/end_dev_session.sh
```

### **Recovering from Excursion**
```bash
# Realize you've gone off track
git log --oneline -10  # See recent commits

# Option 1: Soft reset (keep changes)
git reset --soft HEAD~3  # Go back 3 commits, keep files

# Option 2: Hard reset (lose changes)  
git reset --hard HEAD~3  # Go back 3 commits, discard files

# Option 3: Branch the excursion
git checkout -b excursion/$(date +%Y%m%d)
git add -A && git commit -m "🚫 EXCURSION: Branched for later review"
git checkout main
```

## **8. Benefits of This Strategy**

### **Safety Net**
- **Frequent commits**: Never lose more than 15-30 minutes of work
- **Branch isolation**: Experiments don't affect main codebase
- **Easy recovery**: Multiple strategies for different scenarios

### **Development Confidence**
- **Fearless experimentation**: Easy to try new approaches
- **Clear history**: Understand what was tried and why
- **Quality integration**: Commits tied to quality metrics

### **Workflow Efficiency**
- **Automated timing**: Smart commit system handles routine commits
- **Session management**: Clear start/end procedures
- **Recovery shortcuts**: Aliases for common recovery operations

This git strategy transforms version control from a safety requirement into a **development superpower** that encourages experimentation while providing multiple recovery paths.
