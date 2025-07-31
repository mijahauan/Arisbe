#!/usr/bin/env python3
"""
DAU to EGI Converter
Converts DAU RelationalGraphWithCuts objects to legacy EGI format for YAML serialization

CHANGES: Creates bridge between DAU-compliant parser (which handles isolated vertices)
and legacy YAML serializer (which expects EGI format). This enables isolated vertex
support while reusing existing YAML infrastructure.
"""

import sys
import os
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from egi_core_dau import RelationalGraphWithCuts, Vertex as DAUVertex, Edge as DAUEdge, Cut as DAUCut
    from egi_core import EGI, Context, Vertex, Edge, Alphabet, LigatureManager
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)


class DAUToEGIConverter:
    """
    Converts DAU RelationalGraphWithCuts objects to legacy EGI format.
    
    CHANGES: Enables isolated vertex support by bridging DAU parser output
    with legacy YAML serialization system. Maintains mathematical correctness
    while providing compatibility with existing infrastructure.
    """
    
    def __init__(self):
        self.id_mapping = {}  # Maps DAU IDs to EGI IDs
        self.vertex_mapping = {}  # Maps DAU vertices to EGI vertices
        self.context_mapping = {}  # Maps DAU cuts to EGI contexts
        
    def convert(self, dau_graph: RelationalGraphWithCuts) -> EGI:
        """
        Convert DAU RelationalGraphWithCuts to legacy EGI format.
        
        Args:
            dau_graph: DAU-compliant graph with isolated vertex support
            
        Returns:
            Legacy EGI object compatible with existing YAML serializer
        """
        
        # Reset mappings for new conversion
        self.id_mapping = {}
        self.vertex_mapping = {}
        self.context_mapping = {}
        
        # Create new EGI instance
        egi = EGI()
        
        # Convert alphabet (extract relations from edges)
        self._convert_alphabet(dau_graph, egi)
        
        # Convert contexts (sheet + cuts)
        self._convert_contexts(dau_graph, egi)
        
        # Convert vertices
        self._convert_vertices(dau_graph, egi)
        
        # Convert edges
        self._convert_edges(dau_graph, egi)
        
        # Set up ligatures (variable bindings)
        self._setup_ligatures(dau_graph, egi)
        
        return egi
    
    def _convert_alphabet(self, dau_graph: RelationalGraphWithCuts, egi: EGI):
        """Convert DAU relations to EGI alphabet."""
        
        # Extract relations from edges
        relations = {}
        
        for edge in dau_graph.E:
            relation_name = edge.relation_name
            arity = len(edge.incident_vertices)
            
            if relation_name in relations:
                # Verify consistent arity
                if relations[relation_name] != arity:
                    raise ValueError(f"Inconsistent arity for relation {relation_name}: {relations[relation_name]} vs {arity}")
            else:
                relations[relation_name] = arity
        
        # Create alphabet
        egi.alphabet = Alphabet()
        for relation_name, arity in relations.items():
            egi.alphabet.add_relation(relation_name, arity)
    
    def _convert_contexts(self, dau_graph: RelationalGraphWithCuts, egi: EGI):
        """Convert DAU cuts to EGI contexts."""
        
        # Create sheet context (root)
        sheet = Context(
            id="sheet",
            parent=None,
            children=[],
            depth=0,
            polarity=True  # Sheet is always positive
        )
        egi.contexts[sheet.id] = sheet
        egi.sheet = sheet
        self.context_mapping[">"] = sheet  # DAU root context symbol
        
        # Convert cuts to contexts
        cuts_by_depth = {}
        for cut in dau_graph.Cut:
            depth = getattr(cut, 'depth', 1)  # Default depth 1 if not specified
            if depth not in cuts_by_depth:
                cuts_by_depth[depth] = []
            cuts_by_depth[depth].append(cut)
        
        # Process cuts by depth to maintain hierarchy
        for depth in sorted(cuts_by_depth.keys()):
            for cut in cuts_by_depth[depth]:
                self._convert_cut_to_context(cut, dau_graph, egi)
    
    def _convert_cut_to_context(self, cut: DAUCut, dau_graph: RelationalGraphWithCuts, egi: EGI):
        """Convert a single DAU cut to EGI context."""
        
        # Determine parent context
        parent_context = None
        if hasattr(cut, 'parent') and cut.parent:
            if cut.parent in self.context_mapping:
                parent_context = self.context_mapping[cut.parent]
            else:
                # Parent is another cut - find it
                for other_cut in dau_graph.Cut:
                    if other_cut.id == cut.parent:
                        # Convert parent first if not already converted
                        if cut.parent not in self.context_mapping:
                            self._convert_cut_to_context(other_cut, dau_graph, egi)
                        parent_context = self.context_mapping[cut.parent]
                        break
        
        if parent_context is None:
            parent_context = egi.sheet  # Default to sheet
        
        # Create context
        context = Context(
            id=f"context_{cut.id}",
            parent=parent_context,
            children=[],
            depth=parent_context.depth + 1,
            polarity=not parent_context.polarity  # Alternate polarity
        )
        
        # Add to parent's children
        parent_context.children.append(context)
        
        # Store in EGI and mapping
        egi.contexts[context.id] = context
        self.context_mapping[cut.id] = context
    
    def _convert_vertices(self, dau_graph: RelationalGraphWithCuts, egi: EGI):
        """Convert DAU vertices to EGI vertices."""
        
        for dau_vertex in dau_graph.V:
            # Determine context
            context = self._get_vertex_context(dau_vertex, dau_graph, egi)
            
            # Create EGI vertex
            vertex = Vertex(
                id=f"vertex_{dau_vertex.id}",
                context=context,
                incident_edges=[],  # Will be populated when converting edges
                label=getattr(dau_vertex, 'label', None),
                is_generic=not getattr(dau_vertex, 'is_constant', True)
            )
            
            # Store in EGI and mapping
            egi.vertices[vertex.id] = vertex
            self.vertex_mapping[dau_vertex.id] = vertex
    
    def _convert_edges(self, dau_graph: RelationalGraphWithCuts, egi: EGI):
        """Convert DAU edges to EGI edges."""
        
        for dau_edge in dau_graph.E:
            # Determine context
            context = self._get_edge_context(dau_edge, dau_graph, egi)
            
            # Get incident vertices
            incident_vertices = []
            for dau_vertex_id in dau_edge.incident_vertices:
                if dau_vertex_id in self.vertex_mapping:
                    incident_vertices.append(self.vertex_mapping[dau_vertex_id])
                else:
                    raise ValueError(f"Edge {dau_edge.id} references unknown vertex {dau_vertex_id}")
            
            # Create EGI edge
            edge = Edge(
                id=f"edge_{dau_edge.id}",
                context=context,
                relation_name=dau_edge.relation_name,
                incident_vertices=incident_vertices
            )
            
            # Update vertex incident edges
            for vertex in incident_vertices:
                vertex.incident_edges.append(edge)
            
            # Store in EGI
            egi.edges[edge.id] = edge
    
    def _setup_ligatures(self, dau_graph: RelationalGraphWithCuts, egi: EGI):
        """Set up ligature manager for variable bindings."""
        
        egi.ligature_manager = LigatureManager()
        
        # Group vertices by variable name
        variable_groups = {}
        
        for dau_vertex in dau_graph.V:
            # Extract variable name from vertex
            var_name = self._extract_variable_name(dau_vertex)
            if var_name:
                if var_name not in variable_groups:
                    variable_groups[var_name] = []
                
                # Find corresponding EGI vertex
                if dau_vertex.id in self.vertex_mapping:
                    egi_vertex = self.vertex_mapping[dau_vertex.id]
                    variable_groups[var_name].append(egi_vertex)
        
        # Create ligatures for variable groups with multiple vertices
        for var_name, vertices in variable_groups.items():
            if len(vertices) > 1:
                egi.ligature_manager.create_ligature(vertices)
    
    def _get_vertex_context(self, dau_vertex: DAUVertex, dau_graph: RelationalGraphWithCuts, egi: EGI) -> Context:
        """Determine the context for a DAU vertex."""
        
        # Check if vertex has explicit context
        if hasattr(dau_vertex, 'context') and dau_vertex.context:
            if dau_vertex.context in self.context_mapping:
                return self.context_mapping[dau_vertex.context]
        
        # Default to sheet
        return egi.sheet
    
    def _get_edge_context(self, dau_edge: DAUEdge, dau_graph: RelationalGraphWithCuts, egi: EGI) -> Context:
        """Determine the context for a DAU edge."""
        
        # Check if edge has explicit context
        if hasattr(dau_edge, 'context') and dau_edge.context:
            if dau_edge.context in self.context_mapping:
                return self.context_mapping[dau_edge.context]
        
        # Default to sheet
        return egi.sheet
    
    def _extract_variable_name(self, dau_vertex: DAUVertex) -> Optional[str]:
        """Extract variable name from DAU vertex."""
        
        # Try different ways to get variable name
        if hasattr(dau_vertex, 'label') and dau_vertex.label:
            return dau_vertex.label
        
        if hasattr(dau_vertex, 'name') and dau_vertex.name:
            return dau_vertex.name
        
        if hasattr(dau_vertex, 'variable_name') and dau_vertex.variable_name:
            return dau_vertex.variable_name
        
        # Try to extract from ID if it contains variable info
        vertex_id = str(dau_vertex.id)
        if '_' in vertex_id:
            parts = vertex_id.split('_')
            if len(parts) > 1:
                return parts[-1]  # Last part might be variable name
        
        return None


