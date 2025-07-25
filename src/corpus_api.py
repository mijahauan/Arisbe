"""
Corpus Access API

Provides a simple, unified interface for accessing the EGRF corpus from any component
of the Arisbe system. This API abstracts the file system structure and provides
convenient methods for loading examples, metadata, and different representations.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass


@dataclass
class CorpusExample:
    """Represents a single example from the corpus."""
    id: str
    category: str
    title: str
    description: str
    source: Dict[str, Any]
    logical_pattern: str
    clif_content: str
    egrf_content: Dict[str, Any]
    eg_hg_content: str
    metadata: Dict[str, Any]
    
    @property
    def logical_form(self) -> Optional[str]:
        """Get the logical form if available in metadata."""
        return self.metadata.get('logical_form')
    
    @property
    def notes(self) -> Optional[str]:
        """Get notes if available in metadata."""
        return self.metadata.get('notes')


class CorpusAPI:
    """Main API for accessing the corpus."""
    
    def __init__(self, corpus_dir: Optional[str] = None):
        """
        Initialize the corpus API.
        
        Args:
            corpus_dir: Path to the corpus directory. If None, uses default location.
        """
        if corpus_dir is None:
            # Default to corpus/corpus directory relative to this file
            self.corpus_dir = Path(__file__).parent.parent / 'corpus' / 'corpus'
        else:
            self.corpus_dir = Path(corpus_dir)
        
        self.index_path = self.corpus_dir / 'corpus_index.json'
        self._index = None
        self._examples_cache = {}
    
    @property
    def index(self) -> Dict[str, Any]:
        """Get the corpus index, loading it if necessary."""
        if self._index is None:
            self._load_index()
        return self._index
    
    def _load_index(self) -> None:
        """Load the corpus index from disk."""
        if not self.index_path.exists():
            raise FileNotFoundError(f"Corpus index not found at {self.index_path}")
        
        with open(self.index_path, 'r') as f:
            self._index = json.load(f)
    
    def get_example_ids(self) -> List[str]:
        """Get all example IDs in the corpus."""
        return [example['id'] for example in self.index['examples']]
    
    def get_categories(self) -> List[str]:
        """Get all categories in the corpus."""
        return list(set(example['category'] for example in self.index['examples']))
    
    def get_examples_by_category(self, category: str) -> List[str]:
        """
        Get example IDs for a specific category.
        
        Args:
            category: Category name (e.g., 'canonical', 'peirce', 'scholars')
            
        Returns:
            List of example IDs in the category
        """
        return [
            example['id'] 
            for example in self.index['examples'] 
            if example['category'] == category
        ]
    
    def get_examples_by_pattern(self, pattern: str) -> List[str]:
        """
        Get example IDs for a specific logical pattern.
        
        Args:
            pattern: Logical pattern (e.g., 'implication', 'quantification', 'ligature')
            
        Returns:
            List of example IDs with the pattern
        """
        return [
            example['id'] 
            for example in self.index['examples'] 
            if example.get('logical_pattern') == pattern
        ]
    
    def load_example(self, example_id: str) -> CorpusExample:
        """
        Load a complete example with all its representations.
        
        Args:
            example_id: ID of the example to load
            
        Returns:
            CorpusExample instance with all data loaded
            
        Raises:
            ValueError: If example ID is not found
            FileNotFoundError: If required files are missing
        """
        # Check cache first
        if example_id in self._examples_cache:
            return self._examples_cache[example_id]
        
        # Find example in index
        example_info = None
        for example in self.index['examples']:
            if example['id'] == example_id:
                example_info = example
                break
        
        if not example_info:
            raise ValueError(f"Example '{example_id}' not found in corpus")
        
        category = example_info['category']
        category_dir = self.corpus_dir / category
        
        # Load all file types
        clif_path = category_dir / f"{example_id}.clif"
        egrf_path = category_dir / f"{example_id}.egrf"
        eg_hg_path = category_dir / f"{example_id}.eg-hg"
        metadata_path = category_dir / f"{example_id}.json"
        
        # Load CLIF content
        if not clif_path.exists():
            raise FileNotFoundError(f"CLIF file not found: {clif_path}")
        with open(clif_path, 'r') as f:
            clif_content = f.read().strip()
        
        # Load EGRF content
        if not egrf_path.exists():
            raise FileNotFoundError(f"EGRF file not found: {egrf_path}")
        with open(egrf_path, 'r') as f:
            egrf_content = json.load(f)
        
        # Load EG-HG content
        if not eg_hg_path.exists():
            raise FileNotFoundError(f"EG-HG file not found: {eg_hg_path}")
        with open(eg_hg_path, 'r') as f:
            eg_hg_content = f.read().strip()
        
        # Load metadata
        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Create example object
        example = CorpusExample(
            id=example_id,
            category=category,
            title=example_info['title'],
            description=example_info['description'],
            source=example_info.get('source', {}),
            logical_pattern=example_info.get('logical_pattern', ''),
            clif_content=clif_content,
            egrf_content=egrf_content,
            eg_hg_content=eg_hg_content,
            metadata=metadata
        )
        
        # Cache the example
        self._examples_cache[example_id] = example
        
        return example
    
    def load_all_examples(self) -> List[CorpusExample]:
        """
        Load all examples in the corpus.
        
        Returns:
            List of all CorpusExample instances
        """
        return [self.load_example(example_id) for example_id in self.get_example_ids()]
    
    def search_examples(self, query: str) -> List[str]:
        """
        Search examples by title, description, or source.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching example IDs
        """
        query_lower = query.lower()
        matches = []
        
        for example in self.index['examples']:
            if (query_lower in example['title'].lower() or
                query_lower in example['description'].lower() or
                query_lower in str(example.get('source', '')).lower()):
                matches.append(example['id'])
        
        return matches
    
    def get_example_info(self, example_id: str) -> Dict[str, Any]:
        """
        Get basic information about an example without loading all files.
        
        Args:
            example_id: ID of the example
            
        Returns:
            Dictionary with example information from the index
            
        Raises:
            ValueError: If example ID is not found
        """
        for example in self.index['examples']:
            if example['id'] == example_id:
                return example.copy()
        
        raise ValueError(f"Example '{example_id}' not found in corpus")
    
    def validate_corpus(self) -> Tuple[bool, List[str]]:
        """
        Validate that all referenced files exist and are accessible.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        try:
            # Check index exists
            if not self.index_path.exists():
                errors.append(f"Corpus index not found: {self.index_path}")
                return False, errors
            
            # Check each example
            for example in self.index['examples']:
                example_id = example['id']
                category = example['category']
                category_dir = self.corpus_dir / category
                
                # Check category directory exists
                if not category_dir.exists():
                    errors.append(f"Category directory not found: {category_dir}")
                    continue
                
                # Check required files
                required_files = [
                    f"{example_id}.clif",
                    f"{example_id}.egrf", 
                    f"{example_id}.eg-hg",
                    f"{example_id}.json"
                ]
                
                for filename in required_files:
                    file_path = category_dir / filename
                    if not file_path.exists():
                        errors.append(f"Missing file for {example_id}: {file_path}")
        
        except Exception as e:
            errors.append(f"Error validating corpus: {str(e)}")
        
        return len(errors) == 0, errors


# Global instance for easy access
corpus = CorpusAPI()


# Convenience functions for common operations
def get_example(example_id: str) -> CorpusExample:
    """Get an example by ID using the global corpus instance."""
    return corpus.load_example(example_id)


def get_canonical_examples() -> List[CorpusExample]:
    """Get all canonical examples."""
    return [corpus.load_example(eid) for eid in corpus.get_examples_by_category('canonical')]


def get_peirce_examples() -> List[CorpusExample]:
    """Get all Peirce examples."""
    return [corpus.load_example(eid) for eid in corpus.get_examples_by_category('peirce')]


def get_scholar_examples() -> List[CorpusExample]:
    """Get all scholar examples."""
    return [corpus.load_example(eid) for eid in corpus.get_examples_by_category('scholars')]


def search_corpus(query: str) -> List[CorpusExample]:
    """Search the corpus and return matching examples."""
    return [corpus.load_example(eid) for eid in corpus.search_examples(query)]



