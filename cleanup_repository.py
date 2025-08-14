#!/usr/bin/env python3
"""
Repository Cleanup Script for Arisbe EG Works

This script implements the comprehensive cleanup plan to remove obsolete files,
archive analysis documents, and organize the repository for production readiness.

Run with: python cleanup_repository.py --dry-run (to preview)
Run with: python cleanup_repository.py --execute (to actually clean)
"""

import os
import shutil
import argparse
from pathlib import Path

def setup_archive_structure():
    """Create archive directory structure."""
    archive_dirs = [
        "attic",
        "attic/analysis", 
        "attic/experimental",
        "attic/reports",
        "attic/test_files",
        "attic/debug_files"
    ]
    
    for dir_path in archive_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {dir_path}")

def get_files_to_delete():
    """Get list of files to delete."""
    files_to_delete = [
        # Root directory test/debug files
        "test_annotations.py",
        "test_api_containment_contracts.py", 
        "test_area_aware_egdf.py",
        "test_area_manager.py",
        "test_cgal_installation.py",
        "test_containment_fix.py",
        "test_corpus_loading.py",
        "test_dau_canonical.py",
        "test_dau_compliant_egdf_pipeline.py",
        "test_dau_convention_validation.py",
        "test_dual_format_support.py",
        "test_egdf_sanity.py",
        "test_enhanced_dau_conventions.py",
        "test_enhanced_gui_direct.py",
        "test_fixes_verification.py",
        "test_foundation.py",
        "test_full_dot_output.py",
        "test_graphviz_api_contracts.py",
        "test_gui_baseline.py",
        "test_hover_detection.py",
        "test_improved_layout.py",
        "test_phase1d_api_contracts.py",
        "test_position_correction.py",
        "test_position_correction_simple.py",
        "test_proper_eg_rendering.py",
        "test_qt_fixes.py",
        "test_shapely_installation.py",
        "test_standalone_loi.py",
        "test_variable_names_dau.py",
        "test_visual_rendering.py",
        "test_visual_selection.py",
        
        # Debug files
        "debug_hover_issue.py",
        "debug_layout_structure.py", 
        "debug_ligature_rendering.py",
        "debug_loves_vertices.py",
        "debug_visual_elements.py",
        "debug_zero_vertex.py",
        
        # Validation files
        "validate_corrected_dau_conventions.py",
        "validate_enhanced_dau_compliance.py",
        "validate_qt_dau_rendering.py",
        "validate_qt_egif_rendering.py",
        "validate_visual_output.py",
        "visual_compliance_audit.py",
        
        # Other obsolete files
        "api_contract_review.py",
        "phase2_gui_foundation.py",
        "trace_graphviz_build_order.py",
        
        # Debug output files
        "debug_dot_1.dot",
        "debug_dot_2.dot", 
        "debug_dot_3.dot",
        "debug_loves.txt",
        "debug_output.txt",
        "minimal_test.dot",
        
        # Test output images
        "test_binary_final_fix.png",
        "test_binary_fix.png",
        "test_render_1_simple_relation.png",
        "test_render_2_sibling_cuts.png",
        "test_render_3_nested_cuts.png",
        "test_render_4_binary_relation.png",
        
        # Obsolete main files
        "arisbe_eg_works.py",  # Replaced by arisbe_eg_clean.py
    ]
    
    return files_to_delete

def get_src_files_to_delete():
    """Get list of src/ files to delete."""
    src_files_to_delete = [
        # Test files in src/
        "src/test_basic_drawing.py",
        "src/test_clean_architecture.py",
        "src/test_clean_layout.py",
        "src/test_complete_pipeline.py",
        "src/test_constraint_layout_integration.py",
        "src/test_constraint_replacement_comprehensive.py",
        "src/test_constraint_simple.py",
        "src/test_egif_variety.py",
        "src/test_enhanced_graphviz_layout.py",
        "src/test_enhanced_layout_simple.py",
        "src/test_parser_fix.py",
        "src/test_predicate_rendering.py",
        "src/test_pyside6_direct_integration.py",
        "src/test_pyside6_egif_suite.py",
        "src/test_pyside6_integration.py",
        "src/test_pyside6_simple.py",
        "src/test_rendering_comprehensive.py",
        "src/test_roundtrip_comprehensive.py",
        "src/test_visual_corrected_pipeline.py",
        "src/test_visual_enhanced_layout.py",
        "src/test_xdot_integration.py",
        
        # Debug files in src/
        "src/debug_graphviz_output.py",
        "src/debug_layout_output.py",
        "src/debug_qt_simple.py",
        "src/debug_warmup_integration.py",
        
        # Demo files in src/
        "src/demo_clean_architecture.py",
        "src/demo_constraint_canvas.py",
        "src/demo_constraint_qt.py",
        "src/demo_constraint_web.py",
        "src/demo_phase2_concepts.py",
        "src/demo_phase2_enhanced.py",
        "src/demo_phase2_selection.py",
        "src/demo_phase2_simple.py",
        "src/demo_phase3_validation.py",
        "src/demo_visual_drawing.py",
        
        # Obsolete implementations
        "src/arisbe_gui_standard.py",  # Replaced by arisbe_eg_clean.py
        "src/layout_engine_clean.py",  # Duplicate of layout_engine.py
        "src/diagram_canvas.py",
        "src/diagram_controller.py",
        "src/diagram_controller_corrected.py",
        "src/diagram_controller_enhanced.py",
        "src/diagram_demo.py",
        "src/diagram_renderer_dau.py",
        
        # Experimental/unused components
        "src/background_validation_system.py",
        "src/content_driven_layout.py",
        "src/dual_mode_layout_engine.py",
        "src/eg_transformation_engine.py",
        "src/eg_transformation_rules.py",
        "src/enhanced_diagram_controller.py",
        "src/enhanced_selection_system.py",
        "src/interaction_controller.py",
        "src/mode_aware_selection.py",
        "src/selection_system.py",
        "src/selection_system_enhanced.py",
        "src/warmup_mode_controller.py",
        
        # Enhanced/corrected versions
        "src/egi_diagram_controller.py",
        "src/interactive_canvas.py",
        "src/layout_post_processor.py",
        "src/primary_visual_renderer.py",
        "src/qt_diagram_canvas.py",
        "src/renderer_minimal_dau.py",
        "src/visual_elements_primary.py",
    ]
    
    return src_files_to_delete

