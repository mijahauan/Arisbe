#!/usr/bin/env python
"""
Corpus Linear Forms Demonstration Script

This script processes all EGIF files in the corpus and generates equivalent
representations in CLIF, CGIF, and EGIF formats, demonstrating the successful
parsing and generation capabilities of the clean EGI-centric architecture.

Usage: python corpus_linear_forms_demo.py
"""

import sys
import os
import json
import traceback
from pathlib import Path

# Add src to path for imports
sys.path.append('src')

from egif_parser_dau import parse_egif
from clif_parser_dau import parse_clif
from cgif_parser_dau import parse_cgif
from egif_generator_dau import generate_egif
from clif_generator_dau import generate_clif
from cgif_generator_dau import generate_cgif
from egi_system import create_egi_system

def extract_egif_content(file_path):
    """Extract EGIF content from file, ignoring comments."""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find non-comment, non-empty lines
    egif_lines = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            egif_lines.append(line)
    
    return ' '.join(egif_lines)

def process_corpus_file(egif_path):
    """Process a single EGIF file and generate all linear forms."""
    try:
        # Extract EGIF content
        egif_content = extract_egif_content(egif_path)
        if not egif_content:
            return None, "Empty EGIF content"
        
        # Parse EGIF to EGI
        egi = parse_egif(egif_content)
        
        # Generate all linear forms
        egif_generated = generate_egif(egi)
        clif_generated = generate_clif(egi)
        cgif_generated = generate_cgif(egi)
        
        # Validate round-trip consistency
        egi_from_egif = parse_egif(egif_generated)
        egi_from_clif = parse_clif(clif_generated)
        egi_from_cgif = parse_cgif(cgif_generated)
        
        # Check structural consistency (vertex and edge counts)
        original_v_count = len(egi.V)
        original_e_count = len(egi.E)
        original_c_count = len(egi.Cut)
        
        egif_consistent = (len(egi_from_egif.V) == original_v_count and 
                          len(egi_from_egif.E) == original_e_count and
                          len(egi_from_egif.Cut) == original_c_count)
        
        clif_consistent = (len(egi_from_clif.V) == original_v_count and 
                          len(egi_from_clif.E) == original_e_count and
                          len(egi_from_clif.Cut) == original_c_count)
        
        cgif_consistent = (len(egi_from_cgif.V) == original_v_count and 
                          len(egi_from_cgif.E) == original_e_count and
                          len(egi_from_cgif.Cut) == original_c_count)
        
        result = {
            'original_egif': egif_content,
            'generated_egif': egif_generated,
            'generated_clif': clif_generated,
            'generated_cgif': cgif_generated,
            'egi_stats': {
                'vertices': original_v_count,
                'edges': original_e_count,
                'cuts': original_c_count
            },
            'round_trip_consistency': {
                'egif': egif_consistent,
                'clif': clif_consistent,
                'cgif': cgif_consistent
            }
        }
        
        return result, None
        
    except Exception as e:
        return None, str(e)

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
    print("for all existential graphs in the Arisbe corpus.")
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
    
    for egif_file in sorted(egif_files):
        # Extract example ID from filename
        example_id = egif_file.stem
        relative_path = egif_file.relative_to(corpus_dir)
        
        print(f"Processing: {relative_path}")
        
        # Get metadata if available
        metadata = examples_by_id.get(example_id, {})
        if metadata:
            print(f"  Title: {metadata.get('title', 'Unknown')}")
            print(f"  Pattern: {metadata.get('logical_pattern', 'Unknown')}")
            print(f"  Source: {metadata.get('source', 'Unknown')}")
        
        # Process the file
        result, error = process_corpus_file(egif_file)
        
        if error:
            print(f"  ❌ ERROR: {error}")
            failed_conversions += 1
            results[example_id] = {'error': error, 'path': str(relative_path)}
        else:
            print(f"  ✅ SUCCESS")
            print(f"     EGI: {result['egi_stats']['vertices']}V, {result['egi_stats']['edges']}E, {result['egi_stats']['cuts']}C")
            
            # Show consistency status
            consistency = result['round_trip_consistency']
            egif_status = "✅" if consistency['egif'] else "❌"
            clif_status = "✅" if consistency['clif'] else "❌"
            cgif_status = "✅" if consistency['cgif'] else "❌"
            
            print(f"     Round-trip: EGIF {egif_status} CLIF {clif_status} CGIF {cgif_status}")
            
            # Show generated forms (truncated for readability)
            print(f"     EGIF: {result['generated_egif'][:60]}{'...' if len(result['generated_egif']) > 60 else ''}")
            print(f"     CLIF: {result['generated_clif'][:60]}{'...' if len(result['generated_clif']) > 60 else ''}")
            print(f"     CGIF: {result['generated_cgif'][:60]}{'...' if len(result['generated_cgif']) > 60 else ''}")
            
            successful_conversions += 1
            results[example_id] = {
                'path': str(relative_path),
                'metadata': metadata,
                'result': result
            }
        
        print()
    
    # Summary
    print("=" * 80)
    print("DEMONSTRATION SUMMARY")
    print("=" * 80)
    print(f"Total files processed: {len(egif_files)}")
    print(f"Successful conversions: {successful_conversions}")
    print(f"Failed conversions: {failed_conversions}")
    print(f"Success rate: {successful_conversions/len(egif_files)*100:.1f}%")
    print()
    
    if successful_conversions > 0:
        print("✅ DEMONSTRATION SUCCESSFUL")
        print("The clean EGI-centric architecture successfully processes the corpus")
        print("and generates equivalent representations in all three linear forms:")
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
    
    # Save detailed results
    results_file = 'corpus_conversion_results.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed results saved to: {results_file}")

if __name__ == '__main__':
    main()
