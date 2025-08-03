#!/usr/bin/env python3
"""
Simple Corpus Loader for Development and Testing

Provides programmatic access to the corpus of EG examples without requiring
full Browser integration. Useful for development, testing, and validation.
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CorpusExample:
    """A single example from the corpus."""
    id: str
    title: str
    description: str
    category: str
    source: Dict[str, Any]
    logical_pattern: str
    logical_form: Optional[str] = None
    notes: Optional[str] = None
    egif_content: Optional[str] = None
    metadata_path: Optional[str] = None


class CorpusLoader:
    """
    Simple loader for the EG corpus.
    
    Provides access to corpus examples for development and testing without
    requiring full Browser sub-application implementation.
    """
    
    def __init__(self, corpus_path: Optional[str] = None):
        """Initialize corpus loader."""
        if corpus_path is None:
            # Default to corpus directory relative to this file
            current_dir = Path(__file__).parent
            corpus_path = current_dir.parent / "corpus" / "corpus"
        
        self.corpus_path = Path(corpus_path)
        self.examples: Dict[str, CorpusExample] = {}
        self._load_corpus()
    
    def _load_corpus(self):
        """Load all corpus examples."""
        if not self.corpus_path.exists():
            print(f"Warning: Corpus path {self.corpus_path} does not exist")
            return
        
        # Load from corpus index if available
        index_path = self.corpus_path / "corpus_index.json"
        if index_path.exists():
            self._load_from_index(index_path)
        else:
            # Fallback: scan directories for .json files
            self._scan_directories()
    
    def _load_from_index(self, index_path: Path):
        """Load corpus from index file."""
        try:
            with open(index_path, 'r') as f:
                index_data = json.load(f)
            
            for example_info in index_data.get('examples', []):
                example_id = example_info['id']
                
                # Find the actual metadata file
                metadata_path = self._find_metadata_file(example_id)
                if metadata_path:
                    example = self._load_example(metadata_path, example_info)
                    if example:
                        self.examples[example_id] = example
                        
        except Exception as e:
            print(f"Error loading corpus index: {e}")
            # Fallback to directory scanning
            self._scan_directories()
    
    def _scan_directories(self):
        """Scan corpus directories for .json metadata files."""
        for category_dir in self.corpus_path.iterdir():
            if category_dir.is_dir():
                for json_file in category_dir.glob("*.json"):
                    example = self._load_example(json_file)
                    if example:
                        self.examples[example.id] = example
    
    def _find_metadata_file(self, example_id: str) -> Optional[Path]:
        """Find metadata file for given example ID."""
        for category_dir in self.corpus_path.iterdir():
            if category_dir.is_dir():
                metadata_file = category_dir / f"{example_id}.json"
                if metadata_file.exists():
                    return metadata_file
        return None
    
    def _load_example(self, metadata_path: Path, index_info: Optional[Dict] = None) -> Optional[CorpusExample]:
        """Load a single example from its metadata file."""
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Try to load EGIF content if available
            egif_content = None
            base_name = metadata_path.stem
            
            # Look for various EGIF-like formats
            for ext in ['.egif', '.eg', '.txt']:
                egif_path = metadata_path.parent / f"{base_name}{ext}"
                if egif_path.exists():
                    try:
                        with open(egif_path, 'r') as f:
                            egif_content = f.read().strip()
                        break
                    except Exception:
                        continue
            
            # Create example object
            example = CorpusExample(
                id=metadata.get('id', base_name),
                title=metadata.get('title', 'Untitled'),
                description=metadata.get('description', ''),
                category=metadata.get('category', metadata_path.parent.name),
                source=metadata.get('source', {}),
                logical_pattern=metadata.get('logical_pattern', 'unknown'),
                logical_form=metadata.get('logical_form'),
                notes=metadata.get('notes'),
                egif_content=egif_content,
                metadata_path=str(metadata_path)
            )
            
            return example
            
        except Exception as e:
            print(f"Error loading example from {metadata_path}: {e}")
            return None
    
    def get_example(self, example_id: str) -> Optional[CorpusExample]:
        """Get a specific example by ID."""
        return self.examples.get(example_id)
    
    def list_examples(self, category: Optional[str] = None) -> List[CorpusExample]:
        """List all examples, optionally filtered by category."""
        examples = list(self.examples.values())
        
        if category:
            examples = [ex for ex in examples if ex.category == category]
        
        return sorted(examples, key=lambda x: x.id)
    
    def get_categories(self) -> List[str]:
        """Get list of all categories."""
        categories = set(ex.category for ex in self.examples.values())
        return sorted(categories)
    
    def get_examples_by_pattern(self, pattern: str) -> List[CorpusExample]:
        """Get examples matching a logical pattern."""
        return [ex for ex in self.examples.values() 
                if ex.logical_pattern == pattern]
    
    def get_examples_by_author(self, author: str) -> List[CorpusExample]:
        """Get examples by a specific author."""
        return [ex for ex in self.examples.values() 
                if ex.source.get('author', '').lower() == author.lower()]
    
    def search_examples(self, query: str) -> List[CorpusExample]:
        """Search examples by title, description, or notes."""
        query = query.lower()
        results = []
        
        for example in self.examples.values():
            if (query in example.title.lower() or 
                query in example.description.lower() or 
                (example.notes and query in example.notes.lower())):
                results.append(example)
        
        return sorted(results, key=lambda x: x.id)
    
    def get_random_example(self, category: Optional[str] = None) -> Optional[CorpusExample]:
        """Get a random example, optionally from a specific category."""
        examples = self.list_examples(category)
        if examples:
            import random
            return random.choice(examples)
        return None


# Convenience functions for easy access
_corpus_loader = None

def get_corpus_loader() -> CorpusLoader:
    """Get the global corpus loader instance."""
    global _corpus_loader
    if _corpus_loader is None:
        _corpus_loader = CorpusLoader()
    return _corpus_loader

def get_example(example_id: str) -> Optional[CorpusExample]:
    """Get a corpus example by ID."""
    return get_corpus_loader().get_example(example_id)

def list_examples(category: Optional[str] = None) -> List[CorpusExample]:
    """List corpus examples."""
    return get_corpus_loader().list_examples(category)

def get_random_example(category: Optional[str] = None) -> Optional[CorpusExample]:
    """Get a random corpus example."""
    return get_corpus_loader().get_random_example(category)


if __name__ == "__main__":
    # Test the corpus loader
    print("=== Testing Corpus Loader ===")
    
    loader = CorpusLoader()
    
    print(f"Loaded {len(loader.examples)} examples")
    print(f"Categories: {loader.get_categories()}")
    
    # Show a few examples
    for example in loader.list_examples()[:3]:
        print(f"\n{example.id}:")
        print(f"  Title: {example.title}")
        print(f"  Category: {example.category}")
        print(f"  Pattern: {example.logical_pattern}")
        if example.egif_content:
            print(f"  EGIF: {example.egif_content[:50]}...")
