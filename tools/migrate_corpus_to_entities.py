"""
Migrate existing corpus graphs to entity format.

Adds .meta.json files to existing .egi.json files.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import uuid
from datetime import datetime

from graph_entity import EntityCategory, EntityMetadata, EntityType
from entity_storage import EntityStorageManager
from egi_io import load_egi_json


# Heuristic category assignment based on name
def guess_category(name: str) -> EntityCategory:
    """Guess category from entity name."""
    name_lower = name.lower()
    
    if "peirce" in name_lower:
        return EntityCategory.PEIRCE
    elif "roberts" in name_lower or "sowa" in name_lower or "dau" in name_lower:
        return EntityCategory.SCHOLARS
    elif "canonical" in name_lower or "test" in name_lower:
        return EntityCategory.CANONICAL
    elif "epg" in name_lower or "game" in name_lower:
        return EntityCategory.EPG
    elif "theorem" in name_lower or "proof" in name_lower:
        return EntityCategory.THEOREM_PROVING
    elif "domain" in name_lower:
        return EntityCategory.DOMAIN_MODELING
    else:
        return EntityCategory.USER_CREATED


# Heuristic description generation
def generate_description(name: str) -> str:
    """Generate description from name."""
    # Convert snake_case to title
    words = name.replace("_", " ").split()
    return " ".join(word.capitalize() for word in words)


def migrate_corpus(corpus_root: Path, dry_run: bool = False):
    """
    Migrate existing corpus to entity format.
    
    Args:
        corpus_root: Root corpus directory
        dry_run: If True, just report what would be done
    """
    migrated = 0
    skipped = 0
    errors = []
    
    print(f"📂 Scanning corpus: {corpus_root}")
    print()
    
    # Find all .egi.json files
    for egi_file in corpus_root.rglob("*.egi.json"):
        # Remove .egi.json to get entity name
        # e.g., "peirce_cp_4_394_man_mortal.egi.json" -> "peirce_cp_4_394_man_mortal"
        entity_name = egi_file.name.replace(".egi.json", "")
        entity_dir = egi_file.parent
        
        # Check if already migrated
        meta_file = entity_dir / f"{entity_name}.meta.json"
        if meta_file.exists():
            print(f"⏭️  Skipping {entity_name} (already has metadata)")
            skipped += 1
            continue
        
        try:
            print(f"🔄 Migrating {entity_name}...")
            
            # Load EGI to get stats
            egi = load_egi_json(egi_file)
            
            # Guess category
            category = guess_category(entity_name)
            
            # Generate description
            description = generate_description(entity_name)
            
            # Get file timestamps
            stat = egi_file.stat()
            created = datetime.fromtimestamp(stat.st_birthtime if hasattr(stat, 'st_birthtime') else stat.st_ctime)
            modified = datetime.fromtimestamp(stat.st_mtime)
            
            # Create metadata
            metadata = EntityMetadata(
                entity_id=f"entity_{uuid.uuid4().hex[:8]}",
                entity_type=EntityType.STANDALONE,
                name=entity_name,
                description=description,
                category=category,
                created=created,
                last_modified=modified,
                corpus_path=entity_dir,
            )
            
            if dry_run:
                print(f"   Would create: {meta_file}")
                print(f"   Category: {category.value}")
                print(f"   Description: {description}")
            else:
                # Save metadata
                import json
                with open(meta_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata.to_dict(), f, indent=2, ensure_ascii=False)
                print(f"   ✅ Created {meta_file.name}")
                print(f"   Category: {category.value}")
            
            migrated += 1
            
        except Exception as e:
            error_msg = f"Failed to migrate {entity_name}: {e}"
            print(f"   ❌ {error_msg}")
            errors.append(error_msg)
    
    print()
    print("=" * 60)
    print("Migration Summary:")
    print(f"  ✅ Migrated: {migrated}")
    print(f"  ⏭️  Skipped: {skipped}")
    print(f"  ❌ Errors: {len(errors)}")
    
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
    
    return migrated, skipped, errors


def main():
    """Run migration."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate corpus to entity format")
    parser.add_argument(
        "--corpus",
        type=Path,
        default=Path(__file__).parent.parent / "corpus" / "graphs",
        help="Corpus root directory"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually doing it"
    )
    
    args = parser.parse_args()
    
    if not args.corpus.exists():
        print(f"❌ Corpus directory not found: {args.corpus}")
        return 1
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
        print()
    
    migrated, skipped, errors = migrate_corpus(args.corpus, args.dry_run)
    
    if errors:
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
