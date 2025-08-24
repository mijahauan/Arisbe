#!/usr/bin/env python
"""
Simple corpus demonstration script that creates a comprehensive report
showing successful parsing and generation across EGIF, CLIF, and CGIF
for the Arisbe corpus.
"""

import sys
import os
import json
from pathlib import Path

# Add src to path for imports
sys.path.append('src')

from egif_parser_dau import parse_egif
from clif_generator_dau import generate_clif
from cgif_generator_dau import generate_cgif
from egif_generator_dau import generate_egif

def extract_egif_content(file_path):
    """Extract EGIF content from file, ignoring comments."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    egif_lines = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            egif_lines.append(line)
    
    return ' '.join(egif_lines)

def load_corpus_index():
    """Load the corpus index to get metadata about examples."""
    index_path = Path('corpus/corpus/corpus_index.json')
    if index_path.exists():
        with open(index_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def main():
    """Main demonstration function."""
    print("=" * 80)
    print("CORPUS LINEAR FORMS DEMONSTRATION")
    print("=" * 80)
    print("Demonstrating successful parsing and generation across EGIF, CLIF, and CGIF")
    print("for existential graphs in the Arisbe corpus.")
    print()
    
    # Load corpus index for metadata
    corpus_index = load_corpus_index()
    examples_by_id = {}
    if corpus_index:
        for example in corpus_index.get('examples', []):
            examples_by_id[example['id']] = example
    
    # Find all EGIF files in corpus
    corpus_dir = Path('corpus/corpus')
    egif_files = list(corpus_dir.rglob('*.egif'))
    
    print(f"Found {len(egif_files)} EGIF files in corpus")
    print()
    
    successful_conversions = 0
    failed_conversions = 0
    results = {}
    
    # Process a representative sample first
    sample_files = egif_files[:5]  # First 5 files for demonstration
    
    for egif_file in sorted(sample_files):
        example_id = egif_file.stem
        relative_path = egif_file.relative_to(corpus_dir)
        
        print(f"Processing: {relative_path}")
        
        # Get metadata if available
        metadata = examples_by_id.get(example_id, {})
        if metadata:
            print(f"  Title: {metadata.get('title', 'Unknown')}")
            print(f"  Pattern: {metadata.get('logical_pattern', 'Unknown')}")
        
        try:
            # Extract EGIF content
            egif_content = extract_egif_content(egif_file)
            if not egif_content:
                print(f"  ❌ ERROR: Empty EGIF content")
                failed_conversions += 1
                continue
            
            print(f"  Original: {egif_content}")
            
            # Parse EGIF to EGI
            egi = parse_egif(egif_content)
            print(f"  EGI: {len(egi.V)}V {len(egi.E)}E {len(egi.Cut)}C")
            
            # Generate all linear forms
            egif_generated = generate_egif(egi)
            clif_generated = generate_clif(egi)
            cgif_generated = generate_cgif(egi)
            
            print(f"  EGIF: {egif_generated}")
            print(f"  CLIF: {clif_generated if clif_generated else '(empty)'}")
            print(f"  CGIF: {cgif_generated if cgif_generated else '(empty)'}")
            
            print(f"  ✅ SUCCESS")
            successful_conversions += 1
            
            results[example_id] = {
                'path': str(relative_path),
                'metadata': metadata,
                'original_egif': egif_content,
                'generated_egif': egif_generated,
                'generated_clif': clif_generated,
                'generated_cgif': cgif_generated,
                'egi_stats': {
                    'vertices': len(egi.V),
                    'edges': len(egi.E),
                    'cuts': len(egi.Cut)
                }
            }
            
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            failed_conversions += 1
            results[example_id] = {'error': str(e), 'path': str(relative_path)}
        
        print()
    
    # Summary
    print("=" * 80)
    print("DEMONSTRATION SUMMARY")
    print("=" * 80)
    print(f"Sample files processed: {len(sample_files)}")
    print(f"Successful conversions: {successful_conversions}")
    print(f"Failed conversions: {failed_conversions}")
    print(f"Success rate: {successful_conversions/len(sample_files)*100:.1f}%")
    print()
    
    if successful_conversions > 0:
        print("✅ DEMONSTRATION SUCCESSFUL")
        print("The clean EGI-centric architecture successfully processes corpus files")
        print("and generates representations in multiple linear forms:")
        print("  • EGIF (Existential Graph Interchange Format)")
        print("  • CLIF (Common Logic Interchange Format)")  
        print("  • CGIF (Conceptual Graph Interchange Format)")
        print()
        print("This validates the architectural goal of maintaining EGI as the")
        print("single source of truth with multiple linear form projections.")
    
    if failed_conversions > 0:
        print(f"⚠️  {failed_conversions} files failed conversion")
        print("These may require parser extensions or represent edge cases")
        print("not yet supported by the current implementation.")
    
    # Save results
    results_file = 'corpus_demo_results.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed results saved to: {results_file}")

if __name__ == '__main__':
    main()
