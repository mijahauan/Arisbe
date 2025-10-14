#!/usr/bin/env python3
"""
Rebuild corpus index from actual files.

This scans the corpus directories and rebuilds index.json
to reflect the current state of the corpus.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from corpus_service import CorpusService


def rebuild_index(corpus_root: Path):
    """Rebuild corpus index from filesystem."""
    print("=" * 70)
    print("REBUILDING CORPUS INDEX")
    print("=" * 70)
    print()
    
    corpus = CorpusService(corpus_root)
    
    print(f"📂 Corpus root: {corpus_root}")
    print(f"📚 Literature dir: {corpus.literature_dir}")
    print(f"🧠 Universes dir: {corpus.universes_dir}")
    print()
    
    # Clear existing index
    old_count = len(corpus._index.universes)
    print(f"🗑️  Clearing {old_count} old index entries")
    corpus._index.universes = []
    
    # Scan literature directory
    print(f"📖 Scanning literature directory...")
    literature_count = 0
    if corpus.literature_dir.exists():
        for uod_dir in sorted(corpus.literature_dir.iterdir()):
            if not uod_dir.is_dir():
                continue
            
            meta_file = uod_dir / "uod.meta.json"
            if not meta_file.exists():
                print(f"   ⚠️  Skipping {uod_dir.name} (no metadata)")
                continue
            
            # Load directly from filesystem (bypass index lookup)
            try:
                uod = corpus._load_uod_old_format(uod_dir.name, uod_dir)
                if not uod:
                    # Try new format
                    from universe_of_discourse import UoDMetadata
                    from egi_io import load_egi_json
                    import json
                    
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        meta_data = json.load(f)
                        metadata = UoDMetadata.from_dict(meta_data)
                    
                    egi_file = uod_dir / "current.egi.json"
                    if egi_file.exists():
                        from universe_of_discourse import UniverseOfDiscourse
                        current_egi = load_egi_json(str(egi_file))
                        uod = UniverseOfDiscourse(
                            metadata=metadata,
                            current_egi=current_egi,
                            current_layout_deltas=None,
                            history=None
                        )
                
                if uod:
                    corpus._update_index_entry(uod)
                    literature_count += 1
                    print(f"   ✅ Added: {uod_dir.name}")
            except Exception as e:
                print(f"   ❌ Error loading {uod_dir.name}: {e}")
    
    # Scan universes directory
    print(f"🌌 Scanning universes directory...")
    universes_count = 0
    if corpus.universes_dir.exists():
        for uod_dir in sorted(corpus.universes_dir.iterdir()):
            if not uod_dir.is_dir():
                continue
            
            meta_file = uod_dir / "uod.meta.json"
            if not meta_file.exists():
                print(f"   ⚠️  Skipping {uod_dir.name} (no metadata)")
                continue
            
            # Load directly from filesystem (bypass index lookup)
            try:
                from universe_of_discourse import UoDMetadata, UniverseOfDiscourse
                from egi_io import load_egi_json
                import json
                
                with open(meta_file, 'r', encoding='utf-8') as f:
                    meta_data = json.load(f)
                    metadata = UoDMetadata.from_dict(meta_data)
                
                egi_file = uod_dir / "current.egi.json"
                if egi_file.exists():
                    current_egi = load_egi_json(str(egi_file))
                    uod = UniverseOfDiscourse(
                        metadata=metadata,
                        current_egi=current_egi,
                        current_layout_deltas=None,
                        history=None
                    )
                    corpus._update_index_entry(uod)
                    universes_count += 1
                    print(f"   ✅ Added: {uod_dir.name}")
            except Exception as e:
                print(f"   ❌ Error loading {uod_dir.name}: {e}")
    
    # Save index
    corpus._save_index()
    
    print()
    print("=" * 70)
    print("INDEX REBUILT")
    print("=" * 70)
    print(f"📚 Literature: {literature_count}")
    print(f"🌌 Universes: {universes_count}")
    print(f"📊 Total: {literature_count + universes_count}")
    print()
    print(f"✅ Index saved to: {corpus.index_path}")
    print()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Rebuild corpus index from filesystem"
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=Path(__file__).parent.parent / "corpus",
        help="Corpus root directory (default: ../corpus)"
    )
    
    args = parser.parse_args()
    
    rebuild_index(args.corpus)


if __name__ == "__main__":
    main()
