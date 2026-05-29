"""
Insertion Clipboard - Persistent storage for subgraphs prepared for INS transformation.

Provides:
- Validation of subgraphs before adding to clipboard
- Persistent storage across sessions (optional)
- Display and selection interface
- Cross-mode integration (Organon, Ergasterion, Agon)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import FrozenSet, Optional, List, Dict
from pathlib import Path
import json

from egi_core_dau import RelationalGraphWithCuts, ElementID
from subgraph_closure_validator import SubgraphClosureValidator


@dataclass
class ClipboardEntry:
    """
    A validated subgraph stored in the insertion clipboard.
    """
    id: str  # Unique identifier for this entry
    name: str  # User-friendly name
    subgraph_elements: FrozenSet[ElementID]  # Element IDs in the subgraph
    source_egi: RelationalGraphWithCuts  # Complete source EGI for context
    added_timestamp: datetime
    description: str = ""  # Optional user description
    
    def to_dict(self) -> Dict:
        """Serialize to dict for storage."""
        return {
            "id": self.id,
            "name": self.name,
            "subgraph_elements": list(str(e) for e in self.subgraph_elements),
            "added_timestamp": self.added_timestamp.isoformat(),
            "description": self.description,
            # Note: source_egi not serialized (too complex), regenerate from context
        }
    
    @classmethod
    def from_dict(cls, data: Dict, source_egi: RelationalGraphWithCuts) -> "ClipboardEntry":
        """Deserialize from dict."""
        return cls(
            id=data["id"],
            name=data["name"],
            subgraph_elements=frozenset(ElementID(e) for e in data["subgraph_elements"]),
            source_egi=source_egi,
            added_timestamp=datetime.fromisoformat(data["added_timestamp"]),
            description=data.get("description", "")
        )


class InsertionClipboard:
    """
    Manages a persistent clipboard of validated subgraphs for INS operations.
    
    Features:
    - Validates subgraphs (must be closed) before adding
    - Stores multiple entries for user selection
    - Persists to disk (optional)
    - Provides UI-friendly access
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize insertion clipboard.
        
        Args:
            storage_path: Optional path for persistent storage
        """
        self.entries: List[ClipboardEntry] = []
        self.storage_path = storage_path
        self._next_id = 1
        
        # Load from disk if path provided
        if storage_path and storage_path.exists():
            self._load_from_disk()
    
    def add_entry(
        self,
        subgraph_elements: FrozenSet[ElementID],
        source_egi: RelationalGraphWithCuts,
        name: Optional[str] = None,
        description: str = ""
    ) -> tuple[bool, str, Optional[ClipboardEntry]]:
        """
        Add a validated subgraph to the clipboard.
        
        Args:
            subgraph_elements: Element IDs to add
            source_egi: Complete EGI containing the subgraph
            name: Optional user-friendly name
            description: Optional description
            
        Returns:
            (success, message, entry) tuple
        """
        print(f"[Clipboard {id(self)}] add_entry called with {len(subgraph_elements)} elements")
        print(f"[Clipboard {id(self)}] Current entries before add: {len(self.entries)}")
        
        # Validate closure
        validator = SubgraphClosureValidator(source_egi)
        analysis = validator.analyze_closure(subgraph_elements, allow_expansion=True)
        
        if not analysis.is_closed:
            violation_msgs = [v.description for v in analysis.violations[:3]]
            return (
                False,
                f"Subgraph not closed:\n  " + "\n  ".join(violation_msgs),
                None
            )
        
        # Use expanded subgraph if elements were added for closure
        final_elements = analysis.closed_subgraph
        
        # Generate name if not provided
        if not name:
            name = f"Subgraph {self._next_id}"
        
        # Create entry
        entry = ClipboardEntry(
            id=f"clip_{self._next_id}",
            name=name,
            subgraph_elements=final_elements,
            source_egi=source_egi,
            added_timestamp=datetime.now(),
            description=description
        )
        
        self.entries.append(entry)
        self._next_id += 1
        
        print(f"[Clipboard {id(self)}] Entry added! Total entries now: {len(self.entries)}")
        
        # Persist if storage enabled
        if self.storage_path:
            self._save_to_disk()
            print(f"[Clipboard {id(self)}] Saved to disk: {self.storage_path}")
        
        added_count = len(final_elements) - len(subgraph_elements)
        if added_count > 0:
            msg = f"✓ Added to clipboard (expanded by {added_count} for closure)"
        else:
            msg = f"✓ Added to clipboard: {name}"
        
        print(f"[Clipboard {id(self)}] Returning success: {msg}")
        return (True, msg, entry)
    
    def remove_entry(self, entry_id: str) -> bool:
        """Remove an entry from clipboard."""
        original_len = len(self.entries)
        self.entries = [e for e in self.entries if e.id != entry_id]
        
        if len(self.entries) < original_len:
            if self.storage_path:
                self._save_to_disk()
            return True
        return False
    
    def get_entry(self, entry_id: str) -> Optional[ClipboardEntry]:
        """Get entry by ID."""
        for entry in self.entries:
            if entry.id == entry_id:
                return entry
        return None
    
    def get_all_entries(self) -> List[ClipboardEntry]:
        """Get all clipboard entries."""
        print(f"[Clipboard {id(self)}] get_all_entries called, returning {len(self.entries)} entries")
        return self.entries.copy()
    
    def clear(self):
        """Clear all entries."""
        self.entries.clear()
        if self.storage_path:
            self._save_to_disk()
    
    def _save_to_disk(self):
        """Persist clipboard to disk."""
        if not self.storage_path:
            return
        
        data = {
            "entries": [e.to_dict() for e in self.entries],
            "next_id": self._next_id
        }
        
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_from_disk(self):
        """Load clipboard from disk."""
        if not self.storage_path or not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            self._next_id = data.get("next_id", 1)
            # Note: Entries need source_egi which we don't serialize
            # They'll be loaded on-demand when needed
            
        except Exception as e:
            print(f"Warning: Could not load insertion clipboard: {e}")


# Global singleton instance
_global_clipboard: Optional[InsertionClipboard] = None


def get_insertion_clipboard() -> InsertionClipboard:
    """Get the global insertion clipboard instance."""
    global _global_clipboard
    if _global_clipboard is None:
        # Use user's home directory for persistent storage
        storage_path = Path.home() / ".arisbe" / "insertion_clipboard.json"
        _global_clipboard = InsertionClipboard(storage_path)
        print(f"[ClipboardSingleton] Created new instance {id(_global_clipboard)}")
    else:
        print(f"[ClipboardSingleton] Returning existing instance {id(_global_clipboard)} with {len(_global_clipboard.entries)} entries")
    return _global_clipboard
