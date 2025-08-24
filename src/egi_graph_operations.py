"""
EGI Graph Operations - Graph-to-graph operations only.

This module implements the fundamental constraint that all EGI operations
are performed on complete graphs, never on individual elements.
"""

from typing import Dict, Set, List, Optional, Tuple, Any
from egi_logical_areas import EGILogicalSystem, EGIGraph, LogicalArea
from egi_spatial_correspondence import SpatialCorrespondenceEngine as EGISpatialCorrespondence, SpatialBounds


class EGIGraphOperations:
    """
    Manages all graph-to-graph operations in the EGI system.
    
    Core principle: You never add elements to a graph, you add graphs to graphs.
    All operations work on complete graphs that are added to logical areas.
    """
    
    def __init__(self, logical_system: EGILogicalSystem):
        self.logical_system = logical_system
        self.graph_counter = 1
    
    def add_vertex_graph_to_area(self, vertex_id: str, target_area_id: str) -> bool:
        """
        Add a graph containing only a vertex to a logical area.
        This is how vertices are added - as complete graphs.
        """
        vertex_graph = self.logical_system.create_vertex_graph(vertex_id)
        return self.logical_system.add_graph_to_area(vertex_graph, target_area_id)
    
    def add_predicate_graph_to_area(self, edge_id: str, relation_name: str, target_area_id: str) -> bool:
        """
        Add a graph containing only a predicate (edge) to a logical area.
        Step 1: Add predicate without vertices - vertices added separately.
        """
        predicate_graph = EGIGraph(
            graph_id=f"graph_{edge_id}",
            vertices=set(),  # No vertices initially
            edges={edge_id},
            cuts=set(),
            nu_mapping={},  # Empty nu mapping initially
            relation_mapping={edge_id: relation_name}
        )
        return self.logical_system.add_graph_to_area(predicate_graph, target_area_id)
    
    def create_negation_in_area(self, cut_id: str, parent_area_id: str) -> bool:
        """
        Create a negation (cut) within a parent area.
        This represents the logical operator ~[].
        """
        return self.logical_system.create_negation_area(cut_id, parent_area_id)
    
    def bind_vertex_to_predicate(self, vertex_id: str, edge_id: str, target_area_id: str) -> bool:
        """
        Step 3: Bind a vertex to a predicate with ligature and update nu mapping.
        This creates the connection between predicate and vertex graphs.
        Ligatures CAN cross cut boundaries - this is valid in EGI.
        """
        if target_area_id not in self.logical_system.logical_areas:
            return False
        
        target_area = self.logical_system.logical_areas[target_area_id]
        
        # Find the predicate graph and vertex graph (may be in different areas)
        predicate_graph = None
        vertex_graph = None
        
        # Search in target area for predicate
        for graph in target_area.contained_graphs:
            if edge_id in graph.edges:
                predicate_graph = graph
                break
        
        # Search all areas for vertex (cross-cut binding allowed)
        for area_id, area in self.logical_system.logical_areas.items():
            for graph in area.contained_graphs:
                if vertex_id in graph.vertices:
                    vertex_graph = graph
                    break
            if vertex_graph:
                break
        
        if not predicate_graph or not vertex_graph:
            print(f"DEBUG: Binding failed - predicate_graph: {predicate_graph is not None}, vertex_graph: {vertex_graph is not None}")
            return False
        
        # Update predicate graph's nu mapping to include the vertex
        predicate_graph.nu_mapping[edge_id] = predicate_graph.nu_mapping.get(edge_id, set())
        predicate_graph.nu_mapping[edge_id].add(vertex_id)
        
        print(f"DEBUG: Bound {vertex_id} to {edge_id}, nu_mapping: {predicate_graph.nu_mapping}")
        return True
    
    def conjoin_graphs_in_area(self, graph1_id: str, graph2_id: str, 
                              target_area_id: str) -> Optional[str]:
        """
        Conjoin two graphs within the same logical area.
        This represents logical conjunction through spatial juxtaposition.
        """
        if target_area_id not in self.logical_system.logical_areas:
            return None
        
        target_area = self.logical_system.logical_areas[target_area_id]
        
        # Find the graphs to conjoin
        graph1 = None
        graph2 = None
        
        for graph in target_area.contained_graphs:
            if graph.graph_id == graph1_id:
                graph1 = graph
            elif graph.graph_id == graph2_id:
                graph2 = graph
        
        if not graph1 or not graph2:
            return None
        
        # Create conjoined graph
        conjoined_graph_id = f"conjoined_{self.graph_counter}"
        self.graph_counter += 1
        
        conjoined_graph = EGIGraph(
            graph_id=conjoined_graph_id,
            vertices=graph1.vertices.union(graph2.vertices),
            edges=graph1.edges.union(graph2.edges),
            cuts=graph1.cuts.union(graph2.cuts),
            nu_mapping={**graph1.nu_mapping, **graph2.nu_mapping},
            relation_mapping={**graph1.relation_mapping, **graph2.relation_mapping}
        )
        
        # Remove original graphs and add conjoined graph
        target_area.contained_graphs = [
            g for g in target_area.contained_graphs 
            if g.graph_id not in [graph1_id, graph2_id]
        ]
        
        target_area.add_graph(conjoined_graph)
        return conjoined_graph_id
    
    def move_graph_between_areas(self, graph_id: str, source_area_id: str, 
                               target_area_id: str) -> bool:
        """
        Move a complete graph from one logical area to another.
        This validates that the move doesn't violate logical constraints.
        """
        if (source_area_id not in self.logical_system.logical_areas or
            target_area_id not in self.logical_system.logical_areas):
            return False
        
        source_area = self.logical_system.logical_areas[source_area_id]
        target_area = self.logical_system.logical_areas[target_area_id]
        
        # Find the graph to move
        graph_to_move = None
        for graph in source_area.contained_graphs:
            if graph.graph_id == graph_id:
                graph_to_move = graph
                break
        
        if not graph_to_move:
            return False
        
        # Check if move is logically valid (conjunction constraints)
        if not self.logical_system.can_conjoin_graphs(source_area_id, target_area_id):
            return False
        
        # Perform the move
        source_area.contained_graphs.remove(graph_to_move)
        return target_area.add_graph(graph_to_move)
    
    def validate_graph_operation(self, operation_type: str, **kwargs) -> List[str]:
        """
        Validate that a graph operation respects EGI logical constraints.
        Returns list of violations if any.
        """
        violations = []
        
        if operation_type == "add_to_area":
            target_area_id = kwargs.get('target_area_id')
            if target_area_id not in self.logical_system.logical_areas:
                violations.append(f"Target area {target_area_id} does not exist")
        
        elif operation_type == "conjoin":
            area_id = kwargs.get('area_id')
            if area_id not in self.logical_system.logical_areas:
                violations.append(f"Area {area_id} does not exist")
            
            # Check that conjunction doesn't cross negation boundaries
            # (This would be expanded with specific EGI rules)
        
        elif operation_type == "create_negation":
            parent_area_id = kwargs.get('parent_area_id')
            if parent_area_id not in self.logical_system.logical_areas:
                violations.append(f"Parent area {parent_area_id} does not exist")
        
        return violations
    
    def get_area_graph_summary(self, area_id: str) -> Dict[str, Any]:
        """Get summary of all graphs in a logical area."""
        if area_id not in self.logical_system.logical_areas:
            return {}
        
        area = self.logical_system.logical_areas[area_id]
        
        return {
            'area_id': area_id,
            'is_negation': area.is_cut,
            'graph_count': len(area.contained_graphs),
            'total_vertices': len(area.get_all_vertices()),
            'total_edges': len(area.get_all_edges()),
            'graphs': [
                {
                    'graph_id': graph.graph_id,
                    'vertex_count': len(graph.vertices),
                    'edge_count': len(graph.edges),
                    'cut_count': len(graph.cuts)
                }
                for graph in area.contained_graphs
            ]
        }


