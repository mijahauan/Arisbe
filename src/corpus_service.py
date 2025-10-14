"""
CorpusService - Unified API for Universe of Discourse Corpus Management

This service provides a clean, UoD-centric interface for all corpus operations,
consolidating the previously fragmented systems (corpus_index, entity_storage,
integrated_corpus_manager).

Key Features:
- UoD-centric operations (not graph-centric)
- Support for both static (literature) and dynamic (reasoning) UoDs
- History tracking integration
- Efficient lazy loading
- Migration support from old corpus structure
- Backward compatibility during transition

Architecture:
- Single unified API for all corpus operations
- Delegates to appropriate storage backends
- Abstracts storage details from consumers
- Supports future corpus reorganization

See: UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md for philosophical foundation
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from enum import Enum

from universe_of_discourse import (
    UniverseOfDiscourse,
    UoDMetadata,
    UoDType,
    UoDCategory,
)
from egi_core_dau import RelationalGraphWithCuts
from egi_io import load_egi_json, save_egi_json
import json


class CorpusVersion(Enum):
    """Corpus structure version."""
    LEGACY = "legacy"  # Old corpus/graphs/ structure
    V2 = "v2"          # New corpus/universes/ structure


@dataclass
class CorpusIndex:
    """
    Lightweight index of all UoDs in corpus.
    
    Provides fast browsing without loading full UoDs.
    """
    corpus_name: str
    version: CorpusVersion
    universes: List[Dict]  # Lightweight metadata for each UoD
    last_updated: datetime
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "corpus_name": self.corpus_name,
            "version": self.version.value,
            "universes": self.universes,
            "last_updated": self.last_updated.isoformat(),
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'CorpusIndex':
        """Deserialize from dictionary."""
        # Handle both old and new index formats
        corpus_name = data.get("corpus_name", data.get("name", "Arisbe Corpus"))
        
        # Handle old format (list of entries) vs new format
        universes = data.get("universes", data.get("entries", []))
        
        # Handle missing last_updated
        last_updated_str = data.get("last_updated")
        if last_updated_str:
            last_updated = datetime.fromisoformat(last_updated_str)
        else:
            last_updated = datetime.now()
        
        # Handle version string - default to LEGACY for unknown versions
        version_str = data.get("version", "legacy")
        try:
            version = CorpusVersion(version_str)
        except ValueError:
            # Unknown version (like "0.1"), treat as legacy
            version = CorpusVersion.LEGACY
        
        return CorpusIndex(
            corpus_name=corpus_name,
            version=version,
            universes=universes,
            last_updated=last_updated,
        )


class CorpusService:
    """
    Unified service for Universe of Discourse corpus management.
    
    Provides high-level operations for:
    - Listing and browsing UoDs
    - Loading and saving UoDs
    - Searching and filtering
    - Import/export operations
    - Migration from old corpus structure
    
    Usage:
        corpus = CorpusService(corpus_root)
        
        # List all UoDs
        uods = corpus.list_uods()
        
        # Load specific UoD
        uod = corpus.load_uod("inquiry_001")
        
        # Save UoD (with history)
        corpus.save_uod(uod)
        
        # Search
        results = corpus.search(query="modus ponens", category=UoDCategory.LITERATURE_EXAMPLE)
    """
    
    def __init__(self, corpus_root: Path):
        """
        Initialize CorpusService.
        
        Args:
            corpus_root: Root directory of corpus (e.g., "corpus/")
        """
        self.corpus_root = Path(corpus_root)
        self.corpus_root.mkdir(parents=True, exist_ok=True)
        
        # Paths
        self.index_path = self.corpus_root / "index.json"
        self.universes_dir = self.corpus_root / "universes"
        self.literature_dir = self.corpus_root / "literature"
        self.legacy_graphs_dir = self.corpus_root / "graphs"
        
        # Create directories
        self.universes_dir.mkdir(exist_ok=True)
        self.literature_dir.mkdir(exist_ok=True)
        
        # Load or create index
        self._index: Optional[CorpusIndex] = None
        self._load_index()
    
    # ===== Index Management =====
    
    def _load_index(self):
        """Load corpus index from disk."""
        if self.index_path.exists():
            with open(self.index_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._index = CorpusIndex.from_dict(data)
        else:
            # Create new index
            self._index = CorpusIndex(
                corpus_name="Arisbe Corpus",
                version=CorpusVersion.V2,
                universes=[],
                last_updated=datetime.now()
            )
            self._save_index()
    
    def _save_index(self):
        """Save corpus index to disk."""
        self._index.last_updated = datetime.now()
        with open(self.index_path, 'w', encoding='utf-8') as f:
            json.dump(self._index.to_dict(), f, indent=2)
    
    def _update_index_entry(self, uod: UniverseOfDiscourse):
        """Update or add entry in index for given UoD."""
        # Remove old entry if exists
        self._index.universes = [
            u for u in self._index.universes 
            if u.get("uod_id") != uod.uod_id
        ]
        
        # Add new entry
        entry = {
            "uod_id": uod.uod_id,
            "name": uod.name,
            "category": uod.category.value,
            "uod_type": uod.uod_type.value,
            "is_static": uod.is_static,
            "is_dynamic": uod.is_dynamic,
            "created": uod.metadata.created.isoformat(),
            "last_modified": uod.metadata.last_modified.isoformat(),
            "total_states": uod.metadata.total_states,
            "total_transformations": uod.metadata.total_transformations,
            "authors": uod.metadata.authors,
            "tags": list(uod.metadata.tags),
            "path": str(self._get_uod_path(uod)),
        }
        
        self._index.universes.append(entry)
        self._save_index()
    
    # ===== Path Management =====
    
    def _get_uod_path(self, uod: UniverseOfDiscourse) -> Path:
        """Get storage path for UoD."""
        if uod.is_static:
            return self.literature_dir / uod.uod_id
        else:
            return self.universes_dir / uod.uod_id
    
    def _get_uod_files(self, uod_path: Path) -> Dict[str, Path]:
        """Get file paths for UoD storage."""
        return {
            "meta": uod_path / "uod.meta.json",
            "current_egi": uod_path / "current.egi.json",
            "current_deltas": uod_path / "current.deltas.json",
            "history_dir": uod_path / "history",
            "history_log": uod_path / "history" / "history.jsonl",
            "snapshots_dir": uod_path / "history" / "snapshots",
            "linear_forms_dir": uod_path / "linear_forms",
            "exports_dir": uod_path / "exports",
        }
    
    # ===== Core Operations =====
    
    def _normalize_entry(self, entry: Dict) -> Dict:
        """
        Normalize old corpus format to new format.
        
        Old format: id, title, category, path
        New format: uod_id, name, category, is_static, is_dynamic, path
        """
        # If already has uod_id, assume it's new format
        if "uod_id" in entry:
            return entry
        
        # Translate old format to new format
        normalized = {
            "uod_id": entry.get("id", entry.get("uod_id", "unknown")),
            "name": entry.get("title", entry.get("name", "Untitled")),
            "category": entry.get("category", "literature"),
            "path": entry.get("path", ""),
            # For old corpus, everything is static literature
            "is_static": True,
            "is_dynamic": False,
            "uod_type": "standalone",
            "created": entry.get("updated", entry.get("created", "")),
            "last_modified": entry.get("updated", entry.get("last_modified", "")),
            "authors": entry.get("authors", []),
            "tags": entry.get("tags", []),
        }
        
        return normalized
    
    def list_uods(
        self,
        category: Optional[UoDCategory] = None,
        is_static: Optional[bool] = None,
        is_dynamic: Optional[bool] = None,
    ) -> List[Dict]:
        """
        List all UoDs in corpus.
        
        Args:
            category: Filter by category (optional)
            is_static: Filter by static (literature) UoDs (optional)
            is_dynamic: Filter by dynamic (reasoning) UoDs (optional)
            
        Returns:
            List of lightweight UoD metadata dicts
        """
        # Normalize all entries to new format
        results = [self._normalize_entry(u) for u in self._index.universes]
        
        if category is not None:
            results = [u for u in results if u.get("category") == category.value]
        
        if is_static is not None:
            results = [u for u in results if u.get("is_static") == is_static]
        
        if is_dynamic is not None:
            results = [u for u in results if u.get("is_dynamic") == is_dynamic]
        
        return results
    
    def get_uod_metadata(self, uod_id: str) -> Optional[Dict]:
        """
        Get lightweight metadata for UoD without loading full UoD.
        
        Args:
            uod_id: UoD identifier
            
        Returns:
            Metadata dict or None if not found
        """
        for entry in self._index.universes:
            # Normalize entry first
            normalized = self._normalize_entry(entry)
            # Check both old "id" and new "uod_id"
            if normalized.get("uod_id") == uod_id or entry.get("id") == uod_id:
                return normalized
        return None
    
    def uod_exists(self, uod_id: str) -> bool:
        """Check if UoD exists in corpus."""
        return self.get_uod_metadata(uod_id) is not None
    
    def _load_uod_old_format(self, uod_id: str, uod_path: Path) -> Optional[UniverseOfDiscourse]:
        """
        Load UoD from old corpus format.
        
        Old format:
        - {uod_id}.meta.json
        - {uod_id}.egi.json
        - {uod_id}.json (full entity data)
        """
        from datetime import datetime
        
        # Try to find meta file
        meta_file = uod_path / f"{uod_id}.meta.json"
        egi_file = uod_path / f"{uod_id}.egi.json"
        
        if not meta_file.exists() or not egi_file.exists():
            return None
        
        # Load metadata
        with open(meta_file, 'r', encoding='utf-8') as f:
            old_meta = json.load(f)
        
        # Convert old metadata to new UoDMetadata
        created = old_meta.get("created", "")
        last_modified = old_meta.get("last_modified", "")
        
        # Parse dates
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
            "peirce": UoDCategory.LITERATURE,
            "literature": UoDCategory.LITERATURE,
            None: UoDCategory.LITERATURE,
        }
        category = category_map.get(old_category, UoDCategory.LITERATURE)
        
        metadata = UoDMetadata(
            uod_id=uod_id,
            uod_type=UoDType.STANDALONE,
            name=old_meta.get("name", uod_id),
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
        
        # Create UoD (no history for old format)
        uod = UniverseOfDiscourse(
            metadata=metadata,
            current_egi=current_egi,
            current_layout_deltas=None,
            history=None
        )
        
        return uod
    
    def load_uod(
        self,
        uod_id: str,
        load_history: bool = True
    ) -> Optional[UniverseOfDiscourse]:
        """
        Load UoD from corpus.
        
        Handles both old and new corpus formats.
        
        Args:
            uod_id: UoD identifier
            load_history: If True, load full history (default: True)
            
        Returns:
            UniverseOfDiscourse or None if not found
        """
        entry = self.get_uod_metadata(uod_id)
        if entry is None:
            return None
        
        uod_path = Path(entry["path"])
        if not uod_path.exists():
            return None
        
        # Check if this is old or new format
        files = self._get_uod_files(uod_path)
        
        # If new format files don't exist, try old format
        if not files["meta"].exists():
            return self._load_uod_old_format(uod_id, uod_path)
        
        # Load from new format
        with open(files["meta"], 'r', encoding='utf-8') as f:
            meta_data = json.load(f)
            metadata = UoDMetadata.from_dict(meta_data)
        
        # Load current EGI
        if not files["current_egi"].exists():
            return None
        
        current_egi = load_egi_json(files["current_egi"])
        
        # Load current deltas if exists
        current_deltas = None
        if files["current_deltas"].exists():
            with open(files["current_deltas"], 'r', encoding='utf-8') as f:
                current_deltas = json.load(f)
        
        # Load history if requested and exists
        history = None
        if load_history and metadata.uod_type == UoDType.HISTORICAL:
            if files["history_log"].exists():
                # TODO: Implement history loading from JSONL
                # For now, history will be None
                pass
        
        # Create UoD
        uod = UniverseOfDiscourse(
            metadata=metadata,
            current_egi=current_egi,
            current_layout_deltas=current_deltas,
            history=history
        )
        
        return uod
    
    def save_uod(self, uod: UniverseOfDiscourse):
        """
        Save UoD to corpus.
        
        Saves:
        - Metadata
        - Current EGI
        - Current layout deltas
        - History (if historical)
        
        Args:
            uod: UniverseOfDiscourse to save
        """
        uod_path = self._get_uod_path(uod)
        uod_path.mkdir(parents=True, exist_ok=True)
        
        files = self._get_uod_files(uod_path)
        
        # Create subdirectories
        if uod.is_historical:
            files["history_dir"].mkdir(exist_ok=True)
            files["snapshots_dir"].mkdir(exist_ok=True)
        files["linear_forms_dir"].mkdir(exist_ok=True)
        files["exports_dir"].mkdir(exist_ok=True)
        
        # Save metadata
        with open(files["meta"], 'w', encoding='utf-8') as f:
            json.dump(uod.metadata.to_dict(), f, indent=2)
        
        # Save current EGI
        save_egi_json(uod.current_egi, files["current_egi"])
        
        # Save current deltas
        if uod.current_layout_deltas:
            with open(files["current_deltas"], 'w', encoding='utf-8') as f:
                json.dump(uod.current_layout_deltas, f, indent=2)
        
        # Save history if exists
        if uod.is_historical and uod.history is not None:
            # TODO: Implement history saving to JSONL
            # For now, just save marker file
            with open(files["history_log"], 'w', encoding='utf-8') as f:
                f.write(f"# History for {uod.uod_id}\n")
        
        # Update index
        self._update_index_entry(uod)
    
    def delete_uod(self, uod_id: str) -> bool:
        """
        Delete UoD from corpus.
        
        Args:
            uod_id: UoD identifier
            
        Returns:
            True if deleted, False if not found
        """
        entry = self.get_uod_metadata(uod_id)
        if entry is None:
            return False
        
        uod_path = Path(entry["path"])
        if uod_path.exists():
            import shutil
            shutil.rmtree(uod_path)
        
        # Remove from index
        self._index.universes = [
            u for u in self._index.universes 
            if u.get("uod_id") != uod_id
        ]
        self._save_index()
        
        return True
    
    # ===== Search and Filter =====
    
    def search(
        self,
        query: Optional[str] = None,
        category: Optional[UoDCategory] = None,
        tags: Optional[Set[str]] = None,
        author: Optional[str] = None,
    ) -> List[Dict]:
        """
        Search UoDs in corpus.
        
        Args:
            query: Search in name and description (optional)
            category: Filter by category (optional)
            tags: Filter by tags (any match) (optional)
            author: Filter by author (optional)
            
        Returns:
            List of matching UoD metadata dicts
        """
        results = self._index.universes
        
        if category is not None:
            results = [u for u in results if u.get("category") == category.value]
        
        if tags is not None:
            results = [
                u for u in results 
                if any(t in u.get("tags", []) for t in tags)
            ]
        
        if author is not None:
            results = [
                u for u in results 
                if author in u.get("authors", [])
            ]
        
        if query is not None:
            query_lower = query.lower()
            results = [
                u for u in results 
                if query_lower in u.get("name", "").lower()
            ]
        
        return results
    
    # ===== Import/Export =====
    
    def import_literature(
        self,
        egi: RelationalGraphWithCuts,
        name: str,
        source_citation: str,
        authors: Optional[List[str]] = None,
        tags: Optional[Set[str]] = None,
    ) -> UniverseOfDiscourse:
        """
        Import literature example as static UoD.
        
        Args:
            egi: EGI to import
            name: Name of example
            source_citation: Citation (e.g., "Peirce CP 4.394")
            authors: Authors (optional)
            tags: Tags (optional)
            
        Returns:
            Created UniverseOfDiscourse
        """
        import uuid
        
        uod_id = f"lit_{uuid.uuid4().hex[:8]}"
        
        metadata = UoDMetadata(
            uod_id=uod_id,
            uod_type=UoDType.STANDALONE,
            name=name,
            description=f"Literature example from {source_citation}",
            category=UoDCategory.LITERATURE_EXAMPLE,
            created=datetime.now(),
            last_modified=datetime.now(),
            source_citation=source_citation,
            authors=authors or [],
            tags=tags or set(),
        )
        
        uod = UniverseOfDiscourse(
            metadata=metadata,
            current_egi=egi,
            history=None
        )
        
        self.save_uod(uod)
        
        return uod
    
    # ===== Migration Support =====
    
    def migrate_from_legacy(self):
        """
        Migrate UoDs from legacy corpus/graphs/ structure to new structure.
        
        This is a one-time migration operation.
        """
        if not self.legacy_graphs_dir.exists():
            return
        
        # Load legacy index
        legacy_index_path = self.legacy_graphs_dir.parent / "index.json"
        if not legacy_index_path.exists():
            return
        
        with open(legacy_index_path, 'r', encoding='utf-8') as f:
            legacy_index = json.load(f)
        
        migrated_count = 0
        
        for entry in legacy_index.get("entries", []):
            try:
                # Load from legacy location
                from entity_storage import EntityStorageManager
                legacy_storage = EntityStorageManager(self.legacy_graphs_dir)
                entity = legacy_storage.load_entity(entry["id"])
                
                # entity is already a UniverseOfDiscourse (via alias)
                # Just save to new location
                self.save_uod(entity)
                
                migrated_count += 1
                print(f"✅ Migrated: {entity.name}")
                
            except Exception as e:
                print(f"❌ Failed to migrate {entry['id']}: {e}")
        
        print(f"\n✅ Migration complete: {migrated_count} UoDs migrated")
    
    # ===== Statistics =====
    
    def get_statistics(self) -> Dict:
        """
        Get corpus statistics.
        
        Returns:
            Dictionary with statistics
        """
        total = len(self._index.universes)
        static = len([u for u in self._index.universes if u.get("is_static")])
        dynamic = len([u for u in self._index.universes if u.get("is_dynamic")])
        
        categories = {}
        for u in self._index.universes:
            cat = u.get("category", "unknown")
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_uods": total,
            "static_uods": static,
            "dynamic_uods": dynamic,
            "by_category": categories,
            "corpus_version": self._index.version.value,
            "last_updated": self._index.last_updated.isoformat(),
        }
