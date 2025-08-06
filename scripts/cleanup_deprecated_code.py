#!/usr/bin/env python3
"""
Systematic Deprecated Code Cleanup Script

This script removes all lingering, obsolescent, and distracting code references
from the codebase to maintain architectural discipline and prevent confusion.

CRITICAL: Run this before any new development to ensure clean foundation.
"""

import os
import sys
import re
from typing import List, Dict, Set, Tuple
import shutil
from pathlib import Path

class DeprecatedCodeCleaner:
    """Systematic cleaner for deprecated code patterns."""
    
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.backup_dir = self.repo_root / "cleanup_backups"
        self.cleanup_log = []
        
        # Deprecated patterns to remove/replace
        self.deprecated_patterns = {
            # Hook line references (per Dau formalism - hooks are invisible)
            'hook_line_patterns': [
                r'hook_line',
                r'HookLine',
                r'add_hook_line',
                r'_render_hook_line',
                r'draw_hook_line',
                r'hook_lines',
                r'hookline',
                r'hook-line'
            ],
            
            # Old/placeholder imports
            'deprecated_imports': [
                r'from.*hook_line.*import',
                r'import.*hook_line',
                r'from tkinter import.*# TODO: Replace with PySide6',
                r'import tkinter.*# Temporary backend'
            ],
            
            # Placeholder/TODO comments that should be resolved
            'placeholder_todos': [
                r'# TODO: This should come from the actual layout engine',
                r'# FIXME: Temporary implementation',
                r'# HACK: Quick fix',
                r'# XXX: Remove this'
            ],
            
            # Old API patterns
            'old_api_patterns': [
                r'line_width.*# Should be width',
                r'\.success.*# Old parser API',
                r'parsing_result\.graph.*# Direct return now'
            ]
        }
        
        # Files to completely remove (obsolete validation/test files)
        self.files_to_remove = [
            'diagnose_dau_compliance.py',
            'validate_qt_egif_rendering.py', 
            'validate_enhanced_dau_compliance.py',
            'validate_qt_dau_rendering.py',
            'diagnose_qt_rendering.py',
            'test_enhanced_dau_conventions.py',
            'generate_visual_examples.py'  # Contains deprecated hook_line references
        ]
        
        # Directories to clean
        self.target_directories = [
            'src',
            'tests',
            '.'  # Root level files
        ]
    
    def create_backup(self):
        """Create backup of current state before cleanup."""
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        
        self.backup_dir.mkdir()
        
        # Backup key files that will be modified
        for target_dir in self.target_directories:
            source_dir = self.repo_root / target_dir
            if source_dir.exists() and source_dir.is_dir():
                backup_target = self.backup_dir / target_dir
                shutil.copytree(source_dir, backup_target, dirs_exist_ok=True)
        
        print(f"✅ Created backup in {self.backup_dir}")
    
    def remove_deprecated_files(self):
        """Remove completely obsolete files."""
        removed_files = []
        
        for filename in self.files_to_remove:
            file_path = self.repo_root / filename
            if file_path.exists():
                file_path.unlink()
                removed_files.append(str(file_path))
                self.cleanup_log.append(f"REMOVED FILE: {filename}")
        
        if removed_files:
            print(f"✅ Removed {len(removed_files)} obsolete files")
            for f in removed_files:
                print(f"   • {f}")
        else:
            print("ℹ️  No obsolete files found to remove")
    
    def clean_file_content(self, file_path: Path) -> bool:
        """Clean deprecated patterns from a single file."""
        if not file_path.suffix == '.py':
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except Exception as e:
            print(f"⚠️  Could not read {file_path}: {e}")
            return False
        
        modified_content = original_content
        changes_made = False
        
        # Remove deprecated patterns
        for pattern_category, patterns in self.deprecated_patterns.items():
            for pattern in patterns:
                # Remove lines containing deprecated patterns
                lines = modified_content.split('\n')
                filtered_lines = []
                
                for line in lines:
                    if re.search(pattern, line, re.IGNORECASE):
                        changes_made = True
                        self.cleanup_log.append(f"REMOVED LINE in {file_path.name}: {line.strip()}")
                        # Skip this line (remove it)
                        continue
                    else:
                        filtered_lines.append(line)
                
                modified_content = '\n'.join(filtered_lines)
        
        # Write back if changes were made
        if changes_made:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                return True
            except Exception as e:
                print(f"⚠️  Could not write {file_path}: {e}")
                return False
        
        return False
    
    def clean_directory(self, directory: Path) -> Tuple[int, int]:
        """Clean all Python files in a directory."""
        files_processed = 0
        files_modified = 0
        
        if not directory.exists():
            return files_processed, files_modified
        
        for file_path in directory.rglob('*.py'):
            files_processed += 1
            if self.clean_file_content(file_path):
                files_modified += 1
        
        return files_processed, files_modified
    
    def run_cleanup(self):
        """Run the complete cleanup process."""
        print("🧹 STARTING SYSTEMATIC DEPRECATED CODE CLEANUP")
        print("=" * 60)
        
        # Create backup
        self.create_backup()
        
        # Remove obsolete files
        self.remove_deprecated_files()
        
        # Clean file contents
        total_processed = 0
        total_modified = 0
        
        for target_dir in self.target_directories:
            dir_path = self.repo_root / target_dir
            processed, modified = self.clean_directory(dir_path)
            total_processed += processed
            total_modified += modified
            
            if processed > 0:
                print(f"✅ Cleaned {target_dir}/: {modified}/{processed} files modified")
        
        # Generate cleanup report
        self.generate_report()
        
        print("\n" + "=" * 60)
        print(f"🎯 CLEANUP COMPLETE")
        print(f"   • Files processed: {total_processed}")
        print(f"   • Files modified: {total_modified}")
        print(f"   • Changes logged: {len(self.cleanup_log)}")
        print(f"   • Backup created: {self.backup_dir}")
        print(f"   • Report saved: cleanup_report.txt")
    
    def generate_report(self):
        """Generate detailed cleanup report."""
        report_path = self.repo_root / "cleanup_report.txt"
        
        with open(report_path, 'w') as f:
            f.write("ARISBE DEPRECATED CODE CLEANUP REPORT\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Total changes made: {len(self.cleanup_log)}\n\n")
            
            f.write("DETAILED CHANGES:\n")
            f.write("-" * 20 + "\n")
            for change in self.cleanup_log:
                f.write(f"{change}\n")
            
            f.write(f"\nBackup location: {self.backup_dir}\n")
            f.write("Restore command: cp -r cleanup_backups/* .\n")

def main():
    """Main cleanup execution."""
    if len(sys.argv) > 1:
        repo_root = sys.argv[1]
    else:
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    cleaner = DeprecatedCodeCleaner(repo_root)
    
    # Confirm before proceeding
    print(f"🧹 DEPRECATED CODE CLEANUP")
    print(f"Repository: {repo_root}")
    print(f"This will remove deprecated patterns and obsolete files.")
    print(f"A backup will be created in cleanup_backups/")
    
    response = input("\nProceed with cleanup? (y/N): ").strip().lower()
    if response != 'y':
        print("Cleanup cancelled.")
        return
    
    cleaner.run_cleanup()
    
    print("\n🎯 NEXT STEPS:")
    print("1. Run core pipeline tests: python tests/core_pipeline_tests.py")
    print("2. Verify no regressions in functionality")
    print("3. Commit cleaned codebase")
    print("4. Proceed with disciplined development on clean foundation")

if __name__ == '__main__':
    main()
