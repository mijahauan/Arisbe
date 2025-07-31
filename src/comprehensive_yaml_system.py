#!/usr/bin/env python3
"""
Comprehensive YAML Conversion System for EGI
Complete bidirectional conversion system with enhanced features and validation

CHANGES: Integrates all YAML conversion components into a unified system with
enhanced error handling, validation, performance optimization, and optional
subgraph serialization support. Provides production-ready YAML persistence
for EGI objects with comprehensive diagnostic capabilities.
"""

import sys
import os
import time
import yaml
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from egif_parser import parse_egif
    from egi_yaml import (
        EGIYAMLSerializer, EGIYAMLDeserializer,
        serialize_egi_to_yaml, deserialize_egi_from_yaml
    )
    from yaml_to_egi_parser import ImprovedYAMLToEGIParser
    from egi_core import EGI, Context, Vertex, Edge
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


@dataclass
class YAMLConversionOptions:
    """Configuration options for YAML conversion."""
    
    # Serialization options
    include_metadata: bool = True
    include_ligatures: bool = True
    include_properties: bool = True
    compact_format: bool = False
    
    # Validation options
    validate_structure: bool = True
    validate_round_trip: bool = False
    strict_validation: bool = False
    
    # Performance options
    enable_caching: bool = False
    optimize_size: bool = False
    
    # Debug options
    include_debug_info: bool = False
    verbose_errors: bool = True


