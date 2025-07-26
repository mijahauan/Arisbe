"""
Corpus Manager for Existential Graphs

Handles discovery, categorization, and organization of corpus examples
for the graph editor dropdown selector.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class CorpusExample:
    """Represents a single corpus example with metadata."""
    name: str
    filepath: str
    category: str
    complexity_level: str
    description: str
    clif: str
    source: str
    logical_pattern: str
    teaching_purpose: str
    
    @property
    def display_name(self) -> str:
        """Generate a user-friendly display name."""
        return f"{self.description}"
    
    @property
    def category_display(self) -> str:
        """Generate category display name."""
        category_names = {
            'alpha': 'Alpha (Propositional)',
            'beta': 'Beta (Predicate Logic)', 
            'gamma': 'Gamma (Modal Logic)',
            'canonical': 'Canonical Examples',
            'peirce': 'Peirce Primary Sources',
            'scholars': 'Modern Scholars'
        }
        return category_names.get(self.category, self.category.title())


class CorpusManager:
    """Manages corpus examples for the graph editor."""
    
    def __init__(self, corpus_root: str = "corpus/corpus"):
        self.corpus_root = Path(corpus_root)
        self.examples: Dict[str, CorpusExample] = {}
        self.categories: Dict[str, List[CorpusExample]] = defaultdict(list)
        self.complexity_levels: Dict[str, List[CorpusExample]] = defaultdict(list)
        
    def discover_examples(self) -> None:
        """Discover all corpus examples in the corpus directory."""
        if not self.corpus_root.exists():
            print(f"Warning: Corpus directory not found: {self.corpus_root}")
            return
            
        # Find all EGRF files, excluding generated ones
        egrf_files = []
        for egrf_file in self.corpus_root.rglob("*.egrf"):
            if not egrf_file.name.endswith('.generated.egrf'):
                egrf_files.append(egrf_file)
        
        print(f"Found {len(egrf_files)} corpus files")
        
        for egrf_file in egrf_files:
            try:
                example = self._load_example(egrf_file)
                if example:
                    self.examples[example.name] = example
                    self.categories[example.category].append(example)
                    self.complexity_levels[example.complexity_level].append(example)
                    
            except Exception as e:
                print(f"Warning: Could not load {egrf_file}: {e}")
                
        print(f"Loaded {len(self.examples)} corpus examples")
        self._sort_categories()
        
    def _load_example(self, egrf_file: Path) -> Optional[CorpusExample]:
        """Load a single EGRF example file."""
        try:
            with open(egrf_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Extract metadata
            metadata = data.get('metadata', {})
            logical_content = data.get('logical_content', {})
            
            # Determine category from file path
            category = egrf_file.parent.name
            
            # Create example object
            example = CorpusExample(
                name=egrf_file.stem,
                filepath=str(egrf_file),
                category=category,
                complexity_level=metadata.get('complexity_level', 'unknown'),
                description=metadata.get('description', egrf_file.stem),
                clif=logical_content.get('clif', ''),
                source=metadata.get('source', 'Unknown'),
                logical_pattern=metadata.get('logical_pattern', 'unknown'),
                teaching_purpose=metadata.get('teaching_purpose', '')
            )
            
            return example
            
        except Exception as e:
            print(f"Error loading {egrf_file}: {e}")
            return None
            
    def _sort_categories(self) -> None:
        """Sort examples within each category."""
        # Define category order
        category_order = ['alpha', 'beta', 'gamma', 'canonical', 'peirce', 'scholars']
        
        # Sort examples within each category by complexity then name
        for category, examples in self.categories.items():
            examples.sort(key=lambda x: (
                self._complexity_order(x.complexity_level),
                x.description
            ))
            
    def _complexity_order(self, complexity: str) -> int:
        """Get sort order for complexity levels."""
        order = {
            'beginner': 0,
            'intermediate': 1, 
            'advanced': 2,
            'expert': 3,
            'unknown': 99
        }
        return order.get(complexity, 99)
        
    def get_categories(self) -> List[str]:
        """Get list of available categories in display order."""
        category_order = ['alpha', 'beta', 'gamma', 'canonical', 'peirce', 'scholars']
        available_categories = []
        
        for category in category_order:
            if category in self.categories and self.categories[category]:
                available_categories.append(category)
                
        # Add any other categories not in the standard order
        for category in self.categories:
            if category not in category_order and self.categories[category]:
                available_categories.append(category)
                
        return available_categories
        
    def get_examples_by_category(self, category: str) -> List[CorpusExample]:
        """Get examples for a specific category."""
        return self.categories.get(category, [])
        
    def get_example(self, name: str) -> Optional[CorpusExample]:
        """Get a specific example by name."""
        return self.examples.get(name)
        
    def get_all_examples(self) -> List[CorpusExample]:
        """Get all examples sorted by category and complexity."""
        all_examples = []
        for category in self.get_categories():
            all_examples.extend(self.categories[category])
        return all_examples
        
    def get_examples_by_complexity(self, complexity: str) -> List[CorpusExample]:
        """Get examples by complexity level."""
        return self.complexity_levels.get(complexity, [])
        
    def get_complexity_levels(self) -> List[str]:
        """Get available complexity levels."""
        levels = ['beginner', 'intermediate', 'advanced', 'expert']
        available_levels = []
        
        for level in levels:
            if level in self.complexity_levels and self.complexity_levels[level]:
                available_levels.append(level)
                
        return available_levels
        
    def search_examples(self, query: str) -> List[CorpusExample]:
        """Search examples by description, source, or logical pattern."""
        query = query.lower()
        results = []
        
        for example in self.examples.values():
            if (query in example.description.lower() or
                query in example.source.lower() or
                query in example.logical_pattern.lower() or
                query in example.teaching_purpose.lower()):
                results.append(example)
                
        return results
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get corpus statistics."""
        stats = {
            'total_examples': len(self.examples),
            'categories': {cat: len(examples) for cat, examples in self.categories.items()},
            'complexity_levels': {level: len(examples) for level, examples in self.complexity_levels.items()},
            'logical_patterns': {}
        }
        
        # Count logical patterns
        pattern_counts = defaultdict(int)
        for example in self.examples.values():
            pattern_counts[example.logical_pattern] += 1
        stats['logical_patterns'] = dict(pattern_counts)
        
        return stats
        
    def validate_examples(self) -> List[str]:
        """Validate all examples and return list of issues."""
        issues = []
        
        for name, example in self.examples.items():
            # Check required fields
            if not example.clif:
                issues.append(f"{name}: Missing CLIF statement")
            if not example.description:
                issues.append(f"{name}: Missing description")
            if example.complexity_level == 'unknown':
                issues.append(f"{name}: Unknown complexity level")
                
            # Check file exists
            if not Path(example.filepath).exists():
                issues.append(f"{name}: File not found: {example.filepath}")
                
        return issues


def test_corpus_manager():
    """Test the corpus manager functionality."""
    print("Testing Corpus Manager")
    print("=" * 50)
    
    manager = CorpusManager()
    manager.discover_examples()
    
    # Print statistics
    stats = manager.get_statistics()
    print(f"Total examples: {stats['total_examples']}")
    print(f"Categories: {list(stats['categories'].keys())}")
    print(f"Complexity levels: {list(stats['complexity_levels'].keys())}")
    
    # Print examples by category
    for category in manager.get_categories():
        examples = manager.get_examples_by_category(category)
        print(f"\n{category.upper()} ({len(examples)} examples):")
        for example in examples:
            print(f"  - {example.display_name} ({example.complexity_level})")
            
    # Validate examples
    issues = manager.validate_examples()
    if issues:
        print(f"\nValidation Issues ({len(issues)}):")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n✅ All examples validated successfully")


if __name__ == "__main__":
    test_corpus_manager()

