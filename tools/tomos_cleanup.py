#!/usr/bin/env python3
"""
Arisbe Tomos Cleanup Script

Removes low-quality entries from the tomos based on the audit report:
- Test/debug entries
- Auto-harvested fragments with corrupted content
- Malformed or incomplete entries

Updates the tomos index.json to reflect removals.
"""

import argparse
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

# Entries to remove based on audit
ENTRIES_TO_REMOVE = [
    # Test/debug entries
    "test",
    # Common Logic harvests (corrupted)
    "harvest_Common_Logic_final_extracted_egif",
    "harvest_Common_Logic_final_extracted_egif_1",
    "harvest_Common_Logic_final_extracted_egif_2",
    "harvest_Common_Logic_final_extracted_egif_3",
    "harvest_Common_Logic_final_extracted_egif_4",
    "harvest_Common_Logic_final_extracted_egif_5",
    "harvest_Common_Logic_final_extracted_egif_6",
    "harvest_Common_Logic_final_extracted_egif_7",
    "harvest_Common_Logic_final_extracted_egif_8",
    # EGIF-Sowa harvests (auto-generated fragments)
    "harvest_EGIF-Sowa_extracted_egif",
    "harvest_EGIF-Sowa_extracted_egif_1",
    "harvest_EGIF-Sowa_extracted_egif_2",
    "harvest_EGIF-Sowa_extracted_egif_3",
    "harvest_EGIF-Sowa_extracted_egif_4",
    "harvest_EGIF-Sowa_extracted_egif_5",
    "harvest_EGIF-Sowa_extracted_egif_6",
    "harvest_EGIF-Sowa_extracted_egif_7",
    "harvest_EGIF-Sowa_extracted_egif_8",
    "harvest_EGIF-Sowa_extracted_egif_9",
    "harvest_EGIF-Sowa_extracted_egif_10",
    "harvest_EGIF-Sowa_extracted_egif_11",
    "harvest_EGIF-Sowa_extracted_egif_12",
    "harvest_EGIF-Sowa_summary_egif",
    "harvest_EGIF-Sowa_summary_egif_1",
    "harvest_EGIF-Sowa_summary_egif_2",
    "harvest_EGIF-Sowa_summary_egif_3",
    "harvest_EGIF-Sowa_summary_egif_4",
    "harvest_EGIF-Sowa_summary_egif_5",
    "harvest_EGIF-Sowa_summary_egif_6",
    "harvest_EGIF-Sowa_summary_egif_7",
    "harvest_EGIF-Sowa_summary_egif_8",
    "harvest_EGIF-Sowa_summary_egif_9",
    # Other harvests (fragmented)
    "harvest_Existential_Graphs_of_Peirce_extracted_egif",
    "harvest_Existential_Graphs_of_Peirce_extracted_egif_1",
    "harvest_Existential_Graphs_of_Peirce_extracted_egif_2",
    "harvest_Existential_Graphs_of_Peirce_extracted_egif_3",
    "harvest_mathematical_logic_with_diagrams_extracted_egif",
    "harvest_mathematical_logic_with_diagrams_extracted_egif_1",
    "harvest_mathematical_logic_with_diagrams_extracted_egif_2",
]


def backup_corpus(corpus_dir: Path, backup_dir: Path):
    """Create a backup of the current tomos before cleanup."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"corpus_backup_{timestamp}"

    print(f"Creating backup at: {backup_path}")
    shutil.copytree(corpus_dir, backup_path)
    return backup_path


def load_corpus_index(index_path: Path) -> dict:
    """Load the tomos index.json file."""
    with open(index_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_corpus_index(index_path: Path, index_data: dict):
    """Save the updated tomos index.json file."""
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)


def remove_entry_directory(graphs_dir: Path, entry_id: str) -> bool:
    """Remove an entry's directory from the tomos."""
    entry_path = graphs_dir / entry_id
    if entry_path.exists():
        print(f"  Removing directory: {entry_path}")
        shutil.rmtree(entry_path)
        return True
    else:
        print(f"  Warning: Directory not found: {entry_path}")
        return False


def cleanup_corpus(corpus_dir: Path, dry_run: bool = False):
    """Main cleanup function."""
    index_path = corpus_dir / "index.json"
    graphs_dir = corpus_dir / "graphs"

    if not index_path.exists():
        raise FileNotFoundError(f"Tomos index not found: {index_path}")

    # Load current index
    print("Loading tomos index...")
    index_data = load_corpus_index(index_path)
    original_count = len(index_data["entries"])

    # Filter out entries to remove
    print(f"\nOriginal corpus: {original_count} entries")
    print(f"Entries to remove: {len(ENTRIES_TO_REMOVE)}")

    removed_entries = []
    kept_entries = []

    for entry in index_data["entries"]:
        if entry["id"] in ENTRIES_TO_REMOVE:
            removed_entries.append(entry)
            if not dry_run:
                remove_entry_directory(graphs_dir, entry["id"])
        else:
            kept_entries.append(entry)

    # Update index with kept entries only
    index_data["entries"] = kept_entries
    final_count = len(kept_entries)

    print(f"\nCleanup Summary:")
    print(f"  Removed: {len(removed_entries)} entries")
    print(f"  Retained: {final_count} entries")
    print(f"  Quality improvement: {final_count/original_count:.1%} retention rate")

    # Show removed entries
    print(f"\nRemoved entries:")
    for entry in removed_entries:
        category = entry.get("category", "uncategorized")
        print(f"  - {entry['id']} ({category})")

    # Save updated index
    if not dry_run:
        print(f"\nUpdating tomos index...")
        save_corpus_index(index_path, index_data)
        print("Cleanup completed successfully!")
    else:
        print(f"\nDry run completed - no changes made")

    return removed_entries, kept_entries


def main():
    parser = argparse.ArgumentParser(description="Clean up Arisbe corpus")
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        default=Path(__file__).parent.parent / "corpus",
        help="Path to tomos directory",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=Path(__file__).parent.parent / "corpus_backups",
        help="Path to backup directory",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without making changes",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating backup (not recommended)",
    )

    args = parser.parse_args()

    corpus_dir = args.corpus_dir.resolve()
    backup_dir = args.backup_dir.resolve()

    if not corpus_dir.exists():
        print(f"Error: Tomos directory not found: {corpus_dir}")
        return 1

    print(f"Arisbe Tomos Cleanup")
    print(f"Tomos directory: {corpus_dir}")
    print(f"Backup directory: {backup_dir}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE CLEANUP'}")

    try:
        # Create backup unless skipped or dry run
        if not args.dry_run and not args.no_backup:
            backup_dir.mkdir(exist_ok=True)
            backup_path = backup_corpus(corpus_dir, backup_dir)
            print(f"Backup created: {backup_path}")

        # Perform cleanup
        removed, kept = cleanup_corpus(corpus_dir, dry_run=args.dry_run)

        if not args.dry_run:
            print(f"\nTomos cleanup completed!")
            print(f"Next steps:")
            print(f"1. Review retained entries for attribution needs")
            print(f"2. Add proper citations and metadata")
            print(f"3. Validate entries against current EGI system")

        return 0

    except Exception as e:
        print(f"Error during cleanup: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
