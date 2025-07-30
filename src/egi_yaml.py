"""
YAML serialization and deserialization for EGI instances.
Provides human-readable representation of existential graphs.
"""

import yaml
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from egi_core import EGI, Context, Vertex, Edge, ElementID, ElementType, Alphabet


class EGIYAMLSerializer:
    """Serializes EGI instances to YAML format."""
    
    def __init__(self):
        pass
    
    def serialize(self, egi: EGI) -> str:
        """Serializes an EGI instance to YAML string."""
        data = self._egi_to_dict(egi)
        return yaml.dump(data, default_flow_style=False, sort_keys=False)
    
    def _egi_to_dict(self, egi: EGI) -> Dict[str, Any]:
        """Converts an EGI instance to a dictionary."""
        return {
            'egi': {
                'metadata': {
                    'version': '1.0',
                    'type': 'existential_graph_instance'
                },
                'alphabet': self._alphabet_to_dict(egi.alphabet),
                'sheet': self._context_to_dict(egi.sheet, egi),
                'vertices': [self._vertex_to_dict(v) for v in egi.vertices.values()],
                'edges': [self._edge_to_dict(e) for e in egi.edges.values()],
                'cuts': [self._context_to_dict(c, egi) for c in egi.cuts.values()],
                'ligatures': self._ligatures_to_dict(egi)
            }
        }
    
    def _alphabet_to_dict(self, alphabet: Alphabet) -> Dict[str, Any]:
        """Converts an Alphabet to a dictionary."""
        return {
            'relations': alphabet.get_all_relations()
        }
    
    def _context_to_dict(self, context: Context, egi: EGI) -> Dict[str, Any]:
        """Converts a Context to a dictionary."""
        return {
            'id': str(context.id),
            'type': context.id.element_type.value,
            'depth': context.depth,
            'is_positive': context.is_positive(),
            'parent_id': str(context.parent.id) if context.parent else None,
            'children_ids': [str(child_id) for child_id in context.children],
            'enclosed_elements': [str(elem_id) for elem_id in context.enclosed_elements]
        }
    
    def _vertex_to_dict(self, vertex: Vertex) -> Dict[str, Any]:
        """Converts a Vertex to a dictionary."""
        return {
            'id': str(vertex.id),
            'context_id': str(vertex.context.id),
            'is_constant': vertex.is_constant,
            'constant_name': vertex.constant_name,
            'properties': vertex.properties,
            'incident_edges': [str(edge_id) for edge_id in vertex.incident_edges],
            'degree': vertex.degree()
        }
    
    def _edge_to_dict(self, edge: Edge) -> Dict[str, Any]:
        """Converts an Edge to a dictionary."""
        return {
            'id': str(edge.id),
            'context_id': str(edge.context.id),
            'relation_name': edge.relation_name,
            'arity': edge.arity,
            'incident_vertices': [str(v_id) for v_id in edge.incident_vertices],
            'is_identity': edge.is_identity,
            'properties': edge.properties
        }
    
    def _ligatures_to_dict(self, egi: EGI) -> List[Dict[str, Any]]:
        """Converts ligatures to a list of dictionaries."""
        ligatures = []
        for ligature in egi.ligature_manager.ligatures.values():
            ligatures.append({
                'id': str(ligature.id),
                'vertices': [str(v_id) for v_id in ligature.vertices],
                'identity_edges': [str(e_id) for e_id in ligature.identity_edges],
                'size': ligature.size()
            })
        return ligatures


