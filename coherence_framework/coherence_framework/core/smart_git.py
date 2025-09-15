#!/usr/bin/env python3
"""
Smart Git System - Standalone Version

Intelligent git workflow with automated commit timing, recovery options,
and graceful handling of development excursions.
"""

import os
import subprocess
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import yaml


class SmartCommitSystem:
    """Standalone smart git commit system for any codebase."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.config_dir = self.project_root / ".coherence"
        self.config = self._load_config()
        self.auto_commit_active = False
        
    def _load_config(self) -> Dict[str, Any]:
        """Load git configuration."""
        config_file = self.config_dir / "config.yaml"
        if config_file.exists():
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        
        return {
            "git": {
                "auto_commit_interval": 900,  # 15 minutes
                "branch_prefix": "feature/",
                "checkpoint_prefix": "checkpoint/",
            }
        }
    
    def smart_commit(self, message: Optional[str] = None, is_wip: bool = False) -> bool:
        """Create intelligent commit with auto-generated message."""
        try:
            # Check if there are changes to commit
            result = subprocess.run(["git", "status", "--porcelain"], 
                                  capture_output=True, text=True, cwd=self.project_root)
            
            if not result.stdout.strip():
                print("📝 No changes to commit")
                return True
            
            # Generate commit message if not provided
            if not message:
                message = self._generate_commit_message(is_wip)
            
            # Add prefix for WIP commits
            if is_wip and not message.startswith("🚧"):
                message = f"🚧 WIP: {message}"
            
            # Stage all changes
            subprocess.run(["git", "add", "-A"], cwd=self.project_root, check=True)
            
            # Commit with message
            subprocess.run(["git", "commit", "-m", message], 
                          cwd=self.project_root, check=True)
            
            print(f"✅ Committed: {message}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Commit failed: {e}")
            return False
    
    def _generate_commit_message(self, is_wip: bool = False) -> str:
        """Generate intelligent commit message based on changes."""
        try:
            # Get changed files
            result = subprocess.run(["git", "diff", "--cached", "--name-only"], 
                                  capture_output=True, text=True, cwd=self.project_root)
            
            changed_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
            
            if not changed_files:
                return "Minor updates"
            
            # Categorize changes
            categories = {
                "src": "📝 SRC",
                "test": "🧪 TEST", 
                "tool": "🔧 TOOL",
                "doc": "📚 DOC",
                "config": "⚙️ CONFIG"
            }
            
            file_categories = []
            for file_path in changed_files:
                file_lower = file_path.lower()
                
                if any(test_dir in file_lower for test_dir in ["test", "spec"]):
                    file_categories.append("test")
                elif any(src_dir in file_lower for src_dir in ["src", "lib"]):
                    file_categories.append("src")
                elif any(tool_dir in file_lower for tool_dir in ["tool", "script"]):
                    file_categories.append("tool")
                elif any(doc_ext in file_lower for doc_ext in [".md", ".rst", ".txt"]):
                    file_categories.append("doc")
                elif any(config_file in file_lower for config_file in ["config", ".yaml", ".json", ".toml"]):
                    file_categories.append("config")
                else:
                    file_categories.append("src")  # Default
            
            # Get most common category
            most_common = max(set(file_categories), key=file_categories.count)
            category_prefix = categories.get(most_common, "📝 SRC")
            
            # Generate description
            if len(changed_files) == 1:
                file_name = Path(changed_files[0]).name
                description = f"Update {file_name}"
            elif len(changed_files) <= 3:
                description = f"Update {len(changed_files)} files"
            else:
                description = f"Update {len(changed_files)} files across {len(set(file_categories))} areas"
            
            return f"{category_prefix}: {description}"
            
        except Exception:
            timestamp = datetime.now().strftime("%H:%M")
            return f"📝 SRC: Updates at {timestamp}"
    
    def create_checkpoint(self, description: str) -> bool:
        """Create a checkpoint commit before risky changes."""
        try:
            # First commit any current changes
            self.smart_commit(f"Checkpoint: {description}", is_wip=True)
            
            # Create checkpoint branch
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            branch_name = f"checkpoint/{timestamp}_{description.replace(' ', '_')}"
            
            subprocess.run(["git", "checkout", "-b", branch_name], 
                          cwd=self.project_root, check=True)
            
            print(f"🔖 Created checkpoint: {branch_name}")
            
            # Return to original branch
            result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD~1"], 
                                  capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                original_branch = result.stdout.strip()
                subprocess.run(["git", "checkout", original_branch], 
                              cwd=self.project_root)
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Checkpoint creation failed: {e}")
            return False
    
    def start_auto_commit(self):
        """Start auto-commit background process."""
        if self.auto_commit_active:
            print("🔄 Auto-commit already active")
            return
        
        self.auto_commit_active = True
        interval = self.config["git"]["auto_commit_interval"]
        
        def auto_commit_loop():
            while self.auto_commit_active:
                time.sleep(interval)
                if self.auto_commit_active:  # Check again after sleep
                    self.smart_commit(is_wip=True)
        
        thread = threading.Thread(target=auto_commit_loop, daemon=True)
        thread.start()
        
        print(f"🔄 Auto-commit started (every {interval//60} minutes)")
        print("Press Ctrl+C to stop")
        
        try:
            while self.auto_commit_active:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_auto_commit()
    
    def stop_auto_commit(self):
        """Stop auto-commit background process."""
        self.auto_commit_active = False
        print("⏹️  Auto-commit stopped")
    
    def show_recovery_options(self):
        """Show available recovery options."""
        print("🔧 Git Recovery Options:\n")
        
        # Show recent commits
        try:
            result = subprocess.run([
                "git", "log", "--oneline", "-10", "--graph"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                print("📝 Recent commits:")
                print(result.stdout)
        except:
            pass
        
        # Show available branches
        try:
            result = subprocess.run([
                "git", "branch", "-a"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                print("\n🌿 Available branches:")
                branches = result.stdout.strip().split('\n')
                for branch in branches:
                    if "checkpoint/" in branch:
                        print(f"  🔖 {branch.strip()}")
                    elif "feature/" in branch:
                        print(f"  ✨ {branch.strip()}")
                    else:
                        print(f"     {branch.strip()}")
        except:
            pass
        
        print("\n🛠️  Recovery Commands:")
        print("  git reset --soft HEAD~1     # Undo last commit, keep changes")
        print("  git reset --hard HEAD~1     # Undo last commit, discard changes")
        print("  git checkout checkpoint/... # Switch to checkpoint branch")
        print("  git stash                   # Save current work temporarily")
        print("  git stash pop               # Restore saved work")
        
        # Show stashes
        try:
            result = subprocess.run([
                "git", "stash", "list"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0 and result.stdout.strip():
                print("\n💾 Available stashes:")
                print(result.stdout)
        except:
            pass
    
    def create_excursion_branch(self, description: str) -> bool:
        """Create branch for failed experiment documentation."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            branch_name = f"excursion/{timestamp}_{description.replace(' ', '_')}"
            
            # Commit current state
            self.smart_commit(f"🚫 EXCURSION: {description}", is_wip=True)
            
            # Create excursion branch
            subprocess.run(["git", "checkout", "-b", branch_name], 
                          cwd=self.project_root, check=True)
            
            print(f"🚫 Created excursion branch: {branch_name}")
            print("💡 This preserves your work for future reference")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Excursion branch creation failed: {e}")
            return False
    
    def get_git_status(self) -> Dict[str, Any]:
        """Get comprehensive git status."""
        status = {
            "clean": False,
            "branch": "unknown",
            "ahead": 0,
            "behind": 0,
            "staged": 0,
            "modified": 0,
            "untracked": 0,
        }
        
        try:
            # Current branch
            result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], 
                                  capture_output=True, text=True, cwd=self.project_root)
            if result.returncode == 0:
                status["branch"] = result.stdout.strip()
            
            # File status
            result = subprocess.run(["git", "status", "--porcelain"], 
                                  capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
                
                for line in lines:
                    if line.startswith('A ') or line.startswith('M ') or line.startswith('D '):
                        status["staged"] += 1
                    elif line.startswith(' M') or line.startswith(' D'):
                        status["modified"] += 1
                    elif line.startswith('??'):
                        status["untracked"] += 1
                
                status["clean"] = len(lines) == 0
            
        except Exception:
            pass
        
        return status


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Smart Git Commit System")
    parser.add_argument("--auto", action="store_true", help="Start auto-commit")
    parser.add_argument("--checkpoint", type=str, help="Create checkpoint")
    parser.add_argument("--recovery", action="store_true", help="Show recovery options")
    parser.add_argument("--excursion", type=str, help="Create excursion branch")
    parser.add_argument("--message", "-m", type=str, help="Commit message")
    parser.add_argument("--wip", action="store_true", help="WIP commit")
    
    args = parser.parse_args()
    
    system = SmartCommitSystem()
    
    if args.auto:
        system.start_auto_commit()
    elif args.checkpoint:
        system.create_checkpoint(args.checkpoint)
    elif args.recovery:
        system.show_recovery_options()
    elif args.excursion:
        system.create_excursion_branch(args.excursion)
    else:
        # Regular commit
        system.smart_commit(message=args.message, is_wip=args.wip)


if __name__ == "__main__":
    main()
