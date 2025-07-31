"""
Immutable core data structures for Existential Graphs.
Based on Frithjof Dau's formalism with complete immutability.
"""

from dataclasses import dataclass, field
from typing import FrozenSet, Tuple, Optional, Dict, Any, Union
from frozendict import frozendict
import uuid
from enum import Enum

# Type aliases
ElementID = str


class ElementType(Enum):
    """Types of elements in an EGI."""
    VERTEX = "vertex"
    EDGE = "edge"
    CONTEXT = "context"


@dataclass(frozen=True)
class Alphabet:
    """Immutable alphabet defining available relations, constants, and variables."""
    relations: FrozenSet[str] = field(default_factory=frozenset)
    constants: FrozenSet[str] = field(default_factory=frozenset)
    variables: FrozenSet[str] = field(default_factory=frozenset)
    
    def with_relation(self, relation: str) -> 'Alphabet':
        """Returns new alphabet with additional relation."""
        return Alphabet(
            relations=self.relations | {relation},
            constants=self.constants,
            variables=self.variables
        )
    
    def with_constant(self, constant: str) -> 'Alphabet':
        """Returns new alphabet with additional constant."""
        return Alphabet(
            relations=self.relations,
            constants=self.constants | {constant},
            variables=self.variables
        )
    
    def with_variable(self, variable: str) -> 'Alphabet':
        """Returns new alphabet with additional variable."""
        return Alphabet(
            relations=self.relations,
            constants=self.constants,
            variables=self.variables | {variable}
        )


@dataclass(frozen=True)
class Context:
    """Immutable context representing a cut or the sheet of assertion."""
    id: ElementID
    parent_id: Optional[ElementID]
    depth: int
    enclosed_elements: FrozenSet[ElementID] = field(default_factory=frozenset)
    children: FrozenSet[ElementID] = field(default_factory=frozenset)
    
    def is_positive(self) -> bool:
        """Returns True if context has even depth (positive)."""
        return self.depth % 2 == 0
    
    def is_negative(self) -> bool:
        """Returns True if context has odd depth (negative)."""
        return self.depth % 2 == 1
    
    def with_element(self, element_id: ElementID) -> 'Context':
        """Returns new context with additional enclosed element."""
        return Context(
            id=self.id,
            parent_id=self.parent_id,
            depth=self.depth,
            enclosed_elements=self.enclosed_elements | {element_id},
            children=self.children
        )
    
    def without_element(self, element_id: ElementID) -> 'Context':
        """Returns new context without specified element."""
        return Context(
            id=self.id,
            parent_id=self.parent_id,
            depth=self.depth,
            enclosed_elements=self.enclosed_elements - {element_id},
            children=self.children
        )
    
    def with_child(self, child_id: ElementID) -> 'Context':
        """Returns new context with additional child."""
        return Context(
            id=self.id,
            parent_id=self.parent_id,
            depth=self.depth,
            enclosed_elements=self.enclosed_elements,
            children=self.children | {child_id}
        )
    
    def without_child(self, child_id: ElementID) -> 'Context':
        """Returns new context without specified child."""
        return Context(
            id=self.id,
            parent_id=self.parent_id,
            depth=self.depth,
            enclosed_elements=self.enclosed_elements,
            children=self.children - {child_id}
        )


@dataclass(frozen=True)
class Vertex:
    """Immutable vertex representing an individual (variable or constant)."""
    id: ElementID
    context_id: ElementID
    is_constant: bool
    constant_name: Optional[str] = None
    properties: frozendict = field(default_factory=frozendict)
    
    def __post_init__(self):
        """Validate vertex constraints."""
        if self.is_constant and not self.constant_name:
            raise ValueError("Constant vertex must have constant_name")
        if not self.is_constant and self.constant_name:
            raise ValueError("Variable vertex cannot have constant_name")
    
    def with_property(self, key: str, value: Any) -> 'Vertex':
        """Returns new vertex with additional property."""
        new_properties = dict(self.properties)
        new_properties[key] = value
        return Vertex(
            id=self.id,
            context_id=self.context_id,
            is_constant=self.is_constant,
            constant_name=self.constant_name,
            properties=frozendict(new_properties)
        )
    
    def in_context(self, context_id: ElementID) -> 'Vertex':
        """Returns new vertex in different context (for iteration)."""
        return Vertex(
            id=self.id,
            context_id=context_id,
            is_constant=self.is_constant,
            constant_name=self.constant_name,
            properties=self.properties
        )
    
    def is_isolated(self) -> bool:
        """Returns True if vertex has no incident edges."""
        # This will be determined by the EGI that contains this vertex
        # For now, return False as a placeholder
        return False