class EGISystemController:
    """
    Main controller that coordinates logical operations with spatial correspondence.
    This replaces the previous controller with graph-based operations only.
    """
    
    def __init__(self, sheet_id: str, canvas_bounds: SpatialBounds):
        self.logical_system = EGILogicalSystem(sheet_id)
        self.spatial_correspondence = EGISpatialCorrespondence(
            self.logical_system, canvas_bounds
        )
        self.graph_operations = EGIGraphOperations(self.logical_system)
        self.presentation_adapters = []
    
    def register_presentation_adapter(self, adapter):
        """Register a presentation adapter (e.g., Qt GUI)."""
        self.presentation_adapters.append(adapter)
    
    def add_vertex_to_area(self, vertex_id: str, area_id: str) -> bool:
        """Add a vertex graph to a logical area."""
        success = self.graph_operations.add_vertex_graph_to_area(vertex_id, area_id)
        if success:
            self._update_presentation()
        return success
    
    def add_predicate_to_area(self, edge_id: str, relation_name: str, area_id: str) -> bool:
        """Step 1: Add a predicate graph to a logical area (without vertices)."""
        success = self.graph_operations.add_predicate_graph_to_area(edge_id, relation_name, area_id)
        if success:
            self._update_presentation()
        return success
    
    def bind_vertex_to_predicate(self, vertex_id: str, edge_id: str, area_id: str) -> bool:
        """Step 3: Bind vertex to predicate with ligature and update nu mapping."""
        success = self.graph_operations.bind_vertex_to_predicate(vertex_id, edge_id, area_id)
        if success:
            self._update_presentation()
        return success
    
    def create_negation(self, cut_id: str, parent_area_id: str) -> bool:
        """Create a negation (cut) in a parent area."""
        success = self.graph_operations.create_negation_in_area(cut_id, parent_area_id)
        if success:
            self._update_presentation()
        return success
    
    def conjoin_graphs(self, graph1_id: str, graph2_id: str, area_id: str) -> Optional[str]:
        """Conjoin two graphs in the same area."""
        result = self.graph_operations.conjoin_graphs_in_area(graph1_id, graph2_id, area_id)
        if result:
            self._update_presentation()
        return result
    
    def get_complete_layout(self) -> Dict[str, Any]:
        """Get complete spatial layout for rendering."""
        layout = self.spatial_correspondence.generate_complete_spatial_layout()
        
        # Add linear graph replica for debugging
        layout['linear_replica'] = self._generate_linear_replica()
        
        return layout
    
    def _generate_linear_replica(self) -> str:
        """Generate linear graph representation (CGIF-style) for debugging."""
        linear_parts = []
        
        for area_id, area in self.logical_system.logical_areas.items():
            area_graphs = []
            
            for graph in area.contained_graphs:
                # Generate graph representation
                if graph.vertices and not graph.edges:
                    # Vertex-only graph
                    for vertex_id in graph.vertices:
                        area_graphs.append(f"[{vertex_id}]")
                
                elif graph.edges:
                    # Predicate graph with nu mapping
                    for edge_id in graph.edges:
                        relation_name = graph.relation_mapping.get(edge_id, edge_id)
                        if edge_id in graph.nu_mapping and graph.nu_mapping[edge_id]:
                            # Get incident vertices
                            vertices = list(graph.nu_mapping[edge_id])
                            if len(vertices) == 1:
                                area_graphs.append(f"[{relation_name}: {vertices[0]}]")
                            else:
                                vertex_list = ", ".join(vertices)
                                area_graphs.append(f"[{relation_name}: {vertex_list}]")
                        else:
                            area_graphs.append(f"[{relation_name}: ?]")
            
            if area_graphs:
                if area_id == self.logical_system.sheet_id:
                    # Main sheet
                    linear_parts.append(" ".join(area_graphs))
                else:
                    # Cut area
                    linear_parts.append(f"~[{' '.join(area_graphs)}]")
        
        return " ".join(linear_parts)
    
    def validate_system_consistency(self) -> List[str]:
        """Validate that the entire system maintains logical-spatial correspondence."""
        logical_violations = self.logical_system.validate_logical_consistency()
        
        # Add spatial validation here if needed
        spatial_violations = []
        
        return logical_violations + spatial_violations
    
    def _update_presentation(self):
        """Update all registered presentation adapters."""
        layout = self.get_complete_layout()
        
        for adapter in self.presentation_adapters:
            if hasattr(adapter, 'update_display'):
                adapter.update_display(layout)
    
    def get_system_state(self) -> Dict[str, Any]:
        """Get complete system state for debugging/inspection."""
        return {
            'logical_areas': {
                area_id: self.logical_system.get_area_logical_content(area_id)
                for area_id in self.logical_system.logical_areas.keys()
            },
            'spatial_layout': self.get_complete_layout(),
            'validation_results': self.validate_system_consistency()
        }