class EGIYAMLDeserializer:
    """Deserializes EGI instances from YAML format."""
    
    def __init__(self):
        pass
    
    def deserialize(self, yaml_str: str) -> EGI:
        """Deserializes an EGI instance from YAML string."""
        data = yaml.safe_load(yaml_str)
        return self._dict_to_egi(data)
    
    def _dict_to_egi(self, data: Dict[str, Any]) -> EGI:
        """Converts a dictionary to an EGI instance."""
        egi_data = data['egi']
        
        # Create alphabet
        alphabet = self._dict_to_alphabet(egi_data['alphabet'])
        
        # Create EGI with alphabet
        egi = EGI(alphabet)
        
        # Track ID mappings for reconstruction
        id_to_context: Dict[str, Context] = {}
        id_to_vertex: Dict[str, Vertex] = {}
        id_to_edge: Dict[str, Edge] = {}
        
        # Reconstruct sheet (already exists in EGI)
        sheet_data = egi_data['sheet']
        id_to_context[sheet_data['id']] = egi.sheet
        
        # Reconstruct cuts first (to build context hierarchy)
        cuts_data = egi_data.get('cuts', [])
        self._reconstruct_cuts(cuts_data, egi, id_to_context)
        
        # Reconstruct vertices
        vertices_data = egi_data.get('vertices', [])
        self._reconstruct_vertices(vertices_data, egi, id_to_context, id_to_vertex)
        
        # Reconstruct edges
        edges_data = egi_data.get('edges', [])
        self._reconstruct_edges(edges_data, egi, id_to_context, id_to_vertex, id_to_edge)
        
        # Rebuild ligatures
        egi.ligature_manager.find_ligatures(egi)
        
        return egi
    
    def _dict_to_alphabet(self, alphabet_data: Dict[str, Any]) -> Alphabet:
        """Converts a dictionary to an Alphabet."""
        alphabet = Alphabet()
        relations = alphabet_data.get('relations', {})
        for name, arity in relations.items():
            if name != "=":  # Skip identity relation (already added)
                alphabet.add_relation(name, arity)
        return alphabet
    
    def _reconstruct_cuts(self, cuts_data: List[Dict[str, Any]], egi: EGI, 
                         id_to_context: Dict[str, Context]) -> None:
        """Reconstructs cuts and builds context hierarchy."""
        # Sort cuts by depth to ensure parents are created before children
        cuts_data.sort(key=lambda x: x['depth'])
        
        for cut_data in cuts_data:
            cut_id_str = cut_data['id']
            parent_id_str = cut_data['parent_id']
            
            # Find parent context
            parent_context = id_to_context[parent_id_str]
            
            # Create cut
            cut = egi.add_cut(parent_context)
            
            # Update ID mapping
            id_to_context[cut_id_str] = cut
    
    def _reconstruct_vertices(self, vertices_data: List[Dict[str, Any]], egi: EGI,
                            id_to_context: Dict[str, Context], 
                            id_to_vertex: Dict[str, Vertex]) -> None:
        """Reconstructs vertices."""
        for vertex_data in vertices_data:
            vertex_id_str = vertex_data['id']
            context_id_str = vertex_data['context_id']
            
            # Find context
            context = id_to_context[context_id_str]
            
            # Create vertex
            vertex = egi.add_vertex(
                context=context,
                is_constant=vertex_data['is_constant'],
                constant_name=vertex_data.get('constant_name')
            )
            
            # Restore properties
            vertex.properties.update(vertex_data.get('properties', {}))
            
            # Update ID mapping
            id_to_vertex[vertex_id_str] = vertex
    
    def _reconstruct_edges(self, edges_data: List[Dict[str, Any]], egi: EGI,
                          id_to_context: Dict[str, Context],
                          id_to_vertex: Dict[str, Vertex],
                          id_to_edge: Dict[str, Edge]) -> None:
        """Reconstructs edges."""
        for edge_data in edges_data:
            edge_id_str = edge_data['id']
            context_id_str = edge_data['context_id']
            
            # Find context
            context = id_to_context[context_id_str]
            
            # Find incident vertices
            incident_vertex_ids = []
            for vertex_id_str in edge_data['incident_vertices']:
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
            edge.properties.update(edge_data.get('properties', {}))
            
            # Update ID mapping
            id_to_edge[edge_id_str] = edge


def serialize_egi_to_yaml(egi: EGI) -> str:
    """Convenience function to serialize EGI to YAML."""
    serializer = EGIYAMLSerializer()
    return serializer.serialize(egi)


def deserialize_egi_from_yaml(yaml_str: str) -> EGI:
    """Convenience function to deserialize EGI from YAML."""
    deserializer = EGIYAMLDeserializer()
    return deserializer.deserialize(yaml_str)


# Test the serialization
if __name__ == "__main__":
    from egif_parser import parse_egif
    
    # Test with a simple EGIF
    egif = "(man *x) ~[ (mortal x) ]"
    print(f"Original EGIF: {egif}")
    
    # Parse to EGI
    egi = parse_egif(egif)
    print(f"Parsed EGI: {len(egi.vertices)} vertices, {len(egi.edges)} edges, {len(egi.cuts)} cuts")
    
    # Serialize to YAML
    yaml_str = serialize_egi_to_yaml(egi)
    print(f"\nSerialized YAML:\n{yaml_str}")
    
    # Deserialize back to EGI
    egi2 = deserialize_egi_from_yaml(yaml_str)
    print(f"Deserialized EGI: {len(egi2.vertices)} vertices, {len(egi2.edges)} edges, {len(egi2.cuts)} cuts")
    
    # Serialize again to check round-trip
    yaml_str2 = serialize_egi_to_yaml(egi2)
    print(f"\nRound-trip successful: {yaml_str == yaml_str2}")
    
    print("\nYAML serialization test completed!")

