#!/usr/bin/env python3
"""
Rebuild tomos index from actual files.

This scans the tomos directories and rebuilds index.json
to reflect the current state of the tomos.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tomos_service import TomosService


def rebuild_index(tomos_root: Path):
    """Rebuild tomos index from filesystem."""
    print("=" * 70)
    print("REBUILDING TOMOS INDEX")
    print("=" * 70)
    print()
    
    tomos = TomosService(tomos_root)
    
    print(f"📂 Tomos root: {tomos_root}")
    print(f"📚 Literature dir: {tomos.literature_dir}")
    print(f"🧠 Universes dir: {tomos.universes_dir}")
    print()
    
    # Clear existing index
    old_count = len(tomos._index.universes)
    print(f"🗑️  Clearing {old_count} old index entries")
    tomos._index.universes = []
    
    # Scan literature directory
    print(f"📖 Scanning literature directory...")
    literature_count = 0
    if tomos.literature_dir.exists():
        for uod_dir in sorted(tomos.literature_dir.iterdir()):
            if not uod_dir.is_dir():
                continue
            
            meta_file = uod_dir / "uod.meta.json"
            if not meta_file.exists():
                print(f"   ⚠️  Skipping {uod_dir.name} (no metadata)")
                continue
            
            # Load directly from filesystem (bypass index lookup)
            try:
                uod = tomos._load_uod_old_format(uod_dir.name, uod_dir)
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
                    tomos._update_index_entry(uod)
                    literature_count += 1
                    print(f"   ✅ Added: {uod_dir.name}")
            except Exception as e:
                print(f"   ❌ Error loading {uod_dir.name}: {e}")
    
    # Scan universes directory
    print(f"🌌 Scanning universes directory...")
    universes_count = 0
    if tomos.universes_dir.exists():
        for uod_dir in sorted(tomos.universes_dir.iterdir()):
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
                    tomos._update_index_entry(uod)
                    universes_count += 1
                    print(f"   ✅ Added: {uod_dir.name}")
            except Exception as e:
                print(f"   ❌ Error loading {uod_dir.name}: {e}")
    
    # Save index
    tomos._save_index()
    
    print()
    print("=" * 70)
    print("INDEX REBUILT")
    print("=" * 70)
    print(f"📚 Literature: {literature_count}")
    print(f"🌌 Universes: {universes_count}")
    print(f"📊 Total: {literature_count + universes_count}")
    print()
    print(f"✅ Index saved to: {tomos.index_path}")
    print()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Rebuild tomos index from filesystem"
    )
    parser.add_argument(
        "--tomos",
        type=Path,
        default=Path(__file__).parent.parent / "tomos",
        help="Tomos root directory (default: ../tomos)"
    )
    
    args = parser.parse_args()
    
    rebuild_index(args.tomos)


if __name__ == "__main__":
    main()