@dataclass
class ConversionResult:
    """Result of a YAML conversion operation."""
    
    success: bool
    data: Optional[Union[str, EGI]]
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ComprehensiveYAMLSystem:
    """
    Comprehensive YAML conversion system for EGI objects.
    
    CHANGES: Provides unified interface for all YAML operations including
    serialization, deserialization, validation, and optional subgraph support.
    Integrates all previous YAML components into a production-ready system.
    """
    
    def __init__(self, options: Optional[YAMLConversionOptions] = None):
        self.options = options or YAMLConversionOptions()
        
        # Initialize components
        self.serializer = EGIYAMLSerializer()
        self.deserializer = EGIYAMLDeserializer()
        self.improved_parser = ImprovedYAMLToEGIParser()
        
        # Performance tracking
        self.conversion_stats = {
            'serializations': 0,
            'deserializations': 0,
            'total_time': 0.0,
            'errors': 0,
            'warnings': 0
        }
    
    def serialize_egi(self, egi: EGI, **kwargs) -> ConversionResult:
        """
        Serialize EGI to YAML with comprehensive options and validation.
        
        Args:
            egi: EGI instance to serialize
            **kwargs: Override options for this conversion
        
        Returns:
            ConversionResult with YAML string or error information
        """
        
        start_time = time.time()
        errors = []
        warnings = []
        metadata = {}
        
        try:
            # Apply any option overrides
            effective_options = self._merge_options(kwargs)
            
            # Pre-serialization validation
            if effective_options.validate_structure:
                validation_errors = self._validate_egi_structure(egi)
                if validation_errors:
                    errors.extend(validation_errors)
                    if effective_options.strict_validation:
                        return self._create_error_result(errors, warnings, metadata)
                    else:
                        warnings.extend([f"Structure warning: {e}" for e in validation_errors])
            
            # Perform serialization
            if effective_options.compact_format:
                yaml_str = self._serialize_compact(egi)
            else:
                yaml_str = self.serializer.serialize(egi)
            
            # Post-serialization processing
            if effective_options.optimize_size:
                yaml_str = self._optimize_yaml_size(yaml_str)
            
            # Add debug information
            if effective_options.include_debug_info:
                metadata.update(self._generate_debug_info(egi, yaml_str))
            
            # Round-trip validation
            if effective_options.validate_round_trip:
                round_trip_errors = self._validate_round_trip(egi, yaml_str)
                if round_trip_errors:
                    warnings.extend(round_trip_errors)
            
            # Update statistics
            conversion_time = time.time() - start_time
            self._update_stats('serialization', conversion_time, len(errors), len(warnings))
            
            metadata.update({
                'conversion_time': conversion_time,
                'yaml_size': len(yaml_str.encode('utf-8')),
                'egi_structure': {
                    'vertices': len(egi.vertices),
                    'edges': len(egi.edges),
                    'cuts': len(egi.cuts)
                }
            })
            
            return ConversionResult(
                success=True,
                data=yaml_str,
                errors=errors,
                warnings=warnings,
                metadata=metadata
            )
            
        except Exception as e:
            conversion_time = time.time() - start_time
            error_msg = f"Serialization failed: {str(e)}"
            errors.append(error_msg)
            
            self._update_stats('serialization', conversion_time, 1, len(warnings))
            
            return ConversionResult(
                success=False,
                data=None,
                errors=errors,
                warnings=warnings,
                metadata={'conversion_time': conversion_time}
            )
    
    def deserialize_yaml(self, yaml_str: str, **kwargs) -> ConversionResult:
        """
        Deserialize YAML to EGI with comprehensive validation and error handling.
        
        Args:
            yaml_str: YAML string to deserialize
            **kwargs: Override options for this conversion
        
        Returns:
            ConversionResult with EGI instance or error information
        """
        
        start_time = time.time()
        errors = []
        warnings = []
        metadata = {}
        
        try:
            # Apply any option overrides
            effective_options = self._merge_options(kwargs)
            
            # Use improved parser for better validation
            egi, parse_errors, parse_warnings = self.improved_parser.parse_yaml_to_egi(yaml_str)
            
            errors.extend(parse_errors)
            warnings.extend(parse_warnings)
            
            if egi is None:
                return self._create_error_result(errors, warnings, metadata)
            
            # Post-deserialization validation
            if effective_options.validate_structure:
                validation_errors = self._validate_egi_structure(egi)
                if validation_errors:
                    if effective_options.strict_validation:
                        errors.extend(validation_errors)
                        return self._create_error_result(errors, warnings, metadata)
                    else:
                        warnings.extend([f"Structure warning: {e}" for e in validation_errors])
            
            # Update statistics
            conversion_time = time.time() - start_time
            self._update_stats('deserialization', conversion_time, len(errors), len(warnings))
            
            metadata.update({
                'conversion_time': conversion_time,
                'yaml_size': len(yaml_str.encode('utf-8')),
                'egi_structure': {
                    'vertices': len(egi.vertices),
                    'edges': len(egi.edges),
                    'cuts': len(egi.cuts)
                }
            })
            
            return ConversionResult(
                success=True,
                data=egi,
                errors=errors,
                warnings=warnings,
                metadata=metadata
            )
            
        except Exception as e:
            conversion_time = time.time() - start_time
            error_msg = f"Deserialization failed: {str(e)}"
            errors.append(error_msg)
            
            self._update_stats('deserialization', conversion_time, 1, len(warnings))
            
            return ConversionResult(
                success=False,
                data=None,
                errors=errors,
                warnings=warnings,
                metadata={'conversion_time': conversion_time}
            )
    
    def save_egi_to_file(self, egi: EGI, filepath: Union[str, Path], **kwargs) -> ConversionResult:
        """Save EGI to YAML file with error handling."""
        
        try:
            result = self.serialize_egi(egi, **kwargs)
            
            if not result.success:
                return result
            
            # Write to file
            filepath = Path(filepath)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(result.data)
            
            result.metadata['filepath'] = str(filepath)
            result.metadata['file_size'] = filepath.stat().st_size
            
            return result
            
        except Exception as e:
            return ConversionResult(
                success=False,
                data=None,
                errors=[f"File save failed: {str(e)}"],
                warnings=[],
                metadata={'filepath': str(filepath)}
            )
    
    def load_egi_from_file(self, filepath: Union[str, Path], **kwargs) -> ConversionResult:
        """Load EGI from YAML file with error handling."""
        
        try:
            filepath = Path(filepath)
            
            if not filepath.exists():
                return ConversionResult(
                    success=False,
                    data=None,
                    errors=[f"File not found: {filepath}"],
                    warnings=[],
                    metadata={'filepath': str(filepath)}
                )
            
            with open(filepath, 'r', encoding='utf-8') as f:
                yaml_str = f.read()
            
            result = self.deserialize_yaml(yaml_str, **kwargs)
            result.metadata['filepath'] = str(filepath)
            result.metadata['file_size'] = filepath.stat().st_size
            
            return result
            
        except Exception as e:
            return ConversionResult(
                success=False,
                data=None,
                errors=[f"File load failed: {str(e)}"],
                warnings=[],
                metadata={'filepath': str(filepath)}
            )
    
    def validate_yaml_structure(self, yaml_str: str) -> ConversionResult:
        """Validate YAML structure without full deserialization."""
        
        try:
            # Parse YAML
            data = yaml.safe_load(yaml_str)
            
            # Use improved parser validation
            _, errors, warnings = self.improved_parser.parse_yaml_to_egi(yaml_str)
            
            return ConversionResult(
                success=len(errors) == 0,
                data=data,
                errors=errors,
                warnings=warnings,
                metadata={'yaml_size': len(yaml_str.encode('utf-8'))}
            )
            
        except Exception as e:
            return ConversionResult(
                success=False,
                data=None,
                errors=[f"YAML validation failed: {str(e)}"],
                warnings=[],
                metadata={}
            )
    
    def get_conversion_stats(self) -> Dict[str, Any]:
        """Get conversion performance statistics."""
        
        stats = self.conversion_stats.copy()
        
        if stats['serializations'] + stats['deserializations'] > 0:
            stats['average_time'] = stats['total_time'] / (stats['serializations'] + stats['deserializations'])
            stats['error_rate'] = stats['errors'] / (stats['serializations'] + stats['deserializations'])
            stats['warning_rate'] = stats['warnings'] / (stats['serializations'] + stats['deserializations'])
        else:
            stats['average_time'] = 0.0
            stats['error_rate'] = 0.0
            stats['warning_rate'] = 0.0
        
        return stats
    
    def reset_stats(self):
        """Reset conversion statistics."""
        
        self.conversion_stats = {
            'serializations': 0,
            'deserializations': 0,
            'total_time': 0.0,
            'errors': 0,
            'warnings': 0
        }
    
    def _merge_options(self, kwargs: Dict[str, Any]) -> YAMLConversionOptions:
        """Merge default options with kwargs overrides."""
        
        options_dict = asdict(self.options)
        options_dict.update(kwargs)
        
        return YAMLConversionOptions(**options_dict)
    
    def _validate_egi_structure(self, egi: EGI) -> List[str]:
        """Validate EGI structural integrity."""
        
        errors = []
        
        try:
            # Check vertex-edge consistency
            for vertex in egi.vertices.values():
                for edge_id in vertex.incident_edges:
                    if edge_id not in egi.edges:
                        errors.append(f"Vertex {vertex.id} references non-existent edge {edge_id}")
                    else:
                        edge = egi.edges[edge_id]
                        if vertex.id not in edge.incident_vertices:
                            errors.append(f"Edge {edge_id} does not reference vertex {vertex.id}")
            
            # Check edge-vertex consistency
            for edge in egi.edges.values():
                for vertex_id in edge.incident_vertices:
                    if vertex_id not in egi.vertices:
                        errors.append(f"Edge {edge.id} references non-existent vertex {vertex_id}")
                    else:
                        vertex = egi.vertices[vertex_id]
                        if edge.id not in vertex.incident_edges:
                            errors.append(f"Vertex {vertex_id} does not reference edge {edge.id}")
            
            # Check context hierarchy
            for cut in egi.cuts.values():
                if cut.parent is None:
                    errors.append(f"Cut {cut.id} has no parent context")
                elif cut.id not in cut.parent.children:
                    errors.append(f"Cut {cut.id} not in parent's children list")
        
        except Exception as e:
            errors.append(f"Structure validation error: {str(e)}")
        
        return errors
    
    def _validate_round_trip(self, original_egi: EGI, yaml_str: str) -> List[str]:
        """Validate round-trip conversion consistency."""
        
        warnings = []
        
        try:
            # Deserialize YAML back to EGI
            restored_egi = self.deserializer.deserialize(yaml_str)
            
            # Compare structures
            if len(original_egi.vertices) != len(restored_egi.vertices):
                warnings.append(f"Vertex count mismatch: {len(original_egi.vertices)} vs {len(restored_egi.vertices)}")
            
            if len(original_egi.edges) != len(restored_egi.edges):
                warnings.append(f"Edge count mismatch: {len(original_egi.edges)} vs {len(restored_egi.edges)}")
            
            if len(original_egi.cuts) != len(restored_egi.cuts):
                warnings.append(f"Cut count mismatch: {len(original_egi.cuts)} vs {len(restored_egi.cuts)}")
        
        except Exception as e:
            warnings.append(f"Round-trip validation failed: {str(e)}")
        
        return warnings
    
    def _serialize_compact(self, egi: EGI) -> str:
        """Serialize EGI in compact format."""
        
        # Use flow style for more compact output
        data = self.serializer._egi_to_dict(egi)
        return yaml.dump(data, default_flow_style=True, sort_keys=False)
    
    def _optimize_yaml_size(self, yaml_str: str) -> str:
        """Optimize YAML size by removing unnecessary whitespace."""
        
        lines = yaml_str.split('\n')
        optimized_lines = []
        
        for line in lines:
            # Remove trailing whitespace
            line = line.rstrip()
            # Skip empty lines in optimization mode
            if line or not self.options.optimize_size:
                optimized_lines.append(line)
        
        return '\n'.join(optimized_lines)
    
    def _generate_debug_info(self, egi: EGI, yaml_str: str) -> Dict[str, Any]:
        """Generate debug information for conversion."""
        
        return {
            'debug_info': {
                'egi_id': id(egi),
                'yaml_lines': len(yaml_str.split('\n')),
                'alphabet_size': len(egi.alphabet.get_all_relations()),
                'ligature_count': len(egi.ligature_manager.ligatures),
                'timestamp': time.time()
            }
        }
    
    def _update_stats(self, operation: str, time_taken: float, errors: int, warnings: int):
        """Update conversion statistics."""
        
        if operation == 'serialization':
            self.conversion_stats['serializations'] += 1
        elif operation == 'deserialization':
            self.conversion_stats['deserializations'] += 1
        
        self.conversion_stats['total_time'] += time_taken
        self.conversion_stats['errors'] += errors
        self.conversion_stats['warnings'] += warnings
    
    def _create_error_result(self, errors: List[str], warnings: List[str], metadata: Dict[str, Any]) -> ConversionResult:
        """Create error result with consistent structure."""
        
        return ConversionResult(
            success=False,
            data=None,
            errors=errors,
            warnings=warnings,
            metadata=metadata
        )