def get_files_to_archive():
    """Get list of files to archive."""
    files_to_archive = [
        # Analysis documents
        ("dau_compliance_analysis.md", "attic/analysis/"),
        ("dau_transformation_schema.md", "attic/analysis/"),
        ("dau_yaml_system_documentation.md", "attic/analysis/"),
        ("frontend_assessment.md", "attic/analysis/"),
        ("Front_End_description.md", "attic/analysis/"),
        ("todo.md", "attic/analysis/"),
        
        # Output directories
        ("out_cli_demo/", "attic/reports/"),
        ("out_logical_baseline/", "attic/reports/"),
        ("test_egdf_output/", "attic/test_files/"),
        ("test_gui_debug/", "attic/test_files/"),
        ("reports/", "attic/"),
    ]
    
    return files_to_archive

def cleanup_repository(dry_run=True):
    """Execute repository cleanup."""
    print("🧹 ARISBE REPOSITORY CLEANUP")
    print("=" * 50)
    
    if dry_run:
        print("🔍 DRY RUN MODE - No files will be modified")
    else:
        print("⚠️  EXECUTION MODE - Files will be deleted/moved")
    
    print()
    
    # Setup archive structure
    if not dry_run:
        setup_archive_structure()
    
    # Delete obsolete files
    files_to_delete = get_files_to_delete() + get_src_files_to_delete()
    
    print(f"📁 Files to DELETE: {len(files_to_delete)}")
    for file_path in files_to_delete:
        if os.path.exists(file_path):
            print(f"  🗑️  {file_path}")
            if not dry_run:
                os.remove(file_path)
        else:
            print(f"  ⚠️  {file_path} (not found)")
    
    print()
    
    # Archive files
    files_to_archive = get_files_to_archive()
    
    print(f"📦 Files to ARCHIVE: {len(files_to_archive)}")
    for source, dest_dir in files_to_archive:
        if os.path.exists(source):
            dest_path = os.path.join(dest_dir, os.path.basename(source))
            print(f"  📦 {source} → {dest_path}")
            if not dry_run:
                if os.path.isdir(source):
                    shutil.copytree(source, dest_path, dirs_exist_ok=True)
                    shutil.rmtree(source)
                else:
                    shutil.copy2(source, dest_path)
                    os.remove(source)
        else:
            print(f"  ⚠️  {source} (not found)")
    
    print()
    
    # Summary
    if dry_run:
        print("✅ DRY RUN COMPLETE - Run with --execute to perform cleanup")
    else:
        print("✅ REPOSITORY CLEANUP COMPLETE")
        print("📁 Core files preserved:")
        print("  - arisbe_eg_clean.py (main application)")
        print("  - src/canonical/ (canonical API)")
        print("  - src/egi_core_dau.py (EGI data structures)")
        print("  - src/egdf_dau_canonical.py (EGDF generation)")
        print("  - src/egif_parser_dau.py (EGIF parser)")
        print("  - src/egif_generator_dau.py (EGIF generator)")
        print("  - src/egdf_parser.py (EGDF parser with JSON/YAML)")
        print("  - src/dau_yaml_serializer.py (YAML serialization)")
        print("  - src/corpus_egif_generator.py (corpus utilities)")
        print("  - src/xdot_parser_simple.py (Graphviz integration)")
        print("  - corpus/ (examples)")
        print("  - requirements.txt, setup.py, LICENSE")

def main():
    parser = argparse.ArgumentParser(description="Clean up Arisbe repository")
    parser.add_argument("--dry-run", action="store_true", default=True,
                       help="Preview changes without executing (default)")
    parser.add_argument("--execute", action="store_true", 
                       help="Actually perform the cleanup")
    
    args = parser.parse_args()
    
    # If --execute is specified, turn off dry_run
    if args.execute:
        args.dry_run = False
    
    cleanup_repository(dry_run=args.dry_run)

if __name__ == "__main__":
    main()