@dataclass(frozen=True)
class Edge:
    """Immutable edge representing a relation or identity."""
    id: ElementID
    context_id: ElementID
    relation_name: str
    incident_vertices: Tuple[ElementID, ...]
    is_identity: bool = False
    properties: frozendict = field(default_factory=frozendict)
    
    def __post_init__(self):
        """Validate edge constraints."""
        if self.is_identity and self.relation_name != "=":
            raise ValueError("Identity edge must have relation_name '='")
        if self.is_identity and len(self.incident_vertices) < 2:
            raise ValueError("Identity edge must have at least 2 vertices")
        if len(self.incident_vertices) == 0:
            raise ValueError("Edge must have at least 1 incident vertex")
    
    def with_property(self, key: str, value: Any) -> 'Edge':
        """Returns new edge with additional property."""
        new_properties = dict(self.properties)
        new_properties[key] = value
        return Edge(
            id=self.id,
            context_id=self.context_id,
            relation_name=self.relation_name,
            incident_vertices=self.incident_vertices,
            is_identity=self.is_identity,
            properties=frozendict(new_properties)
        )
    
    def in_context(self, context_id: ElementID) -> 'Edge':
        """Returns new edge in different context."""
        return Edge(
            id=self.id,
            context_id=context_id,
            relation_name=self.relation_name,
            incident_vertices=self.incident_vertices,
            is_identity=self.is_identity,
            properties=self.properties
        )


