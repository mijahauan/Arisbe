#!/usr/bin/env python3
"""
Systematic Cleanup of Obsolete Files

This script safely removes obsolescent, unused, or otherwise irrelevant files
to eliminate contamination of future development with the canonical core established.

SAFETY FEATURES:
- Dry-run mode by default
- Backup creation before deletion
- Validation checks before and after cleanup
- Detailed logging of all actions
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Set
import argparse
from datetime import datetime

# Repository root
REPO_ROOT = Path(__file__).parent.parent

def run_command(cmd: str, cwd: Path = REPO_ROOT) -> tuple[int, str]:
    """Run command and return exit code and output."""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.returncode, result.stdout + result.stderr
    except Exception as e:
        return 1, str(e)

def validate_canonical_core() -> bool:
    """Validate that canonical core tests pass."""
    print("🔍 Validating canonical core before cleanup...")
    
    test_files = [
        "tests/minimal_pipeline_test.py",
        "tests/bidirectional_pipeline_test.py", 
        "tests/canonical_core_validation.py"
    ]
    
    for test_file in test_files:
        test_path = REPO_ROOT / test_file
        if not test_path.exists():
            print(f"❌ Test file missing: {test_file}")
            return False
        
        print(f"  Running {test_file}...")
        exit_code, output = run_command(f"python {test_file}")
        if exit_code != 0:
            print(f"❌ Test failed: {test_file}")
            print(f"Output: {output}")
            return False
        else:
            print(f"  ✅ {test_file} passed")
    
    print("✅ All canonical core tests pass")
    return True

def get_obsolete_files() -> Dict[str, List[str]]:
    """Get categorized list of obsolete files to remove."""
    
    obsolete_files = {
        "debug_analysis_scripts": [
            "analyze_layout_problems.py",
            "analyze_visual_output.py", 
            "apply_bounds_fix.py",
            "debug_containment_bug.py",
            "debug_containment_bugs.py",
            "debug_containment_detailed.py",
            "debug_cut_hierarchy.py",
            "debug_dot_syntax.py",
            "debug_graphviz_integration.py",
            "debug_gui_containment.py",
            "debug_layout_spacing.py",
            "debug_overlap_test.py",
            "debug_predicate_positioning.py",
            "debug_visual_output.py",
            "diagnose_dau_compliance.py",
            "diagnose_qt_rendering.py",
            "fix_containment_positioning.py",
            "fix_graphviz_layout.py",
            "fix_predicate_positioning.py",
            "generate_sample_egif_visuals.py",
            "generate_visual_examples.py",
            "improve_dau_visual_conventions.py",
            "simple_bounds_fix.py",
            "solidify_graphviz_modeling.py"
        ],
        
        "experimental_src_files": [
            "src/audit_roundtrip.py",  # Superseded by canonical tests
            "src/debug_direct_rendering.py",  # Debug tool
            "src/debug_display_pipeline.py",  # Debug tool
            "src/debug_layout_engine.py",  # Debug tool
            "src/debug_rendering_pipeline.py",  # Debug tool
            "src/experimental_layout.py",  # Experimental
            "src/layout_debug.py",  # Debug tool
            "src/layout_engine_old.py",  # Old implementation
            "src/old_diagram_renderer.py",  # Old implementation
            "src/prototype_gui.py",  # Prototype
            "src/test_canvas.py",  # Test file in wrong location
            "src/test_layout.py",  # Test file in wrong location
            "src/validate_qt_egif_rendering.py",  # Validation tool
        ],
        
        "potentially_obsolete_src": [
            # These need evaluation - may contain useful functionality
            "src/arisbe_gui.py",  # Old GUI - check if superseded
            "src/arisbe_gui_integrated.py",  # Experimental - check if superseded
            "src/constraint_layout_engine.py",  # May be superseded by Graphviz
            "src/constraint_layout_integration.py",  # May be superseded
            "src/constraint_layout_prototype.py",  # Prototype
            "src/dau_eg_renderer.py",  # May be superseded
            "src/dau_subgraph_model.py",  # May be superseded
        ]
    }
    
    return obsolete_files

def check_file_references(file_path: str) -> List[str]:
    """Check if file is referenced by canonical implementations."""
    references = []
    
    # Files that should never reference obsolete files
    canonical_files = [
        "src/canonical/__init__.py",
        "src/canonical/contracts.py", 
        "src/egi_core_dau.py",
        "src/egif_parser_dau.py",
        "src/egif_generator_dau.py",
        "src/egdf_parser.py",
        "src/graphviz_layout_engine_v2.py",
        "src/arisbe_gui_standard.py",
        "phase2_gui_foundation.py"
    ]
    
    file_name = Path(file_path).name
    module_name = file_name.replace('.py', '')
    
    for canonical_file in canonical_files:
        canonical_path = REPO_ROOT / canonical_file
        if canonical_path.exists():
            try:
                content = canonical_path.read_text()
                if file_name in content or module_name in content:
                    references.append(canonical_file)
            except Exception:
                pass
    
    return references

def create_backup() -> str:
    """Create backup of repository before cleanup."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"arisbe_backup_before_cleanup_{timestamp}"
    backup_path = REPO_ROOT.parent / backup_name
    
    print(f"📦 Creating backup: {backup_path}")
    try:
        shutil.copytree(REPO_ROOT, backup_path, ignore=shutil.ignore_patterns('.git', '__pycache__', '*.pyc'))
        print(f"✅ Backup created successfully")
        return str(backup_path)
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return ""

