"""
Core data structures for Existential Graph Instances (EGI)
Based on Frithjof Dau's formalism and property hypergraph model.
"""

from typing import Union, Set, List, Dict, Optional, Tuple, Any
from enum import Enum
import uuid
from dataclasses import dataclass, field


class ElementType(Enum):
    VERTEX = "vertex"
    EDGE = "edge" 
    CUT = "cut"
    SHEET = "sheet"


@dataclass(frozen=True)
class ElementID:
    """Immutable identifier for graph elements."""
    value: str = field(default_factory=lambda: str(uuid.uuid4()))
    element_type: ElementType = field(default=ElementType.VERTEX)
    
    def __str__(self) -> str:
        return f"{self.element_type.value}_{self.value[:8]}"


@dataclass
class Context:
    """Represents a context in the EGI (either a cut or the sheet of assertion)."""
    id: ElementID
    parent: Optional['Context'] = None
    children: Set[ElementID] = field(default_factory=set)  # Store IDs instead of objects
    enclosed_elements: Set[ElementID] = field(default_factory=set)
    depth: int = 0
    
    def __hash__(self):
        return hash(self.id)
    
    def is_positive(self) -> bool:
        """Returns True if this context is positive (evenly enclosed)."""
        return self.depth % 2 == 0
    
    def is_negative(self) -> bool:
        """Returns True if this context is negative (oddly enclosed)."""
        return self.depth % 2 == 1
    
    def add_child(self, child: 'Context') -> None:
        """Adds a child context and updates the hierarchy."""
        child.parent = self
        child.depth = self.depth + 1
        self.children.add(child.id)
    
    def encloses(self, element_id: ElementID) -> bool:
        """Returns True if this context directly encloses the given element."""
        return element_id in self.enclosed_elements
    
    def encloses_transitively(self, element_id: ElementID, egi: 'EGI') -> bool:
        """Returns True if this context encloses the element directly or indirectly."""
        if self.encloses(element_id):
            return True
        # Need EGI reference to look up child contexts
        for child_id in self.children:
            child_context = egi.get_context(child_id)
            if child_context.encloses_transitively(element_id, egi):
                return True
        return False


@dataclass
class Vertex:
    """Represents a vertex in the EGI."""
    id: ElementID
    context: Context
    is_constant: bool = False
    constant_name: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    incident_edges: Set[ElementID] = field(default_factory=set)
    
    def __post_init__(self):
        """Validates vertex consistency after initialization."""
        if self.is_constant and self.constant_name is None:
            raise ValueError("Constant vertices must have a constant_name")
        if not self.is_constant and self.constant_name is not None:
            raise ValueError("Generic vertices cannot have a constant_name")
        
        # Ensure vertex is properly registered with its context
        self.context.enclosed_elements.add(self.id)
    
    def add_incident_edge(self, edge_id: ElementID) -> None:
        """Registers an edge as incident to this vertex."""
        self.incident_edges.add(edge_id)
    
    def remove_incident_edge(self, edge_id: ElementID) -> None:
        """Removes an edge from the incident edges set."""
        self.incident_edges.discard(edge_id)
    
    def is_isolated(self) -> bool:
        """Returns True if this vertex has no incident edges."""
        return len(self.incident_edges) == 0
    
    def degree(self) -> int:
        """Returns the number of edges incident to this vertex."""
        return len(self.incident_edges)


