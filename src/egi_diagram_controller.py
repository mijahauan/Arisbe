"""
EGI-Aware Diagram Controller

Implements the correct correspondence between diagrammatic manipulations
and atomic EGI operations, following Dau's formalism.
"""

from typing import Dict, List, Tuple, Optional, Set, Literal
from dataclasses import dataclass
from frozendict import frozendict

from egi_core_dau import RelationalGraphWithCuts, Vertex, Edge, Cut


@dataclass
class LigatureComponent:
    """Represents a component of a ligature (connected identity lines)"""
    vertices: Set[str]
    identity_edges: Set[str]
    connected_predicates: Dict[str, int]  # predicate_id -> hook_position


@dataclass
class DiagramElement:
    """Base class for diagram elements that correspond to EGI components"""
    element_id: str
    element_type: str  # 'vertex', 'predicate', 'identity_edge', 'cut'
    position: Tuple[float, float]
    area_id: str


class EGIDiagramController:
    """
    Controller that maintains strict correspondence between diagram state
    and EGI operations, following Dau's formalism.
    """
    
    def __init__(self, egi: RelationalGraphWithCuts):
        self.egi = egi
        self.ligatures: Dict[str, LigatureComponent] = {}
        self._build_ligature_map()

    # ------------------------
    # Transactional operations
    # ------------------------
    @dataclass
    class Transaction:
        op: str
        proposed_egi: Optional[RelationalGraphWithCuts] = None
        errors: List[str] = None

    def begin_transaction(self, op: str) -> "EGIDiagramController.Transaction":
        return EGIDiagramController.Transaction(op=op, proposed_egi=self.egi, errors=[])

    def _simulate_attach_loi_endpoint(self, tx: "EGIDiagramController.Transaction", loi_vertex_id: str, predicate_id: str, hook_position: int) -> None:
        """Build a proposed EGI reflecting attaching a ligature endpoint to a predicate hook."""
        egi = tx.proposed_egi
        # Basic structural copies
        new_nu = dict(egi.nu)
        # Current ν for predicate (edge) – treat as tuple of vertex ids (or None)
        current = list(new_nu.get(predicate_id, ()))
        if hook_position >= len(current):
            current.extend([None] * (hook_position - len(current) + 1))
        current[hook_position] = loi_vertex_id
        new_nu[predicate_id] = tuple(current)
        tx.proposed_egi = egi._replace(nu=frozendict(new_nu))

    def _validate_syntax(self, tx: "EGIDiagramController.Transaction") -> List[str]:
        """Syntax-only checks that must always hold (Dau formalism constraints at structure level)."""
        egi = tx.proposed_egi
        errs: List[str] = []
        # ν references must be to existing vertices and edges
        for edge_id, vertex_seq in egi.nu.items():
            if edge_id not in egi.edges:
                errs.append(f"ν references non-existent edge: {edge_id}")
            for v in vertex_seq:
                if v is not None and v not in egi.vertices:
                    errs.append(f"ν references non-existent vertex: {v}")
        # Every edge must have κ label
        for e in egi.edges:
            if e not in egi.rel:
                errs.append(f"Edge missing κ label: {e}")
        return errs

    def _validate_semantics(self, prev_egi: RelationalGraphWithCuts, next_egi: RelationalGraphWithCuts, op: str) -> List[str]:
        """Placeholder for Practice Mode rule validation. Returns list of violations."""
        # TODO: integrate with rule engine (iteration/deiteration, etc.). For now, accept attach as neutral.
        if op in {"attach_loi_endpoint"}:
            return []
        return []

    def commit(self, tx: "EGIDiagramController.Transaction") -> None:
        self.egi = tx.proposed_egi
        self._build_ligature_map()

    def rollback(self, tx: "EGIDiagramController.Transaction") -> None:
        tx.proposed_egi = self.egi
        tx.errors = []

    def attach_loi_endpoint_transactional(self, loi_vertex_id: str, predicate_id: str, hook_position: int,
                                           mode: Literal["playground", "practice"] = "playground") -> Tuple[bool, List[str]]:
        """Perform attach with simulate → validate syntax → (optional) validate semantics → commit."""
        tx = self.begin_transaction("attach_loi_endpoint")
        # Quick guards
        if loi_vertex_id not in self.egi.vertices:
            return False, [f"Unknown vertex: {loi_vertex_id}"]
        if predicate_id not in self.egi.edges:
            return False, [f"Unknown edge (predicate): {predicate_id}"]
        if self.egi.rel.get(predicate_id, "=") == "=":
            return False, ["Cannot attach endpoint to identity edge; must attach to predicate edge."]
        if hook_position < 0:
            return False, ["Invalid hook position (<0)"]

        # Simulate
        self._simulate_attach_loi_endpoint(tx, loi_vertex_id, predicate_id, hook_position)
        # Syntax checks
        sx_errs = self._validate_syntax(tx)
        if sx_errs:
            return False, sx_errs
        # Semantics in Practice Mode
        if mode == "practice":
            sem_errs = self._validate_semantics(self.egi, tx.proposed_egi, tx.op)
            if sem_errs:
                return False, sem_errs
        # Commit
        self.commit(tx)
        return True, []

    def delete_identity_edge_transactional(self, identity_edge_id: str,
                                            mode: Literal["playground", "practice"] = "playground") -> Tuple[bool, List[str]]:
        """Remove an identity edge (κ='=') from the EGI in a transaction."""
        if identity_edge_id not in self.egi.edges:
            return False, [f"Unknown edge: {identity_edge_id}"]
        if self.egi.rel.get(identity_edge_id) != "=":
            return False, ["Can only delete identity edges with κ='='"]
        tx = self.begin_transaction("delete_identity_edge")
        egi = tx.proposed_egi
        new_edges = set(egi.edges)
        new_edges.discard(identity_edge_id)
        new_rel = dict(egi.rel)
        new_rel.pop(identity_edge_id, None)
        new_nu = dict(egi.nu)
        new_nu.pop(identity_edge_id, None)
        # Note: vertices remain; components may split into separate ligatures
        tx.proposed_egi = egi._replace(
            edges=frozenset(new_edges),
            rel=frozendict(new_rel),
            nu=frozendict(new_nu)
        )
        sx_errs = self._validate_syntax(tx)
        if sx_errs:
            return False, sx_errs
        if mode == "practice":
            sem_errs = self._validate_semantics(self.egi, tx.proposed_egi, tx.op)
            if sem_errs:
                return False, sem_errs
        self.commit(tx)
        return True, []
    
    def _build_ligature_map(self):
        """Build ligature components from current EGI state using Dau-compliant methods"""
        self.ligatures.clear()
        
        # Find all identity edges (κ(e) = "=") using Dau-compliant access
        identity_edges = set()
        for edge in self.egi.E:
            if self.egi.get_relation_name(edge.id) == "=":
                identity_edges.add(edge.id)
        
        # Build connected components (ligatures)
        visited_vertices = set()
        ligature_id = 0
        
        for vertex in self.egi.V:
            if vertex.id in visited_vertices:
                continue
                
            # Find all vertices connected via identity edges
            connected_vertices = self._find_connected_vertices(vertex.id, identity_edges)
            
            if connected_vertices:
                ligature_key = f"ligature_{ligature_id}"
                
                # Find predicates connected to this ligature using Dau-compliant methods
                connected_predicates = {}
                for v_id in connected_vertices:
                    for edge in self.egi.E:
                        if self.egi.get_relation_name(edge.id) != "=":
                            vertex_seq = self.egi.get_incident_vertices(edge.id)
                            if v_id in vertex_seq:
                                hook_position = vertex_seq.index(v_id)
                                connected_predicates[edge.id] = hook_position
                
                # Find identity edges in this ligature
                ligature_identity_edges = set()
                for edge_id in identity_edges:
                    vertex_seq = self.egi.get_incident_vertices(edge_id)
                    if any(v_id in connected_vertices for v_id in vertex_seq):
                        ligature_identity_edges.add(edge_id)
                
                self.ligatures[ligature_key] = LigatureComponent(
                    vertices=connected_vertices,
                    identity_edges=ligature_identity_edges,
                    connected_predicates=connected_predicates
                )
                
                visited_vertices.update(connected_vertices)
                ligature_id += 1
    
    def _find_connected_vertices(self, start_vertex: str, identity_edges: Set[str]) -> Set[str]:
        """Find all vertices connected to start_vertex via identity edges using Dau-compliant methods"""
        connected = {start_vertex}
        queue = [start_vertex]
        
        while queue:
            current = queue.pop(0)
            
            # Check all identity edges using Dau-compliant access
            for edge_id in identity_edges:
                vertex_seq = self.egi.get_incident_vertices(edge_id)
                if current in vertex_seq:
                    # Add all other vertices in this identity edge
                    for v_id in vertex_seq:
                        if v_id not in connected:
                            connected.add(v_id)
                            queue.append(v_id)
        
        return connected
    
    def attach_loi_to_predicate(self, loi_endpoint_vertex: str, predicate_id: str, hook_position: int) -> bool:
        """
        Attach a Line of Identity endpoint to a predicate hook.
        Updates the ν mapping to reflect the connection using Dau-compliant operations.
        """
        try:
            # Get current ν mapping for predicate using Dau-compliant method
            current_nu = list(self.egi.get_incident_vertices(predicate_id))
            
            # Extend or modify the ν mapping
            if hook_position >= len(current_nu):
                # Extend the mapping
                current_nu.extend([None] * (hook_position - len(current_nu) + 1))
            
            current_nu[hook_position] = loi_endpoint_vertex
            
            # Update the EGI using Dau-compliant structure
            new_nu = dict(self.egi.nu)
            new_nu[predicate_id] = tuple(current_nu)
            
            self.egi = self.egi._replace(nu=frozendict(new_nu))
            self._build_ligature_map()
            
            return True
            
        except Exception as e:
            print(f"Error attaching LoI to predicate: {e}")
            return False
    
    def detach_loi_from_predicate(self, loi_endpoint_vertex: str, predicate_id: str) -> bool:
        """
        Detach a Line of Identity from a predicate hook.
        Updates the ν mapping to remove the connection.
        """
        try:
            current_nu = list(self.egi.nu.get(predicate_id, ()))
            
            # Remove the vertex from the ν mapping
            updated_nu = [v if v != loi_endpoint_vertex else None for v in current_nu]
            
            # Clean up trailing Nones
            while updated_nu and updated_nu[-1] is None:
                updated_nu.pop()
            
            new_nu = dict(self.egi.nu)
            if updated_nu:
                new_nu[predicate_id] = tuple(updated_nu)
            else:
                # Remove predicate if no connections remain
                del new_nu[predicate_id]
            
            self.egi = self.egi._replace(nu=frozendict(new_nu))
            self._build_ligature_map()
            
            return True
            
        except Exception as e:
            print(f"Error detaching LoI from predicate: {e}")
            return False
    
    def merge_ligatures_end_to_end(self, ligature1_id: str, ligature2_id: str) -> bool:
        """
        Merge two ligatures end-to-end, creating a single continuous ligature.
        This corresponds to connecting two LoI endpoints.
        """
        try:
            if ligature1_id not in self.ligatures or ligature2_id not in self.ligatures:
                return False
            
            lig1 = self.ligatures[ligature1_id]
            lig2 = self.ligatures[ligature2_id]
            
            # Choose a representative vertex from each ligature
            rep1 = next(iter(lig1.vertices))
            rep2 = next(iter(lig2.vertices))
            
            # Create new identity edge connecting the ligatures
            new_edge_id = f"identity_merge_{len(self.egi.edges)}"
            
            # Update EGI
            new_edges = set(self.egi.edges) | {new_edge_id}
            new_rel = dict(self.egi.rel)
            new_rel[new_edge_id] = "="
            new_nu = dict(self.egi.nu)
            new_nu[new_edge_id] = (rep1, rep2)
            
            self.egi = self.egi._replace(
                edges=frozenset(new_edges),
                rel=frozendict(new_rel),
                nu=frozendict(new_nu)
            )
            
            self._build_ligature_map()
            return True
            
        except Exception as e:
            print(f"Error merging ligatures: {e}")
            return False
    
    def branch_ligature(self, junction_vertex_id: str, new_vertex_id: str) -> bool:
        """
        Add a new branch to an existing ligature at a junction point.
        Creates a new identity edge connecting to the junction.
        """
        try:
            # Create new identity edge for the branch
            new_edge_id = f"identity_branch_{len(self.egi.edges)}"
            
            # Update EGI
            new_vertices = set(self.egi.vertices) | {new_vertex_id}
            new_edges = set(self.egi.edges) | {new_edge_id}
            new_rel = dict(self.egi.rel)
            new_rel[new_edge_id] = "="
            new_nu = dict(self.egi.nu)
            new_nu[new_edge_id] = (junction_vertex_id, new_vertex_id)
            
            self.egi = self.egi._replace(
                vertices=frozenset(new_vertices),
                edges=frozenset(new_edges),
                rel=frozendict(new_rel),
                nu=frozendict(new_nu)
            )
            
            self._build_ligature_map()
            return True
            
        except Exception as e:
            print(f"Error branching ligature: {e}")
            return False
    
    def create_standalone_loi(self, vertex1_id: str, vertex2_id: str, area_id: str) -> bool:
        """
        Create a standalone Line of Identity between two vertices.
        This creates an identity edge with κ(e) = "=".
        """
        try:
            new_edge_id = f"identity_standalone_{len(self.egi.edges)}"
            
            # Update EGI
            new_vertices = set(self.egi.vertices) | {vertex1_id, vertex2_id}
            new_edges = set(self.egi.edges) | {new_edge_id}
            new_rel = dict(self.egi.rel)
            new_rel[new_edge_id] = "="
            new_nu = dict(self.egi.nu)
            new_nu[new_edge_id] = (vertex1_id, vertex2_id)
            
            # Update area mapping
            new_area_map = dict(self.egi.areaMap)
            current_area = set(new_area_map.get(area_id, set()))
            current_area.update({vertex1_id, vertex2_id, new_edge_id})
            new_area_map[area_id] = frozenset(current_area)
            
            self.egi = self.egi._replace(
                vertices=frozenset(new_vertices),
                edges=frozenset(new_edges),
                rel=frozendict(new_rel),
                nu=frozendict(new_nu),
                areaMap=frozendict(new_area_map)
            )
            
            self._build_ligature_map()
            return True
            
        except Exception as e:
            print(f"Error creating standalone LoI: {e}")
            return False
    
    def create_medad(self, predicate_name: str, area_id: str) -> bool:
        """
        Create a medad (arity 0 predicate) - atomic proposition.
        This creates an edge with κ(e) = predicate_name and no ν mapping.
        """
        try:
            new_edge_id = f"medad_{predicate_name}_{len(self.egi.edges)}"
            
            # Update EGI
            new_edges = set(self.egi.edges) | {new_edge_id}
            new_rel = dict(self.egi.rel)
            new_rel[new_edge_id] = predicate_name
            
            # No ν mapping for medads (arity 0)
            
            # Update area mapping
            new_area_map = dict(self.egi.areaMap)
            current_area = set(new_area_map.get(area_id, set()))
            current_area.add(new_edge_id)
            new_area_map[area_id] = frozenset(current_area)
            
            self.egi = self.egi._replace(
                edges=frozenset(new_edges),
                rel=frozendict(new_rel),
                areaMap=frozendict(new_area_map)
            )
            
            self._build_ligature_map()
            return True
            
        except Exception as e:
            print(f"Error creating medad: {e}")
            return False
    
    def get_ligature_for_vertex(self, vertex_id: str) -> Optional[str]:
        """Find which ligature contains the given vertex"""
        for ligature_id, ligature in self.ligatures.items():
            if vertex_id in ligature.vertices:
                return ligature_id
        return None
    
    def get_predicate_hooks(self, predicate_id: str) -> List[Tuple[int, Optional[str]]]:
        """Get all hooks for a predicate with their positions and connected vertices"""
        nu_mapping = self.egi.nu.get(predicate_id, ())
        return [(i, vertex_id) for i, vertex_id in enumerate(nu_mapping)]
    
    def validate_egi_consistency(self) -> List[str]:
        """Validate that the EGI is consistent and well-formed"""
        errors = []
        
        # Check that all vertices in ν mappings exist
        for edge_id, vertex_seq in self.egi.nu.items():
            for vertex_id in vertex_seq:
                if vertex_id and vertex_id not in self.egi.vertices:
                    errors.append(f"ν mapping references non-existent vertex: {vertex_id}")
        
        # Check that all edges in ν mappings exist
        for edge_id in self.egi.nu.keys():
            if edge_id not in self.egi.edges:
                errors.append(f"ν mapping references non-existent edge: {edge_id}")
        
        # Check that all edges have labels in rel mapping
        for edge_id in self.egi.edges:
            if edge_id not in self.egi.rel:
                errors.append(f"Edge missing label in rel mapping: {edge_id}")
        
        return errors