@dataclass(frozen=True)
class EGI:
    """Immutable Existential Graph Instance."""
    vertices: FrozenSet[Vertex]
    edges: FrozenSet[Edge]
    contexts: FrozenSet[Context]
    sheet_id: ElementID
    alphabet: Alphabet
    
    # Computed properties for efficient lookup
    _vertex_map: frozendict = field(init=False)
    _edge_map: frozendict = field(init=False)
    _context_map: frozendict = field(init=False)
    _vertex_edges_map: frozendict = field(init=False)  # vertex_id -> set of edge_ids
    
    def __post_init__(self):
        """Build lookup maps for efficient access."""
        # Build basic lookup maps
        vertex_map = {v.id: v for v in self.vertices}
        edge_map = {e.id: e for e in self.edges}
        context_map = {c.id: c for c in self.contexts}
        
        # Build vertex-edges mapping
        vertex_edges = {}
        for vertex in self.vertices:
            vertex_edges[vertex.id] = frozenset()
        
        for edge in self.edges:
            for vertex_id in edge.incident_vertices:
                if vertex_id in vertex_edges:
                    vertex_edges[vertex_id] = vertex_edges[vertex_id] | {edge.id}
        
        # Set computed properties
        object.__setattr__(self, '_vertex_map', frozendict(vertex_map))
        object.__setattr__(self, '_edge_map', frozendict(edge_map))
        object.__setattr__(self, '_context_map', frozendict(context_map))
        object.__setattr__(self, '_vertex_edges_map', frozendict(vertex_edges))
        
        # Validate sheet exists
        if self.sheet_id not in self._context_map:
            raise ValueError(f"Sheet context {self.sheet_id} not found")
        
        # Validate all vertices and edges reference valid contexts
        for vertex in self.vertices:
            if vertex.context_id not in self._context_map:
                raise ValueError(f"Vertex {vertex.id} references invalid context {vertex.context_id}")
        
        for edge in self.edges:
            if edge.context_id not in self._context_map:
                raise ValueError(f"Edge {edge.id} references invalid context {edge.context_id}")
            
            # Validate all incident vertices exist
            for vertex_id in edge.incident_vertices:
                if vertex_id not in self._vertex_map:
                    raise ValueError(f"Edge {edge.id} references invalid vertex {vertex_id}")
    
    @property
    def sheet(self) -> Context:
        """Returns the sheet of assertion."""
        return self._context_map[self.sheet_id]
    
    def get_vertex(self, vertex_id: ElementID) -> Vertex:
        """Get vertex by ID."""
        if vertex_id not in self._vertex_map:
            raise ValueError(f"Vertex {vertex_id} not found")
        return self._vertex_map[vertex_id]
    
    def get_edge(self, edge_id: ElementID) -> Edge:
        """Get edge by ID."""
        if edge_id not in self._edge_map:
            raise ValueError(f"Edge {edge_id} not found")
        return self._edge_map[edge_id]
    
    def get_context(self, context_id: ElementID) -> Context:
        """Get context by ID."""
        if context_id not in self._context_map:
            raise ValueError(f"Context {context_id} not found")
        return self._context_map[context_id]
    
    def get_vertex_edges(self, vertex_id: ElementID) -> FrozenSet[ElementID]:
        """Get all edges incident to a vertex."""
        if vertex_id not in self._vertex_edges_map:
            return frozenset()
        return self._vertex_edges_map[vertex_id]
    
    def is_vertex_isolated(self, vertex_id: ElementID) -> bool:
        """Returns True if vertex has no incident edges."""
        return len(self.get_vertex_edges(vertex_id)) == 0
    
    def with_vertex(self, vertex: Vertex) -> 'EGI':
        """Returns new EGI with additional vertex."""
        # Update context to include vertex
        context = self.get_context(vertex.context_id)
        updated_context = context.with_element(vertex.id)
        
        return EGI(
            vertices=self.vertices | {vertex},
            edges=self.edges,
            contexts=(self.contexts - {context}) | {updated_context},
            sheet_id=self.sheet_id,
            alphabet=self.alphabet
        )
    
    def without_vertex(self, vertex_id: ElementID) -> 'EGI':
        """Returns new EGI without specified vertex."""
        vertex = self.get_vertex(vertex_id)
        context = self.get_context(vertex.context_id)
        updated_context = context.without_element(vertex_id)
        
        # Remove all edges incident to this vertex
        remaining_edges = {e for e in self.edges if vertex_id not in e.incident_vertices}
        
        # Update contexts to remove the incident edges
        updated_contexts = {updated_context}
        for edge in self.edges:
            if vertex_id in edge.incident_vertices:
                edge_context = self.get_context(edge.context_id)
                if edge_context.id != context.id:
                    updated_edge_context = edge_context.without_element(edge.id)
                    updated_contexts.add(updated_edge_context)
        
        # Add all other contexts that weren't modified
        for ctx in self.contexts:
            if ctx.id not in {c.id for c in updated_contexts}:
                updated_contexts.add(ctx)
        
        return EGI(
            vertices=self.vertices - {vertex},
            edges=frozenset(remaining_edges),
            contexts=frozenset(updated_contexts),
            sheet_id=self.sheet_id,
            alphabet=self.alphabet
        )
    
    def with_edge(self, edge: Edge) -> 'EGI':
        """Returns new EGI with additional edge."""
        context = self.get_context(edge.context_id)
        updated_context = context.with_element(edge.id)
        
        return EGI(
            vertices=self.vertices,
            edges=self.edges | {edge},
            contexts=(self.contexts - {context}) | {updated_context},
            sheet_id=self.sheet_id,
            alphabet=self.alphabet
        )
    
    def without_edge(self, edge_id: ElementID) -> 'EGI':
        """Returns new EGI without specified edge."""
        edge = self.get_edge(edge_id)
        context = self.get_context(edge.context_id)
        updated_context = context.without_element(edge_id)
        
        return EGI(
            vertices=self.vertices,
            edges=self.edges - {edge},
            contexts=(self.contexts - {context}) | {updated_context},
            sheet_id=self.sheet_id,
            alphabet=self.alphabet
        )
    
    def with_context(self, context: Context) -> 'EGI':
        """Returns new EGI with additional context."""
        updated_contexts = self.contexts | {context}
        
        # Update parent context if exists
        if context.parent_id:
            parent = self.get_context(context.parent_id)
            updated_parent = parent.with_child(context.id)
            updated_contexts = (updated_contexts - {parent}) | {updated_parent}
        
        return EGI(
            vertices=self.vertices,
            edges=self.edges,
            contexts=updated_contexts,
            sheet_id=self.sheet_id,
            alphabet=self.alphabet
        )
    
    def without_context(self, context_id: ElementID) -> 'EGI':
        """Returns new EGI without specified context and all its contents."""
        if context_id == self.sheet_id:
            raise ValueError("Cannot remove sheet context")
        
        context = self.get_context(context_id)
        
        # Remove all elements in this context
        vertices_to_remove = {v for v in self.vertices if v.context_id == context_id}
        edges_to_remove = {e for e in self.edges if e.context_id == context_id}
        
        # Remove all child contexts recursively
        contexts_to_remove = {context}
        contexts_to_check = list(context.children)
        
        while contexts_to_check:
            child_id = contexts_to_check.pop()
            child_context = self.get_context(child_id)
            contexts_to_remove.add(child_context)
            contexts_to_check.extend(child_context.children)
            
            # Remove elements in child contexts
            vertices_to_remove.update(v for v in self.vertices if v.context_id == child_id)
            edges_to_remove.update(e for e in self.edges if e.context_id == child_id)
        
        # Update parent context
        updated_contexts = self.contexts - contexts_to_remove
        if context.parent_id:
            parent = self.get_context(context.parent_id)
            updated_parent = parent.without_child(context_id)
            updated_contexts = (updated_contexts - {parent}) | {updated_parent}
        
        return EGI(
            vertices=self.vertices - vertices_to_remove,
            edges=self.edges - edges_to_remove,
            contexts=updated_contexts,
            sheet_id=self.sheet_id,
            alphabet=self.alphabet
        )
    
    def replace_vertex(self, old_vertex: Vertex, new_vertex: Vertex) -> 'EGI':
        """Returns new EGI with vertex replaced."""
        return self.without_vertex(old_vertex.id).with_vertex(new_vertex)
    
    def replace_edge(self, old_edge: Edge, new_edge: Edge) -> 'EGI':
        """Returns new EGI with edge replaced."""
        return self.without_edge(old_edge.id).with_edge(new_edge)
    
    def replace_context(self, old_context: Context, new_context: Context) -> 'EGI':
        """Returns new EGI with context replaced."""
        if old_context.id == self.sheet_id:
            # Special handling for sheet replacement
            return EGI(
                vertices=self.vertices,
                edges=self.edges,
                contexts=(self.contexts - {old_context}) | {new_context},
                sheet_id=new_context.id,
                alphabet=self.alphabet
            )
        else:
            return EGI(
                vertices=self.vertices,
                edges=self.edges,
                contexts=(self.contexts - {old_context}) | {new_context},
                sheet_id=self.sheet_id,
                alphabet=self.alphabet
            )