@dataclass
class Edge:
    """Represents a hyperedge in the EGI."""
    id: ElementID
    context: Context
    relation_name: str
    arity: int
    incident_vertices: List[ElementID]  # Ordered list for n-adic relations
    is_identity: bool = False
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validates edge consistency after initialization."""
        if len(self.incident_vertices) != self.arity:
            raise ValueError(f"Edge arity {self.arity} does not match vertex count {len(self.incident_vertices)}")
        
        if self.is_identity and self.arity != 2:
            raise ValueError("Identity edges must have arity 2")
        
        if self.is_identity and self.relation_name != "=":
            raise ValueError("Identity edges must have relation_name '='")
        
        # Ensure edge is properly registered with its context
        self.context.enclosed_elements.add(self.id)
    
    def connects(self, vertex_id: ElementID) -> bool:
        """Returns True if this edge is incident to the given vertex."""
        return vertex_id in self.incident_vertices
    
    def get_other_vertex(self, vertex_id: ElementID) -> Optional[ElementID]:
        """For binary edges, returns the other vertex. None if not binary or vertex not found."""
        if self.arity != 2 or vertex_id not in self.incident_vertices:
            return None
        return next(v for v in self.incident_vertices if v != vertex_id)
    
    def is_strict_identity(self, egi: 'EGI') -> bool:
        """Returns True if this is a strict identity edge (both vertices in same context)."""
        if not self.is_identity:
            return False
        
        v1_context = egi.get_vertex(self.incident_vertices[0]).context
        v2_context = egi.get_vertex(self.incident_vertices[1]).context
        return v1_context == self.context and v2_context == self.context


@dataclass
class Ligature:
    """Represents a connected component of identity edges and vertices."""
    id: ElementID
    vertices: Set[ElementID]
    identity_edges: Set[ElementID]
    is_connected: bool = True
    
    def __post_init__(self):
        """Validates ligature consistency."""
        if len(self.vertices) < 1:
            raise ValueError("Ligature must contain at least one vertex")
    
    def add_vertex(self, vertex_id: ElementID) -> None:
        """Adds a vertex to this ligature."""
        self.vertices.add(vertex_id)
    
    def add_identity_edge(self, edge_id: ElementID) -> None:
        """Adds an identity edge to this ligature."""
        self.identity_edges.add(edge_id)
    
    def merge_with(self, other: 'Ligature') -> 'Ligature':
        """Merges this ligature with another, returning a new ligature."""
        merged_vertices = self.vertices.union(other.vertices)
        merged_edges = self.identity_edges.union(other.identity_edges)
        
        return Ligature(
            id=ElementID(element_type=ElementType.VERTEX),
            vertices=merged_vertices,
            identity_edges=merged_edges
        )
    
    def size(self) -> int:
        """Returns the number of vertices in this ligature."""
        return len(self.vertices)


class LigatureManager:
    """Manages ligature detection and maintenance in an EGI."""
    
    def __init__(self):
        self.ligatures: Dict[ElementID, Ligature] = {}
        self.vertex_to_ligature: Dict[ElementID, ElementID] = {}
    
    def find_ligatures(self, egi: 'EGI') -> None:
        """Discovers all ligatures in the given EGI using union-find algorithm."""
        # Reset ligature tracking
        self.ligatures.clear()
        self.vertex_to_ligature.clear()
        
        # Initialize each vertex as its own ligature
        for vertex_id in egi.vertices:
            ligature_id = ElementID(element_type=ElementType.VERTEX)
            ligature = Ligature(
                id=ligature_id,
                vertices={vertex_id},
                identity_edges=set()
            )
            self.ligatures[ligature_id] = ligature
            self.vertex_to_ligature[vertex_id] = ligature_id
        
        # Process identity edges to merge ligatures
        for edge in egi.edges.values():
            if edge.is_identity:
                v1_id, v2_id = edge.incident_vertices
                self._union_vertices(v1_id, v2_id, edge.id)
    
    def _union_vertices(self, v1_id: ElementID, v2_id: ElementID, edge_id: ElementID) -> None:
        """Merges the ligatures containing the two vertices."""
        lig1_id = self._find_ligature(v1_id)
        lig2_id = self._find_ligature(v2_id)
        
        if lig1_id == lig2_id:
            # Vertices already in same ligature, just add the edge
            self.ligatures[lig1_id].add_identity_edge(edge_id)
            return
        
        # Merge the smaller ligature into the larger one
        lig1 = self.ligatures[lig1_id]
        lig2 = self.ligatures[lig2_id]
        
        if lig1.size() < lig2.size():
            lig1, lig2 = lig2, lig1
            lig1_id, lig2_id = lig2_id, lig1_id
        
        # Merge lig2 into lig1
        lig1.vertices.update(lig2.vertices)
        lig1.identity_edges.update(lig2.identity_edges)
        lig1.add_identity_edge(edge_id)
        
        # Update vertex mappings
        for vertex_id in lig2.vertices:
            self.vertex_to_ligature[vertex_id] = lig1_id
        
        # Remove the merged ligature
        del self.ligatures[lig2_id]
    
    def _find_ligature(self, vertex_id: ElementID) -> ElementID:
        """Finds the ligature containing the given vertex."""
        return self.vertex_to_ligature[vertex_id]
    
    def get_ligature_for_vertex(self, vertex_id: ElementID) -> Optional[Ligature]:
        """Returns the ligature containing the given vertex."""
        ligature_id = self.vertex_to_ligature.get(vertex_id)
        return self.ligatures.get(ligature_id) if ligature_id else None
    
    def are_vertices_connected(self, v1_id: ElementID, v2_id: ElementID) -> bool:
        """Returns True if the two vertices are in the same ligature."""
        return self._find_ligature(v1_id) == self._find_ligature(v2_id)


@dataclass
class Alphabet:
    """Manages relation names and their arities for an EGI."""
    
    def __init__(self):
        self.relations: Dict[str, int] = {}
        # Identity relation is always present
        self.relations["="] = 2
    
    def add_relation(self, name: str, arity: int) -> None:
        """Adds a relation name with its arity to the alphabet."""
        if arity < 0:
            raise ValueError("Relation arity must be non-negative")
        
        if name in self.relations and self.relations[name] != arity:
            raise ValueError(f"Relation {name} already exists with different arity")
        
        self.relations[name] = arity
    
    def is_valid_relation(self, name: str, arity: int) -> bool:
        """Returns True if the relation name and arity are valid."""
        return name in self.relations and self.relations[name] == arity
    
    def get_arity(self, name: str) -> Optional[int]:
        """Returns the arity of the given relation name."""
        return self.relations.get(name)
    
    def get_all_relations(self) -> Dict[str, int]:
        """Returns a copy of all relations in the alphabet."""
        return self.relations.copy()


class EGI:
    """Complete Existential Graph Instance implementation."""
    
    def __init__(self, alphabet: Optional[Alphabet] = None):
        """Initializes an empty EGI with optional alphabet specification."""
        self.vertices: Dict[ElementID, Vertex] = {}
        self.edges: Dict[ElementID, Edge] = {}
        self.cuts: Dict[ElementID, Context] = {}
        
        # Sheet of assertion (root context)
        self.sheet_id = ElementID(element_type=ElementType.SHEET)
        self.sheet = Context(id=self.sheet_id, depth=0)
        
        # Ligature management
        self.ligature_manager = LigatureManager()
        
        # Alphabet for relation names and arities
        self.alphabet = alphabet or Alphabet()
        
        # Transformation history for debugging and validation
        self.transformation_history: List[Dict] = []
    
    def add_vertex(self, context: Context, is_constant: bool = False, 
                   constant_name: Optional[str] = None) -> Vertex:
        """Adds a new vertex to the EGI."""
        vertex_id = ElementID(element_type=ElementType.VERTEX)
        vertex = Vertex(
            id=vertex_id,
            context=context,
            is_constant=is_constant,
            constant_name=constant_name
        )
        
        self.vertices[vertex_id] = vertex
        self._validate_dominating_nodes()
        return vertex
    
    def add_edge(self, context: Context, relation_name: str, 
                 incident_vertices: List[ElementID], check_dominance: bool = True) -> Edge:
        """Adds a new edge to the EGI."""
        # Auto-register unknown relations
        if relation_name not in self.alphabet.relations:
            self.alphabet.add_relation(relation_name, len(incident_vertices))
        
        # Validate relation name and arity
        if not self.alphabet.is_valid_relation(relation_name, len(incident_vertices)):
            raise ValueError(f"Invalid relation {relation_name} with arity {len(incident_vertices)}")
        
        # Validate dominating nodes constraint (optional for parser)
        if check_dominance:
            for vertex_id in incident_vertices:
                vertex = self.vertices[vertex_id]
                if not self._context_dominates(context, vertex.context):
                    raise ValueError(f"Edge context must dominate all incident vertex contexts")
        
        edge_id = ElementID(element_type=ElementType.EDGE)
        is_identity = relation_name == "="
        
        edge = Edge(
            id=edge_id,
            context=context,
            relation_name=relation_name,
            arity=len(incident_vertices),
            incident_vertices=incident_vertices,
            is_identity=is_identity
        )
        
        self.edges[edge_id] = edge
        
        # Update vertex incident edge sets
        for vertex_id in incident_vertices:
            self.vertices[vertex_id].add_incident_edge(edge_id)
        
        # Update ligatures if this is an identity edge
        if is_identity:
            self.ligature_manager.find_ligatures(self)
        
        return edge
    
    def add_cut(self, parent_context: Context) -> Context:
        """Adds a new cut (negative context) to the EGI."""
        cut_id = ElementID(element_type=ElementType.CUT)
        cut = Context(id=cut_id)
        
        parent_context.add_child(cut)
        self.cuts[cut_id] = cut
        
        return cut
    
    def get_vertex(self, vertex_id: ElementID) -> Vertex:
        """Returns the vertex with the given ID."""
        if vertex_id not in self.vertices:
            raise ValueError(f"Vertex {vertex_id} not found")
        return self.vertices[vertex_id]
    
    def get_edge(self, edge_id: ElementID) -> Edge:
        """Returns the edge with the given ID."""
        if edge_id not in self.edges:
            raise ValueError(f"Edge {edge_id} not found")
        return self.edges[edge_id]
    
    def get_context(self, context_id: ElementID) -> Context:
        """Returns the context with the given ID."""
        if context_id == self.sheet_id:
            return self.sheet
        if context_id not in self.cuts:
            raise ValueError(f"Context {context_id} not found")
        return self.cuts[context_id]
    
    def _context_dominates(self, edge_context: Context, vertex_context: Context) -> bool:
        """Returns True if edge_context dominates vertex_context (edge_context <= vertex_context)."""
        current = vertex_context
        while current is not None:
            if current == edge_context:
                return True
            current = current.parent
        return False
    
    def _validate_dominating_nodes(self) -> None:
        """Validates that all edges satisfy the dominating nodes constraint."""
        for edge in self.edges.values():
            for vertex_id in edge.incident_vertices:
                vertex = self.vertices[vertex_id]
                if not self._context_dominates(edge.context, vertex.context):
                    raise ValueError(f"Dominating nodes constraint violated for edge {edge.id}")
    
    def is_well_formed(self) -> bool:
        """Validates that this EGI satisfies all well-formedness constraints."""
        try:
            # Check dominating nodes constraint
            self._validate_dominating_nodes()
            return True
        except ValueError:
            return False