def cleanup_files(dry_run: bool = True) -> Dict[str, List[str]]:
    """Clean up obsolete files."""
    obsolete_files = get_obsolete_files()
    cleanup_results = {
        "removed": [],
        "kept_referenced": [],
        "kept_missing": [],
        "errors": []
    }
    
    print(f"🧹 Starting cleanup (dry_run={dry_run})...")
    
    for category, files in obsolete_files.items():
        print(f"\n📂 Processing category: {category}")
        
        for file_path in files:
            full_path = REPO_ROOT / file_path
            
            if not full_path.exists():
                print(f"  ⚠️  File not found: {file_path}")
                cleanup_results["kept_missing"].append(file_path)
                continue
            
            # Check for references in canonical files
            references = check_file_references(file_path)
            if references:
                print(f"  🔗 File referenced by canonical implementations: {file_path}")
                print(f"      Referenced by: {references}")
                cleanup_results["kept_referenced"].append(file_path)
                continue
            
            # Safe to remove
            if dry_run:
                print(f"  🗑️  Would remove: {file_path}")
            else:
                try:
                    full_path.unlink()
                    print(f"  ✅ Removed: {file_path}")
                    cleanup_results["removed"].append(file_path)
                except Exception as e:
                    print(f"  ❌ Error removing {file_path}: {e}")
                    cleanup_results["errors"].append(f"{file_path}: {e}")
    
    return cleanup_results

def main():
    parser = argparse.ArgumentParser(description="Clean up obsolete files from Arisbe repository")
    parser.add_argument("--execute", action="store_true", help="Actually remove files (default is dry-run)")
    parser.add_argument("--skip-validation", action="store_true", help="Skip canonical core validation")
    parser.add_argument("--no-backup", action="store_true", help="Skip backup creation")
    
    args = parser.parse_args()
    
    print("🎯 ARISBE OBSOLETE FILES CLEANUP")
    print("=" * 50)
    
    # Validate canonical core first
    if not args.skip_validation:
        if not validate_canonical_core():
            print("❌ Canonical core validation failed - aborting cleanup")
            return 1
    
    # Create backup if not dry run
    backup_path = ""
    if not args.execute or args.no_backup:
        print("📦 Skipping backup (dry-run mode or --no-backup)")
    else:
        backup_path = create_backup()
        if not backup_path:
            print("❌ Backup creation failed - aborting cleanup")
            return 1
    
    # Perform cleanup
    results = cleanup_files(dry_run=not args.execute)
    
    # Report results
    print("\n📊 CLEANUP RESULTS")
    print("=" * 30)
    print(f"Files removed: {len(results['removed'])}")
    print(f"Files kept (referenced): {len(results['kept_referenced'])}")
    print(f"Files kept (missing): {len(results['kept_missing'])}")
    print(f"Errors: {len(results['errors'])}")
    
    if results['removed']:
        print(f"\n✅ Removed files:")
        for file_path in results['removed']:
            print(f"  - {file_path}")
    
    if results['kept_referenced']:
        print(f"\n🔗 Kept files (referenced by canonical implementations):")
        for file_path in results['kept_referenced']:
            print(f"  - {file_path}")
    
    if results['errors']:
        print(f"\n❌ Errors:")
        for error in results['errors']:
            print(f"  - {error}")
    
    # Validate after cleanup if files were actually removed
    if not args.skip_validation and results['removed']:
        print("\n🔍 Validating canonical core after cleanup...")
        if not validate_canonical_core():
            print("❌ Canonical core validation failed after cleanup!")
            if backup_path:
                print(f"💾 Restore from backup: {backup_path}")
            return 1
        else:
            print("✅ Canonical core still works after cleanup")
    
    if args.execute:
        print(f"\n✅ CLEANUP COMPLETED")
        if backup_path:
            print(f"💾 Backup available at: {backup_path}")
    else:
        print(f"\n🔍 DRY-RUN COMPLETED")
        print("Use --execute to actually remove files")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