def test_dau_to_egi_converter():
    """Test the DAU to EGI converter with isolated vertices."""
    
    print("DAU to EGI Converter Test")
    print("=" * 40)
    
    from egif_parser_dau import EGIFParser
    
    test_cases = [
        "[*x]",
        "[*x] [*y] (loves x y)",
        "(P *x)"
    ]
    
    converter = DAUToEGIConverter()
    
    for i, egif in enumerate(test_cases, 1):
        print(f"\nTest {i}: {egif}")
        print("-" * 30)
        
        try:
            # Parse with DAU parser
            dau_parser = EGIFParser(egif)
            dau_graph = dau_parser.parse()
            
            print(f"DAU Graph: {len(dau_graph.V)} vertices, {len(dau_graph.E)} edges, {len(dau_graph.Cut)} cuts")
            
            # Convert to EGI
            egi = converter.convert(dau_graph)
            
            print(f"EGI: {len(egi.vertices)} vertices, {len(egi.edges)} edges, {len(egi.contexts)} contexts")
            print(f"Alphabet: {len(egi.alphabet.get_all_relations())} relations")
            print("✅ Conversion successful")
            
        except Exception as e:
            print(f"❌ Conversion failed: {str(e)}")
    
    print("\n🎉 DAU to EGI converter test completed!")


if __name__ == "__main__":
    test_dau_to_egi_converter()

