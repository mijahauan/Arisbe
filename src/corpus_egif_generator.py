#!/usr/bin/env python3
"""
Corpus EGIF Generator

Generates EGIF expressions for corpus examples based on their metadata
and logical forms. This populates the corpus with actual parseable EGIF
content that users can load and experiment with.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from corpus_loader import CorpusLoader, CorpusExample


class CorpusEGIFGenerator:
    """Generates EGIF expressions for corpus examples."""
    
    def __init__(self, corpus_path: Optional[str] = None):
        """Initialize the generator."""
        self.corpus_loader = CorpusLoader(corpus_path)
        
        # Common EGIF patterns based on logical forms
        self.pattern_templates = {
            # Basic patterns
            'implication': self._generate_implication,
            'conjunction': self._generate_conjunction,
            'disjunction': self._generate_disjunction,
            'negation': self._generate_negation,
            'quantification': self._generate_quantification,
            'ligature': self._generate_ligature,
            
            # Specific examples
            'man_mortal': lambda: '(Human "Socrates") ~[ (Mortal "Socrates") ]',
            'universal_statement': lambda: '*x (Human x) ~[ (Mortal x) ]',
        }
    
    def _generate_implication(self, example: CorpusExample) -> str:
        """Generate EGIF for implication patterns."""
        if 'man' in example.description.lower() and 'mortal' in example.description.lower():
            return '(Human "Socrates") ~[ (Mortal "Socrates") ]'
        elif example.logical_form and '→' in example.logical_form:
            # Try to parse P → Q pattern
            parts = example.logical_form.split('→')
            if len(parts) == 2:
                p = parts[0].strip()
                q = parts[1].strip()
                return f'({p} "x") ~[ ({q} "x") ]'
        
        # Default implication
        return '(P "x") ~[ (Q "x") ]'
    
    def _generate_conjunction(self, example: CorpusExample) -> str:
        """Generate EGIF for conjunction patterns."""
        if 'pear' in example.description.lower() and 'orange' in example.description.lower():
            return '(Pear "x") (Ripe "x") (Orange "y") (Red "y")'
        elif example.logical_form and '∧' in example.logical_form:
            # Try to parse P ∧ Q pattern
            parts = example.logical_form.split('∧')
            if len(parts) == 2:
                p = parts[0].strip()
                q = parts[1].strip()
                return f'({p} "x") ({q} "x")'
        
        # Default conjunction
        return '(P "x") (Q "x")'
    
    def _generate_disjunction(self, example: CorpusExample) -> str:
        """Generate EGIF for disjunction patterns."""
        if example.logical_form and '∨' in example.logical_form:
            # Disjunction: P ∨ Q ≡ ~(~P ∧ ~Q)
            parts = example.logical_form.split('∨')
            if len(parts) == 2:
                p = parts[0].strip()
                q = parts[1].strip()
                return f'~[ ~[ ({p} "x") ] ~[ ({q} "x") ] ]'
        
        # Default disjunction
        return '~[ ~[ (P "x") ] ~[ (Q "x") ] ]'
    
    def _generate_negation(self, example: CorpusExample) -> str:
        """Generate EGIF for negation patterns."""
        return '~[ (P "x") ]'
    
    def _generate_quantification(self, example: CorpusExample) -> str:
        """Generate EGIF for quantification patterns."""
        if 'existential' in example.description.lower():
            return '*x (Human x) (Mortal x)'
        elif 'universal' in example.description.lower():
            return '*x (Human x) ~[ (Mortal x) ]'
        
        # Default existential
        return '*x (P x)'
    
    def _generate_ligature(self, example: CorpusExample) -> str:
        """Generate EGIF for ligature examples."""
        # Ligatures crossing cut boundaries
        return '*x (P x) ~[ (Q x) (R x) ]'
    
    def generate_egif_for_example(self, example: CorpusExample) -> str:
        """Generate EGIF expression for a specific example."""
        
        # Try pattern-specific generation
        pattern = example.logical_pattern.lower()
        if pattern in self.pattern_templates:
            generator = self.pattern_templates[pattern]
            if callable(generator):
                if generator.__name__.startswith('_generate_'):
                    return generator(example)
                else:
                    return generator()
        
        # Try based on example ID
        example_id = example.id.lower()
        if 'man_mortal' in example_id:
            return '(Human "Socrates") ~[ (Mortal "Socrates") ]'
        elif 'conjunction' in example_id:
            return self._generate_conjunction(example)
        elif 'disjunction' in example_id:
            return self._generate_disjunction(example)
        elif 'quantification' in example_id:
            return self._generate_quantification(example)
        elif 'ligature' in example_id:
            return self._generate_ligature(example)
        
        # Try based on logical form
        if example.logical_form:
            logical_form = example.logical_form.lower()
            if '→' in logical_form or '⊃' in logical_form:
                return self._generate_implication(example)
            elif '∧' in logical_form or '&' in logical_form:
                return self._generate_conjunction(example)
            elif '∨' in logical_form or '|' in logical_form:
                return self._generate_disjunction(example)
            elif '¬' in logical_form or '~' in logical_form:
                return self._generate_negation(example)
            elif '∃' in logical_form or '∀' in logical_form:
                return self._generate_quantification(example)
        
        # Default fallback
        return f'# {example.title}\n# {example.description}\n(P "x")'
    
    def generate_all_egif_files(self, output_dir: Optional[str] = None) -> Dict[str, str]:
        """Generate EGIF files for all corpus examples."""
        if output_dir is None:
            output_dir = self.corpus_loader.corpus_path
        
        output_path = Path(output_dir)
        generated_files = {}
        
        for example in self.corpus_loader.list_examples():
            # Generate EGIF content
            egif_content = self.generate_egif_for_example(example)
            
            # Add header comment
            header = f"""# {example.title}
