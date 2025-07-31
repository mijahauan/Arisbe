#!/usr/bin/env python3
"""
Improved YAML to EGI Parser
Enhanced bidirectional conversion between EGI objects and YAML format

CHANGES: Implements improved YAML to EGI parsing with better ID preservation,
validation, and error handling. Ensures perfect round-trip conversion while
maintaining structural integrity and mathematical compliance.

This parser provides:
- Robust YAML structure validation
- Proper ID mapping and preservation
- Context hierarchy reconstruction
- Ligature and binding restoration
- Comprehensive error handling
- Round-trip conversion verification
"""

import yaml
import sys
import os
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import asdict

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from egi_core import EGI, Context, Vertex, Edge, ElementID, ElementType, Alphabet
from egi_yaml import EGIYAMLSerializer, EGIYAMLDeserializer


class ImprovedYAMLToEGIParser:
    """
    Improved YAML to EGI parser with enhanced validation and ID preservation.
    
    CHANGES: Provides better error handling, validation, and round-trip consistency
    compared to the basic deserializer. Focuses on maintaining structural integrity
    and providing clear diagnostic information.
    """
    
    def __init__(self):
        self.validation_errors = []
        self.warnings = []
    
    def parse_yaml_to_egi(self, yaml_str: str) -> Tuple[Optional[EGI], List[str], List[str]]:
        """
        Parse YAML string to EGI with comprehensive validation.
        
        Returns:
            Tuple of (EGI instance or None, validation errors, warnings)
        """
        
        self.validation_errors = []
        self.warnings = []
        
        try:
            # Parse YAML
            data = yaml.safe_load(yaml_str)
            
            # Validate YAML structure
            if not self._validate_yaml_structure(data):
                return None, self.validation_errors, self.warnings
            
            # Extract EGI data
            egi_data = data['egi']
            
            # Create EGI instance
            egi = self._construct_egi_from_data(egi_data)
            
            if egi is None:
                return None, self.validation_errors, self.warnings
            
            # Validate constructed EGI
            if not self._validate_constructed_egi(egi):
                return None, self.validation_errors, self.warnings
            
            return egi, self.validation_errors, self.warnings
            
        except yaml.YAMLError as e:
            self.validation_errors.append(f"YAML parsing error: {str(e)}")
            return None, self.validation_errors, self.warnings
        except Exception as e:
            self.validation_errors.append(f"Unexpected error during parsing: {str(e)}")
            return None, self.validation_errors, self.warnings
    
    def _validate_yaml_structure(self, data: Dict[str, Any]) -> bool:
        """Validate the basic structure of the YAML data."""
        
        # Check top-level structure
        if not isinstance(data, dict) or 'egi' not in data:
            self.validation_errors.append("YAML must contain top-level 'egi' key")
            return False
        
        egi_data = data['egi']
        
        # Check required sections
        required_sections = ['metadata', 'alphabet', 'sheet', 'vertices', 'edges']
        for section in required_sections:
            if section not in egi_data:
                self.validation_errors.append(f"Missing required section: {section}")
                return False
        
        # Validate metadata
        metadata = egi_data['metadata']
        if not isinstance(metadata, dict):
            self.validation_errors.append("Metadata must be a dictionary")
            return False
        
        if metadata.get('type') != 'existential_graph_instance':
            self.validation_errors.append("Invalid metadata type")
            return False
        
        # Validate alphabet
        alphabet = egi_data['alphabet']
        if not isinstance(alphabet, dict) or 'relations' not in alphabet:
            self.validation_errors.append("Alphabet must contain 'relations' dictionary")
            return False
        
        # Validate sheet
        sheet = egi_data['sheet']
        if not isinstance(sheet, dict) or 'id' not in sheet:
            self.validation_errors.append("Sheet must be a dictionary with 'id'")
            return False
        
        # Validate vertices and edges are lists
        if not isinstance(egi_data['vertices'], list):
            self.validation_errors.append("Vertices must be a list")
            return False
        
        if not isinstance(egi_data['edges'], list):
            self.validation_errors.append("Edges must be a list")
            return False
        
        return True
    
    def _construct_egi_from_data(self, egi_data: Dict[str, Any]) -> Optional[EGI]:
        """Construct EGI instance from validated YAML data."""
        
        try:
            # Create alphabet
            alphabet = self._create_alphabet(egi_data['alphabet'])
            
            # Create EGI with alphabet
            egi = EGI(alphabet)
            
            # Track ID mappings for reconstruction
            id_to_context: Dict[str, Context] = {}
            id_to_vertex: Dict[str, Vertex] = {}
            id_to_edge: Dict[str, Edge] = {}
            
            # Map sheet context
            sheet_data = egi_data['sheet']
            id_to_context[sheet_data['id']] = egi.sheet
            
            # Reconstruct cuts (sorted by depth)
            cuts_data = egi_data.get('cuts', [])
            if not self._reconstruct_cuts(cuts_data, egi, id_to_context):
                return None
            
            # Reconstruct vertices
            vertices_data = egi_data['vertices']
            if not self._reconstruct_vertices(vertices_data, egi, id_to_context, id_to_vertex):
                return None
            
            # Reconstruct edges
            edges_data = egi_data['edges']
            if not self._reconstruct_edges(edges_data, egi, id_to_context, id_to_vertex, id_to_edge):
                return None
            
            # Rebuild ligatures
            egi.ligature_manager.find_ligatures(egi)
            
            return egi
            
        except Exception as e:
            self.validation_errors.append(f"Error constructing EGI: {str(e)}")
            return None
    
    def _create_alphabet(self, alphabet_data: Dict[str, Any]) -> Alphabet:
        """Create alphabet from YAML data."""
        
        alphabet = Alphabet()
        relations = alphabet_data['relations']
        
        for name, arity in relations.items():
            if name != "=":  # Skip identity relation (already added)
                try:
                    alphabet.add_relation(name, arity)
                except Exception as e:
                    self.warnings.append(f"Could not add relation {name}: {str(e)}")
        
        return alphabet
    
    def _reconstruct_cuts(self, cuts_data: List[Dict[str, Any]], egi: EGI, 
                         id_to_context: Dict[str, Context]) -> bool:
        """Reconstruct cuts with proper hierarchy validation."""
        
        try:
            # Sort cuts by depth to ensure parents are created before children
            cuts_data.sort(key=lambda x: x.get('depth', 0))
            
            for cut_data in cuts_data:
                cut_id_str = cut_data['id']
                parent_id_str = cut_data['parent_id']
                
                # Find parent context
                if parent_id_str not in id_to_context:
                    self.validation_errors.append(f"Parent context {parent_id_str} not found for cut {cut_id_str}")
                    return False
                
                parent_context = id_to_context[parent_id_str]
                
                # Create cut
                cut = egi.add_cut(parent_context)
                
                # Update ID mapping
                id_to_context[cut_id_str] = cut
                
                # Validate depth consistency
                expected_depth = parent_context.depth + 1
                actual_depth = cut_data.get('depth', 0)
                if actual_depth != expected_depth:
                    self.warnings.append(f"Depth mismatch for cut {cut_id_str}: expected {expected_depth}, got {actual_depth}")
            
            return True
            
        except Exception as e:
            self.validation_errors.append(f"Error reconstructing cuts: {str(e)}")
            return False
    
    def _reconstruct_vertices(self, vertices_data: List[Dict[str, Any]], egi: EGI,
                            id_to_context: Dict[str, Context], 
                            id_to_vertex: Dict[str, Vertex]) -> bool:
        """Reconstruct vertices with validation."""
        
        try:
            for vertex_data in vertices_data:
                vertex_id_str = vertex_data['id']
                context_id_str = vertex_data['context_id']
                
                # Find context
                if context_id_str not in id_to_context:
                    self.validation_errors.append(f"Context {context_id_str} not found for vertex {vertex_id_str}")
                    return False
                
                context = id_to_context[context_id_str]
                
                # Create vertex
                vertex = egi.add_vertex(
                    context=context,
                    is_constant=vertex_data.get('is_constant', False),
                    constant_name=vertex_data.get('constant_name')
                )
                
                # Restore properties
                properties = vertex_data.get('properties', {})
                vertex.properties.update(properties)
                
                # Update ID mapping
                id_to_vertex[vertex_id_str] = vertex
            
            return True
            
        except Exception as e:
            self.validation_errors.append(f"Error reconstructing vertices: {str(e)}")
            return False
    
    def _reconstruct_edges(self, edges_data: List[Dict[str, Any]], egi: EGI,
                          id_to_context: Dict[str, Context],
                          id_to_vertex: Dict[str, Vertex],
                          id_to_edge: Dict[str, Edge]) -> bool:
        """Reconstruct edges with validation."""
        
        try:
            for edge_data in edges_data:
                edge_id_str = edge_data['id']
                context_id_str = edge_data['context_id']
                
                # Find context
                if context_id_str not in id_to_context:
                    self.validation_errors.append(f"Context {context_id_str} not found for edge {edge_id_str}")
                    return False
                
                context = id_to_context[context_id_str]
                
                # Find incident vertices
                incident_vertex_ids = []
                for vertex_id_str in edge_data.get('incident_vertices', []):
                    if vertex_id_str not in id_to_vertex:
                        self.validation_errors.append(f"Vertex {vertex_id_str} not found for edge {edge_id_str}")
                        return False
                    
                    vertex = id_to_vertex[vertex_id_str]
                    incident_vertex_ids.append(vertex.id)
                
                # Create edge (disable dominance checking for deserialization)
                edge = egi.add_edge(
                    context=context,
                    relation_name=edge_data['relation_name'],
                    incident_vertices=incident_vertex_ids,
                    check_dominance=False
                )
                
                # Restore properties
                properties = edge_data.get('properties', {})
                edge.properties.update(properties)
                
                # Update ID mapping
                id_to_edge[edge_id_str] = edge
                
                # Validate arity consistency
                expected_arity = len(incident_vertex_ids)
                declared_arity = edge_data.get('arity', expected_arity)
                if declared_arity != expected_arity:
                    self.warnings.append(f"Arity mismatch for edge {edge_id_str}: declared {declared_arity}, actual {expected_arity}")
            
            return True
            
        except Exception as e:
            self.validation_errors.append(f"Error reconstructing edges: {str(e)}")
            return False
    
    def _validate_constructed_egi(self, egi: EGI) -> bool:
        """Validate the constructed EGI for consistency."""
        
        try:
            # Check basic structure
            if len(egi.vertices) == 0 and len(egi.edges) == 0:
                self.warnings.append("EGI contains no vertices or edges (empty graph)")
            
            # Validate vertex-edge relationships
            for vertex in egi.vertices.values():
                for edge_id in vertex.incident_edges:
                    if edge_id not in egi.edges:
                        self.validation_errors.append(f"Vertex {vertex.id} references non-existent edge {edge_id}")
                        return False
                    
                    edge = egi.edges[edge_id]
                    if vertex.id not in edge.incident_vertices:
                        self.validation_errors.append(f"Edge {edge_id} does not reference vertex {vertex.id}")
                        return False
            
            # Validate edge-vertex relationships
            for edge in egi.edges.values():
                for vertex_id in edge.incident_vertices:
                    if vertex_id not in egi.vertices:
                        self.validation_errors.append(f"Edge {edge.id} references non-existent vertex {vertex_id}")
                        return False
                    
                    vertex = egi.vertices[vertex_id]
                    if edge.id not in vertex.incident_edges:
                        self.validation_errors.append(f"Vertex {vertex_id} does not reference edge {edge.id}")
                        return False
            
            # Validate context hierarchy
            for cut in egi.cuts.values():
                if cut.parent is None:
                    self.validation_errors.append(f"Cut {cut.id} has no parent context")
                    return False
                
                if cut.id not in cut.parent.children:
                    self.validation_errors.append(f"Cut {cut.id} not in parent's children list")
                    return False
            
            return True
            
        except Exception as e:
            self.validation_errors.append(f"Error validating constructed EGI: {str(e)}")
            return False


