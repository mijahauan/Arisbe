"""
TomosService - Unified API for Universe of Discourse Tomos Management

This service provides a clean, UoD-centric interface for all tomos operations,
consolidating the previously fragmented systems (corpus_index, entity_storage,
integrated_corpus_manager).

Key Features:
- UoD-centric operations (not graph-centric)
- Support for both static (literature) and dynamic (reasoning) UoDs
- History tracking integration
- Efficient lazy loading
- Migration support from old tomos structure
- Backward compatibility during transition

Architecture:
- Single unified API for all tomos operations
- Delegates to appropriate storage backends
- Abstracts storage details from consumers
- Supports future tomos reorganization

See: UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md for philosophical foundation
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from enum import Enum

from universe_of_discourse import (
    UniverseOfDiscourse,
    UoDMetadata,
    UoDType,
    UoDCategory,
)
from correspondence_attestation import attest_correspondence
from egi_core_dau import RelationalGraphWithCuts
from egi_io import load_egi_json, save_egi_json
from elk_layout_engine import ELKLayoutEngine
from style_loader import load_default_style
import json


# ---------------------------------------------------------------------------
# Chain model — V1 persistence of a Peircean reasoning chain.
# ---------------------------------------------------------------------------
#
# In Peircean terms, every assertion resides in a context.  A workshop
# session is a chain of rule applications anchored at a base state; each
# step's logical force comes from its parent state plus its place in the
# chain.  These dataclasses are the slim on-disk shape of that chain —
# the diachronic record that turns a single snapshot into an asserted
# reasoning process.
#
# This is intentionally NOT a hydration of ``EGITransformationHistory``
# (which is protected and whose ``add_transformation`` API is designed
# for live application, not disk hydration).  V1 keeps the chain
# external to the UoD; later phases may extend the protected model.
#
# See ``docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md`` §4.2 and
# ``docs/UNIVERSE_OF_DISCOURSE_ARCHITECTURE.md`` for the conceptual
# grounding.

CHAIN_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class ChainStep:
    """One rule application in a transformation chain.

    Each step names the rule, the parent state it was applied against
    (``from_state_id``), the resulting state (``to_state_id``), and the
    rule-specific parameters that produced the move.  ``parameters`` is
    a free-form JSON dict whose shape varies by rule (e.g. ERA gets a
    selected_elements list, INS gets an egif_content string).
    """

    step_id: str
    rule_name: str
    from_state_id: str
    to_state_id: str
    parameters: Dict[str, Any]
    timestamp: str
    user_annotation: Optional[str] = None


@dataclass
class TransformationChain:
    """A linear chain of rule applications anchored at an initial state.

    The chain is the unit of meaning for a Peircean reasoning episode:
    each step's force is conferred by its parent state plus the chain's
    accumulated context.  V1 supports only linear (non-branching)
    chains; the JSONL format leaves room for ``branch_id`` later.

    Attributes:
        initial_state_id: ID of the base state — the context against
            which the chain's first step was applied.
        steps: Ordered list of rule applications.  An empty list is
            valid (a chain with no steps is just a base state).
        states: All EGI snapshots referenced by the chain, keyed by
            state_id.  Includes ``initial_state_id`` and every step's
            ``from_state_id`` / ``to_state_id``.
    """

    initial_state_id: str
    steps: List[ChainStep]
    states: Dict[str, RelationalGraphWithCuts]

    @property
    def initial_egi(self) -> RelationalGraphWithCuts:
        return self.states[self.initial_state_id]

    @property
    def current_state_id(self) -> str:
        return self.steps[-1].to_state_id if self.steps else self.initial_state_id

    @property
    def current_egi(self) -> RelationalGraphWithCuts:
        return self.states[self.current_state_id]


def _attest_uod_in_correspondence(
    uod: "UniverseOfDiscourse", context: str
) -> None:
    """Render the UoD's current EGI and attest §3.3 correspondence.

    Called at the tomos save/load boundary events named in
    ``docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md`` §6: "Save to tomos
    corpus — the graph becomes a persistent record; correspondence
    must hold from this point" and "Load from corpus — the loaded
    graph's drawing must correspond to its stored EGI".

    The function is a no-op for UoDs whose ``current_egi`` is None
    (empty / freshly-created UoDs that hold no claim yet).  For
    everything else, it instantiates the canonical layout path
    (``ELKLayoutEngine`` + default style), renders the EGI, and runs
    the full §3.3 check via ``attest_correspondence``.  A failure
    raises ``CorrespondenceViolation`` with the supplied context label.

    ``context`` should describe the boundary event — e.g.
    ``"tomos_service.save_uod(my-uod)"`` — so post-mortems can name
    which boundary refused.
    """
    if uod.current_egi is None:
        return
    engine = ELKLayoutEngine()
    style = load_default_style()
    dto = engine.generate_layout(uod.current_egi, style)
    attest_correspondence(uod.current_egi, dto, context=context)


class TomosVersion(Enum):
    """Tomos structure version."""
    LEGACY = "legacy"  # Old tomos/graphs/ structure
    V2 = "v2"          # New tomos/universes/ structure


@dataclass
class TomosIndex:
    """
    Lightweight index of all UoDs in tomos.
    
    Provides fast browsing without loading full UoDs.
    """
    tomos_name: str
    version: TomosVersion
    universes: List[Dict]  # Lightweight metadata for each UoD
    last_updated: datetime
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "tomos_name": self.tomos_name,
            "version": self.version.value,
            "universes": self.universes,
            "last_updated": self.last_updated.isoformat(),
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'TomosIndex':
        """Deserialize from dictionary."""
        # Handle both old and new index formats (corpus_name → tomos_name)
        tomos_name = data.get("tomos_name", data.get("corpus_name", data.get("name", "Arisbe Tomos")))
        
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
            version = TomosVersion(version_str)
        except ValueError:
            # Unknown version (like "0.1"), treat as legacy
            version = TomosVersion.LEGACY
        
        return TomosIndex(
            tomos_name=tomos_name,
            version=version,
            universes=universes,
            last_updated=last_updated,
        )


class TomosService:
    """
    Unified service for Universe of Discourse tomos management.
    
    Provides high-level operations for:
    - Listing and browsing UoDs
    - Loading and saving UoDs
    - Searching and filtering
    - Import/export operations
    - Migration from old tomos structure
    
    Usage:
        tomos = TomosService(tomos_root)
        
        # List all UoDs
        uods = tomos.list_uods()
        
        # Load specific UoD
        uod = tomos.load_uod("inquiry_001")
        
        # Save UoD (with history)
        tomos.save_uod(uod)
        
        # Search
        results = tomos.search(query="modus ponens", category=UoDCategory.LITERATURE_EXAMPLE)
    """
    
    def __init__(self, tomos_root: Path):
        """
        Initialize TomosService.
        
        Args:
            tomos_root: Root directory of tomos (e.g., "tomos/")
        """
        self.tomos_root = Path(tomos_root)
        self.tomos_root.mkdir(parents=True, exist_ok=True)
        
        # Paths
        self.index_path = self.tomos_root / "index.json"
        self.universes_dir = self.tomos_root / "universes"
        self.literature_dir = self.tomos_root / "literature"
        self.legacy_graphs_dir = self.tomos_root / "graphs"
        
        # Create directories
        self.universes_dir.mkdir(exist_ok=True)
        self.literature_dir.mkdir(exist_ok=True)
        
        # Load or create index
        self._index: Optional[TomosIndex] = None
        self._load_index()
    
    # ===== Index Management =====
    
    def _load_index(self):
        """Load tomos index from disk."""
        if self.index_path.exists():
            with open(self.index_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._index = TomosIndex.from_dict(data)
        else:
            # Create new index
            self._index = TomosIndex(
                tomos_name="Arisbe Tomos",
                version=TomosVersion.V2,
                universes=[],
                last_updated=datetime.now()
            )
            self._save_index()
    
    def _save_index(self):
        """Save tomos index to disk."""
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
        """Convert a legacy index entry to the current V2 index-entry schema.

        The legacy format (pre-V2) used different field names and assumed all
        UoDs were static literature examples:

            Legacy fields  →  V2 fields
            id             →  uod_id
            title          →  name
            updated        →  created / last_modified
            (none)         →  is_static = True, is_dynamic = False,
                               uod_type = "standalone"

        If the entry already contains ``uod_id`` it is returned unchanged
        (idempotent).

        Args:
            entry: Raw dict from the index file (either legacy or V2 format).

        Returns:
            A dict conforming to the V2 index-entry schema with all required
            fields present.
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
            # For old tomos format, everything is static literature
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
        List all UoDs in tomos.
        
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
        """Check if UoD exists in tomos."""
        return self.get_uod_metadata(uod_id) is not None
    
    def _load_uod_old_format(self, uod_id: str, uod_path: Path) -> Optional[UniverseOfDiscourse]:
        """Load a UoD stored in the pre-V2 (legacy) flat-file format.

        The legacy format placed two files directly inside the UoD directory:

            {uod_id}.meta.json  — metadata (name, description, dates, category …)
            {uod_id}.egi.json   — the serialised RelationalGraphWithCuts

        An optional ``{uod_id}.json`` full-entity file was also written by the
        old ``EntityStorageManager`` but is not read here.

        Conversion performed:
            - ``created`` / ``last_modified`` ISO strings are parsed to
              ``datetime`` objects (falling back to ``datetime.now()`` on parse
              error).
            - The legacy ``category`` string (e.g. ``"peirce"`` or
              ``"literature"``) is mapped to the corresponding
              ``UoDCategory`` enum value via a hard-coded lookup; unknown
              values default to ``UoDCategory.LITERATURE_EXAMPLE``.
            - History is not present in the legacy format; the returned UoD
              has ``history=None``.

        Args:
            uod_id: The UoD identifier string.
            uod_path: Directory containing the legacy files.

        Returns:
            A ``UniverseOfDiscourse`` built from the legacy files, or ``None``
            if the expected files do not exist.
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
            "peirce": UoDCategory.LITERATURE_EXAMPLE,
            "literature": UoDCategory.LITERATURE_EXAMPLE,
            None: UoDCategory.LITERATURE_EXAMPLE,
        }
        category = category_map.get(old_category, UoDCategory.LITERATURE_EXAMPLE)
        
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
        load_history: bool = True,
        attest: bool = True,
    ) -> Optional[UniverseOfDiscourse]:
        """Load a UoD from tomos, transparently handling both legacy and V2 formats.

        Format detection:
            - If the UoD directory does not contain a ``uod.meta.json`` file
              (the V2 metadata filename), loading is delegated to
              ``_load_uod_old_format`` which reads ``{uod_id}.meta.json`` and
              ``{uod_id}.egi.json`` instead.
            - V2 UoDs are loaded from ``uod.meta.json``, ``current.egi.json``,
              and optionally ``current.deltas.json`` for layout overrides.

        History loading:
            History is only loaded when ``load_history=True`` **and** the UoD
            type is ``UoDType.HISTORICAL``.  The JSONL history log is not yet
            implemented (marked TODO); the returned ``history`` attribute will
            be ``None`` until that feature is complete.

        Args:
            uod_id: The UoD identifier to load.
            load_history: Whether to attempt loading transformation history.
                Defaults to ``True``; set to ``False`` for faster browsing
                when history is not needed.
            attest: Whether to run the §3.3 correspondence attestation (a full
                layout of the stored EGI) at the load boundary.  Defaults to
                ``True`` — the boundary guarantee for any caller that will *draw*
                the graph.  Set to ``False`` when the UoD is read purely as
                **data** (an ontology used as a model M for materialization /
                the semantic game / the theory query, which never draws M — the
                "M is data, draw only the contested fragment" principle,
                ``docs/DOMAIN_ORACLE_AND_M.md`` §5).  A large ontology's layout is
                super-linear, so attesting it per query would make using it as M
                unusably slow; the drawing was already attested at save time.

        Returns:
            The loaded ``UniverseOfDiscourse``, or ``None`` if the UoD is not
            in the index or its directory does not exist on disk.
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

        # Boundary-event attestation: the loaded graph's drawing must
        # correspond to its stored EGI
        # (docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md §6).  Catches drift
        # introduced by external edits to the persisted file or by
        # layout-engine changes since the file was written.  Skipped when the
        # caller reads the UoD purely as data (attest=False) — M is never drawn.
        if attest:
            _attest_uod_in_correspondence(
                uod, context=f"tomos_service.load_uod({uod_id})"
            )

        return uod

    def save_uod(self, uod: UniverseOfDiscourse):
        """Persist a UoD to disk in V2 format and update the tomos index.

        Files written under ``<universes_dir|literature_dir>/{uod.uod_id}/``:

            uod.meta.json           — ``UoDMetadata`` serialised to JSON
            current.egi.json        — current ``RelationalGraphWithCuts``
            current.deltas.json     — layout position overrides (optional;
                                       only written when
                                       ``uod.current_layout_deltas`` is set)
            history/history.jsonl   — transformation history placeholder
                                       (written only for HISTORICAL UoDs;
                                       full JSONL serialisation is TODO)

        The UoD is routed to ``literature_dir`` for static UoDs and to
        ``universes_dir`` for dynamic ones, as determined by ``_get_uod_path``.
        The ``index.json`` file is updated (or the entry created) after each
        successful save.

        Args:
            uod: The ``UniverseOfDiscourse`` to save.  Must have a valid
                ``uod_id`` and a non-``None`` ``current_egi``.

        Raises:
            Any IO error raised by the filesystem (propagates unhandled).
            ``CorrespondenceViolation`` (from
            ``correspondence_attestation``) if the UoD's current EGI
            cannot be rendered into a §3.3-compliant drawing.  Save is
            aborted before any files are written; the tomos corpus is
            never left with a graph it can't render in correspondence.
        """
        # Boundary-event attestation: the graph is about to become a
        # persistent record claimed to mean something definite
        # (docs/LINEAR_GRAPHICAL_CORRESPONDENCE.md §4.2, §6).  Attest
        # before any disk writes so the corpus never reaches a
        # half-saved drifted state.
        _attest_uod_in_correspondence(
            uod, context=f"tomos_service.save_uod({uod.uod_id})"
        )

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

    # ===== Chain persistence (Peircean reasoning chains) =====

    def save_uod_with_chain(
        self,
        uod: UniverseOfDiscourse,
        chain: TransformationChain,
        presentation_deltas: Optional[Dict[str, List[dict]]] = None,
        provenance: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Persist a UoD together with its transformation chain.

        Calls ``save_uod`` first — which runs §3.3 attestation on the
        UoD's current EGI and aborts before any disk writes if
        correspondence fails.  Only after that succeeds are the chain
        artefacts written, so the corpus never contains a chain whose
        tail state could not be attested.

        Files written under ``<uod_path>/history/`` (in addition to
        whatever ``save_uod`` writes at the UoD root):

            chain.jsonl              — initial-state header + one JSON
                                       object per ``ChainStep``
            states/<state_id>.egi.json — per-state EGI snapshots, one
                                       per state referenced by the chain
            deltas.json              — {state_id: [delta-dict, …]} regime-3
                                       presentation deltas per state (written
                                       only when non-empty)

        Args:
            uod: UoD to save.  Its ``current_egi`` should equal
                ``chain.current_egi`` (the caller's responsibility — V1
                does not enforce this beyond §3.3 attestation, which
                would catch a drifted final state at save_uod).
            chain: The transformation chain to persist alongside.
            presentation_deltas: Optional already-serialized regime-3 deltas
                (``{state_id: [delta-dict]}``) to persist beside the chain so
                a corpus UoD reopened in the workshop keeps its appearance.
                The symmetric read is ``load_chain_deltas``.
            provenance: Optional already-serialized provenance bundle (from
                ``provenance.Provenance.to_dict``) — the typed theorem /
                EG-derivation / calculus source layers + per-layer warrant.
                This is the doorway-union: a worked proof imports as a chain
                that *carries* its low-warrant attribution.  Written to
                ``<uod_path>/provenance.json``; read back via ``load_provenance``.

        Raises:
            ``CorrespondenceViolation`` (from ``save_uod``) if the
            final-state §3.3 check fails.  In that case no chain files
            are written.
        """
        # Final-state attestation happens inside save_uod *before* any
        # writes.  If it raises, we never reach the chain-write block —
        # so a refusal aborts cleanly with no half-saved chain on disk.
        self.save_uod(uod)

        uod_path = self._get_uod_path(uod)
        history_dir = uod_path / "history"
        states_dir = history_dir / "states"
        history_dir.mkdir(parents=True, exist_ok=True)
        states_dir.mkdir(parents=True, exist_ok=True)

        # Write every state snapshot referenced by the chain.  Includes
        # the initial state (the context against which step 1 was
        # applied) and every from_state / to_state of every step.
        for state_id, state_egi in chain.states.items():
            snap_path = states_dir / f"{state_id}.egi.json"
            save_egi_json(state_egi, snap_path)

        # Write the JSONL log.  First line is the initial-state header;
        # subsequent lines are step records in chain order.
        chain_jsonl = history_dir / "chain.jsonl"
        with open(chain_jsonl, "w", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "type": "initial",
                        "initial_state_id": chain.initial_state_id,
                        "schema_version": CHAIN_SCHEMA_VERSION,
                    }
                )
                + "\n"
            )
            for step in chain.steps:
                f.write(
                    json.dumps(
                        {
                            "type": "step",
                            "step_id": step.step_id,
                            "rule_name": step.rule_name,
                            "from_state_id": step.from_state_id,
                            "to_state_id": step.to_state_id,
                            "parameters": step.parameters,
                            "timestamp": step.timestamp,
                            "user_annotation": step.user_annotation,
                        }
                    )
                    + "\n"
                )

        # Per-state regime-3 presentation deltas (sparse; only nudged states
        # appear).  Written only when non-empty; an overwriting save clears a
        # stale file so a UoD never keeps deltas it no longer has.
        deltas_path = history_dir / "deltas.json"
        pruned = {k: v for k, v in (presentation_deltas or {}).items() if v}
        if pruned:
            with open(deltas_path, "w", encoding="utf-8") as f:
                json.dump(pruned, f, indent=2)
        elif deltas_path.exists():
            deltas_path.unlink()

        # Provenance bundle (UoD-root side-file, like bibliography.json) — the
        # doorway-union: the chain carries its typed, low-warrant attribution.
        self.save_provenance(uod, provenance or {})

    def load_chain_deltas(self, uod_id: str) -> Dict[str, List[dict]]:
        """Load the per-state regime-3 deltas persisted beside a UoD's chain.

        Returns ``{state_id: [delta-dict]}`` (serialized form, deserialized by
        the caller via ``presentation_deltas.deltas_from_list``), or an empty
        dict if the UoD is unknown or carries no ``history/deltas.json``.  The
        symmetric write is ``save_uod_with_chain``'s ``presentation_deltas``.
        """
        entry = self.get_uod_metadata(uod_id)
        if entry is None:
            return {}
        deltas_path = Path(entry["path"]) / "history" / "deltas.json"
        if not deltas_path.exists():
            return {}
        try:
            with open(deltas_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            return loaded if isinstance(loaded, dict) else {}
        except (json.JSONDecodeError, OSError):
            return {}

    def load_chain(self, uod_id: str) -> Optional[TransformationChain]:
        """Load the transformation chain persisted alongside a UoD.

        Returns ``None`` if the UoD is not in the index, has no
        ``history/chain.jsonl``, or the chain file references a state
        whose snapshot file is missing (a broken chain — we refuse to
        return a half-loaded one).

        Args:
            uod_id: UoD identifier.

        Returns:
            The parsed ``TransformationChain``, or ``None``.
        """
        entry = self.get_uod_metadata(uod_id)
        if entry is None:
            return None

        uod_path = Path(entry["path"])
        chain_jsonl = uod_path / "history" / "chain.jsonl"
        states_dir = uod_path / "history" / "states"

        if not chain_jsonl.exists() or not states_dir.exists():
            return None

        initial_state_id: Optional[str] = None
        steps: List[ChainStep] = []

        with open(chain_jsonl, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                obj_type = obj.get("type")
                if obj_type == "initial":
                    initial_state_id = obj["initial_state_id"]
                elif obj_type == "step":
                    steps.append(
                        ChainStep(
                            step_id=obj["step_id"],
                            rule_name=obj["rule_name"],
                            from_state_id=obj["from_state_id"],
                            to_state_id=obj["to_state_id"],
                            parameters=obj.get("parameters", {}),
                            timestamp=obj["timestamp"],
                            user_annotation=obj.get("user_annotation"),
                        )
                    )

        if initial_state_id is None:
            return None

        # Gather every state_id referenced by the chain and load the
        # snapshot file for each.  A missing snapshot means the chain
        # is broken — refuse to return a partial chain.
        needed: Set[str] = {initial_state_id}
        for step in steps:
            needed.add(step.from_state_id)
            needed.add(step.to_state_id)

        states: Dict[str, RelationalGraphWithCuts] = {}
        for sid in needed:
            snap_path = states_dir / f"{sid}.egi.json"
            if not snap_path.exists():
                return None
            states[sid] = load_egi_json(snap_path)

        return TransformationChain(
            initial_state_id=initial_state_id,
            steps=steps,
            states=states,
        )

    # ===== Bibliographic provenance (imports) =====

    def save_bibliography(
        self,
        uod: UniverseOfDiscourse,
        record: Dict[str, Any],
        formatted: str,
    ) -> None:
        """Persist a structured bibliographic record beside a UoD.

        For corpus imports, the provenance is the trace of the un-hosted
        dialogue the linear form came from (see
        ``docs/MANIFEST_AND_MEANING.md``).  The structured ``record``
        (CSL-compatible) is kept so the citation can be re-styled later;
        ``formatted`` is the human-readable string also stored in the
        UoD metadata's ``source_citation``.

        Written to ``<uod_path>/bibliography.json``.  Call after
        ``save_uod`` (so the UoD directory exists).
        """
        uod_path = self._get_uod_path(uod)
        uod_path.mkdir(parents=True, exist_ok=True)
        biblio_path = uod_path / "bibliography.json"
        with open(biblio_path, "w", encoding="utf-8") as f:
            json.dump({"record": record, "formatted": formatted}, f, indent=2)

    def load_bibliography(self, uod_id: str) -> Optional[Dict[str, Any]]:
        """Load the bibliographic record for a UoD, or ``None`` if absent.

        Returns ``{"record": {...}, "formatted": "..."}``.
        """
        entry = self.get_uod_metadata(uod_id)
        if entry is None:
            return None
        biblio_path = Path(entry["path"]) / "bibliography.json"
        if not biblio_path.exists():
            return None
        try:
            with open(biblio_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    # ===== Annotation layer (marginalia about a UoD / chain / step / element) =====

    def save_annotations(
        self, uod: UniverseOfDiscourse, annotations: List[Dict[str, Any]]
    ) -> None:
        """Persist the annotation layer beside a UoD.

        Annotations are *marginalia about* the reasoning, not part of it — a
        side layer that rides alongside the UoD exactly as ``bibliography.json``
        and ``history/deltas.json`` do, and like them is **outside §3.3** (a
        comment is not a sign in the graph, so the correspondence chord does not
        answer for it; this method runs no attestation).  See
        ``src/annotations.py`` and ``docs/ORGANON_IMPORT_WALKTHROUGH.md`` §3.

        ``annotations`` is the already-serialized list (from
        ``annotations.annotations_to_list``).  Written to
        ``<uod_path>/annotations.json`` as ``{"annotations": [...]}`` only when
        non-empty; an overwriting save with an empty list clears a stale file so
        a UoD never keeps annotations it no longer has (same discipline as the
        per-state deltas).  Call after ``save_uod`` (so the directory exists).
        """
        uod_path = self._get_uod_path(uod)
        uod_path.mkdir(parents=True, exist_ok=True)
        ann_path = uod_path / "annotations.json"
        if annotations:
            with open(ann_path, "w", encoding="utf-8") as f:
                json.dump({"annotations": annotations}, f, indent=2)
        elif ann_path.exists():
            ann_path.unlink()

    def load_annotations(self, uod_id: str) -> List[Dict[str, Any]]:
        """Load the annotation layer for a UoD, or ``[]`` if absent.

        Returns the serialized list of annotation dicts (rehydrated by the
        caller via ``annotations.annotations_from_list``).  The symmetric write
        is ``save_annotations``.
        """
        entry = self.get_uod_metadata(uod_id)
        if entry is None:
            return []
        ann_path = Path(entry["path"]) / "annotations.json"
        if not ann_path.exists():
            return []
        try:
            with open(ann_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            items = loaded.get("annotations") if isinstance(loaded, dict) else None
            return items if isinstance(items, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    # ===== Provenance bundle (typed multi-layer attribution for a proof) =====

    def save_provenance(
        self, uod: UniverseOfDiscourse, provenance: Dict[str, Any]
    ) -> None:
        """Persist a provenance bundle beside a UoD.

        The bundle (``src/provenance.py``) carries the *theorem* / *EG-derivation*
        / *calculus* source layers — which do not share a source — plus a
        per-layer warrant and a transcribed-vs-authored-here flag.  It is the
        proof-chain analogue of the single-CSL ``bibliography.json`` and, like it,
        is **outside §3.3** (it describes the source, it is not a sign in the
        graph; no attestation runs here).  Written to
        ``<uod_path>/provenance.json``; an empty/falsy bundle clears a stale file.
        Call after ``save_uod`` (so the directory exists).
        """
        uod_path = self._get_uod_path(uod)
        uod_path.mkdir(parents=True, exist_ok=True)
        prov_path = uod_path / "provenance.json"
        if provenance:
            with open(prov_path, "w", encoding="utf-8") as f:
                json.dump(provenance, f, indent=2)
        elif prov_path.exists():
            prov_path.unlink()

    def load_provenance(self, uod_id: str) -> Optional[Dict[str, Any]]:
        """Load the provenance bundle for a UoD, or ``None`` if absent.

        Returns the serialized bundle (rehydrated by the caller via
        ``provenance.Provenance.from_dict``).  Symmetric write: ``save_provenance``.
        """
        entry = self.get_uod_metadata(uod_id)
        if entry is None:
            return None
        prov_path = Path(entry["path"]) / "provenance.json"
        if not prov_path.exists():
            return None
        try:
            with open(prov_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            return loaded if isinstance(loaded, dict) else None
        except (json.JSONDecodeError, OSError):
            return None

    def delete_uod(self, uod_id: str) -> bool:
        """
        Delete UoD from tomos.
        
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
        """Search the tomos index and return matching lightweight UoD metadata dicts.

        Filters are applied in order: category → tags → author → query.
        All filters are optional; calling with no arguments returns the full
        (un-normalised) index.

        Note: the ``query`` filter currently matches only against the ``name``
        field (case-insensitive substring match); description search is not
        yet implemented.

        Note: unlike ``list_uods``, this method does *not* normalise legacy
        entries before filtering.  If the index contains legacy entries their
        field names may differ from the V2 schema.

        Args:
            query: Case-insensitive substring matched against the UoD ``name``
                field.  ``None`` skips this filter.
            category: Return only UoDs whose ``category`` value matches this
                ``UoDCategory``.  ``None`` skips this filter.
            tags: Return UoDs that have *any* of the specified tags in their
                ``tags`` list.  ``None`` skips this filter.
            author: Return only UoDs that list this author string in their
                ``authors`` list.  ``None`` skips this filter.

        Returns:
            List of raw index-entry dicts (not normalised) that satisfy all
            supplied filters.
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
        """Migrate UoDs from the legacy ``tomos/graphs/`` structure to the V2 structure.

        This is a one-time operation.  After migration the legacy ``graphs/``
        directory can be archived; the new ``universes/`` and ``literature/``
        directories take over.

        Legacy layout (pre-V2):
            tomos/
              index.json          ← flat list under key "entries" (not "universes")
              graphs/
                {id}.meta.json
                {id}.egi.json

        V2 layout (post-migration):
            tomos/
              index.json          ← key "universes", version "v2"
              universes/{id}/     ← dynamic UoDs
              literature/{id}/    ← static literature UoDs
                uod.meta.json
                current.egi.json

        Each legacy entity is loaded via ``EntityStorageManager`` (which
        understands the flat-file format) and then re-saved with ``save_uod``
        which writes the V2 directory structure and updates the index.
        """
        if not self.legacy_graphs_dir.exists():
            return

        # The legacy index lives one level above the graphs/ subdirectory
        legacy_index_path = self.legacy_graphs_dir.parent / "index.json"
        if not legacy_index_path.exists():
            return

        with open(legacy_index_path, 'r', encoding='utf-8') as f:
            legacy_index = json.load(f)

        migrated_count = 0

        # Legacy index uses "entries" key; V2 index uses "universes"
        for entry in legacy_index.get("entries", []):
            try:
                # EntityStorageManager reads the flat {id}.meta.json + {id}.egi.json
                # files and returns a UniverseOfDiscourse (previously called "entity")
                from entity_storage import EntityStorageManager
                legacy_storage = EntityStorageManager(self.legacy_graphs_dir)
                entity = legacy_storage.load_entity(entry["id"])

                # save_uod writes V2 directory layout and updates index.json
                self.save_uod(entity)

                migrated_count += 1
                print(f"✅ Migrated: {entity.name}")

            except Exception as e:
                print(f"❌ Failed to migrate {entry['id']}: {e}")

        print(f"\n✅ Migration complete: {migrated_count} UoDs migrated")
    
    # ===== Statistics =====
    
    def get_statistics(self) -> Dict:
        """
        Get tomos statistics.
        
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
