#!/usr/bin/env python3
"""
Migrate old tomos format to new UoD format.

Old format (corpus/graphs/{id}/):
- {id}.meta.json
- {id}.egi.json
- {id}.json

New format (corpus/literature/{id}/ or corpus/universes/{id}/):
- uod.meta.json
- current.egi.json
- current.deltas.json (optional)
- history/ (optional)

This migration preserves all data while restructuring for the new UoD model.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tomos_service import TomosService
from universe_of_discourse import UniverseOfDiscourse, UoDMetadata, UoDType, UoDCategory
from egi_io import load_egi_json


def migrate_corpus(tomos_root: Path, dry_run: bool = False):
    """
    Migrate old tomos to new UoD format.
    
    Args:
        tomos_root: Root directory of corpus
        dry_run: If True, only report what would be migrated
    """
    print("=" * 70)
    print("CORPUS MIGRATION TO UOD FORMAT")
    print("=" * 70)
    print()
    
    # Locate old corpus
    old_graphs_dir = tomos_root / "graphs"
    if not old_graphs_dir.exists():
        print(f"❌ Old tomos not found at: {old_graphs_dir}")
        return
    
    # Get all graph directories
    graph_dirs = [d for d in old_graphs_dir.iterdir() if d.is_dir()]
    
    print(f"📊 Found {len(graph_dirs)} graphs in old corpus")
    print()
    
    if dry_run:
        print("🔍 DRY RUN - No changes will be made")
        print()
    
    # Initialize TomosService for new format
    tomos = TomosService(tomos_root)
    
    migrated_count = 0
    skipped_count = 0
    error_count = 0
    
    for graph_dir in sorted(graph_dirs):
        graph_id = graph_dir.name
        
        try:
            print(f"📦 Processing: {graph_id}")
            
            # Load old format files
            meta_file = graph_dir / f"{graph_id}.meta.json"
            egi_file = graph_dir / f"{graph_id}.egi.json"
            
            if not meta_file.exists():
                print(f"   ⚠️  No metadata file, skipping")
                skipped_count += 1
                continue
            
            if not egi_file.exists():
                print(f"   ⚠️  No EGI file, skipping")
                skipped_count += 1
                continue
            
            # Load old metadata
            with open(meta_file, 'r', encoding='utf-8') as f:
                old_meta = json.load(f)
            
            # Parse dates
            created = old_meta.get("created", "")
            last_modified = old_meta.get("last_modified", "")
            
            try:
                created_dt = datetime.fromisoformat(created) if created else datetime.now()
            except:
                created_dt = datetime.now()
            
            try:
                modified_dt = datetime.fromisoformat(last_modified) if last_modified else datetime.now()
            except:
                modified_dt = datetime.now()
            
            # Map old category to new category
            old_category = old_meta.get("category", "literature")
            category_map = {
                "peirce": UoDCategory.LITERATURE_EXAMPLE,
                "literature": UoDCategory.LITERATURE_EXAMPLE,
                "test": UoDCategory.PRACTICE_SESSION,
                None: UoDCategory.LITERATURE_EXAMPLE,
            }
            category = category_map.get(old_category, UoDCategory.LITERATURE_EXAMPLE)
            
            # Create new metadata
            metadata = UoDMetadata(
                uod_id=graph_id,
                uod_type=UoDType.STANDALONE,
                name=old_meta.get("name", graph_id),
                description=old_meta.get("description", ""),
                category=category,
                created=created_dt,
                last_modified=modified_dt,
                authors=old_meta.get("authors", []),
                tags=set(old_meta.get("tags", [])),
                source_citation=old_meta.get("source_citation"),
                total_states=old_meta.get("total_states", 1),
                total_transformations=old_meta.get("total_transformations", 0),
            )
            
            # Load EGI
            current_egi = load_egi_json(str(egi_file))
            
            # Create UoD
            uod = UniverseOfDiscourse(
                metadata=metadata,
                current_egi=current_egi,
                current_layout_deltas=None,
                history=None
            )
            
            print(f"   ✅ Converted to UoD")
            print(f"      Name: {uod.name}")
            print(f"      Category: {uod.category.value}")
            print(f"      Type: {uod.uod_type.value}")
            print(f"      EGI: {len(uod.current_egi.V)}V, {len(uod.current_egi.E)}E, {len(uod.current_egi.Cut)}C")
            
            if not dry_run:
                # Save in new format
                tomos.save_uod(uod)
                print(f"   💾 Saved to new format")
            
            migrated_count += 1
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            error_count += 1
        
        print()
    
    # Summary
    print("=" * 70)
    print("MIGRATION SUMMARY")
    print("=" * 70)
    print(f"✅ Migrated: {migrated_count}")
    print(f"⚠️  Skipped: {skipped_count}")
    print(f"❌ Errors: {error_count}")
    print(f"📊 Total: {len(graph_dirs)}")
    print()
    
    if dry_run:
        print("🔍 This was a DRY RUN - no changes were made")
        print("   Run without --dry-run to perform migration")
    else:
        print("✅ Migration complete!")
        print()
        print("New tomos structure:")
        print(f"   Literature: {corpus.literature_dir}")
        print(f"   Dynamic: {corpus.universes_dir}")
        print()
        print("You can now delete the old corpus/graphs/ directory if desired.")
    
    print()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Migrate old tomos to new UoD format"
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=Path(__file__).parent.parent / "corpus",
        help="Tomos root directory (default: ../corpus)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview migration without making changes"
    )
    
    args = parser.parse_args()
    
    migrate_corpus(args.corpus, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