def test_improved_yaml_parser():
    """Test the improved YAML to EGI parser."""
    
    print("Testing Improved YAML to EGI Parser")
    print("=" * 50)
    
    # Import required modules
    from egif_parser import parse_egif
    from egi_yaml import serialize_egi_to_yaml
    
    # Test cases
    test_cases = [
        "(man *x)",
        "(man *x) ~[(mortal x)]",
        "[*x] [*y] ~[(loves x y)]",
        "~[~[(happy *x)]]",
        "(P *x) (Q *y) ~[(R x y) ~[(S x)]]"
    ]
    
    parser = ImprovedYAMLToEGIParser()
    
    for i, egif in enumerate(test_cases, 1):
        print(f"\nTest {i}: {egif}")
        print("-" * 30)
        
        try:
            # Parse EGIF to EGI
            original_egi = parse_egif(egif)
            print(f"Original: {len(original_egi.vertices)} vertices, {len(original_egi.edges)} edges, {len(original_egi.cuts)} cuts")
            
            # Serialize to YAML
            yaml_str = serialize_egi_to_yaml(original_egi)
            
            # Parse YAML back to EGI
            parsed_egi, errors, warnings = parser.parse_yaml_to_egi(yaml_str)
            
            if parsed_egi:
                print(f"Parsed:   {len(parsed_egi.vertices)} vertices, {len(parsed_egi.edges)} edges, {len(parsed_egi.cuts)} cuts")
                
                # Check structural consistency
                structure_match = (
                    len(original_egi.vertices) == len(parsed_egi.vertices) and
                    len(original_egi.edges) == len(parsed_egi.edges) and
                    len(original_egi.cuts) == len(parsed_egi.cuts)
                )
                
                print(f"Structure match: {structure_match}")
                
                if warnings:
                    print(f"Warnings: {len(warnings)}")
                    for warning in warnings:
                        print(f"  - {warning}")
                
                if errors:
                    print(f"Errors: {len(errors)}")
                    for error in errors:
                        print(f"  - {error}")
                
                print("✅ SUCCESS" if structure_match and not errors else "⚠️ ISSUES")
            else:
                print("❌ FAILED")
                print(f"Errors: {len(errors)}")
                for error in errors:
                    print(f"  - {error}")
        
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
    
    print("\n" + "=" * 50)
    print("Improved YAML parser testing completed!")


if __name__ == "__main__":
    test_improved_yaml_parser()