# Category: {example.category}
# Description: {example.description}
# Source: {example.source.get('author', 'Unknown')}
# Pattern: {example.logical_pattern}

"""
            
            full_content = header + egif_content
            
            # Determine output file path
            category_dir = output_path / example.category
            category_dir.mkdir(exist_ok=True)
            
            egif_file = category_dir / f"{example.id}.egif"
            
            # Write EGIF file
            try:
                with open(egif_file, 'w') as f:
                    f.write(full_content)
                
                generated_files[example.id] = str(egif_file)
                print(f"✅ Generated {egif_file}")
                
            except Exception as e:
                print(f"❌ Error generating {egif_file}: {e}")
        
        return generated_files
    
    def preview_egif_for_example(self, example_id: str) -> Optional[str]:
        """Preview EGIF content for a specific example."""
        example = self.corpus_loader.get_example(example_id)
        if not example:
            return None
        
        return self.generate_egif_for_example(example)


def main():
    """Generate EGIF files for all corpus examples."""
    print("=== Corpus EGIF Generator ===")
    
    generator = CorpusEGIFGenerator()
    
    # Preview what will be generated
    print("\nPreviewing EGIF generation:")
    for example in generator.corpus_loader.list_examples()[:3]:
        egif = generator.generate_egif_for_example(example)
        print(f"\n{example.id}:")
        print(f"  Title: {example.title}")
        print(f"  Pattern: {example.logical_pattern}")
        print(f"  EGIF: {egif}")
    
    # Ask user if they want to generate files
    response = input("\nGenerate EGIF files for all examples? (y/n): ")
    if response.lower().startswith('y'):
        generated = generator.generate_all_egif_files()
        print(f"\n✅ Generated {len(generated)} EGIF files")
        
        # Test that they can be loaded
        print("\nTesting generated EGIF files:")
        from egif_parser_dau import EGIFParser
        
        for example_id, file_path in list(generated.items())[:2]:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                parser = EGIFParser(content)
                graph = parser.parse()
                print(f"✅ {example_id}: Successfully parsed")
                
            except Exception as e:
                print(f"❌ {example_id}: Parse error - {e}")


if __name__ == "__main__":
    main()
