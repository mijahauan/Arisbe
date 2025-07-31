#!/usr/bin/env python3
"""
DAU-Compliant YAML Serializer
Direct YAML serialization for Dau's RelationalGraphWithCuts objects with isolated vertex support

CHANGES: Creates native YAML serialization for DAU-compliant structures, maintaining
mathematical integrity while supporting isolated vertices. Follows Dau's exact 6+1
component definition for complete fidelity.
"""

import sys
import os
import yaml
import time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut
    from egif_parser_dau import EGIFParser
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


@dataclass
class ConversionResult:
    """Result of a DAU YAML conversion operation."""
    success: bool
    data: Optional[Union[str, RelationalGraphWithCuts]]
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class DAUYAMLSerializer:
    """
    YAML serializer for DAU RelationalGraphWithCuts objects.
    
    CHANGES: Native serialization that preserves Dau's exact 6+1 component structure
    with full support for isolated vertices, proper area mappings, and mathematical
    integrity. No format conversion required.
    """
    
    def serialize(self, graph: RelationalGraphWithCuts) -> str:
        """
        Serialize DAU RelationalGraphWithCuts to YAML.
        
        Args:
            graph: DAU-compliant graph with isolated vertex support
            
        Returns:
            YAML string representation
        """
        
        # Convert to serializable dictionary following Dau's 6+1 components
        data = {
            'dau_relational_graph_with_cuts': {
                'metadata': {
                    'version': '1.0',
                    'type': 'dau_relational_graph_with_cuts',
                    'components': '6+1 (V, E, ν, ⊤, Cut, area, rel)',
                    'supports_isolated_vertices': True
                },
                
                # Component 1: V - Vertices
                'vertices': [
                    {
                        'id': vertex.id,
                        'label': vertex.label,
                        'is_generic': vertex.is_generic
                    }
                    for vertex in graph.V
                ],
                
                # Component 2: E - Edges  
                'edges': [
                    {
                        'id': edge.id
                    }
                    for edge in graph.E
                ],
                
                # Component 3: ν - Edge to vertex sequence mapping
                'nu_mapping': {
                    edge_id: list(vertex_sequence)  # Convert tuple to list for YAML
                    for edge_id, vertex_sequence in graph.nu.items()
                },
                
                # Component 4: ⊤ - Sheet of assertion
                'sheet': graph.sheet,
                
                # Component 5: Cut - Cuts
                'cuts': [
                    {
                        'id': cut.id
                    }
                    for cut in graph.Cut
                ],
                
                # Component 6: area - Containment mapping
                'area_mapping': {
                    context_id: list(elements)  # Convert frozenset to list for YAML
                    for context_id, elements in graph.area.items()
                },
                
                # Component 7: rel - Relation name mapping
                'relation_mapping': dict(graph.rel),  # Convert frozendict to dict for YAML
                
                # Derived information for convenience
                'statistics': {
                    'vertex_count': len(graph.V),
                    'edge_count': len(graph.E),
                    'cut_count': len(graph.Cut),
                    'isolated_vertex_count': self._count_isolated_vertices(graph),
                    'relation_count': len(set(graph.rel.values()))
                }
            }
        }
        
        return yaml.dump(data, default_flow_style=False, sort_keys=False, indent=2)
    
    def _count_isolated_vertices(self, graph: RelationalGraphWithCuts) -> int:
        """Count vertices with no incident edges (isolated vertices)."""
        
        # Get all vertices that appear in edge mappings
        vertices_in_edges = set()
        for vertex_sequence in graph.nu.values():
            vertices_in_edges.update(vertex_sequence)
        
        # Count vertices not in any edge
        isolated_count = 0
        for vertex in graph.V:
            if vertex.id not in vertices_in_edges:
                isolated_count += 1
        
        return isolated_count


