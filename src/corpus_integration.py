"""
Corpus integration module for Ergasterion.

Provides functionality to browse, load, and integrate corpus examples
into the drawing editor for composition and practice.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from egif_parser_dau import EGIFParser
from egi_core_dau import RelationalGraphWithCuts


class CorpusCategory(Enum):
    """Categories of corpus items."""
    PEIRCE = "peirce"
    SCHOLARS = "scholars" 
    CANONICAL = "canonical"
    CHALLENGING = "challenging"
    DERIVED = "derived"


@dataclass
class CorpusItem:
    """Represents a single corpus item."""
    id: str
    title: str
    category: CorpusCategory
    description: str
    egif_content: Optional[str] = None
    cgif_content: Optional[str] = None
    clif_content: Optional[str] = None
    metadata: Dict[str, Any] = None
    file_path: Optional[Path] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CorpusManager:
    """Manages corpus items and provides integration with Ergasterion."""
    
    def __init__(self, corpus_root: Path = None):
        self.corpus_root = corpus_root or Path("corpus")
        self.items: Dict[str, CorpusItem] = {}
        self._load_corpus_index()
    
    def _load_corpus_index(self):
        """Load corpus items from the filesystem."""
        if not self.corpus_root.exists():
            return
        
        # Load from corpus/corpus directory structure
        corpus_dir = self.corpus_root / "corpus"
        if corpus_dir.exists():
            self._scan_directory(corpus_dir)
    
    def _scan_directory(self, directory: Path):
        """Recursively scan directory for corpus files."""
        try:
            for item in directory.iterdir():
                if item.is_file():
                    self._process_file(item)
                elif item.is_dir():
                    self._scan_directory(item)
        except (OSError, PermissionError):
            # Skip directories that can't be accessed
            pass
    
    def _process_file(self, file_path: Path):
        """Process a single corpus file."""
        if file_path.suffix not in ['.egif', '.cgif', '.clif']:
            return
        
        try:
            # Determine category from path
            category = self._determine_category(file_path)
            
            # Generate ID from filename
            item_id = file_path.stem
            
            # Read content
            content = file_path.read_text(encoding='utf-8')
            
            # Parse metadata from comments
            metadata = self._parse_metadata(content)
            
            # Create corpus item
            item = CorpusItem(
                id=item_id,
                title=metadata.get('title', item_id.replace('_', ' ').title()),
                category=category,
                description=metadata.get('description', ''),
                file_path=file_path,
                metadata=metadata
            )
            
            # Set content based on file type
            if file_path.suffix == '.egif':
                item.egif_content = self._clean_content(content)
            elif file_path.suffix == '.cgif':
                item.cgif_content = self._clean_content(content)
            elif file_path.suffix == '.clif':
                item.clif_content = self._clean_content(content)
            
            self.items[item_id] = item
            
        except Exception as e:
            print(f"Warning: Failed to process corpus file {file_path}: {e}")
    
    def _determine_category(self, file_path: Path) -> CorpusCategory:
        """Determine category from file path."""
        path_str = str(file_path).lower()
        
        if 'peirce' in path_str:
            return CorpusCategory.PEIRCE
        elif 'scholars' in path_str:
            return CorpusCategory.SCHOLARS
        elif 'canonical' in path_str:
            return CorpusCategory.CANONICAL
        elif 'challenging' in path_str:
            return CorpusCategory.CHALLENGING
        else:
            return CorpusCategory.DERIVED
    
    def _parse_metadata(self, content: str) -> Dict[str, str]:
        """Parse metadata from file comments."""
        metadata = {}
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('#'):
                # Parse comment metadata
                if ':' in line:
                    key, value = line[1:].split(':', 1)
                    metadata[key.strip().lower()] = value.strip()
        
        return metadata
    
    def _clean_content(self, content: str) -> str:
        """Clean content by removing comments and extra whitespace."""
        lines = []
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                lines.append(line)
        
        return '\n'.join(lines)
    
    def get_items_by_category(self, category: CorpusCategory) -> List[CorpusItem]:
        """Get all items in a specific category."""
        return [item for item in self.items.values() if item.category == category]
    
    def get_item(self, item_id: str) -> Optional[CorpusItem]:
        """Get a specific corpus item by ID."""
        return self.items.get(item_id)
    
    def search_items(self, query: str) -> List[CorpusItem]:
        """Search corpus items by title or description."""
        query = query.lower()
        results = []
        
        for item in self.items.values():
            if (query in item.title.lower() or 
                query in item.description.lower() or
                query in item.id.lower()):
                results.append(item)
        
        return results
    
    def parse_item_to_egi(self, item_id: str) -> Optional[RelationalGraphWithCuts]:
        """Parse a corpus item to EGI structure."""
        item = self.get_item(item_id)
        if not item:
            return None
        
        # Try EGIF first, then CGIF, then CLIF
        content = item.egif_content or item.cgif_content or item.clif_content
        if not content:
            return None
        
        try:
            if item.egif_content:
                parser = EGIFParser(content)
                return parser.parse()
            else:
                # Would need CGIF/CLIF parsers for other formats
                print(f"Warning: No EGIF content available for {item_id}")
                return None
        except Exception as e:
            print(f"Error parsing {item_id}: {e}")
            return None
    
    def get_drawing_schema_for_item(self, item_id: str) -> Optional[Dict]:
        """Convert a corpus item to drawing schema for the editor."""
        egi = self.parse_item_to_egi(item_id)
        if not egi:
            return None
        
        # Convert EGI to drawing schema
        # This is a simplified conversion - would need full spatial layout
        schema = {
            "sheet_id": egi.sheet,
            "cuts": [],
            "vertices": [],
            "predicates": [],
            "ligatures": [],
            "predicate_outputs": {}
        }
        
        # Add cuts
        for i, cut in enumerate(egi.Cut):
            schema["cuts"].append({
                "id": cut.id,
                "parent_id": None  # Would need to determine from area mapping
            })
        
        # Add vertices
        for i, vertex in enumerate(egi.V):
            schema["vertices"].append({
                "id": vertex.id,
                "area_id": egi.sheet,  # Simplified - would need area lookup
                "label": vertex.label,
                "label_kind": "constant" if not vertex.is_generic else "variable"
            })
        
        # Add predicates
        for i, edge in enumerate(egi.E):
            relation_name = egi.rel.get(edge.id, f"R{i}")
            schema["predicates"].append({
                "id": edge.id,
                "name": relation_name,
                "area_id": egi.sheet  # Simplified - would need area lookup
            })
        
        # Add ligatures
        for edge_id, vertex_sequence in egi.nu.items():
            schema["ligatures"].append({
                "edge_id": edge_id,
                "vertex_ids": list(vertex_sequence)
            })
        
        return schema
    
    def get_categories(self) -> List[CorpusCategory]:
        """Get all available categories."""
        categories = set()
        for item in self.items.values():
            categories.add(item.category)
        return sorted(list(categories), key=lambda x: x.value)
    
    def get_statistics(self) -> Dict[str, int]:
        """Get corpus statistics."""
        stats = {
            "total_items": len(self.items),
            "by_category": {},
            "by_format": {"egif": 0, "cgif": 0, "clif": 0}
        }
        
        for item in self.items.values():
            # Count by category
            cat_name = item.category.value
            stats["by_category"][cat_name] = stats["by_category"].get(cat_name, 0) + 1
            
            # Count by format
            if item.egif_content:
                stats["by_format"]["egif"] += 1
            if item.cgif_content:
                stats["by_format"]["cgif"] += 1
            if item.clif_content:
                stats["by_format"]["clif"] += 1
        
        return stats


class CorpusIntegration:
    """Integration layer between corpus and drawing editor."""
    
    def __init__(self, corpus_manager: CorpusManager):
        self.corpus_manager = corpus_manager
    
    def get_corpus_list_for_ui(self) -> List[Dict[str, Any]]:
        """Get corpus items formatted for UI display."""
        items = []
        
        for item in self.corpus_manager.items.values():
            items.append({
                "id": item.id,
                "title": item.title,
                "category": item.category.value,
                "description": item.description,
                "has_egif": item.egif_content is not None,
                "has_cgif": item.cgif_content is not None,
                "has_clif": item.clif_content is not None,
                "metadata": item.metadata
            })
        
        return sorted(items, key=lambda x: (x["category"], x["title"]))
    
    def load_item_for_editor(self, item_id: str) -> Optional[Dict]:
        """Load a corpus item for the drawing editor."""
        schema = self.corpus_manager.get_drawing_schema_for_item(item_id)
        if schema:
            item = self.corpus_manager.get_item(item_id)
            schema["corpus_metadata"] = {
                "source_id": item_id,
                "title": item.title,
                "category": item.category.value,
                "description": item.description
            }
        
        return schema
    
    def get_related_items(self, item_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get items related to the given item."""
        item = self.corpus_manager.get_item(item_id)
        if not item:
            return []
        
        # Find items in same category or with similar keywords
        related = []
        for other_item in self.corpus_manager.items.values():
            if other_item.id == item_id:
                continue
            
            score = 0
            
            # Same category gets points
            if other_item.category == item.category:
                score += 3
            
            # Shared keywords in title/description
            item_words = set(item.title.lower().split() + item.description.lower().split())
            other_words = set(other_item.title.lower().split() + other_item.description.lower().split())
            shared_words = item_words & other_words
            score += len(shared_words)
            
            if score > 0:
                related.append({
                    "id": other_item.id,
                    "title": other_item.title,
                    "category": other_item.category.value,
                    "description": other_item.description,
                    "relevance_score": score
                })
        
        # Sort by relevance and return top items
        related.sort(key=lambda x: x["relevance_score"], reverse=True)
        return related[:limit]


# Global corpus manager instance
_corpus_manager = None

def get_corpus_manager() -> CorpusManager:
    """Get the global corpus manager instance."""
    global _corpus_manager
    if _corpus_manager is None:
        _corpus_manager = CorpusManager()
    return _corpus_manager

def get_corpus_integration() -> CorpusIntegration:
    """Get the corpus integration instance."""
    return CorpusIntegration(get_corpus_manager())

