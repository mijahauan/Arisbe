#!/usr/bin/env python3
"""
Corpus Conversion Tool

This tool converts existing corpus files to the canonical EG-HG YAML format.
It processes CLIF files and existing .eg-hg files to create consistent YAML representations.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import json
import yaml
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

from clif_parser import CLIFParser
from eg_serialization import serialize_graph_to_yaml, save_graph_to_file
from eg_yaml_validator import validate_yaml_content


class CorpusConverter:
    """Converts corpus files to canonical YAML format."""
    
    def __init__(self):
        """Initialize the converter."""
        self.parser = CLIFParser()
        self.conversion_stats = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0
        }
    
    def convert_clif_to_yaml(self, clif_path: Path, output_path: Path, 
                           metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Convert a CLIF file to YAML format.
        
        Args:
            clif_path: Path to the CLIF file
            output_path: Path for the output YAML file
            metadata: Optional metadata to include
            
        Returns:
            True if conversion successful, False otherwise
        """
        try:
            # Read CLIF content
            with open(clif_path, 'r', encoding='utf-8') as f:
                clif_content = f.read().strip()
            
            if not clif_content:
                print(f"Warning: Empty CLIF file: {clif_path}")
                return False
            
            # Parse CLIF
            result = self.parser.parse(clif_content)
            if result.graph is None:
                print(f"Error: Failed to parse CLIF file: {clif_path}")
                if result.errors:
                    for error in result.errors:
                        print(f"  - {error}")
                return False
            
            # Generate metadata if not provided
            if metadata is None:
                metadata = self._generate_metadata_from_path(clif_path, clif_content)
            
            # Serialize to YAML
            yaml_content = serialize_graph_to_yaml(result.graph, metadata)
            
            # Validate the YAML
            validation_result = validate_yaml_content(yaml_content)
            if not validation_result['valid']:
                print(f"Error: Generated YAML is invalid for {clif_path}")
                for error in validation_result['errors']:
                    print(f"  - {error}")
                return False
            
            # Write YAML file
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
            
            print(f"Converted: {clif_path} -> {output_path}")
            return True
            
        except Exception as e:
            print(f"Error converting {clif_path}: {e}")
            return False
    
    def convert_existing_eg_hg_to_yaml(self, eg_hg_path: Path, output_path: Path) -> bool:
        """
        Convert an existing .eg-hg file to canonical YAML format.
        
        Args:
            eg_hg_path: Path to the .eg-hg file
            output_path: Path for the output YAML file
            
        Returns:
            True if conversion successful, False otherwise
        """
        try:
            with open(eg_hg_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # Try to parse as YAML first (newer format)
            try:
                data = yaml.safe_load(content)
                if isinstance(data, dict) and 'metadata' in data:
                    # Already in YAML format, just validate and copy
                    validation_result = validate_yaml_content(content)
                    if validation_result['valid']:
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"Copied valid YAML: {eg_hg_path} -> {output_path}")
                        return True
                    else:
                        print(f"Warning: Invalid YAML format in {eg_hg_path}")
                        return False
            except yaml.YAMLError:
                pass  # Not YAML, try custom format
            
            # Try to parse as custom format
            # This is a simplified parser for the custom format
            parsed_data = self._parse_custom_eg_hg_format(content)
            if parsed_data:
                # Convert to canonical YAML
                metadata = self._generate_metadata_from_path(eg_hg_path)
                yaml_content = self._convert_parsed_data_to_yaml(parsed_data, metadata)
                
                # Validate
                validation_result = validate_yaml_content(yaml_content)
                if validation_result['valid']:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(yaml_content)
                    print(f"Converted custom format: {eg_hg_path} -> {output_path}")
                    return True
                else:
                    print(f"Error: Generated YAML is invalid for {eg_hg_path}")
                    return False
            
            print(f"Warning: Could not parse {eg_hg_path} in any known format")
            return False
            
        except Exception as e:
            print(f"Error converting {eg_hg_path}: {e}")
            return False
    
    def convert_corpus_directory(self, corpus_dir: Path, output_dir: Path) -> Dict[str, Any]:
        """
        Convert an entire corpus directory to YAML format.
        
        Args:
            corpus_dir: Path to the corpus directory
            output_dir: Path to the output directory
            
        Returns:
            Dictionary with conversion statistics
        """
        self.conversion_stats = {'processed': 0, 'successful': 0, 'failed': 0, 'skipped': 0}
        
        # Find all CLIF and .eg-hg files
        clif_files = list(corpus_dir.glob('**/*.clif'))
        eg_hg_files = list(corpus_dir.glob('**/*.eg-hg'))
        
        print(f"Found {len(clif_files)} CLIF files and {len(eg_hg_files)} .eg-hg files")
        
        # Convert CLIF files
        for clif_file in clif_files:
            self.conversion_stats['processed'] += 1
            
            # Generate output path
            relative_path = clif_file.relative_to(corpus_dir)
            output_path = output_dir / relative_path.with_suffix('.yaml')
            
            # Load metadata if available
            metadata = self._load_metadata_for_file(clif_file)
            
            if self.convert_clif_to_yaml(clif_file, output_path, metadata):
                self.conversion_stats['successful'] += 1
            else:
                self.conversion_stats['failed'] += 1
        
        # Convert .eg-hg files (only if no corresponding CLIF file)
        for eg_hg_file in eg_hg_files:
            clif_equivalent = eg_hg_file.with_suffix('.clif')
            if clif_equivalent.exists():
                continue  # Skip, already converted from CLIF
            
            self.conversion_stats['processed'] += 1
            
            # Generate output path
            relative_path = eg_hg_file.relative_to(corpus_dir)
            output_path = output_dir / relative_path.with_suffix('.yaml')
            
            if self.convert_existing_eg_hg_to_yaml(eg_hg_file, output_path):
                self.conversion_stats['successful'] += 1
            else:
                self.conversion_stats['failed'] += 1
        
        # Create corpus index
        self._create_corpus_index(output_dir)
        
        return self.conversion_stats
    
    def _generate_metadata_from_path(self, file_path: Path, 
                                   content: Optional[str] = None) -> Dict[str, Any]:
        """Generate metadata from file path and content."""
        stem = file_path.stem
        
        # Extract information from filename
        metadata = {
            'id': stem,
            'title': stem.replace('_', ' ').title(),
            'format_version': '1.0'
        }
        
        # Ensure title is always present and non-empty
        if not metadata.get('title'):
            metadata['title'] = f"Example {stem}"
        
        # Try to extract scholarly information from filename
        if 'peirce' in stem.lower():
            metadata['source'] = {
                'author': 'Charles Sanders Peirce',
                'work': 'Collected Papers'
            }
            if 'cp_' in stem:
                parts = stem.split('_')
                for i, part in enumerate(parts):
                    if part == 'cp' and i + 1 < len(parts):
                        metadata['source']['volume'] = parts[i + 1]
                        if i + 2 < len(parts):
                            metadata['source']['section'] = parts[i + 2]
            
            # Better title for Peirce examples
            if 'man_mortal' in stem.lower():
                metadata['title'] = "Peirce's Man-Mortal Implication"
                metadata['description'] = "Classic example demonstrating implication in Existential Graphs"
        
        elif 'roberts' in stem.lower():
            metadata['source'] = {
                'author': 'Don D. Roberts',
                'work': 'The Existential Graphs of Charles S. Peirce',
                'year': 1973
            }
        
        elif 'sowa' in stem.lower():
            metadata['source'] = {
                'author': 'John F. Sowa',
                'work': 'Knowledge Representation',
                'year': 2000
            }
        
        elif 'dau' in stem.lower():
            metadata['source'] = {
                'author': 'Frithjof Dau',
                'work': 'The Logic System of Concept Graphs with Negation',
                'year': 2003
            }
        
        # Infer logical pattern from content or filename
        if content:
            content_lower = content.lower()
            if 'forall' in content_lower and 'if' in content_lower:
                metadata['logical_pattern'] = 'implication'
                metadata['logical_form'] = content.strip()
            elif 'forall' in content_lower:
                metadata['logical_pattern'] = 'quantification'
                metadata['logical_form'] = content.strip()
            elif 'exists' in content_lower:
                metadata['logical_pattern'] = 'quantification'
                metadata['logical_form'] = content.strip()
            elif 'and' in content_lower:
                metadata['logical_pattern'] = 'conjunction'
                metadata['logical_form'] = content.strip()
            elif 'or' in content_lower:
                metadata['logical_pattern'] = 'disjunction'
                metadata['logical_form'] = content.strip()
            elif 'not' in content_lower:
                metadata['logical_pattern'] = 'negation'
                metadata['logical_form'] = content.strip()
            else:
                metadata['logical_form'] = content.strip()
        
        # Infer from filename
        if 'implication' in stem.lower() or 'mortal' in stem.lower():
            metadata['logical_pattern'] = 'implication'
        elif 'disjunction' in stem.lower():
            metadata['logical_pattern'] = 'disjunction'
        elif 'quantification' in stem.lower():
            metadata['logical_pattern'] = 'quantification'
        elif 'ligature' in stem.lower():
            metadata['logical_pattern'] = 'identity'
        
        return metadata
    
    def _load_metadata_for_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load metadata from a corresponding JSON file if it exists."""
        json_path = file_path.with_suffix('.json')
        if json_path.exists():
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return None
    
    def _parse_custom_eg_hg_format(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse the custom EG-HG format (simplified parser)."""
        # This is a basic parser for the custom format
        # In a full implementation, this would be more robust
        lines = content.strip().split('\n')
        
        data = {
            'entities': {},
            'predicates': {},
            'contexts': {},
            'ligatures': []
        }
        
        current_section = None
        current_item = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('CONTEXT'):
                current_section = 'contexts'
                parts = line.split()
                if len(parts) >= 2:
                    current_item = parts[1]
                    data['contexts'][current_item] = {'type': 'sheet_of_assertion', 'nesting_level': 0}
            
            elif line.startswith('PREDICATE'):
                current_section = 'predicates'
                parts = line.split()
                if len(parts) >= 2:
                    current_item = parts[1]
                    data['predicates'][current_item] = {'entities': [], 'type': 'relation'}
            
            elif line.startswith('ENTITY'):
                current_section = 'entities'
                parts = line.split()
                if len(parts) >= 2:
                    current_item = parts[1]
                    data['entities'][current_item] = {'type': 'variable'}
            
            elif current_item and current_section:
                # Parse properties
                if line.startswith('NAME'):
                    name = line.split(None, 1)[1] if len(line.split(None, 1)) > 1 else ''
                    if current_section == 'predicates':
                        data['predicates'][current_item]['name'] = name
                    elif current_section == 'entities':
                        data['entities'][current_item]['name'] = name
                
                elif line.startswith('ARITY'):
                    arity = int(line.split()[1]) if len(line.split()) > 1 else 0
                    if current_section == 'predicates':
                        data['predicates'][current_item]['arity'] = arity
                
                elif line.startswith('TYPE'):
                    type_val = line.split()[1] if len(line.split()) > 1 else ''
                    if current_section == 'contexts':
                        data['contexts'][current_item]['type'] = type_val
                    elif current_section == 'entities':
                        data['entities'][current_item]['type'] = type_val
        
        return data if any(data.values()) else None
    
    def _convert_parsed_data_to_yaml(self, data: Dict[str, Any], 
                                   metadata: Dict[str, Any]) -> str:
        """Convert parsed custom format data to YAML."""
        yaml_data = {
            'metadata': metadata,
            'entities': data.get('entities', {}),
            'predicates': data.get('predicates', {}),
            'contexts': data.get('contexts', {}),
            'ligatures': data.get('ligatures', [])
        }
        
        return yaml.dump(yaml_data, default_flow_style=False, sort_keys=False, 
                        allow_unicode=True, width=120, indent=2)
    
    def _create_corpus_index(self, output_dir: Path) -> None:
        """Create an index of all YAML files in the corpus."""
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        yaml_files = list(output_dir.glob('**/*.yaml'))
        
        index = {
            'corpus_info': {
                'name': 'EG-HG Corpus',
                'description': 'Collection of Existential Graph examples in canonical YAML format',
                'format_version': '1.0',
                'total_examples': len(yaml_files)
            },
            'examples': []
        }
        
        for yaml_file in sorted(yaml_files):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                if data and 'metadata' in data:
                    relative_path = yaml_file.relative_to(output_dir)
                    example_info = {
                        'file': str(relative_path),
                        'id': data['metadata'].get('id', yaml_file.stem),
                        'title': data['metadata'].get('title', ''),
                        'logical_pattern': data['metadata'].get('logical_pattern', 'unknown')
                    }
                    
                    if 'source' in data['metadata']:
                        example_info['source'] = data['metadata']['source']
                    
                    index['examples'].append(example_info)
            
            except Exception as e:
                print(f"Warning: Could not index {yaml_file}: {e}")
        
        # Write index
        index_path = output_dir / 'corpus_index.yaml'
        with open(index_path, 'w', encoding='utf-8') as f:
            yaml.dump(index, f, default_flow_style=False, sort_keys=False, 
                     allow_unicode=True, width=120, indent=2)
        
        print(f"Created corpus index: {index_path}")


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description='Convert corpus files to canonical YAML format')
    parser.add_argument('input_dir', type=Path, help='Input corpus directory')
    parser.add_argument('output_dir', type=Path, help='Output directory for YAML files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if not args.input_dir.exists():
        print(f"Error: Input directory does not exist: {args.input_dir}")
        sys.exit(1)
    
    converter = CorpusConverter()
    
    print(f"Converting corpus from {args.input_dir} to {args.output_dir}")
    stats = converter.convert_corpus_directory(args.input_dir, args.output_dir)
    
    print("\nConversion Summary:")
    print(f"  Processed: {stats['processed']}")
    print(f"  Successful: {stats['successful']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Skipped: {stats['skipped']}")
    
    if stats['failed'] > 0:
        print(f"\nWarning: {stats['failed']} files failed to convert")
        sys.exit(1)
    else:
        print("\nAll files converted successfully!")


if __name__ == '__main__':
    main()

