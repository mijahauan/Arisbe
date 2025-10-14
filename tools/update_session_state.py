#!/usr/bin/env python3
"""
Update Session State - Auto-update on Git Commits

This tool maintains .coherence_session_state.json with current information:
- Updates timestamp
- Adds recent accomplishments from git log
- Tracks modified files
- Updates session metadata

USAGE:
    python tools/update_session_state.py
    
Called automatically by git pre-commit hook.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class SessionStateUpdater:
    """Updates .coherence_session_state.json with current information."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path.cwd()
        self.state_file = self.project_root / ".coherence_session_state.json"
        
    def load_current_state(self) -> Dict[str, Any]:
        """Load current session state."""
        if not self.state_file.exists():
            print(f"❌ Session state file not found: {self.state_file}")
            print("   Run coherence framework initialization first.")
            sys.exit(1)
            
        with open(self.state_file, 'r') as f:
            return json.load(f)
    
    def get_recent_commits(self, count: int = 5) -> List[str]:
        """Get recent git commits."""
        try:
            result = subprocess.run(
                ['git', 'log', f'-{count}', '--pretty=format:%h - %s'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode != 0:
                return []
            
            commits = result.stdout.strip().split('\n')
            return [c for c in commits if c]
            
        except Exception as e:
            print(f"⚠️  Could not get git commits: {e}")
            return []
    
    def get_modified_files(self) -> List[str]:
        """Get currently modified files."""
        try:
            # Staged files
            staged = subprocess.run(
                ['git', 'diff', '--cached', '--name-only'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            # Unstaged files
            unstaged = subprocess.run(
                ['git', 'diff', '--name-only'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            files = set()
            if staged.returncode == 0:
                files.update(staged.stdout.strip().split('\n'))
            if unstaged.returncode == 0:
                files.update(unstaged.stdout.strip().split('\n'))
            
            return sorted([f for f in files if f])
            
        except Exception as e:
            print(f"⚠️  Could not get modified files: {e}")
            return []
    
    def get_git_branch(self) -> str:
        """Get current git branch."""
        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            return "unknown"
            
        except Exception:
            return "unknown"
    
    def get_last_commit_hash(self) -> str:
        """Get hash of last commit."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            return "unknown"
            
        except Exception:
            return "unknown"
    
    def format_accomplishment_from_commit(self, commit_line: str) -> str:
        """Format a git commit as an accomplishment."""
        # commit_line format: "abc1234 - Commit message"
        parts = commit_line.split(' - ', 1)
        if len(parts) == 2:
            commit_hash, message = parts
            # Get date of this commit
            try:
                result = subprocess.run(
                    ['git', 'show', '-s', '--format=%ci', commit_hash],
                    capture_output=True,
                    text=True,
                    cwd=self.project_root
                )
                if result.returncode == 0:
                    date_str = result.stdout.strip().split()[0]  # YYYY-MM-DD
                    return f"{date_str}: {message}"
            except Exception:
                pass
            
            return f"{datetime.now().strftime('%Y-%m-%d')}: {message}"
        
        return commit_line
    
    def update_state(self) -> Dict[str, Any]:
        """Update session state with current information."""
        state = self.load_current_state()
        
        print("📝 Updating session state...")
        
        # Update timestamp
        state["last_updated"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        
        # Update recent accomplishments from git log
        recent_commits = self.get_recent_commits(5)
        if recent_commits:
            accomplishments = [
                self.format_accomplishment_from_commit(c) 
                for c in recent_commits
            ]
            state["recent_accomplishments"] = accomplishments[:5]
            print(f"   Updated recent accomplishments ({len(accomplishments)} commits)")
        
        # Update session metadata
        if "session_metadata" not in state:
            state["session_metadata"] = {}
        
        state["session_metadata"]["git_branch"] = self.get_git_branch()
        state["session_metadata"]["last_commit"] = self.get_last_commit_hash()
        
        # Get modified files (for information, not stored in state)
        modified_files = self.get_modified_files()
        if modified_files:
            print(f"   Currently modified files: {len(modified_files)}")
        
        return state
    
    def save_state(self, state: Dict[str, Any]) -> None:
        """Save updated session state."""
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        print(f"✅ Session state updated: {self.state_file}")
    
    def run(self) -> bool:
        """Run the session state update."""
        try:
            state = self.update_state()
            self.save_state(state)
            return True
            
        except Exception as e:
            print(f"❌ Error updating session state: {e}")
            return False


def main():
    """Main entry point."""
    updater = SessionStateUpdater()
    success = updater.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