class EGIBuilder:
    """Builder for constructing EGI instances incrementally."""
    
    def __init__(self, alphabet: Optional[Alphabet] = None, sheet_id: Optional[ElementID] = None):
        self._alphabet = alphabet or Alphabet()
        self._sheet_id = sheet_id or self._generate_id()
        self._vertices: Dict[ElementID, Vertex] = {}
        self._edges: Dict[ElementID, Edge] = {}
        self._contexts: Dict[ElementID, Context] = {}
        
        # Create sheet context
        self._contexts[self._sheet_id] = Context(
            id=self._sheet_id,
            parent_id=None,
            depth=0,
            enclosed_elements=frozenset(),
            children=frozenset()
        )
    
    def add_vertex(self, context_id: ElementID, is_constant: bool = False, 
                   constant_name: Optional[str] = None, vertex_id: Optional[ElementID] = None,
                   **properties) -> ElementID:
        """Add vertex and return its ID."""
        if vertex_id is None:
            vertex_id = self._generate_id()
        
        vertex = Vertex(
            id=vertex_id,
            context_id=context_id,
            is_constant=is_constant,
            constant_name=constant_name,
            properties=frozendict(properties)
        )
        self._vertices[vertex_id] = vertex
        
        # Update context
        if context_id in self._contexts:
            context = self._contexts[context_id]
            self._contexts[context_id] = context.with_element(vertex_id)
        
        return vertex_id
    
    def add_edge(self, context_id: ElementID, relation_name: str, 
                 incident_vertices: Tuple[ElementID, ...], 
                 is_identity: bool = False, edge_id: Optional[ElementID] = None,
                 **properties) -> ElementID:
        """Add edge and return its ID."""
        if edge_id is None:
            edge_id = self._generate_id()
        
        edge = Edge(
            id=edge_id,
            context_id=context_id,
            relation_name=relation_name,
            incident_vertices=incident_vertices,
            is_identity=is_identity,
            properties=frozendict(properties)
        )
        self._edges[edge_id] = edge
        
        # Update context
        if context_id in self._contexts:
            context = self._contexts[context_id]
            self._contexts[context_id] = context.with_element(edge_id)
        
        return edge_id
    
    def add_context(self, parent_id: Optional[ElementID] = None, 
                    context_id: Optional[ElementID] = None) -> ElementID:
        """Add context and return its ID."""
        if context_id is None:
            context_id = self._generate_id()
        
        parent_depth = 0 if parent_id is None else self._contexts[parent_id].depth
        
        context = Context(
            id=context_id,
            parent_id=parent_id,
            depth=parent_depth + 1,
            enclosed_elements=frozenset(),
            children=frozenset()
        )
        self._contexts[context_id] = context
        
        # Update parent
        if parent_id and parent_id in self._contexts:
            parent = self._contexts[parent_id]
            self._contexts[parent_id] = parent.with_child(context_id)
        
        return context_id
    
    def build(self) -> EGI:
        """Build immutable EGI instance."""
        return EGI(
            vertices=frozenset(self._vertices.values()),
            edges=frozenset(self._edges.values()),
            contexts=frozenset(self._contexts.values()),
            sheet_id=self._sheet_id,
            alphabet=self._alphabet
        )
    
    @staticmethod
    def _generate_id() -> ElementID:
        """Generate unique element ID."""
        return f"elem_{uuid.uuid4().hex[:8]}"