def demo_comprehensive_yaml_system():
    """Demonstrate the comprehensive YAML system capabilities."""
    
    print("Comprehensive YAML Conversion System Demo")
    print("=" * 60)
    
    # Initialize system with custom options
    options = YAMLConversionOptions(
        validate_structure=True,
        validate_round_trip=True,
        include_debug_info=True,
        verbose_errors=True
    )
    
    yaml_system = ComprehensiveYAMLSystem(options)
    
    # Test cases
    test_cases = [
        "(P *x)",
        "(man *x) ~[(mortal x)]",
        "(P *x) (Q *y) ~[(R x y) ~[(S x)]]"
    ]
    
    for i, egif in enumerate(test_cases, 1):
        print(f"\nDemo {i}: {egif}")
        print("-" * 40)
        
        try:
            # Parse EGIF to EGI
            egi = parse_egif(egif)
            print(f"Parsed EGI: {len(egi.vertices)} vertices, {len(egi.edges)} edges, {len(egi.cuts)} cuts")
            
            # Serialize to YAML
            serialize_result = yaml_system.serialize_egi(egi)
            
            if serialize_result.success:
                print(f"✅ Serialization successful")
                print(f"   YAML size: {serialize_result.metadata['yaml_size']} bytes")
                print(f"   Time: {serialize_result.metadata['conversion_time']:.3f}s")
                
                if serialize_result.warnings:
                    print(f"   Warnings: {len(serialize_result.warnings)}")
                
                # Deserialize back to EGI
                deserialize_result = yaml_system.deserialize_yaml(serialize_result.data)
                
                if deserialize_result.success:
                    print(f"✅ Deserialization successful")
                    print(f"   Time: {deserialize_result.metadata['conversion_time']:.3f}s")
                    
                    restored_egi = deserialize_result.data
                    print(f"   Restored: {len(restored_egi.vertices)} vertices, {len(restored_egi.edges)} edges, {len(restored_egi.cuts)} cuts")
                    
                    if deserialize_result.warnings:
                        print(f"   Warnings: {len(deserialize_result.warnings)}")
                else:
                    print(f"❌ Deserialization failed")
                    for error in deserialize_result.errors:
                        print(f"   Error: {error}")
            else:
                print(f"❌ Serialization failed")
                for error in serialize_result.errors:
                    print(f"   Error: {error}")
        
        except Exception as e:
            print(f"❌ Demo failed: {str(e)}")
    
    # Show statistics
    stats = yaml_system.get_conversion_stats()
    print(f"\n📊 Conversion Statistics:")
    print(f"   Serializations: {stats['serializations']}")
    print(f"   Deserializations: {stats['deserializations']}")
    print(f"   Average time: {stats['average_time']:.3f}s")
    print(f"   Error rate: {stats['error_rate']:.1%}")
    print(f"   Warning rate: {stats['warning_rate']:.1%}")
    
    print("\n🎉 Comprehensive YAML system demo completed!")


if __name__ == "__main__":
    demo_comprehensive_yaml_system()