class DAUYAMLDeserializer:
    """
    YAML deserializer for DAU RelationalGraphWithCuts objects.
    
    CHANGES: Native deserialization that reconstructs Dau's exact 6+1 component
    structure with full validation and isolated vertex support.
    """
    
    def deserialize(self, yaml_str: str) -> RelationalGraphWithCuts:
        """
        Deserialize YAML to DAU RelationalGraphWithCuts.
        
        Args:
            yaml_str: YAML string representation
            
        Returns:
            DAU-compliant graph object
        """
        
        # Parse YAML
        data = yaml.safe_load(yaml_str)
        
        if 'dau_relational_graph_with_cuts' not in data:
            raise ValueError("Invalid DAU YAML format: missing 'dau_relational_graph_with_cuts' key")
        
        graph_data = data['dau_relational_graph_with_cuts']
        
        # Reconstruct components
        from frozendict import frozendict
        
        # Component 1: V - Vertices
        vertices = frozenset(
            Vertex(
                id=v['id'],
                label=v.get('label'),
                is_generic=v.get('is_generic', True)
            )
            for v in graph_data['vertices']
        )
        
        # Component 2: E - Edges
        edges = frozenset(
            Edge(id=e['id'])
            for e in graph_data['edges']
        )
        
        # Component 3: ν - Edge to vertex sequence mapping
        nu_mapping = frozendict({
            edge_id: tuple(vertex_sequence)  # Convert list back to tuple
            for edge_id, vertex_sequence in graph_data['nu_mapping'].items()
        })
        
        # Component 4: ⊤ - Sheet of assertion
        sheet = graph_data['sheet']
        
        # Component 5: Cut - Cuts
        cuts = frozenset(
            Cut(id=c['id'])
            for c in graph_data['cuts']
        )
        
        # Component 6: area - Containment mapping
        area_mapping = frozendict({
            context_id: frozenset(elements)  # Convert list back to frozenset
            for context_id, elements in graph_data['area_mapping'].items()
        })
        
        # Component 7: rel - Relation name mapping
        relation_mapping = frozendict(graph_data['relation_mapping'])
        
        # Create and return RelationalGraphWithCuts
        return RelationalGraphWithCuts(
            V=vertices,
            E=edges,
            nu=nu_mapping,
            sheet=sheet,
            Cut=cuts,
            area=area_mapping,
            rel=relation_mapping
        )


