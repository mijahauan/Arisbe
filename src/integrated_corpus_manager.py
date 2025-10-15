"""
Integrated Tomos Manager

This module provides a Dau formalism-compliant tomos management system that integrates
with the core formalism manager to provide validated EGI loading, storage, and retrieval.
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import logging

# Core formalism integration
from .core_dau_formalism import CoreDauFormalismManager, LinearFormat, get_dau_formalism_manager
from .dau_chapters_integration import get_dau_chapters_manager
from .egi_core_dau import RelationalGraphWithCuts
from .integration_interfaces import CorpusManager as CorpusManagerProtocol


class CorpusCategory(Enum):
    """Categories of tomos items."""
    PEIRCE = "peirce"
    SCHOLARS = "scholars"
    CANONICAL = "canonical"
    CHALLENGING = "challenging"
    DERIVED = "derived"
    EXAMPLES = "examples"
    TESTS = "tests"


class CorpusFormat(Enum):
    """Supported tomos formats."""
    EGIF = "egif"
    CGIF = "cgif"
    CLIF = "clif"
    FOPL = "fopl"
    JSON = "json"  # For metadata and specifications


@dataclass
class CorpusItem:
    """Represents a validated tomos item with full Dau formalism compliance."""
    
    id: str
    title: str
    category: CorpusCategory
    description: str
    
    # Content in various formats
    egif_content: Optional[str] = None
    cgif_content: Optional[str] = None
    clif_content: Optional[str] = None
    fopl_content: Optional[str] = None
    
    # Parsed and validated EGI
    egi: Optional[RelationalGraphWithCuts] = None
    
    # Validation results
    validation_results: Dict[str, Any] = field(default_factory=dict)
    chapter_compliance: Dict[str, bool] = field(default_factory=dict)
    
    # Metadata and provenance
    metadata: Dict[str, Any] = field(default_factory=dict)
    file_path: Optional[Path] = None
    source_format: Optional[CorpusFormat] = None
    
    # Quality metrics
    complexity_score: Optional[float] = None
    educational_value: Optional[str] = None
    difficulty_level: Optional[str] = None


@dataclass
class CorpusSearchResult:
    """Result of tomos search operation."""
    items: List[CorpusItem]
    total_count: int
    categories: Dict[CorpusCategory, int]
    search_metadata: Dict[str, Any]


class IntegratedCorpusManager(CorpusManagerProtocol):
    """
    Integrated tomos manager that provides Dau formalism-compliant tomos management.
    
    Features:
    - Full validation of all tomos items against Dau formalism
    - Multi-format support (EGIF, CGIF, CLIF, FOPL)
    - Chapter compliance checking
    - Advanced search and filtering
    - Quality metrics and educational categorization
    """
    
    def __init__(self, tomos_root: Path = None, core_manager: CoreDauFormalismManager = None):
        self.logger = logging.getLogger(__name__)
        
        # Initialize paths
        self.tomos_root = tomos_root or Path("corpus")
        self.index_file = self.tomos_root / "corpus_index.json"
        self.validation_cache_file = self.tomos_root / "validation_cache.json"
        
        # Initialize core formalism integration
        self.core_manager = core_manager or get_dau_formalism_manager()
        self.chapters_manager = get_dau_chapters_manager()
        
        # Storage
        self.items: Dict[str, CorpusItem] = {}
        self.validation_cache: Dict[str, Dict[str, Any]] = {}
        
        # Load existing corpus
        self._load_corpus_index()
        self._load_validation_cache()
        
        self.logger.info(f"IntegratedCorpusManager initialized with {len(self.items)} items")
    
    # ========================================================================
    # Core CorpusManager Protocol Implementation
    # ========================================================================
    
    def add_egi(self, egi: RelationalGraphWithCuts, metadata: Dict[str, Any]) -> str:
        """Add EGI to tomos with full validation."""
        try:
            # Generate unique ID
            item_id = self._generate_item_id(metadata.get("title", "untitled"))
            
            # Validate EGI
            validation_results = self.core_manager.validate_egi(egi)
            if not validation_results["overall_valid"]:
                raise ValueError(f"EGI validation failed: {validation_results['errors']}")
            
            # Check chapter compliance
            chapter_compliance = self._validate_chapter_compliance(egi)
            
            # Generate linear forms
            linear_forms = self._generate_all_linear_forms(egi)
            
            # Determine category
            category = self._determine_category_from_metadata(metadata)
            
            # Calculate quality metrics
            complexity_score = self._calculate_complexity_score(egi)
            
            # Create tomos item
            item = CorpusItem(
                id=item_id,
                title=metadata.get("title", item_id),
                category=category,
                description=metadata.get("description", ""),
                egif_content=linear_forms.get(LinearFormat.EGIF),
                cgif_content=linear_forms.get(LinearFormat.CGIF),
                clif_content=linear_forms.get(LinearFormat.CLIF),
                fopl_content=linear_forms.get(LinearFormat.FOPL),
                egi=egi,
                validation_results=validation_results,
                chapter_compliance=chapter_compliance,
                metadata=metadata,
                source_format=CorpusFormat.JSON,  # Added programmatically
                complexity_score=complexity_score,
                educational_value=metadata.get("educational_value", "medium"),
                difficulty_level=metadata.get("difficulty_level", "intermediate")
            )
            
            # Store item
            self.items[item_id] = item
            
            # Update caches
            self._update_validation_cache(item_id, validation_results, chapter_compliance)
            self._save_corpus_index()
            
            self.logger.info(f"Added EGI to corpus: {item_id}")
            return item_id
            
        except Exception as e:
            self.logger.error(f"Failed to add EGI to corpus: {e}")
            raise
    
    def get_egi(self, item_id: str) -> Optional[RelationalGraphWithCuts]:
        """Get validated EGI by ID."""
        item = self.items.get(item_id)
        if not item:
            return None
        
        # Return cached EGI if available
        if item.egi:
            return item.egi
        
        # Parse from available linear form
        try:
            if item.egif_content:
                item.egi = self.core_manager.parse_linear_form(item.egif_content, LinearFormat.EGIF)
            elif item.cgif_content:
                item.egi = self.core_manager.parse_linear_form(item.cgif_content, LinearFormat.CGIF)
            elif item.clif_content:
                item.egi = self.core_manager.parse_linear_form(item.clif_content, LinearFormat.CLIF)
            elif item.fopl_content:
                item.egi = self.core_manager.parse_linear_form(item.fopl_content, LinearFormat.FOPL)
            
            return item.egi
            
        except Exception as e:
            self.logger.error(f"Failed to parse EGI for item {item_id}: {e}")
            return None
    
    def remove_egi(self, item_id: str) -> bool:
        """Remove EGI from tomos."""
        if item_id in self.items:
            del self.items[item_id]
            if item_id in self.validation_cache:
                del self.validation_cache[item_id]
            self._save_corpus_index()
            self.logger.info(f"Removed EGI from corpus: {item_id}")
            return True
        return False
    
    def list_egis(self, category: Optional[str] = None) -> List[str]:
        """List EGI IDs, optionally filtered by category."""
        if category:
            try:
                cat_enum = CorpusCategory(category.lower())
                return [item_id for item_id, item in self.items.items() if item.category == cat_enum]
            except ValueError:
                return []
        return list(self.items.keys())
    
    # ========================================================================
    # Enhanced Tomos Management
    # ========================================================================
    
    def load_from_filesystem(self, force_revalidation: bool = False) -> Dict[str, Any]:
        """Load tomos items from filesystem with full validation."""
        results = {
            "loaded": 0,
            "validated": 0,
            "failed": 0,
            "errors": []
        }
        
        if not self.tomos_root.exists():
            self.tomos_root.mkdir(parents=True, exist_ok=True)
            return results
        
        # Scan for tomos files
        for file_path in self._scan_corpus_files():
            try:
                item = self._load_corpus_file(file_path, force_revalidation)
                if item:
                    self.items[item.id] = item
                    results["loaded"] += 1
                    
                    if item.validation_results.get("overall_valid", False):
                        results["validated"] += 1
                
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Failed to load {file_path}: {e}")
                self.logger.error(f"Failed to load tomos file {file_path}: {e}")
        
        # Save updated index
        self._save_corpus_index()
        
        self.logger.info(f"Loaded {results['loaded']} tomos items, {results['validated']} validated")
        return results
    
    def search_corpus(self, query: str = "", category: Optional[CorpusCategory] = None,
                     min_complexity: Optional[float] = None, max_complexity: Optional[float] = None,
                     difficulty_level: Optional[str] = None, 
                     chapter_compliance: Optional[List[str]] = None) -> CorpusSearchResult:
        """Advanced tomos search with multiple filters."""
        
        filtered_items = []
        
        for item in self.items.values():
            # Text search
            if query and not self._matches_text_query(item, query):
                continue
            
            # Category filter
            if category and item.category != category:
                continue
            
            # Complexity filter
            if min_complexity is not None and (item.complexity_score or 0) < min_complexity:
                continue
            if max_complexity is not None and (item.complexity_score or float('inf')) > max_complexity:
                continue
            
            # Difficulty filter
            if difficulty_level and item.difficulty_level != difficulty_level:
                continue
            
            # Chapter compliance filter
            if chapter_compliance:
                if not all(item.chapter_compliance.get(chapter, False) for chapter in chapter_compliance):
                    continue
            
            filtered_items.append(item)
        
        # Generate category counts
        category_counts = {}
        for category in CorpusCategory:
            category_counts[category] = sum(1 for item in filtered_items if item.category == category)
        
        return CorpusSearchResult(
            items=filtered_items,
            total_count=len(filtered_items),
            categories=category_counts,
            search_metadata={
                "query": query,
                "filters_applied": {
                    "category": category.value if category else None,
                    "min_complexity": min_complexity,
                    "max_complexity": max_complexity,
                    "difficulty_level": difficulty_level,
                    "chapter_compliance": chapter_compliance
                }
            }
        )
    
    def get_corpus_statistics(self) -> Dict[str, Any]:
        """Get comprehensive tomos statistics."""
        stats = {
            "total_items": len(self.items),
            "categories": {},
            "formats": {},
            "validation_status": {"valid": 0, "invalid": 0, "unknown": 0},
            "chapter_compliance": {},
            "complexity_distribution": {"low": 0, "medium": 0, "high": 0},
            "difficulty_distribution": {}
        }
        
        for item in self.items.values():
            # Category counts
            category = item.category.value
            stats["categories"][category] = stats["categories"].get(category, 0) + 1
            
            # Format availability
            if item.egif_content:
                stats["formats"]["egif"] = stats["formats"].get("egif", 0) + 1
            if item.cgif_content:
                stats["formats"]["cgif"] = stats["formats"].get("cgif", 0) + 1
            if item.clif_content:
                stats["formats"]["clif"] = stats["formats"].get("clif", 0) + 1
            if item.fopl_content:
                stats["formats"]["fopl"] = stats["formats"].get("fopl", 0) + 1
            
            # Validation status
            if item.validation_results.get("overall_valid") is True:
                stats["validation_status"]["valid"] += 1
            elif item.validation_results.get("overall_valid") is False:
                stats["validation_status"]["invalid"] += 1
            else:
                stats["validation_status"]["unknown"] += 1
            
            # Chapter compliance
            for chapter, compliant in item.chapter_compliance.items():
                if chapter not in stats["chapter_compliance"]:
                    stats["chapter_compliance"][chapter] = {"compliant": 0, "non_compliant": 0}
                
                if compliant:
                    stats["chapter_compliance"][chapter]["compliant"] += 1
                else:
                    stats["chapter_compliance"][chapter]["non_compliant"] += 1
            
            # Complexity distribution
            if item.complexity_score:
                if item.complexity_score < 3.0:
                    stats["complexity_distribution"]["low"] += 1
                elif item.complexity_score < 7.0:
                    stats["complexity_distribution"]["medium"] += 1
                else:
                    stats["complexity_distribution"]["high"] += 1
            
            # Difficulty distribution
            difficulty = item.difficulty_level or "unknown"
            stats["difficulty_distribution"][difficulty] = stats["difficulty_distribution"].get(difficulty, 0) + 1
        
        return stats
    
    def export_corpus_item(self, item_id: str, format_type: LinearFormat, output_path: Optional[Path] = None) -> str:
        """Export tomos item in specified format."""
        item = self.items.get(item_id)
        if not item:
            raise ValueError(f"Tomos item not found: {item_id}")
        
        # Get EGI
        egi = self.get_egi(item_id)
        if not egi:
            raise ValueError(f"Could not load EGI for item: {item_id}")
        
        # Generate in requested format
        content = self.core_manager.generate_linear_form(egi, format_type)
        
        # Save to file if path provided
        if output_path:
            output_path.write_text(content, encoding="utf-8")
            self.logger.info(f"Exported {item_id} to {output_path}")
        
        return content
    
    def validate_corpus_item(self, item_id: str, force_revalidation: bool = False) -> Dict[str, Any]:
        """Validate specific tomos item against current Dau formalism."""
        item = self.items.get(item_id)
        if not item:
            raise ValueError(f"Tomos item not found: {item_id}")
        
        # Check cache
        if not force_revalidation and item_id in self.validation_cache:
            cached_result = self.validation_cache[item_id]
            if cached_result.get("timestamp"):  # Has recent validation
                return cached_result
        
        # Get EGI
        egi = self.get_egi(item_id)
        if not egi:
            return {"valid": False, "error": "Could not load EGI"}
        
        # Perform validation
        validation_results = self.core_manager.validate_egi(egi)
        chapter_compliance = self._validate_chapter_compliance(egi)
        
        # Update item
        item.validation_results = validation_results
        item.chapter_compliance = chapter_compliance
        
        # Update cache
        self._update_validation_cache(item_id, validation_results, chapter_compliance)
        
        return {
            "valid": validation_results.get("overall_valid", False),
            "validation_results": validation_results,
            "chapter_compliance": chapter_compliance
        }
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def _scan_corpus_files(self) -> List[Path]:
        """Scan tomos directory for supported files."""
        files = []
        
        for ext in [".egif", ".cgif", ".clif", ".fopl", ".json"]:
            files.extend(self.tomos_root.rglob(f"*{ext}"))
        
        return files
    
    def _load_corpus_file(self, file_path: Path, force_revalidation: bool = False) -> Optional[CorpusItem]:
        """Load and validate a single tomos file."""
        try:
            # Determine format
            format_type = CorpusFormat(file_path.suffix[1:])  # Remove dot
            
            # Read content
            content = file_path.read_text(encoding="utf-8")
            
            # Generate item ID
            item_id = file_path.stem
            
            # Parse metadata from content or companion files
            metadata = self._parse_file_metadata(file_path, content)
            
            # Create basic item
            item = CorpusItem(
                id=item_id,
                title=metadata.get("title", item_id.replace("_", " ").title()),
                category=self._determine_category_from_path(file_path),
                description=metadata.get("description", ""),
                metadata=metadata,
                file_path=file_path,
                source_format=format_type
            )
            
            # Set content based on format
            if format_type == CorpusFormat.EGIF:
                item.egif_content = content
            elif format_type == CorpusFormat.CGIF:
                item.cgif_content = content
            elif format_type == CorpusFormat.CLIF:
                item.clif_content = content
            elif format_type == CorpusFormat.FOPL:
                item.fopl_content = content
            
            # Parse and validate EGI if not JSON metadata file
            if format_type != CorpusFormat.JSON:
                try:
                    linear_format = LinearFormat(format_type.value)
                    item.egi = self.core_manager.parse_linear_form(content, linear_format)
                    
                    # Validate if not cached or forced
                    if force_revalidation or item_id not in self.validation_cache:
                        item.validation_results = self.core_manager.validate_egi(item.egi)
                        item.chapter_compliance = self._validate_chapter_compliance(item.egi)
                        item.complexity_score = self._calculate_complexity_score(item.egi)
                    else:
                        # Use cached validation
                        cached = self.validation_cache[item_id]
                        item.validation_results = cached.get("validation_results", {})
                        item.chapter_compliance = cached.get("chapter_compliance", {})
                
                except Exception as e:
                    self.logger.warning(f"Failed to parse/validate {file_path}: {e}")
                    item.validation_results = {"overall_valid": False, "error": str(e)}
            
            return item
            
        except Exception as e:
            self.logger.error(f"Failed to load tomos file {file_path}: {e}")
            return None
    
    def _validate_chapter_compliance(self, egi: RelationalGraphWithCuts) -> Dict[str, bool]:
        """Validate EGI against all Dau chapters."""
        try:
            # Use chapters manager for comprehensive validation
            integration_result = self.chapters_manager.validate_full_integration(egi)
            
            compliance = {}
            for chapter, result in integration_result.chapter_results.items():
                compliance[chapter.value] = result.compliant
            
            return compliance
            
        except Exception as e:
            self.logger.error(f"Chapter compliance validation failed: {e}")
            return {}
    
    def _generate_all_linear_forms(self, egi: RelationalGraphWithCuts) -> Dict[LinearFormat, str]:
        """Generate all supported linear forms for an EGI."""
        forms = {}
        
        for format_type in LinearFormat:
            try:
                forms[format_type] = self.core_manager.generate_linear_form(egi, format_type)
            except Exception as e:
                self.logger.warning(f"Failed to generate {format_type.value}: {e}")
        
        return forms
    
    def _calculate_complexity_score(self, egi: RelationalGraphWithCuts) -> float:
        """Calculate complexity score for an EGI."""
        try:
            # Basic complexity metrics
            vertex_count = len(egi.V) if hasattr(egi, 'V') else 0
            edge_count = len(egi.E) if hasattr(egi, 'E') else 0
            cut_count = len(egi.Cut) if hasattr(egi, 'Cut') else 0
            
            # Calculate nesting depth
            max_depth = 0
            if hasattr(egi, 'hierarchical_index') and egi.hierarchical_index.areas:
                for area_id in egi.area.keys():
                    depth = egi.hierarchical_index.get_nesting_level(area_id) or 0
                    max_depth = max(max_depth, depth)
            
            # Weighted complexity score
            complexity = (
                vertex_count * 0.5 +
                edge_count * 0.7 +
                cut_count * 1.5 +
                max_depth * 2.0
            )
            
            return round(complexity, 2)
            
        except Exception as e:
            self.logger.error(f"Complexity calculation failed: {e}")
            return 0.0
    
    def _determine_category_from_path(self, file_path: Path) -> CorpusCategory:
        """Determine category from file path."""
        path_str = str(file_path).lower()
        
        if "peirce" in path_str:
            return CorpusCategory.PEIRCE
        elif "scholar" in path_str:
            return CorpusCategory.SCHOLARS
        elif "canonical" in path_str:
            return CorpusCategory.CANONICAL
        elif "challenging" in path_str or "difficult" in path_str:
            return CorpusCategory.CHALLENGING
        elif "derived" in path_str:
            return CorpusCategory.DERIVED
        elif "example" in path_str:
            return CorpusCategory.EXAMPLES
        elif "test" in path_str:
            return CorpusCategory.TESTS
        else:
            return CorpusCategory.EXAMPLES
    
    def _determine_category_from_metadata(self, metadata: Dict[str, Any]) -> CorpusCategory:
        """Determine category from metadata."""
        category_str = metadata.get("category", "examples").lower()
        
        try:
            return CorpusCategory(category_str)
        except ValueError:
            return CorpusCategory.EXAMPLES
    
    def _parse_file_metadata(self, file_path: Path, content: str) -> Dict[str, Any]:
        """Parse metadata from file content or companion files."""
        metadata = {}
        
        # Look for companion JSON metadata file
        json_path = file_path.with_suffix(".json")
        if json_path.exists():
            try:
                with open(json_path, 'r') as f:
                    metadata.update(json.load(f))
            except Exception as e:
                self.logger.warning(f"Failed to load metadata from {json_path}: {e}")
        
        # Parse inline metadata from comments
        lines = content.split('\n')
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if line.startswith('#') or line.startswith('//'):
                # Look for key: value patterns
                if ':' in line:
                    key_value = line[1:].strip()  # Remove comment marker
                    if ':' in key_value:
                        key, value = key_value.split(':', 1)
                        metadata[key.strip().lower()] = value.strip()
        
        return metadata
    
    def _matches_text_query(self, item: CorpusItem, query: str) -> bool:
        """Check if item matches text query."""
        query_lower = query.lower()
        
        return (
            query_lower in item.title.lower() or
            query_lower in item.description.lower() or
            query_lower in item.id.lower() or
            any(query_lower in str(value).lower() for value in item.metadata.values())
        )
    
    def _generate_item_id(self, title: str) -> str:
        """Generate unique item ID from title."""
        base_id = title.lower().replace(' ', '_').replace('-', '_')
        base_id = ''.join(c for c in base_id if c.isalnum() or c == '_')
        
        # Ensure uniqueness
        if base_id not in self.items:
            return base_id
        
        counter = 1
        while f"{base_id}_{counter}" in self.items:
            counter += 1
        
        return f"{base_id}_{counter}"
    
    def _load_corpus_index(self):
        """Load tomos index from file."""
        if not self.index_file.exists():
            return
        
        try:
            with open(self.index_file, 'r') as f:
                data = json.load(f)
            
            for item_data in data.get("items", []):
                item = CorpusItem(**item_data)
                self.items[item.id] = item
                
        except Exception as e:
            self.logger.error(f"Failed to load tomos index: {e}")
    
    def _save_corpus_index(self):
        """Save tomos index to file."""
        try:
            self.tomos_root.mkdir(parents=True, exist_ok=True)
            
            data = {
                "version": "1.0",
                "items": [
                    {
                        "id": item.id,
                        "title": item.title,
                        "category": item.category.value,
                        "description": item.description,
                        "metadata": item.metadata,
                        "file_path": str(item.file_path) if item.file_path else None,
                        "source_format": item.source_format.value if item.source_format else None,
                        "complexity_score": item.complexity_score,
                        "educational_value": item.educational_value,
                        "difficulty_level": item.difficulty_level
                    }
                    for item in self.items.values()
                ]
            }
            
            with open(self.index_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save tomos index: {e}")
    
    def _load_validation_cache(self):
        """Load validation cache from file."""
        if not self.validation_cache_file.exists():
            return
        
        try:
            with open(self.validation_cache_file, 'r') as f:
                self.validation_cache = json.load(f)
                
        except Exception as e:
            self.logger.error(f"Failed to load validation cache: {e}")
    
    def _update_validation_cache(self, item_id: str, validation_results: Dict[str, Any], 
                                chapter_compliance: Dict[str, bool]):
        """Update validation cache for an item."""
        from datetime import datetime
        
        self.validation_cache[item_id] = {
            "timestamp": datetime.now().isoformat(),
            "validation_results": validation_results,
            "chapter_compliance": chapter_compliance
        }
        
        # Save cache
        try:
            with open(self.validation_cache_file, 'w') as f:
                json.dump(self.validation_cache, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save validation cache: {e}")


# ============================================================================
# Global Instance Management
# ============================================================================

_global_corpus_manager: Optional[IntegratedCorpusManager] = None

def get_integrated_corpus_manager() -> IntegratedCorpusManager:
    """Get the global integrated tomos manager instance."""
    global _global_corpus_manager
    if _global_corpus_manager is None:
        _global_corpus_manager = IntegratedCorpusManager()
    return _global_corpus_manager

def reset_corpus_manager():
    """Reset global tomos manager (for testing)."""
    global _global_corpus_manager
    _global_corpus_manager = None
