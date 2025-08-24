#!/usr/bin/env python
"""
Corpus Enhancement Script

This script enhances the existing corpus by generating complete linear form coverage.
For each existing EGIF file, it generates the corresponding CLIF and CGIF representations,
creating a comprehensive multi-format corpus that demonstrates the EGI-centric architecture.

The enhanced corpus will include:
- Original EGIF files (preserved)
- Generated CLIF files (.clif)
- Generated CGIF files (.cgif)
- Enhanced corpus index with all three linear forms
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

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

def extract_metadata_from_egif(file_path):
    """Extract metadata comments from EGIF file."""
    metadata = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#'):
                # Parse metadata comments
                if ':' in line:
                    key_part = line[1:].strip()
                    if key_part.startswith('Category:'):
                        metadata['category'] = key_part.split(':', 1)[1].strip()
                    elif key_part.startswith('Description:'):
                        metadata['description'] = key_part.split(':', 1)[1].strip()
                    elif key_part.startswith('Source:'):
                        metadata['source'] = key_part.split(':', 1)[1].strip()
                    elif key_part.startswith('Pattern:'):
                        metadata['logical_pattern'] = key_part.split(':', 1)[1].strip()
            elif line and not line.startswith('#'):
                break  # Stop at first non-comment line
    return metadata

def create_linear_form_file(content, file_path, format_name, metadata=None):
    """Create a linear form file with proper header and content."""
    header_lines = []
    
    if metadata:
        if 'title' in metadata:
            header_lines.append(f"# {metadata['title']}")
        if 'category' in metadata:
            header_lines.append(f"# Category: {metadata['category']}")
        if 'description' in metadata:
            header_lines.append(f"# Description: {metadata['description']}")
        if 'source' in metadata:
            header_lines.append(f"# Source: {metadata['source']}")
        if 'logical_pattern' in metadata:
            header_lines.append(f"# Pattern: {metadata['logical_pattern']}")
    
    header_lines.append(f"# Generated {format_name} representation from EGI")
    header_lines.append(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    header_lines.append("")
    header_lines.append(content)
    header_lines.append("")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(header_lines))

def load_corpus_index():
    """Load the existing corpus index."""
    index_path = Path('corpus/corpus/corpus_index.json')
    if index_path.exists():
        with open(index_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def create_enhanced_corpus_index(results):
    """Create enhanced corpus index with all linear forms."""
    enhanced_index = {
        "name": "EGRF v4.0 Enhanced Corpus",
        "description": "Enhanced corpus with complete linear form coverage: EGIF, CLIF, and CGIF representations",
        "version": "2.0.0",
        "schema_version": "enhanced_v1",
        "generation_date": datetime.now().isoformat(),
        "linear_forms": {
            "egif": {
                "name": "Existential Graph Interchange Format",
                "description": "Dau-compliant linear form using cuts and quantifiers",
                "file_extension": ".egif"
            },
            "clif": {
                "name": "Common Logic Interchange Format", 
                "description": "ISO/IEC 24707:2007 compliant logical expressions",
                "file_extension": ".clif"
            },
            "cgif": {
                "name": "Conceptual Graph Interchange Format",
                "description": "ISO/IEC 24707:2007 Annex B conceptual graph notation",
                "file_extension": ".cgif"
            }
        },
        "examples": []
    }
    
    for example_id, result in results.items():
        if 'error' not in result:
            example = {
                "id": example_id,
                "category": result.get('metadata', {}).get('category', 'unknown'),
                "title": result.get('metadata', {}).get('title', example_id.replace('_', ' ').title()),
                "description": result.get('metadata', {}).get('description', ''),
                "source": result.get('metadata', {}).get('source', ''),
                "logical_pattern": result.get('metadata', {}).get('logical_pattern', ''),
                "linear_forms": {
                    "egif": {
                        "content": result['original_egif'],
                        "source": "original",
                        "file": f"{example_id}.egif"
                    },
                    "clif": {
                        "content": result['generated_clif'],
                        "source": "generated",
                        "file": f"{example_id}.clif"
                    },
                    "cgif": {
                        "content": result['generated_cgif'],
                        "source": "generated",
                        "file": f"{example_id}.cgif"
                    }
                },
                "egi_stats": result['egi_stats']
            }
            enhanced_index["examples"].append(example)
    
    return enhanced_index

def main():
    """Main enhancement function."""
    print("=" * 80)
    print("CORPUS ENHANCEMENT SCRIPT")
    print("=" * 80)
    print("Generating complete linear form coverage for the Arisbe corpus")
    print("Creating CLIF and CGIF files for all existing EGIF examples")
    print()
    
    # Load existing corpus index
    corpus_index = load_corpus_index()
    examples_by_id = {}
    if corpus_index:
        for example in corpus_index.get('examples', []):
            examples_by_id[example['id']] = example
    
    # Find all EGIF files
    corpus_dir = Path('corpus/corpus')
    egif_files = list(corpus_dir.rglob('*.egif'))
    
    print(f"Found {len(egif_files)} EGIF files to enhance")
    print()
    
    successful_enhancements = 0
    failed_enhancements = 0
    results = {}
    
    for egif_file in sorted(egif_files):
        example_id = egif_file.stem
        relative_path = egif_file.relative_to(corpus_dir)
        
        print(f"Enhancing: {relative_path}")
        
        try:
            # Extract EGIF content and metadata
            egif_content = extract_egif_content(egif_file)
            file_metadata = extract_metadata_from_egif(egif_file)
            
            # Merge with index metadata
            metadata = examples_by_id.get(example_id, {})
            metadata.update(file_metadata)
            
            if not egif_content:
                print(f"  ❌ ERROR: Empty EGIF content")
                failed_enhancements += 1
                continue
            
            # Parse to EGI and generate other forms
            egi = parse_egif(egif_content)
            clif_content = generate_clif(egi)
            cgif_content = generate_cgif(egi)
            
            # Create CLIF file
            clif_path = egif_file.with_suffix('.clif')
            create_linear_form_file(clif_content, clif_path, 'CLIF', metadata)
            
            # Create CGIF file  
            cgif_path = egif_file.with_suffix('.cgif')
            create_linear_form_file(cgif_content, cgif_path, 'CGIF', metadata)
            
            print(f"  ✅ Created: {clif_path.name}, {cgif_path.name}")
            print(f"     EGI: {len(egi.V)}V {len(egi.E)}E {len(egi.Cut)}C")
            
            successful_enhancements += 1
            results[example_id] = {
                'path': str(relative_path),
                'metadata': metadata,
                'original_egif': egif_content,
                'generated_clif': clif_content,
                'generated_cgif': cgif_content,
                'egi_stats': {
                    'vertices': len(egi.V),
                    'edges': len(egi.E),
                    'cuts': len(egi.Cut)
                }
            }
            
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            failed_enhancements += 1
            results[example_id] = {'error': str(e), 'path': str(relative_path)}
    
    print()
    print("=" * 80)
    print("CORPUS ENHANCEMENT SUMMARY")
    print("=" * 80)
    print(f"Files processed: {len(egif_files)}")
    print(f"Successful enhancements: {successful_enhancements}")
    print(f"Failed enhancements: {failed_enhancements}")
    print(f"Success rate: {successful_enhancements/len(egif_files)*100:.1f}%")
    print()
    
    if successful_enhancements > 0:
        # Create enhanced corpus index
        enhanced_index = create_enhanced_corpus_index(results)
        
        # Save enhanced index
        enhanced_index_path = 'corpus/corpus/corpus_enhanced_index.json'
        with open(enhanced_index_path, 'w', encoding='utf-8') as f:
            json.dump(enhanced_index, f, indent=2, ensure_ascii=False)
        
        print("✅ CORPUS ENHANCEMENT SUCCESSFUL")
        print(f"Created {successful_enhancements * 2} new linear form files:")
        print(f"  • {successful_enhancements} CLIF files (.clif)")
        print(f"  • {successful_enhancements} CGIF files (.cgif)")
        print(f"  • Enhanced corpus index: {enhanced_index_path}")
        print()
        print("The enhanced corpus now provides:")
        print("  🎯 Complete linear form coverage for all examples")
        print("  🔄 Validated EGI-centric interconversion")
        print("  📚 Comprehensive multi-format reference corpus")
    
    if failed_enhancements > 0:
        print(f"⚠️  {failed_enhancements} files could not be enhanced")
    
    print(f"\n🎉 CORPUS ENHANCEMENT COMPLETE")

if __name__ == '__main__':
    main()