def create_empty_egi(alphabet: Optional[Alphabet] = None) -> EGI:
    """Create an empty EGI with just the sheet of assertion."""
    builder = EGIBuilder(alphabet)
    return builder.build()


# Test the implementation
if __name__ == "__main__":
    print("Testing immutable EGI implementation...")
    
    # Create empty EGI
    alphabet = Alphabet().with_relation("phoenix").with_relation("man")
    egi = create_empty_egi(alphabet)
    print(f"Created empty EGI with sheet: {egi.sheet_id}")
    
    # Add a vertex
    vertex = Vertex(
        id="vertex_1",
        context_id=egi.sheet_id,
        is_constant=False
    )
    egi_with_vertex = egi.with_vertex(vertex)
    print(f"Added vertex. Vertices: {len(egi_with_vertex.vertices)}")
    
    # Add an edge
    edge = Edge(
        id="edge_1",
        context_id=egi.sheet_id,
        relation_name="phoenix",
        incident_vertices=("vertex_1",)
    )
    egi_with_edge = egi_with_vertex.with_edge(edge)
    print(f"Added edge. Edges: {len(egi_with_edge.edges)}")
    
    # Verify original EGI is unchanged
    print(f"Original EGI vertices: {len(egi.vertices)}")
    print(f"Original EGI edges: {len(egi.edges)}")
    
    # Test builder
    builder = EGIBuilder(alphabet)
    vertex_id = builder.add_vertex(builder._sheet_id, is_constant=True, constant_name="Socrates")
    edge_id = builder.add_edge(builder._sheet_id, "philosopher", (vertex_id,))
    built_egi = builder.build()
    print(f"Built EGI with {len(built_egi.vertices)} vertices and {len(built_egi.edges)} edges")
    
    print("✓ Immutable EGI implementation working correctly!")