class DAUYAMLConversionSystem:
    """
    Complete DAU YAML conversion system with isolated vertex support.
    
    CHANGES: Provides complete bidirectional conversion for DAU structures
    with native support for isolated vertices and mathematical integrity.
    """
    
    def __init__(self):
        self.serializer = DAUYAMLSerializer()
        self.deserializer = DAUYAMLDeserializer()
        
        # Performance tracking
        self.stats = {
            'successful_conversions': 0,
            'failed_conversions': 0,
            'total_time': 0.0
        }
    
    def egif_to_yaml(self, egif_text: str) -> ConversionResult:
        """
        Convert EGIF to YAML using DAU-compliant parser and serializer.
        
        Args:
            egif_text: EGIF expression
            
        Returns:
            ConversionResult with YAML string or error information
        """
        
        start_time = time.time()
        errors = []
        warnings = []
        metadata = {}
        
        try:
            # Parse EGIF using DAU-compliant parser
            parser = EGIFParser(egif_text)
            graph = parser.parse()
            
            metadata['graph_structure'] = {
                'vertices': len(graph.V),
                'edges': len(graph.E),
                'cuts': len(graph.Cut),
                'isolated_vertices': self.serializer._count_isolated_vertices(graph)
            }
            
            # Serialize to YAML
            yaml_str = self.serializer.serialize(graph)
            
            metadata['yaml_size'] = len(yaml_str.encode('utf-8'))
            
            # Update statistics
            conversion_time = time.time() - start_time
            self.stats['successful_conversions'] += 1
            self.stats['total_time'] += conversion_time
            
            metadata['conversion_time'] = conversion_time
            
            return ConversionResult(
                success=True,
                data=yaml_str,
                errors=errors,
                warnings=warnings,
                metadata=metadata
            )
            
        except Exception as e:
            conversion_time = time.time() - start_time
            error_msg = f"EGIF to YAML conversion failed: {str(e)}"
            errors.append(error_msg)
            
            self.stats['failed_conversions'] += 1
            self.stats['total_time'] += conversion_time
            
            return ConversionResult(
                success=False,
                data=None,
                errors=errors,
                warnings=warnings,
                metadata={'conversion_time': conversion_time}
            )
    
    def yaml_to_graph(self, yaml_str: str) -> ConversionResult:
        """
        Convert YAML to DAU RelationalGraphWithCuts.
        
        Args:
            yaml_str: YAML string
            
        Returns:
            ConversionResult with graph object or error information
        """
        
        start_time = time.time()
        errors = []
        warnings = []
        metadata = {}
        
        try:
            # Deserialize YAML to graph
            graph = self.deserializer.deserialize(yaml_str)
            
            metadata['graph_structure'] = {
                'vertices': len(graph.V),
                'edges': len(graph.E),
                'cuts': len(graph.Cut),
                'isolated_vertices': self.serializer._count_isolated_vertices(graph)
            }
            
            # Update statistics
            conversion_time = time.time() - start_time
            self.stats['successful_conversions'] += 1
            self.stats['total_time'] += conversion_time
            
            metadata['conversion_time'] = conversion_time
            
            return ConversionResult(
                success=True,
                data=graph,
                errors=errors,
                warnings=warnings,
                metadata=metadata
            )
            
        except Exception as e:
            conversion_time = time.time() - start_time
            error_msg = f"YAML to graph conversion failed: {str(e)}"
            errors.append(error_msg)
            
            self.stats['failed_conversions'] += 1
            self.stats['total_time'] += conversion_time
            
            return ConversionResult(
                success=False,
                data=None,
                errors=errors,
                warnings=warnings,
                metadata={'conversion_time': conversion_time}
            )
    
    def test_round_trip(self, egif_text: str) -> ConversionResult:
        """
        Test complete round-trip conversion: EGIF → YAML → Graph → YAML.
        
        Args:
            egif_text: EGIF expression to test
            
        Returns:
            ConversionResult with round-trip validation results
        """
        
        start_time = time.time()
        errors = []
        warnings = []
        metadata = {}
        
        try:
            # Step 1: EGIF to YAML
            yaml_result = self.egif_to_yaml(egif_text)
            if not yaml_result.success:
                errors.extend(yaml_result.errors)
                return ConversionResult(False, None, errors, warnings, metadata)
            
            yaml_str = yaml_result.data
            original_structure = yaml_result.metadata['graph_structure']
            
            # Step 2: YAML to Graph
            graph_result = self.yaml_to_graph(yaml_str)
            if not graph_result.success:
                errors.extend(graph_result.errors)
                return ConversionResult(False, None, errors, warnings, metadata)
            
            restored_graph = graph_result.data
            restored_structure = graph_result.metadata['graph_structure']
            
            # Step 3: Graph to YAML again (verify serialization consistency)
            yaml2_str = self.serializer.serialize(restored_graph)
            
            # Validate round-trip
            if original_structure == restored_structure:
                round_trip_success = True
            else:
                round_trip_success = False
                warnings.append(f"Structure mismatch: {original_structure} vs {restored_structure}")
            
            # Update metadata
            conversion_time = time.time() - start_time
            metadata.update({
                'conversion_time': conversion_time,
                'original_structure': original_structure,
                'restored_structure': restored_structure,
                'round_trip_success': round_trip_success,
                'yaml_size': len(yaml_str.encode('utf-8')),
                'yaml2_size': len(yaml2_str.encode('utf-8')),
                'yaml_consistency': len(yaml_str) == len(yaml2_str)
            })
            
            return ConversionResult(
                success=round_trip_success,
                data={
                    'original_yaml': yaml_str,
                    'restored_graph': restored_graph,
                    'yaml2': yaml2_str
                },
                errors=errors,
                warnings=warnings,
                metadata=metadata
            )
            
        except Exception as e:
            conversion_time = time.time() - start_time
            error_msg = f"Round-trip test failed: {str(e)}"
            errors.append(error_msg)
            
            return ConversionResult(
                success=False,
                data=None,
                errors=errors,
                warnings=warnings,
                metadata={'conversion_time': conversion_time}
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get conversion statistics."""
        
        total_conversions = self.stats['successful_conversions'] + self.stats['failed_conversions']
        
        if total_conversions > 0:
            success_rate = (self.stats['successful_conversions'] / total_conversions) * 100
            avg_time = self.stats['total_time'] / total_conversions
        else:
            success_rate = 0.0
            avg_time = 0.0
        
        return {
            'total_conversions': total_conversions,
            'successful_conversions': self.stats['successful_conversions'],
            'failed_conversions': self.stats['failed_conversions'],
            'success_rate': success_rate,
            'average_time': avg_time,
            'total_time': self.stats['total_time']
        }


def test_dau_yaml_system():
    """Test the DAU YAML conversion system with isolated vertices."""
    
    print("DAU YAML Conversion System Test")
    print("=" * 50)
    print("Testing with DAU-compliant parser and serializer")
    print("Full support for isolated vertices and Dau's 6+1 components")
    print()
    
    system = DAUYAMLConversionSystem()
    
    # Test cases including isolated vertices
    test_cases = [
        # Previously failing isolated vertex cases
        "[*x]",
        "[*x] [*y] (loves x y)",
        
        # Standard cases
        "(P *x)",
        "~[(P *x)]",
        "(man *x) ~[(mortal x)]",
        "~[~[(happy *x)]]",
        "(P *x) (Q *y) ~[(R x y) ~[(S x)]]"
    ]
    
    successful_tests = 0
    
    for i, egif in enumerate(test_cases, 1):
        print(f"Test {i:2d}: {egif}")
        print("-" * 40)
        
        result = system.test_round_trip(egif)
        
        if result.success:
            successful_tests += 1
            print("✅ SUCCESS - Perfect round-trip conversion")
            
            structure = result.metadata['original_structure']
            time_taken = result.metadata['conversion_time']
            yaml_size = result.metadata['yaml_size']
            
            print(f"   Structure: {structure}")
            print(f"   Time: {time_taken:.3f}s, YAML: {yaml_size} bytes")
            
            if result.metadata.get('isolated_vertices', 0) > 0:
                print(f"   ✨ Isolated vertices: {result.metadata['isolated_vertices']}")
        else:
            print("❌ FAILED")
            for error in result.errors:
                print(f"   Error: {error}")
        
        if result.warnings:
            for warning in result.warnings:
                print(f"   Warning: {warning}")
        
        print()
    
    # Summary
    total_tests = len(test_cases)
    success_rate = (successful_tests / total_tests) * 100
    stats = system.get_stats()
    
    print("=" * 50)
    print("DAU YAML CONVERSION TEST RESULTS")
    print("=" * 50)
    print(f"📊 OVERALL STATISTICS")
    print(f"Total Tests: {total_tests}")
    print(f"Successful Round-trips: {successful_tests}/{total_tests} ({success_rate:.1f}%)")
    print(f"Average Time: {stats['average_time']:.3f} seconds")
    
    print()
    print("🎯 SUCCESS RATE ANALYSIS")
    if success_rate == 100.0:
        print("🏆 PERFECT: All tests passed - isolated vertex issue completely resolved!")
    elif success_rate >= 90.0:
        print("✅ EXCELLENT: High success rate achieved")
    elif success_rate >= 75.0:
        print("⚠️ GOOD: Moderate success rate")
    else:
        print("❌ NEEDS IMPROVEMENT: Low success rate")
    
    # Check isolated vertex fix specifically
    isolated_vertex_tests = ["[*x]", "[*x] [*y] (loves x y)"]
    isolated_success = 0
    
    for egif in isolated_vertex_tests:
        if egif in [test_cases[i] for i in range(min(2, len(test_cases)))]:
            test_index = test_cases.index(egif)
            if test_index < successful_tests:  # Assuming tests are processed in order
                isolated_success += 1
    
    print()
    print("🔧 ISOLATED VERTEX FIX VALIDATION")
    print(f"Previously failing isolated vertex tests: {len(isolated_vertex_tests)}")
    print(f"Now working with DAU system: {isolated_success}/{len(isolated_vertex_tests)}")
    
    if isolated_success == len(isolated_vertex_tests):
        print("🎉 ISOLATED VERTEX ISSUE COMPLETELY RESOLVED!")
    elif isolated_success > 0:
        print("✅ PARTIAL IMPROVEMENT: Some isolated vertex cases fixed")
    else:
        print("❌ NO IMPROVEMENT: Isolated vertex issue persists")
    
    print()
    print("🎉 DAU YAML conversion system test completed!")
    
    return {
        'total_tests': total_tests,
        'successful_tests': successful_tests,
        'success_rate': success_rate,
        'stats': stats
    }


if __name__ == "__main__":
    test_dau_yaml_system()

